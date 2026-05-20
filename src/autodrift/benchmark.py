"""Benchmark runner for comparing policies on shared scenario seeds."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.evaluate import SEGMENT_NAMES, evaluate_policy, load_env_config


def _bucket(output: pd.DataFrame, column: str, target: str, bins: list[float], labels: list[str]) -> None:
    if column in output:
        output[target] = pd.cut(output[column], bins=bins, labels=labels, include_lowest=True)


def add_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    _bucket(output, "mu", "mu_bucket", [0.0, 0.45, 0.80, float("inf")], ["low", "medium", "high"])
    if "initial_mu" in output:
        _bucket(output, "initial_mu", "initial_mu_bucket", [0.0, 0.45, 0.80, float("inf")], ["low", "medium", "high"])
    _bucket(output, "mass_scale", "mass_bucket", [0.0, 0.95, 1.05, float("inf")], ["light", "nominal", "heavy"])
    _bucket(output, "cg_shift", "cg_bucket", [-float("inf"), -0.04, 0.04, float("inf")], ["rear", "nominal", "front"])
    _bucket(output, "brake_scale", "brake_bucket", [0.0, 0.90, 1.05, float("inf")], ["weak", "nominal", "strong"])
    _bucket(output, "tire_stiffness_scale", "tire_bucket", [0.0, 0.85, 1.15, float("inf")], ["weak", "nominal", "strong"])
    _bucket(
        output,
        "steer_tau_scale",
        "steering_tau_bucket",
        [0.0, 0.90, 1.20, float("inf")],
        ["fast", "nominal", "slow"],
    )
    output["success"] = ~output["terminated"]
    return output


def summarize(frame: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(by, observed=True)
    summary = grouped.agg(
        episodes=("seed", "count"),
        return_mean=("return", "mean"),
        success_rate=("success", "mean"),
        termination_rate=("terminated", "mean"),
        lateral_rmse_mean=("lateral_rmse", "mean"),
        lateral_peak_mean=("lateral_peak", "mean"),
        beta_abs_error_mean=("beta_abs_error_mean", "mean"),
        beta_abs_peak_mean=("beta_abs_peak", "mean"),
        high_sideslip_fraction_mean=("high_sideslip_fraction", "mean"),
        speed_mean=("speed_mean", "mean"),
        action_rate_mean=("action_rate_mean", "mean"),
        collision_rate=("collision", "mean"),
        obstacle_completion_rate=("obstacle_completed", "mean"),
        min_obstacle_clearance_mean=("min_obstacle_clearance", "mean"),
        plan_horizon_mean=("plan_horizon", "mean"),
        plan_action_rate_mean=("plan_action_rate_mean", "mean"),
        mu_min=("mu", "min"),
        mu_max=("mu", "max"),
    )
    return summary.reset_index()


def parse_checkpoint_specs(specs: list[str] | None) -> list[tuple[str, Path, str]]:
    parsed: list[tuple[str, Path, str]] = []
    for spec in specs or []:
        if "=" not in spec:
            raise ValueError(f"checkpoint policy spec must be NAME=PATH, got {spec!r}")
        name, raw_path = spec.split("=", 1)
        ablation = "none"
        if "@" in raw_path:
            raw_path, ablation = raw_path.rsplit("@", 1)
        if ablation not in {"none", "zero_action_history", "single_frame_history", "shuffled_history"}:
            raise ValueError(f"unknown checkpoint ablation {ablation!r} in spec {spec!r}")
        name = name.strip()
        if not name:
            raise ValueError(f"checkpoint policy spec has empty name: {spec!r}")
        parsed.append((name, Path(raw_path), ablation))
    return parsed


def build_segment_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, source in frame.iterrows():
        for segment in SEGMENT_NAMES:
            steps = int(source.get(f"{segment}_steps", 0))
            if steps <= 0:
                continue
            rows.append(
                {
                    "policy": source["policy"],
                    "seed": source["seed"],
                    "segment": segment,
                    "steps": steps,
                    "success": bool(source["success"]),
                    "terminated": bool(source["terminated"]),
                    "mu": source["mu"],
                    "initial_mu": source.get("initial_mu", source["mu"]),
                    "mu_bucket": source.get("mu_bucket"),
                    "initial_mu_bucket": source.get("initial_mu_bucket"),
                    "lateral_rmse": source[f"{segment}_lateral_rmse"],
                    "beta_abs_error_mean": source[f"{segment}_beta_abs_error_mean"],
                    "speed_mean": source[f"{segment}_speed_mean"],
                    "reward_mean": source[f"{segment}_reward_mean"],
                }
            )
    return pd.DataFrame(rows)


def summarize_segments(segment_frame: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    if segment_frame.empty:
        return segment_frame
    grouped = segment_frame.groupby(by or ["policy", "segment"], observed=True)
    summary = grouped.agg(
        episodes=("seed", "count"),
        steps_total=("steps", "sum"),
        success_rate=("success", "mean"),
        termination_rate=("terminated", "mean"),
        lateral_rmse_mean=("lateral_rmse", "mean"),
        beta_abs_error_mean=("beta_abs_error_mean", "mean"),
        speed_mean=("speed_mean", "mean"),
        reward_mean=("reward_mean", "mean"),
        mu_min=("mu", "min"),
        mu_max=("mu", "max"),
    )
    return summary.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AutoDrift benchmark sweeps.")
    parser.add_argument(
        "--policies",
        nargs="+",
        default=["heuristic", "random"],
        choices=["heuristic", "random", "aeb", "aes_heuristic", "envelope_aes", "checkpoint"],
    )
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument(
        "--checkpoint-policy",
        action="append",
        default=[],
        help="Additional checkpoint policy in NAME=PATH form. Can be repeated.",
    )
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--env-config", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="benchmark", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    env_config = None
    if args.env_config is not None:
        env_config = load_env_config(args.env_config)
    all_rows = []
    policy_summaries = {}

    for policy in [policy for policy in args.policies if policy != "checkpoint"]:
        rows, summary = evaluate_policy(
            policy_name=policy,
            episodes=args.episodes,
            seed=args.seed,
            checkpoint=args.checkpoint,
            device=args.device,
            env_config=env_config,
        )
        all_rows.extend(rows)
        policy_summaries[policy] = summary
    checkpoint_specs = parse_checkpoint_specs(args.checkpoint_policy)
    if "checkpoint" in args.policies:
        if args.checkpoint is None:
            raise ValueError("--checkpoint is required when --policies includes checkpoint")
        checkpoint_specs.insert(0, ("checkpoint", args.checkpoint, "none"))
    for label, checkpoint_path, ablation in checkpoint_specs:
        rows, summary = evaluate_policy(
            policy_name="checkpoint",
            episodes=args.episodes,
            seed=args.seed,
            checkpoint=checkpoint_path,
            device=args.device,
            env_config=env_config,
            checkpoint_ablation=ablation,
        )
        for row in rows:
            row["policy"] = label
            row["checkpoint_ablation"] = ablation
        summary["policy"] = label
        summary["checkpoint_ablation"] = ablation
        all_rows.extend(rows)
        policy_summaries[label] = summary

    frame = add_buckets(pd.DataFrame(all_rows))
    policy_summary = summarize(frame, ["policy"])
    bucket_summary = summarize(frame, ["policy", "mu_bucket"])
    initial_bucket_summary = summarize(frame, ["policy", "initial_mu_bucket"]) if "initial_mu_bucket" in frame else None
    obstacle_label_summary = (
        summarize(frame[frame["obstacle_enabled"]], ["policy", "obstacle_label"])
        if "obstacle_enabled" in frame and frame["obstacle_enabled"].any()
        else None
    )
    vehicle_road_columns = [
        column
        for column in ["policy", "obstacle_label", "mu_bucket", "mass_bucket", "brake_bucket", "steering_tau_bucket"]
        if column in frame
    ]
    vehicle_road_summary = summarize(frame, vehicle_road_columns) if len(vehicle_road_columns) > 1 else None
    segment_frame = build_segment_frame(frame)
    segment_summary = summarize_segments(segment_frame)
    segment_mu_bucket_summary = summarize_segments(segment_frame, ["policy", "mu_bucket", "segment"])

    episodes_csv = run_dir / "episodes.csv"
    policy_csv = run_dir / "policy_summary.csv"
    bucket_csv = run_dir / "mu_bucket_summary.csv"
    initial_bucket_csv = run_dir / "initial_mu_bucket_summary.csv"
    obstacle_label_csv = run_dir / "obstacle_label_summary.csv"
    vehicle_road_csv = run_dir / "vehicle_road_bucket_summary.csv"
    segment_csv = run_dir / "segment_summary.csv"
    segment_mu_bucket_csv = run_dir / "segment_mu_bucket_summary.csv"
    frame.to_csv(episodes_csv, index=False)
    policy_summary.to_csv(policy_csv, index=False)
    bucket_summary.to_csv(bucket_csv, index=False)
    if initial_bucket_summary is not None:
        initial_bucket_summary.to_csv(initial_bucket_csv, index=False)
    if obstacle_label_summary is not None:
        obstacle_label_summary.to_csv(obstacle_label_csv, index=False)
    if vehicle_road_summary is not None:
        vehicle_road_summary.to_csv(vehicle_road_csv, index=False)
    if not segment_summary.empty:
        segment_summary.to_csv(segment_csv, index=False)
        segment_mu_bucket_summary.to_csv(segment_mu_bucket_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "benchmark",
            "policies": args.policies,
            "checkpoint": args.checkpoint,
            "checkpoint_policies": {
                label: {"path": path, "ablation": ablation} for label, path, ablation in checkpoint_specs
            },
            "episodes": args.episodes,
            "seed": args.seed,
            "device": args.device,
            "env_config": args.env_config,
            "artifacts": {
                "episodes_csv": episodes_csv,
                "policy_summary_csv": policy_csv,
                "mu_bucket_summary_csv": bucket_csv,
                "initial_mu_bucket_summary_csv": initial_bucket_csv if initial_bucket_summary is not None else None,
                "obstacle_label_summary_csv": obstacle_label_csv if obstacle_label_summary is not None else None,
                "vehicle_road_bucket_summary_csv": vehicle_road_csv if vehicle_road_summary is not None else None,
                "segment_summary_csv": segment_csv if not segment_summary.empty else None,
                "segment_mu_bucket_summary_csv": segment_mu_bucket_csv if not segment_summary.empty else None,
            },
            "policy_summaries": policy_summaries,
        },
    )

    print(policy_summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
