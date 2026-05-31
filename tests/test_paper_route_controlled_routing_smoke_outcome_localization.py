from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_controlled_routing_smoke_outcome_localization as loc
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    workload_id: str,
    task_source_id: str,
    profile_name: str,
    panel_task_family: str = "T1_reactive_active_safety",
    source_kind: str = "anchor_neighborhood",
    proxy_template_family: str = "t5_near_boundary_warmup",
    generated_source_row: bool = False,
    outcome_bucket: str,
    termination_reason: str,
    success: bool,
    collision: bool,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "task_source_id": task_source_id,
        "panel_source_id": f"{task_source_id}_panel",
        "panel_task_family": panel_task_family,
        "source_origin": "unit_test",
        "source_kind": source_kind,
        "source_edge": "unit_edge",
        "source_role_semantics": "stable_aeb",
        "parent_feasibility_tier_id": "tier_c_boundary_near_miss",
        "normalized_surface_variant": "steady_surface",
        "sampled_obstacle_label": "aeb_feasible",
        "source_reference": f"{task_source_id}_reference",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": proxy_template_family,
        "generated_source_row": generated_source_row,
        "paper_validity_claim": False,
        "profile_name": profile_name,
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "success": success,
        "collision": collision,
        "min_clearance_margin": 1.0 if success else (-0.1 if collision else 2.0),
        "return": 10.0 if success else -1.0,
        "steps": 20,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
    }


def _write_inputs(tmp_path: Path, rows: list[dict[str, object]], *, mismatch: bool = False) -> tuple[Path, Path]:
    counts = {
        "success_obstacle_pass": sum(1 for row in rows if row["outcome_bucket"] == "success_obstacle_pass"),
        "collision_failure": sum(1 for row in rows if row["outcome_bucket"] == "collision_failure"),
        "off_track_noncollision_noncompletion": sum(
            1 for row in rows if row["outcome_bucket"] == "off_track_noncollision_noncompletion"
        ),
    }
    if mismatch:
        counts["success_obstacle_pass"] += 1
    summary_path = tmp_path / "summary.json"
    episode_rows_path = tmp_path / "episode_rows.csv"
    write_json(summary_path, {"result_class": "controlled_routing_smoke_measured_execution_pass", "outcome_counts": counts})
    write_csv_rows(episode_rows_path, rows)
    return summary_path, episode_rows_path


def test_routing_smoke_localization_writes_aggregates_and_reproduces_counts(tmp_path: Path) -> None:
    rows: list[dict[str, object]] = []
    for index in range(6):
        rows.append(
            _episode(
                workload_id=f"success_{index}",
                task_source_id=f"source_{index % 3}",
                profile_name=f"L{index % 3}_profile",
                outcome_bucket="success_obstacle_pass",
                termination_reason="",
                success=True,
                collision=False,
            )
        )
    for index in range(12):
        rows.append(
            _episode(
                workload_id=f"offtrack_{index}",
                task_source_id=f"offtrack_source_{index % 3}",
                profile_name="L2_window_13",
                panel_task_family="T2_same_current_different_older_history",
                source_kind="same_current_steer_lag_older_history_proxy",
                proxy_template_family="t5_boundary_axis_retarget",
                generated_source_row=True,
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
                success=False,
                collision=False,
            )
        )
    for index in range(6):
        rows.append(
            _episode(
                workload_id=f"collision_{index}",
                task_source_id=f"collision_source_{index % 2}",
                profile_name="L1_one_step",
                panel_task_family="T5_source_rich_extreme_dynamics",
                source_kind="mitigation_isolation_check",
                outcome_bucket="collision_failure",
                termination_reason="obstacle_collision",
                success=False,
                collision=True,
            )
        )
    summary_path, episode_rows_path = _write_inputs(tmp_path, rows)

    summary = loc.localize_controlled_routing_smoke_outcomes(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=24,
        target_profile_count=5,
        target_spec_count=8,
        target_family_count=3,
    )

    assert summary["result_class"] == "controlled_routing_smoke_outcome_localization_pass"
    assert summary["outcome_counts_match_source_summary"] is True
    assert summary["success_row_count"] == 6
    assert summary["comparison_ready_candidate_count"] >= 1
    assert summary["offtrack_dominance_slice_count"] > 0
    assert summary["collision_dominance_slice_count"] > 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert (tmp_path / "out" / "outcome_by_profile.csv").exists()
    assert (tmp_path / "out" / "outcome_by_profile_family.csv").exists()
    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "finite_window_vs_gru_conclusion" in claim_boundary
    assert "False" in claim_boundary


def test_routing_smoke_localization_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    rows = [
        _episode(
            workload_id="success_0",
            task_source_id="source_0",
            profile_name="L3_online_gru",
            outcome_bucket="success_obstacle_pass",
            termination_reason="",
            success=True,
            collision=False,
        )
    ]
    summary_path, episode_rows_path = _write_inputs(tmp_path, rows, mismatch=True)

    summary = loc.localize_controlled_routing_smoke_outcomes(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=1,
        target_profile_count=1,
        target_spec_count=1,
        target_family_count=1,
    )

    assert summary["result_class"] == "controlled_routing_smoke_outcome_localization_incomplete_or_fail"
    assert summary["outcome_counts_match_source_summary"] is False
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["paper_level_claim_made"] is False
    assert persisted["level3_self_id_claim_made"] is False


def test_routing_smoke_localization_fails_closed_on_missing_schema(tmp_path: Path) -> None:
    row = _episode(
        workload_id="success_0",
        task_source_id="source_0",
        profile_name="L3_online_gru",
        outcome_bucket="success_obstacle_pass",
        termination_reason="",
        success=True,
        collision=False,
    )
    del row["proxy_template_family"]
    summary_path, episode_rows_path = _write_inputs(tmp_path, [row])

    summary = loc.localize_controlled_routing_smoke_outcomes(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=1,
        target_profile_count=1,
        target_spec_count=1,
        target_family_count=1,
    )

    assert summary["result_class"] == "controlled_routing_smoke_outcome_localization_incomplete_or_fail"
    assert summary["missing_schema_fields"] == ["proxy_template_family"]
