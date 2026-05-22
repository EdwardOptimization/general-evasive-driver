from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.rejected_history_trajectory_anchor import (
    _combine_anchors,
    _save_anchor,
    select_corpus_rows,
)


def _corpus_row(**overrides):
    row = {
        "row_id": 1,
        "target": "future_braking_deceleration",
        "physical_pair_key": "9530:6:9550:6",
        "left_seed": 9530,
        "right_seed": 9550,
        "left_step": 6,
        "right_step": 6,
        "relocated_obstacle_body_x": 13.8,
        "relocated_obstacle_body_y": 0.2,
        "relocated_obstacle_half_width": 0.7,
    }
    row.update(overrides)
    return row


def _write_anchor(path, rows: int, source_offset: int = 0):
    _save_anchor(
        path,
        observation=np.zeros((rows, 72), dtype=np.float32),
        hidden=np.zeros((rows, 128), dtype=np.float32),
        reference_action=np.zeros((rows, 3), dtype=np.float32),
        source_index=np.arange(source_offset, source_offset + rows, dtype=np.int64),
        step_index=np.zeros(rows, dtype=np.int64),
        weight=np.ones(rows, dtype=np.float32),
    )


def test_select_corpus_rows_requires_forced_rows():
    frame = pd.DataFrame([_corpus_row(row_id=1), _corpus_row(row_id=4)])

    selected = select_corpus_rows(frame, required_row_ids=(4,), max_rows=0)

    assert selected["row_id"].tolist() == [1, 4]
    with pytest.raises(ValueError, match="missing"):
        select_corpus_rows(frame, required_row_ids=(16,), max_rows=0)


def test_select_corpus_rows_refuses_max_rows_that_drop_required_row():
    frame = pd.DataFrame([_corpus_row(row_id=1), _corpus_row(row_id=4)])

    with pytest.raises(ValueError, match="max_rows omitted"):
        select_corpus_rows(frame, required_row_ids=(4,), max_rows=1)


def test_combine_anchors_repeats_rejected_rows_and_offsets_source_index(tmp_path):
    base = tmp_path / "base.npz"
    rejected = tmp_path / "rejected.npz"
    combined = tmp_path / "combined.npz"
    _write_anchor(base, rows=2, source_offset=0)
    _write_anchor(rejected, rows=3, source_offset=0)

    summary = _combine_anchors(
        base_anchor_npz=base,
        rejected_anchor_npz=rejected,
        output_npz=combined,
        rejected_repeat=4,
        rejected_source_index_offset=100000,
    )

    assert summary["combined_rows"] == 14
    anchor = load_trajectory_action_anchor(
        combined,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=128,
        act_dim=3,
    )
    assert anchor.size == 14
    assert int(anchor.source_index[-1]) >= 100000
