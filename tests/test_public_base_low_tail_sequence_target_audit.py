from autodrift.public_base_low_tail_sequence_target_audit import classify_sequence_target_audit


def test_sequence_target_classifier_flags_contract_artifact() -> None:
    assert (
        classify_sequence_target_audit(
            contract_changed=False,
            training_started=True,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            sequence_family_count=3,
            first_action_retained_family_count=3,
            sequence_low_tail_candidate_count=1,
            m267_sequence_preflight_pass_count=1,
            joint_sequence_candidate_count=1,
        )
        == "low_tail_sequence_target_audit_contract_artifact"
    )


def test_sequence_target_classifier_accepts_joint_candidate() -> None:
    assert (
        classify_sequence_target_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            sequence_family_count=3,
            first_action_retained_family_count=3,
            sequence_low_tail_candidate_count=1,
            m267_sequence_preflight_pass_count=1,
            joint_sequence_candidate_count=1,
        )
        == "low_tail_sequence_target_audit_joint_candidate"
    )


def test_sequence_target_classifier_routes_no_sequence_candidate() -> None:
    assert (
        classify_sequence_target_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            sequence_family_count=3,
            first_action_retained_family_count=3,
            sequence_low_tail_candidate_count=0,
            m267_sequence_preflight_pass_count=3,
            joint_sequence_candidate_count=0,
        )
        == "low_tail_sequence_target_audit_no_sequence_low_tail_candidate"
    )
