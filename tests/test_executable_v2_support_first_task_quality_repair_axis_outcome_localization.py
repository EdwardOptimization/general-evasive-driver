from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_support_first_task_quality_repair_axis_outcome_localization as loc
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


def _row(
    *,
    workload_id: str,
    execution_row_kind: str,
    explicit_fields: bool,
    collision: bool,
    termination_reason: str,
    margin: float,
    overshoot: float,
    offtrack_time: float | str,
) -> dict[str, object]:
    row: dict[str, object] = {
        "workload_id": workload_id,
        "task_quality_repair_axis_row_id": f"axis::{workload_id}",
        "task_quality_axis_id": "post_clearance_containment_recovery",
        "repair_axis_variant_id": "post_clearance_recovery_window_plus",
        "axis_applicability": "targeted",
        "target_conflict_class": "clearance_only_offtrack",
        "target_near_miss_class": "near_containment_after_clearance",
        "execution_row_kind": execution_row_kind,
        "row_provenance": execution_row_kind,
        "controller_profile_name": "L3_online_gru",
        "profile_name": "L3_online_gru",
        "role_panel_id": "stable_aes_only",
        "v2_role_surface_id": "stable_aes_only::post_friction_step",
        "hidden_dynamics_bucket": "mu_0p25::post_friction_step",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": "post_friction_step",
        "obstacle_lateral_bucket": "support_first_width_0p7",
        "sampled_obstacle_label": "aes_feasible",
        "collision": collision,
        "success": False,
        "min_clearance_margin": margin,
        "max_off_track_overshoot": overshoot,
        "impact_severity_proxy": 1.0 if collision else 0.0,
        "time_to_first_off_track_s": offtrack_time,
        "termination_reason": termination_reason,
        "outcome_bucket": "collision_failure" if collision else "off_track_noncollision_noncompletion",
        "return": 1.0,
        "steps": 20,
        "action_rate_mean": 0.05,
        "high_sideslip_fraction": 0.0,
    }
    if explicit_fields:
        obstacle_clearance = (not collision) and margin > 0.0
        road_containment = termination_reason != "off_track"
        row.update(
            {
                "obstacle_clearance_pass": obstacle_clearance,
                "road_containment_pass": road_containment,
                "collision_failure": collision,
                "obstacle_pass_before_offtrack": False,
                "offtrack_after_clearance": obstacle_clearance and not road_containment,
                "controlled_recovery_pass": False,
            }
        )
    else:
        for field in loc.FLAG_FIELDS:
            row[field] = ""
    return row


def test_infer_task_quality_flags_from_raw_measured_row() -> None:
    row = _row(
        workload_id="raw_clearance_only",
        execution_row_kind="rollout_geometry_variant",
        explicit_fields=False,
        collision=False,
        termination_reason="off_track",
        margin=0.5,
        overshoot=0.1,
        offtrack_time=2.5,
    )

    flags = loc.infer_task_quality_flags(row)
    assert flags["obstacle_clearance_pass"] is True
    assert flags["road_containment_pass"] is False
    assert flags["collision_failure"] is False
    localized = loc.localized_conflict_rows([row])[0]
    assert localized["classification_source"] == "raw_metric_inference"
    assert localized["primary_conflict_class"] == "clearance_only_offtrack"
    assert localized["near_containment_after_clearance"] is True
    assert localized["late_offtrack_after_clearance"] is True


def test_localization_writes_full_panel_artifacts(tmp_path: Path) -> None:
    rows = [
        _row(
            workload_id="explicit_clearance_only",
            execution_row_kind="postprocess_existing_episode",
            explicit_fields=True,
            collision=False,
            termination_reason="off_track",
            margin=0.8,
            overshoot=0.12,
            offtrack_time=2.0,
        ),
        _row(
            workload_id="raw_containment_collision",
            execution_row_kind="rollout_geometry_variant",
            explicit_fields=False,
            collision=True,
            termination_reason="obstacle_collision",
            margin=-0.1,
            overshoot=0.0,
            offtrack_time="nan",
        ),
        _row(
            workload_id="raw_collision_offtrack",
            execution_row_kind="rollout_geometry_variant",
            explicit_fields=False,
            collision=True,
            termination_reason="off_track",
            margin=-0.5,
            overshoot=0.2,
            offtrack_time=1.0,
        ),
    ]
    episode_rows = tmp_path / "episode_rows.csv"
    source_summary = tmp_path / "summary.json"
    write_csv_rows(episode_rows, rows)
    write_json(source_summary, {"result_class": "task_quality_repair_axis_measured_wrapper_execution_pass"})

    summary = loc.localize_task_quality_repair_axis_outcomes(
        episode_rows_path=episode_rows,
        summary_path=source_summary,
        output_dir=tmp_path / "out",
        target_episode_count=3,
    )

    assert summary["result_class"] == "task_quality_repair_axis_measured_panel_outcome_localization_pass"
    assert summary["episode_count"] == 3
    assert summary["classification_source_counts"] == {
        "explicit_task_quality_fields": 1,
        "raw_metric_inference": 2,
    }
    assert summary["primary_conflict_class_counts"]["clearance_only_offtrack"] == 1
    assert summary["primary_conflict_class_counts"]["containment_collision"] == 1
    assert summary["primary_conflict_class_counts"]["collision_and_offtrack"] == 1
    assert summary["near_miss_counts"]["near_containment_after_clearance"] == 1
    assert summary["near_miss_row_count"] == 2
    assert summary["recommended_next_route"] == "route_to_branch_synthesis_with_task_quality_findings"
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "task_axis_variant_conflict_aggregate.csv").exists()
    localized_rows = read_csv_rows(tmp_path / "out" / "conflict_class_rows.csv")
    assert len(localized_rows) == 3
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["required_aggregate_files_written"] is True
