from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from autodrift.intervention_objectives import load_old_key_recovery_snippets
from autodrift.old_key_recovery_targets import (
    _write_old_key_recovery_corpus,
    recovery_row_weight,
    select_recovery_target,
)


def _source_row(**overrides):
    row = {
        "case_id": "10033|perturbed|29|23|9.500000|-1.200000|0.700000",
        "key": "10033|perturbed|29|23",
        "seed": 10033,
        "source_condition": "perturbed",
        "source_step": 29,
        "paired_step": 23,
        "target_obstacle_distance": 9.5,
        "relocated_obstacle_body_y": -1.2,
        "relocated_obstacle_half_width": 0.7,
        "candidate_gap_delta": -0.001,
        "candidate_normal_delta": -0.0008,
    }
    row.update(overrides)
    return pd.Series(row)


def _candidate(**overrides):
    row = {
        "candidate_id": 7,
        "candidate_steer": 0.2,
        "candidate_throttle": -0.1,
        "candidate_brake": 0.3,
        "candidate_margin": 0.013,
        "margin_improvement": 0.003,
        "action_l2": 0.04,
        "accepted": True,
        "rejection_reason": "accepted",
    }
    row.update(overrides)
    return row


def test_recovery_row_weight_reflects_severity_and_improvement():
    row = _source_row(candidate_gap_delta=-0.001, candidate_normal_delta=-0.0005)

    recovered = recovery_row_weight(
        row,
        accepted_recovery=True,
        margin_improvement=0.0001,
        min_margin_improvement=0.00005,
    )
    retention = recovery_row_weight(
        row,
        accepted_recovery=False,
        margin_improvement=0.0,
        min_margin_improvement=0.00005,
    )

    assert recovered > retention > 0.0


def test_select_recovery_target_uses_accepted_candidate():
    target = select_recovery_target(
        row=_source_row(),
        row_index=3,
        base_action=np.asarray([0.1, -0.2, 0.0], dtype=np.float32),
        rejected_anchor_action=np.asarray([-0.1, -0.3, 0.2], dtype=np.float32),
        baseline={"success": True, "min_clearance_margin": 0.010},
        candidate_rows=[
            _candidate(candidate_id=1, candidate_margin=0.011, margin_improvement=0.001),
            _candidate(candidate_id=2, candidate_margin=0.013, margin_improvement=0.003),
        ],
        min_margin_improvement=0.00005,
        include_base_retention=True,
    )

    assert target is not None
    assert target["accepted_recovery"] is True
    assert target["recovery_status"] == "recovered"
    assert target["selected_candidate_id"] == 2
    np.testing.assert_allclose(target["recovery_action"], np.asarray([0.2, -0.1, 0.3], dtype=np.float32))
    np.testing.assert_allclose(target["rejected_anchor_action"], np.asarray([-0.1, -0.3, 0.2], dtype=np.float32))


def test_select_recovery_target_marks_base_retention_without_accepted_candidate():
    target = select_recovery_target(
        row=_source_row(),
        row_index=4,
        base_action=np.asarray([0.1, -0.2, 0.0], dtype=np.float32),
        rejected_anchor_action=np.asarray([-0.1, -0.3, 0.2], dtype=np.float32),
        baseline={"success": True, "min_clearance_margin": 0.010},
        candidate_rows=[
            _candidate(accepted=False, rejection_reason="insufficient_margin_improvement", candidate_margin=0.0101),
        ],
        min_margin_improvement=0.0005,
        include_base_retention=True,
    )

    assert target is not None
    assert target["accepted_recovery"] is False
    assert target["recovery_status"] == "base_retention"
    np.testing.assert_allclose(target["recovery_action"], np.asarray([0.1, -0.2, 0.0], dtype=np.float32))


def test_write_old_key_recovery_corpus_loads_with_m383_loader(tmp_path):
    target = select_recovery_target(
        row=_source_row(),
        row_index=0,
        base_action=np.asarray([0.1, -0.2, 0.0], dtype=np.float32),
        rejected_anchor_action=np.asarray([-0.1, -0.3, 0.2], dtype=np.float32),
        baseline={"success": True, "min_clearance_margin": 0.010},
        candidate_rows=[_candidate()],
        min_margin_improvement=0.00005,
        include_base_retention=True,
    )
    assert target is not None
    output = tmp_path / "old_key_recovery_corpus.npz"

    _write_old_key_recovery_corpus(
        output_npz=output,
        observations=[np.zeros(72, dtype=np.float32)],
        preferred_hidden=[np.zeros(128, dtype=np.float32)],
        rejected_hidden=[np.ones(128, dtype=np.float32)],
        targets=[target],
    )
    loaded = load_old_key_recovery_snippets(
        output,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=128,
        act_dim=3,
    )

    assert loaded.size == 1
    assert loaded.row_id.tolist() == [0]
