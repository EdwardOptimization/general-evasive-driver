"""No-training audit for weighted source-history repeat tradeoffs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _offset_pass(row: dict[str, Any]) -> bool:
    return bool(
        not _bool(row.get("forbidden_parameter_mutation_detected", False))
        and _finite_float(row.get("eval_group_all_rows_both_positive_fraction", 0.0)) >= 0.25
        and _finite_float(row.get("eval_both_directional_fraction", 0.0)) >= 0.25
        and int(float(row.get("full_group_all_rows_both_positive_count", 0))) > 15
        and int(float(row.get("full_both_positive_count", 0))) > 30
    )


def _offset_rows_by_offset(run_dir: Path, scope: str) -> dict[int, dict[str, str]]:
    rows = _read_csv(run_dir / "scope_summaries.csv")
    by_offset: dict[int, dict[str, str]] = {}
    for row in rows:
        if str(row.get("scope", scope)) != scope:
            continue
        by_offset[int(float(row["split_offset"]))] = row
    if not by_offset:
        raise ValueError(f"no scope_summaries rows for scope={scope} in {run_dir}")
    return by_offset


def _weight_meta_by_group(plan_run_dir: Path) -> dict[tuple[int, str], dict[str, Any]]:
    rows = _read_csv(plan_run_dir / "group_weight_rows.csv")
    meta: dict[tuple[int, str], dict[str, Any]] = {}
    for row in rows:
        key = (int(float(row["pair_id"])), str(row["probe_template"]))
        meta[key] = {
            "source_family_pair": str(row.get("source_family_pair", "")),
            "source_fault_pair": str(row.get("source_fault_pair", "")),
            "margin_bucket": str(row.get("margin_bucket", "")),
            "group_weight": _finite_float(row.get("group_weight", 1.0)),
            "failed_combo_boost": _finite_float(row.get("failed_combo_boost", 0.0)),
            "pair_specific_weight_used": _bool(row.get("pair_specific_weight_used", False)),
        }
    if not meta:
        raise ValueError(f"group weights are empty in {plan_run_dir}")
    return meta


def _full_group_rows_by_key(run_dir: Path, scope: str) -> dict[tuple[int, int, str], dict[str, str]]:
    rows = _read_csv(run_dir / "group_rows.csv")
    by_key: dict[tuple[int, int, str], dict[str, str]] = {}
    for row in rows:
        if str(row.get("scope", scope)) != scope:
            continue
        if str(row.get("split", "")) != "full":
            continue
        key = (int(float(row["split_offset"])), int(float(row["pair_id"])), str(row["probe_template"]))
        by_key[key] = row
    if not by_key:
        raise ValueError(f"no full group rows for scope={scope} in {run_dir}")
    return by_key


def _offset_comparison_rows(
    baseline_by_offset: dict[int, dict[str, str]],
    weighted_by_offset: dict[int, dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset in sorted(set(baseline_by_offset) & set(weighted_by_offset)):
        baseline = baseline_by_offset[offset]
        weighted = weighted_by_offset[offset]
        baseline_pass = _offset_pass(baseline)
        weighted_pass = _offset_pass(weighted)
        eval_delta = _finite_float(weighted["eval_both_directional_fraction"]) - _finite_float(
            baseline["eval_both_directional_fraction"]
        )
        eval_group_delta = _finite_float(weighted["eval_group_all_rows_both_positive_fraction"]) - _finite_float(
            baseline["eval_group_all_rows_both_positive_fraction"]
        )
        full_row_delta = int(float(weighted["full_both_positive_count"])) - int(
            float(baseline["full_both_positive_count"])
        )
        full_group_delta = int(float(weighted["full_group_all_rows_both_positive_count"])) - int(
            float(baseline["full_group_all_rows_both_positive_count"])
        )
        if weighted_pass and not baseline_pass:
            status = "new_pass"
        elif baseline_pass and not weighted_pass:
            status = "lost_pass"
        elif eval_delta > 0.0 and eval_group_delta > 0.0 and full_row_delta >= 0 and full_group_delta >= 0:
            status = "improved"
        elif eval_delta < 0.0 and eval_group_delta < 0.0 and full_row_delta <= 0 and full_group_delta <= 0:
            status = "regressed"
        else:
            status = "mixed"
        rows.append(
            {
                "split_offset": offset,
                "baseline_pass": baseline_pass,
                "weighted_pass": weighted_pass,
                "offset_status": status,
                "baseline_eval_both_directional_fraction": _finite_float(
                    baseline["eval_both_directional_fraction"]
                ),
                "weighted_eval_both_directional_fraction": _finite_float(
                    weighted["eval_both_directional_fraction"]
                ),
                "eval_both_directional_fraction_delta": eval_delta,
                "baseline_eval_group_all_rows_both_positive_fraction": _finite_float(
                    baseline["eval_group_all_rows_both_positive_fraction"]
                ),
                "weighted_eval_group_all_rows_both_positive_fraction": _finite_float(
                    weighted["eval_group_all_rows_both_positive_fraction"]
                ),
                "eval_group_all_rows_both_positive_fraction_delta": eval_group_delta,
                "baseline_full_both_positive_count": int(float(baseline["full_both_positive_count"])),
                "weighted_full_both_positive_count": int(float(weighted["full_both_positive_count"])),
                "full_both_positive_count_delta": full_row_delta,
                "baseline_full_group_all_rows_both_positive_count": int(
                    float(baseline["full_group_all_rows_both_positive_count"])
                ),
                "weighted_full_group_all_rows_both_positive_count": int(
                    float(weighted["full_group_all_rows_both_positive_count"])
                ),
                "full_group_all_rows_both_positive_count_delta": full_group_delta,
            }
        )
    return rows


def _group_comparison_rows(
    baseline_rows: dict[tuple[int, int, str], dict[str, str]],
    weighted_rows: dict[tuple[int, int, str], dict[str, str]],
    meta_by_group: dict[tuple[int, str], dict[str, Any]],
    *,
    top_failed_source_family_pair: str,
    top_failed_probe_template: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(set(baseline_rows) & set(weighted_rows)):
        split_offset, pair_id, probe_template = key
        baseline = baseline_rows[key]
        weighted = weighted_rows[key]
        meta = meta_by_group.get((pair_id, probe_template), {})
        baseline_positive = _bool(baseline.get("all_rows_both_positive", False))
        weighted_positive = _bool(weighted.get("all_rows_both_positive", False))
        baseline_margin = _finite_float(baseline["group_min_margin"])
        weighted_margin = _finite_float(weighted["group_min_margin"])
        margin_delta = weighted_margin - baseline_margin
        if weighted_positive and not baseline_positive:
            status = "improved_to_positive"
        elif baseline_positive and not weighted_positive:
            status = "regressed_from_positive"
        elif margin_delta > 0.0:
            status = "margin_improved"
        elif margin_delta < 0.0:
            status = "margin_regressed"
        else:
            status = "unchanged"
        source_family_pair = str(meta.get("source_family_pair", ""))
        rows.append(
            {
                "split_offset": split_offset,
                "pair_id": pair_id,
                "probe_template": probe_template,
                "source_family_pair": source_family_pair,
                "source_fault_pair": str(meta.get("source_fault_pair", "")),
                "margin_bucket": str(meta.get("margin_bucket", "")),
                "group_weight": _finite_float(meta.get("group_weight", 1.0)),
                "failed_combo_boost": _finite_float(meta.get("failed_combo_boost", 0.0)),
                "top_failed_source_family_match": source_family_pair == top_failed_source_family_pair,
                "top_failed_probe_match": probe_template == top_failed_probe_template,
                "top_failed_combo_match": source_family_pair == top_failed_source_family_pair
                and probe_template == top_failed_probe_template,
                "baseline_all_rows_both_positive": baseline_positive,
                "weighted_all_rows_both_positive": weighted_positive,
                "baseline_group_min_margin": baseline_margin,
                "weighted_group_min_margin": weighted_margin,
                "group_min_margin_delta": margin_delta,
                "status": status,
            }
        )
    return rows


def _summarize_group_subset(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    baseline_positive = [row for row in rows if _bool(row["baseline_all_rows_both_positive"])]
    weighted_positive = [row for row in rows if _bool(row["weighted_all_rows_both_positive"])]
    improved = [row for row in rows if str(row["status"]) == "improved_to_positive"]
    regressed = [row for row in rows if str(row["status"]) == "regressed_from_positive"]
    return {
        f"{prefix}_group_count": len(rows),
        f"{prefix}_baseline_positive_count": len(baseline_positive),
        f"{prefix}_weighted_positive_count": len(weighted_positive),
        f"{prefix}_improved_to_positive_count": len(improved),
        f"{prefix}_regressed_from_positive_count": len(regressed),
        f"{prefix}_mean_margin_delta": _mean([_finite_float(row["group_min_margin_delta"]) for row in rows]),
        f"{prefix}_mean_group_weight": _mean([_finite_float(row["group_weight"]) for row in rows]),
    }


def _source_probe_summary_rows(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in group_rows:
        grouped[(str(row["source_family_pair"]), str(row["probe_template"]))].append(row)
    rows: list[dict[str, Any]] = []
    for (source_family_pair, probe_template), values in sorted(grouped.items()):
        summary = _summarize_group_subset(values, "combo")
        rows.append(
            {
                "source_family_pair": source_family_pair,
                "probe_template": probe_template,
                **summary,
            }
        )
    return rows


def _weight_gain_summary_rows(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in group_rows:
        grouped[str(row["status"])].append(row)
    rows: list[dict[str, Any]] = []
    for status, values in sorted(grouped.items()):
        rows.append(
            {
                "status": status,
                "count": len(values),
                "mean_group_weight": _mean([_finite_float(row["group_weight"]) for row in values]),
                "mean_margin_delta": _mean([_finite_float(row["group_min_margin_delta"]) for row in values]),
                "top_failed_combo_count": sum(1 for row in values if _bool(row["top_failed_combo_match"])),
            }
        )
    return rows


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    mean_x = _mean(xs)
    mean_y = _mean(ys)
    dx = [value - mean_x for value in xs]
    dy = [value - mean_y for value in ys]
    var_x = sum(value * value for value in dx)
    var_y = sum(value * value for value in dy)
    if var_x <= 0.0 or var_y <= 0.0:
        return 0.0
    return float(sum(a * b for a, b in zip(dx, dy, strict=True)) / ((var_x * var_y) ** 0.5))


def _result_class(
    *,
    baseline_pass_count: int,
    weighted_pass_count: int,
    best_eval_delta: float,
    top_combo_positive_delta: int,
    improved_group_count: int,
    regressed_group_count: int,
) -> str:
    if weighted_pass_count < baseline_pass_count and best_eval_delta > 0.0 and top_combo_positive_delta > 0:
        return "weighted_repeat_top_combo_partial_improvement_global_regression"
    if weighted_pass_count < baseline_pass_count and best_eval_delta > 0.0:
        return "weighted_repeat_single_fold_improvement_global_regression"
    if weighted_pass_count < baseline_pass_count:
        return "weighted_repeat_global_regression"
    if weighted_pass_count >= baseline_pass_count and improved_group_count > regressed_group_count:
        return "weighted_repeat_tradeoff_nonregressive"
    return "weighted_repeat_mixed_tradeoff"


def run_tradeoff_audit(
    *,
    weighted_run_dir: Path,
    baseline_run_dir: Path,
    failed_offset_run_dir: Path,
    plan_run_dir: Path,
    run_dir: Path,
    scope: str = "fusion_head",
) -> dict[str, Any]:
    weighted_run_dir = Path(weighted_run_dir)
    baseline_run_dir = Path(baseline_run_dir)
    failed_offset_run_dir = Path(failed_offset_run_dir)
    plan_run_dir = Path(plan_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    baseline_summary = _read_json(baseline_run_dir / "summary.json")
    weighted_summary = _read_json(weighted_run_dir / "summary.json")
    failed_summary = _read_json(failed_offset_run_dir / "summary.json")
    plan_summary = _read_json(plan_run_dir / "summary.json")

    baseline_offsets = _offset_rows_by_offset(baseline_run_dir, scope)
    weighted_offsets = _offset_rows_by_offset(weighted_run_dir, scope)
    offset_rows = _offset_comparison_rows(baseline_offsets, weighted_offsets)

    meta_by_group = _weight_meta_by_group(plan_run_dir)
    pair_specific_weight_used = bool(
        any(_bool(meta.get("pair_specific_weight_used", False)) for meta in meta_by_group.values())
    )
    top_source_family = str(failed_summary.get("top_failed_source_family_pair", ""))
    top_probe = str(failed_summary.get("top_failed_probe_template", ""))
    group_rows = _group_comparison_rows(
        _full_group_rows_by_key(baseline_run_dir, scope),
        _full_group_rows_by_key(weighted_run_dir, scope),
        meta_by_group,
        top_failed_source_family_pair=top_source_family,
        top_failed_probe_template=top_probe,
    )
    source_probe_rows = _source_probe_summary_rows(group_rows)
    weight_gain_rows = _weight_gain_summary_rows(group_rows)
    top_combo_rows = [row for row in group_rows if _bool(row["top_failed_combo_match"])]

    baseline_pass_count = sum(1 for row in offset_rows if _bool(row["baseline_pass"]))
    weighted_pass_count = sum(1 for row in offset_rows if _bool(row["weighted_pass"]))
    lost_pass_offsets = [str(row["split_offset"]) for row in offset_rows if str(row["offset_status"]) == "lost_pass"]
    new_pass_offsets = [str(row["split_offset"]) for row in offset_rows if str(row["offset_status"]) == "new_pass"]
    improved_offsets = [
        str(row["split_offset"])
        for row in offset_rows
        if _finite_float(row["eval_both_directional_fraction_delta"]) > 0.0
    ]
    regressed_offsets = [
        str(row["split_offset"])
        for row in offset_rows
        if _finite_float(row["eval_both_directional_fraction_delta"]) < 0.0
    ]
    best_offset_row = max(offset_rows, key=lambda row: _finite_float(row["weighted_eval_both_directional_fraction"]))

    all_group_summary = _summarize_group_subset(group_rows, "full")
    top_combo_summary = _summarize_group_subset(top_combo_rows, "top_failed_combo")
    top_combo_positive_delta = int(
        top_combo_summary["top_failed_combo_weighted_positive_count"]
        - top_combo_summary["top_failed_combo_baseline_positive_count"]
    )
    improved_group_count = int(all_group_summary["full_improved_to_positive_count"])
    regressed_group_count = int(all_group_summary["full_regressed_from_positive_count"])

    result_class = _result_class(
        baseline_pass_count=baseline_pass_count,
        weighted_pass_count=weighted_pass_count,
        best_eval_delta=_finite_float(best_offset_row["eval_both_directional_fraction_delta"]),
        top_combo_positive_delta=top_combo_positive_delta,
        improved_group_count=improved_group_count,
        regressed_group_count=regressed_group_count,
    )
    recommended_next_step = (
        "route to robust min-fold or lexicographic objective design before PPO"
        if weighted_pass_count < baseline_pass_count
        else "route to result audit before any PPO or promotion"
    )

    weights = [_finite_float(row["group_weight"]) for row in group_rows]
    deltas = [_finite_float(row["group_min_margin_delta"]) for row in group_rows]
    summary: dict[str, Any] = {
        "run_type": "source_history_weighted_repeat_tradeoff_audit",
        "result_class": result_class,
        "weighted_run_dir": str(weighted_run_dir),
        "baseline_run_dir": str(baseline_run_dir),
        "failed_offset_run_dir": str(failed_offset_run_dir),
        "plan_run_dir": str(plan_run_dir),
        "scope": scope,
        "offset_count": len(offset_rows),
        "baseline_repeat_offset_pass_count": baseline_pass_count,
        "weighted_repeat_offset_pass_count": weighted_pass_count,
        "offset_pass_count_delta": weighted_pass_count - baseline_pass_count,
        "new_pass_offsets": "|".join(new_pass_offsets),
        "lost_pass_offsets": "|".join(lost_pass_offsets),
        "eval_improved_offsets": "|".join(improved_offsets),
        "eval_regressed_offsets": "|".join(regressed_offsets),
        "best_weighted_offset": int(best_offset_row["split_offset"]),
        "best_weighted_eval_both_directional_fraction": _finite_float(
            best_offset_row["weighted_eval_both_directional_fraction"]
        ),
        "best_weighted_eval_delta": _finite_float(best_offset_row["eval_both_directional_fraction_delta"]),
        "m1302_mean_eval_both_directional_fraction": _finite_float(
            baseline_summary.get("best_repeat_mean_eval_both_directional_fraction", 0.0)
        ),
        "m1309_mean_eval_both_directional_fraction": _finite_float(
            weighted_summary.get("best_repeat_mean_eval_both_directional_fraction", 0.0)
        ),
        "mean_eval_both_directional_fraction_delta": _finite_float(
            weighted_summary.get("best_repeat_mean_eval_both_directional_fraction", 0.0)
        )
        - _finite_float(baseline_summary.get("best_repeat_mean_eval_both_directional_fraction", 0.0)),
        "m1302_mean_full_both_positive_count": _finite_float(
            baseline_summary.get("best_repeat_mean_full_both_positive_count", 0.0)
        ),
        "m1309_mean_full_both_positive_count": _finite_float(
            weighted_summary.get("best_repeat_mean_full_both_positive_count", 0.0)
        ),
        "mean_full_both_positive_count_delta": _finite_float(
            weighted_summary.get("best_repeat_mean_full_both_positive_count", 0.0)
        )
        - _finite_float(baseline_summary.get("best_repeat_mean_full_both_positive_count", 0.0)),
        "top_failed_source_family_pair": top_source_family,
        "top_failed_probe_template": top_probe,
        "top_failed_combo_positive_delta": top_combo_positive_delta,
        "top_failed_combo_partial_improvement": top_combo_positive_delta > 0,
        "group_weight_margin_delta_correlation": _pearson(weights, deltas),
        "pair_specific_weight_used": pair_specific_weight_used,
        "max_group_weight": _finite_float(plan_summary.get("max_group_weight", 0.0)),
        "training_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "recommended_next_step": recommended_next_step,
        "offset_comparison_csv": str(run_dir / "offset_comparison.csv"),
        "full_group_comparison_csv": str(run_dir / "full_group_comparison.csv"),
        "source_probe_summary_csv": str(run_dir / "source_probe_summary.csv"),
        "weight_gain_summary_csv": str(run_dir / "weight_gain_summary.csv"),
    }
    summary.update(all_group_summary)
    summary.update(top_combo_summary)

    write_csv_rows(run_dir / "offset_comparison.csv", offset_rows)
    write_csv_rows(run_dir / "full_group_comparison.csv", group_rows)
    write_csv_rows(run_dir / "source_probe_summary.csv", source_probe_rows)
    write_csv_rows(run_dir / "weight_gain_summary.csv", weight_gain_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weighted-run-dir", type=Path, required=True)
    parser.add_argument("--baseline-run-dir", type=Path, required=True)
    parser.add_argument("--failed-offset-run-dir", type=Path, required=True)
    parser.add_argument("--plan-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--scope", type=str, default="fusion_head")
    args = parser.parse_args()
    summary = run_tradeoff_audit(
        weighted_run_dir=args.weighted_run_dir,
        baseline_run_dir=args.baseline_run_dir,
        failed_offset_run_dir=args.failed_offset_run_dir,
        plan_run_dir=args.plan_run_dir,
        run_dir=args.run_dir,
        scope=args.scope,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
