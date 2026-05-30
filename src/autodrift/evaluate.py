"""Command-line evaluator for AutoDrift policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.env import (
    AutoDriftEnv,
    DriftEnvConfig,
    FRONT_REAR_WHEEL_OBS_DIM,
    FRONT_REAR_WHEEL_OBSERVATION_MODES,
)
from autodrift.outcome_metric_instrumentation import compute_episode_outcome_metrics
from autodrift.policies import Policy, make_policy
from autodrift.train_ppo import ActorCritic


CHECKPOINT_ABLATIONS = (
    "none",
    "zero_action_history",
    "single_frame_history",
    "shuffled_history",
    "zero_current_response",
    "zero_all_response",
    "zero_wheel_response",
    "reset_recurrent_state",
)


def load_env_config(path: Path) -> DriftEnvConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "env" not in data:
        raise ValueError(f"{path} is missing required top-level 'env' config")
    return build_env_config(data["env"])


class ActorPolicy(Policy):
    def __init__(
        self,
        model: ActorCritic,
        env_config: DriftEnvConfig,
        ablation: str = "none",
        reset_hidden_policy: str = "episode_persistent",
    ):
        self.model = model
        self.env_config = env_config
        self.ablation = ablation
        self.reset_hidden_policy = reset_hidden_policy
        self.last_sequence: np.ndarray | None = None
        self.hidden: torch.Tensor | None = None
        self._rng_seed = 0
        self._rng = np.random.default_rng(self._rng_seed)

    def reset(self) -> None:
        self.last_sequence = None
        self.hidden = None
        self._rng = np.random.default_rng(self._rng_seed)

    def _action_history_indices(self) -> list[int]:
        if self.env_config.action_history_mode == "full":
            return [9, 10, 11]
        return []

    def _response_feature_indices(self, base_dim: int) -> list[int]:
        del base_dim
        indices = list(range(0, 9))
        indices.extend(self._action_history_indices())
        if self.env_config.wheel_observation_mode in FRONT_REAR_WHEEL_OBSERVATION_MODES:
            indices.extend(self._wheel_feature_indices())
        return sorted(set(indices))

    def _wheel_feature_indices(self) -> list[int]:
        if self.env_config.wheel_observation_mode not in FRONT_REAR_WHEEL_OBSERVATION_MODES:
            return []
        start = 9
        if self.env_config.action_history_mode == "full":
            start += len(self._action_history_indices())
        return list(range(start, start + FRONT_REAR_WHEEL_OBS_DIM))

    def _zero_response_features(self, observation: np.ndarray, base_dim: int, frame_starts: list[int]) -> None:
        indices = self._response_feature_indices(base_dim)
        for start in frame_starts:
            for index in indices:
                observation[start + index] = 0.0

    def _transform_observation(self, observation: np.ndarray) -> np.ndarray:
        if self.ablation == "none":
            return observation
        transformed = observation.copy()
        base_dim = len(transformed) // self.env_config.history_length
        if self.ablation == "single_frame_history":
            current = transformed[:base_dim].copy()
            transformed = np.tile(current, self.env_config.history_length).astype(np.float32)
        if self.ablation == "shuffled_history" and self.env_config.history_length > 1:
            frames = transformed.reshape(self.env_config.history_length, base_dim)
            transformed = frames[self._rng.permutation(self.env_config.history_length)].reshape(-1).astype(np.float32)
        if self.ablation == "zero_action_history":
            for start in range(0, len(transformed), base_dim):
                for index in self._action_history_indices():
                    transformed[start + index] = 0.0
        if self.ablation == "zero_current_response":
            self._zero_response_features(transformed, base_dim, [0])
        if self.ablation == "zero_all_response":
            self._zero_response_features(
                transformed,
                base_dim,
                list(range(0, len(transformed), base_dim)),
            )
        if self.ablation == "zero_wheel_response":
            wheel_indices = self._wheel_feature_indices()
            for start in range(0, len(transformed), base_dim):
                for index in wheel_indices:
                    transformed[start + index] = 0.0
        return transformed

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        del info
        observation = self._transform_observation(observation)
        if self.model.is_online_recurrent:
            if self.ablation == "reset_recurrent_state" or self.reset_hidden_policy == "every_step_control":
                self.hidden = None
            action, _, _, self.hidden = self.model.act_recurrent(
                observation,
                self.hidden,
                deterministic=True,
            )
            self.last_sequence = None
            return action
        if self.model.action_sequence_horizon > 1:
            self.last_sequence = self.model.predict_sequence(observation)
            return self.last_sequence[0].astype(np.float32)
        self.last_sequence = None
        action, _, _ = self.model.act(observation, deterministic=True)
        return action


SEGMENT_NAMES = ("left_curve", "right_curve", "near_zero")


def curvature_segment(curvature: float, threshold: float = 1e-3) -> str:
    if curvature > threshold:
        return "left_curve"
    if curvature < -threshold:
        return "right_curve"
    return "near_zero"


def empty_segment_stats() -> dict[str, dict[str, list[float]]]:
    return {
        name: {
            "lateral_errors": [],
            "beta_errors": [],
            "speeds": [],
            "rewards": [],
        }
        for name in SEGMENT_NAMES
    }


def add_segment_metrics(row: dict, segment_stats: dict[str, dict[str, list[float]]]) -> dict:
    for segment, stats in segment_stats.items():
        lateral_errors = stats["lateral_errors"]
        beta_errors = stats["beta_errors"]
        speeds = stats["speeds"]
        rewards = stats["rewards"]
        row[f"{segment}_steps"] = len(lateral_errors)
        row[f"{segment}_lateral_rmse"] = (
            float(np.sqrt(np.mean(np.square(lateral_errors)))) if lateral_errors else float("nan")
        )
        row[f"{segment}_beta_abs_error_mean"] = float(np.mean(np.abs(beta_errors))) if beta_errors else float("nan")
        row[f"{segment}_speed_mean"] = float(np.mean(speeds)) if speeds else float("nan")
        row[f"{segment}_reward_mean"] = float(np.mean(rewards)) if rewards else float("nan")
    return row


def outcome_bucket_from_info(info: dict, *, terminated: bool, truncated: bool) -> str:
    """Classify terminal outcome without changing environment behavior."""

    collision = bool(info.get("collision", False))
    obstacle_completed = bool(info.get("obstacle_completed", False))
    if obstacle_completed and not collision:
        return "success_obstacle_pass"
    if collision:
        return "collision_failure"
    termination_reason = str(info.get("termination_reason", "") or "")
    if terminated and termination_reason:
        return f"{termination_reason}_noncollision_noncompletion"
    if truncated:
        return "max_steps_noncompletion"
    return "other_terminated_noncompletion"


def run_episode_with_policy(env: AutoDriftEnv, policy: Policy, policy_name: str, seed: int) -> dict:
    obs, info = env.reset(seed=seed)
    policy.reset()

    rewards: list[float] = []
    lateral_errors: list[float] = []
    beta_errors: list[float] = []
    betas: list[float] = []
    speeds: list[float] = []
    actions: list[np.ndarray] = []
    step_infos: list[dict] = []
    plan_action_rates: list[float] = []
    plan_first_action_errors: list[float] = []
    segment_stats = empty_segment_stats()
    friction_step_applied = False
    terminated = False
    truncated = False
    while not (terminated or truncated):
        action = policy.act(obs, info)
        sequence = getattr(policy, "last_sequence", None)
        if sequence is not None and len(sequence) > 0:
            plan_first_action_errors.append(float(np.linalg.norm(np.asarray(sequence[0]) - np.asarray(action))))
            if len(sequence) > 1:
                plan_action_rates.append(float(np.mean(np.linalg.norm(np.diff(sequence, axis=0), axis=1))))
        obs, reward, terminated, truncated, info = env.step(action)
        step_infos.append(dict(info))
        beta_error = abs(float(info["beta"])) - float(info["beta_target"])
        segment = curvature_segment(float(info.get("curvature", 0.0)))
        rewards.append(float(reward))
        lateral_errors.append(float(info["lateral_error"]))
        beta_errors.append(beta_error)
        betas.append(float(info["beta"]))
        speeds.append(float(info["speed"]))
        actions.append(np.asarray(action, dtype=np.float32))
        segment_stats[segment]["lateral_errors"].append(float(info["lateral_error"]))
        segment_stats[segment]["beta_errors"].append(beta_error)
        segment_stats[segment]["speeds"].append(float(info["speed"]))
        segment_stats[segment]["rewards"].append(float(reward))
        friction_step_applied = friction_step_applied or bool(info.get("friction_step_applied", False))

    outcome_metric_fields = compute_episode_outcome_metrics(
        step_infos,
        default_dt=float(getattr(env.config, "dt", 0.02)),
        default_track_width=float(getattr(env.config, "track_width", 5.0)),
    )
    row = {
        "seed": seed,
        "policy": policy_name,
        "steps": int(info["step"]),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "mu": float(info["mu"]),
        "initial_mu": float(info.get("initial_mu", info["mu"])),
        "mass": float(info["mass"]),
        "mass_scale": float(info.get("mass_scale", float("nan"))),
        "inertia_scale": float(info.get("inertia_scale", float("nan"))),
        "cg_shift": float(info.get("cg_shift", float("nan"))),
        "tire_stiffness_scale": float(info.get("tire_stiffness_scale", float("nan"))),
        "brake_scale": float(info.get("brake_scale", float("nan"))),
        "drive_scale": float(info.get("drive_scale", float("nan"))),
        "steer_tau_scale": float(info.get("steer_tau_scale", float("nan"))),
        "drive_tau_scale": float(info.get("drive_tau_scale", float("nan"))),
        "friction_step_at": info.get("friction_step_at"),
        "friction_step_applied": friction_step_applied,
        "obstacle_enabled": bool(info.get("obstacle_enabled", False)),
        "obstacle_label": str(info.get("obstacle_label", "")),
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "obstacle_passed_raw": bool(info.get("obstacle_passed_raw", False)),
        "completion_reason": str(info.get("completion_reason", "") or ""),
        "outcome_bucket": outcome_bucket_from_info(info, terminated=terminated, truncated=truncated),
        "return": float(np.sum(rewards)),
        "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
        "lateral_rmse": float(np.sqrt(np.mean(np.square(lateral_errors)))) if lateral_errors else float("nan"),
        "lateral_peak": float(np.max(np.abs(lateral_errors))) if lateral_errors else float("nan"),
        "beta_abs_error_mean": float(np.mean(np.abs(beta_errors))) if beta_errors else float("nan"),
        "beta_abs_peak": float(np.max(np.abs(betas))) if betas else float("nan"),
        "high_sideslip_fraction": float(np.mean(np.abs(betas) > 0.35)) if betas else float("nan"),
        "speed_mean": float(np.mean(speeds)) if speeds else float("nan"),
        "action_rate_mean": (
            float(np.mean(np.linalg.norm(np.diff(np.asarray(actions), axis=0), axis=1))) if len(actions) > 1 else 0.0
        ),
        "plan_horizon": int(getattr(getattr(policy, "model", None), "action_sequence_horizon", 1)),
        "plan_action_rate_mean": float(np.mean(plan_action_rates)) if plan_action_rates else float("nan"),
        "plan_first_action_error_mean": (
            float(np.mean(plan_first_action_errors)) if plan_first_action_errors else float("nan")
        ),
        **outcome_metric_fields,
    }
    return add_segment_metrics(row, segment_stats)


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
        "min_clearance_margin_mean": (
            float(frame["min_clearance_margin"].mean()) if "min_clearance_margin" in frame else float("nan")
        ),
        "min_clearance_margin_min": (
            float(frame["min_clearance_margin"].min()) if "min_clearance_margin" in frame else float("nan")
        ),
    }


def evaluate_policy(
    policy_name: str,
    episodes: int,
    seed: int,
    checkpoint: Path | None = None,
    device: str = "auto",
    env_config: DriftEnvConfig | None = None,
    checkpoint_ablation: str = "none",
    seeds: list[int] | None = None,
) -> tuple[list[dict], dict[str, float | int | str]]:
    if checkpoint_ablation not in CHECKPOINT_ABLATIONS:
        raise ValueError(f"unknown checkpoint_ablation: {checkpoint_ablation}")
    resolved_env_config = env_config or DriftEnvConfig()
    actor_policy: ActorPolicy | None = None
    checkpoint_path = checkpoint
    if policy_name == "checkpoint":
        if checkpoint_path is None:
            raise ValueError("--checkpoint is required when --policy checkpoint is used")
        model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=device)
        metadata_env = checkpoint_data.get("metadata", {}).get("env")
        controller_profile_runtime = checkpoint_data.get("metadata", {}).get("controller_profile_runtime", {})
        reset_hidden_policy = (
            str(controller_profile_runtime.get("reset_hidden_policy", "episode_persistent"))
            if isinstance(controller_profile_runtime, dict)
            else "episode_persistent"
        )
        if env_config is None and isinstance(metadata_env, dict):
            resolved_env_config = build_env_config(metadata_env)
    env = AutoDriftEnv(resolved_env_config)
    if policy_name == "checkpoint":
        assert checkpoint_path is not None
        target_obs_dim = int(env.observation_space.shape[0])
        if model.obs_dim != target_obs_dim:
            model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device, obs_dim=target_obs_dim)
        actor_policy = ActorPolicy(
            model,
            resolved_env_config,
            ablation=checkpoint_ablation,
            reset_hidden_policy=reset_hidden_policy,
        )

    rows = []
    episode_seeds = list(seeds) if seeds is not None else [seed + episode for episode in range(episodes)]
    for episode_seed in episode_seeds:
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
    parser.add_argument(
        "--policy",
        choices=["random", "heuristic", "aeb", "aes_heuristic", "envelope_aes", "checkpoint"],
        default="heuristic",
    )
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument(
        "--checkpoint-ablation",
        choices=CHECKPOINT_ABLATIONS,
        default="none",
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--env-config", type=Path, default=None)
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

    env_config = None
    if args.env_config is not None:
        env_config = load_env_config(args.env_config)

    rows, summary = evaluate_policy(
        policy_name=args.policy,
        episodes=args.episodes,
        seed=args.seed,
        checkpoint=args.checkpoint,
        device=args.device,
        env_config=env_config,
        checkpoint_ablation=args.checkpoint_ablation,
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
                "checkpoint_ablation": args.checkpoint_ablation,
                "episodes": args.episodes,
                "seed": args.seed,
                "device": args.device,
                "env_config": args.env_config,
                "artifacts": {"episodes_csv": csv_path, "summary_json": json_path},
            },
        )
        print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
