from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_support_first_clearance_containment_conflict_localization as loc
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


def _episode(
    *,
    workload_id: str,
    obstacle_clearance: bool,
    road_containment: bool,
    collision_failure: bool,
    margin: float,
    overshoot: float,
    offtrack_time: float | str,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "repaired_workload_id": f"repaired::{workload_id}",
        "support_first_workload_id": workload_id,
        "task_source_id": workload_id.split("::")[0],
        "controller_profile_name": "L3_online_gru",
        "profile_name": "L3_online_gru",
        "role_panel_id": "stable_aes_only",
        "v2_role_surface_id": "stable_aes_only::post_friction_step",
        "repair_variant_id": "road_relaxed",
        "repair_variant_kind": "geometry",
        "geometry_variant_id": "road_relaxed_geometry",
        "success_semantics_variant_id": "role_aware_success_v1",
        "hidden_dynamics_bucket": "mu_0p25::post_friction_step",
        "obstacle_timing_bucket": "post_friction_step",
        "obstacle_lateral_bucket": "support_first_width_0p7",
        "sampled_obstacle_label": "aes_feasible",
        "obstacle_clearance_pass": obstacle_clearance,
        "road_containment_pass": road_containment,
        "collision_failure": collision_failure,
        "obstacle_pass_before_offtrack": False,
        "offtrack_after_clearance": obstacle_clearance and not road_containment,
        "collision": collision_failure,
        "success": obstacle_clearance and road_containment,
        "min_clearance_margin": margin,
        "max_off_track_overshoot": overshoot,
        "impact_severity_proxy": 1.0 if collision_failure else 0.0,
        "time_to_first_off_track_s": offtrack_time,
        "termination_reason": "obstacle_collision" if collision_failure else "off_track",
        "outcome_bucket": "collision_failure" if collision_failure else "off_track_noncollision_noncompletion",
        "return": 1.0,
        "steps": 20,
        "action_rate_mean": 0.05,
        "high_sideslip_fraction": 0.0,
    }


def test_primary_conflict_and_near_miss_classification() -> None:
    joint = _episode(
        workload_id="spec0::L3_online_gru",
        obstacle_clearance=True,
        road_containment=True,
        collision_failure=False,
        margin=1.0,
        overshoot=0.0,
        offtrack_time="nan",
    )
    clearance_only = _episode(
        workload_id="spec1::L3_online_gru",
        obstacle_clearance=True,
        road_containment=False,
        collision_failure=False,
        margin=1.0,
        overshoot=0.10,
        offtrack_time=2.5,
    )
    containment_collision = _episode(
        workload_id="spec2::L3_online_gru",
        obstacle_clearance=False,
        road_containment=True,
        collision_failure=True,
        margin=-0.10,
        overshoot=0.0,
        offtrack_time="nan",
    )
    collision_and_offtrack = _episode(
        workload_id="spec3::L3_online_gru",
        obstacle_clearance=False,
        road_containment=False,
        collision_failure=True,
        margin=-0.50,
        overshoot=0.2,
        offtrack_time=1.0,
    )

    assert loc.classify_primary_conflict(joint) == "joint_clearance_containment"
    assert loc.classify_primary_conflict(clearance_only) == "clearance_only_offtrack"
    assert loc.classify_primary_conflict(containment_collision) == "containment_collision"
    assert loc.classify_primary_conflict(collision_and_offtrack) == "collision_and_offtrack"
    assert loc.near_miss_flags(clearance_only) == {
        "near_containment_after_clearance": True,
        "near_clearance_with_containment": False,
        "late_offtrack_after_clearance": True,
    }
    assert loc.near_miss_flags(containment_collision)["near_clearance_with_containment"] is True


def test_clearance_containment_localization_writes_artifacts(tmp_path: Path) -> None:
    rows = [
        _episode(
            workload_id="spec0::L3_online_gru",
            obstacle_clearance=True,
            road_containment=False,
            collision_failure=False,
            margin=1.0,
            overshoot=0.10,
            offtrack_time=2.5,
        ),
        _episode(
            workload_id="spec1::L3_online_gru",
            obstacle_clearance=False,
            road_containment=True,
            collision_failure=True,
            margin=-0.10,
            overshoot=0.0,
            offtrack_time="nan",
        ),
        _episode(
            workload_id="spec2::L3_online_gru",
            obstacle_clearance=False,
            road_containment=False,
            collision_failure=True,
            margin=-0.50,
            overshoot=0.2,
            offtrack_time=1.0,
        ),
    ]
    episode_rows = tmp_path / "episode_rows.csv"
    source_summary = tmp_path / "summary.json"
    write_csv_rows(episode_rows, rows)
    write_json(source_summary, {"result_class": "executable_v2_support_first_repaired_bounded_smoke_execution_pass"})

    summary = loc.localize_clearance_containment_conflicts(
        episode_rows_path=episode_rows,
        summary_path=source_summary,
        output_dir=tmp_path / "out",
        target_episode_count=3,
    )

    assert summary["result_class"] == "clearance_containment_conflict_localization_pass"
    assert summary["source_result_class"] == "executable_v2_support_first_repaired_bounded_smoke_execution_pass"
    assert summary["episode_count"] == 3
    assert summary["all_rows_classified_once"] is True
    assert summary["primary_conflict_class_counts"]["joint_clearance_containment"] == 0
    assert summary["primary_conflict_class_counts"]["clearance_only_offtrack"] == 1
    assert summary["primary_conflict_class_counts"]["containment_collision"] == 1
    assert summary["primary_conflict_class_counts"]["collision_and_offtrack"] == 1
    assert summary["near_miss_counts"]["near_containment_after_clearance"] == 1
    assert summary["near_miss_counts"]["near_clearance_with_containment"] == 1
    assert summary["near_miss_counts"]["late_offtrack_after_clearance"] == 1
    assert summary["recommended_next_route"] == "route_to_task_quality_repair_axis_design"
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "conflict_class_rows.csv").exists()
    assert (tmp_path / "out" / "role_surface_repair_variant_conflict_aggregate.csv").exists()
    assert read_csv_rows(tmp_path / "out" / "near_miss_rows.csv")
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["required_aggregate_files_written"] is True
