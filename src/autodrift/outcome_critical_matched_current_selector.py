"""Select outcome-critical matched-current rows from intervention artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key


JOIN_KEYS = ["left_seed", "right_seed", "left_step", "right_step", "target"]


def _bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.astype(str).str.lower().isin(("true", "1", "yes"))


def _optional_bool(frame: pd.DataFrame, key: str, default: bool = False) -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=bool)
    return _bool_series(frame[key])


def _optional_float(frame: pd.DataFrame, key: str, default: float = 0.0) -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=float)
    return pd.to_numeric(frame[key], errors="coerce").fillna(default)


def _limited_pair_metadata(pairs: pd.DataFrame, max_pairs_per_checkpoint_target: int) -> pd.DataFrame:
    frame = pairs.copy()
    if max_pairs_per_checkpoint_target > 0:
        selected = []
        for _, group in frame.groupby(["checkpoint_label", "target"], observed=True):
            selected.append(
                group.sort_values(["target_z_delta", "visible_distance"], ascending=[False, True]).head(
                    int(max_pairs_per_checkpoint_target)
                )
            )
        frame = pd.concat(selected, ignore_index=True) if selected else frame.head(0).copy()
    frame = frame.reset_index(drop=True).copy()
    frame["selector_pair_id"] = np.arange(len(frame), dtype=int)
    metadata_columns = [
        "selector_pair_id",
        "checkpoint_label",
        "probe_seed",
        "target",
        "left_seed",
        "right_seed",
        "left_step",
        "right_step",
        "target_z_delta",
        "visible_distance",
        "left_obstacle_label",
        "right_obstacle_label",
        "left_obstacle_distance",
        "right_obstacle_distance",
        "left_obstacle_lateral_offset",
        "right_obstacle_lateral_offset",
    ]
    for column in metadata_columns:
        if column not in frame:
            frame[column] = np.nan
    return frame[metadata_columns]


def build_outcome_critical_candidates(
    *,
    pairs: pd.DataFrame,
    action_rows: pd.DataFrame,
    outcome_rows: pd.DataFrame,
    max_pairs_per_checkpoint_target: int,
    min_margin_gap: float,
    min_action_distance: float,
    max_normal_pair_action_distance: float,
    min_target_z_delta: float,
    max_visible_distance: float | None,
    require_action_prefilter: bool,
) -> pd.DataFrame:
    pair_meta = _limited_pair_metadata(pairs, max_pairs_per_checkpoint_target=max_pairs_per_checkpoint_target)
    variant_rows = outcome_rows[outcome_rows["variant"].astype(str) != "normal"].copy()
    normal_rows = outcome_rows[outcome_rows["variant"].astype(str) == "normal"].copy()
    normal_columns = [*JOIN_KEYS, "collision", "obstacle_completed", "return", "min_clearance_margin"]
    normal = normal_rows[normal_columns].rename(
        columns={
            "collision": "normal_collision_observed",
            "obstacle_completed": "normal_obstacle_completed_observed",
            "return": "normal_return_observed",
            "min_clearance_margin": "normal_margin_observed",
        }
    )
    merged = variant_rows.merge(normal, on=JOIN_KEYS, how="left", validate="many_to_one")
    action_columns = [
        *JOIN_KEYS,
        "variant",
        "normal_pair_action_distance",
        "action_distance",
        "variant_to_right_action_distance",
        "wrong_history_closer_to_right_action",
        "abs_steer_delta",
        "abs_throttle_delta",
        "abs_brake_delta",
    ]
    action_available = [column for column in action_columns if column in action_rows]
    merged = merged.merge(action_rows[action_available], on=[*JOIN_KEYS, "variant"], how="left", validate="many_to_one")
    merged = merged.merge(
        pair_meta,
        on=["checkpoint_label", *JOIN_KEYS],
        how="left",
        validate="many_to_one",
        suffixes=("", "_pair"),
    )
    for column in (
        "selector_pair_id",
        "probe_seed",
        "target_z_delta",
        "visible_distance",
        "left_obstacle_label",
        "right_obstacle_label",
        "left_obstacle_distance",
        "right_obstacle_distance",
        "left_obstacle_lateral_offset",
        "right_obstacle_lateral_offset",
    ):
        pair_column = f"{column}_pair"
        if pair_column in merged:
            merged[column] = merged[pair_column]

    normal_success = _optional_bool(merged, "normal_success")
    variant_success = _optional_bool(merged, "variant_success")
    success_drop = normal_success & ~variant_success
    margin_gap = _optional_float(merged, "margin_gap", default=float("nan"))
    positive_margin_gap = margin_gap >= float(min_margin_gap)

    normal_collision = _optional_bool(merged, "normal_collision_observed")
    variant_collision = _optional_bool(merged, "collision")
    collision_gap = ~normal_collision & variant_collision

    normal_completed = _optional_bool(merged, "normal_obstacle_completed_observed")
    variant_completed = _optional_bool(merged, "obstacle_completed")
    obstacle_completion_drop = normal_completed & ~variant_completed

    normal_return = _optional_float(merged, "normal_return_observed", default=float("nan"))
    variant_return = _optional_float(merged, "return", default=float("nan"))
    merged["return_gap"] = normal_return - variant_return

    action_distance_values = _optional_float(merged, "action_distance")
    normal_pair_action = _optional_float(merged, "normal_pair_action_distance")
    wrong_closer = _optional_bool(merged, "wrong_history_closer_to_right_action")
    action_prefilter = (
        (action_distance_values >= float(min_action_distance))
        & (normal_pair_action <= float(max_normal_pair_action_distance))
    ) | ((merged["variant"].astype(str) == "wrong_matched_history") & wrong_closer)

    target_z = _optional_float(merged, "target_z_delta")
    visible_distance = _optional_float(merged, "visible_distance")
    matched_current_ok = target_z >= float(min_target_z_delta)
    if max_visible_distance is not None:
        matched_current_ok &= visible_distance <= float(max_visible_distance)

    outcome_critical = normal_success & (success_drop | positive_margin_gap | collision_gap | obstacle_completion_drop)
    accepted = matched_current_ok & outcome_critical
    if require_action_prefilter:
        accepted &= action_prefilter

    merged["success_drop"] = success_drop
    merged["positive_margin_gap"] = positive_margin_gap
    merged["collision_gap"] = collision_gap
    merged["obstacle_completion_drop"] = obstacle_completion_drop
    merged["action_prefilter_pass"] = action_prefilter
    merged["matched_current_pass"] = matched_current_ok
    merged["outcome_critical"] = outcome_critical
    merged["action_only"] = matched_current_ok & action_prefilter & ~outcome_critical
    merged["accepted"] = accepted
    merged["positive_margin_gap_clipped"] = np.minimum(np.maximum(margin_gap.fillna(0.0), 0.0), 0.5)
    return merged


def _obstacle_bucket(row: dict[str, Any], distance_width: float, lateral_width: float) -> str:
    return source_obstacle_bucket_key(
        row,
        distance_width=distance_width,
        lateral_width=lateral_width,
    )


def select_compact_outcome_critical_rows(
    candidates: pd.DataFrame,
    *,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_target: int,
    max_per_variant: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
) -> pd.DataFrame:
    accepted = candidates[candidates["accepted"].astype(bool)].copy()
    if accepted.empty or max_rows == 0:
        return accepted.head(0).copy()
    accepted["obstacle_bucket"] = [
        _obstacle_bucket(row, obstacle_distance_bucket_width, obstacle_lateral_bucket_width)
        for row in accepted.to_dict(orient="records")
    ]
    accepted = accepted.sort_values(
        [
            "success_drop",
            "positive_margin_gap_clipped",
            "collision_gap",
            "obstacle_completion_drop",
            "wrong_history_closer_to_right_action",
            "action_distance",
            "target_z_delta",
            "visible_distance",
        ],
        ascending=[False, False, False, False, False, False, False, True],
    )
    selected: list[dict[str, Any]] = []
    seed_counts: dict[int, int] = {}
    target_counts: dict[str, int] = {}
    variant_counts: dict[str, int] = {}
    bucket_counts: dict[str, int] = {}
    for row in accepted.to_dict(orient="records"):
        if max_rows > 0 and len(selected) >= int(max_rows):
            break
        probe_seed = int(row.get("probe_seed", -1))
        target = str(row.get("target", ""))
        variant = str(row.get("variant", ""))
        bucket = str(row.get("obstacle_bucket", ""))
        if max_per_probe_seed > 0 and seed_counts.get(probe_seed, 0) >= int(max_per_probe_seed):
            continue
        if max_per_target > 0 and target_counts.get(target, 0) >= int(max_per_target):
            continue
        if max_per_variant > 0 and variant_counts.get(variant, 0) >= int(max_per_variant):
            continue
        if max_per_obstacle_bucket > 0 and bucket_counts.get(bucket, 0) >= int(max_per_obstacle_bucket):
            continue
        selected.append(row)
        seed_counts[probe_seed] = seed_counts.get(probe_seed, 0) + 1
        target_counts[target] = target_counts.get(target, 0) + 1
        variant_counts[variant] = variant_counts.get(variant, 0) + 1
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    return pd.DataFrame(selected, columns=list(accepted.columns))


def summarize_selection(candidates: pd.DataFrame, compact: pd.DataFrame, *, min_accepted_rows: int) -> dict[str, Any]:
    accepted = candidates[candidates["accepted"].astype(bool)]
    action_only = candidates[candidates["action_only"].astype(bool)]
    labels = compact["left_obstacle_label"].dropna().astype(str).unique().tolist() if "left_obstacle_label" in compact else []
    probe_seeds = compact["probe_seed"].dropna().astype(int).unique().tolist() if "probe_seed" in compact else []
    targets = compact["target"].dropna().astype(str).unique().tolist() if "target" in compact else []
    variants = compact["variant"].dropna().astype(str).unique().tolist() if "variant" in compact else []
    return {
        "candidate_row_count": int(len(candidates)),
        "matched_current_pass_count": int(candidates["matched_current_pass"].astype(bool).sum()),
        "action_prefilter_pass_count": int(candidates["action_prefilter_pass"].astype(bool).sum()),
        "action_only_count": int(len(action_only)),
        "outcome_critical_count": int(candidates["outcome_critical"].astype(bool).sum()),
        "accepted_row_count": int(len(accepted)),
        "compact_row_count": int(len(compact)),
        "compact_probe_seed_count": int(len(probe_seeds)),
        "compact_obstacle_label_count": int(len(labels)),
        "compact_target_count": int(len(targets)),
        "compact_variant_count": int(len(variants)),
        "compact_probe_seeds": probe_seeds,
        "compact_obstacle_labels": labels,
        "compact_targets": targets,
        "compact_variants": variants,
        "selector_pass": bool(len(accepted) >= int(min_accepted_rows) and len(compact) >= int(min_accepted_rows)),
        "accepted_by_variant": {
            str(key): int(value)
            for key, value in accepted.groupby("variant", observed=True).size().to_dict().items()
        },
        "accepted_by_target": {
            str(key): int(value)
            for key, value in accepted.groupby("target", observed=True).size().to_dict().items()
        },
    }


def run_selector(
    *,
    pairs_csv: Path,
    action_interventions_csv: Path,
    outcome_interventions_csv: Path,
    max_pairs_per_checkpoint_target: int,
    min_margin_gap: float,
    min_action_distance: float,
    max_normal_pair_action_distance: float,
    min_target_z_delta: float,
    max_visible_distance: float | None,
    require_action_prefilter: bool,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_target: int,
    max_per_variant: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
    min_accepted_rows: int,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    pairs = pd.read_csv(pairs_csv)
    action_rows = pd.read_csv(action_interventions_csv)
    outcome_rows = pd.read_csv(outcome_interventions_csv)
    candidates = build_outcome_critical_candidates(
        pairs=pairs,
        action_rows=action_rows,
        outcome_rows=outcome_rows,
        max_pairs_per_checkpoint_target=max_pairs_per_checkpoint_target,
        min_margin_gap=min_margin_gap,
        min_action_distance=min_action_distance,
        max_normal_pair_action_distance=max_normal_pair_action_distance,
        min_target_z_delta=min_target_z_delta,
        max_visible_distance=max_visible_distance,
        require_action_prefilter=require_action_prefilter,
    )
    compact = select_compact_outcome_critical_rows(
        candidates,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_target=max_per_target,
        max_per_variant=max_per_variant,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        obstacle_distance_bucket_width=obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=obstacle_lateral_bucket_width,
    )
    write_csv_rows(run_dir / "candidates.csv", candidates.to_dict(orient="records"))
    write_csv_rows(run_dir / "compact_corpus.csv", compact.to_dict(orient="records"))
    selection_summary = summarize_selection(candidates, compact, min_accepted_rows=min_accepted_rows)
    summary = {
        "run_type": "outcome_critical_matched_current_selector",
        "pairs_csv": pairs_csv,
        "action_interventions_csv": action_interventions_csv,
        "outcome_interventions_csv": outcome_interventions_csv,
        "max_pairs_per_checkpoint_target": int(max_pairs_per_checkpoint_target),
        "min_margin_gap": float(min_margin_gap),
        "min_action_distance": float(min_action_distance),
        "max_normal_pair_action_distance": float(max_normal_pair_action_distance),
        "min_target_z_delta": float(min_target_z_delta),
        "max_visible_distance": max_visible_distance,
        "require_action_prefilter": bool(require_action_prefilter),
        "max_rows": int(max_rows),
        "min_accepted_rows": int(min_accepted_rows),
        **selection_summary,
        "candidates_csv": run_dir / "candidates.csv",
        "compact_corpus_csv": run_dir / "compact_corpus.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select outcome-critical matched-current rows.")
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--action-interventions-csv", type=Path, required=True)
    parser.add_argument("--outcome-interventions-csv", type=Path, required=True)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=60)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--min-action-distance", type=float, default=0.05)
    parser.add_argument("--max-normal-pair-action-distance", type=float, default=0.08)
    parser.add_argument("--min-target-z-delta", type=float, default=1.0)
    parser.add_argument("--max-visible-distance", type=float, default=None)
    parser.add_argument("--disable-action-prefilter", action="store_true")
    parser.add_argument("--max-rows", type=int, default=96)
    parser.add_argument("--max-per-probe-seed", type=int, default=16)
    parser.add_argument("--max-per-target", type=int, default=32)
    parser.add_argument("--max-per-variant", type=int, default=32)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=8)
    parser.add_argument("--obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--obstacle-lateral-bucket-width", type=float, default=1.0)
    parser.add_argument("--min-accepted-rows", type=int, default=16)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="outcome_critical_matched_current_selector")
    summary = run_selector(
        pairs_csv=args.pairs_csv,
        action_interventions_csv=args.action_interventions_csv,
        outcome_interventions_csv=args.outcome_interventions_csv,
        max_pairs_per_checkpoint_target=args.max_pairs_per_checkpoint_target,
        min_margin_gap=args.min_margin_gap,
        min_action_distance=args.min_action_distance,
        max_normal_pair_action_distance=args.max_normal_pair_action_distance,
        min_target_z_delta=args.min_target_z_delta,
        max_visible_distance=args.max_visible_distance,
        require_action_prefilter=not args.disable_action_prefilter,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_target=args.max_per_target,
        max_per_variant=args.max_per_variant,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        obstacle_distance_bucket_width=args.obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=args.obstacle_lateral_bucket_width,
        min_accepted_rows=args.min_accepted_rows,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
