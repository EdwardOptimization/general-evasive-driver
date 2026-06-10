import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_neutral_candidate_vs_incumbent_trace_delta_diagnostic_materialization_preflight as m3199


def _source(tmp_path):
    cfg = tmp_path / "profile.json"
    cfg.write_text('{"controller_profile": {"name": "parent"}, "env": {"history_length": 1}}', encoding="utf-8")
    axes = [
        ("0007", "clearance_timing_axis", "collision", "candidate"),
        ("0010", "clearance_timing_axis", "collision", "parent"),
        ("0013", "boundary_recovery_stability_axis", "offtrack", "candidate"),
        ("0024", "boundary_recovery_stability_axis", "offtrack", "parent"),
        ("0025", "boundary_recovery_collision_axis", "collision", "candidate"),
        ("0026", "boundary_recovery_collision_axis", "collision", "parent"),
        ("0029", "boundary_recovery_collision_axis", "collision", "candidate"),
    ]
    bindings = []
    incumbents = []
    workload_rows = []
    for index, (suffix, evidence_axis, family, role) in enumerate(axes, start=1):
        binding_id = f"m3187-trace-source-binding-{index:04d}"
        workload_id = f"workload-{index}"
        binding = {
            "trace_source_binding_id": binding_id,
            "evidence_axis": evidence_axis,
            "fresh_panel_row_id": f"m3082-fresh-panel-{suffix}",
            "source_measurement_episode_id": f"m3084-measurement-episode-{suffix}",
            "blocker_family": family,
            "axis_id": "offtrack_boundary_recovery" if family == "offtrack" else "collision_lateral_intrusion",
            "binding_role": role,
            "task_family": "T5",
            "offline_labels_only": "True",
            "runtime_actor_input_allowed": "False",
        }
        bindings.append(binding)
        incumbents.append(
            {
                **binding,
                "trace_execution_id": f"m3189-trace-execution-{index:04d}",
                "eval_seed": str(401500 + index),
                "executable_workload_id": workload_id,
                "executable_source_spec_id": "spec-1",
                "task_source_id": "source-1",
                "base_profile_name": "parent",
                "scheduled_status_pass": "True",
                "output_semantics": m3199.OUTPUT_SEMANTICS,
                "runtime_base_policy_required": "False",
                "success": "False",
                "collision": str(family == "collision"),
                "termination_reason": "off_track" if family == "offtrack" else "obstacle_collision",
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
            "m3198_synthesis": True,
            "m3194_summary": True,
            "m3194_gate_rows": True,
            "m3189_summary": True,
            "m3189_trace_execution_rows": True,
            "m3189_trace_step_rows": True,
            "m3189_gate_rows": True,
            "m3187_summary": True,
            "m3187_trace_source_bindings": True,
            "m3012_summary": True,
            "m3012_executable_specs": True,
            "m3012_workload_rows": True,
        },
        "m3198_synthesis_text": m3199.MILESTONE_ID,
        "m3194_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3194_gate_rows": [{"status_pass": "True"}],
        "m3189_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3189_trace_execution_rows": incumbents,
        "m3189_trace_step_rows": [],
        "m3189_gate_rows": [{"status_pass": "True"}],
        "m3187_summary": {"status_pass": True},
        "m3187_trace_source_bindings": bindings,
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


def _step(trace_execution_id, binding_id, index, steer, throttle=0.0, brake=0.0):
    return {
        "trace_execution_id": trace_execution_id,
        "incumbent_trace_execution_id": "m3189-trace-execution-0001",
        "trace_source_binding_id": binding_id,
        "step_index": index,
        "evidence_axis": "clearance_timing_axis",
        "fresh_panel_row_id": "m3082-fresh-panel-0007",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "blocker_family": "collision",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "401501",
        "obs72_sha256": f"obs-{index}",
        "final_steer": steer,
        "final_throttle": throttle,
        "final_brake": brake,
        "action_clip_hit": False,
        "post_speed": 8.0 + index,
        "relative_clearance_proxy": 1.0 - index * 0.1,
        "post_lateral_error": 0.2,
        "terminated": index == 5,
        "termination_reason": "obstacle_collision" if index == 5 else "",
        "actor_runtime_inputs": "obs72",
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


def test_trace_execution_plan_preserves_m3189_bindings_and_contract(tmp_path):
    plan = m3199.trace_execution_plan(_source(tmp_path))

    assert len(plan) == m3199.EXPECTED_TRACE_BINDINGS
    assert plan[0]["trace_execution_id"] == "m3199-candidate-trace-execution-0001"
    assert plan[0]["incumbent_trace_execution_id"] == "m3189-trace-execution-0001"
    assert all(row["status_pass"] for row in plan)
    assert not any(row["hidden_label_violation"] for row in plan)
    assert {row["trace_source_binding_id"] for row in plan} == {
        f"m3187-trace-source-binding-{index:04d}" for index in range(1, 8)
    }


def test_trace_delta_rows_classify_action_delta_without_success_claims():
    binding_id = "m3187-trace-source-binding-0001"
    incumbent = [_step("m3189-trace-execution-0001", binding_id, index, steer=0.0) for index in range(12)]
    candidate = [
        _step("m3199-candidate-trace-execution-0001", binding_id, index, steer=0.2 if index in (2, 10) else 0.0)
        for index in range(12)
    ]

    deltas = m3199.trace_delta_rows(candidate_steps=candidate, incumbent_steps=incumbent)
    by_step = {row["step_index"]: row for row in deltas}

    assert len(deltas) == 12
    assert by_step[2]["delta_timing_bucket"] == "preterminal"
    assert by_step[10]["delta_timing_bucket"] == "terminal_window"
    assert by_step[2]["steer_delta_sign"] == "positive"
    assert not any(row["validation_run"] for row in deltas)
    assert not any(row["repair_success_claim_made"] for row in deltas)


def test_gate_matrix_accepts_complete_trace_delta_pack(tmp_path):
    source = _source(tmp_path)
    plan = m3199.trace_execution_plan(source)
    executions = []
    steps = []
    delta_summaries = []
    for index, row in enumerate(plan, start=1):
        executions.append(
            {
                "trace_execution_id": row["trace_execution_id"],
                "incumbent_trace_execution_id": row["incumbent_trace_execution_id"],
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
                "min_clearance_margin": "0.0",
            }
        )
        steps.append(_step(row["trace_execution_id"], row["trace_source_binding_id"], 0, steer=0.0))
        delta_summaries.append(
            {
                "trace_source_binding_id": row["trace_source_binding_id"],
                "candidate_trace_execution_id": row["trace_execution_id"],
                "incumbent_trace_execution_id": row["incumbent_trace_execution_id"],
                "outcome_changed": False,
            }
        )
    deltas = [
        {
            "trace_delta_id": "m3199-trace-delta-0001",
            "trace_source_binding_id": plan[0]["trace_source_binding_id"],
            "candidate_step_present": True,
            "incumbent_step_present": True,
            "action_delta_l2": 0.0,
            "terminal_window_step": False,
            "validation_run": False,
            "repair_success_claim_made": False,
        }
    ]
    guards = m3199.contract_guard_rows(
        source=source,
        plan_rows=plan,
        executions=executions,
        steps=steps,
        failures=[],
        deltas=deltas,
    )
    claims = m3199.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3199.gate_matrix_rows(
        source=source,
        plan_rows=plan,
        executions=executions,
        steps=steps,
        failures=[],
        deltas=deltas,
        delta_summaries=delta_summaries,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in guards)
    assert all(row["status_pass"] for row in claims)
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_and_claim_rows_remain_process_only(tmp_path):
    manifest = m3199.build_follow_up_manifest(output_dir=tmp_path / "m3199", doc_path=tmp_path / "m3199.md")
    claims = m3199.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in claims}

    assert manifest["id"] == m3199.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert by_id["m3199-trace_delta_rows"]["claim_made"] is True
    assert by_id["m3199-validation_result"]["claim_made"] is False
    assert by_id["m3199-repair_success"]["claim_made"] is False
    assert by_id["m3199-public_driver_default_mutation"]["claim_made"] is False
    assert by_id["m3199-self_id"]["claim_made"] is False
    assert all(row["status_pass"] for row in claims)
