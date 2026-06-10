import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_recovery_clearance_supervisor_residual_trace_measurement_preflight as m3210


def _execution(binding_id, trace_execution_id, *, collision=False, offtrack=False, success=False, margin=0.0):
    return {
        "trace_execution_id": trace_execution_id,
        "trace_source_binding_id": binding_id,
        "evidence_axis": "clearance_timing_axis",
        "fresh_panel_row_id": f"fresh-{binding_id}",
        "source_measurement_episode_id": f"source-{binding_id}",
        "blocker_family": "collision" if collision else "offtrack" if offtrack else "none",
        "axis_id": "axis",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": 100,
        "executable_workload_id": f"workload-{binding_id}",
        "executable_source_spec_id": f"spec-{binding_id}",
        "task_source_id": f"task-{binding_id}",
        "base_profile_name": "profile",
        "runtime_driver_id": "driver",
        "actor_runtime_inputs": "obs72",
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "action_components": "steer|throttle|brake",
        "output_semantics": m3210.OUTPUT_SEMANTICS,
        "scheduled_status_pass": True,
        "steps": 2,
        "terminated": True,
        "truncated": False,
        "success": success,
        "collision": collision,
        "obstacle_completed": success,
        "termination_reason": "off_track" if offtrack else "obstacle_collision" if collision else "",
        "min_clearance_margin": margin,
        "return": 1.0,
        "speed_mean": 10.0,
        "environment_reset_run": True,
        "environment_step_run": True,
        "policy_action_run": True,
        "policy_rollout_run": True,
        "trace_execution_run": True,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "public_driver_default_mutated": False,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "terminal_status_offline_only": True,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_boundary": m3210.CLAIM_SCOPE,
    }


def _step(binding_id, trace_execution_id, step_index, *, steer=0.0, throttle=0.0, brake=0.0, obs_hash="hash"):
    return {
        "trace_step_id": f"{trace_execution_id}-step-{step_index}",
        "trace_execution_id": trace_execution_id,
        "trace_source_binding_id": binding_id,
        "step_index": step_index,
        "evidence_axis": "clearance_timing_axis",
        "fresh_panel_row_id": f"fresh-{binding_id}",
        "source_measurement_episode_id": f"source-{binding_id}",
        "blocker_family": "collision",
        "axis_id": "axis",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": 100,
        "obs72_dim": m3210.P0_OBSERVATION_DIM,
        "obs72_sha256": obs_hash,
        "previous_steer": 0.0,
        "previous_throttle": 0.0,
        "previous_brake": 0.0,
        "final_steer": steer,
        "final_throttle": throttle,
        "final_brake": brake,
        "action_clip_hit": False,
        "actor_runtime_inputs": "obs72",
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "action_components": "steer|throttle|brake",
        "terminal_status_offline_only": True,
        "terminated": False,
        "truncated": False,
        "termination_reason": "",
        "runtime_label_inputs_used": False,
        "hidden_oracle_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "validation_run": False,
        "repair_success_claim_made": False,
        "claim_boundary": m3210.CLAIM_SCOPE,
    }


def _source(tmp_path):
    incumbent_rows = []
    workloads = []
    bindings = []
    m3205_rows = []
    m3194_rows = []
    for index in range(1, 8):
        binding_id = f"binding-{index}"
        work_id = f"workload-{binding_id}"
        spec_id = f"spec-{binding_id}"
        task_id = f"task-{binding_id}"
        evidence_axis = (
            "clearance_timing_axis"
            if index <= 2
            else "boundary_recovery_collision_axis"
            if index <= 5
            else "boundary_recovery_stability_axis"
        )
        incumbent_rows.append(
            {
                **_execution(binding_id, f"inc-{index}", collision=index <= 5, offtrack=index > 5),
                "evidence_axis": evidence_axis,
                "executable_workload_id": work_id,
                "executable_source_spec_id": spec_id,
                "task_source_id": task_id,
            }
        )
        m3205_rows.append({**_execution(binding_id, f"m3205-{index}", collision=index <= 5, offtrack=index > 5), "evidence_axis": evidence_axis})
        m3194_rows.append({**_execution(binding_id, f"m3194-{index}", collision=index <= 5, offtrack=index > 5), "evidence_axis": evidence_axis})
        config_path = tmp_path / f"config-{index}.json"
        config_path.write_text("{}", encoding="utf-8")
        workloads.append(
            {
                "executable_workload_id": work_id,
                "executable_source_spec_id": spec_id,
                "task_source_id": task_id,
                "profile_binding_name": "profile",
                "config_path": str(config_path),
                "status_pass": True,
            }
        )
        bindings.append(
            {
                "trace_source_binding_id": binding_id,
                "evidence_axis": evidence_axis,
                "fresh_panel_row_id": f"fresh-{binding_id}",
                "source_measurement_episode_id": f"source-{binding_id}",
                "blocker_family": "collision" if index <= 5 else "offtrack",
                "axis_id": "axis",
                "binding_role": "candidate",
                "task_family": "T5",
                "eval_seed": 100 + index,
            }
        )
    return {
        "source_exists": {
            "m3209_audit": True,
            "m3208_summary": True,
            "m3208_gate_rows": True,
            "m3208_runtime_contract_rows": True,
            "m3205_summary": True,
            "m3205_candidate_trace_execution_rows": True,
            "m3205_candidate_trace_step_rows": True,
            "m3205_gate_rows": True,
            "m3199_summary": True,
            "m3199_candidate_trace_execution_rows": True,
            "m3199_candidate_trace_step_rows": True,
            "m3199_gate_rows": True,
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
        "m3209_audit_text": "M3210 may execute the M3208 candidate",
        "m3208_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3208_gate_rows": [{"status_pass": "True"}],
        "m3208_runtime_contract_rows": [{"status_pass": "True"}],
        "m3205_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3205_candidate_trace_execution_rows": m3205_rows,
        "m3205_candidate_trace_step_rows": [],
        "m3205_gate_rows": [{"status_pass": "True"}],
        "m3199_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3199_candidate_trace_execution_rows": m3194_rows,
        "m3199_candidate_trace_step_rows": [],
        "m3199_gate_rows": [{"status_pass": "True"}],
        "m3189_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3189_trace_execution_rows": incumbent_rows,
        "m3189_trace_step_rows": [],
        "m3189_gate_rows": [{"status_pass": "True"}],
        "m3187_summary": {"status_pass": True},
        "m3187_trace_source_bindings": bindings,
        "m3012_summary": {"status_pass": True},
        "m3012_executable_specs": [],
        "m3012_workload_rows": workloads,
    }


def test_candidate_driver_uses_recovery_clearance_supervisor_action():
    obs = np.zeros(m3210.P0_OBSERVATION_DIM, dtype=np.float32)
    expected = m3210.recovery_clearance_supervisor_candidate_action(obs, m3210.POLICY_CONFIG)
    observed = m3210.M3210CandidateTraceDriver().act(obs)

    assert observed.shape == (m3210.ACTION_DIM,)
    assert np.all(np.isfinite(observed))
    assert np.allclose(observed, expected)


def test_trace_execution_plan_preserves_m3205_and_m3194_baselines(tmp_path):
    plan = m3210.trace_execution_plan(_source(tmp_path))

    assert len(plan) == 7
    assert all(row["status_pass"] for row in plan)
    assert {row["evidence_axis"] for row in plan} == {
        "clearance_timing_axis",
        "boundary_recovery_collision_axis",
        "boundary_recovery_stability_axis",
    }
    assert all(row["m3205_trace_execution_id"] for row in plan)
    assert all(row["m3194_trace_execution_id"] for row in plan)
    assert all(row["incumbent_trace_execution_id"] for row in plan)


def test_same_trace_comparison_rows_compute_m3205_baseline_deltas():
    candidate = [_execution("binding-1", "m3210-1", success=True, margin=1.0)]
    m3205 = [_execution("binding-1", "m3205-1", collision=True, margin=-0.25)]
    m3194 = [_execution("binding-1", "m3194-1", collision=True, margin=-0.5)]
    incumbent = [_execution("binding-1", "inc-1", collision=True, margin=-1.0)]
    candidate_steps = [
        _step("binding-1", "m3210-1", 0, steer=0.0, throttle=0.0, brake=0.0),
        _step("binding-1", "m3210-1", 1, steer=0.2, throttle=-0.3, brake=0.4),
    ]
    m3205_steps = [
        _step("binding-1", "m3205-1", 0, steer=0.0, throttle=0.0, brake=0.0),
        _step("binding-1", "m3205-1", 1, steer=0.1, throttle=-0.1, brake=0.1),
    ]

    rows = m3210.same_trace_comparison_rows(
        m3210_executions=candidate,
        m3210_steps=candidate_steps,
        m3205_executions=m3205,
        m3205_steps=m3205_steps,
        m3194_executions=m3194,
        m3194_steps=[],
        incumbent_executions=incumbent,
        incumbent_steps=[],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["outcome_changed_vs_m3205"] is True
    assert row["hard_safety_improved_vs_m3205"] is True
    assert row["m3210_vs_m3205_clearance_margin_delta"] == 1.25
    assert row["meaningful_action_delta_step_count_vs_m3205"] == 1


def test_gates_contracts_and_claims_accept_complete_pack(tmp_path):
    source = _source(tmp_path)
    plan = m3210.trace_execution_plan(source)
    executions = []
    steps = []
    for index, plan_row in enumerate(plan, start=1):
        binding_id = plan_row["trace_source_binding_id"]
        executions.append(
            {
                **_execution(binding_id, plan_row["trace_execution_id"], collision=index <= 5, offtrack=index > 5),
                "evidence_axis": plan_row["evidence_axis"],
                "runtime_base_policy_required": False,
                "public_driver_default_mutated": False,
                "terminal_status_offline_only": True,
            }
        )
        steps.append(_step(binding_id, plan_row["trace_execution_id"], 0))
    comparisons = m3210.same_trace_comparison_rows(
        m3210_executions=executions,
        m3210_steps=steps,
        m3205_executions=source["m3205_candidate_trace_execution_rows"],
        m3205_steps=[],
        m3194_executions=source["m3199_candidate_trace_execution_rows"],
        m3194_steps=[],
        incumbent_executions=source["m3189_trace_execution_rows"],
        incumbent_steps=[],
    )
    guards = m3210.contract_guard_rows(
        source=source,
        plan_rows=plan,
        executions=executions,
        steps=steps,
        failures=[],
        comparisons=comparisons,
    )
    claims = m3210.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3210.gate_matrix_rows(
        source=source,
        plan_rows=plan,
        executions=executions,
        steps=steps,
        failures=[],
        comparisons=comparisons,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in guards)
    assert all(row["status_pass"] for row in claims)
    assert all(row["status_pass"] for row in gates)
    assert not any(row["claim_made"] for row in claims if row["claim_family"] == "forbidden")


def test_follow_up_manifest_is_m3211_recovery_clearance_result_audit(tmp_path):
    manifest = m3210.build_follow_up_manifest(output_dir=tmp_path / "m3210", doc_path=tmp_path / "m3210.md")

    assert manifest["id"] == m3210.NEXT_ID
    assert manifest["priority"] == 32110
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_hard_safety_recovery_clearance_supervisor"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
