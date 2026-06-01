from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis as diagnosis
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
    selected_floor: bool = False,
    obstacle_label: str = "drift_required",
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
        "high_sideslip_fraction": 0.0,
        "truncated": False,
        "recovery_success": False,
        "drift_used": False,
        "selected_readiness_floor_pass": selected_floor,
        "obstacle_label": obstacle_label,
    }


def _offtrack_episode(index: int) -> dict[str, object]:
    return _episode(
        seed_id=222600 + index,
        outcome_bucket="off_track_noncollision_noncompletion",
        termination_reason="off_track",
        obstacle_completed=False,
        return_value=42.0,
        overshoot=0.03,
        offtrack_time=1.4,
        margin=0.7,
    )


def _collision_episode(index: int) -> dict[str, object]:
    return _episode(
        seed_id=333600 + index,
        outcome_bucket="collision_failure",
        termination_reason="collision",
        collision=True,
        obstacle_completed=False,
        return_value=10.0,
        margin=-0.4,
    )


def _panel(success_count: int, offtrack_count: int, collision_count: int) -> list[dict[str, object]]:
    rows = [_episode(seed_id=111000 + index) for index in range(success_count)]
    rows.extend(_offtrack_episode(index) for index in range(offtrack_count))
    rows.extend(_collision_episode(index) for index in range(collision_count))
    return rows


def test_midcourse_containment_slice_diagnosis_uses_three_accurate_panels(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(diagnosis, "EXPECTED_PANEL_ROWS", 8)
    baseline = _panel(success_count=3, offtrack_count=4, collision_count=1)
    targeted = _panel(success_count=5, offtrack_count=2, collision_count=1)
    generic = _panel(success_count=2, offtrack_count=5, collision_count=1)
    baseline_path = tmp_path / "baseline.csv"
    targeted_path = tmp_path / "targeted.csv"
    generic_path = tmp_path / "generic.csv"
    write_csv_rows(baseline_path, baseline)
    write_csv_rows(targeted_path, targeted)
    write_csv_rows(generic_path, generic)

    summary = diagnosis.run_midcourse_corridor_containment_failure_slice_diagnosis(
        baseline_episodes=baseline_path,
        targeted_episodes=targeted_path,
        reference_episodes=generic_path,
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_midcourse_corridor_containment_failure_slice_diagnosis_pass"
    assert summary["panel_labels"] == ["baseline_m2244", "targeted_m2265", "generic_m2253"]
    assert summary["baseline_episode_count"] == 8
    assert summary["targeted_episode_count"] == 8
    assert summary["reference_episode_count"] == 8
    assert summary["global_delta_vs_base"]["offtrack_delta"] == -2
    assert summary["targeted_vs_generic_delta"]["offtrack_delta"] == -3
    assert summary["mid_offtrack_delta_vs_base"] == -2
    assert summary["mild_overshoot_delta_vs_base"] == -2
    assert summary["primary_route"] == "targeted_containment_repair_supported_result_audit"
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected"] is False

    output = tmp_path / "out"
    assert (output / "reference_comparison_delta.csv").exists()
    assert (output / "failure_slice_routes.csv").exists()
    saved = read_json(output / "summary.json")
    assert saved["next_blocker"] == "next"
    assert saved["paper_level_claim_made"] is False


def test_midcourse_containment_slice_diagnosis_fails_incomplete_support(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(diagnosis, "EXPECTED_PANEL_ROWS", 8)
    baseline_path = tmp_path / "baseline.csv"
    targeted_path = tmp_path / "targeted.csv"
    generic_path = tmp_path / "generic.csv"
    write_csv_rows(baseline_path, _panel(success_count=3, offtrack_count=4, collision_count=1))
    write_csv_rows(targeted_path, _panel(success_count=5, offtrack_count=2, collision_count=1))
    write_csv_rows(generic_path, _panel(success_count=2, offtrack_count=4, collision_count=1))

    summary = diagnosis.run_midcourse_corridor_containment_failure_slice_diagnosis(
        baseline_episodes=baseline_path,
        targeted_episodes=targeted_path,
        reference_episodes=generic_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_midcourse_corridor_containment_failure_slice_diagnosis_fail"
    assert summary["support_complete"] is False
    assert summary["primary_route"] == "artifact_repair_before_interpretation"
