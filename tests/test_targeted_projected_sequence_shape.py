import pandas as pd

from autodrift.targeted_projected_sequence_shape import (
    baseline_summary_to_near_sources,
    filter_source_ids,
    targeted_source_summary,
)
from autodrift.trust_projected_sequence_shape import build_projected_sequence_candidates


def test_targeted_families_build_trust_projected_candidates():
    import numpy as np

    base = np.zeros((9, 3), dtype=np.float32)
    candidates = build_projected_sequence_candidates(
        base,
        steer_deltas=(0.04,),
        throttle_deltas=(-0.06,),
        brake_deltas=(0.04,),
        families=("targeted_constant_delta", "targeted_late_brake_hold", "targeted_steer_build_brake_hold"),
        per_step_action_l2=0.10,
        sequence_mean_l2_limit=0.08,
        sequence_max_l2_limit=0.10,
        max_delta_delta_l2_limit=0.08,
    )

    assert len(candidates) == 3
    assert all(candidate.candidate.trust_region_ok for candidate in candidates)
    assert {candidate.raw_family for candidate in candidates} == {
        "constant_delta",
        "late_brake_hold",
        "steer_build_brake_hold",
    }


def test_filter_source_ids_preserves_requested_order():
    frame = pd.DataFrame(
        [
            {"source_index": 0},
            {"source_index": 7},
            {"source_index": 8},
            {"source_index": 30},
        ]
    )

    selected = filter_source_ids(frame, (8, 0, 7, 30))

    assert selected["source_index"].tolist() == [8, 0, 7, 30]


def test_baseline_summary_to_near_sources_uses_previous_projection_counts():
    baseline = pd.DataFrame(
        [
            {"source_index": 8, "accepted_after_projection": 0},
            {"source_index": 30, "accepted_after_projection": 4},
        ]
    )
    source_rows = pd.DataFrame(
        [
            {"source_index": 8, "surface": "ood", "target": "future_yaw_response", "variant": "delayed_history"},
            {"source_index": 30, "surface": "ood", "target": "future_braking_deceleration", "variant": "wrong"},
        ]
    )

    near = baseline_summary_to_near_sources(baseline, source_rows)

    assert near["accepted_candidate_count"].tolist() == [0, 4]
    assert near["best_primary_failure"].tolist() == ["mean_l2_excess", "mean_l2_excess"]


def test_targeted_source_summary_marks_sentinel_regression():
    baseline = pd.DataFrame(
        [
            {"source_index": 8, "accepted_after_projection": 0, "best_projected_margin_improvement": 0.018},
            {"source_index": 30, "accepted_after_projection": 4, "best_projected_margin_improvement": 0.021},
        ]
    )
    sources = pd.DataFrame([{"source_index": 8}, {"source_index": 30}])
    rows = [
        {
            "source_index": 8,
            "accepted": True,
            "margin_improvement": 0.022,
            "risk_improvement": 0.022,
            "family": "targeted_constant_delta",
            "raw_family": "constant_delta",
            "sequence_length": 9,
            "projection_scale": 0.9,
            "rejection_reason": "margin_improved",
        },
        {
            "source_index": 30,
            "accepted": False,
            "margin_improvement": 0.01,
            "risk_improvement": 0.01,
            "family": "targeted_constant_delta",
            "raw_family": "constant_delta",
            "sequence_length": 9,
            "projection_scale": 1.0,
            "rejection_reason": "insufficient_margin_or_risk_improvement",
        },
    ]

    summary = targeted_source_summary(rows, baseline, sources)
    by_source = {row["source_index"]: row for row in summary}

    assert by_source[8]["accepted_after_projection"] == 1
    assert by_source[8]["best_margin_delta_vs_m630"] > 0
    assert by_source[30]["targeted_regression"] is True
