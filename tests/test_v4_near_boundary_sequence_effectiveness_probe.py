from __future__ import annotations

import numpy as np

from autodrift.v4_near_boundary_sequence_effectiveness_probe import (
    accepted_sequence_effective_rows_for_pair,
    classify_sequence_effectiveness_result,
    sequence_override_stats,
)


def test_sequence_override_stats_reports_sequence_norm_and_clips() -> None:
    stats = sequence_override_stats(
        [np.asarray([0.03, 0.0, 0.0]), np.asarray([0.0, 0.04, 0.0])],
        [0.0, 0.5],
        severe_clip_steps=1,
    )

    assert np.isclose(stats["effective_delta_l2_mean"], 0.035)
    assert np.isclose(stats["effective_delta_l2_max"], 0.04)
    assert np.isclose(stats["effective_sequence_l2"], 0.05)
    assert np.isclose(stats["clip_fraction_mean"], 0.25)
    assert stats["clip_fraction_max"] == 0.5
    assert stats["severe_clip_steps"] == 1


def test_accepted_sequence_effective_rows_uses_mean_delta_and_margin() -> None:
    row = {
        "pair_id": 1,
        "direction": "steer_positive",
        "direction_family": "steer_axis",
        "hold_steps": 4,
        "epsilon_l2": 0.05,
        "normal_success": True,
        "normal_collision": False,
        "normal_margin": 0.02,
        "sequence_success": True,
        "sequence_collision": False,
        "sequence_margin": 0.005,
        "margin_delta": -0.015,
        "abs_margin_delta": 0.015,
        "degradation_margin_delta": 0.015,
        "improvement_margin_delta": 0.0,
        "success_flip": False,
        "collision_flip": False,
        "effective_delta_l2_mean": 0.05,
        "effective_sequence_l2": 0.1,
        "clip_fraction_max": 0.0,
        "severe_clip_steps": 0,
    }

    accepted = accepted_sequence_effective_rows_for_pair(
        [row],
        boundary_margin_threshold=0.05,
        margin_delta_threshold=0.01,
        action_l2_threshold=0.014,
    )

    assert len(accepted) == 1
    assert accepted[0]["accepted_class"] == "directional_degradation"
    assert accepted[0]["hold_steps"] == 4


def test_classification_marks_all_weak_when_no_sequence_margin_or_flip() -> None:
    result = classify_sequence_effectiveness_result(
        actor_changed=False,
        residual_changed=False,
        selected_pairs=3,
        reconstructed_snapshots=3,
        accepted_rows=[],
        all_rows=[
            {"abs_margin_delta": 0.002, "success_flip": False, "collision_flip": False},
            {"abs_margin_delta": 0.003, "success_flip": False, "collision_flip": False},
        ],
        margin_delta_threshold=0.01,
        min_primary_rows=40,
        min_sparse_rows=10,
        min_left_sources=8,
        min_fault_families=5,
        min_direction_families=2,
        min_hold_steps=2,
        max_source_dominance=0.3,
    )

    assert result == "v4_near_boundary_sequence_effectiveness_all_weak"
