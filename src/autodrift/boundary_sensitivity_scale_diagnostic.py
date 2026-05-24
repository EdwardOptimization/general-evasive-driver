"""Run a no-training boundary sensitivity window/scale diagnostic."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import run_fresh_trajectory_boundary_sampler
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config
from autodrift.train_ppo import resolve_device


@dataclass(frozen=True)
class ScaleSpec:
    name: str
    steer: float
    throttle: float
    brake: float
    scale_class: str


def parse_scale(raw: str) -> ScaleSpec:
    if "=" not in str(raw):
        raise argparse.ArgumentTypeError(f"scale must be NAME=STEER,THROTTLE,BRAKE, got {raw!r}")
    name, values = str(raw).split("=", 1)
    name = name.strip()
    parts = [part.strip() for part in values.split(",") if part.strip()]
    if not name or len(parts) != 3:
        raise argparse.ArgumentTypeError(f"scale must be NAME=STEER,THROTTLE,BRAKE, got {raw!r}")
    steer, throttle, brake = (float(part) for part in parts)
    if name in {"local", "plausible"}:
        scale_class = "plausible"
    elif name == "stress":
        scale_class = "stress"
    else:
        scale_class = "unrealistic"
    return ScaleSpec(
        name=name,
        steer=abs(float(steer)),
        throttle=abs(float(throttle)),
        brake=abs(float(brake)),
        scale_class=scale_class,
    )


def deltas_for_scale(max_abs: float) -> tuple[float, ...]:
    value = abs(float(max_abs))
    if value == 0.0:
        return (0.0,)
    half = 0.5 * value
    return (-value, -half, half, value)


def slug_float(value: float) -> str:
    prefix = "m" if float(value) < 0.0 else ""
    text = f"{abs(float(value)):.2f}".rstrip("0").rstrip(".")
    return prefix + text.replace(".", "p")


def variant_id(
    *,
    target_obstacle_distance: float,
    max_prepass_margin: float,
    scale: ScaleSpec,
) -> str:
    return (
        f"target_{slug_float(target_obstacle_distance)}"
        f"_margin_{slug_float(max_prepass_margin)}"
        f"_scale_{scale.name}"
    )


def classify_scale_diagnostic(variant_rows: list[dict[str, Any]]) -> str:
    if not variant_rows:
        return "implementation_failed"
    frame = pd.DataFrame(variant_rows)
    accepted = frame["accepted_rows"].astype(int) if "accepted_rows" in frame.columns else pd.Series(dtype=int)
    positive = frame["result_class"].astype(str).eq("fresh_source_positive")
    plausible_positive = positive & frame["scale_class"].astype(str).eq("plausible")
    if bool(plausible_positive.any()):
        return "scale_positive_plausible"
    stress_positive = positive & frame["scale_class"].astype(str).eq("stress")
    if bool(stress_positive.any()):
        return "scale_positive_stress_only"
    unrealistic_positive = positive & frame["scale_class"].astype(str).eq("unrealistic")
    if bool(unrealistic_positive.any()):
        return "scale_positive_unrealistic_only"
    if int(accepted.sum()) <= 0:
        classes = set(frame["result_class"].astype(str))
        if classes and classes.issubset({"normal_failed_only", "too_safe_only"}):
            return "windowing_failure"
        return "scale_empty"
    plausible_accepted = frame[frame["scale_class"].astype(str).eq("plausible")]["accepted_rows"].astype(int).sum()
    stress_accepted = frame[frame["scale_class"].astype(str).eq("stress")]["accepted_rows"].astype(int).sum()
    if int(plausible_accepted) > 0:
        return "scale_sparse_plausible"
    if int(stress_accepted) > 0:
        return "scale_sparse_stress_only"
    return "scale_sparse_unrealistic_only"


def _load_rows(path: Path, *, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    rows = frame.to_dict(orient="records")
    for row in rows:
        row.update(variant)
    return rows


def summarize_group(frame: pd.DataFrame, group_fields: list[str]) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(group_fields, observed=True):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = {field: value for field, value in zip(group_fields, key_tuple, strict=True)}
        row.update(
            {
                "variants": int(len(group)),
                "accepted_rows": int(group["accepted_rows"].astype(int).sum()),
                "trajectory_boundary_rows": int(group["trajectory_boundary_rows"].astype(int).sum()),
                "history_action_critical_rows": int(group["history_action_critical_rows"].astype(int).sum()),
                "perturbation_evaluated_rows": int(group["perturbation_evaluated_rows"].astype(int).sum()),
                "normal_failed_rejected": int(group["normal_failed_rejected"].astype(int).sum()),
                "too_safe_rejected": int(group["too_safe_rejected"].astype(int).sum()),
                "best_margin_sensitivity_p95": float(group["margin_sensitivity_p95"].astype(float).max()),
                "best_risk_sensitivity_p95": float(group["risk_sensitivity_p95"].astype(float).max()),
                "result_classes": ";".join(sorted(set(group["result_class"].astype(str)))),
            }
        )
        rows.append(row)
    return rows


def first_scale_with_rows(variant_rows: list[dict[str, Any]], allowed_classes: set[str] | None = None) -> str:
    if not variant_rows:
        return ""
    frame = pd.DataFrame(variant_rows)
    if allowed_classes is not None:
        frame = frame[frame["scale_class"].astype(str).isin(allowed_classes)]
    frame = frame[frame["accepted_rows"].astype(int) > 0]
    if frame.empty:
        return ""
    priority = {"local": 0, "plausible": 1, "stress": 2, "unrealistic_probe": 3}
    ordered = frame.assign(_priority=frame["scale_name"].astype(str).map(lambda name: priority.get(name, 99)))
    ordered = ordered.sort_values(["_priority", "target_obstacle_distance", "max_prepass_margin"])
    return str(ordered.iloc[0]["variant_id"])


def run_boundary_sensitivity_scale_diagnostic(
    *,
    checkpoint_path: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    seed_start: int,
    seed_count: int,
    target_obstacle_distances: tuple[float, ...],
    max_prepass_margins: tuple[float, ...],
    scales: tuple[ScaleSpec, ...],
    min_step: int,
    max_step: int,
    snapshot_stride: int,
    max_snapshots_per_episode: int,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
    terminal_cliff_margin: float,
    near_boundary_margin: float,
    min_margin_sensitivity: float,
    min_risk_sensitivity: float,
    min_history_margin_gap: float,
    min_history_risk_gap: float,
    max_continuation_steps: int,
    heldout_fraction: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    # Resolve early so invalid devices fail before partial variant directories are created.
    resolve_device(device)
    variant_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    actor_changed = False

    variant_index = 0
    for target in target_obstacle_distances:
        for max_margin in max_prepass_margins:
            for scale in scales:
                current_variant_id = variant_id(
                    target_obstacle_distance=float(target),
                    max_prepass_margin=float(max_margin),
                    scale=scale,
                )
                subdir = run_dir / current_variant_id
                summary = run_fresh_trajectory_boundary_sampler(
                    checkpoint_path=checkpoint_path,
                    surface_configs=surface_configs,
                    seed_start=seed_start,
                    seed_count=seed_count,
                    min_step=min_step,
                    max_step=max_step,
                    snapshot_stride=snapshot_stride,
                    max_snapshots_per_episode=max_snapshots_per_episode,
                    target_obstacle_distance=float(target),
                    obstacle_longitudinal_min=obstacle_longitudinal_min,
                    obstacle_longitudinal_max=obstacle_longitudinal_max,
                    steer_deltas=deltas_for_scale(scale.steer),
                    throttle_deltas=deltas_for_scale(scale.throttle),
                    brake_deltas=deltas_for_scale(scale.brake),
                    terminal_cliff_margin=terminal_cliff_margin,
                    near_boundary_margin=near_boundary_margin,
                    max_prepass_margin=float(max_margin),
                    min_margin_sensitivity=min_margin_sensitivity,
                    min_risk_sensitivity=min_risk_sensitivity,
                    min_history_margin_gap=min_history_margin_gap,
                    min_history_risk_gap=min_history_risk_gap,
                    max_continuation_steps=max_continuation_steps,
                    heldout_fraction=heldout_fraction,
                    max_vx_gap=1.0,
                    max_vy_gap=0.8,
                    max_yaw_rate_gap=0.25,
                    max_obstacle_x_gap=8.0,
                    max_obstacle_y_gap=1.0,
                    max_match_step_gap=8,
                    min_accepted_rows=80,
                    min_trajectory_rows=50,
                    min_history_rows=20,
                    min_unique_seeds=30,
                    min_unique_step_buckets=4,
                    min_unique_distance_buckets=4,
                    max_seed_dominance=0.08,
                    max_bucket_dominance=0.25,
                    device=device,
                    run_dir=subdir,
                )
                actor_changed = actor_changed or bool(summary.get("actor_parameters_changed", False))
                variant_meta = {
                    "variant_id": current_variant_id,
                    "variant_index": int(variant_index),
                    "target_obstacle_distance": float(target),
                    "max_prepass_margin": float(max_margin),
                    "scale_name": scale.name,
                    "scale_class": scale.scale_class,
                    "scale_steer": float(scale.steer),
                    "scale_throttle": float(scale.throttle),
                    "scale_brake": float(scale.brake),
                }
                variant_row = {
                    **variant_meta,
                    "run_dir": str(subdir),
                    "result_class": str(summary.get("result_class", "")),
                    "episodes_attempted": int(summary.get("episodes_attempted", 0)),
                    "snapshots_collected": int(summary.get("snapshots_collected", 0)),
                    "prepass_rows": int(summary.get("prepass_rows", 0)),
                    "normal_failed_rejected": int(summary.get("normal_failed_rejected", 0)),
                    "too_safe_rejected": int(summary.get("too_safe_rejected", 0)),
                    "perturbation_evaluated_rows": int(summary.get("perturbation_evaluated_rows", 0)),
                    "accepted_rows": int(summary.get("accepted_rows", 0)),
                    "trajectory_boundary_rows": int(summary.get("trajectory_boundary_rows", 0)),
                    "history_action_critical_rows": int(summary.get("history_action_critical_rows", 0)),
                    "margin_sensitivity_mean": float(summary.get("margin_sensitivity_mean") or 0.0),
                    "margin_sensitivity_p95": float(summary.get("margin_sensitivity_p95") or 0.0),
                    "risk_sensitivity_mean": float(summary.get("risk_sensitivity_mean") or 0.0),
                    "risk_sensitivity_p95": float(summary.get("risk_sensitivity_p95") or 0.0),
                    "success_flip_count": int(summary.get("success_flip_count", 0)),
                    "collision_flip_count": int(summary.get("collision_flip_count", 0)),
                    "fresh_source_positive": bool(summary.get("fresh_source_positive", False)),
                }
                variant_rows.append(variant_row)
                accepted_rows.extend(_load_rows(subdir / "accepted_rows.csv", variant=variant_meta))
                rejected_rows.extend(_load_rows(subdir / "rejected_rows.csv", variant=variant_meta))
                variant_index += 1

    variant_frame = pd.DataFrame(variant_rows)
    result_class = classify_scale_diagnostic(variant_rows)
    scale_summary = summarize_group(variant_frame, ["scale_name", "scale_class"])
    window_summary = summarize_group(variant_frame, ["target_obstacle_distance", "max_prepass_margin"])
    plausible_frame = (
        variant_frame[variant_frame["scale_class"].astype(str).eq("plausible")] if not variant_frame.empty else pd.DataFrame()
    )
    stress_frame = (
        variant_frame[variant_frame["scale_class"].astype(str).eq("stress")] if not variant_frame.empty else pd.DataFrame()
    )
    unrealistic_frame = (
        variant_frame[variant_frame["scale_class"].astype(str).eq("unrealistic")] if not variant_frame.empty else pd.DataFrame()
    )
    summary = {
        "run_type": "boundary_sensitivity_scale_diagnostic",
        "checkpoint": checkpoint_path,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "target_obstacle_distances": target_obstacle_distances,
        "max_prepass_margins": max_prepass_margins,
        "scales": [
            {
                "name": scale.name,
                "scale_class": scale.scale_class,
                "steer": scale.steer,
                "throttle": scale.throttle,
                "brake": scale.brake,
            }
            for scale in scales
        ],
        "variant_count": int(len(variant_rows)),
        "episodes_attempted": int(variant_frame["episodes_attempted"].astype(int).sum()) if not variant_frame.empty else 0,
        "snapshots_collected": int(variant_frame["snapshots_collected"].astype(int).sum()) if not variant_frame.empty else 0,
        "perturbation_evaluated_rows": int(variant_frame["perturbation_evaluated_rows"].astype(int).sum()) if not variant_frame.empty else 0,
        "accepted_rows": int(variant_frame["accepted_rows"].astype(int).sum()) if not variant_frame.empty else 0,
        "best_variant_accepted_rows": int(variant_frame["accepted_rows"].astype(int).max()) if not variant_frame.empty else 0,
        "best_margin_sensitivity_p95": float(variant_frame["margin_sensitivity_p95"].astype(float).max()) if not variant_frame.empty else float("nan"),
        "best_risk_sensitivity_p95": float(variant_frame["risk_sensitivity_p95"].astype(float).max()) if not variant_frame.empty else float("nan"),
        "first_scale_with_any_accepted_rows": first_scale_with_rows(variant_rows),
        "first_plausible_scale_with_any_accepted_rows": first_scale_with_rows(variant_rows, {"plausible"}),
        "plausible_accepted_rows": (
            int(plausible_frame["accepted_rows"].astype(int).sum()) if not plausible_frame.empty else 0
        ),
        "stress_accepted_rows": int(stress_frame["accepted_rows"].astype(int).sum()) if not stress_frame.empty else 0,
        "unrealistic_accepted_rows": (
            int(unrealistic_frame["accepted_rows"].astype(int).sum()) if not unrealistic_frame.empty else 0
        ),
        "plausible_source_positive_variants": (
            int(plausible_frame["result_class"].astype(str).eq("fresh_source_positive").sum())
            if not plausible_frame.empty
            else 0
        ),
        "stress_source_positive_variants": (
            int(stress_frame["result_class"].astype(str).eq("fresh_source_positive").sum()) if not stress_frame.empty else 0
        ),
        "unrealistic_source_positive_variants": (
            int(unrealistic_frame["result_class"].astype(str).eq("fresh_source_positive").sum())
            if not unrealistic_frame.empty
            else 0
        ),
        "best_plausible_accepted_rows": (
            int(plausible_frame["accepted_rows"].astype(int).max())
            if not plausible_frame.empty
            else 0
        ),
        "best_stress_accepted_rows": (
            int(stress_frame["accepted_rows"].astype(int).max())
            if not stress_frame.empty
            else 0
        ),
        "best_unrealistic_accepted_rows": (
            int(unrealistic_frame["accepted_rows"].astype(int).max())
            if not unrealistic_frame.empty
            else 0
        ),
        "actor_parameters_changed": bool(actor_changed),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "scale_positive_plausible": bool(result_class == "scale_positive_plausible"),
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "scale_summary_csv": run_dir / "scale_summary.csv",
        "window_summary_csv": run_dir / "window_summary.csv",
        "accepted_rows_csv": run_dir / "accepted_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_csv_rows(run_dir / "variant_summary.csv", variant_rows)
    write_csv_rows(run_dir / "scale_summary.csv", scale_summary)
    write_csv_rows(run_dir / "window_summary.csv", window_summary)
    write_csv_rows(run_dir / "accepted_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run boundary sensitivity scale diagnostic.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--seed-start", type=int, default=30000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--target-obstacle-distance", type=float, action="append", required=True)
    parser.add_argument("--max-prepass-margin", type=float, action="append", required=True)
    parser.add_argument("--scale", type=parse_scale, action="append", required=True)
    parser.add_argument("--min-step", type=int, default=10)
    parser.add_argument("--max-step", type=int, default=0)
    parser.add_argument("--snapshot-stride", type=int, default=3)
    parser.add_argument("--max-snapshots-per-episode", type=int, default=8)
    parser.add_argument("--obstacle-longitudinal-min", type=float, default=-5.0)
    parser.add_argument("--obstacle-longitudinal-max", type=float, default=80.0)
    parser.add_argument("--terminal-cliff-margin", type=float, default=0.02)
    parser.add_argument("--near-boundary-margin", type=float, default=0.15)
    parser.add_argument("--min-margin-sensitivity", type=float, default=0.02)
    parser.add_argument("--min-risk-sensitivity", type=float, default=0.02)
    parser.add_argument("--min-history-margin-gap", type=float, default=0.01)
    parser.add_argument("--min-history-risk-gap", type=float, default=0.01)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--heldout-fraction", type=float, default=0.2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_sensitivity_scale_diagnostic")
    summary = run_boundary_sensitivity_scale_diagnostic(
        checkpoint_path=args.checkpoint,
        surface_configs=tuple(args.surface_config),
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        target_obstacle_distances=tuple(float(item) for item in args.target_obstacle_distance),
        max_prepass_margins=tuple(float(item) for item in args.max_prepass_margin),
        scales=tuple(args.scale),
        min_step=args.min_step,
        max_step=args.max_step,
        snapshot_stride=args.snapshot_stride,
        max_snapshots_per_episode=args.max_snapshots_per_episode,
        obstacle_longitudinal_min=args.obstacle_longitudinal_min,
        obstacle_longitudinal_max=args.obstacle_longitudinal_max,
        terminal_cliff_margin=args.terminal_cliff_margin,
        near_boundary_margin=args.near_boundary_margin,
        min_margin_sensitivity=args.min_margin_sensitivity,
        min_risk_sensitivity=args.min_risk_sensitivity,
        min_history_margin_gap=args.min_history_margin_gap,
        min_history_risk_gap=args.min_history_risk_gap,
        max_continuation_steps=args.max_continuation_steps,
        heldout_fraction=args.heldout_fraction,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
