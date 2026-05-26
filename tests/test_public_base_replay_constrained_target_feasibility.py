from autodrift.public_base_replay_constrained_target_feasibility import classify_target_feasibility


def test_target_feasibility_classifier_flags_contract_artifact() -> None:
    assert (
        classify_target_feasibility(
            contract_changed=True,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            exact_target_candidate_count=1,
            m267_target_preflight_pass_count=1,
            joint_feasible_target_count=1,
        )
        == "replay_constrained_target_feasibility_contract_artifact"
    )


def test_target_feasibility_classifier_accepts_joint_candidate() -> None:
    assert (
        classify_target_feasibility(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            exact_target_candidate_count=2,
            m267_target_preflight_pass_count=3,
            joint_feasible_target_count=1,
        )
        == "replay_constrained_target_feasibility_joint_candidate"
    )


def test_target_feasibility_classifier_routes_single_sided_evidence() -> None:
    assert (
        classify_target_feasibility(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            exact_target_candidate_count=0,
            m267_target_preflight_pass_count=3,
            joint_feasible_target_count=0,
        )
        == "replay_constrained_target_feasibility_low_tail_exact_failure"
    )
