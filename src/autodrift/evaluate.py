"""Command-line evaluator for AutoDrift policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.policies import Policy, make_policy
from autodrift.train_ppo import ActorCritic


class ActorPolicy(Policy):
    def __init__(self, model: ActorCritic):
        self.model = model

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        del info
        action, _, _ = self.model.act(observation, deterministic=True)
        return action


def run_episode_with_policy(env: AutoDriftEnv, policy: Policy, policy_name: str, seed: int) -> dict:
    obs, info = env.reset(seed=seed)
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


def run_episode(env: AutoDriftEnv, policy_name: str, seed: int) -> dict:
    policy = make_policy(policy_name, env, seed=seed)
    return run_episode_with_policy(env, policy, policy_name, seed)


def summarize_rows(rows: list[dict]) -> dict[str, float | int | str]:
    frame = pd.DataFrame(rows)
    return {
        "episodes": int(len(frame)),
        "policy": str(frame["policy"].iloc[0]) if len(frame) else "",
        "return_mean": float(frame["return"].mean()),
        "steps_mean": float(frame["steps"].mean()),
        "lateral_rmse_mean": float(frame["lateral_rmse"].mean()),
        "lateral_peak_mean": float(frame["lateral_peak"].mean()),
        "beta_abs_error_mean": float(frame["beta_abs_error_mean"].mean()),
        "termination_rate": float(frame["terminated"].mean()),
        "mu_min": float(frame["mu"].min()),
        "mu_max": float(frame["mu"].max()),
    }


def evaluate_policy(
    policy_name: str,
    episodes: int,
    seed: int,
    checkpoint: Path | None = None,
    device: str = "auto",
) -> tuple[list[dict], dict[str, float | int | str]]:
    env_config = DriftEnvConfig()
    actor_policy: ActorPolicy | None = None
    if policy_name == "checkpoint":
        if checkpoint is None:
            raise ValueError("--checkpoint is required when --policy checkpoint is used")
        model, checkpoint_data = load_actor_critic_checkpoint(checkpoint, device=device)
        metadata_env = checkpoint_data.get("metadata", {}).get("env")
        if isinstance(metadata_env, dict):
            env_config = build_env_config(metadata_env)
        actor_policy = ActorPolicy(model)
    env = AutoDriftEnv(env_config)

    rows = []
    for episode in range(episodes):
        episode_seed = seed + episode
        if actor_policy is not None:
            row = run_episode_with_policy(env, actor_policy, policy_name, episode_seed)
        else:
            row = run_episode(env, policy_name, episode_seed)
        rows.append(row)
    return rows, summarize_rows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an AutoDrift policy.")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--policy", choices=["random", "heuristic", "checkpoint"], default="heuristic")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir
    csv_path = args.csv
    json_path = args.json
    if run_dir is not None:
        run_dir.mkdir(parents=True, exist_ok=True)
        csv_path = csv_path or run_dir / "episodes.csv"
        json_path = json_path or run_dir / "summary.json"
    elif csv_path is None and json_path is None:
        run_dir = make_run_dir(prefix=f"eval_{args.policy}", seed=args.seed)
        csv_path = run_dir / "episodes.csv"
        json_path = run_dir / "summary.json"

    rows, summary = evaluate_policy(
        policy_name=args.policy,
        episodes=args.episodes,
        seed=args.seed,
        checkpoint=args.checkpoint,
        device=args.device,
    )
    frame = pd.DataFrame(rows)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(csv_path, index=False)
    if json_path is not None:
        write_json(json_path, summary)
    if run_dir is not None:
        write_json(
            run_dir / "manifest.json",
            {
                "run_type": "evaluate",
                "policy": args.policy,
                "checkpoint": args.checkpoint,
                "episodes": args.episodes,
                "seed": args.seed,
                "device": args.device,
                "artifacts": {"episodes_csv": csv_path, "summary_json": json_path},
            },
        )
        print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
