"""Objective-only actor coupling for M98 hidden-envelope belief."""

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
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_optimize import (
    HiddenEnvelopeObjectiveBatch,
    collect_hidden_envelope_objective_batch,
    save_checkpoint_like,
)
from autodrift.train_ppo import ActorCritic, resolve_device


@dataclass(frozen=True)
class ActorCouplingMetrics:
    phase: str
    split: str
    samples: int
    normal_anchor_mse: float
    reset_anchor_mse: float
    normal_reset_action_distance_mean: float
    normal_reset_action_distance_min: float
    normal_reset_action_distance_p10: float
    margin_pass_rate: float


def actor_coupling_trainable_parameters(model: ActorCritic) -> list[nn.Parameter]:
    if not model.is_online_recurrent or model.response_context_fusion is None:
        raise ValueError("actor coupling requires a human-view online recurrent actor")
    return [
        *model.response_context_fusion.parameters(),
        *model.actor_mean.parameters(),
    ]


def _sample_masks(
    batch: HiddenEnvelopeObjectiveBatch,
    train_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    from autodrift.input_observability_audit import split_by_episode

    train_flat = split_by_episode(batch.rows, train_fraction=train_fraction, seed=seed)
    sample_mask = batch.sample_mask
    train_mask = np.zeros_like(sample_mask, dtype=bool)
    test_mask = np.zeros_like(sample_mask, dtype=bool)
    train_mask[sample_mask] = train_flat
    test_mask[sample_mask] = ~train_flat
    return train_mask, test_mask


def _action_mean_sequences(
    model: ActorCritic,
    observations: torch.Tensor,
    dones: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    initial_hidden = model.initial_hidden(observations.shape[1], observations.device)
    reset_dones = torch.ones_like(dones)
    normal_actions = model.action_mean_recurrent_sequence(observations, initial_hidden, dones)
    reset_actions = model.action_mean_recurrent_sequence(observations, initial_hidden, reset_dones)
    return normal_actions, reset_actions


def _actor_coupling_metrics(
    *,
    model: ActorCritic,
    reference_normal_actions: torch.Tensor,
    observations: torch.Tensor,
    dones: torch.Tensor,
    mask: torch.Tensor,
    margin: float,
    phase: str,
    split: str,
) -> ActorCouplingMetrics:
    if int(mask.sum().item()) == 0:
        return ActorCouplingMetrics(
            phase=phase,
            split=split,
            samples=0,
            normal_anchor_mse=float("nan"),
            reset_anchor_mse=float("nan"),
            normal_reset_action_distance_mean=float("nan"),
            normal_reset_action_distance_min=float("nan"),
            normal_reset_action_distance_p10=float("nan"),
            margin_pass_rate=float("nan"),
        )
    with torch.no_grad():
        normal_actions, reset_actions = _action_mean_sequences(model, observations, dones)
        normal = normal_actions[mask]
        reset = reset_actions[mask]
        reference = reference_normal_actions[mask]
        distances = torch.linalg.vector_norm(normal - reset, dim=-1)
    return ActorCouplingMetrics(
        phase=phase,
        split=split,
        samples=int(mask.sum().item()),
        normal_anchor_mse=float(torch.square(normal - reference).mean().item()),
        reset_anchor_mse=float(torch.square(reset - reference).mean().item()),
        normal_reset_action_distance_mean=float(distances.mean().item()),
        normal_reset_action_distance_min=float(distances.min().item()),
        normal_reset_action_distance_p10=float(torch.quantile(distances, 0.10).item()),
        margin_pass_rate=float((distances >= float(margin)).float().mean().item()),
    )


def optimize_actor_coupling(
    *,
    checkpoint_path: Path,
    env_config_path: Path,
    episodes: int,
    seed: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    train_fraction: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    anchor_coef: float,
    contrast_coef: float,
    action_margin: float,
    grad_clip_norm: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    resolved_device = resolve_device(device)
    torch.manual_seed(seed)
    np.random.seed(seed)
    model, source_checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    reference_model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    reference_model.eval()
    for parameter in reference_model.parameters():
        parameter.requires_grad_(False)
    env_config = load_env_config(env_config_path)
    batch = collect_hidden_envelope_objective_batch(
        model=reference_model,
        env_config=env_config,
        episodes=episodes,
        seed=seed,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        device=resolved_device,
    )
    train_mask_np, test_mask_np = _sample_masks(batch, train_fraction=train_fraction, seed=seed + 41)

    for parameter in model.parameters():
        parameter.requires_grad_(False)
    trainable_parameters = actor_coupling_trainable_parameters(model)
    for parameter in trainable_parameters:
        parameter.requires_grad_(True)
    optimizer = torch.optim.AdamW(trainable_parameters, lr=learning_rate, weight_decay=1e-4)

    observations = torch.as_tensor(batch.observations, dtype=torch.float32, device=resolved_device)
    dones = torch.as_tensor(batch.dones, dtype=torch.float32, device=resolved_device)
    train_mask = torch.as_tensor(train_mask_np, dtype=torch.bool, device=resolved_device)
    test_mask = torch.as_tensor(test_mask_np, dtype=torch.bool, device=resolved_device)
    with torch.no_grad():
        reference_normal_actions, _ = _action_mean_sequences(reference_model, observations, dones)

    before_metrics = [
        _actor_coupling_metrics(
            model=model,
            reference_normal_actions=reference_normal_actions,
            observations=observations,
            dones=dones,
            mask=train_mask,
            margin=action_margin,
            phase="before",
            split="train",
        ),
        _actor_coupling_metrics(
            model=model,
            reference_normal_actions=reference_normal_actions,
            observations=observations,
            dones=dones,
            mask=test_mask,
            margin=action_margin,
            phase="before",
            split="test",
        ),
    ]

    rng = np.random.default_rng(seed + 103)
    train_positions = torch.nonzero(train_mask.reshape(-1), as_tuple=False).squeeze(1).cpu().numpy()
    if len(train_positions) == 0:
        raise ValueError("actor coupling objective has no train samples")
    flat_reference = reference_normal_actions.reshape(-1, reference_normal_actions.shape[-1]).detach()
    train_rows: list[dict[str, Any]] = []
    for step in range(1, max(1, int(steps)) + 1):
        normal_actions, reset_actions = _action_mean_sequences(model, observations, dones)
        flat_normal = normal_actions.reshape(-1, normal_actions.shape[-1])
        flat_reset = reset_actions.reshape(-1, reset_actions.shape[-1])
        batch_positions = rng.choice(
            train_positions,
            size=min(batch_size, len(train_positions)),
            replace=len(train_positions) < batch_size,
        )
        batch_index = torch.as_tensor(batch_positions, dtype=torch.long, device=resolved_device)
        normal = flat_normal[batch_index]
        reset = flat_reset[batch_index]
        reference = flat_reference[batch_index]
        anchor_loss = torch.square(normal - reference).mean()
        distances = torch.linalg.vector_norm(normal - reset, dim=-1)
        contrast_loss = torch.nn.functional.softplus(float(action_margin) - distances).mean()
        loss = anchor_coef * anchor_loss + contrast_coef * contrast_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = nn.utils.clip_grad_norm_(trainable_parameters, grad_clip_norm)
        optimizer.step()
        if step == 1 or step == steps or step % max(1, steps // 10) == 0:
            train_rows.append(
                {
                    "step": step,
                    "loss": float(loss.detach().cpu().item()),
                    "anchor_loss": float(anchor_loss.detach().cpu().item()),
                    "contrast_loss": float(contrast_loss.detach().cpu().item()),
                    "action_distance_mean": float(distances.detach().mean().cpu().item()),
                    "action_distance_min": float(distances.detach().min().cpu().item()),
                    "margin_pass_rate": float((distances.detach() >= float(action_margin)).float().mean().cpu().item()),
                    "grad_norm": float(
                        grad_norm.detach().cpu().item() if isinstance(grad_norm, torch.Tensor) else grad_norm
                    ),
                }
            )

    after_metrics = [
        _actor_coupling_metrics(
            model=model,
            reference_normal_actions=reference_normal_actions,
            observations=observations,
            dones=dones,
            mask=train_mask,
            margin=action_margin,
            phase="after",
            split="train",
        ),
        _actor_coupling_metrics(
            model=model,
            reference_normal_actions=reference_normal_actions,
            observations=observations,
            dones=dones,
            mask=test_mask,
            margin=action_margin,
            phase="after",
            split="test",
        ),
    ]

    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    train_metrics_csv = run_dir / "train_metrics.csv"
    action_metrics_csv = run_dir / "action_coupling_metrics.csv"
    checkpoint_path_out = run_dir / "optimized_checkpoint.pt"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(samples_csv, batch.rows)
    write_csv_rows(train_metrics_csv, train_rows)
    metric_rows = [metric.__dict__ for metric in [*before_metrics, *after_metrics]]
    write_csv_rows(action_metrics_csv, metric_rows)
    save_checkpoint_like(
        model,
        source_checkpoint,
        checkpoint_path_out,
        {
            "run_type": "actor_coupling_objective_only",
            "init_checkpoint": checkpoint_path,
            "env_config": env_config_path,
            "steps": steps,
            "seed": seed,
            "anchor_coef": anchor_coef,
            "contrast_coef": contrast_coef,
            "action_margin": action_margin,
        },
    )
    before_test = next(row for row in metric_rows if row["phase"] == "before" and row["split"] == "test")
    after_test = next(row for row in metric_rows if row["phase"] == "after" and row["split"] == "test")
    distance_gain = float(
        after_test["normal_reset_action_distance_mean"] - before_test["normal_reset_action_distance_mean"]
    )
    summary = {
        "run_type": "actor_coupling_objective_only",
        "checkpoint": checkpoint_path,
        "optimized_checkpoint": checkpoint_path_out,
        "env_config": env_config_path,
        "episodes": episodes,
        "samples": int(len(batch.rows)),
        "train_samples": int(train_mask.sum().item()),
        "test_samples": int(test_mask.sum().item()),
        "seed": seed,
        "horizon_steps": horizon_steps,
        "sample_stride": sample_stride,
        "steps": steps,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "anchor_coef": anchor_coef,
        "contrast_coef": contrast_coef,
        "action_margin": action_margin,
        "before_test_action_distance_mean": float(before_test["normal_reset_action_distance_mean"]),
        "after_test_action_distance_mean": float(after_test["normal_reset_action_distance_mean"]),
        "test_action_distance_gain": distance_gain,
        "after_test_normal_anchor_mse": float(after_test["normal_anchor_mse"]),
        "after_test_margin_pass_rate": float(after_test["margin_pass_rate"]),
        "artifacts": {
            "samples_csv": samples_csv,
            "train_metrics_csv": train_metrics_csv,
            "action_metrics_csv": action_metrics_csv,
            "optimized_checkpoint": checkpoint_path_out,
        },
    }
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "actor_coupling_objective_only",
            "checkpoint": checkpoint_path,
            "env_config": env_config_path,
            "episodes": episodes,
            "seed": seed,
            "steps": steps,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "anchor_coef": anchor_coef,
            "contrast_coef": contrast_coef,
            "action_margin": action_margin,
            "artifacts": summary["artifacts"],
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize actor coupling to recurrent hidden belief.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=9520)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    parser.add_argument("--anchor-coef", type=float, default=10.0)
    parser.add_argument("--contrast-coef", type=float, default=1.0)
    parser.add_argument("--action-margin", type=float, default=0.04)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="actor_coupling_optimize", seed=args.seed)
    summary = optimize_actor_coupling(
        checkpoint_path=args.checkpoint,
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        anchor_coef=args.anchor_coef,
        contrast_coef=args.contrast_coef,
        action_margin=args.action_margin,
        grad_clip_norm=args.grad_clip_norm,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.read_csv(run_dir / "action_coupling_metrics.csv").to_string(index=False))
    print(f"run_dir={run_dir}")
    print(f"test_action_distance_gain={summary['test_action_distance_gain']:.6f}")
    print(f"after_test_normal_anchor_mse={summary['after_test_normal_anchor_mse']:.6f}")


if __name__ == "__main__":
    main()
