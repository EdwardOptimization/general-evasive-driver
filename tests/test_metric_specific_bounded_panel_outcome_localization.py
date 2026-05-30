from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.metric_specific_bounded_panel_outcome_localization import (
    localize_metric_specific_bounded_panel_outcomes,
)


def _episode_row(
    *,
    idx: int,
    role_panel_id: str,
    profile_name: str,
    outcome_bucket: str,
    collision: bool,
    success: bool = False,
) -> dict[str, object]:
    return {
        "workload_id": f"w{idx}",
        "bounded_panel_workload_id": f"bp{idx}",
        "bounded_panel_spec_id": f"spec_{idx // 2}",
        "role_panel_id": role_panel_id,
        "scenario_family": "family",
        "sampled_obstacle_label": "drift_required",
        "profile_name": profile_name,
        "evaluation_role": "benchmark",
        "primary_metric_family": "avoidance_success",
        "road_boundary_bucket": "narrow",
        "hidden_dynamics_bucket": "low_mu",
        "obstacle_timing_bucket": "close",
        "obstacle_lateral_bucket": "center",
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


def test_metric_specific_bounded_panel_outcome_localization_smoke(tmp_path: Path) -> None:
    episode_rows = [
        _episode_row(
            idx=idx,
            role_panel_id="hidden_dynamics_robustness",
            profile_name="L3_online_gru" if idx % 2 else "L3_reset_control_corrected",
            outcome_bucket="collision_failure",
            collision=True,
        )
        for idx in range(12)
    ]
    episode_rows.extend(
        _episode_row(
            idx=idx,
            role_panel_id="stable_avoidance_aes",
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
    write_json(summary_path, {"result_class": "metric_specific_bounded_panel_measured_execution_pass"})

    summary = localize_metric_specific_bounded_panel_outcomes(
        episode_rows_path=rows_path,
        summary_path=summary_path,
        output_dir=tmp_path / "out",
        target_episode_count=16,
    )

    assert summary["result_class"] == "metric_specific_bounded_panel_outcome_localization_pass"
    assert summary["episode_count"] == 16
    assert summary["dominant_slice_count"] > 0
    assert summary["target_dominant_slice_count"] > 0
    assert "role_panel" in summary["target_slice_types_present"]
    assert summary["ranking_blocked"] is True
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "dominant_slices.csv").exists()
    assert (tmp_path / "out" / "target_dominant_slices.csv").exists()
    assert (tmp_path / "out" / "role_panel_profile_aggregate.csv").exists()
