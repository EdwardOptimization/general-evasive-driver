import csv

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPENDENCY_INVENTORY_FIELDNAMES,
    GATE_FIELDNAMES,
    PROBE_READINESS_FIELDNAMES,
    PROTOCOL_SKELETON_FIELDNAMES,
    SELECTED_PLATFORM_FAMILY,
    VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES,
    build_actor_action_guard_rows,
    build_claim_boundary_checks,
    build_dependency_inventory_rows,
    build_gate_matrix_rows,
    build_protocol_skeleton_rows,
    build_source_build_adapter_probe_readiness_rows,
    build_validation_admission_prerequisite_rows,
    materialize_route_a_hf3_selected_platform_dependency_protocol_readiness,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2607_summary():
    return read_json(
        "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/"
        "summary.json"
    )


def test_build_hf3_selected_platform_dependency_protocol_readiness_rows_preserve_boundaries():
    summary = _m2607_summary()
    dependency_rows = build_dependency_inventory_rows(summary)
    probe_rows = build_source_build_adapter_probe_readiness_rows(dependency_rows)
    protocol_rows = build_protocol_skeleton_rows(dependency_rows, probe_rows)
    prerequisite_rows = build_validation_admission_prerequisite_rows(
        dependency_rows,
        protocol_rows,
    )
    guard_rows = build_actor_action_guard_rows(prerequisite_rows)
    claim_rows = build_claim_boundary_checks(
        dependency_rows,
        probe_rows,
        protocol_rows,
        prerequisite_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists={"present": True},
        m2607_summary=summary,
        dependency_rows=dependency_rows,
        probe_rows=probe_rows,
        protocol_rows=protocol_rows,
        prerequisite_rows=prerequisite_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    assert len(dependency_rows) == 4
    assert set(dependency_rows[0]) == set(DEPENDENCY_INVENTORY_FIELDNAMES)
    assert {row["selected_platform_family"] for row in dependency_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["dependency_family"] for row in dependency_rows} == {
        "vehicle_dynamics_backend_source",
        "scenario_adapter_contract",
        "sensor_actor_interface_contract",
        "result_export_and_replay_contract",
    }
    assert {row["source_or_equivalent_trace_required"] for row in dependency_rows} == {True}
    assert {row["license_or_api_review_required_later"] for row in dependency_rows} == {True}
    assert {row["source_build_or_adapter_probe_required_later"] for row in dependency_rows} == {
        True
    }
    assert {row["external_install_allowed_in_m2611"] for row in dependency_rows} == {False}
    assert {row["external_import_allowed_in_m2611"] for row in dependency_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2611"] for row in dependency_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2611"] for row in dependency_rows} == {False}

    assert len(probe_rows) == 4
    assert set(probe_rows[0]) == set(PROBE_READINESS_FIELDNAMES)
    assert {row["selected_platform_family"] for row in probe_rows} == {SELECTED_PLATFORM_FAMILY}
    assert {row["probe_family"] for row in probe_rows} == {
        "source_tree_or_equivalent_trace_probe",
        "build_system_contract_probe",
        "state_action_adapter_contract_probe",
        "deterministic_replay_export_contract_probe",
    }
    assert {row["static_contract_defined_in_m2611"] for row in probe_rows} == {True}
    assert {row["source_build_executed_in_m2611"] for row in probe_rows} == {False}
    assert {row["adapter_probe_executed_in_m2611"] for row in probe_rows} == {False}
    assert {row["external_install_allowed_in_m2611"] for row in probe_rows} == {False}
    assert {row["external_import_allowed_in_m2611"] for row in probe_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2611"] for row in probe_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2611"] for row in probe_rows} == {False}

    assert len(protocol_rows) == 2
    assert set(protocol_rows[0]) == set(PROTOCOL_SKELETON_FIELDNAMES)
    assert {row["route_role_id"] for row in protocol_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in protocol_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in protocol_rows} == {ACTION_DIM}
    assert {row["protocol_skeleton_defined_in_m2611"] for row in protocol_rows} == {True}
    assert {row["reset_contract_required_later"] for row in protocol_rows} == {True}
    assert {row["rollout_contract_required_later"] for row in protocol_rows} == {True}
    assert {row["holdout_or_generalization_policy_required_later"] for row in protocol_rows} == {
        True
    }
    assert {row["source_build_or_adapter_probe_required_later"] for row in protocol_rows} == {
        True
    }
    assert {row["reset_allowed_in_m2611"] for row in protocol_rows} == {False}
    assert {row["policy_action_allowed_in_m2611"] for row in protocol_rows} == {False}
    assert {row["environment_step_allowed_in_m2611"] for row in protocol_rows} == {False}
    assert {row["rollout_allowed_in_m2611"] for row in protocol_rows} == {False}
    assert {row["external_validation_execution_allowed_in_m2611"] for row in protocol_rows} == {
        False
    }
    assert {row["validation_protocol_ready_in_m2611"] for row in protocol_rows} == {False}
    assert {row["validation_result_claim_allowed"] for row in protocol_rows} == {False}

    assert len(prerequisite_rows) == 2
    assert set(prerequisite_rows[0]) == set(VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES)
    assert {row["dependency_inventory_materialized_in_m2611"] for row in prerequisite_rows} == {
        True
    }
    assert {row["protocol_skeleton_materialized_in_m2611"] for row in prerequisite_rows} == {
        True
    }
    assert {row["source_build_or_adapter_probe_required_later"] for row in prerequisite_rows} == {
        True
    }
    assert {row["reset_feasibility_evidence_required_later"] for row in prerequisite_rows} == {
        True
    }
    assert {row["rollout_feasibility_evidence_required_later"] for row in prerequisite_rows} == {
        True
    }
    assert {row["executable_protocol_required_later"] for row in prerequisite_rows} == {True}
    assert {
        row["holdout_or_generalization_policy_required_later"] for row in prerequisite_rows
    } == {True}
    assert {row["validation_protocol_ready_in_m2611"] for row in prerequisite_rows} == {False}
    assert {row["validation_admission_granted_in_m2611"] for row in prerequisite_rows} == {
        False
    }
    assert {row["external_validation_execution_allowed_in_m2611"] for row in prerequisite_rows} == {
        False
    }
    assert {row["validation_result_claim_allowed"] for row in prerequisite_rows} == {False}

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

    assert len(claim_rows) == 20
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2611"]
    } == {
        "selected_platform_dependency_protocol_readiness_design_materialized",
        "selected_platform_dependency_inventory_materialized",
        "selected_platform_protocol_skeleton_materialized",
    }

    assert len(gate_rows) == 12
    assert set(gate_rows[0]) == set(GATE_FIELDNAMES)
    assert {row["status_pass"] for row in gate_rows} == {True}


def test_materialize_hf3_selected_platform_dependency_protocol_readiness_writes_expected_artifacts(
    tmp_path,
):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2611.md"

    summary = materialize_route_a_hf3_selected_platform_dependency_protocol_readiness(
        output_dir,
        milestone="m2611-test",
        next_blocker="m2612-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness_materialization_preflight_pass"
    )
    assert summary["dependency_inventory_row_count"] == 4
    assert summary["probe_readiness_row_count"] == 4
    assert summary["protocol_skeleton_row_count"] == 2
    assert summary["validation_admission_prerequisite_row_count"] == 2
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 20
    assert summary["materialization_gate_count"] == 12
    assert summary["source_artifacts_exist"] is True
    assert summary["m2607_status_pass"] is True
    assert summary["m2607_selected_platform_family"] == SELECTED_PLATFORM_FAMILY
    assert summary["selected_platform_dependency_protocol_readiness_design_materialized_in_m2611"] is True
    assert summary["selected_platform_dependency_inventory_materialized_in_m2611"] is True
    assert summary["selected_platform_protocol_skeleton_materialized_in_m2611"] is True
    assert summary["selected_platform_family_in_m2611"] == SELECTED_PLATFORM_FAMILY
    assert (
        summary[
            "selected_platform_dependency_protocol_readiness_design_materialized_claim_allowed"
        ]
        is True
    )
    assert summary["selected_platform_dependency_inventory_materialized_claim_allowed"] is True
    assert summary["selected_platform_protocol_skeleton_materialized_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2611"] is False
    assert summary["external_install_allowed_in_m2611"] is False
    assert summary["external_import_allowed_in_m2611"] is False
    assert summary["runtime_execution_allowed_in_m2611"] is False
    assert summary["dependency_mutation_allowed_in_m2611"] is False
    assert summary["source_build_executed_in_m2611"] is False
    assert summary["adapter_probe_executed_in_m2611"] is False
    assert summary["reset_allowed_in_m2611"] is False
    assert summary["policy_action_allowed_in_m2611"] is False
    assert summary["environment_step_allowed_in_m2611"] is False
    assert summary["rollout_allowed_in_m2611"] is False
    assert summary["external_validation_execution_allowed_in_m2611"] is False
    assert summary["validation_protocol_ready_in_m2611"] is False
    assert summary["validation_admission_granted_in_m2611"] is False
    assert summary["validation_result_claim_allowed"] is False
    assert summary["driver_performance_claim_allowed_in_m2611"] is False
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

    dependency_rows = _read_csv(output_dir / "hf3_selected_platform_dependency_inventory_rows.csv")
    probe_rows = _read_csv(
        output_dir / "hf3_selected_platform_source_build_adapter_probe_readiness_rows.csv"
    )
    protocol_rows = _read_csv(output_dir / "hf3_selected_platform_protocol_skeleton_rows.csv")
    prerequisite_rows = _read_csv(
        output_dir / "hf3_selected_platform_validation_admission_prerequisite_rows.csv"
    )
    guard_rows = _read_csv(output_dir / "hf3_selected_platform_actor_action_guard_rows.csv")
    claim_rows = _read_csv(
        output_dir / "hf3_selected_platform_dependency_protocol_claim_boundary_checks.csv"
    )
    gate_rows = _read_csv(output_dir / "selected_platform_dependency_protocol_readiness_gate_matrix.csv")

    assert len(dependency_rows) == 4
    assert len(probe_rows) == 4
    assert len(protocol_rows) == 2
    assert len(prerequisite_rows) == 2
    assert len(guard_rows) == 2
    assert len(claim_rows) == 20
    assert len(gate_rows) == 12
    assert {row["selected_platform_family"] for row in dependency_rows} == {
        SELECTED_PLATFORM_FAMILY
    }
    assert {row["external_install_allowed_in_m2611"] for row in dependency_rows} == {"False"}
    assert {row["external_import_allowed_in_m2611"] for row in dependency_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2611"] for row in dependency_rows} == {"False"}
    assert {row["dependency_mutation_allowed_in_m2611"] for row in dependency_rows} == {"False"}
    assert {row["source_build_executed_in_m2611"] for row in probe_rows} == {"False"}
    assert {row["adapter_probe_executed_in_m2611"] for row in probe_rows} == {"False"}
    assert {row["reset_allowed_in_m2611"] for row in protocol_rows} == {"False"}
    assert {row["policy_action_allowed_in_m2611"] for row in protocol_rows} == {"False"}
    assert {row["environment_step_allowed_in_m2611"] for row in protocol_rows} == {"False"}
    assert {row["rollout_allowed_in_m2611"] for row in protocol_rows} == {"False"}
    assert {row["external_validation_execution_allowed_in_m2611"] for row in protocol_rows} == {
        "False"
    }
    assert {row["validation_protocol_ready_in_m2611"] for row in protocol_rows} == {"False"}
    assert {row["validation_result_claim_allowed"] for row in prerequisite_rows} == {"False"}
    assert {row["selected_platform_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["protocol_status_actor_visible"] for row in guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2611"] == "True"
    } == {
        "selected_platform_dependency_protocol_readiness_design_materialized",
        "selected_platform_dependency_inventory_materialized",
        "selected_platform_protocol_skeleton_materialized",
    }
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
