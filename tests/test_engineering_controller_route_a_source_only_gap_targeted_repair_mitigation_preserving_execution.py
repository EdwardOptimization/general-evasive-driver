import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_execution import (
    REPAIRED_SUBJECT_ID,
)
from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution import (
    run_mitigation_preserving_repair_execution,
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


def _write_checkpoint(path: Path):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    torch.save(
        {
            "model_state": {
                key: value.detach().cpu() for key, value in model.state_dict().items()
            },
            "config": _model_config(),
        },
        path,
    )


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_mitigation_preserving_route_a_repair_execution_writes_gate_aware_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2655.md"
    source_checkpoint = tmp_path / "source.pt"
    _write_checkpoint(source_checkpoint)

    summary = run_mitigation_preserving_repair_execution(
        output_dir,
        source_checkpoint=source_checkpoint,
        horizon_steps=1,
        candidate_specs=(
            {
                "candidate_id": "m2655_test_retain",
                "steer_bias_delta": 0.12,
                "throttle_bias_delta": -3.0,
                "brake_bias_delta": 3.0,
            },
            {
                "candidate_id": "m2655_test_soft",
                "steer_bias_delta": 0.08,
                "throttle_bias_delta": -2.0,
                "brake_bias_delta": 2.0,
            },
        ),
        milestone="m2655-test",
        next_blocker="m2656-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution_preflight_pass"
    )
    assert summary["m2653_status_pass"] is True
    assert summary["m2653_gate_matrix_pass"] is True
    assert summary["repair_execution_started"] is True
    assert summary["repair_training_started"] is True
    assert summary["training_run"] is True
    assert summary["source_only_backend_reset_run"] is True
    assert summary["source_only_backend_step_run"] is True
    assert summary["policy_action_run"] is True
    assert summary["repaired_checkpoint_written"] is True
    assert summary["checkpoint_behavior_changed"] is True
    assert summary["training_observation_count"] == 24
    assert summary["candidate_sweep_row_count"] == 2
    assert summary["selected_repair_trace_row_count"] == 1
    assert summary["post_repair_behavior_row_count"] == 160
    assert summary["telemetry_row_count"] == 160
    assert summary["mitigation_preserving_gate_evaluation_row_count"] == 9
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["taxonomy_labels_actor_visible"] is False
    assert summary["repair_target_labels_actor_visible"] is False
    assert summary["objective_gate_labels_actor_visible"] is False
    assert summary["route_decision_actor_visible"] is False
    assert summary["active_config_overwritten"] is False
    assert summary["objective_artifacts_mutated"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["driver_performance_claim_made"] is False

    config = json.loads((output_dir / "repair_config_snapshot.json").read_text())
    checkpoint_manifest = json.loads((output_dir / "repaired_checkpoint_manifest.json").read_text())
    sweep_rows = _read_csv(output_dir / "repair_candidate_sweep.csv")
    selected_rows = _read_csv(output_dir / "selected_repair_trace.csv")
    post_rows = _read_csv(output_dir / "post_repair_behavior_rows.csv")
    gate_rows = _read_csv(output_dir / "mitigation_preserving_gate_evaluation.csv")

    assert config["actor_contract"]["observation_shape"] == P0_OBSERVATION_DIM
    assert config["actor_contract"]["action_shape"] == ACTION_DIM
    assert config["actor_contract"]["objective_gate_labels_actor_visible"] is False
    assert checkpoint_manifest["behavior_changed"] is True
    assert checkpoint_manifest["checkpoint_promoted"] is False
    assert checkpoint_manifest["selected_candidate_id"] == summary["selected_candidate_id"]
    assert Path(checkpoint_manifest["repaired_checkpoint"]).exists()
    assert len(sweep_rows) == 2
    assert [row["selected_for_repair_trace"] for row in sweep_rows].count("True") == 1
    assert {row["diagnostic_only_no_ranking_claim"] for row in sweep_rows} == {"True"}
    assert {row["success_rate_field_emitted"] for row in sweep_rows} == {"False"}
    assert {row["ranking_or_winner_field_emitted"] for row in sweep_rows} == {"False"}
    assert len(selected_rows) == 1
    assert selected_rows[0]["candidate_id"] == summary["selected_candidate_id"]
    assert len(post_rows) == 160
    assert {row["subject_id"] for row in post_rows if row["subject_id"] == REPAIRED_SUBJECT_ID}
    assert {row["observation_shape"] for row in post_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in post_rows} == {str(ACTION_DIM)}
    assert {row["actor_input_leak_flags"] for row in post_rows} == {"none"}
    assert {row["taxonomy_labels_actor_visible"] for row in post_rows} == {"False"}
    assert {row["repair_target_labels_actor_visible"] for row in post_rows} == {"False"}
    assert {row["objective_gate_labels_actor_visible"] for row in post_rows} == {"False"}
    assert {row["route_decision_actor_visible"] for row in post_rows} == {"False"}
    assert {row["repair_execution_started"] for row in post_rows} == {"True"}
    assert {row["repaired_checkpoint_written"] for row in post_rows} == {"True"}
    assert {
        row["gate_id"] for row in gate_rows
    } == {
        "target_road_boundary_margin_control",
        "target_drift_collision_recovery_tradeoff",
        "severity_proxy_non_regression",
        "obstacle_penetration_non_regression",
        "minimum_obstacle_clearance_preservation",
        "event_transition_guard",
        "contract_p0_72_3",
        "no_oracle_actor_inputs",
        "no_ranking_no_success_rate",
    }
    assert {
        row["gate_id"]: row["gate_pass"]
        for row in gate_rows
        if row["gate_id"] in {"contract_p0_72_3", "no_oracle_actor_inputs", "no_ranking_no_success_rate"}
    } == {
        "contract_p0_72_3": "True",
        "no_oracle_actor_inputs": "True",
        "no_ranking_no_success_rate": "True",
    }
    assert doc_path.exists()
