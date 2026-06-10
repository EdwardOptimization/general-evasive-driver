import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_recovery_clearance_supervisor_architecture_materialization_preflight as m3208


def _source():
    return {
        "source_exists": {
            "m3207_synthesis": True,
            "m3205_summary": True,
            "m3205_comparison_rows": True,
            "m3205_gate_rows": True,
            "m3189_summary": True,
            "m3105_summary": True,
        },
        "m3207_synthesis_text": m3208.MILESTONE_ID,
        "m3205_summary": {
            "status_pass": True,
            "hard_safety_improved_vs_incumbent_count": 0,
            "outcome_changed_vs_incumbent_count": 0,
        },
        "m3205_comparison_rows": [],
        "m3205_gate_rows": [{"status_pass": "True"}],
        "m3189_summary": {"status_pass": True},
        "m3105_summary": {"status_pass": True},
    }


def test_supervisor_action_preserves_low_risk_fallback_and_bounds():
    observations = dict(m3208.probe_observations())
    low_risk = observations["low_risk_fallback_probe"]
    candidate = m3208.recovery_clearance_supervisor_candidate_action(low_risk)

    assert candidate.shape == (m3208.ACTION_DIM,)
    assert np.all(np.isfinite(candidate))
    assert np.max(np.abs(candidate)) <= 1.0
    assert np.allclose(
        candidate,
        m3208.v4_v2_fallback_no_regression_hard_safety_direct_action(low_risk, m3208.V4_POLICY_CONFIG),
    )


def test_action_probes_cover_recovery_clearance_modes():
    rows = m3208.action_probe_rows()
    by_family = {row["probe_family"]: row for row in rows}
    modes = {row["selected_mode"] for row in rows}

    assert len(rows) == 5
    assert by_family["low_risk_fallback_probe"]["fallback_path_selected"] is True
    assert {"collision_clearance_supervision", "boundary_recovery_supervision", "stability_recovery_supervision"}.issubset(
        modes
    )
    high_risk = [row for row in rows if not row["fallback_path_selected"]]
    assert len(high_risk) == 4
    assert all(row["action_finite"] and row["action_bounded"] and row["delta_limited"] for row in rows)
    assert by_family["collision_clearance_probe"]["candidate_brake"] >= by_family["collision_clearance_probe"]["fallback_brake"]
    assert by_family["collision_clearance_probe"]["candidate_throttle"] <= by_family["collision_clearance_probe"]["fallback_throttle"]
    assert by_family["boundary_recovery_probe"]["candidate_brake"] >= by_family["boundary_recovery_probe"]["fallback_brake"]


def test_modes_contracts_and_claims_preserve_public_driver_boundary():
    modes = m3208.supervisor_mode_rows()
    features = m3208.feature_contract_rows()
    contracts = m3208.runtime_contract_rows()
    claims = m3208.claim_boundary_rows(follow_up_manifest_registered=True)

    assert {row["mode_family"] for row in modes} == {
        "fallback",
        "collision_clearance_supervision",
        "boundary_recovery_supervision",
        "stability_recovery_supervision",
        "action_budget_guard",
    }
    assert not any(row["public_driver_default_mutated"] for row in modes + contracts)
    assert all(row["runtime_base_policy_required"] is False for row in modes + features + contracts)
    assert all(row["hidden_oracle_actor_input_required"] is False for row in modes + features + contracts)
    assert all(row["status_pass"] for row in features + contracts)
    assert all(row["status_pass"] for row in claims)
    assert not any(row["claim_made"] for row in claims if row["claim_family"] == "forbidden")


def test_gate_matrix_accepts_complete_supervisor_pack():
    modes = m3208.supervisor_mode_rows()
    features = m3208.feature_contract_rows()
    contracts = m3208.runtime_contract_rows()
    probes = m3208.action_probe_rows()
    claims = m3208.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3208.gate_matrix_rows(
        source=_source(),
        modes=modes,
        features=features,
        contracts=contracts,
        probes=probes,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_m3209_result_audit(tmp_path):
    manifest = m3208.build_follow_up_manifest(output_dir=tmp_path / "m3208", doc_path=tmp_path / "m3208.md")

    assert manifest["id"] == m3208.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
