from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_bounded_repair_plan_materialization as repair_plan
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _row(
    *,
    axis: str,
    value: str,
    route: str,
    repair: bool,
    collision: bool,
    r4: bool = False,
    diagnostic: bool = False,
) -> dict[str, Any]:
    return {
        "slice_axis": axis,
        "slice_key": axis,
        "slice_value": value,
        "episode_count": 50,
        "success_rate": 0.0,
        "offtrack_rate": 0.8 if repair else 0.1,
        "collision_rate": 0.3 if collision or r4 else 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure" if repair else "collision_dominated_failure",
        "is_high_priority_offtrack": repair,
        "source_route_class": route,
        "consolidated_route": route,
        "actionability_class": "r4_mitigation_semantics" if r4 else "role_semantics",
        "repair_target_admissible": repair,
        "collision_guardrail_required": collision,
        "r4_mitigation_semantics": r4,
        "diagnostic_only": diagnostic,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_source(tmp_path: Path, rows: list[dict[str, Any]], *, result_class: str | None = None) -> Path:
    source = tmp_path / "source"
    summary = {
        "result_class": result_class or "current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass",
        "offtrack_repair_target_row_count": sum(bool(row["repair_target_admissible"]) for row in rows),
        "collision_guardrail_row_count": sum(bool(row["collision_guardrail_required"]) for row in rows),
        "r4_mitigation_semantics_row_count": sum(bool(row["r4_mitigation_semantics"]) for row in rows),
        "diagnostic_guardrail_row_count": sum(bool(row["diagnostic_only"]) for row in rows),
        "ranking_admissible_count": 0,
        "winner_selected_count": 0,
    }
    write_json(source / "summary.json", summary)
    write_csv_rows(source / "consolidated_rows.csv", rows)
    return source


def test_bounded_repair_plan_keeps_guardrails_separate(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(
            axis="sampled_obstacle_label",
            value="drift_required",
            route="offtrack_repair_target_with_collision_guardrail",
            repair=True,
            collision=True,
        ),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="candidate_id", value="candidate_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows)

    summary = repair_plan.run_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows),
    )

    assert summary["result_class"] == repair_plan.RESULT_PASS
    assert summary["repair_plan_row_count"] == len(rows)
    assert summary["offtrack_repair_plan_row_count"] == 2
    assert summary["collision_guardrail_plan_row_count"] == 2
    assert summary["r4_mitigation_plan_row_count"] == 1
    assert summary["diagnostic_axis_repair_plan_count"] == 0
    assert summary["r4_ordinary_repair_plan_count"] == 0
    assert summary["collision_guardrail_as_plain_repair_count"] == 0
    assert summary["repair_execution_allowed_count"] == 0
    assert summary["training_allowed_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["current_sim_verdict_claim_made"] is False

    plan_rows = repair_plan.read_csv_rows(tmp_path / "out" / "repair_plan_rows.csv")
    r4 = next(row for row in plan_rows if row["slice_value"] == "R4_unavoidable_mitigation")
    assert r4["plan_route"] == "r4_mitigation_semantics_guardrail"
    assert "ordinary avoidable" in r4["candidate_levers"]
    diagnostic = next(row for row in plan_rows if row["slice_axis"] == "candidate_id")
    assert diagnostic["plan_route"] == "diagnostic_monitoring_only"
    assert diagnostic["ranking_admissible"] == "False"


def test_bounded_repair_plan_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="candidate_id", value="candidate_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows, result_class="current_sim_dual_axis_effective_candidate_actionable_target_consolidation_fail")

    summary = repair_plan.run_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows),
    )

    assert summary["result_class"] == repair_plan.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_bounded_repair_plan_fails_closed_on_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="candidate_id", value="candidate_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows)

    summary = repair_plan.run_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows) + 1,
    )

    assert summary["result_class"] == repair_plan.RESULT_FAIL
    assert summary["source_consolidated_row_count"] == len(rows)


def test_bounded_repair_plan_summary_is_strict_json(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="candidate_id", value="candidate_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows)

    repair_plan.run_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows),
    )

    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == repair_plan.RESULT_PASS
