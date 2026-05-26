from autodrift.m1013_candidate_b_full_replay_gate import (
    classify_m1019_gate,
    failure_types_for_m1019_result,
    next_blocker_for_m1019_result,
)


def test_m1019_classifier_requires_exact_retention() -> None:
    result = classify_m1019_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=0,
        candidate_preflight_pass_count=0,
        six_public_replay_gates_pass=False,
        source_diverse_pass=False,
        behavior_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "m1013_candidate_b_full_replay_gate_exact_retention_failed"
    assert failure_types_for_m1019_result(result) == ["proof_washout"]
    assert next_blocker_for_m1019_result(result) == "candidate_b_exact_retention_failure_audit"


def test_m1019_classifier_requires_source_diverse_diagnostic() -> None:
    result = classify_m1019_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=1,
        candidate_preflight_pass_count=1,
        six_public_replay_gates_pass=True,
        source_diverse_pass=False,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "m1013_candidate_b_full_replay_gate_source_diverse_diagnostic_failed"
    assert failure_types_for_m1019_result(result) == ["proof_washout"]


def test_m1019_classifier_accepts_full_gate_pass() -> None:
    result = classify_m1019_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=1,
        candidate_preflight_pass_count=1,
        six_public_replay_gates_pass=True,
        source_diverse_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "m1013_candidate_b_full_replay_gate_pass"
    assert failure_types_for_m1019_result(result) == ["none"]
    assert next_blocker_for_m1019_result(result) == "candidate_b_promotion_generalization_or_branch_synthesis_audit"
