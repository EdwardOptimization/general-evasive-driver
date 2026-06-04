import csv

from autodrift.engineering_controller_route_a_hf3_source_only_adapter_blocker_closure import (
    ACTOR_VISIBILITY_GUARD_FIELDNAMES,
    CLAIM_FIELDNAMES,
    EXTERNAL_STATE_CLOSURE_FIELDNAMES,
    FIXTURE_CLOSURE_FIELDNAMES,
    STATUS_CLOSURE_FIELDNAMES,
    TIMING_CLOSURE_FIELDNAMES,
    build_actor_visibility_guard_rows,
    build_claim_boundary_checks,
    build_external_state_extraction_closure_rows,
    build_failure_status_taxonomy_closure_rows,
    build_source_only_fixture_smoke_closure_rows,
    build_time_step_actuator_latency_closure_rows,
    materialize_route_a_hf3_source_only_adapter_blocker_closure,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_hf3_source_only_adapter_blocker_closure_rows_preserve_boundaries():
    external_state_rows = build_external_state_extraction_closure_rows()
    timing_rows = build_time_step_actuator_latency_closure_rows()
    status_rows = build_failure_status_taxonomy_closure_rows()
    fixture_rows = build_source_only_fixture_smoke_closure_rows()
    actor_guard_rows = build_actor_visibility_guard_rows()
    claim_rows = build_claim_boundary_checks(
        external_state_rows,
        timing_rows,
        status_rows,
        fixture_rows,
        actor_guard_rows,
    )

    assert len(external_state_rows) == 4
    assert set(external_state_rows[0]) == set(EXTERNAL_STATE_CLOSURE_FIELDNAMES)
    assert {row["closure_family"] for row in external_state_rows} == {
        "ego_state_extractor_schema_closure",
        "external_backend_to_p0_mapping_closure",
        "diagnostic_state_redaction_closure",
        "validation_metadata_non_actor_channel_closure",
    }
    assert {row["fixture_schema_declared"] for row in external_state_rows} == {True}
    assert {row["extractor_output_schema_declared"] for row in external_state_rows} == {True}
    assert {row["backend_state_read_by_adapter_only"] for row in external_state_rows} == {True}
    assert {row["adapter_only_fields_redacted_from_actor"] for row in external_state_rows} == {True}
    assert {row["actor_observation_shape"] for row in external_state_rows} == {P0_OBSERVATION_DIM}
    assert {row["actor_visible"] for row in external_state_rows} == {False}
    assert {row["hidden_or_oracle_actor_input_detected"] for row in external_state_rows} == {False}
    assert {row["source_only_closure_materialized_in_m2592"] for row in external_state_rows} == {True}
    assert {row["validation_protocol_ready_in_m2592"] for row in external_state_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2592"] for row in external_state_rows} == {False}

    assert len(timing_rows) == 4
    assert set(timing_rows[0]) == set(TIMING_CLOSURE_FIELDNAMES)
    assert {row["closure_family"] for row in timing_rows} == {
        "simulation_time_step_value_closure",
        "control_update_rate_alignment_closure",
        "actuator_latency_channel_mapping_closure",
        "command_hold_delay_semantics_closure",
    }
    assert {row["actor_observation_shape"] for row in timing_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in timing_rows} == {ACTION_DIM}
    assert {row["deployed_action_mapping_preserved"] for row in timing_rows} == {True}
    assert {row["action_contract_mutation_detected"] for row in timing_rows} == {False}
    assert {row["source_only_closure_materialized_in_m2592"] for row in timing_rows} == {True}
    assert {row["validation_protocol_ready_in_m2592"] for row in timing_rows} == {False}

    assert len(status_rows) == 4
    assert set(status_rows[0]) == set(STATUS_CLOSURE_FIELDNAMES)
    assert {row["closure_family"] for row in status_rows} == {
        "reset_failure_status_closure",
        "step_failure_status_closure",
        "collision_or_contact_status_closure",
        "validation_abort_status_closure",
    }
    assert {row["repo_local_status_class_declared"] for row in status_rows} == {True}
    assert {row["terminal_or_abort_semantics_declared"] for row in status_rows} == {True}
    assert {row["backend_status_actor_visible"] for row in status_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in status_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in status_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in status_rows} == {False}

    assert len(fixture_rows) == 4
    assert set(fixture_rows[0]) == set(FIXTURE_CLOSURE_FIELDNAMES)
    assert {row["closure_family"] for row in fixture_rows} == {
        "fixture_source_manifest_closure",
        "fixture_expected_schema_closure",
        "fixture_no_external_runtime_closure",
        "fixture_replayable_hash_and_smoke_closure",
    }
    assert {row["fixture_source_declared"] for row in fixture_rows} == {True}
    assert {row["expected_schema_declared"] for row in fixture_rows} == {True}
    assert {row["fixture_hash_declared"] for row in fixture_rows} == {True}
    assert {row["fixture_smoke_replay_declared"] for row in fixture_rows} == {True}
    assert {row["external_runtime_required"] for row in fixture_rows} == {False}
    assert {row["external_runtime_executed_in_m2592"] for row in fixture_rows} == {False}

    assert len(actor_guard_rows) == 4
    assert set(actor_guard_rows[0]) == set(ACTOR_VISIBILITY_GUARD_FIELDNAMES)
    assert {row["blocker_family"] for row in actor_guard_rows} == {
        "external_state_extraction_boundary",
        "time_step_and_actuator_latency_contract",
        "failure_status_taxonomy_mapping",
        "source_only_fixture_smoke_lineage",
    }
    assert {row["actor_observation_shape"] for row in actor_guard_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in actor_guard_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_guard_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["platform_selection_actor_visible"] for row in actor_guard_rows} == {False}
    assert {row["protocol_status_actor_visible"] for row in actor_guard_rows} == {False}

    assert len(claim_rows) == 15
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2592"]
    } == {"repo_local_source_only_adapter_blocker_closure_materialized"}


def test_materialize_route_a_hf3_source_only_adapter_blocker_closure_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2592.md"

    summary = materialize_route_a_hf3_source_only_adapter_blocker_closure(
        output_dir,
        milestone="m2592-test",
        next_blocker="m2593-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_source_only_adapter_blocker_closure_materialization_preflight_pass"
    )
    assert summary["external_state_extraction_closure_row_count"] == 4
    assert summary["time_step_actuator_latency_closure_row_count"] == 4
    assert summary["failure_status_taxonomy_closure_row_count"] == 4
    assert summary["source_only_fixture_smoke_closure_row_count"] == 4
    assert summary["actor_visibility_guard_row_count"] == 4
    assert summary["claim_boundary_check_count"] == 15
    assert summary["materialization_gate_count"] == 13
    assert summary["source_only_adapter_blocker_closure_claim_allowed"] is True
    assert summary["repo_local_source_only_adapter_blocker_closure_materialized"] is True
    assert summary["forbidden_claim_allowed_in_m2592"] is False
    assert summary["source_only_closure_materialized_in_m2592"] is True
    assert summary["validation_protocol_ready_in_m2592"] is False
    assert summary["external_validation_execution_allowed_in_m2592"] is False
    assert summary["platform_selected_in_m2592"] is False
    assert summary["driver_performance_claim_allowed_in_m2592"] is False
    assert summary["actor_visible"] is False
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["diagnostics_actor_visible"] is False
    assert summary["taxonomy_label_actor_visible"] is False
    assert summary["backend_status_actor_visible"] is False
    assert summary["external_runtime_required"] is False
    assert summary["external_runtime_executed_in_m2592"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    external_state_rows = _read_csv(output_dir / "hf3_external_state_extraction_closure_rows.csv")
    timing_rows = _read_csv(output_dir / "hf3_time_step_actuator_latency_closure_rows.csv")
    status_rows = _read_csv(output_dir / "hf3_failure_status_taxonomy_closure_rows.csv")
    fixture_rows = _read_csv(output_dir / "hf3_source_only_fixture_smoke_closure_rows.csv")
    actor_guard_rows = _read_csv(output_dir / "hf3_source_only_adapter_closure_actor_visibility_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_source_only_adapter_closure_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "source_only_adapter_blocker_closure_gate_matrix.csv")

    assert len(external_state_rows) == 4
    assert len(timing_rows) == 4
    assert len(status_rows) == 4
    assert len(fixture_rows) == 4
    assert len(actor_guard_rows) == 4
    assert len(claim_rows) == 15
    assert len(gate_rows) == 13
    assert {row["actor_visible"] for row in external_state_rows} == {"False"}
    assert {row["source_only_closure_materialized_in_m2592"] for row in external_state_rows} == {"True"}
    assert {row["source_only_closure_materialized_in_m2592"] for row in timing_rows} == {"True"}
    assert {row["source_only_closure_materialized_in_m2592"] for row in status_rows} == {"True"}
    assert {row["source_only_closure_materialized_in_m2592"] for row in fixture_rows} == {"True"}
    assert {row["validation_protocol_ready_in_m2592"] for row in external_state_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2592"] for row in timing_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2592"] for row in status_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2592"] for row in fixture_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2592"] for row in external_state_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2592"] for row in timing_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2592"] for row in status_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2592"] for row in fixture_rows} == {"False"}
    assert {row["actor_observation_shape"] for row in timing_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in timing_rows} == {str(ACTION_DIM)}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_guard_rows} == {"False"}
    assert {row["validation_outcome_actor_visible"] for row in actor_guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2592"] == "True"
    } == {"repo_local_source_only_adapter_blocker_closure_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
