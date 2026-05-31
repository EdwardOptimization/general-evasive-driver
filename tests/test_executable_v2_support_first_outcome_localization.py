from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_support_first_outcome_localization as loc
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


def _episode(
    *,
    workload_id: str,
    role: str,
    surface: str,
    profile: str,
    outcome: str,
    collision: bool,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "support_first_workload_id": workload_id,
        "task_source_id": workload_id.split("::")[0],
        "support_first_v2_panel_spec_id": workload_id.split("::")[0],
        "controller_profile_name": profile,
        "profile_name": profile,
        "role_panel_id": role,
        "v2_role_surface_id": f"{role}::{surface}",
        "surface_variant": surface,
        "scenario_profile_name": f"{role}_{surface}_grid_v0",
        "hidden_dynamics_bucket": "mu_0p4::steady_surface",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": surface,
        "obstacle_lateral_bucket": "support_first_width_0p7",
        "sampled_obstacle_label": "drift_required" if "drift" in role else "aeb_feasible",
        "success": False,
        "obstacle_completed": False,
        "collision": collision,
        "min_clearance_margin": -0.2 if collision else 4.0,
        "return": -2.0 if collision else 1.0,
        "steps": 20,
        "action_rate_mean": 0.05,
        "high_sideslip_fraction": 0.0,
        "outcome_bucket": outcome,
        "termination_reason": "collision" if collision else "off_track",
        "dt": 0.02,
        "track_width": 5.0,
        "recovery_success": False,
        "drift_used": False,
        "controlled_drift_recovery_success": False,
        "collision_mitigation_score": 1.0 if collision else 0.0,
        "max_abs_beta": 0.1,
        "max_abs_yaw_rate": 0.2,
        "max_off_track_overshoot": 0.2 if not collision else 0.0,
        "off_track_severity_proxy": 0.2 if not collision else 0.0,
        "obstacle_passed_raw": False,
    }


def test_support_first_outcome_localization_writes_dominance_tables(tmp_path: Path) -> None:
    rows = [
        _episode(
            workload_id="spec0::L0_current_masked",
            role="stable_aeb",
            surface="steady_surface",
            profile="L0_current_masked",
            outcome="off_track_noncollision_noncompletion",
            collision=False,
        ),
        _episode(
            workload_id="spec1::L1_one_step",
            role="stable_aeb",
            surface="steady_surface",
            profile="L1_one_step",
            outcome="off_track_noncollision_noncompletion",
            collision=False,
        ),
        _episode(
            workload_id="spec2::L0_current_masked",
            role="unavoidable_mitigation",
            surface="steady_surface",
            profile="L0_current_masked",
            outcome="collision_failure",
            collision=True,
        ),
        _episode(
            workload_id="spec3::L1_one_step",
            role="unavoidable_mitigation",
            surface="steady_surface",
            profile="L1_one_step",
            outcome="collision_failure",
            collision=True,
        ),
    ]
    episode_rows = tmp_path / "episode_rows.csv"
    source_summary = tmp_path / "summary.json"
    write_csv_rows(episode_rows, rows)
    write_json(source_summary, {"result_class": "executable_v2_support_first_measured_runner_execution_pass"})

    summary = loc.localize_support_first_outcomes(
        episode_rows_path=episode_rows,
        summary_path=source_summary,
        output_dir=tmp_path / "out",
        target_episode_count=4,
        min_dominant_episodes=1,
    )

    assert summary["result_class"] == "support_first_outcome_localization_pass"
    assert summary["episode_count"] == 4
    assert summary["outcome_counts"] == {
        "collision_failure": 2,
        "off_track_noncollision_noncompletion": 2,
    }
    assert summary["ranking_blocked"] is True
    assert summary["recommended_next_route"] == "scenario_task_quality_repair_design"
    assert summary["guardrail_violation_count"] == 0
    assert set(loc.TARGET_LOCALIZATION_SLICE_TYPES).issubset(set(summary["target_slice_types_present"]))
    assert (tmp_path / "out" / "dominant_slices.csv").exists()
    assert (tmp_path / "out" / "role_surface_profile_aggregate.csv").exists()
    assert read_csv_rows(tmp_path / "out" / "target_dominant_slices.csv")
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["source_result_class"] == "executable_v2_support_first_measured_runner_execution_pass"
