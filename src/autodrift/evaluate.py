"""Command-line evaluator for AutoDrift policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.policies import make_policy


def run_episode(env: AutoDriftEnv, policy_name: str, seed: int) -> dict:
    obs, info = env.reset(seed=seed)
    policy = make_policy(policy_name, env, seed=seed)
    policy.reset()

    rewards: list[float] = []
    lateral_errors: list[float] = []
    beta_errors: list[float] = []
    speeds: list[float] = []
    terminated = False
    truncated = False
    while not (terminated or truncated):
        action = policy.act(obs, info)
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        lateral_errors.append(float(info["lateral_error"]))
        beta_errors.append(abs(float(info["beta"])) - float(info["beta_target"]))
        speeds.append(float(info["speed"]))

    return {
        "seed": seed,
        "policy": policy_name,
        "steps": int(info["step"]),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "mu": float(info["mu"]),
        "mass": float(info["mass"]),
        "return": float(np.sum(rewards)),
        "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
        "lateral_rmse": float(np.sqrt(np.mean(np.square(lateral_errors)))) if lateral_errors else float("nan"),
        "lateral_peak": float(np.max(np.abs(lateral_errors))) if lateral_errors else float("nan"),
        "beta_abs_error_mean": float(np.mean(np.abs(beta_errors))) if beta_errors else float("nan"),
        "speed_mean": float(np.mean(speeds)) if speeds else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an AutoDrift policy.")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--policy", choices=["random", "heuristic"], default="heuristic")
    parser.add_argument("--csv", type=Path, default=None)
    args = parser.parse_args()

    env = AutoDriftEnv(DriftEnvConfig())
    rows = [run_episode(env, args.policy, args.seed + i) for i in range(args.episodes)]
    frame = pd.DataFrame(rows)
    summary = {
        "episodes": args.episodes,
        "policy": args.policy,
        "return_mean": float(frame["return"].mean()),
        "steps_mean": float(frame["steps"].mean()),
        "lateral_rmse_mean": float(frame["lateral_rmse"].mean()),
        "lateral_peak_mean": float(frame["lateral_peak"].mean()),
        "beta_abs_error_mean": float(frame["beta_abs_error_mean"].mean()),
        "termination_rate": float(frame["terminated"].mean()),
        "mu_min": float(frame["mu"].min()),
        "mu_max": float(frame["mu"].max()),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.csv is not None:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(args.csv, index=False)


if __name__ == "__main__":
    main()
