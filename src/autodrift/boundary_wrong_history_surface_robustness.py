"""Robustness gate for the M115 boundary wrong-history surface."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


PHYSICAL_PAIR_COLUMNS = ("left_seed", "left_step", "right_seed", "right_step")


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0).astype(float) != 0.0
    return series.fillna("").astype(str).str.lower().isin({"1", "true", "yes", "y"})


def _finite_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def add_robustness_keys(frame: pd.DataFrame, *, margin_bucket_width: float) -> pd.DataFrame:
    if margin_bucket_width <= 0.0:
        raise ValueError("margin_bucket_width must be positive")
    missing = [column for column in PHYSICAL_PAIR_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"boundary rows missing physical pair columns: {missing}")
    next_frame = frame.copy()
    next_frame["physical_pair_key"] = next_frame.apply(
        lambda row: ":".join(str(int(row[column])) for column in PHYSICAL_PAIR_COLUMNS),
        axis=1,
    )
    normal_margin = _finite_float_series(next_frame["normal_margin"])
    bucket_start = np.floor(normal_margin / float(margin_bucket_width)) * float(margin_bucket_width)
    next_frame["normal_margin_bucket"] = bucket_start.map(
        lambda value: f"{value:.3f}-{value + float(margin_bucket_width):.3f}"
        if np.isfinite(value)
        else "nan"
    )
    return next_frame


def accepted_wrong_history_rows(frame: pd.DataFrame, *, margin_bucket_width: float) -> pd.DataFrame:
    required = {"variant", "accepted", "success_drop", "normal_margin", "margin_gap", *PHYSICAL_PAIR_COLUMNS}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"boundary rows missing columns: {missing}")
    keyed = add_robustness_keys(frame, margin_bucket_width=margin_bucket_width)
    return keyed[
        (keyed["variant"].astype(str) == "wrong_matched_history")
        & _bool_series(keyed["accepted"])
    ].copy()


def physical_pair_summary(accepted_wrong: pd.DataFrame) -> list[dict[str, Any]]:
    if accepted_wrong.empty:
        return []
    rows: list[dict[str, Any]] = []
    for key, group in accepted_wrong.groupby("physical_pair_key", observed=True):
        rows.append(
            {
                "physical_pair_key": str(key),
                "row_count": int(len(group)),
                "checkpoints": ",".join(sorted(group["checkpoint_label"].astype(str).unique()))
                if "checkpoint_label" in group
                else "",
                "targets": ",".join(sorted(group["target"].astype(str).unique())) if "target" in group else "",
                "left_seed": int(group["left_seed"].iloc[0]),
                "left_step": int(group["left_step"].iloc[0]),
                "right_seed": int(group["right_seed"].iloc[0]),
                "right_step": int(group["right_step"].iloc[0]),
                "normal_margin_mean": float(_finite_float_series(group["normal_margin"]).mean()),
                "margin_gap_mean": float(_finite_float_series(group["margin_gap"]).mean()),
                "success_drop_fraction": float(_bool_series(group["success_drop"]).mean()),
                "normal_margin_buckets": ",".join(sorted(group["normal_margin_bucket"].astype(str).unique())),
            }
        )
    return rows


def summarize_surface(
    frame: pd.DataFrame,
    *,
    margin_bucket_width: float,
    control_checkpoint_label: str,
) -> dict[str, Any]:
    keyed = add_robustness_keys(frame, margin_bucket_width=margin_bucket_width)
    accepted_wrong = accepted_wrong_history_rows(keyed, margin_bucket_width=margin_bucket_width)
    accepted_reset = keyed[(keyed["variant"].astype(str) == "reset_hidden") & _bool_series(keyed["accepted"])]
    accepted_zero_current = keyed[
        (keyed["variant"].astype(str) == "zero_current_response") & _bool_series(keyed["accepted"])
    ]
    wrong_rows = keyed[keyed["variant"].astype(str) == "wrong_matched_history"]

    accepted_count = int(len(accepted_wrong))
    physical_counts = (
        accepted_wrong.groupby("physical_pair_key", observed=True).size()
        if accepted_count
        else pd.Series(dtype=int)
    )
    max_rows_per_pair = int(physical_counts.max()) if len(physical_counts) else 0
    max_rows_fraction = float(max_rows_per_pair / accepted_count) if accepted_count else 0.0
    control_accepted = (
        accepted_wrong[accepted_wrong["checkpoint_label"].astype(str) == str(control_checkpoint_label)]
        if "checkpoint_label" in accepted_wrong
        else accepted_wrong.head(0)
    )
    checkpoint_count = (
        int(accepted_wrong["checkpoint_label"].astype(str).nunique())
        if accepted_count and "checkpoint_label" in accepted_wrong
        else 0
    )
    target_count = (
        int(accepted_wrong["target"].astype(str).nunique())
        if accepted_count and "target" in accepted_wrong
        else 0
    )
    bucket_count = int(accepted_wrong["normal_margin_bucket"].astype(str).nunique()) if accepted_count else 0
    return {
        "row_count": int(len(frame)),
        "wrong_history_row_count": int(len(wrong_rows)),
        "accepted_wrong_rows": accepted_count,
        "accepted_wrong_physical_pairs": int(accepted_wrong["physical_pair_key"].nunique()) if accepted_count else 0,
        "accepted_wrong_left_steps": int(accepted_wrong["left_step"].nunique()) if accepted_count else 0,
        "accepted_wrong_right_steps": int(accepted_wrong["right_step"].nunique()) if accepted_count else 0,
        "accepted_wrong_checkpoints": checkpoint_count,
        "accepted_wrong_targets": target_count,
        "accepted_wrong_normal_margin_buckets": bucket_count,
        "accepted_wrong_success_drop_fraction": float(_bool_series(accepted_wrong["success_drop"]).mean())
        if accepted_count
        else 0.0,
        "accepted_wrong_margin_gap_mean": float(_finite_float_series(accepted_wrong["margin_gap"]).mean())
        if accepted_count
        else float("nan"),
        "accepted_wrong_margin_gap_max": float(_finite_float_series(accepted_wrong["margin_gap"]).max())
        if accepted_count
        else float("nan"),
        "accepted_wrong_normal_margin_mean": float(_finite_float_series(accepted_wrong["normal_margin"]).mean())
        if accepted_count
        else float("nan"),
        "accepted_wrong_normal_margin_min": float(_finite_float_series(accepted_wrong["normal_margin"]).min())
        if accepted_count
        else float("nan"),
        "accepted_wrong_normal_margin_max": float(_finite_float_series(accepted_wrong["normal_margin"]).max())
        if accepted_count
        else float("nan"),
        "max_rows_per_physical_pair": max_rows_per_pair,
        "max_rows_per_physical_pair_fraction": max_rows_fraction,
        "control_checkpoint_label": str(control_checkpoint_label),
        "control_accepted_wrong_rows": int(len(control_accepted)),
        "accepted_reset_rows": int(len(accepted_reset)),
        "accepted_zero_current_rows": int(len(accepted_zero_current)),
        "wrong_to_reset_accepted_ratio": float(accepted_count / len(accepted_reset)) if len(accepted_reset) else float("nan"),
        "wrong_to_zero_current_accepted_ratio": float(accepted_count / len(accepted_zero_current))
        if len(accepted_zero_current)
        else float("nan"),
    }


def build_gate_rows(
    summary: dict[str, Any],
    *,
    min_accepted_wrong_rows: int,
    min_physical_pairs: int,
    min_left_steps: int,
    min_checkpoints: int,
    min_targets: int,
    min_margin_buckets: int,
    min_success_drop_fraction: float,
    max_rows_per_pair_fraction: float,
    max_control_accepted_rows: int,
) -> list[dict[str, Any]]:
    specs = [
        (
            "accepted_wrong_rows",
            summary["accepted_wrong_rows"],
            ">=",
            min_accepted_wrong_rows,
            "surface has enough accepted wrong-history rows",
        ),
        (
            "accepted_wrong_physical_pairs",
            summary["accepted_wrong_physical_pairs"],
            ">=",
            min_physical_pairs,
            "surface is not dominated by duplicate source pairs",
        ),
        (
            "accepted_wrong_left_steps",
            summary["accepted_wrong_left_steps"],
            ">=",
            min_left_steps,
            "surface covers enough distinct source decision steps",
        ),
        (
            "accepted_wrong_checkpoints",
            summary["accepted_wrong_checkpoints"],
            ">=",
            min_checkpoints,
            "surface appears on more than one non-control checkpoint",
        ),
        (
            "accepted_wrong_targets",
            summary["accepted_wrong_targets"],
            ">=",
            min_targets,
            "surface covers braking/lateral/yaw target groups",
        ),
        (
            "accepted_wrong_normal_margin_buckets",
            summary["accepted_wrong_normal_margin_buckets"],
            ">=",
            min_margin_buckets,
            "surface survives more than one boundary bucket",
        ),
        (
            "accepted_wrong_success_drop_fraction",
            summary["accepted_wrong_success_drop_fraction"],
            ">=",
            min_success_drop_fraction,
            "accepted rows are actual success drops",
        ),
        (
            "max_rows_per_physical_pair_fraction",
            summary["max_rows_per_physical_pair_fraction"],
            "<=",
            max_rows_per_pair_fraction,
            "no single physical pair dominates the accepted rows",
        ),
        (
            "control_accepted_wrong_rows",
            summary["control_accepted_wrong_rows"],
            "<=",
            max_control_accepted_rows,
            "control checkpoint remains unadmitted",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for name, observed, op, threshold, description in specs:
        observed_float = float(observed)
        threshold_float = float(threshold)
        if op == ">=":
            passed = observed_float >= threshold_float
        elif op == "<=":
            passed = observed_float <= threshold_float
        else:  # pragma: no cover - specs above are fixed.
            raise ValueError(f"unknown gate operator: {op}")
        rows.append(
            {
                "gate": name,
                "observed": observed,
                "op": op,
                "threshold": threshold,
                "passed": bool(passed),
                "description": description,
            }
        )
    return rows


def decision_from_gates(gate_rows: list[dict[str, Any]]) -> str:
    failed = [row["gate"] for row in gate_rows if not bool(row["passed"])]
    if not failed:
        return "admit_boundary_wrong_history_objective"
    if "accepted_wrong_physical_pairs" in failed or "accepted_wrong_left_steps" in failed:
        return "reject_duplicate_dominated_boundary_surface"
    if "accepted_wrong_normal_margin_buckets" in failed:
        return "reject_boundary_bucket_tuned_surface"
    return "reject_boundary_wrong_history_surface"


def run_boundary_wrong_history_surface_robustness(
    *,
    boundary_rows_csv: Path,
    control_checkpoint_label: str,
    margin_bucket_width: float,
    min_accepted_wrong_rows: int,
    min_physical_pairs: int,
    min_left_steps: int,
    min_checkpoints: int,
    min_targets: int,
    min_margin_buckets: int,
    min_success_drop_fraction: float,
    max_rows_per_pair_fraction: float,
    max_control_accepted_rows: int,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(boundary_rows_csv)
    accepted_wrong = accepted_wrong_history_rows(frame, margin_bucket_width=margin_bucket_width)
    summary = summarize_surface(
        frame,
        margin_bucket_width=margin_bucket_width,
        control_checkpoint_label=control_checkpoint_label,
    )
    gates = build_gate_rows(
        summary,
        min_accepted_wrong_rows=min_accepted_wrong_rows,
        min_physical_pairs=min_physical_pairs,
        min_left_steps=min_left_steps,
        min_checkpoints=min_checkpoints,
        min_targets=min_targets,
        min_margin_buckets=min_margin_buckets,
        min_success_drop_fraction=min_success_drop_fraction,
        max_rows_per_pair_fraction=max_rows_per_pair_fraction,
        max_control_accepted_rows=max_control_accepted_rows,
    )
    pair_summary_rows = physical_pair_summary(accepted_wrong)
    decision = decision_from_gates(gates)
    write_csv_rows(run_dir / "accepted_wrong_history_rows.csv", accepted_wrong.to_dict("records"))
    write_csv_rows(run_dir / "physical_pair_summary.csv", pair_summary_rows)
    write_csv_rows(run_dir / "robustness_gates.csv", gates)
    write_json(
        run_dir / "summary.json",
        {
            "run_type": "boundary_wrong_history_surface_robustness",
            "boundary_rows_csv": boundary_rows_csv,
            "control_checkpoint_label": control_checkpoint_label,
            "margin_bucket_width": float(margin_bucket_width),
            "thresholds": {
                "min_accepted_wrong_rows": int(min_accepted_wrong_rows),
                "min_physical_pairs": int(min_physical_pairs),
                "min_left_steps": int(min_left_steps),
                "min_checkpoints": int(min_checkpoints),
                "min_targets": int(min_targets),
                "min_margin_buckets": int(min_margin_buckets),
                "min_success_drop_fraction": float(min_success_drop_fraction),
                "max_rows_per_pair_fraction": float(max_rows_per_pair_fraction),
                "max_control_accepted_rows": int(max_control_accepted_rows),
            },
            "metrics": summary,
            "decision": decision,
            "passed": bool(decision == "admit_boundary_wrong_history_objective"),
            "accepted_wrong_history_rows_csv": run_dir / "accepted_wrong_history_rows.csv",
            "physical_pair_summary_csv": run_dir / "physical_pair_summary.csv",
            "robustness_gates_csv": run_dir / "robustness_gates.csv",
        },
    )
    return {
        "run_type": "boundary_wrong_history_surface_robustness",
        "boundary_rows_csv": boundary_rows_csv,
        "decision": decision,
        "passed": bool(decision == "admit_boundary_wrong_history_objective"),
        **summary,
        "robustness_gates_csv": run_dir / "robustness_gates.csv",
        "physical_pair_summary_csv": run_dir / "physical_pair_summary.csv",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate robustness of the M115 boundary wrong-history surface.")
    parser.add_argument("--boundary-rows-csv", type=Path, required=True)
    parser.add_argument("--control-checkpoint-label", type=str, default="m62")
    parser.add_argument("--margin-bucket-width", type=float, default=0.01)
    parser.add_argument("--min-accepted-wrong-rows", type=int, default=10)
    parser.add_argument("--min-physical-pairs", type=int, default=6)
    parser.add_argument("--min-left-steps", type=int, default=5)
    parser.add_argument("--min-checkpoints", type=int, default=2)
    parser.add_argument("--min-targets", type=int, default=3)
    parser.add_argument("--min-margin-buckets", type=int, default=2)
    parser.add_argument("--min-success-drop-fraction", type=float, default=1.0)
    parser.add_argument("--max-rows-per-pair-fraction", type=float, default=0.40)
    parser.add_argument("--max-control-accepted-rows", type=int, default=0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_wrong_history_surface_robustness")
    result = run_boundary_wrong_history_surface_robustness(
        boundary_rows_csv=args.boundary_rows_csv,
        control_checkpoint_label=args.control_checkpoint_label,
        margin_bucket_width=args.margin_bucket_width,
        min_accepted_wrong_rows=args.min_accepted_wrong_rows,
        min_physical_pairs=args.min_physical_pairs,
        min_left_steps=args.min_left_steps,
        min_checkpoints=args.min_checkpoints,
        min_targets=args.min_targets,
        min_margin_buckets=args.min_margin_buckets,
        min_success_drop_fraction=args.min_success_drop_fraction,
        max_rows_per_pair_fraction=args.max_rows_per_pair_fraction,
        max_control_accepted_rows=args.max_control_accepted_rows,
        run_dir=run_dir,
    )
    print(pd.Series(result).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
