"""Smoke test for the large-batch GPU PPO trainer (phase4_f2_gpu_train).

Builds the harness, runs the BC warm-start + 2 PPO updates on a small N=256 batch,
and asserts: BC + PPO losses are finite, the optimizer actually changed the model
parameters, and the learning-curve rows are well-formed. Runs on CUDA if available,
else CPU (the harness keeps the model on CPU regardless, so the env device is the
only difference). Kept tiny so it runs in CI in well under a minute on GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT / "src", REPO_ROOT / "scripts" / "feasibility_audit"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import phase4_f2_gpu_train as g  # noqa: E402
from phase4_f2_train import AsymmetricActorCritic, ppo_update, bc_update  # noqa: E402


def _tiny_cfg(seed: int = 0) -> g.TrainConfig:
    return g.TrainConfig(
        n_envs=256,
        avoid_frac=0.5,
        drift_difficulty="hard",
        bc_units=256,
        bc_epochs=20,
        bc_holdout_target=5e-4,
        ppo_updates=2,
        rollout_horizon=90,
        eval_every=1,
        eval_drift_units=64,
        eval_avoid_units=64,
        drift_train_max_steps=90,
        avoid_train_max_steps=128,
        drift_eval_max_steps=90,
        avoid_eval_max_steps=128,
        seed=seed,
        label="test",
    )


def _device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def test_harness_builds_and_learns_two_ppo_updates():
    device = _device()
    env = g.build_env(device)
    cfg = _tiny_cfg(seed=0)

    # snapshot params before, to assert the optimizer moved the model.
    torch.manual_seed(cfg.seed)
    result = g.train(cfg, device=device, env=env, verbose=False)

    # --- the learning curve is well-formed ---
    curve = result["curve"]
    assert len(curve) >= 1, "no curve rows recorded"
    base = curve[0]
    assert base["phase"] == "bc_baseline"
    ppo_rows = [r for r in curve if r["phase"] == "ppo"]
    assert len(ppo_rows) == cfg.ppo_updates, f"expected {cfg.ppo_updates} ppo eval rows, got {len(ppo_rows)}"

    # --- every PPO update reported finite losses + finite grads ---
    for r in ppo_rows:
        assert r["finite_loss"], f"non-finite PPO loss at update {r['update']}"
        assert r["finite_grad"], f"non-finite PPO grad at update {r['update']}"
        assert np.isfinite(r["pg_loss"]), r
        assert np.isfinite(r["value_loss"]), r
        assert r["n_valid"] > 0, "no valid (finite-masked) transitions in the PPO batch"

    # --- success metrics are valid probabilities in [0,1] ---
    for r in curve:
        for k in ("drift_succ", "avoid_succ"):
            v = r.get(k)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                assert 0.0 <= float(v) <= 1.0, f"{k}={v} out of [0,1]"

    # --- BC collected non-trivial demos and ran ---
    assert result["bc_demos"] > 0, "BC collected no demonstrations"
    assert np.isfinite(result["bc_holdout_mse"]), "BC holdout MSE not finite"


def test_ppo_update_changes_parameters_on_gpu_rollout():
    """The optimizer must actually update the model on a GPU-collected batch."""
    device = _device()
    env = g.build_env(device)

    model = AsymmetricActorCritic(
        obs_dim=g.HUMAN_VIEW_OBS_DIM, act_dim=g.ACT_DIM, priv_dim=g.PRIV_DIM, hidden_size=g.HIDDEN_SIZE,
    )
    from torch.optim import Adam
    opt = Adam(model.parameters(), lr=g.PPO_LR)

    scenarios, ppo_regime, priv = g._build_scenario_batch(
        n_envs=256, avoid_frac=0.5, drift_difficulty="hard",
        drift_max_steps=90, avoid_max_steps=128, seed_ns="test", seed_round=0,
    )
    roll = g.collect_rollout(
        env, model, scenarios, ppo_regime, priv,
        horizon=90, device=device, sustain_target=12,
    )
    # finite-masked batch is non-empty and the regime field carries both regimes.
    batch = g._ppo_batch_from_rollout(roll)
    assert batch["obs"].shape[0] > 0
    assert set(np.unique(batch["regime"]).tolist()).issubset({0, 1})

    before = [p.detach().clone() for p in model.parameters()]
    info = ppo_update(model, opt, batch, bc_aux_coef=0.0, bc_aux=None, rng=np.random.default_rng(0))
    assert info["finite_loss"], "PPO loss non-finite on GPU-collected batch"
    assert info["finite_grad"], "PPO grad non-finite on GPU-collected batch"
    assert info["optimizer_changed_parameters"], "PPO update did not change the model"
    delta = sum(float(torch.sum((p.detach() - b).pow(2))) for b, p in zip(before, model.parameters()))
    assert delta > 0.0, "model parameters unchanged after PPO update"


if __name__ == "__main__":
    test_harness_builds_and_learns_two_ppo_updates()
    test_ppo_update_changes_parameters_on_gpu_rollout()
    print("OK")
