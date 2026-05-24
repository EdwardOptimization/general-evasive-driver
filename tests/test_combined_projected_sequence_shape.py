import pandas as pd

from autodrift.combined_projected_sequence_shape import (
    combined_source_summary,
    default_grid_specs,
)


def test_default_grid_specs_keep_recovery_and_preservation_separate():
    specs = {spec.name: spec for spec in default_grid_specs()}

    assert specs["source8_recovery_grid"].source_ids == (8, 0, 30)
    assert specs["source7_preservation_grid"].source_ids == (7,)
    assert 0.08 in specs["source7_preservation_grid"].steer_deltas
    assert 0.0 in specs["source7_preservation_grid"].throttle_deltas


def test_combined_source_summary_records_accepted_grid_names():
    baseline = pd.DataFrame(
        [
            {"source_index": 8, "accepted_after_projection": 0, "best_projected_margin_improvement": 0.018},
            {"source_index": 7, "accepted_after_projection": 0, "best_projected_margin_improvement": 0.019},
        ]
    )
    rows = [
        {
            "grid_name": "source8_recovery_grid",
            "source_index": 8,
            "accepted": True,
            "margin_improvement": 0.026,
            "risk_improvement": 0.026,
            "family": "targeted_constant_delta",
            "raw_family": "constant_delta",
            "sequence_length": 9,
            "projection_scale": 0.9,
            "rejection_reason": "margin_improved",
        },
        {
            "grid_name": "source7_preservation_grid",
            "source_index": 7,
            "accepted": True,
            "margin_improvement": 0.021,
            "risk_improvement": 0.021,
            "family": "targeted_constant_delta",
            "raw_family": "constant_delta",
            "sequence_length": 7,
            "projection_scale": 1.0,
            "rejection_reason": "margin_improved",
        },
    ]

    summary = combined_source_summary(rows, baseline)
    by_source = {row["source_index"]: row for row in summary}

    assert by_source[8]["accepted_grid_names"] == "source8_recovery_grid"
    assert by_source[7]["accepted_grid_names"] == "source7_preservation_grid"
    assert by_source[7]["has_acceptance"] is True
