import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_admission_materialization_preflight as m3192


def _source():
    executions = []
    steps = []
    axes = [
        ("0001", "clearance_timing_axis", "collision", 29),
        ("0002", "clearance_timing_axis", "collision", 38),
        ("0003", "boundary_recovery_stability_axis", "offtrack", 52),
        ("0004", "boundary_recovery_stability_axis", "offtrack", 50),
        ("0005", "boundary_recovery_collision_axis", "collision", 36),
        ("0006", "boundary_recovery_collision_axis", "collision", 27),
        ("0007", "boundary_recovery_collision_axis", "collision", 23),
    ]
    for index, (suffix, axis, family, step_count) in enumerate(axes, start=1):
        execution_id = f"m3189-trace-execution-{suffix}"
        terminal = "off_track" if family == "offtrack" else "obstacle_collision"
        executions.append(
            {
                "trace_execution_id": execution_id,
                "trace_source_binding_id": f"m3187-trace-source-binding-{index:04d}",
                "evidence_axis": axis,
                "blocker_family": family,
                "steps": str(step_count),
                "termination_reason": terminal,
            }
        )
        for step in range(step_count):
            is_terminal_window = step >= step_count - 5
            steps.append(
                {
                    "trace_execution_id": execution_id,
                    "step_index": str(step),
                    "post_speed": "17.0" if family == "collision" else "14.5",
                    "relative_clearance_proxy": "-0.2" if family == "collision" and is_terminal_window else "1.0",
                    "post_lateral_error": "2.0" if family == "collision" else "5.0",
                    "post_beta": "0.3" if family == "collision" else "0.6",
                    "action_clip_hit": "True" if family == "collision" and is_terminal_window else "False",
                }
            )
    return {
        "source_exists": {
            "m3191_synthesis": True,
            "m3189_summary": True,
            "m3189_trace_execution_rows": True,
            "m3189_trace_step_rows": True,
            "m3189_gate_rows": True,
            "m3187_summary": True,
            "m3187_trace_spec_rows": True,
            "m3187_boundary_rows": True,
            "m3187_forbidden_label_guard_rows": True,
        },
        "m3191_synthesis_text": "m3192-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-admission-materialization-preflight",
        "m3189_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3189_trace_execution_rows": executions,
        "m3189_trace_step_rows": steps,
        "m3189_gate_rows": [{"status_pass": "True"}],
        "m3187_summary": {"status_pass": True},
        "m3187_trace_spec_rows": [],
        "m3187_boundary_rows": [],
        "m3187_forbidden_label_guard_rows": [],
    }


def test_implementation_admissions_keep_saturation_as_guard_only():
    rows = m3192.implementation_admission_rows(_source())
    by_family = {row["rule_family"]: row for row in rows}

    assert len(rows) == 3
    assert by_family["preterminal_clearance_authority_timing"]["source_trace_execution_count"] == 5
    assert by_family["boundary_stability_recovery_authority"]["source_trace_execution_count"] == 2
    assert by_family["preterminal_clearance_authority_timing"]["implementation_admission_recommended"] is True
    assert by_family["boundary_stability_recovery_authority"]["implementation_admission_recommended"] is True
    assert by_family["action_authority_saturation_guard"]["implementation_admission_recommended"] is False
    assert all(row["implementation_allowed_now"] is False for row in rows)
    assert all("ttc_oracle" in row["forbidden_actor_inputs"] for row in rows)


def test_rule_contracts_and_forbidden_labels_preserve_obs72_boundary():
    admissions = m3192.implementation_admission_rows(_source())
    contracts = m3192.rule_contract_rows(admissions)
    forbidden = m3192.forbidden_label_guard_rows()

    assert len(contracts) >= 9
    assert all(row["status_pass"] for row in contracts)
    assert all(row["runtime_actor_inputs"] == "obs72" for row in contracts)
    assert not any(row["public_driver_mutation_allowed"] for row in contracts)
    assert len(forbidden) >= 5
    assert not any(row["actor_runtime_allowed"] for row in forbidden)
    assert all(row["status_pass"] for row in forbidden)


def test_gate_matrix_accepts_complete_admission_pack():
    source = _source()
    admissions = m3192.implementation_admission_rows(source)
    contracts = m3192.rule_contract_rows(admissions)
    forbidden = m3192.forbidden_label_guard_rows()
    claims = m3192.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3192.gate_matrix_rows(
        source=source,
        admissions=admissions,
        contracts=contracts,
        forbidden_rows=forbidden,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3192.build_follow_up_manifest(output_dir=tmp_path / "m3192", doc_path=tmp_path / "m3192.md")

    assert manifest["id"] == m3192.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_admission_result_audit_doc",
            "command": "true",
        }
    ]
