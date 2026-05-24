"""Select boundary mechanism projection rows from scored projection audits."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key
from autodrift.obstacle_boundary_projection_miner import projection_bucket_key
from autodrift.terminal_boundary_anchor_miner import _counts, _le_count, _max_share, pair_action_boundary_score


def projected_obstacle_bucket_key(
    row: dict[str, Any],
    *,
    distance_width: float,
    lateral_width: float,
) -> str:
    """Return a geometry bucket for the relocated obstacle position."""

    return source_obstacle_bucket_key(
        {
            **row,
            "left_obstacle_distance": row.get("projected_obstacle_distance"),
            "left_obstacle_lateral_offset": row.get("projected_obstacle_lateral_offset"),
        },
        distance_width=distance_width,
        lateral_width=lateral_width,
    )


def build_boundary_mechanism_candidates(
    scored_pairs: pd.DataFrame,
    *,
    max_normal_margin: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_projection_l2: float,
    max_half_width_delta_abs: float,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
    projection_l2_bucket_width: float,
    projection_lateral_bucket_width: float,
) -> pd.DataFrame:
    if scored_pairs.empty:
        return scored_pairs.copy()
    frame = scored_pairs.copy()
    frame["boundary_pass"] = (
        frame["normal_min_clearance_margin"].astype(float) <= float(max_normal_margin)
    )
    frame["soft_action_pass"] = (
        (frame["first_action_distance"].astype(float) >= float(first_action_threshold))
        | (frame["action_trajectory_distance_mean"].astype(float) >= float(trajectory_mean_threshold))
        | (frame["action_trajectory_distance_max"].astype(float) >= float(trajectory_max_threshold))
    )
    frame["bounded_projection_pass"] = (
        (frame["projection_l2"].astype(float) <= float(max_projection_l2))
        & (frame["half_width_delta_abs"].astype(float) <= float(max_half_width_delta_abs))
    )
    frame["projected_obstacle_bucket"] = [
        projected_obstacle_bucket_key(
            row,
            distance_width=obstacle_distance_bucket_width,
            lateral_width=obstacle_lateral_bucket_width,
        )
        for row in frame.to_dict(orient="records")
    ]
    frame["projection_bucket"] = [
        projection_bucket_key(
            row,
            l2_width=projection_l2_bucket_width,
            lateral_width=projection_lateral_bucket_width,
        )
        for row in frame.to_dict(orient="records")
    ]
    frame["mechanism_score"] = [
        pair_action_boundary_score(row, candidate_margin_max=max_normal_margin)
        for row in frame.to_dict(orient="records")
    ]
    return frame[
        frame["boundary_pass"].astype(bool)
        & frame["soft_action_pass"].astype(bool)
        & frame["bounded_projection_pass"].astype(bool)
    ].copy()


def select_boundary_mechanism_rows(
    candidates: pd.DataFrame,
    *,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_source_pair: int,
    max_per_target: int,
    max_per_config: int,
    max_per_obstacle_bucket: int,
    max_per_projection_bucket: int,
) -> pd.DataFrame:
    if candidates.empty or max_rows == 0:
        return candidates.head(0).copy()
    frame = candidates.copy()
    if "source_pair_id" not in frame:
        frame["source_pair_id"] = np.arange(len(frame), dtype=int)
    frame["_selector_row_id"] = np.arange(len(frame), dtype=int)
    frame = frame.sort_values(
        [
            "mechanism_score",
            "normal_min_clearance_margin",
            "action_trajectory_distance_mean",
            "first_action_distance",
            "projection_l2",
            "half_width_delta_abs",
            "target_z_delta",
        ],
        ascending=[False, True, False, False, True, True, False],
    )
    selected: list[dict[str, Any]] = []
    selected_row_ids: set[Any] = set()
    counts: dict[str, dict[Any, int]] = {
        "probe_seed": {},
        "left_seed": {},
        "source_pair_id": {},
        "target": {},
        "config": {},
        "projected_obstacle_bucket": {},
        "projection_bucket": {},
    }
    caps = {
        "probe_seed": int(max_per_probe_seed),
        "left_seed": int(max_per_left_seed),
        "source_pair_id": int(max_per_source_pair),
        "target": int(max_per_target),
        "config": int(max_per_config),
        "projected_obstacle_bucket": int(max_per_obstacle_bucket),
        "projection_bucket": int(max_per_projection_bucket),
    }

    def add_if_allowed(row: dict[str, Any]) -> bool:
        row_id = row.get("_selector_row_id")
        if row_id in selected_row_ids:
            return False
        if len(selected) >= int(max_rows):
            return False
        for key, cap in caps.items():
            if cap <= 0:
                continue
            value = row.get(key)
            if counts[key].get(value, 0) >= cap:
                return False
        selected.append(row)
        selected_row_ids.add(row_id)
        for key in counts:
            value = row.get(key)
            counts[key][value] = counts[key].get(value, 0) + 1
        return True

    # First cover rare diversity values so high-score braking rows do not consume
    # all caps before small seed/geometry/target groups are represented.
    for key in ("probe_seed", "target", "config", "projected_obstacle_bucket", "projection_bucket"):
        values = list(frame.groupby(key, observed=True).size().sort_values().index)
        for value in values:
            group = frame[frame[key] == value]
            for row in group.to_dict(orient="records"):
                if add_if_allowed(row):
                    break

    for row in frame.to_dict(orient="records"):
        if len(selected) >= int(max_rows):
            break
        add_if_allowed(row)
    return pd.DataFrame(selected, columns=list(frame.columns))


def summarize_boundary_mechanism_selection(
    *,
    scored_pairs: pd.DataFrame,
    candidates: pd.DataFrame,
    targeted_pairs: pd.DataFrame,
    min_pair_count: int,
    min_probe_seed_count: int,
    min_target_count: int,
    min_config_count: int,
    min_projected_obstacle_bucket_count: int,
    min_projection_bucket_count: int,
    max_single_seed_share: float,
    max_single_config_share: float,
    max_single_target_share: float,
    max_single_obstacle_bucket_share: float,
    max_single_projection_bucket_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
) -> dict[str, Any]:
    pair_count = int(len(targeted_pairs))
    probe_seed_count = int(targeted_pairs["probe_seed"].nunique()) if "probe_seed" in targeted_pairs else 0
    target_count = int(targeted_pairs["target"].nunique()) if "target" in targeted_pairs else 0
    config_count = int(targeted_pairs["config"].nunique()) if "config" in targeted_pairs else 0
    obstacle_bucket_count = (
        int(targeted_pairs["projected_obstacle_bucket"].nunique())
        if "projected_obstacle_bucket" in targeted_pairs
        else 0
    )
    projection_bucket_count = (
        int(targeted_pairs["projection_bucket"].nunique()) if "projection_bucket" in targeted_pairs else 0
    )
    single_seed_share = _max_share(targeted_pairs, "probe_seed")
    single_config_share = _max_share(targeted_pairs, "config")
    single_target_share = _max_share(targeted_pairs, "target")
    single_obstacle_bucket_share = _max_share(targeted_pairs, "projected_obstacle_bucket")
    single_projection_bucket_share = _max_share(targeted_pairs, "projection_bucket")
    rows_le_0_50 = _le_count(targeted_pairs, 0.50)
    rows_le_1_00 = _le_count(targeted_pairs, 1.00)
    trajectory_mean = (
        float(targeted_pairs["action_trajectory_distance_mean"].astype(float).mean())
        if len(targeted_pairs)
        else None
    )
    trajectory_p90 = (
        float(targeted_pairs["action_trajectory_distance_mean"].astype(float).quantile(0.90))
        if len(targeted_pairs)
        else None
    )
    gate_pass = (
        pair_count >= int(min_pair_count)
        and probe_seed_count >= int(min_probe_seed_count)
        and target_count >= int(min_target_count)
        and config_count >= int(min_config_count)
        and obstacle_bucket_count >= int(min_projected_obstacle_bucket_count)
        and projection_bucket_count >= int(min_projection_bucket_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_config_share <= float(max_single_config_share)
        and single_target_share <= float(max_single_target_share)
        and single_obstacle_bucket_share <= float(max_single_obstacle_bucket_share)
        and single_projection_bucket_share <= float(max_single_projection_bucket_share)
        and rows_le_0_50 >= int(min_margin_le_0_50_rows)
        and rows_le_1_00 >= int(min_margin_le_1_00_rows)
        and trajectory_mean is not None
        and trajectory_mean >= float(min_trajectory_mean)
        and trajectory_p90 is not None
        and trajectory_p90 >= float(min_trajectory_p90)
    )
    return {
        "run_type": "boundary_mechanism_projection_selector",
        "scored_pair_count": int(len(scored_pairs)),
        "candidate_row_count": int(len(candidates)),
        "targeted_pair_count": pair_count,
        "probe_seed_count": probe_seed_count,
        "target_count": target_count,
        "config_count": config_count,
        "projected_obstacle_bucket_count": obstacle_bucket_count,
        "projection_bucket_count": projection_bucket_count,
        "left_seed_count": int(targeted_pairs["left_seed"].nunique()) if "left_seed" in targeted_pairs else 0,
        "source_pair_id_count": (
            int(targeted_pairs["source_pair_id"].nunique()) if "source_pair_id" in targeted_pairs else 0
        ),
        "single_seed_share": single_seed_share,
        "single_left_seed_share": _max_share(targeted_pairs, "left_seed"),
        "single_source_pair_share": _max_share(targeted_pairs, "source_pair_id"),
        "single_config_share": single_config_share,
        "single_target_share": single_target_share,
        "single_obstacle_bucket_share": single_obstacle_bucket_share,
        "single_projection_bucket_share": single_projection_bucket_share,
        "rows_normal_margin_le_0_50": rows_le_0_50,
        "rows_normal_margin_le_1_00": rows_le_1_00,
        "rows_normal_margin_le_2_00": _le_count(targeted_pairs, 2.00),
        "targeted_trajectory_mean": trajectory_mean,
        "targeted_trajectory_p90": trajectory_p90,
        "targeted_first_action_mean": (
            float(targeted_pairs["first_action_distance"].astype(float).mean()) if len(targeted_pairs) else None
        ),
        "targeted_normal_margin_min": (
            float(targeted_pairs["normal_min_clearance_margin"].astype(float).min()) if len(targeted_pairs) else None
        ),
        "targeted_normal_margin_p50": (
            float(targeted_pairs["normal_min_clearance_margin"].astype(float).quantile(0.50))
            if len(targeted_pairs)
            else None
        ),
        "projection_l2_p50": (
            float(targeted_pairs["projection_l2"].astype(float).quantile(0.50)) if len(targeted_pairs) else None
        ),
        "projection_l2_p90": (
            float(targeted_pairs["projection_l2"].astype(float).quantile(0.90)) if len(targeted_pairs) else None
        ),
        "half_width_delta_abs_p90": (
            float(targeted_pairs["half_width_delta_abs"].astype(float).quantile(0.90))
            if len(targeted_pairs)
            else None
        ),
        "targeted_by_probe_seed": _counts(targeted_pairs, "probe_seed"),
        "targeted_by_target": _counts(targeted_pairs, "target"),
        "targeted_by_config": _counts(targeted_pairs, "config"),
        "targeted_by_projected_obstacle_bucket": _counts(targeted_pairs, "projected_obstacle_bucket"),
        "targeted_by_projection_bucket": _counts(targeted_pairs, "projection_bucket"),
        "targeted_by_projected_obstacle_label": _counts(targeted_pairs, "projected_obstacle_label"),
        "scenario_label_diversity_required": False,
        "mechanism_gate_pass": bool(gate_pass),
        "outcome_gate_admitted": bool(gate_pass),
        "actor_contract_changed": False,
        "training_or_promotion_performed": False,
    }


def run_boundary_mechanism_projection_selector(
    *,
    scored_pairs_csv: Path,
    max_normal_margin: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_projection_l2: float,
    max_half_width_delta_abs: float,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
    projection_l2_bucket_width: float,
    projection_lateral_bucket_width: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_source_pair: int,
    max_per_target: int,
    max_per_config: int,
    max_per_obstacle_bucket: int,
    max_per_projection_bucket: int,
    min_pair_count: int,
    min_probe_seed_count: int,
    min_target_count: int,
    min_config_count: int,
    min_projected_obstacle_bucket_count: int,
    min_projection_bucket_count: int,
    max_single_seed_share: float,
    max_single_config_share: float,
    max_single_target_share: float,
    max_single_obstacle_bucket_share: float,
    max_single_projection_bucket_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scored_pairs = pd.read_csv(scored_pairs_csv)
    candidates = build_boundary_mechanism_candidates(
        scored_pairs,
        max_normal_margin=max_normal_margin,
        first_action_threshold=first_action_threshold,
        trajectory_mean_threshold=trajectory_mean_threshold,
        trajectory_max_threshold=trajectory_max_threshold,
        max_projection_l2=max_projection_l2,
        max_half_width_delta_abs=max_half_width_delta_abs,
        obstacle_distance_bucket_width=obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=obstacle_lateral_bucket_width,
        projection_l2_bucket_width=projection_l2_bucket_width,
        projection_lateral_bucket_width=projection_lateral_bucket_width,
    )
    targeted_pairs = select_boundary_mechanism_rows(
        candidates,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_left_seed=max_per_left_seed,
        max_per_source_pair=max_per_source_pair,
        max_per_target=max_per_target,
        max_per_config=max_per_config,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        max_per_projection_bucket=max_per_projection_bucket,
    )
    summary = {
        "scored_pairs_csv": scored_pairs_csv,
        "max_normal_margin": float(max_normal_margin),
        "first_action_threshold": float(first_action_threshold),
        "trajectory_mean_threshold": float(trajectory_mean_threshold),
        "trajectory_max_threshold": float(trajectory_max_threshold),
        "max_projection_l2": float(max_projection_l2),
        "max_half_width_delta_abs": float(max_half_width_delta_abs),
        "max_rows": int(max_rows),
        **summarize_boundary_mechanism_selection(
            scored_pairs=scored_pairs,
            candidates=candidates,
            targeted_pairs=targeted_pairs,
            min_pair_count=min_pair_count,
            min_probe_seed_count=min_probe_seed_count,
            min_target_count=min_target_count,
            min_config_count=min_config_count,
            min_projected_obstacle_bucket_count=min_projected_obstacle_bucket_count,
            min_projection_bucket_count=min_projection_bucket_count,
            max_single_seed_share=max_single_seed_share,
            max_single_config_share=max_single_config_share,
            max_single_target_share=max_single_target_share,
            max_single_obstacle_bucket_share=max_single_obstacle_bucket_share,
            max_single_projection_bucket_share=max_single_projection_bucket_share,
            min_margin_le_0_50_rows=min_margin_le_0_50_rows,
            min_margin_le_1_00_rows=min_margin_le_1_00_rows,
            min_trajectory_mean=min_trajectory_mean,
            min_trajectory_p90=min_trajectory_p90,
        ),
        "candidates_csv": run_dir / "boundary_mechanism_candidates.csv",
        "targeted_pairs_csv": run_dir / "targeted_pairs.csv",
    }
    write_csv_rows(run_dir / "boundary_mechanism_candidates.csv", candidates.to_dict(orient="records"))
    write_csv_rows(
        run_dir / "targeted_pairs.csv",
        targeted_pairs.to_dict(orient="records"),
        fieldnames=list(targeted_pairs.columns),
    )
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select boundary mechanism projection proof rows.")
    parser.add_argument("--scored-pairs-csv", type=Path, required=True)
    parser.add_argument("--max-normal-margin", type=float, default=2.0)
    parser.add_argument("--first-action-threshold", type=float, default=0.02)
    parser.add_argument("--trajectory-mean-threshold", type=float, default=0.02)
    parser.add_argument("--trajectory-max-threshold", type=float, default=0.05)
    parser.add_argument("--max-projection-l2", type=float, default=6.0)
    parser.add_argument("--max-half-width-delta-abs", type=float, default=0.8)
    parser.add_argument("--obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--obstacle-lateral-bucket-width", type=float, default=1.0)
    parser.add_argument("--projection-l2-bucket-width", type=float, default=1.0)
    parser.add_argument("--projection-lateral-bucket-width", type=float, default=0.5)
    parser.add_argument("--max-rows", type=int, default=360)
    parser.add_argument("--max-per-probe-seed", type=int, default=80)
    parser.add_argument("--max-per-left-seed", type=int, default=0)
    parser.add_argument("--max-per-source-pair", type=int, default=0)
    parser.add_argument("--max-per-target", type=int, default=130)
    parser.add_argument("--max-per-config", type=int, default=190)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=70)
    parser.add_argument("--max-per-projection-bucket", type=int, default=70)
    parser.add_argument("--min-pair-count", type=int, default=240)
    parser.add_argument("--min-probe-seed-count", type=int, default=6)
    parser.add_argument("--min-target-count", type=int, default=2)
    parser.add_argument("--min-config-count", type=int, default=2)
    parser.add_argument("--min-projected-obstacle-bucket-count", type=int, default=8)
    parser.add_argument("--min-projection-bucket-count", type=int, default=8)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-config-share", type=float, default=0.70)
    parser.add_argument("--max-single-target-share", type=float, default=0.70)
    parser.add_argument("--max-single-obstacle-bucket-share", type=float, default=0.35)
    parser.add_argument("--max-single-projection-bucket-share", type=float, default=0.35)
    parser.add_argument("--min-margin-le-0-50-rows", type=int, default=40)
    parser.add_argument("--min-margin-le-1-00-rows", type=int, default=100)
    parser.add_argument("--min-trajectory-mean", type=float, default=0.04)
    parser.add_argument("--min-trajectory-p90", type=float, default=0.08)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_mechanism_projection_selector")
    summary = run_boundary_mechanism_projection_selector(
        scored_pairs_csv=args.scored_pairs_csv,
        max_normal_margin=args.max_normal_margin,
        first_action_threshold=args.first_action_threshold,
        trajectory_mean_threshold=args.trajectory_mean_threshold,
        trajectory_max_threshold=args.trajectory_max_threshold,
        max_projection_l2=args.max_projection_l2,
        max_half_width_delta_abs=args.max_half_width_delta_abs,
        obstacle_distance_bucket_width=args.obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=args.obstacle_lateral_bucket_width,
        projection_l2_bucket_width=args.projection_l2_bucket_width,
        projection_lateral_bucket_width=args.projection_lateral_bucket_width,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_left_seed=args.max_per_left_seed,
        max_per_source_pair=args.max_per_source_pair,
        max_per_target=args.max_per_target,
        max_per_config=args.max_per_config,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        max_per_projection_bucket=args.max_per_projection_bucket,
        min_pair_count=args.min_pair_count,
        min_probe_seed_count=args.min_probe_seed_count,
        min_target_count=args.min_target_count,
        min_config_count=args.min_config_count,
        min_projected_obstacle_bucket_count=args.min_projected_obstacle_bucket_count,
        min_projection_bucket_count=args.min_projection_bucket_count,
        max_single_seed_share=args.max_single_seed_share,
        max_single_config_share=args.max_single_config_share,
        max_single_target_share=args.max_single_target_share,
        max_single_obstacle_bucket_share=args.max_single_obstacle_bucket_share,
        max_single_projection_bucket_share=args.max_single_projection_bucket_share,
        min_margin_le_0_50_rows=args.min_margin_le_0_50_rows,
        min_margin_le_1_00_rows=args.min_margin_le_1_00_rows,
        min_trajectory_mean=args.min_trajectory_mean,
        min_trajectory_p90=args.min_trajectory_p90,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
