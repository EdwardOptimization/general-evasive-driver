"""No-checkpoint stress test for contour-aware damped projection repair."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.contour_aware_exact_objective_projection_repair import (
    DEFAULT_BACKTRACKING_FACTORS,
    DEFAULT_INITIAL_STEP_FRACTION,
    DEFAULT_MAX_PROJECTION_STEPS,
    DEFAULT_MATERIALIZATION_RUN_DIR,
    DEFAULT_PERTURB_SCALE,
    DEFAULT_PROJECTION_MODE,
    MIN_INITIAL_EXACT_RESIDUAL,
    PROJECTION_MODE_DAMPED_BACKTRACKING,
    run_contour_aware_exact_objective_projection_repair,
)
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT


DEFAULT_RUN_DIR = Path("runs/m1646_contour_aware_damped_projection_stress_test")
DEFAULT_STRESS_SCALES = (1e-4, 3e-4, 1e-3)
DEFAULT_STRESS_SEEDS = (1645, 1646, 1647)
MIN_CANDIDATE_PUBLIC_PASS_COUNT = 8
MIN_ACCEPTED_BACKTRACKING_COUNT = 8
MIN_REDUCTION_RATIO = 0.25
MEDIAN_REDUCTION_RATIO = 0.50


RepairFunction = Callable[..., dict[str, Any]]


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


def _candidate_id(scale: float, seed: int) -> str:
    scale_id = f"{float(scale):.0e}".replace("+", "").replace("-", "m")
    return f"scale_{scale_id}_seed_{int(seed)}"


def _candidate_row(candidate_id: str, scale: float, seed: int, run_dir: Path, summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "perturb_scale": float(scale),
        "perturb_seed": int(seed),
        "candidate_run_dir": str(run_dir),
        "initial_positive_exact_residual_mean": summary.get("initial_positive_exact_residual_mean"),
        "repaired_positive_exact_residual_mean": summary.get("repaired_positive_exact_residual_mean"),
        "positive_exact_residual_reduction_ratio": summary.get("positive_exact_residual_reduction_ratio"),
        "initial_positive_action_l2_max": summary.get("initial_positive_action_l2_max"),
        "repaired_positive_action_l2_max": summary.get("repaired_positive_action_l2_max"),
        "initial_actor_mean_l2_to_base": summary.get("initial_actor_mean_l2_to_base"),
        "repaired_actor_mean_l2_to_base": summary.get("repaired_actor_mean_l2_to_base"),
        "accepted_backtracking_step_count": summary.get("accepted_backtracking_step_count"),
        "backtracking_candidate_count": summary.get("backtracking_candidate_count"),
        "projection_stop_reason": summary.get("projection_stop_reason"),
        "passes_public_smoke_gates": summary.get("passes_public_smoke_gates"),
        "null_result_classification": summary.get("null_result_classification"),
        "guardrail_violation_count": summary.get("guardrail_violation_count"),
        "repaired_checkpoint_written": summary.get("repaired_checkpoint_written"),
        "base_interpolation_used_for_repair": summary.get("base_interpolation_used_for_repair"),
        "diagnostic_rows_used_as_positive": summary.get("diagnostic_rows_used_as_positive"),
        "donor_plus_action_used_as_loss_target": summary.get("donor_plus_action_used_as_loss_target"),
        "training_started": summary.get("training_started"),
        "ppo_used": summary.get("ppo_used"),
        "promoted": summary.get("promoted"),
        "private_holdout_used": summary.get("private_holdout_used"),
        "actor_input_contract_changed": summary.get("actor_input_contract_changed"),
        "level3_self_id_claim_made": summary.get("level3_self_id_claim_made"),
    }


def _count(rows: Sequence[Mapping[str, Any]], key: str, predicate: Callable[[Any], bool]) -> int:
    return sum(1 for row in rows if predicate(row.get(key)))


def _max_float(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    return max(finite) if finite else float("nan")


def _min_float(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    return min(finite) if finite else float("nan")


def _median_float(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    return float(np.median(finite)) if finite else float("nan")


def _aggregate(rows: Sequence[Mapping[str, Any]], *, expected_count: int, checkpoint_artifact_count: int) -> dict[str, Any]:
    measurable = _count(rows, "initial_positive_exact_residual_mean", lambda value: _float(value) > MIN_INITIAL_EXACT_RESIDUAL)
    reduced = sum(
        1
        for row in rows
        if _float(row.get("repaired_positive_exact_residual_mean")) < _float(row.get("initial_positive_exact_residual_mean"))
    )
    candidate_public_pass = _count(rows, "passes_public_smoke_gates", _bool)
    accepted_backtracking = sum(1 for row in rows if _float(row.get("accepted_backtracking_step_count")) >= 1.0)
    summary: dict[str, Any] = {
        "stress_candidate_count": len(rows),
        "expected_stress_candidate_count": int(expected_count),
        "measurable_initial_residual_count": measurable,
        "residual_reduced_count": reduced,
        "candidate_public_pass_count": candidate_public_pass,
        "accepted_backtracking_candidate_count": accepted_backtracking,
        "min_positive_exact_residual_reduction_ratio": _min_float(rows, "positive_exact_residual_reduction_ratio"),
        "median_positive_exact_residual_reduction_ratio": _median_float(rows, "positive_exact_residual_reduction_ratio"),
        "max_positive_exact_residual_reduction_ratio": _max_float(rows, "positive_exact_residual_reduction_ratio"),
        "max_guardrail_violation_count": _max_float(rows, "guardrail_violation_count"),
        "checkpoint_artifact_count": int(checkpoint_artifact_count),
        "base_interpolation_used_for_repair_count": _count(rows, "base_interpolation_used_for_repair", _bool),
        "diagnostic_rows_used_as_positive_count": _count(rows, "diagnostic_rows_used_as_positive", _bool),
        "donor_plus_action_used_as_loss_target_count": _count(rows, "donor_plus_action_used_as_loss_target", _bool),
        "training_started_count": _count(rows, "training_started", _bool),
        "ppo_used_count": _count(rows, "ppo_used", _bool),
        "promoted_count": _count(rows, "promoted", _bool),
        "private_holdout_used_count": _count(rows, "private_holdout_used", _bool),
        "actor_input_contract_changed_count": _count(rows, "actor_input_contract_changed", _bool),
        "level3_self_id_claim_count": _count(rows, "level3_self_id_claim_made", _bool),
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["stress_candidate_count"]) == int(expected_count)
        and int(summary["measurable_initial_residual_count"]) == int(expected_count)
        and int(summary["residual_reduced_count"]) == int(expected_count)
        and int(summary["candidate_public_pass_count"]) >= MIN_CANDIDATE_PUBLIC_PASS_COUNT
        and int(summary["accepted_backtracking_candidate_count"]) >= MIN_ACCEPTED_BACKTRACKING_COUNT
        and _float(summary["min_positive_exact_residual_reduction_ratio"]) >= MIN_REDUCTION_RATIO
        and _float(summary["median_positive_exact_residual_reduction_ratio"]) >= MEDIAN_REDUCTION_RATIO
        and _float(summary["max_guardrail_violation_count"]) == 0.0
        and int(summary["checkpoint_artifact_count"]) == 0
        and int(summary["base_interpolation_used_for_repair_count"]) == 0
        and int(summary["diagnostic_rows_used_as_positive_count"]) == 0
        and int(summary["donor_plus_action_used_as_loss_target_count"]) == 0
        and int(summary["training_started_count"]) == 0
        and int(summary["ppo_used_count"]) == 0
        and int(summary["promoted_count"]) == 0
        and int(summary["private_holdout_used_count"]) == 0
        and int(summary["actor_input_contract_changed_count"]) == 0
        and int(summary["level3_self_id_claim_count"]) == 0
    )
    if int(summary["stress_candidate_count"]) != int(expected_count):
        null_class = "stress_candidate_count_mismatch"
    elif int(summary["measurable_initial_residual_count"]) != int(expected_count):
        null_class = "nonmeasurable_initial_residual"
    elif int(summary["residual_reduced_count"]) != int(expected_count):
        null_class = "residual_not_reduced"
    elif int(summary["candidate_public_pass_count"]) < MIN_CANDIDATE_PUBLIC_PASS_COUNT:
        null_class = "candidate_pass_count_below_threshold"
    elif int(summary["accepted_backtracking_candidate_count"]) < MIN_ACCEPTED_BACKTRACKING_COUNT:
        null_class = "accepted_backtracking_count_below_threshold"
    elif _float(summary["min_positive_exact_residual_reduction_ratio"]) < MIN_REDUCTION_RATIO:
        null_class = "reduction_ratio_below_threshold"
    elif _float(summary["median_positive_exact_residual_reduction_ratio"]) < MEDIAN_REDUCTION_RATIO:
        null_class = "reduction_ratio_below_threshold"
    elif _float(summary["max_guardrail_violation_count"]) != 0.0:
        null_class = "guardrail_violation"
    elif int(summary["checkpoint_artifact_count"]) != 0:
        null_class = "checkpoint_artifact_written"
    elif int(summary["base_interpolation_used_for_repair_count"]) != 0:
        null_class = "base_interpolation_repair_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "damped_projection_stress_public_pass"
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
        "base_interpolation_used_for_repair_count",
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


def run_contour_aware_exact_objective_projection_stress_test(
    *,
    materialization_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
    device: str = "cpu",
    scales: Sequence[float] = DEFAULT_STRESS_SCALES,
    seeds: Sequence[int] = DEFAULT_STRESS_SEEDS,
    repair_fn: RepairFunction = run_contour_aware_exact_objective_projection_repair,
) -> dict[str, Any]:
    """Run the M1646 fixed-grid damped projection stress test."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate_root = output / "candidates"
    candidate_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for scale in scales:
        for seed in seeds:
            candidate_id = _candidate_id(float(scale), int(seed))
            candidate_run_dir = candidate_root / candidate_id
            candidate_summary = repair_fn(
                materialization_run_dir=materialization_run_dir,
                checkpoint=checkpoint,
                run_dir=candidate_run_dir,
                device=device,
                perturb_scale=float(scale),
                perturb_seed=int(seed),
                projection_mode=PROJECTION_MODE_DAMPED_BACKTRACKING,
                max_projection_steps=DEFAULT_MAX_PROJECTION_STEPS,
                initial_step_fraction=DEFAULT_INITIAL_STEP_FRACTION,
                backtracking_factors=DEFAULT_BACKTRACKING_FACTORS,
            )
            rows.append(_candidate_row(candidate_id, float(scale), int(seed), candidate_run_dir, candidate_summary))
    checkpoint_artifact_count = len(list(output.rglob("*.pt")))
    aggregate = _aggregate(rows, expected_count=len(scales) * len(seeds), checkpoint_artifact_count=checkpoint_artifact_count)
    summary = {
        "result_class": aggregate["result_class"],
        "materialization_run_dir": str(materialization_run_dir),
        "checkpoint": str(checkpoint),
        "projection_mode": PROJECTION_MODE_DAMPED_BACKTRACKING,
        "perturb_scales": list(scales),
        "perturb_seeds": [int(seed) for seed in seeds],
        "checkpoint_artifacts_allowed": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "labels_enter_actor_input": False,
        "level3_self_id_claim_made": False,
        **aggregate,
    }
    write_csv_rows(output / "candidate_summary.csv", rows)
    write_csv_rows(output / "aggregate_summary.csv", _aggregate_rows(aggregate))
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def _parse_scales(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def _parse_seeds(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contour-aware damped projection stress test.")
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--scales", type=_parse_scales, default=DEFAULT_STRESS_SCALES)
    parser.add_argument("--seeds", type=_parse_seeds, default=DEFAULT_STRESS_SEEDS)
    args = parser.parse_args()
    summary = run_contour_aware_exact_objective_projection_stress_test(
        materialization_run_dir=args.materialization_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
        device=args.device,
        scales=tuple(args.scales),
        seeds=tuple(args.seeds),
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"stress_candidate_count={summary['stress_candidate_count']}")
    print(f"candidate_public_pass_count={summary['candidate_public_pass_count']}")
    print(f"residual_reduced_count={summary['residual_reduced_count']}")
    print(f"min_positive_exact_residual_reduction_ratio={summary['min_positive_exact_residual_reduction_ratio']}")
    print(f"median_positive_exact_residual_reduction_ratio={summary['median_positive_exact_residual_reduction_ratio']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
