"""Learned supervised history probes for AutoDrift self-identification inputs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.input_observability_audit import (
    P0_RESPONSE_ONLY,
    P1_RESPONSE_ONLY,
    TARGETS,
    build_input_feature_profiles,
    collect_input_observability_dataset,
    split_by_episode,
    train_ridge_regression_probe,
)
from autodrift.train_ppo import (
    HUMAN_VIEW_RESPONSE_FEATURE_DIM,
    WHEEL_HUMAN_VIEW_OBS_DIM,
    WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM,
)


P0_RESPONSE_HISTORY = "p0_response_history"
P1_RESPONSE_HISTORY = "p1_response_history"
P0_CURRENT_RIDGE = "p0_current_ridge"
P1_CURRENT_RIDGE = "p1_current_ridge"


@dataclass(frozen=True)
class LearnedProbeConfig:
    hidden_size: int = 64
    epochs: int = 80
    batch_size: int = 128
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    train_fraction: float = 0.70
    device: str = "cpu"


class HistoryGRURegressor(nn.Module):
    def __init__(self, input_dim: int, hidden_size: int, output_dim: int):
        super().__init__()
        self.encoder = nn.GRU(input_dim, hidden_size, batch_first=True)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, output_dim),
        )

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        _, hidden = self.encoder(sequence)
        return self.head(hidden[-1])


def response_history_sequence(frames: np.ndarray, profile: str) -> np.ndarray:
    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3 or frames.shape[2] != WHEEL_HUMAN_VIEW_OBS_DIM:
        raise ValueError(
            "history frames must have shape (samples, steps, "
            f"{WHEEL_HUMAN_VIEW_OBS_DIM})"
        )
    if profile == P0_RESPONSE_HISTORY:
        return frames[:, :, :HUMAN_VIEW_RESPONSE_FEATURE_DIM].astype(np.float32)
    if profile == P1_RESPONSE_HISTORY:
        return frames[:, :, :WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM].astype(np.float32)
    raise ValueError(f"unknown learned history profile: {profile}")


def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = float(np.sum(np.square(y_true - np.mean(y_true))))
    if denom <= 1e-12:
        return float("nan")
    return float(1.0 - float(np.sum(np.square(y_true - y_pred))) / denom)


def metric_rows(
    profile: str,
    target_names: tuple[str, ...],
    train_targets: np.ndarray,
    test_targets: np.ndarray,
    train_pred: np.ndarray,
    test_pred: np.ndarray,
    history_window_steps: int,
    model_type: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, target in enumerate(target_names):
        baseline_pred = np.full_like(test_targets[:, index], train_targets[:, index].mean())
        test_mae = float(np.mean(np.abs(test_targets[:, index] - test_pred[:, index])))
        baseline_mae = float(np.mean(np.abs(test_targets[:, index] - baseline_pred)))
        rows.append(
            {
                "profile": profile,
                "feature_set": profile,
                "model_type": model_type,
                "target": target,
                "history_window_steps": history_window_steps,
                "history_mode": "raw",
                "train_samples": int(len(train_targets)),
                "test_samples": int(len(test_targets)),
                "train_r2": _r2_score(train_targets[:, index], train_pred[:, index]),
                "test_r2": _r2_score(test_targets[:, index], test_pred[:, index]),
                "test_mae": test_mae,
                "baseline_mae": baseline_mae,
                "mae_improvement": float(baseline_mae - test_mae),
                "status": "ok",
            }
        )
    return rows


def train_learned_history_probe(
    features: np.ndarray,
    targets: np.ndarray,
    train_mask: np.ndarray,
    profile: str,
    history_window_steps: int,
    config: LearnedProbeConfig,
    seed: int,
) -> list[dict[str, Any]]:
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    device = torch.device(config.device)

    train_x = features[train_mask].astype(np.float32)
    test_x = features[~train_mask].astype(np.float32)
    train_y = targets[train_mask].astype(np.float32)
    test_y = targets[~train_mask].astype(np.float32)
    if len(train_y) < 2 or len(test_y) == 0:
        raise ValueError("learned history probe requires non-empty train and test splits")

    x_mean = train_x.mean(axis=(0, 1), keepdims=True)
    x_std = train_x.std(axis=(0, 1), keepdims=True) + 1e-6
    y_mean = train_y.mean(axis=0, keepdims=True)
    y_std = train_y.std(axis=0, keepdims=True) + 1e-6

    train_x_t = torch.as_tensor((train_x - x_mean) / x_std, dtype=torch.float32, device=device)
    test_x_t = torch.as_tensor((test_x - x_mean) / x_std, dtype=torch.float32, device=device)
    train_y_t = torch.as_tensor((train_y - y_mean) / y_std, dtype=torch.float32, device=device)

    model = HistoryGRURegressor(
        input_dim=int(features.shape[2]),
        hidden_size=config.hidden_size,
        output_dim=len(TARGETS),
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    loss_fn = nn.MSELoss()

    for _ in range(config.epochs):
        order = rng.permutation(len(train_x))
        for start in range(0, len(order), config.batch_size):
            batch = torch.as_tensor(order[start : start + config.batch_size], dtype=torch.long, device=device)
            pred = model(train_x_t[batch])
            loss = loss_fn(pred, train_y_t[batch])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

    model.eval()
    with torch.no_grad():
        train_pred = model(train_x_t).cpu().numpy() * y_std + y_mean
        test_pred = model(test_x_t).cpu().numpy() * y_std + y_mean
    return metric_rows(
        profile=profile,
        target_names=TARGETS,
        train_targets=train_y,
        test_targets=test_y,
        train_pred=train_pred,
        test_pred=test_pred,
        history_window_steps=history_window_steps,
        model_type="gru",
    )


def current_frame_ridge_rows(
    frames: np.ndarray,
    targets: dict[str, np.ndarray],
    train_mask: np.ndarray,
    history_window_steps: int,
    ridge: float,
) -> list[dict[str, Any]]:
    current_observations = frames[:, -1, :]
    feature_profiles = build_input_feature_profiles(current_observations)
    rows: list[dict[str, Any]] = []
    for profile_name, feature_name in (
        (P0_CURRENT_RIDGE, P0_RESPONSE_ONLY),
        (P1_CURRENT_RIDGE, P1_RESPONSE_ONLY),
    ):
        for target_name, target_values in targets.items():
            result = train_ridge_regression_probe(
                features=feature_profiles[feature_name],
                targets=target_values,
                train_mask=train_mask,
                target_name=target_name,
                feature_set=feature_name,
                ridge=ridge,
                history_window_steps=1,
            )
            row = dict(result.__dict__)
            row["profile"] = profile_name
            row["model_type"] = "ridge_current"
            row["history_window_steps"] = history_window_steps
            rows.append(row)
    return rows


def run_learned_history_observability_probe(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_window: int,
    config: LearnedProbeConfig,
    ridge: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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

    probe_rows = current_frame_ridge_rows(
        frames=frames,
        targets=targets,
        train_mask=train_mask,
        history_window_steps=history_window,
        ridge=ridge,
    )
    for profile in (P0_RESPONSE_HISTORY, P1_RESPONSE_HISTORY):
        sequence = response_history_sequence(frames, profile)
        probe_rows.extend(
            train_learned_history_probe(
                features=sequence,
                targets=target_matrix,
                train_mask=train_mask,
                profile=profile,
                history_window_steps=history_window,
                config=config,
                seed=seed + (101 if profile == P0_RESPONSE_HISTORY else 211),
            )
        )
    return sample_rows, probe_rows


def resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a learned supervised history observability probe.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9360)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--history-window", type=int, default=50)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    torch.set_num_threads(1)
    device = resolve_device(args.device)
    config = LearnedProbeConfig(
        hidden_size=args.hidden_size,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        train_fraction=args.train_fraction,
        device=device,
    )
    sample_rows, probe_rows = run_learned_history_observability_probe(
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        history_window=args.history_window,
        config=config,
        ridge=args.ridge,
    )

    run_dir = args.run_dir or make_run_dir(prefix="learned_history_observability", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    probe_summary_csv = run_dir / "probe_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(samples_csv, sample_rows)
    write_csv_rows(probe_summary_csv, probe_rows)
    write_json(
        summary_json,
        {
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_window": args.history_window,
            "targets": TARGETS,
            "probe_results": probe_rows,
            "config": config.__dict__,
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "learned_history_observability_probe",
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
                "summary_json": summary_json,
            },
        },
    )
    print(pd.DataFrame(probe_rows).to_string(index=False))


if __name__ == "__main__":
    main()
