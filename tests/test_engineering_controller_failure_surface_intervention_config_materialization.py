import csv
import json

from autodrift.engineering_controller_failure_surface_intervention_config_materialization import (
    materialize_failure_surface_candidate_config,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materialize_candidate_config_writes_immutable_artifacts(tmp_path):
    output_dir = tmp_path / "config"

    summary = materialize_failure_surface_candidate_config(
        output_dir,
        milestone="m2528-test",
        next_blocker="m2529-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_failure_surface_intervention_config_materialization_pass"
    )
    assert summary["candidate_config_file_written"] is True
    assert summary["active_config_overwritten"] is False
    assert summary["immutable_candidate_config"] is True
    assert summary["config_patch_audit_row_count"] == 4
    assert summary["protected_gate_binding_row_count"] == 7
    assert summary["protected_rows_traceable"] is True
    assert summary["gate_binding_traceable"] is True
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["actor_input_contract_changed"] is False
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["rule_switching_controller_modes_allowed"] is False
    assert summary["training_started"] is False
    assert summary["policy_action_run"] is False
    assert summary["driver_performance_claim_made"] is False

    candidate = json.loads((output_dir / "candidate_config.json").read_text())
    patch_audit = _read_csv(output_dir / "config_patch_audit.csv")
    gate_bindings = _read_csv(output_dir / "protected_gate_bindings.csv")

    assert candidate["actor_contract"]["observation_shape"] == P0_OBSERVATION_DIM
    assert candidate["actor_contract"]["action_shape"] == ACTION_DIM
    assert candidate["actor_contract"]["actor_input_contract_changed"] is False
    assert candidate["actor_contract"]["rule_switching_controller_modes_allowed"] is False
    assert candidate["active_config_overwritten"] is False
    assert candidate["training_started"] is False
    assert candidate["policy_action_run"] is False
    assert candidate["protected_dataset"]["protected_row_count"] == 45
    assert candidate["protected_dataset"]["primary_protected_row_count"] == 15
    assert "controller_mode" in candidate["forbidden_actor_input_fields"]
    assert "mu" in candidate["forbidden_actor_input_fields"]
    assert {
        row["patch_family"]
        for row in patch_audit
    } == {
        "road_boundary_reward_or_constraint",
        "mitigation_severity_shaping",
        "simultaneous_throttle_brake_regularizer",
        "protected_row_seed_mix",
    }
    assert {row["active_config_overwritten"] for row in patch_audit} == {"False"}
    assert {row["training_started"] for row in patch_audit} == {"False"}
    assert {row["policy_action_run"] for row in patch_audit} == {"False"}
    assert {row["binding_status"] for row in gate_bindings} == {
        "bound_to_m2527_plan_rows"
    }
    assert any(row["gate_id"] == "road_boundary_proof" for row in gate_bindings)
    assert any(row["gate_id"] == "fresh_seed_generalization" for row in gate_bindings)
