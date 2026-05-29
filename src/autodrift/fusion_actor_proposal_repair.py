"""No-checkpoint differentiable-feature fusion_actor proposal repair probe."""

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
    DEFAULT_MAX_PROJECTION_STEPS,
    MIN_INITIAL_EXACT_RESIDUAL,
    TRUST_REGION_TOLERANCE,
    _float,
    _load_base_model,
    _named_parameter_snapshots,
    _target_separation_margin,
)
from autodrift.contour_aware_policy_target_exact_evaluator import (
    DEFAULT_MATERIALIZATION_RUN_DIR,
    _diagnostics_used_as_positive,
    _load_npz,
)
from autodrift.contour_aware_tensor_capture_dry_run import _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT
from autodrift.selected_proposal_repair import DEFAULT_CANDIDATE_SUMMARY, DEFAULT_SELECTED_ALPHAS, _bool, _safe_id, _selected_rows
from autodrift.selected_proposal_scope_sensitivity import (
    FEATURE_MODE_DIFFERENTIABLE,
    _grad_vector,
    _loss_from_arrays,
    _max_delta_to_snapshot,
    _metrics_from_arrays,
    _param_vector,
    _parameter_group,
    _restore_snapshot,
    _scope_l2,
    _set_param_vector,
    _set_trainable_scope,
)


DEFAULT_RUN_DIR = Path("runs/m1660_fusion_actor_proposal_repair")
FUSION_ACTOR_SCOPE = "fusion_actor"
PRIMARY_ALPHA = 0.2
MIN_CANDIDATE_REDUCTION_RATIO = 0.25


RepairFunction = Callable[..., dict[str, Any]]


def _excluded_delta_max(model: Any, snapshots: Mapping[str, torch.Tensor], trainable_names: Sequence[str]) -> float:
    allowed = set(trainable_names)
    values: list[float] = []
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            if name in allowed:
                continue
            reference = snapshots[name].to(device=parameter.device, dtype=parameter.dtype)
            values.append(float(torch.max(torch.abs(parameter.detach() - reference)).cpu().item()))
    return max(values) if values else 0.0


def _trainable_group_delta_rows(
    model: Any,
    snapshots: Mapping[str, torch.Tensor],
    *,
    candidate_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            reference = snapshots[name].to(device=parameter.device, dtype=parameter.dtype)
            delta = parameter.detach() - reference
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "parameter": name,
                    "group": _parameter_group(name),
                    "l2_delta": float(torch.linalg.vector_norm(delta.float().reshape(-1)).cpu().item()),
                    "max_abs_delta": float(torch.max(torch.abs(delta)).cpu().item()) if delta.numel() else 0.0,
                    "allowed_group": _parameter_group(name) in {"actor_mean", "response_context_fusion"},
                }
            )
    return rows


def _trace_row(
    *,
    step: int,
    metrics: Mapping[str, float],
    fusion_actor_l2_to_base: float,
    grad_norm: float,
    accepted_factor: float | None,
    accepted_step_l2: float | None,
    stop_reason: str,
) -> dict[str, Any]:
    return {
        "step": step,
        "positive_exact_residual_mean": metrics["exact_residual_mean"],
        "positive_policy_action_residual_l2_max": metrics["policy_action_residual_l2_max"],
        "fusion_actor_l2_to_base": fusion_actor_l2_to_base,
        "grad_norm": grad_norm,
        "accepted_factor": "" if accepted_factor is None else accepted_factor,
        "accepted_step_l2": "" if accepted_step_l2 is None else accepted_step_l2,
        "stop_reason": stop_reason,
    }


def _backtracking_row(
    *,
    step: int,
    factor: float,
    step_l2: float,
    metrics: Mapping[str, float],
    fusion_actor_l2_to_base: float,
    accepted: bool,
    rejection_reason: str,
) -> dict[str, Any]:
    return {
        "step": step,
        "factor": factor,
        "step_l2": step_l2,
        "positive_exact_residual_mean": metrics["exact_residual_mean"],
        "positive_policy_action_residual_l2_max": metrics["policy_action_residual_l2_max"],
        "fusion_actor_l2_to_base": fusion_actor_l2_to_base,
        "accepted": accepted,
        "rejection_reason": rejection_reason,
    }


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "checkpoint_artifact_written",
        "base_interpolation_used_for_repair",
        "used_frozen_features_for_repair",
        "widened_beyond_fusion_actor",
        "excluded_parameter_delta_violation",
        "model_restored_after_probe",
        "diagnostic_rows_used_as_positive",
        "donor_plus_action_used_as_loss_target",
        "training_started",
        "ppo_used",
        "promoted",
        "private_holdout_used",
        "actor_input_contract_changed",
        "level3_self_id_claim_made",
    ]
    rows: list[dict[str, Any]] = []
    for key in keys:
        value = summary.get(key, False)
        if key == "model_restored_after_probe":
            violated = not _bool(value)
        else:
            violated = bool(value)
        rows.append({"guardrail": key, "violated": violated, "value": value})
    return rows


def run_fusion_actor_candidate_repair(
    *,
    materialization_run_dir: Path | str,
    base_checkpoint: Path | str,
    proposal_checkpoint: Path | str,
    candidate_id: str,
    alpha: float,
    run_dir: Path | str,
    device: str = "cpu",
    max_projection_steps: int = DEFAULT_MAX_PROJECTION_STEPS,
    initial_step_fraction: float = DEFAULT_INITIAL_STEP_FRACTION,
    backtracking_factors: Sequence[float] = DEFAULT_BACKTRACKING_FACTORS,
) -> dict[str, Any]:
    """Run no-checkpoint in-memory fusion_actor repair for one proposal."""

    materialization_dir = Path(materialization_run_dir)
    base_path = Path(base_checkpoint)
    proposal_path = Path(proposal_checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    base_checksum_before = _sha256(base_path)
    proposal_checksum_before = _sha256(proposal_path)
    positive_arrays = _load_npz(materialization_dir / "positive_policy_targets.npz")
    diagnostic_rows = read_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv")
    positive_rows = read_csv_rows(materialization_dir / "positive_policy_target_rows.csv")
    sep_margin = _target_separation_margin(positive_arrays["preferred_action"], positive_arrays["wrong_history_action"])
    base_model = _load_base_model(base_path, device)
    proposal_model = _load_base_model(proposal_path, device)
    candidate = copy.deepcopy(proposal_model)
    candidate.eval()
    initial_snapshots = _named_parameter_snapshots(candidate)
    trainable_names = _set_trainable_scope(candidate, FUSION_ACTOR_SCOPE)
    initial_metrics = _metrics_from_arrays(
        model=candidate,
        arrays=positive_arrays,
        feature_mode=FEATURE_MODE_DIFFERENTIABLE,
        sep_margin=sep_margin,
    )
    current_metrics = dict(initial_metrics)
    initial_l2_to_base = _scope_l2(candidate, base_model, trainable_names)
    current_l2_to_base = float(initial_l2_to_base)
    base_step_l2 = float(initial_step_fraction) * max(current_l2_to_base, 1e-12)
    accepted_step_count = 0
    grad_norm_max = 0.0
    stop_reason = "max_projection_steps_reached"
    trace_rows: list[dict[str, Any]] = [
        _trace_row(
            step=0,
            metrics=initial_metrics,
            fusion_actor_l2_to_base=initial_l2_to_base,
            grad_norm=0.0,
            accepted_factor=None,
            accepted_step_l2=None,
            stop_reason="initial",
        )
    ]
    backtracking_rows: list[dict[str, Any]] = []
    for step in range(1, int(max_projection_steps) + 1):
        candidate.zero_grad(set_to_none=True)
        loss = _loss_from_arrays(
            model=candidate,
            arrays=positive_arrays,
            feature_mode=FEATURE_MODE_DIFFERENTIABLE,
            sep_margin=sep_margin,
        )
        loss.backward()
        grad = _grad_vector(candidate, trainable_names)
        grad_norm_tensor = torch.linalg.vector_norm(grad.float())
        grad_norm = float(grad_norm_tensor.detach().cpu().item())
        grad_norm_max = max(grad_norm_max, grad_norm)
        if not math.isfinite(grad_norm) or grad_norm <= 0.0:
            stop_reason = "gradient_null_or_nonfinite"
            trace_rows.append(
                _trace_row(
                    step=step,
                    metrics=current_metrics,
                    fusion_actor_l2_to_base=current_l2_to_base,
                    grad_norm=grad_norm,
                    accepted_factor=None,
                    accepted_step_l2=None,
                    stop_reason=stop_reason,
                )
            )
            break
        current_vector = _param_vector(candidate, trainable_names).detach().clone()
        direction = -grad / torch.clamp(grad_norm_tensor.to(dtype=grad.dtype), min=torch.finfo(grad.dtype).eps)
        accepted_vector: torch.Tensor | None = None
        accepted_metrics: dict[str, float] | None = None
        accepted_l2_to_base: float | None = None
        accepted_factor: float | None = None
        accepted_step_l2: float | None = None
        for factor in backtracking_factors:
            step_l2 = base_step_l2 * float(factor)
            proposal_vector = current_vector + step_l2 * direction
            _set_param_vector(candidate, trainable_names, proposal_vector)
            proposal_metrics = _metrics_from_arrays(
                model=candidate,
                arrays=positive_arrays,
                feature_mode=FEATURE_MODE_DIFFERENTIABLE,
                sep_margin=sep_margin,
            )
            proposal_l2_to_base = _scope_l2(candidate, base_model, trainable_names)
            finite_candidate = math.isfinite(proposal_metrics["exact_residual_mean"])
            improves_exact = proposal_metrics["exact_residual_mean"] < current_metrics["exact_residual_mean"]
            trust_base = proposal_l2_to_base <= current_l2_to_base + TRUST_REGION_TOLERANCE
            accepted = bool(finite_candidate and improves_exact and trust_base)
            if not finite_candidate:
                rejection_reason = "nonfinite_candidate"
            elif not improves_exact:
                rejection_reason = "residual_not_reduced"
            elif not trust_base:
                rejection_reason = "base_trust_region_expansion"
            else:
                rejection_reason = ""
            backtracking_rows.append(
                _backtracking_row(
                    step=step,
                    factor=float(factor),
                    step_l2=step_l2,
                    metrics=proposal_metrics,
                    fusion_actor_l2_to_base=proposal_l2_to_base,
                    accepted=accepted,
                    rejection_reason=rejection_reason,
                )
            )
            if accepted:
                accepted_vector = proposal_vector.detach().clone()
                accepted_metrics = dict(proposal_metrics)
                accepted_l2_to_base = proposal_l2_to_base
                accepted_factor = float(factor)
                accepted_step_l2 = step_l2
                break
        if accepted_vector is None or accepted_metrics is None or accepted_l2_to_base is None:
            _set_param_vector(candidate, trainable_names, current_vector)
            stop_reason = "no_backtracking_candidate_accepted"
            trace_rows.append(
                _trace_row(
                    step=step,
                    metrics=current_metrics,
                    fusion_actor_l2_to_base=current_l2_to_base,
                    grad_norm=grad_norm,
                    accepted_factor=None,
                    accepted_step_l2=None,
                    stop_reason=stop_reason,
                )
            )
            break
        _set_param_vector(candidate, trainable_names, accepted_vector)
        accepted_step_count += 1
        current_metrics = dict(accepted_metrics)
        current_l2_to_base = float(accepted_l2_to_base)
        trace_rows.append(
            _trace_row(
                step=step,
                metrics=current_metrics,
                fusion_actor_l2_to_base=current_l2_to_base,
                grad_norm=grad_norm,
                accepted_factor=accepted_factor,
                accepted_step_l2=accepted_step_l2,
                stop_reason="accepted",
            )
        )
        reduction = initial_metrics["exact_residual_mean"] - current_metrics["exact_residual_mean"]
        reduction_ratio = reduction / initial_metrics["exact_residual_mean"] if initial_metrics["exact_residual_mean"] > 0.0 else 0.0
        if reduction_ratio >= MIN_CANDIDATE_REDUCTION_RATIO:
            stop_reason = "target_reduction_reached"
            break
    excluded_delta_max = _excluded_delta_max(candidate, initial_snapshots, trainable_names)
    parameter_delta_rows = _trainable_group_delta_rows(candidate, initial_snapshots, candidate_id=candidate_id)
    repaired_metrics = dict(current_metrics)
    repaired_l2_to_base = float(current_l2_to_base)
    reduction = initial_metrics["exact_residual_mean"] - repaired_metrics["exact_residual_mean"]
    reduction_ratio = reduction / initial_metrics["exact_residual_mean"] if initial_metrics["exact_residual_mean"] > 0.0 else 0.0
    _restore_snapshot(candidate, initial_snapshots)
    max_delta_after_restore = _max_delta_to_snapshot(candidate, initial_snapshots)
    model_restored_after_probe = bool(max_delta_after_restore == 0.0)
    checkpoint_artifact_written = bool(list(output.rglob("*.pt")) or list(output.rglob("*.pth")))
    base_checksum_after = _sha256(base_path)
    proposal_checksum_after = _sha256(proposal_path)
    diagnostic_rows_used_as_positive = _diagnostics_used_as_positive(diagnostic_rows)
    widened_beyond_fusion_actor = any(_parameter_group(name) not in {"actor_mean", "response_context_fusion"} for name in trainable_names)
    guardrail_values = {
        "checkpoint_artifact_written": checkpoint_artifact_written,
        "base_interpolation_used_for_repair": False,
        "used_frozen_features_for_repair": False,
        "widened_beyond_fusion_actor": bool(widened_beyond_fusion_actor),
        "excluded_parameter_delta_violation": bool(excluded_delta_max != 0.0),
        "model_restored_after_probe": model_restored_after_probe,
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "donor_plus_action_used_as_loss_target": False,
        "checkpoint_weights_mutated": bool(base_checksum_before != base_checksum_after or proposal_checksum_before != proposal_checksum_after),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(
        1
        for key, value in guardrail_values.items()
        if (key == "model_restored_after_probe" and not _bool(value)) or (key != "model_restored_after_probe" and bool(value))
    )
    candidate_pass = (
        len(positive_rows) > 0
        and initial_metrics["exact_residual_mean"] > MIN_INITIAL_EXACT_RESIDUAL
        and repaired_metrics["exact_residual_mean"] < initial_metrics["exact_residual_mean"]
        and reduction_ratio >= MIN_CANDIDATE_REDUCTION_RATIO
        and accepted_step_count >= 1
        and repaired_l2_to_base <= initial_l2_to_base + TRUST_REGION_TOLERANCE
        and excluded_delta_max == 0.0
        and model_restored_after_probe
        and guardrail_violation_count == 0
    )
    if len(positive_rows) == 0:
        null_class = "positive_target_count_zero"
    elif initial_metrics["exact_residual_mean"] <= MIN_INITIAL_EXACT_RESIDUAL:
        null_class = "nonmeasurable_initial_residual"
    elif repaired_metrics["exact_residual_mean"] >= initial_metrics["exact_residual_mean"]:
        null_class = "residual_not_reduced"
    elif reduction_ratio < MIN_CANDIDATE_REDUCTION_RATIO:
        null_class = "reduction_ratio_below_threshold"
    elif accepted_step_count < 1:
        null_class = "no_backtracking_candidate_accepted"
    elif excluded_delta_max != 0.0:
        null_class = "excluded_parameter_delta_violation"
    elif not model_restored_after_probe:
        null_class = "model_restore_guardrail_failure"
    elif guardrail_violation_count != 0:
        null_class = "guardrail_violation"
    elif candidate_pass:
        null_class = "fusion_actor_candidate_repair_public_pass"
    else:
        null_class = "public_gate_failure"
    summary: dict[str, Any] = {
        "result_class": null_class,
        "candidate_id": candidate_id,
        "proposal_source_type": "same_line_interpolation",
        "alpha": float(alpha),
        "materialization_run_dir": str(materialization_dir),
        "base_checkpoint": str(base_path),
        "proposal_checkpoint": str(proposal_path),
        "feature_mode": FEATURE_MODE_DIFFERENTIABLE,
        "trainable_scope": FUSION_ACTOR_SCOPE,
        "trainable_parameter_names": ";".join(trainable_names),
        "initial_positive_exact_residual_mean": initial_metrics["exact_residual_mean"],
        "repaired_positive_exact_residual_mean": repaired_metrics["exact_residual_mean"],
        "positive_exact_residual_reduction": reduction,
        "positive_exact_residual_reduction_ratio": reduction_ratio,
        "initial_positive_action_l2_max": initial_metrics["policy_action_residual_l2_max"],
        "repaired_positive_action_l2_max": repaired_metrics["policy_action_residual_l2_max"],
        "initial_fusion_actor_l2_to_base": initial_l2_to_base,
        "repaired_fusion_actor_l2_to_base": repaired_l2_to_base,
        "excluded_parameter_delta_max": excluded_delta_max,
        "max_parameter_delta_after_restore": max_delta_after_restore,
        "accepted_backtracking_step_count": int(accepted_step_count),
        "backtracking_candidate_count": len(backtracking_rows),
        "projection_stop_reason": stop_reason,
        "grad_norm_max": grad_norm_max,
        "guardrail_violation_count": int(guardrail_violation_count),
        "passes_candidate_gate": bool(candidate_pass),
        "null_result_classification": null_class,
        **guardrail_values,
    }
    write_csv_rows(output / "repair_trace.csv", trace_rows)
    write_csv_rows(output / "backtracking_candidates.csv", backtracking_rows)
    write_csv_rows(output / "parameter_delta_summary.csv", parameter_delta_rows)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _candidate_row(candidate_summary: Mapping[str, Any], run_dir: Path, summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": summary.get("candidate_id"),
        "proposal_source_type": summary.get("proposal_source_type"),
        "alpha": summary.get("alpha"),
        "proposal_checkpoint": summary.get("proposal_checkpoint"),
        "candidate_run_dir": str(run_dir),
        "feature_mode": summary.get("feature_mode"),
        "trainable_scope": summary.get("trainable_scope"),
        "initial_positive_exact_residual_mean": summary.get("initial_positive_exact_residual_mean"),
        "repaired_positive_exact_residual_mean": summary.get("repaired_positive_exact_residual_mean"),
        "positive_exact_residual_reduction": summary.get("positive_exact_residual_reduction"),
        "positive_exact_residual_reduction_ratio": summary.get("positive_exact_residual_reduction_ratio"),
        "initial_positive_action_l2_max": summary.get("initial_positive_action_l2_max"),
        "repaired_positive_action_l2_max": summary.get("repaired_positive_action_l2_max"),
        "initial_fusion_actor_l2_to_base": summary.get("initial_fusion_actor_l2_to_base"),
        "repaired_fusion_actor_l2_to_base": summary.get("repaired_fusion_actor_l2_to_base"),
        "excluded_parameter_delta_max": summary.get("excluded_parameter_delta_max"),
        "model_restored_after_probe": summary.get("model_restored_after_probe"),
        "accepted_backtracking_step_count": summary.get("accepted_backtracking_step_count"),
        "projection_stop_reason": summary.get("projection_stop_reason"),
        "passes_candidate_gate": summary.get("passes_candidate_gate"),
        "null_result_classification": summary.get("null_result_classification"),
        "guardrail_violation_count": summary.get("guardrail_violation_count"),
        "source_candidate_id": candidate_summary.get("candidate_id"),
    }


def _count(rows: Sequence[Mapping[str, Any]], key: str, predicate: Callable[[Any], bool]) -> int:
    return sum(1 for row in rows if predicate(row.get(key)))


def _aggregate(rows: Sequence[Mapping[str, Any]], *, selected_count: int, checkpoint_artifact_count: int) -> dict[str, Any]:
    measurable = _count(rows, "initial_positive_exact_residual_mean", lambda value: _float(value) > MIN_INITIAL_EXACT_RESIDUAL)
    primary_rows = [row for row in rows if math.isclose(_float(row.get("alpha")), PRIMARY_ALPHA, rel_tol=0.0, abs_tol=1e-12)]
    primary_pass = bool(primary_rows and _bool(primary_rows[0].get("passes_candidate_gate")))
    candidate_public_pass_count = _count(rows, "passes_candidate_gate", _bool)
    summary: dict[str, Any] = {
        "selected_candidate_count": len(rows),
        "expected_selected_candidate_count": int(selected_count),
        "measurable_initial_residual_count": int(measurable),
        "candidate_public_pass_count": int(candidate_public_pass_count),
        "primary_alpha_0_2_pass": bool(primary_pass),
        "checkpoint_artifact_count": int(checkpoint_artifact_count),
        "excluded_parameter_delta_violation_count": _count(rows, "excluded_parameter_delta_max", lambda value: _float(value) != 0.0),
        "model_restored_after_probe_count": _count(rows, "model_restored_after_probe", _bool),
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
        and int(summary["excluded_parameter_delta_violation_count"]) == 0
        and int(summary["model_restored_after_probe_count"]) == int(summary["selected_candidate_count"])
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
        and int(summary["measurable_initial_residual_count"]) == int(selected_count)
        and int(summary["candidate_public_pass_count"]) >= 1
        and bool(summary["primary_alpha_0_2_pass"])
        and guardrails_clean
    )
    if int(summary["selected_candidate_count"]) != int(selected_count):
        null_class = "selected_candidate_count_mismatch"
    elif int(summary["measurable_initial_residual_count"]) != int(selected_count):
        null_class = "nonmeasurable_initial_residual"
    elif int(summary["model_restored_after_probe_count"]) != int(summary["selected_candidate_count"]):
        null_class = "model_restore_guardrail_failure"
    elif not bool(summary["primary_alpha_0_2_pass"]):
        null_class = "primary_alpha_0_2_not_repaired"
    elif int(summary["checkpoint_artifact_count"]) != 0:
        null_class = "checkpoint_artifact_written"
    elif int(summary["excluded_parameter_delta_violation_count"]) != 0:
        null_class = "excluded_parameter_delta_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "fusion_actor_proposal_repair_public_pass"
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
        "excluded_parameter_delta_violation_count",
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


def run_fusion_actor_proposal_repair(
    *,
    base_checkpoint: Path | str,
    candidate_summary: Path | str,
    materialization_run_dir: Path | str,
    run_dir: Path | str,
    selected_alphas: Sequence[float] = DEFAULT_SELECTED_ALPHAS,
    device: str = "cpu",
    repair_fn: RepairFunction = run_fusion_actor_candidate_repair,
) -> dict[str, Any]:
    """Run fusion_actor repair over selected proposals and aggregate metrics."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate_root = output / "candidates"
    candidate_root.mkdir(parents=True, exist_ok=True)
    source_rows = read_csv_rows(candidate_summary)
    selected = _selected_rows(source_rows, selected_alphas)
    rows: list[dict[str, Any]] = []
    for row in selected:
        alpha = _float(row.get("alpha"))
        candidate_id = str(row.get("candidate_id", f"alpha_{alpha:g}"))
        candidate_run_dir = candidate_root / _safe_id(candidate_id)
        summary = repair_fn(
            materialization_run_dir=materialization_run_dir,
            base_checkpoint=base_checkpoint,
            proposal_checkpoint=row.get("checkpoint"),
            candidate_id=candidate_id,
            alpha=alpha,
            run_dir=candidate_run_dir,
            device=device,
        )
        rows.append(_candidate_row(row, candidate_run_dir, summary))
    checkpoint_artifact_count = len(list(output.rglob("*.pt")) + list(output.rglob("*.pth")))
    aggregate = _aggregate(rows, selected_count=len(tuple(selected_alphas)), checkpoint_artifact_count=checkpoint_artifact_count)
    materialization_dir = Path(materialization_run_dir)
    diagnostic_rows = read_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv")
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
        "proposal_source_type": "same_line_interpolation",
        "feature_mode": FEATURE_MODE_DIFFERENTIABLE,
        "trainable_scope": FUSION_ACTOR_SCOPE,
        "checkpoint_artifacts_allowed": False,
        **aggregate,
    }
    write_csv_rows(output / "candidate_summary.csv", rows)
    write_csv_rows(output / "aggregate_summary.csv", _aggregate_rows(aggregate))
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _parse_alphas(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-checkpoint fusion_actor proposal repair probe.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--selected-alphas", type=_parse_alphas, default=DEFAULT_SELECTED_ALPHAS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_fusion_actor_proposal_repair(
        base_checkpoint=args.base_checkpoint,
        candidate_summary=args.candidate_summary,
        materialization_run_dir=args.materialization_run_dir,
        run_dir=args.run_dir,
        selected_alphas=tuple(args.selected_alphas),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"selected_candidate_count={summary['selected_candidate_count']}")
    print(f"candidate_public_pass_count={summary['candidate_public_pass_count']}")
    print(f"primary_alpha_0_2_pass={summary['primary_alpha_0_2_pass']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
