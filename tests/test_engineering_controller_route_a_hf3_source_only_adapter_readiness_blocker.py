import csv

from autodrift.engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker import (
    ACTOR_VISIBILITY_GUARD_FIELDNAMES,
    CLAIM_FIELDNAMES,
    EXTERNAL_STATE_FIELDNAMES,
    FIXTURE_LINEAGE_FIELDNAMES,
    STATUS_MAPPING_FIELDNAMES,
    TIMING_CONTRACT_FIELDNAMES,
    build_actor_visibility_guard_rows,
    build_claim_boundary_checks,
    build_external_state_extraction_boundary_rows,
    build_failure_status_taxonomy_mapping_rows,
    build_source_only_fixture_smoke_lineage_rows,
    build_time_step_actuator_latency_contract_rows,
    materialize_route_a_hf3_source_only_adapter_readiness_blocker,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_hf3_source_only_adapter_readiness_blocker_rows_preserve_claim_boundary():
    external_state_rows = build_external_state_extraction_boundary_rows()
    timing_rows = build_time_step_actuator_latency_contract_rows()
    status_rows = build_failure_status_taxonomy_mapping_rows()
    fixture_rows = build_source_only_fixture_smoke_lineage_rows()
    actor_guard_rows = build_actor_visibility_guard_rows()
    claim_rows = build_claim_boundary_checks(
        external_state_rows,
        timing_rows,
        status_rows,
        fixture_rows,
        actor_guard_rows,
    )

    assert len(external_state_rows) == 4
    assert set(external_state_rows[0]) == set(EXTERNAL_STATE_FIELDNAMES)
    assert {row["boundary_family"] for row in external_state_rows} == {
        "ego_state_extraction_contract",
        "external_backend_state_mapping_contract",
        "diagnostic_state_redaction_contract",
        "validation_metadata_separation_contract",
    }
    assert {row["adapter_contract_required_before_external_execution"] for row in external_state_rows} == {True}
    assert {row["actor_visible"] for row in external_state_rows} == {False}
    assert {row["hidden_or_oracle_actor_input_detected"] for row in external_state_rows} == {False}
    assert {row["blocker_contract_defined_in_m2588"] for row in external_state_rows} == {True}
    assert {row["readiness_satisfied_in_m2588"] for row in external_state_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2588"] for row in external_state_rows} == {False}

    assert len(timing_rows) == 4
    assert set(timing_rows[0]) == set(TIMING_CONTRACT_FIELDNAMES)
    assert {row["contract_family"] for row in timing_rows} == {
        "simulation_time_step_contract",
        "control_update_rate_contract",
        "actuator_latency_mapping_contract",
        "command_hold_and_delay_contract",
    }
    assert {row["actor_observation_shape"] for row in timing_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in timing_rows} == {ACTION_DIM}
    assert {row["action_contract_mutation_detected"] for row in timing_rows} == {False}
    assert {row["blocker_contract_defined_in_m2588"] for row in timing_rows} == {True}
    assert {row["readiness_satisfied_in_m2588"] for row in timing_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2588"] for row in timing_rows} == {False}

    assert len(status_rows) == 4
    assert set(status_rows[0]) == set(STATUS_MAPPING_FIELDNAMES)
    assert {row["mapping_family"] for row in status_rows} == {
        "reset_failure_status_mapping",
        "step_failure_status_mapping",
        "collision_or_contact_status_mapping",
        "validation_abort_status_mapping",
    }
    assert {row["backend_status_actor_visible"] for row in status_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in status_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in status_rows} == {False}
    assert {row["maps_to_repo_local_status_class"] for row in status_rows} == {True}
    assert {row["blocker_contract_defined_in_m2588"] for row in status_rows} == {True}
    assert {row["readiness_satisfied_in_m2588"] for row in status_rows} == {False}

    assert len(fixture_rows) == 4
    assert set(fixture_rows[0]) == set(FIXTURE_LINEAGE_FIELDNAMES)
    assert {row["lineage_family"] for row in fixture_rows} == {
        "fixture_source_manifest_lineage",
        "fixture_expected_schema_lineage",
        "fixture_no_external_runtime_lineage",
        "fixture_replayable_artifact_hash_lineage",
    }
    assert {row["fixture_source_declared"] for row in fixture_rows} == {True}
    assert {row["expected_schema_declared"] for row in fixture_rows} == {True}
    assert {row["external_runtime_required"] for row in fixture_rows} == {False}
    assert {row["external_runtime_executed_in_m2588"] for row in fixture_rows} == {False}
    assert {row["replayable_artifact_hash_declared"] for row in fixture_rows} == {True}

    assert len(actor_guard_rows) == 4
    assert set(actor_guard_rows[0]) == set(ACTOR_VISIBILITY_GUARD_FIELDNAMES)
    assert {row["blocker_family"] for row in actor_guard_rows} == {
        "external_state_extraction_boundary",
        "time_step_and_actuator_latency_contract",
        "failure_status_taxonomy_mapping",
        "source_only_fixture_smoke_lineage",
    }
    assert {row["actor_observation_shape"] for row in actor_guard_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_guard_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_guard_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["reset_outcome_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["rollout_outcome_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["platform_selection_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["protocol_status_actor_visible"] for row in actor_guard_rows} == {False}

    assert len(claim_rows) == 15
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2588"]
    } == {"source_only_adapter_readiness_blocker_design_materialized"}


def test_materialize_route_a_hf3_source_only_adapter_readiness_blocker_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2588.md"

    summary = materialize_route_a_hf3_source_only_adapter_readiness_blocker(
        output_dir,
        milestone="m2588-test",
        next_blocker="m2589-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker_materialization_preflight_pass"
    )
    assert summary["m2584_missing_blocker_count"] == 4
    assert summary["external_state_extraction_boundary_row_count"] == 4
    assert summary["time_step_actuator_latency_contract_row_count"] == 4
    assert summary["failure_status_taxonomy_mapping_row_count"] == 4
    assert summary["source_only_fixture_smoke_lineage_row_count"] == 4
    assert summary["actor_visibility_guard_row_count"] == 4
    assert summary["claim_boundary_check_count"] == 15
    assert summary["materialization_gate_count"] == 11
    assert summary["source_only_adapter_readiness_blocker_design_materialized_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2588"] is False
    assert summary["blocker_contract_defined_in_m2588"] is True
    assert summary["readiness_satisfied_in_m2588"] is False
    assert summary["external_validation_execution_allowed_in_m2588"] is False
    assert summary["source_only_adapter_blockers_closed_claim_allowed"] is False
    assert summary["platform_selection_claim_allowed"] is False
    assert summary["validation_protocol_ready_claim_allowed"] is False
    assert summary["validation_admission_granted"] is False
    assert summary["actor_visible"] is False
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["diagnostics_actor_visible"] is False
    assert summary["taxonomy_label_actor_visible"] is False
    assert summary["backend_status_actor_visible"] is False
    assert summary["external_runtime_required"] is False
    assert summary["external_runtime_executed_in_m2588"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    external_state_rows = _read_csv(output_dir / "hf3_external_state_extraction_boundary_rows.csv")
    timing_rows = _read_csv(output_dir / "hf3_time_step_actuator_latency_contract_rows.csv")
    status_rows = _read_csv(output_dir / "hf3_failure_status_taxonomy_mapping_rows.csv")
    fixture_rows = _read_csv(output_dir / "hf3_source_only_fixture_smoke_lineage_rows.csv")
    actor_guard_rows = _read_csv(output_dir / "hf3_source_only_adapter_actor_visibility_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_source_only_adapter_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "source_only_adapter_readiness_blocker_gate_matrix.csv")

    assert len(external_state_rows) == 4
    assert len(timing_rows) == 4
    assert len(status_rows) == 4
    assert len(fixture_rows) == 4
    assert len(actor_guard_rows) == 4
    assert len(claim_rows) == 15
    assert len(gate_rows) == 11
    assert {row["actor_visible"] for row in external_state_rows} == {"False"}
    assert {row["readiness_satisfied_in_m2588"] for row in external_state_rows} == {"False"}
    assert {row["readiness_satisfied_in_m2588"] for row in timing_rows} == {"False"}
    assert {row["readiness_satisfied_in_m2588"] for row in status_rows} == {"False"}
    assert {row["readiness_satisfied_in_m2588"] for row in fixture_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2588"] for row in external_state_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2588"] for row in timing_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2588"] for row in status_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2588"] for row in fixture_rows} == {"False"}
    assert {row["actor_observation_shape"] for row in timing_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in timing_rows} == {str(ACTION_DIM)}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_guard_rows} == {"False"}
    assert {row["validation_outcome_actor_visible"] for row in actor_guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2588"] == "True"
    } == {"source_only_adapter_readiness_blocker_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
