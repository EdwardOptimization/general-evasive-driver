import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_hf3_low_cost_pilot_materialization import (
    CLAIM_BOUNDARY_FIELDNAMES,
    EXTERNAL_BOUNDARY_FIELDNAMES,
    PILOT_CANDIDATE_FIELDNAMES,
    RESET_FEASIBILITY_FIELDNAMES,
    ROLLOUT_FEASIBILITY_FIELDNAMES,
    build_claim_boundary_checks,
    build_external_backend_boundary_checks,
    build_pilot_candidate_rows,
    build_reset_feasibility_rows,
    build_rollout_feasibility_rows,
    materialize_route_a_hf3_low_cost_pilot_preflight,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _hf2_binding_rows():
    return _read_csv(
        Path(
            "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_surface_fixture_binding.csv"
        )
    )


def test_build_hf3_preflight_rows_preserve_boundaries():
    candidate_rows = build_pilot_candidate_rows(_hf2_binding_rows())
    reset_rows = build_reset_feasibility_rows(candidate_rows)
    rollout_rows = build_rollout_feasibility_rows(candidate_rows)
    external_rows = build_external_backend_boundary_checks()
    claim_rows = build_claim_boundary_checks()

    assert len(candidate_rows) == 2
    assert set(candidate_rows[0]) == set(PILOT_CANDIDATE_FIELDNAMES)
    assert {row["route_role_id"] for row in candidate_rows} == {
        "stable_avoidable_aeb_feasible",
        "stable_aes_aeb_infeasible",
    }
    assert {row["actor_observation_shape"] for row in candidate_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in candidate_rows} == {ACTION_DIM}
    assert {row["hf3_admission_status"] for row in candidate_rows} == {
        "requires_m2560_reset_and_rollout_feasibility"
    }
    assert {row["validation_claim_allowed"] for row in candidate_rows} == {False}
    assert {row["status_pass"] for row in candidate_rows} == {True}

    assert len(reset_rows) == 2
    assert set(reset_rows[0]) == set(RESET_FEASIBILITY_FIELDNAMES)
    assert {row["policy_action_allowed_in_m2560"] for row in reset_rows} == {False}
    assert {row["environment_step_allowed_in_m2560"] for row in reset_rows} == {False}
    assert {row["reset_success_claim_allowed"] for row in reset_rows} == {False}
    assert {row["status_pass"] for row in reset_rows} == {True}

    assert len(rollout_rows) == 2
    assert set(rollout_rows[0]) == set(ROLLOUT_FEASIBILITY_FIELDNAMES)
    assert {row["rollout_execution_allowed_in_m2560"] for row in rollout_rows} == {False}
    assert {row["success_rate_claim_allowed"] for row in rollout_rows} == {False}
    assert {row["controller_family_verdict_allowed"] for row in rollout_rows} == {False}
    assert {row["status_pass"] for row in rollout_rows} == {True}

    assert len(external_rows) == 6
    assert set(external_rows[0]) == set(EXTERNAL_BOUNDARY_FIELDNAMES)
    assert {row["install_allowed"] for row in external_rows} == {False}
    assert {row["import_allowed"] for row in external_rows} == {False}
    assert {row["simulation_run_allowed"] for row in external_rows} == {False}
    assert {row["policy_action_allowed"] for row in external_rows} == {False}
    assert {row["environment_step_allowed"] for row in external_rows} == {False}

    assert len(claim_rows) == 7
    assert set(claim_rows[0]) == set(CLAIM_BOUNDARY_FIELDNAMES)
    assert {row["claim_allowed_in_m2560"] for row in claim_rows} == {False}
    assert {row["status_pass"] for row in claim_rows} == {True}


def test_materialize_route_a_hf3_low_cost_pilot_preflight_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2560.md"

    summary = materialize_route_a_hf3_low_cost_pilot_preflight(
        output_dir,
        milestone="m2560-test",
        next_blocker="m2561-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf3_low_cost_pilot_materialization_preflight_pass"
    )
    assert summary["pilot_candidate_row_count"] == 2
    assert summary["pilot_candidate_rows_all_pass"] is True
    assert summary["reset_feasibility_row_count"] == 2
    assert summary["reset_feasibility_rows_all_pass"] is True
    assert summary["rollout_feasibility_row_count"] == 2
    assert summary["rollout_feasibility_rows_all_pass"] is True
    assert summary["external_boundary_check_count"] == 6
    assert summary["external_boundary_checks_all_pass"] is True
    assert summary["claim_boundary_check_count"] == 7
    assert summary["claim_boundary_checks_all_pass"] is True
    assert summary["candidate_rows_pilot_admitted"] is False
    assert summary["policy_action_allowed_in_m2560"] is False
    assert summary["environment_step_allowed_in_m2560"] is False
    assert summary["rollout_execution_allowed_in_m2560"] is False
    assert summary["claim_allowed_in_m2560"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["driver_performance_claim_made"] is False

    candidate_rows = _read_csv(output_dir / "hf3_pilot_candidate_rows.csv")
    reset_rows = _read_csv(output_dir / "hf3_reset_feasibility_plan.csv")
    rollout_rows = _read_csv(output_dir / "hf3_rollout_feasibility_plan.csv")
    external_rows = _read_csv(output_dir / "hf3_external_backend_boundary_checks.csv")
    claim_rows = _read_csv(output_dir / "hf3_claim_boundary_checks.csv")
    gate_rows = _read_csv(output_dir / "materialization_gate_matrix.csv")

    assert len(candidate_rows) == 2
    assert len(reset_rows) == 2
    assert len(rollout_rows) == 2
    assert len(external_rows) == 6
    assert len(claim_rows) == 7
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["actor_observation_shape"] for row in candidate_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in candidate_rows} == {str(ACTION_DIM)}
    assert {row["hf3_admission_status"] for row in candidate_rows} == {
        "requires_m2560_reset_and_rollout_feasibility"
    }
    assert {row["policy_action_allowed_in_m2560"] for row in reset_rows} == {"False"}
    assert {row["rollout_execution_allowed_in_m2560"] for row in rollout_rows} == {"False"}
    assert {row["simulation_run_allowed"] for row in external_rows} == {"False"}
    assert {row["claim_allowed_in_m2560"] for row in claim_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
