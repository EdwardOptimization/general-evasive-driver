import autodrift.engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_validation_spec_materialization_preflight as m3159


def _source():
    return {
        "m3158_plan_text": "route_to_m3159_validation_spec_materialization_preflight",
        "source_exists": {
            "m3158_plan": True,
            "m3156_summary": True,
            "m3156_contract_snapshot": True,
            "m3156_pack_manifest": True,
            "m3156_metric_rows": True,
            "m3156_failure_rows": True,
            "m3156_gate_rows": True,
        },
        "m3156_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "m3105_measurement_episode_row_count": 64,
            "m3105_success_count": 57,
            "m3105_collision_count": 5,
            "m3105_offtrack_count": 2,
            "m3105_speed_too_low_count": 0,
            "known_failure_taxonomy_row_count": 7,
            "m3153_comparison_count": 21,
            "m3153_action_channel_sensitive_comparison_count": 0,
        },
        "m3156_contract_snapshot": {
            "driver_contract": {
                "observation_shape": 72,
                "action_shape": 3,
                "action_components": ["steer", "throttle", "brake"],
                "runtime_base_policy_required": False,
            }
        },
        "m3156_metric_rows": [
            {"metric_name": "measurement_episode_count", "value": "64"},
            {"metric_name": "m3153_comparison_count", "value": "21"},
            {"metric_name": "m3153_action_channel_sensitive_count", "value": "0"},
        ],
        "m3156_failure_rows": [
            {"blocker_family": "collision", "axis_id": "collision_lateral_intrusion"},
            {"blocker_family": "collision", "axis_id": "collision_lateral_intrusion"},
            {"blocker_family": "collision", "axis_id": "offtrack_boundary_recovery"},
            {"blocker_family": "collision", "axis_id": "offtrack_boundary_recovery"},
            {"blocker_family": "collision", "axis_id": "offtrack_boundary_recovery"},
            {"blocker_family": "offtrack", "axis_id": "collision_lateral_intrusion"},
            {"blocker_family": "offtrack", "axis_id": "offtrack_boundary_recovery"},
        ],
    }


def test_validation_denominator_rows_preserve_pack_denominators():
    rows = m3159.validation_denominator_rows(_source())
    by_id = {row["denominator_id"]: row for row in rows}

    assert len(rows) == 5
    assert by_id["m3159-m3105-full-fresh-current-sim-denominator"]["source_row_count"] == 64
    assert by_id["m3159-known-residual-failure-taxonomy"]["known_blocker_count"] == 7
    assert by_id["m3159-known-residual-failure-taxonomy"]["collision_count"] == 5
    assert by_id["m3159-known-residual-failure-taxonomy"]["offtrack_count"] == 2
    assert by_id["m3159-m3153-negative-replay-diagnostic"]["source_row_count"] == 21
    assert all(row["execution_in_m3159"] is False for row in rows)


def test_validation_gate_specs_block_overclaiming_and_require_contract():
    rows = m3159.validation_gate_spec_rows(_source())
    by_name = {row["gate_name"]: row for row in rows}

    assert by_name["obs72_input_shape"]["threshold"] == 72
    assert by_name["action3_output_shape"]["threshold"] == 3
    assert by_name["direct_action_components"]["threshold"] == "steer|throttle|brake"
    assert by_name["m3105_full_fresh_rows"]["threshold"] == 64
    assert by_name["known_residual_blocker_rows"]["threshold"] == 7
    assert by_name["validation_result_claim_blocked_in_m3159"]["threshold"] is True
    assert all(row["execution_in_m3159"] is False for row in rows)


def test_claim_boundary_blocks_validation_performance_and_repair_claims():
    rows = m3159.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3159-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3159-validation_result"]["allowed_in_m3159"] is False
    assert by_id["m3159-driver_performance_verdict"]["claim_made"] is False
    assert by_id["m3159-repair_success"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_gate_matrix_accepts_complete_claim_safe_specs():
    source = _source()
    denominator_rows = m3159.validation_denominator_rows(source)
    gate_spec_rows = m3159.validation_gate_spec_rows(source)
    reporting_rows = m3159.validation_reporting_artifact_rows()
    claim_rows = m3159.claim_boundary_rows(follow_up_manifest_registered=True)

    gates = m3159.gate_matrix_rows(
        source=source,
        denominator_rows=denominator_rows,
        gate_spec_rows=gate_spec_rows,
        reporting_rows=reporting_rows,
        claim_rows=claim_rows,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_process_audit_not_validation(tmp_path):
    manifest = m3159.build_follow_up_manifest(output_dir=tmp_path / "m3159", doc_path=tmp_path / "m3159.md")

    assert manifest["id"] == m3159.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_route_a_deployable_benchmark_pack_validation_spec_result_audit_doc",
            "command": "true",
        }
    ]
