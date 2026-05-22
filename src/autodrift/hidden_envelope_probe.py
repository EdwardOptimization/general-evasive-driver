"""Probe whether a frozen recurrent policy hidden state predicts handling envelope."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.input_observability_audit import (
    TARGETS,
    future_envelope_targets,
    split_by_episode,
    train_ridge_regression_probe,
)
from autodrift.train_ppo import (
    HUMAN_VIEW_RESPONSE_FEATURE_DIM,
    PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER,
    WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER,
    WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM,
    ActorCritic,
    resolve_device,
)


FULL_OBSERVATION = "full_observation"
CURRENT_RESPONSE = "current_response"
POLICY_FEATURES = "policy_features"
RESPONSE_HIDDEN = "response_hidden"
RESET_POLICY_FEATURES = "reset_policy_features"
RESET_RESPONSE_HIDDEN = "reset_response_hidden"
HIDDEN_ENVELOPE_FEATURE_SETS = (
    FULL_OBSERVATION,
    CURRENT_RESPONSE,
    POLICY_FEATURES,
    RESPONSE_HIDDEN,
    RESET_POLICY_FEATURES,
    RESET_RESPONSE_HIDDEN,
)


@dataclass(frozen=True)
class HiddenEnvelopeDataset:
    features: dict[str, np.ndarray]
    targets: dict[str, np.ndarray]
    rows: list[dict[str, Any]]


def response_feature_dim_for_model(model: ActorCritic) -> int:
    if model.actor_encoder == WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER:
        return WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM
    if model.actor_encoder == PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER:
        return HUMAN_VIEW_RESPONSE_FEATURE_DIM
    if model.response_feature_indices:
        return len(model.response_feature_indices)
    return HUMAN_VIEW_RESPONSE_FEATURE_DIM


def _collect_feature_snapshot(
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, torch.Tensor]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    reset_hidden = model.initial_hidden(1, device)
    with torch.no_grad():
        policy_features, next_hidden = model.recurrent_features_tensor(obs_t, hidden)
        reset_policy_features, reset_next_hidden = model.recurrent_features_tensor(obs_t, reset_hidden)
    return (
        policy_features.squeeze(0).detach().cpu().numpy().astype(np.float32),
        next_hidden.squeeze(0).detach().cpu().numpy().astype(np.float32),
        reset_policy_features.squeeze(0).detach().cpu().numpy().astype(np.float32),
        reset_next_hidden.squeeze(0).detach().cpu().numpy().astype(np.float32),
        next_hidden.detach(),
    )


def deterministic_recurrent_action(model: ActorCritic, features: np.ndarray, device: torch.device) -> np.ndarray:
    features_t = torch.as_tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.no_grad():
        action = torch.tanh(model.actor_mean(features_t))
    return action.squeeze(0).detach().cpu().numpy().astype(np.float32)


def collect_hidden_envelope_dataset(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    episodes: int,
    seed: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    device: torch.device,
) -> HiddenEnvelopeDataset:
    if not model.is_online_recurrent:
        raise ValueError("hidden envelope probe requires an online recurrent checkpoint")
    if sample_stride < 1:
        raise ValueError("sample_stride must be at least 1")
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be at least 1")

    env = AutoDriftEnv(env_config)
    response_dim = response_feature_dim_for_model(model)
    feature_lists: dict[str, list[np.ndarray]] = {name: [] for name in HIDDEN_ENVELOPE_FEATURE_SETS}
    target_lists: dict[str, list[float]] = {name: [] for name in TARGETS}
    rows: list[dict[str, Any]] = []

    try:
        for episode in range(episodes):
            episode_seed = seed + episode
            obs, info = env.reset(seed=episode_seed)
            hidden = model.initial_hidden(1, device)
            terminated = False
            truncated = False
            while not (terminated or truncated):
                observation = np.asarray(obs, dtype=np.float32)
                policy_features, response_hidden, reset_policy_features, reset_response_hidden, next_hidden = (
                    _collect_feature_snapshot(model, observation, hidden, device)
                )
                if int(info["step"]) % sample_stride == 0:
                    target_values = future_envelope_targets(env, horizon_steps=horizon_steps)
                    feature_lists[FULL_OBSERVATION].append(observation.copy())
                    feature_lists[CURRENT_RESPONSE].append(observation[:response_dim].copy())
                    feature_lists[POLICY_FEATURES].append(policy_features)
                    feature_lists[RESPONSE_HIDDEN].append(response_hidden)
                    feature_lists[RESET_POLICY_FEATURES].append(reset_policy_features)
                    feature_lists[RESET_RESPONSE_HIDDEN].append(reset_response_hidden)
                    for name in TARGETS:
                        target_lists[name].append(float(target_values[name]))
                    rows.append(
                        {
                            "episode": episode,
                            "seed": episode_seed,
                            "step": int(info["step"]),
                            "obstacle_label": str(info.get("obstacle_label", "")),
                            "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
                            "obstacle_lateral_offset": float(info.get("obstacle_lateral_offset", float("nan"))),
                            **target_values,
                        }
                    )
                    if max_samples is not None and len(rows) >= max_samples:
                        break
                action = deterministic_recurrent_action(model, policy_features, device)
                obs, _, terminated, truncated, info = env.step(action)
                hidden = next_hidden
            if max_samples is not None and len(rows) >= max_samples:
                break
    finally:
        env.close()

    return HiddenEnvelopeDataset(
        features={
            name: np.asarray(values, dtype=np.float32)
            for name, values in feature_lists.items()
        },
        targets={name: np.asarray(values, dtype=np.float32) for name, values in target_lists.items()},
        rows=rows,
    )


def run_hidden_envelope_probe(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    episodes: int,
    seed: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    ridge: float,
    train_fraction: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    dataset = collect_hidden_envelope_dataset(
        model=model,
        env_config=env_config,
        episodes=episodes,
        seed=seed,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        device=device,
    )
    if len(dataset.rows) == 0:
        raise ValueError("hidden envelope probe dataset is empty")
    train_mask = split_by_episode(dataset.rows, train_fraction=train_fraction, seed=seed + 31)
    probe_rows: list[dict[str, Any]] = []
    for target_name, target_values in dataset.targets.items():
        for feature_name in HIDDEN_ENVELOPE_FEATURE_SETS:
            result = train_ridge_regression_probe(
                features=dataset.features[feature_name],
                targets=target_values,
                train_mask=train_mask,
                target_name=target_name,
                feature_set=feature_name,
                ridge=ridge,
            )
            probe_rows.append(result.__dict__)
    return dataset.rows, probe_rows, summarize_hidden_envelope_gains(probe_rows)


def summarize_hidden_envelope_gains(probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_target: dict[str, dict[str, dict[str, Any]]] = {}
    for row in probe_rows:
        by_target.setdefault(str(row["target"]), {})[str(row["feature_set"])] = row
    summary: list[dict[str, Any]] = []
    for target, rows in sorted(by_target.items()):
        response_hidden = rows[RESPONSE_HIDDEN]
        reset_response_hidden = rows[RESET_RESPONSE_HIDDEN]
        policy_features = rows[POLICY_FEATURES]
        reset_policy_features = rows[RESET_POLICY_FEATURES]
        current_response = rows[CURRENT_RESPONSE]
        full_observation = rows[FULL_OBSERVATION]
        summary.append(
            {
                "target": target,
                "response_hidden_test_r2": response_hidden["test_r2"],
                "reset_response_hidden_test_r2": reset_response_hidden["test_r2"],
                "response_hidden_minus_reset_test_r2": response_hidden["test_r2"]
                - reset_response_hidden["test_r2"],
                "response_hidden_minus_current_response_test_r2": response_hidden["test_r2"]
                - current_response["test_r2"],
                "policy_features_test_r2": policy_features["test_r2"],
                "reset_policy_features_test_r2": reset_policy_features["test_r2"],
                "policy_features_minus_reset_test_r2": policy_features["test_r2"]
                - reset_policy_features["test_r2"],
                "full_observation_test_r2": full_observation["test_r2"],
                "response_hidden_mae_improvement": response_hidden["mae_improvement"],
                "reset_response_hidden_mae_improvement": reset_response_hidden["mae_improvement"],
                "response_hidden_minus_reset_mae_improvement": response_hidden["mae_improvement"]
                - reset_response_hidden["mae_improvement"],
                "status": "ok" if response_hidden["status"] == "ok" and reset_response_hidden["status"] == "ok" else "skipped",
            }
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe frozen recurrent hidden state against future envelope targets.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=9400)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    device = resolve_device(args.device)
    model, checkpoint = load_actor_critic_checkpoint(args.checkpoint, device=str(device))
    model.eval()
    env_config = load_env_config(args.env_config)
    sample_rows, probe_rows, gain_rows = run_hidden_envelope_probe(
        model=model,
        env_config=env_config,
        episodes=args.episodes,
        seed=args.seed,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        ridge=args.ridge,
        train_fraction=args.train_fraction,
        device=device,
    )

    run_dir = args.run_dir or make_run_dir(prefix="hidden_envelope_probe", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    probe_summary_csv = run_dir / "probe_summary.csv"
    hidden_gain_csv = run_dir / "hidden_gain_summary.csv"
    write_csv_rows(samples_csv, sample_rows)
    write_csv_rows(probe_summary_csv, probe_rows)
    write_csv_rows(hidden_gain_csv, gain_rows)
    write_json(
        run_dir / "summary.json",
        {
            "checkpoint": args.checkpoint,
            "checkpoint_config": checkpoint.get("config", {}),
            "env_config": args.env_config,
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "seed": args.seed,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "feature_sets": HIDDEN_ENVELOPE_FEATURE_SETS,
            "targets": TARGETS,
            "probe_results": probe_rows,
            "hidden_gain_summary": gain_rows,
        },
    )
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "hidden_envelope_probe",
            "checkpoint": args.checkpoint,
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "artifacts": {
                "samples_csv": samples_csv,
                "probe_summary_csv": probe_summary_csv,
                "hidden_gain_summary_csv": hidden_gain_csv,
                "summary_json": run_dir / "summary.json",
            },
        },
    )
    print(pd.DataFrame(gain_rows).to_string(index=False))


if __name__ == "__main__":
    main()
