from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization as localization
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    candidate_id: str,
    profile_name: str,
    role_family: str,
    outcome_bucket: str,
    collision: bool = False,
    termination_reason: str = "",
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "repair_family": "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": role_family,
        "pack_id": "g_primary_pack",
        "profile_name": profile_name,
        "role_family": role_family,
        "scenario_family_id": role_family.split("_", maxsplit=1)[0],
        "sampled_obstacle_label": "drift_required" if role_family.startswith("R2") else "aeb_feasible",
        "hidden_dynamics_bucket": "low_mu",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "success": outcome_bucket == "success_obstacle_pass",
        "collision": collision,
        "truncated": False,
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
    }


def _write_source(tmp_path: Path, rows: list[dict[str, Any]]) -> Path:
    source = tmp_path / "source"
    write_json(source / "summary.json", {"result_class": "current_sim_dual_axis_effective_candidate_measured_validation_pass"})
    write_csv_rows(source / "episode_rows.csv", rows)
    return source


def test_effective_candidate_outcome_localization_materializes_slice_classes(tmp_path: Path) -> None:
    rows = [
        *[
            _episode(
                candidate_id="candidate_a",
                profile_name="L3_online_gru",
                role_family="R2_handling_limit_drift_capable_avoidance",
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
            )
            for _ in range(8)
        ],
        *[
            _episode(
                candidate_id="candidate_a",
                profile_name="L3_online_gru",
                role_family="R2_handling_limit_drift_capable_avoidance",
                outcome_bucket="collision_failure",
                collision=True,
                termination_reason="obstacle_collision",
            )
            for _ in range(2)
        ],
        *[
            _episode(
                candidate_id="candidate_b",
                profile_name="L0_current_masked",
                role_family="R4_unavoidable_mitigation",
                outcome_bucket="collision_failure",
                collision=True,
                termination_reason="obstacle_collision",
            )
            for _ in range(5)
        ],
        *[
            _episode(
                candidate_id="candidate_b",
                profile_name="L0_current_masked",
                role_family="R4_unavoidable_mitigation",
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
            )
            for _ in range(5)
        ],
    ]
    source = _write_source(tmp_path, rows)

    summary = localization.run_effective_candidate_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=len(rows),
        minimum_slice_episode_count=1,
        offtrack_target_threshold=0.70,
        high_priority_offtrack_threshold=0.85,
        collision_guardrail_threshold=0.15,
    )

    assert summary["result_class"] == localization.RESULT_PASS
    assert summary["source_episode_count"] == len(rows)
    assert summary["source_candidate_count"] == 2
    assert summary["source_profile_count"] == 2
    assert summary["offtrack_target_slice_count"] > 0
    assert summary["collision_guardrail_slice_count"] > 0
    assert summary["r4_mitigation_semantics_slice_count"] > 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["effective_candidate_ranking_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    slice_rows = localization.read_csv_rows(tmp_path / "out" / "slice_rows.csv")
    assert {row["effective_candidate_outcome_localization"] for row in slice_rows} == {"True"}
    assert any(row["slice_axis"] == "candidate_id+role_family" for row in slice_rows)
    claim_rows = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "current_sim_verdict" in claim_rows
    assert "effective_candidate_ranking" in claim_rows


def test_effective_candidate_outcome_localization_fails_closed_on_bad_count(tmp_path: Path) -> None:
    rows = [
        _episode(
            candidate_id="candidate_a",
            profile_name="L3_online_gru",
            role_family="R2_handling_limit_drift_capable_avoidance",
            outcome_bucket="off_track_noncollision_noncompletion",
            termination_reason="off_track",
        )
    ]
    source = _write_source(tmp_path, rows)

    summary = localization.run_effective_candidate_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=2,
        minimum_slice_episode_count=1,
    )

    assert summary["result_class"] == localization.RESULT_FAIL
    assert summary["source_episode_count"] == 1


def test_effective_candidate_outcome_localization_fails_closed_on_source_failure(tmp_path: Path) -> None:
    rows = [
        _episode(
            candidate_id="candidate_a",
            profile_name="L3_online_gru",
            role_family="R2_handling_limit_drift_capable_avoidance",
            outcome_bucket="off_track_noncollision_noncompletion",
            termination_reason="off_track",
        )
    ]
    source = _write_source(tmp_path, rows)
    payload = read_json(source / "summary.json")
    payload["result_class"] = "current_sim_dual_axis_effective_candidate_measured_validation_incomplete_or_fail"
    write_json(source / "summary.json", payload)

    summary = localization.run_effective_candidate_measured_outcome_localization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_episode_count=1,
        minimum_slice_episode_count=1,
    )

    assert summary["result_class"] == localization.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")
