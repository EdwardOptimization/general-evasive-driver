from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_scenario_task_family_offtrack_collision_guardrail_materialization as materialization
from autodrift.artifacts import read_json, write_csv_rows


def _slice(
    *,
    axis: str,
    group_key: str,
    dominant: str,
    offtrack: int = 0,
    collision: int = 0,
    episode_count: int = 120,
) -> dict[str, object]:
    success = max(0, episode_count - offtrack - collision)
    return {
        "axis": axis,
        "group_key": group_key,
        "episode_count": episode_count,
        "success_count": success,
        "success_rate": success / max(1, episode_count),
        "failure_count": offtrack + collision,
        "failure_rate": (offtrack + collision) / max(1, episode_count),
        "offtrack_count": offtrack,
        "offtrack_rate": offtrack / max(1, episode_count),
        "collision_count": collision,
        "collision_rate": collision / max(1, episode_count),
        "max_step_noncompletion_count": 0,
        "max_step_noncompletion_rate": 0.0,
        "other_failure_count": 0,
        "other_failure_rate": 0.0,
        "mean_return": 1.0,
        "mean_steps": 40.0,
        "mean_min_clearance_margin": 0.1,
        "min_min_clearance_margin": -0.1 if collision else 0.1,
        "mean_high_sideslip_fraction": 0.0,
        "mean_action_rate": 0.1,
        "dominant_failure_mode": dominant,
        "dominant_failure_count": max(offtrack, collision),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _write_inputs(tmp_path: Path, *, sparse: bool = False) -> tuple[Path, Path, Path]:
    offtrack_specs = [
        ("termination_reason", "off_track"),
        ("outcome_bucket", "off_track_noncollision_noncompletion"),
        ("role_family", "R0_stable_avoidable"),
        ("role_family", "R1_aeb_infeasible_stable_aes"),
        ("sampled_obstacle_label", "drift_required"),
        ("sampled_obstacle_label", "aes_feasible"),
        ("obstacle_longitudinal_timing_bucket", "early_far"),
        ("obstacle_lateral_offset_bucket", "centerline"),
        ("hidden_dynamics_bucket", "slow_steer_actuator"),
    ]
    if sparse:
        offtrack_specs = offtrack_specs[:3]
    rows = [
        _slice(axis=axis, group_key=group, dominant="offtrack_dominated_failure", offtrack=110)
        for axis, group in offtrack_specs
    ]
    rows.extend(
        [
            _slice(axis="outcome_bucket", group_key="collision_failure", dominant="collision_dominated_failure", collision=90),
            _slice(axis="termination_reason", group_key="obstacle_collision", dominant="collision_dominated_failure", collision=88),
            _slice(axis="role_family", group_key="R4_unavoidable_mitigation", dominant="collision_dominated_failure", collision=70),
            _slice(axis="profile_name", group_key="L3_online_gru", dominant="offtrack_dominated_failure", offtrack=200),
            _slice(axis="profile_seed", group_key="L3_online_gru|222601", dominant="collision_dominated_failure", collision=120),
        ]
    )
    all_slices = tmp_path / "all_slices.csv"
    dominant_slices = tmp_path / "dominant_slices.csv"
    route = tmp_path / "route.csv"
    write_csv_rows(all_slices, rows)
    write_csv_rows(dominant_slices, rows)
    write_csv_rows(
        route,
        [
            {
                "route": "offtrack_primary_collision_guardrail_failure_slice_result_audit",
                "admitted": True,
            }
        ],
    )
    return all_slices, dominant_slices, route


def test_materialization_selects_non_profile_targets_and_guardrails(tmp_path: Path) -> None:
    all_slices, dominant_slices, route = _write_inputs(tmp_path)

    summary = materialization.run_materialization(
        all_slices_path=all_slices,
        dominant_slices_path=dominant_slices,
        route_recommendation_path=route,
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_pass"
    assert summary["offtrack_target_slice_count"] >= 8
    assert summary["collision_guardrail_slice_count"] >= 3
    assert summary["profile_target_slice_count"] == 0
    assert summary["profile_guardrail_slice_count"] == 0
    assert summary["profile_diagnostic_slice_count"] == 2
    assert summary["primary_route"] == "offtrack_primary_collision_guardrail_failure_slice_result_audit"
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False

    output = tmp_path / "out"
    assert (output / "offtrack_target_slices.csv").exists()
    assert (output / "collision_guardrail_slices.csv").exists()
    assert (output / "profile_diagnostic_slices.csv").exists()
    assert (output / "repair_gate_spec.json").exists()
    gate = read_json(output / "repair_gate_spec.json")
    assert gate["offtrack_target_policy"]["target_slice_count"] == summary["offtrack_target_slice_count"]
    assert gate["collision_guardrail_policy"]["guardrail_slice_count"] == summary["collision_guardrail_slice_count"]
    assert read_json(output / "summary.json")["next_blocker"] == "next"


def test_materialization_fails_when_offtrack_targets_are_too_sparse(tmp_path: Path) -> None:
    all_slices, dominant_slices, route = _write_inputs(tmp_path, sparse=True)

    summary = materialization.run_materialization(
        all_slices_path=all_slices,
        dominant_slices_path=dominant_slices,
        route_recommendation_path=route,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_fail"
    assert summary["offtrack_target_slice_count"] < 8
    assert summary["profile_target_slice_count"] == 0
    assert summary["profile_guardrail_slice_count"] == 0
