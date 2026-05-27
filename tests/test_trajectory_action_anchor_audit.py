from __future__ import annotations

import numpy as np
import pytest
import torch

from autodrift.intervention_objectives import TrajectoryActionAnchor
from autodrift.trajectory_action_anchor_audit import _family_rows, parse_checkpoint_list, trajectory_anchor_mse


class _Dist:
    def __init__(self, mean: torch.Tensor) -> None:
        self.mean = mean


class _Model:
    def forward_recurrent(self, observation: torch.Tensor, hidden: torch.Tensor):
        del hidden
        return _Dist(torch.atanh(torch.clamp(observation[:, :3], -0.9, 0.9))), None, None


def test_trajectory_anchor_mse_matches_weighted_action_error():
    anchor = TrajectoryActionAnchor(
        observation=torch.tensor([[0.1, 0.0, 0.0], [0.2, 0.0, 0.0]], dtype=torch.float32),
        hidden=torch.zeros((2, 4), dtype=torch.float32),
        reference_action=torch.tensor([[0.1, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float32),
        source_index=torch.tensor([0, 1]),
        step_index=torch.tensor([0, 0]),
        weight=torch.tensor([1.0, 3.0], dtype=torch.float32),
        radius=torch.zeros(2),
    )

    mse = trajectory_anchor_mse(_Model(), anchor)

    expected = ((0.0 / 3.0) * 1.0 + ((0.2**2) / 3.0) * 3.0) / 4.0
    assert mse == pytest.approx(expected)


def test_family_rows_reports_weighted_family_mse(tmp_path):
    path = tmp_path / "anchor.npz"
    np.savez(
        path,
        observation=np.zeros((3, 72), dtype=np.float32),
        hidden=np.zeros((3, 128), dtype=np.float32),
        reference_action=np.zeros((3, 3), dtype=np.float32),
        source_index=np.zeros(3, dtype=np.int64),
        step_index=np.zeros(3, dtype=np.int64),
        weight=np.asarray([1.0, 3.0, 2.0], dtype=np.float32),
        family_id=np.asarray([0, 0, 1], dtype=np.int64),
    )

    rows = _family_rows(
        path,
        row_errors=np.asarray([0.1, 0.3, 0.5], dtype=np.float64),
        weights=np.asarray([1.0, 3.0, 2.0], dtype=np.float64),
    )

    assert rows[0]["family_id"] == 0
    assert rows[0]["mse"] == pytest.approx((0.1 + 0.9) / 4.0)
    assert rows[1]["family_id"] == 1
    assert rows[1]["mse"] == pytest.approx(0.5)


def test_parse_checkpoint_list_requires_label_path_pairs():
    specs = parse_checkpoint_list("base=runs/base.pt,candidate=runs/candidate.pt")

    assert [spec.label for spec in specs] == ["base", "candidate"]
    with pytest.raises(Exception):
        parse_checkpoint_list("runs/base.pt")
