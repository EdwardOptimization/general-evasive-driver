from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization as runner


def _row(index: int, *, success: bool = False, hard: bool = False, collision: bool = False) -> dict[str, Any]:
    return {
        "workload_id": f"w{index}",
        "profile_name": "p0" if index < 3 else "p1",
        "profile_seed": "p0|0" if index < 3 else "p1|0",
        "pack_id": "pack",
        "role_family": "R0",
        "scenario_family_id": "S0",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early",
        "obstacle_lateral_offset_bucket": "center",
        "sampled_obstacle_label": "label",
        "termination_reason": "off_track" if hard else "",
        "outcome_bucket": "success_obstacle_pass" if success else ("collision_failure" if collision else "off_track_noncollision_noncompletion"),
        "metric_selected_actual_success": success,
        "metric_selected_hard_offtrack_failure": hard,
        "metric_selected_soft_offtrack_violation": False,
        "metric_selected_boundary_tolerated_success": False,
        "metric_selected_max_offtrack_overshoot_m": 0.25 if hard else 0.0,
        "collision": collision,
        "truncated": False,
        "min_clearance_margin": 1.0,
        "steps": 10,
    }


def test_outcome_localization_summarizes_diagnostic_slices(tmp_path: Path) -> None:
    rows = [
        _row(0, hard=True),
        _row(1, hard=True),
        _row(2, collision=True),
        _row(3, success=True),
    ]

    summary = runner.run_outcome_localization(
        episode_rows=rows,
        output_dir=tmp_path / "out",
        target_episode_count=4,
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["episode_count"] == 4
    assert summary["global_localization"]["hard_offtrack_count"] == 2
    assert summary["global_localization"]["collision_count"] == 1
    assert summary["global_localization"]["actual_success_count"] == 1
    assert summary["guardrail_violation_count"] == 0
    assert summary["policy_action_executed"] is False
    assert (tmp_path / "out" / "localization_rows.csv").exists()
    assert (tmp_path / "out" / "decision_rows.csv").exists()


def test_outcome_localization_fails_closed_on_count_gap(tmp_path: Path) -> None:
    summary = runner.run_outcome_localization(
        episode_rows=[_row(0, hard=True)],
        output_dir=tmp_path / "out",
        target_episode_count=2,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert "metric_artifact" in summary["failure_types_observed"]
