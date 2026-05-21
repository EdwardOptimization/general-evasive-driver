"""Rollout-only throughput benchmark for vector environments."""

from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.train_ppo import PPOConfig, make_vector_env


def run_throughput_case(
    *,
    env_config: DriftEnvConfig,
    mode: str,
    num_envs: int,
    rollout_steps: int,
    seed: int,
    start_method: str = "fork",
) -> dict[str, Any]:
    config = PPOConfig(
        num_envs=num_envs,
        vector_env_mode=mode,
        vector_env_start_method=start_method,
        training_seed_mix_probability=1.0,
        seed=seed,
    )
    env = make_vector_env(config, env_config, seed=seed, seed_sequence=None)
    try:
        obs, _ = env.reset()
        action = np.zeros((num_envs, env.single_action_space.shape[0]), dtype=np.float32)
        started = perf_counter()
        episode_count = 0
        termination_count = 0
        for _ in range(rollout_steps):
            step = env.step(action)
            obs = step.observations
            del obs
            episode_count += sum(1 for info in step.infos if "episode" in info)
            termination_count += int(np.sum(step.terminated))
        elapsed = perf_counter() - started
    finally:
        env.close()
    env_steps = int(num_envs * rollout_steps)
    return {
        "mode": mode,
        "num_envs": int(num_envs),
        "rollout_steps": int(rollout_steps),
        "env_steps": env_steps,
        "seed": int(seed),
        "elapsed_seconds": float(elapsed),
        "env_steps_per_second": float(env_steps / max(elapsed, 1e-9)),
        "episode_count": int(episode_count),
        "termination_count": int(termination_count),
    }


def summarize(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return (
        frame.groupby(["mode", "num_envs", "rollout_steps"], observed=True)
        .agg(
            repeats=("seed", "count"),
            env_steps_per_second_mean=("env_steps_per_second", "mean"),
            env_steps_per_second_min=("env_steps_per_second", "min"),
            env_steps_per_second_max=("env_steps_per_second", "max"),
            elapsed_seconds_mean=("elapsed_seconds", "mean"),
            episode_count_mean=("episode_count", "mean"),
            termination_count_mean=("termination_count", "mean"),
        )
        .reset_index()
    )


def parse_int_list(raw: str) -> list[int]:
    values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    if any(value < 1 for value in values):
        raise argparse.ArgumentTypeError("all values must be >= 1")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark vector-env rollout throughput.")
    parser.add_argument("--env-config", type=Path, default=None)
    parser.add_argument("--modes", nargs="+", choices=["sync", "parallel"], default=["sync", "parallel"])
    parser.add_argument("--num-envs", type=parse_int_list, default=[1, 2, 4, 8])
    parser.add_argument("--rollout-steps", type=int, default=1024)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=5100)
    parser.add_argument("--start-method", default="fork")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.rollout_steps < 1:
        raise ValueError("--rollout-steps must be >= 1")
    if args.repeats < 1:
        raise ValueError("--repeats must be >= 1")

    env_config = load_env_config(args.env_config) if args.env_config is not None else DriftEnvConfig()
    run_dir = args.run_dir or make_run_dir(prefix="rollout_throughput", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for mode in args.modes:
        for num_envs in args.num_envs:
            for repeat in range(args.repeats):
                rows.append(
                    run_throughput_case(
                        env_config=env_config,
                        mode=mode,
                        num_envs=num_envs,
                        rollout_steps=args.rollout_steps,
                        seed=args.seed + repeat,
                        start_method=args.start_method,
                    )
                )

    frame = pd.DataFrame(rows)
    summary = summarize(rows)
    rows_csv = run_dir / "throughput_rows.csv"
    summary_csv = run_dir / "throughput_summary.csv"
    frame.to_csv(rows_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "rollout_throughput",
            "env_config": args.env_config,
            "modes": args.modes,
            "num_envs": args.num_envs,
            "rollout_steps": args.rollout_steps,
            "repeats": args.repeats,
            "seed": args.seed,
            "start_method": args.start_method,
            "rows_csv": rows_csv,
            "summary_csv": summary_csv,
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
