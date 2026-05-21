"""Supervised input observability probes for deployable AutoDrift signals."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import load_env_config
from autodrift.policies import make_policy
from autodrift.train_ppo import HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


P0_NO_WHEEL_RESPONSE_CONTEXT = "p0_no_wheel_response_context"
P1_WHEEL_RESPONSE_CONTEXT = "p1_wheel_response_context"
P0_RESPONSE_ONLY = "p0_response_only"
P1_RESPONSE_ONLY = "p1_response_only"
WHEEL_ONLY = "wheel_only"
CONTEXT_ONLY = "context_only"
INPUT_OBSERVABILITY_PROFILES = (
    P0_NO_WHEEL_RESPONSE_CONTEXT,
    P1_WHEEL_RESPONSE_CONTEXT,
    P0_RESPONSE_ONLY,
    P1_RESPONSE_ONLY,
    WHEEL_ONLY,
    CONTEXT_ONLY,
)
TARGETS = (
    "future_braking_deceleration",
    "future_yaw_response",
    "future_lateral_accel_response",
)


@dataclass(frozen=True)
class RegressionProbeResult:
    target: str
    feature_set: str
    train_samples: int
    test_samples: int
    train_r2: float
    test_r2: float
    test_mae: float
    baseline_mae: float
    mae_improvement: float
    status: str = "ok"


def build_input_feature_profiles(observations: np.ndarray) -> dict[str, np.ndarray]:
    if observations.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if observations.shape[1] < WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM:
        raise ValueError("input observability audit requires wheel-response observations")
    body_end = HUMAN_VIEW_RESPONSE_FEATURE_DIM
    wheel_end = WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM
    return {
        P0_NO_WHEEL_RESPONSE_CONTEXT: np.concatenate([observations[:, :body_end], observations[:, wheel_end:]], axis=1)
        .astype(np.float32),
        P1_WHEEL_RESPONSE_CONTEXT: observations.astype(np.float32),
        P0_RESPONSE_ONLY: observations[:, :body_end].astype(np.float32),
        P1_RESPONSE_ONLY: observations[:, :wheel_end].astype(np.float32),
        WHEEL_ONLY: observations[:, body_end:wheel_end].astype(np.float32),
        CONTEXT_ONLY: observations[:, wheel_end:].astype(np.float32),
    }


def _rollout_probe(env: AutoDriftEnv, action: np.ndarray, horizon_steps: int) -> tuple[AutoDriftEnv, list[float]]:
    probe_env = copy.deepcopy(env)
    ay_values: list[float] = []
    for _ in range(horizon_steps):
        _, _, terminated, truncated, _ = probe_env.step(action)
        _, ay_body = probe_env._body_acceleration(probe_env.last_forces)
        ay_values.append(float(ay_body))
        if terminated or truncated:
            break
    return probe_env, ay_values


def future_envelope_targets(env: AutoDriftEnv, horizon_steps: int) -> dict[str, float]:
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be at least 1")
    initial_vx = float(env.state.vx)
    initial_yaw_rate = float(env.state.yaw_rate)
    elapsed = max(horizon_steps * env.config.dt, env.config.dt)

    brake_env, _ = _rollout_probe(
        env,
        np.asarray([0.0, -1.0, 1.0], dtype=np.float32),
        horizon_steps,
    )
    braking_deceleration = max(0.0, (initial_vx - float(brake_env.state.vx)) / elapsed)

    steer_env, ay_values = _rollout_probe(
        env,
        np.asarray([0.65, -1.0, -1.0], dtype=np.float32),
        horizon_steps,
    )
    yaw_response = abs(float(steer_env.state.yaw_rate) - initial_yaw_rate) / elapsed
    lateral_accel_response = max((abs(value) for value in ay_values), default=0.0)
    return {
        "future_braking_deceleration": float(braking_deceleration),
        "future_yaw_response": float(yaw_response),
        "future_lateral_accel_response": float(lateral_accel_response),
    }


def split_by_episode(rows: list[dict[str, Any]], train_fraction: float, seed: int) -> np.ndarray:
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    episodes = np.asarray(sorted({int(row["episode"]) for row in rows}), dtype=np.int64)
    if len(episodes) < 2:
        raise ValueError("at least two episodes are required for an episode-disjoint split")
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(episodes)
    train_count = int(round(len(shuffled) * train_fraction))
    train_count = min(max(train_count, 1), len(shuffled) - 1)
    train_episodes = set(int(item) for item in shuffled[:train_count])
    return np.asarray([int(row["episode"]) in train_episodes for row in rows], dtype=bool)


def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = float(np.sum(np.square(y_true - np.mean(y_true))))
    if denom <= 1e-12:
        return float("nan")
    return float(1.0 - float(np.sum(np.square(y_true - y_pred))) / denom)


def train_ridge_regression_probe(
    features: np.ndarray,
    targets: np.ndarray,
    train_mask: np.ndarray,
    target_name: str,
    feature_set: str,
    ridge: float = 1e-4,
) -> RegressionProbeResult:
    train_x = features[train_mask].astype(np.float64)
    test_x = features[~train_mask].astype(np.float64)
    train_y = targets[train_mask].astype(np.float64)
    test_y = targets[~train_mask].astype(np.float64)
    if len(train_y) < 2 or len(test_y) == 0:
        return RegressionProbeResult(
            target=target_name,
            feature_set=feature_set,
            train_samples=int(len(train_y)),
            test_samples=int(len(test_y)),
            train_r2=float("nan"),
            test_r2=float("nan"),
            test_mae=float("nan"),
            baseline_mae=float("nan"),
            mae_improvement=float("nan"),
            status="skipped_insufficient_samples",
        )

    mean = train_x.mean(axis=0, keepdims=True)
    std = train_x.std(axis=0, keepdims=True) + 1e-6
    train_x = (train_x - mean) / std
    test_x = (test_x - mean) / std
    train_design = np.concatenate([train_x, np.ones((train_x.shape[0], 1), dtype=np.float64)], axis=1)
    test_design = np.concatenate([test_x, np.ones((test_x.shape[0], 1), dtype=np.float64)], axis=1)
    gram = train_design.T @ train_design
    penalty = ridge * np.eye(gram.shape[0], dtype=np.float64)
    penalty[-1, -1] = 0.0
    weights = np.linalg.solve(gram + penalty, train_design.T @ train_y)
    train_pred = train_design @ weights
    test_pred = test_design @ weights
    baseline_pred = np.full_like(test_y, train_y.mean())
    test_mae = float(np.mean(np.abs(test_y - test_pred)))
    baseline_mae = float(np.mean(np.abs(test_y - baseline_pred)))
    return RegressionProbeResult(
        target=target_name,
        feature_set=feature_set,
        train_samples=int(len(train_y)),
        test_samples=int(len(test_y)),
        train_r2=_r2_score(train_y, train_pred),
        test_r2=_r2_score(test_y, test_pred),
        test_mae=test_mae,
        baseline_mae=baseline_mae,
        mae_improvement=float(baseline_mae - test_mae),
    )


def regression_probe_results_to_rows(results: list[RegressionProbeResult]) -> list[dict[str, Any]]:
    return [result.__dict__ for result in results]


def summarize_profile_gains(results: list[RegressionProbeResult]) -> list[dict[str, Any]]:
    by_target: dict[str, dict[str, RegressionProbeResult]] = {}
    for result in results:
        by_target.setdefault(result.target, {})[result.feature_set] = result
    rows: list[dict[str, Any]] = []
    for target, feature_results in sorted(by_target.items()):
        p0 = feature_results[P0_NO_WHEEL_RESPONSE_CONTEXT]
        p1 = feature_results[P1_WHEEL_RESPONSE_CONTEXT]
        p0_response = feature_results[P0_RESPONSE_ONLY]
        p1_response = feature_results[P1_RESPONSE_ONLY]
        rows.append(
            {
                "target": target,
                "p0_no_wheel_test_r2": p0.test_r2,
                "p1_wheel_test_r2": p1.test_r2,
                "p1_minus_p0_test_r2": p1.test_r2 - p0.test_r2,
                "p0_no_wheel_mae_improvement": p0.mae_improvement,
                "p1_wheel_mae_improvement": p1.mae_improvement,
                "p1_minus_p0_mae_improvement": p1.mae_improvement - p0.mae_improvement,
                "p0_response_only_test_r2": p0_response.test_r2,
                "p1_response_only_test_r2": p1_response.test_r2,
                "p1_response_minus_p0_response_test_r2": p1_response.test_r2 - p0_response.test_r2,
                "status": "ok" if p0.status == "ok" and p1.status == "ok" else "skipped",
            }
        )
    return rows


def collect_input_observability_dataset(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
) -> tuple[np.ndarray, dict[str, np.ndarray], list[dict[str, Any]]]:
    env_config = load_env_config(env_config_path)
    env = AutoDriftEnv(env_config)
    if env_config.wheel_observation_mode != "front_rear":
        raise ValueError("input observability audit currently requires wheel_observation_mode='front_rear'")
    policy = make_policy(policy_name, env, seed=seed)
    observations: list[np.ndarray] = []
    targets: dict[str, list[float]] = {name: [] for name in TARGETS}
    rows: list[dict[str, Any]] = []

    for episode in range(episodes):
        episode_seed = seed + episode
        obs, info = env.reset(seed=episode_seed)
        policy.reset()
        terminated = False
        truncated = False
        while not (terminated or truncated):
            if int(info["step"]) % sample_stride == 0:
                target_values = future_envelope_targets(env, horizon_steps=horizon_steps)
                observations.append(obs.astype(np.float32))
                for name in TARGETS:
                    targets[name].append(float(target_values[name]))
                rows.append(
                    {
                        "episode": episode,
                        "seed": episode_seed,
                        "step": int(info["step"]),
                        "policy": policy_name,
                        "obstacle_label": str(info.get("obstacle_label", "")),
                        **target_values,
                    }
                )
                if max_samples is not None and len(rows) >= max_samples:
                    return (
                        np.asarray(observations, dtype=np.float32),
                        {name: np.asarray(values, dtype=np.float32) for name, values in targets.items()},
                        rows,
                    )
            action = policy.act(obs, info)
            obs, _, terminated, truncated, info = env.step(action)
    return (
        np.asarray(observations, dtype=np.float32),
        {name: np.asarray(values, dtype=np.float32) for name, values in targets.items()},
        rows,
    )


def run_input_observability_audit(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None = None,
    train_fraction: float = 0.70,
    ridge: float = 1e-4,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    observations, targets, rows = collect_input_observability_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
    )
    if len(rows) == 0:
        raise ValueError("input observability dataset is empty")
    train_mask = split_by_episode(rows, train_fraction=train_fraction, seed=seed + 31)
    feature_profiles = build_input_feature_profiles(observations)
    results: list[RegressionProbeResult] = []
    for target_name, target_values in targets.items():
        for feature_name in INPUT_OBSERVABILITY_PROFILES:
            results.append(
                train_ridge_regression_probe(
                    features=feature_profiles[feature_name],
                    targets=target_values,
                    train_mask=train_mask,
                    target_name=target_name,
                    feature_set=feature_name,
                    ridge=ridge,
                )
            )
    return rows, regression_probe_results_to_rows(results), summarize_profile_gains(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit deployable input observability for future response envelope targets.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--seed", type=int, default=9300)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=5)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=1e-4)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    sample_rows, probe_rows, gain_rows = run_input_observability_audit(
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        ridge=args.ridge,
    )

    run_dir = args.run_dir or make_run_dir(prefix="input_observability_audit", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    probe_summary_csv = run_dir / "probe_summary.csv"
    profile_gain_csv = run_dir / "profile_gain_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    write_csv_rows(samples_csv, sample_rows)
    write_csv_rows(probe_summary_csv, probe_rows)
    write_csv_rows(profile_gain_csv, gain_rows)
    write_json(
        summary_json,
        {
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "feature_profiles": INPUT_OBSERVABILITY_PROFILES,
            "targets": TARGETS,
            "profile_gain_summary": gain_rows,
            "probe_results": probe_rows,
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "input_observability_audit",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "artifacts": {
                "samples_csv": samples_csv,
                "probe_summary_csv": probe_summary_csv,
                "profile_gain_summary_csv": profile_gain_csv,
                "summary_json": summary_json,
            },
        },
    )
    print(pd.DataFrame(gain_rows).to_string(index=False))


if __name__ == "__main__":
    main()
