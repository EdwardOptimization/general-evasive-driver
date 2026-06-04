import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    ACTOR_VIEW_AFTER_RESET_EXTRACTION_FIELDNAMES,
    BACKEND_AVAILABILITY_FIXTURE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPLOYED_ACTION_MAPPING,
    GATE_FIELDNAMES,
    RESET_INVOCATION_DRY_RUN_CONTRACT_FIELDNAMES,
    RESET_OUTCOME_AUDIT_SCHEMA_FIELDNAMES,
    RESET_REQUEST_BINDING_FIELDNAMES,
    SELECTED_PLATFORM_FAMILY,
    SOURCE_BUILD_ADAPTER_PROBE_EVIDENCE_ADMISSION_FIELDNAMES,
    build_actor_action_guard_rows,
    build_actor_view_after_reset_extraction_rows,
    build_backend_availability_fixture_rows,
    build_claim_boundary_checks,
    build_gate_matrix_rows,
    build_reset_invocation_dry_run_contract_rows,
    build_reset_outcome_audit_schema_rows,
    build_reset_request_binding_rows,
    build_source_build_adapter_probe_evidence_admission_rows,
    materialize_route_a_hf3_selected_platform_reset_execution_readiness,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2619_summary():
    return read_json(
        "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/"
        "summary.json"
    )


def _build_rows():
    summary = _m2619_summary()
    evidence_rows = build_source_build_adapter_probe_evidence_admission_rows(summary)
    backend_rows = build_backend_availability_fixture_rows(evidence_rows)
    dry_run_rows = build_reset_invocation_dry_run_contract_rows(backend_rows)
    binding_rows = build_reset_request_binding_rows(dry_run_rows)
    actor_view_rows = build_actor_view_after_reset_extraction_rows(binding_rows)
    outcome_rows = build_reset_outcome_audit_schema_rows()
    actor_action_guard_rows = build_actor_action_guard_rows(actor_view_rows)
    claim_rows = build_claim_boundary_checks(
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists={"present": True},
        m2619_summary=summary,
        evidence_rows=evidence_rows,
        backend_rows=backend_rows,
        dry_run_rows=dry_run_rows,
        binding_rows=binding_rows,
        actor_view_rows=actor_view_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )
    return (
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    )


def test_build_hf3_selected_platform_reset_execution_readiness_rows_preserve_boundaries():
    (
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    ) = _build_rows()

    assert len(evidence_rows) == 4
    assert set(evidence_rows[0]) == set(SOURCE_BUILD_ADAPTER_PROBE_EVIDENCE_ADMISSION_FIELDNAMES)
    assert {row["evidence_admission_id"] for row in evidence_rows} == {
        "source_build_log_admission",
        "adapter_probe_trace_admission",
        "dependency_mutation_guard_admission",
        "source_equivalence_trace_admission",
    }
    assert {row["selected_platform_family"] for row in evidence_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["required_before_reset_execution"] for row in evidence_rows} == {True}
    assert {row["materialized_in_m2623"] for row in evidence_rows} == {True}
    assert {row["execution_allowed_in_m2623"] for row in evidence_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2623"] for row in evidence_rows} == {False}
    assert {row["actor_visible_allowed"] for row in evidence_rows} == {False}

    assert len(backend_rows) == 2
    assert set(backend_rows[0]) == set(BACKEND_AVAILABILITY_FIXTURE_FIELDNAMES)
    assert {row["route_role_id"] for row in backend_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["backend_availability_required_before_reset"] for row in backend_rows} == {
        True
    }
    assert {row["fixture_schema_materialized_in_m2623"] for row in backend_rows} == {True}
    assert {row["backend_started_in_m2623"] for row in backend_rows} == {False}
    assert {row["backend_reset_called_in_m2623"] for row in backend_rows} == {False}
    assert {row["actor_visible_allowed"] for row in backend_rows} == {False}

    assert len(dry_run_rows) == 2
    assert set(dry_run_rows[0]) == set(RESET_INVOCATION_DRY_RUN_CONTRACT_FIELDNAMES)
    assert {row["initial_state_binding_required"] for row in dry_run_rows} == {True}
    assert {row["deterministic_seed_required"] for row in dry_run_rows} == {True}
    assert {row["actor_view_required_after_reset"] for row in dry_run_rows} == {True}
    assert {row["source_build_required_before_execution"] for row in dry_run_rows} == {True}
    assert {row["adapter_probe_required_before_execution"] for row in dry_run_rows} == {True}
    assert {row["backend_availability_required_before_execution"] for row in dry_run_rows} == {
        True
    }
    assert {row["reset_invocation_contract_materialized_in_m2623"] for row in dry_run_rows} == {
        True
    }
    assert {row["reset_executed_in_m2623"] for row in dry_run_rows} == {False}

    assert len(binding_rows) == 2
    assert set(binding_rows[0]) == set(RESET_REQUEST_BINDING_FIELDNAMES)
    assert {row["reset_request_schema_id"] for row in binding_rows} == {
        "stable_avoidable_aeb_feasible_reset_request_schema",
        "stable_aes_aeb_infeasible_reset_request_schema",
    }
    assert {row["initial_state_admission_id"] for row in binding_rows} == {
        "stable_avoidable_aeb_feasible_initial_state_admission",
        "stable_aes_aeb_infeasible_initial_state_admission",
    }
    assert {row["seed_lineage_id"] for row in binding_rows} == {
        "stable_avoidable_aeb_feasible_reset_seed_lineage",
        "stable_aes_aeb_infeasible_reset_seed_lineage",
    }
    assert {row["binding_materialized_in_m2623"] for row in binding_rows} == {True}
    assert {row["reset_executed_in_m2623"] for row in binding_rows} == {False}
    assert {row["replay_executed_in_m2623"] for row in binding_rows} == {False}
    assert {row["actor_visible_allowed"] for row in binding_rows} == {False}

    assert len(actor_view_rows) == 2
    assert set(actor_view_rows[0]) == set(ACTOR_VIEW_AFTER_RESET_EXTRACTION_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_view_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_view_rows} == {ACTION_DIM}
    assert {row["deployed_action_mapping"] for row in actor_view_rows} == {
        DEPLOYED_ACTION_MAPPING
    }
    assert {row["ego_kinematics_included"] for row in actor_view_rows} == {True}
    assert {row["actuator_state_included"] for row in actor_view_rows} == {True}
    assert {row["previous_command_included"] for row in actor_view_rows} == {True}
    assert {row["road_geometry_included"] for row in actor_view_rows} == {True}
    assert {row["obstacle_geometry_included"] for row in actor_view_rows} == {True}
    assert {
        row["after_reset_extractor_contract_materialized_in_m2623"]
        for row in actor_view_rows
    } == {True}
    for column in [
        "hidden_oracle_actor_input_detected",
        "diagnostics_actor_visible",
        "taxonomy_label_actor_visible",
        "backend_status_actor_visible",
        "reset_outcome_actor_visible",
        "validation_outcome_actor_visible",
        "selected_platform_actor_visible",
        "protocol_status_actor_visible",
    ]:
        assert {row[column] for row in actor_view_rows} == {False}

    assert len(outcome_rows) == 10
    assert set(outcome_rows[0]) == set(RESET_OUTCOME_AUDIT_SCHEMA_FIELDNAMES)
    assert {row["outcome_field"] for row in outcome_rows} == {
        "backend_available",
        "source_build_artifact",
        "adapter_probe_trace",
        "reset_request_valid",
        "reset_attempted",
        "reset_status",
        "actor_view_available",
        "diagnostics_available",
        "failure_reason",
        "execution_timestamp",
    }
    assert {row["required_for_future_reset_execution_audit"] for row in outcome_rows} == {
        True
    }
    assert {row["actor_visible_allowed"] for row in outcome_rows} == {False}
    assert {row["materialized_in_m2623"] for row in outcome_rows} == {True}
    assert {row["allowed_to_support_reset_success_after_execution"] for row in outcome_rows} == {
        True
    }
    assert {
        row["allowed_to_support_rollout_feasibility_after_execution"]
        for row in outcome_rows
    } == {True}
    assert {row["allowed_to_support_validation_after_execution"] for row in outcome_rows} == {
        True
    }

    assert len(actor_action_guard_rows) == 2
    assert set(actor_action_guard_rows[0]) == set(ACTOR_ACTION_GUARD_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_action_guard_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_action_guard_rows} == {ACTION_DIM}
    assert {row["deployed_action_mapping"] for row in actor_action_guard_rows} == {
        DEPLOYED_ACTION_MAPPING
    }
    assert {row["actor_input_mutation_detected"] for row in actor_action_guard_rows} == {
        False
    }
    assert {row["action_contract_mutation_detected"] for row in actor_action_guard_rows} == {
        False
    }
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_action_guard_rows} == {
        False
    }
    assert {row["metadata_actor_visible"] for row in actor_action_guard_rows} == {False}

    assert len(claim_rows) == 27
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2623"]
    } == {"selected_platform_reset_execution_readiness_design_materialized"}

    assert len(gate_rows) == 13
    assert set(gate_rows[0]) == set(GATE_FIELDNAMES)
    assert {row["status_pass"] for row in gate_rows} == {True}


def test_build_gate_matrix_catches_missing_source_artifacts():
    (
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
        claim_rows,
        _,
    ) = _build_rows()

    gate_rows = build_gate_matrix_rows(
        source_exists={"missing": False},
        m2619_summary=_m2619_summary(),
        evidence_rows=evidence_rows,
        backend_rows=backend_rows,
        dry_run_rows=dry_run_rows,
        binding_rows=binding_rows,
        actor_view_rows=actor_view_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )

    source_gate = next(row for row in gate_rows if row["gate_id"] == "source_artifacts_exist")
    assert source_gate["status_pass"] is False
    assert source_gate["failure_type"] == "lineage_invalid"


def test_materialize_hf3_selected_platform_reset_execution_readiness_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2623.md"

    summary = materialize_route_a_hf3_selected_platform_reset_execution_readiness(
        output_dir,
        milestone="m2623-test",
        next_blocker="m2624-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness_materialization_preflight_pass"
    )
    assert summary["source_build_adapter_probe_evidence_admission_row_count"] == 4
    assert summary["backend_availability_fixture_row_count"] == 2
    assert summary["reset_invocation_dry_run_contract_row_count"] == 2
    assert summary["reset_request_binding_row_count"] == 2
    assert summary["actor_view_after_reset_extraction_row_count"] == 2
    assert summary["reset_outcome_audit_schema_row_count"] == 10
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 27
    assert summary["materialization_gate_count"] == 13
    assert summary["source_artifacts_exist"] is True
    assert summary["m2619_status_pass"] is True
    assert summary["m2619_materialization_gates_all_pass"] is True
    assert summary["m2619_selected_platform_family"] == SELECTED_PLATFORM_FAMILY
    assert summary["m2619_reset_executed"] is False
    assert summary["m2619_validation_protocol_ready"] is False
    assert summary["m2619_validation_admission_granted"] is False
    assert summary["m2619_validation_result_claim_allowed"] is False
    assert summary["m2619_reset_success_claim_allowed"] is False
    assert summary["m2619_rollout_feasibility_claim_allowed"] is False
    assert summary["m2619_driver_performance_claim_allowed"] is False
    assert (
        summary["selected_platform_reset_execution_readiness_design_materialized_in_m2623"]
        is True
    )
    assert summary["selected_platform_family_in_m2623"] == SELECTED_PLATFORM_FAMILY
    assert (
        summary["source_build_adapter_probe_evidence_admission_materialized_in_m2623"]
        is True
    )
    assert summary["backend_availability_fixture_materialized_in_m2623"] is True
    assert summary["reset_invocation_dry_run_contract_materialized_in_m2623"] is True
    assert summary["reset_request_binding_materialized_in_m2623"] is True
    assert summary["actor_view_after_reset_extraction_materialized_in_m2623"] is True
    assert summary["reset_outcome_audit_schema_materialized_in_m2623"] is True
    assert summary["forbidden_claim_allowed_in_m2623"] is False
    assert summary["external_install_allowed_in_m2623"] is False
    assert summary["external_import_allowed_in_m2623"] is False
    assert summary["runtime_execution_allowed_in_m2623"] is False
    assert summary["dependency_mutation_allowed_in_m2623"] is False
    assert summary["source_build_executed_in_m2623"] is False
    assert summary["adapter_probe_executed_in_m2623"] is False
    assert summary["reset_executed_in_m2623"] is False
    assert summary["environment_step_executed_in_m2623"] is False
    assert summary["policy_action_executed_in_m2623"] is False
    assert summary["rollout_executed_in_m2623"] is False
    assert summary["replay_executed_in_m2623"] is False
    assert summary["external_validation_execution_allowed_in_m2623"] is False
    assert summary["validation_protocol_ready_in_m2623"] is False
    assert summary["validation_admission_granted_in_m2623"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["reset_success_claim_allowed_in_m2623"] is False
    assert summary["rollout_feasibility_claim_allowed_in_m2623"] is False
    assert summary["driver_performance_claim_allowed_in_m2623"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["diagnostics_actor_visible"] is False
    assert summary["taxonomy_label_actor_visible"] is False
    assert summary["backend_status_actor_visible"] is False
    assert summary["reset_outcome_actor_visible"] is False
    assert summary["validation_outcome_actor_visible"] is False
    assert summary["selected_platform_actor_visible"] is False
    assert summary["protocol_status_actor_visible"] is False
    assert summary["metadata_actor_visible"] is False
    assert summary["actor_input_mutation_detected"] is False
    assert summary["action_contract_mutation_detected"] is False
    assert summary["source_build_run"] is False
    assert summary["adapter_probe_run"] is False
    assert summary["reset_execution_run"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    evidence_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows.csv"
    )
    backend_rows = _read_csv(output_dir / "hf3_selected_platform_backend_availability_fixture_rows.csv")
    dry_run_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_invocation_dry_run_contract_rows.csv"
    )
    binding_rows = _read_csv(output_dir / "hf3_selected_platform_reset_request_binding_rows.csv")
    actor_view_rows = _read_csv(
        output_dir / "hf3_selected_platform_actor_view_after_reset_extraction_rows.csv"
    )
    outcome_rows = _read_csv(output_dir / "hf3_selected_platform_reset_outcome_audit_schema_rows.csv")
    actor_action_guard_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_execution_actor_action_guard_rows.csv"
    )
    claim_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_execution_readiness_claim_boundary_checks.csv"
    )
    gate_rows = _read_csv(
        output_dir / "selected_platform_reset_execution_readiness_gate_matrix.csv"
    )

    assert len(evidence_rows) == 4
    assert len(backend_rows) == 2
    assert len(dry_run_rows) == 2
    assert len(binding_rows) == 2
    assert len(actor_view_rows) == 2
    assert len(outcome_rows) == 10
    assert len(actor_action_guard_rows) == 2
    assert len(claim_rows) == 27
    assert len(gate_rows) == 13
    assert {row["execution_allowed_in_m2623"] for row in evidence_rows} == {"False"}
    assert {row["dependency_mutation_allowed_in_m2623"] for row in evidence_rows} == {
        "False"
    }
    assert {row["backend_started_in_m2623"] for row in backend_rows} == {"False"}
    assert {row["backend_reset_called_in_m2623"] for row in backend_rows} == {"False"}
    assert {row["reset_executed_in_m2623"] for row in dry_run_rows} == {"False"}
    assert {row["reset_executed_in_m2623"] for row in binding_rows} == {"False"}
    assert {row["replay_executed_in_m2623"] for row in binding_rows} == {"False"}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_view_rows} == {
        "False"
    }
    assert {row["actor_visible_allowed"] for row in outcome_rows} == {"False"}
    assert {row["metadata_actor_visible"] for row in actor_action_guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2623"] == "True"
    } == {"selected_platform_reset_execution_readiness_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
