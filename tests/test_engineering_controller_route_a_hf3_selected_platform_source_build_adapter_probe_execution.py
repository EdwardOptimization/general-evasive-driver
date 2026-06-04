import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution import (
    ACTION_DIM,
    ACTOR_ACTION_GUARD_FIELDNAMES,
    ADAPTER_PROBE_COMMAND_CONTRACT_FIELDNAMES,
    ADAPTER_PROBE_TRACE_CAPTURE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPENDENCY_ENVIRONMENT_ISOLATION_GUARD_FIELDNAMES,
    DEPLOYED_ACTION_MAPPING,
    GATE_FIELDNAMES,
    OUTCOME_TAXONOMY_FIELDNAMES,
    P0_OBSERVATION_DIM,
    SELECTED_PLATFORM_FAMILY,
    SOURCE_BUILD_ARTIFACT_CAPTURE_FIELDNAMES,
    SOURCE_BUILD_COMMAND_CONTRACT_FIELDNAMES,
    build_actor_action_guard_rows,
    build_adapter_probe_command_contract_rows,
    build_adapter_probe_trace_capture_rows,
    build_claim_boundary_checks,
    build_dependency_environment_isolation_guard_rows,
    build_gate_matrix_rows,
    build_source_build_adapter_probe_outcome_taxonomy_rows,
    build_source_build_artifact_capture_rows,
    build_source_build_command_contract_rows,
    materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution,
)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2623_summary():
    return read_json(
        "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/"
        "summary.json"
    )


def _build_rows():
    summary = _m2623_summary()
    source_build_rows = build_source_build_command_contract_rows(summary)
    adapter_probe_rows = build_adapter_probe_command_contract_rows(summary)
    isolation_rows = build_dependency_environment_isolation_guard_rows()
    artifact_rows = build_source_build_artifact_capture_rows(source_build_rows)
    trace_rows = build_adapter_probe_trace_capture_rows(adapter_probe_rows)
    outcome_rows = build_source_build_adapter_probe_outcome_taxonomy_rows()
    actor_action_guard_rows = build_actor_action_guard_rows()
    claim_rows = build_claim_boundary_checks(
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists={"present": True},
        m2623_summary=summary,
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        isolation_rows=isolation_rows,
        artifact_rows=artifact_rows,
        trace_rows=trace_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )
    return (
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
        outcome_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    )


def test_build_hf3_selected_platform_source_build_adapter_probe_rows_preserve_boundaries():
    (
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
        outcome_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    ) = _build_rows()

    assert len(source_build_rows) == 2
    assert set(source_build_rows[0]) == set(SOURCE_BUILD_COMMAND_CONTRACT_FIELDNAMES)
    assert {row["command_contract_id"] for row in source_build_rows} == {
        "selected_platform_source_build_configure_command_contract",
        "selected_platform_source_build_compile_command_contract",
    }
    assert {row["selected_platform_family"] for row in source_build_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["source_tree_required"] for row in source_build_rows} == {True}
    assert {row["out_of_tree_build_required"] for row in source_build_rows} == {True}
    assert {row["dependency_mutation_allowed_in_m2627"] for row in source_build_rows} == {
        False
    }
    assert {row["network_access_allowed_in_m2627"] for row in source_build_rows} == {
        False
    }
    assert {row["build_execution_allowed_in_m2627"] for row in source_build_rows} == {
        False
    }
    assert {row["log_capture_required"] for row in source_build_rows} == {True}
    assert {row["artifact_capture_required"] for row in source_build_rows} == {True}
    assert {row["actor_visible_allowed"] for row in source_build_rows} == {False}

    assert len(adapter_probe_rows) == 2
    assert set(adapter_probe_rows[0]) == set(ADAPTER_PROBE_COMMAND_CONTRACT_FIELDNAMES)
    assert {row["adapter_probe_contract_id"] for row in adapter_probe_rows} == {
        "selected_platform_adapter_import_probe_contract",
        "selected_platform_adapter_backend_probe_contract",
    }
    assert {row["adapter_import_required"] for row in adapter_probe_rows} == {True}
    assert {row["backend_discovery_required"] for row in adapter_probe_rows} == {True}
    assert {row["backend_start_allowed_in_m2627"] for row in adapter_probe_rows} == {
        False
    }
    assert {row["reset_allowed_in_m2627"] for row in adapter_probe_rows} == {False}
    assert {
        row["adapter_probe_execution_allowed_in_m2627"] for row in adapter_probe_rows
    } == {False}
    assert {row["trace_capture_required"] for row in adapter_probe_rows} == {True}
    assert {row["actor_visible_allowed"] for row in adapter_probe_rows} == {False}

    assert len(isolation_rows) == 4
    assert set(isolation_rows[0]) == set(DEPENDENCY_ENVIRONMENT_ISOLATION_GUARD_FIELDNAMES)
    assert {row["isolation_guard_id"] for row in isolation_rows} == {
        "dependency_install_guard",
        "source_tree_mutation_guard",
        "network_access_guard",
        "external_runtime_guard",
    }
    for column in [
        "external_install_allowed_in_m2627",
        "external_import_allowed_in_m2627",
        "dependency_mutation_allowed_in_m2627",
        "source_tree_mutation_allowed_in_m2627",
        "network_access_allowed_in_m2627",
        "external_runtime_allowed_in_m2627",
        "actor_visible_allowed",
    ]:
        assert {row[column] for row in isolation_rows} == {False}

    assert len(artifact_rows) == 4
    assert set(artifact_rows[0]) == set(SOURCE_BUILD_ARTIFACT_CAPTURE_FIELDNAMES)
    assert {row["artifact_capture_id"] for row in artifact_rows} == {
        "configure_log_capture",
        "compile_log_capture",
        "build_artifact_manifest_capture",
        "build_environment_snapshot_capture",
    }
    assert {row["required_for_future_source_build_audit"] for row in artifact_rows} == {
        True
    }
    assert {
        row["required_for_future_adapter_probe_admission"] for row in artifact_rows
    } == {True}
    assert {row["materialized_in_m2627"] for row in artifact_rows} == {True}
    assert {row["source_build_executed_in_m2627"] for row in artifact_rows} == {False}
    assert {row["artifact_observed_in_m2627"] for row in artifact_rows} == {False}
    assert {row["actor_visible_allowed"] for row in artifact_rows} == {False}

    assert len(trace_rows) == 4
    assert set(trace_rows[0]) == set(ADAPTER_PROBE_TRACE_CAPTURE_FIELDNAMES)
    assert {row["trace_capture_id"] for row in trace_rows} == {
        "adapter_import_trace_capture",
        "backend_factory_trace_capture",
        "backend_capability_trace_capture",
        "adapter_failure_trace_capture",
    }
    assert {row["required_for_future_adapter_probe_audit"] for row in trace_rows} == {
        True
    }
    assert {row["required_for_future_reset_execution_admission"] for row in trace_rows} == {
        True
    }
    assert {row["materialized_in_m2627"] for row in trace_rows} == {True}
    assert {row["adapter_probe_executed_in_m2627"] for row in trace_rows} == {False}
    assert {row["backend_started_in_m2627"] for row in trace_rows} == {False}
    assert {row["trace_observed_in_m2627"] for row in trace_rows} == {False}
    assert {row["actor_visible_allowed"] for row in trace_rows} == {False}

    assert len(outcome_rows) == 10
    assert set(outcome_rows[0]) == set(OUTCOME_TAXONOMY_FIELDNAMES)
    assert {row["outcome_field"] for row in outcome_rows} == {
        "source_available",
        "configure_attempted",
        "compile_attempted",
        "build_artifact_available",
        "adapter_import_attempted",
        "adapter_probe_attempted",
        "backend_discovered",
        "probe_status",
        "failure_reason",
        "execution_timestamp",
    }
    assert {
        row["required_for_future_source_build_adapter_probe_audit"]
        for row in outcome_rows
    } == {True}
    assert {
        row["allowed_to_support_backend_availability_after_execution"]
        for row in outcome_rows
    } == {True}
    assert {
        row["allowed_to_support_reset_execution_admission_after_execution"]
        for row in outcome_rows
    } == {True}
    assert {row["actor_visible_allowed"] for row in outcome_rows} == {False}
    assert {row["materialized_in_m2627"] for row in outcome_rows} == {True}

    assert len(actor_action_guard_rows) == 2
    assert set(actor_action_guard_rows[0]) == set(ACTOR_ACTION_GUARD_FIELDNAMES)
    assert {row["route_role_id"] for row in actor_action_guard_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
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

    assert len(claim_rows) == 28
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2627"]
    } == {"selected_platform_source_build_adapter_probe_execution_design_materialized"}

    assert len(gate_rows) == 13
    assert set(gate_rows[0]) == set(GATE_FIELDNAMES)
    assert {row["status_pass"] for row in gate_rows} == {True}


def test_build_gate_matrix_catches_missing_source_artifacts():
    (
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
        outcome_rows,
        actor_action_guard_rows,
        claim_rows,
        _,
    ) = _build_rows()

    gate_rows = build_gate_matrix_rows(
        source_exists={"missing": False},
        m2623_summary=_m2623_summary(),
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        isolation_rows=isolation_rows,
        artifact_rows=artifact_rows,
        trace_rows=trace_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )

    source_gate = next(row for row in gate_rows if row["gate_id"] == "source_artifacts_exist")
    assert source_gate["status_pass"] is False
    assert source_gate["failure_type"] == "lineage_invalid"


def test_materialize_hf3_selected_platform_source_build_adapter_probe_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2627.md"

    summary = materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution(
        output_dir,
        milestone="m2627-test",
        next_blocker="m2628-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_preflight_pass"
    )
    assert summary["source_build_command_contract_row_count"] == 2
    assert summary["adapter_probe_command_contract_row_count"] == 2
    assert summary["dependency_environment_isolation_guard_row_count"] == 4
    assert summary["source_build_artifact_capture_row_count"] == 4
    assert summary["adapter_probe_trace_capture_row_count"] == 4
    assert summary["outcome_taxonomy_row_count"] == 10
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 28
    assert summary["materialization_gate_count"] == 13
    assert summary["source_artifacts_exist"] is True
    assert summary["m2623_status_pass"] is True
    assert summary["m2623_materialization_gates_all_pass"] is True
    assert summary["m2623_selected_platform_family"] == SELECTED_PLATFORM_FAMILY
    assert summary["m2623_source_build_executed"] is False
    assert summary["m2623_adapter_probe_executed"] is False
    assert summary["m2623_reset_executed"] is False
    assert summary["m2623_validation_protocol_ready"] is False
    assert (
        summary[
            "selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627"
        ]
        is True
    )
    assert summary["selected_platform_family_in_m2627"] == SELECTED_PLATFORM_FAMILY
    assert summary["forbidden_claim_allowed_in_m2627"] is False
    assert summary["external_install_allowed_in_m2627"] is False
    assert summary["external_import_allowed_in_m2627"] is False
    assert summary["runtime_execution_allowed_in_m2627"] is False
    assert summary["dependency_mutation_allowed_in_m2627"] is False
    assert summary["source_tree_mutation_allowed_in_m2627"] is False
    assert summary["network_access_allowed_in_m2627"] is False
    assert summary["source_build_executed_in_m2627"] is False
    assert summary["adapter_probe_executed_in_m2627"] is False
    assert summary["backend_started_in_m2627"] is False
    assert summary["reset_executed_in_m2627"] is False
    assert summary["environment_step_executed_in_m2627"] is False
    assert summary["policy_action_executed_in_m2627"] is False
    assert summary["rollout_executed_in_m2627"] is False
    assert summary["replay_executed_in_m2627"] is False
    assert summary["external_validation_execution_allowed_in_m2627"] is False
    assert summary["validation_protocol_ready_in_m2627"] is False
    assert summary["validation_admission_granted_in_m2627"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["backend_availability_claim_allowed_in_m2627"] is False
    assert summary["reset_success_claim_allowed_in_m2627"] is False
    assert summary["rollout_feasibility_claim_allowed_in_m2627"] is False
    assert summary["driver_performance_claim_allowed_in_m2627"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["metadata_actor_visible"] is False
    assert summary["diagnostics_actor_visible"] is False
    assert summary["taxonomy_label_actor_visible"] is False
    assert summary["backend_status_actor_visible"] is False
    assert summary["build_outcome_actor_visible"] is False
    assert summary["probe_outcome_actor_visible"] is False
    assert summary["validation_outcome_actor_visible"] is False
    assert summary["actor_input_mutation_detected"] is False
    assert summary["action_contract_mutation_detected"] is False
    assert summary["source_build_run"] is False
    assert summary["adapter_probe_run"] is False
    assert summary["backend_start_run"] is False
    assert summary["reset_execution_run"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    source_build_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_build_command_contract_rows.csv"
    )
    adapter_probe_rows = _read_csv(
        output_dir / "hf3_selected_platform_adapter_probe_command_contract_rows.csv"
    )
    isolation_rows = _read_csv(
        output_dir / "hf3_selected_platform_dependency_environment_isolation_guard_rows.csv"
    )
    artifact_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_build_artifact_capture_rows.csv"
    )
    trace_rows = _read_csv(
        output_dir / "hf3_selected_platform_adapter_probe_trace_capture_rows.csv"
    )
    outcome_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows.csv"
    )
    actor_action_guard_rows = _read_csv(
        output_dir
        / "hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows.csv"
    )
    claim_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks.csv"
    )
    gate_rows = _read_csv(
        output_dir / "selected_platform_source_build_adapter_probe_execution_gate_matrix.csv"
    )

    assert len(source_build_rows) == 2
    assert len(adapter_probe_rows) == 2
    assert len(isolation_rows) == 4
    assert len(artifact_rows) == 4
    assert len(trace_rows) == 4
    assert len(outcome_rows) == 10
    assert len(actor_action_guard_rows) == 2
    assert len(claim_rows) == 28
    assert len(gate_rows) == 13
    assert {row["build_execution_allowed_in_m2627"] for row in source_build_rows} == {
        "False"
    }
    assert {row["network_access_allowed_in_m2627"] for row in source_build_rows} == {
        "False"
    }
    assert {row["adapter_probe_execution_allowed_in_m2627"] for row in adapter_probe_rows} == {
        "False"
    }
    assert {row["backend_start_allowed_in_m2627"] for row in adapter_probe_rows} == {
        "False"
    }
    assert {row["reset_allowed_in_m2627"] for row in adapter_probe_rows} == {"False"}
    assert {row["external_install_allowed_in_m2627"] for row in isolation_rows} == {
        "False"
    }
    assert {row["dependency_mutation_allowed_in_m2627"] for row in isolation_rows} == {
        "False"
    }
    assert {row["source_tree_mutation_allowed_in_m2627"] for row in isolation_rows} == {
        "False"
    }
    assert {row["source_build_executed_in_m2627"] for row in artifact_rows} == {"False"}
    assert {row["artifact_observed_in_m2627"] for row in artifact_rows} == {"False"}
    assert {row["adapter_probe_executed_in_m2627"] for row in trace_rows} == {"False"}
    assert {row["backend_started_in_m2627"] for row in trace_rows} == {"False"}
    assert {row["trace_observed_in_m2627"] for row in trace_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in outcome_rows} == {"False"}
    assert {row["metadata_actor_visible"] for row in actor_action_guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2627"] == "True"
    } == {"selected_platform_source_build_adapter_probe_execution_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
