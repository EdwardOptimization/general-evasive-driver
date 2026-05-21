from types import SimpleNamespace

import numpy as np
import torch

from autodrift.intervention_objectives import (
    PairedHiddenSnapshots,
    action_mean_margin_contrast_loss,
    baseline_action_anchor_loss,
    load_paired_hidden_snapshots,
    logprob_intervention_contrast_loss,
    negative_advantage_weights,
    paired_hidden_action_contrast_loss,
    positive_advantage_weights,
    weighted_mean,
)


def test_advantage_weight_helpers_detach_and_clip():
    advantages = torch.tensor([-2.0, 0.5, 3.0], requires_grad=True)

    assert torch.allclose(positive_advantage_weights(advantages), torch.tensor([0.0, 0.5, 3.0]))
    assert torch.allclose(negative_advantage_weights(advantages), torch.tensor([2.0, 0.0, 0.0]))
    assert not positive_advantage_weights(advantages).requires_grad
    assert not negative_advantage_weights(advantages).requires_grad


def test_weighted_mean_uses_clamped_denominator_for_zero_weights():
    values = torch.tensor([2.0, 4.0, 8.0])
    weights = torch.zeros(3)

    assert torch.isclose(weighted_mean(values, weights), torch.tensor(0.0))


def test_logprob_intervention_contrast_matches_existing_formula():
    normal_log_prob = torch.tensor([0.2, -0.3, 0.4])
    intervention_log_prob = torch.tensor([0.5, -0.6, 0.7])
    advantages = torch.tensor([1.0, -2.0, 3.0])
    margin = 0.05

    actual = logprob_intervention_contrast_loss(
        normal_log_prob,
        intervention_log_prob,
        advantages,
        margin=margin,
    )
    weights = torch.clamp(advantages.detach(), min=0.0)
    expected = (torch.nn.functional.softplus(intervention_log_prob - normal_log_prob + margin) * weights).sum()
    expected = expected / torch.clamp(weights.sum(), min=1.0)

    assert torch.allclose(actual, expected)


def test_action_mean_margin_contrast_matches_existing_formula():
    normal = torch.tensor([[0.0, 0.0], [1.0, 1.0]])
    intervention = torch.tensor([[0.3, 0.4], [1.0, 1.2]])
    advantages = torch.tensor([2.0, -1.0])
    margin = 0.6

    actual = action_mean_margin_contrast_loss(normal, intervention, advantages, margin=margin)
    distance = torch.linalg.vector_norm(normal - intervention, dim=-1)
    weights = torch.clamp(advantages.detach(), min=0.0)
    expected = (torch.nn.functional.softplus(margin - distance) * weights).sum()
    expected = expected / torch.clamp(weights.sum(), min=1.0)

    assert torch.allclose(actual, expected)


def test_baseline_action_anchor_can_weight_negative_advantage_only():
    action_mean = torch.tensor([[1.0, 0.0], [0.0, 2.0]])
    reference_action_mean = torch.tensor([[0.0, 0.0], [0.0, 0.0]])
    advantages = torch.tensor([1.0, -2.0])

    weighted = baseline_action_anchor_loss(
        action_mean,
        reference_action_mean,
        advantages,
        negative_advantage_only=True,
    )
    unweighted = baseline_action_anchor_loss(
        action_mean,
        reference_action_mean,
        advantages,
        negative_advantage_only=False,
    )

    assert torch.isclose(weighted, torch.tensor(2.0))
    assert torch.isclose(unweighted, torch.tensor(1.25))


def test_load_paired_hidden_snapshots_validates_and_converts_arrays(tmp_path):
    path = tmp_path / "snapshots.npz"
    np.savez(
        path,
        nominal_observation=np.zeros((2, 3), dtype=np.float32),
        perturbed_observation=np.ones((2, 3), dtype=np.float32),
        nominal_hidden=np.zeros((2, 4), dtype=np.float32),
        perturbed_hidden=np.ones((2, 4), dtype=np.float32),
    )

    snapshots = load_paired_hidden_snapshots(path, device=torch.device("cpu"), obs_dim=3, hidden_size=4)

    assert snapshots.size == 2
    assert snapshots.nominal_observation.shape == (2, 3)
    assert snapshots.perturbed_hidden.dtype == torch.float32


def test_paired_hidden_action_contrast_loss_uses_swapped_hidden_states():
    class DummyModel:
        def forward_recurrent(self, observation, hidden):
            mean = observation[:, :2] + hidden[:, :2]
            return SimpleNamespace(mean=mean), None, None

    snapshots = PairedHiddenSnapshots(
        nominal_observation=torch.tensor([[0.0, 0.0], [1.0, 0.0]]),
        perturbed_observation=torch.tensor([[0.5, 0.0], [1.5, 0.0]]),
        nominal_hidden=torch.tensor([[0.0, 0.0], [0.0, 0.0]]),
        perturbed_hidden=torch.tensor([[1.0, 0.0], [1.0, 0.0]]),
    )

    torch.manual_seed(1)
    loss = paired_hidden_action_contrast_loss(DummyModel(), snapshots, batch_size=2, margin=0.1)

    assert torch.isfinite(loss)
    assert loss >= 0.0
