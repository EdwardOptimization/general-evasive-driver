"""Build a no-training source-history concentration refresh plan."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


MARGIN_BUCKETS = (
    "deep_negative",
    "negative",
    "near_boundary",
    "positive",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _margin_bucket(value: Any) -> str:
    margin = _finite_float(value)
    if margin < -1.0:
        return "deep_negative"
    if margin < -0.05:
        return "negative"
    if margin < 0.0:
        return "near_boundary"
    return "positive"


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _group_universe(failed_offset_run_dir: Path) -> list[dict[str, Any]]:
    rows = _read_csv(failed_offset_run_dir / "eval_group_rows.csv")
    universe: list[dict[str, Any]] = []
    for row in rows:
        universe.append(
            {
                "pair_id": int(float(row["pair_id"])),
                "original_split_offset": int(float(row["split_offset"])),
                "original_offset_status": str(row["offset_status"]),
                "probe_template": str(row["probe_template"]),
                "source_family_pair": str(row["source_family_pair"]),
                "source_fault_pair": str(row["source_fault_pair"]),
                "row_count": int(float(row["row_count"])),
                "all_rows_both_positive": _bool(row["all_rows_both_positive"]),
                "group_min_margin": _finite_float(row["group_min_margin"]),
                "margin_bucket": _margin_bucket(row["group_min_margin"]),
            }
        )
    if not universe:
        raise ValueError("eval_group_rows.csv is empty")
    return universe


def _pair_features(group_rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    by_pair: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in group_rows:
        by_pair[int(row["pair_id"])].append(row)
    features: dict[int, dict[str, Any]] = {}
    for pair_id, rows in by_pair.items():
        source_family_pair = Counter(str(row["source_family_pair"]) for row in rows).most_common(1)[0][0]
        source_fault_pair = Counter(str(row["source_fault_pair"]) for row in rows).most_common(1)[0][0]
        feature_counts: Counter[str] = Counter()
        failed_group_count = 0
        for row in rows:
            feature_counts[f"source_family_pair={row['source_family_pair']}"] += 1
            feature_counts[f"source_fault_pair={row['source_fault_pair']}"] += 1
            feature_counts[f"probe_template={row['probe_template']}"] += 1
            feature_counts[f"margin_bucket={row['margin_bucket']}"] += 1
            failed_group_count += 0 if _bool(row["all_rows_both_positive"]) else 1
        features[pair_id] = {
            "pair_id": int(pair_id),
            "group_count": int(len(rows)),
            "source_family_pair": source_family_pair,
            "source_fault_pair": source_fault_pair,
            "feature_counts": dict(feature_counts),
            "failed_group_count": int(failed_group_count),
            "min_group_margin": min(_finite_float(row["group_min_margin"]) for row in rows),
        }
    return features


def _assign_balanced_folds(pair_features: dict[int, dict[str, Any]], *, fold_count: int) -> dict[int, int]:
    all_feature_counts: Counter[str] = Counter()
    for feature in pair_features.values():
        all_feature_counts.update(feature["feature_counts"])

    # Rare/high-failure pairs are placed first so the greedy assignment can spread them.
    ordered_pairs = sorted(
        pair_features.values(),
        key=lambda feature: (
            min(all_feature_counts[name] for name in feature["feature_counts"]),
            -int(feature["failed_group_count"]),
            str(feature["source_family_pair"]),
            int(feature["pair_id"]),
        ),
    )
    fold_pair_counts = [0 for _ in range(fold_count)]
    fold_feature_counts: list[Counter[str]] = [Counter() for _ in range(fold_count)]
    assignments: dict[int, int] = {}

    for feature in ordered_pairs:
        best_fold = 0
        best_score: tuple[float, int] | None = None
        for fold in range(fold_count):
            feature_pressure = 0.0
            for name, count in feature["feature_counts"].items():
                target = max(1.0, float(all_feature_counts[name]) / float(fold_count))
                feature_pressure += float(fold_feature_counts[fold][name] + count) / target
            score = (float(fold_pair_counts[fold]) * 2.0 + feature_pressure, fold)
            if best_score is None or score < best_score:
                best_score = score
                best_fold = fold
        pair_id = int(feature["pair_id"])
        assignments[pair_id] = int(best_fold)
        fold_pair_counts[best_fold] += 1
        fold_feature_counts[best_fold].update(feature["feature_counts"])
    return assignments


def _failed_combo_shares(failed_offset_run_dir: Path) -> dict[tuple[str, str], float]:
    rows = _read_csv(failed_offset_run_dir / "failed_eval_groups.csv")
    if not rows:
        return {}
    counts = Counter((str(row["source_family_pair"]), str(row["probe_template"])) for row in rows)
    total = float(sum(counts.values()))
    return {key: float(count / total) for key, count in counts.items()}


def _group_weights(
    group_rows: list[dict[str, Any]],
    failed_combo_shares: dict[tuple[str, str], float],
    *,
    min_weight: float,
    max_weight: float,
) -> list[dict[str, Any]]:
    family_counts = Counter(str(row["source_family_pair"]) for row in group_rows)
    probe_counts = Counter(str(row["probe_template"]) for row in group_rows)
    family_mean = float(np.mean(list(family_counts.values()))) if family_counts else 1.0
    probe_mean = float(np.mean(list(probe_counts.values()))) if probe_counts else 1.0
    rows: list[dict[str, Any]] = []
    for row in group_rows:
        family = str(row["source_family_pair"])
        probe = str(row["probe_template"])
        family_inverse = family_mean / max(1.0, float(family_counts[family]))
        probe_inverse = probe_mean / max(1.0, float(probe_counts[probe]))
        combo_share = float(failed_combo_shares.get((family, probe), 0.0))
        failed_combo_boost = min(0.5, combo_share)
        bucket = str(row["margin_bucket"])
        if bucket == "near_boundary":
            margin_boost = 0.15
        elif bucket == "deep_negative":
            margin_boost = 0.05
        else:
            margin_boost = 0.0
        raw_weight = 1.0 + 0.4 * (family_inverse - 1.0) + 0.2 * (probe_inverse - 1.0)
        raw_weight += failed_combo_boost + margin_boost
        weight = min(float(max_weight), max(float(min_weight), float(raw_weight)))
        rows.append(
            {
                "pair_id": int(row["pair_id"]),
                "probe_template": probe,
                "source_family_pair": family,
                "source_fault_pair": str(row["source_fault_pair"]),
                "margin_bucket": bucket,
                "original_split_offset": int(row["original_split_offset"]),
                "original_offset_status": str(row["original_offset_status"]),
                "all_rows_both_positive": bool(row["all_rows_both_positive"]),
                "group_min_margin": float(row["group_min_margin"]),
                "family_inverse_component": float(family_inverse),
                "probe_inverse_component": float(probe_inverse),
                "failed_combo_share": float(combo_share),
                "failed_combo_boost": float(failed_combo_boost),
                "margin_boost": float(margin_boost),
                "group_weight": float(weight),
                "pair_specific_weight_used": False,
            }
        )
    return rows


def _balanced_split_rows(group_rows: list[dict[str, Any]], assignments: dict[int, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted(group_rows, key=lambda item: (int(item["pair_id"]), str(item["probe_template"]))):
        rows.append(
            {
                "pair_id": int(row["pair_id"]),
                "assigned_eval_fold": int(assignments[int(row["pair_id"])]),
                "probe_template": str(row["probe_template"]),
                "source_family_pair": str(row["source_family_pair"]),
                "source_fault_pair": str(row["source_fault_pair"]),
                "margin_bucket": str(row["margin_bucket"]),
                "original_split_offset": int(row["original_split_offset"]),
                "original_offset_status": str(row["original_offset_status"]),
                "all_rows_both_positive": bool(row["all_rows_both_positive"]),
                "group_min_margin": float(row["group_min_margin"]),
            }
        )
    return rows


def _fold_composition_summary(rows: list[dict[str, Any]], *, fold_field: str) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for fold in sorted({int(row[fold_field]) for row in rows}):
        fold_rows = [row for row in rows if int(row[fold_field]) == fold]
        for dimension in ("source_family_pair", "source_fault_pair", "probe_template", "margin_bucket"):
            counts = Counter(str(row[dimension]) for row in fold_rows)
            total = sum(counts.values())
            for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
                summary_rows.append(
                    {
                        "fold": int(fold),
                        "dimension": dimension,
                        "value": value,
                        "group_count": int(count),
                        "group_share": float(count / total) if total else 0.0,
                        "unique_value_count_in_fold": int(len(counts)),
                    }
                )
    return summary_rows


def _max_fold_share(summary_rows: list[dict[str, Any]], dimension: str) -> float:
    values = [float(row["group_share"]) for row in summary_rows if str(row["dimension"]) == dimension]
    return max(values) if values else 0.0


def classify_refresh_plan(
    *,
    pair_disjoint: bool,
    all_folds_nonempty: bool,
    all_folds_have_both_probe_templates: bool,
    pair_specific_weight_used: bool,
    max_group_weight: float,
    max_weight: float,
) -> tuple[str, str]:
    if pair_specific_weight_used:
        return "source_history_concentration_refresh_plan_pair_specific_rejected", "repair weight builder"
    if not pair_disjoint or not all_folds_nonempty or not all_folds_have_both_probe_templates:
        return "source_history_concentration_refresh_plan_split_invalid", "repair fold assignment"
    if max_group_weight > max_weight + 1e-9:
        return "source_history_concentration_refresh_plan_weight_cap_violation", "repair weight cap"
    return "source_history_concentration_refresh_plan_admissible", "route to bounded weighted repeat design"


def run_concentration_refresh_plan(
    *,
    failed_offset_run_dir: Path,
    run_dir: Path,
    fold_count: int = 5,
    min_weight: float = 0.5,
    max_weight: float = 2.0,
) -> dict[str, Any]:
    failed_offset_run_dir = Path(failed_offset_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if int(fold_count) < 2:
        raise ValueError("fold_count must be at least 2")

    group_rows = _group_universe(failed_offset_run_dir)
    pair_features = _pair_features(group_rows)
    assignments = _assign_balanced_folds(pair_features, fold_count=int(fold_count))
    balanced_rows = _balanced_split_rows(group_rows, assignments)
    failed_shares = _failed_combo_shares(failed_offset_run_dir)
    weight_rows = _group_weights(
        group_rows,
        failed_combo_shares=failed_shares,
        min_weight=float(min_weight),
        max_weight=float(max_weight),
    )
    fold_summary = _fold_composition_summary(balanced_rows, fold_field="assigned_eval_fold")
    original_rows = [
        {
            **row,
            "original_fold": int(row["original_split_offset"]),
        }
        for row in group_rows
    ]
    original_summary = _fold_composition_summary(original_rows, fold_field="original_fold")

    pair_folds: dict[int, set[int]] = defaultdict(set)
    for row in balanced_rows:
        pair_folds[int(row["pair_id"])].add(int(row["assigned_eval_fold"]))
    pair_disjoint = all(len(folds) == 1 for folds in pair_folds.values())
    fold_ids = set(range(int(fold_count)))
    fold_pair_counts = Counter(int(fold) for fold in assignments.values())
    all_folds_nonempty = all(fold_pair_counts[fold] > 0 for fold in fold_ids)
    probe_values_by_fold: dict[int, set[str]] = defaultdict(set)
    for row in balanced_rows:
        probe_values_by_fold[int(row["assigned_eval_fold"])].add(str(row["probe_template"]))
    all_folds_have_both_probe_templates = all(len(probe_values_by_fold[fold]) >= 2 for fold in fold_ids)
    pair_specific_weight_used = any(_bool(row["pair_specific_weight_used"]) for row in weight_rows)
    max_group_weight = max(float(row["group_weight"]) for row in weight_rows) if weight_rows else 0.0
    min_group_weight = min(float(row["group_weight"]) for row in weight_rows) if weight_rows else 0.0
    result_class, recommended_next_step = classify_refresh_plan(
        pair_disjoint=pair_disjoint,
        all_folds_nonempty=all_folds_nonempty,
        all_folds_have_both_probe_templates=all_folds_have_both_probe_templates,
        pair_specific_weight_used=pair_specific_weight_used,
        max_group_weight=max_group_weight,
        max_weight=float(max_weight),
    )
    original_max_family = _max_fold_share(original_summary, "source_family_pair")
    balanced_max_family = _max_fold_share(fold_summary, "source_family_pair")
    original_max_probe = _max_fold_share(original_summary, "probe_template")
    balanced_max_probe = _max_fold_share(fold_summary, "probe_template")
    composition_improved = bool(
        balanced_max_family < original_max_family - 1e-9 or balanced_max_probe < original_max_probe - 1e-9
    )

    write_csv_rows(run_dir / "balanced_split_rows.csv", balanced_rows)
    write_csv_rows(run_dir / "group_weight_rows.csv", weight_rows)
    write_csv_rows(run_dir / "fold_composition_summary.csv", fold_summary)
    write_csv_rows(run_dir / "original_fold_composition_summary.csv", original_summary)

    family_value_counts = Counter(str(row["source_family_pair"]) for row in group_rows)
    summary = {
        "run_type": "source_history_concentration_refresh_plan",
        "failed_offset_run_dir": failed_offset_run_dir,
        "fold_count": int(fold_count),
        "group_count": int(len(group_rows)),
        "pair_count": int(len(pair_features)),
        "pair_disjoint": bool(pair_disjoint),
        "all_folds_nonempty": bool(all_folds_nonempty),
        "all_folds_have_both_probe_templates": bool(all_folds_have_both_probe_templates),
        "pair_specific_weight_used": bool(pair_specific_weight_used),
        "min_group_weight": float(min_group_weight),
        "max_group_weight": float(max_group_weight),
        "mean_group_weight": _mean([float(row["group_weight"]) for row in weight_rows]),
        "weight_cap": float(max_weight),
        "min_weight": float(min_weight),
        "original_max_source_family_pair_fold_share": float(original_max_family),
        "balanced_max_source_family_pair_fold_share": float(balanced_max_family),
        "original_max_probe_template_fold_share": float(original_max_probe),
        "balanced_max_probe_template_fold_share": float(balanced_max_probe),
        "composition_improved": bool(composition_improved),
        "source_family_pair_count": int(len(family_value_counts)),
        "dominant_source_family_pair": str(family_value_counts.most_common(1)[0][0]),
        "dominant_source_family_pair_share": float(
            family_value_counts.most_common(1)[0][1] / len(group_rows)
        ),
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
        "balanced_split_rows_csv": run_dir / "balanced_split_rows.csv",
        "group_weight_rows_csv": run_dir / "group_weight_rows.csv",
        "fold_composition_summary_csv": run_dir / "fold_composition_summary.csv",
        "original_fold_composition_summary_csv": run_dir / "original_fold_composition_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-history concentration refresh plan.")
    parser.add_argument("--failed-offset-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument("--min-weight", type=float, default=0.5)
    parser.add_argument("--max-weight", type=float, default=2.0)
    args = parser.parse_args()
    summary = run_concentration_refresh_plan(
        failed_offset_run_dir=args.failed_offset_run_dir,
        run_dir=args.run_dir,
        fold_count=args.fold_count,
        min_weight=args.min_weight,
        max_weight=args.max_weight,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
