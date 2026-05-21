import numpy as np
import pandas as pd

from autodrift.near_boundary_outcome_surface import (
    select_near_boundary_rows,
    summarize_near_boundary_surface,
)


def test_select_near_boundary_rows_filters_margin_and_gap():
    frame = pd.DataFrame(
        [
            {
                "pair_id": 1,
                "checkpoint_label": "m105",
                "target": "future_yaw_response",
                "variant": "reset_hidden",
                "normal_margin": 0.18,
                "variant_margin": 0.14,
                "margin_gap": 0.04,
                "normal_success": True,
                "success_drop": False,
                "normal_better": True,
            },
            {
                "pair_id": 2,
                "checkpoint_label": "m105",
                "target": "future_yaw_response",
                "variant": "wrong_matched_history",
                "normal_margin": 0.30,
                "variant_margin": 0.10,
                "margin_gap": 0.20,
                "normal_success": True,
                "success_drop": False,
                "normal_better": True,
            },
            {
                "pair_id": 3,
                "checkpoint_label": "m105",
                "target": "future_yaw_response",
                "variant": "zero_current_response",
                "normal_margin": 0.17,
                "variant_margin": 0.16,
                "margin_gap": 0.01,
                "normal_success": True,
                "success_drop": False,
                "normal_better": False,
            },
        ]
    )

    selected = select_near_boundary_rows(
        frame,
        max_normal_margin=0.20,
        min_margin_gap=0.02,
    )

    assert len(selected) == 1
    assert selected.iloc[0]["pair_id"] == 1


def test_summarize_near_boundary_surface_reports_required_variants():
    accepted = pd.DataFrame(
        [
            {
                "pair_id": 1,
                "checkpoint_label": "m105",
                "target": "future_yaw_response",
                "variant": "reset_hidden",
                "normal_margin": 0.18,
                "variant_margin": 0.14,
                "margin_gap": 0.04,
                "success_drop": False,
                "normal_better": True,
            },
            {
                "pair_id": 2,
                "checkpoint_label": "m105",
                "target": "future_yaw_response",
                "variant": "wrong_matched_history",
                "normal_margin": 0.19,
                "variant_margin": 0.10,
                "margin_gap": 0.09,
                "success_drop": True,
                "normal_better": True,
            },
        ]
    )

    summary = summarize_near_boundary_surface(
        candidates=accepted,
        accepted=accepted,
        min_accepted_rows=2,
        required_variants=("reset_hidden", "wrong_matched_history"),
    )

    aggregate = summary[-1]
    assert aggregate["surface_found"] is True
    assert aggregate["required_variants_present"] is True
    assert aggregate["required_variant_counts"]["wrong_matched_history"] == 1
    assert np.isclose(aggregate["margin_gap_mean"], 0.065)
