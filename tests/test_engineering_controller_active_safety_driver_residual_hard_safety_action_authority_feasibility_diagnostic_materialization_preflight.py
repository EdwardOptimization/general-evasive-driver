import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_action_authority_feasibility_diagnostic_materialization_preflight as m3123


def _episode(source_id: str, *, termination: str, collision: bool, high_sideslip: str = "0.0"):
    return {
        "runtime_smoke_episode_id": f"m3120-{source_id}",
        "source_measurement_episode_id": source_id,
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "success": False,
        "collision": collision,
        "termination_reason": termination,
        "min_clearance_margin": "-0.2" if collision else "2.0",
        "speed_mean": "16.0",
        "high_sideslip_fraction": high_sideslip,
        "lateral_rmse": "1.2",
        "raw_action_abs_max": "1.0",
        "final_action_abs_max": "1.0",
    }


def _comparison(source_id: str, baseline_id: str):
    return {
        "source_measurement_episode_id": source_id,
        "baseline_id": baseline_id,
        "success_delta": 0,
        "collision_delta": 0,
        "offtrack_delta": 0,
        "speed_too_low_delta": 0,
    }


def _influence(source_id: str, label: str = "collision_action_present_but_clearance_unresolved"):
    return {
        "source_measurement_episode_id": source_id,
        "trace_step_count": "29",
        "primary_diagnostic_label": label,
        "terminal_speed_mps": "17.0",
        "terminal_beta_abs": "0.3",
        "terminal_lateral_error_m": "1.4",
        "terminal_min_clearance_margin_m": "-0.1",
        "final_10_mean_brake_physical": "0.8",
        "final_10_mean_abs_steer": "0.9",
        "action_saturation_fraction": "0.2",
        "max_obstacle_urgency_actor_visible": "0.7",
        "step_of_max_obstacle_urgency": "29",
        "max_edge_urgency_actor_visible": "0.9",
        "step_of_max_edge_urgency": "29",
        "terminal_obstacle_x_m_actor_visible": "1.0",
        "terminal_obstacle_y_m_actor_visible": "-2.0",
    }


def test_classify_collision_as_authority_saturated_clearance_unresolved():
    episode = _episode("src-1", termination="obstacle_collision", collision=True)
    authority, feasibility, interpretation, next_evidence = m3123.classify_authority_feasibility(
        episode,
        _influence("src-1"),
    )

    assert authority == "collision_action_authority_saturated_clearance_unresolved"
    assert feasibility == "clearance_or_timing_feasibility_unresolved_under_direct_action"
    assert "high direct-action authority" in interpretation
    assert "feasibility" in next_evidence


def test_residual_action_authority_rows_preserve_identity_and_plateau_flags():
    episodes = [_episode("src-1", termination="obstacle_collision", collision=True)]
    comparisons = [_comparison("src-1", baseline) for baseline in ("m3105", "m3095", "m3100", "m3090")]
    rows = m3123.residual_action_authority_feasibility_rows(episodes, comparisons, [_influence("src-1")])

    assert len(rows) == 1
    assert rows[0]["source_measurement_episode_id"] == "src-1"
    assert rows[0]["same_row_baseline_count"] == 4
    assert rows[0]["same_row_baselines"] == "m3090;m3095;m3100;m3105"
    assert rows[0]["plateau_vs_m3105"] is True
    assert rows[0]["plateau_vs_m3095"] is True
    assert rows[0]["row_identity_preserved"] is True
    assert rows[0]["m3123_no_new_execution"] is True
    assert rows[0]["repair_success_claim_made"] is False


def test_claim_boundary_blocks_repair_success_and_requires_m3124():
    rows = m3123.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3123-follow_up_result_audit_registered"]["allowed_in_m3123"] is True
    assert by_id["m3123-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3123-repair_success"]["allowed_in_m3123"] is False
    assert by_id["m3123-repair_success"]["claim_made"] is False
    assert by_id["m3123-repair_materialization"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_audit_not_validation(tmp_path):
    manifest = m3123.build_follow_up_manifest(
        output_dir=tmp_path / "m3123",
        doc_path=tmp_path / "m3123.md",
    )

    assert manifest["id"] == m3123.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_action_authority_feasibility_diagnostic_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
