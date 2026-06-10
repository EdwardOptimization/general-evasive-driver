import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_failure_source_branch_materialization_preflight as m3164


def _source():
    known_rows = []
    failure_rows = []
    same_case_rows = []
    comparison_rows = []
    specs = [
        ("0007", "collision_lateral_intrusion", "candidate", "collision", "obstacle_collision", -0.11, 0.0, 0.65),
        ("0010", "collision_lateral_intrusion", "parent", "collision", "obstacle_collision", -0.20, 0.58, 1.62),
        ("0013", "collision_lateral_intrusion", "candidate", "offtrack", "off_track", 4.00, 0.52, 2.61),
        ("0024", "offtrack_boundary_recovery", "parent", "offtrack", "off_track", 0.19, 0.24, 2.57),
        ("0025", "offtrack_boundary_recovery", "candidate", "collision", "obstacle_collision", -0.16, 0.0, 1.09),
        ("0026", "offtrack_boundary_recovery", "parent", "collision", "obstacle_collision", -0.20, 0.11, 1.19),
        ("0029", "offtrack_boundary_recovery", "candidate", "collision", "obstacle_collision", -0.23, 0.0, 0.54),
    ]
    for index, (suffix, axis, role, family, terminal, clearance, sideslip, rmse) in enumerate(specs, start=1):
        measurement = f"m3084-measurement-episode-{suffix}"
        known_rows.append(
            {
                "source_blocker_id": f"m3156-known-failure-taxonomy-{index:04d}",
                "validation_episode_id": f"m3161-validation-episode-{index:04d}",
                "source_measurement_episode_id": measurement,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "axis_id": axis,
                "binding_role": role,
                "task_family": "T5",
                "eval_seed": str(401500 + index),
                "source_blocker_family": family,
                "candidate_terminal": terminal,
                "baseline_terminal": terminal,
                "candidate_blocker_family": family,
                "baseline_blocker_family": family,
                "blocker_preserved": True,
                "termination_reason_match": True,
            }
        )
        failure_rows.append(
            {
                "source_measurement_episode_id": measurement,
                "axis_id": axis,
                "binding_role": role,
                "task_family": "T5",
                "eval_seed": str(401500 + index),
                "blocker_family": family,
                "min_clearance_margin": str(clearance),
                "high_sideslip_fraction": str(sideslip),
                "lateral_rmse": str(rmse),
                "speed_mean": "15.0",
                "m3153_comparison_count": "3",
                "m3153_action_channel_sensitive_count": "0",
                "m3153_terminal_invariant": "True",
            }
        )
        same_case_rows.append(
            {
                "source_measurement_episode_id": measurement,
                "candidate_min_clearance_margin": str(clearance),
            }
        )
        for variant in ("brake_saturation_probe", "decel_headroom_probe", "lateral_headroom_probe"):
            comparison_rows.append(
                {
                    "source_measurement_episode_id": measurement,
                    "variant_id": variant,
                    "counterfactual_diagnostic_label": "counterfactual_terminal_outcome_unchanged_diagnostic",
                    "action_channel_sensitive_diagnostic": False,
                }
            )
    return {
        "source_exists": {
            "m3163_synthesis": True,
            "m3161_summary": True,
            "m3161_known_failure_rows": True,
            "m3161_same_case_rows": True,
            "m3161_gate_rows": True,
            "m3156_summary": True,
            "m3156_failure_rows": True,
            "m3156_gate_rows": True,
            "m3153_summary": True,
            "m3153_comparison_rows": True,
            "m3153_gate_rows": True,
        },
        "m3163_synthesis_text": "pivot_to_m3164_residual_hard_safety_failure_source_branch_materialization",
        "m3161_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "validation_episode_row_count": 64,
            "validation_success_count": 57,
            "validation_collision_count": 5,
            "validation_offtrack_count": 2,
            "validation_speed_too_low_count": 0,
        },
        "m3156_summary": {"status_pass": True},
        "m3153_summary": {"status_pass": True},
        "m3161_known_failure_rows": known_rows,
        "m3156_failure_rows": failure_rows,
        "m3161_same_case_rows": same_case_rows,
        "m3153_comparison_rows": comparison_rows,
    }


def test_failure_source_rows_preserve_all_residual_blockers_and_negative_action_delta():
    rows = m3164.failure_source_rows(_source())
    families = [row["blocker_family"] for row in rows]

    assert len(rows) == 7
    assert families.count("collision") == 5
    assert families.count("offtrack") == 2
    assert sum(row["m3153_comparison_count"] for row in rows) == 21
    assert sum(row["m3153_action_channel_sensitive_count"] for row in rows) == 0
    assert all(row["same_case_m3105_match"] for row in rows)
    assert all(not row["same_case_improvement_claim_made"] for row in rows)
    assert any(row["next_evidence_axis"] == "actor_visible_observation_timeline_and_collision_clearance_source_localization" for row in rows)
    assert any(row["next_evidence_axis"] == "actor_visible_boundary_recovery_stability_source_localization" for row in rows)


def test_branch_route_rows_block_local_action_delta_tuning():
    rows = m3164.branch_route_rows()
    by_name = {row["route_name"]: row for row in rows}

    assert by_name["residual_row_accountability"]["required_before_repair"] is True
    assert by_name["observation_timeline_source_localization"]["required_before_repair"] is True
    assert by_name["boundary_recovery_stability_source_localization"]["required_before_repair"] is True
    assert by_name["local_action_delta_tuning"]["required_before_repair"] is False


def test_gate_matrix_accepts_complete_branch_pack():
    source = _source()
    failure_rows = m3164.failure_source_rows(source)
    route_rows = m3164.branch_route_rows()
    claim_rows = m3164.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3164.gate_matrix_rows(
        source=source,
        failure_rows=failure_rows,
        route_rows=route_rows,
        claim_rows=claim_rows,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit_not_repair(tmp_path):
    manifest = m3164.build_follow_up_manifest(output_dir=tmp_path / "m3164", doc_path=tmp_path / "m3164.md")

    assert manifest["id"] == m3164.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_failure_source_branch_result_audit_doc",
            "command": "true",
        }
    ]
