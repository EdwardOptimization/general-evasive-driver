import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_execution_materialization_preflight as m3189


def _source(tmp_path):
    cfg = tmp_path / "profile.json"
    cfg.write_text('{"controller_profile": {"name": "parent"}, "env": {"history_length": 1}}', encoding="utf-8")
    bindings = []
    measurement_rows = []
    workload_rows = []
    axes = [
        ("0007", "clearance_timing_axis", "collision", "candidate"),
        ("0010", "clearance_timing_axis", "collision", "parent"),
        ("0013", "boundary_recovery_stability_axis", "offtrack", "candidate"),
        ("0024", "boundary_recovery_stability_axis", "offtrack", "parent"),
        ("0025", "boundary_recovery_collision_axis", "collision", "candidate"),
        ("0026", "boundary_recovery_collision_axis", "collision", "parent"),
        ("0029", "boundary_recovery_collision_axis", "collision", "candidate"),
    ]
    for index, (suffix, evidence_axis, family, role) in enumerate(axes, start=1):
        source_id = f"m3084-measurement-episode-{suffix}"
        workload_id = f"workload-{index}"
        bindings.append(
            {
                "trace_source_binding_id": f"m3187-trace-source-binding-{index:04d}",
                "evidence_axis": evidence_axis,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "source_measurement_episode_id": source_id,
                "blocker_family": family,
                "axis_id": "offtrack_boundary_recovery" if suffix.startswith("002") else "collision_lateral_intrusion",
                "binding_role": role,
                "task_family": "T5",
                "eval_seed": str(401500 + index),
                "runtime_actor_input_allowed": "False",
            }
        )
        measurement_rows.append(
            {
                "runtime_smoke_episode_id": f"m3105-measurement-episode-{index:04d}",
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
                "axis_id": bindings[-1]["axis_id"],
                "binding_role": role,
                "task_family": "T5",
                "executable_workload_id": workload_id,
                "executable_source_spec_id": "spec-1",
                "task_source_id": "source-1",
                "base_profile_name": "parent",
                "eval_seed": str(401500 + index),
                "candidate_output_semantics": m3189.OUTPUT_SEMANTICS,
                "runtime_base_policy_required": "False",
            }
        )
        workload_rows.append(
            {
                "executable_workload_id": workload_id,
                "profile_binding_name": "parent",
                "config_path": str(cfg),
                "status_pass": "True",
            }
        )
    return {
        "source_exists": {
            "m3188_audit": True,
            "m3187_summary": True,
            "m3187_trace_specs": True,
            "m3187_trace_source_bindings": True,
            "m3187_boundary_rows": True,
            "m3187_forbidden_label_guard_rows": True,
            "m3187_gate_rows": True,
            "m3105_summary": True,
            "m3105_measurement_rows": True,
            "m3012_summary": True,
            "m3012_executable_specs": True,
            "m3012_workload_rows": True,
        },
        "m3188_audit_text": "M3189 trace execution materialization",
        "m3187_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3187_trace_specs": [],
        "m3187_trace_source_bindings": bindings,
        "m3187_boundary_rows": [],
        "m3187_forbidden_label_guard_rows": [],
        "m3187_gate_rows": [],
        "m3105_summary": {"status_pass": True},
        "m3105_measurement_rows": measurement_rows,
        "m3012_summary": {"status_pass": True},
        "m3012_executable_specs": [
            {
                "executable_source_spec_id": "spec-1",
                "task_source_id": "source-1",
                "status_pass": "True",
            }
        ],
        "m3012_workload_rows": workload_rows,
    }


def test_trace_execution_plan_preserves_seven_bindings_without_runtime_labels(tmp_path):
    plan = m3189.trace_execution_plan(_source(tmp_path))

    assert len(plan) == 7
    assert {row["trace_source_binding_id"] for row in plan} == {
        f"m3187-trace-source-binding-{index:04d}" for index in range(1, 8)
    }
    assert all(row["status_pass"] for row in plan)
    assert not any(row["hidden_label_violation"] for row in plan)
    assert all(row["config_path"] for row in plan)


def test_gate_matrix_accepts_complete_trace_execution_pack(tmp_path):
    source = _source(tmp_path)
    plan = m3189.trace_execution_plan(source)
    executions = []
    steps = []
    for row in plan:
        executions.append(
            {
                "trace_execution_id": row["trace_execution_id"],
                "trace_source_binding_id": row["trace_source_binding_id"],
                "evidence_axis": row["evidence_axis"],
                "action_components": "steer|throttle|brake",
                "actor_runtime_inputs": "obs72",
                "terminal_status_offline_only": True,
                "runtime_base_policy_required": False,
                "public_driver_default_mutated": False,
                "success": False,
                "collision": row["blocker_family"] == "collision",
                "termination_reason": "off_track" if row["blocker_family"] == "offtrack" else "obstacle_collision",
            }
        )
        steps.append(
            {
                "trace_execution_id": row["trace_execution_id"],
                "trace_source_binding_id": row["trace_source_binding_id"],
                "actor_runtime_inputs": "obs72",
                "actor_runtime_input_contract": "obs72_only_direct_action3",
                "terminal_status_offline_only": True,
                "runtime_label_inputs_used": False,
                "hidden_oracle_actor_input_required": False,
                "source_labels_actor_visible": False,
                "route_labels_actor_visible": False,
                "outcome_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
                "ttc_actor_input_required": False,
            }
        )
    guards = m3189.contract_guard_rows(source=source, plan_rows=plan, executions=executions, steps=steps, failures=[])
    claims = m3189.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3189.gate_matrix_rows(
        source=source,
        plan_rows=plan,
        executions=executions,
        steps=steps,
        failures=[],
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in guards)
    assert all(row["status_pass"] for row in gates)


def test_claim_rows_reject_validation_repair_success_and_self_id():
    claims = m3189.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in claims}

    assert by_id["m3189-trace_execution_rows"]["claim_made"] is True
    assert by_id["m3189-repair_implementation"]["allowed_in_m3189"] is False
    assert by_id["m3189-validation_result"]["claim_made"] is False
    assert by_id["m3189-repair_success"]["claim_made"] is False
    assert by_id["m3189-self_id"]["claim_made"] is False
    assert all(row["status_pass"] for row in claims)


def test_follow_up_manifest_is_m3190_process_audit(tmp_path):
    manifest = m3189.build_follow_up_manifest(output_dir=tmp_path / "m3189", doc_path=tmp_path / "m3189.md")

    assert manifest["id"] == m3189.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_hard_safety_blocker_axis_expansion"
