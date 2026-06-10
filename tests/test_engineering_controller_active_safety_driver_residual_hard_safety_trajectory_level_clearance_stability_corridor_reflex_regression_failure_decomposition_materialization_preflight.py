import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_regression_failure_decomposition_materialization_preflight as m3133


def _episode(
    source_id: str,
    *,
    success: bool,
    termination: str = "",
    collision: bool = False,
    clearance: str = "10.0",
    ret: str = "100.0",
    speed: str = "10.0",
    sideslip: str = "0.0",
    lateral: str = "0.5",
):
    return {
        "runtime_smoke_episode_id": f"row-{source_id}",
        "source_measurement_episode_id": source_id,
        "fresh_panel_row_id": f"fresh-{source_id}",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "success": success,
        "collision": collision,
        "termination_reason": termination,
        "outcome_bucket": termination or "success_obstacle_pass",
        "min_clearance_margin": clearance,
        "return": ret,
        "speed_mean": speed,
        "high_sideslip_fraction": sideslip,
        "lateral_rmse": lateral,
        "action_rate_mean": "0.2",
        "raw_action_abs_max": "1.0",
        "final_action_abs_max": "1.0",
    }


def _comparison(source_id: str, *, m_success: bool, b_success: bool, m_term: str, b_term: str, m_collision: bool = False):
    m_offtrack = m_term == "off_track"
    b_offtrack = b_term == "off_track"
    m_speed = m_term == "speed_too_low"
    b_speed = b_term == "speed_too_low"
    b_collision = b_term == "obstacle_collision"
    return {
        "source_measurement_episode_id": source_id,
        "baseline_id": "m3105",
        "m3131_success": m_success,
        "baseline_success": b_success,
        "success_delta": int(m_success) - int(b_success),
        "m3131_collision": m_collision,
        "baseline_collision": b_collision,
        "collision_delta": int(m_collision) - int(b_collision),
        "m3131_offtrack": m_offtrack,
        "baseline_offtrack": b_offtrack,
        "offtrack_delta": int(m_offtrack) - int(b_offtrack),
        "m3131_speed_too_low": m_speed,
        "baseline_speed_too_low": b_speed,
        "speed_too_low_delta": int(m_speed) - int(b_speed),
        "clearance_margin_delta": "-2.5",
        "return_delta": "-20.0",
        "speed_mean_delta": "-1.0",
        "action_rate_delta": "0.2",
        "exact_seed_match_m3105": True,
    }


def test_decomposition_classifies_added_failure_axes_against_m3105():
    m3131_rows = [
        _episode("src-off", success=False, termination="off_track", clearance="4.0", ret="50.0", lateral="1.1"),
        _episode("src-speed", success=False, termination="speed_too_low", clearance="8.0", ret="40.0", speed="2.0"),
        _episode("src-coll", success=False, termination="obstacle_collision", collision=True, clearance="-0.2", ret="30.0"),
    ]
    m3105_rows = [
        _episode("src-off", success=True, clearance="10.0", ret="80.0", lateral="0.4"),
        _episode("src-speed", success=True, clearance="10.0", ret="80.0", speed="9.0"),
        _episode("src-coll", success=True, clearance="10.0", ret="80.0"),
    ]
    comparisons = [
        _comparison("src-off", m_success=False, b_success=True, m_term="off_track", b_term=""),
        _comparison("src-speed", m_success=False, b_success=True, m_term="speed_too_low", b_term=""),
        _comparison("src-coll", m_success=False, b_success=True, m_term="obstacle_collision", b_term="", m_collision=True),
    ]

    rows = m3133.regression_failure_decomposition_rows(m3131_rows, m3105_rows, comparisons)
    by_source = {row["source_measurement_episode_id"]: row for row in rows}

    assert by_source["src-off"]["primary_regression_axis"] == "added_offtrack_regression"
    assert by_source["src-off"]["added_offtrack"] is True
    assert by_source["src-off"]["stability_regression"] is True
    assert by_source["src-speed"]["primary_regression_axis"] == "added_speed_floor_regression"
    assert by_source["src-speed"]["added_speed_too_low"] is True
    assert by_source["src-coll"]["primary_regression_axis"] == "added_collision_regression"
    assert by_source["src-coll"]["added_collision"] is True
    assert all(row["same_row_m3105_alignment_preserved"] for row in rows)
    assert all(row["m3133_no_new_execution"] for row in rows)
    assert all(row["repair_success_claim_made"] is False for row in rows)


def test_axis_summary_preserves_counts_and_guard_recommendations():
    rows = [
        {
            "measurement_episode_id": "r1",
            "primary_regression_axis": "added_offtrack_regression",
            "axis_id": "collision_lateral_intrusion",
            "binding_role": "candidate",
            "task_family": "T5",
            "m3131_termination_reason": "off_track",
            "m3131_success": False,
            "m3105_success": True,
            "success_regression": True,
            "success_improvement": False,
            "added_collision": False,
            "added_offtrack": True,
            "added_speed_too_low": False,
            "clearance_margin_regression": True,
            "return_regression": True,
            "stability_regression": True,
            "clearance_margin_delta": -3.0,
            "return_delta": -10.0,
            "speed_mean_delta": -1.0,
            "high_sideslip_fraction_delta": 0.1,
            "lateral_rmse_delta": 0.4,
            "action_rate_delta": 0.2,
            "recommended_next_guard": "edge_stability_guarded_fallback_or_hybrid_before_standalone_corridor",
        },
        {
            "measurement_episode_id": "r2",
            "primary_regression_axis": "added_speed_floor_regression",
            "axis_id": "speed_floor_stress",
            "binding_role": "parent",
            "task_family": "T4",
            "m3131_termination_reason": "speed_too_low",
            "m3131_success": False,
            "m3105_success": True,
            "success_regression": True,
            "success_improvement": False,
            "added_collision": False,
            "added_offtrack": False,
            "added_speed_too_low": True,
            "clearance_margin_regression": False,
            "return_regression": True,
            "stability_regression": False,
            "clearance_margin_delta": 0.0,
            "return_delta": -4.0,
            "speed_mean_delta": -5.0,
            "high_sideslip_fraction_delta": 0.0,
            "lateral_rmse_delta": 0.0,
            "action_rate_delta": 0.1,
            "recommended_next_guard": "speed_floor_guarded_fallback_or_hybrid_before_corridor_authority",
        },
    ]

    summaries = m3133.regression_axis_summary_rows(rows)
    all_row = next(row for row in summaries if row["group_key"] == "all")

    assert all_row["row_count"] == 2
    assert all_row["success_regression_count"] == 2
    assert all_row["added_offtrack_count"] == 1
    assert all_row["added_speed_too_low_count"] == 1
    assert all_row["dominant_primary_regression_axis"] == "added_offtrack_regression"
    assert "edge_stability_guarded_fallback" in all_row["recommended_next_guards"]


def test_claim_boundary_blocks_repair_success_and_requires_m3134():
    rows = m3133.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3133-follow_up_result_audit_registered"]["allowed_in_m3133"] is True
    assert by_id["m3133-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3133-repair_success"]["allowed_in_m3133"] is False
    assert by_id["m3133-repair_success"]["claim_made"] is False
    assert by_id["m3133-feasibility_proof"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_process_audit_not_validation(tmp_path):
    manifest = m3133.build_follow_up_manifest(
        output_dir=tmp_path / "m3133",
        doc_path=tmp_path / "m3133.md",
    )

    assert manifest["id"] == m3133.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_corridor_reflex_regression_decomposition_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
