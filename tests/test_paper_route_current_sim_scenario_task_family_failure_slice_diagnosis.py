from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_scenario_task_family_failure_slice_diagnosis as diagnosis
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    workload_id: str,
    role: str = "R0_stable_avoidable",
    profile: str = "L0_current_masked",
    profile_seed: str = "L0_current_masked|222601",
    outcome_bucket: str = "success_obstacle_pass",
    termination_reason: str = "obstacle_completed",
    collision: bool = False,
    obstacle_completed: bool = True,
    return_value: float = 30.0,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "role_family": role,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "sampled_obstacle_label": "aeb_feasible" if role.startswith("R0") else "unavoidable",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "hidden_dynamics_bucket": "nominal",
        "profile_name": profile,
        "profile_seed": profile_seed,
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "collision": collision,
        "obstacle_completed": obstacle_completed,
        "success": obstacle_completed and not collision,
        "truncated": False,
        "return": return_value,
        "steps": 40,
        "min_clearance_margin": 0.25 if not collision else -0.1,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.05,
    }


def _offtrack(index: int, *, role: str = "R0_stable_avoidable") -> dict[str, object]:
    return _episode(
        workload_id=f"offtrack-{index}",
        role=role,
        outcome_bucket="off_track_noncollision_noncompletion",
        termination_reason="off_track",
        obstacle_completed=False,
        return_value=5.0,
    )


def _collision(index: int, *, role: str = "R4_unavoidable_mitigation") -> dict[str, object]:
    return _episode(
        workload_id=f"collision-{index}",
        role=role,
        outcome_bucket="collision_failure",
        termination_reason="obstacle_collision",
        collision=True,
        obstacle_completed=False,
        return_value=2.0,
    )


def _write_panel(tmp_path: Path, *, summary_episode_count: int = 6) -> tuple[Path, Path]:
    rows = [
        _episode(workload_id="success-0"),
        _offtrack(0),
        _offtrack(1),
        _offtrack(2, role="R2_handling_limit_drift_capable_avoidance"),
        _collision(0),
        _collision(1),
    ]
    episode_path = tmp_path / "episode_rows.csv"
    summary_path = tmp_path / "summary.json"
    write_csv_rows(episode_path, rows)
    write_json(
        summary_path,
        {
            "episode_count": summary_episode_count,
            "global_outcome": {
                "success_count": 1,
                "offtrack_count": 3,
                "collision_count": 2,
                "max_step_noncompletion_count": 0,
            },
        },
    )
    return summary_path, episode_path


def test_failure_slice_diagnosis_reproduces_counts_and_routes(tmp_path: Path) -> None:
    summary_path, episode_path = _write_panel(tmp_path)

    summary = diagnosis.run_failure_slice_diagnosis(
        summary_path=summary_path,
        episode_rows_path=episode_path,
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_failure_slice_diagnosis_pass"
    assert summary["input_episode_count"] == 6
    assert summary["count_matches"] == {
        "episode_count_match": True,
        "success_count_match": True,
        "offtrack_count_match": True,
        "collision_count_match": True,
        "max_step_count_match": True,
    }
    assert summary["global_success_count"] == 1
    assert summary["global_offtrack_count"] == 3
    assert summary["global_collision_count"] == 2
    assert summary["primary_route"] == "offtrack_primary_collision_guardrail_failure_slice_result_audit"
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["winner_selected"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    output = tmp_path / "out"
    assert (output / "slice_by_role_family.csv").exists()
    assert (output / "slice_by_obstacle_longitudinal_timing_bucket.csv").exists()
    assert (output / "slice_by_hidden_dynamics_bucket.csv").exists()
    assert (output / "dominant_slices.csv").exists()
    assert (output / "route_recommendation.csv").exists()
    persisted = read_json(output / "summary.json")
    assert persisted["next_blocker"] == "next"


def test_failure_slice_diagnosis_fails_when_summary_counts_do_not_match(tmp_path: Path) -> None:
    summary_path, episode_path = _write_panel(tmp_path, summary_episode_count=7)

    summary = diagnosis.run_failure_slice_diagnosis(
        summary_path=summary_path,
        episode_rows_path=episode_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_failure_slice_diagnosis_fail"
    assert summary["count_matches"]["episode_count_match"] is False
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
