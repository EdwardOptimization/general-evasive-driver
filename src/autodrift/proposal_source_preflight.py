"""No-checkpoint proposal-source preflight before projection repair."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_policy_target_exact_evaluator import (
    DEFAULT_MATERIALIZATION_RUN_DIR,
    run_contour_aware_policy_target_exact_evaluator,
)
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract


DEFAULT_CANDIDATE_CHECKPOINTS = Path("runs/m1362_bidirectional_active_set_interpolation_preflight/candidate_checkpoints.csv")
DEFAULT_ALPHA_SUMMARY = Path("runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv")
DEFAULT_RUN_DIR = Path("runs/m1650_proposal_source_preflight")
BASE_ALPHA = 0.1
MIN_SELECTED_RESIDUAL = 1e-8
MIN_SOURCE_CANDIDATES = 9
MIN_BRANCH_COMPATIBLE_CANDIDATES = 5
MIN_LARGER_PROPOSALS = 5
MIN_SELECTED_REPAIR_CANDIDATES = 1
FORBIDDEN_GUARDRAILS = {
    "training_started": False,
    "ppo_used": False,
    "projection_used": False,
    "proposal_repaired": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


ExactEvaluateFunction = Callable[..., dict[str, Any]]
ModelDeltaFunction = Callable[[Path, Path, str], dict[str, float]]


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


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


def _index_by_checkpoint(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("checkpoint", "")): row for row in rows}


def _load_model(checkpoint: Path, device: str) -> Any:
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    model.eval()
    return model


def _parameter_delta(base_checkpoint: Path, candidate_checkpoint: Path, device: str) -> dict[str, float]:
    base_model = _load_model(base_checkpoint, device)
    candidate_model = _load_model(candidate_checkpoint, device)
    base_params = dict(base_model.named_parameters())
    actor_parts: list[torch.Tensor] = []
    non_actor_parts: list[torch.Tensor] = []
    all_parts: list[torch.Tensor] = []
    max_abs = 0.0
    with torch.no_grad():
        for name, candidate_param in candidate_model.named_parameters():
            if name not in base_params:
                continue
            diff = (candidate_param.detach().float().cpu() - base_params[name].detach().float().cpu()).reshape(-1)
            if diff.numel() == 0:
                continue
            all_parts.append(diff)
            max_abs = max(max_abs, float(torch.max(torch.abs(diff)).item()))
            if name in {"actor_mean.weight", "actor_mean.bias"}:
                actor_parts.append(diff)
            else:
                non_actor_parts.append(diff)
    return {
        "parameter_l2_to_base": _vector_l2(all_parts),
        "parameter_max_abs_to_base": max_abs,
        "actor_mean_l2_to_base": _vector_l2(actor_parts),
        "non_actor_mean_l2_to_base": _vector_l2(non_actor_parts),
    }


def _vector_l2(parts: Sequence[torch.Tensor]) -> float:
    if not parts:
        return 0.0
    return float(torch.linalg.vector_norm(torch.cat(list(parts))).item())


def _candidate_role(
    *,
    alpha: float,
    branch_compatible: bool,
    m1362_preflight_pass: bool,
    positive_residual: float,
) -> str:
    if not branch_compatible:
        return "excluded"
    if math.isclose(alpha, BASE_ALPHA, rel_tol=0.0, abs_tol=1e-12):
        return "base_anchor"
    if alpha < BASE_ALPHA:
        return "control_pass" if m1362_preflight_pass else "control_failed"
    if positive_residual > MIN_SELECTED_RESIDUAL and not m1362_preflight_pass:
        return "repair_candidate"
    return "proposal_control"


def _candidate_summary_row(
    *,
    candidate_row: Mapping[str, Any],
    alpha_row: Mapping[str, Any],
    exact_summary: Mapping[str, Any],
    delta: Mapping[str, float],
    candidate_run_dir: Path,
) -> dict[str, Any]:
    alpha = _float(candidate_row.get("alpha"))
    checkpoint = str(candidate_row.get("checkpoint", ""))
    checkpoint_exists = Path(checkpoint).exists()
    actor_inputs_changed = _bool(candidate_row.get("actor_inputs_changed", False)) or _bool(
        exact_summary.get("actor_input_contract_changed", False)
    )
    forbidden_mutation = _bool(candidate_row.get("forbidden_parameter_mutation_detected", False))
    log_std_l2 = _float(candidate_row.get("log_std_l2", 0.0))
    branch_compatible = (
        checkpoint_exists
        and not actor_inputs_changed
        and not forbidden_mutation
        and math.isfinite(log_std_l2)
        and log_std_l2 == 0.0
        and not _bool(exact_summary.get("checkpoint_weights_mutated", False))
    )
    m1362_preflight_pass = _bool(alpha_row.get("preflight_pass", candidate_row.get("exact_admitted", False)))
    positive_residual = _float(exact_summary.get("positive_exact_residual_mean"))
    role = _candidate_role(
        alpha=alpha,
        branch_compatible=branch_compatible,
        m1362_preflight_pass=m1362_preflight_pass,
        positive_residual=positive_residual,
    )
    selected = role == "repair_candidate"
    return {
        "candidate_id": str(candidate_row.get("label", f"alpha_{alpha:g}")),
        "proposal_source_type": "same_line_interpolation",
        "alpha": alpha,
        "checkpoint": checkpoint,
        "candidate_run_dir": str(candidate_run_dir),
        "checkpoint_exists": checkpoint_exists,
        "is_base_anchor": role == "base_anchor",
        "branch_compatible": branch_compatible,
        "actor_input_contract_changed": actor_inputs_changed,
        "forbidden_parameter_mutation_detected": forbidden_mutation,
        "log_std_l2_to_base": log_std_l2,
        "parameter_l2_to_base": delta.get("parameter_l2_to_base", float("nan")),
        "parameter_max_abs_to_base": delta.get("parameter_max_abs_to_base", float("nan")),
        "actor_mean_l2_to_base": delta.get("actor_mean_l2_to_base", float("nan")),
        "non_actor_mean_l2_to_base": delta.get("non_actor_mean_l2_to_base", float("nan")),
        "positive_exact_residual_mean": positive_residual,
        "positive_policy_action_residual_l2_max": exact_summary.get("positive_policy_action_residual_l2_max"),
        "diagnostic_policy_action_residual_l2_max": exact_summary.get("diagnostic_policy_action_residual_l2_max"),
        "diagnostic_rows_used_as_positive": exact_summary.get("diagnostic_rows_used_as_positive"),
        "donor_plus_action_used_as_loss_target": exact_summary.get("donor_plus_action_used_as_loss_target"),
        "m1362_preflight_pass": m1362_preflight_pass,
        "m267_m264_gate_pass": _bool(alpha_row.get("m267_m264_gate_pass", False)),
        "m183_m170_gate_pass": _bool(alpha_row.get("m183_m170_gate_pass", False)),
        "repair_candidate_role": role,
        "selected_repair_candidate": selected,
        "exact_evaluator_passes_public_smoke_gates": exact_summary.get("passes_public_smoke_gates"),
        "exact_evaluator_null_result_classification": exact_summary.get("null_result_classification"),
    }


def _count(rows: Sequence[Mapping[str, Any]], key: str, predicate: Callable[[Any], bool]) -> int:
    return sum(1 for row in rows if predicate(row.get(key)))


def _summarize(rows: Sequence[Mapping[str, Any]], *, checkpoint_artifact_count: int) -> dict[str, Any]:
    source_count = len(rows)
    branch_count = _count(rows, "branch_compatible", _bool)
    base_count = _count(rows, "is_base_anchor", _bool)
    larger_count = sum(1 for row in rows if _float(row.get("alpha")) > BASE_ALPHA and _bool(row.get("branch_compatible")))
    selected_count = _count(rows, "selected_repair_candidate", _bool)
    summary: dict[str, Any] = {
        "source_candidate_count": source_count,
        "branch_compatible_candidate_count": branch_count,
        "base_anchor_count": base_count,
        "larger_proposal_candidate_count": larger_count,
        "selected_repair_candidate_count": selected_count,
        "checkpoint_artifact_count": int(checkpoint_artifact_count),
        "projection_used_count": 0,
        "proposal_repaired_count": 0,
        "diagnostic_rows_used_as_positive_count": _count(rows, "diagnostic_rows_used_as_positive", _bool),
        "donor_plus_action_used_as_loss_target_count": _count(rows, "donor_plus_action_used_as_loss_target", _bool),
        "actor_input_contract_changed_count": _count(rows, "actor_input_contract_changed", _bool),
        "training_started_count": 0,
        "ppo_used_count": 0,
        "promoted_count": 0,
        "private_holdout_used_count": 0,
        "level3_self_id_claim_count": 0,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_candidate_count"]) >= MIN_SOURCE_CANDIDATES
        and int(summary["branch_compatible_candidate_count"]) >= MIN_BRANCH_COMPATIBLE_CANDIDATES
        and int(summary["base_anchor_count"]) == 1
        and int(summary["larger_proposal_candidate_count"]) >= MIN_LARGER_PROPOSALS
        and int(summary["selected_repair_candidate_count"]) >= MIN_SELECTED_REPAIR_CANDIDATES
        and int(summary["checkpoint_artifact_count"]) == 0
        and int(summary["projection_used_count"]) == 0
        and int(summary["proposal_repaired_count"]) == 0
        and int(summary["diagnostic_rows_used_as_positive_count"]) == 0
        and int(summary["donor_plus_action_used_as_loss_target_count"]) == 0
        and int(summary["actor_input_contract_changed_count"]) == 0
        and int(summary["training_started_count"]) == 0
        and int(summary["ppo_used_count"]) == 0
        and int(summary["promoted_count"]) == 0
        and int(summary["private_holdout_used_count"]) == 0
        and int(summary["level3_self_id_claim_count"]) == 0
    )
    if int(summary["source_candidate_count"]) < MIN_SOURCE_CANDIDATES:
        null_class = "source_candidate_count_below_threshold"
    elif int(summary["branch_compatible_candidate_count"]) < MIN_BRANCH_COMPATIBLE_CANDIDATES:
        null_class = "branch_compatible_candidate_count_below_threshold"
    elif int(summary["base_anchor_count"]) != 1:
        null_class = "base_anchor_count_mismatch"
    elif int(summary["larger_proposal_candidate_count"]) < MIN_LARGER_PROPOSALS:
        null_class = "larger_proposal_candidate_count_below_threshold"
    elif int(summary["selected_repair_candidate_count"]) < MIN_SELECTED_REPAIR_CANDIDATES:
        null_class = "no_selected_repair_candidate"
    elif int(summary["checkpoint_artifact_count"]) != 0:
        null_class = "checkpoint_artifact_written"
    elif int(summary["projection_used_count"]) != 0 or int(summary["proposal_repaired_count"]) != 0:
        null_class = "projection_or_repair_used"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "proposal_source_preflight_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class
    return summary


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "checkpoint_artifact_count",
        "projection_used_count",
        "proposal_repaired_count",
        "diagnostic_rows_used_as_positive_count",
        "donor_plus_action_used_as_loss_target_count",
        "actor_input_contract_changed_count",
        "training_started_count",
        "ppo_used_count",
        "promoted_count",
        "private_holdout_used_count",
        "level3_self_id_claim_count",
    ]
    return [{"guardrail": key, "violated": _float(summary.get(key, 0)) != 0.0, "value": summary.get(key)} for key in keys]


def run_proposal_source_preflight(
    *,
    base_checkpoint: Path | str,
    candidate_checkpoints: Path | str,
    alpha_summary: Path | str,
    materialization_run_dir: Path | str,
    run_dir: Path | str,
    device: str = "cpu",
    exact_evaluate_fn: ExactEvaluateFunction = run_contour_aware_policy_target_exact_evaluator,
    model_delta_fn: ModelDeltaFunction = _parameter_delta,
) -> dict[str, Any]:
    """Evaluate proposal-source candidates without projection or checkpoint writes."""

    base_path = Path(base_checkpoint)
    candidate_table = Path(candidate_checkpoints)
    alpha_table = Path(alpha_summary)
    materialization_dir = Path(materialization_run_dir)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate_root = output / "candidates"
    candidate_root.mkdir(parents=True, exist_ok=True)
    candidate_rows = read_csv_rows(candidate_table)
    alpha_rows = _index_by_checkpoint(read_csv_rows(alpha_table))
    rows: list[dict[str, Any]] = []
    for raw_row in candidate_rows:
        label = str(raw_row.get("label", f"alpha_{raw_row.get('alpha', '')}"))
        checkpoint = Path(str(raw_row.get("checkpoint", "")))
        candidate_run_dir = candidate_root / _safe_id(label)
        candidate_run_dir.mkdir(parents=True, exist_ok=True)
        exact_summary = exact_evaluate_fn(
            materialization_run_dir=materialization_dir,
            checkpoint=checkpoint,
            run_dir=candidate_run_dir,
            device=device,
        )
        delta = model_delta_fn(base_path, checkpoint, device)
        alpha_row = alpha_rows.get(str(raw_row.get("checkpoint", "")), {})
        rows.append(
            _candidate_summary_row(
                candidate_row=raw_row,
                alpha_row=alpha_row,
                exact_summary=exact_summary,
                delta=delta,
                candidate_run_dir=candidate_run_dir,
            )
        )
    checkpoint_artifact_count = len(list(output.rglob("*.pt")))
    aggregate = _summarize(rows, checkpoint_artifact_count=checkpoint_artifact_count)
    summary = {
        "result_class": aggregate["result_class"],
        "base_checkpoint": str(base_path),
        "candidate_checkpoints": str(candidate_table),
        "alpha_summary": str(alpha_table),
        "materialization_run_dir": str(materialization_dir),
        "proposal_source_type": "same_line_interpolation",
        "checkpoint_artifacts_allowed": False,
        **FORBIDDEN_GUARDRAILS,
        **aggregate,
    }
    write_csv_rows(output / "candidate_summary.csv", rows)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-checkpoint proposal-source preflight.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--candidate-checkpoints", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINTS)
    parser.add_argument("--alpha-summary", type=Path, default=DEFAULT_ALPHA_SUMMARY)
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_proposal_source_preflight(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoints=args.candidate_checkpoints,
        alpha_summary=args.alpha_summary,
        materialization_run_dir=args.materialization_run_dir,
        run_dir=args.run_dir,
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"source_candidate_count={summary['source_candidate_count']}")
    print(f"branch_compatible_candidate_count={summary['branch_compatible_candidate_count']}")
    print(f"selected_repair_candidate_count={summary['selected_repair_candidate_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
