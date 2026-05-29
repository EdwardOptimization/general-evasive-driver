"""No-update exact evaluator for contour-aware policy targets."""

from __future__ import annotations

import argparse
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_tensor_capture_dry_run import _predict_action, _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


DEFAULT_MATERIALIZATION_RUN_DIR = Path("runs/m1630_contour_aware_full_target_materialization")
DEFAULT_RUN_DIR = Path("runs/m1633_contour_aware_policy_target_exact_evaluator")
EXPECTED_POSITIVE_COUNT = 39
EXPECTED_DIAGNOSTIC_COUNT = 232
ACTION_L2_TOLERANCE = 1e-6
LAMBDA_WRONG = 1.0
LAMBDA_SEP = 0.25
MAX_SEP_MARGIN = 0.05
SEP_QUANTILE = 0.25
FORBIDDEN_GUARDRAILS = {
    "loss_constructed": False,
    "objective_config_written": False,
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


PredictFunction = Callable[[Any, np.ndarray, np.ndarray], np.ndarray]


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as handle:
        return {key: np.asarray(handle[key], dtype=np.float32) for key in handle.files}


def _shape_rows(group: str, arrays: Mapping[str, np.ndarray]) -> list[dict[str, Any]]:
    return [
        {
            "corpus_role": group,
            "array": name,
            "dtype": str(array.dtype),
            "shape": "x".join(str(dim) for dim in array.shape),
            "finite": bool(np.all(np.isfinite(array))),
        }
        for name, array in arrays.items()
    ]


def _arrays_finite(arrays: Mapping[str, np.ndarray]) -> bool:
    return all(bool(np.all(np.isfinite(array))) for array in arrays.values())


def _max_source_l2(rows: Sequence[Mapping[str, Any]]) -> float:
    values: list[float] = []
    for row in rows:
        for key in (
            "source_preferred_action_l2",
            "source_wrong_history_action_l2",
            "source_donor_plus_hidden_action_l2",
        ):
            value = _float(row.get(key))
            if math.isfinite(value):
                values.append(value)
    return max(values) if values else float("nan")


def _diagnostic_weight_sum(rows: Sequence[Mapping[str, Any]]) -> float:
    return sum(_float(row.get("role_weight", 0.0)) for row in rows if _truthy(row.get("used_as_positive", False)))


def _diagnostics_used_as_positive(rows: Sequence[Mapping[str, Any]]) -> bool:
    return any(_truthy(row.get("used_as_positive", False)) or _float(row.get("role_weight", 0.0)) != 0.0 for row in rows)


def _shape_ok(arrays: Mapping[str, np.ndarray], *, expected_rows: int) -> bool:
    hidden_dim = int(arrays["correct_hidden"].shape[1]) if arrays["correct_hidden"].ndim == 2 else 0
    return (
        list(arrays["observation"].shape) == [expected_rows, HUMAN_VIEW_OBS_DIM]
        and hidden_dim > 0
        and list(arrays["correct_hidden"].shape) == [expected_rows, hidden_dim]
        and list(arrays["wrong_hidden"].shape) == [expected_rows, hidden_dim]
        and list(arrays["preferred_action"].shape) == [expected_rows, 3]
        and list(arrays["wrong_history_action"].shape) == [expected_rows, 3]
        and list(arrays["donor_plus_hidden_action"].shape) == [expected_rows, 3]
    )


def _evaluate_rows(
    *,
    arrays: Mapping[str, np.ndarray],
    metadata_rows: Sequence[Mapping[str, Any]],
    model: Any,
    predict_fn: PredictFunction,
    role: str,
    role_weight: float,
    sep_margin: float,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    output: list[dict[str, Any]] = []
    correct_l2: list[float] = []
    wrong_l2: list[float] = []
    target_sep_l2: list[float] = []
    policy_sep_l2: list[float] = []
    sep_residual: list[float] = []
    donor_pref_l2: list[float] = []
    donor_wrong_l2: list[float] = []
    for index, row in enumerate(metadata_rows):
        observation = arrays["observation"][index]
        correct_hidden = arrays["correct_hidden"][index]
        wrong_hidden = arrays["wrong_hidden"][index]
        preferred_action = arrays["preferred_action"][index]
        wrong_history_action = arrays["wrong_history_action"][index]
        donor_plus_action = arrays["donor_plus_hidden_action"][index]
        correct_action = np.asarray(predict_fn(model, observation, correct_hidden), dtype=np.float32).reshape(3)
        wrong_action = np.asarray(predict_fn(model, observation, wrong_hidden), dtype=np.float32).reshape(3)
        correct_residual = float(np.linalg.norm(correct_action.astype(np.float64) - preferred_action.astype(np.float64)))
        wrong_residual = float(np.linalg.norm(wrong_action.astype(np.float64) - wrong_history_action.astype(np.float64)))
        target_sep = float(np.linalg.norm(preferred_action.astype(np.float64) - wrong_history_action.astype(np.float64)))
        policy_sep = float(np.linalg.norm(correct_action.astype(np.float64) - wrong_action.astype(np.float64)))
        sep = float(max(0.0, sep_margin - policy_sep))
        donor_pref = float(np.linalg.norm(donor_plus_action.astype(np.float64) - preferred_action.astype(np.float64)))
        donor_wrong = float(np.linalg.norm(donor_plus_action.astype(np.float64) - wrong_history_action.astype(np.float64)))
        correct_l2.append(correct_residual)
        wrong_l2.append(wrong_residual)
        target_sep_l2.append(target_sep)
        policy_sep_l2.append(policy_sep)
        sep_residual.append(sep)
        donor_pref_l2.append(donor_pref)
        donor_wrong_l2.append(donor_wrong)
        output.append(
            {
                "target_id": row.get("target_id", row.get("pair_id", "")),
                "pair_id": row.get("pair_id", ""),
                "corpus_role": role,
                "source_run": row.get("source_run", ""),
                "used_as_positive": role == POSITIVE_ROLE,
                "role_weight": role_weight,
                "correct_action_l2": correct_residual,
                "wrong_history_action_l2": wrong_residual,
                "target_preferred_wrong_action_l2": target_sep,
                "policy_correct_wrong_action_l2": policy_sep,
                "separation_margin": sep_margin,
                "separation_residual": sep,
                "donor_plus_action_preferred_l2": donor_pref,
                "donor_plus_action_wrong_history_l2": donor_wrong,
                "donor_plus_action_used_as_loss_target": False,
            }
        )
    metrics = {
        "correct_l2_max": max(correct_l2) if correct_l2 else float("nan"),
        "wrong_l2_max": max(wrong_l2) if wrong_l2 else float("nan"),
        "correct_mse_mean": float(np.mean(np.square(correct_l2))) if correct_l2 else float("nan"),
        "wrong_mse_mean": float(np.mean(np.square(wrong_l2))) if wrong_l2 else float("nan"),
        "target_sep_l2_min": min(target_sep_l2) if target_sep_l2 else float("nan"),
        "target_sep_l2_mean": float(np.mean(target_sep_l2)) if target_sep_l2 else float("nan"),
        "policy_sep_l2_min": min(policy_sep_l2) if policy_sep_l2 else float("nan"),
        "policy_sep_l2_mean": float(np.mean(policy_sep_l2)) if policy_sep_l2 else float("nan"),
        "sep_residual_max": max(sep_residual) if sep_residual else float("nan"),
        "sep_residual_mse_mean": float(np.mean(np.square(sep_residual))) if sep_residual else float("nan"),
        "donor_plus_action_preferred_l2_mean": float(np.mean(donor_pref_l2)) if donor_pref_l2 else float("nan"),
        "donor_plus_action_wrong_history_l2_mean": float(np.mean(donor_wrong_l2)) if donor_wrong_l2 else float("nan"),
    }
    metrics["exact_residual_mean"] = (
        metrics["correct_mse_mean"] + LAMBDA_WRONG * metrics["wrong_mse_mean"] + LAMBDA_SEP * metrics["sep_residual_mse_mean"]
    )
    return output, metrics


def _objective_summary_rows(metrics_by_role: Mapping[str, Mapping[str, float]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for role, metrics in metrics_by_role.items():
        for metric, value in metrics.items():
            output.append({"corpus_role": role, "metric": metric, "value": value})
    return output


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "diagnostic_rows_used_as_positive",
        "donor_plus_action_used_as_loss_target",
        "checkpoint_weights_mutated",
        *FORBIDDEN_GUARDRAILS.keys(),
    ]
    return [{"guardrail": key, "violated": bool(summary.get(key, False)), "value": summary.get(key, False)} for key in keys]


def run_contour_aware_policy_target_exact_evaluator(
    *,
    materialization_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
    device: str = "cpu",
    expected_positive_count: int = EXPECTED_POSITIVE_COUNT,
    expected_diagnostic_count: int = EXPECTED_DIAGNOSTIC_COUNT,
    predict_fn: PredictFunction | None = None,
    model: Any | None = None,
) -> dict[str, Any]:
    """Evaluate M1632 objective semantics without updating the policy."""

    materialization_dir = Path(materialization_run_dir)
    checkpoint_path = Path(checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checksum_before = _sha256(checkpoint_path)
    positive_arrays = _load_npz(materialization_dir / "positive_policy_targets.npz")
    diagnostic_arrays = _load_npz(materialization_dir / "diagnostic_policy_guardrails.npz")
    positive_rows = read_csv_rows(materialization_dir / "positive_policy_target_rows.csv")
    diagnostic_rows = read_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv")

    if predict_fn is None:
        loaded_model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
        assert_p0_model_contract(loaded_model)
        model_for_predict = loaded_model
        predict = _predict_action
    else:
        model_for_predict = model
        predict = predict_fn

    positive_target_sep = np.linalg.norm(
        positive_arrays["preferred_action"].astype(np.float64) - positive_arrays["wrong_history_action"].astype(np.float64),
        axis=1,
    )
    sep_margin = float(min(MAX_SEP_MARGIN, np.quantile(positive_target_sep, SEP_QUANTILE))) if positive_target_sep.size else 0.0
    positive_eval_rows, positive_metrics = _evaluate_rows(
        arrays=positive_arrays,
        metadata_rows=positive_rows,
        model=model_for_predict,
        predict_fn=predict,
        role=POSITIVE_ROLE,
        role_weight=1.0,
        sep_margin=sep_margin,
    )
    diagnostic_eval_rows, diagnostic_metrics = _evaluate_rows(
        arrays=diagnostic_arrays,
        metadata_rows=diagnostic_rows,
        model=model_for_predict,
        predict_fn=predict,
        role=DIAGNOSTIC_ROLE,
        role_weight=0.0,
        sep_margin=sep_margin,
    )
    checksum_after = _sha256(checkpoint_path)
    checkpoint_weights_mutated = checksum_before != checksum_after
    positive_finite = _arrays_finite(positive_arrays) and all(
        math.isfinite(_float(row.get(key)))
        for row in positive_eval_rows
        for key in ("correct_action_l2", "wrong_history_action_l2", "separation_residual")
    )
    diagnostic_finite = _arrays_finite(diagnostic_arrays) and all(
        math.isfinite(_float(row.get(key)))
        for row in diagnostic_eval_rows
        for key in ("correct_action_l2", "wrong_history_action_l2", "separation_residual")
    )
    diagnostic_rows_used_as_positive = _diagnostics_used_as_positive(diagnostic_rows)
    diagnostic_positive_weight_sum = _diagnostic_weight_sum(diagnostic_rows)
    positive_policy_action_residual_l2_max = max(positive_metrics["correct_l2_max"], positive_metrics["wrong_l2_max"])
    diagnostic_policy_action_residual_l2_max = max(diagnostic_metrics["correct_l2_max"], diagnostic_metrics["wrong_l2_max"])
    positive_source_action_reproduction_l2_max = _max_source_l2(positive_rows)
    diagnostic_source_action_reproduction_l2_max = _max_source_l2(diagnostic_rows)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary: dict[str, Any] = {
        "result_class": "contour_aware_policy_target_exact_evaluator",
        "materialization_run_dir": str(materialization_dir),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "checkpoint_weights_mutated": bool(checkpoint_weights_mutated),
        "exact_evaluator_implemented": True,
        "objective_evaluated": True,
        "positive_policy_target_count": len(positive_rows),
        "diagnostic_policy_guardrail_count": len(diagnostic_rows),
        "positive_observation_shape": list(positive_arrays["observation"].shape),
        "diagnostic_observation_shape": list(diagnostic_arrays["observation"].shape),
        "positive_action_residuals_finite": bool(positive_finite),
        "diagnostic_action_residuals_finite": bool(diagnostic_finite),
        "positive_policy_action_residual_l2_max": positive_policy_action_residual_l2_max,
        "diagnostic_policy_action_residual_l2_max": diagnostic_policy_action_residual_l2_max,
        "positive_source_action_reproduction_l2_max": positive_source_action_reproduction_l2_max,
        "diagnostic_source_action_reproduction_l2_max": diagnostic_source_action_reproduction_l2_max,
        "positive_exact_residual_mean": positive_metrics["exact_residual_mean"],
        "diagnostic_exact_residual_mean": diagnostic_metrics["exact_residual_mean"],
        "separation_margin": sep_margin,
        "donor_plus_action_used_as_loss_target": False,
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "diagnostic_positive_weight_sum": diagnostic_positive_weight_sum,
        "guardrail_violation_count": int(guardrail_violation_count),
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        len(positive_rows) == int(expected_positive_count)
        and len(diagnostic_rows) == int(expected_diagnostic_count)
        and _shape_ok(positive_arrays, expected_rows=int(expected_positive_count))
        and _shape_ok(diagnostic_arrays, expected_rows=int(expected_diagnostic_count))
        and bool(summary["positive_action_residuals_finite"])
        and bool(summary["diagnostic_action_residuals_finite"])
        and float(summary["positive_policy_action_residual_l2_max"]) <= ACTION_L2_TOLERANCE
        and float(summary["diagnostic_policy_action_residual_l2_max"]) <= ACTION_L2_TOLERANCE
        and float(summary["positive_source_action_reproduction_l2_max"]) <= ACTION_L2_TOLERANCE
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and float(summary["diagnostic_positive_weight_sum"]) == 0.0
        and not bool(summary["donor_plus_action_used_as_loss_target"])
        and not bool(summary["checkpoint_weights_mutated"])
        and not bool(summary["loss_constructed"])
        and not bool(summary["objective_config_written"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    if len(positive_rows) != int(expected_positive_count):
        null_class = "positive_target_count_mismatch"
    elif len(diagnostic_rows) != int(expected_diagnostic_count):
        null_class = "diagnostic_guardrail_count_mismatch"
    elif not bool(summary["positive_action_residuals_finite"]) or not bool(summary["diagnostic_action_residuals_finite"]):
        null_class = "nonfinite_action_residual_failure"
    elif bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif bool(summary["donor_plus_action_used_as_loss_target"]):
        null_class = "donor_plus_action_loss_target_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_policy_target_exact_evaluator_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class

    write_csv_rows(output / "positive_objective_rows.csv", positive_eval_rows)
    write_csv_rows(output / "diagnostic_guardrail_rows.csv", diagnostic_eval_rows)
    write_csv_rows(
        output / "objective_summary.csv",
        _objective_summary_rows({POSITIVE_ROLE: positive_metrics, DIAGNOSTIC_ROLE: diagnostic_metrics}),
    )
    write_csv_rows(
        output / "shape_summary.csv",
        _shape_rows(POSITIVE_ROLE, positive_arrays) + _shape_rows(DIAGNOSTIC_ROLE, diagnostic_arrays),
    )
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contour-aware policy-target exact evaluator.")
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_contour_aware_policy_target_exact_evaluator(
        materialization_run_dir=args.materialization_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"positive_policy_target_count={summary['positive_policy_target_count']}")
    print(f"diagnostic_policy_guardrail_count={summary['diagnostic_policy_guardrail_count']}")
    print(f"positive_policy_action_residual_l2_max={summary['positive_policy_action_residual_l2_max']}")
    print(f"diagnostic_policy_action_residual_l2_max={summary['diagnostic_policy_action_residual_l2_max']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
