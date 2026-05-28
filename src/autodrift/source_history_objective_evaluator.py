"""Exact no-update source-history preference objective evaluator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_history_policy_gate import run_source_history_policy_gate


DEFAULT_CORRECT_MARGIN = 0.05
DEFAULT_WRONG_MARGIN = 0.05
DEFAULT_WRONG_COEF = 1.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _softplus(value: float) -> float:
    return float(np.logaddexp(0.0, float(value)))


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def _finite(values: list[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def evaluate_source_history_objective_rows(
    policy_rows: list[dict[str, Any]],
    *,
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
) -> list[dict[str, Any]]:
    objective_rows: list[dict[str, Any]] = []
    for row in policy_rows:
        logp_cp = _finite_float(row["logp_cp"])
        logp_cr = _finite_float(row["logp_cr"])
        logp_wp = _finite_float(row["logp_wp"])
        logp_wr = _finite_float(row["logp_wr"])
        correct_loss = _softplus(logp_cr - logp_cp + float(correct_margin))
        wrong_loss = _softplus(logp_wp - logp_wr + float(wrong_margin))
        combined_loss = float(correct_loss + float(wrong_coef) * wrong_loss)
        finite_values = [
            logp_cp,
            logp_cr,
            logp_wp,
            logp_wr,
            correct_loss,
            wrong_loss,
            combined_loss,
            _finite_float(row["history_action_l2"]),
        ]
        objective_rows.append(
            {
                "history_intervention_id": int(float(row["history_intervention_id"])),
                "intervention_id": int(float(row["intervention_id"])),
                "pair_id": int(float(row["pair_id"])),
                "condition": str(row["condition"]),
                "probe_template": str(row["probe_template"]),
                "correct_history_id": int(float(row["correct_history_id"])),
                "wrong_history_id": int(float(row["wrong_history_id"])),
                "logp_cp": logp_cp,
                "logp_cr": logp_cr,
                "logp_wp": logp_wp,
                "logp_wr": logp_wr,
                "correct_preference_margin": _finite_float(row["correct_preference_margin"]),
                "wrong_history_preference_margin": _finite_float(row["wrong_history_preference_margin"]),
                "preferred_hidden_margin": _finite_float(row["preferred_hidden_margin"]),
                "rejected_hidden_margin": _finite_float(row["rejected_hidden_margin"]),
                "correct_preference_loss": correct_loss,
                "wrong_history_preference_loss": wrong_loss,
                "combined_loss": combined_loss,
                "history_action_l2": _finite_float(row["history_action_l2"]),
                "finite": bool(_finite(finite_values) and str(row.get("finite", "")).lower() == "true"),
            }
        )
    return objective_rows


def run_source_history_objective_evaluator(
    *,
    checkpoint_path: Path,
    history_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_path)
    history_run_dir = Path(history_run_dir)
    intervention_run_dir = Path(intervention_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    checksum_before = _sha256(checkpoint_path)
    policy_gate_dir = run_dir / "policy_gate"
    policy_summary = run_source_history_policy_gate(
        checkpoint_path=checkpoint_path,
        history_run_dir=history_run_dir,
        intervention_run_dir=intervention_run_dir,
        run_dir=policy_gate_dir,
        device=device,
    )
    checksum_after = _sha256(checkpoint_path)
    checkpoint_weights_mutated = checksum_before != checksum_after

    policy_rows = _read_csv(policy_gate_dir / "policy_gate_rows.csv")
    objective_rows = evaluate_source_history_objective_rows(
        policy_rows,
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    write_csv_rows(run_dir / "source_history_objective_rows.csv", objective_rows)

    correct_losses = [_finite_float(row["correct_preference_loss"]) for row in objective_rows]
    wrong_losses = [_finite_float(row["wrong_history_preference_loss"]) for row in objective_rows]
    combined_losses = [_finite_float(row["combined_loss"]) for row in objective_rows]
    correct_positive_count = sum(_finite_float(row["correct_preference_margin"]) > 0.0 for row in objective_rows)
    wrong_positive_count = sum(_finite_float(row["wrong_history_preference_margin"]) > 0.0 for row in objective_rows)
    both_directional_count = sum(
        _finite_float(row["correct_preference_margin"]) > 0.0
        and _finite_float(row["wrong_history_preference_margin"]) > 0.0
        for row in objective_rows
    )
    preferred_hidden_positive_count = sum(_finite_float(row["preferred_hidden_margin"]) > 0.0 for row in objective_rows)
    finite_row_count = sum(bool(row["finite"]) for row in objective_rows)
    exact_objective_finite = bool(finite_row_count == len(objective_rows) and _finite(combined_losses))
    result_class = (
        "source_history_objective_evaluator_pass"
        if exact_objective_finite and not checkpoint_weights_mutated
        else "source_history_objective_evaluator_nonfinite"
    )

    row_count = len(objective_rows)
    summary = {
        "run_type": "source_history_objective_evaluator",
        "checkpoint": str(checkpoint_path),
        "checkpoint_actor_encoder": policy_summary.get("checkpoint_actor_encoder", ""),
        "checkpoint_contract": policy_summary.get("checkpoint_contract", ""),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "checkpoint_weights_mutated": bool(checkpoint_weights_mutated),
        "history_run_dir": str(history_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "policy_gate_run_dir": str(policy_gate_dir),
        "correct_margin": float(correct_margin),
        "wrong_margin": float(wrong_margin),
        "wrong_coef": float(wrong_coef),
        "row_count": int(row_count),
        "finite_row_count": int(finite_row_count),
        "correct_preference_loss_mean": _mean(correct_losses),
        "wrong_history_preference_loss_mean": _mean(wrong_losses),
        "combined_loss_mean": _mean(combined_losses),
        "correct_preference_positive_count": int(correct_positive_count),
        "wrong_history_preference_positive_count": int(wrong_positive_count),
        "both_directional_count": int(both_directional_count),
        "preferred_hidden_margin_positive_count": int(preferred_hidden_positive_count),
        "correct_preference_positive_fraction": float(correct_positive_count / row_count) if row_count else 0.0,
        "wrong_history_preference_positive_fraction": float(wrong_positive_count / row_count) if row_count else 0.0,
        "both_directional_fraction": float(both_directional_count / row_count) if row_count else 0.0,
        "preferred_hidden_margin_positive_fraction": (
            float(preferred_hidden_positive_count / row_count) if row_count else 0.0
        ),
        "history_action_l2_mean": float(policy_summary.get("history_action_l2_mean", float("nan"))),
        "exact_objective_finite": bool(exact_objective_finite),
        "result_class": result_class,
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "source_history_objective_rows_csv": run_dir / "source_history_objective_rows.csv",
        "policy_gate_summary_json": policy_gate_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact no-update source-history objective evaluator.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--correct-margin", type=float, default=DEFAULT_CORRECT_MARGIN)
    parser.add_argument("--wrong-margin", type=float, default=DEFAULT_WRONG_MARGIN)
    parser.add_argument("--wrong-coef", type=float, default=DEFAULT_WRONG_COEF)
    args = parser.parse_args()
    summary = run_source_history_objective_evaluator(
        checkpoint_path=args.checkpoint,
        history_run_dir=args.history_run_dir,
        intervention_run_dir=args.intervention_run_dir,
        run_dir=args.run_dir,
        device=args.device,
        correct_margin=args.correct_margin,
        wrong_margin=args.wrong_margin,
        wrong_coef=args.wrong_coef,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
