import csv
import json
from pathlib import Path

from autodrift.engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas import (
    run_obstacle_clearance_regression_atlas,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DYNAMICS_AXES,
    ORDINARY_ROLE_FAMILIES,
    STRESS_FAMILIES,
)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _source_pairs():
    pairs = []
    for role in ORDINARY_ROLE_FAMILIES:
        for axis in DYNAMICS_AXES:
            for stress in STRESS_FAMILIES:
                for seed_index in range(8, 12):
                    seed = 266100 + seed_index
                    pair_id = f"pair_{role}_{axis}_{stress}_{seed_index}"
                    pairs.append((pair_id, role, axis, stress, seed_index, seed))
    assert len(pairs) == 72
    return pairs


def _delta_rows(delta_family: str, negative_count: int):
    reference_subject = "source" if delta_family == "candidate_minus_source" else "base_candidate"
    rows = []
    for index, (pair_id, role, axis, stress, seed_index, seed) in enumerate(_source_pairs()):
        negative = index < negative_count
        clearance_delta = -0.001 - index * 0.000001 if negative else 0.001 + index * 0.000001
        rows.append(
            {
                "delta_family": delta_family,
                "pair_id": pair_id,
                "role_family": role,
                "dynamics_axis": axis,
                "stress_family": stress,
                "seed_index": seed_index,
                "seed": seed,
                "reference_subject": reference_subject,
                "candidate_subject": "candidate",
                "reference_execution_row_id": f"{pair_id}_{reference_subject}",
                "candidate_execution_row_id": f"{pair_id}_candidate",
                "reference_checkpoint": f"{reference_subject}.pt",
                "candidate_checkpoint": "candidate.pt",
                "reference_checkpoint_hash": f"{reference_subject}_hash",
                "candidate_checkpoint_hash": "candidate_hash",
                "reference_steps_executed": 140,
                "candidate_steps_executed": 140,
                "candidate_minus_reference_minimum_obstacle_clearance_m": clearance_delta,
                "candidate_minus_reference_minimum_road_margin_m": 0.004,
                "candidate_minus_reference_final_road_margin_m": 0.003,
                "candidate_minus_reference_final_speed_mps": 0.002,
                "candidate_minus_reference_max_abs_yaw_rate": -0.0005,
                "candidate_minus_reference_max_abs_y": -0.004,
                "candidate_minus_reference_throttle_brake_conflict_proxy": 0.0,
                "candidate_minus_reference_mean_throttle": 0.0,
                "candidate_minus_reference_mean_brake": 0.0,
                "candidate_minus_reference_mean_action_l1": 0.0002,
                "candidate_minus_reference_command_response_proxy": 0.001,
                "mean_action_delta_l1": 0.0002,
                "paired_row_complete": True,
                "finite_delta": True,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "success_rate_verdict_computed": False,
                "claim_scope": "test",
                "forbidden_interpretation": "test",
            }
        )
    return rows


def _triad_rows():
    rows = []
    for pair_id, role, axis, stress, seed_index, seed in _source_pairs():
        for subject in ("source", "base_candidate", "candidate"):
            rows.append(
                {
                    "pair_id": pair_id,
                    "execution_row_id": f"{pair_id}_{subject}",
                    "checkpoint_subject": subject,
                    "checkpoint_path": f"{subject}.pt",
                    "checkpoint_hash": f"{subject}_hash",
                    "model_state_hash": f"{subject}_state_hash",
                    "role_family": role,
                    "dynamics_axis": axis,
                    "stress_family": stress,
                    "seed_index": seed_index,
                    "seed": seed,
                    "source_curriculum_row_id": f"curriculum_{role}_{axis}_{stress}",
                    "fixture_id": f"fixture_{seed}",
                    "stress_preparation": "test",
                    "warmup_step_count": 1,
                    "horizon_steps": 140,
                    "steps_executed": 140,
                    "observation_shape": 72,
                    "action_shape": 3,
                    "reset_run": True,
                    "policy_action_run": True,
                    "backend_step_run": True,
                    "closed_loop_rollout_run": True,
                    "finite_observation": True,
                    "finite_action": True,
                    "action_within_bounds": True,
                    "backend_terminated": False,
                    "backend_truncated": False,
                    "backend_status": "running",
                    "minimum_obstacle_clearance_m": 1.0,
                    "minimum_road_margin_m": -1.0,
                    "final_road_margin_m": -0.5,
                    "collision_diagnostic": False,
                    "road_departure_diagnostic": True,
                    "final_speed_mps": 3.0,
                    "max_abs_yaw_rate": 0.5,
                    "max_abs_y": 4.0,
                    "mean_throttle": 0.0,
                    "mean_brake": 1.0,
                    "throttle_brake_conflict_proxy": 0.0,
                    "max_abs_steer": 0.9,
                    "mean_abs_steer": 0.8,
                    "mean_action_l1": 0.9,
                    "command_response_proxy": 4.0,
                    "actor_visible_label": False,
                    "hidden_or_oracle_actor_inputs_required": False,
                    "ordinary_denominator_allowed": True,
                    "mitigation_reference": False,
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                    "claim_scope": "test",
                    "forbidden_interpretation": "test",
                }
            )
    assert len(rows) == 216
    return rows


def _write_m2793_sources(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "gate_matrix_pass": True,
                "triad_execution_row_count": 216,
                "candidate_minus_source_delta_row_count": 72,
                "candidate_minus_base_delta_row_count": 72,
                "actor_contract_shape_72_action_3": True,
            }
        ),
        encoding="utf-8",
    )
    _write_rows(path / "triad_execution_rows.csv", _triad_rows())
    _write_rows(path / "candidate_minus_source_delta_rows.csv", _delta_rows("candidate_minus_source", 42))
    _write_rows(path / "candidate_minus_base_delta_rows.csv", _delta_rows("candidate_minus_base", 43))
    _write_rows(
        path / "gate_matrix.csv",
        [
            {
                "gate_id": "m2793_gate",
                "gate_tier": "proof",
                "gate_family": "artifact",
                "status_pass": True,
                "observed": "ok",
                "expected": "ok",
                "row_count": 1,
                "failure_type": "",
                "claim_boundary": "test",
            }
        ],
    )
    _write_rows(
        path / "mitigation_reference_guard_rows.csv",
        [
            {
                "source_guard_id": "mitigation_a",
                "candidate_id": "mitigation_a",
                "role_family": "unavoidable_mitigation",
                "dynamics_axis": "fresh_nominal_or_role_default",
                "seed": 267100,
                "mitigation_reference": True,
                "ordinary_denominator_allowed": False,
                "future_training_allowed": False,
                "future_execution_allowed": False,
                "context_only": True,
                "actor_visible_allowed": False,
                "included_in_paired_execution_rows": False,
                "included_in_delta_rows": False,
                "status_pass": True,
                "guard_family": "test",
                "claim_boundary": "test",
            }
        ],
    )


def test_m2796_clearance_regression_atlas_reanalyzes_m2793_deltas(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2796.md"
    follow_up_manifest = tmp_path / "m2797.json"
    m2795_synthesis = tmp_path / "m2795.md"
    m2794_audit = tmp_path / "m2794.md"
    m2793_dir = tmp_path / "m2793"
    m2795_synthesis.write_text("# synthesis\n", encoding="utf-8")
    m2794_audit.write_text("# audit\n", encoding="utf-8")
    _write_m2793_sources(m2793_dir)

    summary = run_obstacle_clearance_regression_atlas(
        output_dir,
        m2795_synthesis=m2795_synthesis,
        m2794_audit=m2794_audit,
        m2793_dir=m2793_dir,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["new_execution_run"] is False
    assert summary["new_training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["candidate_minus_source_clearance_negative_count"] == 42
    assert summary["candidate_minus_source_clearance_positive_count"] == 30
    assert summary["candidate_minus_base_clearance_negative_count"] == 43
    assert summary["candidate_minus_base_clearance_positive_count"] == 29
    assert summary["clearance_regression_row_count"] == 144
    assert summary["m2797_follow_up_manifest_registered"] is True

    atlas_rows = _read_csv(output_dir / "clearance_regression_rows.csv")
    aggregate_rows = _read_csv(output_dir / "clearance_regression_aggregate_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    follow_up = json.loads(follow_up_manifest.read_text(encoding="utf-8"))

    assert len(atlas_rows) == 144
    assert {row["delta_family"] for row in atlas_rows} == {
        "candidate_minus_source",
        "candidate_minus_base",
    }
    assert sum(row["clearance_regression"] == "True" for row in atlas_rows) == 85
    assert {
        "global",
        "delta_family",
        "role_family",
        "dynamics_axis",
        "stress_family",
        "seed_index",
        "delta_family_role_dynamics_stress",
        "delta_family_role_dynamics_stress_seed",
    }.issubset({row["group_family"] for row in aggregate_rows})
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert mitigation_rows[0]["ordinary_denominator_allowed"] == "False"
    assert mitigation_rows[0]["included_in_delta_rows"] == "False"
    assert follow_up["id"] == (
        "m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-"
        "clearance-regression-atlas-result-audit"
    )
    assert doc_path.read_text(encoding="utf-8").strip()
