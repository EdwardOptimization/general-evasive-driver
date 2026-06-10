import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_behavior_negative_source_repair_decomposition_materialization_preflight as m3175


def _source():
    measurement_rows = []
    baseline_rows = []
    same_rows = []
    specs = [
        ("0007", "collision_lateral_intrusion", "candidate", "collision", False, False),
        ("0010", "collision_lateral_intrusion", "parent", "collision", False, False),
        ("0013", "collision_lateral_intrusion", "candidate", "off_track", False, False),
        ("0020", "offtrack_boundary_recovery", "parent", "collision", False, True),
        ("0024", "offtrack_boundary_recovery", "parent", "off_track", False, False),
        ("0025", "offtrack_boundary_recovery", "candidate", "collision", False, False),
        ("0026", "offtrack_boundary_recovery", "parent", "collision", False, False),
        ("0029", "offtrack_boundary_recovery", "candidate", "collision", False, False),
    ]
    for index, (suffix, axis, role, outcome, m3172_success, m3105_success) in enumerate(specs, start=1):
        src = f"m3084-measurement-episode-{suffix}"
        measurement_id = f"m3172-measurement-episode-{index:04d}"
        baseline_id = f"m3105-measurement-episode-{index:04d}"
        collision = outcome == "collision"
        offtrack = outcome == "off_track"
        baseline_collision = collision and not m3105_success
        baseline_offtrack = offtrack and not m3105_success
        measurement_rows.append(
            {
                "runtime_smoke_episode_id": measurement_id,
                "source_measurement_episode_id": src,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "axis_id": axis,
                "binding_role": role,
                "task_family": "T5",
                "eval_seed": f"4016{index:02d}",
                "success": str(m3172_success),
                "collision": str(collision),
                "termination_reason": "off_track" if offtrack else ("obstacle_collision" if collision else ""),
                "min_clearance_margin": "-0.1" if collision else "0.1",
                "speed_mean": "8.2" if suffix == "0020" else "16.0",
            }
        )
        baseline_rows.append(
            {
                "runtime_smoke_episode_id": baseline_id,
                "source_measurement_episode_id": src,
                "success": str(m3105_success),
                "collision": str(baseline_collision),
                "termination_reason": "off_track" if baseline_offtrack else ("obstacle_collision" if baseline_collision else ""),
            }
        )
        same_rows.append(
            {
                "baseline_id": "m3105",
                "measurement_episode_id": measurement_id,
                "baseline_episode_id": baseline_id,
                "source_measurement_episode_id": src,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "axis_id": axis,
                "binding_role": role,
                "task_family": "T5",
                "eval_seed": f"4016{index:02d}",
                "m3172_success": str(m3172_success),
                "baseline_success": str(m3105_success),
                "success_delta": "-1" if not m3172_success and m3105_success else "0",
                "m3172_collision": str(collision),
                "baseline_collision": str(baseline_collision),
                "collision_delta": "1" if collision and not baseline_collision else "0",
                "m3172_offtrack": str(offtrack),
                "baseline_offtrack": str(baseline_offtrack),
                "offtrack_delta": "1" if offtrack and not baseline_offtrack else "0",
                "speed_too_low_delta": "0",
                "m3172_min_clearance_margin": "-0.117" if suffix == "0020" else "-0.1",
                "baseline_min_clearance_margin": "0.268" if suffix == "0020" else "-0.12",
                "clearance_margin_delta": "-0.385" if suffix == "0020" else "0.02",
                "m3172_speed_mean": "8.27" if suffix == "0020" else "16.0",
                "baseline_speed_mean": "7.46" if suffix == "0020" else "16.1",
                "speed_mean_delta": "0.81" if suffix == "0020" else "-0.1",
                "m3172_return": "8.55" if suffix == "0020" else "1.0",
                "baseline_return": "46.86" if suffix == "0020" else "1.0",
                "return_delta": "-38.31" if suffix == "0020" else "0.0",
            }
        )
    return {
        "source_exists": {
            "m3174_synthesis": True,
            "m3173_audit": True,
            "m3172_summary": True,
            "m3172_measurement_rows": True,
            "m3172_same_row_comparison_rows": True,
            "m3172_gate_rows": True,
            "m3170_summary": True,
            "m3170_source_localized_rule_rows": True,
            "m3170_gate_rows": True,
            "m3105_summary": True,
            "m3105_measurement_rows": True,
        },
        "m3174_synthesis_text": "pivot_to_m3175_behavior_negative_source_repair_decomposition_materialization",
        "m3173_audit_text": "behavior-negative",
        "m3172_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "measurement_episode_row_count": 64,
            "same_row_comparison_row_count": 256,
            "runtime_base_policy_required": False,
            "validation_result_claim_made": False,
            "repair_success_claim_made": False,
            "driver_performance_claim_made": False,
        },
        "m3172_measurement_rows": measurement_rows,
        "m3172_same_row_comparison_rows": same_rows,
        "m3172_gate_rows": [{"status_pass": True}],
        "m3170_summary": {"status_pass": True},
        "m3170_source_localized_rule_rows": [{} for _ in range(4)],
        "m3170_gate_rows": [{"status_pass": True}],
        "m3105_summary": {"status_pass": True},
        "m3105_measurement_rows": baseline_rows,
    }


def test_regression_rows_extract_single_new_collision_against_m3105():
    rows = m3175.regression_rows(_source())

    assert len(rows) == 1
    row = rows[0]
    assert row["fresh_panel_row_id"] == "m3082-fresh-panel-0020"
    assert row["axis_id"] == "offtrack_boundary_recovery"
    assert row["regression_family"] == "new_collision_regression_vs_m3105"
    assert row["success_delta_vs_m3105"] == -1
    assert row["collision_delta_vs_m3105"] == 1
    assert row["runtime_label_inputs_allowed"] is False
    assert "actor_visible_ablation_trace" in row["decomposition_label"]


def test_blocker_context_separates_new_regression_from_inherited_blockers():
    rows = m3175.blocker_context_rows(_source())
    relations = [row["same_row_relation_to_m3105"] for row in rows]

    assert len(rows) == 8
    assert relations.count("new_collision_regression_vs_m3105") == 1
    assert relations.count("inherited_incumbent_hard_safety_blocker") == 7
    assert sum(row["blocker_family"] == "collision" for row in rows) == 6
    assert sum(row["blocker_family"] == "offtrack" for row in rows) == 2


def test_repair_decomposition_routes_to_trace_not_driver_mutation():
    source = _source()
    regression = m3175.regression_rows(source)
    blockers = m3175.blocker_context_rows(source)
    rows = m3175.repair_decomposition_rows(regression=regression, blockers=blockers)
    by_name = {row["route_name"]: row for row in rows}

    primary = by_name["new_collision_regression_actor_visible_ablation_trace"]
    assert primary["source_row_count"] == 1
    assert primary["admission_decision"] == "decomposition_admitted_repair_not_admitted"
    assert primary["public_driver_mutation_allowed"] is False
    assert "row_label" in primary["forbidden_runtime_inputs"]
    assert by_name["direct_public_driver_mutation"]["admission_decision"] == "blocked_until_actor_visible_ablation_trace_and_audit"


def test_gate_matrix_accepts_complete_decomposition_pack():
    source = _source()
    regression = m3175.regression_rows(source)
    blockers = m3175.blocker_context_rows(source)
    decomposition = m3175.repair_decomposition_rows(regression=regression, blockers=blockers)
    guards = m3175.contract_guard_rows(source, regression, blockers)
    claims = m3175.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3175.gate_matrix_rows(
        source=source,
        regression=regression,
        blockers=blockers,
        decomposition=decomposition,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3175.build_follow_up_manifest(output_dir=tmp_path / "m3175", doc_path=tmp_path / "m3175.md")

    assert manifest["id"] == m3175.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_behavior_negative_source_repair_decomposition"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_behavior_negative_source_repair_decomposition_result_audit_doc",
            "command": "true",
        }
    ]
