from autodrift.m1013_candidate_b_promotion_generalization_gate import (
    classify_candidate_b_promotion_gate,
    failure_types_for_candidate_b_result,
    next_blocker_for_candidate_b_result,
)


def test_candidate_b_promotion_gate_requires_exact_retention() -> None:
    result = classify_candidate_b_promotion_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=0,
        proof_pass=True,
        source_diverse_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_promotion_gate_exact_retention_failed"
    assert failure_types_for_candidate_b_result(result) == ["proof_washout"]
    assert next_blocker_for_candidate_b_result(result) == "candidate_b_exact_retention_failure_audit"


def test_candidate_b_promotion_gate_routes_generalization_regression() -> None:
    result = classify_candidate_b_promotion_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=1,
        proof_pass=True,
        source_diverse_pass=True,
        generalization_pass=False,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_promotion_gate_generalization_regression"
    assert failure_types_for_candidate_b_result(result) == ["scenario_sampling_failure"]


def test_candidate_b_promotion_gate_accepts_candidate_state() -> None:
    result = classify_candidate_b_promotion_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=1,
        proof_pass=True,
        source_diverse_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_promotion_gate_candidate"
    assert failure_types_for_candidate_b_result(result) == ["none"]
    assert next_blocker_for_candidate_b_result(result) == "candidate_b_promotion_audit"
