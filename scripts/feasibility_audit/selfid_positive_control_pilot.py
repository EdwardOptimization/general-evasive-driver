"""Self-ID positive-control pilot: train smoke twins, then run the hidden-swap gate chain.

Purpose (infrastructure + plumbing only, NO scientific conclusion)
------------------------------------------------------------------

This script exercises the execution chain

    train_ppo (privileged obs76 twin, P0 obs72 twin)
        -> load_actor_critic_checkpoint
        -> autodrift.hidden_swap_gate.run_hidden_swap_gate
        -> privileged-channel value-swap probe

at smoke budget (default 1024 training steps per twin). It exists because the
planned self-ID completion experiments need a POSITIVE CONTROL for the
hidden-swap gate methodology, and M1199/M1497 taught us that short-budget runs
must never be interpreted as evidence. This script therefore only verifies
that every link of the chain runs, produces finite metrics, and handles the
privileged 76-value observation correctly. Any number it prints is plumbing
output, not a result.

What "hidden swap" means when the actor input is privileged
-----------------------------------------------------------

The hidden-swap gate intervenes on the policy's RECURRENT HIDDEN STATE: it
collects matched decision snapshots under a nominal and a perturbed hidden
condition, then replays continuations where the GRU hidden state is swapped
between the two conditions. For a P0 (human-view) policy, the hidden state is
the only place a hidden-dynamics belief can live, so hidden-swap sensitivity
is evidence about history-encoded belief.

For a PRIVILEGED policy the semantics change in three important ways:

1. The current frame already contains the hidden parameters explicitly
   (per-frame indices 72-75 in basic mode: [mu, mass/mass0, lf/lf0, cr/cr0]).
   A well-trained privileged policy has no need to store capability belief in
   its GRU hidden state, so swapping the hidden state alone is EXPECTED to
   produce little or no outcome change. A null hidden-swap result on the
   privileged twin is therefore NOT a gate failure; it is the predicted
   behavior of a policy whose belief channel is the observation itself.
2. The gate's matched-observation acceptance distance includes the privileged
   channels. Because mu differs between the nominal and perturbed conditions
   by construction, the full-observation distance has a floor of roughly
   |mu_nominal - mu_perturbed| (~0.5-0.9), so ``max_observation_distance``
   must be raised above the P0 default (0.75) or every privileged pair would
   be rejected as unmatched. The gate's ``zero_response`` variant zeroes only
   the per-frame response indices 0-11; privileged channels are context and
   stay intact, which is the correct handling for this control.
3. The analogue of "swap the belief" for a privileged policy is to swap the
   PRIVILEGED CHANNEL VALUES in the observation, not the GRU hidden state.
   That is the decisive positive control implemented here as the
   ``privileged_value_swap`` probe: continuations are replayed with the
   per-frame privileged dims overridden (frozen) to the paired condition's
   snapshot values while the simulator keeps the true dynamics.

Pre-registered expectation for the FULL-BUDGET positive control (recorded in
docs/selfid-completion-experiment-design-2026-06.md): a converged privileged
policy must show a significant action and outcome change under
``privileged_value_swap`` (it is reading those channels, or it could not beat
the P0 twin). If even a converged privileged policy shows no detectable
outcome change under this intervention, the outcome-difference detection
machinery shared with the hidden-swap gate is not sensitive enough, and the
gate methodology itself is invalid for this task family. That would be a
paper-level methodological finding, not a nuisance.

At THIS script's smoke budget, none of the above expectations are tested;
only the chain's executability is.

Usage:

    python scripts/feasibility_audit/selfid_positive_control_pilot.py \
        --output-dir runs/selfid_positive_control_pilot

Exit code 0 means every chain link executed and produced the required rows.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, BASIC_PRIVILEGED_OBS_DIM, DriftEnvConfig
from autodrift.hidden_swap_gate import (
    DecisionSnapshot,
    clone_hidden,
    collect_decision_snapshot,
    replay_continuation,
    run_hidden_swap_gate,
    terminal_reason,
)
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import ActorCritic


PRIVILEGED_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_privileged_smoke.json"
P0_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_p0_smoke.json"

NOMINAL_MU_RANGE = (0.85, 1.15)
PERTURBED_MU_RANGE = (0.25, 0.35)


def load_raw_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def privileged_slice(env_config: DriftEnvConfig) -> slice:
    """Per-frame slice of the privileged basic channels (history_length must be 1)."""

    if not env_config.include_privileged_params:
        raise ValueError("env config does not include privileged params")
    if env_config.privileged_observation_mode != "basic":
        raise ValueError("this pilot only supports privileged_observation_mode='basic'")
    if env_config.history_length != 1:
        raise ValueError("this pilot only supports history_length=1")
    base_dim = AutoDriftEnv(env_config).base_obs_dim
    return slice(base_dim - BASIC_PRIVILEGED_OBS_DIM, base_dim)


def run_training(
    config_path: Path,
    run_dir: Path,
    *,
    total_steps: int | None,
    device: str,
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = run_dir / "checkpoint.pt"
    command = [
        sys.executable,
        "-m",
        "autodrift.train_ppo",
        "--config",
        str(config_path),
        "--run-dir",
        str(run_dir),
        "--save",
        str(checkpoint_path),
        "--device",
        device,
        "--eval-episodes",
        "1",
    ]
    if total_steps is not None:
        command.extend(["--total-steps", str(int(total_steps))])
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    (run_dir / "train_stdout.log").write_text(result.stdout, encoding="utf-8")
    (run_dir / "train_stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(
            f"training failed for {config_path} (exit {result.returncode}); "
            f"see {run_dir / 'train_stderr.log'}"
        )
    if not checkpoint_path.exists():
        raise RuntimeError(f"training did not produce a checkpoint at {checkpoint_path}")
    return checkpoint_path


def replay_privileged_value_swap(
    model: ActorCritic,
    snapshot: DecisionSnapshot,
    override_values: np.ndarray,
    *,
    env_config: DriftEnvConfig,
    normal_first_action: np.ndarray | None,
    max_continuation_steps: int | None,
) -> dict[str, Any]:
    """Replay a continuation with the privileged channels frozen to paired values.

    The simulator keeps the TRUE dynamics of the source snapshot; only the
    policy's explicit capability channel is replaced, every step, with the
    paired condition's snapshot values. This is the privileged analogue of a
    wrong-history / hidden-swap intervention.
    """

    priv = privileged_slice(env_config)
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = clone_hidden(snapshot.hidden)

    max_steps = max_continuation_steps
    if max_steps is None or max_steps <= 0:
        max_steps = max(1, env_config.max_steps - snapshot.step)

    rewards: list[float] = []
    actions: list[np.ndarray] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        policy_obs[priv] = override_values.astype(np.float32)
        action, _, _, hidden = model.act_recurrent(policy_obs, hidden, deterministic=True)
        actions.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        if terminated or truncated:
            break

    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_action_distance = (
        float(np.linalg.norm(first_action - normal_first_action))
        if normal_first_action is not None and np.all(np.isfinite(first_action))
        else float("nan")
    )
    reason = terminal_reason(info, terminated, truncated, env_config)
    return {
        "variant": "privileged_value_swap",
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "first_action_distance": first_action_distance,
    }


def run_privileged_value_swap_probe(
    model: ActorCritic,
    base_env_config: DriftEnvConfig,
    seeds: list[int],
    *,
    target_obstacle_distance: float,
    max_continuation_steps: int | None,
) -> pd.DataFrame:
    configs = {
        "nominal": condition_config(base_env_config, NOMINAL_MU_RANGE, None),
        "perturbed": condition_config(base_env_config, PERTURBED_MU_RANGE, None),
    }
    priv = privileged_slice(base_env_config)
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        snapshots = {
            condition: collect_decision_snapshot(
                model,
                env_config,
                condition,
                seed,
                target_obstacle_distance=target_obstacle_distance,
            )
            for condition, env_config in configs.items()
        }
        nominal = snapshots["nominal"]
        perturbed = snapshots["perturbed"]
        if nominal is None or perturbed is None:
            rows.append({"seed": seed, "pair_status": "missing_snapshot"})
            continue
        for source, paired in ((nominal, perturbed), (perturbed, nominal)):
            source_config = configs[source.condition]
            normal, _ = replay_continuation(
                model,
                source,
                env_config=source_config,
                variant="normal",
                max_continuation_steps=max_continuation_steps,
            )
            normal_first_action = np.array(
                [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
                dtype=np.float32,
            )
            override_values = np.asarray(paired.observation[priv], dtype=np.float64)
            swap = replay_privileged_value_swap(
                model,
                source,
                override_values,
                env_config=source_config,
                normal_first_action=normal_first_action,
                max_continuation_steps=max_continuation_steps,
            )
            rows.append(
                {
                    "seed": seed,
                    "pair_status": "paired",
                    "source_condition": source.condition,
                    "paired_condition": paired.condition,
                    "source_step": source.step,
                    "privileged_value_distance": float(
                        np.linalg.norm(
                            np.asarray(source.observation[priv], dtype=np.float64) - override_values
                        )
                    ),
                    "normal_success": bool(normal["success"]),
                    "normal_return": float(normal["return"]),
                    "normal_min_clearance_margin": float(normal["min_clearance_margin"]),
                    "swap_success": bool(swap["success"]),
                    "swap_return": float(swap["return"]),
                    "swap_min_clearance_margin": float(swap["min_clearance_margin"]),
                    "swap_terminal_reason": swap["terminal_reason"],
                    "first_action_distance": float(swap["first_action_distance"]),
                    "success_delta": float(swap["success"]) - float(normal["success"]),
                    "margin_delta": float(swap["min_clearance_margin"]) - float(normal["min_clearance_margin"]),
                }
            )
    return pd.DataFrame(rows)


def run_gate_for_checkpoint(
    name: str,
    checkpoint_path: Path,
    env_config: DriftEnvConfig,
    output_dir: Path,
    *,
    device: str,
    seeds: list[int],
    max_observation_distance: float,
    target_obstacle_distance: float,
    max_continuation_steps: int | None,
) -> dict[str, Any]:
    obs_dim = int(AutoDriftEnv(env_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device, obs_dim=obs_dim)
    if not model.is_online_recurrent:
        raise RuntimeError(f"{name} checkpoint is not online recurrent; gate chain cannot run")
    pairs, replays, summary = run_hidden_swap_gate(
        model=model,
        base_config=env_config,
        seeds=seeds,
        nominal_friction_mu_range=NOMINAL_MU_RANGE,
        perturbed_friction_mu_range=PERTURBED_MU_RANGE,
        nominal_randomization={},
        perturbed_randomization={},
        target_obstacle_distance=target_obstacle_distance,
        min_probe_steps=10,
        max_probe_steps=180,
        require_friction_step=True,
        min_hidden_updates_after_friction=2,
        max_observation_distance=max_observation_distance,
        max_continuation_steps=max_continuation_steps,
    )
    gate_dir = output_dir / f"gate_{name}"
    gate_dir.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(gate_dir / "pairs.csv", index=False)
    replays.to_csv(gate_dir / "replays.csv", index=False)
    summary.to_csv(gate_dir / "summary.csv", index=False)
    replay_returns = replays["return"].to_numpy(dtype=np.float64) if not replays.empty else np.array([])
    return {
        "name": name,
        "obs_dim": obs_dim,
        "pair_rows": int(len(pairs)),
        "paired_rows": int((pairs.get("pair_status") == "paired").sum()) if not pairs.empty else 0,
        "accepted_match_rows": int(pairs.get("accepted_match", pd.Series(dtype=bool)).sum()) if not pairs.empty else 0,
        "replay_rows": int(len(replays)),
        "replay_variants": sorted(replays["variant"].unique().tolist()) if not replays.empty else [],
        "replay_returns_finite": bool(np.all(np.isfinite(replay_returns))) if replay_returns.size else False,
        "gate_dir": str(gate_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "runs" / "selfid_positive_control_pilot")
    parser.add_argument("--privileged-config", type=Path, default=PRIVILEGED_CONFIG)
    parser.add_argument("--p0-config", type=Path, default=P0_CONFIG)
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument("--total-steps", type=int, default=None, help="override config total_steps for both twins")
    parser.add_argument("--gate-episodes", type=int, default=8)
    parser.add_argument("--gate-seed", type=int, default=90600)
    parser.add_argument("--target-obstacle-distance", type=float, default=12.0)
    parser.add_argument(
        "--max-observation-distance",
        type=float,
        default=1.5,
        help=(
            "matched-pair acceptance distance; raised above the P0 default 0.75 because "
            "privileged channels add an irreducible cross-condition observation distance"
        ),
    )
    parser.add_argument("--max-continuation-steps", type=int, default=0)
    parser.add_argument("--skip-training", action="store_true", help="reuse checkpoints already in output-dir")
    args = parser.parse_args()

    torch.manual_seed(0)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    max_continuation_steps = args.max_continuation_steps if args.max_continuation_steps > 0 else None
    seeds = [args.gate_seed + index for index in range(args.gate_episodes)]

    twins = {
        "privileged": args.privileged_config,
        "p0": args.p0_config,
    }
    summary: dict[str, Any] = {
        "run_type": "selfid_positive_control_pilot",
        "stage": "infrastructure_smoke_only",
        "claim_level": "not_applicable",
        "no_scientific_conclusion": True,
        "configs": {name: str(path) for name, path in twins.items()},
        "gate_seeds": seeds,
        "max_observation_distance": args.max_observation_distance,
        "twins": {},
    }
    failures: list[str] = []

    checkpoints: dict[str, Path] = {}
    env_configs: dict[str, DriftEnvConfig] = {}
    for name, config_path in twins.items():
        raw = load_raw_config(config_path)
        env_configs[name] = build_env_config(raw["env"])
        run_dir = output_dir / f"train_{name}"
        checkpoint_path = run_dir / "checkpoint.pt"
        if args.skip_training and checkpoint_path.exists():
            print(f"[{name}] reusing checkpoint {checkpoint_path}")
        else:
            print(f"[{name}] training smoke from {config_path} ...")
            checkpoint_path = run_training(
                config_path,
                run_dir,
                total_steps=args.total_steps,
                device=args.device,
            )
        checkpoints[name] = checkpoint_path
        summary["twins"][name] = {"checkpoint": str(checkpoint_path)}

    expected_obs_dims = {"privileged": 76, "p0": 72}
    for name in twins:
        print(f"[{name}] running hidden-swap gate chain ...")
        gate_summary = run_gate_for_checkpoint(
            name,
            checkpoints[name],
            env_configs[name],
            output_dir,
            device=args.device,
            seeds=seeds,
            max_observation_distance=args.max_observation_distance,
            target_obstacle_distance=args.target_obstacle_distance,
            max_continuation_steps=max_continuation_steps,
        )
        summary["twins"][name]["gate"] = gate_summary
        if gate_summary["obs_dim"] != expected_obs_dims[name]:
            failures.append(f"{name}: unexpected obs dim {gate_summary['obs_dim']}")
        if gate_summary["replay_rows"] < 1:
            failures.append(f"{name}: hidden-swap gate produced no replay rows")
        elif not gate_summary["replay_returns_finite"]:
            failures.append(f"{name}: hidden-swap gate produced non-finite replay returns")

    print("[privileged] running privileged-value-swap probe ...")
    obs_dim = int(AutoDriftEnv(env_configs["privileged"]).observation_space.shape[0])
    privileged_model, _ = load_actor_critic_checkpoint(
        checkpoints["privileged"], device=args.device, obs_dim=obs_dim
    )
    probe = run_privileged_value_swap_probe(
        privileged_model,
        env_configs["privileged"],
        seeds,
        target_obstacle_distance=args.target_obstacle_distance,
        max_continuation_steps=max_continuation_steps,
    )
    probe_csv = output_dir / "privileged_value_swap_probe.csv"
    probe.to_csv(probe_csv, index=False)
    paired_probe = probe[probe.get("pair_status") == "paired"] if not probe.empty else probe
    summary["privileged_value_swap_probe"] = {
        "rows": int(len(probe)),
        "paired_rows": int(len(paired_probe)),
        "first_action_distance_mean": (
            float(paired_probe["first_action_distance"].mean()) if len(paired_probe) else float("nan")
        ),
        "csv": str(probe_csv),
    }
    if len(paired_probe) < 1:
        failures.append("privileged_value_swap probe produced no paired rows")
    elif not np.all(np.isfinite(paired_probe["first_action_distance"].to_numpy(dtype=np.float64))):
        failures.append("privileged_value_swap probe produced non-finite first-action distances")

    summary["failures"] = failures
    summary["smoke_pass"] = not failures
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"summary={summary_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
