import torch

from autodrift.intervention_objectives import (
    action_mean_margin_contrast_loss,
    baseline_action_anchor_loss,
    logprob_intervention_contrast_loss,
    negative_advantage_weights,
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
