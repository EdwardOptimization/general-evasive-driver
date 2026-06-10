import autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight as m3108


def _episode(source_id: str, success: bool, axis: str, termination: str, collision: bool = False):
    return {
        "runtime_smoke_episode_id": f"m3105-{source_id}",
        "source_measurement_episode_id": source_id,
        "fresh_panel_row_id": "fresh-1",
        "axis_id": axis,
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "success": success,
        "collision": collision,
        "termination_reason": termination,
        "outcome_bucket": termination or "success_obstacle_pass",
        "min_clearance_margin": "-0.1" if collision else "4.0",
        "return": "1.0",
        "speed_mean": "10.0",
        "lateral_rmse": "0.5",
        "high_sideslip_fraction": "0.0",
        "action_rate_mean": "0.1",
        "raw_action_abs_max": "1.0",
        "final_action_abs_max": "1.0",
        "recoverability_window_success_available": "False",
        "recoverability_window_success": "False",
    }


def _comparison(source_id: str, baseline_id: str, termination: str):
    return {
        "comparison_id": f"cmp-{source_id}-{baseline_id}",
        "measurement_episode_id": f"m3105-{source_id}",
        "baseline_id": baseline_id,
        "baseline_episode_id": f"{baseline_id}-{source_id}",
        "source_measurement_episode_id": source_id,
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "m3105_policy": "v4",
        "baseline_policy": baseline_id,
        "m3105_success": False,
        "baseline_success": False,
        "success_delta": 0,
        "m3105_collision": termination == "obstacle_collision",
        "baseline_collision": termination == "obstacle_collision",
        "collision_delta": 0,
        "m3105_offtrack": termination == "off_track",
        "baseline_offtrack": termination == "off_track",
        "offtrack_delta": 0,
        "m3105_speed_too_low": False,
        "baseline_speed_too_low": False,
        "speed_too_low_delta": 0,
        "m3105_termination_reason": termination,
        "baseline_termination_reason": termination,
        "termination_reason_match": True,
        "m3105_outcome_bucket": termination,
        "baseline_outcome_bucket": termination,
        "outcome_bucket_match": True,
        "m3105_min_clearance_margin": "-0.1",
        "baseline_min_clearance_margin": "-0.1",
        "clearance_margin_delta": 0.0,
        "m3105_return": "1.0",
        "baseline_return": "1.0",
        "return_delta": 0.0,
        "m3105_speed_mean": "10.0",
        "baseline_speed_mean": "10.0",
        "speed_mean_delta": 0.0,
        "m3105_action_rate_mean": "0.1",
        "baseline_action_rate_mean": "0.1",
        "action_rate_delta": 0.0,
        "exact_seed_match_m3095": baseline_id == "m3095",
        "exact_seed_match_m3100": baseline_id == "m3100",
        "exact_seed_match_m3090": baseline_id == "m3090",
        "comparison_claim_made": False,
        "repair_success_claim_made": False,
        "validation_run": False,
        "driver_performance_claim_made": False,
        "claim_boundary": "source",
    }


def test_residual_failure_rows_preserve_non_success_rows_and_baselines():
    episodes = [
        _episode("src-1", True, "speed_floor_stress", ""),
        _episode("src-2", False, "collision_lateral_intrusion", "obstacle_collision", collision=True),
    ]
    comparisons = [_comparison("src-2", baseline, "obstacle_collision") for baseline in ("m3095", "m3100", "m3090")]

    rows = m3108.residual_failure_rows(episodes, comparisons)

    assert len(rows) == 1
    assert rows[0]["source_measurement_episode_id"] == "src-2"
    assert rows[0]["collision"] is True
    assert rows[0]["same_row_baseline_count"] == 3
    assert rows[0]["same_row_baselines"] == "m3090;m3095;m3100"
    assert rows[0]["m3108_no_new_execution"] is True
    assert rows[0]["repair_success_claim_made"] is False


def test_axis_summary_and_repair_requirements_keep_collision_offtrack_separate():
    residual = [
        _episode("src-2", False, "collision_lateral_intrusion", "obstacle_collision", collision=True),
        _episode("src-3", False, "offtrack_boundary_recovery", "off_track"),
    ]
    residual[0]["measurement_episode_id"] = "m3105-src-2"
    residual[1]["measurement_episode_id"] = "m3105-src-3"
    residual[0]["residual_failure_id"] = "r1"
    residual[1]["residual_failure_id"] = "r2"
    residual[0]["offtrack"] = False
    residual[0]["speed_too_low"] = False
    residual[1]["collision"] = False
    residual[1]["offtrack"] = True
    residual[1]["speed_too_low"] = False

    axis_rows = m3108.residual_axis_summary_rows(residual)
    requirements = m3108.build_repair_requirement_rows(residual, axis_rows)
    by_requirement = {row["requirement_family"]: row for row in requirements}

    assert any(row["group_key"] == "axis_id" and row["group_value"] == "collision_lateral_intrusion" for row in axis_rows)
    assert any(row["group_key"] == "axis_id" and row["group_value"] == "offtrack_boundary_recovery" for row in axis_rows)
    assert by_requirement["collision_lateral_intrusion_guard"]["priority"] == "p0"
    assert by_requirement["offtrack_boundary_recovery_guard"]["priority"] == "p0"
    assert by_requirement["speed_floor_preservation"]["row_count"] == 0


def test_claim_boundary_blocks_repair_success_and_requires_m3109():
    rows = m3108.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3108-follow_up_result_audit_registered"]["allowed_in_m3108"] is True
    assert by_id["m3108-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3108-repair_success"]["allowed_in_m3108"] is False
    assert by_id["m3108-repair_success"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_audit_not_validation(tmp_path):
    manifest = m3108.build_follow_up_manifest(
        output_dir=tmp_path / "m3108",
        doc_path=tmp_path / "m3108.md",
    )

    assert manifest["id"] == m3108.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_collision_offtrack_decomposition_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
