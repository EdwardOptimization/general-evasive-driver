"""Per-step continuation snippets for critical closed-loop scenarios."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import load_seed_csv, parse_checkpoint_specs
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy, load_env_config
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.policies import Policy, make_policy


STEP_INFO_FIELDS = [
    "mu",
    "initial_mu",
    "mass_scale",
    "inertia_scale",
    "cg_shift",
    "brake_scale",
    "drive_scale",
    "tire_stiffness_scale",
    "steer_tau_scale",
    "drive_tau_scale",
    "speed",
    "speed_ref",
    "beta",
    "beta_target",
    "lateral_error",
    "heading_error",
    "curvature",
    "obstacle_distance",
    "obstacle_lateral_offset",
    "obstacle_required_lateral_offset",
    "obstacle_threshold_score",
    "obstacle_time_after_friction_step",
    "min_obstacle_clearance",
]
REWARD_TERM_FIELDS = [
    "progress",
    "drift_bonus",
    "rear_saturation",
    "track_cost",
    "heading_cost",
    "speed_cost",
    "beta_cost",
    "stable_aes_sideslip_cost",
    "pass_reward",
    "collision_penalty",
    "termination_penalty",
]


@dataclass(frozen=True)
class TracePolicySpec:
    label: str
    kind: str
    checkpoint: Path | None = None
    ablation: str = "none"


def parse_policy_specs(policy_names: list[str], checkpoint_specs: list[str]) -> list[TracePolicySpec]:
    specs = [TracePolicySpec(label=name, kind=name) for name in policy_names]
    specs.extend(
        TracePolicySpec(label=label, kind="checkpoint", checkpoint=path, ablation=ablation)
        for label, path, ablation in parse_checkpoint_specs(checkpoint_specs)
    )
    if not specs:
        raise ValueError("at least one policy or checkpoint-policy is required")
    labels = [spec.label for spec in specs]
    duplicated = sorted({label for label in labels if labels.count(label) > 1})
    if duplicated:
        raise ValueError(f"duplicate policy labels: {duplicated}")
    return specs


def _load_checkpoint_policy(
    spec: TracePolicySpec,
    *,
    env_config: DriftEnvConfig,
    obs_dim: int,
    device: str,
) -> ActorPolicy:
    if spec.checkpoint is None:
        raise ValueError(f"checkpoint spec {spec.label!r} is missing a checkpoint path")
    model, checkpoint_data = load_actor_critic_checkpoint(spec.checkpoint, device=device)
    metadata_env = checkpoint_data.get("metadata", {}).get("env")
    if model.obs_dim != obs_dim:
        model, _ = load_actor_critic_checkpoint(spec.checkpoint, device=device, obs_dim=obs_dim)
    del metadata_env
    return ActorPolicy(model, env_config, ablation=spec.ablation)


def _make_policy(spec: TracePolicySpec, env: AutoDriftEnv, seed: int, loaded: dict[str, ActorPolicy]) -> Policy:
    if spec.kind == "checkpoint":
        policy = loaded[spec.label]
        policy.reset()
        return policy
    return make_policy(spec.kind, env, seed=seed)


def _float_info(info: dict[str, Any], field: str) -> float:
    value = info.get(field, float("nan"))
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _collision_radius(env: AutoDriftEnv) -> float:
    if env.obstacle_scenario is None:
        return float("nan")
    return float(env.config.obstacle.ego_half_width + env.obstacle_scenario.obstacle_half_width)


def trace_episode(
    *,
    seed: int,
    spec: TracePolicySpec,
    env_config: DriftEnvConfig,
    loaded_checkpoint_policies: dict[str, ActorPolicy],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[np.ndarray], list[np.ndarray]]:
    env = AutoDriftEnv(env_config)
    policy = _make_policy(spec, env, seed, loaded_checkpoint_policies)
    obs, info = env.reset(seed=seed)
    policy.reset()

    rows: list[dict[str, Any]] = []
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    terminated = False
    truncated = False
    step_index = 0
    final_info = dict(info)
    while not (terminated or truncated):
        observations.append(np.asarray(obs, dtype=np.float32).copy())
        action = np.asarray(policy.act(obs, info), dtype=np.float32)
        actions.append(action.copy())
        pre_info = dict(info)
        pre_collision_radius = _collision_radius(env)
        obs, reward, terminated, truncated, info = env.step(action)
        final_info = dict(info)
        post_collision_radius = _collision_radius(env)
        rewards.append(float(reward))
        reason = terminal_reason(info, terminated, truncated, env_config) if (terminated or truncated) else ""
        reward_terms = info.get("reward_terms", {})
        pre_clearance_margin = _float_info(pre_info, "min_obstacle_clearance") - pre_collision_radius
        post_clearance_margin = _float_info(info, "min_obstacle_clearance") - post_collision_radius

        row: dict[str, Any] = {
            "seed": int(seed),
            "policy": spec.label,
            "step": int(step_index),
            "observation_index": len(observations) - 1,
            "action_steer": float(action[0]),
            "action_throttle": float(action[1]),
            "action_brake": float(action[2]),
            "reward": float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "terminal_reason": reason,
            "collision": bool(info.get("collision", False)),
            "obstacle_completed": bool(info.get("obstacle_completed", False)),
            "friction_step_applied": bool(info.get("friction_step_applied", False)),
            "friction_step_at": info.get("friction_step_at"),
            "pre_collision_radius": pre_collision_radius,
            "post_collision_radius": post_collision_radius,
            "pre_clearance_margin": pre_clearance_margin,
            "post_clearance_margin": post_clearance_margin,
        }
        for field in STEP_INFO_FIELDS:
            row[f"pre_{field}"] = _float_info(pre_info, field)
            row[f"post_{field}"] = _float_info(info, field)
        for field in REWARD_TERM_FIELDS:
            row[f"reward_{field}"] = float(reward_terms.get(field, 0.0))
        rows.append(row)
        step_index += 1

    reason = terminal_reason(final_info, terminated, truncated, env_config)
    summary = {
        "seed": int(seed),
        "policy": spec.label,
        "steps": int(len(rows)),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "terminal_reason": reason,
        "collision": bool(final_info.get("collision", False)),
        "obstacle_completed": bool(final_info.get("obstacle_completed", False)),
        "min_obstacle_clearance": _float_info(final_info, "min_obstacle_clearance"),
        "collision_radius": _collision_radius(env),
        "min_clearance_margin": _float_info(final_info, "min_obstacle_clearance") - _collision_radius(env),
        "final_obstacle_distance": _float_info(final_info, "obstacle_distance"),
        "mu": _float_info(final_info, "mu"),
        "initial_mu": _float_info(final_info, "initial_mu"),
        "obstacle_label": str(final_info.get("obstacle_label", "")),
    }
    return rows, summary, observations, actions


def build_action_delta_summary(steps: pd.DataFrame, baseline_policy: str) -> pd.DataFrame:
    if baseline_policy not in set(steps["policy"].astype(str)):
        raise ValueError(f"baseline policy {baseline_policy!r} not found in step traces")
    rows: list[dict[str, Any]] = []
    action_columns = ["action_steer", "action_throttle", "action_brake"]
    for seed in sorted(steps["seed"].unique()):
        seed_frame = steps[steps["seed"] == seed]
        baseline = seed_frame[seed_frame["policy"] == baseline_policy][["step", *action_columns]]
        for policy in sorted(set(seed_frame["policy"].astype(str)) - {baseline_policy}):
            candidate = seed_frame[seed_frame["policy"] == policy][["step", *action_columns]]
            joined = baseline.merge(candidate, on="step", suffixes=("_baseline", "_candidate"))
            if joined.empty:
                continue
            base_actions = joined[[f"{column}_baseline" for column in action_columns]].to_numpy(dtype=np.float64)
            cand_actions = joined[[f"{column}_candidate" for column in action_columns]].to_numpy(dtype=np.float64)
            diff = cand_actions - base_actions
            distances = np.linalg.norm(diff, axis=1)
            rows.append(
                {
                    "seed": int(seed),
                    "baseline_policy": baseline_policy,
                    "candidate_policy": policy,
                    "common_steps": int(len(joined)),
                    "first_action_distance": float(distances[0]),
                    "action_distance_mean": float(np.mean(distances)),
                    "action_distance_rms": float(np.sqrt(np.mean(np.square(distances)))),
                    "action_distance_max": float(np.max(distances)),
                    "steer_delta_mean": float(np.mean(diff[:, 0])),
                    "throttle_delta_mean": float(np.mean(diff[:, 1])),
                    "brake_delta_mean": float(np.mean(diff[:, 2])),
                }
            )
    return pd.DataFrame(rows)


def run_snippets(
    *,
    seeds: list[int],
    specs: list[TracePolicySpec],
    env_config: DriftEnvConfig,
    device: str,
    baseline_policy: str | None,
    run_dir: Path | str,
) -> dict[str, Any]:
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    sample_env = AutoDriftEnv(env_config)
    obs_dim = int(sample_env.observation_space.shape[0])
    loaded = {
        spec.label: _load_checkpoint_policy(spec, env_config=env_config, obs_dim=obs_dim, device=device)
        for spec in specs
        if spec.kind == "checkpoint"
    }

    step_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    observation_arrays: list[np.ndarray] = []
    action_arrays: list[np.ndarray] = []
    observation_offsets: list[int] = []
    for seed in seeds:
        for spec in specs:
            rows, summary, observations, actions = trace_episode(
                seed=seed,
                spec=spec,
                env_config=env_config,
                loaded_checkpoint_policies=loaded,
            )
            offset = len(observation_arrays)
            for row in rows:
                row["observation_index"] = int(row["observation_index"]) + offset
            observation_offsets.append(offset)
            step_rows.extend(rows)
            episode_rows.append(summary)
            observation_arrays.extend(observations)
            action_arrays.extend(actions)

    steps = pd.DataFrame(step_rows)
    episodes = pd.DataFrame(episode_rows)
    action_delta = (
        build_action_delta_summary(steps, baseline_policy)
        if baseline_policy is not None and not steps.empty
        else pd.DataFrame()
    )

    steps_csv = output / "steps.csv"
    episodes_csv = output / "episodes.csv"
    action_delta_csv = output / "action_delta_summary.csv"
    arrays_npz = output / "observations.npz"
    steps.to_csv(steps_csv, index=False)
    episodes.to_csv(episodes_csv, index=False)
    action_delta.to_csv(action_delta_csv, index=False)
    np.savez_compressed(
        arrays_npz,
        observations=np.asarray(observation_arrays, dtype=np.float32),
        actions=np.asarray(action_arrays, dtype=np.float32),
    )
    manifest = {
        "run_type": "continuation_snippets",
        "seeds": seeds,
        "policies": [
            {
                "label": spec.label,
                "kind": spec.kind,
                "checkpoint": spec.checkpoint,
                "ablation": spec.ablation,
            }
            for spec in specs
        ],
        "baseline_policy": baseline_policy,
        "device": device,
        "observation_count": len(observation_arrays),
        "observation_dim": obs_dim,
        "artifacts": {
            "steps_csv": steps_csv,
            "episodes_csv": episodes_csv,
            "action_delta_summary_csv": action_delta_csv,
            "observations_npz": arrays_npz,
        },
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace per-step continuation snippets on critical seeds.")
    parser.add_argument("--env-config", type=Path, default=None)
    parser.add_argument("--seed", type=int, action="append", default=[])
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument(
        "--policy",
        action="append",
        default=[],
        choices=["random", "heuristic", "aeb", "aes_heuristic", "envelope_aes"],
    )
    parser.add_argument("--checkpoint-policy", action="append", default=[])
    parser.add_argument("--baseline-policy", default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    seeds = list(args.seed)
    if args.seed_csv is not None:
        seeds.extend(load_seed_csv(args.seed_csv))
    if not seeds:
        raise ValueError("at least one --seed or --seed-csv seed is required")
    env_config = load_env_config(args.env_config) if args.env_config is not None else DriftEnvConfig()
    specs = parse_policy_specs(args.policy, args.checkpoint_policy)
    run_dir = args.run_dir or make_run_dir(prefix="continuation_snippets")
    manifest = run_snippets(
        seeds=seeds,
        specs=specs,
        env_config=env_config,
        device=args.device,
        baseline_policy=args.baseline_policy,
        run_dir=run_dir,
    )
    episodes = pd.read_csv(manifest["artifacts"]["episodes_csv"])
    print(episodes.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
