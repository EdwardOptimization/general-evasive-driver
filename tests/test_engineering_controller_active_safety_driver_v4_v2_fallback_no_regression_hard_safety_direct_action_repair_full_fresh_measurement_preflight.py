import numpy as np

import autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight as m3105


def test_v4_policy_adapter_telemetry_preserves_direct_action_contract():
    policy = m3105.V4RepairMeasurementPolicy()
    action = policy.act(np.zeros(m3105.P0_OBSERVATION_DIM, dtype=np.float32), {})
    telemetry = policy.telemetry()

    assert action.shape == (m3105.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert telemetry["runtime_driver_id"] == m3105.POLICY_ID
    assert telemetry["candidate_output_semantics"] == m3105.OUTPUT_SEMANTICS
    assert telemetry["runtime_base_policy_required"] is False
    assert telemetry["checkpoint_model_required"] is False
    assert telemetry["recurrent_hidden_state_required"] is False
    assert telemetry["direct_action_step_count"] == 1


def test_same_row_comparison_records_three_baselines_without_claims():
    episode = {
        "runtime_smoke_episode_id": "m3105-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "speed_floor_stress",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "policy": "v4",
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
    m3100_baseline = {
        "runtime_smoke_episode_id": "m3100-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "policy": "v3",
        "success": True,
        "collision": False,
        "termination_reason": "",
        "outcome_bucket": "success_obstacle_pass",
        "min_clearance_margin": "3.0",
        "return": "7.0",
        "speed_mean": "6.0",
        "action_rate_mean": "0.25",
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

    rows = m3105.same_row_comparison_rows([episode], [m3095_baseline], [m3100_baseline], [m3090_baseline])
    by_baseline = {row["baseline_id"]: row for row in rows}

    assert [row["comparison_id"] for row in rows] == [
        "m3105-same-row-comparison-0001",
        "m3105-same-row-comparison-0002",
        "m3105-same-row-comparison-0003",
    ]
    assert set(by_baseline) == {"m3095", "m3100", "m3090"}
    assert by_baseline["m3095"]["baseline_episode_id"] == "m3095-measurement-episode-0001"
    assert by_baseline["m3095"]["success_delta"] == 1
    assert by_baseline["m3095"]["collision_delta"] == -1
    assert by_baseline["m3100"]["success_delta"] == 0
    assert by_baseline["m3100"]["clearance_margin_delta"] == 1.0
    assert by_baseline["m3090"]["speed_too_low_delta"] == -1
    assert by_baseline["m3095"]["exact_seed_match_m3095"] is True
    assert by_baseline["m3100"]["exact_seed_match_m3100"] is True
    assert by_baseline["m3090"]["exact_seed_match_m3090"] is True
    assert all(row["comparison_claim_made"] is False for row in rows)
    assert all(row["repair_success_claim_made"] is False for row in rows)
    assert all(row["validation_run"] is False for row in rows)
    assert all(row["driver_performance_claim_made"] is False for row in rows)


def test_claim_boundary_blocks_repair_success_and_requires_m3106_audit():
    rows = m3105.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3105-follow_up_result_audit_registered"]["allowed_in_m3105"] is True
    assert by_id["m3105-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3105-repair_success"]["allowed_in_m3105"] is False
    assert by_id["m3105-repair_success"]["claim_made"] is False
    assert by_id["m3105-driver_performance_verdict"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3105.build_follow_up_manifest(
        output_dir=tmp_path / "m3105",
        doc_path=tmp_path / "m3105.md",
    )

    assert manifest["id"] == m3105.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_full_fresh_measurement_result_audit_doc",
            "command": "true",
        }
    ]
    assert "repair-success" in manifest["hypothesis"]
    assert "validation" in manifest["forbidden_shortcuts"][1]
