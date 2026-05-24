"""Mine label-targeted projected obstacle-boundary proof rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key
from autodrift.natural_wrong_history_action_sensitive_selector import parse_env_config_map
from autodrift.obstacle_boundary_projection_miner import (
    _load_source_pairs,
    parse_float_values,
    projection_bucket_key,
    score_projected_pairs,
)
from autodrift.terminal_boundary_anchor_miner import (
    _counts,
    _finite_float,
    _le_count,
    _max_share,
    pair_action_boundary_score,
)
from autodrift.train_ppo import resolve_device


def parse_label_values(raw: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one projected label is required")
    return values


def build_label_targeted_projection_candidates(
    *,
    source_pairs: pd.DataFrame,
    absolute_longitudinal: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_scales: tuple[float, ...],
    min_longitudinal: float,
    diagnostic_projection_l2_max: float,
    max_projected_candidates: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for source_pair_id, pair in source_pairs.reset_index(drop=True).iterrows():
        source_x = _finite_float(pair.get("left_obstacle_distance"))
        source_y = _finite_float(pair.get("left_obstacle_lateral_offset"), 0.0)
        if not np.isfinite(source_x) or not np.isfinite(source_y):
            continue
        for body_x in absolute_longitudinal:
            projected_x = max(float(min_longitudinal), float(body_x))
            for lateral_delta in lateral_deltas:
                projected_y = source_y + float(lateral_delta)
                dx = projected_x - source_x
                dy = projected_y - source_y
                projection_l2 = float(np.hypot(dx, dy))
                if projection_l2 > float(diagnostic_projection_l2_max):
                    continue
                for half_width_scale in half_width_scales:
                    if half_width_scale <= 0.0:
                        continue
                    row = dict(pair.to_dict())
                    row.update(
                        {
                            "source_pair_id": int(source_pair_id),
                            "proof_surface_type": "label_targeted_obstacle_boundary_projection",
                            "snapshot_relocated": True,
                            "source_obstacle_body_x": source_x,
                            "source_obstacle_body_y": source_y,
                            "projected_obstacle_body_x": projected_x,
                            "projected_obstacle_body_y": projected_y,
                            "projected_obstacle_half_width": float("nan"),
                            "half_width_scale": float(half_width_scale),
                            "projection_dx": dx,
                            "projection_dy": dy,
                            "projection_l2": projection_l2,
                        }
                    )
                    row["projection_family"] = "primary"
                    row["projection_bucket"] = projection_bucket_key(row, l2_width=1.0, lateral_width=0.5)
                    rows.append(row)
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    frame = frame.sort_values(
        [
            "projection_l2",
            "normal_min_clearance_margin",
            "action_trajectory_distance_mean",
            "target_z_delta",
        ],
        ascending=[True, True, False, False],
    )
    if max_projected_candidates > 0:
        frame = frame.head(int(max_projected_candidates)).copy()
    return frame.reset_index(drop=True)


def select_label_targeted_projected_pairs(
    candidates: pd.DataFrame,
    *,
    target_projected_labels: tuple[str, ...],
    candidate_margin_max: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    primary_projection_l2_max: float,
    primary_half_width_delta_abs_max: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_obstacle_bucket: int,
    max_per_projection_bucket: int,
) -> pd.DataFrame:
    if candidates.empty or max_rows == 0:
        return candidates.head(0).copy()
    frame = candidates.copy()
    allowed_labels = {str(label) for label in target_projected_labels}
    frame["target_projected_label_pass"] = frame["projected_obstacle_label"].astype(str).isin(allowed_labels)
    frame["boundary_pass"] = (
        frame["normal_min_clearance_margin"].astype(float) <= float(candidate_margin_max)
    )
    frame["soft_action_pass"] = (
        (frame["first_action_distance"].astype(float) >= float(first_action_threshold))
        | (frame["action_trajectory_distance_mean"].astype(float) >= float(trajectory_mean_threshold))
        | (frame["action_trajectory_distance_max"].astype(float) >= float(trajectory_max_threshold))
    )
    frame["primary_projection"] = (
        (frame["projection_l2"].astype(float) <= float(primary_projection_l2_max))
        & (frame["half_width_delta_abs"].astype(float) <= float(primary_half_width_delta_abs_max))
    )
    eligible = frame[
        frame["target_projected_label_pass"].astype(bool)
        & frame["boundary_pass"].astype(bool)
        & frame["soft_action_pass"].astype(bool)
        & frame["primary_projection"].astype(bool)
    ].copy()
    if eligible.empty:
        return eligible
    eligible["obstacle_bucket"] = [
        source_obstacle_bucket_key(
            {
                **row,
                "left_obstacle_distance": row.get("projected_obstacle_distance"),
                "left_obstacle_lateral_offset": row.get("projected_obstacle_lateral_offset"),
            },
            distance_width=5.0,
            lateral_width=1.0,
        )
        for row in eligible.to_dict(orient="records")
    ]
    eligible["projection_bucket"] = [
        projection_bucket_key(row, l2_width=1.0, lateral_width=0.5)
        for row in eligible.to_dict(orient="records")
    ]
    eligible = eligible.sort_values(
        [
            "pair_action_boundary_score",
            "projection_l2",
            "half_width_delta_abs",
            "normal_min_clearance_margin",
            "action_trajectory_distance_mean",
            "first_action_distance",
            "target_z_delta",
        ],
        ascending=[False, True, True, True, False, False, False],
    )
    selected: list[dict[str, Any]] = []
    counts: dict[str, dict[Any, int]] = {
        "probe_seed": {},
        "left_seed": {},
        "projected_obstacle_label": {},
        "target": {},
        "config": {},
        "obstacle_bucket": {},
        "projection_bucket": {},
    }
    caps = {
        "probe_seed": int(max_per_probe_seed),
        "left_seed": int(max_per_left_seed),
        "projected_obstacle_label": int(max_per_label),
        "target": int(max_per_target),
        "config": int(max_per_config),
        "obstacle_bucket": int(max_per_obstacle_bucket),
        "projection_bucket": int(max_per_projection_bucket),
    }
    for row in eligible.to_dict(orient="records"):
        if len(selected) >= int(max_rows):
            break
        blocked = False
        for key, cap in caps.items():
            if cap <= 0:
                continue
            value = row.get(key)
            if counts[key].get(value, 0) >= cap:
                blocked = True
                break
        if blocked:
            continue
        selected.append(row)
        for key in counts:
            value = row.get(key)
            counts[key][value] = counts[key].get(value, 0) + 1
    return pd.DataFrame(selected, columns=list(eligible.columns))


def summarize_label_targeted_projection(
    *,
    source_pairs: pd.DataFrame,
    projected_pairs: pd.DataFrame,
    scored_pairs: pd.DataFrame,
    targeted_pairs: pd.DataFrame,
    min_pair_count: int,
    min_probe_seed_count: int,
    min_projected_obstacle_label_count: int,
    min_target_count: int,
    min_config_count: int,
    max_single_seed_share: float,
    max_single_projected_label_share: float,
    max_single_config_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
    max_projection_l2_p50: float,
    max_projection_l2_p90: float,
    max_half_width_delta_abs_p90: float,
    min_primary_projection_share: float,
) -> dict[str, Any]:
    pair_count = int(len(targeted_pairs))
    probe_seed_count = int(targeted_pairs["probe_seed"].nunique()) if "probe_seed" in targeted_pairs else 0
    label_count = (
        int(targeted_pairs["projected_obstacle_label"].nunique())
        if "projected_obstacle_label" in targeted_pairs
        else 0
    )
    target_count = int(targeted_pairs["target"].nunique()) if "target" in targeted_pairs else 0
    config_count = int(targeted_pairs["config"].nunique()) if "config" in targeted_pairs else 0
    single_seed_share = _max_share(targeted_pairs, "probe_seed")
    single_label_share = _max_share(targeted_pairs, "projected_obstacle_label")
    single_config_share = _max_share(targeted_pairs, "config")
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
    projection_l2_p50 = (
        float(targeted_pairs["projection_l2"].astype(float).quantile(0.50)) if len(targeted_pairs) else None
    )
    projection_l2_p90 = (
        float(targeted_pairs["projection_l2"].astype(float).quantile(0.90)) if len(targeted_pairs) else None
    )
    half_width_delta_abs_p90 = (
        float(targeted_pairs["half_width_delta_abs"].astype(float).quantile(0.90))
        if len(targeted_pairs)
        else None
    )
    primary_share = (
        float(targeted_pairs["primary_projection"].astype(bool).mean())
        if "primary_projection" in targeted_pairs and len(targeted_pairs)
        else None
    )
    gate_pass = (
        pair_count >= int(min_pair_count)
        and probe_seed_count >= int(min_probe_seed_count)
        and label_count >= int(min_projected_obstacle_label_count)
        and target_count >= int(min_target_count)
        and config_count >= int(min_config_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_projected_label_share)
        and single_config_share <= float(max_single_config_share)
        and rows_le_0_50 >= int(min_margin_le_0_50_rows)
        and rows_le_1_00 >= int(min_margin_le_1_00_rows)
        and trajectory_mean is not None
        and trajectory_mean >= float(min_trajectory_mean)
        and trajectory_p90 is not None
        and trajectory_p90 >= float(min_trajectory_p90)
        and projection_l2_p50 is not None
        and projection_l2_p50 <= float(max_projection_l2_p50)
        and projection_l2_p90 is not None
        and projection_l2_p90 <= float(max_projection_l2_p90)
        and half_width_delta_abs_p90 is not None
        and half_width_delta_abs_p90 <= float(max_half_width_delta_abs_p90)
        and primary_share is not None
        and primary_share >= float(min_primary_projection_share)
    )
    return {
        "run_type": "label_targeted_projection_miner",
        "source_pair_count": int(len(source_pairs)),
        "projected_candidate_count": int(len(projected_pairs)),
        "scored_pair_count": int(len(scored_pairs)),
        "pair_count": pair_count,
        "probe_seed_count": probe_seed_count,
        "projected_obstacle_label_count": label_count,
        "target_count": target_count,
        "config_count": config_count,
        "single_seed_share": single_seed_share,
        "single_projected_label_share": single_label_share,
        "single_config_share": single_config_share,
        "rows_normal_margin_le_0_50": rows_le_0_50,
        "rows_normal_margin_le_1_00": rows_le_1_00,
        "targeted_trajectory_mean": trajectory_mean,
        "targeted_trajectory_p90": trajectory_p90,
        "projection_l2_p50": projection_l2_p50,
        "projection_l2_p90": projection_l2_p90,
        "half_width_delta_abs_p90": half_width_delta_abs_p90,
        "primary_projection_share": primary_share,
        "targeted_by_probe_seed": _counts(targeted_pairs, "probe_seed"),
        "targeted_by_projected_obstacle_label": _counts(targeted_pairs, "projected_obstacle_label"),
        "targeted_by_target": _counts(targeted_pairs, "target"),
        "targeted_by_config": _counts(targeted_pairs, "config"),
        "projection_gate_pass": bool(gate_pass),
        "outcome_gate_admitted": bool(gate_pass),
    }


def run_label_targeted_projection_miner(
    *,
    source_pairs_csv: Path,
    checkpoint_spec: CheckpointSpec,
    env_config_map: dict[str, Path],
    source_margin_max: float,
    max_source_pairs: int,
    absolute_longitudinal: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_scales: tuple[float, ...],
    target_projected_labels: tuple[str, ...],
    min_longitudinal: float,
    primary_projection_l2_max: float,
    diagnostic_projection_l2_max: float,
    primary_half_width_delta_abs_max: float,
    max_projected_candidates: int,
    short_horizon_steps: int,
    candidate_margin_max: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_obstacle_bucket: int,
    max_per_projection_bucket: int,
    min_pair_count: int,
    min_probe_seed_count: int,
    min_projected_obstacle_label_count: int,
    min_target_count: int,
    min_config_count: int,
    max_single_seed_share: float,
    max_single_projected_label_share: float,
    max_single_config_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
    max_projection_l2_p50: float,
    max_projection_l2_p90: float,
    max_half_width_delta_abs_p90: float,
    min_primary_projection_share: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_pairs = _load_source_pairs(
        source_pairs_csv,
        max_source_pairs=max_source_pairs,
        source_margin_max=source_margin_max,
    )
    projected_pairs = build_label_targeted_projection_candidates(
        source_pairs=source_pairs,
        absolute_longitudinal=absolute_longitudinal,
        lateral_deltas=lateral_deltas,
        half_width_scales=half_width_scales,
        min_longitudinal=min_longitudinal,
        diagnostic_projection_l2_max=diagnostic_projection_l2_max,
        max_projected_candidates=max_projected_candidates,
    )
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    scored_rows, invalid_rows = score_projected_pairs(
        projected_pairs=projected_pairs,
        model=model,
        env_config_map=env_config_map,
        response_dim=response_dim,
        horizon_steps=short_horizon_steps,
        candidate_margin_max=candidate_margin_max,
        device=resolved_device,
    )
    scored_pairs = pd.DataFrame(scored_rows)
    if not scored_pairs.empty:
        scored_pairs["pair_action_boundary_score"] = [
            pair_action_boundary_score(row, candidate_margin_max=candidate_margin_max)
            for row in scored_pairs.to_dict(orient="records")
        ]
    targeted_pairs = select_label_targeted_projected_pairs(
        scored_pairs,
        target_projected_labels=target_projected_labels,
        candidate_margin_max=candidate_margin_max,
        first_action_threshold=first_action_threshold,
        trajectory_mean_threshold=trajectory_mean_threshold,
        trajectory_max_threshold=trajectory_max_threshold,
        primary_projection_l2_max=primary_projection_l2_max,
        primary_half_width_delta_abs_max=primary_half_width_delta_abs_max,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_left_seed=max_per_left_seed,
        max_per_label=max_per_label,
        max_per_target=max_per_target,
        max_per_config=max_per_config,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        max_per_projection_bucket=max_per_projection_bucket,
    )
    summary = {
        "checkpoint": {"label": checkpoint_spec.label, "path": checkpoint_spec.path},
        "source_pairs_csv": source_pairs_csv,
        "env_config_map": env_config_map,
        "source_margin_max": float(source_margin_max),
        "max_source_pairs": int(max_source_pairs),
        "absolute_longitudinal": absolute_longitudinal,
        "lateral_deltas": lateral_deltas,
        "half_width_scales": half_width_scales,
        "target_projected_labels": target_projected_labels,
        "min_longitudinal": float(min_longitudinal),
        "primary_projection_l2_max": float(primary_projection_l2_max),
        "diagnostic_projection_l2_max": float(diagnostic_projection_l2_max),
        "primary_half_width_delta_abs_max": float(primary_half_width_delta_abs_max),
        "max_projected_candidates": int(max_projected_candidates),
        "short_horizon_steps": int(short_horizon_steps),
        "candidate_margin_max": float(candidate_margin_max),
        "first_action_threshold": float(first_action_threshold),
        "trajectory_mean_threshold": float(trajectory_mean_threshold),
        "trajectory_max_threshold": float(trajectory_max_threshold),
        **summarize_label_targeted_projection(
            source_pairs=source_pairs,
            projected_pairs=projected_pairs,
            scored_pairs=scored_pairs,
            targeted_pairs=targeted_pairs,
            min_pair_count=min_pair_count,
            min_probe_seed_count=min_probe_seed_count,
            min_projected_obstacle_label_count=min_projected_obstacle_label_count,
            min_target_count=min_target_count,
            min_config_count=min_config_count,
            max_single_seed_share=max_single_seed_share,
            max_single_projected_label_share=max_single_projected_label_share,
            max_single_config_share=max_single_config_share,
            min_margin_le_0_50_rows=min_margin_le_0_50_rows,
            min_margin_le_1_00_rows=min_margin_le_1_00_rows,
            min_trajectory_mean=min_trajectory_mean,
            min_trajectory_p90=min_trajectory_p90,
            max_projection_l2_p50=max_projection_l2_p50,
            max_projection_l2_p90=max_projection_l2_p90,
            max_half_width_delta_abs_p90=max_half_width_delta_abs_p90,
            min_primary_projection_share=min_primary_projection_share,
        ),
        "source_pairs_out_csv": run_dir / "source_pairs.csv",
        "projected_pairs_csv": run_dir / "projected_pairs.csv",
        "scored_pairs_csv": run_dir / "scored_pairs.csv",
        "targeted_pairs_csv": run_dir / "targeted_pairs.csv",
        "invalid_snapshots_csv": run_dir / "invalid_snapshots.csv",
    }
    write_csv_rows(run_dir / "source_pairs.csv", source_pairs.to_dict(orient="records"))
    write_csv_rows(run_dir / "projected_pairs.csv", projected_pairs.to_dict(orient="records"))
    write_csv_rows(run_dir / "scored_pairs.csv", scored_rows)
    write_csv_rows(run_dir / "targeted_pairs.csv", targeted_pairs.to_dict(orient="records"), fieldnames=list(targeted_pairs.columns))
    write_csv_rows(run_dir / "invalid_snapshots.csv", invalid_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine label-targeted projected obstacle-boundary rows.")
    parser.add_argument("--source-pairs-csv", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config-map", action="append", type=parse_env_config_map, required=True)
    parser.add_argument("--source-margin-max", type=float, default=1.0)
    parser.add_argument("--max-source-pairs", type=int, default=600)
    parser.add_argument("--absolute-longitudinal", type=parse_float_values, default=(4.0, 6.0, 8.0, 10.0, 12.0, 14.0))
    parser.add_argument("--lateral-deltas", type=parse_float_values, default=(-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5))
    parser.add_argument("--half-width-scales", type=parse_float_values, default=(0.75, 1.0, 1.25))
    parser.add_argument(
        "--target-projected-labels",
        type=parse_label_values,
        default=("drift_required", "unavoidable", "aeb_feasible", "aes_feasible"),
    )
    parser.add_argument("--min-longitudinal", type=float, default=3.0)
    parser.add_argument("--primary-projection-l2-max", type=float, default=8.0)
    parser.add_argument("--diagnostic-projection-l2-max", type=float, default=12.0)
    parser.add_argument("--primary-half-width-delta-abs-max", type=float, default=0.40)
    parser.add_argument("--max-projected-candidates", type=int, default=9000)
    parser.add_argument("--short-horizon-steps", type=int, default=8)
    parser.add_argument("--candidate-margin-max", type=float, default=2.0)
    parser.add_argument("--first-action-threshold", type=float, default=0.02)
    parser.add_argument("--trajectory-mean-threshold", type=float, default=0.02)
    parser.add_argument("--trajectory-max-threshold", type=float, default=0.05)
    parser.add_argument("--max-rows", type=int, default=360)
    parser.add_argument("--max-per-probe-seed", type=int, default=80)
    parser.add_argument("--max-per-left-seed", type=int, default=8)
    parser.add_argument("--max-per-label", type=int, default=180)
    parser.add_argument("--max-per-target", type=int, default=150)
    parser.add_argument("--max-per-config", type=int, default=190)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=24)
    parser.add_argument("--max-per-projection-bucket", type=int, default=24)
    parser.add_argument("--min-pair-count", type=int, default=240)
    parser.add_argument("--min-probe-seed-count", type=int, default=6)
    parser.add_argument("--min-projected-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-target-count", type=int, default=2)
    parser.add_argument("--min-config-count", type=int, default=2)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-projected-label-share", type=float, default=0.70)
    parser.add_argument("--max-single-config-share", type=float, default=0.70)
    parser.add_argument("--min-margin-le-0-50-rows", type=int, default=40)
    parser.add_argument("--min-margin-le-1-00-rows", type=int, default=100)
    parser.add_argument("--min-trajectory-mean", type=float, default=0.04)
    parser.add_argument("--min-trajectory-p90", type=float, default=0.08)
    parser.add_argument("--max-projection-l2-p50", type=float, default=5.0)
    parser.add_argument("--max-projection-l2-p90", type=float, default=8.0)
    parser.add_argument("--max-half-width-delta-abs-p90", type=float, default=0.40)
    parser.add_argument("--min-primary-projection-share", type=float, default=0.80)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="label_targeted_projection_miner")
    summary = run_label_targeted_projection_miner(
        source_pairs_csv=args.source_pairs_csv,
        checkpoint_spec=args.checkpoint_policy,
        env_config_map=dict(args.env_config_map),
        source_margin_max=args.source_margin_max,
        max_source_pairs=args.max_source_pairs,
        absolute_longitudinal=tuple(args.absolute_longitudinal),
        lateral_deltas=tuple(args.lateral_deltas),
        half_width_scales=tuple(args.half_width_scales),
        target_projected_labels=tuple(args.target_projected_labels),
        min_longitudinal=args.min_longitudinal,
        primary_projection_l2_max=args.primary_projection_l2_max,
        diagnostic_projection_l2_max=args.diagnostic_projection_l2_max,
        primary_half_width_delta_abs_max=args.primary_half_width_delta_abs_max,
        max_projected_candidates=args.max_projected_candidates,
        short_horizon_steps=args.short_horizon_steps,
        candidate_margin_max=args.candidate_margin_max,
        first_action_threshold=args.first_action_threshold,
        trajectory_mean_threshold=args.trajectory_mean_threshold,
        trajectory_max_threshold=args.trajectory_max_threshold,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_left_seed=args.max_per_left_seed,
        max_per_label=args.max_per_label,
        max_per_target=args.max_per_target,
        max_per_config=args.max_per_config,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        max_per_projection_bucket=args.max_per_projection_bucket,
        min_pair_count=args.min_pair_count,
        min_probe_seed_count=args.min_probe_seed_count,
        min_projected_obstacle_label_count=args.min_projected_obstacle_label_count,
        min_target_count=args.min_target_count,
        min_config_count=args.min_config_count,
        max_single_seed_share=args.max_single_seed_share,
        max_single_projected_label_share=args.max_single_projected_label_share,
        max_single_config_share=args.max_single_config_share,
        min_margin_le_0_50_rows=args.min_margin_le_0_50_rows,
        min_margin_le_1_00_rows=args.min_margin_le_1_00_rows,
        min_trajectory_mean=args.min_trajectory_mean,
        min_trajectory_p90=args.min_trajectory_p90,
        max_projection_l2_p50=args.max_projection_l2_p50,
        max_projection_l2_p90=args.max_projection_l2_p90,
        max_half_width_delta_abs_p90=args.max_half_width_delta_abs_p90,
        min_primary_projection_share=args.min_primary_projection_share,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
