import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_expansion_pack_materialization_preflight as m3185


def _source():
    known_rows = [
        ("0007", "collision_lateral_intrusion", "candidate", "collision", "obstacle_collision", -0.11, 0.0, 0.65),
        ("0010", "collision_lateral_intrusion", "parent", "collision", "obstacle_collision", -0.20, 0.57, 1.62),
        ("0013", "collision_lateral_intrusion", "candidate", "offtrack", "off_track", 4.00, 0.51, 2.61),
        ("0024", "offtrack_boundary_recovery", "parent", "offtrack", "off_track", 0.19, 0.24, 2.57),
        ("0025", "offtrack_boundary_recovery", "candidate", "collision", "obstacle_collision", -0.16, 0.0, 1.09),
        ("0026", "offtrack_boundary_recovery", "parent", "collision", "obstacle_collision", -0.20, 0.11, 1.19),
        ("0029", "offtrack_boundary_recovery", "candidate", "collision", "obstacle_collision", -0.23, 0.0, 0.54),
    ]
    m3156_rows = []
    m3161_rows = []
    for index, (suffix, axis, role, family, terminal, margin, sideslip, rmse) in enumerate(known_rows, start=1):
        source_id = f"m3084-measurement-episode-{suffix}"
        m3156_rows.append(
            {
                "source_blocker_id": f"m3139-residual-blocker-{index:04d}",
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "axis_id": axis,
                "binding_role": role,
                "task_family": "T5",
                "eval_seed": f"4016{index:02d}",
                "blocker_family": family,
                "termination_reason": terminal,
                "outcome_bucket": "collision_failure" if family == "collision" else "off_track_noncollision_noncompletion",
                "min_clearance_margin": str(margin),
                "high_sideslip_fraction": str(sideslip),
                "lateral_rmse": str(rmse),
                "speed_mean": "16.0",
                "m3153_action_channel_sensitive_count": "0",
            }
        )
        m3161_rows.append(
            {
                "source_measurement_episode_id": source_id,
                "blocker_preserved": "True",
            }
        )
    return {
        "source_exists": {
            "m3184_plan": True,
            "m3156_known_failure_rows": True,
            "m3156_summary": True,
            "m3161_known_failure_validation_rows": True,
            "m3161_summary": True,
            "m3153_summary": True,
            "m3181_summary": True,
        },
        "m3184_plan_text": "M3185 blocker-axis expansion pack materialization",
        "m3156_known_failure_rows": m3156_rows,
        "m3156_summary": {"status_pass": True},
        "m3161_known_failure_validation_rows": m3161_rows,
        "m3161_summary": {"status_pass": True},
        "m3153_summary": {"status_pass": True, "action_channel_sensitive_comparison_count": 0},
        "m3181_summary": {"status_pass": True},
    }


def test_residual_blocker_axis_rows_preserve_all_inherited_blockers():
    rows = m3185.residual_blocker_axis_rows(_source())

    assert len(rows) == 7
    assert sum(row["blocker_family"] == "collision" for row in rows) == 5
    assert sum(row["blocker_family"] == "offtrack" for row in rows) == 2
    assert all(row["m3153_action_channel_sensitive_count"] == 0 for row in rows)
    assert all(row["m3161_blocker_preserved"] for row in rows)
    assert not any(row["runtime_actor_input_allowed"] for row in rows)
    assert {row["proposed_evidence_axis"] for row in rows} >= {
        "clearance_timing_axis",
        "boundary_recovery_stability_axis",
        "boundary_recovery_collision_axis",
    }


def test_axis_candidate_rows_keep_implementation_unadmitted():
    blockers = m3185.residual_blocker_axis_rows(_source())
    rows = m3185.actor_visible_axis_candidate_rows(blockers)
    by_axis = {row["evidence_axis"]: row for row in rows}

    assert len(rows) == 4
    assert by_axis["action_authority_saturation_axis"]["source_blocker_count"] == 7
    assert by_axis["clearance_timing_axis"]["hidden_labels_required"] is False
    assert all(row["actor_runtime_input_contract"] == "obs72_only_direct_action3" for row in rows)
    assert not any(row["implementation_admitted"] for row in rows)


def test_forbidden_label_guards_block_runtime_labels():
    rows = m3185.forbidden_label_guard_rows()

    assert len(rows) >= 5
    assert all(row["status_pass"] for row in rows)
    assert not any(row["actor_runtime_allowed"] for row in rows)
    assert any("ttc_oracle" in row["example_fields"] for row in rows)


def test_gate_matrix_accepts_complete_pack():
    source = _source()
    blockers = m3185.residual_blocker_axis_rows(source)
    summaries = m3185.blocker_family_summary_rows(blockers)
    axes = m3185.actor_visible_axis_candidate_rows(blockers)
    forbidden = m3185.forbidden_label_guard_rows()
    gaps = m3185.evidence_gap_rows(source)
    admission = m3185.candidate_admission_rows(axes)
    guards = m3185.contract_guard_rows(source, blockers, axes, forbidden)
    claims = m3185.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3185.gate_matrix_rows(
        source=source,
        blockers=blockers,
        family_summaries=summaries,
        axis_rows=axes,
        forbidden_rows=forbidden,
        evidence_gaps=gaps,
        admission_rows=admission,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3185.build_follow_up_manifest(output_dir=tmp_path / "m3185", doc_path=tmp_path / "m3185.md")

    assert manifest["id"] == m3185.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_hard_safety_blocker_axis_expansion"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_blocker_axis_expansion_pack_result_audit_doc",
            "command": "true",
        }
    ]
