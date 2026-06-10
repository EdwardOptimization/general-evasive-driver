import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_action_delta_coverage_diagnostic_materialization_preflight as m3147


def test_residual_action_delta_plan_filters_m3144_failures_and_preserves_m3105_comparison():
    source = {
        "m3144_measurement_rows": [
            {
                "runtime_smoke_episode_id": "m3144-measurement-episode-0001",
                "source_measurement_episode_id": "m3084-measurement-episode-0001",
                "success": "True",
                "collision": "False",
                "termination_reason": "",
                "executable_workload_id": "m3012-executable-workload-0001",
            },
            {
                "runtime_smoke_episode_id": "m3144-measurement-episode-0007",
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "fresh_panel_row_id": "m3082-fresh-panel-0007",
                "axis_id": "collision_lateral_intrusion",
                "binding_role": "candidate",
                "task_family": "T5",
                "executable_workload_id": "m3012-executable-workload-0015",
                "executable_source_spec_id": "m3012-executable-source-spec-0008",
                "task_source_id": "m3006-src-0007",
                "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
                "eval_seed": "401530",
                "success": "False",
                "collision": "True",
                "termination_reason": "obstacle_collision",
                "outcome_bucket": "collision_failure",
            },
            {
                "runtime_smoke_episode_id": "m3144-measurement-episode-0013",
                "source_measurement_episode_id": "m3084-measurement-episode-0013",
                "fresh_panel_row_id": "m3082-fresh-panel-0013",
                "axis_id": "collision_lateral_intrusion",
                "binding_role": "candidate",
                "task_family": "T5",
                "executable_workload_id": "m3012-executable-workload-0027",
                "executable_source_spec_id": "m3012-executable-source-spec-0014",
                "task_source_id": "m3006-src-0013",
                "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
                "eval_seed": "401560",
                "success": "False",
                "collision": "False",
                "termination_reason": "off_track",
                "outcome_bucket": "off_track_noncollision_noncompletion",
            },
        ],
        "m3144_same_row_comparison_rows": [
            {
                "comparison_id": "m3144-same-row-comparison-0025",
                "baseline_id": "m3105",
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "baseline_termination_reason": "obstacle_collision",
                "baseline_outcome_bucket": "collision_failure",
                "exact_seed_match_m3105": "True",
            },
            {
                "comparison_id": "m3144-same-row-comparison-0049",
                "baseline_id": "m3105",
                "source_measurement_episode_id": "m3084-measurement-episode-0013",
                "baseline_termination_reason": "off_track",
                "baseline_outcome_bucket": "off_track_noncollision_noncompletion",
                "exact_seed_match_m3105": "True",
            },
        ],
        "m3012_workload_rows": [
            {
                "executable_workload_id": "m3012-executable-workload-0015",
                "config_path": "runs/profile-a/config.json",
            },
            {
                "executable_workload_id": "m3012-executable-workload-0027",
                "config_path": "runs/profile-b/config.json",
            },
        ],
    }

    rows = m3147.residual_action_delta_plan(source)

    assert [row["trace_episode_id"] for row in rows] == [
        "m3147-action-delta-trace-episode-0001",
        "m3147-action-delta-trace-episode-0002",
    ]
    assert [row["target_failure_kind"] for row in rows] == ["collision", "offtrack"]
    assert rows[0]["m3144_measurement_episode_id"] == "m3144-measurement-episode-0007"
    assert rows[0]["m3105_same_row_comparison_id"] == "m3144-same-row-comparison-0025"
    assert rows[1]["config_path"] == "runs/profile-b/config.json"
    assert all(row["status_pass"] is True for row in rows)
    assert all(row["claim_boundary"] == m3147.CLAIM_SCOPE for row in rows)


def test_action_delta_from_observation_is_actor_visible_bounded_and_nonzero_under_overlay():
    obs = m3147._sample_overlay_observation()

    payload = m3147.action_delta_from_observation(obs)
    fallback = payload["fallback_action"]
    candidate = payload["candidate_action"]
    delta = payload["delta"]
    features = payload["features"]

    assert fallback.shape == (m3147.ACTION_DIM,)
    assert candidate.shape == (m3147.ACTION_DIM,)
    assert np.all(np.isfinite(fallback))
    assert np.all(np.isfinite(candidate))
    assert np.max(np.abs(fallback)) <= 1.0
    assert np.max(np.abs(candidate)) <= 1.0
    assert features["overlay_alpha"] > 0.0
    assert np.max(np.abs(delta)) > 0.0
    assert delta[1] <= 1e-6
    assert delta[2] >= -1e-6


def test_coverage_row_from_trace_classifies_overlay_absence_without_overclaiming():
    plan = {
        "trace_episode_id": "m3147-action-delta-trace-episode-0001",
        "residual_failure_id": "m3147-residual-failure-0001",
        "m3144_measurement_episode_id": "m3144-measurement-episode-0007",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fresh_panel_row_id": "m3082-fresh-panel-0007",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "executable_workload_id": "m3012-executable-workload-0015",
        "executable_source_spec_id": "m3012-executable-source-spec-0008",
        "task_source_id": "m3006-src-0007",
        "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
        "eval_seed": "401530",
        "m3105_same_row_comparison_id": "m3144-same-row-comparison-0025",
        "m3105_termination_reason": "obstacle_collision",
        "m3105_outcome_bucket": "collision_failure",
        "source_m3144_termination_reason": "obstacle_collision",
        "source_m3144_outcome_bucket": "collision_failure",
        "target_failure_kind": "collision",
    }
    step = {
        **plan,
        "step_index": 29,
        "termination_reason_after_step": "obstacle_collision",
        "outcome_bucket_after_step": "collision_failure",
        "collision_after_step": True,
        "offtrack_after_step": False,
        "success_after_step": False,
        "speed_mps_after_step": 16.0,
        "min_clearance_margin_m_after_step": -0.1,
        "overlay_active": False,
        "overlay_alpha": 0.0,
        "delta_max_abs": 0.0,
        "delta_l1": 0.0,
        "delta_throttle": 0.0,
        "delta_brake": 0.0,
        "delta_steer": 0.0,
        "candidate_action_saturated": False,
        "fallback_action_saturated": False,
        "obstacle_risk_actor_visible": 0.1,
        "edge_risk_actor_visible": 0.0,
        "stability_risk_actor_visible": 0.0,
        "min_clearance_margin_m_after_step": -0.1,
    }

    row = m3147.coverage_row_from_trace(plan=plan, step_rows=[step])

    assert row["terminal_collision"] is True
    assert row["coverage_diagnostic_label"] == "overlay_never_active_on_residual_row"
    assert row["overlay_active_step_count"] == 0
    assert row["repair_success_claim_made"] is False
    assert row["validation_run"] is False
    assert row["driver_performance_claim_made"] is False
    assert row["claim_boundary"] == m3147.CLAIM_SCOPE


def test_claim_boundary_blocks_repair_success_validation_and_feasibility_proof():
    rows = m3147.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3147-follow_up_result_audit_registered"]["allowed_in_m3147"] is True
    assert by_id["m3147-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3147-repair_success"]["allowed_in_m3147"] is False
    assert by_id["m3147-validation_result"]["claim_made"] is False
    assert by_id["m3147-feasibility_proof"]["claim_made"] is False
    assert by_id["m3147-level3_self_identification"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3147.build_follow_up_manifest(output_dir=tmp_path / "m3147", doc_path=tmp_path / "m3147.md")

    assert manifest["id"] == m3147.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
    assert "repair-success" in manifest["hypothesis"]
