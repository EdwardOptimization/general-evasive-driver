import numpy as np
import torch

from autodrift.action_critical_wrong_history_source_miner import BankSnapshot, scene_context_vector, response_context_vector
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.normal_success_boundary_source_miner import (
    candidate_pairs_for_lefts,
    classify_normal_window,
    select_evenly_by_step,
)


def _snapshot(seed: int, step: int) -> BankSnapshot:
    obs = np.zeros(72, dtype=np.float32)
    obs[44] = 1.0
    obs[45] = 0.25
    obs[46] = 0.05
    hidden = np.full(4, float(seed + step), dtype=np.float32)
    return BankSnapshot(
        snapshot=OutcomeSnapshot(
            seed=seed,
            step=step,
            observation=obs,
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
        hidden_flat=hidden,
        normal_first_action=np.zeros(3, dtype=np.float32),
    )


def test_classify_normal_window_separates_margin_bands():
    assert (
        classify_normal_window(
            normal_success=True,
            normal_margin=0.5,
            normal_margin_min=0.0,
            normal_margin_max=1.0,
        )
        == "near_boundary_preferred"
    )
    assert (
        classify_normal_window(
            normal_success=True,
            normal_margin=2.0,
            normal_margin_min=0.0,
            normal_margin_max=1.0,
        )
        == "early_safe_diagnostic"
    )
    assert (
        classify_normal_window(
            normal_success=False,
            normal_margin=0.5,
            normal_margin_min=0.0,
            normal_margin_max=1.0,
        )
        == "already_failed_diagnostic"
    )


def test_select_evenly_by_step_keeps_range():
    snapshots = [_snapshot(1, step) for step in range(10)]

    selected = select_evenly_by_step(snapshots, 3)

    assert [item.snapshot.step for item in selected] == [0, 4, 9]


def test_candidate_pairs_for_lefts_filters_to_requested_lefts():
    left = _snapshot(1, 10)
    right = _snapshot(2, 12)
    extra = _snapshot(3, 12)

    pairs = candidate_pairs_for_lefts(
        [left],
        [left, right, extra],
        max_right_candidates_per_left=4,
        max_candidate_pairs=10,
        context_distance_threshold=0.25,
        response_distance_threshold=0.20,
        obstacle_x_abs_delta=10.0,
        obstacle_y_abs_delta=2.0,
        step_abs_delta=30,
    )

    assert pairs
    assert {pair[0].snapshot.seed for pair in pairs} == {1}
    assert {pair[1].snapshot.seed for pair in pairs}.issubset({2, 3})
