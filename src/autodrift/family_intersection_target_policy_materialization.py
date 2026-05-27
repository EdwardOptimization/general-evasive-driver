"""Materialize family-intersection rows for one target policy."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_corpus_objective import validate_boundary_row_frame
from autodrift.family_aggregate_intersection_selector import build_diversity_summary, validate_replay_rows
from autodrift.family_aggregate_replay_sanity import validate_family_rows


TARGET_REPLAY_COLUMNS = (
    "policy",
    "checkpoint",
    "family_row_id",
    "normal_success",
    "wrong_history_success",
    "success_drop",
    "normal_margin",
    "wrong_history_margin",
    "margin_gap",
    "normal_first_steer",
    "normal_first_throttle",
    "normal_first_brake",
    "wrong_history_first_steer",
    "wrong_history_first_throttle",
    "wrong_history_first_brake",
)
SOURCE_DIAGNOSTIC_COLUMNS = (
    "checkpoint_label",
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
)


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def validate_target_replay_rows(frame: pd.DataFrame) -> None:
    validate_replay_rows(frame)
    missing = [column for column in TARGET_REPLAY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("target replay rows missing columns: " + ", ".join(missing))


def _validate_target_replay_row(row: pd.Series, *, family_row_id: int, target_policy_label: str) -> None:
    if not _bool_value(row["normal_success"]):
        raise ValueError(f"target policy {target_policy_label} normal history failed for row {family_row_id}")
    if _bool_value(row["wrong_history_success"]):
        raise ValueError(f"target policy {target_policy_label} wrong history succeeded for row {family_row_id}")
    if not _bool_value(row["success_drop"]):
        raise ValueError(f"target policy {target_policy_label} success drop missing for row {family_row_id}")
    for column in ("normal_margin", "wrong_history_margin", "margin_gap"):
        if not np.isfinite(_as_float(row[column])):
            raise ValueError(f"target policy {target_policy_label} has non-finite {column} for row {family_row_id}")


def materialize_target_policy_rows(
    *,
    intersection_frame: pd.DataFrame,
    replay_frame: pd.DataFrame,
    target_policy_label: str,
) -> pd.DataFrame:
    validate_family_rows(intersection_frame)
    validate_target_replay_rows(replay_frame)
    intersections = intersection_frame.copy()
    intersections["family_row_id"] = intersections["family_row_id"].astype(int)
    replay = replay_frame.copy()
    replay["family_row_id"] = replay["family_row_id"].astype(int)
    target_rows = replay[replay["policy"].astype(str) == str(target_policy_label)].copy()
    target_by_row_id = {
        int(row["family_row_id"]): row
        for _, row in target_rows.iterrows()
    }
    missing = sorted(set(intersections["family_row_id"].astype(int)) - set(target_by_row_id))
    if missing:
        raise ValueError(
            f"target policy {target_policy_label} missing replay rows for family_row_id: "
            + ",".join(str(value) for value in missing[:20])
        )

    materialized_rows: list[dict[str, Any]] = []
    for _, source_row in intersections.sort_values("family_row_id").iterrows():
        family_row_id = int(source_row["family_row_id"])
        replay_row = target_by_row_id[family_row_id]
        _validate_target_replay_row(
            replay_row,
            family_row_id=family_row_id,
            target_policy_label=target_policy_label,
        )
        row = source_row.to_dict()
        for column in SOURCE_DIAGNOSTIC_COLUMNS:
            if column in row:
                row[f"source_{column}"] = row[column]
        row["source_original_checkpoint_label"] = str(source_row.get("checkpoint_label", ""))
        row["target_policy_label"] = str(target_policy_label)
        row["target_policy_checkpoint"] = str(replay_row.get("checkpoint", ""))
        row["checkpoint_label"] = str(target_policy_label)
        row["variant"] = "wrong_matched_history"
        row["accepted"] = True
        row["normal_margin"] = float(replay_row["normal_margin"])
        row["variant_margin"] = float(replay_row["wrong_history_margin"])
        row["margin_gap"] = float(replay_row["margin_gap"])
        row["normal_success"] = _bool_value(replay_row["normal_success"])
        row["variant_success"] = _bool_value(replay_row["wrong_history_success"])
        row["success_drop"] = _bool_value(replay_row["success_drop"])
        row["normal_first_steer"] = float(replay_row["normal_first_steer"])
        row["normal_first_throttle"] = float(replay_row["normal_first_throttle"])
        row["normal_first_brake"] = float(replay_row["normal_first_brake"])
        row["variant_first_steer"] = float(replay_row["wrong_history_first_steer"])
        row["variant_first_throttle"] = float(replay_row["wrong_history_first_throttle"])
        row["variant_first_brake"] = float(replay_row["wrong_history_first_brake"])
        row["materialized_from_family_intersection"] = True
        materialized_rows.append(row)

    materialized = pd.DataFrame(materialized_rows)
    validate_boundary_row_frame(materialized)
    return materialized.reset_index(drop=True)


def build_source_summary(rows: pd.DataFrame) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for source_label, group in rows.groupby("source_checkpoint_label", observed=True):
        summary_rows.append(
            {
                "source_checkpoint_label": str(source_label),
                "rows": int(len(group)),
                "physical_pairs": int(group["physical_pair_key"].astype(str).nunique()),
                "targets": int(group["target"].astype(str).nunique()),
                "left_steps": int(group["left_step"].astype(int).nunique()),
                "normal_margin_min": float(pd.to_numeric(group["normal_margin"], errors="coerce").min()),
                "wrong_history_margin_max": float(pd.to_numeric(group["variant_margin"], errors="coerce").max()),
                "margin_gap_min": float(pd.to_numeric(group["margin_gap"], errors="coerce").min()),
            }
        )
    return sorted(summary_rows, key=lambda row: str(row["source_checkpoint_label"]))


def build_target_summary(rows: pd.DataFrame) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for target, group in rows.groupby("target", observed=True):
        summary_rows.append(
            {
                "target": str(target),
                "rows": int(len(group)),
                "physical_pairs": int(group["physical_pair_key"].astype(str).nunique()),
                "source_labels": int(group["source_checkpoint_label"].astype(str).nunique()),
                "left_steps": int(group["left_step"].astype(int).nunique()),
                "normal_margin_min": float(pd.to_numeric(group["normal_margin"], errors="coerce").min()),
                "wrong_history_margin_max": float(pd.to_numeric(group["variant_margin"], errors="coerce").max()),
                "margin_gap_min": float(pd.to_numeric(group["margin_gap"], errors="coerce").min()),
            }
        )
    return sorted(summary_rows, key=lambda row: str(row["target"]))


def _finite_objective_rows(rows: pd.DataFrame) -> int:
    margin_columns = ("normal_margin", "variant_margin", "margin_gap")
    finite_mask = np.ones(len(rows), dtype=bool)
    for column in margin_columns:
        finite_mask &= np.isfinite(pd.to_numeric(rows[column], errors="coerce").astype(float).to_numpy())
    return int(finite_mask.sum())


def run_target_policy_materialization(
    *,
    family_intersection_rows_csv: Path,
    cross_family_replay_rows_csv: Path,
    target_policy_label: str,
    run_dir: Path,
    expected_rows: int = 133,
    min_physical_pairs: int = 10,
    min_source_labels: int = 4,
    min_targets: int = 3,
    min_left_steps: int = 8,
    max_physical_pair_fraction: float = 0.20,
    max_source_label_fraction: float = 0.45,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    intersection = pd.read_csv(family_intersection_rows_csv)
    replay = pd.read_csv(cross_family_replay_rows_csv)
    materialized = materialize_target_policy_rows(
        intersection_frame=intersection,
        replay_frame=replay,
        target_policy_label=target_policy_label,
    )
    diversity = build_diversity_summary(
        materialized,
        min_rows=expected_rows,
        min_physical_pairs=min_physical_pairs,
        min_source_labels=min_source_labels,
        min_targets=min_targets,
        min_left_steps=min_left_steps,
        max_physical_pair_fraction=max_physical_pair_fraction,
        max_source_label_fraction=max_source_label_fraction,
    )
    row_count = int(len(materialized))
    normal_success_count = int(sum(_bool_value(value) for value in materialized["normal_success"]))
    wrong_success_count = int(sum(_bool_value(value) for value in materialized["variant_success"]))
    success_drop_count = int(sum(_bool_value(value) for value in materialized["success_drop"]))
    finite_objective_rows = _finite_objective_rows(materialized)
    validation_pass = bool(
        row_count == int(expected_rows)
        and normal_success_count == row_count
        and wrong_success_count == 0
        and success_drop_count == row_count
        and finite_objective_rows == row_count
        and diversity["gate_pass"]
    )
    source_summary = build_source_summary(materialized)
    target_summary = build_target_summary(materialized)
    prefix = str(target_policy_label)
    boundary_rows_path = run_dir / f"{prefix}_boundary_rows.csv"
    source_summary_path = run_dir / f"{prefix}_source_summary.csv"
    target_summary_path = run_dir / f"{prefix}_target_summary.csv"
    summary_path = run_dir / f"{prefix}_materialization_summary.json"

    write_csv_rows(boundary_rows_path, materialized.to_dict("records"))
    write_csv_rows(source_summary_path, source_summary)
    write_csv_rows(target_summary_path, target_summary)
    summary = {
        "run_type": "family_intersection_target_policy_materialization",
        "family_intersection_rows_csv": family_intersection_rows_csv,
        "cross_family_replay_rows_csv": cross_family_replay_rows_csv,
        "target_policy_label": str(target_policy_label),
        "rows": row_count,
        "expected_rows": int(expected_rows),
        "normal_success_count": normal_success_count,
        "wrong_history_success_count": wrong_success_count,
        "success_drop_count": success_drop_count,
        "finite_objective_rows": finite_objective_rows,
        "diversity_summary": diversity,
        "source_summary": source_summary,
        "target_summary": target_summary,
        "decision": "target_policy_materialization_pass" if validation_pass else "target_policy_materialization_reject",
        "passed": validation_pass,
        "boundary_rows_csv": boundary_rows_path,
        "source_summary_csv": source_summary_path,
        "target_summary_csv": target_summary_path,
        "training_started": False,
        "ppo_used": False,
        "replay_started": False,
        "objective_optimization_started": False,
        "objective_npz_written": False,
        "mining_started": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
    }
    write_json(summary_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize family-intersection rows for one target policy.")
    parser.add_argument("--family-intersection-rows-csv", type=Path, required=True)
    parser.add_argument("--cross-family-replay-rows-csv", type=Path, required=True)
    parser.add_argument("--target-policy-label", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=133)
    parser.add_argument("--min-physical-pairs", type=int, default=10)
    parser.add_argument("--min-source-labels", type=int, default=4)
    parser.add_argument("--min-targets", type=int, default=3)
    parser.add_argument("--min-left-steps", type=int, default=8)
    parser.add_argument("--max-physical-pair-fraction", type=float, default=0.20)
    parser.add_argument("--max-source-label-fraction", type=float, default=0.45)
    args = parser.parse_args()

    summary = run_target_policy_materialization(
        family_intersection_rows_csv=args.family_intersection_rows_csv,
        cross_family_replay_rows_csv=args.cross_family_replay_rows_csv,
        target_policy_label=args.target_policy_label,
        run_dir=args.run_dir,
        expected_rows=args.expected_rows,
        min_physical_pairs=args.min_physical_pairs,
        min_source_labels=args.min_source_labels,
        min_targets=args.min_targets,
        min_left_steps=args.min_left_steps,
        max_physical_pair_fraction=args.max_physical_pair_fraction,
        max_source_label_fraction=args.max_source_label_fraction,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
