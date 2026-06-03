import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_hf3_reset_feasibility_execution_materialization import (
    BACKEND_AVAILABILITY_FIELDNAMES,
    CLAIM_BOUNDARY_FIELDNAMES,
    OUTCOME_SCHEMA_FIELDNAMES,
    RESET_CANDIDATE_FIELDNAMES,
    RESET_PLAN_FIELDNAMES,
    RESET_REQUEST_FIELDNAMES,
    build_backend_availability_checks,
    build_claim_boundary_checks,
    build_reset_execution_candidate_rows,
    build_reset_execution_plan_rows,
    build_reset_outcome_schema_rows,
    build_reset_request_contract_rows,
    materialize_route_a_hf3_reset_feasibility_execution_preflight,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _hf3_candidate_rows():
    return _read_csv(
        Path(
            "runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_pilot_candidate_rows.csv"
        )
    )


def test_build_hf3_reset_execution_boundary_rows_preserve_no_execution_contract():
    reset_candidate_rows = build_reset_execution_candidate_rows(_hf3_candidate_rows())
    backend_rows = build_backend_availability_checks()
    request_rows = build_reset_request_contract_rows(reset_candidate_rows)
    plan_rows = build_reset_execution_plan_rows(reset_candidate_rows)
    outcome_rows = build_reset_outcome_schema_rows()
    claim_rows = build_claim_boundary_checks()

    assert len(reset_candidate_rows) == 2
    assert set(reset_candidate_rows[0]) == set(RESET_CANDIDATE_FIELDNAMES)
    assert {row["route_role_id"] for row in reset_candidate_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in reset_candidate_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in reset_candidate_rows} == {ACTION_DIM}
    assert {row["pilot_admission_status"] for row in reset_candidate_rows} == {
        "not_admitted_reset_execution_preflight_only"
    }
    assert {row["reset_execution_status"] for row in reset_candidate_rows} == {
        "planned_not_executed_in_m2564"
    }
    assert {row["reset_success_claim_allowed"] for row in reset_candidate_rows} == {False}

    assert len(backend_rows) == 4
    assert set(backend_rows[0]) == set(BACKEND_AVAILABILITY_FIELDNAMES)
    assert {row["install_allowed"] for row in backend_rows} == {False}
    assert {row["import_allowed"] for row in backend_rows} == {False}
    assert {row["runtime_execution_allowed"] for row in backend_rows} == {False}
    assert {row["dependency_mutation_allowed"] for row in backend_rows} == {False}

    assert len(request_rows) == 2
    assert set(request_rows[0]) == set(RESET_REQUEST_FIELDNAMES)
    assert {row["actor_input_mutation_allowed"] for row in request_rows} == {False}
    assert {row["oracle_field_allowed"] for row in request_rows} == {False}
    assert {row["metadata_actor_visible"] for row in request_rows} == {False}

    assert len(plan_rows) == 2
    assert set(plan_rows[0]) == set(RESET_PLAN_FIELDNAMES)
    assert {row["reset_execution_allowed_in_m2564"] for row in plan_rows} == {False}
    assert {row["policy_action_allowed_in_m2564"] for row in plan_rows} == {False}
    assert {row["environment_step_allowed_in_m2564"] for row in plan_rows} == {False}
    assert {row["rollout_execution_allowed_in_m2564"] for row in plan_rows} == {False}

    assert len(outcome_rows) == 8
    assert set(outcome_rows[0]) == set(OUTCOME_SCHEMA_FIELDNAMES)
    assert {row["actor_visible_allowed"] for row in outcome_rows} == {False}
    assert {row["allowed_to_support_validation"] for row in outcome_rows} == {False}

    assert len(claim_rows) == 8
    assert set(claim_rows[0]) == set(CLAIM_BOUNDARY_FIELDNAMES)
    assert {row["claim_allowed_in_m2564"] for row in claim_rows} == {False}


def test_materialize_route_a_hf3_reset_execution_preflight_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2564.md"

    summary = materialize_route_a_hf3_reset_feasibility_execution_preflight(
        output_dir,
        milestone="m2564-test",
        next_blocker="m2565-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_reset_feasibility_execution_materialization_preflight_pass"
    )
    assert summary["reset_execution_candidate_row_count"] == 2
    assert summary["backend_availability_check_count"] == 4
    assert summary["reset_request_contract_count"] == 2
    assert summary["reset_execution_plan_count"] == 2
    assert summary["reset_outcome_schema_row_count"] == 8
    assert summary["claim_boundary_check_count"] == 8
    assert summary["candidate_rows_pilot_admitted"] is False
    assert summary["reset_success_claim_allowed"] is False
    assert summary["external_install_allowed"] is False
    assert summary["external_import_allowed"] is False
    assert summary["reset_execution_allowed_in_m2564"] is False
    assert summary["policy_action_allowed_in_m2564"] is False
    assert summary["environment_step_allowed_in_m2564"] is False
    assert summary["rollout_execution_allowed_in_m2564"] is False
    assert summary["runtime_execution_allowed"] is False
    assert summary["external_runtime_execution_allowed"] is False
    assert summary["dependency_mutation_allowed"] is False
    assert summary["claim_allowed_in_m2564"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["environment_reset_run"] is False
    assert summary["reset_execution_run"] is False
    assert summary["rollout_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False

    reset_candidate_rows = _read_csv(output_dir / "hf3_reset_execution_candidate_rows.csv")
    backend_rows = _read_csv(output_dir / "hf3_backend_availability_checks.csv")
    request_rows = _read_csv(output_dir / "hf3_reset_request_contract.csv")
    plan_rows = _read_csv(output_dir / "hf3_reset_execution_plan.csv")
    outcome_rows = _read_csv(output_dir / "hf3_reset_outcome_schema.csv")
    claim_rows = _read_csv(output_dir / "hf3_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "materialization_gate_matrix.csv")

    assert len(reset_candidate_rows) == 2
    assert len(backend_rows) == 4
    assert len(request_rows) == 2
    assert len(plan_rows) == 2
    assert len(outcome_rows) == 8
    assert len(claim_rows) == 8
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["reset_execution_status"] for row in reset_candidate_rows} == {
        "planned_not_executed_in_m2564"
    }
    assert {row["runtime_execution_allowed"] for row in backend_rows} == {"False"}
    assert {row["actor_input_mutation_allowed"] for row in request_rows} == {"False"}
    assert {row["reset_execution_allowed_in_m2564"] for row in plan_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in outcome_rows} == {"False"}
    assert {row["claim_allowed_in_m2564"] for row in claim_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
