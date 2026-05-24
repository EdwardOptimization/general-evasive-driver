"""Capability-supervised hidden repair objective utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn
import torch.nn.functional as F

from autodrift.input_observability_audit import TARGETS


CAPABILITY_TARGETS = TARGETS


class CapabilityHead(nn.Module):
    """Training-only capability head attached to recurrent hidden state."""

    def __init__(self, hidden_size: int, output_dim: int = len(CAPABILITY_TARGETS)) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(int(hidden_size), int(hidden_size)),
            nn.Tanh(),
            nn.Linear(int(hidden_size), int(output_dim)),
        )

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        return self.net(hidden)


@dataclass(frozen=True)
class CapabilityRepairWeights:
    action_bc: float = 1.0
    capability_regression: float = 1.0
    capability_rank: float = 0.25
    action_anchor: float = 0.25


@dataclass(frozen=True)
class CapabilityRepairLoss:
    total: torch.Tensor
    action_bc: torch.Tensor
    capability_regression: torch.Tensor
    capability_rank: torch.Tensor
    action_anchor: torch.Tensor


def _safe_target_std(target_std: torch.Tensor) -> torch.Tensor:
    return torch.clamp(target_std, min=1e-6)


def zscore_values(values: torch.Tensor, *, mean: torch.Tensor, std: torch.Tensor) -> torch.Tensor:
    return (values - mean) / _safe_target_std(std)


def capability_regression_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    *,
    target_mean: torch.Tensor,
    target_std: torch.Tensor,
) -> torch.Tensor:
    normalized_prediction = zscore_values(prediction, mean=target_mean, std=target_std)
    normalized_target = zscore_values(target, mean=target_mean, std=target_std)
    return F.smooth_l1_loss(normalized_prediction, normalized_target)


def capability_rank_loss(
    prediction_left: torch.Tensor,
    prediction_right: torch.Tensor,
    target_left: torch.Tensor,
    target_right: torch.Tensor,
    *,
    target_std: torch.Tensor,
    rank_margin: float = 0.2,
) -> torch.Tensor:
    """Pairwise ranking loss for matched-current capability pairs.

    Each target dimension is ranked independently. Dimensions with nearly equal
    targets contribute approximately zero desired direction.
    """

    target_delta = (target_left - target_right) / _safe_target_std(target_std)
    direction = torch.sign(target_delta)
    prediction_delta = prediction_left - prediction_right
    normalized_prediction_delta = prediction_delta / _safe_target_std(target_std)
    desired_margin = torch.abs(target_delta) * float(rank_margin)
    return F.softplus(desired_margin - direction * normalized_prediction_delta).mean()


def action_mse_loss(action: torch.Tensor, target_action: torch.Tensor) -> torch.Tensor:
    return torch.mean(torch.square(action - target_action))


def capability_repair_loss(
    *,
    action: torch.Tensor,
    target_action: torch.Tensor,
    anchor_action: torch.Tensor,
    capability_prediction: torch.Tensor,
    capability_target: torch.Tensor,
    pair_prediction_left: torch.Tensor,
    pair_prediction_right: torch.Tensor,
    pair_target_left: torch.Tensor,
    pair_target_right: torch.Tensor,
    target_mean: torch.Tensor,
    target_std: torch.Tensor,
    weights: CapabilityRepairWeights | None = None,
) -> CapabilityRepairLoss:
    resolved_weights = weights or CapabilityRepairWeights()
    action_bc = action_mse_loss(action, target_action)
    regression = capability_regression_loss(
        capability_prediction,
        capability_target,
        target_mean=target_mean,
        target_std=target_std,
    )
    ranking = capability_rank_loss(
        pair_prediction_left,
        pair_prediction_right,
        pair_target_left,
        pair_target_right,
        target_std=target_std,
    )
    anchor = action_mse_loss(action, anchor_action)
    total = (
        float(resolved_weights.action_bc) * action_bc
        + float(resolved_weights.capability_regression) * regression
        + float(resolved_weights.capability_rank) * ranking
        + float(resolved_weights.action_anchor) * anchor
    )
    return CapabilityRepairLoss(
        total=total,
        action_bc=action_bc,
        capability_regression=regression,
        capability_rank=ranking,
        action_anchor=anchor,
    )


def build_capability_repair_metadata(base_metadata: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(base_metadata)
    metadata["capability_repair"] = {
        "training_only_targets": list(CAPABILITY_TARGETS),
        "labels_enter_actor_input": False,
        "objective": "future_response_capability_regression_and_matched_current_ranking",
    }
    metadata["ppo_used"] = False
    metadata["promoted"] = False
    return metadata
