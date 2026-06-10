import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_counterfactual_action_authority_envelope_diagnostic_materialization_preflight as m3125


def _m3123_row(source_id: str, *, collision: bool = True, offtrack: bool = False):
    return {
        "diagnostic_id": "m3123-action-authority-feasibility-0001",
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
        "authority_label": (
            "collision_action_authority_saturated_clearance_unresolved"
            if collision
            else "offtrack_stability_edge_authority_limited"
        ),
        "feasibility_label": (
            "clearance_or_timing_feasibility_unresolved_under_direct_action"
            if collision
            else "boundary_recovery_feasibility_unresolved_under_sideslip"
        ),
        "primary_diagnostic_label": (
            "collision_action_present_but_clearance_unresolved"
            if collision
            else "offtrack_stability_recovery_limited"
        ),
        "trace_step_count": "20",
        "terminal_speed_mps": "16.0",
        "terminal_beta_abs": "0.3",
        "terminal_lateral_error_m": "1.4",
        "terminal_min_clearance_margin_m": "-0.1" if collision else "0.1",
        "high_sideslip_fraction": "0.0" if collision else "0.5",
        "final_10_mean_brake_physical": "0.92" if collision else "0.22",
        "final_10_mean_abs_steer": "0.95" if collision else "0.75",
        "action_saturation_fraction": "0.35" if collision else "0.0",
        "max_obstacle_urgency_actor_visible": "0.7",
        "max_edge_urgency_actor_visible": "0.99",
        "terminal_obstacle_x_m_actor_visible": "1.0",
        "terminal_obstacle_y_m_actor_visible": "-2.0",
    }


def _influence(source_id: str, *, final_throttle: str = "-0.7"):
    return {
        "trace_episode_id": "m3115-residual-trace-episode-0001",
        "source_measurement_episode_id": source_id,
        "trace_step_count": "20",
        "primary_diagnostic_label": "collision_action_present_but_clearance_unresolved",
        "terminal_speed_mps": "16.0",
        "terminal_beta_abs": "0.3",
        "terminal_lateral_error_m": "1.4",
        "terminal_min_clearance_margin_m": "-0.1",
        "final_10_mean_throttle_action": final_throttle,
        "final_10_mean_brake_physical": "0.92",
        "final_10_mean_abs_steer": "0.95",
        "action_saturation_fraction": "0.35",
        "max_obstacle_urgency_actor_visible": "0.7",
        "max_edge_urgency_actor_visible": "0.99",
        "terminal_obstacle_x_m_actor_visible": "1.0",
        "terminal_obstacle_y_m_actor_visible": "-2.0",
    }


def _step(source_id: str, index: int):
    return {
        "source_measurement_episode_id": source_id,
        "step_index": str(index),
        "steer_action": "0.9",
        "throttle_action": "-0.8",
        "brake_physical": "0.95",
    }


def test_collision_envelope_exhausted_without_repair_success_claim():
    status, route, interpretation = m3125.classify_envelope(_m3123_row("src-1"), _influence("src-1"))

    assert status == "joint_brake_steer_envelope_exhausted_clearance_unresolved"
    assert "trajectory_level" in route
    assert "not repair success" in interpretation


def test_counterfactual_rows_preserve_identity_and_materialize_margins():
    rows = m3125.counterfactual_action_authority_envelope_rows(
        [_m3123_row("src-1")],
        [_influence("src-1")],
        [_step("src-1", index) for index in range(1, 21)],
    )

    assert len(rows) == 1
    assert rows[0]["source_measurement_episode_id"] == "src-1"
    assert rows[0]["row_identity_preserved"] is True
    assert rows[0]["m3125_no_new_execution"] is True
    assert rows[0]["repair_success_claim_made"] is False
    assert rows[0]["final_10_brake_margin_to_full"] == 0.07999999999999996
    assert rows[0]["final_10_steer_margin_to_saturation"] == 0.050000000000000044
    assert rows[0]["negative_throttle_margin_to_full_decel"] == 0.30000000000000004
    assert rows[0]["throttle_deceleration_tradeoff_label"] == (
        "negative_throttle_and_physical_brake_near_full_under_speed_floor_preservation"
    )


def test_offtrack_row_routes_to_stability_timing_diagnostic():
    rows = m3125.counterfactual_action_authority_envelope_rows(
        [_m3123_row("src-2", collision=False, offtrack=True)],
        [_influence("src-2", final_throttle="-0.2")],
        [_step("src-2", index) for index in range(1, 21)],
    )

    assert rows[0]["envelope_status"] == "stability_recovery_envelope_timing_limited"
    assert rows[0]["route_recommendation"] == "stability_recovery_timing_or_trajectory_level_controller_diagnostic"


def test_claim_boundary_blocks_repair_success_and_requires_m3126():
    rows = m3125.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3125-follow_up_result_audit_registered"]["allowed_in_m3125"] is True
    assert by_id["m3125-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3125-repair_success"]["allowed_in_m3125"] is False
    assert by_id["m3125-repair_success"]["claim_made"] is False
    assert by_id["m3125-feasibility_or_infeasibility_proof"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_audit_not_validation(tmp_path):
    manifest = m3125.build_follow_up_manifest(
        output_dir=tmp_path / "m3125",
        doc_path=tmp_path / "m3125.md",
    )

    assert manifest["id"] == m3125.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_counterfactual_action_authority_envelope_diagnostic_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
