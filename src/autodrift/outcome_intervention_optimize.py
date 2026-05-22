"""Optimize the outcome-weighted intervention objective outside PPO."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, to_jsonable, write_json
from autodrift.actor_coupling_optimize import actor_coupling_trainable_parameters
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_optimize import collect_hidden_envelope_objective_batch
from autodrift.intervention_objectives import (
    OutcomeInterventionSnippets,
    TrajectoryActionAnchor,
    load_trajectory_action_anchor,
    load_outcome_intervention_snippets,
    outcome_weighted_intervention_loss,
    trajectory_action_anchor_loss,
    weighted_mean,
)
from autodrift.outcome_intervention_eval import evaluate_checkpoint
from autodrift.train_ppo import resolve_device


def _snippet_dims(snippet_npz: Path) -> tuple[int, int]:
    data = np.load(snippet_npz)
    return int(data["observation"].shape[1]), int(data["preferred_action"].shape[1])


def _trainable_parameters(
    model: torch.nn.Module,
    *,
    freeze_log_std: bool,
    train_scope: str,
) -> list[torch.nn.Parameter]:
    if train_scope not in {"all", "actor_coupling"}:
        raise ValueError("train_scope must be 'all' or 'actor_coupling'")
    if train_scope == "actor_coupling":
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        parameters = actor_coupling_trainable_parameters(model)  # type: ignore[arg-type]
        for parameter in parameters:
            parameter.requires_grad_(True)
        if not freeze_log_std and hasattr(model, "log_std"):
            model.log_std.requires_grad_(True)
            parameters = [*parameters, model.log_std]
        return parameters
    if freeze_log_std and hasattr(model, "log_std"):
        model.log_std.requires_grad_(False)
    return [parameter for parameter in model.parameters() if parameter.requires_grad]


def _collect_action_anchor(
    *,
    checkpoint: Path,
    env_config_path: Path,
    device: torch.device,
    obs_dim: int,
    episodes: int,
    seed: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
) -> dict[str, torch.Tensor]:
    reference_model, _ = load_actor_critic_checkpoint(checkpoint, device=str(device), obs_dim=obs_dim)
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
        device=device,
    )
    observations = torch.as_tensor(batch.observations, dtype=torch.float32, device=device)
    dones = torch.as_tensor(batch.dones, dtype=torch.float32, device=device)
    sample_mask = torch.as_tensor(batch.sample_mask, dtype=torch.bool, device=device)
    positions = torch.nonzero(sample_mask.reshape(-1), as_tuple=False).squeeze(1)
    if int(positions.numel()) == 0:
        raise ValueError("action anchor batch has no sampled positions")
    with torch.no_grad():
        initial_hidden = reference_model.initial_hidden(observations.shape[1], device)
        reference_actions = reference_model.action_mean_recurrent_sequence(observations, initial_hidden, dones)
    return {
        "observations": observations,
        "dones": dones,
        "positions": positions,
        "reference_actions": reference_actions.detach(),
    }


def _action_anchor_mse(model: torch.nn.Module, anchor: dict[str, torch.Tensor]) -> torch.Tensor:
    observations = anchor["observations"]
    dones = anchor["dones"]
    initial_hidden = model.initial_hidden(observations.shape[1], observations.device)  # type: ignore[attr-defined]
    actions = model.action_mean_recurrent_sequence(observations, initial_hidden, dones)  # type: ignore[attr-defined]
    flat_actions = actions.reshape(-1, actions.shape[-1])
    flat_reference = anchor["reference_actions"].reshape(-1, actions.shape[-1])
    positions = anchor["positions"]
    return torch.square(flat_actions[positions] - flat_reference[positions].detach()).mean()


def _sampled_action_anchor_loss(
    model: torch.nn.Module,
    anchor: dict[str, torch.Tensor],
    *,
    batch_size: int,
) -> torch.Tensor:
    positions = anchor["positions"]
    count = int(positions.numel())
    batch_count = max(1, min(int(batch_size), count))
    sample_index = torch.randint(count, (batch_count,), device=positions.device)
    sampled_positions = positions[sample_index]
    observations = anchor["observations"]
    dones = anchor["dones"]
    initial_hidden = model.initial_hidden(observations.shape[1], observations.device)  # type: ignore[attr-defined]
    actions = model.action_mean_recurrent_sequence(observations, initial_hidden, dones)  # type: ignore[attr-defined]
    flat_actions = actions.reshape(-1, actions.shape[-1])
    flat_reference = anchor["reference_actions"].reshape(-1, actions.shape[-1])
    return torch.square(flat_actions[sampled_positions] - flat_reference[sampled_positions].detach()).mean()


def _collect_snippet_action_anchor(
    *,
    checkpoint: Path,
    snippets: OutcomeInterventionSnippets,
    device: torch.device,
    obs_dim: int,
    include_rejected_hidden: bool,
) -> dict[str, torch.Tensor]:
    reference_model, _ = load_actor_critic_checkpoint(checkpoint, device=str(device), obs_dim=obs_dim)
    reference_model.eval()
    for parameter in reference_model.parameters():
        parameter.requires_grad_(False)
    with torch.no_grad():
        preferred_dist, _, _ = reference_model.forward_recurrent(
            snippets.observation,
            snippets.preferred_hidden,
        )
        reference_preferred_action = torch.tanh(preferred_dist.mean).detach()
        reference_rejected_action = torch.empty_like(reference_preferred_action)
        if include_rejected_hidden:
            rejected_dist, _, _ = reference_model.forward_recurrent(
                snippets.observation,
                snippets.rejected_hidden,
            )
            reference_rejected_action = torch.tanh(rejected_dist.mean).detach()
    return {
        "observation": snippets.observation,
        "preferred_hidden": snippets.preferred_hidden,
        "rejected_hidden": snippets.rejected_hidden,
        "weight": snippets.weight.detach(),
        "reference_preferred_action": reference_preferred_action,
        "reference_rejected_action": reference_rejected_action,
        "include_rejected_hidden": torch.tensor(
            1 if include_rejected_hidden else 0,
            dtype=torch.int64,
            device=device,
        ),
    }


def _snippet_action_anchor_errors(
    model: torch.nn.Module,
    anchor: dict[str, torch.Tensor],
    indices: torch.Tensor,
) -> torch.Tensor:
    observation = anchor["observation"][indices]
    preferred_hidden = anchor["preferred_hidden"][indices]
    preferred_dist, _, _ = model.forward_recurrent(observation, preferred_hidden)  # type: ignore[attr-defined]
    preferred_action = torch.tanh(preferred_dist.mean)
    error = torch.square(preferred_action - anchor["reference_preferred_action"][indices].detach()).mean(dim=-1)
    if bool(int(anchor["include_rejected_hidden"].detach().cpu().item())):
        rejected_hidden = anchor["rejected_hidden"][indices]
        rejected_dist, _, _ = model.forward_recurrent(observation, rejected_hidden)  # type: ignore[attr-defined]
        rejected_action = torch.tanh(rejected_dist.mean)
        rejected_error = torch.square(
            rejected_action - anchor["reference_rejected_action"][indices].detach()
        ).mean(dim=-1)
        error = 0.5 * (error + rejected_error)
    return error


def _snippet_action_anchor_mse(model: torch.nn.Module, anchor: dict[str, torch.Tensor]) -> torch.Tensor:
    indices = torch.arange(anchor["observation"].shape[0], device=anchor["observation"].device)
    errors = _snippet_action_anchor_errors(model, anchor, indices)
    return weighted_mean(errors, anchor["weight"])


def _sampled_snippet_action_anchor_loss(
    model: torch.nn.Module,
    anchor: dict[str, torch.Tensor],
    *,
    batch_size: int,
) -> torch.Tensor:
    count = int(anchor["observation"].shape[0])
    batch_count = max(1, min(int(batch_size), count))
    indices = torch.randint(count, (batch_count,), device=anchor["observation"].device)
    errors = _snippet_action_anchor_errors(model, anchor, indices)
    return weighted_mean(errors, anchor["weight"][indices])


def _trajectory_action_anchor_mse(model: torch.nn.Module, anchor: TrajectoryActionAnchor) -> torch.Tensor:
    dist, _, _ = model.forward_recurrent(anchor.observation, anchor.hidden)  # type: ignore[attr-defined]
    action = torch.tanh(dist.mean)
    error = torch.square(action - anchor.reference_action.detach()).mean(dim=-1)
    return weighted_mean(error, anchor.weight.detach())


def save_checkpoint_like(
    *,
    model: torch.nn.Module,
    source_checkpoint: dict[str, Any],
    path: Path,
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": source_checkpoint["config"],
            "metadata": to_jsonable(metadata),
        },
        path,
    )


def optimize_outcome_intervention(
    *,
    init_checkpoint: Path,
    snippet_npz: Path,
    device: str,
    steps: int,
    batch_size: int,
    learning_rate: float,
    logprob_margin: float,
    seed: int,
    freeze_log_std: bool,
    grad_clip_norm: float,
    log_interval: int,
    run_dir: Path,
    eval_batch_size: int,
    eval_batches: int,
    eval_seed: int,
    train_scope: str = "all",
    action_anchor_checkpoint: Path | None = None,
    action_anchor_env_config: Path | None = None,
    action_anchor_coef: float = 0.0,
    action_anchor_episodes: int = 30,
    action_anchor_seed: int = 0,
    action_anchor_horizon_steps: int = 15,
    action_anchor_sample_stride: int = 3,
    action_anchor_max_samples: int | None = 800,
    action_anchor_batch_size: int = 256,
    snippet_action_anchor_checkpoint: Path | None = None,
    snippet_action_anchor_coef: float = 0.0,
    snippet_action_anchor_batch_size: int = 128,
    snippet_action_anchor_include_rejected_hidden: bool = True,
    trajectory_action_anchor_snapshot_npz: Path | None = None,
    trajectory_action_anchor_coef: float = 0.0,
    trajectory_action_anchor_batch_size: int = 128,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    torch.manual_seed(int(seed))
    np.random.seed(int(seed))
    obs_dim, act_dim = _snippet_dims(snippet_npz)
    model, source_checkpoint = load_actor_critic_checkpoint(init_checkpoint, device=str(resolved_device), obs_dim=obs_dim)
    snippets = load_outcome_intervention_snippets(
        snippet_npz,
        device=next(model.parameters()).device,
        obs_dim=obs_dim,
        hidden_size=model.actor_mean.in_features,
        act_dim=act_dim,
    )
    parameters = _trainable_parameters(model, freeze_log_std=freeze_log_std, train_scope=train_scope)
    if not parameters:
        raise RuntimeError("no trainable parameters are available for outcome objective optimization")
    optimizer = torch.optim.Adam(parameters, lr=float(learning_rate))
    anchor: dict[str, torch.Tensor] | None = None
    if action_anchor_coef > 0.0:
        if action_anchor_env_config is None:
            raise ValueError("action_anchor_env_config is required when action_anchor_coef > 0")
        anchor_checkpoint = action_anchor_checkpoint or init_checkpoint
        anchor = _collect_action_anchor(
            checkpoint=anchor_checkpoint,
            env_config_path=action_anchor_env_config,
            device=resolved_device,
            obs_dim=obs_dim,
            episodes=action_anchor_episodes,
            seed=action_anchor_seed,
            horizon_steps=action_anchor_horizon_steps,
            sample_stride=action_anchor_sample_stride,
            max_samples=action_anchor_max_samples,
        )
    snippet_action_anchor: dict[str, torch.Tensor] | None = None
    if snippet_action_anchor_coef > 0.0:
        anchor_checkpoint = snippet_action_anchor_checkpoint or init_checkpoint
        snippet_action_anchor = _collect_snippet_action_anchor(
            checkpoint=anchor_checkpoint,
            snippets=snippets,
            device=resolved_device,
            obs_dim=obs_dim,
            include_rejected_hidden=snippet_action_anchor_include_rejected_hidden,
        )
    trajectory_action_anchor: TrajectoryActionAnchor | None = None
    if trajectory_action_anchor_coef < 0.0:
        raise ValueError("trajectory_action_anchor_coef must be non-negative")
    if trajectory_action_anchor_batch_size < 1:
        raise ValueError("trajectory_action_anchor_batch_size must be at least 1")
    if trajectory_action_anchor_coef > 0.0:
        if trajectory_action_anchor_snapshot_npz is None:
            raise ValueError("trajectory_action_anchor_snapshot_npz is required when trajectory_action_anchor_coef > 0")
        trajectory_action_anchor = load_trajectory_action_anchor(
            trajectory_action_anchor_snapshot_npz,
            device=resolved_device,
            obs_dim=obs_dim,
            hidden_size=model.actor_mean.in_features,
            act_dim=act_dim,
        )

    before_summary, before_batches = evaluate_checkpoint(
        label="before",
        checkpoint=init_checkpoint,
        snippet_npz=snippet_npz,
        device=str(resolved_device),
        batch_size=eval_batch_size,
        batches=eval_batches,
        seed=eval_seed,
        logprob_margin=logprob_margin,
    )
    with torch.no_grad():
        before_action_anchor_mse = float(_action_anchor_mse(model, anchor).detach().cpu().item()) if anchor else None
        before_snippet_action_anchor_mse = (
            float(_snippet_action_anchor_mse(model, snippet_action_anchor).detach().cpu().item())
            if snippet_action_anchor
            else None
        )
        before_trajectory_action_anchor_mse = (
            float(_trajectory_action_anchor_mse(model, trajectory_action_anchor).detach().cpu().item())
            if trajectory_action_anchor
            else None
        )

    metrics: list[dict[str, Any]] = []
    model.train()
    total_steps = max(1, int(steps))
    interval = max(1, int(log_interval))
    for step in range(1, total_steps + 1):
        optimizer.zero_grad(set_to_none=True)
        loss = outcome_weighted_intervention_loss(
            model,
            snippets,
            batch_size=batch_size,
            logprob_margin=logprob_margin,
        )
        outcome_loss = loss
        action_anchor_loss = torch.zeros((), dtype=torch.float32, device=resolved_device)
        snippet_action_anchor_loss = torch.zeros((), dtype=torch.float32, device=resolved_device)
        trajectory_anchor_loss = torch.zeros((), dtype=torch.float32, device=resolved_device)
        if anchor is not None:
            action_anchor_loss = _sampled_action_anchor_loss(
                model,
                anchor,
                batch_size=action_anchor_batch_size,
            )
            loss = outcome_loss + float(action_anchor_coef) * action_anchor_loss
        if snippet_action_anchor is not None:
            snippet_action_anchor_loss = _sampled_snippet_action_anchor_loss(
                model,
                snippet_action_anchor,
                batch_size=snippet_action_anchor_batch_size,
            )
            loss = loss + float(snippet_action_anchor_coef) * snippet_action_anchor_loss
        if trajectory_action_anchor is not None:
            trajectory_anchor_loss = trajectory_action_anchor_loss(
                model,
                trajectory_action_anchor,
                batch_size=trajectory_action_anchor_batch_size,
            )
            loss = loss + float(trajectory_action_anchor_coef) * trajectory_anchor_loss
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, max_norm=float(grad_clip_norm))
        optimizer.step()
        if step == 1 or step == total_steps or step % interval == 0:
            metrics.append(
                {
                    "step": step,
                    "loss": float(loss.detach().cpu().item()),
                    "outcome_loss": float(outcome_loss.detach().cpu().item()),
                    "action_anchor_loss": float(action_anchor_loss.detach().cpu().item()),
                    "action_anchor_coef": float(action_anchor_coef),
                    "snippet_action_anchor_loss": float(snippet_action_anchor_loss.detach().cpu().item()),
                    "snippet_action_anchor_coef": float(snippet_action_anchor_coef),
                    "trajectory_action_anchor_loss": float(trajectory_anchor_loss.detach().cpu().item()),
                    "trajectory_action_anchor_coef": float(trajectory_action_anchor_coef),
                    "grad_norm": float(grad_norm.detach().cpu().item() if isinstance(grad_norm, torch.Tensor) else grad_norm),
                    "learning_rate": float(learning_rate),
                }
            )

    checkpoint_path = run_dir / "optimized_checkpoint.pt"
    save_checkpoint_like(
        model=model,
        source_checkpoint=source_checkpoint,
        path=checkpoint_path,
        metadata={
            "run_type": "outcome_intervention_optimize",
            "init_checkpoint": init_checkpoint,
            "snippet_npz": snippet_npz,
            "steps": total_steps,
            "batch_size": int(batch_size),
            "learning_rate": float(learning_rate),
            "logprob_margin": float(logprob_margin),
            "seed": int(seed),
            "freeze_log_std": bool(freeze_log_std),
            "train_scope": train_scope,
            "action_anchor_checkpoint": action_anchor_checkpoint,
            "action_anchor_env_config": action_anchor_env_config,
            "action_anchor_coef": float(action_anchor_coef),
            "action_anchor_episodes": int(action_anchor_episodes),
            "action_anchor_seed": int(action_anchor_seed),
            "action_anchor_horizon_steps": int(action_anchor_horizon_steps),
            "action_anchor_sample_stride": int(action_anchor_sample_stride),
            "action_anchor_max_samples": action_anchor_max_samples,
            "action_anchor_batch_size": int(action_anchor_batch_size),
            "snippet_action_anchor_checkpoint": snippet_action_anchor_checkpoint,
            "snippet_action_anchor_coef": float(snippet_action_anchor_coef),
            "snippet_action_anchor_batch_size": int(snippet_action_anchor_batch_size),
            "snippet_action_anchor_include_rejected_hidden": bool(snippet_action_anchor_include_rejected_hidden),
            "trajectory_action_anchor_snapshot_npz": trajectory_action_anchor_snapshot_npz,
            "trajectory_action_anchor_coef": float(trajectory_action_anchor_coef),
            "trajectory_action_anchor_batch_size": int(trajectory_action_anchor_batch_size),
            "grad_clip_norm": float(grad_clip_norm),
        },
    )
    after_summary, after_batches = evaluate_checkpoint(
        label="after",
        checkpoint=checkpoint_path,
        snippet_npz=snippet_npz,
        device=str(resolved_device),
        batch_size=eval_batch_size,
        batches=eval_batches,
        seed=eval_seed,
        logprob_margin=logprob_margin,
    )
    with torch.no_grad():
        after_action_anchor_mse = float(_action_anchor_mse(model, anchor).detach().cpu().item()) if anchor else None
        after_snippet_action_anchor_mse = (
            float(_snippet_action_anchor_mse(model, snippet_action_anchor).detach().cpu().item())
            if snippet_action_anchor
            else None
        )
        after_trajectory_action_anchor_mse = (
            float(_trajectory_action_anchor_mse(model, trajectory_action_anchor).detach().cpu().item())
            if trajectory_action_anchor
            else None
        )

    policy_summary = pd.DataFrame([before_summary, after_summary])
    batch_losses = pd.DataFrame([*before_batches, *after_batches])
    train_metrics = pd.DataFrame(metrics)
    improvement = float(before_summary["loss_mean"] - after_summary["loss_mean"])
    summary = {
        "run_type": "outcome_intervention_optimize",
        "init_checkpoint": init_checkpoint,
        "optimized_checkpoint": checkpoint_path,
        "snippet_npz": snippet_npz,
        "device": str(resolved_device),
        "steps": total_steps,
        "batch_size": int(batch_size),
        "learning_rate": float(learning_rate),
        "logprob_margin": float(logprob_margin),
        "seed": int(seed),
        "freeze_log_std": bool(freeze_log_std),
        "train_scope": train_scope,
        "action_anchor_checkpoint": action_anchor_checkpoint,
        "action_anchor_env_config": action_anchor_env_config,
        "action_anchor_coef": float(action_anchor_coef),
        "action_anchor_episodes": int(action_anchor_episodes),
        "action_anchor_seed": int(action_anchor_seed),
        "action_anchor_horizon_steps": int(action_anchor_horizon_steps),
        "action_anchor_sample_stride": int(action_anchor_sample_stride),
        "action_anchor_max_samples": action_anchor_max_samples,
        "action_anchor_batch_size": int(action_anchor_batch_size),
        "snippet_action_anchor_checkpoint": snippet_action_anchor_checkpoint,
        "snippet_action_anchor_coef": float(snippet_action_anchor_coef),
        "snippet_action_anchor_batch_size": int(snippet_action_anchor_batch_size),
        "snippet_action_anchor_include_rejected_hidden": bool(snippet_action_anchor_include_rejected_hidden),
        "trajectory_action_anchor_snapshot_npz": trajectory_action_anchor_snapshot_npz,
        "trajectory_action_anchor_coef": float(trajectory_action_anchor_coef),
        "trajectory_action_anchor_batch_size": int(trajectory_action_anchor_batch_size),
        "before_action_anchor_mse": before_action_anchor_mse,
        "after_action_anchor_mse": after_action_anchor_mse,
        "before_snippet_action_anchor_mse": before_snippet_action_anchor_mse,
        "after_snippet_action_anchor_mse": after_snippet_action_anchor_mse,
        "before_trajectory_action_anchor_mse": before_trajectory_action_anchor_mse,
        "after_trajectory_action_anchor_mse": after_trajectory_action_anchor_mse,
        "grad_clip_norm": float(grad_clip_norm),
        "eval_batch_size": int(eval_batch_size),
        "eval_batches": int(eval_batches),
        "eval_seed": int(eval_seed),
        "before_loss_mean": float(before_summary["loss_mean"]),
        "after_loss_mean": float(after_summary["loss_mean"]),
        "loss_mean_improvement": improvement,
        "passed_objective_sanity": improvement > 0.0,
        "train_metrics_csv": run_dir / "train_metrics.csv",
        "policy_summary_csv": run_dir / "policy_summary.csv",
        "batch_losses_csv": run_dir / "batch_losses.csv",
    }
    train_metrics.to_csv(run_dir / "train_metrics.csv", index=False)
    policy_summary.to_csv(run_dir / "policy_summary.csv", index=False)
    batch_losses.to_csv(run_dir / "batch_losses.csv", index=False)
    write_json(run_dir / "summary.json", summary)
    return summary, train_metrics, policy_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize outcome intervention loss outside PPO.")
    parser.add_argument("--init-checkpoint", type=Path, required=True)
    parser.add_argument("--snippet-npz", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--logprob-margin", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--train-log-std", action="store_true")
    parser.add_argument("--train-scope", choices=["all", "actor_coupling"], default="all")
    parser.add_argument("--action-anchor-checkpoint", type=Path, default=None)
    parser.add_argument("--action-anchor-env-config", type=Path, default=None)
    parser.add_argument("--action-anchor-coef", type=float, default=0.0)
    parser.add_argument("--action-anchor-episodes", type=int, default=30)
    parser.add_argument("--action-anchor-seed", type=int, default=0)
    parser.add_argument("--action-anchor-horizon-steps", type=int, default=15)
    parser.add_argument("--action-anchor-sample-stride", type=int, default=3)
    parser.add_argument("--action-anchor-max-samples", type=int, default=800)
    parser.add_argument("--action-anchor-batch-size", type=int, default=256)
    parser.add_argument("--snippet-action-anchor-checkpoint", type=Path, default=None)
    parser.add_argument("--snippet-action-anchor-coef", type=float, default=0.0)
    parser.add_argument("--snippet-action-anchor-batch-size", type=int, default=128)
    parser.add_argument("--snippet-action-anchor-preferred-only", action="store_true")
    parser.add_argument("--trajectory-action-anchor-snapshot-npz", type=Path, default=None)
    parser.add_argument("--trajectory-action-anchor-coef", type=float, default=0.0)
    parser.add_argument("--trajectory-action-anchor-batch-size", type=int, default=128)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--log-interval", type=int, default=20)
    parser.add_argument("--eval-batch-size", type=int, default=128)
    parser.add_argument("--eval-batches", type=int, default=20)
    parser.add_argument("--eval-seed", type=int, default=0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="outcome_intervention_optimize", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    summary, train_metrics, policy_summary = optimize_outcome_intervention(
        init_checkpoint=args.init_checkpoint,
        snippet_npz=args.snippet_npz,
        device=args.device,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        logprob_margin=args.logprob_margin,
        seed=args.seed,
        freeze_log_std=not args.train_log_std,
        train_scope=args.train_scope,
        grad_clip_norm=args.grad_clip_norm,
        log_interval=args.log_interval,
        run_dir=run_dir,
        eval_batch_size=args.eval_batch_size,
        eval_batches=args.eval_batches,
        eval_seed=args.eval_seed,
        action_anchor_checkpoint=args.action_anchor_checkpoint,
        action_anchor_env_config=args.action_anchor_env_config,
        action_anchor_coef=args.action_anchor_coef,
        action_anchor_episodes=args.action_anchor_episodes,
        action_anchor_seed=args.action_anchor_seed,
        action_anchor_horizon_steps=args.action_anchor_horizon_steps,
        action_anchor_sample_stride=args.action_anchor_sample_stride,
        action_anchor_max_samples=args.action_anchor_max_samples,
        action_anchor_batch_size=args.action_anchor_batch_size,
        snippet_action_anchor_checkpoint=args.snippet_action_anchor_checkpoint,
        snippet_action_anchor_coef=args.snippet_action_anchor_coef,
        snippet_action_anchor_batch_size=args.snippet_action_anchor_batch_size,
        snippet_action_anchor_include_rejected_hidden=not args.snippet_action_anchor_preferred_only,
        trajectory_action_anchor_snapshot_npz=args.trajectory_action_anchor_snapshot_npz,
        trajectory_action_anchor_coef=args.trajectory_action_anchor_coef,
        trajectory_action_anchor_batch_size=args.trajectory_action_anchor_batch_size,
    )
    print(train_metrics.tail(5).to_string(index=False))
    print(policy_summary.to_string(index=False))
    print(f"loss_mean_improvement={summary['loss_mean_improvement']:.6f}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
