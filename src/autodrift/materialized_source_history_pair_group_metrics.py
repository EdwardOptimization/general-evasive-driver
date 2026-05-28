"""No-update group metrics for materialized source-history objective rows."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return float(np.mean(finite)) if finite else float("nan")


def _fraction(flags: list[bool]) -> float:
    return float(sum(bool(flag) for flag in flags) / len(flags)) if flags else 0.0


def _sign_quadrant(row: dict[str, str]) -> str:
    correct_positive = _finite_float(row["correct_preference_margin"]) > 0.0
    wrong_positive = _finite_float(row["wrong_history_preference_margin"]) > 0.0
    return ("c+" if correct_positive else "c-") + "_" + ("w+" if wrong_positive else "w-")


def _distance_margins(row: dict[str, str]) -> tuple[float, float]:
    correct_margin = _finite_float(row["correct_distance_to_rejected"]) - _finite_float(row["correct_distance_to_preferred"])
    wrong_margin = _finite_float(row["wrong_distance_to_preferred"]) - _finite_float(row["wrong_distance_to_rejected"])
    return float(correct_margin), float(wrong_margin)


def _group_key(row: dict[str, str]) -> str:
    return f"{row.get('source_identity', '')}|{row.get('probe_template', '')}"


def _group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row)].append(row)
    return dict(grouped)


def _same(values: set[str]) -> str:
    return next(iter(values)) if len(values) == 1 else ""


def build_pair_group_metrics(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    group_outputs: list[dict[str, Any]] = []
    for group_id, values in sorted(_group_rows(rows).items()):
        conditions = {str(row.get("condition", "")) for row in values}
        source_identities = {str(row.get("source_identity", "")) for row in values}
        probe_templates = {str(row.get("probe_template", "")) for row in values}
        source_families = {str(row.get("source_family", "")) for row in values}
        folds = {str(row.get("fold", "")) for row in values}
        quadrants = [_sign_quadrant(row) for row in values]
        correct_margins = [_finite_float(row["correct_preference_margin"]) for row in values]
        wrong_margins = [_finite_float(row["wrong_history_preference_margin"]) for row in values]
        joint_margins = [min(correct, wrong) for correct, wrong in zip(correct_margins, wrong_margins)]
        distance_margins = [_distance_margins(row) for row in values]
        distance_joint = [min(correct, wrong) for correct, wrong in distance_margins]
        all_rows_both_directional = all(item == "c+_w+" for item in quadrants)
        all_rows_distance_both = all(correct > 0.0 and wrong > 0.0 for correct, wrong in distance_margins)
        one_sided_conflict = Counter(quadrants) == Counter({"c+_w-": 1, "c-_w+": 1})
        both_negative = all(item == "c-_w-" for item in quadrants)
        valid_two_condition_group = (
            len(values) == 2
            and conditions == {"A", "B"}
            and len(source_identities) == 1
            and len(probe_templates) == 1
        )
        group_outputs.append(
            {
                "group_id": group_id,
                "source_identity": _same(source_identities),
                "probe_template": _same(probe_templates),
                "source_family": _same(source_families),
                "fold": int(float(_same(folds))) if len(folds) == 1 and _same(folds) else -1,
                "row_count": int(len(values)),
                "condition_count": int(len(conditions)),
                "conditions": "|".join(sorted(conditions)),
                "valid_two_condition_group": bool(valid_two_condition_group),
                "quadrant_counts": ";".join(f"{key}:{count}" for key, count in sorted(Counter(quadrants).items())),
                "group_all_rows_both_directional": bool(all_rows_both_directional),
                "group_all_rows_distance_both": bool(all_rows_distance_both),
                "group_one_sided_conflict": bool(one_sided_conflict),
                "group_both_negative": bool(both_negative),
                "group_min_correct_margin": float(min(correct_margins)) if correct_margins else float("nan"),
                "group_min_wrong_margin": float(min(wrong_margins)) if wrong_margins else float("nan"),
                "group_min_joint_margin": float(min(joint_margins)) if joint_margins else float("nan"),
                "group_mean_joint_margin": _mean(joint_margins),
                "group_min_distance_joint_margin": float(min(distance_joint)) if distance_joint else float("nan"),
                "group_mean_combined_loss": _mean([_finite_float(row["combined_loss"]) for row in values]),
                "group_mean_history_action_l2": _mean([_finite_float(row["history_action_l2"]) for row in values]),
            }
        )
    family_summary = _summary_by(group_outputs, "source_family")
    fold_summary = _summary_by(group_outputs, "fold")
    return group_outputs, family_summary, fold_summary


def _summary_by(groups: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in groups:
        grouped[str(row.get(key, ""))].append(row)
    output: list[dict[str, Any]] = []
    for value, rows in sorted(grouped.items(), key=lambda item: item[0]):
        output.append(
            {
                key: value,
                "group_count": int(len(rows)),
                "valid_two_condition_group_fraction": _fraction(
                    [bool(row["valid_two_condition_group"]) for row in rows]
                ),
                "group_all_rows_both_directional_fraction": _fraction(
                    [bool(row["group_all_rows_both_directional"]) for row in rows]
                ),
                "group_all_rows_distance_both_fraction": _fraction(
                    [bool(row["group_all_rows_distance_both"]) for row in rows]
                ),
                "group_one_sided_conflict_fraction": _fraction(
                    [bool(row["group_one_sided_conflict"]) for row in rows]
                ),
                "group_both_negative_fraction": _fraction([bool(row["group_both_negative"]) for row in rows]),
                "group_min_joint_margin_mean": _mean([float(row["group_min_joint_margin"]) for row in rows]),
                "group_mean_combined_loss_mean": _mean([float(row["group_mean_combined_loss"]) for row in rows]),
            }
        )
    return output


def run_pair_group_metrics(*, rows_path: Path, run_dir: Path) -> dict[str, Any]:
    rows_path = Path(rows_path)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_csv(rows_path)
    group_rows, family_rows, fold_rows = build_pair_group_metrics(rows)
    write_csv_rows(run_dir / "group_rows.csv", group_rows)
    write_csv_rows(run_dir / "family_group_summary.csv", family_rows)
    write_csv_rows(run_dir / "fold_group_summary.csv", fold_rows)

    valid_count = sum(bool(row["valid_two_condition_group"]) for row in group_rows)
    both_count = sum(bool(row["group_all_rows_both_directional"]) for row in group_rows)
    distance_both_count = sum(bool(row["group_all_rows_distance_both"]) for row in group_rows)
    one_sided_count = sum(bool(row["group_one_sided_conflict"]) for row in group_rows)
    both_negative_count = sum(bool(row["group_both_negative"]) for row in group_rows)
    result_class = (
        "materialized_source_history_pair_group_metrics_pass"
        if valid_count == len(group_rows) and len(group_rows) > 0
        else "materialized_source_history_pair_group_metrics_group_failure"
    )
    summary = {
        "run_type": "materialized_source_history_pair_group_metrics",
        "result_class": result_class,
        "rows_path": str(rows_path),
        "row_count": int(len(rows)),
        "group_count": int(len(group_rows)),
        "valid_two_condition_group_count": int(valid_count),
        "group_all_rows_both_directional_count": int(both_count),
        "group_all_rows_distance_both_count": int(distance_both_count),
        "group_one_sided_conflict_count": int(one_sided_count),
        "group_both_negative_count": int(both_negative_count),
        "group_all_rows_both_directional_fraction": float(both_count / len(group_rows)) if group_rows else 0.0,
        "group_one_sided_conflict_fraction": float(one_sided_count / len(group_rows)) if group_rows else 0.0,
        "group_both_negative_fraction": float(both_negative_count / len(group_rows)) if group_rows else 0.0,
        "group_min_joint_margin_mean": _mean([float(row["group_min_joint_margin"]) for row in group_rows]),
        "worst_family_group_pass_fraction": min(
            (float(row["group_all_rows_both_directional_fraction"]) for row in family_rows),
            default=float("nan"),
        ),
        "worst_fold_group_pass_fraction": min(
            (float(row["group_all_rows_both_directional_fraction"]) for row in fold_rows),
            default=float("nan"),
        ),
        "checkpoint_loaded": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_update_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "labels_enter_actor_input": False,
        "group_rows_csv": run_dir / "group_rows.csv",
        "family_group_summary_csv": run_dir / "family_group_summary.csv",
        "fold_group_summary_csv": run_dir / "fold_group_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="materialized_source_history_pair_group_metrics")
    summary = run_pair_group_metrics(rows_path=args.rows, run_dir=run_dir)
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
