from types import SimpleNamespace

import numpy as np
import pytest
import torch

from autodrift.intervention_objectives import (
    OutcomeInterventionSnippets,
    PairedHiddenSnapshots,
    TrajectoryActionAnchor,
    action_mean_margin_contrast_loss,
    baseline_action_anchor_loss,
    load_outcome_intervention_snippets,
    load_paired_hidden_snapshots,
    load_trajectory_action_anchor,
    logprob_intervention_contrast_loss,
    negative_advantage_weights,
    outcome_weighted_intervention_loss,
    paired_hidden_action_contrast_loss,
    positive_advantage_weights,
    squashed_action_log_prob,
    trajectory_action_anchor_loss,
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


def test_load_outcome_intervention_snippets_validates_and_converts_arrays(tmp_path):
    path = tmp_path / "outcome_snippets.npz"
    np.savez(
        path,
        observation=np.zeros((2, 3), dtype=np.float32),
        preferred_hidden=np.zeros((2, 4), dtype=np.float32),
        rejected_hidden=np.ones((2, 4), dtype=np.float32),
        preferred_action=np.zeros((2, 2), dtype=np.float32),
        weight=np.asarray([0.0, 1.5], dtype=np.float32),
    )

    snippets = load_outcome_intervention_snippets(
        path,
        device=torch.device("cpu"),
        obs_dim=3,
        hidden_size=4,
        act_dim=2,
    )

    assert snippets.size == 2
    assert snippets.observation.shape == (2, 3)
    assert snippets.preferred_action.shape == (2, 2)
    assert torch.isclose(snippets.weight.max(), torch.tensor(1.5))


def test_load_trajectory_action_anchor_validates_and_converts_arrays(tmp_path):
    path = tmp_path / "trajectory_anchor.npz"
    np.savez(
        path,
        observation=np.zeros((2, 3), dtype=np.float32),
        hidden=np.zeros((2, 4), dtype=np.float32),
        reference_action=np.zeros((2, 2), dtype=np.float32),
        source_index=np.asarray([0, 1], dtype=np.int64),
        step_index=np.asarray([0, 3], dtype=np.int64),
        weight=np.asarray([0.5, 1.5], dtype=np.float32),
    )

    anchor = load_trajectory_action_anchor(
        path,
        device=torch.device("cpu"),
        obs_dim=3,
        hidden_size=4,
        act_dim=2,
    )

    assert anchor.size == 2
    assert anchor.observation.shape == (2, 3)
    assert anchor.hidden.shape == (2, 4)
    assert anchor.reference_action.shape == (2, 2)
    assert anchor.source_index.dtype == torch.long
    assert torch.isclose(anchor.weight.max(), torch.tensor(1.5))
    assert anchor.radius is not None
    assert torch.allclose(anchor.radius, torch.zeros(2))


def test_load_trajectory_action_anchor_supports_radius(tmp_path):
    path = tmp_path / "trajectory_anchor_radius.npz"
    np.savez(
        path,
        observation=np.zeros((2, 3), dtype=np.float32),
        hidden=np.zeros((2, 4), dtype=np.float32),
        reference_action=np.zeros((2, 2), dtype=np.float32),
        source_index=np.asarray([0, 1], dtype=np.int64),
        step_index=np.asarray([0, 3], dtype=np.int64),
        weight=np.asarray([0.5, 1.5], dtype=np.float32),
        radius=np.asarray([0.1, 0.2], dtype=np.float32),
    )

    anchor = load_trajectory_action_anchor(
        path,
        device=torch.device("cpu"),
        obs_dim=3,
        hidden_size=4,
        act_dim=2,
    )

    assert anchor.radius is not None
    assert anchor.radius.tolist() == pytest.approx([0.1, 0.2])


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


def test_outcome_weighted_intervention_loss_prefers_normal_history_action():
    class DummyDist:
        def __init__(self, mean):
            self.mean = mean

        def log_prob(self, raw_action):
            return -torch.square(raw_action - self.mean)

    class DummyModel:
        def forward_recurrent(self, observation, hidden):
            del observation
            return DummyDist(hidden[:, :2]), None, None

    snippets = OutcomeInterventionSnippets(
        observation=torch.zeros((2, 3)),
        preferred_hidden=torch.zeros((2, 4)),
        rejected_hidden=torch.ones((2, 4)),
        preferred_action=torch.zeros((2, 2)),
        weight=torch.tensor([1.0, 2.0]),
    )

    torch.manual_seed(2)
    loss = outcome_weighted_intervention_loss(
        DummyModel(),
        snippets,
        batch_size=2,
        logprob_margin=0.1,
    )

    preferred_logp = torch.zeros(2)
    rejected_logp = torch.full((2,), -2.0)
    expected = torch.nn.functional.softplus(rejected_logp - preferred_logp + 0.1).mean()
    assert torch.isclose(loss, expected)


def test_trajectory_action_anchor_loss_matches_reference_actions():
    class DummyModel:
        def forward_recurrent(self, observation, hidden):
            mean = torch.atanh(torch.clamp(observation[:, :2] + hidden[:, :2], -0.95, 0.95))
            return type("DummyDist", (), {"mean": mean})(), None, None

    anchor = TrajectoryActionAnchor(
        observation=torch.tensor([[0.1, 0.0, 0.0], [0.2, 0.1, 0.0]]),
        hidden=torch.tensor([[0.0, 0.2, 0.0, 0.0], [0.1, 0.0, 0.0, 0.0]]),
        reference_action=torch.tensor([[0.1, 0.2], [0.3, 0.1]]),
        source_index=torch.tensor([0, 1]),
        step_index=torch.tensor([0, 1]),
        weight=torch.tensor([1.0, 2.0]),
    )

    torch.manual_seed(3)
    loss = trajectory_action_anchor_loss(DummyModel(), anchor, batch_size=2)

    assert torch.isclose(loss, torch.tensor(0.0), atol=1e-6)


def test_trajectory_action_anchor_loss_uses_radius_hinge():
    class DummyModel:
        def forward_recurrent(self, observation, hidden):
            del hidden
            mean = torch.atanh(torch.clamp(observation[:, :2], -0.95, 0.95))
            return type("DummyDist", (), {"mean": mean})(), None, None

    anchor = TrajectoryActionAnchor(
        observation=torch.tensor([[0.3, 0.4, 0.0], [0.3, 0.4, 0.0]]),
        hidden=torch.zeros((2, 4)),
        reference_action=torch.zeros((2, 2)),
        source_index=torch.tensor([0, 1]),
        step_index=torch.tensor([0, 1]),
        weight=torch.tensor([1.0, 1.0]),
        radius=torch.tensor([0.25, 0.25]),
    )

    torch.manual_seed(4)
    loss = trajectory_action_anchor_loss(DummyModel(), anchor, batch_size=2)

    first_distance = torch.sqrt(torch.tensor((0.3**2 + 0.4**2) / 2.0))
    expected = torch.square(torch.clamp(first_distance - 0.25, min=0.0))
    assert torch.isclose(loss, expected, atol=1e-6)


def test_squashed_action_log_prob_handles_bounded_actions():
    dist = torch.distributions.Normal(torch.zeros((1, 2)), torch.ones((1, 2)))
    action = torch.tensor([[0.0, 0.5]])

    log_prob = squashed_action_log_prob(dist, action)

    assert log_prob.shape == (1,)
    assert torch.isfinite(log_prob).all()
