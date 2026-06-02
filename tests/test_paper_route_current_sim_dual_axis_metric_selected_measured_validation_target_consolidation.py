from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation import (
    RESULT_FAIL,
    RESULT_PASS,
    read_csv_rows,
    run_target_consolidation,
)


def _loc(
    *,
    axis: str,
    value: str,
    episodes: int,
    hard_count: int,
    collision_count: int,
    soft_count: int = 0,
    pattern: str = "hard_offtrack_dominated",
) -> dict[str, Any]:
    success_count = max(0, episodes - hard_count - collision_count - soft_count)
    return {
        "axis": axis,
        "value": value,
        "episode_count": episodes,
        "actual_success_count": success_count,
        "actual_success_rate": success_count / episodes if episodes else 0.0,
        "hard_offtrack_count": hard_count,
        "hard_offtrack_rate": hard_count / episodes if episodes else 0.0,
        "soft_offtrack_violation_count": soft_count,
        "soft_offtrack_violation_rate": soft_count / episodes if episodes else 0.0,
        "boundary_tolerated_success_count": 0,
        "boundary_tolerated_success_rate": 0.0,
        "collision_count": collision_count,
        "collision_rate": collision_count / episodes if episodes else 0.0,
        "max_step_noncompletion_count": 0,
        "max_step_noncompletion_rate": 0.0,
        "other_count": 0,
        "other_rate": 0.0,
        "mean_min_clearance_margin": 1.0,
        "min_min_clearance_margin": -0.1,
        "mean_overshoot_m": 0.05,
        "max_overshoot_m": 0.1,
        "mean_steps": 80.0,
        "diagnostic_pattern": pattern,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _write_inputs(tmp_path: Path, rows: list[dict[str, Any]], *, result_class: str = "source_pass") -> tuple[Path, Path]:
    summary_path = tmp_path / "summary.json"
    rows_path = tmp_path / "localization_rows.csv"
    write_json(summary_path, {"result_class": result_class})
    write_csv_rows(rows_path, rows)
    return summary_path, rows_path


def test_target_consolidation_separates_targets_guardrails_and_diagnostics(tmp_path: Path) -> None:
    rows = [
        _loc(axis="global", value="all", episodes=1000, hard_count=700, collision_count=200),
        _loc(axis="role_family", value="R2_handling_limit_drift_capable_avoidance", episodes=100, hard_count=80, collision_count=15),
        _loc(axis="hidden_dynamics_bucket", value="low_mu", episodes=100, hard_count=75, collision_count=20, soft_count=2),
        _loc(axis="sampled_obstacle_label", value="unavoidable", episodes=100, hard_count=20, collision_count=70, pattern="collision_dominated"),
        _loc(axis="profile_name", value="L3_online_gru", episodes=100, hard_count=80, collision_count=15),
        _loc(axis="outcome_bucket", value="off_track_noncollision_noncompletion", episodes=100, hard_count=100, collision_count=0),
    ]
    summary_path, rows_path = _write_inputs(tmp_path, rows)

    summary = run_target_consolidation(
        source_summary_path=summary_path,
        localization_rows_path=rows_path,
        output_dir=tmp_path / "out",
        target_localization_row_count=len(rows),
        minimum_target_episode_count=90,
        minimum_hard_offtrack_rate=0.5,
        minimum_collision_guardrail_rate=0.1,
    )

    assert summary["result_class"] == RESULT_PASS
    assert summary["hard_offtrack_target_row_count"] == 2
    assert summary["guardrail_row_count"] >= 4
    assert summary["diagnostic_row_count"] == 4
    assert summary["diagnostic_axis_repair_target_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["training_started"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    target_rows = read_csv_rows(tmp_path / "out" / "target_rows.csv")
    assert {row["axis"] for row in target_rows} == {"hidden_dynamics_bucket", "role_family"}
    assert {row["repair_target_admissible"] for row in target_rows} == {"True"}

    diagnostic_rows = read_csv_rows(tmp_path / "out" / "diagnostic_rows.csv")
    profile_row = next(row for row in diagnostic_rows if row["axis"] == "profile_name")
    assert profile_row["repair_target_admissible"] == "False"
    outcome_row = next(row for row in diagnostic_rows if row["axis"] == "outcome_bucket")
    assert outcome_row["repair_target_admissible"] == "False"

    decision_text = (tmp_path / "out" / "decision_rows.csv").read_text(encoding="utf-8")
    assert "diagnostic_axes_used_for_ranking,false,True" in decision_text
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["target_rows"].endswith("target_rows.csv")


def test_target_consolidation_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = [
        _loc(axis="global", value="all", episodes=100, hard_count=80, collision_count=10),
        _loc(axis="role_family", value="R2", episodes=100, hard_count=80, collision_count=10),
    ]
    summary_path, rows_path = _write_inputs(tmp_path, rows, result_class="source_fail")

    summary = run_target_consolidation(
        source_summary_path=summary_path,
        localization_rows_path=rows_path,
        output_dir=tmp_path / "out",
        target_localization_row_count=len(rows),
    )

    assert summary["result_class"] == RESULT_FAIL
    assert summary["source_result_class"] == "source_fail"
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False


def test_target_consolidation_fails_closed_on_row_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _loc(axis="global", value="all", episodes=100, hard_count=80, collision_count=10),
        _loc(axis="role_family", value="R2", episodes=100, hard_count=80, collision_count=10),
    ]
    summary_path, rows_path = _write_inputs(tmp_path, rows)

    summary = run_target_consolidation(
        source_summary_path=summary_path,
        localization_rows_path=rows_path,
        output_dir=tmp_path / "out",
        target_localization_row_count=3,
    )

    assert summary["result_class"] == RESULT_FAIL
    assert summary["source_localization_row_count"] == 2
