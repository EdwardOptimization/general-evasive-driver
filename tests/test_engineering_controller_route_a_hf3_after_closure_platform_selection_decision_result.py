import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    CANDIDATE_DISPOSITION_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DECISION_RESULT_FIELDNAMES,
    DEPENDENCY_EXECUTION_GUARD_FIELDNAMES,
    EVIDENCE_FIELDNAMES,
    SELECTED_PLATFORM_FAMILY,
    VALIDATION_ADMISSION_GUARD_FIELDNAMES,
    build_actor_action_guard_rows,
    build_candidate_disposition_rows,
    build_claim_boundary_checks,
    build_decision_evidence_rows,
    build_decision_result_rows,
    build_dependency_execution_guard_rows,
    build_validation_admission_guard_rows,
    materialize_route_a_hf3_after_closure_platform_selection_decision_result,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2604_summary():
    return read_json(
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/summary.json"
    )


def test_build_hf3_after_closure_platform_selection_decision_result_rows_preserve_boundaries():
    summary = _m2604_summary()
    decision_rows = build_decision_result_rows(summary)
    evidence_rows = build_decision_evidence_rows(m2604_summary=summary)
    candidate_rows = build_candidate_disposition_rows(decision_rows, evidence_rows)
    dependency_rows = build_dependency_execution_guard_rows()
    admission_rows = build_validation_admission_guard_rows(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
    )
    guard_rows = build_actor_action_guard_rows(admission_rows)
    claim_rows = build_claim_boundary_checks(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
        admission_rows,
        guard_rows,
    )

    assert len(decision_rows) == 1
    assert set(decision_rows[0]) == set(DECISION_RESULT_FIELDNAMES)
    assert {row["selected_platform_family"] for row in decision_rows} == {SELECTED_PLATFORM_FAMILY}
    assert {row["source_or_equivalent_trace_required"] for row in decision_rows} == {True}
    assert {row["open_auditable_backend_selected"] for row in decision_rows} == {True}
    assert {row["black_box_backend_selected"] for row in decision_rows} == {False}
    assert {row["repo_local_current_sim_selected"] for row in decision_rows} == {False}
    assert {row["future_selection_result_audit_required"] for row in decision_rows} == {True}
    assert {row["validation_protocol_ready_in_m2607"] for row in decision_rows} == {False}
    assert {row["validation_admission_granted_in_m2607"] for row in decision_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2607"] for row in decision_rows} == {False}
    assert {row["driver_performance_claim_allowed_in_m2607"] for row in decision_rows} == {False}

    assert len(evidence_rows) == 12
    assert set(evidence_rows[0]) == set(EVIDENCE_FIELDNAMES)
    assert {row["admitted_for_platform_selection_decision_in_m2607"] for row in evidence_rows} == {True}
    assert {row["admitted_for_validation_readiness_in_m2607"] for row in evidence_rows} == {False}
    assert {row["admitted_for_driver_performance_in_m2607"] for row in evidence_rows} == {False}

    assert len(candidate_rows) == 3
    assert set(candidate_rows[0]) == set(CANDIDATE_DISPOSITION_FIELDNAMES)
    assert {row["platform_family"] for row in candidate_rows} == {
        "chrono_vehicle_or_equivalent_open_backend",
        "black_box_industry_demonstration_backend",
        "repo_local_current_sim_backend",
    }
    assert [
        row["platform_family"] for row in candidate_rows if row["selected_in_m2607"]
    ] == [SELECTED_PLATFORM_FAMILY]
    assert any(
        row["platform_family"] == SELECTED_PLATFORM_FAMILY
        and row["open_auditable_backend"]
        and row["validation_authority_after_future_protocol_audit"]
        for row in candidate_rows
    )
    assert any(
        row["platform_family"] == "black_box_industry_demonstration_backend"
        and row["black_box_demonstration_only"]
        and not row["selected_in_m2607"]
        for row in candidate_rows
    )
    assert any(
        row["platform_family"] == "repo_local_current_sim_backend"
        and row["repo_local_diagnostic_only"]
        and not row["selected_in_m2607"]
        for row in candidate_rows
    )
    assert {row["validation_execution_allowed_in_m2607"] for row in candidate_rows} == {False}

    assert len(dependency_rows) == 3
    assert set(dependency_rows[0]) == set(DEPENDENCY_EXECUTION_GUARD_FIELDNAMES)
    assert {row["external_install_allowed_in_m2607"] for row in dependency_rows} == {False}
    assert {row["external_import_allowed_in_m2607"] for row in dependency_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2607"] for row in dependency_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2607"] for row in dependency_rows} == {False}

    assert len(admission_rows) == 2
    assert set(admission_rows[0]) == set(VALIDATION_ADMISSION_GUARD_FIELDNAMES)
    assert {row["route_role_id"] for row in admission_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["selected_platform_family"] for row in admission_rows} == {SELECTED_PLATFORM_FAMILY}
    assert {row["actor_observation_shape"] for row in admission_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in admission_rows} == {ACTION_DIM}
    assert {row["platform_selection_decision_made_in_m2607"] for row in admission_rows} == {True}
    assert {row["reset_feasibility_evidence_required_later"] for row in admission_rows} == {True}
    assert {row["rollout_feasibility_evidence_required_later"] for row in admission_rows} == {True}
    assert {row["executable_protocol_required_later"] for row in admission_rows} == {True}
    assert {row["holdout_or_generalization_policy_required_later"] for row in admission_rows} == {True}
    assert {row["validation_protocol_ready_in_m2607"] for row in admission_rows} == {False}
    assert {row["validation_admission_granted_in_m2607"] for row in admission_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2607"] for row in admission_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in admission_rows} == {False}

    assert len(guard_rows) == 2
    assert set(guard_rows[0]) == set(ACTOR_ACTION_GUARD_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in guard_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in guard_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in guard_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in guard_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in guard_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in guard_rows} == {False}
    assert {row["reset_outcome_actor_visible"] for row in guard_rows} == {False}
    assert {row["rollout_outcome_actor_visible"] for row in guard_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in guard_rows} == {False}
    assert {row["platform_selection_actor_visible"] for row in guard_rows} == {False}
    assert {row["platform_selection_criteria_actor_visible"] for row in guard_rows} == {False}
    assert {row["platform_selection_decision_actor_visible"] for row in guard_rows} == {False}
    assert {row["selected_platform_actor_visible"] for row in guard_rows} == {False}
    assert {row["protocol_status_actor_visible"] for row in guard_rows} == {False}
    assert {row["action_contract_mutation_detected"] for row in guard_rows} == {False}

    assert len(claim_rows) == 17
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2607"]
    } == {
        "after_closure_platform_selection_decision_result_materialized",
        "bounded_open_auditable_platform_family_selected",
    }


def test_materialize_route_a_hf3_after_closure_platform_selection_decision_result_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2607.md"

    summary = materialize_route_a_hf3_after_closure_platform_selection_decision_result(
        output_dir,
        milestone="m2607-test",
        next_blocker="m2608-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result_materialization_preflight_pass"
    )
    assert summary["decision_result_row_count"] == 1
    assert summary["decision_evidence_row_count"] == 12
    assert summary["candidate_disposition_row_count"] == 3
    assert summary["dependency_execution_guard_row_count"] == 3
    assert summary["validation_admission_guard_row_count"] == 2
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 17
    assert summary["materialization_gate_count"] == 12
    assert summary["platform_selection_decision_result_materialized_in_m2607"] is True
    assert summary["after_closure_platform_selection_decision_result_materialized_claim_allowed"] is True
    assert summary["bounded_open_auditable_platform_family_selected_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2607"] is False
    assert summary["m2604_status_pass"] is True
    assert summary["m2604_decision_design_materialized"] is True
    assert summary["m2604_platform_selected"] is False
    assert summary["m2604_selection_decision_made"] is False
    assert summary["m2604_selected_platform_family"] == "none"
    assert summary["platform_selection_decision_made_in_m2607"] is True
    assert summary["selected_platform_family_in_m2607"] == SELECTED_PLATFORM_FAMILY
    assert summary["selected_platform_family_is_open_auditable"] is True
    assert summary["black_box_backend_selected_in_m2607"] is False
    assert summary["repo_local_current_sim_selected_in_m2607"] is False
    assert summary["external_install_allowed_in_m2607"] is False
    assert summary["external_import_allowed_in_m2607"] is False
    assert summary["runtime_execution_allowed_in_m2607"] is False
    assert summary["dependency_mutation_allowed_in_m2607"] is False
    assert summary["validation_protocol_ready_in_m2607"] is False
    assert summary["validation_admission_granted_in_m2607"] is False
    assert summary["external_validation_execution_allowed_in_m2607"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["driver_performance_claim_allowed_in_m2607"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["platform_selection_actor_visible"] is False
    assert summary["platform_selection_criteria_actor_visible"] is False
    assert summary["platform_selection_decision_actor_visible"] is False
    assert summary["selected_platform_actor_visible"] is False
    assert summary["protocol_status_actor_visible"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    decision_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_decision_result_rows.csv")
    evidence_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_decision_evidence_rows.csv")
    candidate_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_candidate_disposition_rows.csv")
    dependency_rows = _read_csv(
        output_dir / "hf3_after_closure_platform_selection_dependency_execution_guard_rows.csv"
    )
    admission_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_validation_admission_guard_rows.csv")
    guard_rows = _read_csv(
        output_dir / "hf3_after_closure_platform_selection_decision_result_actor_action_guard_rows.csv"
    )
    claim_rows = _read_csv(
        output_dir / "hf3_after_closure_platform_selection_decision_result_claim_boundary_checks.csv"
    )
    gate_rows = _read_csv(output_dir / "after_closure_platform_selection_decision_result_gate_matrix.csv")

    assert len(decision_rows) == 1
    assert len(evidence_rows) == 12
    assert len(candidate_rows) == 3
    assert len(dependency_rows) == 3
    assert len(admission_rows) == 2
    assert len(guard_rows) == 2
    assert len(claim_rows) == 17
    assert len(gate_rows) == 12
    assert {row["selected_platform_family"] for row in decision_rows} == {SELECTED_PLATFORM_FAMILY}
    assert {row["open_auditable_backend_selected"] for row in decision_rows} == {"True"}
    assert {row["black_box_backend_selected"] for row in decision_rows} == {"False"}
    assert {row["repo_local_current_sim_selected"] for row in decision_rows} == {"False"}
    assert {row["admitted_for_platform_selection_decision_in_m2607"] for row in evidence_rows} == {"True"}
    assert {row["admitted_for_validation_readiness_in_m2607"] for row in evidence_rows} == {"False"}
    assert {row["admitted_for_driver_performance_in_m2607"] for row in evidence_rows} == {"False"}
    assert [
        row["platform_family"] for row in candidate_rows if row["selected_in_m2607"] == "True"
    ] == [SELECTED_PLATFORM_FAMILY]
    assert {row["validation_execution_allowed_in_m2607"] for row in candidate_rows} == {"False"}
    assert {row["external_install_allowed_in_m2607"] for row in dependency_rows} == {"False"}
    assert {row["external_import_allowed_in_m2607"] for row in dependency_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2607"] for row in dependency_rows} == {"False"}
    assert {row["dependency_mutation_allowed_in_m2607"] for row in dependency_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2607"] for row in admission_rows} == {"False"}
    assert {row["validation_admission_granted_in_m2607"] for row in admission_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2607"] for row in admission_rows} == {"False"}
    assert {row["validation_result_claim_allowed"] for row in admission_rows} == {"False"}
    assert {row["platform_selection_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["platform_selection_criteria_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["platform_selection_decision_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["selected_platform_actor_visible"] for row in guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2607"] == "True"
    } == {
        "after_closure_platform_selection_decision_result_materialized",
        "bounded_open_auditable_platform_family_selected",
    }
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
