"""Expand rollout-backed source rows before repeating sequence target mining."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


SUPPORTED_HISTORY_VARIANTS = ("wrong_matched_history", "delayed_history")
PHYSICAL_KEY = ["left_seed", "left_step", "right_seed", "right_step"]
PROVENANCE_COLUMNS = [
    "source_index",
    "coupling_row_index",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "capability_z_distance",
    "action_distance",
    "coupling_gap",
    "base_steer",
    "base_throttle",
    "base_brake",
    "baseline_success",
    "baseline_collision",
    "baseline_off_road",
    "baseline_spin_out",
    "baseline_terminal_reason",
    "baseline_margin",
    "baseline_risk_score",
    "obstacle_completed",
    "continuation_steps",
]
EXPANSION_COLUMNS = [
    "source_tier",
    "expansion_reason",
    "original_m609_boundary",
    "m613_accepted_sequence",
    "source_expansion_rank",
]


@dataclass(frozen=True)
class ExpandedSourceDiversity:
    rows: int
    unique_physical_pairs: int
    unique_left_seeds: int
    surfaces: int
    variants: int
    targets: int
    max_physical_pair_dominance: float
    pass_diversity: bool


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _check_windows(core_margin_window: float, near_margin_window: float, support_margin_window: float) -> None:
    if not (core_margin_window <= near_margin_window <= support_margin_window):
        raise ValueError("expected core_margin_window <= near_margin_window <= support_margin_window")


def classify_expanded_source(
    row: pd.Series | dict[str, Any],
    *,
    core_margin_window: float,
    near_margin_window: float,
    support_margin_window: float,
) -> tuple[bool, str, str]:
    """Return accepted flag, reason, and source tier for a rollout row."""

    _check_windows(core_margin_window, near_margin_window, support_margin_window)
    variant = str(row.get("variant", ""))
    if variant not in SUPPORTED_HISTORY_VARIANTS:
        return False, "unsupported_history_variant", ""
    if _bool(row.get("baseline_off_road", False)):
        return False, "baseline_off_road", ""
    if _bool(row.get("baseline_spin_out", False)):
        return False, "baseline_spin_out", ""

    margin = _finite_float(row.get("baseline_margin"))
    if not np.isfinite(margin):
        return False, "baseline_margin_not_finite", ""

    if _bool(row.get("baseline_collision", False)):
        return True, "baseline_collision", "core_boundary"
    if margin <= float(core_margin_window):
        return True, "core_margin_window", "core_boundary"
    if margin <= float(near_margin_window):
        return True, "near_margin_window", "near_boundary"
    if margin <= float(support_margin_window):
        return True, "support_margin_window", "support_boundary"
    return False, "baseline_outside_support_window", ""


def expanded_source_diversity(rows: pd.DataFrame) -> ExpandedSourceDiversity:
    if rows.empty:
        return ExpandedSourceDiversity(
            rows=0,
            unique_physical_pairs=0,
            unique_left_seeds=0,
            surfaces=0,
            variants=0,
            targets=0,
            max_physical_pair_dominance=0.0,
            pass_diversity=False,
        )

    pair_counts = rows.groupby(PHYSICAL_KEY, observed=True).size()
    dominance = float(pair_counts.max() / len(rows)) if len(rows) else 0.0
    unique_pairs = int(len(pair_counts))
    left_seeds = int(rows["left_seed"].nunique())
    surfaces = int(rows["surface"].nunique())
    variants = int(rows["variant"].nunique())
    targets = int(rows["target"].nunique())
    pass_diversity = (
        len(rows) >= 24
        and unique_pairs >= 16
        and left_seeds >= 10
        and surfaces >= 2
        and variants >= 2
        and targets >= 2
        and dominance <= 0.20
    )
    return ExpandedSourceDiversity(
        rows=int(len(rows)),
        unique_physical_pairs=unique_pairs,
        unique_left_seeds=left_seeds,
        surfaces=surfaces,
        variants=variants,
        targets=targets,
        max_physical_pair_dominance=dominance,
        pass_diversity=bool(pass_diversity),
    )


def _required_columns() -> set[str]:
    return set(PROVENANCE_COLUMNS)


def _read_source_indices(path: Path, column: str = "source_index") -> set[int]:
    if not path.exists():
        return set()
    frame = pd.read_csv(path)
    if column not in frame.columns:
        return set()
    return {int(value) for value in frame[column].dropna().astype(int).tolist()}


def _fieldnames(source_rollouts: pd.DataFrame) -> list[str]:
    fieldnames = list(source_rollouts.columns)
    for column in EXPANSION_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)
    return fieldnames


def expand_sequence_sources(
    source_rollouts: pd.DataFrame,
    *,
    original_boundary_source_indices: set[int],
    accepted_sequence_source_indices: set[int],
    core_margin_window: float,
    near_margin_window: float,
    support_margin_window: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], ExpandedSourceDiversity]:
    missing = sorted(_required_columns().difference(source_rollouts.columns))
    if missing:
        raise ValueError("source rollouts missing columns: " + ", ".join(missing))
    _check_windows(core_margin_window, near_margin_window, support_margin_window)

    expanded: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for _, row in source_rollouts.sort_values("source_index").iterrows():
        accepted, reason, tier = classify_expanded_source(
            row,
            core_margin_window=core_margin_window,
            near_margin_window=near_margin_window,
            support_margin_window=support_margin_window,
        )
        source_index = int(row["source_index"])
        item = row.to_dict()
        item["source_tier"] = tier
        item["expansion_reason"] = reason
        item["original_m609_boundary"] = source_index in original_boundary_source_indices
        item["m613_accepted_sequence"] = source_index in accepted_sequence_source_indices
        if accepted:
            item["source_expansion_rank"] = len(expanded)
            expanded.append(item)
        else:
            item["source_expansion_rank"] = ""
            rejected.append(item)

    expanded_frame = pd.DataFrame(expanded)
    return expanded, rejected, expanded_source_diversity(expanded_frame)


def run_expanded_sequence_source_miner(
    *,
    source_rollouts_csv: Path,
    original_boundary_source_rows_csv: Path,
    accepted_sequences_csv: Path,
    core_margin_window: float,
    near_margin_window: float,
    support_margin_window: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_rollouts = pd.read_csv(source_rollouts_csv)
    original_indices = _read_source_indices(original_boundary_source_rows_csv)
    accepted_indices = _read_source_indices(accepted_sequences_csv)

    expanded_rows, rejected_rows, diversity = expand_sequence_sources(
        source_rollouts,
        original_boundary_source_indices=original_indices,
        accepted_sequence_source_indices=accepted_indices,
        core_margin_window=core_margin_window,
        near_margin_window=near_margin_window,
        support_margin_window=support_margin_window,
    )
    fieldnames = _fieldnames(source_rollouts)
    write_csv_rows(run_dir / "expanded_sequence_source_rows.csv", expanded_rows, fieldnames=fieldnames)
    write_csv_rows(run_dir / "rejected_sequence_source_rows.csv", rejected_rows, fieldnames=fieldnames)

    tier_counts = Counter(str(row["source_tier"]) for row in expanded_rows)
    reason_counts = Counter(str(row["expansion_reason"]) for row in expanded_rows)
    rejected_reason_counts = Counter(str(row["expansion_reason"]) for row in rejected_rows)
    summary = {
        "run_type": "expanded_sequence_source_miner",
        "source_rollouts_csv": source_rollouts_csv,
        "original_boundary_source_rows_csv": original_boundary_source_rows_csv,
        "accepted_sequences_csv": accepted_sequences_csv,
        "core_margin_window": float(core_margin_window),
        "near_margin_window": float(near_margin_window),
        "support_margin_window": float(support_margin_window),
        "source_rollout_rows": int(len(source_rollouts)),
        "expanded_source_rows": int(len(expanded_rows)),
        "rejected_source_rows": int(len(rejected_rows)),
        "original_m609_boundary_rows_included": int(sum(bool(row["original_m609_boundary"]) for row in expanded_rows)),
        "m613_accepted_sequence_rows_included": int(sum(bool(row["m613_accepted_sequence"]) for row in expanded_rows)),
        "tier_counts": dict(tier_counts),
        "expansion_reason_counts": dict(reason_counts),
        "rejected_reason_counts": dict(rejected_reason_counts),
        "diversity": asdict(diversity),
        "diversity_pass": bool(diversity.pass_diversity),
        "supported_history_variants": list(SUPPORTED_HISTORY_VARIANTS),
        "target_acceptance_thresholds_changed": False,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "expanded_sequence_source_rows_csv": run_dir / "expanded_sequence_source_rows.csv",
        "rejected_sequence_source_rows_csv": run_dir / "rejected_sequence_source_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand sequence-target source rows from rollout artifacts.")
    parser.add_argument("--source-rollouts", type=Path, required=True)
    parser.add_argument("--original-boundary-source-rows", type=Path, required=True)
    parser.add_argument("--accepted-sequences", type=Path, required=True)
    parser.add_argument("--core-margin-window", type=float, default=0.50)
    parser.add_argument("--near-margin-window", type=float, default=1.00)
    parser.add_argument("--support-margin-window", type=float, default=2.00)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="expanded_sequence_source_miner")
    summary = run_expanded_sequence_source_miner(
        source_rollouts_csv=args.source_rollouts,
        original_boundary_source_rows_csv=args.original_boundary_source_rows,
        accepted_sequences_csv=args.accepted_sequences,
        core_margin_window=args.core_margin_window,
        near_margin_window=args.near_margin_window,
        support_margin_window=args.support_margin_window,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
