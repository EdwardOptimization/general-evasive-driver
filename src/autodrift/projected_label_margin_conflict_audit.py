"""Audit projected-label and terminal-margin overlap for projection proof rows."""

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
from autodrift.label_targeted_projection_miner import (
    build_label_targeted_projection_candidates,
    parse_float_values,
)
from autodrift.natural_wrong_history_action_sensitive_selector import parse_env_config_map
from autodrift.obstacle_boundary_projection_miner import _load_source_pairs, score_projected_pairs
from autodrift.terminal_boundary_anchor_miner import _counts
from autodrift.train_ppo import resolve_device


MARGIN_BUCKETS = (0.5, 1.0, 2.0, 4.0, 8.0, 12.0)


def _soft_action_mask(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series([], dtype=bool)
    return (
        (frame["first_action_distance"].astype(float) >= 0.02)
        | (frame["action_trajectory_distance_mean"].astype(float) >= 0.02)
        | (frame["action_trajectory_distance_max"].astype(float) >= 0.05)
    )


def _margin_mask(frame: pd.DataFrame, margin: float) -> pd.Series:
    if frame.empty:
        return pd.Series([], dtype=bool)
    return frame["normal_min_clearance_margin"].astype(float) <= float(margin)


def build_label_margin_rows(scored_pairs: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if scored_pairs.empty:
        return rows
    soft = _soft_action_mask(scored_pairs)
    for label, group in scored_pairs.groupby("projected_obstacle_label", observed=True):
        group_soft = soft.loc[group.index]
        row: dict[str, Any] = {
            "projected_obstacle_label": str(label),
            "row_count": int(len(group)),
            "probe_seed_count": int(group["probe_seed"].nunique()) if "probe_seed" in group else 0,
            "target_count": int(group["target"].nunique()) if "target" in group else 0,
            "config_count": int(group["config"].nunique()) if "config" in group else 0,
            "normal_margin_min": float(group["normal_min_clearance_margin"].astype(float).min()),
            "normal_margin_p10": float(group["normal_min_clearance_margin"].astype(float).quantile(0.10)),
            "normal_margin_p50": float(group["normal_min_clearance_margin"].astype(float).quantile(0.50)),
            "trajectory_mean": float(group["action_trajectory_distance_mean"].astype(float).mean()),
            "trajectory_p90": float(group["action_trajectory_distance_mean"].astype(float).quantile(0.90)),
            "projection_l2_p50": float(group["projection_l2"].astype(float).quantile(0.50)),
            "projection_l2_p90": float(group["projection_l2"].astype(float).quantile(0.90)),
            "half_width_delta_abs_p90": float(group["half_width_delta_abs"].astype(float).quantile(0.90)),
            "soft_action_count": int(group_soft.sum()),
        }
        for margin in MARGIN_BUCKETS:
            margin_pass = _margin_mask(group, margin)
            row[f"margin_le_{margin:g}_count"] = int(margin_pass.sum())
            row[f"soft_margin_le_{margin:g}_count"] = int((group_soft & margin_pass).sum())
        rows.append(row)
    rows.sort(key=lambda row: (row["normal_margin_min"], row["projected_obstacle_label"]))
    return rows


def build_margin_bucket_rows(scored_pairs: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if scored_pairs.empty:
        return rows
    previous = -float("inf")
    for bucket in MARGIN_BUCKETS:
        bucket_mask = (
            scored_pairs["normal_min_clearance_margin"].astype(float) > previous
        ) & (scored_pairs["normal_min_clearance_margin"].astype(float) <= float(bucket))
        group = scored_pairs[bucket_mask]
        rows.append(
            {
                "margin_bucket": f"({previous:g},{bucket:g}]",
                "row_count": int(len(group)),
                "by_projected_obstacle_label": _counts(group, "projected_obstacle_label"),
                "soft_action_count": int(_soft_action_mask(group).sum()) if len(group) else 0,
                "projection_l2_p50": (
                    float(group["projection_l2"].astype(float).quantile(0.50)) if len(group) else None
                ),
                "half_width_delta_abs_p90": (
                    float(group["half_width_delta_abs"].astype(float).quantile(0.90)) if len(group) else None
                ),
            }
        )
        previous = float(bucket)
    group = scored_pairs[scored_pairs["normal_min_clearance_margin"].astype(float) > previous]
    rows.append(
        {
            "margin_bucket": f"({previous:g},inf)",
            "row_count": int(len(group)),
            "by_projected_obstacle_label": _counts(group, "projected_obstacle_label"),
            "soft_action_count": int(_soft_action_mask(group).sum()) if len(group) else 0,
            "projection_l2_p50": (
                float(group["projection_l2"].astype(float).quantile(0.50)) if len(group) else None
            ),
            "half_width_delta_abs_p90": (
                float(group["half_width_delta_abs"].astype(float).quantile(0.90)) if len(group) else None
            ),
        }
    )
    return rows


def summarize_label_margin_conflict(
    *,
    source_pairs: pd.DataFrame,
    projected_pairs: pd.DataFrame,
    scored_pairs: pd.DataFrame,
    low_margin_threshold: float,
    non_unavoidable_label: str,
) -> dict[str, Any]:
    if scored_pairs.empty:
        non_unavoidable = scored_pairs
    else:
        non_unavoidable = scored_pairs[
            scored_pairs["projected_obstacle_label"].astype(str) != str(non_unavoidable_label)
        ]
    low_non_unavoidable = non_unavoidable[
        non_unavoidable["normal_min_clearance_margin"].astype(float) <= float(low_margin_threshold)
    ] if len(non_unavoidable) else non_unavoidable
    soft_low_non_unavoidable = (
        low_non_unavoidable[_soft_action_mask(low_non_unavoidable)]
        if len(low_non_unavoidable)
        else low_non_unavoidable
    )
    recommended_next_path = (
        "selector_family_from_low_margin_non_unavoidable_rows"
        if len(soft_low_non_unavoidable)
        else "pre_register_proof_scenario_gate_split"
    )
    return {
        "run_type": "projected_label_margin_conflict_audit",
        "source_pair_count": int(len(source_pairs)),
        "projected_candidate_count": int(len(projected_pairs)),
        "scored_pair_count": int(len(scored_pairs)),
        "projected_obstacle_label_count": (
            int(scored_pairs["projected_obstacle_label"].nunique())
            if "projected_obstacle_label" in scored_pairs
            else 0
        ),
        "scored_by_projected_obstacle_label": _counts(scored_pairs, "projected_obstacle_label"),
        "non_unavoidable_row_count": int(len(non_unavoidable)),
        "non_unavoidable_min_normal_margin": (
            float(non_unavoidable["normal_min_clearance_margin"].astype(float).min())
            if len(non_unavoidable)
            else None
        ),
        "low_margin_threshold": float(low_margin_threshold),
        "low_margin_non_unavoidable_count": int(len(low_non_unavoidable)),
        "soft_low_margin_non_unavoidable_count": int(len(soft_low_non_unavoidable)),
        "low_margin_non_unavoidable_exists": bool(len(soft_low_non_unavoidable) > 0),
        "recommended_next_path": recommended_next_path,
        "actor_contract_changed": False,
        "training_or_promotion_performed": False,
    }


def run_label_margin_conflict_audit(
    *,
    source_pairs_csv: Path,
    checkpoint_spec: CheckpointSpec,
    env_config_map: dict[str, Path],
    source_margin_max: float,
    max_source_pairs: int,
    absolute_longitudinal: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_scales: tuple[float, ...],
    min_longitudinal: float,
    diagnostic_projection_l2_max: float,
    max_projected_candidates: int,
    short_horizon_steps: int,
    candidate_margin_max: float,
    low_margin_threshold: float,
    non_unavoidable_label: str,
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
    label_margin_rows = build_label_margin_rows(scored_pairs)
    margin_bucket_rows = build_margin_bucket_rows(scored_pairs)
    if scored_pairs.empty:
        low_non_unavoidable_rows: list[dict[str, Any]] = []
    else:
        low = scored_pairs[
            (scored_pairs["projected_obstacle_label"].astype(str) != str(non_unavoidable_label))
            & (scored_pairs["normal_min_clearance_margin"].astype(float) <= float(low_margin_threshold))
        ].copy()
        low_non_unavoidable_rows = low.to_dict(orient="records")
    summary = {
        "checkpoint": {"label": checkpoint_spec.label, "path": checkpoint_spec.path},
        "source_pairs_csv": source_pairs_csv,
        "env_config_map": env_config_map,
        "source_margin_max": float(source_margin_max),
        "max_source_pairs": int(max_source_pairs),
        "absolute_longitudinal": absolute_longitudinal,
        "lateral_deltas": lateral_deltas,
        "half_width_scales": half_width_scales,
        "min_longitudinal": float(min_longitudinal),
        "diagnostic_projection_l2_max": float(diagnostic_projection_l2_max),
        "max_projected_candidates": int(max_projected_candidates),
        "short_horizon_steps": int(short_horizon_steps),
        "candidate_margin_max": float(candidate_margin_max),
        **summarize_label_margin_conflict(
            source_pairs=source_pairs,
            projected_pairs=projected_pairs,
            scored_pairs=scored_pairs,
            low_margin_threshold=low_margin_threshold,
            non_unavoidable_label=non_unavoidable_label,
        ),
        "source_pairs_out_csv": run_dir / "source_pairs.csv",
        "projected_pairs_csv": run_dir / "projected_pairs.csv",
        "scored_pairs_csv": run_dir / "scored_pairs.csv",
        "label_margin_summary_csv": run_dir / "label_margin_summary.csv",
        "margin_bucket_summary_csv": run_dir / "margin_bucket_summary.csv",
        "low_margin_non_unavoidable_rows_csv": run_dir / "low_margin_non_unavoidable_rows.csv",
        "invalid_snapshots_csv": run_dir / "invalid_snapshots.csv",
    }
    write_csv_rows(run_dir / "source_pairs.csv", source_pairs.to_dict(orient="records"))
    write_csv_rows(run_dir / "projected_pairs.csv", projected_pairs.to_dict(orient="records"))
    write_csv_rows(run_dir / "scored_pairs.csv", scored_rows)
    write_csv_rows(run_dir / "label_margin_summary.csv", label_margin_rows)
    write_csv_rows(run_dir / "margin_bucket_summary.csv", margin_bucket_rows)
    write_csv_rows(run_dir / "low_margin_non_unavoidable_rows.csv", low_non_unavoidable_rows)
    write_csv_rows(run_dir / "invalid_snapshots.csv", invalid_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit projected label and terminal margin overlap.")
    parser.add_argument("--source-pairs-csv", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config-map", action="append", type=parse_env_config_map, required=True)
    parser.add_argument("--source-margin-max", type=float, default=1.0)
    parser.add_argument("--max-source-pairs", type=int, default=180)
    parser.add_argument(
        "--absolute-longitudinal",
        type=parse_float_values,
        default=(3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0),
    )
    parser.add_argument(
        "--lateral-deltas",
        type=parse_float_values,
        default=(-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0),
    )
    parser.add_argument("--half-width-scales", type=parse_float_values, default=(0.5, 0.75, 1.0, 1.25, 1.5))
    parser.add_argument("--min-longitudinal", type=float, default=3.0)
    parser.add_argument("--diagnostic-projection-l2-max", type=float, default=16.0)
    parser.add_argument("--max-projected-candidates", type=int, default=0)
    parser.add_argument("--short-horizon-steps", type=int, default=8)
    parser.add_argument("--candidate-margin-max", type=float, default=2.0)
    parser.add_argument("--low-margin-threshold", type=float, default=2.0)
    parser.add_argument("--non-unavoidable-label", type=str, default="unavoidable")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="projected_label_margin_conflict_audit")
    summary = run_label_margin_conflict_audit(
        source_pairs_csv=args.source_pairs_csv,
        checkpoint_spec=args.checkpoint_policy,
        env_config_map=dict(args.env_config_map),
        source_margin_max=args.source_margin_max,
        max_source_pairs=args.max_source_pairs,
        absolute_longitudinal=tuple(args.absolute_longitudinal),
        lateral_deltas=tuple(args.lateral_deltas),
        half_width_scales=tuple(args.half_width_scales),
        min_longitudinal=args.min_longitudinal,
        diagnostic_projection_l2_max=args.diagnostic_projection_l2_max,
        max_projected_candidates=args.max_projected_candidates,
        short_horizon_steps=args.short_horizon_steps,
        candidate_margin_max=args.candidate_margin_max,
        low_margin_threshold=args.low_margin_threshold,
        non_unavoidable_label=args.non_unavoidable_label,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
