import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_trajectory_authority_stability_recovery_repair_materialization_preflight as m3118


def test_m3118_direct_action_preserves_obs72_action3_contract():
    action = m3118.residual_trajectory_authority_stability_recovery_direct_action(
        np.zeros(m3118.P0_OBSERVATION_DIM, dtype=np.float32),
        m3118.M3118_POLICY_CONFIG,
    )

    assert action.shape == (m3118.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert m3118.M3118_POLICY_CONFIG["runtime_base_policy_required"] is False
    assert m3118.M3118_POLICY_CONFIG["checkpoint_model_required"] is False
    assert m3118.M3118_POLICY_CONFIG["recurrent_hidden_state_required"] is False
    assert m3118.M3118_POLICY_CONFIG["output_components"] == ["steer", "throttle", "brake"]


def test_early_obstacle_probe_changes_action_without_hidden_inputs():
    obs = np.zeros(m3118.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.90
    obs[44] = 1.0
    obs[45] = 0.20
    obs[46] = -0.05
    obs[49] = 0.20

    action = m3118.residual_trajectory_authority_stability_recovery_direct_action(obs, m3118.M3118_POLICY_CONFIG)
    features = m3118._early_obstacle_features(obs, m3118.M3118_POLICY_CONFIG)

    assert features["early_obstacle_risk"] > 0.0
    assert features["early_obstacle_avoid_direction"] == 1.0
    assert action.shape == (m3118.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0


def test_residual_trace_requirement_rows_map_labels_to_rule_families():
    rows = m3118.residual_trace_requirement_rows(
        [
            {
                "trace_episode_id": "m3115-residual-trace-episode-0001",
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "axis_id": "collision_lateral_intrusion",
                "terminal_termination_reason": "obstacle_collision",
                "primary_diagnostic_label": "collision_action_present_but_clearance_unresolved",
                "trace_step_count": "29",
                "max_obstacle_urgency_actor_visible": "0.64",
                "max_edge_urgency_actor_visible": "0.85",
                "final_10_mean_brake_physical": "0.56",
                "final_10_mean_abs_steer": "0.72",
                "action_saturation_fraction": "0.10",
            },
            {
                "trace_episode_id": "m3115-residual-trace-episode-0003",
                "source_measurement_episode_id": "m3084-measurement-episode-0013",
                "axis_id": "collision_lateral_intrusion",
                "terminal_termination_reason": "off_track",
                "primary_diagnostic_label": "offtrack_stability_recovery_limited",
                "trace_step_count": "52",
                "max_obstacle_urgency_actor_visible": "0.20",
                "max_edge_urgency_actor_visible": "0.99",
                "final_10_mean_brake_physical": "0.22",
                "final_10_mean_abs_steer": "0.70",
                "action_saturation_fraction": "0.0",
            },
        ]
    )

    assert rows[0]["required_rule_families"] == (
        "early_obstacle_corridor_commitment;brake_throttle_timing;speed_floor_preservation"
    )
    assert rows[1]["required_rule_families"] == (
        "stability_biased_steering_allocation;speed_floor_preservation"
    )
    assert all(row["preserves_speed_floor"] is True for row in rows)
    assert all(row["runtime_base_policy_required"] is False for row in rows)
    assert all(row["hidden_oracle_actor_input_required"] is False for row in rows)
    assert all(row["status_pass"] is True for row in rows)


def test_claim_boundary_blocks_measurement_and_repair_success():
    rows = m3118.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3118-follow_up_result_audit_registered"]["allowed_in_m3118"] is True
    assert by_id["m3118-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3118-measurement_result"]["allowed_in_m3118"] is False
    assert by_id["m3118-measurement_result"]["claim_made"] is False
    assert by_id["m3118-repair_success"]["claim_made"] is False
    assert by_id["m3118-driver_performance_verdict"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_m3119_audit_not_measurement(tmp_path):
    manifest = m3118.build_follow_up_manifest(
        output_dir=tmp_path / "m3118",
        doc_path=tmp_path / "m3118.md",
    )

    assert manifest["id"] == m3118.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_trajectory_authority_stability_recovery_repair_result_audit_doc",
            "command": "true",
        }
    ]
    assert "repair-success" in manifest["hypothesis"]
    assert "validation" in manifest["forbidden_shortcuts"][1]
