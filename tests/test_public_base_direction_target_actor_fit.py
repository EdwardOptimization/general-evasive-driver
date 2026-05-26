from autodrift.public_base_direction_target_actor_fit import classify_direction_target_actor_fit


def test_direction_target_actor_fit_classifier_flags_contract_artifact() -> None:
    assert (
        classify_direction_target_actor_fit(
            non_actor_mean_changed=True,
            actor_mean_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_rows=0,
            candidate_count=1,
            target_fit_improved_count=1,
            proof_preflight_pass_count=1,
            retention_pass_count=1,
            ppo_used=False,
            promoted=False,
        )
        == "direction_target_actor_fit_contract_artifact"
    )


def test_direction_target_actor_fit_classifier_accepts_candidate() -> None:
    assert (
        classify_direction_target_actor_fit(
            non_actor_mean_changed=False,
            actor_mean_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_rows=0,
            candidate_count=1,
            target_fit_improved_count=1,
            proof_preflight_pass_count=1,
            retention_pass_count=1,
            ppo_used=False,
            promoted=False,
        )
        == "direction_target_actor_fit_candidate"
    )


def test_direction_target_actor_fit_classifier_routes_proof_washout() -> None:
    assert (
        classify_direction_target_actor_fit(
            non_actor_mean_changed=False,
            actor_mean_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_rows=0,
            candidate_count=0,
            target_fit_improved_count=3,
            proof_preflight_pass_count=0,
            retention_pass_count=3,
            ppo_used=False,
            promoted=False,
        )
        == "direction_target_actor_fit_proof_washout"
    )


def test_direction_target_actor_fit_classifier_routes_no_target_fit() -> None:
    assert (
        classify_direction_target_actor_fit(
            non_actor_mean_changed=False,
            actor_mean_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_rows=0,
            candidate_count=0,
            target_fit_improved_count=0,
            proof_preflight_pass_count=3,
            retention_pass_count=3,
            ppo_used=False,
            promoted=False,
        )
        == "direction_target_actor_fit_no_target_fit"
    )
