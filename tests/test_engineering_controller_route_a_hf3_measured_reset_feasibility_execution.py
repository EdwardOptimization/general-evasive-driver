import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_hf3_measured_reset_feasibility_execution import (
    ACTOR_VIEW_FIELDNAMES,
    BACKEND_PROBE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    EXECUTION_FIELDNAMES,
    OUTCOME_FIELDNAMES,
    REQUEST_FIELDNAMES,
    build_backend_probe_rows,
    build_claim_boundary_checks,
    build_measured_reset_request_rows,
    execute_reset_only_rows,
    materialize_route_a_hf3_measured_reset_feasibility_execution,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2564_candidate_rows():
    return _read_csv(
        Path(
            "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_candidate_rows.csv"
        )
    )


def test_build_hf3_measured_reset_rows_execute_reset_only_contract():
    request_rows = build_measured_reset_request_rows(_m2564_candidate_rows())
    backend_rows = build_backend_probe_rows(request_rows)
    execution_rows, actor_view_rows, outcome_rows = execute_reset_only_rows(request_rows)
    claim_rows = build_claim_boundary_checks(execution_rows)

    assert len(request_rows) == 2
    assert set(request_rows[0]) == set(REQUEST_FIELDNAMES)
    assert {row["route_role_id"] for row in request_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in request_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in request_rows} == {ACTION_DIM}
    assert {row["policy_action_allowed"] for row in request_rows} == {False}
    assert {row["environment_step_allowed"] for row in request_rows} == {False}
    assert {row["rollout_allowed"] for row in request_rows} == {False}
    assert {row["actor_input_mutation_allowed"] for row in request_rows} == {False}
    assert {row["status_pass"] for row in request_rows} == {True}

    assert len(backend_rows) == 2
    assert set(backend_rows[0]) == set(BACKEND_PROBE_FIELDNAMES)
    assert {row["backend_class"] for row in backend_rows} == {"CurrentSimDynamicsBackend"}
    assert {row["backend_reset_allowed_in_m2568"] for row in backend_rows} == {True}
    assert {row["backend_step_allowed_in_m2568"] for row in backend_rows} == {False}
    assert {row["external_install_allowed"] for row in backend_rows} == {False}
    assert {row["external_import_allowed"] for row in backend_rows} == {False}
    assert {row["dependency_mutation_allowed"] for row in backend_rows} == {False}

    assert len(execution_rows) == 2
    assert set(execution_rows[0]) == set(EXECUTION_FIELDNAMES)
    assert {row["reset_attempted"] for row in execution_rows} == {True}
    assert {row["reset_status"] for row in execution_rows} == {
        "reset_observed_actor_view_available"
    }
    assert {row["actor_view_available"] for row in execution_rows} == {True}
    assert {row["diagnostics_recorded"] for row in execution_rows} == {True}
    assert {row["policy_action_executed"] for row in execution_rows} == {False}
    assert {row["environment_step_executed"] for row in execution_rows} == {False}
    assert {row["rollout_executed"] for row in execution_rows} == {False}
    assert {row["reset_success_claim_allowed"] for row in execution_rows} == {False}

    assert len(actor_view_rows) == 2
    assert set(actor_view_rows[0]) == set(ACTOR_VIEW_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_view_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_view_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_view_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in actor_view_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in actor_view_rows} == {False}

    assert len(outcome_rows) == 2
    assert set(outcome_rows[0]) == set(OUTCOME_FIELDNAMES)
    assert {row["reset_attempted"] for row in outcome_rows} == {True}
    assert {row["actor_view_available"] for row in outcome_rows} == {True}
    assert {row["reset_success_claim_allowed"] for row in outcome_rows} == {False}
    assert {row["validation_claim_allowed"] for row in outcome_rows} == {False}

    assert len(claim_rows) == 8
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2568"]
    } == {"reset_execution_observed"}


def test_materialize_route_a_hf3_measured_reset_feasibility_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2568.md"

    summary = materialize_route_a_hf3_measured_reset_feasibility_execution(
        output_dir,
        milestone="m2568-test",
        next_blocker="m2569-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_measured_reset_feasibility_execution_materialization_preflight_pass"
    )
    assert summary["measured_reset_request_row_count"] == 2
    assert summary["backend_probe_row_count"] == 2
    assert summary["reset_execution_row_count"] == 2
    assert summary["actor_view_contract_row_count"] == 2
    assert summary["reset_outcome_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 8
    assert summary["reset_only_execution_run"] is True
    assert summary["reset_execution_attempted_count"] == 2
    assert summary["actor_view_available_count"] == 2
    assert summary["policy_action_executed"] is False
    assert summary["environment_step_executed"] is False
    assert summary["rollout_executed"] is False
    assert summary["reset_success_claim_allowed"] is False
    assert summary["reset_execution_observed_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2568"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["driver_performance_claim_made"] is False

    request_rows = _read_csv(output_dir / "hf3_measured_reset_request_rows.csv")
    backend_rows = _read_csv(output_dir / "hf3_backend_probe_rows.csv")
    execution_rows = _read_csv(output_dir / "hf3_measured_reset_execution_rows.csv")
    actor_view_rows = _read_csv(output_dir / "hf3_actor_view_contract_rows.csv")
    outcome_rows = _read_csv(output_dir / "hf3_reset_outcome_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "measured_reset_gate_matrix.csv")

    assert len(request_rows) == 2
    assert len(backend_rows) == 2
    assert len(execution_rows) == 2
    assert len(actor_view_rows) == 2
    assert len(outcome_rows) == 2
    assert len(claim_rows) == 8
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["reset_attempted"] for row in execution_rows} == {"True"}
    assert {row["actor_view_available"] for row in execution_rows} == {"True"}
    assert {row["policy_action_executed"] for row in execution_rows} == {"False"}
    assert {row["environment_step_executed"] for row in execution_rows} == {"False"}
    assert {row["rollout_executed"] for row in execution_rows} == {"False"}
    assert {row["actor_observation_shape"] for row in actor_view_rows} == {
        str(P0_OBSERVATION_DIM)
    }
    assert {row["validation_claim_allowed"] for row in outcome_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2568"] == "True"
    } == {"reset_execution_observed"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
