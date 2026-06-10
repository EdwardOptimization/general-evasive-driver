import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_action_authority_effectiveness_candidate_implementation_materialization_preflight as m3203


def _source():
    admission_rows = [
        {"admission_family": "longitudinal_collision_authority_effectiveness_gap", "admission_role": "implementation_candidate_after_audit"},
        {"admission_family": "lateral_collision_clearance_authority_effectiveness_gap", "admission_role": "implementation_candidate_after_audit"},
        {"admission_family": "boundary_recovery_override_authority_effectiveness_gap", "admission_role": "implementation_candidate_after_audit"},
        {"admission_family": "action_effectiveness_saturation_guard", "admission_role": "cross_cutting_guard_only"},
    ]
    return {
        "source_exists": {
            "m3202_audit": True,
            "m3201_summary": True,
            "m3201_admission_rows": True,
            "m3201_contract_guard_rows": True,
            "m3201_claim_boundary_rows": True,
            "m3201_gate_rows": True,
            "m3199_summary": True,
            "m3199_gate_rows": True,
        },
        "m3202_audit_text": "m3203-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-effectiveness-candidate-implementation-materialization-preflight",
        "m3201_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3201_admission_rows": admission_rows,
        "m3201_contract_guard_rows": [],
        "m3201_claim_boundary_rows": [],
        "m3201_gate_rows": [{"status_pass": "True"}],
        "m3199_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3199_gate_rows": [{"status_pass": "True"}],
    }


def test_candidate_action_preserves_low_risk_fallback_and_bounds():
    observations = dict(m3203.probe_observations())
    low_risk = observations["low_risk_fallback_probe"]
    candidate = m3203.action_authority_effectiveness_candidate_action(low_risk)

    assert candidate.shape == (m3203.ACTION_DIM,)
    assert np.all(np.isfinite(candidate))
    assert np.max(np.abs(candidate)) <= 1.0
    assert np.allclose(
        candidate,
        m3203.v4_v2_fallback_no_regression_hard_safety_direct_action(low_risk, m3203.V4_POLICY_CONFIG),
    )


def test_action_probes_are_stronger_than_m3194_on_high_risk_rows():
    rows = m3203.action_probe_rows()
    by_family = {row["probe_family"]: row for row in rows}

    assert len(rows) >= 4
    assert by_family["low_risk_fallback_probe"]["fallback_path_selected"] is True
    high_risk = [row for row in rows if row["probe_family"] != "low_risk_fallback_probe"]
    assert len(high_risk) == 3
    assert all(row["stronger_than_m3194"] for row in high_risk)
    assert by_family["collision_authority_probe"]["candidate_throttle"] <= by_family["collision_authority_probe"]["m3194_throttle"]
    assert by_family["collision_authority_probe"]["candidate_brake"] >= by_family["collision_authority_probe"]["m3194_brake"]
    assert by_family["boundary_recovery_override_probe"]["candidate_throttle"] <= by_family["boundary_recovery_override_probe"]["m3194_throttle"]
    assert by_family["boundary_recovery_override_probe"]["candidate_brake"] >= by_family["boundary_recovery_override_probe"]["m3194_brake"]
    assert all(row["action_finite"] and row["action_bounded"] and row["delta_limited"] for row in rows)


def test_rules_contracts_and_claims_preserve_public_driver_boundary():
    rules = m3203.candidate_rule_rows()
    contracts = m3203.runtime_contract_rows()
    claims = m3203.claim_boundary_rows(follow_up_manifest_registered=True)

    assert {row["rule_family"] for row in rules} == {
        "longitudinal_collision_authority_effectiveness_gap",
        "lateral_collision_clearance_authority_effectiveness_gap",
        "boundary_recovery_override_authority_effectiveness_gap",
        "action_effectiveness_saturation_guard",
    }
    assert not any(row["public_driver_default_mutated"] for row in rules + contracts)
    assert all(row["runtime_base_policy_required"] is False for row in rules + contracts)
    assert all(row["hidden_oracle_actor_input_required"] is False for row in rules + contracts)
    assert all(row["status_pass"] for row in contracts)
    assert all(row["status_pass"] for row in claims)
    assert not any(row["claim_made"] for row in claims if row["claim_family"] == "forbidden")


def test_gate_matrix_accepts_complete_candidate_pack():
    rules = m3203.candidate_rule_rows()
    contracts = m3203.runtime_contract_rows()
    probes = m3203.action_probe_rows()
    claims = m3203.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3203.gate_matrix_rows(
        source=_source(),
        rules=rules,
        contracts=contracts,
        probes=probes,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_m3204_result_audit(tmp_path):
    manifest = m3203.build_follow_up_manifest(output_dir=tmp_path / "m3203", doc_path=tmp_path / "m3203.md")

    assert manifest["id"] == m3203.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
