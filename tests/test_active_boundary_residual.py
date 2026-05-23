import numpy as np
import pytest
import torch
from torch.distributions import Normal

from autodrift.active_boundary_residual import (
    VIOLATION_GAP_EROSION,
    VIOLATION_NORMAL_COLLISION,
    VIOLATION_WRONG_SAFE,
    active_boundary_weight,
    classify_active_boundary_violation,
)
from autodrift.exact_post_ppo_repair import ExactRepairConfig, exact_active_boundary_terms
from autodrift.intervention_objectives import load_active_boundary_snippets


class _TinyRecurrentPolicy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = torch.nn.Linear(4, 3, bias=False)
        with torch.no_grad():
            self.proj.weight.copy_(
                torch.tensor(
                    [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                    ]
                )
            )

    def forward_recurrent(self, observation, hidden):
        del observation
        mean = self.proj(hidden)
        scale = torch.ones_like(mean) * 0.5
        return Normal(mean, scale), None, hidden


def _active_boundary_arrays(**overrides):
    arrays = {
        "observation": np.zeros((3, 72), dtype=np.float32),
        "normal_hidden": np.asarray(
            [[0.7, 0.0, 0.0, 0.1], [0.6, 0.1, 0.0, 0.2], [0.5, 0.0, 0.1, 0.3]],
            dtype=np.float32,
        ),
        "wrong_hidden": np.asarray(
            [[-0.7, 0.0, 0.0, 0.1], [-0.6, -0.1, 0.0, 0.2], [-0.5, 0.0, -0.1, 0.3]],
            dtype=np.float32,
        ),
        "proof_normal_action": np.asarray(
            [[0.5, 0.0, 0.0], [0.4, 0.1, 0.0], [0.35, 0.0, 0.1]],
            dtype=np.float32,
        ),
        "proof_wrong_action": np.asarray(
            [[-0.5, 0.0, 0.0], [-0.4, -0.1, 0.0], [-0.35, 0.0, -0.1]],
            dtype=np.float32,
        ),
        "candidate_normal_action": np.asarray(
            [[0.45, 0.0, 0.0], [0.35, 0.1, 0.0], [0.3, 0.0, 0.1]],
            dtype=np.float32,
        ),
        "candidate_wrong_action": np.asarray(
            [[0.5, 0.0, 0.0], [0.4, 0.1, 0.0], [0.35, 0.0, 0.1]],
            dtype=np.float32,
        ),
        "normal_margin": np.asarray([0.02, 0.01, -0.001], dtype=np.float32),
        "wrong_history_margin": np.asarray([0.002, -0.003, -0.004], dtype=np.float32),
        "margin_gap": np.asarray([0.018, 0.013, 0.003], dtype=np.float32),
        "violation_type": np.asarray(
            [VIOLATION_WRONG_SAFE, VIOLATION_GAP_EROSION, VIOLATION_NORMAL_COLLISION],
            dtype=np.int64,
        ),
        "weight": np.asarray([1.0, 2.0, 3.0], dtype=np.float32),
        "row_id": np.asarray([0, 1, 2], dtype=np.int64),
        "profile_index": np.asarray([0, 1, 1], dtype=np.int64),
    }
    arrays.update(overrides)
    return arrays


def test_active_boundary_violation_classification_and_weight():
    wrong_safe = {
        "normal_success": "True",
        "normal_margin": 0.02,
        "wrong_history_margin": 0.0015,
        "reference_wrong_history_margin": -0.001,
        "reference_margin_gap": 0.02,
        "margin_gap": 0.005,
    }
    assert classify_active_boundary_violation(wrong_safe) == VIOLATION_WRONG_SAFE
    assert active_boundary_weight(wrong_safe, VIOLATION_WRONG_SAFE) > 0.0015

    gap = dict(wrong_safe, wrong_history_margin=-0.002, reference_wrong_history_margin=-0.004)
    assert classify_active_boundary_violation(gap) == VIOLATION_GAP_EROSION
    assert active_boundary_weight(gap, VIOLATION_GAP_EROSION) == pytest.approx(0.015)

    normal_collision = dict(wrong_safe, normal_success="False", normal_margin=-0.003)
    assert classify_active_boundary_violation(normal_collision) == VIOLATION_NORMAL_COLLISION
    assert active_boundary_weight(normal_collision, VIOLATION_NORMAL_COLLISION) == pytest.approx(0.003)


def test_active_boundary_loader_and_exact_terms_are_finite(tmp_path):
    path = tmp_path / "active_boundary.npz"
    np.savez(path, **_active_boundary_arrays())

    snippets = load_active_boundary_snippets(
        path,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=4,
        act_dim=3,
    )
    assert snippets.size == 3

    terms = exact_active_boundary_terms(_TinyRecurrentPolicy(), snippets, ExactRepairConfig())
    assert set(terms) == {
        "active_boundary_loss",
        "active_boundary_wrong_loss",
        "active_boundary_gap_loss",
        "active_boundary_normal_loss",
    }
    for value in terms.values():
        assert torch.isfinite(value)
        assert float(value.detach().cpu()) >= 0.0


def test_active_boundary_loader_rejects_invalid_actions(tmp_path):
    path = tmp_path / "bad_active_boundary.npz"
    arrays = _active_boundary_arrays()
    arrays["proof_wrong_action"] = arrays["proof_wrong_action"].copy()
    arrays["proof_wrong_action"][0, 0] = 1.1
    np.savez(path, **arrays)

    with pytest.raises(ValueError, match="values must be in"):
        load_active_boundary_snippets(
            path,
            device=torch.device("cpu"),
            obs_dim=72,
            hidden_size=4,
            act_dim=3,
        )
