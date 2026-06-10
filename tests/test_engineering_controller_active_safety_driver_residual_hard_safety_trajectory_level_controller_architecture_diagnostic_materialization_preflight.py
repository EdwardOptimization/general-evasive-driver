import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_controller_architecture_diagnostic_materialization_preflight as m3127


def _envelope(source_id: str, *, collision: bool = True, offtrack: bool = False):
    return {
        "envelope_id": "m3125-counterfactual-action-authority-envelope-0001",
        "trace_episode_id": "m3115-residual-trace-episode-0001",
        "measurement_episode_id": "m3120-measurement-episode-0001",
        "source_measurement_episode_id": source_id,
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "collision_lateral_intrusion" if collision else "offtrack_boundary_recovery",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "termination_reason": "obstacle_collision" if collision else "off_track",
        "collision": collision,
        "offtrack": offtrack,
        "speed_too_low": False,
        "envelope_status": (
            "joint_brake_steer_envelope_exhausted_clearance_unresolved"
            if collision
            else "stability_steer_envelope_near_exhausted"
        ),
        "route_recommendation": "trajectory_level_controller_architecture_or_feasibility_diagnostic_before_more_direct_gain",
        "terminal_speed_mps": "16.0",
        "terminal_beta_abs": "0.3",
        "terminal_lateral_error_m": "1.4",
        "terminal_min_clearance_margin_m": "-0.1" if collision else "0.1",
        "high_sideslip_fraction": "0.0" if collision else "0.5",
        "final_10_mean_throttle_action": "-0.7",
        "final_10_mean_brake_physical": "0.92",
        "final_10_brake_margin_to_full": "0.08",
        "final_10_mean_abs_steer": "0.95",
        "final_10_steer_margin_to_saturation": "0.05",
        "action_saturation_fraction": "0.35",
        "max_obstacle_urgency_actor_visible": "0.7",
        "max_edge_urgency_actor_visible": "0.99",
        "terminal_obstacle_x_m_actor_visible": "1.0",
        "terminal_obstacle_y_m_actor_visible": "-2.0",
    }


def _influence(source_id: str):
    return {
        "trace_episode_id": "m3115-residual-trace-episode-0001",
        "source_measurement_episode_id": source_id,
        "terminal_speed_mps": "16.0",
        "terminal_beta_abs": "0.3",
        "terminal_lateral_error_m": "1.4",
        "terminal_min_clearance_margin_m": "-0.1",
        "high_sideslip_fraction": "0.5",
        "final_10_mean_throttle_action": "-0.7",
        "final_10_mean_brake_physical": "0.92",
        "final_10_mean_abs_steer": "0.95",
        "action_saturation_fraction": "0.35",
        "max_obstacle_urgency_actor_visible": "0.7",
        "max_edge_urgency_actor_visible": "0.99",
        "max_abs_road_center_error_actor_visible": "1.0",
        "min_actor_edge_margin_m_min": "0.1",
        "visible_obstacle_fraction": "0.5",
    }


def test_collision_exhausted_routes_to_clearance_corridor_architecture():
    family, mode, contract, primary, secondary, interpretation = m3127.classify_architecture_candidate(
        _envelope("src-1")
    )

    assert family == "actor_visible_receding_horizon_clearance_corridor_reflex"
    assert mode == "short_horizon_clearance_timing_and_lateral_offset_scheduler"
    assert contract == "obs72_current_frame_geometry_to_direct_action3_no_runtime_base_policy"
    assert primary == "collision_clearance_margin"
    assert "speed_floor" in secondary
    assert "local gain" in interpretation


def test_architecture_rows_preserve_direct_action_contract_and_claim_boundary():
    rows = m3127.architecture_candidate_rows([_envelope("src-1")], [_influence("src-1")])

    assert len(rows) == 1
    assert rows[0]["source_measurement_episode_id"] == "src-1"
    assert rows[0]["row_identity_preserved"] is True
    assert rows[0]["candidate_output_components"] == "steer;throttle;brake"
    assert rows[0]["runtime_base_policy_required"] is False
    assert rows[0]["hidden_oracle_actor_input_required"] is False
    assert rows[0]["ttc_actor_input_required"] is False
    assert rows[0]["implementation_allowed_in_m3127"] is False
    assert rows[0]["measurement_allowed_in_m3127"] is False
    assert rows[0]["repair_success_claim_made"] is False


def test_offtrack_near_exhausted_routes_to_stability_corridor_architecture():
    rows = m3127.architecture_candidate_rows(
        [_envelope("src-2", collision=False, offtrack=True)],
        [_influence("src-2")],
    )

    assert rows[0]["architecture_family"] == "actor_visible_stability_corridor_recovery_reflex"
    assert rows[0]["primary_metric_target"] == "offtrack_and_recovery_stability"


def test_claim_boundary_blocks_implementation_and_requires_m3128():
    rows = m3127.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3127-follow_up_result_audit_registered"]["allowed_in_m3127"] is True
    assert by_id["m3127-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3127-controller_implementation"]["allowed_in_m3127"] is False
    assert by_id["m3127-controller_implementation"]["claim_made"] is False
    assert by_id["m3127-repair_success"]["claim_made"] is False
    assert by_id["m3127-feasibility_or_infeasibility_proof"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_audit_not_validation(tmp_path):
    manifest = m3127.build_follow_up_manifest(
        output_dir=tmp_path / "m3127",
        doc_path=tmp_path / "m3127.md",
    )

    assert manifest["id"] == m3127.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_trajectory_level_controller_architecture_diagnostic_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
