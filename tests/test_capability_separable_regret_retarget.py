from __future__ import annotations

import numpy as np

from autodrift.capability_separable_regret_retarget import (
    is_regret_boundary_target,
    parse_candidate_sequence,
    retarget_diagnostics,
    retarget_geometry_candidates,
    select_target_pairs,
)


def test_retarget_geometry_candidates_uses_cross_product_and_bounds():
    candidates = retarget_geometry_candidates(
        base_body_x=1.0,
        base_body_y=-0.5,
        base_half_width=0.12,
        body_x_deltas=(-1.0, 0.0, 1.0),
        body_y_deltas=(-0.1, 0.0),
        half_width_deltas=(-0.05, 0.0, 0.05),
        min_body_x=0.5,
        min_half_width=0.1,
    )

    assert candidates
    assert all(candidate["relocated_obstacle_body_x"] > 0.5 for candidate in candidates)
    assert all(candidate["relocated_obstacle_half_width"] >= 0.1 for candidate in candidates)
    assert len(
        {
            (
                candidate["relocated_obstacle_body_x"],
                candidate["relocated_obstacle_body_y"],
                candidate["relocated_obstacle_half_width"],
            )
            for candidate in candidates
        }
    ) == len(candidates)
    assert [candidate["retarget_id"] for candidate in candidates] == list(range(len(candidates)))


def test_parse_candidate_sequence_validates_length():
    sequence = parse_candidate_sequence(
        {
            "candidate_id": "4",
            "sequence_length": "2",
            "candidate_vector": "[0.1, 0.2, 0.3, -0.1, -0.2, -0.3]",
        }
    )

    assert sequence.shape == (2, 3)
    np.testing.assert_allclose(sequence[0], [0.1, 0.2, 0.3])


def test_select_target_pairs_filters_low_regret_viable_rows():
    rows = [
        {
            "pair_id": "5",
            "accepted": "False",
            "best_A_success": "True",
            "best_B_success": "True",
            "rejection_reason": "insufficient_cross_regret",
            "best_action_l2": "0.7",
            "cross_regret_A": "0.005",
            "cross_regret_B": "0.004",
        },
        {
            "pair_id": "6",
            "accepted": "False",
            "best_A_success": "True",
            "best_B_success": "False",
            "rejection_reason": "best_candidate_not_viable",
            "best_action_l2": "0.8",
            "cross_regret_A": "0.030",
            "cross_regret_B": "0.040",
        },
    ]

    assert is_regret_boundary_target(rows[0], min_best_action_l2=0.12, min_cross_regret_margin=0.02)
    assert not is_regret_boundary_target(rows[1], min_best_action_l2=0.12, min_cross_regret_margin=0.02)
    selected = select_target_pairs(
        rows,
        target_pair_id=5,
        max_target_pairs=1,
        min_best_action_l2=0.12,
        min_cross_regret_margin=0.02,
    )
    assert [row["pair_id"] for row in selected] == ["5"]


def test_retarget_diagnostics_reports_collision_and_low_regret():
    rollout_rows = [
        {"collision": True},
        {"collision": True},
        {"collision": True},
        {"collision": True},
    ]
    diagnostics = retarget_diagnostics(
        rollout_rows=rollout_rows,
        decision={
            "best_A_success": False,
            "best_B_success": False,
            "A_using_B_success": False,
            "B_using_A_success": False,
            "cross_regret_A": 0.001,
            "cross_regret_B": 0.002,
        },
        min_cross_regret_margin=0.02,
    )

    assert diagnostics["all_four_rollouts_collision"]
    assert diagnostics["own_branch_viability_fail"]
    assert diagnostics["wrong_branch_collision"]
    assert diagnostics["low_regret"]
