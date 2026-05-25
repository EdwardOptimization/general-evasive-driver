from __future__ import annotations

import numpy as np

from autodrift.v4_full_wrong_history_response_intervention import (
    accepted_rows_for_pair,
    compose_wrong_history_observation,
)


def test_compose_wrong_history_observation_preserves_context() -> None:
    left = np.arange(72, dtype=np.float32)
    right = left + 1000.0

    ego = compose_wrong_history_observation(left, right, variant="wrong_ego_response_obs")
    action = compose_wrong_history_observation(left, right, variant="wrong_action_history_obs")
    both = compose_wrong_history_observation(left, right, variant="wrong_response_action_hidden")

    assert np.all(ego[:9] == right[:9])
    assert np.all(ego[9:12] == left[9:12])
    assert np.all(ego[12:] == left[12:])
    assert np.all(action[:9] == left[:9])
    assert np.all(action[9:12] == right[9:12])
    assert np.all(action[12:] == left[12:])
    assert np.all(both[:12] == right[:12])
    assert np.all(both[12:] == left[12:])


def test_accepted_rows_separates_primary_component_and_mitigation() -> None:
    base = {
        "pair_id": 1,
        "normal_success": True,
        "normal_collision": False,
        "normal_margin": 0.02,
        "variant_success": True,
        "variant_collision": False,
        "variant_margin": 0.005,
        "margin_gap_from_normal": 0.015,
        "first_action_l2_vs_normal": 0.02,
        "prefix_l2_mean_vs_normal": 0.01,
    }
    rows = [
        {**base, "variant": "normal", "margin_gap_from_normal": 0.0, "first_action_l2_vs_normal": 0.0},
        {**base, "variant": "wrong_response_action_hidden"},
        {**base, "variant": "wrong_hidden_only"},
        {**base, "variant": "zero_command_obs", "margin_gap_from_normal": 0.001},
    ]

    primary, component, mitigation = accepted_rows_for_pair(
        rows,
        boundary_margin_threshold=0.05,
        primary_margin_gap_threshold=0.01,
        mitigation_margin_gap_threshold=0.02,
        action_l2_threshold=0.014,
    )

    assert [row["variant"] for row in primary] == ["wrong_response_action_hidden"]
    assert {row["accepted_class"] for row in component} == {"response_action_plus_hidden", "hidden_only"}
    assert mitigation == []
