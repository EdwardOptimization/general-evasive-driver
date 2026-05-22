"""M145 speed-cue audit for driver-like input profiles."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.driver_like_input_profile_audit import (
    P0_CURRENT_BASELINE,
    P1_DRIVER_LIKE_MINIMAL,
    driver_like_history_sequence,
    profile_spec_by_name,
)
from autodrift.input_observability_audit import (
    HISTORY_MODES,
    TARGETS,
    collect_input_observability_dataset,
    parse_history_windows,
    regression_probe_results_to_rows,
    split_by_episode,
    train_ridge_regression_probe,
)
from autodrift.learned_history_observability_probe import (
    LearnedProbeConfig,
    resolve_device,
    train_learned_history_probe,
)
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM


P5_DRIVER_LIKE_SPEEDOMETER = "p5_driver_like_speedometer"
P6_DRIVER_LIKE_EGO_VELOCITY = "p6_driver_like_ego_velocity"
SPEED_CUE_PROFILE_ORDER = (
    P0_CURRENT_BASELINE,
    P1_DRIVER_LIKE_MINIMAL,
    P5_DRIVER_LIKE_SPEEDOMETER,
    P6_DRIVER_LIKE_EGO_VELOCITY,
)


@dataclass(frozen=True)
class SpeedCueProfileSpec:
    name: str
    description: str
    per_frame_indices: tuple[int, ...]
    deployable_cues: tuple[str, ...]


def speed_cue_profile_specs() -> tuple[SpeedCueProfileSpec, ...]:
    base_specs = profile_spec_by_name()
    p1_indices = base_specs[P1_DRIVER_LIKE_MINIMAL].per_frame_indices
    return (
        SpeedCueProfileSpec(
            name=P0_CURRENT_BASELINE,
            description="current no-wheel human-view baseline",
            per_frame_indices=base_specs[P0_CURRENT_BASELINE].per_frame_indices,
            deployable_cues=("vx", "vy"),
        ),
        SpeedCueProfileSpec(
            name=P1_DRIVER_LIKE_MINIMAL,
            description="driver-like minimal without explicit speed cue",
            per_frame_indices=p1_indices,
            deployable_cues=(),
        ),
        SpeedCueProfileSpec(
            name=P5_DRIVER_LIKE_SPEEDOMETER,
            description="P1 plus longitudinal speedometer-like vx cue",
            per_frame_indices=(0,) + p1_indices,
            deployable_cues=("vx",),
        ),
        SpeedCueProfileSpec(
            name=P6_DRIVER_LIKE_EGO_VELOCITY,
            description="P1 plus body-frame ego velocity vx/vy cues",
            per_frame_indices=(0, 1) + p1_indices,
            deployable_cues=("vx", "vy"),
        ),
    )


def speed_cue_profile_spec_rows() -> list[dict[str, Any]]:
    return [
        {
            "profile": spec.name,
            "feature_count_per_frame": len(spec.per_frame_indices),
            "indices": " ".join(str(index) for index in spec.per_frame_indices),
            "description": spec.description,
            "deployable_cues": " ".join(spec.deployable_cues),
        }
        for spec in speed_cue_profile_specs()
    ]


def speed_cue_spec_by_name() -> dict[str, SpeedCueProfileSpec]:
    return {spec.name: spec for spec in speed_cue_profile_specs()}


def speed_cue_history_sequence(frames: np.ndarray, profile: str) -> np.ndarray:
    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3 or frames.shape[2] != WHEEL_HUMAN_VIEW_OBS_DIM:
        raise ValueError(
            "speed-cue history sequences require frames with shape "
            f"(samples, steps, {WHEEL_HUMAN_VIEW_OBS_DIM})"
        )
    specs = speed_cue_spec_by_name()
    if profile == P0_CURRENT_BASELINE or profile == P1_DRIVER_LIKE_MINIMAL:
        return driver_like_history_sequence(frames, profile)
    if profile not in specs:
        raise ValueError("unknown speed-cue profile: " + profile)
    return frames[:, :, list(specs[profile].per_frame_indices)].astype(np.float32)


def build_speed_cue_feature_profiles(observations: np.ndarray) -> dict[str, np.ndarray]:
    observations = np.asarray(observations, dtype=np.float32)
    if observations.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if observations.shape[1] % WHEEL_HUMAN_VIEW_OBS_DIM != 0:
        raise ValueError(
            "speed-cue audit requires one or more concatenated "
            f"{WHEEL_HUMAN_VIEW_OBS_DIM}-value wheel-response frames"
        )
    frame_count = observations.shape[1] // WHEEL_HUMAN_VIEW_OBS_DIM
    frames = observations.reshape(observations.shape[0], frame_count, WHEEL_HUMAN_VIEW_OBS_DIM)
    return {
        profile: speed_cue_history_sequence(frames, profile).reshape(observations.shape[0], -1).astype(np.float32)
        for profile in SPEED_CUE_PROFILE_ORDER
    }


def summarize_speed_cue_deltas(probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = {}
    for row in probe_rows:
        key = (str(row["target"]), int(row["history_window_steps"]), str(row["history_mode"]))
        by_key.setdefault(key, {})[str(row["feature_set"])] = row

    def delta(rows: dict[str, dict[str, Any]], left: str, right: str, metric: str) -> float:
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
                "p1_minus_p0_test_r2": delta(rows, P1_DRIVER_LIKE_MINIMAL, P0_CURRENT_BASELINE, "test_r2"),
                "p1_minus_p0_mae_improvement": delta(
                    rows, P1_DRIVER_LIKE_MINIMAL, P0_CURRENT_BASELINE, "mae_improvement"
                ),
                "speedometer_p5_minus_p1_test_r2": delta(
                    rows, P5_DRIVER_LIKE_SPEEDOMETER, P1_DRIVER_LIKE_MINIMAL, "test_r2"
                ),
                "speedometer_p5_minus_p1_mae_improvement": delta(
                    rows, P5_DRIVER_LIKE_SPEEDOMETER, P1_DRIVER_LIKE_MINIMAL, "mae_improvement"
                ),
                "ego_velocity_p6_minus_p1_test_r2": delta(
                    rows, P6_DRIVER_LIKE_EGO_VELOCITY, P1_DRIVER_LIKE_MINIMAL, "test_r2"
                ),
                "ego_velocity_p6_minus_p1_mae_improvement": delta(
                    rows, P6_DRIVER_LIKE_EGO_VELOCITY, P1_DRIVER_LIKE_MINIMAL, "mae_improvement"
                ),
                "ego_velocity_p6_minus_p0_test_r2": delta(
                    rows, P6_DRIVER_LIKE_EGO_VELOCITY, P0_CURRENT_BASELINE, "test_r2"
                ),
                "ego_velocity_p6_minus_p0_mae_improvement": delta(
                    rows, P6_DRIVER_LIKE_EGO_VELOCITY, P0_CURRENT_BASELINE, "mae_improvement"
                ),
                "status": "ok" if all(profile in rows for profile in SPEED_CUE_PROFILE_ORDER) else "skipped",
            }
        )
    return delta_rows


def aggregate_speed_cue_deltas(delta_rows: list[dict[str, Any]]) -> dict[str, float]:
    metrics = (
        "p1_minus_p0_test_r2",
        "p1_minus_p0_mae_improvement",
        "speedometer_p5_minus_p1_test_r2",
        "speedometer_p5_minus_p1_mae_improvement",
        "ego_velocity_p6_minus_p1_test_r2",
        "ego_velocity_p6_minus_p1_mae_improvement",
        "ego_velocity_p6_minus_p0_test_r2",
        "ego_velocity_p6_minus_p0_mae_improvement",
    )
    aggregate: dict[str, float] = {}
    for metric in metrics:
        values = np.asarray([float(row[metric]) for row in delta_rows if row.get("status") == "ok"], dtype=np.float64)
        finite = values[np.isfinite(values)]
        aggregate[f"mean_{metric}"] = float(np.mean(finite)) if len(finite) else float("nan")
    return aggregate


def run_speed_cue_ridge_audit(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    train_fraction: float,
    ridge: float,
    history_windows: tuple[int, ...],
    history_mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
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
    train_mask = split_by_episode(sample_rows, train_fraction=train_fraction, seed=seed + 31)
    results = []
    for history_window_steps, observations in observations_by_window.items():
        feature_profiles = build_speed_cue_feature_profiles(observations)
        for target_name, target_values in targets.items():
            for profile_name in SPEED_CUE_PROFILE_ORDER:
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
    delta_rows = summarize_speed_cue_deltas(probe_rows)
    return sample_rows, probe_rows, delta_rows, aggregate_speed_cue_deltas(delta_rows)


def run_speed_cue_learned_history_probe(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_window: int,
    config: LearnedProbeConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
    observations_by_window, targets, sample_rows = collect_input_observability_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        history_windows=(history_window,),
        history_mode="raw",
    )
    observations = observations_by_window[history_window]
    frames = observations.reshape(observations.shape[0], history_window, WHEEL_HUMAN_VIEW_OBS_DIM)
    train_mask = split_by_episode(sample_rows, train_fraction=config.train_fraction, seed=seed + 31)
    target_matrix = np.stack([targets[name] for name in TARGETS], axis=1).astype(np.float32)

    probe_rows: list[dict[str, Any]] = []
    for offset, profile in enumerate(SPEED_CUE_PROFILE_ORDER):
        probe_rows.extend(
            train_learned_history_probe(
                features=speed_cue_history_sequence(frames, profile),
                targets=target_matrix,
                train_mask=train_mask,
                profile=profile,
                history_window_steps=history_window,
                config=config,
                seed=seed + 101 + 37 * offset,
            )
        )
    delta_rows = summarize_speed_cue_deltas(probe_rows)
    return sample_rows, probe_rows, delta_rows, aggregate_speed_cue_deltas(delta_rows)


def write_speed_cue_artifacts(
    run_dir: Path,
    run_type: str,
    args: argparse.Namespace,
    sample_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    aggregate: dict[str, float],
    config: LearnedProbeConfig | None = None,
) -> None:
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
    write_csv_rows(profile_spec_csv, speed_cue_profile_spec_rows())
    summary: dict[str, Any] = {
        "run_type": run_type,
        "env_config": args.env_config,
        "episodes": args.episodes,
        "samples": len(sample_rows),
        "seed": args.seed,
        "policy": args.policy,
        "horizon_steps": args.horizon_steps,
        "sample_stride": args.sample_stride,
        "targets": TARGETS,
        "feature_profiles": SPEED_CUE_PROFILE_ORDER,
        "profile_delta_summary": delta_rows,
        "aggregate_profile_deltas": aggregate,
    }
    if hasattr(args, "history_windows"):
        summary["history_windows"] = args.history_windows
        summary["history_mode"] = args.history_mode
    if hasattr(args, "history_window"):
        summary["history_window"] = args.history_window
    if config is not None:
        summary["config"] = config.__dict__
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": run_type,
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "artifacts": {
                "samples_csv": samples_csv,
                "probe_summary_csv": probe_summary_csv,
                "profile_delta_summary_csv": profile_delta_csv,
                "profile_spec_csv": profile_spec_csv,
                "summary_json": summary_json,
            },
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M145 deployable speed-cue profile audit.")
    parser.add_argument("--mode", choices=("ridge", "learned"), required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9460)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--history-windows", type=parse_history_windows, default=(1, 10, 25))
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--history-window", type=int, default=50)
    parser.add_argument("--hidden-size", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "ridge":
        sample_rows, probe_rows, delta_rows, aggregate = run_speed_cue_ridge_audit(
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
        run_dir = args.run_dir or make_run_dir(prefix="m145_speed_cue_ridge", seed=args.seed)
        write_speed_cue_artifacts(run_dir, "speed_cue_ridge_audit", args, sample_rows, probe_rows, delta_rows, aggregate)
    else:
        torch.set_num_threads(1)
        config = LearnedProbeConfig(
            hidden_size=args.hidden_size,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
            train_fraction=args.train_fraction,
            device=resolve_device(args.device),
        )
        sample_rows, probe_rows, delta_rows, aggregate = run_speed_cue_learned_history_probe(
            env_config_path=args.env_config,
            episodes=args.episodes,
            seed=args.seed,
            policy_name=args.policy,
            horizon_steps=args.horizon_steps,
            sample_stride=args.sample_stride,
            max_samples=args.max_samples,
            history_window=args.history_window,
            config=config,
        )
        run_dir = args.run_dir or make_run_dir(prefix="m145_speed_cue_learned", seed=args.seed)
        write_speed_cue_artifacts(
            run_dir,
            "speed_cue_learned_history_probe",
            args,
            sample_rows,
            probe_rows,
            delta_rows,
            aggregate,
            config=config,
        )
    print(pd.DataFrame(delta_rows).to_string(index=False))


if __name__ == "__main__":
    main()
