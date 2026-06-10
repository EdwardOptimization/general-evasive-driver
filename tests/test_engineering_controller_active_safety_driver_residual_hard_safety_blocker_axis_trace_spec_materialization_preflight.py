import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_materialization_preflight as m3187


def _source():
    blockers = [
        ("0007", "clearance_timing_axis", "collision"),
        ("0010", "clearance_timing_axis", "collision"),
        ("0013", "boundary_recovery_stability_axis", "offtrack"),
        ("0024", "boundary_recovery_stability_axis", "offtrack"),
        ("0025", "boundary_recovery_collision_axis", "collision"),
        ("0026", "boundary_recovery_collision_axis", "collision"),
        ("0029", "boundary_recovery_collision_axis", "collision"),
    ]
    blocker_rows = []
    for index, (suffix, axis, family) in enumerate(blockers, start=1):
        blocker_rows.append(
            {
                "proposed_evidence_axis": axis,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "source_measurement_episode_id": f"m3084-measurement-episode-{suffix}",
                "blocker_family": family,
                "axis_id": "offtrack_boundary_recovery" if suffix.startswith("002") else "collision_lateral_intrusion",
                "binding_role": "candidate",
                "task_family": "T5",
                "eval_seed": f"4016{index:02d}",
                "offline_labels_only": "source_measurement_episode_id|fresh_panel_row_id|blocker_family",
            }
        )
    axis_rows = [
        {
            "evidence_axis": "clearance_timing_axis",
            "route_role": "primary_collision_axis",
            "source_blocker_count": "2",
            "source_blocker_rows": "m3082-fresh-panel-0007|m3082-fresh-panel-0010",
            "allowed_signal_families": "ego_speed|obstacle_geometry_proxy",
        },
        {
            "evidence_axis": "boundary_recovery_collision_axis",
            "route_role": "boundary_collision_axis",
            "source_blocker_count": "3",
            "source_blocker_rows": "m3082-fresh-panel-0025|m3082-fresh-panel-0026|m3082-fresh-panel-0029",
            "allowed_signal_families": "lane_boundary_geometry|obstacle_geometry_proxy",
        },
        {
            "evidence_axis": "boundary_recovery_stability_axis",
            "route_role": "primary_offtrack_axis",
            "source_blocker_count": "2",
            "source_blocker_rows": "m3082-fresh-panel-0013|m3082-fresh-panel-0024",
            "allowed_signal_families": "lane_boundary_geometry|lateral_error",
        },
        {
            "evidence_axis": "action_authority_saturation_axis",
            "route_role": "cross_cutting_authority_axis",
            "source_blocker_count": "7",
            "source_blocker_rows": "|".join(row["fresh_panel_row_id"] for row in blocker_rows),
            "allowed_signal_families": "raw_action_bounds|final_action_bounds|action_rate|clip_fraction",
        },
    ]
    forbidden = [
        {
            "label_family": "row_identity_labels",
            "example_fields": "source_measurement_episode_id|fresh_panel_row_id",
            "actor_runtime_allowed": "False",
            "offline_analysis_allowed": "True",
        },
        {
            "label_family": "scenario_role_labels",
            "example_fields": "axis_id|binding_role|task_family",
            "actor_runtime_allowed": "False",
            "offline_analysis_allowed": "True",
        },
        {
            "label_family": "terminal_outcome_labels",
            "example_fields": "blocker_family|termination_reason|outcome_bucket",
            "actor_runtime_allowed": "False",
            "offline_analysis_allowed": "True",
        },
        {
            "label_family": "baseline_comparison_labels",
            "example_fields": "baseline_success|baseline_collision|same_row_delta",
            "actor_runtime_allowed": "False",
            "offline_analysis_allowed": "True",
        },
        {
            "label_family": "oracle_progress_labels",
            "example_fields": "target_label|ttc_oracle|verdict_label",
            "actor_runtime_allowed": "False",
            "offline_analysis_allowed": "True",
        },
    ]
    return {
        "source_exists": {
            "m3186_audit": True,
            "m3185_summary": True,
            "m3185_residual_blocker_axis_rows": True,
            "m3185_actor_visible_axis_candidate_rows": True,
            "m3185_forbidden_label_guard_rows": True,
            "m3185_gate_matrix": True,
        },
        "m3186_audit_text": "M3187 trace-spec materialization",
        "m3185_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3185_residual_blocker_axis_rows": blocker_rows,
        "m3185_actor_visible_axis_candidate_rows": axis_rows,
        "m3185_forbidden_label_guard_rows": forbidden,
        "m3185_gate_matrix": [{"status_pass": "True"}],
    }


def test_trace_specs_preserve_all_m3185_axes_without_implementation():
    rows = m3187.trace_spec_rows(_source())
    by_axis = {row["evidence_axis"]: row for row in rows}

    assert set(by_axis) == {
        "clearance_timing_axis",
        "boundary_recovery_collision_axis",
        "boundary_recovery_stability_axis",
        "action_authority_saturation_axis",
    }
    assert by_axis["action_authority_saturation_axis"]["source_blocker_count"] == 7
    assert "raw_action_bounds" in by_axis["action_authority_saturation_axis"]["required_trace_channels"]
    assert all(row["actor_runtime_input_contract"] == "obs72_only_direct_action3" for row in rows)
    assert not any(row["implementation_admitted"] for row in rows)


def test_trace_source_bindings_preserve_seven_blocker_rows():
    rows = m3187.trace_source_binding_rows(_source())

    assert len(rows) == 7
    assert sum(row["evidence_axis"] == "clearance_timing_axis" for row in rows) == 2
    assert sum(row["evidence_axis"] == "boundary_recovery_collision_axis" for row in rows) == 3
    assert sum(row["evidence_axis"] == "boundary_recovery_stability_axis" for row in rows) == 2
    assert not any(row["runtime_actor_input_allowed"] for row in rows)


def test_boundaries_disallow_oracle_trace_and_runtime_labels():
    boundaries = m3187.obs72_public_telemetry_boundary_rows()
    by_signal = {row["signal_family"]: row for row in boundaries}
    forbidden = m3187.forbidden_label_guard_rows(_source())

    assert by_signal["obs72_snapshot"]["actor_runtime_allowed"] is True
    assert by_signal["oracle_ttc_or_verdict"]["offline_trace_allowed"] is False
    assert not any(row["actor_runtime_allowed"] for row in forbidden)


def test_gate_matrix_accepts_complete_trace_spec_pack():
    source = _source()
    specs = m3187.trace_spec_rows(source)
    bindings = m3187.trace_source_binding_rows(source)
    boundaries = m3187.obs72_public_telemetry_boundary_rows()
    forbidden = m3187.forbidden_label_guard_rows(source)
    admissions = m3187.implementation_admission_guard_rows(specs)
    claims = m3187.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3187.gate_matrix_rows(
        source=source,
        trace_specs=specs,
        bindings=bindings,
        boundaries=boundaries,
        forbidden_rows=forbidden,
        admissions=admissions,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3187.build_follow_up_manifest(output_dir=tmp_path / "m3187", doc_path=tmp_path / "m3187.md")

    assert manifest["id"] == m3187.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_hard_safety_blocker_axis_expansion"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_result_audit_doc",
            "command": "true",
        }
    ]
