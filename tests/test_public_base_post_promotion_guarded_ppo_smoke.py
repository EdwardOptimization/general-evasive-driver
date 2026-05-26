from autodrift.public_base_post_promotion_guarded_ppo_smoke import (
    classify_post_promotion_guarded_ppo,
    failure_types_for_result_class,
)


def test_post_promotion_guarded_ppo_classifier_accepts_raw_candidate() -> None:
    result = classify_post_promotion_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=0,
        training_metrics_finite=True,
        proof_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        promoted=False,
        private_holdout_used=False,
    )
    assert result == "post_promotion_guarded_ppo_raw_candidate"
    assert failure_types_for_result_class(result) == ["none"]


def test_post_promotion_guarded_ppo_classifier_routes_training_instability() -> None:
    result = classify_post_promotion_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=2,
        training_metrics_finite=False,
        proof_pass=False,
        generalization_pass=False,
        behavior_pass=False,
        promoted=False,
        private_holdout_used=False,
    )
    assert result == "post_promotion_guarded_ppo_training_instability"
    assert failure_types_for_result_class(result) == ["training_instability"]


def test_post_promotion_guarded_ppo_classifier_routes_proof_washout() -> None:
    result = classify_post_promotion_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=0,
        training_metrics_finite=True,
        proof_pass=False,
        generalization_pass=True,
        behavior_pass=True,
        promoted=False,
        private_holdout_used=False,
    )
    assert result == "post_promotion_guarded_ppo_proof_washout"
    assert failure_types_for_result_class(result) == ["proof_washout"]


def test_post_promotion_guarded_ppo_classifier_routes_generalization_regression() -> None:
    result = classify_post_promotion_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=0,
        training_metrics_finite=True,
        proof_pass=True,
        generalization_pass=False,
        behavior_pass=True,
        promoted=False,
        private_holdout_used=False,
    )
    assert result == "post_promotion_guarded_ppo_generalization_regression"
    assert failure_types_for_result_class(result) == ["scenario_sampling_failure"]


def test_post_promotion_guarded_ppo_classifier_routes_contract_artifact() -> None:
    result = classify_post_promotion_guarded_ppo(
        actor_inputs_changed=True,
        ppo_returncode=0,
        training_metrics_finite=True,
        proof_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        promoted=False,
        private_holdout_used=False,
    )
    assert result == "post_promotion_guarded_ppo_contract_artifact"
    assert failure_types_for_result_class(result) == ["contract_violation"]
