import csv
import json

from autodrift.engineering_controller_failure_surface_intervention_repair_smoke import (
    run_failure_surface_intervention_repair_smoke,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    DEFAULT_SEED_COUNT,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_failure_surface_repair_smoke_writes_traceable_negative_smoke(tmp_path):
    output_dir = tmp_path / "run"

    summary = run_failure_surface_intervention_repair_smoke(
        output_dir,
        seed_count=DEFAULT_SEED_COUNT,
        horizon_steps=100,
        milestone="m2529-test",
        next_blocker="m2530-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_failure_surface_intervention_repair_smoke_pass"
    )
    assert summary["smoke_outcome_class"] == "negative_no_update_repair_smoke_recorded"
    assert summary["candidate_config_loaded"] is True
    assert summary["candidate_config_mutated"] is False
    assert summary["active_config_overwritten"] is False
    assert summary["repair_smoke_row_count"] == 45
    assert summary["protected_gate_evaluation_row_count"] == 7
    assert summary["protected_row_match_count"] == 45
    assert summary["all_protected_rows_matched"] is True
    assert summary["gate_evaluation_traceable"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["source_only_backend_step_run"] is True
    assert summary["policy_action_run"] is True
    assert summary["open_loop_action_rollout_run"] is True
    assert summary["repair_training_started"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["protected_proof_gates_all_passed"] is False
    assert summary["protected_proof_gate_fail_count"] == 3

    candidate_snapshot = json.loads((output_dir / "candidate_config_snapshot.json").read_text())
    repair_rows = _read_csv(output_dir / "repair_smoke_rows.csv")
    gate_rows = _read_csv(output_dir / "protected_gate_evaluation.csv")

    assert candidate_snapshot["candidate_config"]["actor_contract"]["observation_shape"] == 72
    assert candidate_snapshot["candidate_config_mutated"] is False
    assert len(repair_rows) == 45
    assert len(gate_rows) == 7
    assert {row["protected_row_matched"] for row in repair_rows} == {"True"}
    assert {row["actor_input_leak_flags"] for row in repair_rows} == {"none"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in repair_rows} == {"False"}
    assert {row["success_rate_field_emitted"] for row in repair_rows} == {"False"}
    assert {row["ranking_or_winner_field_emitted"] for row in repair_rows} == {"False"}
    assert {row["observation_shape"] for row in repair_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in repair_rows} == {str(ACTION_DIM)}
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
    assert {
        row["gate_id"]: row["gate_pass"]
        for row in gate_rows
        if row["gate_id"]
        in {"road_boundary_proof", "mitigation_proof", "command_conflict_proof"}
    } == {
        "road_boundary_proof": "False",
        "mitigation_proof": "False",
        "command_conflict_proof": "False",
    }
    assert {row["trace_to_protected_rows"] for row in gate_rows} == {"True"}
