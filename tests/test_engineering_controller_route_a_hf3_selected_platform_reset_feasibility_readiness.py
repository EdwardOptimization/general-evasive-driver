import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    ACTOR_VIEW_PARITY_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPLOYED_ACTION_MAPPING,
    GATE_FIELDNAMES,
    INITIAL_STATE_ADMISSION_FIELDNAMES,
    RESET_EXECUTION_PRECONDITION_FIELDNAMES,
    RESET_OUTCOME_TAXONOMY_GUARD_FIELDNAMES,
    RESET_REQUEST_SCHEMA_FIELDNAMES,
    RESET_SEED_LINEAGE_FIELDNAMES,
    SELECTED_PLATFORM_FAMILY,
    build_actor_action_guard_rows,
    build_actor_view_parity_rows,
    build_claim_boundary_checks,
    build_gate_matrix_rows,
    build_initial_state_admission_rows,
    build_reset_execution_precondition_rows,
    build_reset_outcome_taxonomy_guard_rows,
    build_reset_request_schema_rows,
    build_reset_seed_lineage_rows,
    materialize_route_a_hf3_selected_platform_reset_feasibility_readiness,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2615_summary():
    return read_json(
        "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/"
        "summary.json"
    )


def _build_rows():
    summary = _m2615_summary()
    request_rows = build_reset_request_schema_rows(summary)
    initial_state_rows = build_initial_state_admission_rows(request_rows)
    actor_view_rows = build_actor_view_parity_rows(initial_state_rows)
    seed_lineage_rows = build_reset_seed_lineage_rows(actor_view_rows, summary)
    outcome_guard_rows = build_reset_outcome_taxonomy_guard_rows()
    precondition_rows = build_reset_execution_precondition_rows(
        request_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
    )
    actor_action_guard_rows = build_actor_action_guard_rows(actor_view_rows)
    claim_rows = build_claim_boundary_checks(
        request_rows,
        initial_state_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
        precondition_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists={"present": True},
        m2615_summary=summary,
        request_rows=request_rows,
        initial_state_rows=initial_state_rows,
        actor_view_rows=actor_view_rows,
        seed_lineage_rows=seed_lineage_rows,
        outcome_guard_rows=outcome_guard_rows,
        precondition_rows=precondition_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )
    return (
        request_rows,
        initial_state_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
        precondition_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    )


def test_build_hf3_selected_platform_reset_feasibility_readiness_rows_preserve_boundaries():
    (
        request_rows,
        initial_state_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
        precondition_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    ) = _build_rows()

    assert len(request_rows) == 2
    assert set(request_rows[0]) == set(RESET_REQUEST_SCHEMA_FIELDNAMES)
    assert {row["route_role_id"] for row in request_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["selected_platform_family"] for row in request_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["actor_observation_shape"] for row in request_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in request_rows} == {ACTION_DIM}
    assert {row["reset_request_schema_materialized_in_m2619"] for row in request_rows} == {
        True
    }
    assert {row["source_build_required_before_execution"] for row in request_rows} == {True}
    assert {row["adapter_probe_required_before_execution"] for row in request_rows} == {True}
    assert {row["reset_executed_in_m2619"] for row in request_rows} == {False}
    assert {row["policy_action_allowed_in_m2619"] for row in request_rows} == {False}
    assert {row["environment_step_allowed_in_m2619"] for row in request_rows} == {False}
    assert {row["rollout_allowed_in_m2619"] for row in request_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in request_rows} == {False}

    assert len(initial_state_rows) == 2
    assert set(initial_state_rows[0]) == set(INITIAL_STATE_ADMISSION_FIELDNAMES)
    assert {row["initial_state_admission_materialized_in_m2619"] for row in initial_state_rows} == {
        True
    }
    assert {row["geometry_binding_required"] for row in initial_state_rows} == {True}
    assert {row["actor_view_required_after_reset"] for row in initial_state_rows} == {True}
    assert {row["hidden_oracle_actor_input_allowed"] for row in initial_state_rows} == {False}
    assert {row["feasibility_label_actor_visible"] for row in initial_state_rows} == {False}
    assert {row["reset_status_actor_visible"] for row in initial_state_rows} == {False}
    assert {row["validation_status_actor_visible"] for row in initial_state_rows} == {False}
    assert {row["reset_execution_allowed_in_m2619"] for row in initial_state_rows} == {False}

    assert len(actor_view_rows) == 2
    assert set(actor_view_rows[0]) == set(ACTOR_VIEW_PARITY_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_view_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_view_rows} == {ACTION_DIM}
    assert {row["ego_kinematics_included"] for row in actor_view_rows} == {True}
    assert {row["actuator_state_included"] for row in actor_view_rows} == {True}
    assert {row["previous_command_included"] for row in actor_view_rows} == {True}
    assert {row["road_geometry_included"] for row in actor_view_rows} == {True}
    assert {row["obstacle_geometry_included"] for row in actor_view_rows} == {True}
    for column in [
        "hidden_oracle_actor_input_detected",
        "diagnostics_actor_visible",
        "taxonomy_label_actor_visible",
        "backend_status_actor_visible",
        "reset_outcome_actor_visible",
        "selected_platform_actor_visible",
        "protocol_status_actor_visible",
    ]:
        assert {row[column] for row in actor_view_rows} == {False}

    assert len(seed_lineage_rows) == 2
    assert set(seed_lineage_rows[0]) == set(RESET_SEED_LINEAGE_FIELDNAMES)
    assert {row["parent_checkpoint_count"] for row in seed_lineage_rows} == {3}
    assert {row["deterministic_seed_required"] for row in seed_lineage_rows} == {True}
    assert {row["replay_lineage_required"] for row in seed_lineage_rows} == {True}
    assert {row["lineage_materialized_in_m2619"] for row in seed_lineage_rows} == {True}
    assert {row["reset_executed_in_m2619"] for row in seed_lineage_rows} == {False}
    assert {row["replay_executed_in_m2619"] for row in seed_lineage_rows} == {False}

    assert len(outcome_guard_rows) == 8
    assert set(outcome_guard_rows[0]) == set(RESET_OUTCOME_TAXONOMY_GUARD_FIELDNAMES)
    assert {row["outcome_field"] for row in outcome_guard_rows} == {
        "backend_available",
        "reset_request_valid",
        "reset_attempted",
        "reset_status",
        "actor_view_available",
        "diagnostics_available",
        "failure_reason",
        "execution_timestamp",
    }
    assert {row["actor_visible_allowed"] for row in outcome_guard_rows} == {False}
    assert {row["audit_metadata_allowed"] for row in outcome_guard_rows} == {True}
    assert {row["required_for_future_execution_audit"] for row in outcome_guard_rows} == {
        True
    }
    assert {row["allowed_to_support_reset_success_after_execution"] for row in outcome_guard_rows} == {
        True
    }
    assert {row["allowed_to_support_validation"] for row in outcome_guard_rows} == {False}
    assert {row["reset_outcome_actor_visible"] for row in outcome_guard_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in outcome_guard_rows} == {False}

    assert len(precondition_rows) == 6
    assert set(precondition_rows[0]) == set(RESET_EXECUTION_PRECONDITION_FIELDNAMES)
    assert {row["precondition_id"] for row in precondition_rows} == {
        "source_or_equivalent_trace_precondition",
        "source_build_precondition",
        "adapter_probe_precondition",
        "backend_availability_precondition",
        "reset_request_schema_precondition",
        "actor_view_and_lineage_precondition",
    }
    assert {row["materialized_in_m2619"] for row in precondition_rows} == {True}
    assert {row["reset_execution_allowed_in_m2619"] for row in precondition_rows} == {False}

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
        if row["claim_allowed_in_m2619"]
    } == {"selected_platform_reset_feasibility_readiness_design_materialized"}

    assert len(gate_rows) == 13
    assert set(gate_rows[0]) == set(GATE_FIELDNAMES)
    assert {row["status_pass"] for row in gate_rows} == {True}


def test_materialize_hf3_selected_platform_reset_feasibility_readiness_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2619.md"

    summary = materialize_route_a_hf3_selected_platform_reset_feasibility_readiness(
        output_dir,
        milestone="m2619-test",
        next_blocker="m2620-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness_materialization_preflight_pass"
    )
    assert summary["reset_request_schema_row_count"] == 2
    assert summary["initial_state_admission_row_count"] == 2
    assert summary["actor_view_parity_row_count"] == 2
    assert summary["reset_seed_lineage_row_count"] == 2
    assert summary["reset_outcome_taxonomy_guard_row_count"] == 8
    assert summary["reset_execution_precondition_row_count"] == 6
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 27
    assert summary["materialization_gate_count"] == 13
    assert summary["source_artifacts_exist"] is True
    assert summary["m2615_status_pass"] is True
    assert summary["m2615_selected_platform_family"] == SELECTED_PLATFORM_FAMILY
    assert (
        summary["selected_platform_reset_feasibility_readiness_design_materialized_in_m2619"]
        is True
    )
    assert summary["selected_platform_family_in_m2619"] == SELECTED_PLATFORM_FAMILY
    assert summary["reset_request_schema_materialized_in_m2619"] is True
    assert summary["initial_state_admission_materialized_in_m2619"] is True
    assert summary["actor_view_parity_materialized_in_m2619"] is True
    assert summary["reset_seed_lineage_materialized_in_m2619"] is True
    assert summary["reset_outcome_taxonomy_guard_materialized_in_m2619"] is True
    assert summary["reset_execution_precondition_materialized_in_m2619"] is True
    assert summary["forbidden_claim_allowed_in_m2619"] is False
    assert summary["external_install_allowed_in_m2619"] is False
    assert summary["external_import_allowed_in_m2619"] is False
    assert summary["runtime_execution_allowed_in_m2619"] is False
    assert summary["dependency_mutation_allowed_in_m2619"] is False
    assert summary["source_build_executed_in_m2619"] is False
    assert summary["adapter_probe_executed_in_m2619"] is False
    assert summary["reset_executed_in_m2619"] is False
    assert summary["environment_step_executed_in_m2619"] is False
    assert summary["policy_action_executed_in_m2619"] is False
    assert summary["rollout_executed_in_m2619"] is False
    assert summary["replay_executed_in_m2619"] is False
    assert summary["external_validation_execution_allowed_in_m2619"] is False
    assert summary["validation_protocol_ready_in_m2619"] is False
    assert summary["validation_admission_granted_in_m2619"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["reset_success_claim_allowed_in_m2619"] is False
    assert summary["driver_performance_claim_allowed_in_m2619"] is False
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
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    request_rows = _read_csv(output_dir / "hf3_selected_platform_reset_request_schema_rows.csv")
    initial_state_rows = _read_csv(
        output_dir / "hf3_selected_platform_initial_state_admission_rows.csv"
    )
    actor_view_rows = _read_csv(output_dir / "hf3_selected_platform_actor_view_parity_rows.csv")
    seed_lineage_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_seed_lineage_rows.csv"
    )
    outcome_guard_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_outcome_taxonomy_guard_rows.csv"
    )
    precondition_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_execution_precondition_rows.csv"
    )
    actor_action_guard_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_feasibility_actor_action_guard_rows.csv"
    )
    claim_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_feasibility_claim_boundary_checks.csv"
    )
    gate_rows = _read_csv(
        output_dir / "selected_platform_reset_feasibility_readiness_gate_matrix.csv"
    )

    assert len(request_rows) == 2
    assert len(initial_state_rows) == 2
    assert len(actor_view_rows) == 2
    assert len(seed_lineage_rows) == 2
    assert len(outcome_guard_rows) == 8
    assert len(precondition_rows) == 6
    assert len(actor_action_guard_rows) == 2
    assert len(claim_rows) == 27
    assert len(gate_rows) == 13
    assert {row["reset_executed_in_m2619"] for row in request_rows} == {"False"}
    assert {row["policy_action_allowed_in_m2619"] for row in request_rows} == {"False"}
    assert {row["environment_step_allowed_in_m2619"] for row in request_rows} == {"False"}
    assert {row["rollout_allowed_in_m2619"] for row in request_rows} == {"False"}
    assert {row["reset_execution_allowed_in_m2619"] for row in initial_state_rows} == {
        "False"
    }
    assert {row["reset_outcome_actor_visible"] for row in actor_view_rows} == {"False"}
    assert {row["reset_executed_in_m2619"] for row in seed_lineage_rows} == {"False"}
    assert {row["replay_executed_in_m2619"] for row in seed_lineage_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in outcome_guard_rows} == {"False"}
    assert {row["allowed_to_support_validation"] for row in outcome_guard_rows} == {"False"}
    assert {row["reset_execution_allowed_in_m2619"] for row in precondition_rows} == {
        "False"
    }
    assert {row["metadata_actor_visible"] for row in actor_action_guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2619"] == "True"
    } == {"selected_platform_reset_feasibility_readiness_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
