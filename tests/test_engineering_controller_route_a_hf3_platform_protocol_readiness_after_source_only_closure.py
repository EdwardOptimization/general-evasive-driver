import csv

from autodrift.engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPENDENCY_IMPORT_POLICY_FIELDNAMES,
    PLATFORM_CANDIDATE_FIELDNAMES,
    SOURCE_ONLY_CLOSURE_EVIDENCE_FIELDNAMES,
    VALIDATION_PROTOCOL_SKELETON_FIELDNAMES,
    build_actor_action_guard_rows,
    build_claim_boundary_checks,
    build_dependency_import_policy_rows,
    build_platform_candidate_rows,
    build_source_only_closure_evidence_rows,
    build_validation_protocol_skeleton_rows,
    materialize_route_a_hf3_platform_protocol_readiness_after_source_only_closure,
)
from autodrift.artifacts import read_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2592_summary():
    return read_json(
        "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/summary.json"
    )


def test_build_hf3_after_closure_platform_protocol_rows_preserve_boundaries():
    summary = _m2592_summary()
    platform_rows = build_platform_candidate_rows(summary)
    dependency_rows = build_dependency_import_policy_rows(summary)
    protocol_rows = build_validation_protocol_skeleton_rows(summary)
    closure_rows = build_source_only_closure_evidence_rows(summary)
    guard_rows = build_actor_action_guard_rows(protocol_rows)
    claim_rows = build_claim_boundary_checks(
        platform_rows,
        dependency_rows,
        protocol_rows,
        closure_rows,
        guard_rows,
    )

    assert len(platform_rows) == 3
    assert set(platform_rows[0]) == set(PLATFORM_CANDIDATE_FIELDNAMES)
    assert {row["platform_family"] for row in platform_rows} == {
        "chrono_vehicle_or_equivalent_open_backend",
        "black_box_industry_demonstration_backend",
        "repo_local_current_sim_backend",
    }
    assert {row["source_only_closure_required_before_selection"] for row in platform_rows} == {True}
    assert {row["source_only_closure_accepted_in_m2596"] for row in platform_rows} == {True}
    assert {row["selected_for_validation_in_m2596"] for row in platform_rows} == {False}
    assert {row["install_allowed_in_m2596"] for row in platform_rows} == {False}
    assert {row["import_allowed_in_m2596"] for row in platform_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2596"] for row in platform_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2596"] for row in platform_rows} == {False}

    assert len(dependency_rows) == 3
    assert set(dependency_rows[0]) == set(DEPENDENCY_IMPORT_POLICY_FIELDNAMES)
    assert {row["source_only_closure_accepted_in_m2596"] for row in dependency_rows} == {True}
    assert {row["external_install_allowed_in_m2596"] for row in dependency_rows} == {False}
    assert {row["external_import_allowed_in_m2596"] for row in dependency_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2596"] for row in dependency_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2596"] for row in dependency_rows} == {False}

    assert len(protocol_rows) == 2
    assert set(protocol_rows[0]) == set(VALIDATION_PROTOCOL_SKELETON_FIELDNAMES)
    assert {row["route_role_id"] for row in protocol_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in protocol_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in protocol_rows} == {ACTION_DIM}
    assert {row["source_only_closure_accepted_in_m2596"] for row in protocol_rows} == {True}
    assert {row["protocol_skeleton_defined"] for row in protocol_rows} == {True}
    assert {row["holdout_or_generalization_policy_defined"] for row in protocol_rows} == {False}
    assert {row["reset_allowed_in_m2596"] for row in protocol_rows} == {False}
    assert {row["policy_action_allowed_in_m2596"] for row in protocol_rows} == {False}
    assert {row["environment_step_allowed_in_m2596"] for row in protocol_rows} == {False}
    assert {row["rollout_allowed_in_m2596"] for row in protocol_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2596"] for row in protocol_rows} == {False}
    assert {row["validation_protocol_ready_in_m2596"] for row in protocol_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in protocol_rows} == {False}

    assert len(closure_rows) == 4
    assert set(closure_rows[0]) == set(SOURCE_ONLY_CLOSURE_EVIDENCE_FIELDNAMES)
    assert {row["closure_family"] for row in closure_rows} == {
        "external_state_extraction_boundary",
        "time_step_and_actuator_latency_contract",
        "failure_status_taxonomy_mapping",
        "source_only_fixture_smoke_lineage",
    }
    assert {row["closure_materialized_in_m2592"] for row in closure_rows} == {True}
    assert {row["closure_audited_in_m2593"] for row in closure_rows} == {True}
    assert {row["accepted_by_m2594_synthesis"] for row in closure_rows} == {True}
    assert {row["missing_after_source_only_closure"] for row in closure_rows} == {False}

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
    assert {row["protocol_status_actor_visible"] for row in guard_rows} == {False}
    assert {row["action_contract_mutation_detected"] for row in guard_rows} == {False}

    assert len(claim_rows) == 14
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2596"]
    } == {"after_closure_platform_protocol_readiness_design_materialized"}


def test_materialize_route_a_hf3_after_closure_platform_protocol_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2596.md"

    summary = materialize_route_a_hf3_platform_protocol_readiness_after_source_only_closure(
        output_dir,
        milestone="m2596-test",
        next_blocker="m2597-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure_materialization_preflight_pass"
    )
    assert summary["platform_candidate_row_count"] == 3
    assert summary["dependency_import_policy_row_count"] == 3
    assert summary["validation_protocol_skeleton_row_count"] == 2
    assert summary["source_only_closure_evidence_row_count"] == 4
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 14
    assert summary["materialization_gate_count"] == 12
    assert summary["after_closure_platform_protocol_readiness_design_materialized_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2596"] is False
    assert summary["source_only_closure_accepted_in_m2596"] is True
    assert summary["source_only_closure_missing_after_m2596"] is False
    assert summary["selected_for_validation_in_m2596"] is False
    assert summary["platform_selected_in_m2596"] is False
    assert summary["install_allowed_in_m2596"] is False
    assert summary["import_allowed_in_m2596"] is False
    assert summary["runtime_execution_allowed_in_m2596"] is False
    assert summary["external_install_allowed_in_m2596"] is False
    assert summary["external_import_allowed_in_m2596"] is False
    assert summary["dependency_runtime_execution_allowed_in_m2596"] is False
    assert summary["dependency_mutation_allowed_in_m2596"] is False
    assert summary["protocol_skeleton_defined"] is True
    assert summary["holdout_or_generalization_policy_defined"] is False
    assert summary["reset_allowed_in_m2596"] is False
    assert summary["policy_action_allowed_in_m2596"] is False
    assert summary["environment_step_allowed_in_m2596"] is False
    assert summary["rollout_allowed_in_m2596"] is False
    assert summary["external_validation_execution_allowed_in_m2596"] is False
    assert summary["validation_protocol_ready_in_m2596"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["validation_protocol_ready_claim_allowed"] is False
    assert summary["validation_admission_granted_in_m2596"] is False
    assert summary["driver_performance_claim_allowed_in_m2596"] is False
    assert summary["platform_selection_actor_visible"] is False
    assert summary["protocol_status_actor_visible"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    platform_rows = _read_csv(output_dir / "hf3_after_closure_platform_candidate_rows.csv")
    dependency_rows = _read_csv(output_dir / "hf3_after_closure_dependency_import_policy_rows.csv")
    protocol_rows = _read_csv(output_dir / "hf3_after_closure_validation_protocol_skeleton_rows.csv")
    closure_rows = _read_csv(output_dir / "hf3_after_closure_source_only_evidence_rows.csv")
    guard_rows = _read_csv(output_dir / "hf3_after_closure_actor_action_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_after_closure_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "after_closure_platform_protocol_readiness_gate_matrix.csv")

    assert len(platform_rows) == 3
    assert len(dependency_rows) == 3
    assert len(protocol_rows) == 2
    assert len(closure_rows) == 4
    assert len(guard_rows) == 2
    assert len(claim_rows) == 14
    assert len(gate_rows) == 12
    assert {row["selected_for_validation_in_m2596"] for row in platform_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2596"] for row in platform_rows} == {"False"}
    assert {row["external_install_allowed_in_m2596"] for row in dependency_rows} == {"False"}
    assert {row["external_import_allowed_in_m2596"] for row in dependency_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2596"] for row in dependency_rows} == {"False"}
    assert {row["protocol_skeleton_defined"] for row in protocol_rows} == {"True"}
    assert {row["holdout_or_generalization_policy_defined"] for row in protocol_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2596"] for row in protocol_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2596"] for row in protocol_rows} == {"False"}
    assert {row["missing_after_source_only_closure"] for row in closure_rows} == {"False"}
    assert {row["platform_selection_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["protocol_status_actor_visible"] for row in guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2596"] == "True"
    } == {"after_closure_platform_protocol_readiness_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
