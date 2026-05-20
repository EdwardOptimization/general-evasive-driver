"""Benchmark runner for comparing policies on shared scenario seeds."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.evaluate import evaluate_policy


def add_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["mu_bucket"] = pd.cut(
        output["mu"],
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
        mu_min=("mu", "min"),
        mu_max=("mu", "max"),
    )
    return summary.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AutoDrift benchmark sweeps.")
    parser.add_argument("--policies", nargs="+", default=["heuristic", "random"], choices=["heuristic", "random", "checkpoint"])
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="benchmark", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    all_rows = []
    policy_summaries = {}

    for policy in args.policies:
        rows, summary = evaluate_policy(
            policy_name=policy,
            episodes=args.episodes,
            seed=args.seed,
            checkpoint=args.checkpoint,
            device=args.device,
        )
        all_rows.extend(rows)
        policy_summaries[policy] = summary

    frame = add_buckets(pd.DataFrame(all_rows))
    policy_summary = summarize(frame, ["policy"])
    bucket_summary = summarize(frame, ["policy", "mu_bucket"])

    episodes_csv = run_dir / "episodes.csv"
    policy_csv = run_dir / "policy_summary.csv"
    bucket_csv = run_dir / "mu_bucket_summary.csv"
    frame.to_csv(episodes_csv, index=False)
    policy_summary.to_csv(policy_csv, index=False)
    bucket_summary.to_csv(bucket_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "benchmark",
            "policies": args.policies,
            "checkpoint": args.checkpoint,
            "episodes": args.episodes,
            "seed": args.seed,
            "device": args.device,
            "artifacts": {
                "episodes_csv": episodes_csv,
                "policy_summary_csv": policy_csv,
                "mu_bucket_summary_csv": bucket_csv,
            },
            "policy_summaries": policy_summaries,
        },
    )

    print(policy_summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
