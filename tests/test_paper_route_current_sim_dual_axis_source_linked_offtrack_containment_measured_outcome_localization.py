from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import (
    paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization as localization,
)
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    index: int,
    profile_name: str,
    role_family: str,
    outcome_bucket: str,
    collision: bool = False,
    termination_reason: str = "",
) -> dict[str, Any]:
    return {
        "workload_id": f"workload_{index:03d}",
        "reset_target_key": f"pack|spec_{index % 4}|hash_{index % 4}",
        "pack_id": "g_primary_pack",
        "profile_name": profile_name,
        "role_family": role_family,
        "scenario_family_id": role_family.split("_", maxsplit=1)[0],
        "sampled_obstacle_label": "drift_required" if role_family.startswith("R2") else "aeb_feasible",
        "hidden_dynamics_bucket": "low_mu" if index % 2 else "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "success": outcome_bucket == "success_obstacle_pass",
        "collision": collision,
        "truncated": outcome_bucket == "max_steps_noncompletion",
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
    }


def _membership_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    membership: list[dict[str, Any]] = []
    for row in rows:
        family_ids = ["c03_general_offtrack_boundary_containment"]
        if str(row["role_family"]).startswith("R4"):
            family_ids.append("c04_role_conditioned_containment")
        else:
            family_ids.append("c01_geometry_timing_containment")
        for family_id in family_ids:
            member = dict(row)
            member["family_id"] = family_id
            membership.append(member)
    return membership


def _source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for _ in range(8):
        rows.append(
            _episode(
                index=index,
                profile_name="L3_online_gru",
                role_family="R2_handling_limit_drift_capable_avoidance",
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
            )
        )
        index += 1
    for _ in range(2):
        rows.append(
            _episode(
                index=index,
                profile_name="L3_online_gru",
                role_family="R2_handling_limit_drift_capable_avoidance",
                outcome_bucket="collision_failure",
                collision=True,
                termination_reason="obstacle_collision",
            )
        )
        index += 1
    for _ in range(5):
        rows.append(
            _episode(
                index=index,
                profile_name="L0_current_masked",
                role_family="R4_unavoidable_mitigation",
                outcome_bucket="collision_failure",
                collision=True,
                termination_reason="obstacle_collision",
            )
        )
        index += 1
    for _ in range(3):
        rows.append(
            _episode(
                index=index,
                profile_name="L1_one_step",
                role_family="R0_stable_avoidable",
                outcome_bucket="speed_too_low_noncollision_noncompletion",
                termination_reason="speed_too_low",
            )
        )
        index += 1
    for _ in range(2):
        rows.append(
            _episode(
                index=index,
                profile_name="L2_window_25",
                role_family="R5_hidden_dynamics_robustness",
                outcome_bucket="max_steps_noncompletion",
                termination_reason="",
            )
        )
        index += 1
    for _ in range(2):
        rows.append(
            _episode(
                index=index,
                profile_name="L2_window_50",
                role_family="R1_aeb_infeasible_stable_aes",
                outcome_bucket="success_obstacle_pass",
                termination_reason="obstacle_completed",
            )
        )
        index += 1
    return rows


def _write_source(tmp_path: Path, rows: list[dict[str, Any]], *, result_class: str | None = None) -> Path:
    source = tmp_path / "source"
    write_json(
        source / "summary.json",
        {"result_class": result_class or "current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass"},
    )
    write_csv_rows(source / "episode_rows.csv", rows)
    write_csv_rows(source / "episode_family_membership_rows.csv", _membership_rows(rows))
    return source


def test_source_linked_outcome_localization_materializes_slice_classes(tmp_path: Path) -> None:
    rows = _source_rows()
    membership_rows = _membership_rows(rows)
    source = _write_source(tmp_path, rows)

    summary = localization.run_source_linked_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=len(rows),
        target_family_membership_row_count=len(membership_rows),
        minimum_slice_episode_count=1,
        offtrack_target_threshold=0.70,
        high_priority_offtrack_threshold=0.85,
        collision_guardrail_threshold=0.15,
        speed_too_low_threshold=0.05,
    )

    assert summary["result_class"] == localization.RESULT_PASS
    assert summary["source_episode_count"] == len(rows)
    assert summary["source_family_membership_row_count"] == len(membership_rows)
    assert summary["source_family_id_count"] == 3
    assert summary["slice_row_count"] > 0
    assert summary["episode_slice_row_count"] > 0
    assert summary["family_membership_slice_row_count"] > 0
    assert summary["offtrack_target_slice_count"] > 0
    assert summary["collision_guardrail_slice_count"] > 0
    assert summary["r4_mitigation_semantics_slice_count"] > 0
    assert summary["max_step_noncompletion_slice_count"] > 0
    assert summary["speed_too_low_slice_count"] > 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_family_ranking_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    slice_rows = localization.read_csv_rows(tmp_path / "out" / "slice_rows.csv")
    assert {row["source_linked_outcome_localization"] for row in slice_rows} == {"True"}
    assert {"episode_rows", "episode_family_membership_rows"} <= {row["source_table"] for row in slice_rows}
    assert any(row["slice_axis"] == "family_id+role_family" for row in slice_rows)
    assert (tmp_path / "out" / "speed_too_low_slice_rows.csv").exists()
    assert (tmp_path / "out" / "max_step_noncompletion_slice_rows.csv").exists()
    claim_rows = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "candidate_family_ranking" in claim_rows
    assert "current_sim_verdict" in claim_rows


def test_source_linked_outcome_localization_fails_closed_on_bad_count(tmp_path: Path) -> None:
    rows = _source_rows()
    source = _write_source(tmp_path, rows)

    summary = localization.run_source_linked_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=len(rows) + 1,
        target_family_membership_row_count=len(_membership_rows(rows)),
        minimum_slice_episode_count=1,
    )

    assert summary["result_class"] == localization.RESULT_FAIL
    assert summary["source_episode_count"] == len(rows)


def test_source_linked_outcome_localization_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = _source_rows()
    source = _write_source(
        tmp_path,
        rows,
        result_class="current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_incomplete_or_fail",
    )

    summary = localization.run_source_linked_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=len(rows),
        target_family_membership_row_count=len(_membership_rows(rows)),
        minimum_slice_episode_count=1,
    )

    assert summary["result_class"] == localization.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_source_linked_outcome_localization_fails_closed_on_membership_count(tmp_path: Path) -> None:
    rows = _source_rows()
    source = _write_source(tmp_path, rows)

    summary = localization.run_source_linked_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=len(rows),
        target_family_membership_row_count=len(_membership_rows(rows)) + 1,
        minimum_slice_episode_count=1,
    )

    assert summary["result_class"] == localization.RESULT_FAIL
    assert summary["source_family_membership_row_count"] == len(_membership_rows(rows))
