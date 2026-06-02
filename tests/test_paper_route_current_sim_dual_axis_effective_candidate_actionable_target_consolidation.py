from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation as consolidation
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _slice(
    *,
    axis: str,
    value: str,
    route_class: str,
    offtrack: bool,
    collision: bool,
    r4: bool = False,
    episodes: int = 50,
) -> dict[str, Any]:
    return {
        "slice_axis": axis,
        "slice_key": axis.replace("+", "+"),
        "slice_value": value,
        "episode_count": episodes,
        "success_rate": 0.0,
        "offtrack_rate": 0.8 if offtrack else 0.1,
        "collision_rate": 0.2 if collision else 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure" if offtrack else "collision_dominated_failure",
        "is_high_priority_offtrack": offtrack,
        "route_class": route_class,
        "is_offtrack_target": offtrack,
        "is_collision_guardrail": collision,
        "is_r4_mitigation_semantics": r4,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _write_source(tmp_path: Path, rows: list[dict[str, Any]]) -> Path:
    source = tmp_path / "source"
    write_json(source / "summary.json", {"result_class": "current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass"})
    write_csv_rows(source / "slice_rows.csv", rows)
    return source


def test_effective_candidate_target_consolidation_keeps_candidate_axes_diagnostic(tmp_path: Path) -> None:
    rows = [
        _slice(axis="candidate_id", value="candidate_a", route_class="offtrack_target", offtrack=True, collision=False),
        _slice(axis="role_family", value="R2_handling_limit_drift_capable_avoidance", route_class="offtrack_target", offtrack=True, collision=False),
        _slice(
            axis="sampled_obstacle_label",
            value="drift_required",
            route_class="offtrack_target_with_collision_guardrail",
            offtrack=True,
            collision=True,
        ),
        _slice(axis="role_family", value="R4_unavoidable_mitigation", route_class="r4_mitigation_semantics", offtrack=False, collision=True, r4=True),
    ]
    source = _write_source(tmp_path, rows)

    summary = consolidation.run_effective_candidate_actionable_target_consolidation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_slice_row_count=len(rows),
        minimum_actionable_episode_count=1,
    )

    assert summary["result_class"] == consolidation.RESULT_PASS
    assert summary["source_slice_row_count"] == len(rows)
    assert summary["offtrack_repair_target_row_count"] > 0
    assert summary["collision_guardrail_row_count"] > 0
    assert summary["r4_mitigation_semantics_row_count"] > 0
    assert summary["diagnostic_axis_repair_target_count"] == 0
    assert summary["r4_ordinary_repair_target_count"] == 0
    assert summary["effective_candidate_ranking_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    consolidated_rows = consolidation.read_csv_rows(tmp_path / "out" / "consolidated_rows.csv")
    candidate_row = next(row for row in consolidated_rows if row["slice_axis"] == "candidate_id")
    assert candidate_row["consolidated_route"] == "diagnostic_guardrail"
    assert candidate_row["repair_target_admissible"] == "False"
    role_row = next(row for row in consolidated_rows if row["slice_value"] == "R2_handling_limit_drift_capable_avoidance")
    assert role_row["repair_target_admissible"] == "True"


def test_effective_candidate_target_consolidation_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = [
        _slice(axis="role_family", value="R2_handling_limit_drift_capable_avoidance", route_class="offtrack_target", offtrack=True, collision=False)
    ]
    source = _write_source(tmp_path, rows)
    payload = read_json(source / "summary.json")
    payload["result_class"] = "current_sim_dual_axis_effective_candidate_measured_outcome_localization_incomplete_or_fail"
    write_json(source / "summary.json", payload)

    summary = consolidation.run_effective_candidate_actionable_target_consolidation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_slice_row_count=len(rows),
        minimum_actionable_episode_count=1,
    )

    assert summary["result_class"] == consolidation.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_effective_candidate_target_consolidation_fails_closed_on_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _slice(axis="role_family", value="R2_handling_limit_drift_capable_avoidance", route_class="offtrack_target", offtrack=True, collision=False)
    ]
    source = _write_source(tmp_path, rows)

    summary = consolidation.run_effective_candidate_actionable_target_consolidation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_slice_row_count=2,
        minimum_actionable_episode_count=1,
    )

    assert summary["result_class"] == consolidation.RESULT_FAIL
    assert summary["source_slice_row_count"] == 1
