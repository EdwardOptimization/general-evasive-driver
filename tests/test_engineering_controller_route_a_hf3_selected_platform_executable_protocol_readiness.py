import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness import (
    ACTION_MAPPING_PARITY_FIELDNAMES,
    ACTOR_ACTION_GUARD_FIELDNAMES,
    ACTOR_EXTRACTOR_PARITY_FIELDNAMES,
    BUILD_PROBE_PLAN_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPLOYED_ACTION_MAPPING,
    GATE_FIELDNAMES,
    RESULT_EXPORT_REPLAY_READINESS_FIELDNAMES,
    SCENARIO_ROLE_BINDING_FIELDNAMES,
    SELECTED_PLATFORM_FAMILY,
    SOURCE_DEPENDENCY_REVIEW_ADMISSION_FIELDNAMES,
    VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES,
    RESET_STEP_API_READINESS_FIELDNAMES,
    build_action_mapping_parity_rows,
    build_actor_action_guard_rows,
    build_actor_extractor_parity_rows,
    build_build_probe_plan_rows,
    build_claim_boundary_checks,
    build_gate_matrix_rows,
    build_reset_step_api_readiness_rows,
    build_result_export_replay_readiness_rows,
    build_scenario_role_binding_rows,
    build_source_dependency_review_admission_rows,
    build_validation_admission_prerequisite_rows,
    materialize_route_a_hf3_selected_platform_executable_protocol_readiness,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2611_summary():
    return read_json(
        "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/"
        "summary.json"
    )


def _build_rows():
    summary = _m2611_summary()
    review_rows = build_source_dependency_review_admission_rows(summary)
    build_probe_rows = build_build_probe_plan_rows(review_rows)
    reset_step_rows = build_reset_step_api_readiness_rows(build_probe_rows)
    actor_extractor_rows = build_actor_extractor_parity_rows(reset_step_rows)
    action_mapping_rows = build_action_mapping_parity_rows(reset_step_rows)
    scenario_role_rows = build_scenario_role_binding_rows(reset_step_rows)
    export_replay_rows = build_result_export_replay_readiness_rows(review_rows)
    prerequisite_rows = build_validation_admission_prerequisite_rows(
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
    )
    guard_rows = build_actor_action_guard_rows(prerequisite_rows)
    claim_rows = build_claim_boundary_checks(
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
        prerequisite_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists={"present": True},
        m2611_summary=summary,
        review_rows=review_rows,
        build_probe_rows=build_probe_rows,
        reset_step_rows=reset_step_rows,
        actor_extractor_rows=actor_extractor_rows,
        action_mapping_rows=action_mapping_rows,
        scenario_role_rows=scenario_role_rows,
        export_replay_rows=export_replay_rows,
        prerequisite_rows=prerequisite_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )
    return (
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
        prerequisite_rows,
        guard_rows,
        claim_rows,
        gate_rows,
    )


def test_build_hf3_selected_platform_executable_protocol_readiness_rows_preserve_boundaries():
    (
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
        prerequisite_rows,
        guard_rows,
        claim_rows,
        gate_rows,
    ) = _build_rows()

    assert len(review_rows) == 4
    assert set(review_rows[0]) == set(SOURCE_DEPENDENCY_REVIEW_ADMISSION_FIELDNAMES)
    assert {row["selected_platform_family"] for row in review_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["review_family"] for row in review_rows} == {
        "selected_platform_source_trace_admission",
        "dependency_license_api_review_admission",
        "execution_sandbox_plan_admission",
        "repo_local_adapter_boundary_admission",
    }
    assert {row["review_materialized_in_m2615"] for row in review_rows} == {True}
    assert {row["external_install_allowed_in_m2615"] for row in review_rows} == {False}
    assert {row["external_import_allowed_in_m2615"] for row in review_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2615"] for row in review_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2615"] for row in review_rows} == {False}

    assert len(build_probe_rows) == 4
    assert set(build_probe_rows[0]) == set(BUILD_PROBE_PLAN_FIELDNAMES)
    assert {row["plan_family"] for row in build_probe_rows} == {
        "source_build_plan",
        "state_action_adapter_probe_plan",
        "deterministic_replay_export_probe_plan",
        "failure_status_taxonomy_probe_plan",
    }
    assert {row["plan_materialized_in_m2615"] for row in build_probe_rows} == {True}
    assert {row["source_build_required_later"] for row in build_probe_rows} == {True}
    assert {row["adapter_probe_required_later"] for row in build_probe_rows} == {True}
    assert {row["source_build_executed_in_m2615"] for row in build_probe_rows} == {False}
    assert {row["adapter_probe_executed_in_m2615"] for row in build_probe_rows} == {False}

    assert len(reset_step_rows) == 2
    assert set(reset_step_rows[0]) == set(RESET_STEP_API_READINESS_FIELDNAMES)
    assert {row["route_role_id"] for row in reset_step_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in reset_step_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in reset_step_rows} == {ACTION_DIM}
    assert {row["reset_api_contract_defined_in_m2615"] for row in reset_step_rows} == {True}
    assert {row["step_api_contract_defined_in_m2615"] for row in reset_step_rows} == {True}
    assert {
        row["termination_status_contract_defined_in_m2615"] for row in reset_step_rows
    } == {True}
    assert {row["reset_executed_in_m2615"] for row in reset_step_rows} == {False}
    assert {row["environment_step_executed_in_m2615"] for row in reset_step_rows} == {
        False
    }
    assert {row["policy_action_executed_in_m2615"] for row in reset_step_rows} == {False}
    assert {row["rollout_executed_in_m2615"] for row in reset_step_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2615"] for row in reset_step_rows} == {
        False
    }
    assert {row["validation_protocol_ready_in_m2615"] for row in reset_step_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in reset_step_rows} == {False}

    assert len(actor_extractor_rows) == 2
    assert set(actor_extractor_rows[0]) == set(ACTOR_EXTRACTOR_PARITY_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_extractor_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["ego_kinematics_included"] for row in actor_extractor_rows} == {True}
    assert {row["actuator_state_included"] for row in actor_extractor_rows} == {True}
    assert {row["previous_command_included"] for row in actor_extractor_rows} == {True}
    assert {row["road_geometry_included"] for row in actor_extractor_rows} == {True}
    assert {row["obstacle_geometry_included"] for row in actor_extractor_rows} == {True}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_extractor_rows} == {
        False
    }
    assert {row["diagnostics_actor_visible"] for row in actor_extractor_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in actor_extractor_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in actor_extractor_rows} == {False}
    assert {row["selected_platform_actor_visible"] for row in actor_extractor_rows} == {False}
    assert {row["protocol_status_actor_visible"] for row in actor_extractor_rows} == {False}

    assert len(action_mapping_rows) == 2
    assert set(action_mapping_rows[0]) == set(ACTION_MAPPING_PARITY_FIELDNAMES)
    assert {row["action_shape"] for row in action_mapping_rows} == {ACTION_DIM}
    assert {row["deployed_action_mapping"] for row in action_mapping_rows} == {
        DEPLOYED_ACTION_MAPPING
    }
    assert {row["steer_command_channel_preserved"] for row in action_mapping_rows} == {True}
    assert {row["throttle_command_channel_preserved"] for row in action_mapping_rows} == {True}
    assert {row["brake_command_channel_preserved"] for row in action_mapping_rows} == {True}
    assert {row["action_contract_mutation_detected"] for row in action_mapping_rows} == {
        False
    }
    assert {row["policy_action_executed_in_m2615"] for row in action_mapping_rows} == {False}

    assert len(scenario_role_rows) == 2
    assert set(scenario_role_rows[0]) == set(SCENARIO_ROLE_BINDING_FIELDNAMES)
    assert {row["scenario_label_actor_visible"] for row in scenario_role_rows} == {False}
    assert {row["reset_feasibility_evidence_required_later"] for row in scenario_role_rows} == {
        True
    }
    assert {row["rollout_feasibility_evidence_required_later"] for row in scenario_role_rows} == {
        True
    }
    assert {
        row["holdout_or_generalization_policy_required_later"] for row in scenario_role_rows
    } == {True}
    assert {row["reset_executed_in_m2615"] for row in scenario_role_rows} == {False}
    assert {row["rollout_executed_in_m2615"] for row in scenario_role_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in scenario_role_rows} == {False}

    assert len(export_replay_rows) == 3
    assert set(export_replay_rows[0]) == set(RESULT_EXPORT_REPLAY_READINESS_FIELDNAMES)
    assert {row["export_replay_family"] for row in export_replay_rows} == {
        "deterministic_result_schema",
        "replay_seed_and_lineage_manifest",
        "artifact_export_index",
    }
    assert {row["contract_defined_in_m2615"] for row in export_replay_rows} == {True}
    assert {row["replay_execution_required_later"] for row in export_replay_rows} == {True}
    assert {row["validation_execution_required_later"] for row in export_replay_rows} == {True}
    assert {row["replay_executed_in_m2615"] for row in export_replay_rows} == {False}
    assert {
        row["external_validation_execution_allowed_in_m2615"] for row in export_replay_rows
    } == {False}
    assert {row["validation_result_claim_allowed"] for row in export_replay_rows} == {False}

    assert len(prerequisite_rows) == 2
    assert set(prerequisite_rows[0]) == set(VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES)
    for column in [
        "source_dependency_review_materialized_in_m2615",
        "build_probe_plan_materialized_in_m2615",
        "reset_step_api_contract_materialized_in_m2615",
        "actor_extractor_parity_materialized_in_m2615",
        "action_mapping_parity_materialized_in_m2615",
        "scenario_role_binding_materialized_in_m2615",
        "result_export_replay_materialized_in_m2615",
    ]:
        assert {row[column] for row in prerequisite_rows} == {True}
    assert {row["validation_protocol_ready_in_m2615"] for row in prerequisite_rows} == {
        False
    }
    assert {row["validation_admission_granted_in_m2615"] for row in prerequisite_rows} == {
        False
    }
    assert {
        row["external_validation_execution_allowed_in_m2615"] for row in prerequisite_rows
    } == {False}
    assert {row["validation_result_claim_allowed"] for row in prerequisite_rows} == {False}

    assert len(guard_rows) == 2
    assert set(guard_rows[0]) == set(ACTOR_ACTION_GUARD_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in guard_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in guard_rows} == {ACTION_DIM}
    for column in [
        "hidden_oracle_actor_input_detected",
        "diagnostics_actor_visible",
        "taxonomy_label_actor_visible",
        "backend_status_actor_visible",
        "reset_outcome_actor_visible",
        "rollout_outcome_actor_visible",
        "validation_outcome_actor_visible",
        "platform_selection_actor_visible",
        "platform_selection_criteria_actor_visible",
        "platform_selection_decision_actor_visible",
        "selected_platform_actor_visible",
        "protocol_status_actor_visible",
        "action_contract_mutation_detected",
    ]:
        assert {row[column] for row in guard_rows} == {False}

    assert len(claim_rows) == 28
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2615"]
    } == {
        "selected_platform_executable_protocol_readiness_design_materialized",
        "source_dependency_review_admission_materialized",
        "build_probe_plan_materialized",
        "reset_step_api_contract_materialized",
        "actor_extractor_parity_materialized",
        "action_mapping_parity_materialized",
        "scenario_role_binding_materialized",
        "result_export_replay_readiness_materialized",
    }

    assert len(gate_rows) == 14
    assert set(gate_rows[0]) == set(GATE_FIELDNAMES)
    assert {row["status_pass"] for row in gate_rows} == {True}


def test_materialize_hf3_selected_platform_executable_protocol_readiness_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2615.md"

    summary = materialize_route_a_hf3_selected_platform_executable_protocol_readiness(
        output_dir,
        milestone="m2615-test",
        next_blocker="m2616-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness_materialization_preflight_pass"
    )
    assert summary["source_dependency_review_admission_row_count"] == 4
    assert summary["build_probe_plan_row_count"] == 4
    assert summary["reset_step_api_readiness_row_count"] == 2
    assert summary["actor_extractor_parity_row_count"] == 2
    assert summary["action_mapping_parity_row_count"] == 2
    assert summary["scenario_role_binding_row_count"] == 2
    assert summary["result_export_replay_readiness_row_count"] == 3
    assert summary["validation_admission_prerequisite_row_count"] == 2
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 28
    assert summary["materialization_gate_count"] == 14
    assert summary["source_artifacts_exist"] is True
    assert summary["m2611_status_pass"] is True
    assert summary["m2611_selected_platform_family"] == SELECTED_PLATFORM_FAMILY
    assert (
        summary[
            "selected_platform_executable_protocol_readiness_design_materialized_in_m2615"
        ]
        is True
    )
    assert summary["selected_platform_family_in_m2615"] == SELECTED_PLATFORM_FAMILY
    assert summary["source_dependency_review_materialized_in_m2615"] is True
    assert summary["build_probe_plan_materialized_in_m2615"] is True
    assert summary["reset_step_api_contract_materialized_in_m2615"] is True
    assert summary["actor_extractor_parity_materialized_in_m2615"] is True
    assert summary["action_mapping_parity_materialized_in_m2615"] is True
    assert summary["scenario_role_binding_materialized_in_m2615"] is True
    assert summary["result_export_replay_materialized_in_m2615"] is True
    assert summary["forbidden_claim_allowed_in_m2615"] is False
    assert summary["external_install_allowed_in_m2615"] is False
    assert summary["external_import_allowed_in_m2615"] is False
    assert summary["runtime_execution_allowed_in_m2615"] is False
    assert summary["dependency_mutation_allowed_in_m2615"] is False
    assert summary["source_build_executed_in_m2615"] is False
    assert summary["adapter_probe_executed_in_m2615"] is False
    assert summary["reset_executed_in_m2615"] is False
    assert summary["environment_step_executed_in_m2615"] is False
    assert summary["policy_action_executed_in_m2615"] is False
    assert summary["rollout_executed_in_m2615"] is False
    assert summary["replay_executed_in_m2615"] is False
    assert summary["external_validation_execution_allowed_in_m2615"] is False
    assert summary["validation_protocol_ready_in_m2615"] is False
    assert summary["validation_admission_granted_in_m2615"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["driver_performance_claim_allowed_in_m2615"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["diagnostics_actor_visible"] is False
    assert summary["taxonomy_label_actor_visible"] is False
    assert summary["backend_status_actor_visible"] is False
    assert summary["scenario_label_actor_visible"] is False
    assert summary["selected_platform_actor_visible"] is False
    assert summary["protocol_status_actor_visible"] is False
    assert summary["action_contract_mutation_detected"] is False
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    review_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_dependency_review_admission_rows.csv"
    )
    build_probe_rows = _read_csv(output_dir / "hf3_selected_platform_build_probe_plan_rows.csv")
    reset_step_rows = _read_csv(
        output_dir / "hf3_selected_platform_reset_step_api_readiness_rows.csv"
    )
    actor_extractor_rows = _read_csv(
        output_dir / "hf3_selected_platform_actor_extractor_parity_rows.csv"
    )
    action_mapping_rows = _read_csv(
        output_dir / "hf3_selected_platform_action_mapping_parity_rows.csv"
    )
    scenario_role_rows = _read_csv(
        output_dir / "hf3_selected_platform_scenario_role_binding_rows.csv"
    )
    export_replay_rows = _read_csv(
        output_dir / "hf3_selected_platform_result_export_replay_readiness_rows.csv"
    )
    prerequisite_rows = _read_csv(
        output_dir
        / "hf3_selected_platform_executable_protocol_validation_admission_prerequisite_rows.csv"
    )
    guard_rows = _read_csv(
        output_dir / "hf3_selected_platform_executable_protocol_actor_action_guard_rows.csv"
    )
    claim_rows = _read_csv(
        output_dir / "hf3_selected_platform_executable_protocol_claim_boundary_checks.csv"
    )
    gate_rows = _read_csv(
        output_dir / "selected_platform_executable_protocol_readiness_gate_matrix.csv"
    )

    assert len(review_rows) == 4
    assert len(build_probe_rows) == 4
    assert len(reset_step_rows) == 2
    assert len(actor_extractor_rows) == 2
    assert len(action_mapping_rows) == 2
    assert len(scenario_role_rows) == 2
    assert len(export_replay_rows) == 3
    assert len(prerequisite_rows) == 2
    assert len(guard_rows) == 2
    assert len(claim_rows) == 28
    assert len(gate_rows) == 14
    assert {row["selected_platform_family"] for row in review_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["external_install_allowed_in_m2615"] for row in review_rows} == {"False"}
    assert {row["source_build_executed_in_m2615"] for row in build_probe_rows} == {
        "False"
    }
    assert {row["adapter_probe_executed_in_m2615"] for row in build_probe_rows} == {
        "False"
    }
    assert {row["reset_executed_in_m2615"] for row in reset_step_rows} == {"False"}
    assert {row["environment_step_executed_in_m2615"] for row in reset_step_rows} == {
        "False"
    }
    assert {row["policy_action_executed_in_m2615"] for row in action_mapping_rows} == {
        "False"
    }
    assert {row["rollout_executed_in_m2615"] for row in scenario_role_rows} == {"False"}
    assert {row["replay_executed_in_m2615"] for row in export_replay_rows} == {"False"}
    assert {row["validation_protocol_ready_in_m2615"] for row in prerequisite_rows} == {
        "False"
    }
    assert {row["validation_admission_granted_in_m2615"] for row in prerequisite_rows} == {
        "False"
    }
    assert {
        row["external_validation_execution_allowed_in_m2615"] for row in prerequisite_rows
    } == {"False"}
    assert {row["validation_result_claim_allowed"] for row in prerequisite_rows} == {"False"}
    assert {row["selected_platform_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["protocol_status_actor_visible"] for row in guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2615"] == "True"
    } == {
        "selected_platform_executable_protocol_readiness_design_materialized",
        "source_dependency_review_admission_materialized",
        "build_probe_plan_materialized",
        "reset_step_api_contract_materialized",
        "actor_extractor_parity_materialized",
        "action_mapping_parity_materialized",
        "scenario_role_binding_materialized",
        "result_export_replay_readiness_materialized",
    }
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
