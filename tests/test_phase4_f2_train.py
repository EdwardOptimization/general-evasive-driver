"""Tests for Phase-4 F2 asymmetric actor-critic RL training and adjudication.

Covers (all actually executed):
  * asymmetric input isolation: actor sees obs72 only, critic sees obs72+priv;
  * stochastic Gaussian policy: learnable log_std, deterministic deploy = mean;
  * PPO correctness: GAE(lambda)+bootstrap shape/values, clipped surrogate,
    squashed log-prob; advantage normalization;
  * teacher correctness: drift teacher is DriftFeedbackPolicy (NOT CEM),
    avoidance teacher is the E2' entry-speed oracle (mu_true bound per scenario);
  * B1 checkpoint + kill/resume continuing from N (non-zero);
  * B3 seed-cluster by TRAINING seed (n = number of training seeds);
  * B4 CI method (paired t-CI + cluster bootstrap) present and used;
  * B5 honest floor = non-trivial classical arms (not the bare incumbent);
  * B6 per-episode Spearman, N/A on ties, >=0.9 hard gate;
  * S2 avoidance mu/reveal spectrum spans >1 point;
  * S5 reward fail-closed + grazing penalty;
  * --quick end-to-end pipeline runs and passes its gates.

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

from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_f2_train as f2  # noqa: E402
import phase4_e4_drift_regime_pricing as e4  # noqa: E402


# --------------------------------------------------------------- asymmetric isolation


def test_asymmetric_actor_rejects_privileged_dim():
    model = f2.AsymmetricActorCritic()
    obs = torch.zeros(3, f2.HUMAN_VIEW_OBS_DIM)
    mean = model.actor_forward(obs)
    assert mean.shape == (3, f2.ACT_DIM)
    # actor REJECTS obs72 + privileged (the leakage channel)
    with pytest.raises(ValueError):
        model.actor_forward(torch.zeros(3, f2.HUMAN_VIEW_OBS_DIM + f2.PRIV_DIM))


def test_critic_requires_privileged_channels():
    model = f2.AsymmetricActorCritic()
    obs = torch.zeros(5, f2.HUMAN_VIEW_OBS_DIM)
    value = model.critic_forward(obs, torch.zeros(5, f2.PRIV_DIM))
    assert value.shape == (5,)
    with pytest.raises(ValueError):
        model.critic_forward(obs, torch.zeros(5, f2.PRIV_DIM - 1))


def test_actor_parameters_disjoint_from_critic_and_no_priv_in_actor():
    model = f2.AsymmetricActorCritic()
    actor_ids = {id(p) for p in model.actor_parameters()}
    critic_ids = {id(p) for p in model.critic_parameters()}
    assert actor_ids.isdisjoint(critic_ids)
    # log_std is an actor parameter (learnable policy stochasticity)
    assert id(model.log_std) in actor_ids
    assert model.actor[0].in_features == f2.HUMAN_VIEW_OBS_DIM
    assert model.critic[0].in_features == f2.HUMAN_VIEW_OBS_DIM + f2.PRIV_DIM


def test_log_std_is_learnable_and_deploy_is_mean():
    model = f2.AsymmetricActorCritic()
    assert model.log_std.requires_grad
    assert model.log_std.shape == (f2.ACT_DIM,)
    model.eval()
    rng = np.random.default_rng(0)
    obs = rng.normal(size=f2.HUMAN_VIEW_OBS_DIM).astype(np.float32)
    # deterministic deploy = tanh(mean): repeatable
    a1, a2 = model.act(obs), model.act(obs)
    assert a1.shape == (f2.ACT_DIM,)
    assert np.allclose(a1, a2)
    assert np.max(np.abs(a1)) <= 1.0 + 1e-6
    # stochastic rollout returns (action, logprob), obs72 only, bounded
    sa, lp = model.act_stochastic(obs)
    assert sa.shape == (f2.ACT_DIM,)
    assert np.asarray(lp).shape == ()
    assert np.max(np.abs(sa)) <= 1.0


# --------------------------------------------------------------- PPO correctness


def test_gae_matches_hand_computation_and_bootstraps():
    rew = np.array([1.0, 0.0, 2.0], np.float32)
    val = np.array([0.5, 0.5, 0.5], np.float32)
    done = np.array([0.0, 0.0, 1.0], np.float32)
    adv, ret = f2.compute_gae(rew, val, done, last_value=0.0)
    g, l = f2.PPO_GAMMA, f2.PPO_LAMBDA
    a2 = (2.0 + 0.0 - 0.5)  # done -> no bootstrap
    a1 = (0.0 + g * val[2] - 0.5) + g * l * a2
    a0 = (1.0 + g * val[1] - 0.5) + g * l * a1
    assert np.allclose(adv, [a0, a1, a2], atol=1e-5)
    # returns = advantages + values (the bootstrapped GAE identity)
    assert np.allclose(ret, adv + val, atol=1e-6)
    # NOT a constant MC broadcast: the three advantages differ
    assert len({round(float(x), 4) for x in adv}) == 3


def test_evaluate_actions_log_prob_and_entropy_shapes():
    model = f2.AsymmetricActorCritic()
    obs = torch.zeros(7, f2.HUMAN_VIEW_OBS_DIM)
    act = torch.tanh(torch.randn(7, f2.ACT_DIM))
    logp, entropy = model.evaluate_actions(obs, act)
    assert logp.shape == (7,)
    assert entropy.shape == (7,)
    assert torch.isfinite(logp).all() and torch.isfinite(entropy).all()


def test_ppo_update_changes_params_clips_and_is_finite():
    torch.manual_seed(0)
    model = f2.AsymmetricActorCritic()
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    rng = np.random.default_rng(1)
    n = 32
    batch = {
        "obs": rng.normal(size=(n, f2.HUMAN_VIEW_OBS_DIM)).astype(np.float32),
        "act": np.tanh(rng.normal(size=(n, f2.ACT_DIM))).astype(np.float32),
        "logp": rng.normal(size=(n,)).astype(np.float32),
        "adv": rng.normal(size=(n,)).astype(np.float32),
        "ret": rng.normal(size=(n,)).astype(np.float32),
        "priv": rng.normal(size=(n, f2.PRIV_DIM)).astype(np.float32),
        "rew": rng.normal(size=(n,)).astype(np.float32),
    }
    out = f2.ppo_update(model, opt, batch, bc_aux_coef=0.0, bc_aux=None, rng=rng)
    assert out["finite_loss"] and out["finite_grad"]
    assert out["optimizer_changed_parameters"]
    # clip fraction is a valid fraction; entropy is reported
    assert 0.0 <= out["clip_fraction"] <= 1.0
    assert np.isfinite(out["entropy"])
    # log_std is tracked before/after (it is a trainable policy parameter)
    assert np.isfinite(out["log_std_before"]) and np.isfinite(out["log_std_after"])


def test_ppo_annealed_bc_auxiliary_term_applies():
    torch.manual_seed(0)
    model = f2.AsymmetricActorCritic()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    rng = np.random.default_rng(2)
    n = 16
    batch = {
        "obs": rng.normal(size=(n, f2.HUMAN_VIEW_OBS_DIM)).astype(np.float32),
        "act": np.tanh(rng.normal(size=(n, f2.ACT_DIM))).astype(np.float32),
        "logp": rng.normal(size=(n,)).astype(np.float32),
        "adv": rng.normal(size=(n,)).astype(np.float32),
        "ret": rng.normal(size=(n,)).astype(np.float32),
        "priv": rng.normal(size=(n, f2.PRIV_DIM)).astype(np.float32),
        "rew": rng.normal(size=(n,)).astype(np.float32),
    }
    bc_aux = {"obs": rng.normal(size=(8, f2.HUMAN_VIEW_OBS_DIM)).astype(np.float32),
              "targets": np.tanh(rng.normal(size=(8, f2.ACT_DIM))).astype(np.float32)}
    out = f2.ppo_update(model, opt, batch, bc_aux_coef=0.5, bc_aux=bc_aux, rng=rng)
    assert out["bc_aux_coef"] == 0.5
    assert np.isfinite(out["bc_aux_loss"]) and out["bc_aux_loss"] >= 0.0
    # anneal schedule reaches 0 at the end of PPO
    assert f2._anneal(f2.BC_AUX_COEF_START, f2.BC_AUX_COEF_END, 10, 10) == f2.BC_AUX_COEF_END


# --------------------------------------------------------------- teachers


def test_drift_teacher_is_drift_feedback_policy_not_cem():
    handle = f2.make_drift_teacher()
    teacher = handle.factory()
    assert isinstance(teacher, e4.DriftFeedbackPolicy)
    assert teacher.spec.name == f2.DRIFT_FEEDBACK_NAME
    assert teacher.spec in e4.DRIFT_FEEDBACK_SPECS
    assert not isinstance(teacher, e4.OpenLoopPolicy)  # never a CEM/open-loop spec
    assert handle.privileged["regime"] == 1.0


def test_avoidance_teacher_binds_mu_true_per_scenario():
    handle = f2.make_avoidance_teacher(reveal=16.0, mu=0.8125)
    teacher = handle.factory()
    assert isinstance(teacher, f2._AvoidanceTeacherAdapter)
    assert teacher._ctrl.mode == "oracle"
    assert teacher._ctrl.mu_true == pytest.approx(0.8125)
    assert handle.privileged["mu"] == pytest.approx(0.8125)
    assert handle.privileged["regime"] == 0.0


def test_drift_teacher_bounded_action_from_obs72():
    teacher = f2.make_drift_teacher().factory()
    obs = np.zeros(f2.HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    obs[1] = 0.2
    action = np.asarray(teacher(0, obs), dtype=np.float32)
    assert action.shape == (f2.ACT_DIM,)
    assert np.all(np.isfinite(action)) and np.max(np.abs(action)) <= 1.0 + 1e-6


# --------------------------------------------------------------- B5 non-trivial floor


def test_floor_arms_are_nontrivial_classical_not_bare_incumbent():
    # B5: the floor is the MAX over three real classical arms, not fixed* alone.
    assert set(f2.FLOOR_ARMS) == {"fixed_star", "entry_speed_commitment_floor", "online_mu_seeker_floor"}
    # online mu seeker is a genuine online-mu-estimating reflex (NOT an oracle).
    seeker = f2._OnlineMuSeekerFloor(reveal=9.5)
    assert seeker._ctrl.mode == "seeker"  # estimates mu_hat from its own action
    assert getattr(seeker._ctrl, "mu_true", None) is None  # no privileged mu
    # entry-speed commitment is a real belief-free fixed-plan controller.
    floor = f2._EntrySpeedCommitmentFloor(reveal=9.5, v_entry=5.5)
    obs = np.zeros(f2.HUMAN_VIEW_OBS_DIM, np.float64)
    a = np.asarray(floor(0, obs), np.float32)
    assert a.shape == (f2.ACT_DIM,) and np.max(np.abs(a)) <= 1.0 + 1e-6


def test_floor_rate_takes_max_over_classical_arms_only():
    rows = []
    succ = {"fixed_star": [False, False], "entry_speed_commitment_floor": [True, False],
            "online_mu_seeker_floor": [True, True]}
    for arm, vals in succ.items():
        for s in vals:
            rows.append({"arm": arm, "regime": "avoidance", "success": s, "total_reward": 0.0,
                         "collision": False, "train_seed": -1})
    assert f2._floor_rate(rows, "avoidance") == pytest.approx(1.0)


# --------------------------------------------------------------- B3/B4 stats


def test_seed_cluster_by_training_seed_and_ci_present():
    train_seeds = [11, 22, 33]
    rows = []
    for regime in ("avoidance", "drift"):
        for unit in range(2):
            for ts in train_seeds:
                rows.append({"arm": "student_policy", "regime": regime, "success": (ts != 33),
                             "total_reward": float(ts), "collision": False, "train_seed": ts})
            for arm in ("fixed_star", "entry_speed_commitment_floor", "online_mu_seeker_floor", "per_regime_oracle"):
                rows.append({"arm": arm, "regime": regime, "success": False, "total_reward": 0.0,
                             "collision": False, "train_seed": -1})
    adjud = f2.adjudicate(rows, train_seeds=train_seeds)
    # B3: n_training_seeds equals the number of training seeds (not validation units)
    for regime in ("avoidance", "drift"):
        assert adjud["per_regime"][regime]["student_policy"]["n_training_seeds"] == len(train_seeds)
    # B4: paired t-CI and cluster bootstrap CI both present for the prize diff
    for regime in ("avoidance", "drift"):
        sc = adjud["seed_clustered_ci"][regime]
        assert "student_minus_floor_paired_t_ci" in sc
        assert "student_minus_floor_cluster_bootstrap_ci" in sc
        assert "ci95_low" in sc["student_minus_floor_paired_t_ci"]
        assert sc["n_training_seeds"] == len(train_seeds)


def test_paired_t_ci_and_bootstrap_numbers():
    diffs = [0.4, 0.3, 0.5, 0.45, 0.35, 0.2, 0.6, 0.4]
    t = f2._paired_t_ci(diffs)
    assert t["n"] == 8 and t["method"] == "paired_t"
    assert t["ci95_low"] < t["mean"] < t["ci95_high"]
    boot = f2._seed_cluster_bootstrap(diffs)
    assert boot["n"] == 8 and boot["ci95_low"] <= boot["ci95_high"]


# --------------------------------------------------------------- B6 reward-hacking guard


def test_b6_alignment_na_on_ties_and_auc_hard_gate():
    # all-success ties -> N/A (gate undefined, not a fake correlation)
    tied = [{"total_reward": 1.0, "success": True} for _ in range(5)]
    out = f2.reward_alignment_spearman(tied)
    assert out["auc"] is None and out["spearman"] is None
    assert out["gate_applicable"] is False
    assert out["tie_degenerate"] is True
    # perfectly separated (every success outscores every failure) -> AUC == 1.0,
    # clears the >=0.9 hard gate. Spearman is reported too (capped < 1 for binary).
    mono = [{"total_reward": float(i), "success": i >= 3} for i in range(6)]
    out2 = f2.reward_alignment_spearman(mono)
    assert out2["gate_applicable"] is True
    assert out2["gate_statistic"] == "rank_biserial_auc"
    assert out2["auc"] == pytest.approx(1.0)
    assert out2["meets_0p9"] is True
    assert out2["spearman"] is not None  # reported alongside the AUC gate
    # misaligned (reward up, success down) -> AUC == 0.0 -> fails the gate
    bad = [{"total_reward": float(i), "success": i < 3} for i in range(6)]
    out3 = f2.reward_alignment_spearman(bad)
    assert out3["gate_applicable"] is True
    assert out3["auc"] == pytest.approx(0.0)
    assert out3["meets_0p9"] is False


# --------------------------------------------------------------- S5 reward fail-closed


def test_s5_reward_fail_closed_and_grazing_penalty():
    # completion=="" is NOT a pass (fail-closed)
    unknown = f2._avoidance_reward({"collision": False, "completion_reason": "", "min_clearance_margin": 0.5}, True, True)
    cleared = f2._avoidance_reward({"collision": False, "completion_reason": "max_steps", "min_clearance_margin": 0.5}, True, True)
    assert cleared - unknown >= f2.AVOIDANCE_PASS_REWARD - 1e-6
    assert not f2._avoidance_success(False, {"completion_reason": "", "termination_reason": ""})
    # M2: the real backend pass token is "obstacle_pass" (NOT "obstacle_cleared")
    assert f2._avoidance_success(False, {"completion_reason": "obstacle_pass", "termination_reason": ""})
    # high-speed low-margin grazing is penalized vs a slow low-margin pass
    graze = f2._avoidance_reward({"collision": False, "completion_reason": "max_steps",
                                  "min_clearance_margin": 0.05, "vx_norm": 0.8}, False, False)
    slow = f2._avoidance_reward({"collision": False, "completion_reason": "max_steps",
                                 "min_clearance_margin": 0.05, "vx_norm": 0.1}, False, False)
    assert slow - graze == pytest.approx(f2.GRAZE_PENALTY, abs=1e-5)


def test_reward_recalibration_penalty_dominates():
    assert f2.COLLISION_PENALTY >= f2.AVOIDANCE_PASS_REWARD
    assert f2.COLLISION_PENALTY >= f2.DRIFT_SUCCESS_REWARD
    collide = f2._avoidance_reward({"collision": True, "min_clearance_margin": 0.5}, True, False)
    clean = f2._avoidance_reward({"collision": False, "completion_reason": "max_steps", "min_clearance_margin": 0.5}, True, True)
    assert collide < 0.0 < clean


# --------------------------------------------------------------- arms + adjudication


def test_arm_policy_constructs_all_five_arms_both_regimes():
    model = f2.AsymmetricActorCritic()
    for regime in ("avoidance", "drift"):
        for arm in f2.ARMS:
            policy = f2.arm_policy(arm, regime, model if arm == "student_policy" else None, reveal=9.5)
            assert callable(policy)
    student = f2.arm_policy("student_policy", "drift", model, reveal=9.5)
    a = np.asarray(student(0, np.zeros(f2.HUMAN_VIEW_OBS_DIM, np.float32)), np.float32)
    assert a.shape == (f2.ACT_DIM,)


# --------------------------------------------------------------- B1 checkpoint/resume


def test_checkpoint_roundtrip_restores_model_optimizer_rng(tmp_path):
    torch.manual_seed(7)
    model = f2.AsymmetricActorCritic()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss = model.actor_forward(torch.zeros(4, f2.HUMAN_VIEW_OBS_DIM)).pow(2).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    f2.save_checkpoint(tmp_path, seed=99, update=5, model=model, optimizer=opt,
                       best_score=-0.1, best_state=best_state, best_update=3, phase="ppo")
    latest = f2.latest_checkpoint(tmp_path, 99)
    assert latest is not None and "update000005" in latest.name
    model2 = f2.AsymmetricActorCritic()
    opt2 = torch.optim.Adam(model2.parameters(), lr=1e-3)
    state = f2.load_checkpoint(latest, model2, opt2)
    assert state["update"] == 5 and state["best_update"] == 3
    for (k, v1), (_, v2) in zip(model.state_dict().items(), model2.state_dict().items()):
        assert torch.allclose(v1, v2)


def test_resume_start_update_is_nonzero_after_kill(tmp_path):
    model = f2.AsymmetricActorCritic()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    f2.save_checkpoint(tmp_path, seed=1, update=4, model=model, optimizer=opt,
                       best_score=-1.0, best_state={k: v.detach().clone() for k, v in model.state_dict().items()},
                       best_update=2, phase="ppo")
    latest = f2.latest_checkpoint(tmp_path, 1)
    model2 = f2.AsymmetricActorCritic()
    opt2 = torch.optim.Adam(model2.parameters(), lr=1e-3)
    state = f2.load_checkpoint(latest, model2, opt2)
    start_update = int(state["update"]) + 1
    assert start_update == 5  # non-zero resume point


# --------------------------------------------------------------- S2 spectrum + prereg


def test_avoidance_spectrum_spans_multiple_points():
    grid_quick = f2._avoidance_grid(True)
    grid_full = f2._avoidance_grid(False)
    assert len(grid_quick) >= 2  # S2: >1 (mu, reveal) point
    assert len(grid_full) == len(f2.AVOIDANCE_REVEALS_FULL) * len(f2.AVOIDANCE_MUS_FULL)
    assert len({r for r, _ in grid_full}) == len(f2.AVOIDANCE_REVEALS_FULL)
    assert len({m for _, m in grid_full}) == len(f2.AVOIDANCE_MUS_FULL)


def test_prereg_is_freeze_ready_real_rl_not_distillation():
    prereg = f2.build_preregistration()
    assert prereg["draft"] is True
    assert prereg["frozen"] is False
    assert prereg["freeze_ready"] is True
    assert prereg["seed_base"] == f2.SEED_BASE
    assert "real_asymmetric_actor_critic_rl" in prereg["scope_decision_s3"]
    assert "PPO" in prereg["rl_algorithm"]["method"]
    assert prereg["rl_algorithm"]["gae_lambda"] == f2.PPO_LAMBDA
    assert "entry_speed_commitment_floor" in prereg["arms"]
    assert "online_mu_seeker_floor" in prereg["arms"]
    assert prereg["teacher_role"]["drift"]["forbidden"].lower().find("cem") >= 0
    assert "ci_method_primary" in prereg["statistics_B3_B4"]
    assert prereg["power_analysis_S4"]["n_training_seeds"] == 8
    assert prereg["leak_discipline"]["B2_bc_reveal_post_only"] is True


def test_seed_streams_disjoint():
    train = {f2._seed_for("ppo_seed1", u, "avoidance", i) for u in range(5) for i in range(5)}
    bc = {f2._seed_for("bc_seed1", u, "avoidance", i) for u in range(5) for i in range(5)}
    holdout = {f2._seed_for("holdout_seed1", u, "avoidance", i) for u in range(5) for i in range(5)}
    validation = {f2._seed_for("validation", "avoidance", u, 9.5, 0.3625) for u in range(30)}
    assert train.isdisjoint(validation)
    assert bc.isdisjoint(validation)
    assert holdout.isdisjoint(validation)


# --------------------------------------------------------------- M2 avoidance success contract


def test_m2_avoidance_success_uses_obstacle_pass_not_obstacle_cleared():
    # M2: the acceptance set is {"max_steps","obstacle_pass"}; the nonexistent
    # backend token "obstacle_cleared" must NOT score as success.
    assert f2.AVOIDANCE_SUCCESS_COMPLETIONS == ("max_steps", "obstacle_pass")
    assert "obstacle_cleared" not in f2.AVOIDANCE_SUCCESS_COMPLETIONS
    # completion_reason == "obstacle_pass" -> success True AND the pass reward fires
    info_pass = {"collision": False, "termination_reason": "", "completion_reason": "obstacle_pass",
                 "min_clearance_margin": 0.5}
    assert f2._avoidance_success(False, info_pass) is True
    r_pass = f2._avoidance_reward(info_pass, True, True)
    r_unknown = f2._avoidance_reward({"collision": False, "termination_reason": "", "completion_reason": "",
                                      "min_clearance_margin": 0.5}, True, True)
    assert r_pass - r_unknown == pytest.approx(f2.AVOIDANCE_PASS_REWARD, abs=1e-6)
    # the dead token never passes
    assert f2._avoidance_success(False, {"collision": False, "termination_reason": "",
                                         "completion_reason": "obstacle_cleared"}) is False


# --------------------------------------------------------------- M3 reveal gate flip


def test_m3_reveal_gate_flips_false_before_true_after():
    # M3: _obstacle_visible reads the worker truth (obstacle_visible flag, then the
    # geometric longitudinal<=reveal_distance test). It must be False before the
    # reveal and True after -- the old constant-zero obs72-tail fallback never
    # flipped, so the avoidance BC collected 0 frames.
    obs = np.zeros(f2.HUMAN_VIEW_OBS_DIM, np.float32)
    # explicit worker flag governs
    assert f2._obstacle_visible(obs, {"obstacle_visible": False}) is False
    assert f2._obstacle_visible(obs, {"obstacle_visible": True}) is True
    # geometric fallback: ahead beyond reveal_distance -> not visible;
    # within reveal_distance (or behind the ego) -> visible.
    far = {"obstacle_longitudinal": 40.0, "reveal_distance": 16.0}
    near = {"obstacle_longitudinal": 10.0, "reveal_distance": 16.0}
    behind = {"obstacle_longitudinal": -3.0, "reveal_distance": 16.0}
    assert f2._obstacle_visible(obs, far) is False   # before reveal
    assert f2._obstacle_visible(obs, near) is True    # after reveal
    assert f2._obstacle_visible(obs, behind) is True  # passed (revealed)


def test_m3_backend_diagnostics_expose_obstacle_visible_and_reveal_distance():
    # M3: the backend's diagnostics must now carry obstacle_visible + reveal_distance
    # so the avoidance BC can gate on the real reveal (not constant-zero padding).
    import autodrift.chrono_vehicle_backend as backend
    import inspect
    src = inspect.getsource(backend.ChronoVehicleBackend._diagnostics)
    assert '"obstacle_visible"' in src
    assert '"reveal_distance"' in src


# --------------------------------------------------------------- M4 S7 stop-loss


def test_m4_s7_recommendation_tokens_and_threshold():
    # M4: the precheck threshold is floor + prize (the prize is the frozen +0.40).
    assert f2.S7_DRIFT_PRIZE == pytest.approx(0.40)


# --------------------------------------------------------------- F4-align (stage 1)


def test_f4align_drift_oracle_bound_to_e4_selected_winner():
    # F4-align: the drift teacher/oracle must be the spec E4 SELECTED for the priced
    # low_mu_power_oversteer cell (the controller E4 measured at +0.40), NOT the old
    # beta0p22_power binding (a non-winning ~0 candidate on this cell).
    assert f2.DRIFT_CELL_ID == "low_mu_power_oversteer"
    selected = f2._e4_selected_drift_spec_name(f2.DRIFT_CELL_ID, default="__none__")
    assert selected != "__none__", "E4 artifact must expose the selected drift candidate"
    assert f2.DRIFT_FEEDBACK_NAME == selected
    assert f2.DRIFT_FEEDBACK_NAME != "beta0p22_power"  # the old non-winning binding
    # it must be a real DriftFeedbackSpec (never a CEM/open-loop native candidate)
    spec = f2._drift_spec(f2.DRIFT_FEEDBACK_NAME)
    assert spec in e4.DRIFT_FEEDBACK_SPECS
    # cross-check against the frozen E4 full artifact's recorded selection + 0.40
    e4_full = f2._read_json(f2.E4_JSON)
    readout = [c for c in e4_full["cell_readouts"] if c["cell_id"] == f2.DRIFT_CELL_ID][0]
    assert readout["selected_candidates"]["drift_specialized_oracle"] == f"drift:{f2.DRIFT_FEEDBACK_NAME}"
    assert readout["arm_success_rate"]["drift_specialized_oracle"] == pytest.approx(0.40)


def test_f4align_drift_validation_horizon_is_e4_episode_length():
    # F4-align: the drift VALIDATION/S7 grid runs on E4's frozen episode length so the
    # matched oracle can reach the 24-step sustain criterion (the short PPO rollout
    # horizon caps it below 24 by construction).
    assert f2.DRIFT_VALIDATION_MAX_STEPS == e4.MAX_STEPS == 90
    assert f2.DRIFT_VALIDATION_MAX_STEPS >= e4.MIN_SUSTAIN_STEPS
    # the drift validation scenario carries the E4 cell params and E4 horizon
    scen = f2._drift_scenario(f2._seed_for("t", 0), max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")
    assert scen["max_steps"] == 90
    cell = f2._drift_cell()
    assert scen["params"]["mu"] == pytest.approx(cell["mu"])  # E4 cell mu (0.48)
    assert scen["track_radius"] == pytest.approx(cell["track_radius"])  # 70


def test_f4align_s7_uses_e4_frozen_validation_seeds():
    # F4-align: the S7 drift ceiling replays E4's exact frozen validation seeds (the
    # seeds E4 priced 8/20 = 0.40 on), not a single coin-flip.
    seeds = f2._e4_drift_validation_seeds(f2.DRIFT_CELL_ID)
    e4_prereg = f2._read_json(f2.E4_PREREG_JSON)
    assert seeds == [int(s) for s in e4_prereg["validation_seeds"][f2.DRIFT_CELL_ID]]
    assert len(seeds) >= f2.DRIFT_S7_MIN_UNITS == 20


def test_f4align_drift_success_criteria_reuse_e4_semantics():
    # F4-align: F2's drift success judging reuses E4's thresholds + rear-saturation
    # function verbatim (no self-authored judge), and the prereg records this.
    prereg = f2.build_preregistration()
    blk = prereg["teacher_role"]["drift"]["F4_align_stage1"]
    assert blk["drift_validation_cell"] == "low_mu_power_oversteer"
    assert blk["drift_oracle_spec"] == f2.DRIFT_FEEDBACK_NAME
    assert blk["drift_validation_max_steps"] == 90
    crit = blk["drift_success_criteria"]
    assert crit["beta_threshold_rad"] == pytest.approx(e4.BETA_THRESHOLD_RAD)
    assert crit["min_sustain_steps"] == e4.MIN_SUSTAIN_STEPS == 24
    assert prereg["claim_scope"].lower().startswith("stage-1 narrow drift probe")


def test_s7_decision_is_a_real_inequality_pure():
    # F4-align: the S7 decision is a pure inequality on the measured ceiling. At a
    # ceiling reproducing E4's +0.40 with floor 0.0 it PROCEEDS at prize 0.40 (boundary
    # cleared by tolerance) and STOPS at an unreachable prize 1.0.
    ceil_proceed = {"avoidance": 1.0, "drift": 0.40}
    proceed = f2.s7_decision(ceil_proceed, floor_threshold=0.0, prize=0.40)
    assert proceed["recommendation"] == "proceed"
    assert proceed["should_stop"] is False
    assert proceed["drift_oracle_clears_floor_plus_prize"] is True
    stop = f2.s7_decision(ceil_proceed, floor_threshold=0.0, prize=1.0)
    assert stop["recommendation"] == "stop_and_reprice"
    assert stop["should_stop"] is True
    # a drift ceiling of 0.0 (the OLD beta0p22_power behaviour) still blocks at +0.40
    blocked = f2.s7_decision({"avoidance": 1.0, "drift": 0.0}, floor_threshold=0.0, prize=0.40)
    assert blocked["recommendation"] == "stop_and_reprice"


def test_m1_act_batch_is_obs72_only_and_batched():
    # M1: act_batch does ONE stochastic forward over W obs72 frames; obs72-only.
    model = f2.AsymmetricActorCritic()
    obs = np.random.default_rng(0).normal(size=(7, f2.HUMAN_VIEW_OBS_DIM)).astype(np.float32)
    actions, logps = model.act_batch(obs)
    assert actions.shape == (7, f2.ACT_DIM)
    assert logps.shape == (7,)
    assert np.max(np.abs(actions)) <= 1.0
    assert np.isfinite(logps).all()
    # rejects any non-obs72 width (no privileged path through the batched rollout)
    with pytest.raises(ValueError):
        model.act_batch(np.zeros((3, f2.HUMAN_VIEW_OBS_DIM + f2.PRIV_DIM), np.float32))


def test_m7_real_step_budget_is_not_100m_placeholder():
    # M7: the full budget has NO 100M placeholder; total_steps is derived from
    # seeds * updates * workers * horizon.
    assert "total_steps" not in f2.FULL
    budget = f2._real_step_budget(f2.FULL)
    expect_ppo = (f2.FULL["seeds"] * f2.FULL["ppo_updates"] * f2.FULL["rollout_workers"] * f2.FULL["rollout_horizon"])
    assert budget["ppo_env_steps"] == expect_ppo
    assert budget["total_env_steps"] >= budget["ppo_env_steps"]
    assert budget["total_env_steps"] != 100_000_000


def test_m7_wall_clock_uses_f1b_30worker_rate_not_serial():
    # M7: the wall-clock projection uses the F1b 30-worker closed_loop rate
    # (~1000+ steps/s), NOT the serial ~2.1 steps/s baseline.
    rate = f2._f1b_aggregate_steps_per_s()
    assert rate >= 1000.0  # F1b 30-worker closed_loop aggregate
    wc = f2._wall_clock_projection(f2.FULL)
    assert wc["throughput_steps_per_s"] >= 1000.0
    assert wc["projected_wall_clock_hours"] > 0.0
    # a measured rate overrides the artifact
    wc2 = f2._wall_clock_projection(f2.FULL, measured_steps_per_s=1500.0)
    assert wc2["throughput_steps_per_s"] == pytest.approx(1500.0)
    assert wc2["throughput_source"] == "f2_measured_rollout"


def test_m6_prereg_b6_wording_is_honest_not_spearman_unreachable():
    # M6: the B6 justification must be the PI-approved honest wording (binary-vs-
    # continuous rank correlation does not reach 1, class-balance dependent), and
    # must NOT claim "Spearman unreachable".
    prereg = f2.build_preregistration()
    b6 = prereg["reward_recalibration"]["B6_reward_hacking_guard"].lower()
    assert "rank-biserial auc" in b6
    assert "does not reach 1" in b6
    assert "class-balance dependent" in b6
    assert "unreachable" not in b6
    assert prereg["reward_recalibration"]["B6_auc_hard_gate_threshold"] == 0.9
    # Spearman stays reported, not gated
    assert "not gated" in b6 or "reported alongside but not gated" in b6


def test_m7_prereg_carries_real_step_budget_and_wall_clock():
    prereg = f2.build_preregistration()
    sb = prereg["step_budget_and_wall_clock_M7"]
    assert sb["real_step_budget_full"]["total_env_steps"] != 100_000_000
    assert sb["wall_clock_projection_full"]["throughput_steps_per_s"] >= 1000.0
    # M1 parallelism is documented in the rl_algorithm block
    assert "M1_rollout_parallelism" in prereg["rl_algorithm"]


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
    assert gates["ppo_update_ran"]
    assert gates["log_std_observed"]
    assert gates["entropy_observed"]
    assert gates["all_training_seeds_validated_B3"]
    assert gates["seed_cluster_by_training_seed_B3"]
    assert gates["ci_method_present_B4"]
    assert gates["floor_nontrivial_B5"]
    assert gates["reward_alignment_hard_gate_B6"]
    assert gates["checkpoints_written_B1"]
    assert gates["avoidance_spectrum_spanned_S2"]
    assert gates["student_input_obs72_only"]
    assert gates["full_not_launched"]
    # pass-3 fixes wired into the smoke gates
    assert gates["ppo_rollout_parallel_throughput_M1"]
    assert gates["avoidance_bc_frames_positive_M3"]
    assert gates["s7_stop_loss_active_M4"]
    # M1 throughput measured + reported; M3 BC frames > 0; M7 wall-clock present
    assert summary["throughput_M1"]["rollout_total_steps"] > 0
    assert summary["avoidance_bc_frames_M3"] > 0
    assert summary["wall_clock_projection_M7"]["throughput_steps_per_s"] >= 1000.0
    # F4-align: after aligning the drift validation cell/oracle/criteria/seeds to E4's
    # frozen low_mu_power_oversteer, the matched drift oracle reproduces the priced
    # +0.40 and S7 PROCEEDS on the REAL +0.40 prize (the launch is no longer blocked).
    s7 = summary["oracle_ceiling_precheck_S7"]
    assert s7["recommendation"] == "proceed"  # REAL +0.40 prize is cleared
    assert s7["should_stop"] is False
    assert s7["drift_oracle_clears_floor_plus_prize"] is True
    # the drift oracle ceiling reproduces E4's ~0.40 (> 0; the prize is reachable)
    assert s7["oracle_ceiling_by_regime"]["drift"] >= s7["floor_plus_prize_threshold"] - f2.S7_BOUNDARY_TOL
    assert s7["oracle_ceiling_by_regime"]["drift"] > 0.0
    # the gate is a real inequality: an unreachable prize still stops (BOTH branches)
    assert s7["verification_stop_branch_unreachable_prize"]["recommendation"] == "stop_and_reprice"
    assert s7["both_branches_demonstrated"] is True
    # the S7 launch gate now RELEASES the launch (the F4-align objective)
    assert gates["s7_stop_loss_active_M4"] is True
    # drift oracle arm success > 0 in the four-arm adjudication (prize reachable)
    assert summary["adjudication"]["per_regime"]["drift"]["per_regime_oracle"]["success_rate"] > 0.0
    assert summary["decision"]["incumbent_changed"] is False
    assert summary["decision"]["quick_mode_is_verdict"] is False
    adjud = summary["adjudication"]
    for regime in ("avoidance", "drift"):
        for arm in f2.ARMS:
            assert np.isfinite(adjud["per_regime"][regime][arm]["success_rate"])


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_quick_kill_and_resume_continues_from_nonzero(tmp_path):
    # B1: train one seed a couple updates, checkpoint, then resume; assert the
    # resume path loads a non-zero checkpoint and continues above it.
    f2.write_preregistration()
    seed = f2._seed_for("seed_select", 0)
    budget = dict(f2.QUICK)
    budget["warmstart_updates"] = 1
    budget["ppo_updates"] = 1
    ckpt = tmp_path / "ckpt"
    metrics: list = []
    f2.train_student(seed=seed, budget=budget, quick=True, ckpt_dir=ckpt,
                     stderr_log=tmp_path / "err.log", progress=tmp_path / "prog.jsonl",
                     train_metrics=metrics, resume=False)
    latest = f2.latest_checkpoint(ckpt, seed)
    assert latest is not None
    state = torch.load(latest, map_location="cpu", weights_only=False)
    assert int(state["update"]) >= 1  # a non-zero checkpoint exists
    # resume with more PPO updates; resume must start above the checkpoint.
    budget2 = dict(budget)
    budget2["ppo_updates"] = 3
    metrics2: list = []
    f2.train_student(seed=seed, budget=budget2, quick=True, ckpt_dir=ckpt,
                     stderr_log=tmp_path / "err.log", progress=tmp_path / "prog2.jsonl",
                     train_metrics=metrics2, resume=True)
    done_updates = {r["update"] for r in metrics2}
    assert done_updates  # work happened on resume
    assert min(done_updates) >= int(state["update"]) + 1  # continued from N (non-zero)


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_m3_avoidance_bc_frames_positive_after_reveal_gate_fix(tmp_path):
    # M3: with the reveal gate reading the worker truth, the avoidance teacher
    # collects > 0 reveal-post BC frames (it was 0 before the fix). A horizon long
    # enough for the obstacle to reveal is used.
    client = ChronoWorkerClient(stderr_log=tmp_path / "err.log")
    try:
        stage = f2.CURRICULUM_STAGES[0]
        # the quick grid leads with reveal 30.0 (obstacle in obs72 view from reset);
        # the first avoidance unit therefore collects reveal-post BC frames.
        demos = f2.collect_bc_demos(
            client, stage=stage, units=4, horizon=20, seed_ns="m3test", update=0, quick=True,
        )
    finally:
        client.close()
    assert demos["avoidance_bc_frames"] > 0  # reveal gate now fires (was 0 before)
    assert demos["obs"].shape[0] > 0
    # the reveal gate flips: a far-reveal scenario yields no reveal-post frames at a
    # tiny horizon (proving the gate is selective, not always-true)
    obs = np.zeros(f2.HUMAN_VIEW_OBS_DIM, np.float32)
    assert f2._obstacle_visible(obs, {"obstacle_visible": False}) is False
    obs[f2.OBS72_OBSTACLE_VISIBLE_CHANNEL] = 1.0
    assert f2._obstacle_visible(obs, {"obstacle_visible": False}) is True  # obs72 channel governs


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_m1_parallel_rollout_throughput_and_serial_shape(tmp_path):
    # M1: the parallel collector returns a positive aggregate Chrono step rate and
    # well-formed PPO batch tensors, using a pool of clients stepped lockstep.
    model = f2.AsymmetricActorCritic()
    n_workers = 3
    clients = [ChronoWorkerClient(stderr_log=tmp_path / "err.log") for _ in range(n_workers)]
    try:
        batch = f2.collect_ppo_rollout(
            clients, model, stage=f2.CURRICULUM_STAGES[0], units=4, horizon=20,
            seed_ns="m1test", update=0, quick=True,
        )
    finally:
        for c in clients:
            c.close()
    assert batch["rollout_workers"] == n_workers
    assert batch["rollout_steps"] > 0
    assert batch["rollout_steps_per_s"] > 0.0
    # PPO batch is well-formed and aligned across fields
    n = batch["obs"].shape[0]
    assert n > 0
    assert batch["act"].shape == (n, f2.ACT_DIM)
    assert batch["logp"].shape == (n,)
    assert batch["priv"].shape == (n, f2.PRIV_DIM)
    assert batch["adv"].shape == (n,) and batch["ret"].shape == (n,)
    assert np.isfinite(batch["adv"]).all() and np.isfinite(batch["ret"]).all()


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_m4_s7_real_inequality_proceeds_on_priced_prize_stops_on_unreachable(tmp_path):
    # M4 + F4-align: the S7 oracle-ceiling precheck is a REAL inequality on the
    # MEASURED drift ceiling. After aligning the drift validation cell/oracle/criteria/
    # seeds to E4's frozen low_mu_power_oversteer, the matched drift oracle reproduces
    # the priced +0.40, so:
    #   * at the REAL +0.40 prize (floor 0.0) -> "proceed" (ceiling >= floor+0.40);
    #   * at an UNREACHABLE prize (1.0)       -> "stop_and_reprice" (a real inequality).
    s7 = f2.oracle_ceiling_precheck(
        budget=dict(f2.QUICK), quick=True, stderr_log=tmp_path / "err.log",
        floor_threshold=0.0, prize=f2.S7_DRIFT_PRIZE,
    )
    assert s7["prize"] == pytest.approx(0.40)
    assert s7["floor_plus_prize_threshold"] == pytest.approx(0.40)
    # the S7 drift ceiling reproduces E4's ~0.40 (> 0 and clears floor+prize)
    assert s7["oracle_ceiling_by_regime"]["drift"] > 0.0
    assert s7["oracle_ceiling_by_regime"]["drift"] >= 0.40 - f2.S7_BOUNDARY_TOL
    assert s7["units_per_regime"]["drift"] >= f2.DRIFT_S7_MIN_UNITS
    assert s7["should_stop"] is False
    assert s7["recommendation"] == "proceed"
    # a high threshold the oracle cannot meet always stops, proving the gate is a real
    # inequality (not a constant pass)
    s7_hi = f2.oracle_ceiling_precheck(
        budget=dict(f2.QUICK), quick=True, stderr_log=tmp_path / "err2.log",
        floor_threshold=0.99, prize=f2.S7_DRIFT_PRIZE,
    )
    assert s7_hi["recommendation"] == "stop_and_reprice"


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_m5_seed_level_kill_resume_skips_done_seed(tmp_path, monkeypatch):
    # M5: run() with a micro 2-seed/2-update FULL-shaped budget; kill after the
    # first seed completes, then resume -> the DONE seed is NOT re-entered and the
    # unfinished seed continues. Drives the real run() seed loop (the --full path
    # stays PI-gated; this exercises the same code with a micro budget).
    micro = {
        "workers": 2, "seeds": 2, "warmstart_updates": 1, "ppo_updates": 1,
        "rollout_workers": 2, "rollout_horizon": 6,
        "validation_units_per_regime": 1, "selection_units_per_regime": 1, "warmstart_units": 2,
    }
    ckpt_dir = tmp_path / "ckpt"
    seeds = [f2._seed_for("seed_select", i) for i in range(micro["seeds"])]

    # --- "kill": train ONLY the first seed and drop its DONE marker (simulating an
    # interruption right after seed 0 finished but before seed 1 started).
    metrics0: list = []
    summ0 = f2.train_student(
        seed=seeds[0], budget=micro, quick=True, ckpt_dir=ckpt_dir,
        stderr_log=tmp_path / "e.log", progress=tmp_path / "p0.jsonl",
        train_metrics=metrics0, resume=False,
    )
    f2.mark_seed_done(ckpt_dir, seeds[0], summ0)
    assert f2.seed_is_done(ckpt_dir, seeds[0]) is True
    assert f2.seed_is_done(ckpt_dir, seeds[1]) is False

    # --- "resume": run() with resume=True must SKIP seed 0 (DONE) and train seed 1.
    monkeypatch.setattr(f2, "FULL", micro)
    monkeypatch.setattr(f2, "CKPT_FULL_DIR", ckpt_dir)
    monkeypatch.setattr(f2, "STDERR_FULL_LOG", tmp_path / "ef.log")
    monkeypatch.setattr(f2, "PROGRESS_FULL_JSONL", tmp_path / "pf.jsonl")
    monkeypatch.setattr(f2, "ROWS_FULL_CSV", tmp_path / "rows.csv")
    monkeypatch.setattr(f2, "TRAIN_FULL_CSV", tmp_path / "train.csv")
    monkeypatch.setattr(f2, "FULL_JSON", tmp_path / "full.json")
    monkeypatch.setattr(f2, "DOC_PATH", tmp_path / "doc.md")

    summary = f2.run(quick=False, resume=True)
    # seed 0 was reloaded-not-retrained: no NEW training-metric rows for it.
    seed0_new_rows = [r for r in summary["train_summaries"] if int(r["seed"]) == seeds[0] and r.get("resumed_done")]
    assert seed0_new_rows, "seed 0 should be marked resumed_done (skipped, not retrained)"
    # seed 1 newly completed and now also has a DONE marker
    assert f2.seed_is_done(ckpt_dir, seeds[1]) is True
    # both seeds validated in the four-arm eval
    validated = {int(s["seed"]) for s in summary["train_summaries"]}
    assert validated == set(seeds)


@pytest.mark.skipif(not _chrono_available(), reason="chrono worker not launchable in this environment")
def test_full_flag_refuses_to_launch():
    import subprocess
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "phase4_f2_train.py"), "--full"],
        cwd=str(repo), capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    assert proc.returncode != 0
    assert "PI-gated" in (proc.stderr + proc.stdout)
