"""No-training audit for source-history directional conflicts."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


QUADRANTS = (
    "correct_positive_wrong_positive",
    "correct_positive_wrong_negative",
    "correct_negative_wrong_positive",
    "correct_negative_wrong_negative",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row["history_intervention_id"]), str(row["intervention_id"]), str(row["pair_id"]))


def _quadrant(correct_margin: float, wrong_margin: float) -> str:
    correct_positive = float(correct_margin) > 0.0
    wrong_positive = float(wrong_margin) > 0.0
    if correct_positive and wrong_positive:
        return "correct_positive_wrong_positive"
    if correct_positive and not wrong_positive:
        return "correct_positive_wrong_negative"
    if not correct_positive and wrong_positive:
        return "correct_negative_wrong_positive"
    return "correct_negative_wrong_negative"


def _counts(rows: list[dict[str, Any]], suffix: str) -> dict[str, int]:
    counts = {f"{suffix}_{name}": 0 for name in QUADRANTS}
    for row in rows:
        counts[f"{suffix}_{row[f'{suffix}_quadrant']}"] += 1
    return counts


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def _percentile(values: list[float], q: float) -> float:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return float("nan")
    return float(np.percentile(np.asarray(finite, dtype=np.float64), float(q)))


def build_directional_conflict_rows(
    before_rows: list[dict[str, str]],
    after_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    after_by_key = {_key(row): row for row in after_rows}
    joined: list[dict[str, Any]] = []
    for before in before_rows:
        key = _key(before)
        after = after_by_key.get(key)
        if after is None:
            raise ValueError(f"missing after row for key={key}")
        before_correct = _finite_float(before["correct_preference_margin"])
        before_wrong = _finite_float(before["wrong_history_preference_margin"])
        after_correct = _finite_float(after["correct_preference_margin"])
        after_wrong = _finite_float(after["wrong_history_preference_margin"])
        before_combined = _finite_float(before["combined_loss"])
        after_combined = _finite_float(after["combined_loss"])
        before_abs_margin = min(abs(before_correct), abs(before_wrong))
        after_abs_margin = min(abs(after_correct), abs(after_wrong))
        before_quadrant = _quadrant(before_correct, before_wrong)
        after_quadrant = _quadrant(after_correct, after_wrong)
        joined.append(
            {
                "history_intervention_id": int(float(before["history_intervention_id"])),
                "intervention_id": int(float(before["intervention_id"])),
                "pair_id": int(float(before["pair_id"])),
                "condition": str(before["condition"]),
                "probe_template": str(before["probe_template"]),
                "before_correct_preference_margin": before_correct,
                "before_wrong_history_preference_margin": before_wrong,
                "after_correct_preference_margin": after_correct,
                "after_wrong_history_preference_margin": after_wrong,
                "before_quadrant": before_quadrant,
                "after_quadrant": after_quadrant,
                "quadrant_changed": bool(before_quadrant != after_quadrant),
                "before_both_positive": bool(before_quadrant == "correct_positive_wrong_positive"),
                "after_both_positive": bool(after_quadrant == "correct_positive_wrong_positive"),
                "before_mutually_exclusive": bool(
                    before_quadrant
                    in {
                        "correct_positive_wrong_negative",
                        "correct_negative_wrong_positive",
                    }
                ),
                "after_mutually_exclusive": bool(
                    after_quadrant
                    in {
                        "correct_positive_wrong_negative",
                        "correct_negative_wrong_positive",
                    }
                ),
                "before_combined_loss": before_combined,
                "after_combined_loss": after_combined,
                "combined_loss_delta": float(after_combined - before_combined),
                "before_min_abs_preference_margin": float(before_abs_margin),
                "after_min_abs_preference_margin": float(after_abs_margin),
                "min_abs_preference_margin_delta": float(after_abs_margin - before_abs_margin),
            }
        )
    return joined


def classify_directional_conflict(rows: list[dict[str, Any]]) -> tuple[str, str]:
    row_count = len(rows)
    after_both_positive = sum(bool(row["after_both_positive"]) for row in rows)
    after_mutually_exclusive = sum(bool(row["after_mutually_exclusive"]) for row in rows)
    loss_delta_mean = _mean([_finite_float(row["combined_loss_delta"]) for row in rows])
    min_abs_delta_mean = _mean([_finite_float(row["min_abs_preference_margin_delta"]) for row in rows])
    if row_count == 0:
        return "source_history_directional_conflict_audit_empty", "repair artifact inputs"
    if after_both_positive == row_count:
        return "source_history_directional_conflict_resolved", "route to public proof-retention design"
    if loss_delta_mean < 0.0 and after_mutually_exclusive == row_count:
        if min_abs_delta_mean < 0.0:
            return "source_history_directional_conflict_magnitude_compression", "design row-wise directional repair"
        return "source_history_directional_conflict_sign_locked", "design trainable-scope or corpus conflict audit"
    if loss_delta_mean < 0.0:
        return "source_history_directional_conflict_mixed_loss_positive", "design targeted directional repair"
    return "source_history_directional_conflict_no_loss_improvement", "do not continue this update path"


def run_directional_conflict_audit(
    *,
    before_rows_path: Path,
    after_rows_path: Path,
    run_dir: Path,
) -> dict[str, Any]:
    before_rows_path = Path(before_rows_path)
    after_rows_path = Path(after_rows_path)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    before_rows = _read_csv(before_rows_path)
    after_rows = _read_csv(after_rows_path)
    conflict_rows = build_directional_conflict_rows(before_rows, after_rows)
    write_csv_rows(run_dir / "directional_conflict_rows.csv", conflict_rows)

    row_count = len(conflict_rows)
    result_class, recommended_next_step = classify_directional_conflict(conflict_rows)
    before_counts = _counts(conflict_rows, "before")
    after_counts = _counts(conflict_rows, "after")
    loss_deltas = [_finite_float(row["combined_loss_delta"]) for row in conflict_rows]
    min_abs_margin_deltas = [_finite_float(row["min_abs_preference_margin_delta"]) for row in conflict_rows]
    quadrant_changed_count = sum(bool(row["quadrant_changed"]) for row in conflict_rows)
    after_both_positive_count = sum(bool(row["after_both_positive"]) for row in conflict_rows)
    after_mutually_exclusive_count = sum(bool(row["after_mutually_exclusive"]) for row in conflict_rows)
    loss_improved_count = sum(_finite_float(row["combined_loss_delta"]) < 0.0 for row in conflict_rows)
    min_abs_margin_decreased_count = sum(
        _finite_float(row["min_abs_preference_margin_delta"]) < 0.0 for row in conflict_rows
    )

    group_sizes: dict[tuple[int, str], int] = {}
    for row in conflict_rows:
        group_key = (int(row["pair_id"]), str(row["probe_template"]))
        group_sizes[group_key] = group_sizes.get(group_key, 0) + 1
    group_size_values = list(group_sizes.values())

    summary = {
        "run_type": "source_history_directional_conflict_audit",
        "before_rows": str(before_rows_path),
        "after_rows": str(after_rows_path),
        "row_count": int(row_count),
        **before_counts,
        **after_counts,
        "before_both_directional_fraction": (
            float(before_counts["before_correct_positive_wrong_positive"] / row_count) if row_count else 0.0
        ),
        "after_both_directional_fraction": (
            float(after_counts["after_correct_positive_wrong_positive"] / row_count) if row_count else 0.0
        ),
        "after_mutually_exclusive_count": int(after_mutually_exclusive_count),
        "after_mutually_exclusive_fraction": float(after_mutually_exclusive_count / row_count) if row_count else 0.0,
        "after_both_positive_count": int(after_both_positive_count),
        "quadrant_changed_count": int(quadrant_changed_count),
        "loss_improved_count": int(loss_improved_count),
        "loss_improved_fraction": float(loss_improved_count / row_count) if row_count else 0.0,
        "combined_loss_delta_mean": _mean(loss_deltas),
        "combined_loss_delta_p50": _percentile(loss_deltas, 50),
        "combined_loss_delta_min": min(loss_deltas) if loss_deltas else float("nan"),
        "combined_loss_delta_max": max(loss_deltas) if loss_deltas else float("nan"),
        "min_abs_preference_margin_delta_mean": _mean(min_abs_margin_deltas),
        "min_abs_preference_margin_delta_p50": _percentile(min_abs_margin_deltas, 50),
        "min_abs_margin_decreased_count": int(min_abs_margin_decreased_count),
        "min_abs_margin_decreased_fraction": (
            float(min_abs_margin_decreased_count / row_count) if row_count else 0.0
        ),
        "pair_probe_group_count": int(len(group_sizes)),
        "pair_probe_group_size_min": int(min(group_size_values)) if group_size_values else 0,
        "pair_probe_group_size_max": int(max(group_size_values)) if group_size_values else 0,
        "result_class": result_class,
        "recommended_next_step": recommended_next_step,
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "directional_conflict_rows_csv": run_dir / "directional_conflict_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit source-history before/after directional conflict rows.")
    parser.add_argument("--before-rows", type=Path, required=True)
    parser.add_argument("--after-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run_directional_conflict_audit(
        before_rows_path=args.before_rows,
        after_rows_path=args.after_rows,
        run_dir=args.run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
