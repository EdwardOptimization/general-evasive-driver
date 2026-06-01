from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_offtrack_failure_slice_diagnosis as diagnosis
from autodrift.artifacts import read_json, write_csv_rows


def _episode(
    *,
    profile: str = "L0_current_masked",
    seed_id: int = 222601,
    outcome_bucket: str = "success_obstacle_pass",
    termination_reason: str = "obstacle_completed",
    collision: bool = False,
    obstacle_completed: bool = True,
    return_value: float = 80.0,
    overshoot: float = 0.0,
    offtrack_time: float | str = "",
    margin: float = 1.2,
    sideslip: float = 0.0,
) -> dict[str, object]:
    return {
        "profile_name": profile,
        "seed_id": seed_id,
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "collision": collision,
        "obstacle_completed": obstacle_completed,
        "return": return_value,
        "max_off_track_overshoot": overshoot,
        "time_to_first_off_track_s": offtrack_time,
        "min_clearance_margin": margin,
        "high_sideslip_fraction": sideslip,
        "truncated": False,
        "recovery_success": False,
        "drift_used": False,
    }


def test_offtrack_failure_slice_diagnosis_routes_offtrack_regression(tmp_path: Path) -> None:
    baseline = [_episode() for _ in range(8)]
    repaired = [_episode() for _ in range(3)] + [
        _episode(
            outcome_bucket="off_track_noncollision_noncompletion",
            termination_reason="off_track",
            obstacle_completed=False,
            return_value=45.0,
            overshoot=0.08,
            offtrack_time=1.0,
            margin=0.4,
            sideslip=0.08,
        )
        for _ in range(5)
    ]
    baseline_path = tmp_path / "baseline.csv"
    repaired_path = tmp_path / "repaired.csv"
    write_csv_rows(baseline_path, baseline)
    write_csv_rows(repaired_path, repaired)

    summary = diagnosis.run_offtrack_failure_slice_diagnosis(
        baseline_episodes=baseline_path,
        repaired_episodes=repaired_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_offtrack_failure_slice_diagnosis_fail"
    assert summary["support_complete"] is False
    assert summary["global_delta"]["offtrack_delta"] == 5
    assert summary["primary_route"] == "recovery_corridor_curriculum_redesign"
    assert (tmp_path / "out" / "offtrack_timing_delta.csv").exists()


def test_offtrack_failure_slice_diagnosis_passes_complete_support(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(diagnosis, "EXPECTED_PANEL_ROWS", 8)
    baseline = [_episode() for _ in range(8)]
    repaired = [_episode() for _ in range(7)] + [
        _episode(
            outcome_bucket="off_track_noncollision_noncompletion",
            termination_reason="off_track",
            obstacle_completed=False,
            overshoot=0.03,
            offtrack_time=1.4,
            margin=0.6,
        )
    ]
    baseline_path = tmp_path / "baseline.csv"
    repaired_path = tmp_path / "repaired.csv"
    write_csv_rows(baseline_path, baseline)
    write_csv_rows(repaired_path, repaired)

    summary = diagnosis.run_offtrack_failure_slice_diagnosis(
        baseline_episodes=baseline_path,
        repaired_episodes=repaired_path,
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_offtrack_failure_slice_diagnosis_pass"
    assert summary["baseline_episode_count"] == 8
    assert summary["repaired_episode_count"] == 8
    assert summary["next_blocker"] == "next"
    assert read_json(tmp_path / "out" / "summary.json")["support_complete"] is True
