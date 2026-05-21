"""Objective-only optimization for the wheel-masked friction auxiliary."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv
from autodrift.latent_probe import collect_probe_dataset, split_by_episode
from autodrift.train_ppo import (
    ActorCritic,
    PPOConfig,
    load_init_checkpoint_state,
    mask_friction_aux_observations,
    recurrent_response_hidden_sequence,
    resolve_device,
    save_training_checkpoint,
)


@dataclass(frozen=True)
class FrictionObjectiveMetrics:
    split: str
    loss: float
    accuracy: float
    samples: int


def _wheel_response_norms(model: ActorCritic) -> dict[str, float]:
    if model.response_encoder is None:
        return {"body_norm": float("nan"), "wheel_norm": float("nan"), "wheel_max": float("nan")}
    weight = model.response_encoder[0].weight.detach().cpu()
    return {
        "body_norm": float(weight[:, :12].norm().item()),
        "wheel_norm": float(weight[:, 12:25].norm().item()),
        "wheel_max": float(weight[:, 12:25].abs().max().item()),
    }


def _friction_logits(
    model: ActorCritic,
    classifier: nn.Linear,
    observations: torch.Tensor,
) -> torch.Tensor:
    masked_obs = mask_friction_aux_observations(observations.unsqueeze(0), "wheel_only")
    hidden = model.initial_hidden(observations.shape[0], observations.device)
    dones = torch.zeros((1, observations.shape[0]), dtype=torch.float32, device=observations.device)
    response_hidden = recurrent_response_hidden_sequence(model, masked_obs, hidden, dones).squeeze(0)
    return classifier(response_hidden)


def evaluate_friction_objective(
    model: ActorCritic,
    classifier: nn.Linear,
    observations: torch.Tensor,
    labels: torch.Tensor,
    mask: torch.Tensor,
    split: str,
) -> FrictionObjectiveMetrics:
    if int(mask.sum().item()) == 0:
        return FrictionObjectiveMetrics(split=split, loss=float("nan"), accuracy=float("nan"), samples=0)
    with torch.no_grad():
        logits = _friction_logits(model, classifier, observations[mask])
        split_labels = labels[mask]
        loss = nn.functional.cross_entropy(logits, split_labels)
        accuracy = (torch.argmax(logits, dim=1) == split_labels).float().mean()
    return FrictionObjectiveMetrics(
        split=split,
        loss=float(loss.item()),
        accuracy=float(accuracy.item()),
        samples=int(mask.sum().item()),
    )


def metrics_to_rows(metrics: list[FrictionObjectiveMetrics]) -> list[dict]:
    return [metric.__dict__ for metric in metrics]


def trainable_response_parameters(model: ActorCritic) -> list[nn.Parameter]:
    if model.response_encoder is None or model.online_gru_cell is None:
        raise ValueError("wheel-masked friction optimization requires a response recurrent actor")
    return [
        *model.response_encoder.parameters(),
        *model.online_gru_cell.parameters(),
    ]


def optimize_wheel_masked_friction(
    config_path: Path,
    init_checkpoint: Path,
    episodes: int,
    seed: int,
    device: str,
    max_samples: int | None,
    train_fraction: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    grad_clip_norm: float,
    run_dir: Path,
) -> dict:
    raw_config = read_json(config_path)
    ppo_defaults = PPOConfig()
    ppo_data = {field.name: getattr(ppo_defaults, field.name) for field in fields(PPOConfig)}
    for key, value in raw_config.get("ppo", {}).items():
        if key in ppo_data:
            ppo_data[key] = value
    ppo_config = PPOConfig(**ppo_data)
    env_config = build_env_config(raw_config.get("env", {}))
    env = AutoDriftEnv(env_config)
    resolved_device = resolve_device(device)

    model = ActorCritic(
        obs_dim=int(env.observation_space.shape[0]),
        act_dim=int(env.action_space.shape[0]),
        hidden_size=ppo_config.hidden_size,
        log_std_init=ppo_config.log_std_init,
        log_std_min=ppo_config.log_std_min,
        log_std_max=ppo_config.log_std_max,
        actor_encoder=ppo_config.actor_encoder,
        actor_history_length=ppo_config.actor_history_length,
        action_sequence_horizon=ppo_config.action_sequence_horizon,
        response_prediction_dim=ppo_config.response_prediction_dim,
        response_prediction_horizon=ppo_config.response_prediction_horizon,
    ).to(resolved_device)
    load_mode = load_init_checkpoint_state(model, init_checkpoint, resolved_device)
    classifier = nn.Linear(ppo_config.hidden_size, 3).to(resolved_device)

    dataset = collect_probe_dataset(
        model=model,
        env_config=env_config,
        episodes=episodes,
        seed=seed,
        max_samples=max_samples,
    )
    observations = torch.as_tensor(dataset.observations, dtype=torch.float32, device=resolved_device)
    labels = torch.as_tensor(dataset.labels["mu_bucket"], dtype=torch.long, device=resolved_device)
    train_mask_np = split_by_episode(dataset.rows, train_fraction=train_fraction, seed=seed + 31)
    train_mask = torch.as_tensor(train_mask_np, dtype=torch.bool, device=resolved_device)
    test_mask = ~train_mask

    optimizer = torch.optim.AdamW(
        [*trainable_response_parameters(model), *classifier.parameters()],
        lr=learning_rate,
        weight_decay=1e-4,
    )
    rng = np.random.default_rng(seed + 97)
    train_indices = np.flatnonzero(train_mask_np)
    if len(train_indices) == 0:
        raise ValueError("wheel-masked friction optimization has no train samples")

    before_metrics = [
        evaluate_friction_objective(model, classifier, observations, labels, train_mask, "train_before"),
        evaluate_friction_objective(model, classifier, observations, labels, test_mask, "test_before"),
    ]
    before_norms = _wheel_response_norms(model)
    train_rows: list[dict] = []
    for step in range(1, steps + 1):
        batch_indices = rng.choice(train_indices, size=min(batch_size, len(train_indices)), replace=len(train_indices) < batch_size)
        batch = torch.as_tensor(batch_indices, dtype=torch.long, device=resolved_device)
        logits = _friction_logits(model, classifier, observations[batch])
        loss = nn.functional.cross_entropy(logits, labels[batch])
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_([*trainable_response_parameters(model), *classifier.parameters()], grad_clip_norm)
        optimizer.step()
        if step == 1 or step == steps or step % max(1, steps // 10) == 0:
            with torch.no_grad():
                accuracy = (torch.argmax(logits, dim=1) == labels[batch]).float().mean()
            train_rows.append(
                {
                    "step": step,
                    "loss": float(loss.detach().cpu().item()),
                    "batch_accuracy": float(accuracy.detach().cpu().item()),
                    **_wheel_response_norms(model),
                }
            )

    after_metrics = [
        evaluate_friction_objective(model, classifier, observations, labels, train_mask, "train_after"),
        evaluate_friction_objective(model, classifier, observations, labels, test_mask, "test_after"),
    ]
    after_norms = _wheel_response_norms(model)

    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    train_metrics_csv = run_dir / "train_metrics.csv"
    objective_summary_csv = run_dir / "objective_summary.csv"
    optimized_checkpoint = run_dir / "optimized_checkpoint.pt"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    write_csv_rows(samples_csv, dataset.rows)
    write_csv_rows(train_metrics_csv, train_rows)
    objective_rows = metrics_to_rows([*before_metrics, *after_metrics])
    write_csv_rows(objective_summary_csv, objective_rows)
    save_training_checkpoint(
        model,
        ppo_config,
        {
            "run_type": "wheel_masked_friction_objective_only",
            "init_checkpoint": init_checkpoint,
            "config": config_path,
            "load_mode": load_mode,
        },
        optimized_checkpoint,
    )
    summary = {
        "episodes": episodes,
        "samples": int(len(dataset.rows)),
        "train_samples": int(train_mask.sum().item()),
        "test_samples": int(test_mask.sum().item()),
        "load_mode": load_mode,
        "before_norms": before_norms,
        "after_norms": after_norms,
        "wheel_norm_delta": float(after_norms["wheel_norm"] - before_norms["wheel_norm"]),
        "objective_summary": objective_rows,
        "artifacts": {
            "samples_csv": samples_csv,
            "train_metrics_csv": train_metrics_csv,
            "objective_summary_csv": objective_summary_csv,
            "optimized_checkpoint": optimized_checkpoint,
        },
    }
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "wheel_masked_friction_objective_only",
            "config": config_path,
            "init_checkpoint": init_checkpoint,
            "episodes": episodes,
            "seed": seed,
            "device": device,
            "max_samples": max_samples,
            "train_fraction": train_fraction,
            "steps": steps,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "grad_clip_norm": grad_clip_norm,
            "artifacts": summary["artifacts"],
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize only the wheel-masked friction auxiliary objective.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--init-checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=9200)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-samples", type=int, default=1500)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="wheel_masked_friction_optimize", seed=args.seed)
    summary = optimize_wheel_masked_friction(
        config_path=args.config,
        init_checkpoint=args.init_checkpoint,
        episodes=args.episodes,
        seed=args.seed,
        device=args.device,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        grad_clip_norm=args.grad_clip_norm,
        run_dir=run_dir,
    )
    print(pd.DataFrame(summary["objective_summary"]).to_string(index=False))
    print(f"run_dir={run_dir}")
    print(f"wheel_norm_delta={summary['wheel_norm_delta']:.6f}")


if __name__ == "__main__":
    main()
