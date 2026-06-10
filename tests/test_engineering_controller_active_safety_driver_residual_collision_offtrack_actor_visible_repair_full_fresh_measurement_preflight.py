import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_preflight as m3112


def test_m3112_policy_adapter_telemetry_preserves_direct_action_contract():
    policy = m3112.M3112RepairMeasurementPolicy()
    action = policy.act(np.zeros(m3112.P0_OBSERVATION_DIM, dtype=np.float32), {})
    telemetry = policy.telemetry()

    assert action.shape == (m3112.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert telemetry["runtime_driver_id"] == m3112.POLICY_ID
    assert telemetry["candidate_output_semantics"] == m3112.OUTPUT_SEMANTICS
    assert telemetry["runtime_base_policy_required"] is False
    assert telemetry["checkpoint_model_required"] is False
    assert telemetry["recurrent_hidden_state_required"] is False
    assert telemetry["direct_action_step_count"] == 1


def test_same_row_comparison_records_four_baselines_without_claims():
    episode = {
        "runtime_smoke_episode_id": "m3112-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "policy": "m3112",
        "success": True,
        "collision": False,
        "termination_reason": "",
        "outcome_bucket": "success_obstacle_pass",
        "min_clearance_margin": "4.0",
        "return": "8.5",
        "speed_mean": "6.5",
        "action_rate_mean": "0.2",
    }
    m3105_baseline = {
        "runtime_smoke_episode_id": "m3105-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "policy": "m3105",
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
    m3095_baseline = dict(m3105_baseline)
    m3095_baseline["runtime_smoke_episode_id"] = "m3095-measurement-episode-0001"
    m3095_baseline["policy"] = "m3095"
    m3100_baseline = dict(m3105_baseline)
    m3100_baseline["runtime_smoke_episode_id"] = "m3100-measurement-episode-0001"
    m3100_baseline["policy"] = "m3100"
    m3100_baseline["success"] = True
    m3100_baseline["collision"] = False
    m3100_baseline["termination_reason"] = ""
    m3100_baseline["outcome_bucket"] = "success_obstacle_pass"
    m3100_baseline["min_clearance_margin"] = "3.0"
    m3090_baseline = {
        "runtime_smoke_episode_id": "m3090-runtime-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "policy": "m3090",
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

    rows = m3112.same_row_comparison_rows(
        [episode],
        [m3105_baseline],
        [m3095_baseline],
        [m3100_baseline],
        [m3090_baseline],
    )
    by_baseline = {row["baseline_id"]: row for row in rows}

    assert [row["comparison_id"] for row in rows] == [
        "m3112-same-row-comparison-0001",
        "m3112-same-row-comparison-0002",
        "m3112-same-row-comparison-0003",
        "m3112-same-row-comparison-0004",
    ]
    assert set(by_baseline) == {"m3105", "m3095", "m3100", "m3090"}
    assert by_baseline["m3105"]["success_delta"] == 1
    assert by_baseline["m3105"]["collision_delta"] == -1
    assert by_baseline["m3100"]["success_delta"] == 0
    assert by_baseline["m3100"]["clearance_margin_delta"] == 1.0
    assert by_baseline["m3090"]["speed_too_low_delta"] == -1
    assert by_baseline["m3105"]["exact_seed_match_m3105"] is True
    assert by_baseline["m3095"]["exact_seed_match_m3095"] is True
    assert by_baseline["m3100"]["exact_seed_match_m3100"] is True
    assert by_baseline["m3090"]["exact_seed_match_m3090"] is True
    assert all(row["comparison_claim_made"] is False for row in rows)
    assert all(row["repair_success_claim_made"] is False for row in rows)
    assert all(row["validation_run"] is False for row in rows)
    assert all(row["driver_performance_claim_made"] is False for row in rows)


def test_claim_boundary_blocks_repair_success_and_requires_m3113_audit():
    rows = m3112.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3112-follow_up_result_audit_registered"]["allowed_in_m3112"] is True
    assert by_id["m3112-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3112-repair_success"]["allowed_in_m3112"] is False
    assert by_id["m3112-repair_success"]["claim_made"] is False
    assert by_id["m3112-driver_performance_verdict"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3112.build_follow_up_manifest(
        output_dir=tmp_path / "m3112",
        doc_path=tmp_path / "m3112.md",
    )

    assert manifest["id"] == m3112.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_repair_full_fresh_measurement_result_audit_doc",
            "command": "true",
        }
    ]
    assert "repair-success" in manifest["hypothesis"]
    assert "validation" in manifest["forbidden_shortcuts"][1]
