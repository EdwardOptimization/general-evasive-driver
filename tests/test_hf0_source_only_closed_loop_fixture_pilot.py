import csv

import numpy as np
import torch

from autodrift.hf0_source_only_closed_loop_fixture_pilot import (
    admit_actor_checkpoint,
    run_preflight,
    run_source_only_closed_loop_fixture_pilot,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import ActorCritic


def _model_config(**overrides):
    config = {
        "device": "cpu",
        "actor_encoder": "human_view_online_gru",
        "actor_history_length": 1,
        "action_sequence_horizon": 1,
        "response_prediction_dim": 0,
        "response_prediction_horizon": 1,
        "log_std_init": -1.0,
        "log_std_min": -5.0,
        "log_std_max": -0.5,
    }
    config.update(overrides)
    return config


def _write_checkpoint(path, *, actor_encoder="human_view_online_gru", obs_dim=P0_OBSERVATION_DIM):
    model = ActorCritic(
        obs_dim=obs_dim,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder=actor_encoder,
        action_sequence_horizon=1,
    )
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(actor_encoder=actor_encoder),
        },
        path,
    )


def test_admit_actor_checkpoint_requires_canonical_recurrent_actor(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    model, admission = admit_actor_checkpoint(checkpoint_path)

    assert model is not None
    assert admission.checkpoint_admitted is True
    assert admission.obs_dim == P0_OBSERVATION_DIM
    assert admission.action_dim == ACTION_DIM
    assert admission.actor_encoder == "human_view_online_gru"


def test_admit_actor_checkpoint_rejects_non_recurrent_actor(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    model = ActorCritic(obs_dim=P0_OBSERVATION_DIM, act_dim=ACTION_DIM, hidden_size=16)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(actor_encoder="mlp"),
        },
        checkpoint_path,
    )

    model, admission = admit_actor_checkpoint(checkpoint_path)

    assert model is None
    assert admission.checkpoint_admitted is False
    assert "actor_encoder=mlp" in admission.reason


def test_run_source_only_closed_loop_fixture_pilot_executes_policy_actions(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    rows, summary = run_source_only_closed_loop_fixture_pilot(checkpoint_path, horizon_steps=2)

    assert summary["status_pass"] is True
    assert summary["result_class"] == "source_only_closed_loop_fixture_pilot_pass"
    assert summary["checkpoint_admitted"] is True
    assert summary["fixture_count"] == 3
    assert summary["reset_count"] == 3
    assert summary["step_count"] == 6
    assert summary["horizon_steps_per_fixture"] == 2
    assert summary["policy_action"] is True
    assert summary["policy_rollout_run"] is True
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["verdict_claim_made"] is False
    assert summary["all_reset_observations_shape_72"] is True
    assert summary["all_step_observations_shape_72"] is True
    assert summary["all_action_shapes_3"] is True
    assert summary["all_actions_finite"] is True
    assert summary["all_actions_within_bounds"] is True
    assert summary["all_backend_statuses_running"] is True
    assert summary["all_diagnostic_wheel_force_counts_4"] is True
    assert summary["fixture_labels_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert len(rows) == 6
    assert {row.role_family for row in rows} == {
        "stable_aes",
        "drift_required_recovery",
        "unavoidable_mitigation",
    }
    assert all(row.policy_action for row in rows)
    assert all(row.action_shape == ACTION_DIM for row in rows)
    assert all(np.isfinite([row.action_steer, row.action_throttle, row.action_brake]).all() for row in rows)


def test_run_preflight_writes_summary_and_rollout_rows(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    summary = run_preflight(
        tmp_path / "run",
        checkpoint_path=checkpoint_path,
        horizon_steps=1,
        next_blocker="m2489-source-only-closed-loop-fixture-pilot-result-audit",
    )

    assert summary["status_pass"] is True
    assert summary["milestone"] == "m2488-source-only-closed-loop-fixture-pilot-implementation-preflight"
    assert summary["step_count"] == 3
    assert summary["pilot_rollout_rows"] == str(tmp_path / "run" / "pilot_rollout_rows.csv")

    rows_path = tmp_path / "run" / "pilot_rollout_rows.csv"
    with rows_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert {row["observation_shape"] for row in rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in rows} == {str(ACTION_DIM)}
    assert {row["policy_action"] for row in rows} == {"True"}
