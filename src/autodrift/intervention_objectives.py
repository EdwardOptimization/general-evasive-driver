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


@dataclass(frozen=True)
class OutcomeInterventionSnippets:
    observation: torch.Tensor
    preferred_hidden: torch.Tensor
    rejected_hidden: torch.Tensor
    preferred_action: torch.Tensor
    weight: torch.Tensor

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class RejectedHistoryPreferenceSnippets:
    observation: torch.Tensor
    preferred_hidden: torch.Tensor
    rejected_hidden: torch.Tensor
    preferred_action: torch.Tensor
    rejected_action: torch.Tensor
    preferred_score: torch.Tensor
    rejected_score: torch.Tensor
    score_delta: torch.Tensor
    normal_margin: torch.Tensor
    wrong_history_margin: torch.Tensor
    margin_floor: torch.Tensor
    weight: torch.Tensor
    row_id: torch.Tensor
    group_index: torch.Tensor
    target_index: torch.Tensor
    hard_row: torch.Tensor | None = None
    gap_tail_row: torch.Tensor | None = None
    preferred_branch_weight: torch.Tensor | None = None
    wrong_branch_weight: torch.Tensor | None = None

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class OldKeyRecoverySnippets:
    observation: torch.Tensor
    preferred_hidden: torch.Tensor
    rejected_hidden: torch.Tensor
    recovery_action: torch.Tensor
    rejected_anchor_action: torch.Tensor
    weight: torch.Tensor
    row_id: torch.Tensor

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class CurrentFamilyConflictSnippets:
    observation: torch.Tensor
    preferred_hidden: torch.Tensor
    rejected_hidden: torch.Tensor
    preferred_anchor_action: torch.Tensor
    rejected_boundary_action: torch.Tensor
    weight: torch.Tensor
    row_id: torch.Tensor
    boundary_margin: torch.Tensor

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class ActiveBoundarySnippets:
    observation: torch.Tensor
    normal_hidden: torch.Tensor
    wrong_hidden: torch.Tensor
    proof_normal_action: torch.Tensor
    proof_wrong_action: torch.Tensor
    candidate_normal_action: torch.Tensor
    candidate_wrong_action: torch.Tensor
    normal_margin: torch.Tensor
    wrong_history_margin: torch.Tensor
    margin_gap: torch.Tensor
    violation_type: torch.Tensor
    weight: torch.Tensor
    row_id: torch.Tensor
    profile_index: torch.Tensor

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class ActiveBoundaryV2Snippets:
    observation: torch.Tensor
    normal_hidden: torch.Tensor
    wrong_hidden: torch.Tensor
    proof_normal_action: torch.Tensor
    proof_wrong_action: torch.Tensor
    candidate_normal_action: torch.Tensor
    candidate_wrong_action: torch.Tensor
    normal_margin: torch.Tensor
    wrong_history_margin: torch.Tensor
    margin_gap: torch.Tensor
    reference_wrong_history_margin: torch.Tensor
    reference_margin_gap: torch.Tensor
    wrong_safety_weight: torch.Tensor
    gap_weight: torch.Tensor
    normal_safety_weight: torch.Tensor
    violation_type: torch.Tensor
    row_id: torch.Tensor
    profile_index: torch.Tensor
    window_offset: torch.Tensor

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class SnippetActionAnchor:
    observation: torch.Tensor
    preferred_hidden: torch.Tensor
    rejected_hidden: torch.Tensor
    weight: torch.Tensor
    reference_preferred_action: torch.Tensor
    reference_rejected_action: torch.Tensor
    include_rejected_hidden: bool

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


@dataclass(frozen=True)
class TrajectoryActionAnchor:
    observation: torch.Tensor
    hidden: torch.Tensor
    reference_action: torch.Tensor
    source_index: torch.Tensor
    step_index: torch.Tensor
    weight: torch.Tensor
    radius: torch.Tensor | None = None

    @property
    def size(self) -> int:
        return int(self.observation.shape[0])


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


def squashed_action_log_prob(dist: Any, action: torch.Tensor) -> torch.Tensor:
    clipped = torch.clamp(action.detach(), -1.0 + 1e-6, 1.0 - 1e-6)
    raw = torch.atanh(clipped)
    correction = torch.log(torch.clamp(1.0 - clipped.pow(2), min=1e-6)).sum(dim=-1)
    return dist.log_prob(raw).sum(dim=-1) - correction


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


def load_outcome_intervention_snippets(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> OutcomeInterventionSnippets:
    data = np.load(Path(path))
    required = {
        "observation",
        "preferred_hidden",
        "rejected_hidden",
        "preferred_action",
        "weight",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"outcome intervention snippet npz missing fields: {missing}")
    observation = np.asarray(data["observation"], dtype=np.float32)
    preferred_hidden = np.asarray(data["preferred_hidden"], dtype=np.float32)
    rejected_hidden = np.asarray(data["rejected_hidden"], dtype=np.float32)
    preferred_action = np.asarray(data["preferred_action"], dtype=np.float32)
    weight = np.asarray(data["weight"], dtype=np.float32)
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(f"outcome observations must have shape (N, {obs_dim}), got {observation.shape}")
    if preferred_hidden.shape != rejected_hidden.shape:
        raise ValueError("preferred and rejected hidden states must have matching shapes")
    if preferred_hidden.ndim != 2 or preferred_hidden.shape[1] != hidden_size:
        raise ValueError(f"outcome hidden states must have shape (N, {hidden_size}), got {preferred_hidden.shape}")
    if preferred_action.ndim != 2 or preferred_action.shape[1] != act_dim:
        raise ValueError(f"preferred actions must have shape (N, {act_dim}), got {preferred_action.shape}")
    if weight.ndim != 1 or weight.shape[0] != observation.shape[0]:
        raise ValueError(f"weights must have shape (N,), got {weight.shape}")
    if observation.shape[0] < 1:
        raise ValueError("outcome intervention snippet npz must contain at least one row")
    if not np.all(np.isfinite(weight)):
        raise ValueError("outcome intervention weights must be finite")
    if float(np.max(weight)) <= 0.0:
        raise ValueError("outcome intervention snippets require at least one positive weight")
    return OutcomeInterventionSnippets(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        preferred_hidden=torch.as_tensor(preferred_hidden, dtype=torch.float32, device=device),
        rejected_hidden=torch.as_tensor(rejected_hidden, dtype=torch.float32, device=device),
        preferred_action=torch.as_tensor(preferred_action, dtype=torch.float32, device=device),
        weight=torch.as_tensor(np.clip(weight, 0.0, None), dtype=torch.float32, device=device),
    )


def load_rejected_history_preference_snippets(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> RejectedHistoryPreferenceSnippets:
    data = np.load(Path(path))
    required = {
        "observation",
        "preferred_hidden",
        "rejected_hidden",
        "preferred_action",
        "rejected_action",
        "preferred_score",
        "rejected_score",
        "score_delta",
        "normal_margin",
        "wrong_history_margin",
        "margin_floor",
        "weight",
        "row_id",
        "group_index",
        "target_index",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"rejected history preference npz missing fields: {missing}")

    observation = np.asarray(data["observation"], dtype=np.float32)
    preferred_hidden = np.asarray(data["preferred_hidden"], dtype=np.float32)
    rejected_hidden = np.asarray(data["rejected_hidden"], dtype=np.float32)
    preferred_action = np.asarray(data["preferred_action"], dtype=np.float32)
    rejected_action = np.asarray(data["rejected_action"], dtype=np.float32)
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("rejected history preference npz must contain at least one row")
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(f"preference observations must have shape (N, {obs_dim}), got {observation.shape}")
    if preferred_hidden.shape != rejected_hidden.shape:
        raise ValueError("preferred and rejected hidden states must have matching shapes")
    if preferred_hidden.ndim != 2 or preferred_hidden.shape[1] != hidden_size:
        raise ValueError(f"preference hidden states must have shape (N, {hidden_size}), got {preferred_hidden.shape}")
    for name, value in (("preferred_action", preferred_action), ("rejected_action", rejected_action)):
        if value.ndim != 2 or value.shape[1] != act_dim:
            raise ValueError(f"{name} must have shape (N, {act_dim}), got {value.shape}")
        if int(value.shape[0]) != rows:
            raise ValueError(f"{name} row count {value.shape[0]} does not match {rows}")

    float_arrays = {
        "preferred_score": np.asarray(data["preferred_score"], dtype=np.float32),
        "rejected_score": np.asarray(data["rejected_score"], dtype=np.float32),
        "score_delta": np.asarray(data["score_delta"], dtype=np.float32),
        "normal_margin": np.asarray(data["normal_margin"], dtype=np.float32),
        "wrong_history_margin": np.asarray(data["wrong_history_margin"], dtype=np.float32),
        "margin_floor": np.asarray(data["margin_floor"], dtype=np.float32),
        "weight": np.asarray(data["weight"], dtype=np.float32),
    }
    int_arrays = {
        "row_id": np.asarray(data["row_id"], dtype=np.int64),
        "group_index": np.asarray(data["group_index"], dtype=np.int64),
        "target_index": np.asarray(data["target_index"], dtype=np.int64),
    }
    optional_float_arrays = {
        name: np.asarray(data[name], dtype=np.float32)
        for name in ("preferred_branch_weight", "wrong_branch_weight")
        if name in data.files
    }
    optional_int_arrays = {
        name: np.asarray(data[name], dtype=np.int64) if name in data.files else None
        for name in ("hard_row", "gap_tail_row")
    }
    for name, value in {**float_arrays, **int_arrays}.items():
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"{name} must have shape (N,), got {value.shape}")
    for name, value in optional_float_arrays.items():
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"{name} must have shape (N,), got {value.shape}")
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must be finite")
        if np.any(value < 0.0):
            raise ValueError(f"{name} must be non-negative")
    for name, value in optional_int_arrays.items():
        if value is None:
            continue
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"{name} must have shape (N,), got {value.shape}")
    for name, value in {
        "observation": observation,
        "preferred_hidden": preferred_hidden,
        "rejected_hidden": rejected_hidden,
        "preferred_action": preferred_action,
        "rejected_action": rejected_action,
        **float_arrays,
    }.items():
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must be finite")
    weight = np.clip(float_arrays["weight"], 0.0, None)
    if float(np.max(weight)) <= 0.0:
        raise ValueError("rejected history preference snippets require at least one positive weight")

    return RejectedHistoryPreferenceSnippets(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        preferred_hidden=torch.as_tensor(preferred_hidden, dtype=torch.float32, device=device),
        rejected_hidden=torch.as_tensor(rejected_hidden, dtype=torch.float32, device=device),
        preferred_action=torch.as_tensor(preferred_action, dtype=torch.float32, device=device),
        rejected_action=torch.as_tensor(rejected_action, dtype=torch.float32, device=device),
        preferred_score=torch.as_tensor(float_arrays["preferred_score"], dtype=torch.float32, device=device),
        rejected_score=torch.as_tensor(float_arrays["rejected_score"], dtype=torch.float32, device=device),
        score_delta=torch.as_tensor(float_arrays["score_delta"], dtype=torch.float32, device=device),
        normal_margin=torch.as_tensor(float_arrays["normal_margin"], dtype=torch.float32, device=device),
        wrong_history_margin=torch.as_tensor(float_arrays["wrong_history_margin"], dtype=torch.float32, device=device),
        margin_floor=torch.as_tensor(float_arrays["margin_floor"], dtype=torch.float32, device=device),
        weight=torch.as_tensor(weight, dtype=torch.float32, device=device),
        row_id=torch.as_tensor(int_arrays["row_id"], dtype=torch.long, device=device),
        group_index=torch.as_tensor(int_arrays["group_index"], dtype=torch.long, device=device),
        target_index=torch.as_tensor(int_arrays["target_index"], dtype=torch.long, device=device),
        hard_row=(
            torch.as_tensor(optional_int_arrays["hard_row"], dtype=torch.long, device=device)
            if optional_int_arrays["hard_row"] is not None
            else None
        ),
        gap_tail_row=(
            torch.as_tensor(optional_int_arrays["gap_tail_row"], dtype=torch.long, device=device)
            if optional_int_arrays["gap_tail_row"] is not None
            else None
        ),
        preferred_branch_weight=(
            torch.as_tensor(optional_float_arrays["preferred_branch_weight"], dtype=torch.float32, device=device)
            if "preferred_branch_weight" in optional_float_arrays
            else None
        ),
        wrong_branch_weight=(
            torch.as_tensor(optional_float_arrays["wrong_branch_weight"], dtype=torch.float32, device=device)
            if "wrong_branch_weight" in optional_float_arrays
            else None
        ),
    )


def load_old_key_recovery_snippets(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> OldKeyRecoverySnippets:
    data = np.load(Path(path))
    required = {
        "observation",
        "preferred_hidden",
        "rejected_hidden",
        "recovery_action",
        "rejected_anchor_action",
        "weight",
        "row_id",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"old-key recovery npz missing fields: {missing}")
    observation = np.asarray(data["observation"], dtype=np.float32)
    preferred_hidden = np.asarray(data["preferred_hidden"], dtype=np.float32)
    rejected_hidden = np.asarray(data["rejected_hidden"], dtype=np.float32)
    recovery_action = np.asarray(data["recovery_action"], dtype=np.float32)
    rejected_anchor_action = np.asarray(data["rejected_anchor_action"], dtype=np.float32)
    weight = np.asarray(data["weight"], dtype=np.float32)
    row_id = np.asarray(data["row_id"], dtype=np.int64)
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("old-key recovery npz must contain at least one row")
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(f"old-key recovery observations must have shape (N, {obs_dim}), got {observation.shape}")
    if preferred_hidden.shape != rejected_hidden.shape:
        raise ValueError("old-key recovery preferred and rejected hidden states must have matching shapes")
    if preferred_hidden.ndim != 2 or preferred_hidden.shape[1] != hidden_size:
        raise ValueError(
            f"old-key recovery hidden states must have shape (N, {hidden_size}), got {preferred_hidden.shape}"
        )
    for name, value in (
        ("recovery_action", recovery_action),
        ("rejected_anchor_action", rejected_anchor_action),
    ):
        if value.ndim != 2 or value.shape[1] != act_dim:
            raise ValueError(f"{name} must have shape (N, {act_dim}), got {value.shape}")
        if int(value.shape[0]) != rows:
            raise ValueError(f"{name} row count {value.shape[0]} does not match {rows}")
    for name, value in (("weight", weight), ("row_id", row_id)):
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"{name} must have shape (N,), got {value.shape}")
    for name, value in (
        ("observation", observation),
        ("preferred_hidden", preferred_hidden),
        ("rejected_hidden", rejected_hidden),
        ("recovery_action", recovery_action),
        ("rejected_anchor_action", rejected_anchor_action),
        ("weight", weight),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must be finite")
    if np.any(np.abs(recovery_action) > 1.0 + 1e-6):
        raise ValueError("recovery_action values must be in [-1, 1]")
    if np.any(np.abs(rejected_anchor_action) > 1.0 + 1e-6):
        raise ValueError("rejected_anchor_action values must be in [-1, 1]")
    weight = np.clip(weight, 0.0, None)
    if float(np.max(weight)) <= 0.0:
        raise ValueError("old-key recovery snippets require at least one positive weight")
    return OldKeyRecoverySnippets(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        preferred_hidden=torch.as_tensor(preferred_hidden, dtype=torch.float32, device=device),
        rejected_hidden=torch.as_tensor(rejected_hidden, dtype=torch.float32, device=device),
        recovery_action=torch.as_tensor(recovery_action, dtype=torch.float32, device=device),
        rejected_anchor_action=torch.as_tensor(rejected_anchor_action, dtype=torch.float32, device=device),
        weight=torch.as_tensor(weight, dtype=torch.float32, device=device),
        row_id=torch.as_tensor(row_id, dtype=torch.long, device=device),
    )


def load_current_family_conflict_snippets(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> CurrentFamilyConflictSnippets:
    data = np.load(Path(path))
    required = {
        "observation",
        "preferred_hidden",
        "rejected_hidden",
        "preferred_anchor_action",
        "rejected_boundary_action",
        "weight",
        "row_id",
        "boundary_margin",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"current-family conflict npz missing fields: {missing}")
    observation = np.asarray(data["observation"], dtype=np.float32)
    preferred_hidden = np.asarray(data["preferred_hidden"], dtype=np.float32)
    rejected_hidden = np.asarray(data["rejected_hidden"], dtype=np.float32)
    preferred_anchor_action = np.asarray(data["preferred_anchor_action"], dtype=np.float32)
    rejected_boundary_action = np.asarray(data["rejected_boundary_action"], dtype=np.float32)
    weight = np.asarray(data["weight"], dtype=np.float32)
    row_id = np.asarray(data["row_id"], dtype=np.int64)
    boundary_margin = np.asarray(data["boundary_margin"], dtype=np.float32)
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("current-family conflict npz must contain at least one row")
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(
            f"current-family conflict observations must have shape (N, {obs_dim}), got {observation.shape}"
        )
    if preferred_hidden.shape != rejected_hidden.shape:
        raise ValueError("current-family conflict preferred and rejected hidden states must have matching shapes")
    if preferred_hidden.ndim != 2 or preferred_hidden.shape[1] != hidden_size:
        raise ValueError(
            f"current-family conflict hidden states must have shape (N, {hidden_size}), got {preferred_hidden.shape}"
        )
    for name, value in (
        ("preferred_anchor_action", preferred_anchor_action),
        ("rejected_boundary_action", rejected_boundary_action),
    ):
        if value.ndim != 2 or value.shape[1] != act_dim:
            raise ValueError(f"{name} must have shape (N, {act_dim}), got {value.shape}")
        if int(value.shape[0]) != rows:
            raise ValueError(f"{name} row count {value.shape[0]} does not match {rows}")
    for name, value in (("weight", weight), ("row_id", row_id), ("boundary_margin", boundary_margin)):
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"{name} must have shape (N,), got {value.shape}")
    for name, value in (
        ("observation", observation),
        ("preferred_hidden", preferred_hidden),
        ("rejected_hidden", rejected_hidden),
        ("preferred_anchor_action", preferred_anchor_action),
        ("rejected_boundary_action", rejected_boundary_action),
        ("weight", weight),
        ("boundary_margin", boundary_margin),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must be finite")
    if np.any(np.abs(preferred_anchor_action) > 1.0 + 1e-6):
        raise ValueError("preferred_anchor_action values must be in [-1, 1]")
    if np.any(np.abs(rejected_boundary_action) > 1.0 + 1e-6):
        raise ValueError("rejected_boundary_action values must be in [-1, 1]")
    weight = np.clip(weight, 0.0, None)
    if float(np.max(weight)) <= 0.0:
        raise ValueError("current-family conflict snippets require at least one positive weight")
    return CurrentFamilyConflictSnippets(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        preferred_hidden=torch.as_tensor(preferred_hidden, dtype=torch.float32, device=device),
        rejected_hidden=torch.as_tensor(rejected_hidden, dtype=torch.float32, device=device),
        preferred_anchor_action=torch.as_tensor(preferred_anchor_action, dtype=torch.float32, device=device),
        rejected_boundary_action=torch.as_tensor(rejected_boundary_action, dtype=torch.float32, device=device),
        weight=torch.as_tensor(weight, dtype=torch.float32, device=device),
        row_id=torch.as_tensor(row_id, dtype=torch.long, device=device),
        boundary_margin=torch.as_tensor(boundary_margin, dtype=torch.float32, device=device),
    )


def load_active_boundary_snippets(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> ActiveBoundarySnippets:
    data = np.load(Path(path))
    required = {
        "observation",
        "normal_hidden",
        "wrong_hidden",
        "proof_normal_action",
        "proof_wrong_action",
        "candidate_normal_action",
        "candidate_wrong_action",
        "normal_margin",
        "wrong_history_margin",
        "margin_gap",
        "violation_type",
        "weight",
        "row_id",
        "profile_index",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"active-boundary snippets missing fields: {missing}")
    observation = np.asarray(data["observation"], dtype=np.float32)
    normal_hidden = np.asarray(data["normal_hidden"], dtype=np.float32)
    wrong_hidden = np.asarray(data["wrong_hidden"], dtype=np.float32)
    proof_normal_action = np.asarray(data["proof_normal_action"], dtype=np.float32)
    proof_wrong_action = np.asarray(data["proof_wrong_action"], dtype=np.float32)
    candidate_normal_action = np.asarray(data["candidate_normal_action"], dtype=np.float32)
    candidate_wrong_action = np.asarray(data["candidate_wrong_action"], dtype=np.float32)
    normal_margin = np.asarray(data["normal_margin"], dtype=np.float32)
    wrong_history_margin = np.asarray(data["wrong_history_margin"], dtype=np.float32)
    margin_gap = np.asarray(data["margin_gap"], dtype=np.float32)
    violation_type = np.asarray(data["violation_type"], dtype=np.int64)
    weight = np.asarray(data["weight"], dtype=np.float32)
    row_id = np.asarray(data["row_id"], dtype=np.int64)
    profile_index = np.asarray(data["profile_index"], dtype=np.int64)
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("active-boundary snippets must contain at least one row")
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(f"active-boundary observations must have shape (N, {obs_dim}), got {observation.shape}")
    for name, value in (("normal_hidden", normal_hidden), ("wrong_hidden", wrong_hidden)):
        if value.ndim != 2 or value.shape[1] != hidden_size or int(value.shape[0]) != rows:
            raise ValueError(f"active-boundary {name} must have shape (N, {hidden_size}), got {value.shape}")
    for name, value in (
        ("proof_normal_action", proof_normal_action),
        ("proof_wrong_action", proof_wrong_action),
        ("candidate_normal_action", candidate_normal_action),
        ("candidate_wrong_action", candidate_wrong_action),
    ):
        if value.ndim != 2 or value.shape[1] != act_dim or int(value.shape[0]) != rows:
            raise ValueError(f"active-boundary {name} must have shape (N, {act_dim}), got {value.shape}")
        if np.any(np.abs(value) > 1.0 + 1e-6):
            raise ValueError(f"active-boundary {name} values must be in [-1, 1]")
    for name, value in (
        ("normal_margin", normal_margin),
        ("wrong_history_margin", wrong_history_margin),
        ("margin_gap", margin_gap),
        ("violation_type", violation_type),
        ("weight", weight),
        ("row_id", row_id),
        ("profile_index", profile_index),
    ):
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"active-boundary {name} must have shape (N,), got {value.shape}")
    for name, value in (
        ("observation", observation),
        ("normal_hidden", normal_hidden),
        ("wrong_hidden", wrong_hidden),
        ("proof_normal_action", proof_normal_action),
        ("proof_wrong_action", proof_wrong_action),
        ("candidate_normal_action", candidate_normal_action),
        ("candidate_wrong_action", candidate_wrong_action),
        ("normal_margin", normal_margin),
        ("wrong_history_margin", wrong_history_margin),
        ("margin_gap", margin_gap),
        ("weight", weight),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"active-boundary {name} must be finite")
    if not set(int(value) for value in violation_type.tolist()).issubset({0, 1, 2}):
        raise ValueError("active-boundary violation_type values must be 0, 1, or 2")
    weight = np.clip(weight, 0.0, None)
    if float(np.max(weight)) <= 0.0:
        raise ValueError("active-boundary snippets require at least one positive weight")
    return ActiveBoundarySnippets(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        normal_hidden=torch.as_tensor(normal_hidden, dtype=torch.float32, device=device),
        wrong_hidden=torch.as_tensor(wrong_hidden, dtype=torch.float32, device=device),
        proof_normal_action=torch.as_tensor(proof_normal_action, dtype=torch.float32, device=device),
        proof_wrong_action=torch.as_tensor(proof_wrong_action, dtype=torch.float32, device=device),
        candidate_normal_action=torch.as_tensor(candidate_normal_action, dtype=torch.float32, device=device),
        candidate_wrong_action=torch.as_tensor(candidate_wrong_action, dtype=torch.float32, device=device),
        normal_margin=torch.as_tensor(normal_margin, dtype=torch.float32, device=device),
        wrong_history_margin=torch.as_tensor(wrong_history_margin, dtype=torch.float32, device=device),
        margin_gap=torch.as_tensor(margin_gap, dtype=torch.float32, device=device),
        violation_type=torch.as_tensor(violation_type, dtype=torch.long, device=device),
        weight=torch.as_tensor(weight, dtype=torch.float32, device=device),
        row_id=torch.as_tensor(row_id, dtype=torch.long, device=device),
        profile_index=torch.as_tensor(profile_index, dtype=torch.long, device=device),
    )


def load_active_boundary_v2_snippets(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> ActiveBoundaryV2Snippets:
    data = np.load(Path(path))
    required = {
        "observation",
        "normal_hidden",
        "wrong_hidden",
        "proof_normal_action",
        "proof_wrong_action",
        "candidate_normal_action",
        "candidate_wrong_action",
        "normal_margin",
        "wrong_history_margin",
        "margin_gap",
        "reference_wrong_history_margin",
        "reference_margin_gap",
        "wrong_safety_weight",
        "gap_weight",
        "normal_safety_weight",
        "violation_type",
        "row_id",
        "profile_index",
        "window_offset",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"active-boundary-v2 snippets missing fields: {missing}")
    observation = np.asarray(data["observation"], dtype=np.float32)
    normal_hidden = np.asarray(data["normal_hidden"], dtype=np.float32)
    wrong_hidden = np.asarray(data["wrong_hidden"], dtype=np.float32)
    proof_normal_action = np.asarray(data["proof_normal_action"], dtype=np.float32)
    proof_wrong_action = np.asarray(data["proof_wrong_action"], dtype=np.float32)
    candidate_normal_action = np.asarray(data["candidate_normal_action"], dtype=np.float32)
    candidate_wrong_action = np.asarray(data["candidate_wrong_action"], dtype=np.float32)
    normal_margin = np.asarray(data["normal_margin"], dtype=np.float32)
    wrong_history_margin = np.asarray(data["wrong_history_margin"], dtype=np.float32)
    margin_gap = np.asarray(data["margin_gap"], dtype=np.float32)
    reference_wrong_history_margin = np.asarray(data["reference_wrong_history_margin"], dtype=np.float32)
    reference_margin_gap = np.asarray(data["reference_margin_gap"], dtype=np.float32)
    wrong_safety_weight = np.asarray(data["wrong_safety_weight"], dtype=np.float32)
    gap_weight = np.asarray(data["gap_weight"], dtype=np.float32)
    normal_safety_weight = np.asarray(data["normal_safety_weight"], dtype=np.float32)
    violation_type = np.asarray(data["violation_type"], dtype=np.int64)
    row_id = np.asarray(data["row_id"], dtype=np.int64)
    profile_index = np.asarray(data["profile_index"], dtype=np.int64)
    window_offset = np.asarray(data["window_offset"], dtype=np.int64)
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("active-boundary-v2 snippets must contain at least one row")
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(
            f"active-boundary-v2 observations must have shape (N, {obs_dim}), got {observation.shape}"
        )
    for name, value in (("normal_hidden", normal_hidden), ("wrong_hidden", wrong_hidden)):
        if value.ndim != 2 or value.shape[1] != hidden_size or int(value.shape[0]) != rows:
            raise ValueError(f"active-boundary-v2 {name} must have shape (N, {hidden_size}), got {value.shape}")
    for name, value in (
        ("proof_normal_action", proof_normal_action),
        ("proof_wrong_action", proof_wrong_action),
        ("candidate_normal_action", candidate_normal_action),
        ("candidate_wrong_action", candidate_wrong_action),
    ):
        if value.ndim != 2 or value.shape[1] != act_dim or int(value.shape[0]) != rows:
            raise ValueError(f"active-boundary-v2 {name} must have shape (N, {act_dim}), got {value.shape}")
        if np.any(np.abs(value) > 1.0 + 1e-6):
            raise ValueError(f"active-boundary-v2 {name} values must be in [-1, 1]")
    for name, value in (
        ("normal_margin", normal_margin),
        ("wrong_history_margin", wrong_history_margin),
        ("margin_gap", margin_gap),
        ("reference_wrong_history_margin", reference_wrong_history_margin),
        ("reference_margin_gap", reference_margin_gap),
        ("wrong_safety_weight", wrong_safety_weight),
        ("gap_weight", gap_weight),
        ("normal_safety_weight", normal_safety_weight),
        ("violation_type", violation_type),
        ("row_id", row_id),
        ("profile_index", profile_index),
        ("window_offset", window_offset),
    ):
        if value.ndim != 1 or int(value.shape[0]) != rows:
            raise ValueError(f"active-boundary-v2 {name} must have shape (N,), got {value.shape}")
    for name, value in (
        ("observation", observation),
        ("normal_hidden", normal_hidden),
        ("wrong_hidden", wrong_hidden),
        ("proof_normal_action", proof_normal_action),
        ("proof_wrong_action", proof_wrong_action),
        ("candidate_normal_action", candidate_normal_action),
        ("candidate_wrong_action", candidate_wrong_action),
        ("normal_margin", normal_margin),
        ("wrong_history_margin", wrong_history_margin),
        ("margin_gap", margin_gap),
        ("reference_wrong_history_margin", reference_wrong_history_margin),
        ("reference_margin_gap", reference_margin_gap),
        ("wrong_safety_weight", wrong_safety_weight),
        ("gap_weight", gap_weight),
        ("normal_safety_weight", normal_safety_weight),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"active-boundary-v2 {name} must be finite")
    if not set(int(value) for value in violation_type.tolist()).issubset({0, 1, 2}):
        raise ValueError("active-boundary-v2 violation_type values must be 0, 1, or 2")
    for name, value in (
        ("wrong_safety_weight", wrong_safety_weight),
        ("gap_weight", gap_weight),
        ("normal_safety_weight", normal_safety_weight),
    ):
        if np.any(value < -1e-8):
            raise ValueError(f"active-boundary-v2 {name} must be non-negative")
    if float(np.max(wrong_safety_weight + gap_weight + normal_safety_weight)) <= 0.0:
        raise ValueError("active-boundary-v2 snippets require at least one positive family weight")
    return ActiveBoundaryV2Snippets(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        normal_hidden=torch.as_tensor(normal_hidden, dtype=torch.float32, device=device),
        wrong_hidden=torch.as_tensor(wrong_hidden, dtype=torch.float32, device=device),
        proof_normal_action=torch.as_tensor(proof_normal_action, dtype=torch.float32, device=device),
        proof_wrong_action=torch.as_tensor(proof_wrong_action, dtype=torch.float32, device=device),
        candidate_normal_action=torch.as_tensor(candidate_normal_action, dtype=torch.float32, device=device),
        candidate_wrong_action=torch.as_tensor(candidate_wrong_action, dtype=torch.float32, device=device),
        normal_margin=torch.as_tensor(normal_margin, dtype=torch.float32, device=device),
        wrong_history_margin=torch.as_tensor(wrong_history_margin, dtype=torch.float32, device=device),
        margin_gap=torch.as_tensor(margin_gap, dtype=torch.float32, device=device),
        reference_wrong_history_margin=torch.as_tensor(reference_wrong_history_margin, dtype=torch.float32, device=device),
        reference_margin_gap=torch.as_tensor(reference_margin_gap, dtype=torch.float32, device=device),
        wrong_safety_weight=torch.as_tensor(wrong_safety_weight, dtype=torch.float32, device=device),
        gap_weight=torch.as_tensor(gap_weight, dtype=torch.float32, device=device),
        normal_safety_weight=torch.as_tensor(normal_safety_weight, dtype=torch.float32, device=device),
        violation_type=torch.as_tensor(violation_type, dtype=torch.long, device=device),
        row_id=torch.as_tensor(row_id, dtype=torch.long, device=device),
        profile_index=torch.as_tensor(profile_index, dtype=torch.long, device=device),
        window_offset=torch.as_tensor(window_offset, dtype=torch.long, device=device),
    )


def load_trajectory_action_anchor(
    path: Path | str,
    *,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> TrajectoryActionAnchor:
    data = np.load(Path(path))
    required = {
        "observation",
        "hidden",
        "reference_action",
        "source_index",
        "step_index",
        "weight",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"trajectory action anchor npz missing fields: {missing}")
    observation = np.asarray(data["observation"], dtype=np.float32)
    hidden = np.asarray(data["hidden"], dtype=np.float32)
    reference_action = np.asarray(data["reference_action"], dtype=np.float32)
    source_index = np.asarray(data["source_index"], dtype=np.int64)
    step_index = np.asarray(data["step_index"], dtype=np.int64)
    weight = np.asarray(data["weight"], dtype=np.float32)
    radius = np.asarray(data["radius"], dtype=np.float32) if "radius" in data.files else np.zeros_like(weight)
    if observation.ndim != 2 or observation.shape[1] != obs_dim:
        raise ValueError(f"trajectory observations must have shape (N, {obs_dim}), got {observation.shape}")
    if hidden.ndim != 2 or hidden.shape[1] != hidden_size:
        raise ValueError(f"trajectory hidden states must have shape (N, {hidden_size}), got {hidden.shape}")
    if reference_action.ndim != 2 or reference_action.shape[1] != act_dim:
        raise ValueError(f"trajectory reference actions must have shape (N, {act_dim}), got {reference_action.shape}")
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("trajectory action anchor npz must contain at least one row")
    for name, value in (
        ("hidden", hidden),
        ("reference_action", reference_action),
        ("source_index", source_index),
        ("step_index", step_index),
        ("weight", weight),
        ("radius", radius),
    ):
        if value.ndim != 1 and name in {"source_index", "step_index", "weight"}:
            raise ValueError(f"trajectory {name} must have shape (N,), got {value.shape}")
        if value.ndim != 1 and name == "radius":
            raise ValueError(f"trajectory {name} must have shape (N,), got {value.shape}")
        if int(value.shape[0]) != rows:
            raise ValueError(f"trajectory {name} row count {value.shape[0]} does not match {rows}")
    for name, value in (
        ("observation", observation),
        ("hidden", hidden),
        ("reference_action", reference_action),
        ("weight", weight),
        ("radius", radius),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"trajectory {name} must be finite")
    if float(np.max(weight)) <= 0.0:
        raise ValueError("trajectory action anchor requires at least one positive weight")
    return TrajectoryActionAnchor(
        observation=torch.as_tensor(observation, dtype=torch.float32, device=device),
        hidden=torch.as_tensor(hidden, dtype=torch.float32, device=device),
        reference_action=torch.as_tensor(reference_action, dtype=torch.float32, device=device),
        source_index=torch.as_tensor(source_index, dtype=torch.long, device=device),
        step_index=torch.as_tensor(step_index, dtype=torch.long, device=device),
        weight=torch.as_tensor(np.clip(weight, 0.0, None), dtype=torch.float32, device=device),
        radius=torch.as_tensor(np.clip(radius, 0.0, None), dtype=torch.float32, device=device),
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


def outcome_weighted_intervention_loss(
    model: Any,
    snippets: OutcomeInterventionSnippets,
    *,
    batch_size: int,
    logprob_margin: float,
) -> torch.Tensor:
    count = snippets.size
    batch_count = max(1, min(int(batch_size), count))
    indices = torch.randint(count, (batch_count,), device=snippets.observation.device)
    observation = snippets.observation[indices]
    preferred_hidden = snippets.preferred_hidden[indices]
    rejected_hidden = snippets.rejected_hidden[indices]
    preferred_action = snippets.preferred_action[indices]
    weight = snippets.weight[indices]

    preferred_dist, _, _ = model.forward_recurrent(observation, preferred_hidden)
    rejected_dist, _, _ = model.forward_recurrent(observation, rejected_hidden)
    preferred_log_prob = squashed_action_log_prob(preferred_dist, preferred_action)
    rejected_log_prob = squashed_action_log_prob(rejected_dist, preferred_action)
    penalty = torch.nn.functional.softplus(rejected_log_prob - preferred_log_prob + float(logprob_margin))
    return weighted_mean(penalty, weight.detach())


def rejected_history_preference_components(
    model: Any,
    snippets: RejectedHistoryPreferenceSnippets,
    indices: torch.Tensor,
    *,
    preferred_logprob_margin: float,
    wrong_logprob_margin: float,
    wrong_preference_coef: float,
) -> dict[str, torch.Tensor]:
    observation = snippets.observation[indices]
    preferred_hidden = snippets.preferred_hidden[indices]
    rejected_hidden = snippets.rejected_hidden[indices]
    preferred_action = snippets.preferred_action[indices]
    rejected_action = snippets.rejected_action[indices]

    preferred_dist, _, _ = model.forward_recurrent(observation, preferred_hidden)
    wrong_dist, _, _ = model.forward_recurrent(observation, rejected_hidden)
    logp_cp = squashed_action_log_prob(preferred_dist, preferred_action)
    logp_wp = squashed_action_log_prob(wrong_dist, preferred_action)
    logp_wr = squashed_action_log_prob(wrong_dist, rejected_action)
    preferred_separation = torch.nn.functional.softplus(
        logp_wp - logp_cp + float(preferred_logprob_margin)
    )
    wrong_preference = torch.nn.functional.softplus(logp_wp - logp_wr + float(wrong_logprob_margin))
    combined = preferred_separation + float(wrong_preference_coef) * wrong_preference
    return {
        "logp_correct_preferred": logp_cp,
        "logp_wrong_preferred": logp_wp,
        "logp_wrong_rejected": logp_wr,
        "preferred_separation": preferred_separation,
        "wrong_preference": wrong_preference,
        "combined": combined,
    }


def rejected_history_preference_loss(
    model: Any,
    snippets: RejectedHistoryPreferenceSnippets,
    *,
    batch_size: int,
    preferred_logprob_margin: float,
    wrong_logprob_margin: float,
    wrong_preference_coef: float,
) -> torch.Tensor:
    count = snippets.size
    batch_count = max(1, min(int(batch_size), count))
    indices = torch.randint(count, (batch_count,), device=snippets.observation.device)
    components = rejected_history_preference_components(
        model,
        snippets,
        indices,
        preferred_logprob_margin=preferred_logprob_margin,
        wrong_logprob_margin=wrong_logprob_margin,
        wrong_preference_coef=wrong_preference_coef,
    )
    return weighted_mean(components["combined"], snippets.weight[indices].detach())


def build_snippet_action_anchor(
    reference_model: Any,
    snippets: OutcomeInterventionSnippets,
    *,
    include_rejected_hidden: bool,
) -> SnippetActionAnchor:
    with torch.no_grad():
        preferred_dist, _, _ = reference_model.forward_recurrent(
            snippets.observation,
            snippets.preferred_hidden,
        )
        reference_preferred_action = torch.tanh(preferred_dist.mean).detach()
        reference_rejected_action = torch.empty_like(reference_preferred_action)
        if include_rejected_hidden:
            rejected_dist, _, _ = reference_model.forward_recurrent(
                snippets.observation,
                snippets.rejected_hidden,
            )
            reference_rejected_action = torch.tanh(rejected_dist.mean).detach()
    return SnippetActionAnchor(
        observation=snippets.observation,
        preferred_hidden=snippets.preferred_hidden,
        rejected_hidden=snippets.rejected_hidden,
        weight=snippets.weight.detach(),
        reference_preferred_action=reference_preferred_action,
        reference_rejected_action=reference_rejected_action,
        include_rejected_hidden=include_rejected_hidden,
    )


def snippet_action_anchor_errors(
    model: Any,
    anchor: SnippetActionAnchor,
    indices: torch.Tensor,
) -> torch.Tensor:
    observation = anchor.observation[indices]
    preferred_hidden = anchor.preferred_hidden[indices]
    preferred_dist, _, _ = model.forward_recurrent(observation, preferred_hidden)
    preferred_action = torch.tanh(preferred_dist.mean)
    error = torch.square(preferred_action - anchor.reference_preferred_action[indices].detach()).mean(dim=-1)
    if anchor.include_rejected_hidden:
        rejected_hidden = anchor.rejected_hidden[indices]
        rejected_dist, _, _ = model.forward_recurrent(observation, rejected_hidden)
        rejected_action = torch.tanh(rejected_dist.mean)
        rejected_error = torch.square(
            rejected_action - anchor.reference_rejected_action[indices].detach()
        ).mean(dim=-1)
        error = 0.5 * (error + rejected_error)
    return error


def snippet_action_anchor_loss(
    model: Any,
    anchor: SnippetActionAnchor,
    *,
    batch_size: int,
) -> torch.Tensor:
    count = anchor.size
    batch_count = max(1, min(int(batch_size), count))
    indices = torch.randint(count, (batch_count,), device=anchor.observation.device)
    errors = snippet_action_anchor_errors(model, anchor, indices)
    return weighted_mean(errors, anchor.weight[indices])


def trajectory_action_anchor_loss(
    model: Any,
    anchor: TrajectoryActionAnchor,
    *,
    batch_size: int,
) -> torch.Tensor:
    count = anchor.size
    batch_count = max(1, min(int(batch_size), count))
    indices = torch.randint(count, (batch_count,), device=anchor.observation.device)
    observation = anchor.observation[indices]
    hidden = anchor.hidden[indices]
    reference_action = anchor.reference_action[indices]
    weight = anchor.weight[indices]
    dist, _, _ = model.forward_recurrent(observation, hidden)
    action = torch.tanh(dist.mean)
    action_mse = torch.square(action - reference_action.detach()).mean(dim=-1)
    if anchor.radius is not None:
        radius = anchor.radius[indices].detach()
        action_distance = torch.sqrt(torch.clamp(action_mse, min=0.0))
        error = torch.square(torch.clamp(action_distance - radius, min=0.0))
    else:
        error = action_mse
    return weighted_mean(error, weight.detach())
