from autodrift.candidate_b_combined_active_set_full_public_gate import (
    changed_parameters_allowed,
    classify_full_public_gate,
    failure_types_for_full_public_gate,
    next_blocker_for_full_public_gate,
)


def test_changed_parameters_allowed_uses_m1038_trainable_surface() -> None:
    assert changed_parameters_allowed(
        [
            "actor_mean.weight",
            "actor_mean.bias",
            "response_context_fusion.0.weight",
            "response_context_fusion.0.bias",
        ]
    )
    assert not changed_parameters_allowed(["actor_mean.weight", "gru.weight_ih"])
    assert not changed_parameters_allowed(["log_std"])


def test_classify_full_public_gate_orders_failures() -> None:
    assert (
        classify_full_public_gate(
            actor_inputs_changed=False,
            allowed_surface_contract_pass=True,
            exact_pass=True,
            proof_pass=True,
            source_diverse_pass=True,
            generalization_pass=True,
            behavior_pass=True,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_full_public_gate_candidate"
    )
    assert (
        classify_full_public_gate(
            actor_inputs_changed=False,
            allowed_surface_contract_pass=False,
            exact_pass=True,
            proof_pass=True,
            source_diverse_pass=True,
            generalization_pass=True,
            behavior_pass=True,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_full_public_gate_contract_artifact"
    )
    assert (
        classify_full_public_gate(
            actor_inputs_changed=False,
            allowed_surface_contract_pass=True,
            exact_pass=True,
            proof_pass=False,
            source_diverse_pass=True,
            generalization_pass=True,
            behavior_pass=True,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_full_public_gate_public_replay_washout"
    )


def test_failure_types_and_next_blocker_for_full_public_gate() -> None:
    assert failure_types_for_full_public_gate("candidate_b_combined_active_set_full_public_gate_candidate") == [
        "none"
    ]
    assert failure_types_for_full_public_gate(
        "candidate_b_combined_active_set_full_public_gate_generalization_regression"
    ) == ["scenario_sampling_failure"]
    assert (
        next_blocker_for_full_public_gate("candidate_b_combined_active_set_full_public_gate_candidate")
        == "candidate_b_combined_active_set_promotion_audit"
    )
    assert (
        next_blocker_for_full_public_gate("candidate_b_combined_active_set_full_public_gate_behavior_regression")
        == "candidate_b_combined_active_set_behavior_regression_audit"
    )
