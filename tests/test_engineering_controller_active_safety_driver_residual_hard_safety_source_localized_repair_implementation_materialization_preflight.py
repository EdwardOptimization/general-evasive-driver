import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_preflight as m3170


def test_neutral_and_low_speed_paths_preserve_incumbent_exactly():
    zero = np.zeros(m3170.P0_OBSERVATION_DIM, dtype=np.float32)
    low_speed_obstacle = zero.copy()
    low_speed_obstacle[0] = 0.25
    low_speed_obstacle[44] = 1.0
    low_speed_obstacle[45] = 0.2
    low_speed_obstacle[46] = 0.02

    for obs in [zero, low_speed_obstacle]:
        fallback = m3170.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m3170.V4_POLICY_CONFIG)
        candidate = m3170.source_localized_repair_direct_action(obs, m3170.POLICY_CONFIG)
        features = m3170.source_localized_repair_features(obs, m3170.POLICY_CONFIG)

        assert max(features["collision_alpha"], features["boundary_alpha"]) == 0.0
        np.testing.assert_array_equal(candidate, fallback)


def test_collision_overlay_uses_visible_obstacle_and_limits_delta():
    obs = np.zeros(m3170.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.85
    obs[44] = 1.0
    obs[45] = 0.24
    obs[46] = 0.05
    obs[13:28:2] = 0.25
    obs[29:44:2] = -0.25

    fallback = m3170.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m3170.V4_POLICY_CONFIG)
    candidate = m3170.source_localized_repair_direct_action(obs, m3170.POLICY_CONFIG)
    features = m3170.source_localized_repair_features(obs, m3170.POLICY_CONFIG)
    delta = candidate - fallback
    overlay = m3170.POLICY_CONFIG["source_localized_overlay"]

    assert features["collision_alpha"] > 0.0
    assert features["boundary_alpha"] == 0.0
    assert candidate.shape == (m3170.ACTION_DIM,)
    assert np.all(np.isfinite(candidate))
    assert np.max(np.abs(candidate)) <= 1.0
    assert candidate[1] <= fallback[1]
    assert candidate[2] >= fallback[2]
    assert abs(float(delta[0])) <= overlay["max_abs_steer_delta"] + 1e-6
    assert -overlay["max_throttle_drop"] - 1e-6 <= float(delta[1]) <= 1e-6
    assert -1e-6 <= float(delta[2]) <= 2.0 * overlay["max_brake_add"] + 1e-6


def test_boundary_overlay_uses_edge_and_stability_without_hidden_inputs():
    obs = np.zeros(m3170.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.82
    obs[12:28] = 0.02
    obs[28:44] = 0.03
    obs[1] = 0.35
    obs[2] = 0.25
    obs[4] = 0.35

    fallback = m3170.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m3170.V4_POLICY_CONFIG)
    candidate = m3170.source_localized_repair_direct_action(obs, m3170.POLICY_CONFIG)
    features = m3170.source_localized_repair_features(obs, m3170.POLICY_CONFIG)

    assert features["boundary_alpha"] > 0.0
    assert features["collision_alpha"] == 0.0
    assert candidate[1] <= fallback[1]
    assert candidate[2] >= fallback[2]
    assert np.max(np.abs(candidate)) <= 1.0


def test_runtime_contract_and_claim_boundary_keep_public_driver_unmutated():
    contracts = m3170.runtime_contract_rows()
    claims = m3170.claim_boundary_rows(follow_up_manifest_registered=True)
    by_claim = {row["claim_id"]: row for row in claims}

    assert contracts == [
        {
            "contract_id": "m3170-runtime-contract-0001",
            "contract_family": "runtime_api",
            "runtime_symbol": "source_localized_repair_direct_action",
            "input_contract": "actor_visible_obs72_only",
            "output_contract": "direct_action3",
            "observation_shape": m3170.P0_OBSERVATION_DIM,
            "action_shape": m3170.ACTION_DIM,
            "action_components": "|".join(m3170.ACTION_COMPONENTS),
            "output_semantics": m3170.OUTPUT_SEMANTICS,
            "fallback_policy_id": m3170.M3103_POLICY_ID,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "public_driver_default_mutated": False,
            "status_pass": True,
            "claim_boundary": m3170.CLAIM_SCOPE,
        }
    ]
    assert by_claim["m3170-repair_success"]["allowed_in_m3170"] is False
    assert by_claim["m3170-repair_success"]["claim_made"] is False
    assert by_claim["m3170-public_driver_default_replacement"]["claim_made"] is False
    assert by_claim["m3170-level3_self_identification"]["claim_made"] is False


def test_gate_matrix_accepts_materialization_only_with_audited_admission():
    source = {
        "source_exists": {
            "m3169_audit": True,
            "m3168_summary": True,
            "m3168_repair_hypothesis_rows": True,
            "m3168_actor_contract_guard_rows": True,
            "m3168_measurement_readiness_rows": True,
            "m3168_gate_rows": True,
        },
        "m3169_audit_text": "accept_m3168_repair_admission_route_to_m3170_source_localized_repair_implementation_materialization",
        "m3168_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "implementation_admitted_hypothesis_count": 2,
            "validation_admitted_hypothesis_count": 0,
        },
    }
    rules = m3170.rule_rows()
    contracts = m3170.runtime_contract_rows()
    bindings = [
        {
            "binding_id": "binding-1",
            "status_pass": True,
        },
        {
            "binding_id": "binding-2",
            "status_pass": True,
        },
    ]
    probes = m3170.action_probe_rows()
    claims = m3170.claim_boundary_rows(follow_up_manifest_registered=True)

    rows = m3170.gate_matrix_rows(
        source=source,
        rules=rules,
        contracts=contracts,
        bindings=bindings,
        probes=probes,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )
    by_id = {row["gate_id"]: row for row in rows}

    assert by_id["m3170-m3169_selects_m3170"]["status_pass"] is True
    assert by_id["m3170-m3168_implementation_admitted_hypotheses"]["status_pass"] is True
    assert by_id["m3170-m3168_validation_admitted_hypotheses_zero"]["status_pass"] is True
    assert by_id["m3170-bindings_pass"]["status_pass"] is True
    assert by_id["m3170-overlay_probes_present"]["status_pass"] is True
    assert by_id["m3170-public_driver_default_unchanged"]["status_pass"] is True


def test_follow_up_manifest_is_audit_before_measurement():
    manifest = m3170.build_follow_up_manifest(
        output_dir=m3170.DEFAULT_OUTPUT_DIR,
        doc_path=m3170.DEFAULT_DOC_PATH,
    )

    assert manifest["id"] == m3170.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_source_localized_repair_implementation_result_audit_doc",
            "command": "true",
        }
    ]
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_hard_safety_failure_source_resolution"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert "measurement" in manifest["public_gates"][3]
    assert "validation" in manifest["forbidden_shortcuts"][1]


def test_action_rejects_wrong_shape_and_non_finite_observation():
    with np.testing.assert_raises(ValueError):
        m3170.source_localized_repair_direct_action(
            np.zeros(m3170.P0_OBSERVATION_DIM - 1, dtype=np.float32)
        )

    bad = np.zeros(m3170.P0_OBSERVATION_DIM, dtype=np.float32)
    bad[0] = np.nan
    with np.testing.assert_raises(ValueError):
        m3170.source_localized_repair_direct_action(bad)
