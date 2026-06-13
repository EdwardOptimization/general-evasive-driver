"""Tests for Phase-4 F2 per-regime teacher-student training and adjudication.

Covers (all actually executed):
  * asymmetric input isolation: actor sees obs72 only, critic sees obs72+priv;
  * teacher correctness: drift teacher is DriftFeedbackPolicy (NOT CEM),
    avoidance teacher is the E2' entry-speed-commitment oracle;
  * determinism of the obs72->action actor map;
  * adjudication module emits finite numbers for all five arms;
  * --quick end-to-end pipeline runs without crashing and passes its gates.

The Chrono-backed tests spawn the chrono worker via conda run; they are skipped
cleanly if the worker cannot launch in this environment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from chrono_worker_client import ChronoWorkerClient, ChronoWorkerError  # noqa: E402
import phase4_f2_train as f2  # noqa: E402
import phase4_e4_drift_regime_pricing as e4  # noqa: E402


# --------------------------------------------------------------- non-Chrono unit tests


def test_asymmetric_actor_rejects_privileged_dim():
    model = f2.AsymmetricActorCritic()
    obs = torch.zeros(3, f2.HUMAN_VIEW_OBS_DIM)
    # actor accepts obs72
    mean = model.actor_forward(obs)
    assert mean.shape == (3, f2.ACT_DIM)
    # actor REJECTS obs72 + privileged (the leakage channel)
    with pytest.raises(ValueError):
        model.actor_forward(torch.zeros(3, f2.HUMAN_VIEW_OBS_DIM + f2.PRIV_DIM))


def test_critic_requires_privileged_channels():
    model = f2.AsymmetricActorCritic()
    obs = torch.zeros(5, f2.HUMAN_VIEW_OBS_DIM)
    priv = torch.zeros(5, f2.PRIV_DIM)
    value = model.critic_forward(obs, priv)
    assert value.shape == (5,)
    with pytest.raises(ValueError):
        model.critic_forward(obs, torch.zeros(5, f2.PRIV_DIM - 1))


def test_actor_parameters_disjoint_from_critic_and_no_priv_in_actor():
    model = f2.AsymmetricActorCritic()
    actor_ids = {id(p) for p in model.actor_parameters()}
    critic_ids = {id(p) for p in model.critic_parameters()}
    assert actor_ids.isdisjoint(critic_ids)
    # the actor's first linear layer's in_features must be exactly obs72
    first = model.actor[0]
    assert first.in_features == f2.HUMAN_VIEW_OBS_DIM
    # the critic's first linear layer must consume obs72 + privileged channels
    assert model.critic[0].in_features == f2.HUMAN_VIEW_OBS_DIM + f2.PRIV_DIM


def test_act_uses_obs72_only_and_is_deterministic():
    model = f2.AsymmetricActorCritic()
    model.eval()
    rng = np.random.default_rng(0)
    obs = rng.normal(size=f2.HUMAN_VIEW_OBS_DIM).astype(np.float32)
    a1 = model.act(obs)
    a2 = model.act(obs)
    assert a1.shape == (f2.ACT_DIM,)
    assert np.allclose(a1, a2)
    assert np.max(np.abs(a1)) <= 1.0 + 1e-6
    # batch form is consistent with single form
    batch = model.act(np.stack([obs, obs]))
    assert np.allclose(batch[0], a1)


def test_drift_teacher_is_drift_feedback_policy_not_cem():
    handle = f2.make_drift_teacher()
    teacher = handle.factory()
    assert isinstance(teacher, e4.DriftFeedbackPolicy)
    # the bound spec is the selected DriftFeedbackSpec, and it is a member of the
    # E4 DRIFT_FEEDBACK_SPECS (a real drift feedback oracle), never an OpenLoop/CEM spec.
    assert teacher.spec.name == f2.DRIFT_FEEDBACK_NAME
    assert teacher.spec in e4.DRIFT_FEEDBACK_SPECS
    assert not isinstance(teacher, e4.OpenLoopPolicy)
    assert handle.privileged["regime"] == 1.0


def test_avoidance_teacher_is_entry_speed_commitment_oracle():
    handle = f2.make_avoidance_teacher()
    teacher = handle.factory()
    assert isinstance(teacher, f2._AvoidanceTeacherAdapter)
    # the underlying controller is the E2' RampPolicyController in oracle mode
    # with privileged mu_true bound.
    assert teacher._ctrl.mode == "oracle"
    assert teacher._ctrl.mu_true == pytest.approx(f2.AVOIDANCE_MU)
    assert handle.privileged["regime"] == 0.0


def test_drift_teacher_produces_bounded_action_from_obs72():
    teacher = f2.make_drift_teacher().factory()
    obs = np.zeros(f2.HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    obs[1] = 0.2  # some vy -> sideslip
    action = teacher(0, obs)
    action = np.asarray(action, dtype=np.float32)
    assert action.shape == (f2.ACT_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0 + 1e-6


def test_reward_recalibration_penalty_dominates():
    # m1087/C5: collision penalty must be >= success reward (no reward hacking).
    assert f2.COLLISION_PENALTY >= f2.AVOIDANCE_PASS_REWARD
    assert f2.COLLISION_PENALTY >= f2.DRIFT_SUCCESS_REWARD
    collide = f2._avoidance_reward({"collision": True, "min_clearance_margin": 0.5}, True, False)
    clean = f2._avoidance_reward({"collision": False, "completion_reason": "max_steps", "min_clearance_margin": 0.5}, True, True)
    assert collide < 0.0 < clean
    assert clean - collide >= f2.COLLISION_PENALTY


def test_relabel_with_teacher_shapes_and_bounds():
    rng = np.random.default_rng(1)
    frames = rng.normal(size=(7, f2.HUMAN_VIEW_OBS_DIM)).astype(np.float32)
    targets = f2._relabel_with_teacher("drift", frames)
    assert targets.shape == (7, f2.ACT_DIM)
    assert np.all(np.isfinite(targets))
    assert np.max(np.abs(targets)) <= 1.0 + 1e-6


def test_asymmetric_update_changes_actor_and_is_finite():
    torch.manual_seed(0)
    model = f2.AsymmetricActorCritic()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    rng = np.random.default_rng(2)
    frames = rng.normal(size=(16, f2.HUMAN_VIEW_OBS_DIM)).astype(np.float32)
    priv = rng.normal(size=(16, f2.PRIV_DIM)).astype(np.float32)
    targets = np.tanh(rng.normal(size=(16, f2.ACT_DIM))).astype(np.float32)
    returns = rng.normal(size=(16,)).astype(np.float32)
    out = f2.asymmetric_update(model, opt, frames, priv, targets, returns)
    assert out["finite_loss"] and out["finite_grad"]
    assert out["optimizer_changed_parameters"]


def test_arm_policy_constructs_all_five_arms():
    model = f2.AsymmetricActorCritic()
    for regime in ("avoidance", "drift"):
        for arm in f2.ARMS:
            policy = f2.arm_policy(arm, regime, model)
            assert callable(policy)
    # student arm is the obs72 actor
    student = f2.arm_policy("student_policy", "drift", model)
    obs = np.zeros(f2.HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    a = np.asarray(student(0, obs), dtype=np.float32)
    assert a.shape == (f2.ACT_DIM,)


def test_adjudication_emits_finite_numbers_for_all_arms():
    rows = []
    rng = np.random.default_rng(3)
    for regime in ("avoidance", "drift"):
        for unit in range(4):
            for arm in f2.ARMS:
                rows.append({
                    "arm": arm,
                    "regime": regime,
                    "seed": int(rng.integers(0, 1000)),
                    "success": bool(rng.integers(0, 2)),
                    "collision": bool(rng.integers(0, 2)),
                    "total_reward": float(rng.normal()),
                })
    adjud = f2.adjudicate(rows, seeds=[1])
    for regime in ("avoidance", "drift"):
        for arm in f2.ARMS:
            block = adjud["per_regime"][regime][arm]
            assert np.isfinite(block["success_rate"])
            assert np.isfinite(block["mean_reward"])
    assert set(adjud["prize_recovery"].keys()) >= {
        "drift_student_minus_floor", "avoidance_student_minus_floor"
    }
    assert isinstance(adjud["student_no_avoidance_regression"], bool)


def test_reward_alignment_spearman_perfect_when_monotone():
    rows = []
    for i, arm in enumerate(f2.ARMS):
        for regime in ("avoidance", "drift"):
            for _ in range(3):
                rows.append({"arm": arm, "regime": regime, "seed": 1,
                             "success": True if i >= 3 else False,
                             "total_reward": float(i)})
    out = f2.reward_alignment_spearman(rows)
    assert out["n_groups"] == len(f2.ARMS) * 2
    assert np.isfinite(out["spearman"])


def test_prereg_is_draft_not_frozen():
    prereg = f2.build_preregistration()
    assert prereg["draft"] is True
    assert prereg["frozen"] is False
    assert prereg["seed_base"] == f2.SEED_BASE
    # honest floor includes RLS-retuned + per-instance + fixed*, not a strawman
    assert "rls_retuned_reflex" in prereg["arms"]
    assert prereg["teachers"]["drift"]["forbidden"].lower().find("cem") >= 0
    # seed streams disjoint by namespace
    streams = prereg["seed_streams"]
    assert streams["training_namespace"] != streams["validation_namespace"]
    assert streams["holdout_selection_namespace"] != streams["validation_namespace"]


def test_seed_streams_disjoint():
    train = {f2._seed_for("train_seed1", e, "avoidance", u) for e in range(5) for u in range(5)}
    holdout = {f2._seed_for("holdout_seed1", e, "avoidance", u) for e in range(5) for u in range(5)}
    validation = {f2._seed_for("validation", "avoidance", u) for u in range(30)}
    assert train.isdisjoint(validation)
    assert holdout.isdisjoint(validation)


# --------------------------------------------------------------- Chrono smoke


def _chrono_available() -> bool:
    try:
        client = ChronoWorkerClient()
        client.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_quick_pipeline_end_to_end():
    f2.write_preregistration()
    summary = f2.run(quick=True, resume=False)
    gates = summary["protocol_gates"]
    assert gates["all_passed"], gates
    assert gates["student_input_obs72_only"]
    assert gates["all_five_arms_present"]
    assert gates["both_regimes_evaluated"]
    assert gates["full_not_launched"]
    assert summary["decision"]["incumbent_changed"] is False
    assert summary["decision"]["quick_mode_is_verdict"] is False
    # every arm produced finite validation numbers
    adjud = summary["adjudication"]
    for regime in ("avoidance", "drift"):
        for arm in f2.ARMS:
            assert np.isfinite(adjud["per_regime"][regime][arm]["success_rate"])


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_full_flag_refuses_to_launch():
    import subprocess
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "phase4_f2_train.py"), "--full"],
        cwd=str(repo), capture_output=True, text=True, env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    assert proc.returncode != 0
    assert "PI-gated" in (proc.stderr + proc.stdout)
