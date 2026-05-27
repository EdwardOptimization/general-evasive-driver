"""Compactability audit for source-balanced wrong-history boundary rows."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_corpus_objective import (
    boundary_geometry_key,
    physical_pair_key,
    validate_boundary_row_frame,
)


DEFAULT_CAP_CANDIDATES = (0, 2, 3, 4, 5)
DEFAULT_MIN_MARGIN_GAPS = (0.0, 0.002, 0.005)


def parse_int_list(value: str) -> tuple[int, ...]:
    try:
        parsed = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from exc
    if not parsed:
        raise argparse.ArgumentTypeError("at least one integer is required")
    if any(item < 0 for item in parsed):
        raise argparse.ArgumentTypeError("integer candidates must be non-negative")
    return parsed


def parse_float_list(value: str) -> tuple[float, ...]:
    try:
        parsed = tuple(float(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated floats") from exc
    if not parsed:
        raise argparse.ArgumentTypeError("at least one float is required")
    if any(not np.isfinite(item) or item < 0.0 for item in parsed):
        raise argparse.ArgumentTypeError("float candidates must be finite and non-negative")
    return parsed


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype(float)


def _normal_margin_bucket(value: float, width: float) -> str:
    if width <= 0.0:
        raise ValueError("margin bucket width must be positive")
    if not np.isfinite(value):
        return "nan"
    start = math.floor(float(value) / float(width)) * float(width)
    return f"{start:.6f}:{start + float(width):.6f}"


def _ensure_keys(frame: pd.DataFrame) -> pd.DataFrame:
    validate_boundary_row_frame(frame)
    keyed = frame.copy()
    if "physical_pair_key" not in keyed.columns:
        keyed["physical_pair_key"] = [physical_pair_key(row) for _, row in keyed.iterrows()]
    else:
        keyed["physical_pair_key"] = keyed["physical_pair_key"].astype(str)
    if "boundary_geometry_key" not in keyed.columns:
        keyed["boundary_geometry_key"] = [boundary_geometry_key(row) for _, row in keyed.iterrows()]
    else:
        keyed["boundary_geometry_key"] = keyed["boundary_geometry_key"].astype(str)
    keyed["source_row_index"] = np.arange(len(keyed), dtype=np.int64)
    return keyed


def select_compactability_rows(
    frame: pd.DataFrame,
    *,
    checkpoint_label: str | None,
    min_margin_gap: float,
    max_rows_per_physical_pair: int,
    deduplicate_geometry: bool,
) -> pd.DataFrame:
    """Select rows using the same rank/cap semantics as compact conversion."""

    keyed = _ensure_keys(frame)
    selected = keyed[
        (keyed["variant"].astype(str) == "wrong_matched_history")
        & keyed["accepted"].map(_bool_value)
    ].copy()
    if checkpoint_label is not None:
        selected = selected[selected["checkpoint_label"].astype(str) == str(checkpoint_label)].copy()
    selected["_margin_gap"] = _as_float_series(selected["margin_gap"])
    selected = selected[np.isfinite(selected["_margin_gap"])]
    selected = selected[selected["_margin_gap"] >= float(min_margin_gap)].copy()
    if selected.empty:
        return selected.drop(columns=[column for column in ("_margin_gap",) if column in selected]).reset_index(drop=True)

    selected["_success_drop_rank"] = selected["success_drop"].map(_bool_value).astype(int)
    selected["_normal_margin"] = _as_float_series(selected["normal_margin"])
    selected = selected.sort_values(
        ["_success_drop_rank", "_margin_gap", "_normal_margin", "source_row_index"],
        ascending=[False, False, True, True],
    )
    if deduplicate_geometry:
        selected = selected.drop_duplicates("boundary_geometry_key", keep="first")
    if int(max_rows_per_physical_pair) > 0:
        selected = (
            selected.groupby("physical_pair_key", observed=True, group_keys=False)
            .head(int(max_rows_per_physical_pair))
            .reset_index(drop=True)
        )
    return selected.drop(
        columns=[column for column in ("_success_drop_rank", "_margin_gap", "_normal_margin") if column in selected],
        errors="ignore",
    ).reset_index(drop=True)


def compactability_metrics(
    rows: pd.DataFrame,
    *,
    mode: str,
    selection_kind: str,
    checkpoint_label: str,
    min_margin_gap: float,
    max_rows_per_physical_pair: int,
    margin_bucket_width: float,
    min_rows: int,
    min_physical_pairs: int,
    min_left_steps: int,
    min_checkpoints: int,
    min_targets: int,
    min_margin_buckets: int,
    min_success_drop_fraction: float,
    max_rows_per_physical_pair_fraction: float,
    requires_replay: bool = False,
) -> dict[str, Any]:
    row_count = int(len(rows))
    if row_count:
        physical_pairs = int(rows["physical_pair_key"].astype(str).nunique())
        left_steps = int(rows["left_step"].astype(int).nunique())
        checkpoints = int(rows["checkpoint_label"].astype(str).nunique())
        targets = int(rows["target"].astype(str).nunique())
        pair_counts = rows["physical_pair_key"].astype(str).value_counts()
        max_pair_rows = int(pair_counts.max())
        max_pair_fraction = float(max_pair_rows / row_count)
        buckets = {
            _normal_margin_bucket(float(value), margin_bucket_width)
            for value in _as_float_series(rows["normal_margin"]).to_numpy()
            if np.isfinite(float(value))
        }
        success_drop_fraction = float(np.mean([_bool_value(value) for value in rows["success_drop"]]))
    else:
        physical_pairs = 0
        left_steps = 0
        checkpoints = 0
        targets = 0
        max_pair_rows = 0
        max_pair_fraction = 0.0
        buckets = set()
        success_drop_fraction = 0.0

    threshold_pass = bool(
        row_count >= int(min_rows)
        and physical_pairs >= int(min_physical_pairs)
        and left_steps >= int(min_left_steps)
        and checkpoints >= int(min_checkpoints)
        and targets >= int(min_targets)
        and len(buckets) >= int(min_margin_buckets)
        and success_drop_fraction >= float(min_success_drop_fraction)
        and max_pair_fraction <= float(max_rows_per_physical_pair_fraction)
    )
    conversion_ready = bool(threshold_pass and not requires_replay)
    return {
        "mode": mode,
        "selection_kind": selection_kind,
        "checkpoint_label": checkpoint_label,
        "min_margin_gap": float(min_margin_gap),
        "max_rows_per_physical_pair": int(max_rows_per_physical_pair),
        "rows": row_count,
        "physical_pairs": physical_pairs,
        "left_steps": left_steps,
        "targets": targets,
        "checkpoints": checkpoints,
        "max_rows_per_physical_pair_rows": max_pair_rows,
        "max_rows_per_physical_pair_fraction": max_pair_fraction,
        "normal_margin_buckets": int(len(buckets)),
        "success_drop_fraction": success_drop_fraction,
        "requires_replay": bool(requires_replay),
        "threshold_pass": threshold_pass,
        "conversion_ready": conversion_ready,
        "min_rows_required": int(min_rows),
        "min_physical_pairs_required": int(min_physical_pairs),
        "min_left_steps_required": int(min_left_steps),
        "min_checkpoints_required": int(min_checkpoints),
        "min_targets_required": int(min_targets),
        "min_margin_buckets_required": int(min_margin_buckets),
    }


def _best_row(rows: list[dict[str, Any]], *, mode: str, selection_kind: str | None = None) -> dict[str, Any] | None:
    candidates = [
        row
        for row in rows
        if row.get("mode") == mode
        and (selection_kind is None or row.get("selection_kind") == selection_kind)
        and bool(row.get("conversion_ready", False))
    ]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (
            float(row["min_margin_gap"]),
            int(row["max_rows_per_physical_pair"]) if int(row["max_rows_per_physical_pair"]) > 0 else 9999,
            -int(row["physical_pairs"]),
            -int(row["rows"]),
        ),
    )[0]


def choose_recommended_conversion_mode(
    *,
    per_checkpoint_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    checkpoint_labels: tuple[str, ...],
) -> dict[str, Any]:
    grouped: dict[tuple[float, int], list[dict[str, Any]]] = {}
    for row in per_checkpoint_rows:
        if bool(row.get("conversion_ready", False)):
            grouped.setdefault((float(row["min_margin_gap"]), int(row["max_rows_per_physical_pair"])), []).append(row)
    per_checkpoint_candidates = [
        (key, rows)
        for key, rows in grouped.items()
        if {str(row["checkpoint_label"]) for row in rows} == set(checkpoint_labels)
    ]
    if per_checkpoint_candidates:
        (min_gap, cap), rows = sorted(
            per_checkpoint_candidates,
            key=lambda item: (
                item[0][0],
                item[0][1] if item[0][1] > 0 else 9999,
                -sum(int(row["rows"]) for row in item[1]),
            ),
        )[0]
        return {
            "recommended_mode": "per_checkpoint",
            "recommended_selection_kind": "compact_dedup",
            "decision": "source_balanced_compactability_recommend_per_checkpoint_conversion",
            "reason": "all checkpoint labels meet compact corpus thresholds under one cap/min-gap setting",
            "min_margin_gap": float(min_gap),
            "max_rows_per_physical_pair": int(cap),
            "ready_for_existing_conversion_path": True,
            "requires_new_conversion_path": False,
            "requires_replay_before_objective_conversion": False,
            "supporting_rows": rows,
        }

    aggregate_compact = _best_row(aggregate_rows, mode="family_aggregate", selection_kind="compact_dedup")
    if aggregate_compact is not None:
        return {
            "recommended_mode": "family_aggregate",
            "recommended_selection_kind": "compact_dedup",
            "decision": "source_balanced_compactability_recommend_family_aggregate_conversion",
            "reason": "per-checkpoint corpora are sparse but aggregate compact-dedup selection meets source-diversity thresholds",
            "min_margin_gap": float(aggregate_compact["min_margin_gap"]),
            "max_rows_per_physical_pair": int(aggregate_compact["max_rows_per_physical_pair"]),
            "ready_for_existing_conversion_path": False,
            "requires_new_conversion_path": True,
            "requires_replay_before_objective_conversion": False,
            "supporting_rows": [aggregate_compact],
        }

    aggregate_raw = _best_row(aggregate_rows, mode="family_aggregate", selection_kind="raw_retained")
    if aggregate_raw is not None:
        return {
            "recommended_mode": "family_aggregate",
            "recommended_selection_kind": "raw_retained",
            "decision": "source_balanced_compactability_recommend_family_aggregate_conversion_design",
            "reason": (
                "per-checkpoint corpora are sparse and compact-dedup aggregate is row-limited, "
                "but raw retained aggregate rows preserve the passed M1092 source-balanced surface"
            ),
            "min_margin_gap": float(aggregate_raw["min_margin_gap"]),
            "max_rows_per_physical_pair": int(aggregate_raw["max_rows_per_physical_pair"]),
            "ready_for_existing_conversion_path": False,
            "requires_new_conversion_path": True,
            "requires_replay_before_objective_conversion": True,
            "supporting_rows": [aggregate_raw],
        }

    return {
        "recommended_mode": "no_conversion_ready",
        "recommended_selection_kind": "none",
        "decision": "source_balanced_compactability_no_mode_ready",
        "reason": "no audited mode met compactability thresholds without new surface mining or replay-calibrated filtering",
        "ready_for_existing_conversion_path": False,
        "requires_new_conversion_path": False,
        "requires_replay_before_objective_conversion": False,
        "supporting_rows": [],
    }


def run_compactability_audit(
    *,
    accepted_rows_csv: Path,
    run_dir: Path,
    max_rows_per_physical_pair_candidates: tuple[int, ...] = DEFAULT_CAP_CANDIDATES,
    min_margin_gap_candidates: tuple[float, ...] = DEFAULT_MIN_MARGIN_GAPS,
    margin_bucket_width: float = 0.005,
    min_per_checkpoint_rows: int = 20,
    min_per_checkpoint_physical_pairs: int = 10,
    min_per_checkpoint_targets: int = 2,
    min_aggregate_rows: int = 80,
    min_aggregate_physical_pairs: int = 10,
    min_aggregate_left_steps: int = 5,
    min_aggregate_checkpoints: int = 3,
    min_aggregate_targets: int = 2,
    min_aggregate_margin_buckets: int = 2,
    min_success_drop_fraction: float = 1.0,
    max_rows_per_physical_pair_fraction: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(accepted_rows_csv)
    source = _ensure_keys(source)
    checkpoint_labels = tuple(sorted(source["checkpoint_label"].astype(str).unique()))

    per_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []
    for min_gap in min_margin_gap_candidates:
        for cap in max_rows_per_physical_pair_candidates:
            for label in checkpoint_labels:
                selected = select_compactability_rows(
                    source,
                    checkpoint_label=label,
                    min_margin_gap=float(min_gap),
                    max_rows_per_physical_pair=int(cap),
                    deduplicate_geometry=True,
                )
                per_rows.append(
                    compactability_metrics(
                        selected,
                        mode="per_checkpoint",
                        selection_kind="compact_dedup",
                        checkpoint_label=label,
                        min_margin_gap=float(min_gap),
                        max_rows_per_physical_pair=int(cap),
                        margin_bucket_width=margin_bucket_width,
                        min_rows=min_per_checkpoint_rows,
                        min_physical_pairs=min_per_checkpoint_physical_pairs,
                        min_left_steps=1,
                        min_checkpoints=1,
                        min_targets=min_per_checkpoint_targets,
                        min_margin_buckets=1,
                        min_success_drop_fraction=min_success_drop_fraction,
                        max_rows_per_physical_pair_fraction=max_rows_per_physical_pair_fraction,
                    )
                )

            for selection_kind, deduplicate, requires_replay, mode in (
                ("compact_dedup", True, False, "family_aggregate"),
                ("raw_retained", False, False, "family_aggregate"),
                ("family_intersection_replay_required_proxy", False, True, "family_intersection"),
            ):
                selected = select_compactability_rows(
                    source,
                    checkpoint_label=None,
                    min_margin_gap=float(min_gap),
                    max_rows_per_physical_pair=int(cap),
                    deduplicate_geometry=deduplicate,
                )
                aggregate_rows.append(
                    compactability_metrics(
                        selected,
                        mode=mode,
                        selection_kind=selection_kind,
                        checkpoint_label="all",
                        min_margin_gap=float(min_gap),
                        max_rows_per_physical_pair=int(cap),
                        margin_bucket_width=margin_bucket_width,
                        min_rows=min_aggregate_rows,
                        min_physical_pairs=min_aggregate_physical_pairs,
                        min_left_steps=min_aggregate_left_steps,
                        min_checkpoints=min_aggregate_checkpoints,
                        min_targets=min_aggregate_targets,
                        min_margin_buckets=min_aggregate_margin_buckets,
                        min_success_drop_fraction=min_success_drop_fraction,
                        max_rows_per_physical_pair_fraction=max_rows_per_physical_pair_fraction,
                        requires_replay=requires_replay,
                    )
                )

    recommendation = choose_recommended_conversion_mode(
        per_checkpoint_rows=per_rows,
        aggregate_rows=aggregate_rows,
        checkpoint_labels=checkpoint_labels,
    )
    recommendation.update(
        {
            "checkpoint_labels": list(checkpoint_labels),
            "input_csv": accepted_rows_csv,
            "per_checkpoint_labels_all_ready": bool(recommendation["recommended_mode"] == "per_checkpoint"),
        }
    )

    write_csv_rows(run_dir / "per_checkpoint_compactability.csv", per_rows)
    write_csv_rows(run_dir / "aggregate_compactability.csv", aggregate_rows)
    write_json(run_dir / "recommended_conversion_mode.json", recommendation)

    source_wrong = source[
        (source["variant"].astype(str) == "wrong_matched_history")
        & source["accepted"].map(_bool_value)
    ].copy()
    summary = {
        "run_type": "source_balanced_compactability_audit",
        "accepted_rows_csv": accepted_rows_csv,
        "input_rows": int(len(source)),
        "accepted_wrong_rows": int(len(source_wrong)),
        "checkpoint_labels": list(checkpoint_labels),
        "cap_candidates": list(max_rows_per_physical_pair_candidates),
        "min_margin_gap_candidates": list(min_margin_gap_candidates),
        "margin_bucket_width": float(margin_bucket_width),
        "per_checkpoint_table": run_dir / "per_checkpoint_compactability.csv",
        "aggregate_table": run_dir / "aggregate_compactability.csv",
        "recommended_conversion_mode_json": run_dir / "recommended_conversion_mode.json",
        "recommendation": recommendation,
        "audit_completed": True,
        "passed": True,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit source-balanced boundary compactability modes.")
    parser.add_argument("--accepted-rows-csv", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--max-rows-per-physical-pair-candidates",
        type=parse_int_list,
        default=DEFAULT_CAP_CANDIDATES,
    )
    parser.add_argument("--min-margin-gap-candidates", type=parse_float_list, default=DEFAULT_MIN_MARGIN_GAPS)
    parser.add_argument("--margin-bucket-width", type=float, default=0.005)
    parser.add_argument("--min-per-checkpoint-rows", type=int, default=20)
    parser.add_argument("--min-per-checkpoint-physical-pairs", type=int, default=10)
    parser.add_argument("--min-per-checkpoint-targets", type=int, default=2)
    parser.add_argument("--min-aggregate-rows", type=int, default=80)
    parser.add_argument("--min-aggregate-physical-pairs", type=int, default=10)
    parser.add_argument("--min-aggregate-left-steps", type=int, default=5)
    parser.add_argument("--min-aggregate-checkpoints", type=int, default=3)
    parser.add_argument("--min-aggregate-targets", type=int, default=2)
    parser.add_argument("--min-aggregate-margin-buckets", type=int, default=2)
    parser.add_argument("--min-success-drop-fraction", type=float, default=1.0)
    parser.add_argument("--max-rows-per-physical-pair-fraction", type=float, default=0.25)
    args = parser.parse_args()

    summary = run_compactability_audit(
        accepted_rows_csv=args.accepted_rows_csv,
        run_dir=args.run_dir,
        max_rows_per_physical_pair_candidates=args.max_rows_per_physical_pair_candidates,
        min_margin_gap_candidates=args.min_margin_gap_candidates,
        margin_bucket_width=args.margin_bucket_width,
        min_per_checkpoint_rows=args.min_per_checkpoint_rows,
        min_per_checkpoint_physical_pairs=args.min_per_checkpoint_physical_pairs,
        min_per_checkpoint_targets=args.min_per_checkpoint_targets,
        min_aggregate_rows=args.min_aggregate_rows,
        min_aggregate_physical_pairs=args.min_aggregate_physical_pairs,
        min_aggregate_left_steps=args.min_aggregate_left_steps,
        min_aggregate_checkpoints=args.min_aggregate_checkpoints,
        min_aggregate_targets=args.min_aggregate_targets,
        min_aggregate_margin_buckets=args.min_aggregate_margin_buckets,
        min_success_drop_fraction=args.min_success_drop_fraction,
        max_rows_per_physical_pair_fraction=args.max_rows_per_physical_pair_fraction,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
