"""No-training recalibration audit for public-base sequence objective artifacts."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json


ROUTE_TAIL_WEIGHTED = "public_base_tail_weighted_objective_design"
ROUTE_TARGET_REGEN = "public_base_target_regeneration_design"
ROUTE_RESIDUAL_FREE = "residual_free_public_base_sanity_design"
ROUTES = {ROUTE_TAIL_WEIGHTED, ROUTE_TARGET_REGEN, ROUTE_RESIDUAL_FREE}

LOW_TAIL_FIELDS = (
    "contrast_group_id",
    "source_index",
    "seed",
    "step",
    "preferred_fault_family",
    "wrong_fault_family",
    "fault_family_pair",
    "variant",
    "horizon",
    "source_pool",
    "claim_boundary_level",
    "normal_intervention_gap",
    "target_gap",
    "gap_deficit",
    "hard_negative_calibration_loss",
    "low_tail_reason",
)

GROUP_FIELDS = (
    "preferred_fault_family",
    "wrong_fault_family",
    "fault_family_pair",
    "variant",
    "horizon",
    "source_pool",
    "claim_boundary_level",
)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return float(np.mean(finite)) if finite else float("nan")


def _percentile(values: list[float], percentile: float) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return float(np.percentile(np.asarray(finite, dtype=np.float64), percentile)) if finite else float("nan")


def _alpha_key(value: Any) -> str:
    return f"{_as_float(value):.12g}"


def _row_by_alpha(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {_alpha_key(row.get("alpha")): row for row in rows}


def build_alpha_comparison(
    *,
    m909_rows: list[dict[str, str]],
    m761_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    m909_by_alpha = _row_by_alpha(m909_rows)
    m761_by_alpha = _row_by_alpha(m761_rows)
    alphas = sorted(set(m909_by_alpha) | set(m761_by_alpha), key=lambda item: _as_float(item))
    out: list[dict[str, Any]] = []
    for alpha in alphas:
        m909 = m909_by_alpha.get(alpha, {})
        m761 = m761_by_alpha.get(alpha, {})
        m909_p10 = _as_float(m909.get("normal_intervention_gap_p10"))
        m761_p10 = _as_float(m761.get("normal_intervention_gap_p10"))
        m909_deficit = _as_float(m909.get("gap_deficit_mean"))
        m761_deficit = _as_float(m761.get("gap_deficit_mean"))
        out.append(
            {
                "alpha": _as_float(alpha),
                "m761_retention_pass": _as_bool(m761.get("normal_retention_pass")),
                "m761_gap_lift_pass": _as_bool(m761.get("gap_lift_pass")),
                "m761_gap_p10": m761_p10,
                "m761_gap_deficit_mean": m761_deficit,
                "m761_first_action_drift_mean": _as_float(m761.get("first_action_drift_from_base_mean")),
                "m909_retention_pass": _as_bool(m909.get("normal_retention_pass")),
                "m909_gap_lift_pass": _as_bool(m909.get("gap_lift_pass")),
                "m909_gap_p10": m909_p10,
                "m909_gap_deficit_mean": m909_deficit,
                "m909_first_action_drift_mean": _as_float(m909.get("first_action_drift_from_base_mean")),
                "gap_p10_delta_m909_minus_m761": m909_p10 - m761_p10,
                "deficit_delta_m909_minus_m761": m909_deficit - m761_deficit,
            }
        )
    return out


def near_base_rows(rows: list[dict[str, str]], *, near_base_alpha: float) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if math.isclose(_as_float(row.get("alpha")), float(near_base_alpha), rel_tol=0.0, abs_tol=1e-9)
    ]


def low_tail_rows(
    rows: list[dict[str, str]],
    *,
    gap_p10_threshold: float,
    deficit_threshold: float,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        gap = _as_float(row.get("normal_intervention_gap"))
        deficit = _as_float(row.get("gap_deficit"))
        reasons: list[str] = []
        if gap < float(gap_p10_threshold):
            reasons.append("gap_below_threshold")
        if deficit > float(deficit_threshold):
            reasons.append("deficit_above_threshold")
        if not reasons:
            continue
        out.append(
            {
                **{key: row.get(key, "") for key in LOW_TAIL_FIELDS if key != "low_tail_reason"},
                "normal_intervention_gap": gap,
                "target_gap": _as_float(row.get("target_gap")),
                "gap_deficit": deficit,
                "hard_negative_calibration_loss": _as_float(row.get("hard_negative_calibration_loss")),
                "low_tail_reason": ";".join(reasons),
            }
        )
    return out


def group_deficit_summary(rows: list[dict[str, str]], low_tail: list[dict[str, Any]]) -> list[dict[str, Any]]:
    low_keys = {
        (
            str(row.get("contrast_group_id", "")),
            str(row.get("source_index", "")),
            str(row.get("variant", "")),
            str(row.get("horizon", "")),
        )
        for row in low_tail
    }
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in GROUP_FIELDS)
        groups.setdefault(key, []).append(row)
    out: list[dict[str, Any]] = []
    for key, group_rows in groups.items():
        gaps = [_as_float(row.get("normal_intervention_gap")) for row in group_rows]
        deficits = [_as_float(row.get("gap_deficit")) for row in group_rows]
        hard_losses = [_as_float(row.get("hard_negative_calibration_loss")) for row in group_rows]
        group_low_count = 0
        for row in group_rows:
            row_key = (
                str(row.get("contrast_group_id", "")),
                str(row.get("source_index", "")),
                str(row.get("variant", "")),
                str(row.get("horizon", "")),
            )
            if row_key in low_keys:
                group_low_count += 1
        total = len(group_rows)
        out.append(
            {
                **{field: value for field, value in zip(GROUP_FIELDS, key)},
                "rows": total,
                "low_tail_rows": group_low_count,
                "low_tail_fraction": float(group_low_count / total) if total else 0.0,
                "gap_mean": _mean(gaps),
                "gap_p10": _percentile(gaps, 10),
                "gap_deficit_mean": _mean(deficits),
                "hard_negative_calibration_loss_mean": _mean(hard_losses),
            }
        )
    return sorted(out, key=lambda row: (-int(row["low_tail_rows"]), str(row["fault_family_pair"]), str(row["variant"])))


def choose_route(
    *,
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    residual_free_gap_p10_threshold: float,
    residual_free_deficit_threshold: float,
    low_tail_count: int,
    distinct_fault_family_pairs: int,
    distinct_variants: int,
    distinct_source_pools: int,
) -> str:
    if (
        float(near_base_gap_p10) >= float(residual_free_gap_p10_threshold)
        and float(near_base_gap_deficit_mean) <= float(residual_free_deficit_threshold)
    ):
        return ROUTE_RESIDUAL_FREE
    if (
        int(low_tail_count) >= 100
        and int(distinct_fault_family_pairs) >= 3
        and int(distinct_variants) >= 1
        and int(distinct_source_pools) >= 1
    ):
        return ROUTE_TAIL_WEIGHTED
    return ROUTE_TARGET_REGEN


def run_public_base_sequence_recalibration_audit(
    *,
    m909_summary_path: Path,
    m909_alpha_metrics_path: Path,
    m909_objective_rows_path: Path,
    m761_summary_path: Path,
    m761_alpha_metrics_path: Path,
    run_dir: Path,
    near_base_alpha: float = 0.02,
    low_tail_gap_threshold: float = 0.021141,
    low_tail_deficit_threshold: float = 0.02,
    residual_free_deficit_threshold: float = 0.014809,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    m909_summary = read_json(m909_summary_path)
    m761_summary = read_json(m761_summary_path)
    m909_alpha_rows = read_csv_rows(m909_alpha_metrics_path)
    m761_alpha_rows = read_csv_rows(m761_alpha_metrics_path)
    objective_rows = read_csv_rows(m909_objective_rows_path)

    comparison_rows = build_alpha_comparison(m909_rows=m909_alpha_rows, m761_rows=m761_alpha_rows)
    near_rows = near_base_rows(objective_rows, near_base_alpha=float(near_base_alpha))
    low_rows = low_tail_rows(
        near_rows,
        gap_p10_threshold=float(low_tail_gap_threshold),
        deficit_threshold=float(low_tail_deficit_threshold),
    )
    group_rows = group_deficit_summary(near_rows, low_rows)

    near_gaps = [_as_float(row.get("normal_intervention_gap")) for row in near_rows]
    near_deficits = [_as_float(row.get("gap_deficit")) for row in near_rows]
    distinct_pairs = {str(row.get("fault_family_pair", "")) for row in low_rows if str(row.get("fault_family_pair", ""))}
    distinct_variants = {str(row.get("variant", "")) for row in low_rows if str(row.get("variant", ""))}
    distinct_source_pools = {str(row.get("source_pool", "")) for row in low_rows if str(row.get("source_pool", ""))}
    near_gap_p10 = _percentile(near_gaps, 10)
    near_deficit_mean = _mean(near_deficits)
    route = choose_route(
        near_base_gap_p10=near_gap_p10,
        near_base_gap_deficit_mean=near_deficit_mean,
        residual_free_gap_p10_threshold=float(low_tail_gap_threshold),
        residual_free_deficit_threshold=float(residual_free_deficit_threshold),
        low_tail_count=len(low_rows),
        distinct_fault_family_pairs=len(distinct_pairs),
        distinct_variants=len(distinct_variants),
        distinct_source_pools=len(distinct_source_pools),
    )

    summary = {
        "run_type": "public_base_sequence_recalibration_audit",
        "m909_summary": m909_summary_path,
        "m909_alpha_metrics": m909_alpha_metrics_path,
        "m909_objective_rows": m909_objective_rows_path,
        "m761_summary": m761_summary_path,
        "m761_alpha_metrics": m761_alpha_metrics_path,
        "near_base_alpha": float(near_base_alpha),
        "near_base_alpha_is_exact_zero": False,
        "near_base_rows": len(near_rows),
        "near_base_gap_p10": near_gap_p10,
        "near_base_gap_deficit_mean": near_deficit_mean,
        "low_tail_gap_threshold": float(low_tail_gap_threshold),
        "low_tail_deficit_threshold": float(low_tail_deficit_threshold),
        "residual_free_deficit_threshold": float(residual_free_deficit_threshold),
        "low_tail_rows": len(low_rows),
        "low_tail_fraction": float(len(low_rows) / max(len(near_rows), 1)),
        "distinct_fault_family_pairs": len(distinct_pairs),
        "distinct_variants": len(distinct_variants),
        "distinct_source_pools": len(distinct_source_pools),
        "m909_result_class": m909_summary.get("result_class"),
        "m909_candidate_alpha_count": int(m909_summary.get("candidate_alpha_count", 0)),
        "m761_result_class": m761_summary.get("result_class"),
        "route_decision": route,
        "training_started": False,
        "model_checkpoint_loaded": False,
        "m880_exact_used": False,
        "replay_used": False,
        "ppo_used": False,
        "promoted": False,
        "alpha_comparison_csv": run_dir / "alpha_comparison.csv",
        "low_tail_rows_csv": run_dir / "low_tail_rows.csv",
        "group_deficit_summary_csv": run_dir / "group_deficit_summary.csv",
    }
    write_csv_rows(run_dir / "alpha_comparison.csv", comparison_rows)
    write_csv_rows(run_dir / "low_tail_rows.csv", low_rows, fieldnames=list(LOW_TAIL_FIELDS))
    write_csv_rows(run_dir / "group_deficit_summary.csv", group_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training public-base sequence recalibration audit.")
    parser.add_argument("--m909-summary", type=Path, required=True)
    parser.add_argument("--m909-alpha-metrics", type=Path, required=True)
    parser.add_argument("--m909-objective-rows", type=Path, required=True)
    parser.add_argument("--m761-summary", type=Path, required=True)
    parser.add_argument("--m761-alpha-metrics", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--near-base-alpha", type=float, default=0.02)
    parser.add_argument("--low-tail-gap-threshold", type=float, default=0.021141)
    parser.add_argument("--low-tail-deficit-threshold", type=float, default=0.02)
    parser.add_argument("--residual-free-deficit-threshold", type=float, default=0.014809)
    args = parser.parse_args()
    summary = run_public_base_sequence_recalibration_audit(
        m909_summary_path=args.m909_summary,
        m909_alpha_metrics_path=args.m909_alpha_metrics,
        m909_objective_rows_path=args.m909_objective_rows,
        m761_summary_path=args.m761_summary,
        m761_alpha_metrics_path=args.m761_alpha_metrics,
        run_dir=args.run_dir,
        near_base_alpha=args.near_base_alpha,
        low_tail_gap_threshold=args.low_tail_gap_threshold,
        low_tail_deficit_threshold=args.low_tail_deficit_threshold,
        residual_free_deficit_threshold=args.residual_free_deficit_threshold,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
