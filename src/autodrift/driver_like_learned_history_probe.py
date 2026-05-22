"""Regularized learned-history probe for M143 driver-like input profiles."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.driver_like_input_profile_audit import (
    DRIVER_LIKE_PROFILE_ORDER,
    driver_like_history_sequence,
    profile_spec_rows,
    summarize_profile_deltas,
)
from autodrift.input_observability_audit import TARGETS, collect_input_observability_dataset, split_by_episode
from autodrift.learned_history_observability_probe import (
    LearnedProbeConfig,
    resolve_device,
    train_learned_history_probe,
)
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM


def run_driver_like_learned_history_probe(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_window: int,
    config: LearnedProbeConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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
    for offset, profile in enumerate(DRIVER_LIKE_PROFILE_ORDER):
        sequence = driver_like_history_sequence(frames, profile)
        probe_rows.extend(
            train_learned_history_probe(
                features=sequence,
                targets=target_matrix,
                train_mask=train_mask,
                profile=profile,
                history_window_steps=history_window,
                config=config,
                seed=seed + 101 + 37 * offset,
            )
        )
    delta_rows = summarize_profile_deltas(probe_rows)
    return sample_rows, probe_rows, delta_rows


def aggregate_probe_rows(delta_rows: list[dict[str, Any]]) -> dict[str, float]:
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
    summary: dict[str, float] = {}
    for metric in metrics:
        values = np.asarray([float(row[metric]) for row in delta_rows], dtype=np.float64)
        finite = values[np.isfinite(values)]
        summary[f"mean_{metric}"] = float(np.mean(finite)) if len(finite) else float("nan")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a learned-history probe over the M143 input profiles.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9450)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--history-window", type=int, default=50)
    parser.add_argument("--hidden-size", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

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
    sample_rows, probe_rows, delta_rows = run_driver_like_learned_history_probe(
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

    run_dir = args.run_dir or make_run_dir(prefix="driver_like_learned_history_probe", seed=args.seed)
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
            "run_type": "driver_like_learned_history_probe",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_window": args.history_window,
            "targets": TARGETS,
            "feature_profiles": DRIVER_LIKE_PROFILE_ORDER,
            "profile_delta_summary": delta_rows,
            "aggregate_profile_deltas": aggregate_probe_rows(delta_rows),
            "config": config.__dict__,
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "driver_like_learned_history_probe",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_window": args.history_window,
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
