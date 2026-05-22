from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.terminal_margin_recovery_anchor import (
    RowKey,
    _filter_registry_rows,
    _save_recovery_anchor,
    build_action_candidates,
    candidate_acceptance,
    select_best_candidate,
)


def _registry_row(**overrides):
    row = {
        "surface": "m183_m170",
        "row_id": 16,
        "target": "future_braking_deceleration",
        "physical_pair_key": "9530:6:9550:6",
        "left_seed": 9530,
        "left_step": 6,
        "relocated_obstacle_body_x": 13.8,
        "relocated_obstacle_body_y": 0.2,
        "relocated_obstacle_half_width": 0.7,
        "normal_margin": 1e-6,
        "required_margin_floor": 5e-7,
        "retention_weight": 50.0,
    }
    row.update(overrides)
    return row


def test_filter_registry_rows_selects_required_key():
    frame = pd.DataFrame(
        [
            _registry_row(surface="m183_m170", row_id=16),
            _registry_row(surface="m183_m168", row_id=1),
        ]
    )

    selected = _filter_registry_rows(frame, row_keys=(RowKey("m183_m170", 16),), max_rows=0)

    assert selected["surface"].tolist() == ["m183_m170"]
    assert selected["row_id"].tolist() == [16]


def test_build_action_candidates_uses_steer_throttle_brake_order_and_clips():
    candidates = build_action_candidates(
        np.asarray([0.99, -0.99, 0.0], dtype=np.float32),
        steer_deltas=(0.02,),
        throttle_deltas=(-0.02,),
        brake_deltas=(0.015,),
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    np.testing.assert_allclose(candidate.action, np.asarray([1.0, -1.0, 0.015], dtype=np.float32))
    assert candidate.action_l2 > 0.0


def test_candidate_acceptance_requires_success_margin_and_trust_region():
    accepted, reason = candidate_acceptance(
        candidate_margin=0.0002,
        candidate_success=True,
        baseline_margin=0.00001,
        required_margin_floor=0.000001,
        action_l2=0.02,
        min_margin_improvement=0.00005,
        max_action_l2=0.05,
    )

    assert accepted
    assert reason == "accepted"

    accepted, reason = candidate_acceptance(
        candidate_margin=0.00002,
        candidate_success=True,
        baseline_margin=0.00001,
        required_margin_floor=0.000001,
        action_l2=0.02,
        min_margin_improvement=0.00005,
        max_action_l2=0.05,
    )

    assert not accepted
    assert reason == "insufficient_margin_improvement"


def test_select_best_candidate_prefers_largest_margin_improvement():
    best = select_best_candidate(
        [
            {"accepted": True, "margin_improvement": 0.10, "candidate_margin": 0.11, "action_l2": 0.03},
            {"accepted": True, "margin_improvement": 0.20, "candidate_margin": 0.21, "action_l2": 0.04},
            {"accepted": False, "margin_improvement": 0.30, "candidate_margin": 0.31, "action_l2": 0.01},
        ]
    )

    assert best is not None
    assert best["margin_improvement"] == 0.20


def test_save_recovery_anchor_loads_with_existing_trajectory_loader(tmp_path):
    path = tmp_path / "recovery_anchor.npz"
    _save_recovery_anchor(
        output_npz=path,
        observations=[np.zeros(72, dtype=np.float32)],
        hidden_states=[np.zeros(128, dtype=np.float32)],
        reference_actions=[np.asarray([0.1, 0.0, 0.2], dtype=np.float32)],
        source_indices=[0],
        step_indices=[0],
        weights=[50.0],
    )

    anchor = load_trajectory_action_anchor(
        path,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=128,
        act_dim=3,
    )

    assert anchor.size == 1
    assert tuple(anchor.reference_action.shape) == (1, 3)
