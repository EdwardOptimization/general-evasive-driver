from autodrift.public_base_direction_target_export import classify_direction_target_export


def test_direction_target_export_classifier_flags_contract_artifact() -> None:
    assert (
        classify_direction_target_export(
            contract_changed=False,
            training_started=True,
            ppo_used=False,
            promoted=False,
            accepted_family_count=4,
            accepted_target_count=256,
            diagnostic_target_count=0,
            proof_target_count=32,
            retention_anchor_count=100,
            max_direction_family_fraction=0.25,
        )
        == "direction_target_export_contract_artifact"
    )


def test_direction_target_export_classifier_accepts_export() -> None:
    assert (
        classify_direction_target_export(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            accepted_family_count=20,
            accepted_target_count=1280,
            diagnostic_target_count=0,
            proof_target_count=160,
            retention_anchor_count=1149,
            max_direction_family_fraction=0.25,
        )
        == "direction_target_export_pass"
    )


def test_direction_target_export_classifier_rejects_diagnostic_leak() -> None:
    assert (
        classify_direction_target_export(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            accepted_family_count=20,
            accepted_target_count=1280,
            diagnostic_target_count=64,
            proof_target_count=160,
            retention_anchor_count=1149,
            max_direction_family_fraction=0.25,
        )
        == "direction_target_export_diagnostic_family_leak"
    )


def test_direction_target_export_classifier_routes_source_dominance() -> None:
    assert (
        classify_direction_target_export(
            contract_changed=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
            accepted_family_count=20,
            accepted_target_count=1280,
            diagnostic_target_count=0,
            proof_target_count=160,
            retention_anchor_count=1149,
            max_direction_family_fraction=0.80,
        )
        == "direction_target_export_source_dominated"
    )
