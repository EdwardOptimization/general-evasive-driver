from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import (
    paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation as consolidation,
)
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _slice(
    *,
    axis: str,
    value: str,
    route_class: str,
    offtrack: bool,
    collision: bool,
    source_table: str = "episode_rows",
    r4: bool = False,
    max_step: bool = False,
    speed_too_low: bool = False,
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
        "max_step_noncompletion_rate": 0.7 if max_step else 0.0,
        "speed_too_low_rate": 0.6 if speed_too_low else 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure" if offtrack else "diagnostic_failure",
        "is_high_priority_offtrack": offtrack,
        "route_class": route_class,
        "is_offtrack_target": offtrack,
        "is_collision_guardrail": collision,
        "is_r4_mitigation_semantics": r4,
        "is_max_step_target": max_step,
        "is_speed_too_low_target": speed_too_low,
        "priority_score": 1.0,
        "ranking_admissible": False,
        "winner_selected": False,
        "source_table": source_table,
    }


def _write_source(tmp_path: Path, rows: list[dict[str, Any]]) -> Path:
    source = tmp_path / "source"
    write_json(
        source / "summary.json",
        {"result_class": "current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_pass"},
    )
    write_csv_rows(source / "slice_rows.csv", rows)
    return source


def test_source_linked_consolidation_preserves_source_linkage_and_claim_boundaries(tmp_path: Path) -> None:
    rows = [
        _slice(
            axis="family_id",
            value="family_a",
            route_class="offtrack_target_with_collision_guardrail",
            offtrack=True,
            collision=True,
            source_table="episode_family_membership_rows",
        ),
        _slice(
            axis="hidden_dynamics_bucket",
            value="membership_nonfamily_axis",
            route_class="offtrack_target",
            offtrack=True,
            collision=False,
            source_table="episode_family_membership_rows",
        ),
        _slice(
            axis="profile_name",
            value="support_profile_a",
            route_class="offtrack_target",
            offtrack=True,
            collision=False,
        ),
        _slice(
            axis="role_family",
            value="R2_handling_limit_drift_capable_avoidance",
            route_class="offtrack_target",
            offtrack=True,
            collision=False,
        ),
        _slice(
            axis="sampled_obstacle_label",
            value="drift_required",
            route_class="offtrack_target_with_collision_guardrail",
            offtrack=True,
            collision=True,
        ),
        _slice(
            axis="role_family",
            value="R4_unavoidable_mitigation",
            route_class="r4_mitigation_semantics",
            offtrack=False,
            collision=True,
            r4=True,
        ),
        _slice(
            axis="hidden_dynamics_bucket",
            value="max_step_high",
            route_class="diagnostic_only",
            offtrack=False,
            collision=False,
            max_step=True,
        ),
        _slice(
            axis="obstacle_longitudinal_timing_bucket",
            value="speed_too_low_high",
            route_class="diagnostic_only",
            offtrack=False,
            collision=False,
            speed_too_low=True,
        ),
    ]
    source = _write_source(tmp_path, rows)

    summary = consolidation.run_source_linked_actionable_target_consolidation(
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
    assert summary["max_step_noncompletion_row_count"] > 0
    assert summary["speed_too_low_row_count"] > 0
    assert summary["diagnostic_guardrail_row_count"] > 0
    assert summary["family_membership_diagnostic_row_count"] > 0
    assert summary["diagnostic_axis_repair_target_count"] == 0
    assert summary["family_axis_repair_target_count"] == 0
    assert summary["profile_axis_repair_target_count"] == 0
    assert summary["r4_ordinary_repair_target_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_family_ranking_claim_made"] is False
    assert summary["support_policy_ranking_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["training_repair_success_claim_made"] is False

    consolidated_rows = consolidation.read_csv_rows(tmp_path / "out" / "consolidated_rows.csv")
    family_rows = [row for row in consolidated_rows if row["source_table"] == "episode_family_membership_rows"]
    assert family_rows
    assert {row["consolidated_route"] for row in family_rows} == {"source_linked_family_diagnostic_guardrail"}
    assert {row["repair_target_admissible"] for row in family_rows} == {"False"}
    profile_row = next(row for row in consolidated_rows if row["slice_axis"] == "profile_name")
    assert profile_row["consolidated_route"] == "diagnostic_guardrail"
    assert profile_row["repair_target_admissible"] == "False"
    role_row = next(row for row in consolidated_rows if row["slice_value"] == "R2_handling_limit_drift_capable_avoidance")
    assert role_row["consolidated_route"] == "offtrack_repair_target"
    max_row = next(row for row in consolidated_rows if row["slice_value"] == "max_step_high")
    assert max_row["consolidated_route"] == "max_step_noncompletion_target"
    speed_row = next(row for row in consolidated_rows if row["slice_value"] == "speed_too_low_high")
    assert speed_row["consolidated_route"] == "speed_too_low_target"

    claim_rows = consolidation.read_csv_rows(tmp_path / "out" / "claim_boundary.csv")
    blocked_claims = {row["claim"] for row in claim_rows if row["admissible"] == "False"}
    assert "candidate_family_ranking" in blocked_claims
    assert "support_policy_ranking" in blocked_claims
    assert "training_repair_success" in blocked_claims
    assert "current_sim_verdict" in blocked_claims


def test_source_linked_consolidation_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = [
        _slice(
            axis="role_family",
            value="R2_handling_limit_drift_capable_avoidance",
            route_class="offtrack_target",
            offtrack=True,
            collision=False,
        )
    ]
    source = _write_source(tmp_path, rows)
    payload = read_json(source / "summary.json")
    payload["result_class"] = "current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_incomplete_or_fail"
    write_json(source / "summary.json", payload)

    summary = consolidation.run_source_linked_actionable_target_consolidation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_slice_row_count=len(rows),
        minimum_actionable_episode_count=1,
    )

    assert summary["result_class"] == consolidation.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_source_linked_consolidation_fails_closed_on_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _slice(
            axis="role_family",
            value="R2_handling_limit_drift_capable_avoidance",
            route_class="offtrack_target",
            offtrack=True,
            collision=False,
        )
    ]
    source = _write_source(tmp_path, rows)

    summary = consolidation.run_source_linked_actionable_target_consolidation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_slice_row_count=2,
        minimum_actionable_episode_count=1,
    )

    assert summary["result_class"] == consolidation.RESULT_FAIL
    assert summary["source_slice_row_count"] == 1
