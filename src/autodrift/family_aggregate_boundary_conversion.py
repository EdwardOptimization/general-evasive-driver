"""Export family-aggregate raw-retained boundary rows for replay sanity."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_corpus_objective import (
    boundary_geometry_key,
    physical_pair_key,
    validate_boundary_row_frame,
)
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec


DEFAULT_SOURCE_FAMILY = "m1092_public_base_short_ppo_family"


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


def _source_policy_map_from_specs(specs: tuple[CheckpointSpec, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for spec in specs:
        label = str(spec.label)
        if label in result:
            raise ValueError(f"duplicate source policy label: {label}")
        result[label] = str(spec.path)
    return result


def load_source_policy_map(
    *,
    source_policy_map_json: Path | None,
    source_policy_specs: tuple[CheckpointSpec, ...],
) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if source_policy_map_json is not None:
        raw = read_json(source_policy_map_json)
        if not isinstance(raw, dict):
            raise ValueError("source policy map JSON must be an object mapping label to path")
        loaded.update({str(label): str(path) for label, path in raw.items()})
    loaded.update(_source_policy_map_from_specs(source_policy_specs))
    if not loaded:
        raise ValueError("source policy map must contain at least one label")
    return loaded


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


def select_raw_retained_rows(frame: pd.DataFrame, *, min_margin_gap: float) -> pd.DataFrame:
    keyed = _ensure_keys(frame)
    selected = keyed[
        (keyed["variant"].astype(str) == "wrong_matched_history")
        & keyed["accepted"].map(_bool_value)
    ].copy()
    selected["_margin_gap"] = _as_float_series(selected["margin_gap"])
    selected = selected[np.isfinite(selected["_margin_gap"])]
    selected = selected[selected["_margin_gap"] >= float(min_margin_gap)].copy()
    selected["_success_drop_rank"] = selected["success_drop"].map(_bool_value).astype(int)
    selected["_normal_margin"] = _as_float_series(selected["normal_margin"])
    selected = selected.sort_values(
        ["_success_drop_rank", "_margin_gap", "_normal_margin", "source_row_index"],
        ascending=[False, False, True, True],
    )
    return selected.drop(
        columns=[column for column in ("_success_drop_rank", "_margin_gap", "_normal_margin") if column in selected],
        errors="ignore",
    ).reset_index(drop=True)


def add_family_metadata(
    rows: pd.DataFrame,
    *,
    source_policy_map: dict[str, str],
    source_family: str,
) -> pd.DataFrame:
    missing_labels = sorted(set(rows["checkpoint_label"].astype(str)) - set(source_policy_map))
    if missing_labels:
        raise ValueError("source policy map missing labels: " + ", ".join(missing_labels))

    converted = rows.copy().reset_index(drop=True)
    converted["family_row_id"] = np.arange(len(converted), dtype=np.int64)
    converted["source_checkpoint_label"] = converted["checkpoint_label"].astype(str)
    converted["source_checkpoint_path"] = [source_policy_map[str(label)] for label in converted["source_checkpoint_label"]]
    converted["source_checkpoint_family"] = str(source_family)

    geometry_order = {key: index for index, key in enumerate(sorted(converted["boundary_geometry_key"].astype(str).unique()))}
    converted["duplicate_geometry_group_id"] = [
        f"g{geometry_order[str(key)]:05d}" for key in converted["boundary_geometry_key"].astype(str)
    ]
    group_sizes = converted.groupby("duplicate_geometry_group_id", observed=True).size().to_dict()
    group_sources = (
        converted.groupby("duplicate_geometry_group_id", observed=True)["source_checkpoint_label"]
        .apply(lambda values: ",".join(sorted(set(str(value) for value in values))))
        .to_dict()
    )
    converted["duplicate_geometry_group_size"] = [
        int(group_sizes[str(group_id)]) for group_id in converted["duplicate_geometry_group_id"]
    ]
    converted["duplicate_geometry_source_labels"] = [
        str(group_sources[str(group_id)]) for group_id in converted["duplicate_geometry_group_id"]
    ]

    preferred_columns = [
        "family_row_id",
        "source_row_index",
        "source_checkpoint_label",
        "source_checkpoint_path",
        "source_checkpoint_family",
        "checkpoint_label",
        "physical_pair_key",
        "boundary_geometry_key",
        "duplicate_geometry_group_id",
        "duplicate_geometry_group_size",
        "duplicate_geometry_source_labels",
        "target",
        "left_seed",
        "right_seed",
        "left_step",
        "right_step",
        "relocated_obstacle_body_x",
        "relocated_obstacle_body_y",
        "relocated_obstacle_half_width",
        "normal_margin",
        "variant_margin",
        "margin_gap",
        "normal_success",
        "variant_success",
        "success_drop",
        "normal_first_steer",
        "normal_first_throttle",
        "normal_first_brake",
        "variant_first_steer",
        "variant_first_throttle",
        "variant_first_brake",
    ]
    ordered = [column for column in preferred_columns if column in converted.columns]
    ordered.extend(column for column in converted.columns if column not in ordered)
    return converted[ordered].reset_index(drop=True)


def aggregate_metrics(
    rows: pd.DataFrame,
    *,
    margin_bucket_width: float,
    min_rows: int,
    min_physical_pairs: int,
    min_left_steps: int,
    min_checkpoints: int,
    min_targets: int,
    min_margin_buckets: int,
    min_success_drop_fraction: float,
    max_rows_per_physical_pair_fraction: float,
) -> dict[str, Any]:
    row_count = int(len(rows))
    if row_count:
        physical_pairs = int(rows["physical_pair_key"].astype(str).nunique())
        left_steps = int(rows["left_step"].astype(int).nunique())
        checkpoints = int(rows["source_checkpoint_label"].astype(str).nunique())
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
    return {
        "rows": row_count,
        "physical_pairs": physical_pairs,
        "left_steps": left_steps,
        "checkpoints": checkpoints,
        "targets": targets,
        "normal_margin_buckets": int(len(buckets)),
        "success_drop_fraction": success_drop_fraction,
        "max_rows_per_physical_pair_rows": max_pair_rows,
        "max_rows_per_physical_pair_fraction": max_pair_fraction,
        "threshold_pass": threshold_pass,
        "min_rows_required": int(min_rows),
        "min_physical_pairs_required": int(min_physical_pairs),
        "min_left_steps_required": int(min_left_steps),
        "min_checkpoints_required": int(min_checkpoints),
        "min_targets_required": int(min_targets),
        "min_margin_buckets_required": int(min_margin_buckets),
    }


def build_source_summary(rows: pd.DataFrame, *, margin_bucket_width: float) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for label, group in rows.groupby("source_checkpoint_label", observed=True):
        pair_counts = group["physical_pair_key"].astype(str).value_counts()
        buckets = {
            _normal_margin_bucket(float(value), margin_bucket_width)
            for value in _as_float_series(group["normal_margin"]).to_numpy()
            if np.isfinite(float(value))
        }
        summary_rows.append(
            {
                "source_checkpoint_label": str(label),
                "source_checkpoint_path": str(group["source_checkpoint_path"].iloc[0]),
                "rows": int(len(group)),
                "physical_pairs": int(group["physical_pair_key"].astype(str).nunique()),
                "left_steps": int(group["left_step"].astype(int).nunique()),
                "targets": int(group["target"].astype(str).nunique()),
                "normal_margin_buckets": int(len(buckets)),
                "success_drop_fraction": float(np.mean([_bool_value(value) for value in group["success_drop"]])),
                "max_rows_per_physical_pair_rows": int(pair_counts.max()) if len(group) else 0,
                "max_rows_per_physical_pair_fraction": float(pair_counts.max() / len(group)) if len(group) else 0.0,
            }
        )
    return sorted(summary_rows, key=lambda row: str(row["source_checkpoint_label"]))


def build_duplicate_geometry_summary(rows: pd.DataFrame) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for group_id, group in rows.groupby("duplicate_geometry_group_id", observed=True):
        normal_margins = _as_float_series(group["normal_margin"])
        margin_gaps = _as_float_series(group["margin_gap"])
        summary_rows.append(
            {
                "duplicate_geometry_group_id": str(group_id),
                "boundary_geometry_key": str(group["boundary_geometry_key"].iloc[0]),
                "physical_pair_key": str(group["physical_pair_key"].iloc[0]),
                "target": str(group["target"].iloc[0]),
                "rows": int(len(group)),
                "source_checkpoint_labels": ",".join(sorted(set(group["source_checkpoint_label"].astype(str)))),
                "family_row_ids": ",".join(str(int(value)) for value in group["family_row_id"]),
                "normal_margin_min": float(normal_margins.min()),
                "normal_margin_max": float(normal_margins.max()),
                "margin_gap_min": float(margin_gaps.min()),
                "margin_gap_max": float(margin_gaps.max()),
            }
        )
    return sorted(
        summary_rows,
        key=lambda row: (-int(row["rows"]), str(row["duplicate_geometry_group_id"])),
    )


def build_replay_plan(
    *,
    run_dir: Path,
    source_policy_map: dict[str, str],
    source_family: str,
    rows: pd.DataFrame,
    aggregate_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_type": "family_aggregate_boundary_replay_plan",
        "source_checkpoint_family": source_family,
        "source_policy_map_json": run_dir / "source_policy_map.json",
        "family_aggregate_boundary_rows_csv": run_dir / "family_aggregate_boundary_rows.csv",
        "source_policy_count": int(len(source_policy_map)),
        "row_count": int(len(rows)),
        "aggregate_threshold_pass": bool(aggregate_summary["threshold_pass"]),
        "replay_started": False,
        "objective_optimization_started": False,
        "mixed_source_objective_npz_allowed": False,
        "required_future_checks": [
            "source_policy_on_source_rows_normal_success_retention",
            "source_policy_on_source_rows_wrong_history_failure_retention",
            "cross_family_replay_report_before_objective_optimization",
            "duplicate_geometry_group_failure_audit",
        ],
        "promotion_allowed": False,
        "private_holdout_used": False,
    }


def run_family_aggregate_conversion(
    *,
    accepted_rows_csv: Path,
    run_dir: Path,
    source_policy_map: dict[str, str],
    source_family: str = DEFAULT_SOURCE_FAMILY,
    min_margin_gap: float = 0.0,
    margin_bucket_width: float = 0.005,
    min_rows: int = 80,
    min_physical_pairs: int = 10,
    min_left_steps: int = 5,
    min_checkpoints: int = 3,
    min_targets: int = 2,
    min_margin_buckets: int = 2,
    min_success_drop_fraction: float = 1.0,
    max_rows_per_physical_pair_fraction: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(accepted_rows_csv)
    selected = select_raw_retained_rows(source, min_margin_gap=min_margin_gap)
    converted = add_family_metadata(
        selected,
        source_policy_map=source_policy_map,
        source_family=source_family,
    )
    aggregate_summary = aggregate_metrics(
        converted,
        margin_bucket_width=margin_bucket_width,
        min_rows=min_rows,
        min_physical_pairs=min_physical_pairs,
        min_left_steps=min_left_steps,
        min_checkpoints=min_checkpoints,
        min_targets=min_targets,
        min_margin_buckets=min_margin_buckets,
        min_success_drop_fraction=min_success_drop_fraction,
        max_rows_per_physical_pair_fraction=max_rows_per_physical_pair_fraction,
    )
    source_summary = build_source_summary(converted, margin_bucket_width=margin_bucket_width)
    duplicate_summary = build_duplicate_geometry_summary(converted)
    replay_plan = build_replay_plan(
        run_dir=run_dir,
        source_policy_map=source_policy_map,
        source_family=source_family,
        rows=converted,
        aggregate_summary=aggregate_summary,
    )

    write_csv_rows(run_dir / "family_aggregate_boundary_rows.csv", converted.to_dict("records"))
    write_json(run_dir / "source_policy_map.json", source_policy_map)
    write_csv_rows(run_dir / "source_summary.csv", source_summary)
    write_csv_rows(run_dir / "duplicate_geometry_summary.csv", duplicate_summary)
    write_json(run_dir / "replay_plan.json", replay_plan)
    summary = {
        "run_type": "family_aggregate_boundary_conversion",
        "accepted_rows_csv": accepted_rows_csv,
        "source_checkpoint_family": source_family,
        "min_margin_gap": float(min_margin_gap),
        "margin_bucket_width": float(margin_bucket_width),
        "aggregate_summary": aggregate_summary,
        "source_summary": source_summary,
        "duplicate_geometry_groups": int(len(duplicate_summary)),
        "duplicate_geometry_multi_source_groups": int(
            sum("," in str(row["source_checkpoint_labels"]) for row in duplicate_summary)
        ),
        "decision": "family_aggregate_conversion_export_pass"
        if aggregate_summary["threshold_pass"]
        else "family_aggregate_conversion_export_reject",
        "passed": bool(aggregate_summary["threshold_pass"]),
        "family_aggregate_boundary_rows_csv": run_dir / "family_aggregate_boundary_rows.csv",
        "source_policy_map_json": run_dir / "source_policy_map.json",
        "source_summary_csv": run_dir / "source_summary.csv",
        "duplicate_geometry_summary_csv": run_dir / "duplicate_geometry_summary.csv",
        "replay_plan_json": run_dir / "replay_plan.json",
        "training_started": False,
        "ppo_used": False,
        "replay_started": False,
        "objective_optimization_started": False,
        "mixed_source_objective_npz_written": False,
        "mining_started": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export family-aggregate raw-retained boundary rows.")
    parser.add_argument("--accepted-rows-csv", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--source-policy-map-json", type=Path, default=None)
    parser.add_argument("--source-policy", action="append", type=parse_checkpoint_spec, default=[])
    parser.add_argument("--source-family", default=DEFAULT_SOURCE_FAMILY)
    parser.add_argument("--min-margin-gap", type=float, default=0.0)
    parser.add_argument("--margin-bucket-width", type=float, default=0.005)
    parser.add_argument("--min-rows", type=int, default=80)
    parser.add_argument("--min-physical-pairs", type=int, default=10)
    parser.add_argument("--min-left-steps", type=int, default=5)
    parser.add_argument("--min-checkpoints", type=int, default=3)
    parser.add_argument("--min-targets", type=int, default=2)
    parser.add_argument("--min-margin-buckets", type=int, default=2)
    parser.add_argument("--min-success-drop-fraction", type=float, default=1.0)
    parser.add_argument("--max-rows-per-physical-pair-fraction", type=float, default=0.25)
    args = parser.parse_args()

    source_policy_map = load_source_policy_map(
        source_policy_map_json=args.source_policy_map_json,
        source_policy_specs=tuple(args.source_policy),
    )
    summary = run_family_aggregate_conversion(
        accepted_rows_csv=args.accepted_rows_csv,
        run_dir=args.run_dir,
        source_policy_map=source_policy_map,
        source_family=args.source_family,
        min_margin_gap=args.min_margin_gap,
        margin_bucket_width=args.margin_bucket_width,
        min_rows=args.min_rows,
        min_physical_pairs=args.min_physical_pairs,
        min_left_steps=args.min_left_steps,
        min_checkpoints=args.min_checkpoints,
        min_targets=args.min_targets,
        min_margin_buckets=args.min_margin_buckets,
        min_success_drop_fraction=args.min_success_drop_fraction,
        max_rows_per_physical_pair_fraction=args.max_rows_per_physical_pair_fraction,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
