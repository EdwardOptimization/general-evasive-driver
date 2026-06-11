"""Matched-observation hidden-swap gate for recurrent driver validation."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import (
    AutoDriftEnv,
    DriftEnvConfig,
    EGO_OBS_DIM,
    FRONT_REAR_WHEEL_OBS_DIM,
    FRONT_REAR_WHEEL_OBSERVATION_MODES,
    LAST_ACTION_OBS_DIM,
)
from autodrift.evaluate import load_env_config
from autodrift.observation_degradation_wrapper import ObservationDegradationWrapper, make_env_from_config
from autodrift.paired_perturbation_gate import (
    condition_config,
    load_seed_csv,
    parse_randomization_overrides,
    parse_range,
)
from autodrift.train_ppo import ActorCritic


VARIANTS = ("normal", "reset", "zero_response", "hidden_swap")


@dataclass
class DecisionSnapshot:
    condition: str
    seed: int
    step: int
    observation: np.ndarray
    hidden: torch.Tensor | None
    # Bare AutoDriftEnv, or ObservationDegradationWrapper when the env config
    # carries an observation_degradation block (degraded-response task family).
    env: AutoDriftEnv | ObservationDegradationWrapper
    info: dict[str, Any]
    obstacle_distance: float
    snapshot_score: float


def clone_hidden(hidden: torch.Tensor | None) -> torch.Tensor | None:
    return None if hidden is None else hidden.detach().clone()


def response_feature_indices(env_config: DriftEnvConfig, observation_dim: int) -> list[int]:
    base_dim = observation_dim // env_config.history_length
    if base_dim * env_config.history_length != observation_dim:
        raise ValueError("observation dimension must be divisible by history_length")
    per_frame = EGO_OBS_DIM
    if env_config.action_history_mode == "full":
        per_frame += LAST_ACTION_OBS_DIM
    if env_config.wheel_observation_mode in FRONT_REAR_WHEEL_OBSERVATION_MODES:
        per_frame += FRONT_REAR_WHEEL_OBS_DIM
    indices: list[int] = []
    for start in range(0, observation_dim, base_dim):
        indices.extend(range(start, start + per_frame))
    return indices


def zero_response_observation(observation: np.ndarray, env_config: DriftEnvConfig) -> np.ndarray:
    transformed = np.asarray(observation, dtype=np.float32).copy()
    for index in response_feature_indices(env_config, len(transformed)):
        transformed[index] = 0.0
    return transformed


def observation_distances(
    source_observation: np.ndarray,
    paired_observation: np.ndarray,
    env_config: DriftEnvConfig,
) -> dict[str, float]:
    source = np.asarray(source_observation, dtype=np.float32)
    paired = np.asarray(paired_observation, dtype=np.float32)
    if source.shape != paired.shape:
        raise ValueError(f"cannot compare observation shapes {source.shape} and {paired.shape}")
    response_indices = np.asarray(response_feature_indices(env_config, len(source)), dtype=np.int64)
    response_mask = np.zeros(len(source), dtype=bool)
    response_mask[response_indices] = True
    diff = source - paired
    return {
        "observation_distance": float(np.linalg.norm(diff)),
        "response_observation_distance": float(np.linalg.norm(diff[response_mask])),
        "context_observation_distance": float(np.linalg.norm(diff[~response_mask])),
    }


def hidden_state_distance(source_hidden: torch.Tensor | None, paired_hidden: torch.Tensor | None) -> float:
    if source_hidden is None and paired_hidden is None:
        return 0.0
    if source_hidden is None or paired_hidden is None:
        return float("nan")
    source = source_hidden.detach().cpu().numpy().reshape(-1)
    paired = paired_hidden.detach().cpu().numpy().reshape(-1)
    if source.shape != paired.shape:
        return float("nan")
    return float(np.linalg.norm(source - paired))


def action_trajectory_distances(
    actions: list[np.ndarray],
    reference_actions: list[np.ndarray] | None,
) -> dict[str, float | int]:
    if reference_actions is None:
        return {
            "action_trajectory_distance_mean": float("nan"),
            "action_trajectory_distance_rms": float("nan"),
            "action_trajectory_distance_max": float("nan"),
            "action_trajectory_compare_steps": 0,
        }
    common_steps = min(len(actions), len(reference_actions))
    if common_steps == 0:
        return {
            "action_trajectory_distance_mean": float("nan"),
            "action_trajectory_distance_rms": float("nan"),
            "action_trajectory_distance_max": float("nan"),
            "action_trajectory_compare_steps": 0,
        }
    action_array = np.asarray(actions[:common_steps], dtype=np.float32)
    reference_array = np.asarray(reference_actions[:common_steps], dtype=np.float32)
    distances = np.linalg.norm(action_array - reference_array, axis=1)
    return {
        "action_trajectory_distance_mean": float(np.mean(distances)),
        "action_trajectory_distance_rms": float(np.sqrt(np.mean(np.square(distances)))),
        "action_trajectory_distance_max": float(np.max(distances)),
        "action_trajectory_compare_steps": int(common_steps),
    }


def zero_action_trajectory_distances(steps: int) -> dict[str, float | int]:
    return {
        "action_trajectory_distance_mean": 0.0,
        "action_trajectory_distance_rms": 0.0,
        "action_trajectory_distance_max": 0.0,
        "action_trajectory_compare_steps": int(steps),
    }


def _is_snapshot_candidate(
    info: dict[str, Any],
    min_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
) -> bool:
    step = int(info.get("step", 0))
    if step < min_probe_steps:
        return False
    if require_friction_step:
        if not bool(info.get("friction_step_applied", False)):
            return False
        friction_step_at = info.get("friction_step_at")
        if friction_step_at is not None and step < int(friction_step_at) + min_hidden_updates_after_friction:
            return False
    obstacle_distance = float(info.get("obstacle_distance", float("nan")))
    return np.isfinite(obstacle_distance) and obstacle_distance > 0.0


def collect_decision_snapshot(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    condition: str,
    seed: int,
    *,
    target_obstacle_distance: float = 12.0,
    min_probe_steps: int = 10,
    max_probe_steps: int = 180,
    require_friction_step: bool = True,
    min_hidden_updates_after_friction: int = 2,
) -> DecisionSnapshot | None:
    env = make_env_from_config(env_config)
    obs, info = env.reset(seed=seed)
    hidden: torch.Tensor | None = None
    best: DecisionSnapshot | None = None
    terminated = False
    truncated = False

    while not (terminated or truncated):
        step = int(info.get("step", 0))
        if _is_snapshot_candidate(
            info,
            min_probe_steps,
            require_friction_step,
            min_hidden_updates_after_friction,
        ):
            obstacle_distance = float(info["obstacle_distance"])
            score = abs(obstacle_distance - target_obstacle_distance)
            if best is None or score < best.snapshot_score:
                best = DecisionSnapshot(
                    condition=condition,
                    seed=seed,
                    step=step,
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=clone_hidden(hidden),
                    env=copy.deepcopy(env),
                    info=dict(info),
                    obstacle_distance=obstacle_distance,
                    snapshot_score=score,
                )
            if obstacle_distance <= target_obstacle_distance:
                break
        if step >= max_probe_steps:
            break
        action, _, _, hidden = model.act_recurrent(obs, hidden, deterministic=True)
        obs, _, terminated, truncated, info = env.step(action)
    return best


def terminal_reason(info: dict[str, Any], terminated: bool, truncated: bool, env_config: DriftEnvConfig) -> str:
    if bool(info.get("collision", False)):
        return "collision"
    if abs(float(info.get("lateral_error", 0.0))) > env_config.track_width:
        return "off_road"
    if terminated:
        speed = float(info.get("speed", float("nan")))
        if np.isfinite(speed) and speed < 1.0:
            return "too_slow"
        if np.isfinite(speed) and speed > 32.0:
            return "too_fast"
        return "terminated"
    if truncated:
        if bool(info.get("obstacle_completed", False)):
            return "obstacle_completed"
        return "truncated"
    return "continuation_limit"


def replay_continuation(
    model: ActorCritic,
    snapshot: DecisionSnapshot,
    *,
    env_config: DriftEnvConfig,
    variant: str,
    paired_hidden: torch.Tensor | None = None,
    normal_first_action: np.ndarray | None = None,
    normal_actions: list[np.ndarray] | None = None,
    max_continuation_steps: int | None = None,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    if variant not in VARIANTS:
        raise ValueError(f"unknown hidden-swap variant: {variant}")
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = clone_hidden(snapshot.hidden)
    if variant == "hidden_swap":
        hidden = clone_hidden(paired_hidden)
    elif variant == "reset":
        hidden = None

    max_steps = max_continuation_steps
    if max_steps is None or max_steps <= 0:
        max_steps = max(1, env_config.max_steps - snapshot.step)

    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max_steps):
        policy_obs = zero_response_observation(obs, env_config) if variant == "zero_response" else obs
        action_hidden = None if variant == "reset" else hidden
        action, _, _, next_hidden = model.act_recurrent(policy_obs, action_hidden, deterministic=True)
        actions.append(action)
        hidden = None if variant == "reset" else next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break

    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_action_distance = (
        float(np.linalg.norm(first_action - normal_first_action))
        if normal_first_action is not None and np.all(np.isfinite(first_action))
        else float("nan")
    )
    trajectory_distances = action_trajectory_distances(actions, normal_actions)
    reason = terminal_reason(info, terminated, truncated, env_config)
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    return {
        "variant": variant,
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
        "first_action_distance": first_action_distance,
        **trajectory_distances,
    }, actions


def build_pair_row(
    seed: int,
    nominal: DecisionSnapshot | None,
    perturbed: DecisionSnapshot | None,
    env_config: DriftEnvConfig,
    max_observation_distance: float,
) -> dict[str, Any]:
    if nominal is None or perturbed is None:
        if nominal is None and perturbed is None:
            pair_status = "missing_both"
        elif nominal is None:
            pair_status = "missing_nominal"
        else:
            pair_status = "missing_perturbed"
        return {
            "seed": seed,
            "pair_status": pair_status,
            "accepted_match": False,
        }
    distances = observation_distances(nominal.observation, perturbed.observation, env_config)
    accepted = distances["observation_distance"] <= max_observation_distance
    return {
        "seed": seed,
        "pair_status": "paired",
        "accepted_match": bool(accepted),
        "nominal_step": nominal.step,
        "perturbed_step": perturbed.step,
        "nominal_obstacle_distance": nominal.obstacle_distance,
        "perturbed_obstacle_distance": perturbed.obstacle_distance,
        "nominal_snapshot_score": nominal.snapshot_score,
        "perturbed_snapshot_score": perturbed.snapshot_score,
        "hidden_state_distance": hidden_state_distance(nominal.hidden, perturbed.hidden),
        **distances,
    }


def replay_pair(
    model: ActorCritic,
    source: DecisionSnapshot,
    paired: DecisionSnapshot,
    pair_row: dict[str, Any],
    env_config: DriftEnvConfig,
    max_continuation_steps: int | None,
) -> list[dict[str, Any]]:
    normal, normal_actions = replay_continuation(
        model,
        source,
        env_config=env_config,
        variant="normal",
        max_continuation_steps=max_continuation_steps,
    )
    normal["first_action_distance"] = 0.0
    normal.update(zero_action_trajectory_distances(len(normal_actions)))
    normal_first_action = np.array(
        [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
        dtype=np.float32,
    )
    rows = []
    for variant in VARIANTS:
        if variant == "normal":
            replay = normal
        else:
            replay, _ = replay_continuation(
                model,
                source,
                env_config=env_config,
                variant=variant,
                paired_hidden=paired.hidden,
                normal_first_action=normal_first_action,
                normal_actions=normal_actions,
                max_continuation_steps=max_continuation_steps,
            )
        rows.append(
            {
                "seed": source.seed,
                "source_condition": source.condition,
                "paired_condition": paired.condition,
                "source_step": source.step,
                "source_obstacle_distance": source.obstacle_distance,
                "accepted_match": pair_row["accepted_match"],
                "observation_distance": pair_row.get("observation_distance", float("nan")),
                "response_observation_distance": pair_row.get("response_observation_distance", float("nan")),
                "context_observation_distance": pair_row.get("context_observation_distance", float("nan")),
                "hidden_state_distance": pair_row.get("hidden_state_distance", float("nan")),
                **replay,
            }
        )
    return rows


def summarize_replays(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "source_condition",
                "variant",
                "accepted_match",
                "pairs",
                "success_rate",
                "return_mean",
                "collision_rate",
                "off_road_rate",
                "spin_out_rate",
                "first_action_distance_mean",
                "action_trajectory_distance_mean",
                "action_trajectory_distance_rms_mean",
                "action_trajectory_distance_max_mean",
                "action_trajectory_compare_steps_mean",
                "observation_distance_mean",
                "hidden_state_distance_mean",
            ]
        )
    grouped = frame.groupby(["source_condition", "variant", "accepted_match"], observed=True)
    aggregations = {
        "pairs": ("seed", "count"),
        "success_rate": ("success", "mean"),
        "return_mean": ("return", "mean"),
        "termination_rate": ("terminated", "mean"),
        "collision_rate": ("collision", "mean"),
        "off_road_rate": ("off_road", "mean"),
        "spin_out_rate": ("spin_out", "mean"),
        "obstacle_completion_rate": ("obstacle_completed", "mean"),
        "first_action_distance_mean": ("first_action_distance", "mean"),
        "action_trajectory_distance_mean": ("action_trajectory_distance_mean", "mean"),
        "action_trajectory_distance_rms_mean": ("action_trajectory_distance_rms", "mean"),
        "action_trajectory_distance_max_mean": ("action_trajectory_distance_max", "mean"),
        "action_trajectory_compare_steps_mean": ("action_trajectory_compare_steps", "mean"),
        "observation_distance_mean": ("observation_distance", "mean"),
        "response_observation_distance_mean": ("response_observation_distance", "mean"),
        "context_observation_distance_mean": ("context_observation_distance", "mean"),
        "hidden_state_distance_mean": ("hidden_state_distance", "mean"),
    }
    if "min_clearance_margin" in frame:
        aggregations["min_clearance_margin_mean"] = ("min_clearance_margin", "mean")
        aggregations["min_clearance_margin_min"] = ("min_clearance_margin", "min")
    if "min_obstacle_clearance" in frame:
        aggregations["min_obstacle_clearance_mean"] = ("min_obstacle_clearance", "mean")
    return grouped.agg(**aggregations).reset_index()


def run_hidden_swap_gate(
    *,
    model: ActorCritic,
    base_config: DriftEnvConfig,
    seeds: list[int],
    nominal_friction_mu_range: tuple[float, float],
    perturbed_friction_mu_range: tuple[float, float],
    nominal_randomization: dict[str, tuple[float, float]],
    perturbed_randomization: dict[str, tuple[float, float]],
    target_obstacle_distance: float,
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    max_observation_distance: float,
    max_continuation_steps: int | None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    configs = {
        "nominal": condition_config(base_config, nominal_friction_mu_range, nominal_randomization),
        "perturbed": condition_config(base_config, perturbed_friction_mu_range, perturbed_randomization),
    }
    pair_rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    for seed in seeds:
        snapshots = {
            condition: collect_decision_snapshot(
                model,
                env_config,
                condition,
                seed,
                target_obstacle_distance=target_obstacle_distance,
                min_probe_steps=min_probe_steps,
                max_probe_steps=max_probe_steps,
                require_friction_step=require_friction_step,
                min_hidden_updates_after_friction=min_hidden_updates_after_friction,
            )
            for condition, env_config in configs.items()
        }
        pair_row = build_pair_row(
            seed,
            snapshots["nominal"],
            snapshots["perturbed"],
            configs["nominal"],
            max_observation_distance,
        )
        pair_rows.append(pair_row)
        if snapshots["nominal"] is None or snapshots["perturbed"] is None:
            continue
        nominal = snapshots["nominal"]
        perturbed = snapshots["perturbed"]
        replay_rows.extend(
            replay_pair(model, nominal, perturbed, pair_row, configs["nominal"], max_continuation_steps)
        )
        replay_rows.extend(
            replay_pair(model, perturbed, nominal, pair_row, configs["perturbed"], max_continuation_steps)
        )

    pairs = pd.DataFrame(pair_rows)
    replays = pd.DataFrame(replay_rows)
    summary = summarize_replays(replays)
    return pairs, replays, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a matched-observation hidden-swap gate.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--seed", type=int, default=4200)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--nominal-friction-mu-range", type=parse_range, default=(0.85, 1.15))
    parser.add_argument("--perturbed-friction-mu-range", type=parse_range, default=(0.25, 0.35))
    parser.add_argument("--nominal-randomization", action="append", default=[])
    parser.add_argument("--perturbed-randomization", action="append", default=[])
    parser.add_argument("--target-obstacle-distance", type=float, default=12.0)
    parser.add_argument("--min-probe-steps", type=int, default=10)
    parser.add_argument("--max-probe-steps", type=int, default=180)
    parser.add_argument("--allow-pre-friction-snapshot", action="store_true")
    parser.add_argument("--min-hidden-updates-after-friction", type=int, default=2)
    parser.add_argument("--max-observation-distance", type=float, default=0.75)
    parser.add_argument("--max-continuation-steps", type=int, default=0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="hidden_swap_gate", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_env_config(args.env_config)
    target_obs_dim = int(make_env_from_config(base_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(args.checkpoint, device=args.device, obs_dim=target_obs_dim)
    if not model.is_online_recurrent:
        raise ValueError("hidden-swap gate requires an online recurrent checkpoint")

    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    nominal_randomization = parse_randomization_overrides(args.nominal_randomization)
    perturbed_randomization = parse_randomization_overrides(args.perturbed_randomization)
    pairs, replays, summary = run_hidden_swap_gate(
        model=model,
        base_config=base_config,
        seeds=seeds,
        nominal_friction_mu_range=args.nominal_friction_mu_range,
        perturbed_friction_mu_range=args.perturbed_friction_mu_range,
        nominal_randomization=nominal_randomization,
        perturbed_randomization=perturbed_randomization,
        target_obstacle_distance=args.target_obstacle_distance,
        min_probe_steps=args.min_probe_steps,
        max_probe_steps=args.max_probe_steps,
        require_friction_step=not args.allow_pre_friction_snapshot,
        min_hidden_updates_after_friction=args.min_hidden_updates_after_friction,
        max_observation_distance=args.max_observation_distance,
        max_continuation_steps=args.max_continuation_steps,
    )

    pairs_csv = run_dir / "pairs.csv"
    replays_csv = run_dir / "replays.csv"
    summary_csv = run_dir / "summary.csv"
    pairs.to_csv(pairs_csv, index=False)
    replays.to_csv(replays_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "hidden_swap_gate",
            "env_config": args.env_config,
            "checkpoint": args.checkpoint,
            "episodes": len(seeds),
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "nominal_friction_mu_range": args.nominal_friction_mu_range,
            "perturbed_friction_mu_range": args.perturbed_friction_mu_range,
            "nominal_randomization": nominal_randomization,
            "perturbed_randomization": perturbed_randomization,
            "target_obstacle_distance": args.target_obstacle_distance,
            "min_probe_steps": args.min_probe_steps,
            "max_probe_steps": args.max_probe_steps,
            "require_friction_step": not args.allow_pre_friction_snapshot,
            "min_hidden_updates_after_friction": args.min_hidden_updates_after_friction,
            "max_observation_distance": args.max_observation_distance,
            "max_continuation_steps": args.max_continuation_steps,
            "pairs_csv": pairs_csv,
            "replays_csv": replays_csv,
            "summary_csv": summary_csv,
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
