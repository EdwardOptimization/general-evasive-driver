"""Paired hidden-perturbation gate for recurrent driver validation."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import add_buckets, summarize
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import CHECKPOINT_ABLATIONS, evaluate_policy, load_env_config


def condition_config(env_config: DriftEnvConfig, friction_mu_range: tuple[float, float]) -> DriftEnvConfig:
    if not env_config.friction_step.enabled:
        raise ValueError("paired perturbation gate requires friction_step.enabled=true")
    return replace(
        env_config,
        friction_step=replace(
            env_config.friction_step,
            mu_range=friction_mu_range,
            resample_speed_ref=False,
        ),
    )


def parse_range(raw: str) -> tuple[float, float]:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("range must be LOW,HIGH")
    low, high = float(parts[0]), float(parts[1])
    if high < low:
        raise argparse.ArgumentTypeError("range HIGH must be >= LOW")
    return low, high


def parse_checkpoint_specs(specs: list[str], default_checkpoint: Path) -> list[tuple[str, Path, str]]:
    if not specs:
        return [("checkpoint", default_checkpoint, "none")]
    parsed: list[tuple[str, Path, str]] = []
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"checkpoint spec must be NAME=PATH, got {spec!r}")
        name, raw_path = spec.split("=", 1)
        ablation = "none"
        if "@" in raw_path:
            raw_path, ablation = raw_path.rsplit("@", 1)
        if ablation not in CHECKPOINT_ABLATIONS:
            raise ValueError(f"unknown checkpoint ablation {ablation!r} in spec {spec!r}")
        parsed.append((name, Path(raw_path), ablation))
    return parsed


def load_seed_csv(path: Path) -> list[int]:
    frame = pd.read_csv(path)
    if "seed" not in frame.columns:
        raise ValueError(f"seed CSV must contain a 'seed' column: {path}")
    seeds = [int(seed) for seed in frame["seed"].tolist()]
    if not seeds:
        raise ValueError(f"seed CSV is empty: {path}")
    return seeds


def build_pair_summary(frame: pd.DataFrame) -> pd.DataFrame:
    key_columns = ["policy", "seed"]
    required = {"condition", "success", "return", *key_columns}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"paired frame is missing columns: {sorted(missing)}")
    nominal = frame[frame["condition"] == "nominal"][key_columns + ["success", "return"]]
    perturbed = frame[frame["condition"] == "perturbed"][key_columns + ["success", "return"]]
    paired = nominal.merge(
        perturbed,
        on=key_columns,
        suffixes=("_nominal", "_perturbed"),
    )
    paired["success_drop"] = paired["success_nominal"].astype(float) - paired["success_perturbed"].astype(float)
    paired["return_delta"] = paired["return_perturbed"] - paired["return_nominal"]
    summary = paired.groupby("policy", observed=True).agg(
        pairs=("seed", "count"),
        nominal_success=("success_nominal", "mean"),
        perturbed_success=("success_perturbed", "mean"),
        success_drop=("success_drop", "mean"),
        return_delta=("return_delta", "mean"),
    )
    return summary.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a paired hidden-perturbation gate.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", action="append", default=[])
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=1600)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--nominal-friction-mu-range", type=parse_range, default=(0.85, 1.15))
    parser.add_argument("--perturbed-friction-mu-range", type=parse_range, default=(0.25, 0.35))
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="paired_perturbation_gate", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_env_config(args.env_config)
    configs = {
        "nominal": condition_config(base_config, args.nominal_friction_mu_range),
        "perturbed": condition_config(base_config, args.perturbed_friction_mu_range),
    }
    checkpoint_specs = parse_checkpoint_specs(args.checkpoint_policy, args.checkpoint)
    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + episode for episode in range(args.episodes)]
    episodes = len(seeds)

    rows = []
    for condition, env_config in configs.items():
        for name, checkpoint_path, ablation in checkpoint_specs:
            policy_rows, _ = evaluate_policy(
                policy_name="checkpoint",
                episodes=episodes,
                seed=args.seed,
                checkpoint=checkpoint_path,
                device=args.device,
                env_config=env_config,
                checkpoint_ablation=ablation,
                seeds=seeds,
            )
            for row in policy_rows:
                row["condition"] = condition
                row["policy"] = name
                row["checkpoint_ablation"] = ablation
            rows.extend(policy_rows)

    frame = add_buckets(pd.DataFrame(rows))
    condition_summary = summarize(frame, ["condition", "policy"])
    label_summary = summarize(frame[frame["obstacle_enabled"]], ["condition", "policy", "obstacle_label"])
    pair_summary = build_pair_summary(frame)

    episodes_csv = run_dir / "episodes.csv"
    condition_csv = run_dir / "condition_summary.csv"
    label_csv = run_dir / "obstacle_label_summary.csv"
    pair_csv = run_dir / "pair_summary.csv"
    frame.to_csv(episodes_csv, index=False)
    condition_summary.to_csv(condition_csv, index=False)
    label_summary.to_csv(label_csv, index=False)
    pair_summary.to_csv(pair_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "paired_perturbation_gate",
            "env_config": args.env_config,
            "checkpoint": args.checkpoint,
            "checkpoint_policies": {
                name: {"path": path, "ablation": ablation} for name, path, ablation in checkpoint_specs
            },
            "episodes": episodes,
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "nominal_friction_mu_range": args.nominal_friction_mu_range,
            "perturbed_friction_mu_range": args.perturbed_friction_mu_range,
            "episodes_csv": episodes_csv,
            "condition_summary_csv": condition_csv,
            "obstacle_label_summary_csv": label_csv,
            "pair_summary_csv": pair_csv,
        },
    )
    print(pair_summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
