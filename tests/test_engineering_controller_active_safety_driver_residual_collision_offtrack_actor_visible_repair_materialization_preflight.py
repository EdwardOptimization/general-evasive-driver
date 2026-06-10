import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight as m3110
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)


def _requirements():
    families = [
        ("m3108-requirement-0001", "collision_lateral_intrusion_guard", 3),
        ("m3108-requirement-0002", "offtrack_boundary_recovery_guard", 4),
        ("m3108-requirement-0003", "speed_floor_preservation", 0),
        ("m3108-requirement-0004", "residual_collision_reduction", 5),
        ("m3108-requirement-0005", "residual_offtrack_recovery", 2),
        ("m3108-requirement-0006", "deployable_actor_boundary", 7),
        ("m3108-requirement-0007", "claim_boundary_audit", 7),
    ]
    return [
        {
            "requirement_id": requirement_id,
            "requirement_family": family,
            "priority": "p0",
            "affected_group": family,
            "row_count": str(row_count),
        }
        for requirement_id, family, row_count in families
    ]


def test_residual_policy_preserves_direct_action_contract():
    obs = np.zeros(m3110.P0_OBSERVATION_DIM, dtype=np.float32)
    action = m3110.residual_collision_offtrack_actor_visible_direct_action(obs)

    assert action.shape == (m3110.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert m3110.M3110_POLICY_CONFIG["policy_id"] == m3110.POLICY_ID
    assert m3110.M3110_POLICY_CONFIG["runtime_base_policy_required"] is False
    assert m3110.M3110_POLICY_CONFIG["checkpoint_model_required"] is False
    assert m3110.M3110_POLICY_CONFIG["recurrent_hidden_state_required"] is False
    assert m3110.M3110_POLICY_CONFIG["output_components"] == list(m3110.ACTION_COMPONENTS)


def test_residual_overlay_preserves_low_speed_throttle_and_adds_high_speed_brake():
    low_obs = m3110._probe_observation(speed_mps=3.0, obstacle=True)
    low_v4 = v4_v2_fallback_no_regression_hard_safety_direct_action(low_obs, V4_POLICY_CONFIG)
    low_m3110 = m3110.residual_collision_offtrack_actor_visible_direct_action(low_obs)

    high_obs = m3110._probe_observation(speed_mps=18.0, obstacle=True)
    high_v4 = v4_v2_fallback_no_regression_hard_safety_direct_action(high_obs, V4_POLICY_CONFIG)
    high_m3110 = m3110.residual_collision_offtrack_actor_visible_direct_action(high_obs)

    assert low_m3110[1] >= low_v4[1] - 1e-6
    assert high_m3110[2] >= high_v4[2] - 1e-6
    assert np.max(np.abs(high_m3110)) <= 1.0


def test_residual_repair_guards_cover_m3108_requirements():
    rows = m3110.build_residual_repair_guard_rows(_requirements())
    by_family = {row["requirement_family"]: row for row in rows}

    assert len(rows) == 7
    assert by_family["collision_lateral_intrusion_guard"]["status_pass"] is True
    assert by_family["offtrack_boundary_recovery_guard"]["status_pass"] is True
    assert by_family["speed_floor_preservation"]["preserves_speed_floor"] is True
    assert all(row["runtime_base_policy_required"] is False for row in rows)
    assert all(row["hidden_oracle_actor_input_required"] is False for row in rows)


def test_claim_boundary_blocks_measurement_and_repair_success():
    rows = m3110.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3110-follow_up_result_audit_registered"]["allowed_in_m3110"] is True
    assert by_id["m3110-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3110-rollout_measurement"]["allowed_in_m3110"] is False
    assert by_id["m3110-rollout_measurement"]["claim_made"] is False
    assert by_id["m3110-repair_success"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_audit_not_measurement(tmp_path):
    manifest = m3110.build_follow_up_manifest(
        output_dir=tmp_path / "m3110",
        doc_path=tmp_path / "m3110.md",
    )

    assert manifest["id"] == m3110.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_repair_materialization_result_audit_doc",
            "command": "true",
        }
    ]
    assert "measurement" in manifest["forbidden_shortcuts"][0]
    assert "repair-success" in manifest["hypothesis"]
