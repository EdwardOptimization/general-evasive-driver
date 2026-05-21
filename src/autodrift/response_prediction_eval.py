"""Evaluate response-prediction auxiliary heads on rollout data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import load_seed_csv
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.train_ppo import ActorCritic, build_response_prediction_targets, resolve_device


def parse_checkpoint_specs(specs: list[str]) -> list[tuple[str, Path]]:
    parsed = []
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"checkpoint policy spec must be NAME=PATH, got {spec!r}")
        name, raw_path = spec.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"checkpoint policy spec has empty name: {spec!r}")
        parsed.append((name, Path(raw_path)))
    if not parsed:
        raise ValueError("at least one --checkpoint-policy is required")
    return parsed


def collect_episode(
    model: ActorCritic,
    env: AutoDriftEnv,
    *,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    obs, _ = env.reset(seed=seed)
    hidden = None
    observations = []
    actions = []
    dones = []
    terminated = False
    truncated = False
    while not (terminated or truncated):
        observations.append(np.asarray(obs, dtype=np.float32))
        if model.is_online_recurrent:
            action, _, _, hidden = model.act_recurrent(obs, hidden, deterministic=True)
        else:
            action, _, _ = model.act(obs, deterministic=True)
        actions.append(np.asarray(action, dtype=np.float32))
        obs, _, terminated, truncated, _ = env.step(action)
        dones.append(float(terminated or truncated))
    return (
        np.asarray(observations, dtype=np.float32),
        np.asarray(actions, dtype=np.float32),
        np.asarray(dones, dtype=np.float32),
    )


def compute_response_prediction_metrics(
    model: ActorCritic,
    observations: np.ndarray,
    actions: np.ndarray,
    dones: np.ndarray,
    *,
    stride: int,
    device: torch.device,
) -> dict[str, float]:
    if not model.is_online_recurrent:
        raise ValueError("response prediction evaluation requires an online recurrent actor")
    if model.response_prediction_head is None or model.response_prediction_dim < 1:
        raise ValueError("checkpoint does not have a response prediction head")
    obs_batch = observations[:, None, :]
    action_batch = actions[:, None, :]
    done_batch = dones[:, None]
    target, mask = build_response_prediction_targets(
        obs_batch,
        done_batch,
        model.response_prediction_dim,
        model.response_prediction_horizon,
        stride,
    )
    with torch.no_grad():
        obs_t = torch.as_tensor(obs_batch, dtype=torch.float32, device=device)
        action_t = torch.as_tensor(action_batch, dtype=torch.float32, device=device)
        done_t = torch.as_tensor(done_batch, dtype=torch.float32, device=device)
        initial_hidden = model.initial_hidden(1, device)
        prediction = model.predict_response_recurrent_sequence(obs_t, action_t, initial_hidden, done_t)
        target_t = torch.as_tensor(target, dtype=torch.float32, device=device)
        mask_t = torch.as_tensor(mask, dtype=torch.float32, device=device)
        squared_error = torch.square(prediction - target_t) * mask_t.unsqueeze(-1)
        sse_by_horizon = squared_error.sum(dim=(0, 1, 3)).cpu().numpy()
        count_by_horizon = (mask_t.sum(dim=(0, 1)) * model.response_prediction_dim).cpu().numpy()
    metrics: dict[str, float] = {}
    total_sse = 0.0
    total_count = 0.0
    for horizon_index, (sse, count) in enumerate(zip(sse_by_horizon, count_by_horizon), start=1):
        total_sse += float(sse)
        total_count += float(count)
        metrics[f"horizon_{horizon_index}_mse"] = float(sse / count) if count > 0.0 else float("nan")
        metrics[f"horizon_{horizon_index}_valid_targets"] = float(count / model.response_prediction_dim)
    metrics["mse"] = float(total_sse / total_count) if total_count > 0.0 else float("nan")
    metrics["valid_targets"] = float(total_count / model.response_prediction_dim)
    return metrics


def evaluate_checkpoint(
    label: str,
    checkpoint_path: Path,
    *,
    env_config: DriftEnvConfig,
    seeds: list[int],
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(device))
    model.eval()
    stride = int(checkpoint.get("config", {}).get("response_prediction_stride", 1))
    row: dict[str, Any] = {
        "policy": label,
        "checkpoint": checkpoint_path,
        "episodes": len(seeds),
        "response_prediction_dim": getattr(model, "response_prediction_dim", 0),
        "response_prediction_horizon": getattr(model, "response_prediction_horizon", 1),
        "response_prediction_stride": stride,
    }
    if not model.is_online_recurrent or model.response_prediction_head is None or model.response_prediction_dim < 1:
        row["status"] = "unsupported"
        return row, []
    env = AutoDriftEnv(env_config)
    metric_sums: dict[str, float] = {}
    metric_counts: dict[str, float] = {}
    valid_counts: dict[str, float] = {}
    episode_rows: list[dict[str, Any]] = []
    try:
        for episode_seed in seeds:
            observations, actions, dones = collect_episode(model, env, seed=episode_seed)
            metrics = compute_response_prediction_metrics(
                model,
                observations,
                actions,
                dones,
                stride=stride,
                device=device,
            )
            episode_row: dict[str, Any] = {
                "policy": label,
                "checkpoint": checkpoint_path,
                "seed": episode_seed,
                "steps": len(observations),
                "response_prediction_dim": model.response_prediction_dim,
                "response_prediction_horizon": model.response_prediction_horizon,
                "response_prediction_stride": stride,
            }
            episode_row.update(metrics)
            episode_rows.append(episode_row)
            for key, value in metrics.items():
                if key.endswith("_valid_targets") or key == "valid_targets":
                    valid_counts[key] = valid_counts.get(key, 0.0) + float(value)
                else:
                    count_key = "valid_targets"
                    if key.startswith("horizon_") and key.endswith("_mse"):
                        horizon = key.removesuffix("_mse")
                        count_key = f"{horizon}_valid_targets"
                    count = float(metrics[count_key])
                    metric_sums[key] = metric_sums.get(key, 0.0) + float(value) * count
                    metric_counts[key] = metric_counts.get(key, 0.0) + count
        total_valid = valid_counts.get("valid_targets", 0.0)
        row["status"] = "ok"
        row["valid_targets"] = total_valid
        for key, weighted_sum in metric_sums.items():
            count = metric_counts.get(key, 0.0)
            row[key] = float(weighted_sum / count) if count > 0.0 else float("nan")
        for key, count in valid_counts.items():
            if key != "valid_targets":
                row[key] = count
    finally:
        env.close()
    return row, episode_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate response-prediction auxiliary heads.")
    parser.add_argument("--checkpoint-policy", action="append", default=[], help="Checkpoint policy in NAME=PATH form.")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--env-config", type=Path, default=None)
    args = parser.parse_args()

    checkpoint_specs = parse_checkpoint_specs(args.checkpoint_policy)
    env_config = load_env_config(args.env_config) if args.env_config is not None else DriftEnvConfig()
    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    device = resolve_device(args.device)
    run_dir = args.run_dir or make_run_dir(prefix="response_prediction_eval", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    episode_rows = []
    for label, path in checkpoint_specs:
        row, policy_episode_rows = evaluate_checkpoint(label, path, env_config=env_config, seeds=seeds, device=device)
        rows.append(row)
        episode_rows.extend(policy_episode_rows)
    summary_csv = run_dir / "prediction_summary.csv"
    episodes_csv = run_dir / "prediction_episodes.csv"
    frame = pd.DataFrame(rows)
    frame.to_csv(summary_csv, index=False)
    pd.DataFrame(episode_rows).to_csv(episodes_csv, index=False)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "response_prediction_eval",
            "checkpoint_policies": {label: path for label, path in checkpoint_specs},
            "episodes": len(seeds),
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "env_config": args.env_config,
            "summary_csv": summary_csv,
            "episodes_csv": episodes_csv,
        },
    )
    print(frame.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
