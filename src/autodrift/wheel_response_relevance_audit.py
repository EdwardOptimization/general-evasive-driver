"""Audit whether wheel response adds hidden-dynamics information beyond body response."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import CHECKPOINT_ABLATIONS, load_env_config
from autodrift.latent_probe import (
    ProbeResult,
    collect_probe_dataset,
    probe_results_to_rows,
    split_by_episode,
    train_linear_probe,
)
from autodrift.train_ppo import HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


BODY_RESPONSE_FEATURE_SET = "body_response"
WHEEL_RESPONSE_FEATURE_SET = "wheel_response"
BODY_PLUS_WHEEL_FEATURE_SET = "body_plus_wheel"
FULL_OBSERVATION_FEATURE_SET = "full_observation"
WHEEL_AUDIT_FEATURE_SETS = (
    BODY_RESPONSE_FEATURE_SET,
    WHEEL_RESPONSE_FEATURE_SET,
    BODY_PLUS_WHEEL_FEATURE_SET,
    FULL_OBSERVATION_FEATURE_SET,
)


@dataclass(frozen=True)
class WheelGainResult:
    target: str
    body_response_accuracy: float
    wheel_response_accuracy: float
    body_plus_wheel_accuracy: float
    full_observation_accuracy: float
    body_plus_wheel_gain: float
    wheel_vs_body_delta: float
    status: str


def build_wheel_feature_sets(observations: np.ndarray) -> dict[str, np.ndarray]:
    if observations.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if observations.shape[1] < WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM:
        raise ValueError(
            "wheel response relevance audit requires observations with at least "
            f"{WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM} features"
        )
    body_end = HUMAN_VIEW_RESPONSE_FEATURE_DIM
    wheel_end = WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM
    return {
        BODY_RESPONSE_FEATURE_SET: observations[:, :body_end].astype(np.float32),
        WHEEL_RESPONSE_FEATURE_SET: observations[:, body_end:wheel_end].astype(np.float32),
        BODY_PLUS_WHEEL_FEATURE_SET: observations[:, :wheel_end].astype(np.float32),
        FULL_OBSERVATION_FEATURE_SET: observations.astype(np.float32),
    }


def summarize_wheel_gains(results: list[ProbeResult]) -> list[WheelGainResult]:
    by_target: dict[str, dict[str, ProbeResult]] = {}
    for result in results:
        by_target.setdefault(result.target, {})[result.feature_set] = result

    gain_rows: list[WheelGainResult] = []
    for target, feature_results in sorted(by_target.items()):
        missing = [name for name in WHEEL_AUDIT_FEATURE_SETS if name not in feature_results]
        if missing:
            raise ValueError(f"missing probe results for target {target!r}: {missing}")
        body = feature_results[BODY_RESPONSE_FEATURE_SET]
        wheel = feature_results[WHEEL_RESPONSE_FEATURE_SET]
        body_plus_wheel = feature_results[BODY_PLUS_WHEEL_FEATURE_SET]
        full = feature_results[FULL_OBSERVATION_FEATURE_SET]
        if body.status != "ok" or body_plus_wheel.status != "ok":
            status = "skipped"
        else:
            status = "ok"
        gain_rows.append(
            WheelGainResult(
                target=target,
                body_response_accuracy=float(body.test_accuracy),
                wheel_response_accuracy=float(wheel.test_accuracy),
                body_plus_wheel_accuracy=float(body_plus_wheel.test_accuracy),
                full_observation_accuracy=float(full.test_accuracy),
                body_plus_wheel_gain=float(body_plus_wheel.test_accuracy - body.test_accuracy),
                wheel_vs_body_delta=float(wheel.test_accuracy - body.test_accuracy),
                status=status,
            )
        )
    return gain_rows


def wheel_gain_results_to_rows(results: list[WheelGainResult]) -> list[dict]:
    return [result.__dict__ for result in results]


def run_wheel_relevance_audit(
    checkpoint: Path,
    env_config_path: Path,
    episodes: int,
    seed: int,
    device: str,
    checkpoint_ablation: str = "none",
    max_samples: int | None = None,
    train_fraction: float = 0.70,
    epochs: int = 120,
    learning_rate: float = 0.03,
) -> tuple[list[dict], list[dict], list[dict]]:
    env_config = load_env_config(env_config_path)
    env = AutoDriftEnv(env_config)
    if env_config.wheel_observation_mode != "front_rear":
        raise ValueError("wheel response relevance audit requires wheel_observation_mode='front_rear'")
    if int(env.observation_space.shape[0]) < WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM:
        raise ValueError("environment observation space is too small for wheel response audit")
    model, _ = load_actor_critic_checkpoint(
        checkpoint,
        device=device,
        obs_dim=int(env.observation_space.shape[0]),
    )
    dataset = collect_probe_dataset(
        model=model,
        env_config=env_config,
        episodes=episodes,
        seed=seed,
        checkpoint_ablation=checkpoint_ablation,
        max_samples=max_samples,
    )
    train_mask = split_by_episode(dataset.rows, train_fraction=train_fraction, seed=seed + 31)
    feature_sets = build_wheel_feature_sets(dataset.observations)
    probe_results: list[ProbeResult] = []
    for target_name, labels in dataset.labels.items():
        for feature_set_name in WHEEL_AUDIT_FEATURE_SETS:
            probe_results.append(
                train_linear_probe(
                    features=feature_sets[feature_set_name],
                    labels=labels,
                    train_mask=train_mask,
                    target_name=target_name,
                    feature_set=feature_set_name,
                    seed=seed + len(probe_results),
                    epochs=epochs,
                    learning_rate=learning_rate,
                )
            )
    return (
        dataset.rows,
        probe_results_to_rows(probe_results),
        wheel_gain_results_to_rows(summarize_wheel_gains(probe_results)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit wheel response relevance beyond body response.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9100)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument(
        "--checkpoint-ablation",
        choices=CHECKPOINT_ABLATIONS,
        default="none",
    )
    args = parser.parse_args()

    sample_rows, probe_rows, gain_rows = run_wheel_relevance_audit(
        checkpoint=args.checkpoint,
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        device=args.device,
        checkpoint_ablation=args.checkpoint_ablation,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )

    run_dir = args.run_dir or make_run_dir(prefix="wheel_response_relevance_audit", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    probe_summary_csv = run_dir / "probe_summary.csv"
    wheel_gain_csv = run_dir / "wheel_gain_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    write_csv_rows(samples_csv, sample_rows)
    write_csv_rows(probe_summary_csv, probe_rows)
    write_csv_rows(wheel_gain_csv, gain_rows)
    write_json(
        summary_json,
        {
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "checkpoint_ablation": args.checkpoint_ablation,
            "feature_sets": WHEEL_AUDIT_FEATURE_SETS,
            "wheel_gain_summary": gain_rows,
            "probe_results": probe_rows,
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "wheel_response_relevance_audit",
            "checkpoint": args.checkpoint,
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "device": args.device,
            "checkpoint_ablation": args.checkpoint_ablation,
            "artifacts": {
                "samples_csv": samples_csv,
                "probe_summary_csv": probe_summary_csv,
                "wheel_gain_summary_csv": wheel_gain_csv,
                "summary_json": summary_json,
            },
        },
    )
    print(pd.DataFrame(gain_rows).to_string(index=False))


if __name__ == "__main__":
    main()
