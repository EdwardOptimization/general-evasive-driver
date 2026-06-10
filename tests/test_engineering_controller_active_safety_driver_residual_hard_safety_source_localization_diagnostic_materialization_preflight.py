import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_source_localization_diagnostic_materialization_preflight as m3166


def _step_rows(measurement_id: str, count: int, *, family: str) -> list[dict[str, str]]:
    rows = []
    for step in range(1, count + 1):
        rows.append(
            {
                "source_measurement_episode_id": measurement_id,
                "step_index": str(step),
                "obstacle_urgency_actor_visible": "0.7" if family == "collision" and step >= max(1, count - 2) else "0.0",
                "edge_urgency_actor_visible": "0.95" if family == "offtrack" and step >= 2 else "0.2",
                "min_clearance_margin_m_after_step": "-0.1" if family == "collision" and step == count else "0.2",
            }
        )
    return rows


def _delta_step_rows(measurement_id: str, count: int) -> list[dict[str, str]]:
    return [
        {
            "source_measurement_episode_id": measurement_id,
            "step_index": str(step),
            "overlay_active": "True",
            "candidate_action_saturated": "True" if step % 5 == 0 else "False",
            "delta_max_abs": "0.2",
        }
        for step in range(1, count + 1)
    ]


def _source():
    specs = [
        ("0007", "collision_lateral_intrusion", "candidate", "collision", -0.11, 29),
        ("0010", "collision_lateral_intrusion", "parent", "collision", -0.20, 38),
        ("0013", "collision_lateral_intrusion", "candidate", "offtrack", 4.00, 52),
        ("0024", "offtrack_boundary_recovery", "parent", "offtrack", 0.19, 51),
        ("0025", "offtrack_boundary_recovery", "candidate", "collision", -0.16, 28),
        ("0026", "offtrack_boundary_recovery", "parent", "collision", -0.20, 31),
        ("0029", "offtrack_boundary_recovery", "candidate", "collision", -0.23, 27),
    ]
    failure_rows = []
    influence_rows = []
    coverage_rows = []
    step_rows = []
    delta_step_rows = []
    for index, (suffix, axis, role, family, clearance, step_count) in enumerate(specs, start=1):
        measurement = f"m3084-measurement-episode-{suffix}"
        failure_rows.append(
            {
                "source_measurement_episode_id": measurement,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "axis_id": axis,
                "binding_role": role,
                "blocker_family": family,
                "failure_source_label": (
                    "negative_clearance_collision_preserved_under_action_delta_variants"
                    if family == "collision"
                    else "boundary_recovery_stability_failure_preserved_under_action_delta_variants"
                ),
                "next_evidence_axis": (
                    "actor_visible_observation_timeline_and_collision_clearance_source_localization"
                    if family == "collision"
                    else "actor_visible_boundary_recovery_stability_source_localization"
                ),
            }
        )
        influence_rows.append(
            {
                "source_measurement_episode_id": measurement,
                "trace_step_count": str(step_count),
                "primary_diagnostic_label": (
                    "collision_action_present_but_clearance_unresolved"
                    if family == "collision"
                    else "offtrack_stability_recovery_limited"
                ),
                "hard_safety_signal_present": "True",
                "max_obstacle_urgency_actor_visible": "0.7" if family == "collision" else "0.2",
                "step_of_max_obstacle_urgency": str(step_count),
                "max_edge_urgency_actor_visible": "0.96" if family == "offtrack" else "0.85",
                "step_of_max_edge_urgency": str(max(1, step_count - 1)),
                "terminal_min_clearance_margin_m": str(clearance),
                "min_clearance_margin_m_min": str(clearance),
                "high_sideslip_fraction": "0.4" if family == "offtrack" else "0.0",
                "final_10_mean_abs_steer": "0.8",
                "final_10_mean_brake_physical": "0.6",
                "action_saturation_fraction": "0.1",
            }
        )
        coverage_rows.append(
            {
                "source_measurement_episode_id": measurement,
                "overlay_active_fraction": "1.0",
                "max_delta_abs": "0.2",
                "candidate_saturation_fraction": "0.2",
                "final_10_mean_delta_l1": "0.1",
                "final_10_mean_delta_brake": "0.05",
                "coverage_diagnostic_label": (
                    "collision_terminal_window_delta_low"
                    if index == 2
                    else "delta_present_outcome_unresolved"
                ),
            }
        )
        step_rows.extend(_step_rows(measurement, step_count, family=family))
        delta_step_rows.extend(_delta_step_rows(measurement, step_count))
    return {
        "source_exists": {
            "m3165_audit": True,
            "m3164_summary": True,
            "m3164_failure_source_rows": True,
            "m3164_branch_route_rows": True,
            "m3164_gate_rows": True,
            "m3115_summary": True,
            "m3115_residual_action_influence_rows": True,
            "m3115_residual_step_trace_rows": True,
            "m3115_gate_rows": True,
            "m3147_summary": True,
            "m3147_action_delta_coverage_rows": True,
            "m3147_action_delta_step_trace_rows": True,
            "m3147_gate_rows": True,
        },
        "m3165_audit_text": "accept_m3164_branch_pack_route_to_m3166_source_localization_diagnostic_materialization",
        "m3164_summary": {"status_pass": True, "gate_matrix_pass": True, "failure_source_row_count": 7},
        "m3164_failure_source_rows": failure_rows,
        "m3164_branch_route_rows": [{"route_name": "observation_timeline_source_localization"}],
        "m3115_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "residual_step_trace_row_count": 256,
            "residual_action_influence_row_count": 7,
        },
        "m3115_residual_action_influence_rows": influence_rows,
        "m3115_residual_step_trace_rows": step_rows,
        "m3147_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "action_delta_step_trace_row_count": 256,
            "action_delta_coverage_row_count": 7,
        },
        "m3147_action_delta_coverage_rows": coverage_rows,
        "m3147_action_delta_step_trace_rows": delta_step_rows,
    }


def test_source_localization_rows_join_all_residual_and_step_traces():
    rows = m3166.source_localization_rows(_source())
    families = [row["blocker_family"] for row in rows]

    assert len(rows) == 7
    assert families.count("collision") == 5
    assert families.count("offtrack") == 2
    assert sum(row["m3115_step_trace_count"] for row in rows) == 256
    assert sum(row["m3147_delta_step_trace_count"] for row in rows) == 256
    assert any(row["source_localization_label"] == "collision_clearance_unresolved_with_late_or_low_terminal_action_delta" for row in rows)
    assert any(row["source_localization_label"] == "boundary_recovery_unresolved_despite_visible_edge_and_stability_stress" for row in rows)
    assert all(row["repair_admission_label"].startswith("diagnostic_admitted_repair_not_admitted") for row in rows)


def test_repair_admission_rows_admit_diagnostics_but_block_local_delta_tuning():
    localization_rows = m3166.source_localization_rows(_source())
    rows = m3166.repair_admission_rows(localization_rows)
    by_name = {row["route_name"]: row for row in rows}

    assert by_name["collision_observation_timeline_source_localization"]["source_localization_row_count"] == 5
    assert by_name["boundary_recovery_stability_source_localization"]["source_localization_row_count"] == 2
    assert by_name["collision_observation_timeline_source_localization"]["admission_decision"] == "diagnostic_admitted_repair_not_admitted"
    assert by_name["local_action_delta_tuning"]["required_before_repair"] is False
    assert by_name["local_action_delta_tuning"]["admission_decision"] == "blocked_until_source_localization_changes_repair_hypothesis"


def test_gate_matrix_accepts_complete_source_localization_pack():
    source = _source()
    localization_rows = m3166.source_localization_rows(source)
    repair_rows = m3166.repair_admission_rows(localization_rows)
    claim_rows = m3166.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3166.gate_matrix_rows(
        source=source,
        localization_rows=localization_rows,
        repair_rows=repair_rows,
        claim_rows=claim_rows,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit_not_repair(tmp_path):
    manifest = m3166.build_follow_up_manifest(output_dir=tmp_path / "m3166", doc_path=tmp_path / "m3166.md")

    assert manifest["id"] == m3166.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_source_localization_diagnostic_result_audit_doc",
            "command": "true",
        }
    ]
