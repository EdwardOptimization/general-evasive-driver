from autodrift.public_base_low_tail_direction_family_target_audit import (
    classify_direction_family_target_audit,
)


def test_direction_family_target_classifier_flags_contract_artifact() -> None:
    assert (
        classify_direction_family_target_audit(
            contract_changed=False,
            training_started=True,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_target_family_count=4,
            normal_retained_family_count=4,
            behavior_grounded_family_count=4,
            m267_target_preflight_pass_count=4,
            joint_direction_target_candidate_count=2,
        )
        == "low_tail_direction_family_target_audit_contract_artifact"
    )


def test_direction_family_target_classifier_accepts_joint_candidate() -> None:
    assert (
        classify_direction_family_target_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_target_family_count=4,
            normal_retained_family_count=4,
            behavior_grounded_family_count=3,
            m267_target_preflight_pass_count=4,
            joint_direction_target_candidate_count=1,
        )
        == "low_tail_direction_family_target_audit_joint_candidate"
    )


def test_direction_family_target_classifier_routes_retention_failure() -> None:
    assert (
        classify_direction_family_target_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_target_family_count=4,
            normal_retained_family_count=0,
            behavior_grounded_family_count=3,
            m267_target_preflight_pass_count=4,
            joint_direction_target_candidate_count=0,
        )
        == "low_tail_direction_family_target_audit_normal_retention_failure"
    )


def test_direction_family_target_classifier_routes_m267_failure() -> None:
    assert (
        classify_direction_family_target_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_target_family_count=4,
            normal_retained_family_count=3,
            behavior_grounded_family_count=3,
            m267_target_preflight_pass_count=0,
            joint_direction_target_candidate_count=0,
        )
        == "low_tail_direction_family_target_audit_m267_preflight_failure"
    )
