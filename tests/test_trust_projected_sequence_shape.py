import numpy as np
import pandas as pd
import pytest

from autodrift.trust_projected_sequence_shape import (
    PROJECTED_FAMILIES,
    build_projected_sequence_candidates,
    project_delta_sequence,
    projected_sequence_scales,
    select_focused_source_rows,
    source_recovery_summary,
)


def test_projected_sequence_scales_include_smooth_families():
    assert projected_sequence_scales(3, "projected_constant_delta").tolist() == [1.0, 1.0, 1.0]
    assert projected_sequence_scales(3, "projected_half_sine_pulse").tolist() == pytest.approx([0.0, 1.0, 0.0])
    assert projected_sequence_scales(3, "projected_s_curve_pulse").tolist() == pytest.approx([0.0, 0.5, 1.0])
    assert "projected_linear_ramp" in PROJECTED_FAMILIES


def test_project_delta_sequence_scales_back_inside_limits():
    base = np.zeros((5, 3), dtype=np.float32)
    delta = np.full((5, 3), 0.12, dtype=np.float32)

    projected, scale, raw_metrics = project_delta_sequence(
        base_action_sequence=base,
        delta_sequence=delta,
        per_step_action_l2=0.10,
        sequence_mean_l2_limit=0.08,
        sequence_max_l2_limit=0.10,
        max_delta_delta_l2_limit=0.08,
    )

    assert scale < 1.0
    assert raw_metrics[0] > 0.08
    assert np.linalg.norm(projected, axis=1).mean() <= 0.08 + 1e-8
    assert np.linalg.norm(projected, axis=1).max() <= 0.10 + 1e-8


def test_build_projected_sequence_candidates_preserves_trust_region():
    base = np.zeros((7, 3), dtype=np.float32)

    candidates = build_projected_sequence_candidates(
        base,
        steer_deltas=(0.08,),
        throttle_deltas=(-0.06,),
        brake_deltas=(0.08,),
        families=("projected_constant_delta", "projected_half_sine_pulse"),
        per_step_action_l2=0.10,
        sequence_mean_l2_limit=0.08,
        sequence_max_l2_limit=0.10,
        max_delta_delta_l2_limit=0.08,
    )

    assert len(candidates) == 2
    assert {candidate.candidate.family for candidate in candidates} == {
        "projected_constant_delta",
        "projected_half_sine_pulse",
    }
    assert all(candidate.candidate.trust_region_ok for candidate in candidates)
    assert all(candidate.projection_scale <= 1.0 for candidate in candidates)


def test_select_focused_source_rows_filters_trust_primary_low_accepted_sources():
    near = pd.DataFrame(
        [
            _near_source(30, accepted=0, primary="mean_l2_excess", collision=False),
            _near_source(7, accepted=3, primary="max_l2_excess", collision=False),
            _near_source(1, accepted=0, primary="candidate_collision", collision=True),
            _near_source(13, accepted=152, primary="mean_l2_excess", collision=False),
        ]
    )
    sources = pd.DataFrame(
        [
            {"source_index": 30, "surface": "ood"},
            {"source_index": 7, "surface": "fresh"},
            {"source_index": 1, "surface": "ood"},
            {"source_index": 13, "surface": "fresh"},
        ]
    )

    focused = select_focused_source_rows(near, sources, max_accepted_candidates=3)

    assert focused["source_index"].tolist() == [7, 30]
    assert focused["trust_projected_focus"].tolist() == [True, True]


def test_source_recovery_summary_reports_recovered_zero_accepted_sources():
    near = pd.DataFrame(
        [
            _near_source(30, accepted=0, primary="mean_l2_excess", collision=False),
            _near_source(7, accepted=3, primary="mean_l2_excess", collision=False),
        ]
    )
    rows = [
        {
            "source_index": 30,
            "accepted": True,
            "margin_improvement": 0.03,
            "risk_improvement": 0.03,
            "family": "projected_constant_delta",
            "raw_family": "constant_delta",
            "sequence_length": 7,
            "projection_scale": 0.8,
            "rejection_reason": "margin_improved",
        },
        {
            "source_index": 7,
            "accepted": False,
            "margin_improvement": 0.01,
            "risk_improvement": 0.01,
            "family": "projected_decay_pulse",
            "raw_family": "decay_pulse",
            "sequence_length": 5,
            "projection_scale": 1.0,
            "rejection_reason": "insufficient_margin_or_risk_improvement",
        },
    ]

    summary = source_recovery_summary(rows, near)
    by_source = {row["source_index"]: row for row in summary}

    assert by_source[30]["recovered_by_projection"] is True
    assert by_source[30]["accepted_after_projection"] == 1
    assert by_source[7]["recovered_by_projection"] is False


def _near_source(source_index: int, *, accepted: int, primary: str, collision: bool) -> dict[str, object]:
    return {
        "source_index": source_index,
        "source_tier": "core_boundary",
        "surface": "fresh",
        "target": "future_yaw_response",
        "variant": "delayed_history",
        "accepted_candidate_count": accepted,
        "best_primary_failure": primary,
        "has_collision_near_miss": collision,
    }
