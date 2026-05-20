"""Rollout tracing and plotting for trained policies."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
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


def make_rollout_policy(
    policy_name: str,
    env: AutoDriftEnv,
    seed: int,
    checkpoint: Path | None,
    device: str,
) -> Policy:
    if policy_name == "checkpoint":
        if checkpoint is None:
            raise ValueError("--checkpoint is required for checkpoint rollouts")
        model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
        return ActorPolicy(model)
    return make_policy(policy_name, env, seed=seed)


def env_config_from_checkpoint(checkpoint: Path | None) -> DriftEnvConfig:
    if checkpoint is None:
        return DriftEnvConfig()
    _, checkpoint_data = load_actor_critic_checkpoint(checkpoint, device="cpu")
    metadata_env = checkpoint_data.get("metadata", {}).get("env")
    if isinstance(metadata_env, dict):
        return build_env_config(metadata_env)
    return DriftEnvConfig()


def collect_trace(
    policy_name: str,
    seed: int,
    checkpoint: Path | None = None,
    device: str = "auto",
) -> tuple[list[dict], dict]:
    env = AutoDriftEnv(env_config_from_checkpoint(checkpoint) if policy_name == "checkpoint" else DriftEnvConfig())
    policy = make_rollout_policy(policy_name, env, seed, checkpoint, device)
    obs, info = env.reset(seed=seed)
    policy.reset()

    rows: list[dict] = []
    terminated = False
    truncated = False
    total_return = 0.0
    while not (terminated or truncated):
        action = policy.act(obs, info)
        x = env.state.x
        y = env.state.y
        beta = math.atan2(env.state.vy, max(env.state.vx, 1e-6))
        speed = math.hypot(env.state.vx, env.state.vy)
        obs, reward, terminated, truncated, info = env.step(action)
        total_return += reward
        rows.append(
            {
                "step": info["step"],
                "time": info["step"] * env.config.dt,
                "x": x,
                "y": y,
                "beta": beta,
                "beta_target": info["beta_target"],
                "speed": speed,
                "speed_ref": info["speed_ref"],
                "lateral_error": info["lateral_error"],
                "heading_error": info["heading_error"],
                "steer_cmd": float(action[0]),
                "drive_cmd": float(action[1]),
                "reward": reward,
                "mu": info["mu"],
                "mass": info["mass"],
            }
        )

    summary = {
        "seed": seed,
        "policy": policy_name,
        "steps": rows[-1]["step"] if rows else 0,
        "terminated": terminated,
        "truncated": truncated,
        "return": total_return,
        "mu": rows[0]["mu"] if rows else float("nan"),
        "speed_ref": rows[0]["speed_ref"] if rows else float("nan"),
        "beta_target": rows[0]["beta_target"] if rows else float("nan"),
    }
    return rows, summary


def plot_trace(rows: list[dict], summary: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    time = np.asarray([row["time"] for row in rows])
    x = np.asarray([row["x"] for row in rows])
    y = np.asarray([row["y"] for row in rows])
    beta = np.asarray([row["beta"] for row in rows])
    beta_target = np.asarray([row["beta_target"] for row in rows])
    speed = np.asarray([row["speed"] for row in rows])
    speed_ref = np.asarray([row["speed_ref"] for row in rows])
    steer_cmd = np.asarray([row["steer_cmd"] for row in rows])
    drive_cmd = np.asarray([row["drive_cmd"] for row in rows])
    lateral_error = np.asarray([row["lateral_error"] for row in rows])

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    axes[0, 0].plot(x, y, label="trajectory")
    axes[0, 0].set_aspect("equal", adjustable="box")
    axes[0, 0].set_title("trajectory")
    axes[0, 0].set_xlabel("x [m]")
    axes[0, 0].set_ylabel("y [m]")

    axes[0, 1].plot(time, beta, label="beta")
    axes[0, 1].plot(time, beta_target, "--", label="target")
    axes[0, 1].set_title("sideslip")
    axes[0, 1].set_xlabel("time [s]")
    axes[0, 1].set_ylabel("beta [rad]")
    axes[0, 1].legend()

    axes[1, 0].plot(time, speed, label="speed")
    axes[1, 0].plot(time, speed_ref, "--", label="ref")
    axes[1, 0].plot(time, lateral_error, label="lateral error")
    axes[1, 0].set_title("speed and lateral error")
    axes[1, 0].set_xlabel("time [s]")
    axes[1, 0].legend()

    axes[1, 1].plot(time, steer_cmd, label="steer")
    axes[1, 1].plot(time, drive_cmd, label="drive/brake")
    axes[1, 1].set_title("actions")
    axes[1, 1].set_xlabel("time [s]")
    axes[1, 1].set_ylabel("normalized command")
    axes[1, 1].legend()

    fig.suptitle(
        f"{summary['policy']} seed={summary['seed']} return={summary['return']:.1f} "
        f"mu={summary['mu']:.3f} terminated={summary['terminated']}"
    )
    fig.savefig(output, dpi=140)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace and plot AutoDrift policy rollouts.")
    parser.add_argument("--policy", choices=["heuristic", "random", "checkpoint"], default="checkpoint")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--seeds", type=int, nargs="+", default=[7])
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=Path("runs/rollouts"))
    args = parser.parse_args()

    summaries = []
    for seed in args.seeds:
        rows, summary = collect_trace(args.policy, seed, checkpoint=args.checkpoint, device=args.device)
        summaries.append(summary)
        prefix = f"{args.policy}_seed{seed}"
        write_csv_rows(args.out_dir / f"{prefix}.csv", rows)
        write_json(args.out_dir / f"{prefix}_summary.json", summary)
        plot_trace(rows, summary, args.out_dir / f"{prefix}.png")
    write_json(args.out_dir / "manifest.json", {"policy": args.policy, "checkpoint": args.checkpoint, "summaries": summaries})
    print(f"out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
