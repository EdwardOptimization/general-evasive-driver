import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_failure_step_action_influence_trace_materialization_preflight as m3115


def test_residual_trace_plan_preserves_m3108_identity_and_filters_m3112_failures():
    source = {
        "m3108_residual_rows": [
            {
                "residual_failure_id": "m3108-residual-failure-0001",
                "measurement_episode_id": "m3105-measurement-episode-0007",
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "termination_reason": "obstacle_collision",
                "outcome_bucket": "collision_failure",
            },
            {
                "residual_failure_id": "m3108-residual-failure-0002",
                "measurement_episode_id": "m3105-measurement-episode-0013",
                "source_measurement_episode_id": "m3084-measurement-episode-0013",
                "termination_reason": "off_track",
                "outcome_bucket": "off_track_noncollision_noncompletion",
            },
        ],
        "m3112_measurement_rows": [
            {
                "runtime_smoke_episode_id": "m3112-measurement-episode-0007",
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "fresh_panel_row_id": "m3082-fresh-panel-0007",
                "axis_id": "collision_lateral_intrusion",
                "binding_role": "candidate",
                "task_family": "T5",
                "executable_workload_id": "m3012-executable-workload-0003",
                "executable_source_spec_id": "m3012-executable-source-spec-0002",
                "task_source_id": "m3006-src-0001",
                "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
                "eval_seed": "401530",
                "success": "False",
                "collision": "True",
                "termination_reason": "obstacle_collision",
                "outcome_bucket": "collision_failure",
            },
            {
                "runtime_smoke_episode_id": "m3112-measurement-episode-0013",
                "source_measurement_episode_id": "m3084-measurement-episode-0013",
                "fresh_panel_row_id": "m3082-fresh-panel-0013",
                "axis_id": "collision_lateral_intrusion",
                "binding_role": "candidate",
                "task_family": "T5",
                "executable_workload_id": "m3012-executable-workload-0004",
                "executable_source_spec_id": "m3012-executable-source-spec-0002",
                "task_source_id": "m3006-src-0001",
                "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
                "eval_seed": "401560",
                "success": "False",
                "collision": "False",
                "termination_reason": "off_track",
                "outcome_bucket": "off_track_noncollision_noncompletion",
            },
        ],
        "m3012_workload_rows": [
            {
                "executable_workload_id": "m3012-executable-workload-0003",
                "config_path": "runs/profile-a/config.json",
            },
            {
                "executable_workload_id": "m3012-executable-workload-0004",
                "config_path": "runs/profile-b/config.json",
            },
        ],
    }

    rows = m3115.residual_trace_plan(source)

    assert [row["trace_episode_id"] for row in rows] == [
        "m3115-residual-trace-episode-0001",
        "m3115-residual-trace-episode-0002",
    ]
    assert [row["source_measurement_episode_id"] for row in rows] == [
        "m3084-measurement-episode-0007",
        "m3084-measurement-episode-0013",
    ]
    assert rows[0]["measurement_episode_id"] == "m3112-measurement-episode-0007"
    assert rows[1]["source_residual_measurement_episode_id"] == "m3105-measurement-episode-0013"
    assert all(row["status_pass"] is True for row in rows)
    assert all(row["claim_boundary"] == m3115.CLAIM_SCOPE for row in rows)


def test_actor_visible_diagnostic_features_are_finite_and_contract_safe():
    obs = np.zeros(m3115.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.75
    obs[44] = 1.0
    obs[45] = 0.20
    obs[46] = -0.05
    obs[49] = 0.25

    features = m3115.actor_visible_diagnostic_features(obs)

    assert features["vx_body_mps_actor_visible"] == 15.0
    assert features["visible_obstacle_slot_count"] == 1
    assert features["nearest_obstacle_x_m_actor_visible"] == 16.0
    assert features["nearest_obstacle_y_m_actor_visible"] == -1.0
    assert 0.0 <= features["obstacle_urgency_actor_visible"] <= 1.0
    assert 0.0 <= features["edge_urgency_actor_visible"] <= 1.0
    assert np.isfinite(features["road_center_error_actor_visible"])


def test_influence_row_from_trace_keeps_diagnostic_boundary():
    plan = {
        "trace_episode_id": "m3115-residual-trace-episode-0001",
        "residual_failure_id": "m3108-residual-failure-0001",
        "measurement_episode_id": "m3112-measurement-episode-0007",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fresh_panel_row_id": "m3082-fresh-panel-0007",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "executable_workload_id": "m3012-executable-workload-0003",
        "executable_source_spec_id": "m3012-executable-source-spec-0002",
        "task_source_id": "m3006-src-0001",
        "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
        "eval_seed": "401530",
    }
    step = {
        **plan,
        "step_index": 12,
        "termination_reason_after_step": "obstacle_collision",
        "outcome_bucket_after_step": "collision_failure",
        "collision_after_step": True,
        "offtrack_after_step": False,
        "success_after_step": False,
        "speed_mps_after_step": 16.0,
        "beta_after_step": 0.1,
        "lateral_error_m_after_step": 0.4,
        "min_clearance_margin_m_after_step": -0.1,
        "steer_action": 0.2,
        "throttle_action": -0.1,
        "brake_physical": 0.3,
        "action_abs_max": 0.3,
        "obstacle_urgency_actor_visible": 0.8,
        "edge_urgency_actor_visible": 0.0,
        "road_center_error_actor_visible": 0.1,
        "min_actor_edge_margin_m": 2.0,
        "visible_obstacle_slot_count": 1,
        "nearest_obstacle_x_m_actor_visible": 3.0,
        "nearest_obstacle_y_m_actor_visible": -0.5,
        "high_sideslip_after_step": False,
    }

    row = m3115.influence_row_from_trace(plan=plan, step_rows=[step])

    assert row["terminal_collision"] is True
    assert row["terminal_offtrack"] is False
    assert row["primary_diagnostic_label"] == "collision_brake_response_insufficient_under_visible_obstacle_urgency"
    assert row["repair_success_claim_made"] is False
    assert row["validation_run"] is False
    assert row["driver_performance_claim_made"] is False
    assert row["claim_boundary"] == m3115.CLAIM_SCOPE


def test_claim_boundary_blocks_repair_success_and_requires_m3116_audit():
    rows = m3115.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3115-follow_up_result_audit_registered"]["allowed_in_m3115"] is True
    assert by_id["m3115-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3115-repair_success"]["allowed_in_m3115"] is False
    assert by_id["m3115-repair_success"]["claim_made"] is False
    assert by_id["m3115-repair_materialization"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3115.build_follow_up_manifest(
        output_dir=tmp_path / "m3115",
        doc_path=tmp_path / "m3115.md",
    )

    assert manifest["id"] == m3115.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_failure_step_action_influence_trace_result_audit_doc",
            "command": "true",
        }
    ]
    assert "repair-success" in manifest["hypothesis"]
    assert "validation" in manifest["forbidden_shortcuts"][1]
