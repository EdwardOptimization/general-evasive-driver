"""Select all-policy family-intersection rows from replay-calibrated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.family_aggregate_replay_sanity import validate_family_rows


REPLAY_REQUIRED_COLUMNS = (
    "policy",
    "family_row_id",
    "normal_success",
    "wrong_history_success",
    "success_drop",
    "normal_margin",
    "wrong_history_margin",
    "margin_gap",
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


def validate_replay_rows(frame: pd.DataFrame) -> None:
    missing = [column for column in REPLAY_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("cross-family replay rows missing columns: " + ", ".join(missing))
    duplicates = frame.duplicated(subset=["family_row_id", "policy"])
    if duplicates.any():
        raise ValueError("cross-family replay rows must be unique by family_row_id and policy")


def _policy_row_pass(row: pd.Series) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not _bool_value(row["normal_success"]):
        reasons.append("normal_history_failure")
    if _bool_value(row["wrong_history_success"]):
        reasons.append("wrong_history_success")
    if not _bool_value(row["success_drop"]):
        reasons.append("success_drop_failure")
    margins = (
        _as_float(row["normal_margin"]),
        _as_float(row["wrong_history_margin"]),
        _as_float(row["margin_gap"]),
    )
    if not all(np.isfinite(value) for value in margins):
        reasons.append("nonfinite_margin")
    return (len(reasons) == 0, reasons)


def build_policy_pass_matrix(
    *,
    family_frame: pd.DataFrame,
    replay_frame: pd.DataFrame,
    expected_policies: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    validate_family_rows(family_frame)
    validate_replay_rows(replay_frame)
    replay = replay_frame.copy()
    replay["family_row_id"] = replay["family_row_id"].astype(int)
    family = family_frame.copy()
    family["family_row_id"] = family["family_row_id"].astype(int)
    policies = tuple(str(policy) for policy in (expected_policies or tuple(sorted(replay["policy"].astype(str).unique()))))
    if not policies:
        raise ValueError("expected policy list must not be empty")

    replay_by_key = {
        (int(row["family_row_id"]), str(row["policy"])): row
        for _, row in replay.iterrows()
    }
    matrix_rows: list[dict[str, Any]] = []
    for _, family_row in family.sort_values("family_row_id").iterrows():
        family_row_id = int(family_row["family_row_id"])
        source_label = str(family_row["source_checkpoint_label"])
        failed_policies: list[str] = []
        failure_reasons: set[str] = set()
        normal_margins: list[float] = []
        wrong_margins: list[float] = []
        margin_gaps: list[float] = []
        pass_count = 0

        for policy in policies:
            replay_row = replay_by_key.get((family_row_id, policy))
            if replay_row is None:
                failed_policies.append(policy)
                failure_reasons.add("missing_policy_replay")
                continue
            row_pass, reasons = _policy_row_pass(replay_row)
            if row_pass:
                pass_count += 1
            else:
                failed_policies.append(policy)
                failure_reasons.update(reasons)
            normal_margins.append(_as_float(replay_row["normal_margin"]))
            wrong_margins.append(_as_float(replay_row["wrong_history_margin"]))
            margin_gaps.append(_as_float(replay_row["margin_gap"]))

        source_replay = replay_by_key.get((family_row_id, source_label))
        if source_replay is None:
            failure_reasons.add("source_policy_failure")
            if source_label not in failed_policies:
                failed_policies.append(source_label)
        else:
            source_pass, _ = _policy_row_pass(source_replay)
            if not source_pass:
                failure_reasons.add("source_policy_failure")

        finite_gaps = [value for value in margin_gaps if np.isfinite(value)]
        finite_normal = [value for value in normal_margins if np.isfinite(value)]
        finite_wrong = [value for value in wrong_margins if np.isfinite(value)]
        all_policy_pass = bool(pass_count == len(policies) and not failure_reasons)
        matrix_rows.append(
            {
                "family_row_id": family_row_id,
                "source_checkpoint_label": source_label,
                "family_policy_count": int(len(policies)),
                "family_policy_pass_count": int(pass_count),
                "all_policy_pass": all_policy_pass,
                "failed_policy_labels": ",".join(sorted(set(failed_policies))),
                "failure_reasons": ",".join(sorted(failure_reasons)),
                "min_normal_margin": float(min(finite_normal)) if finite_normal else float("nan"),
                "max_wrong_history_margin": float(max(finite_wrong)) if finite_wrong else float("nan"),
                "min_margin_gap": float(min(finite_gaps)) if finite_gaps else float("nan"),
                "mean_margin_gap": float(np.mean(finite_gaps)) if finite_gaps else float("nan"),
            }
        )
    return pd.DataFrame(matrix_rows)


def select_intersection_rows(
    *,
    family_frame: pd.DataFrame,
    replay_frame: pd.DataFrame,
    expected_policies: tuple[str, ...] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matrix = build_policy_pass_matrix(
        family_frame=family_frame,
        replay_frame=replay_frame,
        expected_policies=expected_policies,
    )
    merged = family_frame.merge(matrix, on=["family_row_id", "source_checkpoint_label"], how="left", validate="one_to_one")
    if merged["all_policy_pass"].isna().any():
        raise ValueError("policy pass matrix missing family rows")
    kept = merged[merged["all_policy_pass"].map(_bool_value)].copy().reset_index(drop=True)
    dropped = merged[~merged["all_policy_pass"].map(_bool_value)].copy().reset_index(drop=True)
    return kept, dropped, matrix


def _max_fraction(series: pd.Series, row_count: int) -> tuple[int, float]:
    if row_count <= 0:
        return 0, 0.0
    counts = series.astype(str).value_counts()
    max_rows = int(counts.max()) if len(counts) else 0
    return max_rows, float(max_rows / row_count)


def build_diversity_summary(
    rows: pd.DataFrame,
    *,
    min_rows: int,
    min_physical_pairs: int,
    min_source_labels: int,
    min_targets: int,
    min_left_steps: int,
    max_physical_pair_fraction: float,
    max_source_label_fraction: float,
) -> dict[str, Any]:
    row_count = int(len(rows))
    physical_pairs = int(rows["physical_pair_key"].astype(str).nunique()) if row_count else 0
    source_labels = int(rows["source_checkpoint_label"].astype(str).nunique()) if row_count else 0
    targets = int(rows["target"].astype(str).nunique()) if row_count else 0
    left_steps = int(rows["left_step"].astype(int).nunique()) if row_count else 0
    max_pair_rows, max_pair_fraction = _max_fraction(rows["physical_pair_key"], row_count)
    max_source_rows, max_source_fraction = _max_fraction(rows["source_checkpoint_label"], row_count)
    gate_pass = bool(
        row_count >= int(min_rows)
        and physical_pairs >= int(min_physical_pairs)
        and source_labels >= int(min_source_labels)
        and targets >= int(min_targets)
        and left_steps >= int(min_left_steps)
        and max_pair_fraction <= float(max_physical_pair_fraction)
        and max_source_fraction <= float(max_source_label_fraction)
    )
    return {
        "rows": row_count,
        "physical_pairs": physical_pairs,
        "source_labels": source_labels,
        "targets": targets,
        "left_steps": left_steps,
        "max_physical_pair_rows": max_pair_rows,
        "max_physical_pair_fraction": max_pair_fraction,
        "max_source_label_rows": max_source_rows,
        "max_source_label_fraction": max_source_fraction,
        "min_rows_required": int(min_rows),
        "min_physical_pairs_required": int(min_physical_pairs),
        "min_source_labels_required": int(min_source_labels),
        "min_targets_required": int(min_targets),
        "min_left_steps_required": int(min_left_steps),
        "max_physical_pair_fraction_allowed": float(max_physical_pair_fraction),
        "max_source_label_fraction_allowed": float(max_source_label_fraction),
        "gate_pass": gate_pass,
    }


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
                "min_margin_gap": float(pd.to_numeric(group["min_margin_gap"], errors="coerce").min()),
                "mean_margin_gap": float(pd.to_numeric(group["mean_margin_gap"], errors="coerce").mean()),
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
                "min_margin_gap": float(pd.to_numeric(group["min_margin_gap"], errors="coerce").min()),
                "mean_margin_gap": float(pd.to_numeric(group["mean_margin_gap"], errors="coerce").mean()),
            }
        )
    return sorted(summary_rows, key=lambda row: str(row["target"]))


def run_family_aggregate_intersection_selector(
    *,
    family_rows_csv: Path,
    cross_family_replay_rows_csv: Path,
    run_dir: Path,
    expected_policies: tuple[str, ...] = (),
    min_rows: int = 80,
    min_physical_pairs: int = 10,
    min_source_labels: int = 4,
    min_targets: int = 3,
    min_left_steps: int = 8,
    max_physical_pair_fraction: float = 0.20,
    max_source_label_fraction: float = 0.45,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    family_frame = pd.read_csv(family_rows_csv)
    replay_frame = pd.read_csv(cross_family_replay_rows_csv)
    policies = expected_policies or tuple(sorted(replay_frame["policy"].astype(str).unique()))
    kept, dropped, matrix = select_intersection_rows(
        family_frame=family_frame,
        replay_frame=replay_frame,
        expected_policies=policies,
    )
    diversity = build_diversity_summary(
        kept,
        min_rows=min_rows,
        min_physical_pairs=min_physical_pairs,
        min_source_labels=min_source_labels,
        min_targets=min_targets,
        min_left_steps=min_left_steps,
        max_physical_pair_fraction=max_physical_pair_fraction,
        max_source_label_fraction=max_source_label_fraction,
    )
    source_summary = build_source_summary(kept)
    target_summary = build_target_summary(kept)
    decision = (
        "family_aggregate_intersection_selector_pass"
        if diversity["gate_pass"]
        else "family_aggregate_intersection_selector_reject"
    )

    write_csv_rows(run_dir / "family_intersection_rows.csv", kept.to_dict("records"))
    write_csv_rows(run_dir / "dropped_cross_family_rows.csv", dropped.to_dict("records"))
    write_csv_rows(run_dir / "policy_pass_matrix.csv", matrix.to_dict("records"))
    write_csv_rows(run_dir / "source_summary.csv", source_summary)
    write_csv_rows(run_dir / "target_summary.csv", target_summary)

    summary = {
        "run_type": "family_aggregate_intersection_selector",
        "family_rows_csv": family_rows_csv,
        "cross_family_replay_rows_csv": cross_family_replay_rows_csv,
        "expected_policies": list(policies),
        "family_rows": int(len(family_frame)),
        "replay_rows": int(len(replay_frame)),
        "kept_rows": int(len(kept)),
        "dropped_rows": int(len(dropped)),
        "diversity_summary": diversity,
        "source_summary": source_summary,
        "target_summary": target_summary,
        "decision": decision,
        "passed": bool(diversity["gate_pass"]),
        "family_intersection_rows_csv": run_dir / "family_intersection_rows.csv",
        "dropped_cross_family_rows_csv": run_dir / "dropped_cross_family_rows.csv",
        "policy_pass_matrix_csv": run_dir / "policy_pass_matrix.csv",
        "source_summary_csv": run_dir / "source_summary.csv",
        "target_summary_csv": run_dir / "target_summary.csv",
        "training_started": False,
        "ppo_used": False,
        "replay_started": False,
        "objective_optimization_started": False,
        "mining_started": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select all-policy family-intersection rows from replay artifacts.")
    parser.add_argument("--family-rows-csv", type=Path, required=True)
    parser.add_argument("--cross-family-replay-rows-csv", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-policy", action="append", default=[])
    parser.add_argument("--min-rows", type=int, default=80)
    parser.add_argument("--min-physical-pairs", type=int, default=10)
    parser.add_argument("--min-source-labels", type=int, default=4)
    parser.add_argument("--min-targets", type=int, default=3)
    parser.add_argument("--min-left-steps", type=int, default=8)
    parser.add_argument("--max-physical-pair-fraction", type=float, default=0.20)
    parser.add_argument("--max-source-label-fraction", type=float, default=0.45)
    args = parser.parse_args()

    summary = run_family_aggregate_intersection_selector(
        family_rows_csv=args.family_rows_csv,
        cross_family_replay_rows_csv=args.cross_family_replay_rows_csv,
        run_dir=args.run_dir,
        expected_policies=tuple(args.expected_policy),
        min_rows=args.min_rows,
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
