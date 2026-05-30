from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.task_quality_outcome_dominance_localization import (
    dominant_slices_from_aggregates,
    localize_task_quality_outcome_dominance,
)


def _episode_row(
    *,
    idx: int,
    scenario_family: str,
    profile_name: str,
    outcome_bucket: str,
    collision: bool,
    success: bool = False,
) -> dict[str, object]:
    return {
        "workload_id": f"w{idx}",
        "scenario_family": scenario_family,
        "sampled_obstacle_label": "drift_required",
        "profile_name": profile_name,
        "road_boundary_bucket": "narrow",
        "hidden_dynamics_bucket": "low_mu",
        "obstacle_timing_bucket": "close",
        "sampling_repair_variant_id": "repair_v1",
        "outcome_bucket": outcome_bucket,
        "success": success,
        "collision": collision,
        "obstacle_completed": success,
        "min_clearance_margin": -0.1 if collision else 1.0,
        "return": 1.0,
        "steps": 32,
        "action_rate_mean": 0.2,
        "high_sideslip_fraction": 0.0,
    }


def test_dominant_slices_capture_non_success_without_ranking_claim() -> None:
    rows = [
        {
            "scenario_family": "hidden_dynamics_stress",
            "episode_count": 16,
            "success_obstacle_pass_rate": 0.10,
            "collision_failure_rate": 0.70,
            "off_track_noncollision_noncompletion_rate": 0.20,
            "max_steps_noncompletion_rate": 0.0,
            "safe_noncollision_noncompletion_rate": 0.0,
            "clearance_margin_mean": -0.1,
            "clearance_margin_p10": -0.2,
        },
        {
            "scenario_family": "ordinary_stable_avoidance",
            "episode_count": 16,
            "success_obstacle_pass_rate": 0.80,
            "collision_failure_rate": 0.10,
            "off_track_noncollision_noncompletion_rate": 0.10,
            "max_steps_noncompletion_rate": 0.0,
            "safe_noncollision_noncompletion_rate": 0.0,
            "clearance_margin_mean": 1.0,
            "clearance_margin_p10": 0.5,
        },
    ]

    [dominant] = dominant_slices_from_aggregates(
        rows,
        slice_type="scenario_family",
        slice_keys=("scenario_family",),
    )

    assert dominant["scenario_family"] == "hidden_dynamics_stress"
    assert dominant["dominant_outcome"] == "collision_failure"
    assert dominant["diagnostic_only_no_ranking_claim"] is True


def test_task_quality_outcome_dominance_localization_smoke(tmp_path: Path) -> None:
    episode_rows = [
        _episode_row(
            idx=idx,
            scenario_family="hidden_dynamics_stress",
            profile_name="L3_online_gru" if idx % 2 else "L3_reset_control_corrected",
            outcome_bucket="collision_failure",
            collision=True,
        )
        for idx in range(12)
    ]
    episode_rows.extend(
        _episode_row(
            idx=idx,
            scenario_family="ordinary_stable_avoidance",
            profile_name="L3_online_gru",
            outcome_bucket="success_obstacle_pass",
            collision=False,
            success=True,
        )
        for idx in range(12, 16)
    )
    rows_path = tmp_path / "episode_rows.csv"
    summary_path = tmp_path / "source_summary.json"
    write_csv_rows(rows_path, episode_rows)
    write_json(summary_path, {"result_class": "task_quality_scenario_taxonomy_execution_pass"})

    summary = localize_task_quality_outcome_dominance(
        episode_rows_path=rows_path,
        summary_path=summary_path,
        output_dir=tmp_path / "out",
        target_episode_count=16,
    )

    assert summary["result_class"] == "task_quality_outcome_dominance_localization_pass"
    assert summary["episode_count"] == 16
    assert summary["dominant_slice_count"] > 0
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "dominant_slices.csv").exists()
    assert (tmp_path / "out" / "scenario_family_label_aggregate.csv").exists()
