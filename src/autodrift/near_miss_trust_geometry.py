"""Analyze near-miss sequence candidates against trust-region constraints."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


METADATA_COLUMNS = [
    "source_index",
    "source_tier",
    "expansion_reason",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
]


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if pd.isna(value):
        return False
    return bool(value)


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if np.isfinite(output) else default


def _near_miss_mask(
    rows: pd.DataFrame,
    *,
    min_margin_improvement: float,
    min_risk_improvement: float,
) -> pd.Series:
    accepted = rows["accepted"].map(_bool) if "accepted" in rows.columns else pd.Series(False, index=rows.index)
    margin = rows["margin_improvement"].astype(float) if "margin_improvement" in rows.columns else pd.Series(float("nan"), index=rows.index)
    risk = rows["risk_improvement"].astype(float) if "risk_improvement" in rows.columns else pd.Series(float("nan"), index=rows.index)
    utility = (margin >= float(min_margin_improvement)) | (risk >= float(min_risk_improvement))
    return (~accepted) & utility


def classify_candidate(
    row: pd.Series | dict[str, Any],
    *,
    mean_l2_limit: float,
    max_l2_limit: float,
    delta_delta_l2_limit: float,
) -> dict[str, Any]:
    mean_l2 = _float(row.get("sequence_mean_l2"))
    max_l2 = _float(row.get("sequence_max_l2"))
    delta_delta = _float(row.get("max_delta_delta_l2"))
    mean_excess = max(0.0, mean_l2 - float(mean_l2_limit)) if np.isfinite(mean_l2) else float("nan")
    max_excess = max(0.0, max_l2 - float(max_l2_limit)) if np.isfinite(max_l2) else float("nan")
    delta_delta_excess = (
        max(0.0, delta_delta - float(delta_delta_l2_limit)) if np.isfinite(delta_delta) else float("nan")
    )
    fails_mean = bool(np.isfinite(mean_excess) and mean_excess > 1e-9)
    fails_max = bool(np.isfinite(max_excess) and max_excess > 1e-9)
    fails_delta_delta = bool(np.isfinite(delta_delta_excess) and delta_delta_excess > 1e-9)
    collision = _bool(row.get("candidate_collision", False))
    off_road = _bool(row.get("candidate_off_road", False))
    spin_out = _bool(row.get("candidate_spin_out", False))
    if collision:
        primary = "candidate_collision"
    elif off_road:
        primary = "candidate_off_road"
    elif spin_out:
        primary = "candidate_spin_out"
    elif fails_mean:
        primary = "mean_l2_excess"
    elif fails_max:
        primary = "max_l2_excess"
    elif fails_delta_delta:
        primary = "delta_delta_excess"
    else:
        primary = "other"
    return {
        "mean_l2_excess": mean_excess,
        "max_l2_excess": max_excess,
        "delta_delta_excess": delta_delta_excess,
        "fails_mean_l2": fails_mean,
        "fails_max_l2": fails_max,
        "fails_delta_delta_l2": fails_delta_delta,
        "candidate_collision": collision,
        "candidate_off_road": off_road,
        "candidate_spin_out": spin_out,
        "has_trust_failure": bool(fails_mean or fails_max or fails_delta_delta),
        "has_safety_failure": bool(collision or off_road or spin_out),
        "primary_failure": primary,
    }


def near_miss_candidates(
    rows: pd.DataFrame,
    *,
    mean_l2_limit: float,
    max_l2_limit: float,
    delta_delta_l2_limit: float,
    min_margin_improvement: float,
    min_risk_improvement: float,
) -> pd.DataFrame:
    required = {
        "source_index",
        "accepted",
        "margin_improvement",
        "risk_improvement",
        "sequence_mean_l2",
        "sequence_max_l2",
        "max_delta_delta_l2",
    }
    missing = sorted(required.difference(rows.columns))
    if missing:
        raise ValueError("sequence candidates missing columns: " + ", ".join(missing))
    frame = rows[_near_miss_mask(rows, min_margin_improvement=min_margin_improvement, min_risk_improvement=min_risk_improvement)].copy()
    if frame.empty:
        for column in [
            "mean_l2_excess",
            "max_l2_excess",
            "delta_delta_excess",
            "fails_mean_l2",
            "fails_max_l2",
            "fails_delta_delta_l2",
            "candidate_collision",
            "candidate_off_road",
            "candidate_spin_out",
            "has_trust_failure",
            "has_safety_failure",
            "primary_failure",
        ]:
            frame[column] = []
        return frame
    classifications = pd.DataFrame(
        [
            classify_candidate(
                row,
                mean_l2_limit=mean_l2_limit,
                max_l2_limit=max_l2_limit,
                delta_delta_l2_limit=delta_delta_l2_limit,
            )
            for _, row in frame.iterrows()
        ]
    )
    frame = frame.reset_index(drop=True)
    for column in classifications.columns:
        frame[column] = classifications[column]
    return frame


def source_summary(all_candidates: pd.DataFrame, near_misses: pd.DataFrame) -> pd.DataFrame:
    if near_misses.empty:
        return pd.DataFrame()
    all_counts = all_candidates.groupby("source_index", observed=True).size().rename("candidate_count")
    accepted_counts = (
        all_candidates[all_candidates["accepted"].map(_bool)]
        .groupby("source_index", observed=True)
        .size()
        .rename("accepted_candidate_count")
    )
    rows: list[dict[str, Any]] = []
    for source_index, group in near_misses.groupby("source_index", observed=True):
        ranked = group.sort_values(["margin_improvement", "risk_improvement"], ascending=[False, False])
        best = ranked.iloc[0]
        item = {column: best[column] for column in METADATA_COLUMNS if column in best.index}
        item.update(
            {
                "candidate_count": int(all_counts.get(source_index, 0)),
                "accepted_candidate_count": int(accepted_counts.get(source_index, 0)),
                "near_miss_count": int(len(group)),
                "best_candidate_id": int(best["candidate_id"]) if "candidate_id" in best.index else -1,
                "best_family": str(best.get("family", "")),
                "best_sequence_length": int(best["sequence_length"]) if "sequence_length" in best.index else -1,
                "best_margin_improvement": _float(best.get("margin_improvement")),
                "best_risk_improvement": _float(best.get("risk_improvement")),
                "best_primary_failure": str(best.get("primary_failure", "")),
                "min_mean_l2_excess": _float(group["mean_l2_excess"].min()),
                "min_max_l2_excess": _float(group["max_l2_excess"].min()),
                "min_delta_delta_excess": _float(group["delta_delta_excess"].min()),
                "has_collision_near_miss": bool(group["candidate_collision"].map(_bool).any()),
                "has_trust_near_miss": bool(group["has_trust_failure"].map(_bool).any()),
                "has_safety_near_miss": bool(group["has_safety_failure"].map(_bool).any()),
            }
        )
        rows.append(item)
    return pd.DataFrame(rows).sort_values(["best_margin_improvement", "near_miss_count"], ascending=[False, False])


def _counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].value_counts().to_dict().items()}


def _median(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return float("nan")
    return _float(frame[column].median())


def run_near_miss_trust_geometry(
    *,
    sequence_candidates_csv: Path,
    unaccepted_rows_csv: Path,
    mean_l2_limit: float,
    max_l2_limit: float,
    delta_delta_l2_limit: float,
    min_margin_improvement: float,
    min_risk_improvement: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidates = pd.read_csv(sequence_candidates_csv)
    # Read for provenance and to fail early if the expected source-level artifact is missing.
    pd.read_csv(unaccepted_rows_csv)
    near_misses = near_miss_candidates(
        candidates,
        mean_l2_limit=mean_l2_limit,
        max_l2_limit=max_l2_limit,
        delta_delta_l2_limit=delta_delta_l2_limit,
        min_margin_improvement=min_margin_improvement,
        min_risk_improvement=min_risk_improvement,
    )
    sources = source_summary(candidates, near_misses)
    write_csv_rows(run_dir / "near_miss_candidates.csv", near_misses.to_dict(orient="records"))
    write_csv_rows(run_dir / "near_miss_sources.csv", sources.to_dict(orient="records"))

    constraint_failure_counts = {
        "fails_mean_l2": int(near_misses["fails_mean_l2"].sum()) if not near_misses.empty else 0,
        "fails_max_l2": int(near_misses["fails_max_l2"].sum()) if not near_misses.empty else 0,
        "fails_delta_delta_l2": int(near_misses["fails_delta_delta_l2"].sum()) if not near_misses.empty else 0,
        "candidate_collision": int(near_misses["candidate_collision"].sum()) if not near_misses.empty else 0,
        "candidate_off_road": int(near_misses["candidate_off_road"].sum()) if not near_misses.empty else 0,
        "candidate_spin_out": int(near_misses["candidate_spin_out"].sum()) if not near_misses.empty else 0,
    }
    summary = {
        "run_type": "near_miss_trust_geometry",
        "sequence_candidates_csv": sequence_candidates_csv,
        "unaccepted_rows_csv": unaccepted_rows_csv,
        "mean_l2_limit": float(mean_l2_limit),
        "max_l2_limit": float(max_l2_limit),
        "delta_delta_l2_limit": float(delta_delta_l2_limit),
        "min_margin_improvement": float(min_margin_improvement),
        "min_risk_improvement": float(min_risk_improvement),
        "candidate_rows": int(len(candidates)),
        "near_miss_candidates": int(len(near_misses)),
        "near_miss_sources": int(len(sources)),
        "near_miss_sources_by_tier": _counts(sources, "source_tier"),
        "primary_failure_counts": _counts(near_misses, "primary_failure"),
        "constraint_failure_counts": constraint_failure_counts,
        "sources_with_margin_threshold_near_miss": int(
            sources["source_index"].nunique() if not sources.empty else 0
        ),
        "sources_with_trust_near_miss": int(sources["has_trust_near_miss"].sum()) if not sources.empty else 0,
        "sources_with_collision_near_miss": int(sources["has_collision_near_miss"].sum()) if not sources.empty else 0,
        "best_margin_improvement": _float(near_misses["margin_improvement"].max()) if not near_misses.empty else float("nan"),
        "median_mean_l2_excess": _median(near_misses, "mean_l2_excess"),
        "median_max_l2_excess": _median(near_misses, "max_l2_excess"),
        "median_delta_delta_excess": _median(near_misses, "delta_delta_excess"),
        "target_acceptance_thresholds_changed": False,
        "trust_regions_changed": False,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "near_miss_candidates_csv": run_dir / "near_miss_candidates.csv",
        "near_miss_sources_csv": run_dir / "near_miss_sources.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze sequence near misses against trust-region constraints.")
    parser.add_argument("--sequence-candidates", type=Path, required=True)
    parser.add_argument("--unaccepted-rows", type=Path, required=True)
    parser.add_argument("--mean-l2-limit", type=float, default=0.08)
    parser.add_argument("--max-l2-limit", type=float, default=0.10)
    parser.add_argument("--delta-delta-l2-limit", type=float, default=0.08)
    parser.add_argument("--min-margin-improvement", type=float, default=0.02)
    parser.add_argument("--min-risk-improvement", type=float, default=0.05)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="near_miss_trust_geometry")
    summary = run_near_miss_trust_geometry(
        sequence_candidates_csv=args.sequence_candidates,
        unaccepted_rows_csv=args.unaccepted_rows,
        mean_l2_limit=args.mean_l2_limit,
        max_l2_limit=args.max_l2_limit,
        delta_delta_l2_limit=args.delta_delta_l2_limit,
        min_margin_improvement=args.min_margin_improvement,
        min_risk_improvement=args.min_risk_improvement,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
