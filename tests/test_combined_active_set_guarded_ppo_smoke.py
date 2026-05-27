from autodrift.combined_active_set_guarded_ppo_smoke import (
    PPO_ALLOWED_CHANGED_PREFIXES,
    classify_combined_active_set_guarded_ppo,
    failure_types_for_combined_active_set_guarded_ppo,
    next_blocker_for_combined_active_set_guarded_ppo,
)


def test_classify_combined_active_set_guarded_ppo_orders_failures() -> None:
    assert (
        classify_combined_active_set_guarded_ppo(
            actor_inputs_changed=False,
            ppo_returncode=0,
            training_metrics_finite=True,
            exact_pass=True,
            proof_pass=True,
            family_intersection_pass=True,
            source_diverse_pass=True,
            generalization_pass=True,
            behavior_pass=True,
            promoted=False,
            private_holdout_used=False,
        )
        == "combined_active_set_guarded_ppo_raw_candidate"
    )
    assert (
        classify_combined_active_set_guarded_ppo(
            actor_inputs_changed=True,
            ppo_returncode=1,
            training_metrics_finite=False,
            exact_pass=False,
            proof_pass=False,
            family_intersection_pass=False,
            source_diverse_pass=False,
            generalization_pass=False,
            behavior_pass=False,
            promoted=True,
            private_holdout_used=True,
        )
        == "combined_active_set_guarded_ppo_contract_artifact"
    )
    assert (
        classify_combined_active_set_guarded_ppo(
            actor_inputs_changed=False,
            ppo_returncode=0,
            training_metrics_finite=True,
            exact_pass=False,
            proof_pass=True,
            family_intersection_pass=True,
            source_diverse_pass=True,
            generalization_pass=True,
            behavior_pass=True,
            promoted=False,
            private_holdout_used=False,
        )
        == "combined_active_set_guarded_ppo_exact_retention_regression"
    )
    assert (
        classify_combined_active_set_guarded_ppo(
            actor_inputs_changed=False,
            ppo_returncode=0,
            training_metrics_finite=True,
            exact_pass=True,
            proof_pass=True,
            family_intersection_pass=True,
            source_diverse_pass=False,
            generalization_pass=True,
            behavior_pass=True,
            promoted=False,
            private_holdout_used=False,
        )
        == "combined_active_set_guarded_ppo_source_diagnostic_failed"
    )
    assert (
        classify_combined_active_set_guarded_ppo(
            actor_inputs_changed=False,
            ppo_returncode=0,
            training_metrics_finite=True,
            exact_pass=True,
            proof_pass=True,
            family_intersection_pass=False,
            source_diverse_pass=True,
            generalization_pass=True,
            behavior_pass=True,
            promoted=False,
            private_holdout_used=False,
        )
        == "combined_active_set_guarded_ppo_public_replay_washout"
    )


def test_failure_types_and_next_blocker_for_combined_active_set_guarded_ppo() -> None:
    assert failure_types_for_combined_active_set_guarded_ppo(
        "combined_active_set_guarded_ppo_raw_candidate"
    ) == ["none"]
    assert failure_types_for_combined_active_set_guarded_ppo(
        "combined_active_set_guarded_ppo_public_replay_washout"
    ) == ["proof_washout"]
    assert failure_types_for_combined_active_set_guarded_ppo(
        "combined_active_set_guarded_ppo_behavior_regression"
    ) == ["behavior_regression"]
    assert (
        next_blocker_for_combined_active_set_guarded_ppo("combined_active_set_guarded_ppo_raw_candidate")
        == "combined_active_set_guarded_ppo_promotion_audit"
    )
    assert (
        next_blocker_for_combined_active_set_guarded_ppo("combined_active_set_guarded_ppo_public_replay_washout")
        == "combined_active_set_guarded_ppo_exact_repair_projection_design"
    )


def test_ppo_allowed_changed_prefixes_cover_expected_trainable_surfaces() -> None:
    expected = {
        "actor_mean.",
        "context_encoder.",
        "critic.",
        "online_gru_cell.",
        "response_context_fusion.0.",
        "response_encoder.",
        "response_prediction_head.",
    }
    assert set(PPO_ALLOWED_CHANGED_PREFIXES) == expected
