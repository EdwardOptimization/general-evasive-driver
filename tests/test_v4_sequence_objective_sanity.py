from autodrift.v4_sequence_objective_sanity import (
    _metric_summary,
    classify_v4_sequence_objective_sanity,
)


def test_classify_v4_sequence_objective_sanity_metadata_before_reconstruction():
    assert (
        classify_v4_sequence_objective_sanity(
            positive_rows=100,
            reconstructed_rows=100,
            metadata_missing_rows=1,
            duplicate_group_ids=0,
            missing_normal_rows=0,
            missing_source_snapshots=0,
            exact_losses_finite=True,
            normal_intervention_gap_mean=0.03,
            hard_negative_available_fraction=1.0,
            actor_parameters_changed=False,
        )
        == "v4_sequence_objective_metadata_artifact"
    )


def test_classify_v4_sequence_objective_sanity_reconstruction_blocked():
    assert (
        classify_v4_sequence_objective_sanity(
            positive_rows=100,
            reconstructed_rows=97,
            metadata_missing_rows=0,
            duplicate_group_ids=0,
            missing_normal_rows=0,
            missing_source_snapshots=0,
            exact_losses_finite=True,
            normal_intervention_gap_mean=0.03,
            hard_negative_available_fraction=1.0,
            actor_parameters_changed=False,
        )
        == "v4_sequence_objective_reconstruction_blocked"
    )


def test_classify_v4_sequence_objective_sanity_hard_negative_sparse():
    assert (
        classify_v4_sequence_objective_sanity(
            positive_rows=100,
            reconstructed_rows=100,
            metadata_missing_rows=0,
            duplicate_group_ids=0,
            missing_normal_rows=0,
            missing_source_snapshots=0,
            exact_losses_finite=True,
            normal_intervention_gap_mean=0.03,
            hard_negative_available_fraction=0.72,
            actor_parameters_changed=False,
        )
        == "v4_sequence_objective_hard_negative_sparse"
    )


def test_metric_summary_reports_overall_and_dimensions():
    rows = [
        {
            "contrast_group_id": "g1",
            "variant": "zero_command_obs",
            "horizon": "4",
            "hard_negative_available": True,
            "normal_anchor_mse": 0.0,
            "intervention_anchor_mse": 0.0,
            "normal_intervention_gap": 0.03,
            "target_gap": 0.04,
            "gap_deficit": 0.01,
            "hard_negative_calibration_loss": 0.0,
            "first_action_drift_from_base": 0.0,
            "outcome_weight": 1.5,
        },
        {
            "contrast_group_id": "g2",
            "variant": "reset_hidden_each_step",
            "horizon": "8",
            "hard_negative_available": False,
            "normal_anchor_mse": 0.0,
            "intervention_anchor_mse": 0.0,
            "normal_intervention_gap": 0.02,
            "target_gap": 0.04,
            "gap_deficit": 0.02,
            "hard_negative_calibration_loss": 0.0,
            "first_action_drift_from_base": 0.0,
            "outcome_weight": 1.2,
        },
    ]

    summary = _metric_summary(rows, dimensions=(("overall",), ("variant",)))

    overall = next(row for row in summary if row["dimension"] == "overall")
    assert overall["sample_count"] == 2
    assert overall["hard_negative_available_fraction"] == 0.5
    assert overall["normal_intervention_gap_mean"] == 0.025
    variants = {row["value"] for row in summary if row["dimension"] == "variant"}
    assert variants == {"zero_command_obs", "reset_hidden_each_step"}
