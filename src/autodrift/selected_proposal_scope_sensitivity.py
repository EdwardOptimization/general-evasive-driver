"""No-checkpoint selected-proposal trainable-scope sensitivity probe."""

from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_exact_objective_projection_repair import (
    DEFAULT_BACKTRACKING_FACTORS,
    DEFAULT_INITIAL_STEP_FRACTION,
    MIN_INITIAL_EXACT_RESIDUAL,
    TRUST_REGION_TOLERANCE,
    _device,
    _evaluate_feature_bundle,
    _features_from_arrays,
    _float,
    _load_base_model,
    _loss_from_feature_bundle,
    _named_parameter_snapshots,
    _target_separation_margin,
    _tensor,
)
from autodrift.contour_aware_policy_target_exact_evaluator import (
    DEFAULT_MATERIALIZATION_RUN_DIR,
    _diagnostics_used_as_positive,
    _load_npz,
)
from autodrift.contour_aware_tensor_capture_dry_run import _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT
from autodrift.selected_proposal_repair import DEFAULT_CANDIDATE_SUMMARY, DEFAULT_SELECTED_ALPHAS, _bool, _safe_id, _selected_rows


DEFAULT_RUN_DIR = Path("runs/m1656_selected_proposal_scope_sensitivity")
FEATURE_MODE_FROZEN = "frozen_feature"
FEATURE_MODE_DIFFERENTIABLE = "differentiable_feature"
FEATURE_MODES = (FEATURE_MODE_FROZEN, FEATURE_MODE_DIFFERENTIABLE)
DEFAULT_SCOPES = (
    "actor_mean",
    "fusion_actor",
    "context_fusion_actor",
    "response_fusion_actor",
    "full_policy_actor",
)
SCOPE_ALLOWED_GROUPS = {
    "actor_mean": {"actor_mean"},
    "fusion_actor": {"actor_mean", "response_context_fusion"},
    "context_fusion_actor": {"actor_mean", "context_encoder", "response_context_fusion"},
    "response_fusion_actor": {"actor_mean", "response_encoder", "online_gru_cell", "response_context_fusion"},
    "full_policy_actor": {
        "actor_mean",
        "response_encoder",
        "context_encoder",
        "online_gru_cell",
        "response_context_fusion",
    },
}
EXCLUDED_GROUPS = {"critic", "response_prediction_head", "log_std"}
PRIMARY_ALPHA = 0.2
GRAD_NONZERO_TOLERANCE = 1e-12


CandidateScopeFunction = Callable[..., list[dict[str, Any]]]


def _parameter_group(name: str) -> str:
    if name.startswith("actor_mean."):
        return "actor_mean"
    if name.startswith("response_context_fusion."):
        return "response_context_fusion"
    if name.startswith("context_encoder."):
        return "context_encoder"
    if name.startswith("response_encoder."):
        return "response_encoder"
    if name.startswith("online_gru_cell."):
        return "online_gru_cell"
    if name.startswith("critic."):
        return "critic"
    if name.startswith("response_prediction_head."):
        return "response_prediction_head"
    if name == "log_std":
        return "log_std"
    if name.startswith("privileged_"):
        return "privileged"
    if name.startswith("sequence_tail."):
        return "sequence_tail"
    return "other"


def _scope_names(model: Any, scope: str) -> list[str]:
    if scope not in SCOPE_ALLOWED_GROUPS:
        raise ValueError(f"unknown scope: {scope}")
    allowed = SCOPE_ALLOWED_GROUPS[scope]
    return [name for name, _ in model.named_parameters() if _parameter_group(name) in allowed]


def _set_trainable_scope(model: Any, scope: str) -> list[str]:
    names = set(_scope_names(model, scope))
    if not names:
        raise ValueError(f"scope has no parameters: {scope}")
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(name in names)
    return sorted(names)


def _named_parameters(model: Any, names: Sequence[str]) -> list[tuple[str, torch.nn.Parameter]]:
    wanted = set(names)
    return [(name, parameter) for name, parameter in model.named_parameters() if name in wanted]


def _param_vector(model: Any, names: Sequence[str]) -> torch.Tensor:
    parts = [parameter.detach().reshape(-1) for _, parameter in _named_parameters(model, names)]
    if not parts:
        raise ValueError("scope parameter vector is empty")
    return torch.cat(parts)


def _grad_vector(model: Any, names: Sequence[str]) -> torch.Tensor:
    parts: list[torch.Tensor] = []
    for _, parameter in _named_parameters(model, names):
        if parameter.grad is None:
            parts.append(torch.zeros_like(parameter).reshape(-1))
        else:
            parts.append(parameter.grad.detach().reshape(-1))
    if not parts:
        raise ValueError("scope gradient vector is empty")
    return torch.cat(parts)


def _set_param_vector(model: Any, names: Sequence[str], vector: torch.Tensor) -> None:
    offset = 0
    with torch.no_grad():
        for _, parameter in _named_parameters(model, names):
            count = int(parameter.numel())
            parameter.copy_(vector[offset : offset + count].reshape_as(parameter).to(device=parameter.device, dtype=parameter.dtype))
            offset += count
    if offset != int(vector.numel()):
        raise ValueError("scope vector length mismatch")


def _scope_l2(left: Any, right: Any, names: Sequence[str]) -> float:
    right_params = dict(right.named_parameters())
    values: list[torch.Tensor] = []
    with torch.no_grad():
        for name, parameter in _named_parameters(left, names):
            diff = parameter.detach().float().cpu() - right_params[name].detach().float().cpu()
            values.append(diff.reshape(-1))
    if not values:
        return float("nan")
    return float(torch.linalg.vector_norm(torch.cat(values)).item())


def _max_delta_to_snapshot(model: Any, snapshots: Mapping[str, torch.Tensor]) -> float:
    values: list[float] = []
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            reference = snapshots[name].to(device=parameter.device, dtype=parameter.dtype)
            values.append(float(torch.max(torch.abs(parameter.detach() - reference)).cpu().item()))
    return max(values) if values else 0.0


def _restore_snapshot(model: Any, snapshots: Mapping[str, torch.Tensor]) -> None:
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            parameter.copy_(snapshots[name].to(device=parameter.device, dtype=parameter.dtype))


def _grad_norm(model: Any, names: Sequence[str]) -> float:
    grad = _grad_vector(model, names)
    return float(torch.linalg.vector_norm(grad.float()).detach().cpu().item())


def _group_grad_norm(model: Any, names: Sequence[str], group: str) -> float:
    group_names = [name for name in names if _parameter_group(name) == group]
    if not group_names:
        return 0.0
    return _grad_norm(model, group_names)


def _upstream_grad_norm(model: Any, names: Sequence[str]) -> float:
    upstream_names = [name for name in names if _parameter_group(name) != "actor_mean"]
    if not upstream_names:
        return 0.0
    return _grad_norm(model, upstream_names)


def _feature_tensors(
    model: Any,
    arrays: Mapping[str, Any],
    hidden_key: str,
    *,
    feature_mode: str,
) -> torch.Tensor:
    if feature_mode == FEATURE_MODE_FROZEN:
        return _features_from_arrays(model, arrays, hidden_key)
    if feature_mode != FEATURE_MODE_DIFFERENTIABLE:
        raise ValueError(f"unknown feature mode: {feature_mode}")
    device = _device(model)
    obs = _tensor(arrays["observation"], device=device)
    hidden = _tensor(arrays[hidden_key], device=device)
    features, _ = model.recurrent_features_tensor(obs, hidden)
    return features


def _loss_from_arrays(
    *,
    model: Any,
    arrays: Mapping[str, Any],
    feature_mode: str,
    sep_margin: float,
) -> torch.Tensor:
    correct_features = _feature_tensors(model, arrays, "correct_hidden", feature_mode=feature_mode)
    wrong_features = _feature_tensors(model, arrays, "wrong_hidden", feature_mode=feature_mode)
    preferred = _tensor(arrays["preferred_action"], device=_device(model))
    wrong = _tensor(arrays["wrong_history_action"], device=_device(model))
    return _loss_from_feature_bundle(
        model=model,
        correct_features=correct_features,
        wrong_features=wrong_features,
        preferred_action=preferred,
        wrong_history_action=wrong,
        sep_margin=sep_margin,
    )


def _metrics_from_arrays(
    *,
    model: Any,
    arrays: Mapping[str, Any],
    feature_mode: str,
    sep_margin: float,
) -> dict[str, float]:
    with torch.no_grad():
        correct_features = _feature_tensors(model, arrays, "correct_hidden", feature_mode=feature_mode)
        wrong_features = _feature_tensors(model, arrays, "wrong_hidden", feature_mode=feature_mode)
        preferred = _tensor(arrays["preferred_action"], device=_device(model))
        wrong = _tensor(arrays["wrong_history_action"], device=_device(model))
        return _evaluate_feature_bundle(
            model=model,
            correct_features=correct_features,
            wrong_features=wrong_features,
            preferred_action=preferred,
            wrong_history_action=wrong,
            sep_margin=sep_margin,
        )


def _temporary_one_step(
    *,
    model: Any,
    base_model: Any,
    names: Sequence[str],
    positive_arrays: Mapping[str, Any],
    feature_mode: str,
    sep_margin: float,
    initial_metrics: Mapping[str, float],
    initial_scope_l2_to_base: float,
    initial_step_fraction: float = DEFAULT_INITIAL_STEP_FRACTION,
    backtracking_factors: Sequence[float] = DEFAULT_BACKTRACKING_FACTORS,
) -> dict[str, Any]:
    current_vector = _param_vector(model, names).detach().clone()
    current_l2_to_base = float(initial_scope_l2_to_base)
    grad = _grad_vector(model, names)
    grad_norm_tensor = torch.linalg.vector_norm(grad.float())
    grad_norm = float(grad_norm_tensor.detach().cpu().item())
    if not math.isfinite(grad_norm) or grad_norm <= 0.0:
        return {
            "one_step_reduced": False,
            "one_step_factor": "",
            "one_step_l2": 0.0,
            "one_step_reduction": 0.0,
            "one_step_reduction_ratio": 0.0,
            "one_step_scope_l2_to_base": current_l2_to_base,
            "one_step_stop_reason": "gradient_null_or_nonfinite",
        }
    base_step_l2 = float(initial_step_fraction) * max(current_l2_to_base, 1e-12)
    direction = -grad / torch.clamp(grad_norm_tensor.to(dtype=grad.dtype), min=torch.finfo(grad.dtype).eps)
    accepted: dict[str, Any] | None = None
    for factor in backtracking_factors:
        step_l2 = float(base_step_l2) * float(factor)
        proposal_vector = current_vector + step_l2 * direction
        _set_param_vector(model, names, proposal_vector)
        proposal_metrics = _metrics_from_arrays(
            model=model,
            arrays=positive_arrays,
            feature_mode=feature_mode,
            sep_margin=sep_margin,
        )
        proposal_l2_to_base = _scope_l2(model, base_model, names)
        finite_candidate = math.isfinite(proposal_metrics["exact_residual_mean"])
        improves_exact = proposal_metrics["exact_residual_mean"] < float(initial_metrics["exact_residual_mean"])
        trust_base = proposal_l2_to_base <= current_l2_to_base + TRUST_REGION_TOLERANCE
        if finite_candidate and improves_exact and trust_base:
            reduction = float(initial_metrics["exact_residual_mean"]) - float(proposal_metrics["exact_residual_mean"])
            accepted = {
                "one_step_reduced": True,
                "one_step_factor": float(factor),
                "one_step_l2": step_l2,
                "one_step_reduction": reduction,
                "one_step_reduction_ratio": reduction / float(initial_metrics["exact_residual_mean"])
                if float(initial_metrics["exact_residual_mean"]) > 0.0
                else 0.0,
                "one_step_scope_l2_to_base": proposal_l2_to_base,
                "one_step_stop_reason": "accepted",
            }
            break
    _set_param_vector(model, names, current_vector)
    if accepted is not None:
        return accepted
    return {
        "one_step_reduced": False,
        "one_step_factor": "",
        "one_step_l2": 0.0,
        "one_step_reduction": 0.0,
        "one_step_reduction_ratio": 0.0,
        "one_step_scope_l2_to_base": current_l2_to_base,
        "one_step_stop_reason": "no_backtracking_candidate_accepted",
    }


def _scope_row(
    *,
    candidate_id: str,
    alpha: float,
    proposal_checkpoint: str,
    scope: str,
    feature_mode: str,
    parameter_names: Sequence[str],
    scalar_parameter_count: int,
    initial_metrics: Mapping[str, float],
    grad_norm: float,
    actor_mean_grad_norm: float,
    upstream_grad_norm: float,
    initial_scope_l2_to_base: float,
    one_step: Mapping[str, Any],
    restored: bool,
    max_delta_after_restore: float,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "proposal_source_type": "same_line_interpolation",
        "alpha": float(alpha),
        "proposal_checkpoint": proposal_checkpoint,
        "scope": scope,
        "feature_mode": feature_mode,
        "parameter_count": int(scalar_parameter_count),
        "tensor_parameter_count": int(len(parameter_names)),
        "scalar_parameter_count": int(scalar_parameter_count),
        "parameter_name_count": int(len(parameter_names)),
        "parameter_names": ";".join(parameter_names),
        "initial_positive_exact_residual_mean": initial_metrics["exact_residual_mean"],
        "initial_positive_action_l2_max": initial_metrics["policy_action_residual_l2_max"],
        "scope_grad_norm": grad_norm,
        "actor_mean_grad_norm": actor_mean_grad_norm,
        "upstream_grad_norm": upstream_grad_norm,
        "finite_gradient": math.isfinite(float(grad_norm)),
        "nonzero_gradient": math.isfinite(float(grad_norm)) and float(grad_norm) > GRAD_NONZERO_TOLERANCE,
        "upstream_nonzero_gradient": math.isfinite(float(upstream_grad_norm))
        and float(upstream_grad_norm) > GRAD_NONZERO_TOLERANCE,
        "initial_scope_l2_to_base": initial_scope_l2_to_base,
        "model_restored_after_probe": restored,
        "max_parameter_delta_after_restore": max_delta_after_restore,
        **one_step,
    }


def run_candidate_scope_sensitivity(
    *,
    materialization_run_dir: Path | str,
    base_checkpoint: Path | str,
    proposal_checkpoint: Path | str,
    candidate_id: str,
    alpha: float,
    scopes: Sequence[str] = DEFAULT_SCOPES,
    device: str = "cpu",
) -> list[dict[str, Any]]:
    """Run in-memory scope-sensitivity metrics for one proposal."""

    materialization_dir = Path(materialization_run_dir)
    base_path = Path(base_checkpoint)
    proposal_path = Path(proposal_checkpoint)
    positive_arrays = _load_npz(materialization_dir / "positive_policy_targets.npz")
    sep_margin = _target_separation_margin(positive_arrays["preferred_action"], positive_arrays["wrong_history_action"])
    base_model = _load_base_model(base_path, device)
    proposal_model = _load_base_model(proposal_path, device)
    rows: list[dict[str, Any]] = []
    for scope in scopes:
        for feature_mode in FEATURE_MODES:
            candidate = copy.deepcopy(proposal_model)
            candidate.eval()
            snapshots = _named_parameter_snapshots(candidate)
            names = _set_trainable_scope(candidate, scope)
            candidate.zero_grad(set_to_none=True)
            parameter_map = dict(candidate.named_parameters())
            scalar_parameter_count = sum(int(parameter_map[name].numel()) for name in names)
            initial_metrics = _metrics_from_arrays(
                model=candidate,
                arrays=positive_arrays,
                feature_mode=feature_mode,
                sep_margin=sep_margin,
            )
            loss = _loss_from_arrays(
                model=candidate,
                arrays=positive_arrays,
                feature_mode=feature_mode,
                sep_margin=sep_margin,
            )
            loss.backward()
            grad_norm = _grad_norm(candidate, names)
            actor_mean_grad_norm = _group_grad_norm(candidate, names, "actor_mean")
            upstream_grad_norm = _upstream_grad_norm(candidate, names)
            initial_scope_l2_to_base = _scope_l2(candidate, base_model, names)
            one_step = _temporary_one_step(
                model=candidate,
                base_model=base_model,
                names=names,
                positive_arrays=positive_arrays,
                feature_mode=feature_mode,
                sep_margin=sep_margin,
                initial_metrics=initial_metrics,
                initial_scope_l2_to_base=initial_scope_l2_to_base,
            )
            _restore_snapshot(candidate, snapshots)
            max_delta_after_restore = _max_delta_to_snapshot(candidate, snapshots)
            restored = bool(max_delta_after_restore == 0.0)
            rows.append(
                _scope_row(
                    candidate_id=candidate_id,
                    alpha=alpha,
                    proposal_checkpoint=str(proposal_path),
                    scope=scope,
                    feature_mode=feature_mode,
                    parameter_names=names,
                    scalar_parameter_count=scalar_parameter_count,
                    initial_metrics=initial_metrics,
                    grad_norm=grad_norm,
                    actor_mean_grad_norm=actor_mean_grad_norm,
                    upstream_grad_norm=upstream_grad_norm,
                    initial_scope_l2_to_base=initial_scope_l2_to_base,
                    one_step=one_step,
                    restored=restored,
                    max_delta_after_restore=max_delta_after_restore,
                )
            )
    return rows


def _unique_count(rows: Sequence[Mapping[str, Any]], key: str) -> int:
    return len({str(row.get(key)) for row in rows})


def _truth_count(rows: Sequence[Mapping[str, Any]], key: str) -> int:
    return sum(1 for row in rows if _bool(row.get(key)))


def _aggregate(rows: Sequence[Mapping[str, Any]], *, selected_count: int, scopes: Sequence[str], checkpoint_artifact_count: int) -> dict[str, Any]:
    selected_candidate_count = _unique_count(rows, "candidate_id")
    scope_count = _unique_count(rows, "scope")
    frozen_rows = [row for row in rows if row.get("feature_mode") == FEATURE_MODE_FROZEN]
    differentiable_rows = [row for row in rows if row.get("feature_mode") == FEATURE_MODE_DIFFERENTIABLE]
    wider_primary_rows = [
        row
        for row in differentiable_rows
        if math.isclose(_float(row.get("alpha")), PRIMARY_ALPHA, rel_tol=0.0, abs_tol=1e-12)
        and str(row.get("scope")) != "actor_mean"
    ]
    frozen_feature_upstream_grad_zero = all(_float(row.get("upstream_grad_norm")) <= GRAD_NONZERO_TOLERANCE for row in frozen_rows)
    measurable_scopes = {
        str(row.get("scope"))
        for row in differentiable_rows
        if math.isfinite(_float(row.get("initial_positive_exact_residual_mean"))) and math.isfinite(_float(row.get("scope_grad_norm")))
    }
    primary_nonzero_grad_count = sum(1 for row in wider_primary_rows if _bool(row.get("nonzero_gradient")))
    primary_reduction_count = sum(1 for row in wider_primary_rows if _bool(row.get("one_step_reduced")))
    expected_restore = int(selected_candidate_count) * int(scope_count)
    pair_restore_flags: dict[tuple[str, str], list[bool]] = {}
    for row in rows:
        key = (str(row.get("candidate_id")), str(row.get("scope")))
        pair_restore_flags.setdefault(key, []).append(_bool(row.get("model_restored_after_probe")))
    restored_pair_count = sum(1 for values in pair_restore_flags.values() if values and all(values))
    summary: dict[str, Any] = {
        "selected_candidate_count": int(selected_candidate_count),
        "expected_selected_candidate_count": int(selected_count),
        "scope_count": int(scope_count),
        "expected_scope_count": int(len(tuple(scopes))),
        "feature_mode_count": int(_unique_count(rows, "feature_mode")),
        "scope_row_count": int(len(rows)),
        "frozen_feature_upstream_grad_zero": bool(frozen_feature_upstream_grad_zero),
        "differentiable_feature_scope_measurable_count": int(len(measurable_scopes)),
        "primary_alpha_0_2_wider_scope_nonzero_grad_count": int(primary_nonzero_grad_count),
        "primary_alpha_0_2_wider_scope_reduction_count": int(primary_reduction_count),
        "model_restored_after_probe_count": int(restored_pair_count),
        "expected_model_restored_after_probe_count": int(expected_restore),
        "checkpoint_artifact_count": int(checkpoint_artifact_count),
        "diagnostic_rows_used_as_positive_count": 0,
        "donor_plus_action_used_as_loss_target_count": 0,
        "training_started_count": 0,
        "ppo_used_count": 0,
        "promoted_count": 0,
        "private_holdout_used_count": 0,
        "actor_input_contract_changed_count": 0,
        "level3_self_id_claim_count": 0,
    }
    guardrails_clean = (
        int(summary["checkpoint_artifact_count"]) == 0
        and int(summary["diagnostic_rows_used_as_positive_count"]) == 0
        and int(summary["donor_plus_action_used_as_loss_target_count"]) == 0
        and int(summary["training_started_count"]) == 0
        and int(summary["ppo_used_count"]) == 0
        and int(summary["promoted_count"]) == 0
        and int(summary["private_holdout_used_count"]) == 0
        and int(summary["actor_input_contract_changed_count"]) == 0
        and int(summary["level3_self_id_claim_count"]) == 0
    )
    summary["passes_public_smoke_gates"] = (
        int(summary["selected_candidate_count"]) == int(selected_count)
        and int(summary["scope_count"]) >= 5
        and bool(summary["frozen_feature_upstream_grad_zero"])
        and int(summary["differentiable_feature_scope_measurable_count"]) >= int(scope_count)
        and int(summary["primary_alpha_0_2_wider_scope_nonzero_grad_count"]) >= 1
        and int(summary["primary_alpha_0_2_wider_scope_reduction_count"]) >= 1
        and int(summary["model_restored_after_probe_count"]) == int(summary["expected_model_restored_after_probe_count"])
        and guardrails_clean
    )
    if int(summary["selected_candidate_count"]) != int(selected_count):
        null_class = "selected_candidate_count_mismatch"
    elif int(summary["scope_count"]) < 5:
        null_class = "scope_count_below_threshold"
    elif not bool(summary["frozen_feature_upstream_grad_zero"]):
        null_class = "frozen_feature_upstream_gradient_violation"
    elif int(summary["differentiable_feature_scope_measurable_count"]) < int(scope_count):
        null_class = "differentiable_scope_not_measurable"
    elif int(summary["primary_alpha_0_2_wider_scope_nonzero_grad_count"]) < 1:
        null_class = "primary_wider_scope_gradient_null"
    elif int(summary["primary_alpha_0_2_wider_scope_reduction_count"]) < 1:
        null_class = "primary_wider_scope_no_one_step_reduction"
    elif int(summary["model_restored_after_probe_count"]) != int(summary["expected_model_restored_after_probe_count"]):
        null_class = "model_restore_guardrail_failure"
    elif not guardrails_clean:
        null_class = "guardrail_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "selected_proposal_scope_sensitivity_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class
    return summary


def _aggregate_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{"metric": key, "value": value} for key, value in summary.items()]


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "checkpoint_artifact_count",
        "diagnostic_rows_used_as_positive_count",
        "donor_plus_action_used_as_loss_target_count",
        "training_started_count",
        "ppo_used_count",
        "promoted_count",
        "private_holdout_used_count",
        "actor_input_contract_changed_count",
        "level3_self_id_claim_count",
    ]
    return [{"guardrail": key, "violated": _float(summary.get(key, 0)) != 0.0, "value": summary.get(key)} for key in keys]


def run_selected_proposal_scope_sensitivity(
    *,
    base_checkpoint: Path | str,
    candidate_summary: Path | str,
    materialization_run_dir: Path | str,
    run_dir: Path | str,
    selected_alphas: Sequence[float] = DEFAULT_SELECTED_ALPHAS,
    scopes: Sequence[str] = DEFAULT_SCOPES,
    device: str = "cpu",
    candidate_fn: CandidateScopeFunction = run_candidate_scope_sensitivity,
) -> dict[str, Any]:
    """Run selected-proposal scope-sensitivity metrics and aggregate gates."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows_source = read_csv_rows(candidate_summary)
    selected = _selected_rows(rows_source, selected_alphas)
    materialization_dir = Path(materialization_run_dir)
    diagnostic_rows = read_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv") if materialization_dir.exists() else []
    rows: list[dict[str, Any]] = []
    for row in selected:
        alpha = _float(row.get("alpha"))
        candidate_id = str(row.get("candidate_id", f"alpha_{alpha:g}"))
        candidate_rows = candidate_fn(
            materialization_run_dir=materialization_run_dir,
            base_checkpoint=base_checkpoint,
            proposal_checkpoint=row.get("checkpoint"),
            candidate_id=candidate_id,
            alpha=alpha,
            scopes=scopes,
            device=device,
        )
        for candidate_row in candidate_rows:
            candidate_row["source_candidate_id"] = candidate_id
            candidate_row["candidate_safe_id"] = _safe_id(candidate_id)
            rows.append(candidate_row)
    checkpoint_artifact_count = len(list(output.rglob("*.pt")) + list(output.rglob("*.pth")))
    aggregate = _aggregate(
        rows,
        selected_count=len(tuple(selected_alphas)),
        scopes=scopes,
        checkpoint_artifact_count=checkpoint_artifact_count,
    )
    aggregate["diagnostic_rows_used_as_positive_count"] = 1 if _diagnostics_used_as_positive(diagnostic_rows) else 0
    if int(aggregate["diagnostic_rows_used_as_positive_count"]) != 0:
        aggregate["passes_public_smoke_gates"] = False
        aggregate["null_result_classification"] = "diagnostic_guardrail_violation"
        aggregate["result_class"] = "diagnostic_guardrail_violation"
    summary = {
        "result_class": aggregate["result_class"],
        "base_checkpoint": str(base_checkpoint),
        "candidate_summary": str(candidate_summary),
        "materialization_run_dir": str(materialization_run_dir),
        "selected_alphas": [float(alpha) for alpha in selected_alphas],
        "scopes": list(scopes),
        "feature_modes": list(FEATURE_MODES),
        "proposal_source_type": "same_line_interpolation",
        "checkpoint_artifacts_allowed": False,
        **aggregate,
    }
    write_csv_rows(output / "scope_summary.csv", rows)
    write_csv_rows(output / "aggregate_summary.csv", _aggregate_rows(aggregate))
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _parse_csv_floats(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def _parse_csv_strings(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-checkpoint selected-proposal scope-sensitivity probe.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--selected-alphas", type=_parse_csv_floats, default=DEFAULT_SELECTED_ALPHAS)
    parser.add_argument("--scopes", type=_parse_csv_strings, default=DEFAULT_SCOPES)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_selected_proposal_scope_sensitivity(
        base_checkpoint=args.base_checkpoint,
        candidate_summary=args.candidate_summary,
        materialization_run_dir=args.materialization_run_dir,
        run_dir=args.run_dir,
        selected_alphas=tuple(args.selected_alphas),
        scopes=tuple(args.scopes),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"selected_candidate_count={summary['selected_candidate_count']}")
    print(f"scope_count={summary['scope_count']}")
    print(f"frozen_feature_upstream_grad_zero={summary['frozen_feature_upstream_grad_zero']}")
    print(f"primary_alpha_0_2_wider_scope_nonzero_grad_count={summary['primary_alpha_0_2_wider_scope_nonzero_grad_count']}")
    print(f"primary_alpha_0_2_wider_scope_reduction_count={summary['primary_alpha_0_2_wider_scope_reduction_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
