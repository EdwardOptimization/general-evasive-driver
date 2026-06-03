import csv
import json
from pathlib import Path

from autodrift.engineering_controller_failure_surface_mitigation_preserving_repair_execution import (
    run_mitigation_preserving_repair_execution,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    DEFAULT_SEED_COUNT,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_mitigation_preserving_repair_execution_writes_bounded_candidate_evidence(tmp_path):
    output_dir = tmp_path / "run"

    summary = run_mitigation_preserving_repair_execution(
        output_dir,
        seed_count=DEFAULT_SEED_COUNT,
        horizon_steps=20,
        candidate_relaxations=(0.0, 16.0),
        milestone="m2537-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_failure_surface_mitigation_preserving_repair_execution_pass"
    )
    assert summary["candidate_config_loaded"] is True
    assert summary["candidate_config_mutated"] is False
    assert summary["active_config_overwritten"] is False
    assert summary["repair_execution_started"] is True
    assert summary["repair_training_started"] is True
    assert summary["training_run"] is True
    assert summary["repaired_checkpoint_written"] is True
    assert summary["checkpoint_behavior_changed"] is True
    assert summary["candidate_sweep_row_count"] == 2
    assert summary["selected_repair_trace_row_count"] == 1
    assert summary["post_repair_smoke_row_count"] == 45
    assert summary["protected_gate_evaluation_row_count"] == 7
    assert summary["protected_row_match_count"] == 45
    assert summary["all_protected_rows_matched"] is True
    assert summary["gate_evaluation_traceable"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["source_only_backend_step_run"] is True
    assert summary["policy_action_run"] is True
    assert summary["open_loop_action_rollout_run"] is True
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["fresh_generalization_run"] is False
    assert summary["all_mitigation_primary_rows_considered"] is True
    assert summary["mitigation_primary_evaluated_row_count"] == 5
    assert "protected_proof_gates_all_passed" in summary
    assert "status_pass" in summary

    candidate_snapshot = json.loads((output_dir / "candidate_config_snapshot.json").read_text())
    checkpoint_manifest = json.loads((output_dir / "repaired_checkpoint_manifest.json").read_text())
    sweep_rows = _read_csv(output_dir / "repair_candidate_sweep.csv")
    selected_rows = _read_csv(output_dir / "selected_repair_trace.csv")
    post_rows = _read_csv(output_dir / "post_repair_smoke_rows.csv")
    gate_rows = _read_csv(output_dir / "protected_gate_evaluation.csv")

    assert candidate_snapshot["candidate_config"]["actor_contract"]["observation_shape"] == 72
    assert candidate_snapshot["candidate_config_mutated"] is False
    assert candidate_snapshot["active_config_overwritten"] is False
    assert checkpoint_manifest["behavior_changed"] is True
    assert checkpoint_manifest["checkpoint_promoted"] is False
    assert checkpoint_manifest["source_model_state_hash"] != checkpoint_manifest["repaired_model_state_hash"]
    assert Path(checkpoint_manifest["repaired_checkpoint"]).exists()
    assert len(sweep_rows) == 2
    assert [row["selected_for_repair_trace"] for row in sweep_rows].count("True") == 1
    assert {row["diagnostic_only_no_ranking_claim"] for row in sweep_rows} == {"True"}
    assert {row["success_rate_field_emitted"] for row in sweep_rows} == {"False"}
    assert {row["ranking_or_winner_field_emitted"] for row in sweep_rows} == {"False"}
    assert len(selected_rows) == 1
    assert selected_rows[0]["candidate_id"] == summary["selected_candidate_id"]
    assert len(post_rows) == 45
    assert {row["protected_row_matched"] for row in post_rows} == {"True"}
    assert {row["actor_input_leak_flags"] for row in post_rows} == {"none"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in post_rows} == {"False"}
    assert {row["success_rate_field_emitted"] for row in post_rows} == {"False"}
    assert {row["ranking_or_winner_field_emitted"] for row in post_rows} == {"False"}
    assert {row["repair_training_started"] for row in post_rows} == {"True"}
    assert {row["observation_shape"] for row in post_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in post_rows} == {str(ACTION_DIM)}
    assert {row["source_checkpoint_path"] for row in post_rows} == {summary["source_checkpoint"]}
    assert {row["repaired_checkpoint_path"] for row in post_rows} == {summary["repaired_checkpoint"]}
    assert {row["gate_id"] for row in gate_rows} == {
        "contract_p0_72_3",
        "no_oracle_actor_inputs",
        "road_boundary_proof",
        "mitigation_proof",
        "command_conflict_proof",
        "fresh_seed_generalization",
        "no_ranking_no_success_rate",
    }
    assert {
        row["gate_id"]: row["gate_pass"]
        for row in gate_rows
        if row["gate_id"]
        in {"contract_p0_72_3", "no_oracle_actor_inputs", "no_ranking_no_success_rate"}
    } == {
        "contract_p0_72_3": "True",
        "no_oracle_actor_inputs": "True",
        "no_ranking_no_success_rate": "True",
    }
    assert {row["trace_to_protected_rows"] for row in gate_rows} == {"True"}
