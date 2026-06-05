from __future__ import annotations

import csv
from pathlib import Path

import pytest

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization import (
    INTERVENTION_CONDITION_IDS,
    NORMAL_CONDITION_ID,
    materialize_source_only_action_response_belief_intervention_delta_panel,
)


ROLES = (
    "stable_avoidable",
    "stable_aes",
    "drift_required_recovery",
    "unavoidable_mitigation",
)
AXES = ("fresh_nominal_or_role_default", "fresh_fault_delay_noise")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _candidate_id(role: str, seed: int, axis: str) -> str:
    return f"m2773_{role}_seed_{seed}_{axis}"


def _condition_offset(condition_id: str) -> float:
    return {
        NORMAL_CONDITION_ID: 0.0,
        "reset_hidden_each_step": 0.10,
        "zero_previous_command_history": 0.20,
        "held_actuator_history": 0.30,
    }[condition_id]


def _write_m2773_fixture(tmp_path: Path, *, drop_one_intervention: bool = False) -> tuple[Path, Path]:
    m2773 = tmp_path / "m2773"
    m2773.mkdir()
    audit = tmp_path / "m2774.md"
    audit.write_text("# audit\n", encoding="utf-8")

    candidates = []
    execution_rows = []
    trace_rows = []
    matrix_rows = []
    mitigation_rows = []
    seed_base = 264100
    for role_index, role in enumerate(ROLES):
        for seed_index in range(4):
            for axis_index, axis in enumerate(AXES):
                seed = seed_base + role_index * 1000 + seed_index
                candidate_id = _candidate_id(role, seed, axis)
                mitigation = role == "unavoidable_mitigation"
                candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "role_family": role,
                        "dynamics_axis": axis,
                        "seed": seed,
                        "seed_index": seed_index,
                        "backend_id": "four_wheel_hf0",
                        "source_model": "FourWheelDriftModel",
                        "checkpoint_path": "actor.pt",
                        "horizon_steps": 1,
                        "source_only_surface_id": f"surface_{role}",
                        "fixture_id": f"fixture_{candidate_id}",
                        "base_fixture_id": f"base_{role}",
                        "ordinary_success_denominator_allowed": not mitigation,
                        "mitigation_reference": mitigation,
                        "actor_visible_labels": False,
                        "source_lineage": "test",
                    }
                )
                if mitigation:
                    mitigation_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "role_family": role,
                            "mitigation_reference": True,
                            "execution_scheduled": True,
                            "ordinary_success_denominator_allowed": False,
                            "actor_visible_allowed": False,
                            "claim_boundary": "m2773",
                        }
                    )
                for condition_id in (NORMAL_CONDITION_ID, *INTERVENTION_CONDITION_IDS):
                    matrix_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "intervention_condition_id": condition_id,
                            "execution_scheduled": True,
                            "matched_history_required": False,
                            "ordinary_denominator_allowed": not mitigation,
                            "expected_trace_rows": 1,
                            "stop_if_unresolved": True,
                        }
                    )
                    if (
                        drop_one_intervention
                        and candidate_id == _candidate_id("stable_avoidable", 264100, "fresh_nominal_or_role_default")
                        and condition_id == "held_actuator_history"
                    ):
                        continue
                    offset = _condition_offset(condition_id)
                    execution_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "intervention_condition_id": condition_id,
                            "role_family": role,
                            "dynamics_axis": axis,
                            "seed": seed,
                            "steps_executed": 1,
                            "backend_status": "running",
                            "action_finite": True,
                            "action_within_bounds": True,
                            "observation_shape": 72,
                            "action_shape": 3,
                            "collision_diagnostic": bool(condition_id == "held_actuator_history" and role == "stable_aes"),
                            "road_departure_diagnostic": bool(condition_id != NORMAL_CONDITION_ID and role == "drift_required_recovery"),
                            "minimum_obstacle_clearance_m": 10.0 + offset,
                            "minimum_road_margin_m": 1.0 - offset,
                            "trace_delta_proxy": 0.5 + offset,
                            "command_response_proxy": 2.0 + offset,
                            "diagnostic_only": True,
                        }
                    )
                    trace_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "intervention_condition_id": condition_id,
                            "role_family": role,
                            "dynamics_axis": axis,
                            "seed": seed,
                            "step_index": 0,
                            "steer": offset,
                            "throttle": 0.5,
                            "brake": 0.25,
                            "physical_steer": offset,
                            "physical_throttle": 0.5,
                            "physical_brake": 0.25,
                            "previous_steer_command": 0.0,
                            "previous_throttle_command": 0.0,
                            "previous_brake_command": 0.0,
                            "actuator_steer_state": 0.0,
                            "actuator_throttle_state": 0.0,
                            "actuator_brake_state": 0.0,
                            "vx_body": 5.0 + offset,
                            "vy_body": 0.0,
                            "yaw_rate": 0.0,
                            "ax_body": offset,
                            "ay_body": 0.0,
                            "state_x": 0.0,
                            "state_y": 0.0,
                            "state_vx": 5.0 + offset,
                            "state_vy": 0.0,
                            "state_speed": 5.0 + offset,
                            "state_yaw_rate": 0.0,
                            "backend_status": "running",
                            "trace_delta_proxy": 0.5 + offset,
                            "command_response_proxy": 2.0 + offset,
                            "finite_metric": True,
                        }
                    )

    conditions = [
        {
            "intervention_condition_id": condition_id,
            "intervention_family": "baseline" if condition_id == NORMAL_CONDITION_ID else "ablation",
            "recurrent_hidden_policy": "carry",
            "actor_view_history_policy": "test",
            "actor_input_shape_changed": False,
            "actor_input_feature_added": False,
            "hidden_or_oracle_value_added": False,
            "evaluator_only": condition_id != NORMAL_CONDITION_ID,
            "actor_visible_label": False,
            "allowed_claim_scope": "test",
        }
        for condition_id in (NORMAL_CONDITION_ID, *INTERVENTION_CONDITION_IDS)
    ]
    actor_guards = [
        {
            "guard_id": f"m2773_actor_guard_{index}",
            "guard_family": "actor_contract",
            "protected_field": protected,
            "actor_visible_allowed": False,
            "actor_observation_shape": 72,
            "action_shape": 3,
            "status_pass": True,
            "evidence": "test",
            "claim_boundary": "m2773",
        }
        for index, protected in enumerate(
            (
                "P0_observation_72",
                "action_3",
                "steer_throttle_brake",
                "hidden_dynamics",
                "oracle_labels",
                "route_labels",
                "external_dependency",
            )
        )
    ]
    claim_rows = [
        {
            "claim_id": f"m2773_claim_{index}",
            "claim_family": f"claim_{index}",
            "claim_made": False,
            "allowed": False,
            "status_pass": True,
            "evidence": "test",
            "claim_boundary": "m2773",
        }
        for index in range(13)
    ]
    gate_rows = [
        {
            "gate_id": "source_artifacts_exist",
            "gate_family": "artifact",
            "status_pass": True,
            "observed": True,
            "expected": True,
            "failure_type": "",
            "claim_boundary": "m2773",
        }
    ]
    failure_rows: list[dict[str, object]] = []

    write_json(
        m2773 / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "candidate_row_count": 32,
            "intervention_execution_row_count": len(execution_rows),
            "action_response_trace_row_count": len(trace_rows),
            "horizon_steps": 1,
            "hidden_oracle_actor_input_detected": False,
            "actor_visible_label_detected": False,
        },
    )
    write_csv_rows(m2773 / "source_only_candidate_rows.csv", candidates)
    write_csv_rows(m2773 / "intervention_condition_rows.csv", conditions)
    write_csv_rows(m2773 / "candidate_intervention_matrix.csv", matrix_rows)
    write_csv_rows(m2773 / "intervention_execution_rows.csv", execution_rows)
    write_csv_rows(
        m2773 / "intervention_failure_rows.csv",
        failure_rows,
        fieldnames=["candidate_id", "intervention_condition_id", "failure_type", "failure_reason", "claim_boundary"],
    )
    write_csv_rows(m2773 / "action_response_trace_rows.csv", trace_rows)
    write_csv_rows(m2773 / "mitigation_reference_guard_rows.csv", mitigation_rows)
    write_csv_rows(m2773 / "actor_contract_guard_rows.csv", actor_guards)
    write_csv_rows(m2773 / "claim_boundary_rows.csv", claim_rows)
    write_csv_rows(m2773 / "gate_matrix.csv", gate_rows)
    return m2773, audit


def test_m2775_materializes_complete_normal_vs_intervention_delta_panel(tmp_path: Path) -> None:
    m2773, audit = _write_m2773_fixture(tmp_path)
    output_dir = tmp_path / "out"
    doc = tmp_path / "m2775.md"
    follow_up = tmp_path / "m2776.json"

    summary = materialize_source_only_action_response_belief_intervention_delta_panel(
        output_dir,
        m2774_audit=audit,
        m2773_dir=m2773,
        follow_up_manifest=follow_up,
        milestone="m2775-test",
        next_blocker="m2776-test",
        doc_path=doc,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["intervention_delta_row_count"] == 96
    assert summary["role_dynamics_delta_aggregate_row_count"] == 24
    assert summary["intervention_condition_delta_aggregate_row_count"] == 3
    assert summary["normal_execution_row_count"] == 32
    assert summary["evaluator_intervention_execution_row_count"] == 96
    assert summary["pairing_complete"] is True
    assert summary["trace_pair_accounting"] is True
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["actor_visible_label_detected"] is False
    assert summary["new_execution_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["level3_self_id_claim_made"] is False

    delta_rows = _read_csv(output_dir / "intervention_delta_rows.csv")
    assert len(delta_rows) == 96
    assert {row["intervention_condition_id"] for row in delta_rows} == set(INTERVENTION_CONDITION_IDS)
    assert {row["diagnostic_only"] for row in delta_rows} == {"True"}
    assert {row["ranking_admissible"] for row in delta_rows} == {"False"}
    assert {row["winner_selected"] for row in delta_rows} == {"False"}
    reset_row = next(row for row in delta_rows if row["intervention_condition_id"] == "reset_hidden_each_step")
    assert float(reset_row["action_l1_mean"]) == pytest.approx(0.1)
    assert float(reset_row["minimum_obstacle_clearance_m_delta"]) == pytest.approx(0.1)

    aggregates = _read_csv(output_dir / "intervention_condition_delta_aggregate_rows.csv")
    assert len(aggregates) == 3
    assert {row["role_family"] for row in aggregates} == {"ALL"}
    assert {row["ranking_admissible"] for row in aggregates} == {"False"}
    assert follow_up.exists()
    assert read_json(follow_up)["id"].startswith("m2776-")
    assert doc.exists()


def test_m2775_fails_gate_when_candidate_intervention_pair_is_missing(tmp_path: Path) -> None:
    m2773, audit = _write_m2773_fixture(tmp_path, drop_one_intervention=True)

    summary = materialize_source_only_action_response_belief_intervention_delta_panel(
        tmp_path / "out",
        m2774_audit=audit,
        m2773_dir=m2773,
        follow_up_manifest=tmp_path / "m2776.json",
        milestone="m2775-test",
        next_blocker="m2776-test",
        doc_path=tmp_path / "m2775.md",
    )

    assert summary["status_pass"] is False
    assert summary["pairing_complete"] is False
    assert summary["missing_pair_count"] == 1
    assert summary["intervention_delta_row_count"] == 95
    gate_rows = _read_csv(tmp_path / "out" / "gate_matrix.csv")
    pairing_gate = next(row for row in gate_rows if row["gate_id"] == "pairing_complete")
    assert pairing_gate["status_pass"] == "False"
