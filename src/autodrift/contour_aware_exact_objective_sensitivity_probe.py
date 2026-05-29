"""Sensitivity probe for the contour-aware exact objective."""

from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.contour_aware_policy_target_exact_evaluator import (
    DEFAULT_MATERIALIZATION_RUN_DIR,
    run_contour_aware_policy_target_exact_evaluator,
)
from autodrift.contour_aware_tensor_capture_dry_run import _predict_action, _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract


DEFAULT_RUN_DIR = Path("runs/m1636_contour_aware_exact_objective_sensitivity_probe")
DEFAULT_SCALES = (0.0, 1e-4, 3e-4, 1e-3)
BASE_L2_TOLERANCE = 1e-6
MIN_PERTURBED_EXACT_RESIDUAL = 1e-8
MIN_PERTURBED_L2_RESIDUAL = 1e-5
FORBIDDEN_GUARDRAILS = {
    "perturbed_checkpoint_written": False,
    "actor_update_run": False,
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


LoadModelFunction = Callable[[Path, str], Any]
EvaluateCandidateFunction = Callable[[str, float, Any, Path], dict[str, Any]]


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


def _candidate_id(scale: float) -> str:
    return f"scale_{scale:.0e}".replace("+", "").replace("-", "m")


def _load_base_model(checkpoint: Path, device: str) -> Any:
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    model.eval()
    return model


def _rms_normalized_noise_like(tensor: torch.Tensor, *, generator: torch.Generator) -> torch.Tensor:
    noise = torch.randn(tensor.shape, dtype=tensor.dtype, device=tensor.device, generator=generator)
    rms = torch.sqrt(torch.mean(noise.float() ** 2)).to(dtype=tensor.dtype, device=tensor.device)
    return noise / torch.clamp(rms, min=torch.finfo(tensor.dtype).eps)


def _perturb_actor_mean(model: Any, *, scale: float, seed: int) -> dict[str, float]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    stats: dict[str, float] = {}
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            if name not in {"actor_mean.weight", "actor_mean.bias"}:
                continue
            noise = _rms_normalized_noise_like(parameter, generator=generator)
            delta = float(scale) * noise
            parameter.add_(delta)
            stats[f"{name}_delta_l2"] = float(torch.linalg.vector_norm(delta.float()).item())
            stats[f"{name}_delta_rms"] = float(torch.sqrt(torch.mean(delta.float() ** 2)).item())
    stats["perturbed_parameter_count"] = float(sum(1 for key in stats if key.endswith("_delta_l2")))
    return stats


def _default_evaluate_candidate(
    *,
    materialization_run_dir: Path,
    checkpoint: Path,
    device: str,
) -> EvaluateCandidateFunction:
    def evaluate(candidate_id: str, scale: float, model: Any, candidate_run_dir: Path) -> dict[str, Any]:
        del candidate_id, scale
        return run_contour_aware_policy_target_exact_evaluator(
            materialization_run_dir=materialization_run_dir,
            checkpoint=checkpoint,
            run_dir=candidate_run_dir,
            device=device,
            predict_fn=_predict_action,
            model=model,
        )

    return evaluate


def _guardrail_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"guardrail": key, "violated": bool(summary.get(key, False)), "value": summary.get(key, False)}
        for key in FORBIDDEN_GUARDRAILS
    ]


def run_contour_aware_exact_objective_sensitivity_probe(
    *,
    materialization_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
    device: str = "cpu",
    scales: Sequence[float] = DEFAULT_SCALES,
    seed: int = 1636,
    load_model_fn: LoadModelFunction | None = None,
    evaluate_candidate_fn: EvaluateCandidateFunction | None = None,
) -> dict[str, Any]:
    """Evaluate exact-objective response to in-memory actor_mean perturbations."""

    materialization_dir = Path(materialization_run_dir)
    checkpoint_path = Path(checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates_dir = output / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    checksum_before = _sha256(checkpoint_path)
    loader = load_model_fn or _load_base_model
    evaluator = evaluate_candidate_fn or _default_evaluate_candidate(
        materialization_run_dir=materialization_dir,
        checkpoint=checkpoint_path,
        device=device,
    )
    base_model = loader(checkpoint_path, device)
    candidate_rows: list[dict[str, Any]] = []
    for index, scale_value in enumerate(scales):
        scale = float(scale_value)
        candidate = copy.deepcopy(base_model)
        if hasattr(candidate, "eval"):
            candidate.eval()
        perturb_stats: dict[str, float] = {"perturbed_parameter_count": 0.0}
        if scale != 0.0:
            perturb_stats = _perturb_actor_mean(candidate, scale=scale, seed=int(seed) + index)
        candidate_id = _candidate_id(scale)
        candidate_run_dir = candidates_dir / candidate_id
        candidate_summary = evaluator(candidate_id, scale, candidate, candidate_run_dir)
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "scale": scale,
                "candidate_run_dir": str(candidate_run_dir),
                "positive_exact_residual_mean": candidate_summary.get("positive_exact_residual_mean"),
                "positive_policy_action_residual_l2_max": candidate_summary.get("positive_policy_action_residual_l2_max"),
                "diagnostic_exact_residual_mean": candidate_summary.get("diagnostic_exact_residual_mean"),
                "diagnostic_policy_action_residual_l2_max": candidate_summary.get("diagnostic_policy_action_residual_l2_max"),
                "evaluator_passes_public_smoke_gates": candidate_summary.get("passes_public_smoke_gates"),
                "evaluator_null_result_classification": candidate_summary.get("null_result_classification"),
                "checkpoint_weights_mutated": candidate_summary.get("checkpoint_weights_mutated"),
                "donor_plus_action_used_as_loss_target": candidate_summary.get("donor_plus_action_used_as_loss_target"),
                "diagnostic_rows_used_as_positive": candidate_summary.get("diagnostic_rows_used_as_positive"),
                **perturb_stats,
            }
        )
    checksum_after = _sha256(checkpoint_path)
    base_rows = [row for row in candidate_rows if float(row["scale"]) == 0.0]
    perturbed_rows = [row for row in candidate_rows if float(row["scale"]) != 0.0]
    base_row = base_rows[0] if base_rows else {}
    base_positive_exact = _float(base_row.get("positive_exact_residual_mean"))
    base_positive_l2 = _float(base_row.get("positive_policy_action_residual_l2_max"))
    perturbed_exact_values = [_float(row.get("positive_exact_residual_mean")) for row in perturbed_rows]
    perturbed_l2_values = [_float(row.get("positive_policy_action_residual_l2_max")) for row in perturbed_rows]
    max_perturbed_exact = max([value for value in perturbed_exact_values if math.isfinite(value)], default=float("nan"))
    max_perturbed_l2 = max([value for value in perturbed_l2_values if math.isfinite(value)], default=float("nan"))
    base_residual_near_zero = math.isfinite(base_positive_l2) and base_positive_l2 <= BASE_L2_TOLERANCE
    measurable_perturbation_residual = (
        math.isfinite(max_perturbed_exact)
        and math.isfinite(max_perturbed_l2)
        and max_perturbed_exact > MIN_PERTURBED_EXACT_RESIDUAL
        and max_perturbed_l2 > MIN_PERTURBED_L2_RESIDUAL
    )
    perturbed_checkpoint_written = bool(list(output.rglob("*.pt")))
    guardrail_values = {
        **FORBIDDEN_GUARDRAILS,
        "perturbed_checkpoint_written": perturbed_checkpoint_written,
    }
    guardrail_violation_count = sum(1 for value in guardrail_values.values() if bool(value))
    summary: dict[str, Any] = {
        "result_class": "contour_aware_exact_objective_sensitivity_probe",
        "materialization_run_dir": str(materialization_dir),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "checkpoint_weights_mutated": bool(checksum_before != checksum_after),
        "scale_count": len(scales),
        "candidate_count": len(candidate_rows),
        "base_positive_exact_residual_mean": base_positive_exact,
        "base_positive_policy_action_residual_l2_max": base_positive_l2,
        "base_residual_near_zero": bool(base_residual_near_zero),
        "max_positive_exact_residual_mean_over_perturbations": max_perturbed_exact,
        "max_positive_policy_action_residual_l2_max_over_perturbations": max_perturbed_l2,
        "measurable_perturbation_residual": bool(measurable_perturbation_residual),
        "positive_exact_residual_threshold": MIN_PERTURBED_EXACT_RESIDUAL,
        "positive_l2_residual_threshold": MIN_PERTURBED_L2_RESIDUAL,
        "guardrail_violation_count": int(guardrail_violation_count),
        **guardrail_values,
    }
    summary["passes_public_smoke_gates"] = (
        bool(summary["base_residual_near_zero"])
        and bool(summary["measurable_perturbation_residual"])
        and not bool(summary["checkpoint_weights_mutated"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    if not base_rows:
        null_class = "base_candidate_missing"
    elif not bool(summary["base_residual_near_zero"]):
        null_class = "base_residual_not_zero"
    elif not bool(summary["measurable_perturbation_residual"]):
        null_class = "controlled_perturbation_residual_null"
    elif int(summary["guardrail_violation_count"]) != 0:
        null_class = "guardrail_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_exact_objective_sensitivity_probe_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class
    write_csv_rows(output / "candidate_summary.csv", candidate_rows)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _parse_scales(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contour-aware exact-objective sensitivity probe.")
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--seed", type=int, default=1636)
    parser.add_argument("--scales", type=_parse_scales, default=DEFAULT_SCALES)
    args = parser.parse_args()
    summary = run_contour_aware_exact_objective_sensitivity_probe(
        materialization_run_dir=args.materialization_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
        device=args.device,
        seed=int(args.seed),
        scales=args.scales,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"base_positive_exact_residual_mean={summary['base_positive_exact_residual_mean']}")
    print(f"base_positive_policy_action_residual_l2_max={summary['base_positive_policy_action_residual_l2_max']}")
    print(
        "max_positive_exact_residual_mean_over_perturbations="
        f"{summary['max_positive_exact_residual_mean_over_perturbations']}"
    )
    print(
        "max_positive_policy_action_residual_l2_max_over_perturbations="
        f"{summary['max_positive_policy_action_residual_l2_max_over_perturbations']}"
    )
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
