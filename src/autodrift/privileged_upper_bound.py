"""M67-A harness for comparing deployable drivers to privileged teachers."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import add_buckets, load_seed_csv, parse_checkpoint_specs, summarize
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import evaluate_policy, load_env_config


def _single_checkpoint_spec(kind: str, specs: list[str]) -> tuple[str, Path, str]:
    parsed = parse_checkpoint_specs(specs)
    if len(parsed) != 1:
        raise ValueError(f"exactly one --{kind}-checkpoint-policy is required")
    return parsed[0]


def evaluate_checkpoint_on_config(
    *,
    label: str,
    checkpoint: Path,
    ablation: str,
    env_config: DriftEnvConfig,
    env_config_path: Path,
    episodes: int,
    seed: int,
    seeds: list[int] | None,
    device: str,
) -> list[dict]:
    rows, _ = evaluate_policy(
        policy_name="checkpoint",
        episodes=episodes,
        seed=seed,
        checkpoint=checkpoint,
        device=device,
        env_config=env_config,
        checkpoint_ablation=ablation,
        seeds=seeds,
    )
    for episode_index, row in enumerate(rows):
        row["episode_index"] = episode_index
        row["policy"] = label
        row["checkpoint_ablation"] = ablation
        row["checkpoint_path"] = str(checkpoint)
        row["env_config_path"] = str(env_config_path)
    return rows


def _bool_as_float(series: pd.Series) -> pd.Series:
    return series.astype(float)


def build_seed_delta(frame: pd.DataFrame, baseline_policy: str, candidate_policy: str) -> pd.DataFrame:
    baseline = frame[frame["policy"] == baseline_policy].copy()
    candidate = frame[frame["policy"] == candidate_policy].copy()
    if baseline.empty:
        raise ValueError(f"baseline policy not found in episodes: {baseline_policy}")
    if candidate.empty:
        raise ValueError(f"candidate policy not found in episodes: {candidate_policy}")
    merged = baseline.merge(
        candidate,
        on=["episode_index", "seed"],
        suffixes=("_baseline", "_candidate"),
        validate="one_to_one",
    )
    if len(merged) != len(baseline) or len(merged) != len(candidate):
        raise ValueError("baseline and candidate rows must share the same episode_index and seed sequence")

    output = pd.DataFrame(
        {
            "episode_index": merged["episode_index"],
            "seed": merged["seed"],
            "baseline_policy": baseline_policy,
            "candidate_policy": candidate_policy,
            "baseline_success": ~merged["terminated_baseline"],
            "candidate_success": ~merged["terminated_candidate"],
            "baseline_collision": merged["collision_baseline"],
            "candidate_collision": merged["collision_candidate"],
            "baseline_obstacle_completed": merged["obstacle_completed_baseline"],
            "candidate_obstacle_completed": merged["obstacle_completed_candidate"],
            "baseline_return": merged["return_baseline"],
            "candidate_return": merged["return_candidate"],
            "baseline_min_clearance_margin": merged["min_clearance_margin_baseline"],
            "candidate_min_clearance_margin": merged["min_clearance_margin_candidate"],
            "baseline_mu": merged["mu_baseline"],
            "candidate_mu": merged["mu_candidate"],
            "baseline_brake_scale": merged["brake_scale_baseline"],
            "candidate_brake_scale": merged["brake_scale_candidate"],
            "baseline_steer_tau_scale": merged["steer_tau_scale_baseline"],
            "candidate_steer_tau_scale": merged["steer_tau_scale_candidate"],
        }
    )
    output["success_delta"] = _bool_as_float(output["candidate_success"]) - _bool_as_float(
        output["baseline_success"]
    )
    output["collision_delta"] = _bool_as_float(output["candidate_collision"]) - _bool_as_float(
        output["baseline_collision"]
    )
    output["return_delta"] = output["candidate_return"] - output["baseline_return"]
    output["min_clearance_margin_delta"] = (
        output["candidate_min_clearance_margin"] - output["baseline_min_clearance_margin"]
    )
    return output


def summarize_upper_bound(seed_delta: pd.DataFrame, baseline_policy: str, candidate_policy: str) -> dict:
    margin_delta = seed_delta["min_clearance_margin_delta"]
    return {
        "baseline_policy": baseline_policy,
        "candidate_policy": candidate_policy,
        "episodes": int(len(seed_delta)),
        "baseline_success_rate": float(seed_delta["baseline_success"].mean()),
        "candidate_success_rate": float(seed_delta["candidate_success"].mean()),
        "success_delta": float(seed_delta["success_delta"].mean()),
        "baseline_collision_rate": float(seed_delta["baseline_collision"].mean()),
        "candidate_collision_rate": float(seed_delta["candidate_collision"].mean()),
        "collision_delta": float(seed_delta["collision_delta"].mean()),
        "baseline_min_clearance_margin_mean": float(seed_delta["baseline_min_clearance_margin"].mean()),
        "candidate_min_clearance_margin_mean": float(seed_delta["candidate_min_clearance_margin"].mean()),
        "min_clearance_margin_delta_mean": float(margin_delta.mean()),
        "candidate_margin_improved_count": int((margin_delta > 0.0).sum()),
        "candidate_margin_regressed_count": int((margin_delta < 0.0).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a human-view driver against a privileged teacher.")
    parser.add_argument("--baseline-env-config", type=Path, required=True)
    parser.add_argument("--candidate-env-config", type=Path, required=True)
    parser.add_argument("--baseline-checkpoint-policy", action="append", default=[])
    parser.add_argument("--candidate-checkpoint-policy", action="append", default=[])
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=3600)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    baseline_label, baseline_checkpoint, baseline_ablation = _single_checkpoint_spec(
        "baseline", args.baseline_checkpoint_policy
    )
    candidate_label, candidate_checkpoint, candidate_ablation = _single_checkpoint_spec(
        "candidate", args.candidate_checkpoint_policy
    )
    baseline_env_config = load_env_config(args.baseline_env_config)
    candidate_env_config = load_env_config(args.candidate_env_config)
    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else None
    episodes = len(seeds) if seeds is not None else args.episodes

    baseline_rows = evaluate_checkpoint_on_config(
        label=baseline_label,
        checkpoint=baseline_checkpoint,
        ablation=baseline_ablation,
        env_config=baseline_env_config,
        env_config_path=args.baseline_env_config,
        episodes=episodes,
        seed=args.seed,
        seeds=seeds,
        device=args.device,
    )
    candidate_rows = evaluate_checkpoint_on_config(
        label=candidate_label,
        checkpoint=candidate_checkpoint,
        ablation=candidate_ablation,
        env_config=candidate_env_config,
        env_config_path=args.candidate_env_config,
        episodes=episodes,
        seed=args.seed,
        seeds=seeds,
        device=args.device,
    )
    frame = add_buckets(pd.DataFrame([*baseline_rows, *candidate_rows]))
    policy_summary = summarize(frame, ["policy"])
    seed_delta = build_seed_delta(frame, baseline_label, candidate_label)
    summary = summarize_upper_bound(seed_delta, baseline_label, candidate_label)

    run_dir = args.run_dir or make_run_dir(prefix="m67a_privileged_upper_bound", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    episodes_csv = run_dir / "episodes.csv"
    policy_summary_csv = run_dir / "policy_summary.csv"
    seed_delta_csv = run_dir / "seed_delta.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    frame.to_csv(episodes_csv, index=False)
    policy_summary.to_csv(policy_summary_csv, index=False)
    seed_delta.to_csv(seed_delta_csv, index=False)
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "m67a_privileged_upper_bound",
            "baseline_checkpoint_policy": {
                "label": baseline_label,
                "path": baseline_checkpoint,
                "ablation": baseline_ablation,
                "env_config": args.baseline_env_config,
            },
            "candidate_checkpoint_policy": {
                "label": candidate_label,
                "path": candidate_checkpoint,
                "ablation": candidate_ablation,
                "env_config": args.candidate_env_config,
            },
            "episodes": episodes,
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "artifacts": {
                "episodes_csv": episodes_csv,
                "policy_summary_csv": policy_summary_csv,
                "seed_delta_csv": seed_delta_csv,
                "summary_json": summary_json,
            },
            "summary": summary,
        },
    )
    print(policy_summary.to_string(index=False))
    print(seed_delta[["seed", "success_delta", "min_clearance_margin_delta", "return_delta"]].to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
