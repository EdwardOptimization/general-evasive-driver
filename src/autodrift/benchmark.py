"""Benchmark runner for comparing policies on shared scenario seeds."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.evaluate import SEGMENT_NAMES, evaluate_policy, load_env_config


def add_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["mu_bucket"] = pd.cut(
        output["mu"],
        bins=[0.0, 0.45, 0.80, float("inf")],
        labels=["low", "medium", "high"],
        include_lowest=True,
    )
    if "initial_mu" in output:
        output["initial_mu_bucket"] = pd.cut(
            output["initial_mu"],
            bins=[0.0, 0.45, 0.80, float("inf")],
            labels=["low", "medium", "high"],
            include_lowest=True,
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
        speed_mean=("speed_mean", "mean"),
        collision_rate=("collision", "mean"),
        obstacle_completion_rate=("obstacle_completed", "mean"),
        min_obstacle_clearance_mean=("min_obstacle_clearance", "mean"),
        mu_min=("mu", "min"),
        mu_max=("mu", "max"),
    )
    return summary.reset_index()


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

    for policy in args.policies:
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

    frame = add_buckets(pd.DataFrame(all_rows))
    policy_summary = summarize(frame, ["policy"])
    bucket_summary = summarize(frame, ["policy", "mu_bucket"])
    initial_bucket_summary = summarize(frame, ["policy", "initial_mu_bucket"]) if "initial_mu_bucket" in frame else None
    obstacle_label_summary = (
        summarize(frame[frame["obstacle_enabled"]], ["policy", "obstacle_label"])
        if "obstacle_enabled" in frame and frame["obstacle_enabled"].any()
        else None
    )
    segment_frame = build_segment_frame(frame)
    segment_summary = summarize_segments(segment_frame)
    segment_mu_bucket_summary = summarize_segments(segment_frame, ["policy", "mu_bucket", "segment"])

    episodes_csv = run_dir / "episodes.csv"
    policy_csv = run_dir / "policy_summary.csv"
    bucket_csv = run_dir / "mu_bucket_summary.csv"
    initial_bucket_csv = run_dir / "initial_mu_bucket_summary.csv"
    obstacle_label_csv = run_dir / "obstacle_label_summary.csv"
    segment_csv = run_dir / "segment_summary.csv"
    segment_mu_bucket_csv = run_dir / "segment_mu_bucket_summary.csv"
    frame.to_csv(episodes_csv, index=False)
    policy_summary.to_csv(policy_csv, index=False)
    bucket_summary.to_csv(bucket_csv, index=False)
    if initial_bucket_summary is not None:
        initial_bucket_summary.to_csv(initial_bucket_csv, index=False)
    if obstacle_label_summary is not None:
        obstacle_label_summary.to_csv(obstacle_label_csv, index=False)
    if not segment_summary.empty:
        segment_summary.to_csv(segment_csv, index=False)
        segment_mu_bucket_summary.to_csv(segment_mu_bucket_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "benchmark",
            "policies": args.policies,
            "checkpoint": args.checkpoint,
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
