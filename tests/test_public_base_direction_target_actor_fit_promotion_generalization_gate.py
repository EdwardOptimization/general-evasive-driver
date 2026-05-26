from autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate import (
    classify_promotion_generalization_gate,
    compare_behavior_rows,
    compare_eval_rows,
    failure_types_for_result_class,
)


def test_promotion_generalization_classifier_routes_contract_artifact() -> None:
    result = classify_promotion_generalization_gate(
        actor_inputs_changed=True,
        proof_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_promotion_gate_contract_artifact"
    assert failure_types_for_result_class(result) == ["contract_violation"]


def test_promotion_generalization_classifier_routes_proof_washout() -> None:
    result = classify_promotion_generalization_gate(
        actor_inputs_changed=False,
        proof_pass=False,
        generalization_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_promotion_gate_proof_washout"
    assert failure_types_for_result_class(result) == ["proof_washout"]


def test_promotion_generalization_classifier_routes_generalization_regression() -> None:
    result = classify_promotion_generalization_gate(
        actor_inputs_changed=False,
        proof_pass=True,
        generalization_pass=False,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_promotion_gate_generalization_regression"
    assert failure_types_for_result_class(result) == ["scenario_sampling_failure"]


def test_promotion_generalization_classifier_accepts_candidate() -> None:
    result = classify_promotion_generalization_gate(
        actor_inputs_changed=False,
        proof_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_promotion_gate_candidate"
    assert failure_types_for_result_class(result) == ["none"]


def test_compare_eval_rows_accepts_small_non_regression() -> None:
    rows = [
        {
            "distribution": "fresh_public",
            "seed": 1,
            "policy_label": "m399_base",
            "ablation": "none",
            "success_rate": 0.86,
            "termination_rate": 0.14,
            "min_clearance_margin_mean": 0.03,
            "collision_rate": 0.02,
        },
        {
            "distribution": "fresh_public",
            "seed": 1,
            "policy_label": "candidate",
            "ablation": "none",
            "success_rate": 0.855,
            "termination_rate": 0.145,
            "min_clearance_margin_mean": 0.026,
            "collision_rate": 0.025,
        },
    ]
    comparison = compare_eval_rows(rows, candidate_label="candidate")
    assert comparison[0]["generalization_pass"] is True


def test_compare_eval_rows_rejects_margin_regression() -> None:
    rows = [
        {
            "distribution": "moderate_ood",
            "seed": 1,
            "policy_label": "m399_base",
            "ablation": "none",
            "success_rate": 0.86,
            "termination_rate": 0.14,
            "min_clearance_margin_mean": 0.03,
            "collision_rate": 0.02,
        },
        {
            "distribution": "moderate_ood",
            "seed": 1,
            "policy_label": "candidate",
            "ablation": "none",
            "success_rate": 0.86,
            "termination_rate": 0.14,
            "min_clearance_margin_mean": 0.020,
            "collision_rate": 0.02,
        },
    ]
    comparison = compare_eval_rows(rows, candidate_label="candidate")
    assert comparison[0]["generalization_pass"] is False


def test_compare_behavior_rows_requires_reset_zero_all_ordering() -> None:
    rows = [
        {
            "seed": 7,
            "policy_label": "m399_base",
            "ablation": "none",
            "success_rate": 0.80,
            "termination_rate": 0.20,
        },
        {
            "seed": 7,
            "policy_label": "candidate",
            "ablation": "none",
            "success_rate": 0.81,
            "termination_rate": 0.19,
        },
        {
            "seed": 7,
            "policy_label": "candidate",
            "ablation": "reset_recurrent_state",
            "success_rate": 0.79,
            "termination_rate": 0.21,
        },
        {
            "seed": 7,
            "policy_label": "candidate",
            "ablation": "zero_all_response",
            "success_rate": 0.75,
            "termination_rate": 0.25,
        },
    ]
    comparison = compare_behavior_rows(rows, candidate_label="candidate")
    assert comparison[0]["reset_zero_all_ordering_retained"] is True
    assert comparison[0]["behavior_pass"] is True
