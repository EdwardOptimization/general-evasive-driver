"""M143 driver-like input profile observability audit.

This is a supervised probe harness. It compares deployable feature profiles
under the same dataset and ridge-regression settings before any PPO profile is
tuned independently.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.env import RAW_FRONT_REAR_WHEEL_OBSERVATION_MODES
from autodrift.evaluate import load_env_config
from autodrift.input_observability_audit import (
    HISTORY_MODES,
    TARGETS,
    collect_input_observability_dataset,
    parse_history_windows,
    regression_probe_results_to_rows,
    split_by_episode,
    train_ridge_regression_probe,
)
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


P0_CURRENT_BASELINE = "p0_current_baseline"
P1_DRIVER_LIKE_MINIMAL = "p1_driver_like_minimal"
P2_DRIVER_LIKE_NO_STEERING_FEEL = "p2_driver_like_no_steering_feel"
P3_DRIVER_LIKE_RAW_WHEEL = "p3_driver_like_raw_wheel"
P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL = "p4_driver_like_raw_wheel_vparallel"

DRIVER_LIKE_PROFILE_ORDER = (
    P0_CURRENT_BASELINE,
    P1_DRIVER_LIKE_MINIMAL,
    P2_DRIVER_LIKE_NO_STEERING_FEEL,
    P3_DRIVER_LIKE_RAW_WHEEL,
    P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL,
)


@dataclass(frozen=True)
class ProfileSpec:
    name: str
    description: str
    per_frame_indices: tuple[int, ...]
    missing_intended_channels: tuple[str, ...] = ()


def profile_specs() -> tuple[ProfileSpec, ...]:
    context_indices = tuple(range(WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_OBS_DIM))
    current_baseline_response = tuple(range(0, 12))
    driver_like_with_steer_rate = (
        2,  # yaw_rate
        3,  # ax
        4,  # ay
        5,  # actual steering angle
        6,  # steering-rate proxy for steering feel; true torque/EPS is unavailable.
        7,  # throttle actuator state
        8,  # brake actuator state
        9,  # previous steering command
        10,  # previous physical throttle command
        11,  # previous physical brake command
    )
    driver_like_no_steer_rate = tuple(index for index in driver_like_with_steer_rate if index != 6)
    raw_wheel_speed = (12, 13)
    local_ground_speed = (14, 15)
    return (
        ProfileSpec(
            name=P0_CURRENT_BASELINE,
            description="current no-wheel human-view baseline: body response, previous commands, road/obstacle context",
            per_frame_indices=current_baseline_response + context_indices,
        ),
        ProfileSpec(
            name=P1_DRIVER_LIKE_MINIMAL,
            description="driver-like minimal with steer-rate proxy: commands, actuator actuals, IMU/yaw response, scene",
            per_frame_indices=driver_like_with_steer_rate + context_indices,
            missing_intended_channels=("steering_torque_or_eps_current",),
        ),
        ProfileSpec(
            name=P2_DRIVER_LIKE_NO_STEERING_FEEL,
            description="driver-like minimal with the steer-rate proxy removed",
            per_frame_indices=driver_like_no_steer_rate + context_indices,
            missing_intended_channels=("steering_torque_or_eps_current",),
        ),
        ProfileSpec(
            name=P3_DRIVER_LIKE_RAW_WHEEL,
            description="P1 plus raw front/rear wheel circumferential speeds from the current single-track proxy",
            per_frame_indices=driver_like_with_steer_rate + raw_wheel_speed + context_indices,
            missing_intended_channels=("steering_torque_or_eps_current", "four_wheel_speeds"),
        ),
        ProfileSpec(
            name=P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL,
            description="P3 plus front/rear local ground-speed slots; diagnostic low-level-fusion comparison only",
            per_frame_indices=driver_like_with_steer_rate + raw_wheel_speed + local_ground_speed + context_indices,
            missing_intended_channels=("steering_torque_or_eps_current", "four_wheel_speeds", "four_wheel_v_parallel"),
        ),
    )


def profile_spec_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in profile_specs():
        rows.append(
            {
                "profile": spec.name,
                "feature_count_per_frame": len(spec.per_frame_indices),
                "indices": " ".join(str(index) for index in spec.per_frame_indices),
                "description": spec.description,
                "missing_intended_channels": " ".join(spec.missing_intended_channels),
            }
        )
    return rows


def build_driver_like_feature_profiles(observations: np.ndarray) -> dict[str, np.ndarray]:
    observations = np.asarray(observations, dtype=np.float32)
    if observations.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if observations.shape[1] % WHEEL_HUMAN_VIEW_OBS_DIM != 0:
        raise ValueError(
            "driver-like input profile audit requires one or more concatenated "
            f"{WHEEL_HUMAN_VIEW_OBS_DIM}-value wheel-response frames"
        )
    frame_count = observations.shape[1] // WHEEL_HUMAN_VIEW_OBS_DIM
    frames = observations.reshape(observations.shape[0], frame_count, WHEEL_HUMAN_VIEW_OBS_DIM)
    features: dict[str, np.ndarray] = {}
    for spec in profile_specs():
        selected = frames[:, :, list(spec.per_frame_indices)]
        features[spec.name] = selected.reshape(observations.shape[0], -1).astype(np.float32)
    return features


def summarize_profile_deltas(probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = {}
    for row in probe_rows:
        key = (str(row["target"]), int(row["history_window_steps"]), str(row["history_mode"]))
        by_key.setdefault(key, {})[str(row["feature_set"])] = row

    def metric_delta(rows: dict[str, dict[str, Any]], left: str, right: str, metric: str) -> float:
        if left not in rows or right not in rows:
            return float("nan")
        return float(rows[left][metric]) - float(rows[right][metric])

    delta_rows: list[dict[str, Any]] = []
    for (target, history_window_steps, history_mode), rows in sorted(by_key.items()):
        delta_rows.append(
            {
                "target": target,
                "history_window_steps": history_window_steps,
                "history_mode": history_mode,
                "p1_minus_p0_test_r2": metric_delta(rows, P1_DRIVER_LIKE_MINIMAL, P0_CURRENT_BASELINE, "test_r2"),
                "p1_minus_p0_mae_improvement": metric_delta(
                    rows, P1_DRIVER_LIKE_MINIMAL, P0_CURRENT_BASELINE, "mae_improvement"
                ),
                "steer_proxy_p1_minus_p2_test_r2": metric_delta(
                    rows, P1_DRIVER_LIKE_MINIMAL, P2_DRIVER_LIKE_NO_STEERING_FEEL, "test_r2"
                ),
                "steer_proxy_p1_minus_p2_mae_improvement": metric_delta(
                    rows, P1_DRIVER_LIKE_MINIMAL, P2_DRIVER_LIKE_NO_STEERING_FEEL, "mae_improvement"
                ),
                "raw_wheel_p3_minus_p1_test_r2": metric_delta(
                    rows, P3_DRIVER_LIKE_RAW_WHEEL, P1_DRIVER_LIKE_MINIMAL, "test_r2"
                ),
                "raw_wheel_p3_minus_p1_mae_improvement": metric_delta(
                    rows, P3_DRIVER_LIKE_RAW_WHEEL, P1_DRIVER_LIKE_MINIMAL, "mae_improvement"
                ),
                "vparallel_p4_minus_p3_test_r2": metric_delta(
                    rows, P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL, P3_DRIVER_LIKE_RAW_WHEEL, "test_r2"
                ),
                "vparallel_p4_minus_p3_mae_improvement": metric_delta(
                    rows, P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL, P3_DRIVER_LIKE_RAW_WHEEL, "mae_improvement"
                ),
                "status": "ok" if all(profile in rows for profile in DRIVER_LIKE_PROFILE_ORDER) else "skipped",
            }
        )
    return delta_rows


def aggregate_profile_deltas(delta_rows: list[dict[str, Any]]) -> dict[str, float]:
    metrics = (
        "p1_minus_p0_test_r2",
        "p1_minus_p0_mae_improvement",
        "steer_proxy_p1_minus_p2_test_r2",
        "steer_proxy_p1_minus_p2_mae_improvement",
        "raw_wheel_p3_minus_p1_test_r2",
        "raw_wheel_p3_minus_p1_mae_improvement",
        "vparallel_p4_minus_p3_test_r2",
        "vparallel_p4_minus_p3_mae_improvement",
    )
    aggregate: dict[str, float] = {}
    for metric in metrics:
        values = np.asarray([float(row[metric]) for row in delta_rows if row.get("status") == "ok"], dtype=np.float64)
        finite = values[np.isfinite(values)]
        aggregate[f"mean_{metric}"] = float(np.mean(finite)) if len(finite) else float("nan")
    return aggregate


def run_driver_like_input_profile_audit(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None = None,
    train_fraction: float = 0.70,
    ridge: float = 0.1,
    history_windows: tuple[int, ...] = (1,),
    history_mode: str = "raw",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
    env_config = load_env_config(env_config_path)
    if env_config.wheel_observation_mode not in RAW_FRONT_REAR_WHEEL_OBSERVATION_MODES:
        raise ValueError("M143 audit requires a raw front/rear wheel mode for P3/P4 profile comparison")
    if env_config.wheel_observation_mode != "front_rear_omega_ground":
        raise ValueError("M143 P4 semantics require wheel_observation_mode='front_rear_omega_ground'")
    if env_config.obstacle_relative_velocity_mode != "zero":
        raise ValueError("M143 audit requires obstacle_relative_velocity_mode='zero' to avoid context velocity proxies")

    observations_by_window, targets, sample_rows = collect_input_observability_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        history_windows=history_windows,
        history_mode=history_mode,
    )
    if len(sample_rows) == 0:
        raise ValueError("driver-like input profile audit dataset is empty")

    train_mask = split_by_episode(sample_rows, train_fraction=train_fraction, seed=seed + 31)
    results = []
    for history_window_steps, observations in observations_by_window.items():
        feature_profiles = build_driver_like_feature_profiles(observations)
        for target_name, target_values in targets.items():
            for profile_name in DRIVER_LIKE_PROFILE_ORDER:
                results.append(
                    train_ridge_regression_probe(
                        features=feature_profiles[profile_name],
                        targets=target_values,
                        train_mask=train_mask,
                        target_name=target_name,
                        feature_set=profile_name,
                        ridge=ridge,
                        history_window_steps=history_window_steps,
                        history_mode=history_mode,
                    )
                )
    probe_rows = regression_probe_results_to_rows(results)
    delta_rows = summarize_profile_deltas(probe_rows)
    aggregate = aggregate_profile_deltas(delta_rows)
    return sample_rows, probe_rows, delta_rows, aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M143 driver-like input profile audit.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=9440)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--history-windows", type=parse_history_windows, default=(1, 10, 25))
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    sample_rows, probe_rows, delta_rows, aggregate = run_driver_like_input_profile_audit(
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        ridge=args.ridge,
        history_windows=args.history_windows,
        history_mode=args.history_mode,
    )

    run_dir = args.run_dir or make_run_dir(prefix="m143_driver_like_input_profile_audit", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    probe_summary_csv = run_dir / "probe_summary.csv"
    profile_delta_csv = run_dir / "profile_delta_summary.csv"
    profile_spec_csv = run_dir / "profile_spec.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(samples_csv, sample_rows)
    write_csv_rows(probe_summary_csv, probe_rows)
    write_csv_rows(profile_delta_csv, delta_rows)
    write_csv_rows(profile_spec_csv, profile_spec_rows())
    write_json(
        summary_json,
        {
            "run_type": "driver_like_input_profile_audit",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_windows": args.history_windows,
            "history_mode": args.history_mode,
            "targets": TARGETS,
            "feature_profiles": DRIVER_LIKE_PROFILE_ORDER,
            "profile_delta_summary": delta_rows,
            "aggregate_profile_deltas": aggregate,
            "single_track_limitations": {
                "steering_feel": "true steering torque/EPS current unavailable; P1 uses steering-rate proxy",
                "wheel_speeds": "current simulator exposes front/rear proxy speeds, not four-wheel sensors",
                "v_parallel": "P4 uses front/rear bicycle local ground-speed slots and is diagnostic only",
            },
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "driver_like_input_profile_audit",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_windows": args.history_windows,
            "history_mode": args.history_mode,
            "artifacts": {
                "samples_csv": samples_csv,
                "probe_summary_csv": probe_summary_csv,
                "profile_delta_summary_csv": profile_delta_csv,
                "profile_spec_csv": profile_spec_csv,
                "summary_json": summary_json,
            },
        },
    )
    print(pd.DataFrame(delta_rows).to_string(index=False))


if __name__ == "__main__":
    main()
