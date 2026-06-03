import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_hf3_rollout_feasibility_execution import (
    ACTOR_VIEW_FIELDNAMES,
    BACKEND_STEP_FIELDNAMES,
    CLAIM_FIELDNAMES,
    POLICY_ACTION_FIELDNAMES,
    POLICY_SOURCE_FIELDNAMES,
    ROLLOUT_PLAN_FIELDNAMES,
    ROLLOUT_REQUEST_FIELDNAMES,
    build_claim_boundary_checks,
    build_fixed_policy_source_rows,
    build_rollout_plan_rows,
    build_rollout_request_rows,
    execute_rollout_feasibility_rows,
    materialize_route_a_hf3_rollout_feasibility_execution,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _m2568_request_rows():
    return _read_csv(
        Path(
            "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_request_rows.csv"
        )
    )


def _m2568_execution_rows():
    return _read_csv(
        Path(
            "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_execution_rows.csv"
        )
    )


def test_build_hf3_rollout_feasibility_rows_preserve_contract():
    request_rows = build_rollout_request_rows(_m2568_request_rows(), _m2568_execution_rows())
    policy_rows = build_fixed_policy_source_rows()
    plan_rows = build_rollout_plan_rows(request_rows, policy_rows)
    action_rows, step_rows, actor_view_rows = execute_rollout_feasibility_rows(request_rows, plan_rows)
    claim_rows = build_claim_boundary_checks(request_rows, action_rows, step_rows)

    assert len(request_rows) == 2
    assert set(request_rows[0]) == set(ROLLOUT_REQUEST_FIELDNAMES)
    assert {row["route_role_id"] for row in request_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in request_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in request_rows} == {ACTION_DIM}
    assert {row["policy_action_allowed_in_m2572"] for row in request_rows} == {True}
    assert {row["environment_step_allowed_in_m2572"] for row in request_rows} == {True}
    assert {row["rollout_allowed_in_m2572"] for row in request_rows} == {True}
    assert {row["pilot_admission_allowed"] for row in request_rows} == {False}
    assert {row["validation_claim_allowed"] for row in request_rows} == {False}
    assert {row["status_pass"] for row in request_rows} == {True}

    assert len(policy_rows) == 1
    assert set(policy_rows[0]) == set(POLICY_SOURCE_FIELDNAMES)
    assert policy_rows[0]["policy_source_id"] == "m1154_promoted_public_base_alpha_0_05"
    assert policy_rows[0]["ranking_role"] == "none"
    assert policy_rows[0]["promotion_allowed"] is False
    assert policy_rows[0]["status_pass"] is True

    assert len(plan_rows) == 2
    assert set(plan_rows[0]) == set(ROLLOUT_PLAN_FIELDNAMES)
    assert {row["target_horizon_steps"] for row in plan_rows} == {8}
    assert {row["success_rate_computation_allowed"] for row in plan_rows} == {False}
    assert {row["controller_family_verdict_allowed"] for row in plan_rows} == {False}

    assert len(action_rows) >= 2
    assert len(action_rows) <= 16
    assert set(action_rows[0]) == set(POLICY_ACTION_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in action_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in action_rows} == {ACTION_DIM}
    assert {row["action_finite"] for row in action_rows} == {True}
    assert {row["action_clipped_to_contract"] for row in action_rows} == {True}
    assert {row["policy_action_executed"] for row in action_rows} == {True}
    assert {row["hidden_oracle_actor_input_detected"] for row in action_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in action_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in action_rows} == {False}

    assert len(step_rows) == len(action_rows)
    assert set(step_rows[0]) == set(BACKEND_STEP_FIELDNAMES)
    assert {row["backend_class"] for row in step_rows} == {"CurrentSimDynamicsBackend"}
    assert {row["backend_step_attempted"] for row in step_rows} == {True}
    assert {row["actor_view_available_after_step"] for row in step_rows} == {True}
    assert {row["rollout_success_claim_allowed"] for row in step_rows} == {False}
    assert {row["validation_claim_allowed"] for row in step_rows} == {False}

    assert len(actor_view_rows) == len(step_rows) + 2
    assert set(actor_view_rows[0]) == set(ACTOR_VIEW_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in actor_view_rows} == {
        P0_OBSERVATION_DIM
    }
    assert {row["action_shape"] for row in actor_view_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_detected"] for row in actor_view_rows} == {False}
    assert {row["diagnostics_actor_visible"] for row in actor_view_rows} == {False}
    assert {row["taxonomy_label_actor_visible"] for row in actor_view_rows} == {False}
    assert {row["backend_status_actor_visible"] for row in actor_view_rows} == {False}
    assert {row["reset_outcome_actor_visible"] for row in actor_view_rows} == {False}
    assert {row["rollout_outcome_actor_visible"] for row in actor_view_rows} == {False}

    assert len(claim_rows) == 9
    assert set(claim_rows[0]) == set(CLAIM_FIELDNAMES)
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2572"]
    } == {"reset_execution_observed", "rollout_feasibility_execution_observed"}


def test_materialize_route_a_hf3_rollout_feasibility_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2572.md"

    summary = materialize_route_a_hf3_rollout_feasibility_execution(
        output_dir,
        milestone="m2572-test",
        next_blocker="m2573-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_rollout_feasibility_execution_materialization_preflight_pass"
    )
    assert summary["rollout_request_row_count"] == 2
    assert summary["fixed_policy_source_row_count"] == 1
    assert summary["rollout_plan_row_count"] == 2
    assert summary["policy_action_audit_row_count"] >= 2
    assert summary["policy_action_audit_row_count"] <= 16
    assert summary["backend_step_outcome_row_count"] == summary["policy_action_audit_row_count"]
    assert summary["actor_view_contract_row_count"] == summary["backend_step_outcome_row_count"] + 2
    assert summary["claim_boundary_check_count"] == 9
    assert summary["policy_action_executed"] is True
    assert summary["environment_step_executed"] is True
    assert summary["rollout_execution_run"] is True
    assert summary["reset_execution_observed_claim_allowed"] is True
    assert summary["rollout_feasibility_execution_observed_claim_allowed"] is True
    assert summary["rollout_success_claim_allowed"] is False
    assert summary["validation_claim_allowed"] is False
    assert summary["forbidden_claim_allowed_in_m2572"] is False
    assert summary["success_rate_computed"] is False
    assert summary["ranking_run"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["driver_performance_claim_made"] is False

    request_rows = _read_csv(output_dir / "hf3_rollout_request_rows.csv")
    policy_rows = _read_csv(output_dir / "hf3_fixed_policy_source_rows.csv")
    plan_rows = _read_csv(output_dir / "hf3_rollout_plan_rows.csv")
    action_rows = _read_csv(output_dir / "hf3_policy_action_audit_rows.csv")
    step_rows = _read_csv(output_dir / "hf3_backend_step_outcome_rows.csv")
    actor_view_rows = _read_csv(output_dir / "hf3_rollout_actor_view_contract_rows.csv")
    claim_rows = _read_csv(output_dir / "hf3_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "rollout_feasibility_gate_matrix.csv")

    assert len(request_rows) == 2
    assert len(policy_rows) == 1
    assert len(plan_rows) == 2
    assert len(action_rows) == summary["policy_action_audit_row_count"]
    assert len(step_rows) == summary["backend_step_outcome_row_count"]
    assert len(actor_view_rows) == summary["actor_view_contract_row_count"]
    assert len(claim_rows) == 9
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["policy_action_executed"] for row in action_rows} == {"True"}
    assert {row["backend_step_attempted"] for row in step_rows} == {"True"}
    assert {row["actor_view_available_after_step"] for row in step_rows} == {"True"}
    assert {row["validation_claim_allowed"] for row in step_rows} == {"False"}
    assert {row["actor_observation_shape"] for row in actor_view_rows} == {
        str(P0_OBSERVATION_DIM)
    }
    assert {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2572"] == "True"
    } == {"reset_execution_observed", "rollout_feasibility_execution_observed"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
