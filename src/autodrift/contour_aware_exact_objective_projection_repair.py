"""No-checkpoint projection repair for contour-aware exact objective drift."""

from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_exact_objective_sensitivity_probe import _perturb_actor_mean
from autodrift.contour_aware_policy_target_exact_evaluator import (
    DEFAULT_MATERIALIZATION_RUN_DIR,
    EXPECTED_DIAGNOSTIC_COUNT,
    EXPECTED_POSITIVE_COUNT,
    LAMBDA_SEP,
    MAX_SEP_MARGIN,
    SEP_QUANTILE,
    _diagnostic_weight_sum,
    _diagnostics_used_as_positive,
    _load_npz,
)
from autodrift.contour_aware_tensor_capture_dry_run import _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract


DEFAULT_RUN_DIR = Path("runs/m1640_contour_aware_exact_objective_projection_repair")
DEFAULT_PERTURB_SCALE = 1e-3
DEFAULT_PERTURB_SEED = 1639
DEFAULT_REPAIR_STEPS = 25
DEFAULT_LEARNING_RATE = 1e-3
PROJECTION_MODE_ADAM = "adam"
PROJECTION_MODE_DAMPED_BACKTRACKING = "damped_backtracking"
DEFAULT_PROJECTION_MODE = PROJECTION_MODE_ADAM
DEFAULT_MAX_PROJECTION_STEPS = 10
DEFAULT_INITIAL_STEP_FRACTION = 0.25
DEFAULT_BACKTRACKING_FACTORS = (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625)
MIN_INITIAL_EXACT_RESIDUAL = 1e-8
MIN_REDUCTION_RATIO = 0.50
TRUST_REGION_TOLERANCE = 1e-12
FORBIDDEN_GUARDRAILS = {
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


LoadModelFunction = Callable[[Path, str], Any]


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


def _load_base_model(checkpoint: Path, device: str) -> Any:
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    model.eval()
    return model


def _device(model: Any) -> torch.device:
    return next(model.parameters()).device


def _tensor(value: np.ndarray, *, device: torch.device) -> torch.Tensor:
    return torch.as_tensor(np.asarray(value, dtype=np.float32), dtype=torch.float32, device=device)


def _target_separation_margin(actions_left: np.ndarray, actions_right: np.ndarray) -> float:
    target_sep = np.linalg.norm(
        np.asarray(actions_left, dtype=np.float64) - np.asarray(actions_right, dtype=np.float64),
        axis=1,
    )
    return float(min(MAX_SEP_MARGIN, np.quantile(target_sep, SEP_QUANTILE))) if target_sep.size else 0.0


def _features_from_arrays(model: Any, arrays: Mapping[str, np.ndarray], hidden_key: str) -> torch.Tensor:
    device = _device(model)
    obs = _tensor(arrays["observation"], device=device)
    hidden = _tensor(arrays[hidden_key], device=device)
    with torch.no_grad():
        features, _ = model.recurrent_features_tensor(obs, hidden)
    return features.detach()


def _actions_from_features(model: Any, features: torch.Tensor) -> torch.Tensor:
    return torch.tanh(model.actor_mean(features))


def _exact_metrics_from_actions(
    *,
    correct_action: torch.Tensor,
    wrong_action: torch.Tensor,
    preferred_action: torch.Tensor,
    wrong_history_action: torch.Tensor,
    sep_margin: float,
) -> dict[str, float]:
    correct_l2 = torch.linalg.vector_norm(correct_action - preferred_action, dim=1)
    wrong_l2 = torch.linalg.vector_norm(wrong_action - wrong_history_action, dim=1)
    policy_sep = torch.linalg.vector_norm(correct_action - wrong_action, dim=1)
    sep_residual = torch.clamp(float(sep_margin) - policy_sep, min=0.0)
    correct_mse_mean = torch.mean(correct_l2.square())
    wrong_mse_mean = torch.mean(wrong_l2.square())
    sep_residual_mse_mean = torch.mean(sep_residual.square())
    exact = correct_mse_mean + wrong_mse_mean + float(LAMBDA_SEP) * sep_residual_mse_mean
    action_l2_max = torch.maximum(torch.max(correct_l2), torch.max(wrong_l2))
    return {
        "correct_l2_max": float(torch.max(correct_l2).detach().cpu().item()),
        "wrong_l2_max": float(torch.max(wrong_l2).detach().cpu().item()),
        "policy_correct_wrong_action_l2_min": float(torch.min(policy_sep).detach().cpu().item()),
        "policy_correct_wrong_action_l2_mean": float(torch.mean(policy_sep).detach().cpu().item()),
        "sep_residual_max": float(torch.max(sep_residual).detach().cpu().item()),
        "sep_residual_mse_mean": float(sep_residual_mse_mean.detach().cpu().item()),
        "exact_residual_mean": float(exact.detach().cpu().item()),
        "policy_action_residual_l2_max": float(action_l2_max.detach().cpu().item()),
    }


def _evaluate_feature_bundle(
    *,
    model: Any,
    correct_features: torch.Tensor,
    wrong_features: torch.Tensor,
    preferred_action: torch.Tensor,
    wrong_history_action: torch.Tensor,
    sep_margin: float,
) -> dict[str, float]:
    with torch.no_grad():
        correct_action = _actions_from_features(model, correct_features)
        wrong_action = _actions_from_features(model, wrong_features)
        return _exact_metrics_from_actions(
            correct_action=correct_action,
            wrong_action=wrong_action,
            preferred_action=preferred_action,
            wrong_history_action=wrong_history_action,
            sep_margin=sep_margin,
        )


def _loss_from_feature_bundle(
    *,
    model: Any,
    correct_features: torch.Tensor,
    wrong_features: torch.Tensor,
    preferred_action: torch.Tensor,
    wrong_history_action: torch.Tensor,
    sep_margin: float,
) -> torch.Tensor:
    correct_action = _actions_from_features(model, correct_features)
    wrong_action = _actions_from_features(model, wrong_features)
    correct_mse = torch.mean(torch.sum((correct_action - preferred_action) ** 2, dim=1))
    wrong_mse = torch.mean(torch.sum((wrong_action - wrong_history_action) ** 2, dim=1))
    policy_sep = torch.linalg.vector_norm(correct_action - wrong_action, dim=1)
    sep_residual = torch.clamp(float(sep_margin) - policy_sep, min=0.0)
    return correct_mse + wrong_mse + float(LAMBDA_SEP) * torch.mean(sep_residual.square())


def _named_parameter_snapshots(model: Any) -> dict[str, torch.Tensor]:
    return {name: parameter.detach().clone() for name, parameter in model.named_parameters()}


def _load_named_parameter_snapshots(model: Any, snapshots: Mapping[str, torch.Tensor]) -> None:
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            parameter.copy_(snapshots[name].to(device=parameter.device, dtype=parameter.dtype))


def _actor_mean_l2(left: Any, right: Any) -> float:
    values: list[torch.Tensor] = []
    right_params = dict(right.named_parameters())
    with torch.no_grad():
        for name, parameter in left.named_parameters():
            if name not in {"actor_mean.weight", "actor_mean.bias"}:
                continue
            diff = parameter.detach().float().cpu() - right_params[name].detach().float().cpu()
            values.append(diff.reshape(-1))
    if not values:
        return float("nan")
    return float(torch.linalg.vector_norm(torch.cat(values)).item())


def _actor_mean_named_parameters(model: Any) -> list[tuple[str, torch.nn.Parameter]]:
    return [(name, parameter) for name, parameter in model.named_parameters() if name in {"actor_mean.weight", "actor_mean.bias"}]


def _actor_mean_vector(model: Any) -> torch.Tensor:
    parts = [parameter.detach().reshape(-1) for _, parameter in _actor_mean_named_parameters(model)]
    if not parts:
        raise ValueError("model has no actor_mean parameters")
    return torch.cat(parts)


def _actor_mean_grad_vector(model: Any) -> torch.Tensor:
    parts: list[torch.Tensor] = []
    for _, parameter in _actor_mean_named_parameters(model):
        if parameter.grad is None:
            parts.append(torch.zeros_like(parameter).reshape(-1))
        else:
            parts.append(parameter.grad.detach().reshape(-1))
    if not parts:
        raise ValueError("model has no actor_mean parameters")
    return torch.cat(parts)


def _set_actor_mean_vector(model: Any, vector: torch.Tensor) -> None:
    offset = 0
    with torch.no_grad():
        for _, parameter in _actor_mean_named_parameters(model):
            count = parameter.numel()
            parameter.copy_(vector[offset : offset + count].reshape_as(parameter).to(device=parameter.device, dtype=parameter.dtype))
            offset += count
    if offset != int(vector.numel()):
        raise ValueError("actor_mean vector length mismatch")


def _non_actor_mean_delta_max(
    left: Any,
    snapshots: Mapping[str, torch.Tensor],
) -> float:
    values: list[float] = []
    with torch.no_grad():
        for name, parameter in left.named_parameters():
            if name in {"actor_mean.weight", "actor_mean.bias"}:
                continue
            reference = snapshots[name].to(device=parameter.device, dtype=parameter.dtype)
            values.append(float(torch.max(torch.abs(parameter.detach() - reference)).cpu().item()))
    return max(values) if values else 0.0


def _set_trainable_scope(model: Any) -> None:
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(name in {"actor_mean.weight", "actor_mean.bias"})


def _grad_norm(model: Any) -> float:
    values: list[torch.Tensor] = []
    for name, parameter in model.named_parameters():
        if name not in {"actor_mean.weight", "actor_mean.bias"} or parameter.grad is None:
            continue
        values.append(parameter.grad.detach().float().reshape(-1).cpu())
    if not values:
        return 0.0
    return float(torch.linalg.vector_norm(torch.cat(values)).item())


def _repair_trace_row(
    *,
    step: int,
    loss: float,
    grad_norm: float,
    positive_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
) -> dict[str, Any]:
    return {
        "step": step,
        "loss": loss,
        "grad_norm": grad_norm,
        "positive_exact_residual_mean": positive_metrics["exact_residual_mean"],
        "positive_policy_action_residual_l2_max": positive_metrics["policy_action_residual_l2_max"],
        "actor_mean_l2_to_base": actor_mean_l2_to_base,
    }


def _damped_step_trace_row(
    *,
    step: int,
    positive_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
    grad_norm: float,
    accepted_factor: float | None,
    accepted_step_l2: float | None,
    stop_reason: str,
) -> dict[str, Any]:
    return {
        "step": step,
        "positive_exact_residual_mean": positive_metrics["exact_residual_mean"],
        "positive_policy_action_residual_l2_max": positive_metrics["policy_action_residual_l2_max"],
        "actor_mean_l2_to_base": actor_mean_l2_to_base,
        "grad_norm": grad_norm,
        "accepted_factor": "" if accepted_factor is None else accepted_factor,
        "accepted_step_l2": "" if accepted_step_l2 is None else accepted_step_l2,
        "stop_reason": stop_reason,
    }


def _backtracking_candidate_row(
    *,
    step: int,
    factor: float,
    step_l2: float,
    positive_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
    accepted: bool,
    rejection_reason: str,
) -> dict[str, Any]:
    return {
        "step": step,
        "factor": factor,
        "step_l2": step_l2,
        "positive_exact_residual_mean": positive_metrics["exact_residual_mean"],
        "positive_policy_action_residual_l2_max": positive_metrics["policy_action_residual_l2_max"],
        "actor_mean_l2_to_base": actor_mean_l2_to_base,
        "accepted": accepted,
        "rejection_reason": rejection_reason,
    }


def _phase_row(
    *,
    phase: str,
    positive_metrics: Mapping[str, float],
    diagnostic_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
) -> dict[str, Any]:
    return {
        "phase": phase,
        "positive_exact_residual_mean": positive_metrics["exact_residual_mean"],
        "positive_policy_action_residual_l2_max": positive_metrics["policy_action_residual_l2_max"],
        "positive_correct_l2_max": positive_metrics["correct_l2_max"],
        "positive_wrong_l2_max": positive_metrics["wrong_l2_max"],
        "diagnostic_exact_residual_mean": diagnostic_metrics["exact_residual_mean"],
        "diagnostic_policy_action_residual_l2_max": diagnostic_metrics["policy_action_residual_l2_max"],
        "diagnostic_correct_l2_max": diagnostic_metrics["correct_l2_max"],
        "diagnostic_wrong_l2_max": diagnostic_metrics["wrong_l2_max"],
        "actor_mean_l2_to_base": actor_mean_l2_to_base,
    }


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "repaired_checkpoint_written",
        "diagnostic_rows_used_as_positive",
        "donor_plus_action_used_as_loss_target",
        "checkpoint_weights_mutated",
        "non_actor_mean_parameter_changed",
        "base_interpolation_used_for_repair",
        *FORBIDDEN_GUARDRAILS.keys(),
    ]
    return [{"guardrail": key, "violated": bool(summary.get(key, False)), "value": summary.get(key, False)} for key in keys]


def run_contour_aware_exact_objective_projection_repair(
    *,
    materialization_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
    device: str = "cpu",
    expected_positive_count: int = EXPECTED_POSITIVE_COUNT,
    expected_diagnostic_count: int = EXPECTED_DIAGNOSTIC_COUNT,
    perturb_scale: float = DEFAULT_PERTURB_SCALE,
    perturb_seed: int = DEFAULT_PERTURB_SEED,
    repair_steps: int = DEFAULT_REPAIR_STEPS,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    projection_mode: str = DEFAULT_PROJECTION_MODE,
    max_projection_steps: int = DEFAULT_MAX_PROJECTION_STEPS,
    initial_step_fraction: float = DEFAULT_INITIAL_STEP_FRACTION,
    backtracking_factors: Sequence[float] = DEFAULT_BACKTRACKING_FACTORS,
    load_model_fn: LoadModelFunction | None = None,
) -> dict[str, Any]:
    """Run the M1640 actor_mean-only projection probe without writing a checkpoint."""

    materialization_dir = Path(materialization_run_dir)
    checkpoint_path = Path(checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checksum_before = _sha256(checkpoint_path)

    positive_arrays = _load_npz(materialization_dir / "positive_policy_targets.npz")
    diagnostic_arrays = _load_npz(materialization_dir / "diagnostic_policy_guardrails.npz")
    positive_rows = read_csv_rows(materialization_dir / "positive_policy_target_rows.csv")
    diagnostic_rows = read_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv")

    loader = load_model_fn or _load_base_model
    base_model = loader(checkpoint_path, device)
    if hasattr(base_model, "eval"):
        base_model.eval()
    candidate = copy.deepcopy(base_model)
    if hasattr(candidate, "eval"):
        candidate.eval()
    perturb_stats = _perturb_actor_mean(candidate, scale=float(perturb_scale), seed=int(perturb_seed))
    initial_candidate_snapshots = _named_parameter_snapshots(candidate)
    _set_trainable_scope(candidate)

    sep_margin = _target_separation_margin(
        positive_arrays["preferred_action"],
        positive_arrays["wrong_history_action"],
    )
    dev = _device(candidate)
    positive_correct_features = _features_from_arrays(candidate, positive_arrays, "correct_hidden")
    positive_wrong_features = _features_from_arrays(candidate, positive_arrays, "wrong_hidden")
    diagnostic_correct_features = _features_from_arrays(candidate, diagnostic_arrays, "correct_hidden")
    diagnostic_wrong_features = _features_from_arrays(candidate, diagnostic_arrays, "wrong_hidden")
    positive_preferred = _tensor(positive_arrays["preferred_action"], device=dev)
    positive_wrong = _tensor(positive_arrays["wrong_history_action"], device=dev)
    diagnostic_preferred = _tensor(diagnostic_arrays["preferred_action"], device=dev)
    diagnostic_wrong = _tensor(diagnostic_arrays["wrong_history_action"], device=dev)

    initial_positive_metrics = _evaluate_feature_bundle(
        model=candidate,
        correct_features=positive_correct_features,
        wrong_features=positive_wrong_features,
        preferred_action=positive_preferred,
        wrong_history_action=positive_wrong,
        sep_margin=sep_margin,
    )
    initial_diagnostic_metrics = _evaluate_feature_bundle(
        model=candidate,
        correct_features=diagnostic_correct_features,
        wrong_features=diagnostic_wrong_features,
        preferred_action=diagnostic_preferred,
        wrong_history_action=diagnostic_wrong,
        sep_margin=sep_margin,
    )
    initial_actor_mean_l2_to_base = _actor_mean_l2(candidate, base_model)

    best_snapshots = _named_parameter_snapshots(candidate)
    best_positive_metrics = dict(initial_positive_metrics)
    best_actor_mean_l2_to_base = initial_actor_mean_l2_to_base
    trace_rows: list[dict[str, Any]] = [
        _repair_trace_row(
            step=0,
            loss=initial_positive_metrics["exact_residual_mean"],
            grad_norm=0.0,
            positive_metrics=initial_positive_metrics,
            actor_mean_l2_to_base=initial_actor_mean_l2_to_base,
        )
    ]
    projection_step_rows: list[dict[str, Any]] = [
        _damped_step_trace_row(
            step=0,
            positive_metrics=initial_positive_metrics,
            actor_mean_l2_to_base=initial_actor_mean_l2_to_base,
            grad_norm=0.0,
            accepted_factor=None,
            accepted_step_l2=None,
            stop_reason="initial",
        )
    ]
    backtracking_candidate_rows: list[dict[str, Any]] = []
    grad_norm_max = 0.0
    accepted_backtracking_step_count = 0
    base_interpolation_used_for_repair = False
    base_interpolation_diagnostic_used_for_repair = False
    projection_stop_reason = "not_started"

    if projection_mode == PROJECTION_MODE_ADAM:
        optimizer = torch.optim.Adam(
            [parameter for parameter in candidate.parameters() if parameter.requires_grad],
            lr=float(learning_rate),
        )
        projection_stop_reason = "adam_completed"
        for step in range(1, int(repair_steps) + 1):
            optimizer.zero_grad(set_to_none=True)
            loss = _loss_from_feature_bundle(
                model=candidate,
                correct_features=positive_correct_features,
                wrong_features=positive_wrong_features,
                preferred_action=positive_preferred,
                wrong_history_action=positive_wrong,
                sep_margin=sep_margin,
            )
            loss.backward()
            current_grad_norm = _grad_norm(candidate)
            grad_norm_max = max(grad_norm_max, current_grad_norm)
            optimizer.step()
            positive_metrics = _evaluate_feature_bundle(
                model=candidate,
                correct_features=positive_correct_features,
                wrong_features=positive_wrong_features,
                preferred_action=positive_preferred,
                wrong_history_action=positive_wrong,
                sep_margin=sep_margin,
            )
            actor_mean_l2_to_base = _actor_mean_l2(candidate, base_model)
            trace_rows.append(
                _repair_trace_row(
                    step=step,
                    loss=float(loss.detach().cpu().item()),
                    grad_norm=current_grad_norm,
                    positive_metrics=positive_metrics,
                    actor_mean_l2_to_base=actor_mean_l2_to_base,
                )
            )
            improves_exact = positive_metrics["exact_residual_mean"] < best_positive_metrics["exact_residual_mean"]
            ties_exact = math.isclose(
                positive_metrics["exact_residual_mean"],
                best_positive_metrics["exact_residual_mean"],
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            improves_trust = actor_mean_l2_to_base < best_actor_mean_l2_to_base
            if actor_mean_l2_to_base <= initial_actor_mean_l2_to_base + TRUST_REGION_TOLERANCE and (
                improves_exact or (ties_exact and improves_trust)
            ):
                best_snapshots = _named_parameter_snapshots(candidate)
                best_positive_metrics = dict(positive_metrics)
                best_actor_mean_l2_to_base = actor_mean_l2_to_base
    elif projection_mode == PROJECTION_MODE_DAMPED_BACKTRACKING:
        current_positive_metrics = dict(initial_positive_metrics)
        current_actor_mean_l2_to_base = initial_actor_mean_l2_to_base
        base_step_l2 = float(initial_step_fraction) * float(initial_actor_mean_l2_to_base)
        projection_stop_reason = "max_projection_steps_reached"
        for step in range(1, int(max_projection_steps) + 1):
            candidate.zero_grad(set_to_none=True)
            loss = _loss_from_feature_bundle(
                model=candidate,
                correct_features=positive_correct_features,
                wrong_features=positive_wrong_features,
                preferred_action=positive_preferred,
                wrong_history_action=positive_wrong,
                sep_margin=sep_margin,
            )
            loss.backward()
            grad_vector = _actor_mean_grad_vector(candidate)
            grad_norm_tensor = torch.linalg.vector_norm(grad_vector.float())
            current_grad_norm = float(grad_norm_tensor.detach().cpu().item())
            grad_norm_max = max(grad_norm_max, current_grad_norm)
            if not math.isfinite(current_grad_norm) or current_grad_norm <= 0.0:
                projection_stop_reason = "gradient_null_or_nonfinite"
                projection_step_rows.append(
                    _damped_step_trace_row(
                        step=step,
                        positive_metrics=current_positive_metrics,
                        actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                        grad_norm=current_grad_norm,
                        accepted_factor=None,
                        accepted_step_l2=None,
                        stop_reason=projection_stop_reason,
                    )
                )
                break
            current_vector = _actor_mean_vector(candidate).detach().clone()
            direction = -grad_vector / torch.clamp(grad_norm_tensor.to(dtype=grad_vector.dtype), min=torch.finfo(grad_vector.dtype).eps)
            accepted_vector: torch.Tensor | None = None
            accepted_metrics: dict[str, float] | None = None
            accepted_l2: float | None = None
            accepted_factor: float | None = None
            accepted_step_l2: float | None = None
            for factor in backtracking_factors:
                step_l2 = float(base_step_l2) * float(factor)
                proposal_vector = current_vector + step_l2 * direction
                _set_actor_mean_vector(candidate, proposal_vector)
                proposal_metrics = _evaluate_feature_bundle(
                    model=candidate,
                    correct_features=positive_correct_features,
                    wrong_features=positive_wrong_features,
                    preferred_action=positive_preferred,
                    wrong_history_action=positive_wrong,
                    sep_margin=sep_margin,
                )
                proposal_l2 = _actor_mean_l2(candidate, base_model)
                finite_candidate = math.isfinite(proposal_metrics["exact_residual_mean"]) and math.isfinite(
                    proposal_metrics["policy_action_residual_l2_max"]
                )
                improves_exact = proposal_metrics["exact_residual_mean"] < current_positive_metrics["exact_residual_mean"]
                trust_current = proposal_l2 <= current_actor_mean_l2_to_base + TRUST_REGION_TOLERANCE
                trust_initial = proposal_l2 <= initial_actor_mean_l2_to_base + TRUST_REGION_TOLERANCE
                accepted = bool(finite_candidate and improves_exact and trust_current and trust_initial)
                if not finite_candidate:
                    rejection_reason = "nonfinite_candidate"
                elif not improves_exact:
                    rejection_reason = "residual_not_reduced"
                elif not trust_current:
                    rejection_reason = "current_trust_region_expansion"
                elif not trust_initial:
                    rejection_reason = "initial_trust_region_expansion"
                else:
                    rejection_reason = ""
                backtracking_candidate_rows.append(
                    _backtracking_candidate_row(
                        step=step,
                        factor=float(factor),
                        step_l2=step_l2,
                        positive_metrics=proposal_metrics,
                        actor_mean_l2_to_base=proposal_l2,
                        accepted=accepted,
                        rejection_reason=rejection_reason,
                    )
                )
                if accepted:
                    accepted_vector = proposal_vector.detach().clone()
                    accepted_metrics = dict(proposal_metrics)
                    accepted_l2 = proposal_l2
                    accepted_factor = float(factor)
                    accepted_step_l2 = step_l2
                    break
            if accepted_vector is None or accepted_metrics is None or accepted_l2 is None:
                _set_actor_mean_vector(candidate, current_vector)
                projection_stop_reason = "no_backtracking_candidate_accepted"
                projection_step_rows.append(
                    _damped_step_trace_row(
                        step=step,
                        positive_metrics=current_positive_metrics,
                        actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                        grad_norm=current_grad_norm,
                        accepted_factor=None,
                        accepted_step_l2=None,
                        stop_reason=projection_stop_reason,
                    )
                )
                break
            _set_actor_mean_vector(candidate, accepted_vector)
            accepted_backtracking_step_count += 1
            current_positive_metrics = dict(accepted_metrics)
            current_actor_mean_l2_to_base = float(accepted_l2)
            best_snapshots = _named_parameter_snapshots(candidate)
            best_positive_metrics = dict(current_positive_metrics)
            best_actor_mean_l2_to_base = current_actor_mean_l2_to_base
            projection_step_rows.append(
                _damped_step_trace_row(
                    step=step,
                    positive_metrics=current_positive_metrics,
                    actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                    grad_norm=current_grad_norm,
                    accepted_factor=accepted_factor,
                    accepted_step_l2=accepted_step_l2,
                    stop_reason="accepted",
                )
            )
            trace_rows.append(
                _repair_trace_row(
                    step=step,
                    loss=float(loss.detach().cpu().item()),
                    grad_norm=current_grad_norm,
                    positive_metrics=current_positive_metrics,
                    actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                )
            )
            reduction = initial_positive_metrics["exact_residual_mean"] - current_positive_metrics["exact_residual_mean"]
            reduction_ratio = (
                reduction / initial_positive_metrics["exact_residual_mean"]
                if initial_positive_metrics["exact_residual_mean"] > 0.0
                else 0.0
            )
            if reduction_ratio >= MIN_REDUCTION_RATIO:
                projection_stop_reason = "target_reduction_reached"
                break
    else:
        raise ValueError(f"unknown projection_mode: {projection_mode}")

    _load_named_parameter_snapshots(candidate, best_snapshots)
    repaired_positive_metrics = _evaluate_feature_bundle(
        model=candidate,
        correct_features=positive_correct_features,
        wrong_features=positive_wrong_features,
        preferred_action=positive_preferred,
        wrong_history_action=positive_wrong,
        sep_margin=sep_margin,
    )
    repaired_diagnostic_metrics = _evaluate_feature_bundle(
        model=candidate,
        correct_features=diagnostic_correct_features,
        wrong_features=diagnostic_wrong_features,
        preferred_action=diagnostic_preferred,
        wrong_history_action=diagnostic_wrong,
        sep_margin=sep_margin,
    )
    repaired_actor_mean_l2_to_base = _actor_mean_l2(candidate, base_model)
    non_actor_mean_parameter_delta_max = _non_actor_mean_delta_max(candidate, initial_candidate_snapshots)
    non_actor_mean_parameter_changed = bool(non_actor_mean_parameter_delta_max != 0.0)
    checksum_after = _sha256(checkpoint_path)
    repaired_checkpoint_written = bool(list(output.rglob("*.pt")))
    diagnostic_rows_used_as_positive = _diagnostics_used_as_positive(diagnostic_rows)
    diagnostic_positive_weight_sum = _diagnostic_weight_sum(diagnostic_rows)
    donor_plus_action_used_as_loss_target = False

    positive_exact_residual_reduction = (
        initial_positive_metrics["exact_residual_mean"] - repaired_positive_metrics["exact_residual_mean"]
    )
    positive_exact_residual_reduction_ratio = (
        positive_exact_residual_reduction / initial_positive_metrics["exact_residual_mean"]
        if initial_positive_metrics["exact_residual_mean"] > 0.0
        else 0.0
    )
    guardrail_values = {
        **FORBIDDEN_GUARDRAILS,
        "repaired_checkpoint_written": repaired_checkpoint_written,
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "donor_plus_action_used_as_loss_target": donor_plus_action_used_as_loss_target,
        "checkpoint_weights_mutated": bool(checksum_before != checksum_after),
        "non_actor_mean_parameter_changed": non_actor_mean_parameter_changed,
        "base_interpolation_used_for_repair": bool(base_interpolation_used_for_repair),
    }
    guardrail_violation_count = sum(1 for value in guardrail_values.values() if bool(value))

    summary: dict[str, Any] = {
        "result_class": "contour_aware_exact_objective_projection_repair",
        "materialization_run_dir": str(materialization_dir),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "perturb_scale": float(perturb_scale),
        "perturb_seed": int(perturb_seed),
        "repair_steps": int(repair_steps),
        "learning_rate": float(learning_rate),
        "projection_mode": projection_mode,
        "max_projection_steps": int(max_projection_steps),
        "initial_step_fraction": float(initial_step_fraction),
        "backtracking_factor_count": len(tuple(backtracking_factors)),
        "accepted_backtracking_step_count": int(accepted_backtracking_step_count),
        "backtracking_candidate_count": len(backtracking_candidate_rows),
        "projection_stop_reason": projection_stop_reason,
        "base_interpolation_used_for_repair": bool(base_interpolation_used_for_repair),
        "base_interpolation_diagnostic_used_for_repair": bool(base_interpolation_diagnostic_used_for_repair),
        "positive_policy_target_count": len(positive_rows),
        "diagnostic_policy_guardrail_count": len(diagnostic_rows),
        "positive_observation_shape": list(positive_arrays["observation"].shape),
        "diagnostic_observation_shape": list(diagnostic_arrays["observation"].shape),
        "separation_margin": sep_margin,
        "initial_positive_exact_residual_mean": initial_positive_metrics["exact_residual_mean"],
        "repaired_positive_exact_residual_mean": repaired_positive_metrics["exact_residual_mean"],
        "positive_exact_residual_reduction": positive_exact_residual_reduction,
        "positive_exact_residual_reduction_ratio": positive_exact_residual_reduction_ratio,
        "initial_positive_action_l2_max": initial_positive_metrics["policy_action_residual_l2_max"],
        "repaired_positive_action_l2_max": repaired_positive_metrics["policy_action_residual_l2_max"],
        "initial_diagnostic_exact_residual_mean": initial_diagnostic_metrics["exact_residual_mean"],
        "repaired_diagnostic_exact_residual_mean": repaired_diagnostic_metrics["exact_residual_mean"],
        "initial_diagnostic_action_l2_max": initial_diagnostic_metrics["policy_action_residual_l2_max"],
        "repaired_diagnostic_action_l2_max": repaired_diagnostic_metrics["policy_action_residual_l2_max"],
        "initial_actor_mean_l2_to_base": initial_actor_mean_l2_to_base,
        "repaired_actor_mean_l2_to_base": repaired_actor_mean_l2_to_base,
        "actor_mean_l2_reduction": initial_actor_mean_l2_to_base - repaired_actor_mean_l2_to_base,
        "non_actor_mean_parameter_delta_max": non_actor_mean_parameter_delta_max,
        "grad_norm_max": grad_norm_max,
        "diagnostic_positive_weight_sum": diagnostic_positive_weight_sum,
        "guardrail_violation_count": int(guardrail_violation_count),
        "actor_update_is_projection_probe_only": True,
        **guardrail_values,
        **perturb_stats,
    }
    summary["passes_public_smoke_gates"] = (
        len(positive_rows) == int(expected_positive_count)
        and len(diagnostic_rows) == int(expected_diagnostic_count)
        and _float(summary["initial_positive_exact_residual_mean"]) > MIN_INITIAL_EXACT_RESIDUAL
        and _float(summary["repaired_positive_exact_residual_mean"]) < _float(summary["initial_positive_exact_residual_mean"])
        and _float(summary["positive_exact_residual_reduction_ratio"]) >= MIN_REDUCTION_RATIO
        and _float(summary["repaired_actor_mean_l2_to_base"]) <= _float(summary["initial_actor_mean_l2_to_base"]) + TRUST_REGION_TOLERANCE
        and (
            projection_mode != PROJECTION_MODE_DAMPED_BACKTRACKING
            or int(summary["accepted_backtracking_step_count"]) >= 1
        )
        and not bool(summary["base_interpolation_used_for_repair"])
        and _float(summary["non_actor_mean_parameter_delta_max"]) == 0.0
        and not bool(summary["repaired_checkpoint_written"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and float(summary["diagnostic_positive_weight_sum"]) == 0.0
        and not bool(summary["donor_plus_action_used_as_loss_target"])
        and not bool(summary["checkpoint_weights_mutated"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    if len(positive_rows) != int(expected_positive_count):
        null_class = "positive_target_count_mismatch"
    elif len(diagnostic_rows) != int(expected_diagnostic_count):
        null_class = "diagnostic_guardrail_count_mismatch"
    elif bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif bool(summary["donor_plus_action_used_as_loss_target"]):
        null_class = "donor_plus_action_loss_target_violation"
    elif bool(summary["repaired_checkpoint_written"]):
        null_class = "checkpoint_artifact_written"
    elif bool(summary["checkpoint_weights_mutated"]):
        null_class = "checkpoint_mutation_violation"
    elif bool(summary["non_actor_mean_parameter_changed"]):
        null_class = "non_actor_mean_parameter_delta"
    elif bool(summary["base_interpolation_used_for_repair"]):
        null_class = "base_interpolation_repair_violation"
    elif _float(summary["initial_positive_exact_residual_mean"]) <= MIN_INITIAL_EXACT_RESIDUAL:
        null_class = "initial_perturbation_residual_not_measurable"
    elif projection_mode == PROJECTION_MODE_DAMPED_BACKTRACKING and int(summary["accepted_backtracking_step_count"]) == 0:
        null_class = str(summary["projection_stop_reason"])
    elif _float(summary["repaired_positive_exact_residual_mean"]) >= _float(summary["initial_positive_exact_residual_mean"]):
        null_class = "projection_residual_not_reduced"
    elif _float(summary["positive_exact_residual_reduction_ratio"]) < MIN_REDUCTION_RATIO:
        null_class = "projection_partial_reduction"
    elif _float(summary["repaired_actor_mean_l2_to_base"]) > _float(summary["initial_actor_mean_l2_to_base"]) + TRUST_REGION_TOLERANCE:
        null_class = "trust_region_expansion"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_exact_objective_projection_repair_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class

    write_csv_rows(
        output / "repair_summary.csv",
        [
            _phase_row(
                phase="initial",
                positive_metrics=initial_positive_metrics,
                diagnostic_metrics=initial_diagnostic_metrics,
                actor_mean_l2_to_base=initial_actor_mean_l2_to_base,
            ),
            _phase_row(
                phase="repaired",
                positive_metrics=repaired_positive_metrics,
                diagnostic_metrics=repaired_diagnostic_metrics,
                actor_mean_l2_to_base=repaired_actor_mean_l2_to_base,
            ),
        ],
    )
    write_csv_rows(output / "optimization_trace.csv", trace_rows)
    write_csv_rows(output / "projection_step_trace.csv", projection_step_rows)
    write_csv_rows(output / "backtracking_candidate_trace.csv", backtracking_candidate_rows)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _parse_backtracking_factors(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contour-aware exact-objective projection repair.")
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--perturb-scale", type=float, default=DEFAULT_PERTURB_SCALE)
    parser.add_argument("--perturb-seed", type=int, default=DEFAULT_PERTURB_SEED)
    parser.add_argument("--repair-steps", type=int, default=DEFAULT_REPAIR_STEPS)
    parser.add_argument("--learning-rate", type=float, default=DEFAULT_LEARNING_RATE)
    parser.add_argument("--projection-mode", choices=[PROJECTION_MODE_ADAM, PROJECTION_MODE_DAMPED_BACKTRACKING], default=DEFAULT_PROJECTION_MODE)
    parser.add_argument("--max-projection-steps", type=int, default=DEFAULT_MAX_PROJECTION_STEPS)
    parser.add_argument("--initial-step-fraction", type=float, default=DEFAULT_INITIAL_STEP_FRACTION)
    parser.add_argument("--backtracking-factors", type=_parse_backtracking_factors, default=DEFAULT_BACKTRACKING_FACTORS)
    args = parser.parse_args()
    summary = run_contour_aware_exact_objective_projection_repair(
        materialization_run_dir=args.materialization_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
        device=args.device,
        perturb_scale=float(args.perturb_scale),
        perturb_seed=int(args.perturb_seed),
        repair_steps=int(args.repair_steps),
        learning_rate=float(args.learning_rate),
        projection_mode=str(args.projection_mode),
        max_projection_steps=int(args.max_projection_steps),
        initial_step_fraction=float(args.initial_step_fraction),
        backtracking_factors=tuple(args.backtracking_factors),
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"projection_mode={summary['projection_mode']}")
    print(f"initial_positive_exact_residual_mean={summary['initial_positive_exact_residual_mean']}")
    print(f"repaired_positive_exact_residual_mean={summary['repaired_positive_exact_residual_mean']}")
    print(f"positive_exact_residual_reduction_ratio={summary['positive_exact_residual_reduction_ratio']}")
    print(f"initial_actor_mean_l2_to_base={summary['initial_actor_mean_l2_to_base']}")
    print(f"repaired_actor_mean_l2_to_base={summary['repaired_actor_mean_l2_to_base']}")
    print(f"accepted_backtracking_step_count={summary['accepted_backtracking_step_count']}")
    print(f"projection_stop_reason={summary['projection_stop_reason']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
