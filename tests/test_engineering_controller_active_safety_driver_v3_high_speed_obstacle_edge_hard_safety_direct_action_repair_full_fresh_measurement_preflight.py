import numpy as np

import autodrift.engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight as m3100


def test_v3_policy_adapter_telemetry_preserves_direct_action_contract():
    policy = m3100.V3RepairMeasurementPolicy()
    action = policy.act(np.zeros(m3100.P0_OBSERVATION_DIM, dtype=np.float32), {})
    telemetry = policy.telemetry()

    assert action.shape == (m3100.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert telemetry["runtime_driver_id"] == m3100.POLICY_ID
    assert telemetry["candidate_output_semantics"] == m3100.OUTPUT_SEMANTICS
    assert telemetry["runtime_base_policy_required"] is False
    assert telemetry["checkpoint_model_required"] is False
    assert telemetry["recurrent_hidden_state_required"] is False
    assert telemetry["direct_action_step_count"] == 1


def test_same_row_comparison_records_deltas_without_claims():
    episode = {
        "runtime_smoke_episode_id": "m3100-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "speed_floor_stress",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "policy": "v3",
        "success": True,
        "collision": False,
        "termination_reason": "",
        "outcome_bucket": "success_obstacle_pass",
        "min_clearance_margin": "4.0",
        "return": "8.5",
        "speed_mean": "6.5",
        "action_rate_mean": "0.2",
    }
    m3095_baseline = {
        "runtime_smoke_episode_id": "m3095-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "policy": "v2",
        "success": False,
        "collision": True,
        "termination_reason": "obstacle_collision",
        "outcome_bucket": "collision_failure",
        "min_clearance_margin": "-0.5",
        "return": "-2.0",
        "speed_mean": "9.0",
        "action_rate_mean": "0.4",
        "eval_seed": "123",
    }
    m3090_baseline = {
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

    rows = m3100.same_row_comparison_rows([episode], [m3095_baseline], [m3090_baseline])
    assert rows == [
        {
            "comparison_id": "m3100-same-row-comparison-0001",
            "measurement_episode_id": "m3100-measurement-episode-0001",
            "m3095_episode_id": "m3095-measurement-episode-0001",
            "m3090_episode_id": "m3090-runtime-measurement-episode-0001",
            "source_measurement_episode_id": "m3084-measurement-episode-0001",
            "fresh_panel_row_id": "fresh-1",
            "axis_id": "speed_floor_stress",
            "binding_role": "candidate",
            "task_family": "T5",
            "eval_seed": "123",
            "m3100_policy": "v3",
            "m3095_policy": "v2",
            "m3090_policy": "v1",
            "m3100_success": True,
            "m3095_success": False,
            "m3090_success": False,
            "success_delta_vs_m3095": 1,
            "success_delta_vs_m3090": 1,
            "m3100_collision": False,
            "m3095_collision": True,
            "m3090_collision": False,
            "collision_delta_vs_m3095": -1,
            "collision_delta_vs_m3090": 0,
            "m3100_offtrack": False,
            "m3095_offtrack": False,
            "m3090_offtrack": False,
            "offtrack_delta_vs_m3095": 0,
            "offtrack_delta_vs_m3090": 0,
            "m3100_speed_too_low": False,
            "m3095_speed_too_low": False,
            "m3090_speed_too_low": True,
            "speed_too_low_delta_vs_m3095": 0,
            "speed_too_low_delta_vs_m3090": -1,
            "m3100_termination_reason": "",
            "m3095_termination_reason": "obstacle_collision",
            "m3090_termination_reason": "speed_too_low",
            "termination_reason_match_vs_m3095": False,
            "termination_reason_match_vs_m3090": False,
            "m3100_outcome_bucket": "success_obstacle_pass",
            "m3095_outcome_bucket": "collision_failure",
            "m3090_outcome_bucket": "speed_too_low_noncollision_noncompletion",
            "outcome_bucket_match_vs_m3095": False,
            "outcome_bucket_match_vs_m3090": False,
            "m3100_min_clearance_margin": "4.0",
            "m3095_min_clearance_margin": "-0.5",
            "m3090_min_clearance_margin": "3.5",
            "clearance_margin_delta_vs_m3095": 4.5,
            "clearance_margin_delta_vs_m3090": 0.5,
            "m3100_return": "8.5",
            "m3095_return": "-2.0",
            "m3090_return": "1.5",
            "return_delta_vs_m3095": 10.5,
            "return_delta_vs_m3090": 7.0,
            "m3100_speed_mean": "6.5",
            "m3095_speed_mean": "9.0",
            "m3090_speed_mean": "4.0",
            "speed_mean_delta_vs_m3095": -2.5,
            "speed_mean_delta_vs_m3090": 2.5,
            "m3100_action_rate_mean": "0.2",
            "m3095_action_rate_mean": "0.4",
            "m3090_action_rate_mean": "0.1",
            "action_rate_delta_vs_m3095": -0.2,
            "action_rate_delta_vs_m3090": 0.1,
            "exact_seed_match_m3095": True,
            "exact_seed_match_m3090": True,
            "comparison_claim_made": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": m3100.CLAIM_SCOPE,
        }
    ]


def test_claim_boundary_blocks_repair_success_and_requires_m3101_audit():
    rows = m3100.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3100-follow_up_result_audit_registered"]["allowed_in_m3100"] is True
    assert by_id["m3100-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3100-repair_success"]["allowed_in_m3100"] is False
    assert by_id["m3100-repair_success"]["claim_made"] is False
    assert by_id["m3100-driver_performance_verdict"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3100.build_follow_up_manifest(
        output_dir=tmp_path / "m3100",
        doc_path=tmp_path / "m3100.md",
    )

    assert manifest["id"] == m3100.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_repair_full_fresh_measurement_result_audit_doc",
            "command": "true",
        }
    ]
    assert "repair-success" in manifest["hypothesis"]
    assert "validation" in manifest["forbidden_shortcuts"][1]
