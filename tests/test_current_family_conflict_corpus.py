from __future__ import annotations

import numpy as np
import torch

from autodrift.current_family_conflict_corpus import (
    _write_current_family_conflict_corpus,
    conflict_row_weight,
)
from autodrift.intervention_objectives import load_current_family_conflict_snippets


def test_conflict_row_weight_emphasizes_near_boundary_rows():
    near = conflict_row_weight(
        boundary_margin=-1.0e-5,
        source_weight=0.02,
        margin_floor=1.0e-4,
        max_weight=20.0,
    )
    far = conflict_row_weight(
        boundary_margin=-1.0e-2,
        source_weight=0.02,
        margin_floor=1.0e-4,
        max_weight=20.0,
    )

    assert near > far > 0.0


def test_write_current_family_conflict_corpus_loads(tmp_path):
    output = tmp_path / "conflict.npz"
    rows = [
        {
            "row_id": 15,
            "preferred_anchor_action": np.asarray([0.2, -0.1, 0.0], dtype=np.float32),
            "rejected_boundary_action": np.asarray([-0.2, -0.2, 0.1], dtype=np.float32),
            "weight": 3.0,
            "boundary_margin": -1.5e-5,
        }
    ]

    _write_current_family_conflict_corpus(
        output_npz=output,
        observations=[np.zeros(72, dtype=np.float32)],
        preferred_hidden=[np.zeros(128, dtype=np.float32)],
        rejected_hidden=[np.ones(128, dtype=np.float32)],
        rows=rows,
    )
    loaded = load_current_family_conflict_snippets(
        output,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=128,
        act_dim=3,
    )

    assert loaded.size == 1
    assert loaded.row_id.tolist() == [15]
    assert loaded.boundary_margin.item() < 0.0
