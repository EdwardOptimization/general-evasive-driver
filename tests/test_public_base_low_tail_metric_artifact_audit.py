from autodrift.public_base_low_tail_metric_artifact_audit import classify_metric_artifact_audit


def test_metric_artifact_classifier_flags_contract_artifact() -> None:
    assert (
        classify_metric_artifact_audit(
            contract_changed=True,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_family_count=4,
            target_metric_artifact=True,
            direction_sign_suspicion=False,
            threshold_only_issue=False,
            behavior_improved_family_count=0,
        )
        == "low_tail_metric_artifact_audit_contract_artifact"
    )


def test_metric_artifact_classifier_prioritizes_sign_suspicion() -> None:
    assert (
        classify_metric_artifact_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_family_count=4,
            target_metric_artifact=True,
            direction_sign_suspicion=True,
            threshold_only_issue=False,
            behavior_improved_family_count=1,
        )
        == "low_tail_metric_artifact_audit_direction_sign_suspicion"
    )


def test_metric_artifact_classifier_routes_artifact() -> None:
    assert (
        classify_metric_artifact_audit(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            direction_family_count=4,
            target_metric_artifact=True,
            direction_sign_suspicion=False,
            threshold_only_issue=False,
            behavior_improved_family_count=0,
        )
        == "low_tail_metric_artifact_audit_target_metric_artifact"
    )
