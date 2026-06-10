import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight as m3142


def test_safe_and_low_speed_paths_preserve_m3105_fallback_exactly():
    zero = np.zeros(m3142.P0_OBSERVATION_DIM, dtype=np.float32)
    low_speed = zero.copy()
    low_speed[0] = 0.25

    for obs in [zero, low_speed]:
        fallback = m3142.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m3142.V4_POLICY_CONFIG)
        candidate = m3142.residual_trajectory_timing_speed_envelope_action(obs, m3142.POLICY_CONFIG)
        features = m3142.speed_envelope_features(obs, m3142.POLICY_CONFIG)

        assert features["overlay_alpha"] == 0.0
        np.testing.assert_array_equal(candidate, fallback)


def test_high_speed_obstacle_overlay_is_bounded_deceleration_not_blanket_brake():
    obs = np.zeros(m3142.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.9
    obs[44] = 1.0
    obs[45] = 0.28
    obs[46] = 0.03

    fallback = m3142.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m3142.V4_POLICY_CONFIG)
    candidate = m3142.residual_trajectory_timing_speed_envelope_action(obs, m3142.POLICY_CONFIG)
    features = m3142.speed_envelope_features(obs, m3142.POLICY_CONFIG)
    delta = candidate - fallback
    env = m3142.POLICY_CONFIG["speed_envelope"]

    assert features["overlay_alpha"] > 0.0
    assert candidate.shape == (m3142.ACTION_DIM,)
    assert np.all(np.isfinite(candidate))
    assert np.max(np.abs(candidate)) <= 1.0
    assert candidate[1] <= fallback[1]
    assert candidate[2] >= fallback[2]
    assert abs(float(delta[0])) <= env["max_abs_steer_delta"] + 1e-6
    assert -env["max_throttle_drop"] - 1e-6 <= float(delta[1]) <= 1e-6
    assert 0.0 <= float(delta[2]) <= 2.0 * env["max_brake_add"] + 1e-6
    assert candidate[2] < 1.0


def test_runtime_contract_and_claim_boundary_reject_hidden_inputs_and_overclaims():
    contracts = m3142.runtime_contract_rows()
    claims = m3142.claim_boundary_rows(follow_up_manifest_registered=True)
    by_claim = {row["claim_id"]: row for row in claims}

    assert contracts == [
        {
            "contract_id": "m3142-runtime-contract-0001",
            "contract_family": "runtime_api",
            "runtime_symbol": "residual_trajectory_timing_speed_envelope_action",
            "input_contract": "actor_visible_obs72_only",
            "output_contract": "direct_action3",
            "observation_shape": m3142.P0_OBSERVATION_DIM,
            "action_shape": m3142.ACTION_DIM,
            "action_components": "|".join(m3142.ACTION_COMPONENTS),
            "output_semantics": m3142.OUTPUT_SEMANTICS,
            "fallback_policy_id": m3142.M3103_POLICY_ID,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "status_pass": True,
            "claim_boundary": m3142.CLAIM_SCOPE,
        }
    ]
    assert by_claim["m3142-repair_success"]["allowed_in_m3142"] is False
    assert by_claim["m3142-repair_success"]["claim_made"] is False
    assert by_claim["m3142-validation_result"]["allowed_in_m3142"] is False
    assert by_claim["m3142-level3_self_identification"]["claim_made"] is False


def test_gate_matrix_accepts_materialization_only_when_sources_and_probe_contract_pass():
    source = {
        "source_exists": {"m3141_synthesis": True, "m3139_summary": True, "m3139_residual_blocker_rows": True, "m3105_summary": True},
        "m3141_synthesis_text": "pivot_to_m3142_residual_trajectory_timing_speed_envelope_materialization",
        "m3139_summary": {"status_pass": True},
        "m3105_summary": {"status_pass": True},
    }
    rules = m3142.rule_rows()
    contracts = m3142.runtime_contract_rows()
    probes = m3142.action_probe_rows()
    requirements = [{"requirement_id": f"req-{index}"} for index in range(7)]
    claims = m3142.claim_boundary_rows(follow_up_manifest_registered=True)

    rows = m3142.gate_matrix_rows(
        source=source,
        rules=rules,
        contracts=contracts,
        probes=probes,
        requirements=requirements,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )
    by_id = {row["gate_id"]: row for row in rows}

    assert by_id["m3142-m3141_selects_m3142"]["status_pass"] is True
    assert by_id["m3142-fallback_probes_preserve_m3105_action"]["status_pass"] is True
    assert by_id["m3142-overlay_probes_present"]["status_pass"] is True
    assert by_id["m3142-action_probe_deltas_limited"]["status_pass"] is True
    assert by_id["m3142-claim_boundary_pass"]["status_pass"] is True


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3142.build_follow_up_manifest(output_dir=tmp_path / "m3142", doc_path=tmp_path / "m3142.md")

    assert manifest["id"] == m3142.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_trajectory_timing_speed_envelope"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]


def test_action_rejects_wrong_shape():
    with np.testing.assert_raises(ValueError):
        m3142.residual_trajectory_timing_speed_envelope_action(
            np.zeros(m3142.P0_OBSERVATION_DIM - 1, dtype=np.float32)
        )
