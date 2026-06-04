import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt import (
    ACTION_DIM,
    ACTOR_ACTION_GUARD_FIELDNAMES,
    ADAPTER_PROBE_ATTEMPT_ADMISSION_FIELDNAMES,
    BACKEND_DISCOVERY_EVIDENCE_CAPTURE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPENDENCY_RUNTIME_GUARD_FIELDNAMES,
    DEPLOYED_ACTION_MAPPING,
    EXECUTION_ATTEMPT_LOG_CAPTURE_FIELDNAMES,
    EXECUTION_FAILURE_TAXONOMY_FIELDNAMES,
    GATE_FIELDNAMES,
    P0_OBSERVATION_DIM,
    SELECTED_PLATFORM_FAMILY,
    SOURCE_BUILD_ATTEMPT_ADMISSION_FIELDNAMES,
    build_actor_action_guard_rows,
    build_adapter_probe_execution_attempt_admission_rows,
    build_backend_discovery_evidence_capture_rows,
    build_claim_boundary_checks,
    build_dependency_runtime_execution_guard_rows,
    build_execution_attempt_log_capture_rows,
    build_execution_failure_taxonomy_rows,
    build_gate_matrix_rows,
    build_source_build_execution_attempt_admission_rows,
    materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt,
)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2627_summary():
    return read_json(
        "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/"
        "summary.json"
    )


def _build_rows():
    summary = _m2627_summary()
    source_build_rows = build_source_build_execution_attempt_admission_rows(summary)
    adapter_probe_rows = build_adapter_probe_execution_attempt_admission_rows(summary)
    guard_rows = build_dependency_runtime_execution_guard_rows()
    log_rows = build_execution_attempt_log_capture_rows(source_build_rows, adapter_probe_rows)
    backend_rows = build_backend_discovery_evidence_capture_rows(adapter_probe_rows)
    failure_rows = build_execution_failure_taxonomy_rows()
    actor_action_guard_rows = build_actor_action_guard_rows()
    claim_rows = build_claim_boundary_checks(
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists={"present": True},
        m2627_summary=summary,
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        guard_rows=guard_rows,
        log_rows=log_rows,
        backend_rows=backend_rows,
        failure_rows=failure_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )
    return (
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    )


def test_build_hf3_selected_platform_execution_attempt_rows_preserve_boundaries():
    (
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
        claim_rows,
        gate_rows,
    ) = _build_rows()

    assert len(source_build_rows) == 2
    assert set(source_build_rows[0]) == set(SOURCE_BUILD_ATTEMPT_ADMISSION_FIELDNAMES)
    assert {row["source_build_attempt_admission_id"] for row in source_build_rows} == {
        "selected_platform_source_build_configure_attempt_admission",
        "selected_platform_source_build_compile_attempt_admission",
    }
    assert {row["selected_platform_family"] for row in source_build_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["source_tree_required"] for row in source_build_rows} == {True}
    assert {row["out_of_tree_build_required"] for row in source_build_rows} == {True}
    assert {
        row["command_attempt_schema_materialized_in_m2631"] for row in source_build_rows
    } == {True}
    assert {
        row["execution_attempt_allowed_after_m2631_audit"] for row in source_build_rows
    } == {True}
    assert {row["source_build_executed_in_m2631"] for row in source_build_rows} == {
        False
    }
    assert {
        row["source_build_attempt_executed_in_m2631"] for row in source_build_rows
    } == {False}
    assert {
        row["dependency_mutation_allowed_in_m2631"] for row in source_build_rows
    } == {False}
    assert {row["network_access_allowed_in_m2631"] for row in source_build_rows} == {
        False
    }
    assert {row["actor_visible_allowed"] for row in source_build_rows} == {False}

    assert len(adapter_probe_rows) == 2
    assert set(adapter_probe_rows[0]) == set(ADAPTER_PROBE_ATTEMPT_ADMISSION_FIELDNAMES)
    assert {row["adapter_probe_attempt_admission_id"] for row in adapter_probe_rows} == {
        "selected_platform_adapter_import_attempt_admission",
        "selected_platform_adapter_backend_probe_attempt_admission",
    }
    assert {row["adapter_import_required"] for row in adapter_probe_rows} == {True}
    assert {row["backend_discovery_required"] for row in adapter_probe_rows} == {True}
    assert {
        row["command_attempt_schema_materialized_in_m2631"] for row in adapter_probe_rows
    } == {True}
    assert {row["adapter_probe_executed_in_m2631"] for row in adapter_probe_rows} == {
        False
    }
    assert {
        row["adapter_probe_attempt_executed_in_m2631"] for row in adapter_probe_rows
    } == {False}
    assert {row["backend_start_allowed_in_m2631"] for row in adapter_probe_rows} == {
        False
    }
    assert {row["reset_allowed_in_m2631"] for row in adapter_probe_rows} == {False}
    assert {row["actor_visible_allowed"] for row in adapter_probe_rows} == {False}

    assert len(guard_rows) == 5
    assert set(guard_rows[0]) == set(DEPENDENCY_RUNTIME_GUARD_FIELDNAMES)
    assert {row["execution_guard_id"] for row in guard_rows} == {
        "dependency_install_guard",
        "source_tree_mutation_guard",
        "network_access_guard",
        "external_runtime_guard",
        "backend_start_guard",
    }
    for column in [
        "external_install_allowed_in_m2631",
        "external_import_allowed_in_m2631",
        "dependency_mutation_allowed_in_m2631",
        "source_tree_mutation_allowed_in_m2631",
        "network_access_allowed_in_m2631",
        "external_runtime_allowed_in_m2631",
        "source_build_execution_allowed_in_m2631",
        "adapter_probe_execution_allowed_in_m2631",
        "backend_start_allowed_in_m2631",
        "actor_visible_allowed",
    ]:
        assert {row[column] for row in guard_rows} == {False}

    assert len(log_rows) == 5
    assert set(log_rows[0]) == set(EXECUTION_ATTEMPT_LOG_CAPTURE_FIELDNAMES)
    assert {row["execution_log_capture_id"] for row in log_rows} == {
        "configure_attempt_log_capture",
        "compile_attempt_log_capture",
        "adapter_import_attempt_log_capture",
        "backend_probe_attempt_log_capture",
        "execution_environment_snapshot_log_capture",
    }
    assert {row["required_for_future_execution_attempt_audit"] for row in log_rows} == {
        True
    }
    assert {row["source_build_executed_in_m2631"] for row in log_rows} == {False}
    assert {row["adapter_probe_executed_in_m2631"] for row in log_rows} == {False}
    assert {row["log_observed_in_m2631"] for row in log_rows} == {False}
    assert {row["actor_visible_allowed"] for row in log_rows} == {False}

    assert len(backend_rows) == 4
    assert set(backend_rows[0]) == set(BACKEND_DISCOVERY_EVIDENCE_CAPTURE_FIELDNAMES)
    assert {row["backend_discovery_capture_id"] for row in backend_rows} == {
        "backend_factory_metadata_capture",
        "backend_capability_manifest_capture",
        "backend_healthcheck_trace_capture",
        "backend_failure_trace_capture",
    }
    assert {row["required_for_future_backend_availability_audit"] for row in backend_rows} == {
        True
    }
    assert {row["required_for_future_reset_admission"] for row in backend_rows} == {True}
    assert {row["backend_discovery_schema_materialized_in_m2631"] for row in backend_rows} == {
        True
    }
    assert {row["adapter_probe_executed_in_m2631"] for row in backend_rows} == {False}
    assert {row["backend_started_in_m2631"] for row in backend_rows} == {False}
    assert {
        row["backend_discovered_claim_allowed_in_m2631"] for row in backend_rows
    } == {False}
    assert {
        row["backend_availability_claim_allowed_in_m2631"] for row in backend_rows
    } == {False}
    assert {row["reset_execution_allowed_in_m2631"] for row in backend_rows} == {False}
    assert {row["evidence_observed_in_m2631"] for row in backend_rows} == {False}
    assert {row["actor_visible_allowed"] for row in backend_rows} == {False}

    assert len(failure_rows) == 11
    assert set(failure_rows[0]) == set(EXECUTION_FAILURE_TAXONOMY_FIELDNAMES)
    assert {row["failure_field"] for row in failure_rows} == {
        "source_missing",
        "configure_failed",
        "compile_failed",
        "artifact_missing",
        "adapter_import_failed",
        "backend_probe_failed",
        "backend_unavailable",
        "dependency_mutation_detected",
        "network_access_detected",
        "timeout",
        "unknown_failure",
    }
    assert {row["actor_visible_allowed"] for row in failure_rows} == {False}
    assert {row["materialized_in_m2631"] for row in failure_rows} == {True}

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
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_action_guard_rows} == {
        False
    }
    assert {row["metadata_actor_visible"] for row in actor_action_guard_rows} == {False}

    assert len(claim_rows) == 31
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2631"]
    } == {"selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized"}

    assert len(gate_rows) == 14
    assert set(gate_rows[0]) == set(GATE_FIELDNAMES)
    assert {row["status_pass"] for row in gate_rows} == {True}


def test_build_gate_matrix_catches_missing_source_artifacts():
    (
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
        claim_rows,
        _,
    ) = _build_rows()

    gate_rows = build_gate_matrix_rows(
        source_exists={"missing": False},
        m2627_summary=_m2627_summary(),
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        guard_rows=guard_rows,
        log_rows=log_rows,
        backend_rows=backend_rows,
        failure_rows=failure_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )

    source_gate = next(row for row in gate_rows if row["gate_id"] == "source_artifacts_exist")
    assert source_gate["status_pass"] is False
    assert source_gate["failure_type"] == "lineage_invalid"


def test_materialize_hf3_selected_platform_execution_attempt_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2631.md"

    summary = materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt(
        output_dir,
        milestone="m2631-test",
        next_blocker="m2632-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-result-audit",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialization_preflight_pass"
    )
    assert summary["source_build_attempt_admission_row_count"] == 2
    assert summary["adapter_probe_attempt_admission_row_count"] == 2
    assert summary["dependency_runtime_guard_row_count"] == 5
    assert summary["execution_attempt_log_capture_row_count"] == 5
    assert summary["backend_discovery_evidence_capture_row_count"] == 4
    assert summary["execution_failure_taxonomy_row_count"] == 11
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 31
    assert summary["materialization_gate_count"] == 14
    assert summary["source_artifacts_exist"] is True
    assert summary["m2627_status_pass"] is True
    assert summary["m2627_materialization_gates_all_pass"] is True
    assert summary["m2627_selected_platform_family"] == SELECTED_PLATFORM_FAMILY
    assert summary["m2627_source_build_executed"] is False
    assert summary["m2627_adapter_probe_executed"] is False
    assert summary["m2627_backend_started"] is False
    assert (
        summary[
            "selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized_in_m2631"
        ]
        is True
    )
    assert summary["selected_platform_family_in_m2631"] == SELECTED_PLATFORM_FAMILY
    assert summary["forbidden_claim_allowed_in_m2631"] is False
    assert summary["external_install_allowed_in_m2631"] is False
    assert summary["external_import_allowed_in_m2631"] is False
    assert summary["runtime_execution_allowed_in_m2631"] is False
    assert summary["dependency_mutation_allowed_in_m2631"] is False
    assert summary["source_tree_mutation_allowed_in_m2631"] is False
    assert summary["network_access_allowed_in_m2631"] is False
    assert summary["source_build_executed_in_m2631"] is False
    assert summary["source_build_attempt_executed_in_m2631"] is False
    assert summary["source_build_success_claim_allowed_in_m2631"] is False
    assert summary["adapter_probe_executed_in_m2631"] is False
    assert summary["adapter_probe_attempt_executed_in_m2631"] is False
    assert summary["adapter_probe_success_claim_allowed_in_m2631"] is False
    assert summary["backend_started_in_m2631"] is False
    assert summary["backend_discovered_claim_allowed_in_m2631"] is False
    assert summary["backend_availability_claim_allowed_in_m2631"] is False
    assert summary["reset_executed_in_m2631"] is False
    assert summary["environment_step_executed_in_m2631"] is False
    assert summary["policy_action_executed_in_m2631"] is False
    assert summary["rollout_executed_in_m2631"] is False
    assert summary["replay_executed_in_m2631"] is False
    assert summary["external_validation_execution_allowed_in_m2631"] is False
    assert summary["validation_protocol_ready_in_m2631"] is False
    assert summary["validation_admission_granted_in_m2631"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["reset_success_claim_allowed_in_m2631"] is False
    assert summary["rollout_feasibility_claim_allowed_in_m2631"] is False
    assert summary["driver_performance_claim_allowed_in_m2631"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["metadata_actor_visible"] is False
    assert summary["backend_status_actor_visible"] is False
    assert summary["build_outcome_actor_visible"] is False
    assert summary["probe_outcome_actor_visible"] is False
    assert summary["validation_outcome_actor_visible"] is False
    assert summary["actor_input_mutation_detected"] is False
    assert summary["action_contract_mutation_detected"] is False
    assert summary["source_build_run"] is False
    assert summary["source_build_attempt_run"] is False
    assert summary["adapter_probe_run"] is False
    assert summary["adapter_probe_attempt_run"] is False
    assert summary["backend_start_run"] is False
    assert summary["reset_execution_run"] is False
    assert summary["validation_execution_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    for path_key in [
        "summary",
        "source_build_attempt_admission_rows",
        "adapter_probe_attempt_admission_rows",
        "dependency_runtime_guard_rows",
        "execution_attempt_log_capture_rows",
        "backend_discovery_evidence_capture_rows",
        "execution_failure_taxonomy_rows",
        "actor_action_guard_rows",
        "claim_boundary_checks",
        "execution_attempt_gate_matrix",
    ]:
        assert (tmp_path / "run").joinpath(summary[path_key].split("/")[-1]).exists()

    assert doc_path.exists()
    assert len(_read_csv(output_dir / "hf3_selected_platform_source_build_execution_attempt_admission_rows.csv")) == 2
    assert len(_read_csv(output_dir / "hf3_selected_platform_adapter_probe_execution_attempt_admission_rows.csv")) == 2
    assert len(_read_csv(output_dir / "hf3_selected_platform_dependency_runtime_execution_guard_rows.csv")) == 5
    assert len(_read_csv(output_dir / "hf3_selected_platform_execution_attempt_log_capture_rows.csv")) == 5
    assert len(_read_csv(output_dir / "hf3_selected_platform_backend_discovery_evidence_capture_rows.csv")) == 4
    assert len(_read_csv(output_dir / "hf3_selected_platform_execution_failure_taxonomy_rows.csv")) == 11
    assert len(_read_csv(output_dir / "hf3_selected_platform_execution_attempt_actor_action_guard_rows.csv")) == 2
    assert len(_read_csv(output_dir / "hf3_selected_platform_execution_attempt_claim_boundary_checks.csv")) == 31
    assert len(_read_csv(output_dir / "selected_platform_source_build_adapter_probe_execution_attempt_gate_matrix.csv")) == 14
