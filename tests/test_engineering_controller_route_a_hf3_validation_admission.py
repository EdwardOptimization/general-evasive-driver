import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_hf3_validation_admission import (
    ACTOR_ACTION_GUARD_FIELDNAMES,
    ADMISSION_CRITERIA_FIELDNAMES,
    CLAIM_FIELDNAMES,
    EVIDENCE_SUFFICIENCY_FIELDNAMES,
    EXTERNAL_PLATFORM_READINESS_FIELDNAMES,
    VALIDATION_ADMISSION_REQUEST_FIELDNAMES,
    build_actor_action_guard_rows,
    build_admission_criteria_rows,
    build_claim_boundary_checks,
    build_evidence_sufficiency_rows,
    build_external_platform_readiness_rows,
    build_validation_admission_request_rows,
    materialize_route_a_hf3_validation_admission,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2576_readiness_rows():
    return _read_csv(
        Path(
            "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/"
            "hf3_validation_readiness_request_rows.csv"
        )
    )


def test_build_hf3_validation_admission_rows_preserve_claim_boundary():
    admission_rows = build_validation_admission_request_rows(_m2576_readiness_rows())
    criteria_rows = build_admission_criteria_rows(admission_rows)
    platform_rows = build_external_platform_readiness_rows()
    evidence_rows = build_evidence_sufficiency_rows()
    guard_rows = build_actor_action_guard_rows(admission_rows)
    claim_rows = build_claim_boundary_checks(
        admission_rows,
        criteria_rows,
        platform_rows,
        evidence_rows,
        guard_rows,
    )

    assert len(admission_rows) == 2
    assert set(admission_rows[0]) == set(VALIDATION_ADMISSION_REQUEST_FIELDNAMES)
    assert {row["admission_request_id"] for row in admission_rows} == {
        "stable_aes_aeb_infeasible_validation_admission_request",
        "stable_avoidable_aeb_feasible_validation_admission_request",
    }
    assert {row["route_role_id"] for row in admission_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in admission_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in admission_rows} == {ACTION_DIM}
    assert {row["boundary_materialized"] for row in admission_rows} == {True}
    assert {row["validation_admission_granted_in_m2580"] for row in admission_rows} == {False}
    assert {row["validation_execution_allowed_in_m2580"] for row in admission_rows} == {False}
    assert {row["external_simulation_allowed_in_m2580"] for row in admission_rows} == {False}

    assert len(criteria_rows) == 12
    assert set(criteria_rows[0]) == set(ADMISSION_CRITERIA_FIELDNAMES)
    assert {row["criteria_family"] for row in criteria_rows} == {
        "boundary_materialization_accepted",
        "actor_action_contract_preserved",
        "external_platform_ready",
        "validation_protocol_defined",
        "claim_boundary_audited",
        "holdout_or_generalization_policy_defined",
    }
    assert {
        row["criteria_family"]
        for row in criteria_rows
        if row["criteria_satisfied_by_m2580"]
    } == {"boundary_materialization_accepted", "actor_action_contract_preserved"}
    assert {
        row["criteria_family"]
        for row in criteria_rows
        if row["required_before_validation_admission"]
    } == {
        "external_platform_ready",
        "validation_protocol_defined",
        "claim_boundary_audited",
        "holdout_or_generalization_policy_defined",
    }

    assert len(platform_rows) == 3
    assert set(platform_rows[0]) == set(EXTERNAL_PLATFORM_READINESS_FIELDNAMES)
    assert {row["install_allowed_in_m2580"] for row in platform_rows} == {False}
    assert {row["import_allowed_in_m2580"] for row in platform_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2580"] for row in platform_rows} == {False}
    assert {row["platform_selected_in_m2580"] for row in platform_rows} == {False}
    assert {
        row["platform_family"]
        for row in platform_rows
        if row["open_auditable_backend_required"]
    } == {"chrono_vehicle_or_equivalent_open_backend"}

    assert len(evidence_rows) == 7
    assert set(evidence_rows[0]) == set(EVIDENCE_SUFFICIENCY_FIELDNAMES)
    assert {
        row["evidence_family"]
        for row in evidence_rows
        if row["available_in_m2580"]
    } == {
        "m2576_boundary_materialization",
        "m2577_boundary_audit",
        "m2578_boundary_synthesis",
    }
    assert {
        row["evidence_family"]
        for row in evidence_rows
        if not row["available_in_m2580"]
    } == {
        "external_platform_selection",
        "validation_protocol",
        "validation_execution_result",
        "claim_boundary_audit_after_admission",
    }
    assert any(row["missing_before_validation_admission"] for row in evidence_rows)
    assert any(row["missing_before_validation_readiness"] for row in evidence_rows)
    assert any(row["missing_before_validation_result"] for row in evidence_rows)

    assert len(guard_rows) == 2
    assert set(guard_rows[0]) == set(ACTOR_ACTION_GUARD_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in guard_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in guard_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in guard_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in guard_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in guard_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in guard_rows} == {False}
    assert {row["reset_outcome_actor_visible"] for row in guard_rows} == {False}
    assert {row["rollout_outcome_actor_visible"] for row in guard_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in guard_rows} == {False}
    assert {row["action_contract_mutation_detected"] for row in guard_rows} == {False}

    assert len(claim_rows) == 12
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2580"]
    } == {"validation_admission_design_materialized"}


def test_materialize_route_a_hf3_validation_admission_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2580.md"

    summary = materialize_route_a_hf3_validation_admission(
        output_dir,
        milestone="m2580-test",
        next_blocker="m2581-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_validation_admission_materialization_preflight_pass"
    )
    assert summary["admission_request_row_count"] == 2
    assert summary["admission_criteria_row_count"] == 12
    assert summary["external_platform_readiness_row_count"] == 3
    assert summary["evidence_sufficiency_row_count"] == 7
    assert summary["actor_action_guard_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 12
    assert summary["materialization_gate_count"] == 9
    assert summary["validation_admission_design_materialized_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2580"] is False
    assert summary["validation_admission_granted"] is False
    assert summary["validation_execution_allowed_in_m2580"] is False
    assert summary["external_simulation_allowed_in_m2580"] is False
    assert summary["install_allowed_in_m2580"] is False
    assert summary["import_allowed_in_m2580"] is False
    assert summary["runtime_execution_allowed_in_m2580"] is False
    assert summary["platform_selected_in_m2580"] is False
    assert summary["missing_evidence_before_validation_admission"] is True
    assert summary["missing_evidence_before_validation_readiness"] is True
    assert summary["missing_evidence_before_validation_result"] is True
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["validation_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    admission_rows = _read_csv(output_dir / "hf3_validation_admission_request_rows.csv")
    criteria_rows = _read_csv(output_dir / "hf3_admission_criteria_rows.csv")
    platform_rows = _read_csv(output_dir / "hf3_external_platform_readiness_rows.csv")
    evidence_rows = _read_csv(output_dir / "hf3_evidence_sufficiency_rows.csv")
    guard_rows = _read_csv(output_dir / "hf3_actor_action_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "validation_admission_gate_matrix.csv")

    assert len(admission_rows) == 2
    assert len(criteria_rows) == 12
    assert len(platform_rows) == 3
    assert len(evidence_rows) == 7
    assert len(guard_rows) == 2
    assert len(claim_rows) == 12
    assert len(gate_rows) == 9
    assert {row["validation_admission_granted_in_m2580"] for row in admission_rows} == {"False"}
    assert {row["validation_execution_allowed_in_m2580"] for row in admission_rows} == {"False"}
    assert {row["external_simulation_allowed_in_m2580"] for row in admission_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2580"] for row in platform_rows} == {"False"}
    assert {row["platform_selected_in_m2580"] for row in platform_rows} == {"False"}
    assert {row["validation_outcome_actor_visible"] for row in guard_rows} == {"False"}
    assert {row["action_contract_mutation_detected"] for row in guard_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2580"] == "True"
    } == {"validation_admission_design_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
