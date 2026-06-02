from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_redesign_calibration_materialization import (
    run_dual_axis_redesign_calibration_materialization,
)


def _redesign_row(
    scenario_id: str,
    route: str,
    *,
    hidden: str = "low_mu",
    timing: str = "late_close",
    lateral: str = "centerline",
    failure: str = "collision_dominated_failure",
    theme: str = "collision_timing_pressure",
    role: str = "R2_handling_limit_drift_capable_avoidance",
) -> dict[str, object]:
    return {
        "scenario_spec_id": scenario_id,
        "redesign_source": "test",
        "role_family": role,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "sampled_obstacle_label": "drift_required",
        "same_scene_group_id": scenario_id,
        "hidden_dynamics_bucket": hidden,
        "obstacle_longitudinal_timing_bucket": timing,
        "obstacle_lateral_offset_bucket": lateral,
        "initial_speed_mps": 16.0,
        "track_radius_m": 80.0,
        "track_width_m": 6.0,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "support_label": "support_blocked",
        "dominant_failure_mode": failure,
        "dominant_failure_bucket": failure,
        "source_signature": f"{role}|{hidden}|{timing}|{lateral}",
        "role_timing_lateral_signature": f"{role}|{timing}|{lateral}",
        "hidden_role_signature": f"{role}|{hidden}",
        "aeb_success_count": 0,
        "aeb_collision_count": 5,
        "aeb_offtrack_count": 0,
        "aes_success_count": 0,
        "aes_collision_count": 5 if failure == "collision_dominated_failure" else 0,
        "aes_offtrack_count": 5 if failure == "offtrack_dominated_failure" else 0,
        "envelope_aes_success_count": 0,
        "envelope_aes_collision_count": 0,
        "envelope_aes_offtrack_count": 5,
        "redesign_theme": theme,
        "redesign_priority_bucket": "high",
        "recommended_redesign_route": route,
        "redesign_reason": "test",
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_inputs(root: Path) -> tuple[Path, Path]:
    input_dir = root / "input"
    input_dir.mkdir()
    rows = [
        _redesign_row("g_late", "geometry_timing_rebalance_candidate", hidden="weak_brake"),
        _redesign_row(
            "g_offtrack",
            "geometry_timing_rebalance_candidate",
            hidden="nominal",
            timing="mid",
            lateral="right_offset",
            failure="offtrack_dominated_failure",
            theme="offtrack_geometry_pressure",
        ),
        _redesign_row(
            "h_low",
            "hidden_dynamics_range_rebalance_candidate",
            hidden="low_mu",
            timing="early_far",
            theme="hidden_dynamics_stress",
        ),
        _redesign_row(
            "h_r5",
            "hidden_dynamics_range_rebalance_candidate",
            hidden="nominal",
            timing="late_close",
            theme="hidden_dynamics_robustness_task_quality",
            role="R5_hidden_dynamics_robustness",
        ),
    ]
    write_csv_rows(input_dir / "consolidated_redesign_rows.csv", rows)
    write_csv_rows(
        input_dir / "secondary_coverage_materialization_rows.csv",
        [
            {
                "scenario_spec_id": "secondary_1",
                "scenario_family_id": "R2",
                "role_family": "R2_handling_limit_drift_capable_avoidance",
                "sampled_obstacle_label": "drift_required",
                "same_scene_group_id": "secondary_1",
                "hidden_dynamics_bucket": "slow_steer_actuator",
                "obstacle_longitudinal_timing_bucket": "early_far",
                "obstacle_lateral_offset_bucket": "centerline",
                "initial_speed_mps": 14.0,
                "track_radius_m": 80.0,
                "track_width_m": 6.0,
                "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
                "recommended_next_route": "support_policy_coverage_materialization_candidate",
            }
        ],
    )
    config = root / "config.json"
    write_json(
        config,
        {
            "scenario_specs": [
                {
                    "scenario_spec_id": "ref_r2_low",
                    "role_family": "R2_handling_limit_drift_capable_avoidance",
                    "initial_speed_mps": 12.0,
                    "track_width_m": 6.0,
                    "track_radius_m": 80.0,
                },
                {
                    "scenario_spec_id": "ref_r2_high",
                    "role_family": "R2_handling_limit_drift_capable_avoidance",
                    "initial_speed_mps": 16.0,
                    "track_width_m": 6.5,
                    "track_radius_m": 90.0,
                },
                {
                    "scenario_spec_id": "ref_r5",
                    "role_family": "R5_hidden_dynamics_robustness",
                    "initial_speed_mps": 16.0,
                    "track_width_m": 6.0,
                    "track_radius_m": 80.0,
                },
            ]
        },
    )
    return input_dir, config


def test_dual_axis_materializer_writes_bounded_candidate_artifacts(tmp_path: Path) -> None:
    input_dir, config = _write_inputs(tmp_path)
    output_dir = tmp_path / "out"

    summary = run_dual_axis_redesign_calibration_materialization(
        input_dir=input_dir,
        config=config,
        output_dir=output_dir,
        target_redesign_row_count=4,
        target_geometry_row_count=2,
        target_hidden_row_count=2,
        target_secondary_coverage_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_redesign_calibration_materialization_pass"
    assert summary["input_redesign_row_count"] == 4
    assert summary["geometry_timing_input_row_count"] == 2
    assert summary["hidden_range_input_row_count"] == 2
    assert summary["secondary_coverage_tracked_count"] == 1
    assert summary["rows_without_candidate_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["scenario_redesign_executed_claim_made"] is False

    persisted = read_json(output_dir / "summary.json")
    assert persisted["calibration_candidate_count"] == summary["calibration_candidate_count"]

    all_rows = (output_dir / "calibration_candidate_rows.csv").read_text(encoding="utf-8")
    assert "timing_step_earlier" in all_rows
    assert "lateral_offset_step_toward_centerline" in all_rows
    assert "low_mu_step_toward_nominal" in all_rows
    assert "same_scene_hidden_balance" in all_rows
    assert "GH" in all_rows

    secondary_rows = (output_dir / "secondary_coverage_rows.csv").read_text(encoding="utf-8")
    assert "dual_axis_redesign_calibration_not_materialized" in secondary_rows
    assert "False" in secondary_rows

    config_candidates = read_json(output_dir / "calibration_config_candidates.json")
    assert config_candidates["active_config_overwritten"] is False
    assert config_candidates["candidate_count"] == summary["calibration_candidate_count"]

    claims = (output_dir / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "scenario_redesign_executed,False,False" in claims
