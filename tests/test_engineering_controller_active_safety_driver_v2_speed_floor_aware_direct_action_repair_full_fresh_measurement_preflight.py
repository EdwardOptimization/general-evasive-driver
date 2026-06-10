import numpy as np

import autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight as m3095


def test_v2_policy_adapter_telemetry_preserves_direct_action_contract():
    policy = m3095.V2RepairMeasurementPolicy()
    action = policy.act(np.zeros(m3095.P0_OBSERVATION_DIM, dtype=np.float32), {})
    telemetry = policy.telemetry()

    assert action.shape == (m3095.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert telemetry["runtime_driver_id"] == m3095.POLICY_ID
    assert telemetry["candidate_output_semantics"] == m3095.OUTPUT_SEMANTICS
    assert telemetry["runtime_base_policy_required"] is False
    assert telemetry["checkpoint_model_required"] is False
    assert telemetry["recurrent_hidden_state_required"] is False
    assert telemetry["direct_action_step_count"] == 1


def test_same_row_comparison_records_deltas_without_claims():
    episode = {
        "runtime_smoke_episode_id": "m3095-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "speed_floor_stress",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "policy": "v2",
        "success": True,
        "collision": False,
        "termination_reason": "",
        "outcome_bucket": "success_obstacle_pass",
        "min_clearance_margin": "4.0",
        "return": "8.5",
        "speed_mean": "6.5",
        "action_rate_mean": "0.2",
    }
    baseline = {
        "runtime_smoke_episode_id": "m3090-runtime-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "policy": "v1",
        "success": False,
        "collision": False,
        "termination_reason": "speed_too_low",
        "outcome_bucket": "speed_too_low_noncollision_noncompletion",
        "min_clearance_margin": "3.5",
        "return": "1.5",
        "speed_mean": "4.0",
        "action_rate_mean": "0.1",
        "eval_seed": "123",
    }

    rows = m3095.same_row_comparison_rows([episode], [baseline])
    assert rows == [
        {
            "comparison_id": "m3095-same-row-comparison-0001",
            "measurement_episode_id": "m3095-measurement-episode-0001",
            "m3090_episode_id": "m3090-runtime-measurement-episode-0001",
            "source_measurement_episode_id": "m3084-measurement-episode-0001",
            "fresh_panel_row_id": "fresh-1",
            "axis_id": "speed_floor_stress",
            "binding_role": "candidate",
            "task_family": "T5",
            "eval_seed": "123",
            "m3095_policy": "v2",
            "m3090_policy": "v1",
            "m3095_success": True,
            "m3090_success": False,
            "success_delta": 1,
            "m3095_collision": False,
            "m3090_collision": False,
            "collision_delta": 0,
            "m3095_offtrack": False,
            "m3090_offtrack": False,
            "offtrack_delta": 0,
            "m3095_speed_too_low": False,
            "m3090_speed_too_low": True,
            "speed_too_low_delta": -1,
            "m3095_termination_reason": "",
            "m3090_termination_reason": "speed_too_low",
            "termination_reason_match": False,
            "m3095_outcome_bucket": "success_obstacle_pass",
            "m3090_outcome_bucket": "speed_too_low_noncollision_noncompletion",
            "outcome_bucket_match": False,
            "m3095_min_clearance_margin": "4.0",
            "m3090_min_clearance_margin": "3.5",
            "clearance_margin_delta": 0.5,
            "m3095_return": "8.5",
            "m3090_return": "1.5",
            "return_delta": 7.0,
            "m3095_speed_mean": "6.5",
            "m3090_speed_mean": "4.0",
            "speed_mean_delta": 2.5,
            "m3095_action_rate_mean": "0.2",
            "m3090_action_rate_mean": "0.1",
            "action_rate_delta": 0.1,
            "exact_seed_match": True,
            "comparison_claim_made": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": m3095.CLAIM_SCOPE,
        }
    ]


def test_claim_boundary_blocks_repair_success_and_requires_m3096_audit():
    rows = m3095.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3095-follow_up_result_audit_registered"]["allowed_in_m3095"] is True
    assert by_id["m3095-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3095-repair_success"]["allowed_in_m3095"] is False
    assert by_id["m3095-repair_success"]["claim_made"] is False
    assert by_id["m3095-driver_performance_verdict"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3095.build_follow_up_manifest(
        output_dir=tmp_path / "m3095",
        doc_path=tmp_path / "m3095.md",
    )

    assert manifest["id"] == m3095.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_v2_speed_floor_aware_repair_full_fresh_measurement_result_audit_doc",
            "command": "true",
        }
    ]
    assert "repair-success" in manifest["hypothesis"]
    assert "validation" in manifest["forbidden_shortcuts"][1]
