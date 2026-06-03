import csv
import json

from autodrift.engineering_controller_failure_surface_intervention_plan import (
    materialize_failure_surface_intervention_plan,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materialize_failure_surface_intervention_plan_writes_traceable_artifacts(tmp_path):
    output_dir = tmp_path / "plan"

    summary = materialize_failure_surface_intervention_plan(
        output_dir,
        milestone="m2527-test",
        next_blocker="m2528-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_failure_surface_intervention_plan_materialization_pass"
    )
    assert summary["source_behavior_row_count"] == 45
    assert summary["protected_regression_row_count"] == 45
    assert summary["primary_protected_row_count"] == 15
    assert summary["reference_context_row_count"] == 30
    assert summary["road_boundary_primary_row_count"] == 10
    assert summary["mitigation_primary_row_count"] == 5
    assert summary["command_conflict_primary_row_count"] == 15
    assert summary["gate_matrix_row_count"] >= 7
    assert summary["protected_rows_trace_to_source"] is True
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["actor_input_contract_changed"] is False
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["rule_switching_controller_modes_allowed"] is False
    assert summary["active_config_overwritten"] is False
    assert summary["training_started"] is False
    assert summary["policy_action_run"] is False
    assert summary["driver_performance_claim_made"] is False

    spec = json.loads((output_dir / "intervention_spec.json").read_text())
    protected_rows = _read_csv(output_dir / "protected_regression_rows.csv")
    gates = _read_csv(output_dir / "implementation_gate_matrix.csv")
    patch_plan = json.loads((output_dir / "candidate_config_patch_plan.json").read_text())

    assert spec["observation_shape"] == P0_OBSERVATION_DIM
    assert spec["action_shape"] == ACTION_DIM
    assert spec["actor_input_contract_changed"] is False
    assert spec["rule_switching_controller_modes_allowed"] is False
    assert "mu" in spec["forbidden_actor_input_fields"]
    assert "controller_mode" in spec["forbidden_actor_input_fields"]
    assert "minimum_road_margin_m" in spec["allowed_reward_or_evaluator_fields"]
    assert {row["row_role"] for row in protected_rows} == {
        "primary_protected",
        "reference_context",
    }
    assert {
        row["seed"]
        for row in protected_rows
        if row["protection_group"] == "road_boundary_primary"
    } == {
        "252300",
        "252301",
        "252302",
        "252303",
        "252304",
        "253300",
        "253301",
        "253302",
        "253303",
        "253304",
    }
    assert {
        row["seed"]
        for row in protected_rows
        if row["protection_group"] == "mitigation_primary"
    } == {"254300", "254301", "254302", "254303", "254304"}
    assert any(row["gate_id"] == "no_oracle_actor_inputs" for row in gates)
    assert any(row["gate_id"] == "fresh_seed_generalization" for row in gates)
    assert patch_plan["active_config_overwritten"] is False
    assert patch_plan["training_started"] is False
    assert patch_plan["policy_action_run"] is False
