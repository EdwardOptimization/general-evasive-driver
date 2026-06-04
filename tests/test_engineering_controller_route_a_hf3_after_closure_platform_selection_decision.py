import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_after_closure_platform_selection_decision import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    CANDIDATE_COMPARISON_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DECISION_REQUEST_FIELDNAMES,
    DEPENDENCY_GUARD_FIELDNAMES,
    EVIDENCE_ADMISSION_FIELDNAMES,
    VALIDATION_ROLE_FIELDNAMES,
    build_actor_action_guard_rows,
    build_candidate_comparison_rows,
    build_claim_boundary_checks,
    build_decision_request_rows,
    build_dependency_guard_rows,
    build_evidence_admission_rows,
    build_validation_role_compatibility_rows,
    materialize_route_a_hf3_after_closure_platform_selection_decision,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2600_summary():
    return read_json(
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/summary.json"
    )


def test_build_hf3_after_closure_platform_selection_decision_rows_preserve_boundaries():
    summary = _m2600_summary()
    decision_rows = build_decision_request_rows(summary)
    evidence_rows = build_evidence_admission_rows(m2600_summary=summary)
    candidate_rows = build_candidate_comparison_rows(decision_rows, evidence_rows)
    dependency_rows = build_dependency_guard_rows()
    compatibility_rows = build_validation_role_compatibility_rows(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
    )
    guard_rows = build_actor_action_guard_rows(compatibility_rows)
    claim_rows = build_claim_boundary_checks(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
        compatibility_rows,
        guard_rows,
    )

    assert len(decision_rows) == 2
    assert set(decision_rows[0]) == set(DECISION_REQUEST_FIELDNAMES)
    assert {row["decision_request_id"] for row in decision_rows} == {
        "preferred_open_auditable_backend_decision_request",
        "demonstration_and_diagnostic_exclusion_request",
    }
    assert {row["criteria_materialization_accepted_before_request"] for row in decision_rows} == {True}
    assert {row["actual_selection_allowed_in_m2604"] for row in decision_rows} == {False}
    assert {row["selection_decision_made_in_m2604"] for row in decision_rows} == {False}
    assert {row["selected_platform_family_in_m2604"] for row in decision_rows} == {"none"}

    assert len(evidence_rows) == 8
    assert set(evidence_rows[0]) == set(EVIDENCE_ADMISSION_FIELDNAMES)
    assert {row["admitted_for_decision_design_in_m2604"] for row in evidence_rows} == {True}
    assert {row["admitted_for_actual_selection_in_m2604"] for row in evidence_rows} == {False}
    assert {row["admitted_for_validation_readiness_in_m2604"] for row in evidence_rows} == {False}

    assert len(candidate_rows) == 3
    assert set(candidate_rows[0]) == set(CANDIDATE_COMPARISON_FIELDNAMES)
    assert {row["platform_family"] for row in candidate_rows} == {
        "chrono_vehicle_or_equivalent_open_backend",
        "black_box_industry_demonstration_backend",
        "repo_local_current_sim_backend",
    }
    assert any(
        row["platform_family"] == "chrono_vehicle_or_equivalent_open_backend"
        and row["open_auditable_backend_preferred"]
        and row["eligible_for_future_selection_after_audit"]
        for row in candidate_rows
    )
    assert any(
        row["platform_family"] == "black_box_industry_demonstration_backend"
        and row["black_box_demonstration_only"]
        for row in candidate_rows
    )
    assert any(
        row["platform_family"] == "repo_local_current_sim_backend"
        and row["repo_local_diagnostic_only"]
        for row in candidate_rows
    )
    assert {row["selected_in_m2604"] for row in candidate_rows} == {False}

    assert len(dependency_rows) == 3
    assert set(dependency_rows[0]) == set(DEPENDENCY_GUARD_FIELDNAMES)
    assert {row["external_install_allowed_in_m2604"] for row in dependency_rows} == {False}
    assert {row["external_import_allowed_in_m2604"] for row in dependency_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2604"] for row in dependency_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2604"] for row in dependency_rows} == {False}

    assert len(compatibility_rows) == 2
    assert set(compatibility_rows[0]) == set(VALIDATION_ROLE_FIELDNAMES)
    assert {row["route_role_id"] for row in compatibility_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in compatibility_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in compatibility_rows} == {ACTION_DIM}
    assert {row["decision_design_materialized_in_m2604"] for row in compatibility_rows} == {True}
    assert {row["reset_feasibility_evidence_required_later"] for row in compatibility_rows} == {True}
    assert {row["rollout_feasibility_evidence_required_later"] for row in compatibility_rows} == {True}
    assert {row["holdout_or_generalization_policy_required_later"] for row in compatibility_rows} == {True}
    assert {row["external_validation_execution_allowed_in_m2604"] for row in compatibility_rows} == {False}
    assert {row["validation_protocol_ready_in_m2604"] for row in compatibility_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in compatibility_rows} == {False}

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
    assert {row["protocol_status_actor_visible"] for row in guard_rows} == {False}
    assert {row["action_contract_mutation_detected"] for row in guard_rows} == {False}

    assert len(claim_rows) == 19
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2604"]
    } == {"after_closure_platform_selection_decision_design_materialized"}


def test_materialize_route_a_hf3_after_closure_platform_selection_decision_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2604.md"

    summary = materialize_route_a_hf3_after_closure_platform_selection_decision(
        output_dir,
        milestone="m2604-test",
        next_blocker="m2605-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_after_closure_platform_selection_decision_materialization_preflight_pass"
    )
    assert summary["decision_request_row_count"] == 2
    assert summary["evidence_admission_row_count"] == 8
    assert summary["candidate_comparison_row_count"] == 3
    assert summary["dependency_guard_row_count"] == 3
    assert summary["validation_role_compatibility_row_count"] == 2
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 19
    assert summary["materialization_gate_count"] == 12
    assert summary["platform_selection_decision_design_materialized_in_m2604"] is True
    assert summary["after_closure_platform_selection_decision_design_materialized_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2604"] is False
    assert summary["m2600_status_pass"] is True
    assert summary["m2600_platform_selection_criteria_materialized"] is True
    assert summary["m2600_platform_selected"] is False
    assert summary["m2600_selection_decision_allowed"] is False
    assert summary["m2600_validation_protocol_ready"] is False
    assert summary["m2600_external_validation_execution_allowed"] is False
    assert summary["platform_selected_in_m2604"] is False
    assert summary["selection_decision_made_in_m2604"] is False
    assert summary["selected_platform_family_in_m2604"] == "none"
    assert summary["external_install_allowed_in_m2604"] is False
    assert summary["external_import_allowed_in_m2604"] is False
    assert summary["runtime_execution_allowed_in_m2604"] is False
    assert summary["dependency_mutation_allowed_in_m2604"] is False
    assert summary["validation_protocol_ready_in_m2604"] is False
    assert summary["validation_admission_granted_in_m2604"] is False
    assert summary["external_validation_execution_allowed_in_m2604"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["driver_performance_claim_allowed_in_m2604"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["platform_selection_actor_visible"] is False
    assert summary["platform_selection_criteria_actor_visible"] is False
    assert summary["platform_selection_decision_actor_visible"] is False
    assert summary["protocol_status_actor_visible"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    decision_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_decision_request_rows.csv")
    evidence_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_evidence_admission_rows.csv")
    candidate_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_candidate_comparison_rows.csv")
    dependency_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_dependency_guard_rows.csv")
    compatibility_rows = _read_csv(
        output_dir / "hf3_after_closure_platform_selection_validation_role_compatibility_rows.csv"
    )
    guard_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_decision_actor_action_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_after_closure_platform_selection_decision_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "after_closure_platform_selection_decision_gate_matrix.csv")

    assert len(decision_rows) == 2
    assert len(evidence_rows) == 8
    assert len(candidate_rows) == 3
    assert len(dependency_rows) == 3
    assert len(compatibility_rows) == 2
    assert len(guard_rows) == 2
    assert len(claim_rows) == 19
    assert len(gate_rows) == 12
    assert {row["actual_selection_allowed_in_m2604"] for row in decision_rows} == {"False"}
    assert {row["selection_decision_made_in_m2604"] for row in decision_rows} == {"False"}
    assert {row["selected_platform_family_in_m2604"] for row in decision_rows} == {"none"}
    assert {row["admitted_for_actual_selection_in_m2604"] for row in evidence_rows} == {"False"}
    assert {row["admitted_for_validation_readiness_in_m2604"] for row in evidence_rows} == {"False"}
    assert {row["selected_in_m2604"] for row in candidate_rows} == {"False"}
    assert {row["external_install_allowed_in_m2604"] for row in dependency_rows} == {"False"}
    assert {row["external_import_allowed_in_m2604"] for row in dependency_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2604"] for row in dependency_rows} == {"False"}
    assert {row["dependency_mutation_allowed_in_m2604"] for row in dependency_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2604"] for row in compatibility_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2604"] for row in compatibility_rows} == {"False"}
    assert {row["validation_result_claim_allowed"] for row in compatibility_rows} == {"False"}
    assert {row["platform_selection_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["platform_selection_criteria_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["platform_selection_decision_actor_visible"] for row in guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2604"] == "True"
    } == {"after_closure_platform_selection_decision_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
