import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_hf3_validation_readiness_boundary import (
    ACTOR_INPUT_ISOLATION_FIELDNAMES,
    CLAIM_FIELDNAMES,
    DEPENDENCY_POLICY_FIELDNAMES,
    DISCREPANCY_QUESTION_FIELDNAMES,
    EVIDENCE_ADMISSION_FIELDNAMES,
    PLATFORM_BOUNDARY_FIELDNAMES,
    READINESS_REQUEST_FIELDNAMES,
    build_actor_input_isolation_rows,
    build_claim_boundary_checks,
    build_dependency_policy_rows,
    build_discrepancy_question_rows,
    build_evidence_admission_rows,
    build_platform_boundary_rows,
    build_readiness_request_rows,
    materialize_route_a_hf3_validation_readiness_boundary,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2572_request_rows():
    return _read_csv(
        Path(
            "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_request_rows.csv"
        )
    )


def test_build_hf3_validation_readiness_boundary_rows_preserve_claim_boundary():
    readiness_rows = build_readiness_request_rows(_m2572_request_rows())
    evidence_rows = build_evidence_admission_rows(readiness_rows)
    platform_rows = build_platform_boundary_rows()
    dependency_rows = build_dependency_policy_rows()
    discrepancy_rows = build_discrepancy_question_rows(readiness_rows)
    actor_input_rows = build_actor_input_isolation_rows(readiness_rows)
    claim_rows = build_claim_boundary_checks(
        readiness_rows,
        evidence_rows,
        platform_rows,
        dependency_rows,
        discrepancy_rows,
        actor_input_rows,
    )

    assert len(readiness_rows) == 2
    assert set(readiness_rows[0]) == set(READINESS_REQUEST_FIELDNAMES)
    assert {row["route_role_id"] for row in readiness_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in readiness_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in readiness_rows} == {ACTION_DIM}
    assert {row["accepted_feasibility_evidence"] for row in readiness_rows} == {True}
    assert {row["validation_admission_allowed"] for row in readiness_rows} == {False}
    assert {row["validation_execution_allowed_in_m2576"] for row in readiness_rows} == {False}
    assert {row["external_simulation_allowed_in_m2576"] for row in readiness_rows} == {False}

    assert len(evidence_rows) == 12
    assert set(evidence_rows[0]) == set(EVIDENCE_ADMISSION_FIELDNAMES)
    assert {row["accepted_as_boundary_input"] for row in evidence_rows} == {True}
    assert {row["accepted_as_validation_result"] for row in evidence_rows} == {False}
    assert {row["accepted_as_driver_performance"] for row in evidence_rows} == {False}
    assert {row["accepted_as_ranking_evidence"] for row in evidence_rows} == {False}

    assert len(platform_rows) == 3
    assert set(platform_rows[0]) == set(PLATFORM_BOUNDARY_FIELDNAMES)
    assert {row["external_high_fidelity_execution_allowed_in_m2576"] for row in platform_rows} == {False}
    assert {row["external_validation_result_allowed"] for row in platform_rows} == {False}

    assert len(dependency_rows) == 3
    assert set(dependency_rows[0]) == set(DEPENDENCY_POLICY_FIELDNAMES)
    assert {row["install_allowed_in_m2576"] for row in dependency_rows} == {False}
    assert {row["import_allowed_in_m2576"] for row in dependency_rows} == {False}
    assert {row["runtime_execution_allowed_in_m2576"] for row in dependency_rows} == {False}
    assert {row["dependency_mutation_allowed_in_m2576"] for row in dependency_rows} == {False}

    assert len(discrepancy_rows) == 8
    assert set(discrepancy_rows[0]) == set(DISCREPANCY_QUESTION_FIELDNAMES)
    assert {row["requires_external_validation_execution"] for row in discrepancy_rows} == {True}
    assert {row["answer_allowed_in_m2576"] for row in discrepancy_rows} == {False}
    assert {row["driver_performance_claim_allowed"] for row in discrepancy_rows} == {False}

    assert len(actor_input_rows) == 2
    assert set(actor_input_rows[0]) == set(ACTOR_INPUT_ISOLATION_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_input_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_input_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_input_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in actor_input_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in actor_input_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in actor_input_rows} == {False}
    assert {row["reset_outcome_actor_visible"] for row in actor_input_rows} == {False}
    assert {row["rollout_outcome_actor_visible"] for row in actor_input_rows} == {False}
    assert {row["validation_outcome_actor_visible"] for row in actor_input_rows} == {False}

    assert len(claim_rows) == 12
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2576"]
    } == {"validation_readiness_boundary_materialized"}


def test_materialize_route_a_hf3_validation_readiness_boundary_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2576.md"

    summary = materialize_route_a_hf3_validation_readiness_boundary(
        output_dir,
        milestone="m2576-test",
        next_blocker="m2577-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_validation_readiness_boundary_materialization_preflight_pass"
    )
    assert summary["readiness_request_row_count"] == 2
    assert summary["evidence_admission_row_count"] == 12
    assert summary["platform_boundary_row_count"] == 3
    assert summary["dependency_policy_row_count"] == 3
    assert summary["scenario_discrepancy_question_row_count"] == 8
    assert summary["actor_input_isolation_row_count"] == 2
    assert summary["claim_boundary_check_count"] == 12
    assert summary["validation_readiness_boundary_materialized_claim_allowed"] is True
    assert summary["forbidden_claim_allowed_in_m2576"] is False
    assert summary["validation_admission_allowed"] is False
    assert summary["validation_execution_allowed_in_m2576"] is False
    assert summary["external_simulation_allowed_in_m2576"] is False
    assert summary["accepted_as_validation_result"] is False
    assert summary["accepted_as_driver_performance"] is False
    assert summary["accepted_as_ranking_evidence"] is False
    assert summary["install_allowed_in_m2576"] is False
    assert summary["import_allowed_in_m2576"] is False
    assert summary["runtime_execution_allowed_in_m2576"] is False
    assert summary["hf4_answer_allowed_in_m2576"] is False
    assert summary["answer_allowed_in_m2576"] is False
    assert summary["repo_local_boundary_only"] is True
    assert summary["validation_execution_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["rollout_execution_run"] is False
    assert summary["driver_performance_claim_made"] is False

    readiness_rows = _read_csv(output_dir / "hf3_validation_readiness_request_rows.csv")
    evidence_rows = _read_csv(output_dir / "hf3_evidence_admission_rows.csv")
    platform_rows = _read_csv(output_dir / "hf3_platform_boundary_rows.csv")
    dependency_rows = _read_csv(output_dir / "hf3_dependency_policy_rows.csv")
    discrepancy_rows = _read_csv(output_dir / "hf3_scenario_discrepancy_question_rows.csv")
    actor_input_rows = _read_csv(output_dir / "hf3_actor_input_isolation_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "validation_readiness_gate_matrix.csv")

    assert len(readiness_rows) == 2
    assert len(evidence_rows) == 12
    assert len(platform_rows) == 3
    assert len(dependency_rows) == 3
    assert len(discrepancy_rows) == 8
    assert len(actor_input_rows) == 2
    assert len(claim_rows) == 12
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["validation_execution_allowed_in_m2576"] for row in readiness_rows} == {"False"}
    assert {row["external_simulation_allowed_in_m2576"] for row in readiness_rows} == {"False"}
    assert {row["accepted_as_validation_result"] for row in evidence_rows} == {"False"}
    assert {row["external_validation_result_allowed"] for row in platform_rows} == {"False"}
    assert {row["runtime_execution_allowed_in_m2576"] for row in dependency_rows} == {"False"}
    assert {row["answer_allowed_in_m2576"] for row in discrepancy_rows} == {"False"}
    assert {row["validation_outcome_actor_visible"] for row in actor_input_rows} == {"False"}
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2576"] == "True"
    } == {"validation_readiness_boundary_materialized"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
