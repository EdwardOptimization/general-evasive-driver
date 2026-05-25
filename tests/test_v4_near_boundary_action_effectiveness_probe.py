from __future__ import annotations

import numpy as np

from autodrift.v4_near_boundary_action_effectiveness_probe import (
    accepted_action_effective_rows_for_pair,
    classify_action_effectiveness_result,
    clipped_override_action,
    normalized_pair_delta,
    unit_direction_vector,
)


def test_pair_delta_direction_normalizes_left_to_right_action() -> None:
    left = np.asarray([0.1, 0.2, 0.3])
    right = np.asarray([0.1, 0.5, 0.7])
    unit = normalized_pair_delta(left, right)

    assert unit is not None
    assert np.isclose(np.linalg.norm(unit), 1.0)
    assert np.allclose(unit_direction_vector("pair_delta_positive", unit), unit)
    assert np.allclose(unit_direction_vector("pair_delta_negative", unit), -unit)


def test_clipped_override_action_reports_effective_delta_and_clip_fraction() -> None:
    normal = np.asarray([0.99, 0.0, 0.0])
    unit = np.asarray([1.0, 0.0, 0.0])
    result = clipped_override_action(
        normal,
        unit,
        0.05,
        low=np.asarray([-1.0, -1.0, -1.0]),
        high=np.asarray([1.0, 1.0, 1.0]),
    )

    assert np.allclose(result["override_action"], [1.0, 0.0, 0.0])
    assert np.isclose(result["effective_delta_l2_after_clip"], 0.01)
    assert result["clip_fraction"] > 0.25
    assert result["severe_clip"] is True


def test_accepted_action_effective_rows_splits_degradation_and_improvement() -> None:
    base = {
        "pair_id": 1,
        "normal_success": True,
        "normal_collision": False,
        "normal_margin": 0.02,
        "effective_delta_l2_after_clip": 0.02,
        "clip_fraction": 0.0,
        "severe_clip": False,
        "success_flip": False,
        "collision_flip": False,
    }
    rows = [
        {
            **base,
            "direction": "steer_positive",
            "direction_family": "steer_axis",
            "override_success": True,
            "override_collision": False,
            "override_margin": 0.005,
            "margin_delta": -0.015,
            "abs_margin_delta": 0.015,
            "degradation_margin_delta": 0.015,
            "improvement_margin_delta": 0.0,
        },
        {
            **base,
            "direction": "brake_positive",
            "direction_family": "brake_axis",
            "override_success": True,
            "override_collision": False,
            "override_margin": 0.035,
            "margin_delta": 0.015,
            "abs_margin_delta": 0.015,
            "degradation_margin_delta": 0.0,
            "improvement_margin_delta": 0.015,
        },
    ]

    accepted = accepted_action_effective_rows_for_pair(
        rows,
        boundary_margin_threshold=0.05,
        margin_delta_threshold=0.01,
        action_l2_threshold=0.014,
    )

    assert [row["accepted_class"] for row in accepted] == ["directional_degradation", "directional_improvement"]


def test_classification_marks_first_step_insensitive_when_no_margin_or_flip() -> None:
    result = classify_action_effectiveness_result(
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
        max_source_dominance=0.3,
    )

    assert result == "v4_near_boundary_action_effectiveness_first_step_insensitive"
