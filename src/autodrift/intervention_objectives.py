"""Training-time intervention objectives for recurrent driver policies."""

from __future__ import annotations

import torch


def weighted_mean(values: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
    """Mean with the same zero-weight behavior used by PPO auxiliary losses."""

    return (values * weights).sum() / torch.clamp(weights.sum(), min=1.0)


def positive_advantage_weights(advantages: torch.Tensor) -> torch.Tensor:
    return torch.clamp(advantages.detach(), min=0.0)


def negative_advantage_weights(advantages: torch.Tensor) -> torch.Tensor:
    return torch.clamp(-advantages.detach(), min=0.0)


def logprob_intervention_contrast_loss(
    normal_log_prob: torch.Tensor,
    intervention_log_prob: torch.Tensor,
    advantages: torch.Tensor,
    *,
    margin: float,
) -> torch.Tensor:
    penalty = torch.nn.functional.softplus(intervention_log_prob - normal_log_prob + float(margin))
    return weighted_mean(penalty, positive_advantage_weights(advantages))


def action_mean_margin_contrast_loss(
    normal_action_mean: torch.Tensor,
    intervention_action_mean: torch.Tensor,
    advantages: torch.Tensor,
    *,
    margin: float,
) -> torch.Tensor:
    action_distance = torch.linalg.vector_norm(normal_action_mean - intervention_action_mean, dim=-1)
    penalty = torch.nn.functional.softplus(float(margin) - action_distance)
    return weighted_mean(penalty, positive_advantage_weights(advantages))


def baseline_action_anchor_loss(
    action_mean: torch.Tensor,
    reference_action_mean: torch.Tensor,
    advantages: torch.Tensor,
    *,
    negative_advantage_only: bool,
) -> torch.Tensor:
    action_error = torch.square(action_mean - reference_action_mean.detach()).mean(dim=-1)
    if negative_advantage_only:
        return weighted_mean(action_error, negative_advantage_weights(advantages))
    return action_error.mean()
