"""Exact post-PPO repair/projection for proof-gated recurrent drivers."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from autodrift.actor_coupling_optimize import actor_coupling_trainable_parameters
from autodrift.artifacts import make_run_dir, to_jsonable, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.intervention_objectives import (
    ActiveBoundarySnippets,
    CurrentFamilyConflictSnippets,
    OldKeyRecoverySnippets,
    OutcomeInterventionSnippets,
    RejectedHistoryPreferenceSnippets,
    SnippetActionAnchor,
    TrajectoryActionAnchor,
    build_snippet_action_anchor,
    load_active_boundary_snippets,
    load_current_family_conflict_snippets,
    load_outcome_intervention_snippets,
    load_old_key_recovery_snippets,
    load_rejected_history_preference_snippets,
    load_trajectory_action_anchor,
    rejected_history_preference_components,
    snippet_action_anchor_errors,
    squashed_action_log_prob,
    weighted_mean,
)
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.rejected_history_preference_objective import PreferenceLossConfig
from autodrift.train_ppo import resolve_device


@dataclass(frozen=True)
class ExactRepairConfig:
    """Configuration for lexicographic exact repair candidate generation."""

    preference: PreferenceLossConfig = field(default_factory=PreferenceLossConfig)
    old_key_preference: PreferenceLossConfig = field(default_factory=PreferenceLossConfig)
    outcome_logprob_margin: float = 0.05
    exact_m297_tolerance: float = 1e-7
    exact_m270_tolerance: float = 1e-7
    exact_old_key_tolerance: float = 1e-7
    lambda_m297: float = 1_000_000.0
    lambda_m270: float = 1_000_000.0
    lambda_old_key: float = 1_000_000.0
    lambda_old_key_anchor: float = 1.0
    lambda_old_key_recovery: float = 1.0
    lambda_old_key_recovery_wrong_anchor: float = 1.0
    lambda_current_family_conflict: float = 1.0
    lambda_current_family_conflict_rejected: float = 1.0
    lambda_replay_trajectory_anchor: float = 0.0
    lambda_active_boundary: float = 0.0
    active_boundary_logprob_margin: float = 0.05
    lambda_action_anchor: float = 100.0
    lambda_param_base: float = 1.0
    lambda_param_raw: float = 0.0
    grad_clip_norm: float = 1.0
    project_recovery_gradient: bool = False
    recovery_projection_epsilon: float = 1e-12


@dataclass(frozen=True)
class TrainableParameterSet:
    parameters: list[torch.nn.Parameter]
    names: list[str]


def parse_alpha_list(raw: str) -> list[float]:
    values = [float(part.strip()) for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("alpha list must contain at least one value")
    for value in values:
        if value < 0.0 or value > 1.0:
            raise argparse.ArgumentTypeError("interpolation alphas must be in [0, 1]")
    return values


def exact_rejected_history_preference_loss(
    model: torch.nn.Module,
    snippets: RejectedHistoryPreferenceSnippets,
    config: PreferenceLossConfig,
) -> torch.Tensor:
    """Evaluate M297-style rejected-history preference on every corpus row."""

    indices = torch.arange(snippets.size, device=snippets.observation.device)
    components = rejected_history_preference_components(
        model,
        snippets,
        indices,
        preferred_logprob_margin=config.preferred_logprob_margin,
        wrong_logprob_margin=config.wrong_logprob_margin,
        wrong_preference_coef=config.wrong_preference_coef,
    )
    return weighted_mean(components["combined"], snippets.weight.detach())


def exact_outcome_intervention_loss(
    model: torch.nn.Module,
    snippets: OutcomeInterventionSnippets,
    *,
    logprob_margin: float,
) -> torch.Tensor:
    """Evaluate M270-style outcome intervention loss on every corpus row."""

    preferred_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.preferred_hidden)  # type: ignore[attr-defined]
    rejected_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.rejected_hidden)  # type: ignore[attr-defined]
    preferred_log_prob = squashed_action_log_prob(preferred_dist, snippets.preferred_action)
    rejected_log_prob = squashed_action_log_prob(rejected_dist, snippets.preferred_action)
    penalty = torch.nn.functional.softplus(rejected_log_prob - preferred_log_prob + float(logprob_margin))
    return weighted_mean(penalty, snippets.weight.detach())


def exact_snippet_action_anchor_loss(
    model: torch.nn.Module,
    anchor: SnippetActionAnchor,
) -> torch.Tensor:
    indices = torch.arange(anchor.size, device=anchor.observation.device)
    errors = snippet_action_anchor_errors(model, anchor, indices)
    return weighted_mean(errors, anchor.weight.detach())


def trajectory_action_anchor_errors(
    model: torch.nn.Module,
    anchor: TrajectoryActionAnchor,
) -> torch.Tensor:
    dist, _, _ = model.forward_recurrent(anchor.observation, anchor.hidden)  # type: ignore[attr-defined]
    action = torch.tanh(dist.mean)
    action_mse = torch.square(action - anchor.reference_action.detach()).mean(dim=-1)
    if anchor.radius is not None:
        action_distance = torch.sqrt(torch.clamp(action_mse, min=0.0))
        error = torch.square(torch.clamp(action_distance - anchor.radius.detach(), min=0.0))
    else:
        error = action_mse
    return error


def exact_trajectory_action_anchor_loss(
    model: torch.nn.Module,
    anchor: TrajectoryActionAnchor,
) -> torch.Tensor:
    error = trajectory_action_anchor_errors(model, anchor)
    return weighted_mean(error, anchor.weight.detach())


def exact_trajectory_action_anchor_loss_by_source(
    model: torch.nn.Module,
    anchor: TrajectoryActionAnchor,
) -> dict[int, torch.Tensor]:
    """Evaluate trajectory-anchor loss separately for each source index."""

    error = trajectory_action_anchor_errors(model, anchor)
    losses: dict[int, torch.Tensor] = {}
    for source in torch.unique(anchor.source_index.detach()).detach().cpu().tolist():
        source_index = int(source)
        mask = anchor.source_index == source_index
        losses[source_index] = weighted_mean(error[mask], anchor.weight[mask].detach())
    return losses


def project_flat_gradient_against_hard_constraints(
    utility_gradient: torch.Tensor,
    hard_gradients: Sequence[torch.Tensor],
    *,
    eps: float = 1e-12,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Remove utility-gradient components that would increase hard constraints.

    For a gradient-descent update ``-g_u``, hard loss ``C_i`` increases to first
    order when ``dot(grad(C_i), g_u) < 0``. In that case we project the utility
    gradient away from the hard-gradient direction.
    """

    utility = utility_gradient.detach().reshape(-1)
    projected = utility.clone()
    input_norm = torch.linalg.vector_norm(projected)
    conflict_count = 0
    active_count = 0
    dot_products: list[float] = []
    conflicting: list[torch.Tensor] = []
    for hard_gradient in hard_gradients:
        hard = hard_gradient.detach().reshape(-1).to(device=projected.device, dtype=projected.dtype)
        if hard.numel() != projected.numel():
            raise ValueError("hard gradient must have the same flattened size as utility gradient")
        hard_norm_sq = torch.dot(hard, hard)
        if float(hard_norm_sq.detach().cpu().item()) <= float(eps):
            dot_products.append(0.0)
            continue
        active_count += 1
        dot = torch.dot(projected, hard)
        dot_value = float(dot.detach().cpu().item())
        dot_products.append(dot_value)
        if dot_value < 0.0:
            conflict_count += 1
            conflicting.append(hard)
    if conflicting:
        basis = torch.stack(conflicting, dim=1)
        gram = basis.T @ basis
        eye = torch.eye(gram.shape[0], dtype=gram.dtype, device=gram.device)
        coeff = torch.linalg.solve(gram + float(eps) * eye, basis.T @ utility)
        projected = utility - basis @ coeff
    output_norm = torch.linalg.vector_norm(projected)
    retained_ratio = float(
        (output_norm / torch.clamp(input_norm, min=float(eps))).detach().cpu().item()
    )
    diagnostics = {
        "active_hard_gradients": int(active_count),
        "conflict_count": int(conflict_count),
        "input_norm": float(input_norm.detach().cpu().item()),
        "output_norm": float(output_norm.detach().cpu().item()),
        "retained_norm_ratio": retained_ratio,
        "dot_products": dot_products,
    }
    return projected, diagnostics


def _flatten_optional_gradients(
    gradients: Sequence[torch.Tensor | None],
    parameters: Sequence[torch.nn.Parameter],
) -> torch.Tensor:
    parts: list[torch.Tensor] = []
    for gradient, parameter in zip(gradients, parameters):
        if gradient is None:
            parts.append(torch.zeros_like(parameter, memory_format=torch.preserve_format).reshape(-1))
        else:
            parts.append(gradient.reshape(-1))
    if not parts:
        return torch.zeros(0, dtype=torch.float32)
    return torch.cat(parts)


def _flat_autograd_gradient(
    loss: torch.Tensor,
    parameters: Sequence[torch.nn.Parameter],
    *,
    retain_graph: bool,
) -> torch.Tensor:
    gradients = torch.autograd.grad(loss, parameters, retain_graph=retain_graph, allow_unused=True)
    return _flatten_optional_gradients(gradients, parameters)


def _add_flat_gradient_to_parameters(
    flat_gradient: torch.Tensor,
    parameters: Sequence[torch.nn.Parameter],
    *,
    scale: float = 1.0,
) -> None:
    offset = 0
    for parameter in parameters:
        size = parameter.numel()
        chunk = flat_gradient[offset : offset + size].view_as(parameter)
        offset += size
        if parameter.grad is None:
            parameter.grad = torch.zeros_like(parameter, memory_format=torch.preserve_format)
        parameter.grad.add_(chunk, alpha=float(scale))
    if offset != int(flat_gradient.numel()):
        raise ValueError("flat gradient size does not match trainable parameters")


def exact_preference_action_anchor_loss(
    model: torch.nn.Module,
    snippets: RejectedHistoryPreferenceSnippets,
    *,
    branch_weighted: bool = False,
) -> torch.Tensor:
    indices = torch.arange(snippets.size, device=snippets.observation.device)
    observation = snippets.observation[indices]
    preferred_dist, _, _ = model.forward_recurrent(observation, snippets.preferred_hidden[indices])  # type: ignore[attr-defined]
    rejected_dist, _, _ = model.forward_recurrent(observation, snippets.rejected_hidden[indices])  # type: ignore[attr-defined]
    preferred_error = torch.square(
        torch.tanh(preferred_dist.mean) - snippets.preferred_action[indices].detach()
    ).mean(dim=-1)
    rejected_error = torch.square(
        torch.tanh(rejected_dist.mean) - snippets.rejected_action[indices].detach()
    ).mean(dim=-1)
    if branch_weighted:
        preferred_weight, wrong_weight = _old_key_branch_weights(snippets, indices)
        return weighted_mean(
            preferred_weight.detach() * preferred_error + wrong_weight.detach() * rejected_error,
            snippets.weight.detach(),
        )
    return weighted_mean(0.5 * (preferred_error + rejected_error), snippets.weight.detach())


def _old_key_branch_weights(
    snippets: RejectedHistoryPreferenceSnippets,
    indices: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    if snippets.preferred_branch_weight is None:
        preferred = torch.ones_like(snippets.weight[indices])
    else:
        preferred = snippets.preferred_branch_weight[indices]
    if snippets.wrong_branch_weight is None:
        wrong = torch.ones_like(snippets.weight[indices])
    else:
        wrong = snippets.wrong_branch_weight[indices]
    return preferred, wrong


def exact_old_key_surrogate_terms(
    model: torch.nn.Module,
    snippets: RejectedHistoryPreferenceSnippets,
    config: ExactRepairConfig,
) -> dict[str, torch.Tensor]:
    if snippets.preferred_branch_weight is None and snippets.wrong_branch_weight is None:
        preference = exact_rejected_history_preference_loss(model, snippets, config.old_key_preference)
        anchor = exact_preference_action_anchor_loss(model, snippets)
        surrogate = preference + float(config.lambda_old_key_anchor) * anchor
        return {
            "old_key_surrogate_loss": surrogate,
            "old_key_preference_loss": preference,
            "old_key_action_anchor_loss": anchor,
        }
    indices = torch.arange(snippets.size, device=snippets.observation.device)
    components = rejected_history_preference_components(
        model,
        snippets,
        indices,
        preferred_logprob_margin=config.old_key_preference.preferred_logprob_margin,
        wrong_logprob_margin=config.old_key_preference.wrong_logprob_margin,
        wrong_preference_coef=1.0,
    )
    preferred_weight, wrong_weight = _old_key_branch_weights(snippets, indices)
    preference = weighted_mean(
        preferred_weight.detach() * components["preferred_separation"]
        + float(config.old_key_preference.wrong_preference_coef)
        * wrong_weight.detach()
        * components["wrong_preference"],
        snippets.weight.detach(),
    )
    anchor = exact_preference_action_anchor_loss(model, snippets, branch_weighted=True)
    surrogate = preference + float(config.lambda_old_key_anchor) * anchor
    return {
        "old_key_surrogate_loss": surrogate,
        "old_key_preference_loss": preference,
        "old_key_action_anchor_loss": anchor,
    }


def exact_old_key_recovery_terms(
    model: torch.nn.Module,
    snippets: OldKeyRecoverySnippets,
    config: ExactRepairConfig,
) -> dict[str, torch.Tensor]:
    preferred_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.preferred_hidden)  # type: ignore[attr-defined]
    wrong_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.rejected_hidden)  # type: ignore[attr-defined]
    preferred_error = torch.square(torch.tanh(preferred_dist.mean) - snippets.recovery_action.detach()).mean(dim=-1)
    wrong_anchor_error = torch.square(
        torch.tanh(wrong_dist.mean) - snippets.rejected_anchor_action.detach()
    ).mean(dim=-1)
    preferred_loss = weighted_mean(preferred_error, snippets.weight.detach())
    wrong_anchor_loss = weighted_mean(wrong_anchor_error, snippets.weight.detach())
    recovery_loss = preferred_loss + float(config.lambda_old_key_recovery_wrong_anchor) * wrong_anchor_loss
    return {
        "old_key_recovery_loss": recovery_loss,
        "old_key_recovery_preferred_loss": preferred_loss,
        "old_key_recovery_wrong_anchor_loss": wrong_anchor_loss,
    }


def exact_current_family_conflict_terms(
    model: torch.nn.Module,
    snippets: CurrentFamilyConflictSnippets,
    config: ExactRepairConfig,
) -> dict[str, torch.Tensor]:
    preferred_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.preferred_hidden)  # type: ignore[attr-defined]
    wrong_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.rejected_hidden)  # type: ignore[attr-defined]
    preferred_error = torch.square(
        torch.tanh(preferred_dist.mean) - snippets.preferred_anchor_action.detach()
    ).mean(dim=-1)
    rejected_error = torch.square(
        torch.tanh(wrong_dist.mean) - snippets.rejected_boundary_action.detach()
    ).mean(dim=-1)
    preferred_loss = weighted_mean(preferred_error, snippets.weight.detach())
    rejected_loss = weighted_mean(rejected_error, snippets.weight.detach())
    conflict_loss = preferred_loss + float(config.lambda_current_family_conflict_rejected) * rejected_loss
    return {
        "current_family_conflict_loss": conflict_loss,
        "current_family_conflict_preferred_loss": preferred_loss,
        "current_family_conflict_rejected_loss": rejected_loss,
    }


def _masked_weighted_mean(values: torch.Tensor, weights: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    if bool(mask.any()):
        return weighted_mean(values[mask], weights[mask].detach())
    return torch.zeros((), dtype=values.dtype, device=values.device)


def exact_active_boundary_terms(
    model: torch.nn.Module,
    snippets: ActiveBoundarySnippets,
    config: ExactRepairConfig,
) -> dict[str, torch.Tensor]:
    normal_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.normal_hidden)  # type: ignore[attr-defined]
    wrong_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.wrong_hidden)  # type: ignore[attr-defined]
    margin = float(config.active_boundary_logprob_margin)

    proof_wrong_log_prob = squashed_action_log_prob(wrong_dist, snippets.proof_wrong_action)
    candidate_wrong_log_prob = squashed_action_log_prob(wrong_dist, snippets.candidate_wrong_action)
    wrong_preference = torch.nn.functional.softplus(
        candidate_wrong_log_prob - proof_wrong_log_prob + margin
    )

    proof_normal_log_prob = squashed_action_log_prob(normal_dist, snippets.proof_normal_action)
    wrong_normal_log_prob = squashed_action_log_prob(wrong_dist, snippets.proof_normal_action)
    gap_separation = torch.nn.functional.softplus(wrong_normal_log_prob - proof_normal_log_prob + margin)

    normal_action = torch.tanh(normal_dist.mean)
    normal_anchor = torch.square(normal_action - snippets.proof_normal_action.detach()).mean(dim=-1)

    wrong_mask = snippets.violation_type == 0
    gap_mask = snippets.violation_type == 1
    normal_mask = snippets.violation_type == 2
    combined = torch.zeros_like(snippets.weight)
    combined = torch.where(wrong_mask, wrong_preference, combined)
    combined = torch.where(gap_mask, gap_separation + wrong_preference, combined)
    combined = torch.where(normal_mask, normal_anchor, combined)
    return {
        "active_boundary_loss": weighted_mean(combined, snippets.weight.detach()),
        "active_boundary_wrong_loss": _masked_weighted_mean(wrong_preference, snippets.weight, wrong_mask),
        "active_boundary_gap_loss": _masked_weighted_mean(
            gap_separation + wrong_preference,
            snippets.weight,
            gap_mask,
        ),
        "active_boundary_normal_loss": _masked_weighted_mean(normal_anchor, snippets.weight, normal_mask),
    }


def trainable_parameter_items(
    model: torch.nn.Module,
    *,
    train_scope: str,
    train_log_std: bool,
) -> TrainableParameterSet:
    if train_scope not in {"all", "actor_coupling"}:
        raise ValueError("train_scope must be 'all' or 'actor_coupling'")
    if train_scope == "actor_coupling":
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        selected = actor_coupling_trainable_parameters(model)  # type: ignore[arg-type]
        selected_ids = {id(parameter) for parameter in selected}
        names = []
        parameters = []
        for name, parameter in model.named_parameters():
            if id(parameter) in selected_ids:
                parameter.requires_grad_(True)
                names.append(name)
                parameters.append(parameter)
        if train_log_std and hasattr(model, "log_std"):
            log_std = getattr(model, "log_std")
            log_std.requires_grad_(True)
            if all(id(parameter) != id(log_std) for parameter in parameters):
                names.append("log_std")
                parameters.append(log_std)
        return TrainableParameterSet(parameters=parameters, names=names)

    for parameter in model.parameters():
        parameter.requires_grad_(True)
    if not train_log_std and hasattr(model, "log_std"):
        getattr(model, "log_std").requires_grad_(False)
    names = []
    parameters = []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            names.append(name)
            parameters.append(parameter)
    return TrainableParameterSet(parameters=parameters, names=names)


def parameter_l2_to_reference(
    model: torch.nn.Module,
    reference_state: dict[str, torch.Tensor],
    names: list[str],
) -> torch.Tensor:
    values = []
    for name, parameter in model.named_parameters():
        if name not in names:
            continue
        reference = reference_state[name].to(device=parameter.device, dtype=parameter.dtype)
        values.append(torch.square(parameter - reference.detach()).mean())
    if not values:
        device = next(model.parameters()).device
        return torch.zeros((), dtype=torch.float32, device=device)
    return torch.stack(values).mean()


def interpolate_model_state(
    model: torch.nn.Module,
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    *,
    alpha: float,
) -> None:
    """Load base -> raw linear interpolation into ``model``."""

    alpha_value = float(alpha)
    if alpha_value < 0.0 or alpha_value > 1.0:
        raise ValueError("alpha must be in [0, 1]")
    interpolated: dict[str, torch.Tensor] = {}
    for name, base_tensor in base_state.items():
        if name not in raw_state:
            raise ValueError(f"raw checkpoint is missing state key {name!r}")
        raw_tensor = raw_state[name]
        if base_tensor.shape != raw_tensor.shape:
            raise ValueError(f"state shape mismatch for {name!r}: {base_tensor.shape} vs {raw_tensor.shape}")
        if torch.is_floating_point(base_tensor):
            interpolated[name] = (1.0 - alpha_value) * base_tensor + alpha_value * raw_tensor
        else:
            interpolated[name] = base_tensor.clone()
    model.load_state_dict(interpolated)


def load_repair_corpora(
    *,
    preference_npz: Path,
    outcome_npz: Path,
    device: torch.device,
    obs_dim: int,
    hidden_size: int,
    act_dim: int,
) -> tuple[RejectedHistoryPreferenceSnippets, OutcomeInterventionSnippets]:
    preference = load_rejected_history_preference_snippets(
        preference_npz,
        device=device,
        obs_dim=obs_dim,
        hidden_size=hidden_size,
        act_dim=act_dim,
    )
    outcome = load_outcome_intervention_snippets(
        outcome_npz,
        device=device,
        obs_dim=obs_dim,
        hidden_size=hidden_size,
        act_dim=act_dim,
    )
    return preference, outcome


def exact_loss_summary(
    *,
    label: str,
    checkpoint: Path | str,
    model: torch.nn.Module,
    preference: RejectedHistoryPreferenceSnippets,
    outcome: OutcomeInterventionSnippets,
    config: ExactRepairConfig,
    old_key: RejectedHistoryPreferenceSnippets | None = None,
    old_key_recovery: OldKeyRecoverySnippets | None = None,
    current_family_conflict: CurrentFamilyConflictSnippets | None = None,
    replay_trajectory_anchor: TrajectoryActionAnchor | None = None,
    active_boundary: ActiveBoundarySnippets | None = None,
) -> dict[str, Any]:
    with torch.no_grad():
        m297 = exact_rejected_history_preference_loss(model, preference, config.preference)
        m270 = exact_outcome_intervention_loss(
            model,
            outcome,
            logprob_margin=config.outcome_logprob_margin,
        )
        old_key_terms = exact_old_key_surrogate_terms(model, old_key, config) if old_key is not None else None
        recovery_terms = (
            exact_old_key_recovery_terms(model, old_key_recovery, config)
            if old_key_recovery is not None
            else None
        )
        conflict_terms = (
            exact_current_family_conflict_terms(model, current_family_conflict, config)
            if current_family_conflict is not None
            else None
        )
        replay_trajectory_anchor_loss = (
            exact_trajectory_action_anchor_loss(model, replay_trajectory_anchor)
            if replay_trajectory_anchor is not None
            else None
        )
        active_boundary_terms = (
            exact_active_boundary_terms(model, active_boundary, config)
            if active_boundary is not None
            else None
        )
    summary = {
        "policy": label,
        "checkpoint": str(checkpoint),
        "exact_m297_loss": float(m297.detach().cpu().item()),
        "exact_m270_loss": float(m270.detach().cpu().item()),
        "preference_rows": int(preference.size),
        "outcome_rows": int(outcome.size),
    }
    if old_key_terms is not None:
        summary.update(
            {
                "old_key_rows": int(old_key.size) if old_key is not None else 0,
                **{name: float(value.detach().cpu().item()) for name, value in old_key_terms.items()},
            }
        )
    if recovery_terms is not None:
        summary.update(
            {
                "old_key_recovery_rows": int(old_key_recovery.size) if old_key_recovery is not None else 0,
                **{name: float(value.detach().cpu().item()) for name, value in recovery_terms.items()},
            }
        )
    if conflict_terms is not None:
        summary.update(
            {
                "current_family_conflict_rows": int(current_family_conflict.size)
                if current_family_conflict is not None
                else 0,
                **{name: float(value.detach().cpu().item()) for name, value in conflict_terms.items()},
            }
        )
    if replay_trajectory_anchor_loss is not None:
        summary.update(
            {
                "replay_trajectory_anchor_rows": int(replay_trajectory_anchor.size)
                if replay_trajectory_anchor is not None
                else 0,
                "replay_trajectory_anchor_loss": float(replay_trajectory_anchor_loss.detach().cpu().item()),
            }
        )
    if active_boundary_terms is not None:
        summary.update(
            {
                "active_boundary_rows": int(active_boundary.size) if active_boundary is not None else 0,
                **{name: float(value.detach().cpu().item()) for name, value in active_boundary_terms.items()},
            }
        )
    return summary


def repair_loss_terms(
    *,
    model: torch.nn.Module,
    preference: RejectedHistoryPreferenceSnippets,
    outcome: OutcomeInterventionSnippets,
    old_key: RejectedHistoryPreferenceSnippets | None = None,
    old_key_recovery: OldKeyRecoverySnippets | None = None,
    current_family_conflict: CurrentFamilyConflictSnippets | None = None,
    replay_trajectory_anchor: TrajectoryActionAnchor | None = None,
    active_boundary: ActiveBoundarySnippets | None = None,
    anchor: SnippetActionAnchor,
    base_m297: float,
    base_m270: float,
    base_old_key: float | None = None,
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    trainable_names: list[str],
    config: ExactRepairConfig,
) -> dict[str, torch.Tensor]:
    m297 = exact_rejected_history_preference_loss(model, preference, config.preference)
    m270 = exact_outcome_intervention_loss(
        model,
        outcome,
        logprob_margin=config.outcome_logprob_margin,
    )
    hinge297 = torch.relu(m297 - float(base_m297) - float(config.exact_m297_tolerance))
    hinge270 = torch.relu(m270 - float(base_m270) - float(config.exact_m270_tolerance))
    if old_key is not None:
        old_key_terms = exact_old_key_surrogate_terms(model, old_key, config)
        old_key_surrogate = old_key_terms["old_key_surrogate_loss"]
        base_old_key_value = float(base_old_key if base_old_key is not None else old_key_surrogate.detach().cpu().item())
        hinge_old_key = torch.relu(
            old_key_surrogate - base_old_key_value - float(config.exact_old_key_tolerance)
        )
    else:
        device = m297.device
        old_key_terms = {
            "old_key_surrogate_loss": torch.zeros((), dtype=torch.float32, device=device),
            "old_key_preference_loss": torch.zeros((), dtype=torch.float32, device=device),
            "old_key_action_anchor_loss": torch.zeros((), dtype=torch.float32, device=device),
        }
        hinge_old_key = torch.zeros((), dtype=torch.float32, device=device)
    if old_key_recovery is not None:
        recovery_terms = exact_old_key_recovery_terms(model, old_key_recovery, config)
    else:
        device = m297.device
        recovery_terms = {
            "old_key_recovery_loss": torch.zeros((), dtype=torch.float32, device=device),
            "old_key_recovery_preferred_loss": torch.zeros((), dtype=torch.float32, device=device),
            "old_key_recovery_wrong_anchor_loss": torch.zeros((), dtype=torch.float32, device=device),
        }
    if current_family_conflict is not None:
        conflict_terms = exact_current_family_conflict_terms(model, current_family_conflict, config)
    else:
        device = m297.device
        conflict_terms = {
            "current_family_conflict_loss": torch.zeros((), dtype=torch.float32, device=device),
            "current_family_conflict_preferred_loss": torch.zeros((), dtype=torch.float32, device=device),
            "current_family_conflict_rejected_loss": torch.zeros((), dtype=torch.float32, device=device),
        }
    if replay_trajectory_anchor is not None:
        replay_trajectory_anchor_loss = exact_trajectory_action_anchor_loss(model, replay_trajectory_anchor)
    else:
        replay_trajectory_anchor_loss = torch.zeros((), dtype=torch.float32, device=m297.device)
    if active_boundary is not None:
        active_boundary_terms = exact_active_boundary_terms(model, active_boundary, config)
    else:
        device = m297.device
        active_boundary_terms = {
            "active_boundary_loss": torch.zeros((), dtype=torch.float32, device=device),
            "active_boundary_wrong_loss": torch.zeros((), dtype=torch.float32, device=device),
            "active_boundary_gap_loss": torch.zeros((), dtype=torch.float32, device=device),
            "active_boundary_normal_loss": torch.zeros((), dtype=torch.float32, device=device),
        }
    action_anchor = exact_snippet_action_anchor_loss(model, anchor)
    param_base = parameter_l2_to_reference(model, base_state, trainable_names)
    param_raw = parameter_l2_to_reference(model, raw_state, trainable_names)
    total = (
        float(config.lambda_m297) * hinge297.square()
        + float(config.lambda_m270) * hinge270.square()
        + float(config.lambda_old_key) * hinge_old_key.square()
        + float(config.lambda_old_key_recovery) * recovery_terms["old_key_recovery_loss"]
        + float(config.lambda_current_family_conflict) * conflict_terms["current_family_conflict_loss"]
        + float(config.lambda_replay_trajectory_anchor) * replay_trajectory_anchor_loss
        + float(config.lambda_active_boundary) * active_boundary_terms["active_boundary_loss"]
        + float(config.lambda_action_anchor) * action_anchor
        + float(config.lambda_param_base) * param_base
        + float(config.lambda_param_raw) * param_raw
    )
    return {
        "total_loss": total,
        "exact_m297_loss": m297,
        "exact_m270_loss": m270,
        "hinge_m297": hinge297,
        "hinge_m270": hinge270,
        "hinge_old_key": hinge_old_key,
        **old_key_terms,
        **recovery_terms,
        **conflict_terms,
        "replay_trajectory_anchor_loss": replay_trajectory_anchor_loss,
        **active_boundary_terms,
        "action_anchor_loss": action_anchor,
        "param_l2_to_base": param_base,
        "param_l2_to_raw": param_raw,
    }


def _tensor_value(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())


def _load_state(checkpoint: dict[str, Any], device: torch.device) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().to(device=device) for name, tensor in checkpoint["model_state"].items()}


def _clone_model_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}


def _add_exact_gate_fields(
    row: dict[str, Any],
    *,
    base_m297: float,
    base_m270: float,
    config: ExactRepairConfig,
    base_old_key: float | None = None,
) -> dict[str, Any]:
    m297_delta = float(row["exact_m297_loss"]) - float(base_m297)
    m270_delta = float(row["exact_m270_loss"]) - float(base_m270)
    row["exact_m297_delta_vs_base"] = m297_delta
    row["exact_m270_delta_vs_base"] = m270_delta
    row["exact_m297_no_regression"] = bool(m297_delta <= float(config.exact_m297_tolerance))
    row["exact_m270_no_regression"] = bool(m270_delta <= float(config.exact_m270_tolerance))
    old_key_pass = True
    old_key_violation = 0.0
    if base_old_key is not None and "old_key_surrogate_loss" in row:
        old_key_delta = float(row["old_key_surrogate_loss"]) - float(base_old_key)
        row["old_key_surrogate_delta_vs_base"] = old_key_delta
        row["old_key_surrogate_no_regression"] = bool(old_key_delta <= float(config.exact_old_key_tolerance))
        old_key_pass = bool(row["old_key_surrogate_no_regression"])
        old_key_violation = max(0.0, old_key_delta - float(config.exact_old_key_tolerance))
    row["exact_lexicographic_pass"] = bool(
        row["exact_m297_no_regression"] and row["exact_m270_no_regression"] and old_key_pass
    )
    row["positive_violation"] = float(
        max(0.0, m297_delta - float(config.exact_m297_tolerance))
        + max(0.0, m270_delta - float(config.exact_m270_tolerance))
        + old_key_violation
    )
    return row


def _repair_metrics_row(
    *,
    step: int,
    metric_phase: str,
    terms: dict[str, torch.Tensor],
    grad_norm: float,
    learning_rate: float,
    base_m297: float,
    base_m270: float,
    base_old_key: float | None,
    config: ExactRepairConfig,
) -> dict[str, Any]:
    row = {
        "step": int(step),
        "metric_phase": metric_phase,
        **{name: _tensor_value(value) for name, value in terms.items()},
        "grad_norm": float(grad_norm),
        "learning_rate": float(learning_rate),
    }
    return _add_exact_gate_fields(
        row,
        base_m297=base_m297,
        base_m270=base_m270,
        base_old_key=base_old_key,
        config=config,
    )


def _backward_repair_terms(
    *,
    model: torch.nn.Module,
    terms: dict[str, torch.Tensor],
    trainable_parameters: Sequence[torch.nn.Parameter],
    config: ExactRepairConfig,
    replay_trajectory_anchor: TrajectoryActionAnchor | None,
) -> dict[str, float | int]:
    if not bool(config.project_recovery_gradient) or float(config.lambda_old_key_recovery) <= 0.0:
        terms["total_loss"].backward()
        return {}
    utility_loss = terms["old_key_recovery_loss"]
    if not bool(utility_loss.requires_grad):
        terms["total_loss"].backward()
        return {}

    hard_total = terms["total_loss"] - float(config.lambda_old_key_recovery) * utility_loss
    hard_total.backward(retain_graph=True)
    utility_gradient = _flat_autograd_gradient(
        utility_loss,
        trainable_parameters,
        retain_graph=True,
    )
    hard_losses = [
        terms["hinge_m297"].square(),
        terms["hinge_m270"].square(),
        terms["hinge_old_key"].square(),
        terms["current_family_conflict_loss"],
    ]
    if replay_trajectory_anchor is not None:
        hard_losses.extend(exact_trajectory_action_anchor_loss_by_source(model, replay_trajectory_anchor).values())
    hard_gradients = [
        _flat_autograd_gradient(loss, trainable_parameters, retain_graph=True)
        for loss in hard_losses
        if bool(loss.requires_grad)
    ]
    projected, diagnostics = project_flat_gradient_against_hard_constraints(
        utility_gradient,
        hard_gradients,
        eps=float(config.recovery_projection_epsilon),
    )
    _add_flat_gradient_to_parameters(
        projected,
        trainable_parameters,
        scale=float(config.lambda_old_key_recovery),
    )
    return {
        "recovery_projection_active_hard_gradients": int(diagnostics["active_hard_gradients"]),
        "recovery_projection_conflict_count": int(diagnostics["conflict_count"]),
        "recovery_projection_input_norm": float(diagnostics["input_norm"]),
        "recovery_projection_output_norm": float(diagnostics["output_norm"]),
        "recovery_projection_retained_norm_ratio": float(diagnostics["retained_norm_ratio"]),
    }


def _repair_selection_key(row: dict[str, Any]) -> tuple[int, float, float, float, int]:
    feasible_rank = 0 if bool(row.get("exact_lexicographic_pass")) else 1
    return (
        feasible_rank,
        float(row.get("positive_violation", 0.0)),
        float(row.get("total_loss", 0.0)),
        float(row.get("param_l2_to_base", 0.0)),
        int(row.get("step", 0)),
    )


def _select_best_repair_step(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("repair selection requires at least one metric row")
    return min(rows, key=_repair_selection_key)


def _line_search_rows(
    *,
    model: torch.nn.Module,
    base_checkpoint: Path,
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    preference: RejectedHistoryPreferenceSnippets,
    outcome: OutcomeInterventionSnippets,
    old_key: RejectedHistoryPreferenceSnippets | None,
    old_key_recovery: OldKeyRecoverySnippets | None,
    current_family_conflict: CurrentFamilyConflictSnippets | None,
    replay_trajectory_anchor: TrajectoryActionAnchor | None,
    active_boundary: ActiveBoundarySnippets | None,
    config: ExactRepairConfig,
    alphas: list[float],
    base_m297: float,
    base_m270: float,
    base_old_key: float | None,
) -> tuple[float, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    best_alpha = 0.0
    best_violation: float | None = None
    best_pass_alpha = 0.0
    for alpha in sorted(set(float(value) for value in alphas)):
        interpolate_model_state(model, base_state, raw_state, alpha=alpha)
        summary = exact_loss_summary(
            label=f"line_alpha_{alpha:g}",
            checkpoint=f"{base_checkpoint}@alpha={alpha:g}",
            model=model,
            preference=preference,
            outcome=outcome,
            old_key=old_key,
            old_key_recovery=old_key_recovery,
            current_family_conflict=current_family_conflict,
            replay_trajectory_anchor=replay_trajectory_anchor,
            active_boundary=active_boundary,
            config=config,
        )
        m297_delta = float(summary["exact_m297_loss"]) - float(base_m297)
        m270_delta = float(summary["exact_m270_loss"]) - float(base_m270)
        old_key_delta = (
            float(summary["old_key_surrogate_loss"]) - float(base_old_key)
            if base_old_key is not None and "old_key_surrogate_loss" in summary
            else 0.0
        )
        passes = (
            m297_delta <= float(config.exact_m297_tolerance)
            and m270_delta <= float(config.exact_m270_tolerance)
            and old_key_delta <= float(config.exact_old_key_tolerance)
        )
        violation = max(0.0, m297_delta - float(config.exact_m297_tolerance)) + max(
            0.0,
            m270_delta - float(config.exact_m270_tolerance),
        ) + max(
            0.0,
            old_key_delta - float(config.exact_old_key_tolerance),
        )
        rows.append(
            {
                **summary,
                "alpha": float(alpha),
                "exact_m297_delta_vs_base": m297_delta,
                "exact_m270_delta_vs_base": m270_delta,
                "old_key_surrogate_delta_vs_base": old_key_delta if base_old_key is not None else None,
                "exact_gates_pass": bool(passes),
                "positive_violation": float(violation),
            }
        )
        if passes:
            best_pass_alpha = float(alpha)
        if best_violation is None or violation < best_violation:
            best_violation = float(violation)
            best_alpha = float(alpha)
    return (best_pass_alpha if best_pass_alpha > 0.0 else best_alpha), rows


def _write_policy_summaries(run_dir: Path, rows: list[dict[str, Any]]) -> None:
    write_csv_rows(run_dir / "candidate_summary.csv", rows)
    write_csv_rows(
        run_dir / "exact_m297_policy_summary.csv",
        [
            {
                "policy": row["policy"],
                "checkpoint": row["checkpoint"],
                "exact_m297_loss": row["exact_m297_loss"],
                "preference_rows": row["preference_rows"],
            }
            for row in rows
        ],
    )
    write_csv_rows(
        run_dir / "exact_m270_policy_summary.csv",
        [
            {
                "policy": row["policy"],
                "checkpoint": row["checkpoint"],
                "exact_m270_loss": row["exact_m270_loss"],
                "outcome_rows": row["outcome_rows"],
            }
            for row in rows
        ],
    )


def optimize_exact_post_ppo_repair(
    *,
    base_checkpoint: Path,
    raw_checkpoint: Path,
    preference_npz: Path,
    outcome_npz: Path,
    old_key_preference_npz: Path | None = None,
    old_key_recovery_npz: Path | None = None,
    current_family_conflict_npz: Path | None = None,
    replay_trajectory_anchor_npz: Path | None = None,
    active_boundary_npz: Path | None = None,
    device: str,
    start_mode: str,
    line_search_alphas: list[float],
    steps: int,
    learning_rate: float,
    seed: int,
    train_scope: str,
    train_log_std: bool,
    config: ExactRepairConfig,
    run_dir: Path,
    log_interval: int = 10,
    selection_policy: str = "best_feasible",
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    if selection_policy not in {"best_feasible", "final"}:
        raise ValueError("selection_policy must be 'best_feasible' or 'final'")
    resolved_device = resolve_device(device)
    torch.manual_seed(int(seed))
    np.random.seed(int(seed))

    base_model, base_source = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    raw_model, raw_source = load_actor_critic_checkpoint(raw_checkpoint, device=str(resolved_device))
    del raw_source
    preference_arrays = np.load(preference_npz)
    obs_dim = int(preference_arrays["observation"].shape[1])
    act_dim = int(preference_arrays["preferred_action"].shape[1])
    hidden_size = int(base_model.actor_mean.in_features)
    preference, outcome = load_repair_corpora(
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        device=next(base_model.parameters()).device,
        obs_dim=obs_dim,
        hidden_size=hidden_size,
        act_dim=act_dim,
    )
    old_key = (
        load_rejected_history_preference_snippets(
            old_key_preference_npz,
            device=next(base_model.parameters()).device,
            obs_dim=obs_dim,
            hidden_size=hidden_size,
            act_dim=act_dim,
        )
        if old_key_preference_npz is not None
        else None
    )
    old_key_recovery = (
        load_old_key_recovery_snippets(
            old_key_recovery_npz,
            device=next(base_model.parameters()).device,
            obs_dim=obs_dim,
            hidden_size=hidden_size,
            act_dim=act_dim,
        )
        if old_key_recovery_npz is not None
        else None
    )
    current_family_conflict = (
        load_current_family_conflict_snippets(
            current_family_conflict_npz,
            device=next(base_model.parameters()).device,
            obs_dim=obs_dim,
            hidden_size=hidden_size,
            act_dim=act_dim,
        )
        if current_family_conflict_npz is not None
        else None
    )
    replay_trajectory_anchor = (
        load_trajectory_action_anchor(
            replay_trajectory_anchor_npz,
            device=next(base_model.parameters()).device,
            obs_dim=obs_dim,
            hidden_size=hidden_size,
            act_dim=act_dim,
        )
        if replay_trajectory_anchor_npz is not None
        else None
    )
    active_boundary = (
        load_active_boundary_snippets(
            active_boundary_npz,
            device=next(base_model.parameters()).device,
            obs_dim=obs_dim,
            hidden_size=hidden_size,
            act_dim=act_dim,
        )
        if active_boundary_npz is not None
        else None
    )
    base_state = _load_state(base_source, next(base_model.parameters()).device)
    raw_state = _load_state({"model_state": raw_model.state_dict()}, next(base_model.parameters()).device)

    base_summary = exact_loss_summary(
        label="base",
        checkpoint=base_checkpoint,
        model=base_model,
        preference=preference,
        outcome=outcome,
        old_key=old_key,
        old_key_recovery=old_key_recovery,
        current_family_conflict=current_family_conflict,
        replay_trajectory_anchor=replay_trajectory_anchor,
        active_boundary=active_boundary,
        config=config,
    )
    raw_summary = exact_loss_summary(
        label="raw",
        checkpoint=raw_checkpoint,
        model=raw_model,
        preference=preference,
        outcome=outcome,
        old_key=old_key,
        old_key_recovery=old_key_recovery,
        current_family_conflict=current_family_conflict,
        replay_trajectory_anchor=replay_trajectory_anchor,
        active_boundary=active_boundary,
        config=config,
    )

    model, source_checkpoint = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device), obs_dim=obs_dim)
    line_search_rows: list[dict[str, Any]] = []
    selected_alpha: float | None = None
    if start_mode == "repair_from_base":
        model.load_state_dict(base_state)
        start_label = "start_base"
    elif start_mode == "repair_from_raw":
        model.load_state_dict(raw_state)
        start_label = "start_raw"
    elif start_mode == "line_search_boundary":
        selected_alpha, line_search_rows = _line_search_rows(
            model=model,
            base_checkpoint=base_checkpoint,
            base_state=base_state,
            raw_state=raw_state,
            preference=preference,
            outcome=outcome,
            old_key=old_key,
            old_key_recovery=old_key_recovery,
            current_family_conflict=current_family_conflict,
            replay_trajectory_anchor=replay_trajectory_anchor,
            active_boundary=active_boundary,
            config=config,
            alphas=line_search_alphas,
            base_m297=float(base_summary["exact_m297_loss"]),
            base_m270=float(base_summary["exact_m270_loss"]),
            base_old_key=(
                float(base_summary["old_key_surrogate_loss"]) if "old_key_surrogate_loss" in base_summary else None
            ),
        )
        interpolate_model_state(model, base_state, raw_state, alpha=selected_alpha)
        start_label = f"start_alpha_{selected_alpha:g}"
    else:
        raise ValueError("start_mode must be repair_from_base repair_from_raw or line_search_boundary")

    trainable = trainable_parameter_items(model, train_scope=train_scope, train_log_std=train_log_std)
    if not trainable.parameters:
        raise RuntimeError("no trainable parameters are available for exact repair")
    base_reference_model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device), obs_dim=obs_dim)
    anchor = build_snippet_action_anchor(
        base_reference_model,
        outcome,
        include_rejected_hidden=True,
    )

    start_summary = exact_loss_summary(
        label=start_label,
        checkpoint=base_checkpoint if start_mode != "repair_from_raw" else raw_checkpoint,
        model=model,
        preference=preference,
        outcome=outcome,
        old_key=old_key,
        old_key_recovery=old_key_recovery,
        current_family_conflict=current_family_conflict,
        replay_trajectory_anchor=replay_trajectory_anchor,
        active_boundary=active_boundary,
        config=config,
    )
    base_m297 = float(base_summary["exact_m297_loss"])
    base_m270 = float(base_summary["exact_m270_loss"])
    base_old_key = float(base_summary["old_key_surrogate_loss"]) if "old_key_surrogate_loss" in base_summary else None
    metrics: list[dict[str, Any]] = []
    selection_trace: list[dict[str, Any]] = []
    best_row: dict[str, Any] | None = None
    best_state = _clone_model_state(model)
    optimizer = torch.optim.Adam(trainable.parameters, lr=float(learning_rate)) if int(steps) > 0 else None
    model.train()
    total_steps = max(0, int(steps))
    interval = max(1, int(log_interval))
    with torch.no_grad():
        start_terms = repair_loss_terms(
            model=model,
            preference=preference,
            outcome=outcome,
            old_key=old_key,
            old_key_recovery=old_key_recovery,
            current_family_conflict=current_family_conflict,
            replay_trajectory_anchor=replay_trajectory_anchor,
            active_boundary=active_boundary,
            anchor=anchor,
            base_m297=base_m297,
            base_m270=base_m270,
            base_old_key=base_old_key,
            base_state=base_state,
            raw_state=raw_state,
            trainable_names=trainable.names,
            config=config,
        )
    start_row = _repair_metrics_row(
        step=0,
        metric_phase="start",
        terms=start_terms,
        grad_norm=0.0,
        learning_rate=float(learning_rate),
        base_m297=base_m297,
        base_m270=base_m270,
        base_old_key=base_old_key,
        config=config,
    )
    selection_trace.append(start_row)
    best_row = start_row
    for step in range(1, total_steps + 1):
        assert optimizer is not None
        optimizer.zero_grad(set_to_none=True)
        terms = repair_loss_terms(
            model=model,
            preference=preference,
            outcome=outcome,
            old_key=old_key,
            old_key_recovery=old_key_recovery,
            current_family_conflict=current_family_conflict,
            replay_trajectory_anchor=replay_trajectory_anchor,
            active_boundary=active_boundary,
            anchor=anchor,
            base_m297=base_m297,
            base_m270=base_m270,
            base_old_key=base_old_key,
            base_state=base_state,
            raw_state=raw_state,
            trainable_names=trainable.names,
            config=config,
        )
        projection_diagnostics = _backward_repair_terms(
            model=model,
            terms=terms,
            trainable_parameters=trainable.parameters,
            config=config,
            replay_trajectory_anchor=replay_trajectory_anchor,
        )
        grad_norm = torch.nn.utils.clip_grad_norm_(trainable.parameters, max_norm=float(config.grad_clip_norm))
        optimizer.step()
        grad_norm_value = float(grad_norm.detach().cpu().item() if isinstance(grad_norm, torch.Tensor) else grad_norm)
        with torch.no_grad():
            post_terms = repair_loss_terms(
                model=model,
                preference=preference,
                outcome=outcome,
                old_key=old_key,
                old_key_recovery=old_key_recovery,
                current_family_conflict=current_family_conflict,
                replay_trajectory_anchor=replay_trajectory_anchor,
                active_boundary=active_boundary,
                anchor=anchor,
                base_m297=base_m297,
                base_m270=base_m270,
                base_old_key=base_old_key,
                base_state=base_state,
                raw_state=raw_state,
                trainable_names=trainable.names,
                config=config,
            )
        post_row = _repair_metrics_row(
            step=step,
            metric_phase="post_update",
            terms=post_terms,
            grad_norm=grad_norm_value,
            learning_rate=float(learning_rate),
            base_m297=base_m297,
            base_m270=base_m270,
            base_old_key=base_old_key,
            config=config,
        )
        post_row.update(projection_diagnostics)
        selection_trace.append(post_row)
        if _repair_selection_key(post_row) < _repair_selection_key(best_row):
            best_row = post_row
            best_state = _clone_model_state(model)
        if step == 1 or step == total_steps or step % interval == 0:
            metrics.append(post_row)
    if total_steps == 0:
        metrics.append(start_row)
    selected_row = selection_trace[-1] if selection_policy == "final" else _select_best_repair_step(selection_trace)
    selected_step = int(selected_row["step"])
    selected_metric_phase = str(selected_row["metric_phase"])

    final_summary = exact_loss_summary(
        label="final_optimizer_state",
        checkpoint=f"{run_dir}/final_optimizer_state",
        model=model,
        preference=preference,
        outcome=outcome,
        old_key=old_key,
        old_key_recovery=old_key_recovery,
        current_family_conflict=current_family_conflict,
        replay_trajectory_anchor=replay_trajectory_anchor,
        active_boundary=active_boundary,
        config=config,
    )
    _add_exact_gate_fields(
        final_summary,
        base_m297=base_m297,
        base_m270=base_m270,
        base_old_key=base_old_key,
        config=config,
    )
    if selection_policy == "best_feasible":
        model.load_state_dict(best_state)

    candidate_path = run_dir / "candidate_checkpoint.pt"
    save_checkpoint_like(
        model=model,
        source_checkpoint=source_checkpoint,
        path=candidate_path,
        metadata={
            "run_type": "exact_post_ppo_repair",
            "base_checkpoint": base_checkpoint,
            "raw_checkpoint": raw_checkpoint,
            "preference_npz": preference_npz,
            "outcome_npz": outcome_npz,
            "old_key_preference_npz": old_key_preference_npz,
            "old_key_recovery_npz": old_key_recovery_npz,
            "current_family_conflict_npz": current_family_conflict_npz,
            "replay_trajectory_anchor_npz": replay_trajectory_anchor_npz,
            "active_boundary_npz": active_boundary_npz,
            "start_mode": start_mode,
            "selected_alpha": selected_alpha,
            "steps": total_steps,
            "learning_rate": float(learning_rate),
            "seed": int(seed),
            "train_scope": train_scope,
            "train_log_std": bool(train_log_std),
            "selection_policy": selection_policy,
            "selected_step": selected_step,
            "selected_metric_phase": selected_metric_phase,
            "config": asdict(config),
        },
    )
    candidate_summary = exact_loss_summary(
        label="candidate",
        checkpoint=candidate_path,
        model=model,
        preference=preference,
        outcome=outcome,
        old_key=old_key,
        old_key_recovery=old_key_recovery,
        current_family_conflict=current_family_conflict,
        replay_trajectory_anchor=replay_trajectory_anchor,
        active_boundary=active_boundary,
        config=config,
    )
    _add_exact_gate_fields(
        candidate_summary,
        base_m297=base_m297,
        base_m270=base_m270,
        base_old_key=base_old_key,
        config=config,
    )
    candidate_summary["selection_policy"] = selection_policy
    candidate_summary["selected_step"] = selected_step
    candidate_summary["selected_metric_phase"] = selected_metric_phase
    candidate_summary["selected_total_loss"] = float(selected_row["total_loss"])

    policy_rows = [base_summary, raw_summary, start_summary, final_summary, candidate_summary]
    _write_policy_summaries(run_dir, policy_rows)
    write_csv_rows(run_dir / "train_metrics.csv", metrics)
    write_csv_rows(run_dir / "selection_trace.csv", selection_trace)
    if line_search_rows:
        write_csv_rows(run_dir / "line_search_summary.csv", line_search_rows)

    summary = {
        "run_type": "exact_post_ppo_repair",
        "base_checkpoint": base_checkpoint,
        "raw_checkpoint": raw_checkpoint,
        "candidate_checkpoint": candidate_path,
        "preference_npz": preference_npz,
        "outcome_npz": outcome_npz,
        "old_key_preference_npz": old_key_preference_npz,
        "old_key_recovery_npz": old_key_recovery_npz,
        "current_family_conflict_npz": current_family_conflict_npz,
        "replay_trajectory_anchor_npz": replay_trajectory_anchor_npz,
        "active_boundary_npz": active_boundary_npz,
        "old_key_rows": int(old_key.size) if old_key is not None else 0,
        "old_key_recovery_rows": int(old_key_recovery.size) if old_key_recovery is not None else 0,
        "current_family_conflict_rows": int(current_family_conflict.size)
        if current_family_conflict is not None
        else 0,
        "replay_trajectory_anchor_rows": int(replay_trajectory_anchor.size)
        if replay_trajectory_anchor is not None
        else 0,
        "active_boundary_rows": int(active_boundary.size) if active_boundary is not None else 0,
        "device": str(resolved_device),
        "start_mode": start_mode,
        "selected_alpha": selected_alpha,
        "line_search_summary_csv": run_dir / "line_search_summary.csv" if line_search_rows else None,
        "steps": total_steps,
        "learning_rate": float(learning_rate),
        "seed": int(seed),
        "train_scope": train_scope,
        "train_log_std": bool(train_log_std),
        "selection_policy": selection_policy,
        "selected_step": selected_step,
        "selected_metric_phase": selected_metric_phase,
        "selected_trace_row": selected_row,
        "config": asdict(config),
        "base": base_summary,
        "raw": raw_summary,
        "start": start_summary,
        "final": final_summary,
        "candidate": candidate_summary,
        "candidate_summary_csv": run_dir / "candidate_summary.csv",
        "exact_m297_policy_summary_csv": run_dir / "exact_m297_policy_summary.csv",
        "exact_m270_policy_summary_csv": run_dir / "exact_m270_policy_summary.csv",
        "train_metrics_csv": run_dir / "train_metrics.csv",
        "selection_trace_csv": run_dir / "selection_trace.csv",
        "ppo_run": False,
        "checkpoint_promoted": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--raw-checkpoint", type=Path, required=True)
    parser.add_argument("--preference-npz", type=Path, required=True)
    parser.add_argument("--outcome-npz", type=Path, required=True)
    parser.add_argument("--old-key-preference-npz", type=Path, default=None)
    parser.add_argument("--old-key-recovery-npz", type=Path, default=None)
    parser.add_argument("--current-family-conflict-npz", type=Path, default=None)
    parser.add_argument("--replay-trajectory-anchor-npz", type=Path, default=None)
    parser.add_argument("--active-boundary-npz", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument(
        "--start-mode",
        choices=["repair_from_base", "repair_from_raw", "line_search_boundary"],
        default="line_search_boundary",
    )
    parser.add_argument("--line-search-alphas", type=parse_alpha_list, default=parse_alpha_list("0,0.001,0.0025,0.005,0.01"))
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=10090)
    parser.add_argument("--train-scope", choices=["all", "actor_coupling"], default="actor_coupling")
    parser.add_argument("--train-log-std", action="store_true")
    parser.add_argument("--preferred-logprob-margin", type=float, default=0.05)
    parser.add_argument("--wrong-logprob-margin", type=float, default=0.05)
    parser.add_argument("--wrong-preference-coef", type=float, default=1.0)
    parser.add_argument("--old-key-preferred-logprob-margin", type=float, default=0.05)
    parser.add_argument("--old-key-wrong-logprob-margin", type=float, default=0.05)
    parser.add_argument("--old-key-wrong-preference-coef", type=float, default=1.0)
    parser.add_argument("--outcome-logprob-margin", type=float, default=0.05)
    parser.add_argument("--exact-m297-tolerance", type=float, default=1e-7)
    parser.add_argument("--exact-m270-tolerance", type=float, default=1e-7)
    parser.add_argument("--exact-old-key-tolerance", type=float, default=1e-7)
    parser.add_argument("--lambda-m297", type=float, default=1_000_000.0)
    parser.add_argument("--lambda-m270", type=float, default=1_000_000.0)
    parser.add_argument("--lambda-old-key", type=float, default=1_000_000.0)
    parser.add_argument("--lambda-old-key-anchor", type=float, default=1.0)
    parser.add_argument("--lambda-old-key-recovery", type=float, default=1.0)
    parser.add_argument("--lambda-old-key-recovery-wrong-anchor", type=float, default=1.0)
    parser.add_argument("--lambda-current-family-conflict", type=float, default=1.0)
    parser.add_argument("--lambda-current-family-conflict-rejected", type=float, default=1.0)
    parser.add_argument("--lambda-replay-trajectory-anchor", type=float, default=0.0)
    parser.add_argument("--lambda-active-boundary", type=float, default=0.0)
    parser.add_argument("--active-boundary-logprob-margin", type=float, default=0.05)
    parser.add_argument("--lambda-action-anchor", type=float, default=100.0)
    parser.add_argument("--lambda-param-base", type=float, default=1.0)
    parser.add_argument("--lambda-param-raw", type=float, default=0.0)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--project-recovery-gradient", action="store_true")
    parser.add_argument("--recovery-projection-epsilon", type=float, default=1e-12)
    parser.add_argument("--log-interval", type=int, default=10)
    parser.add_argument("--selection-policy", choices=["best_feasible", "final"], default="best_feasible")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="exact_post_ppo_repair", seed=args.seed)
    summary = optimize_exact_post_ppo_repair(
        base_checkpoint=args.base_checkpoint,
        raw_checkpoint=args.raw_checkpoint,
        preference_npz=args.preference_npz,
        outcome_npz=args.outcome_npz,
        old_key_preference_npz=args.old_key_preference_npz,
        old_key_recovery_npz=args.old_key_recovery_npz,
        current_family_conflict_npz=args.current_family_conflict_npz,
        replay_trajectory_anchor_npz=args.replay_trajectory_anchor_npz,
        active_boundary_npz=args.active_boundary_npz,
        device=args.device,
        start_mode=args.start_mode,
        line_search_alphas=args.line_search_alphas,
        steps=args.steps,
        learning_rate=args.learning_rate,
        seed=args.seed,
        train_scope=args.train_scope,
        train_log_std=args.train_log_std,
        config=ExactRepairConfig(
            preference=PreferenceLossConfig(
                preferred_logprob_margin=args.preferred_logprob_margin,
                wrong_logprob_margin=args.wrong_logprob_margin,
                wrong_preference_coef=args.wrong_preference_coef,
            ),
            old_key_preference=PreferenceLossConfig(
                preferred_logprob_margin=args.old_key_preferred_logprob_margin,
                wrong_logprob_margin=args.old_key_wrong_logprob_margin,
                wrong_preference_coef=args.old_key_wrong_preference_coef,
            ),
            outcome_logprob_margin=args.outcome_logprob_margin,
            exact_m297_tolerance=args.exact_m297_tolerance,
            exact_m270_tolerance=args.exact_m270_tolerance,
            exact_old_key_tolerance=args.exact_old_key_tolerance,
            lambda_m297=args.lambda_m297,
            lambda_m270=args.lambda_m270,
            lambda_old_key=args.lambda_old_key,
            lambda_old_key_anchor=args.lambda_old_key_anchor,
            lambda_old_key_recovery=args.lambda_old_key_recovery,
            lambda_old_key_recovery_wrong_anchor=args.lambda_old_key_recovery_wrong_anchor,
            lambda_current_family_conflict=args.lambda_current_family_conflict,
            lambda_current_family_conflict_rejected=args.lambda_current_family_conflict_rejected,
            lambda_replay_trajectory_anchor=args.lambda_replay_trajectory_anchor,
            lambda_active_boundary=args.lambda_active_boundary,
            active_boundary_logprob_margin=args.active_boundary_logprob_margin,
            lambda_action_anchor=args.lambda_action_anchor,
            lambda_param_base=args.lambda_param_base,
            lambda_param_raw=args.lambda_param_raw,
            grad_clip_norm=args.grad_clip_norm,
            project_recovery_gradient=args.project_recovery_gradient,
            recovery_projection_epsilon=args.recovery_projection_epsilon,
        ),
        run_dir=run_dir,
        log_interval=args.log_interval,
        selection_policy=args.selection_policy,
    )
    print(to_jsonable(summary["candidate"]))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
