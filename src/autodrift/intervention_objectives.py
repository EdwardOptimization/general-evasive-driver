"""Training-time intervention objectives for recurrent driver policies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch


@dataclass(frozen=True)
class PairedHiddenSnapshots:
    nominal_observation: torch.Tensor
    perturbed_observation: torch.Tensor
    nominal_hidden: torch.Tensor
    perturbed_hidden: torch.Tensor

    @property
    def size(self) -> int:
        return int(self.nominal_observation.shape[0])


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


def load_paired_hidden_snapshots(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
) -> PairedHiddenSnapshots:
    data = np.load(Path(path))
    required = {
        "nominal_observation",
        "perturbed_observation",
        "nominal_hidden",
        "perturbed_hidden",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"paired hidden snapshot npz missing fields: {missing}")
    nominal_observation = np.asarray(data["nominal_observation"], dtype=np.float32)
    perturbed_observation = np.asarray(data["perturbed_observation"], dtype=np.float32)
    nominal_hidden = np.asarray(data["nominal_hidden"], dtype=np.float32)
    perturbed_hidden = np.asarray(data["perturbed_hidden"], dtype=np.float32)
    if nominal_observation.shape != perturbed_observation.shape:
        raise ValueError("paired hidden observations must have matching shapes")
    if nominal_hidden.shape != perturbed_hidden.shape:
        raise ValueError("paired hidden states must have matching shapes")
    if nominal_observation.ndim != 2 or nominal_observation.shape[1] != obs_dim:
        raise ValueError(
            f"paired hidden observations must have shape (N, {obs_dim}), got {nominal_observation.shape}"
        )
    if nominal_hidden.ndim != 2 or nominal_hidden.shape[1] != hidden_size:
        raise ValueError(f"paired hidden states must have shape (N, {hidden_size}), got {nominal_hidden.shape}")
    if nominal_observation.shape[0] < 1:
        raise ValueError("paired hidden snapshot npz must contain at least one pair")
    return PairedHiddenSnapshots(
        nominal_observation=torch.as_tensor(nominal_observation, dtype=torch.float32, device=device),
        perturbed_observation=torch.as_tensor(perturbed_observation, dtype=torch.float32, device=device),
        nominal_hidden=torch.as_tensor(nominal_hidden, dtype=torch.float32, device=device),
        perturbed_hidden=torch.as_tensor(perturbed_hidden, dtype=torch.float32, device=device),
    )


def paired_hidden_action_contrast_loss(
    model: Any,
    snapshots: PairedHiddenSnapshots,
    *,
    batch_size: int,
    margin: float,
) -> torch.Tensor:
    count = snapshots.size
    batch_count = max(1, min(int(batch_size), count))
    indices = torch.randint(count, (batch_count,), device=snapshots.nominal_observation.device)
    nominal_observation = snapshots.nominal_observation[indices]
    perturbed_observation = snapshots.perturbed_observation[indices]
    nominal_hidden = snapshots.nominal_hidden[indices]
    perturbed_hidden = snapshots.perturbed_hidden[indices]

    nominal_dist, _, _ = model.forward_recurrent(nominal_observation, nominal_hidden)
    nominal_swapped_dist, _, _ = model.forward_recurrent(nominal_observation, perturbed_hidden)
    perturbed_dist, _, _ = model.forward_recurrent(perturbed_observation, perturbed_hidden)
    perturbed_swapped_dist, _, _ = model.forward_recurrent(perturbed_observation, nominal_hidden)
    nominal_distance = torch.linalg.vector_norm(
        torch.tanh(nominal_dist.mean) - torch.tanh(nominal_swapped_dist.mean),
        dim=-1,
    )
    perturbed_distance = torch.linalg.vector_norm(
        torch.tanh(perturbed_dist.mean) - torch.tanh(perturbed_swapped_dist.mean),
        dim=-1,
    )
    distances = torch.cat([nominal_distance, perturbed_distance])
    return torch.nn.functional.softplus(float(margin) - distances).mean()
