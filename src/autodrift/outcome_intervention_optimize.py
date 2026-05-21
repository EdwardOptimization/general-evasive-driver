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
from autodrift.intervention_objectives import (
    load_outcome_intervention_snippets,
    outcome_weighted_intervention_loss,
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
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, max_norm=float(grad_clip_norm))
        optimizer.step()
        if step == 1 or step == total_steps or step % interval == 0:
            metrics.append(
                {
                    "step": step,
                    "loss": float(loss.detach().cpu().item()),
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
    )
    print(train_metrics.tail(5).to_string(index=False))
    print(policy_summary.to_string(index=False))
    print(f"loss_mean_improvement={summary['loss_mean_improvement']:.6f}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
