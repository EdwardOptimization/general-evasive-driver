import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_steer_delta_regression_guard_materialization_preflight as m3179


def _source():
    return {
        "source_exists": {
            "m3178_audit": True,
            "m3177_summary": True,
            "m3177_ablation_variant_rows": True,
            "m3177_gate_rows": True,
            "m3170_summary": True,
            "m3170_policy_config": True,
            "m3170_gate_rows": True,
            "m3105_summary": True,
        },
        "m3178_audit_text": "accept_m3177_trace_ablation_route_to_m3179_steer_delta_regression_guard_materialization",
        "m3177_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3177_ablation_variant_rows": [
            {"variant_id": "m3177_incumbent_m3105", "success": "True", "collision": "False"},
            {"variant_id": "m3177_candidate_m3170", "success": "False", "collision": "True"},
            {"variant_id": "m3177_ablate_steer_delta", "success": "True", "collision": "False"},
            {"variant_id": "m3177_ablate_throttle_drop", "success": "False", "collision": "True"},
            {"variant_id": "m3177_ablate_brake_add", "success": "False", "collision": "True"},
        ],
        "m3177_gate_rows": [{"status_pass": True}],
        "m3170_summary": {"status_pass": True},
        "m3170_policy_config": {},
        "m3170_gate_rows": [{"status_pass": True}],
        "m3105_summary": {"status_pass": True},
    }


def _active_observation():
    obs = np.zeros(m3179.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.7
    obs[12:28].reshape(8, 2)[:, 1] = 0.3
    obs[28:44].reshape(8, 2)[:, 1] = -0.3
    obs[44] = 1.0
    obs[45] = 0.1
    obs[46] = 0.0
    return obs


def test_guard_direct_action_zeroes_steer_delta_and_preserves_other_deltas():
    obs = _active_observation()
    fallback = m3179.fallback_action(obs)
    source = m3179.m3170_action(obs)
    guarded = m3179.steer_delta_regression_guard_direct_action(obs, m3179.POLICY_CONFIG)
    source_delta = source - fallback
    guarded_delta = guarded - fallback

    assert np.linalg.norm(source_delta) > 0.1
    assert np.isclose(guarded_delta[0], 0.0)
    assert np.isclose(guarded_delta[1], source_delta[1])
    assert np.isclose(guarded_delta[2], source_delta[2])
    assert np.all(np.isfinite(guarded))
    assert float(np.max(np.abs(guarded))) <= 1.0


def test_action_probe_rows_capture_guard_contract():
    rows = m3179.action_probe_rows()

    assert len(rows) >= 2
    assert all(row["action_finite"] for row in rows)
    assert all(row["action_bounded"] for row in rows)
    assert all(row["steer_delta_guarded_to_zero"] for row in rows)
    assert all(row["throttle_delta_preserved"] for row in rows)
    assert all(row["brake_delta_preserved"] for row in rows)


def test_gate_matrix_accepts_complete_materialization_pack():
    source = _source()
    rules = m3179.rule_rows()
    contracts = m3179.runtime_contract_rows()
    probes = m3179.action_probe_rows()
    claims = m3179.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3179.gate_matrix_rows(
        source=source,
        rules=rules,
        contracts=contracts,
        probes=probes,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in contracts)
    assert all(row["status_pass"] for row in claims)
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3179.build_follow_up_manifest(output_dir=tmp_path / "m3179", doc_path=tmp_path / "m3179.md")

    assert manifest["id"] == m3179.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_behavior_negative_source_repair_decomposition"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_steer_delta_regression_guard_result_audit_doc",
            "command": "true",
        }
    ]
