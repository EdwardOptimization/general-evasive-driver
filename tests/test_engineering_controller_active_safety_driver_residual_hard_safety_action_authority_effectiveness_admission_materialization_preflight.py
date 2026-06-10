import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_action_authority_effectiveness_admission_materialization_preflight as m3201


def _source():
    summaries = [
        {
            "trace_source_binding_id": "binding-1",
            "evidence_axis": "clearance_timing_axis",
            "blocker_family": "collision",
            "candidate_steps": "10",
            "meaningful_delta_step_count": "10",
            "preterminal_delta_step_count": "8",
            "terminal_window_delta_step_count": "2",
            "outcome_changed": "False",
            "candidate_collision": "True",
            "candidate_offtrack": "False",
            "clearance_margin_delta": "0.05",
        },
        {
            "trace_source_binding_id": "binding-2",
            "evidence_axis": "boundary_recovery_collision_axis",
            "blocker_family": "collision",
            "candidate_steps": "12",
            "meaningful_delta_step_count": "12",
            "preterminal_delta_step_count": "10",
            "terminal_window_delta_step_count": "2",
            "outcome_changed": "False",
            "candidate_collision": "True",
            "candidate_offtrack": "False",
            "clearance_margin_delta": "-0.01",
        },
        {
            "trace_source_binding_id": "binding-3",
            "evidence_axis": "boundary_recovery_stability_axis",
            "blocker_family": "offtrack",
            "candidate_steps": "14",
            "meaningful_delta_step_count": "14",
            "preterminal_delta_step_count": "12",
            "terminal_window_delta_step_count": "2",
            "outcome_changed": "False",
            "candidate_collision": "False",
            "candidate_offtrack": "True",
            "clearance_margin_delta": "0.2",
        },
    ]
    deltas = []
    for summary in summaries:
        binding_id = summary["trace_source_binding_id"]
        for step in range(int(summary["candidate_steps"])):
            deltas.append(
                {
                    "trace_source_binding_id": binding_id,
                    "action_delta_l2": "0.2",
                    "abs_steer_delta": "0.02",
                    "abs_throttle_delta": "0.1",
                    "abs_brake_delta": "0.15",
                    "steer_delta_sign": "positive" if step % 3 else "negative",
                    "throttle_delta_sign": "negative",
                    "brake_delta_sign": "positive" if step % 4 else "zero",
                    "candidate_clip_hit": step == 0,
                    "incumbent_clip_hit": step in (0, 1),
                }
            )
    return {
        "source_exists": {
            "m3200_audit": True,
            "m3199_summary": True,
            "m3199_candidate_trace_execution_rows": True,
            "m3199_trace_delta_rows": True,
            "m3199_trace_delta_summary_rows": True,
            "m3199_contract_guard_rows": True,
            "m3199_claim_boundary_rows": True,
            "m3199_gate_rows": True,
        },
        "m3200_audit_text": "m3201-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-effectiveness-admission-materialization-preflight",
        "m3199_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "candidate_trace_execution_row_count": 7,
            "trace_delta_row_count": len(deltas),
            "preterminal_delta_step_count": 30,
            "outcome_changed_trace_count": 0,
            "actor_runtime_input_contract": "obs72_only_direct_action3",
            "action_components": ["steer", "throttle", "brake"],
            "hidden_actor_inputs_used": False,
            "public_driver_default_mutated": False,
            "validation_run": False,
            "repair_success_claim_made": False,
        },
        "m3199_candidate_trace_execution_rows": [{} for _ in range(7)],
        "m3199_trace_delta_rows": deltas,
        "m3199_trace_delta_summary_rows": summaries + [
            {
                "trace_source_binding_id": f"extra-{index}",
                "evidence_axis": "boundary_recovery_collision_axis",
                "blocker_family": "collision",
                "candidate_steps": "1",
                "meaningful_delta_step_count": "1",
                "preterminal_delta_step_count": "1",
                "terminal_window_delta_step_count": "0",
                "outcome_changed": "False",
                "candidate_collision": "True",
                "candidate_offtrack": "False",
                "clearance_margin_delta": "0.0",
            }
            for index in range(3)
        ]
        + [
            {
                "trace_source_binding_id": "extra-offtrack",
                "evidence_axis": "boundary_recovery_stability_axis",
                "blocker_family": "offtrack",
                "candidate_steps": "1",
                "meaningful_delta_step_count": "1",
                "preterminal_delta_step_count": "1",
                "terminal_window_delta_step_count": "0",
                "outcome_changed": "False",
                "candidate_collision": "False",
                "candidate_offtrack": "True",
                "clearance_margin_delta": "0.0",
            }
        ],
        "m3199_contract_guard_rows": [{"status_pass": "True"}],
        "m3199_claim_boundary_rows": [{"status_pass": "True"}],
        "m3199_gate_rows": [{"status_pass": "True"}],
    }


def test_action_authority_effectiveness_admissions_are_recommended_but_not_allowed_now():
    rows = m3201.action_authority_effectiveness_admission_rows(_source())
    by_family = {row["admission_family"]: row for row in rows}

    assert len(rows) == 4
    assert by_family["longitudinal_collision_authority_effectiveness_gap"]["implementation_admission_recommended"] is True
    assert by_family["lateral_collision_clearance_authority_effectiveness_gap"]["implementation_admission_recommended"] is True
    assert by_family["boundary_recovery_override_authority_effectiveness_gap"]["implementation_admission_recommended"] is True
    assert by_family["action_effectiveness_saturation_guard"]["implementation_admission_recommended"] is False
    assert by_family["action_effectiveness_saturation_guard"]["admission_role"] == "cross_cutting_guard_only"
    assert all(row["implementation_allowed_now"] is False for row in rows)
    assert all(row["actor_runtime_input_contract"] == "obs72_only_direct_action3" for row in rows)
    assert all("ttc_oracle" in row["forbidden_actor_inputs"] for row in rows)


def test_contract_guards_claims_and_gates_accept_complete_pack():
    source = _source()
    admissions = m3201.action_authority_effectiveness_admission_rows(source)
    guards = m3201.contract_guard_rows(source, admissions)
    claims = m3201.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3201.gate_matrix_rows(
        source=source,
        admissions=admissions,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in guards)
    assert all(row["status_pass"] for row in claims)
    assert all(row["status_pass"] for row in gates)


def test_claim_rows_reject_validation_repair_success_public_mutation_and_self_id():
    claims = m3201.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in claims}

    assert by_id["m3201-action_authority_effectiveness_admission_rows"]["claim_made"] is True
    assert by_id["m3201-validation_result"]["claim_made"] is False
    assert by_id["m3201-repair_success"]["claim_made"] is False
    assert by_id["m3201-public_driver_default_mutation"]["claim_made"] is False
    assert by_id["m3201-self_id"]["claim_made"] is False
    assert all(row["status_pass"] for row in claims)


def test_follow_up_manifest_is_m3202_process_audit(tmp_path):
    manifest = m3201.build_follow_up_manifest(output_dir=tmp_path / "m3201", doc_path=tmp_path / "m3201.md")

    assert manifest["id"] == m3201.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_action_authority_effectiveness_admission_result_audit_doc",
            "command": "true",
        }
    ]
