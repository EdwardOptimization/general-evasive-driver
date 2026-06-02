from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization as repair_plan
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _row(
    *,
    axis: str,
    value: str,
    route: str,
    repair: bool,
    collision: bool,
    source_table: str = "episode_rows",
    r4: bool = False,
    max_step: bool = False,
    speed_too_low: bool = False,
    diagnostic: bool = False,
) -> dict[str, Any]:
    return {
        "slice_axis": axis,
        "slice_key": axis,
        "slice_value": value,
        "source_table": source_table,
        "episode_count": 50,
        "success_rate": 0.0,
        "offtrack_rate": 0.8 if repair else 0.1,
        "collision_rate": 0.3 if collision or r4 else 0.0,
        "max_step_noncompletion_rate": 0.7 if max_step else 0.0,
        "speed_too_low_rate": 0.6 if speed_too_low else 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure" if repair else "diagnostic_failure",
        "is_high_priority_offtrack": repair,
        "source_route_class": route,
        "consolidated_route": route,
        "actionability_class": "r4_mitigation_semantics" if r4 else "role_semantics",
        "repair_target_admissible": repair,
        "collision_guardrail_required": collision,
        "r4_mitigation_semantics": r4,
        "diagnostic_only": diagnostic,
        "source_priority_score": 1.0,
        "max_step_guardrail_required": max_step,
        "speed_too_low_guardrail_required": speed_too_low,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_source(tmp_path: Path, rows: list[dict[str, Any]], *, result_class: str | None = None) -> Path:
    source = tmp_path / "source"
    summary = {
        "result_class": result_class
        or "current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_pass",
        "offtrack_repair_target_row_count": sum(bool(row["repair_target_admissible"]) for row in rows),
        "collision_guardrail_row_count": sum(bool(row["collision_guardrail_required"]) for row in rows),
        "r4_mitigation_semantics_row_count": sum(bool(row["r4_mitigation_semantics"]) for row in rows),
        "max_step_noncompletion_row_count": sum(bool(row["max_step_guardrail_required"]) for row in rows),
        "speed_too_low_row_count": sum(bool(row["speed_too_low_guardrail_required"]) for row in rows),
        "diagnostic_guardrail_row_count": sum(
            bool(row["diagnostic_only"]) or row["source_table"] == "episode_family_membership_rows" for row in rows
        ),
        "family_membership_diagnostic_row_count": sum(row["source_table"] == "episode_family_membership_rows" for row in rows),
        "ranking_admissible_count": 0,
        "winner_selected_count": 0,
    }
    write_json(source / "summary.json", summary)
    write_csv_rows(source / "consolidated_rows.csv", rows)
    return source


def test_source_linked_repair_plan_keeps_all_guardrails_separate(tmp_path: Path) -> None:
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
        _row(axis="hidden_dynamics_bucket", value="max_step_high", route="max_step_noncompletion_target", repair=False, collision=False, max_step=True),
        _row(
            axis="obstacle_longitudinal_timing_bucket",
            value="speed_too_low_high",
            route="speed_too_low_target",
            repair=False,
            collision=False,
            speed_too_low=True,
        ),
        _row(
            axis="hidden_dynamics_bucket",
            value="family_membership_diagnostic",
            route="source_linked_family_diagnostic_guardrail",
            repair=False,
            collision=False,
            source_table="episode_family_membership_rows",
        ),
        _row(axis="profile_name", value="support_profile_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows)

    summary = repair_plan.run_source_linked_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows),
    )

    assert summary["result_class"] == repair_plan.RESULT_PASS
    assert summary["repair_plan_row_count"] == len(rows)
    assert summary["offtrack_repair_plan_row_count"] == 2
    assert summary["collision_guardrail_plan_row_count"] == 2
    assert summary["r4_mitigation_plan_row_count"] == 1
    assert summary["max_step_noncompletion_plan_row_count"] == 1
    assert summary["speed_too_low_plan_row_count"] == 1
    assert summary["diagnostic_monitoring_row_count"] == 2
    assert summary["family_membership_diagnostic_row_count"] == 1
    assert summary["diagnostic_axis_repair_plan_count"] == 0
    assert summary["family_axis_repair_plan_count"] == 0
    assert summary["profile_axis_repair_plan_count"] == 0
    assert summary["r4_ordinary_repair_plan_count"] == 0
    assert summary["collision_guardrail_as_plain_repair_count"] == 0
    assert summary["max_step_as_plain_repair_count"] == 0
    assert summary["speed_too_low_as_plain_repair_count"] == 0
    assert summary["repair_execution_allowed_count"] == 0
    assert summary["training_allowed_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["current_sim_verdict_claim_made"] is False

    plan_rows = repair_plan.read_csv_rows(tmp_path / "out" / "repair_plan_rows.csv")
    family = next(row for row in plan_rows if row["source_table"] == "episode_family_membership_rows")
    assert family["plan_route"] == "family_membership_diagnostic_monitoring"
    assert family["ranking_admissible"] == "False"
    max_row = next(row for row in plan_rows if row["slice_value"] == "max_step_high")
    assert max_row["plan_route"] == "max_step_noncompletion_guardrail"
    assert "timeout" in max_row["stop_rules"]
    speed_row = next(row for row in plan_rows if row["slice_value"] == "speed_too_low_high")
    assert speed_row["plan_route"] == "speed_too_low_guardrail"
    assert "low-speed" in speed_row["candidate_levers"]


def test_source_linked_repair_plan_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="profile_name", value="support_profile_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(
        tmp_path,
        rows,
        result_class="current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_fail",
    )

    summary = repair_plan.run_source_linked_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows),
    )

    assert summary["result_class"] == repair_plan.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_source_linked_repair_plan_fails_closed_on_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="profile_name", value="support_profile_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows)

    summary = repair_plan.run_source_linked_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows) + 1,
    )

    assert summary["result_class"] == repair_plan.RESULT_FAIL
    assert summary["source_consolidated_row_count"] == len(rows)


def test_source_linked_repair_plan_summary_is_strict_json(tmp_path: Path) -> None:
    rows = [
        _row(axis="obstacle_lateral_offset_bucket", value="centerline", route="offtrack_repair_target", repair=True, collision=False),
        _row(axis="role_family", value="R5_hidden_dynamics_robustness", route="collision_guardrail", repair=False, collision=True),
        _row(axis="role_family", value="R4_unavoidable_mitigation", route="r4_mitigation_semantics", repair=False, collision=False, r4=True),
        _row(axis="profile_name", value="support_profile_a", route="diagnostic_guardrail", repair=False, collision=False, diagnostic=True),
    ]
    source = _write_source(tmp_path, rows)

    repair_plan.run_source_linked_bounded_repair_plan_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_consolidated_row_count=len(rows),
    )

    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == repair_plan.RESULT_PASS
