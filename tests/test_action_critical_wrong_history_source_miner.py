import argparse

import numpy as np
import torch

from autodrift.action_critical_wrong_history_source_miner import (
    BankSnapshot,
    action_critical_rejection_reason,
    is_compatible_pair,
    normalized_l2,
    obstacle_xy_from_observation,
    parse_surface_seed_range,
    response_context_vector,
    scene_context_vector,
)
from autodrift.matched_history_outcome_gate import OutcomeSnapshot


def test_parse_surface_seed_range_accepts_inclusive_range():
    parsed = parse_surface_seed_range("fresh=10:12")

    assert parsed.surface == "fresh"
    assert parsed.start_seed == 10
    assert parsed.end_seed == 12
    try:
        parse_surface_seed_range("bad")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("invalid seed range was accepted")


def test_scene_context_ignores_obstacle_relative_velocity():
    left = np.zeros(72, dtype=np.float32)
    right = np.zeros(72, dtype=np.float32)
    left[44] = right[44] = 1.0
    left[45] = right[45] = 0.4
    left[46] = right[46] = 0.1
    left[47] = -0.5
    left[48] = 0.2
    right[47] = 0.5
    right[48] = -0.2

    assert np.allclose(scene_context_vector(left), scene_context_vector(right))
    assert not np.allclose(left[44:72], right[44:72])


def test_obstacle_xy_from_observation_uses_body_frame_scaling():
    obs = np.zeros(72, dtype=np.float32)
    obs[44] = 1.0
    obs[45] = 0.25
    obs[46] = -0.5

    x_m, y_m = obstacle_xy_from_observation(obs)

    assert x_m == 20.0
    assert y_m == -10.0


def _bank_snapshot(seed: int, step: int, obs: np.ndarray, hidden: np.ndarray) -> BankSnapshot:
    return BankSnapshot(
        snapshot=OutcomeSnapshot(
            seed=seed,
            step=step,
            observation=obs.astype(np.float32),
            hidden=torch.as_tensor(hidden, dtype=torch.float32).reshape(1, -1),
            env=None,
            info={},
        ),
        surface="fresh",
        target="drift_required",
        obstacle_x_m=20.0,
        obstacle_y_m=1.0,
        obstacle_distance=20.0,
        scene_context=scene_context_vector(obs),
        response_context=response_context_vector(obs),
        hidden_flat=hidden.astype(np.float32),
        normal_first_action=np.zeros(3, dtype=np.float32),
    )


def test_is_compatible_pair_uses_context_response_and_seed_filters():
    obs = np.zeros(72, dtype=np.float32)
    obs[44] = 1.0
    obs[45] = 0.25
    obs[46] = 0.05
    left = _bank_snapshot(1, 10, obs, np.zeros(4, dtype=np.float32))
    right = _bank_snapshot(2, 12, obs.copy(), np.ones(4, dtype=np.float32))

    compatible, metrics = is_compatible_pair(
        left,
        right,
        context_distance_threshold=0.25,
        response_distance_threshold=0.20,
        obstacle_x_abs_delta=8.0,
        obstacle_y_abs_delta=1.5,
        step_abs_delta=20,
    )

    assert compatible
    assert metrics["context_distance"] == 0.0
    assert normalized_l2(left.hidden_flat, right.hidden_flat) == metrics["hidden_distance"]


def test_action_critical_rejection_reason_allows_success_drop():
    reason = action_critical_rejection_reason(
        first_l2=0.003,
        sequence_mean_l2=0.011,
        preferred_rejected_mean_l2=0.011,
        margin_gap=0.0,
        normal_margin=0.5,
        wrong_margin=0.5,
        success_drop=True,
        min_wrong_first_action_l2=0.002,
        min_wrong_action_sequence_mean_l2=0.006,
        min_preferred_rejected_action_mean_l2=0.010,
        min_margin_gap=0.010,
    )

    assert reason == "accepted"
