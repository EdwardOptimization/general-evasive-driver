import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_implementation_materialization_preflight as m3194


def _source():
    return {
        "source_exists": {
            "m3193_audit": True,
            "m3192_summary": True,
            "m3192_admission_rows": True,
            "m3192_rule_contract_rows": True,
            "m3192_gate_rows": True,
            "m3189_summary": True,
            "m3189_trace_execution_rows": True,
            "m3105_summary": True,
        },
        "m3193_audit_text": "m3194-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-candidate-implementation-materialization-preflight",
        "m3192_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3192_admission_rows": [],
        "m3192_rule_contract_rows": [],
        "m3192_gate_rows": [{"status_pass": "True"}],
        "m3189_summary": {"status_pass": True},
        "m3189_trace_execution_rows": [],
        "m3105_summary": {"status_pass": True},
    }


def test_candidate_action_preserves_shape_bounds_and_low_risk_fallback():
    observations = dict(m3194.probe_observations())
    low_risk = observations["low_risk_fallback_probe"]
    candidate = m3194.preterminal_authority_boundary_stability_candidate_action(low_risk)

    assert candidate.shape == (m3194.ACTION_DIM,)
    assert np.all(np.isfinite(candidate))
    assert np.max(np.abs(candidate)) <= 1.0
    assert np.allclose(candidate, m3194.v4_v2_fallback_no_regression_hard_safety_direct_action(low_risk, m3194.V4_POLICY_CONFIG))


def test_action_probes_include_nontrivial_bounded_candidate_response():
    rows = m3194.action_probe_rows()
    by_family = {row["probe_family"]: row for row in rows}

    assert len(rows) >= 4
    assert by_family["low_risk_fallback_probe"]["fallback_path_selected"] is True
    assert by_family["preterminal_collision_probe"]["fallback_path_selected"] is False
    assert by_family["preterminal_collision_probe"]["candidate_throttle"] <= by_family["preterminal_collision_probe"]["fallback_throttle"]
    assert by_family["preterminal_collision_probe"]["candidate_brake"] >= by_family["preterminal_collision_probe"]["fallback_brake"]
    assert all(row["action_finite"] and row["action_bounded"] and row["delta_limited"] for row in rows)


def test_rules_contracts_and_claims_preserve_public_driver_boundary():
    rules = m3194.candidate_rule_rows()
    contracts = m3194.runtime_contract_rows()
    claims = m3194.claim_boundary_rows(follow_up_manifest_registered=True)

    assert {row["rule_family"] for row in rules} == {
        "preterminal_clearance_authority_timing",
        "boundary_stability_recovery_authority",
        "action_authority_saturation_guard",
    }
    assert not any(row["public_driver_default_mutated"] for row in rules + contracts)
    assert all(row["runtime_base_policy_required"] is False for row in rules + contracts)
    assert all(row["status_pass"] for row in contracts)
    assert all(row["status_pass"] for row in claims)
    assert not any(row["claim_made"] for row in claims if row["claim_family"] == "forbidden")


def test_gate_matrix_accepts_complete_candidate_pack():
    source = _source()
    rules = m3194.candidate_rule_rows()
    contracts = m3194.runtime_contract_rows()
    probes = m3194.action_probe_rows()
    claims = m3194.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3194.gate_matrix_rows(
        source=source,
        rules=rules,
        contracts=contracts,
        probes=probes,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3194.build_follow_up_manifest(output_dir=tmp_path / "m3194", doc_path=tmp_path / "m3194.md")

    assert manifest["id"] == m3194.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
