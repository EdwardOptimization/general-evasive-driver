"""No-checkpoint selected-proposal repair probe."""

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
    _actor_mean_grad_vector,
    _actor_mean_l2,
    _actor_mean_vector,
    _device,
    _evaluate_feature_bundle,
    _features_from_arrays,
    _float,
    _load_base_model,
    _loss_from_feature_bundle,
    _named_parameter_snapshots,
    _non_actor_mean_delta_max,
    _set_actor_mean_vector,
    _set_trainable_scope,
    _target_separation_margin,
    _tensor,
)
from autodrift.contour_aware_policy_target_exact_evaluator import (
    DEFAULT_MATERIALIZATION_RUN_DIR,
    EXPECTED_DIAGNOSTIC_COUNT,
    EXPECTED_POSITIVE_COUNT,
    _diagnostic_weight_sum,
    _diagnostics_used_as_positive,
    _load_npz,
)
from autodrift.contour_aware_tensor_capture_dry_run import _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT


DEFAULT_CANDIDATE_SUMMARY = Path("runs/m1650_proposal_source_preflight/candidate_summary.csv")
DEFAULT_RUN_DIR = Path("runs/m1653_selected_proposal_repair")
DEFAULT_SELECTED_ALPHAS = (0.2, 0.4, 1.0)
PRIMARY_ALPHA = 0.2
MIN_CANDIDATE_REDUCTION_RATIO = 0.25
FORBIDDEN_GUARDRAILS = {
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


RepairFunction = Callable[..., dict[str, Any]]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _safe_id(value: str) -> str:
    return (
        value.strip()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(".", "_")
        .replace("-", "m")
        .replace("+", "")
    )


def _selected_rows(rows: Sequence[Mapping[str, Any]], selected_alphas: Sequence[float]) -> list[Mapping[str, Any]]:
    wanted = {float(alpha) for alpha in selected_alphas}
    output: list[Mapping[str, Any]] = []
    for row in rows:
        alpha = _float(row.get("alpha"))
        if alpha in wanted and _bool(row.get("selected_repair_candidate")):
            output.append(row)
    return sorted(output, key=lambda item: _float(item.get("alpha")))


def _candidate_phase_row(
    *,
    phase: str,
    positive_metrics: Mapping[str, float],
    diagnostic_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
    actor_mean_l2_to_proposal: float,
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
        "actor_mean_l2_to_proposal": actor_mean_l2_to_proposal,
    }


def _step_row(
    *,
    step: int,
    positive_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
    actor_mean_l2_to_proposal: float,
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
        "actor_mean_l2_to_proposal": actor_mean_l2_to_proposal,
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
    positive_metrics: Mapping[str, float],
    actor_mean_l2_to_base: float,
    actor_mean_l2_to_proposal: float,
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
        "actor_mean_l2_to_proposal": actor_mean_l2_to_proposal,
        "accepted": accepted,
        "rejection_reason": rejection_reason,
    }


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "repaired_checkpoint_written",
        "base_interpolation_used_for_repair",
        "diagnostic_rows_used_as_positive",
        "donor_plus_action_used_as_loss_target",
        "checkpoint_weights_mutated",
        "non_actor_mean_parameter_changed",
        *FORBIDDEN_GUARDRAILS.keys(),
    ]
    return [{"guardrail": key, "violated": bool(summary.get(key, False)), "value": summary.get(key, False)} for key in keys]


def run_selected_proposal_candidate_repair(
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
    """Repair one proposal candidate in memory and write metrics only."""

    materialization_dir = Path(materialization_run_dir)
    base_path = Path(base_checkpoint)
    proposal_path = Path(proposal_checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    base_checksum_before = _sha256(base_path)
    proposal_checksum_before = _sha256(proposal_path)

    positive_arrays = _load_npz(materialization_dir / "positive_policy_targets.npz")
    diagnostic_arrays = _load_npz(materialization_dir / "diagnostic_policy_guardrails.npz")
    positive_rows = read_csv_rows(materialization_dir / "positive_policy_target_rows.csv")
    diagnostic_rows = read_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv")

    base_model = _load_base_model(base_path, device)
    proposal_model = _load_base_model(proposal_path, device)
    candidate = copy.deepcopy(proposal_model)
    candidate.eval()
    proposal_snapshots = _named_parameter_snapshots(candidate)
    _set_trainable_scope(candidate)

    sep_margin = _target_separation_margin(positive_arrays["preferred_action"], positive_arrays["wrong_history_action"])
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
    initial_actor_mean_l2_to_proposal = _actor_mean_l2(candidate, proposal_model)
    base_step_l2 = float(initial_step_fraction) * max(float(initial_actor_mean_l2_to_base), 1e-12)

    best_snapshots = _named_parameter_snapshots(candidate)
    current_positive_metrics = dict(initial_positive_metrics)
    current_actor_mean_l2_to_base = initial_actor_mean_l2_to_base
    current_actor_mean_l2_to_proposal = initial_actor_mean_l2_to_proposal
    accepted_backtracking_step_count = 0
    grad_norm_max = 0.0
    projection_stop_reason = "max_projection_steps_reached"
    step_rows: list[dict[str, Any]] = [
        _step_row(
            step=0,
            positive_metrics=initial_positive_metrics,
            actor_mean_l2_to_base=initial_actor_mean_l2_to_base,
            actor_mean_l2_to_proposal=initial_actor_mean_l2_to_proposal,
            grad_norm=0.0,
            accepted_factor=None,
            accepted_step_l2=None,
            stop_reason="initial",
        )
    ]
    backtracking_rows: list[dict[str, Any]] = []

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
        grad_norm = float(grad_norm_tensor.detach().cpu().item())
        grad_norm_max = max(grad_norm_max, grad_norm)
        if not math.isfinite(grad_norm) or grad_norm <= 0.0:
            projection_stop_reason = "gradient_null_or_nonfinite"
            step_rows.append(
                _step_row(
                    step=step,
                    positive_metrics=current_positive_metrics,
                    actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                    actor_mean_l2_to_proposal=current_actor_mean_l2_to_proposal,
                    grad_norm=grad_norm,
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
        accepted_base_l2: float | None = None
        accepted_proposal_l2: float | None = None
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
            proposal_base_l2 = _actor_mean_l2(candidate, base_model)
            proposal_proposal_l2 = _actor_mean_l2(candidate, proposal_model)
            finite_candidate = math.isfinite(proposal_metrics["exact_residual_mean"]) and math.isfinite(
                proposal_metrics["policy_action_residual_l2_max"]
            )
            improves_exact = proposal_metrics["exact_residual_mean"] < current_positive_metrics["exact_residual_mean"]
            trust_base = proposal_base_l2 <= current_actor_mean_l2_to_base + TRUST_REGION_TOLERANCE
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
                    positive_metrics=proposal_metrics,
                    actor_mean_l2_to_base=proposal_base_l2,
                    actor_mean_l2_to_proposal=proposal_proposal_l2,
                    accepted=accepted,
                    rejection_reason=rejection_reason,
                )
            )
            if accepted:
                accepted_vector = proposal_vector.detach().clone()
                accepted_metrics = dict(proposal_metrics)
                accepted_base_l2 = proposal_base_l2
                accepted_proposal_l2 = proposal_proposal_l2
                accepted_factor = float(factor)
                accepted_step_l2 = step_l2
                break
        if (
            accepted_vector is None
            or accepted_metrics is None
            or accepted_base_l2 is None
            or accepted_proposal_l2 is None
        ):
            _set_actor_mean_vector(candidate, current_vector)
            projection_stop_reason = "no_backtracking_candidate_accepted"
            step_rows.append(
                _step_row(
                    step=step,
                    positive_metrics=current_positive_metrics,
                    actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                    actor_mean_l2_to_proposal=current_actor_mean_l2_to_proposal,
                    grad_norm=grad_norm,
                    accepted_factor=None,
                    accepted_step_l2=None,
                    stop_reason=projection_stop_reason,
                )
            )
            break
        _set_actor_mean_vector(candidate, accepted_vector)
        accepted_backtracking_step_count += 1
        current_positive_metrics = dict(accepted_metrics)
        current_actor_mean_l2_to_base = float(accepted_base_l2)
        current_actor_mean_l2_to_proposal = float(accepted_proposal_l2)
        best_snapshots = _named_parameter_snapshots(candidate)
        step_rows.append(
            _step_row(
                step=step,
                positive_metrics=current_positive_metrics,
                actor_mean_l2_to_base=current_actor_mean_l2_to_base,
                actor_mean_l2_to_proposal=current_actor_mean_l2_to_proposal,
                grad_norm=grad_norm,
                accepted_factor=accepted_factor,
                accepted_step_l2=accepted_step_l2,
                stop_reason="accepted",
            )
        )
        reduction = initial_positive_metrics["exact_residual_mean"] - current_positive_metrics["exact_residual_mean"]
        reduction_ratio = (
            reduction / initial_positive_metrics["exact_residual_mean"]
            if initial_positive_metrics["exact_residual_mean"] > 0.0
            else 0.0
        )
        if reduction_ratio >= MIN_CANDIDATE_REDUCTION_RATIO:
            projection_stop_reason = "target_reduction_reached"
            break

    with torch.no_grad():
        for name, parameter in candidate.named_parameters():
            parameter.copy_(best_snapshots[name].to(device=parameter.device, dtype=parameter.dtype))
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
    repaired_actor_mean_l2_to_proposal = _actor_mean_l2(candidate, proposal_model)
    non_actor_mean_delta_to_proposal_max = _non_actor_mean_delta_max(candidate, proposal_snapshots)
    positive_exact_residual_reduction = (
        initial_positive_metrics["exact_residual_mean"] - repaired_positive_metrics["exact_residual_mean"]
    )
    positive_exact_residual_reduction_ratio = (
        positive_exact_residual_reduction / initial_positive_metrics["exact_residual_mean"]
        if initial_positive_metrics["exact_residual_mean"] > 0.0
        else 0.0
    )
    repaired_checkpoint_written = bool(list(output.rglob("*.pt")) or list(output.rglob("*.pth")))
    base_checksum_after = _sha256(base_path)
    proposal_checksum_after = _sha256(proposal_path)
    diagnostic_rows_used_as_positive = _diagnostics_used_as_positive(diagnostic_rows)
    donor_plus_action_used_as_loss_target = False
    guardrail_values = {
        **FORBIDDEN_GUARDRAILS,
        "repaired_checkpoint_written": repaired_checkpoint_written,
        "base_interpolation_used_for_repair": False,
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "donor_plus_action_used_as_loss_target": donor_plus_action_used_as_loss_target,
        "checkpoint_weights_mutated": bool(base_checksum_before != base_checksum_after or proposal_checksum_before != proposal_checksum_after),
        "non_actor_mean_parameter_changed": bool(non_actor_mean_delta_to_proposal_max != 0.0),
    }
    guardrail_violation_count = sum(1 for value in guardrail_values.values() if bool(value))
    candidate_pass = (
        len(positive_rows) == EXPECTED_POSITIVE_COUNT
        and len(diagnostic_rows) == EXPECTED_DIAGNOSTIC_COUNT
        and initial_positive_metrics["exact_residual_mean"] > MIN_INITIAL_EXACT_RESIDUAL
        and repaired_positive_metrics["exact_residual_mean"] < initial_positive_metrics["exact_residual_mean"]
        and positive_exact_residual_reduction_ratio >= MIN_CANDIDATE_REDUCTION_RATIO
        and accepted_backtracking_step_count >= 1
        and guardrail_violation_count == 0
    )
    if len(positive_rows) != EXPECTED_POSITIVE_COUNT:
        null_class = "positive_target_count_mismatch"
    elif len(diagnostic_rows) != EXPECTED_DIAGNOSTIC_COUNT:
        null_class = "diagnostic_guardrail_count_mismatch"
    elif initial_positive_metrics["exact_residual_mean"] <= MIN_INITIAL_EXACT_RESIDUAL:
        null_class = "nonmeasurable_initial_residual"
    elif repaired_positive_metrics["exact_residual_mean"] >= initial_positive_metrics["exact_residual_mean"]:
        null_class = "residual_not_reduced"
    elif positive_exact_residual_reduction_ratio < MIN_CANDIDATE_REDUCTION_RATIO:
        null_class = "reduction_ratio_below_threshold"
    elif guardrail_violation_count != 0:
        null_class = "guardrail_violation"
    elif candidate_pass:
        null_class = "selected_proposal_candidate_repair_public_pass"
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
        "positive_policy_target_count": len(positive_rows),
        "diagnostic_policy_guardrail_count": len(diagnostic_rows),
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
        "proposal_actor_mean_l2_to_base": initial_actor_mean_l2_to_base,
        "repaired_actor_mean_l2_to_base": repaired_actor_mean_l2_to_base,
        "repaired_actor_mean_l2_to_proposal": repaired_actor_mean_l2_to_proposal,
        "non_actor_mean_delta_to_proposal_max": non_actor_mean_delta_to_proposal_max,
        "accepted_backtracking_step_count": int(accepted_backtracking_step_count),
        "backtracking_candidate_count": len(backtracking_rows),
        "projection_stop_reason": projection_stop_reason,
        "grad_norm_max": grad_norm_max,
        "diagnostic_positive_weight_sum": _diagnostic_weight_sum(diagnostic_rows),
        "guardrail_violation_count": int(guardrail_violation_count),
        "passes_candidate_gate": bool(candidate_pass),
        "null_result_classification": null_class,
        **guardrail_values,
    }
    write_csv_rows(
        output / "repair_summary.csv",
        [
            _candidate_phase_row(
                phase="initial",
                positive_metrics=initial_positive_metrics,
                diagnostic_metrics=initial_diagnostic_metrics,
                actor_mean_l2_to_base=initial_actor_mean_l2_to_base,
                actor_mean_l2_to_proposal=initial_actor_mean_l2_to_proposal,
            ),
            _candidate_phase_row(
                phase="repaired",
                positive_metrics=repaired_positive_metrics,
                diagnostic_metrics=repaired_diagnostic_metrics,
                actor_mean_l2_to_base=repaired_actor_mean_l2_to_base,
                actor_mean_l2_to_proposal=repaired_actor_mean_l2_to_proposal,
            ),
        ],
    )
    write_csv_rows(output / "optimization_trace.csv", step_rows)
    write_csv_rows(output / "backtracking_candidates.csv", backtracking_rows)
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
        "initial_positive_exact_residual_mean": summary.get("initial_positive_exact_residual_mean"),
        "repaired_positive_exact_residual_mean": summary.get("repaired_positive_exact_residual_mean"),
        "positive_exact_residual_reduction": summary.get("positive_exact_residual_reduction"),
        "positive_exact_residual_reduction_ratio": summary.get("positive_exact_residual_reduction_ratio"),
        "initial_positive_action_l2_max": summary.get("initial_positive_action_l2_max"),
        "repaired_positive_action_l2_max": summary.get("repaired_positive_action_l2_max"),
        "proposal_actor_mean_l2_to_base": summary.get("proposal_actor_mean_l2_to_base"),
        "repaired_actor_mean_l2_to_base": summary.get("repaired_actor_mean_l2_to_base"),
        "repaired_actor_mean_l2_to_proposal": summary.get("repaired_actor_mean_l2_to_proposal"),
        "non_actor_mean_delta_to_proposal_max": summary.get("non_actor_mean_delta_to_proposal_max"),
        "accepted_backtracking_step_count": summary.get("accepted_backtracking_step_count"),
        "projection_stop_reason": summary.get("projection_stop_reason"),
        "passes_candidate_gate": summary.get("passes_candidate_gate"),
        "null_result_classification": summary.get("null_result_classification"),
        "guardrail_violation_count": summary.get("guardrail_violation_count"),
        "base_interpolation_used_for_repair": summary.get("base_interpolation_used_for_repair"),
        "repaired_checkpoint_written": summary.get("repaired_checkpoint_written"),
        "diagnostic_rows_used_as_positive": summary.get("diagnostic_rows_used_as_positive"),
        "donor_plus_action_used_as_loss_target": summary.get("donor_plus_action_used_as_loss_target"),
        "non_actor_mean_parameter_changed": summary.get("non_actor_mean_parameter_changed"),
        "source_candidate_id": candidate_summary.get("candidate_id"),
    }


def _count(rows: Sequence[Mapping[str, Any]], key: str, predicate: Callable[[Any], bool]) -> int:
    return sum(1 for row in rows if predicate(row.get(key)))


def _aggregate(rows: Sequence[Mapping[str, Any]], *, selected_count: int, checkpoint_artifact_count: int) -> dict[str, Any]:
    measurable = _count(rows, "initial_positive_exact_residual_mean", lambda value: _float(value) > MIN_INITIAL_EXACT_RESIDUAL)
    reduced = sum(
        1
        for row in rows
        if _float(row.get("repaired_positive_exact_residual_mean")) < _float(row.get("initial_positive_exact_residual_mean"))
    )
    primary_rows = [row for row in rows if math.isclose(_float(row.get("alpha")), PRIMARY_ALPHA, rel_tol=0.0, abs_tol=1e-12)]
    primary_pass = bool(primary_rows and _bool(primary_rows[0].get("passes_candidate_gate")))
    candidate_public_pass_count = _count(rows, "passes_candidate_gate", _bool)
    guardrail_violation_count = sum(int(_float(row.get("guardrail_violation_count", 0))) for row in rows)
    summary: dict[str, Any] = {
        "selected_candidate_count": len(rows),
        "expected_selected_candidate_count": int(selected_count),
        "measurable_initial_residual_count": measurable,
        "residual_reduced_count": reduced,
        "candidate_public_pass_count": candidate_public_pass_count,
        "primary_alpha_0_2_pass": primary_pass,
        "checkpoint_artifact_count": int(checkpoint_artifact_count),
        "base_interpolation_used_for_repair_count": _count(rows, "base_interpolation_used_for_repair", _bool),
        "non_actor_mean_parameter_changed_count": _count(rows, "non_actor_mean_parameter_changed", _bool),
        "diagnostic_rows_used_as_positive_count": _count(rows, "diagnostic_rows_used_as_positive", _bool),
        "donor_plus_action_used_as_loss_target_count": _count(rows, "donor_plus_action_used_as_loss_target", _bool),
        "guardrail_violation_count": guardrail_violation_count,
        "training_started_count": 0,
        "ppo_used_count": 0,
        "promoted_count": 0,
        "private_holdout_used_count": 0,
        "actor_input_contract_changed_count": 0,
        "level3_self_id_claim_count": 0,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["selected_candidate_count"]) >= 2
        and int(summary["measurable_initial_residual_count"]) == int(summary["selected_candidate_count"])
        and int(summary["residual_reduced_count"]) >= 1
        and int(summary["candidate_public_pass_count"]) >= 1
        and bool(summary["primary_alpha_0_2_pass"])
        and int(summary["checkpoint_artifact_count"]) == 0
        and int(summary["base_interpolation_used_for_repair_count"]) == 0
        and int(summary["non_actor_mean_parameter_changed_count"]) == 0
        and int(summary["diagnostic_rows_used_as_positive_count"]) == 0
        and int(summary["donor_plus_action_used_as_loss_target_count"]) == 0
        and int(summary["guardrail_violation_count"]) == 0
        and int(summary["training_started_count"]) == 0
        and int(summary["ppo_used_count"]) == 0
        and int(summary["promoted_count"]) == 0
        and int(summary["private_holdout_used_count"]) == 0
        and int(summary["actor_input_contract_changed_count"]) == 0
        and int(summary["level3_self_id_claim_count"]) == 0
    )
    stress_rows = [row for row in rows if math.isclose(_float(row.get("alpha")), 1.0, rel_tol=0.0, abs_tol=1e-12)]
    stress_pass = bool(stress_rows and _bool(stress_rows[0].get("passes_candidate_gate")))
    if int(summary["selected_candidate_count"]) < 2:
        null_class = "selected_candidate_count_below_threshold"
    elif int(summary["measurable_initial_residual_count"]) != int(summary["selected_candidate_count"]):
        null_class = "nonmeasurable_initial_residual"
    elif not bool(summary["primary_alpha_0_2_pass"]):
        null_class = "selected_proposal_repair_scope_insufficient"
    elif int(summary["checkpoint_artifact_count"]) != 0:
        null_class = "checkpoint_artifact_written"
    elif int(summary["base_interpolation_used_for_repair_count"]) != 0:
        null_class = "base_interpolation_repair_violation"
    elif int(summary["guardrail_violation_count"]) != 0:
        null_class = "guardrail_violation"
    elif bool(summary["passes_public_smoke_gates"]) and stress_pass:
        null_class = "selected_proposal_repair_public_pass"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "selected_proposal_primary_pass_stress_fail"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class
    return summary


def _aggregate_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{"metric": key, "value": value} for key, value in summary.items()]


def _aggregate_guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "checkpoint_artifact_count",
        "base_interpolation_used_for_repair_count",
        "non_actor_mean_parameter_changed_count",
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


def run_selected_proposal_repair(
    *,
    base_checkpoint: Path | str,
    candidate_summary: Path | str,
    materialization_run_dir: Path | str,
    run_dir: Path | str,
    selected_alphas: Sequence[float] = DEFAULT_SELECTED_ALPHAS,
    device: str = "cpu",
    repair_fn: RepairFunction = run_selected_proposal_candidate_repair,
) -> dict[str, Any]:
    """Run selected-proposal repair candidates and aggregate metrics."""

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
    summary = {
        "result_class": aggregate["result_class"],
        "base_checkpoint": str(base_checkpoint),
        "candidate_summary": str(candidate_summary),
        "materialization_run_dir": str(materialization_run_dir),
        "selected_alphas": [float(alpha) for alpha in selected_alphas],
        "proposal_source_type": "same_line_interpolation",
        "checkpoint_artifacts_allowed": False,
        "base_interpolation_allowed": False,
        **aggregate,
    }
    write_csv_rows(output / "candidate_summary.csv", rows)
    write_csv_rows(output / "aggregate_summary.csv", _aggregate_rows(aggregate))
    write_csv_rows(output / "guardrail_summary.csv", _aggregate_guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _parse_alphas(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-checkpoint selected-proposal repair probe.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--selected-alphas", type=_parse_alphas, default=DEFAULT_SELECTED_ALPHAS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_selected_proposal_repair(
        base_checkpoint=args.base_checkpoint,
        candidate_summary=args.candidate_summary,
        materialization_run_dir=args.materialization_run_dir,
        run_dir=args.run_dir,
        selected_alphas=tuple(args.selected_alphas),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"selected_candidate_count={summary['selected_candidate_count']}")
    print(f"residual_reduced_count={summary['residual_reduced_count']}")
    print(f"candidate_public_pass_count={summary['candidate_public_pass_count']}")
    print(f"primary_alpha_0_2_pass={summary['primary_alpha_0_2_pass']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
