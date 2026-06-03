import csv

import torch

from autodrift.engineering_controller_runtime_report import (
    parse_batch_sizes,
    run_runtime_report,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import ActorCritic


FALSE_CLAIM_FLAGS = [
    "environment_rollout_run",
    "simulator_step_run",
    "external_high_fidelity_simulation_included",
    "policy_action_run",
    "policy_rollout_run",
    "action_outputs_interpreted_as_control",
    "measured_validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "success_rate_computed",
    "controller_family_verdict_computed",
    "driver_performance_claim_made",
    "verdict_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "level3_self_id_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
]


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


def _write_checkpoint(path):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(),
        },
        path,
    )


def test_parse_batch_sizes_requires_positive_sizes():
    assert parse_batch_sizes("1, 8,32") == (1, 8, 32)

    for invalid in ["", "0", "1,0", "-1"]:
        try:
            parse_batch_sizes(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {invalid!r}")


def test_run_runtime_report_writes_bounded_forward_cost_artifacts(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    summary = run_runtime_report(
        tmp_path / "run",
        checkpoint_path=checkpoint_path,
        batch_sizes=(1, 4),
        warmup_iterations=1,
        measured_iterations=3,
        seed=123,
        next_blocker="m2509-test",
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_runtime_inference_cost_report_pass"
    assert summary["checkpoint_admitted"] is True
    assert summary["checkpoint_obs_dim"] == P0_OBSERVATION_DIM
    assert summary["checkpoint_action_dim"] == ACTION_DIM
    assert summary["checkpoint_actor_encoder"] == "human_view_online_gru"
    assert summary["checkpoint_action_sequence_horizon"] == 1
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["batch_sizes"] == [1, 4]
    assert summary["warmup_iterations"] == 1
    assert summary["measured_iterations"] == 3
    assert summary["measurement_row_count"] == 6
    assert summary["expected_measurement_row_count"] == 6
    assert summary["all_observation_shape_72"] is True
    assert summary["all_action_shape_3"] is True
    assert summary["all_actions_finite"] is True
    assert summary["all_actions_within_bounds"] is True
    assert summary["all_forward_times_positive"] is True
    assert summary["actor_forward_pass_run"] is True
    assert summary["timed_path"] == "recurrent_features_tensor_plus_actor_mean_tanh"
    assert summary["synthetic_observation_source"] == "seeded_normal_shape_only"
    assert set(summary["latency_by_batch"]) == {"1", "4"}
    assert summary["latency_by_batch"]["1"]["measurement_count"] == 3
    assert summary["latency_by_batch"]["4"]["measurement_count"] == 3

    for flag in FALSE_CLAIM_FLAGS:
        assert summary[flag] is False

    rows_path = tmp_path / "run" / "runtime_measurements.csv"
    with rows_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert {row["batch_size"] for row in rows} == {"1", "4"}
    assert {row["observation_shape"] for row in rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in rows} == {str(ACTION_DIM)}
    assert {row["action_finite"] for row in rows} == {"True"}
    assert {row["action_within_bounds"] for row in rows} == {"True"}
    assert all(float(row["forward_time_us"]) > 0.0 for row in rows)
    assert (tmp_path / "run" / "summary.json").exists()
