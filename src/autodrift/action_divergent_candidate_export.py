"""Export action-divergent wrong-history candidates from outcome artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.source_balanced_boundary_relocation_surface import (
    SourceBalanceQuotas,
    add_source_balance_keys,
    wrong_history_candidate_frame,
)


DEFAULT_MIN_MARGIN_GAP = 0.0025
DEFAULT_MIN_FIRST_ACTION_DISTANCE = 0.15
DEFAULT_MIN_TRAJECTORY_DISTANCE = 0.06


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _required_numeric(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"candidate rows missing required columns: {missing}")
    converted = frame.copy()
    for column in columns:
        converted[column] = pd.to_numeric(converted[column], errors="coerce")
    return converted


def action_divergent_candidate_pool(
    frame: pd.DataFrame,
    *,
    min_margin_gap: float = DEFAULT_MIN_MARGIN_GAP,
    min_first_action_distance: float = DEFAULT_MIN_FIRST_ACTION_DISTANCE,
    min_trajectory_distance: float = DEFAULT_MIN_TRAJECTORY_DISTANCE,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
) -> pd.DataFrame:
    """Return wrong-history rows with action divergence and positive margin sensitivity."""

    candidates = wrong_history_candidate_frame(frame)
    candidates = _required_numeric(
        candidates,
        (
            "margin_gap",
            "first_action_distance",
            "action_trajectory_distance_mean",
            "target_z_delta",
            "visible_distance",
        ),
    )
    mask = (candidates["margin_gap"] >= float(min_margin_gap)) & (
        (candidates["first_action_distance"] >= float(min_first_action_distance))
        | (candidates["action_trajectory_distance_mean"] >= float(min_trajectory_distance))
    )
    pool = candidates[mask].copy().reset_index(drop=True)
    if pool.empty:
        return add_source_balance_keys(
            pool,
            distance_bucket_width=distance_bucket_width,
            lateral_bucket_width=lateral_bucket_width,
        )
    pool["action_divergent_score"] = (
        pool["first_action_distance"] / 0.25
        + pool["action_trajectory_distance_mean"] / 0.15
        + pool["margin_gap"].clip(lower=0.0) / 0.01
        + 0.25 * pool["target_z_delta"]
        - pool["visible_distance"] / 0.25
    )
    pool["_candidate_export_index"] = np.arange(len(pool), dtype=int)
    return add_source_balance_keys(
        pool,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )


def _candidate_sort_key(row: pd.Series | dict[str, Any]) -> tuple[Any, ...]:
    return (
        -_as_float(row.get("action_divergent_score"), default=-float("inf")),
        -_as_float(row.get("margin_gap"), default=-float("inf")),
        -_as_float(row.get("first_action_distance"), default=-float("inf")),
        _as_float(row.get("visible_distance"), default=float("inf")),
        str(row.get("checkpoint_label", "")),
        str(row.get("target", "")),
        str(row.get("physical_pair_key", "")),
    )


def select_score_balanced_candidates(
    pool: pd.DataFrame,
    *,
    quotas: SourceBalanceQuotas,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Select action-divergent candidates by physical-pair round robin."""

    if pool.empty:
        summary = {
            "candidate_pool_rows": 0,
            "selected_rows": 0,
            "rejected_rows": 0,
            "selected_physical_pairs": 0,
            "selected_left_steps": 0,
            "selected_targets": 0,
            "selected_checkpoints": 0,
            "max_selected_pair_fraction": 0.0,
            "decision": "action_divergent_pool_empty",
            "passed": False,
        }
        return pool.copy(), pool.copy(), summary

    groups: dict[str, list[pd.Series]] = {}
    for key, group in pool.groupby("physical_pair_key", observed=True):
        rows = [row for _, row in group.iterrows()]
        rows.sort(key=_candidate_sort_key)
        groups[str(key)] = rows

    group_order = sorted(groups, key=lambda key: (_candidate_sort_key(groups[key][0]), key))
    offsets = {key: 0 for key in group_order}
    pair_counts: dict[str, int] = {}
    checkpoint_target_counts: dict[str, int] = {}
    selected_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    selected_indices: set[int] = set()
    while len(selected_rows) < int(quotas.max_candidates):
        progressed = False
        for key in group_order:
            rows = groups[key]
            offset = offsets[key]
            while offset < len(rows):
                row = rows[offset]
                offset += 1
                base = row.to_dict()
                checkpoint_target = f"{base.get('checkpoint_label', '')}|{base.get('target', '')}"
                if pair_counts.get(key, 0) >= int(quotas.max_candidates_per_physical_pair):
                    rejected_rows.append({**base, "export_rejection_reason": "physical_pair_candidate_cap"})
                    continue
                if checkpoint_target_counts.get(checkpoint_target, 0) >= int(
                    quotas.max_candidates_per_checkpoint_target
                ):
                    rejected_rows.append({**base, "export_rejection_reason": "checkpoint_target_candidate_cap"})
                    continue
                selected_rows.append({**base, "selected_balance_rank": len(selected_rows)})
                pair_counts[key] = pair_counts.get(key, 0) + 1
                checkpoint_target_counts[checkpoint_target] = checkpoint_target_counts.get(checkpoint_target, 0) + 1
                selected_indices.add(int(base["_candidate_export_index"]))
                progressed = True
                break
            offsets[key] = offset
            if len(selected_rows) >= int(quotas.max_candidates):
                break
        if not progressed:
            break

    for _, row in pool.iterrows():
        index = int(row["_candidate_export_index"])
        if index not in selected_indices:
            rejected_rows.append({**row.to_dict(), "export_rejection_reason": "not_selected"})

    selected = pd.DataFrame(selected_rows)
    rejected = pd.DataFrame(rejected_rows)
    selected_count = int(len(selected))
    max_rows_per_pair = int(selected["physical_pair_key"].value_counts().max()) if selected_count else 0
    max_pair_fraction = float(max_rows_per_pair / max(selected_count, 1)) if selected_count else 0.0
    selected_physical_pairs = int(selected["physical_pair_key"].nunique()) if selected_count else 0
    selected_targets = int(selected["target"].astype(str).nunique()) if selected_count and "target" in selected else 0
    selected_checkpoints = (
        int(selected["checkpoint_label"].astype(str).nunique())
        if selected_count and "checkpoint_label" in selected
        else 0
    )
    selected_left_steps = int(selected["left_step"].nunique()) if selected_count and "left_step" in selected else 0
    passed = bool(
        selected_count > 0
        and selected_physical_pairs >= int(quotas.target_min_physical_pairs)
        and selected_left_steps >= int(quotas.target_min_left_steps)
        and selected_targets >= int(quotas.target_min_targets)
        and max_pair_fraction <= float(quotas.max_rows_per_pair_fraction)
    )
    summary = {
        "candidate_pool_rows": int(len(pool)),
        "selected_rows": selected_count,
        "rejected_rows": int(len(rejected)),
        "selected_physical_pairs": selected_physical_pairs,
        "selected_left_steps": selected_left_steps,
        "selected_targets": selected_targets,
        "selected_checkpoints": selected_checkpoints,
        "max_selected_rows_per_physical_pair": max_rows_per_pair,
        "max_selected_pair_fraction": max_pair_fraction,
        "target_min_physical_pairs": int(quotas.target_min_physical_pairs),
        "target_min_left_steps": int(quotas.target_min_left_steps),
        "target_min_targets": int(quotas.target_min_targets),
        "decision": "action_divergent_candidates_ready" if passed else "action_divergent_candidates_source_limited",
        "passed": passed,
    }
    return selected, rejected, summary


def _csv_fieldnames(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def export_action_divergent_candidates(
    *,
    outcome_csv: Path,
    run_dir: Path,
    quotas: SourceBalanceQuotas,
    min_margin_gap: float = DEFAULT_MIN_MARGIN_GAP,
    min_first_action_distance: float = DEFAULT_MIN_FIRST_ACTION_DISTANCE,
    min_trajectory_distance: float = DEFAULT_MIN_TRAJECTORY_DISTANCE,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
) -> dict[str, Any]:
    """Filter, score, source-balance, and export wrong-history candidates."""

    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(outcome_csv)
    pool = action_divergent_candidate_pool(
        frame,
        min_margin_gap=min_margin_gap,
        min_first_action_distance=min_first_action_distance,
        min_trajectory_distance=min_trajectory_distance,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )
    selected, rejected, selection_summary = select_score_balanced_candidates(pool, quotas=quotas)

    pool_csv = run_dir / "candidate_pool.csv"
    selected_csv = run_dir / "candidate_outcomes.csv"
    rejected_csv = run_dir / "rejected_candidates.csv"
    write_csv_rows(pool_csv, pool.to_dict("records"), fieldnames=_csv_fieldnames(pool))
    write_csv_rows(selected_csv, selected.to_dict("records"), fieldnames=_csv_fieldnames(selected))
    write_csv_rows(rejected_csv, rejected.to_dict("records"), fieldnames=_csv_fieldnames(rejected))

    summary = {
        "run_type": "action_divergent_candidate_export",
        "outcome_csv": outcome_csv,
        "candidate_pool_csv": pool_csv,
        "candidate_outcomes_csv": selected_csv,
        "rejected_candidates_csv": rejected_csv,
        "input_rows": int(len(frame)),
        "wrong_history_rows": int(len(wrong_history_candidate_frame(frame))),
        "filters": {
            "min_margin_gap": float(min_margin_gap),
            "min_first_action_distance": float(min_first_action_distance),
            "min_trajectory_distance": float(min_trajectory_distance),
        },
        "score": (
            "first_action_distance/0.25 + action_trajectory_distance_mean/0.15 "
            "+ max(margin_gap,0)/0.01 + 0.25*target_z_delta - visible_distance/0.25"
        ),
        "selection": selection_summary,
        "replay_started": False,
        "mining_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
        "surface_conversion_started": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome-csv", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--min-margin-gap", type=float, default=DEFAULT_MIN_MARGIN_GAP)
    parser.add_argument("--min-first-action-distance", type=float, default=DEFAULT_MIN_FIRST_ACTION_DISTANCE)
    parser.add_argument("--min-trajectory-distance", type=float, default=DEFAULT_MIN_TRAJECTORY_DISTANCE)
    parser.add_argument("--max-candidates", type=int, default=240)
    parser.add_argument("--max-candidates-per-physical-pair", type=int, default=20)
    parser.add_argument("--max-candidates-per-checkpoint-target", type=int, default=80)
    parser.add_argument("--target-min-physical-pairs", type=int, default=12)
    parser.add_argument("--target-min-left-steps", type=int, default=6)
    parser.add_argument("--target-min-targets", type=int, default=3)
    parser.add_argument("--max-rows-per-pair-fraction", type=float, default=0.15)
    parser.add_argument("--source-obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--source-obstacle-lateral-bucket-width", type=float, default=1.0)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    quotas = SourceBalanceQuotas(
        max_candidates=args.max_candidates,
        max_candidates_per_physical_pair=args.max_candidates_per_physical_pair,
        max_candidates_per_checkpoint_target=args.max_candidates_per_checkpoint_target,
        target_min_physical_pairs=args.target_min_physical_pairs,
        target_min_left_steps=args.target_min_left_steps,
        target_min_targets=args.target_min_targets,
        max_rows_per_pair_fraction=args.max_rows_per_pair_fraction,
    )
    summary = export_action_divergent_candidates(
        outcome_csv=args.outcome_csv,
        run_dir=args.run_dir,
        quotas=quotas,
        min_margin_gap=args.min_margin_gap,
        min_first_action_distance=args.min_first_action_distance,
        min_trajectory_distance=args.min_trajectory_distance,
        distance_bucket_width=args.source_obstacle_distance_bucket_width,
        lateral_bucket_width=args.source_obstacle_lateral_bucket_width,
    )
    print(f"summary_json={args.run_dir / 'summary.json'}")
    print(f"candidate_outcomes_csv={summary['candidate_outcomes_csv']}")
    print(f"decision={summary['selection']['decision']}")
    print(f"passed={summary['selection']['passed']}")


if __name__ == "__main__":
    main()
