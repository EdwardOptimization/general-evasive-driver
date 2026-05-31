from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_repaired_measured_outcome_localization as loc
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    profile_name: str,
    repair_source_kind: str = "success_stabilizer",
    role: str = "stable_aes_only",
    parent_tier: str = "tier_b_feasible_emergency",
    normalized_surface: str = "steady_surface",
    sampled_label: str = "aes_feasible",
    outcome_bucket: str,
    termination_reason: str,
    success: bool,
    collision: bool,
    workload_id: str,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "candidate_source_id": f"{workload_id}_candidate",
        "task_source_id": f"{workload_id}_task",
        "profile_name": profile_name,
        "repair_source_kind": repair_source_kind,
        "selection_quota_name": f"{repair_source_kind}_quota",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": parent_tier,
        "parent_surface_variant": normalized_surface,
        "normalized_surface_variant": normalized_surface,
        "source_split": "public_debug",
        "base_geometry_source": "unit_test_base",
        "representative_cell_rule": "unit_test_rule",
        "sampled_obstacle_label": sampled_label,
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "success": success,
        "collision": collision,
        "min_clearance_margin": 0.25 if success else (-0.1 if collision else 1.5),
        "return": 10.0 if success else -1.0,
        "steps": 20,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
    }


def _write_inputs(tmp_path: Path, rows: list[dict[str, object]], *, mismatch: bool = False) -> tuple[Path, Path]:
    source_counts = {
        "success_obstacle_pass": sum(1 for row in rows if row["outcome_bucket"] == "success_obstacle_pass"),
        "collision_failure": sum(1 for row in rows if row["outcome_bucket"] == "collision_failure"),
        "off_track_noncollision_noncompletion": sum(
            1 for row in rows if row["outcome_bucket"] == "off_track_noncollision_noncompletion"
        ),
    }
    if mismatch:
        source_counts["success_obstacle_pass"] += 1
    summary_path = tmp_path / "summary.json"
    episode_rows_path = tmp_path / "episode_rows.csv"
    write_json(
        summary_path,
        {"result_class": "task_quality_calibrated_measured_execution_pass", "outcome_counts": source_counts},
    )
    write_csv_rows(episode_rows_path, rows)
    return summary_path, episode_rows_path


def test_calibrated_repaired_localization_writes_aggregates_and_reproduces_source_counts(tmp_path: Path) -> None:
    rows: list[dict[str, object]] = []
    for index in range(6):
        rows.append(
            _episode(
                profile_name="L0_current_masked" if index < 3 else "L3_online_gru",
                outcome_bucket="success_obstacle_pass",
                termination_reason="",
                success=True,
                collision=False,
                workload_id=f"success_{index}",
            )
        )
    for index in range(12):
        rows.append(
            _episode(
                profile_name="L2_window_13" if index < 6 else "L2_window_25",
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
                success=False,
                collision=False,
                workload_id=f"offtrack_{index}",
            )
        )
    for index in range(6):
        rows.append(
            _episode(
                profile_name="L1_one_step",
                repair_source_kind="mitigation_isolation_check",
                role="unavoidable_mitigation",
                parent_tier="tier_d_unavoidable",
                normalized_surface="post_friction_step",
                sampled_label="unavoidable",
                outcome_bucket="collision_failure",
                termination_reason="obstacle_collision",
                success=False,
                collision=True,
                workload_id=f"collision_{index}",
            )
        )
    summary_path, episode_rows_path = _write_inputs(tmp_path, rows)

    summary = loc.localize_calibrated_repaired_outcomes(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=24,
        target_profile_count=5,
        target_source_kind_count=2,
        target_role_count=2,
        target_normalized_surface_count=2,
        target_sampled_label_count=2,
    )

    assert summary["result_class"] == "task_quality_calibrated_repaired_measured_outcome_localization_pass"
    assert summary["episode_count"] == 24
    assert summary["outcome_counts_match_source_summary"] is True
    assert summary["missing_schema_fields"] == []
    assert summary["success_source_row_count"] == 6
    assert summary["l2_total_success_count"] == 0
    assert summary["l2_same_slice_non_l2_success_pattern_count"] == 2
    assert summary["comparison_support_candidate_count"] == 1
    assert summary["comparison_ready_candidate_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert (tmp_path / "out" / "outcome_by_repair_source_kind.csv").exists()
    assert (tmp_path / "out" / "outcome_by_source_kind_role_surface.csv").exists()
    assert (tmp_path / "out" / "comparison_support_candidates.csv").exists()
    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "finite_window_vs_gru_conclusion" in claim_boundary
    assert "False" in claim_boundary


def test_calibrated_repaired_localization_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _episode(
            profile_name="L0_current_masked",
            outcome_bucket="success_obstacle_pass",
            termination_reason="",
            success=True,
            collision=False,
            workload_id="success_0",
        )
    ]
    summary_path, episode_rows_path = _write_inputs(tmp_path, rows, mismatch=True)

    summary = loc.localize_calibrated_repaired_outcomes(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=1,
        target_profile_count=1,
        target_source_kind_count=1,
        target_role_count=1,
        target_normalized_surface_count=1,
        target_sampled_label_count=1,
    )

    assert summary["result_class"] == "task_quality_calibrated_repaired_measured_outcome_localization_incomplete_or_fail"
    assert summary["outcome_counts_match_source_summary"] is False
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["paper_level_claim_made"] is False
    assert persisted["level3_self_id_claim_made"] is False


def test_calibrated_repaired_localization_fails_closed_on_missing_repair_schema(tmp_path: Path) -> None:
    row = _episode(
        profile_name="L0_current_masked",
        outcome_bucket="success_obstacle_pass",
        termination_reason="",
        success=True,
        collision=False,
        workload_id="success_0",
    )
    del row["parent_feasibility_tier_id"]
    summary_path, episode_rows_path = _write_inputs(tmp_path, [row])

    summary = loc.localize_calibrated_repaired_outcomes(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=1,
        target_profile_count=1,
        target_source_kind_count=1,
        target_role_count=1,
        target_normalized_surface_count=1,
        target_sampled_label_count=1,
    )

    assert summary["result_class"] == "task_quality_calibrated_repaired_measured_outcome_localization_incomplete_or_fail"
    assert summary["missing_schema_fields"] == ["parent_feasibility_tier_id"]
