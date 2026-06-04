import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_execution import (
    REPAIRED_SUBJECT_ID,
    run_source_only_gap_targeted_repair_execution,
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


def test_gap_targeted_repair_execution_writes_traceable_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2648.md"
    source_checkpoint = tmp_path / "source.pt"
    _write_checkpoint(source_checkpoint)

    summary = run_source_only_gap_targeted_repair_execution(
        output_dir,
        source_checkpoint=source_checkpoint,
        horizon_steps=1,
        milestone="m2648-test",
        next_blocker="m2649-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_gap_targeted_repair_execution_preflight_pass"
    )
    assert summary["repair_execution_started"] is True
    assert summary["repair_training_started"] is True
    assert summary["training_run"] is True
    assert summary["repaired_checkpoint_written"] is True
    assert summary["checkpoint_behavior_changed"] is True
    assert summary["training_observation_count"] == 24
    assert summary["admitted_repair_target_count"] == 2
    assert summary["protected_reference_count"] == 2
    assert set(summary["target_gap_families"]) == {
        "road_departure_dominant_gap",
        "drift_recovery_mixed_gap",
    }
    assert "mitigation_collision_saturated_reference" in summary["protected_reference_families"]
    assert "axis_sensitivity_not_yet_decisive" in summary["protected_reference_families"]
    assert summary["post_repair_behavior_row_count"] == 160
    assert summary["telemetry_row_count"] == 160
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["source_only_backend_reset_run"] is True
    assert summary["source_only_backend_step_run"] is True
    assert summary["policy_action_run"] is True
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["driver_performance_claim_made"] is False

    config = json.loads((output_dir / "repair_config_snapshot.json").read_text())
    checkpoint_manifest = json.loads((output_dir / "repaired_checkpoint_manifest.json").read_text())
    trace_rows = _read_csv(output_dir / "repair_training_trace.csv")
    post_rows = _read_csv(output_dir / "post_repair_behavior_rows.csv")
    gate_rows = _read_csv(output_dir / "repair_gate_evaluation.csv")

    assert config["actor_contract"]["observation_shape"] == P0_OBSERVATION_DIM
    assert config["active_config_overwritten"] is False
    assert checkpoint_manifest["behavior_changed"] is True
    assert checkpoint_manifest["checkpoint_promoted"] is False
    assert Path(checkpoint_manifest["repaired_checkpoint"]).exists()
    assert len(trace_rows) == 1
    assert trace_rows[0]["finite_update"] == "True"
    assert float(trace_rows[0]["mean_action_delta_l1"]) > 0.0
    assert len(post_rows) == 160
    assert len(gate_rows) == 7
    assert {row["subject_id"] for row in post_rows if row["subject_id"] == REPAIRED_SUBJECT_ID}
    assert {row["observation_shape"] for row in post_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in post_rows} == {str(ACTION_DIM)}
    assert {row["actor_input_leak_flags"] for row in post_rows} == {"none"}
    assert {row["taxonomy_labels_actor_visible"] for row in post_rows} == {"False"}
    assert {row["repair_target_labels_actor_visible"] for row in post_rows} == {"False"}
    assert {row["repair_execution_started"] for row in post_rows} == {"True"}
    assert {row["repaired_checkpoint_written"] for row in post_rows} == {"True"}
    assert {
        row["gate_id"] for row in gate_rows
    } == {
        "target_road_boundary_margin_control",
        "target_drift_collision_recovery_tradeoff",
        "protected_mitigation_reference",
        "protected_axis_diagnostic_only",
        "contract_p0_72_3",
        "no_oracle_actor_inputs",
        "no_ranking_no_success_rate",
    }
    assert {
        row["gate_id"]: row["gate_pass"]
        for row in gate_rows
        if row["gate_id"] in {"contract_p0_72_3", "no_oracle_actor_inputs"}
    } == {
        "contract_p0_72_3": "True",
        "no_oracle_actor_inputs": "True",
    }
    assert doc_path.exists()
