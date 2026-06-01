from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_profile_history_failure_diagnosis as diagnosis
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    task_family: str,
    profile_name: str,
    history_representation: str,
    outcome_bucket: str,
    time_to_offtrack: float | str = "",
) -> dict[str, object]:
    return {
        "task_family": task_family,
        "source_family_template": "template",
        "capability_pair": "capability",
        "profile_name": profile_name,
        "history_representation": history_representation,
        "outcome_bucket": outcome_bucket,
        "success": outcome_bucket == "success_obstacle_pass",
        "collision": outcome_bucket == "collision_failure",
        "termination_reason": "off_track" if outcome_bucket == "off_track_noncollision_noncompletion" else "",
        "return": 1.0 if outcome_bucket == "success_obstacle_pass" else -1.0,
        "action_rate_mean": 0.2,
        "min_clearance_margin": 0.1,
        "max_off_track_overshoot": 0.5,
        "off_track_severity_proxy": 0.4,
        "time_to_first_off_track_s": time_to_offtrack,
        "impact_speed_proxy": 0.0,
        "impact_severity_proxy": 0.0,
        "high_sideslip_fraction": 0.0,
        "max_abs_beta": 0.1,
        "max_abs_yaw_rate": 0.2,
        "drift_used": False,
        "recovery_success": False,
    }


def _candidate() -> dict[str, object]:
    return {
        "candidate_id": "scene_candidate_000",
        "group_key": "task_family",
        "group_value": "task_family=T1",
        "diagnostic_label": "multi_profile_diagnostic_support",
    }


def test_profile_history_failure_diagnosis_confirms_l3_zero_success(tmp_path: Path) -> None:
    episode_rows = tmp_path / "episode_rows.csv"
    diagnostic_summary = tmp_path / "diagnostic_summary.json"
    scene_candidate_summary = tmp_path / "scene_candidate_summary.csv"
    rows = []
    for _ in range(8):
        rows.append(
            _episode(
                task_family="T1",
                profile_name="L2_window_25",
                history_representation="explicit_finite_window",
                outcome_bucket="success_obstacle_pass",
            )
        )
    for _ in range(8):
        rows.append(
            _episode(
                task_family="T1",
                profile_name="L3_online_gru",
                history_representation="online_recurrent_hidden",
                outcome_bucket="off_track_noncollision_noncompletion",
                time_to_offtrack=1.0,
            )
        )
    for _ in range(8):
        rows.append(
            _episode(
                task_family="T1",
                profile_name="L3_reset_control",
                history_representation="online_recurrent_hidden",
                outcome_bucket="off_track_noncollision_noncompletion",
                time_to_offtrack=1.0,
            )
        )
    write_csv_rows(episode_rows, rows)
    write_csv_rows(scene_candidate_summary, [_candidate()])
    write_json(diagnostic_summary, {"result_class": "current_sim_bounded_diagnostic_comparison_pass"})

    result = diagnosis.run_profile_history_failure_diagnosis(
        episode_rows=episode_rows,
        diagnostic_summary=diagnostic_summary,
        scene_candidate_summary=scene_candidate_summary,
        output_dir=tmp_path / "out",
    )

    assert result["result_class"] == "current_sim_profile_history_failure_diagnosis_pass"
    assert result["l3_online_success_count"] == 0
    assert result["l3_reset_success_count"] == 0
    assert result["l2_window_25_success_count"] == 8
    assert result["l3_zero_success_confirmed"] is True
    assert result["l3_reset_equivalent_to_online"] is True
    assert result["finite_window_support_visible"] is True
    assert result["ranking_admissible_count"] == 0
    assert (tmp_path / "out" / "profile_pair_delta_metrics.csv").exists()
    profile_rows = diagnosis.read_csv_rows(tmp_path / "out" / "profile_failure_metric_summary.csv")
    assert all(row["mean_action_rate"] == "0.2" for row in profile_rows)
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["finite_window_vs_gru_conclusion_made"] is False


def test_failure_mode_label_prioritizes_supported_success() -> None:
    metrics = {
        "success_count": 8,
        "collision_count": 0,
        "offtrack_count": 10,
        "mean_time_to_first_off_track_s": 1.0,
        "mean_max_abs_beta": 0.0,
        "mean_high_sideslip_fraction": 0.0,
    }

    assert diagnosis.failure_mode_label(metrics) == "supported_success"
