from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_actionable_target_consolidation import (
    read_csv_rows,
    run_actionable_target_consolidation,
)


def _slice(
    *,
    slice_axis: str,
    slice_value: str,
    route_class: str,
    offtrack: bool = False,
    collision: bool = False,
    r4: bool = False,
    high: bool = False,
    episode_count: int = 30,
) -> dict[str, object]:
    return {
        "slice_axis": slice_axis,
        "slice_key": slice_axis,
        "slice_value": slice_value,
        "episode_count": episode_count,
        "success_rate": 0.0,
        "offtrack_rate": 0.9 if offtrack else 0.1,
        "collision_rate": 0.2 if collision else 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure" if offtrack else "collision_dominated_failure",
        "is_offtrack_target": offtrack,
        "is_collision_guardrail": collision,
        "is_r4_mitigation_semantics": r4,
        "is_high_priority_offtrack": high,
        "route_class": route_class,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    rows = [
        _slice(
            slice_axis="global",
            slice_value="all",
            route_class="offtrack_target_with_collision_guardrail",
            offtrack=True,
            collision=True,
            episode_count=180,
        ),
        _slice(
            slice_axis="profile_name",
            slice_value="L2_window_50",
            route_class="offtrack_target",
            offtrack=True,
            episode_count=90,
        ),
        _slice(
            slice_axis="role_family",
            slice_value="R0_stable_avoidable",
            route_class="offtrack_target",
            offtrack=True,
            high=True,
        ),
        _slice(
            slice_axis="role_family",
            slice_value="R2_handling_limit_drift_capable_avoidance",
            route_class="offtrack_target_with_collision_guardrail",
            offtrack=True,
            collision=True,
        ),
        _slice(
            slice_axis="obstacle_longitudinal_timing_bucket",
            slice_value="late_close",
            route_class="collision_guardrail",
            collision=True,
        ),
        _slice(
            slice_axis="role_family",
            slice_value="R4_unavoidable_mitigation",
            route_class="r4_mitigation_semantics",
            collision=True,
            r4=True,
        ),
    ]
    summary_path = tmp_path / "summary.json"
    slice_rows_path = tmp_path / "slice_rows.csv"
    write_json(summary_path, {"result_class": "current_sim_dual_axis_measured_outcome_localization_pass"})
    write_csv_rows(slice_rows_path, rows)
    return summary_path, slice_rows_path


def test_actionable_target_consolidation_separates_targets_guardrails_and_r4(tmp_path: Path) -> None:
    summary_path, slice_rows_path = _inputs(tmp_path)

    summary = run_actionable_target_consolidation(
        summary_path=summary_path,
        slice_rows_path=slice_rows_path,
        output_dir=tmp_path / "out",
        target_slice_row_count=6,
        minimum_actionable_episode_count=30,
    )

    assert summary["result_class"] == "current_sim_dual_axis_actionable_target_consolidation_pass"
    assert summary["source_slice_row_count"] == 6
    assert summary["offtrack_repair_target_row_count"] == 2
    assert summary["collision_guardrail_row_count"] == 2
    assert summary["r4_mitigation_semantics_row_count"] == 1
    assert summary["diagnostic_guardrail_row_count"] == 2
    assert summary["diagnostic_axis_repair_target_count"] == 0
    assert summary["r4_ordinary_repair_target_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["training_started"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["finite_window_vs_gru_conclusion_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    consolidated = read_csv_rows(tmp_path / "out" / "consolidated_rows.csv")
    global_row = next(row for row in consolidated if row["slice_axis"] == "global")
    assert global_row["consolidated_route"] == "diagnostic_guardrail"
    assert global_row["repair_target_admissible"] == "False"

    r2_row = next(row for row in consolidated if row["slice_value"].startswith("R2_"))
    assert r2_row["consolidated_route"] == "offtrack_repair_target_with_collision_guardrail"
    assert r2_row["repair_target_admissible"] == "True"
    assert r2_row["collision_guardrail_required"] == "True"

    r4_row = next(row for row in consolidated if row["slice_value"].startswith("R4_"))
    assert r4_row["consolidated_route"] == "r4_mitigation_semantics"
    assert r4_row["repair_target_admissible"] == "False"

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "controller_family_ranking,False" in claim_boundary
    assert "training_repair_success,False" in claim_boundary

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["offtrack_repair_target_rows"].endswith("offtrack_repair_target_rows.csv")


def test_actionable_target_consolidation_fails_closed_on_slice_count_mismatch(tmp_path: Path) -> None:
    summary_path, slice_rows_path = _inputs(tmp_path)

    summary = run_actionable_target_consolidation(
        summary_path=summary_path,
        slice_rows_path=slice_rows_path,
        output_dir=tmp_path / "out",
        target_slice_row_count=7,
    )

    assert summary["result_class"] == "current_sim_dual_axis_actionable_target_consolidation_incomplete_or_fail"
    assert summary["source_slice_row_count"] == 6
    assert summary["target_slice_row_count"] == 7
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
