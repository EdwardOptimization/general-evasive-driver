from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.paper_route_current_sim_support_coverage_gap_source_mapping import (
    run_support_coverage_gap_source_mapping,
)


def _write_inputs(root: Path) -> tuple[Path, Path, Path]:
    rescore_dir = root / "rescore"
    residual_dir = root / "residual"
    support_dir = root / "support"
    rescore_dir.mkdir()
    residual_dir.mkdir()
    support_dir.mkdir()
    write_csv_rows(
        rescore_dir / "residual_rescore_rows.csv",
        [
            {"scenario_spec_id": "r2_cov", "rescore_route_label": "support_policy_coverage_gap"},
            {"scenario_spec_id": "r3_cov", "rescore_route_label": "support_policy_coverage_gap"},
            {"scenario_spec_id": "r5_cov", "rescore_route_label": "support_policy_coverage_gap"},
            {"scenario_spec_id": "r2_redesign", "rescore_route_label": "scenario_or_support_redesign_gap"},
        ],
    )
    residual_rows = [
        {
            "scenario_spec_id": "r2_cov",
            "scenario_family_id": "R2",
            "role_family": "R2_handling_limit_drift_capable_avoidance",
            "sampled_obstacle_label": "drift_required",
            "same_scene_group_id": "r2_cov",
            "hidden_dynamics_bucket": "low_mu",
            "obstacle_longitudinal_timing_bucket": "early_far",
            "obstacle_lateral_offset_bucket": "centerline",
            "initial_speed_mps": 14.0,
            "track_radius_m": 80.0,
            "track_width_m": 6.5,
            "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
            "support_label": "support_mixed",
            "dominant_failure_mode": "collision_dominated_failure",
            "aeb_success_count": 0,
            "aeb_collision_count": 5,
            "aeb_offtrack_count": 0,
            "aes_success_count": 1,
            "aes_collision_count": 3,
            "aes_offtrack_count": 1,
            "envelope_aes_success_count": 0,
            "envelope_aes_collision_count": 2,
            "envelope_aes_offtrack_count": 3,
        },
        {
            "scenario_spec_id": "r3_cov",
            "scenario_family_id": "R3",
            "role_family": "R3_recovery_after_limit",
            "sampled_obstacle_label": "recovery_required",
            "same_scene_group_id": "r3_cov",
            "hidden_dynamics_bucket": "brake_weak",
            "obstacle_longitudinal_timing_bucket": "mid",
            "obstacle_lateral_offset_bucket": "left_offset",
            "initial_speed_mps": 16.0,
            "track_radius_m": 70.0,
            "track_width_m": 6.5,
            "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
            "support_label": "support_mixed",
            "dominant_failure_mode": "offtrack_dominated_failure",
            "aeb_success_count": 0,
            "aeb_collision_count": 2,
            "aeb_offtrack_count": 3,
            "aes_success_count": 0,
            "aes_collision_count": 1,
            "aes_offtrack_count": 4,
            "envelope_aes_success_count": 1,
            "envelope_aes_collision_count": 0,
            "envelope_aes_offtrack_count": 4,
        },
        {
            "scenario_spec_id": "r5_cov",
            "scenario_family_id": "R5",
            "role_family": "R5_hidden_dynamics_robustness",
            "sampled_obstacle_label": "hidden_dynamics_required",
            "same_scene_group_id": "r5_cov",
            "hidden_dynamics_bucket": "slow_actuator",
            "obstacle_longitudinal_timing_bucket": "late_close",
            "obstacle_lateral_offset_bucket": "centerline",
            "initial_speed_mps": 15.0,
            "track_radius_m": 90.0,
            "track_width_m": 6.5,
            "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
            "support_label": "support_mixed",
            "dominant_failure_mode": "collision_dominated_failure",
            "aeb_success_count": 1,
            "aeb_collision_count": 4,
            "aeb_offtrack_count": 0,
            "aes_success_count": 0,
            "aes_collision_count": 3,
            "aes_offtrack_count": 2,
            "envelope_aes_success_count": 0,
            "envelope_aes_collision_count": 4,
            "envelope_aes_offtrack_count": 1,
        },
    ]
    write_csv_rows(residual_dir / "residual_scenario_rows.csv", residual_rows)
    write_csv_rows(
        support_dir / "scenario_support_labels.csv",
        [
            {**row, "best_support_success_count": 1, "best_support_policy_name": "aes"}
            for row in residual_rows
        ],
    )
    episode_rows = []
    for scenario in ("r2_cov", "r3_cov", "r5_cov"):
        for policy in ("aeb", "aes", "envelope_aes"):
            for repeat in range(2):
                episode_rows.append(
                    {
                        "scenario_spec_id": scenario,
                        "support_policy_name": policy,
                        "success": policy == "aes" and repeat == 0,
                        "collision": policy == "aeb",
                        "offtrack": policy == "envelope_aes",
                        "truncated": False,
                        "outcome_bucket": (
                            "success_obstacle_pass"
                            if policy == "aes" and repeat == 0
                            else "collision_failure"
                            if policy == "aeb"
                            else "off_track_noncollision_noncompletion"
                        ),
                    }
                )
    write_csv_rows(support_dir / "episode_rows.csv", episode_rows)
    return rescore_dir, residual_dir, support_dir


def test_support_coverage_gap_source_mapping_materializes_artifact_only_outputs(tmp_path: Path) -> None:
    rescore_dir, residual_dir, support_dir = _write_inputs(tmp_path)
    output_dir = tmp_path / "out"

    summary = run_support_coverage_gap_source_mapping(
        rescore_dir=rescore_dir,
        residual_dir=residual_dir,
        support_dir=support_dir,
        output_dir=output_dir,
        target_coverage_gap_row_count=3,
    )

    assert summary["result_class"] == "current_sim_support_coverage_gap_source_mapping_pass"
    assert summary["coverage_gap_row_count"] == 3
    assert summary["support_policy_coverage_materialization_candidate_count"] == 3
    assert summary["unclassified_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["support_policy_ranking_claim_made"] is False

    persisted = read_json(output_dir / "summary.json")
    assert persisted["coverage_gap_row_count"] == 3

    source_rows = (output_dir / "coverage_gap_source_rows.csv").read_text(encoding="utf-8")
    assert "support_policy_coverage_materialization_candidate" in source_rows
    assert "best_support_policy_name_metadata_only" in source_rows

    route_summary = (output_dir / "coverage_gap_recommended_route_summary.csv").read_text(encoding="utf-8")
    assert "support_policy_coverage_materialization_candidate,3" in route_summary

    claims = (output_dir / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "support_policy_ranking,False,False" in claims


def test_support_coverage_gap_source_mapping_routes_mixed_failures_to_coverage(tmp_path: Path) -> None:
    rescore_dir, residual_dir, support_dir = _write_inputs(tmp_path)
    output_dir = tmp_path / "out"

    rows = [
        {
            "scenario_spec_id": "mixed_no_success",
            "scenario_family_id": "R2",
            "role_family": "R2_handling_limit_drift_capable_avoidance",
            "sampled_obstacle_label": "drift_required",
            "same_scene_group_id": "mixed_no_success",
            "hidden_dynamics_bucket": "low_mu",
            "obstacle_longitudinal_timing_bucket": "mid",
            "obstacle_lateral_offset_bucket": "centerline",
            "initial_speed_mps": 14.0,
            "track_radius_m": 80.0,
            "track_width_m": 6.5,
            "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
            "support_label": "support_mixed",
            "dominant_failure_mode": "collision_dominated_failure",
            "aeb_success_count": 0,
            "aeb_collision_count": 5,
            "aeb_offtrack_count": 0,
            "aes_success_count": 0,
            "aes_collision_count": 0,
            "aes_offtrack_count": 5,
            "envelope_aes_success_count": 0,
            "envelope_aes_collision_count": 0,
            "envelope_aes_offtrack_count": 5,
        }
    ]
    write_csv_rows(
        rescore_dir / "residual_rescore_rows.csv",
        [{"scenario_spec_id": "mixed_no_success", "rescore_route_label": "support_policy_coverage_gap"}],
    )
    write_csv_rows(residual_dir / "residual_scenario_rows.csv", rows)
    write_csv_rows(support_dir / "scenario_support_labels.csv", rows)
    write_csv_rows(support_dir / "episode_rows.csv", [])

    summary = run_support_coverage_gap_source_mapping(
        rescore_dir=rescore_dir,
        residual_dir=residual_dir,
        support_dir=support_dir,
        output_dir=output_dir,
        target_coverage_gap_row_count=1,
    )

    assert summary["result_class"] == "current_sim_support_coverage_gap_source_mapping_pass"
    assert summary["support_policy_coverage_materialization_candidate_count"] == 1
    assert summary["scenario_or_support_redesign_candidate_count"] == 0
