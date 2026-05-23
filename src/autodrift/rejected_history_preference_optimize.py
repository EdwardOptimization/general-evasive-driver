"""Optimize rejected-history preference loss outside PPO."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.actor_coupling_optimize import actor_coupling_trainable_parameters
from autodrift.artifacts import make_run_dir, to_jsonable, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.intervention_objectives import (
    load_rejected_history_preference_snippets,
    rejected_history_preference_loss,
)
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.rejected_history_preference_objective import (
    PreferenceLossConfig,
    evaluate_checkpoint,
)
from autodrift.train_ppo import resolve_device


def _trainable_parameters(
    model: torch.nn.Module,
    *,
    train_scope: str,
    train_log_std: bool,
) -> list[torch.nn.Parameter]:
    if train_scope not in {"all", "actor_coupling"}:
        raise ValueError("train_scope must be 'all' or 'actor_coupling'")
    if train_scope == "actor_coupling":
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        parameters = actor_coupling_trainable_parameters(model)  # type: ignore[arg-type]
        for parameter in parameters:
            parameter.requires_grad_(True)
        if train_log_std and hasattr(model, "log_std"):
            model.log_std.requires_grad_(True)
            parameters = [*parameters, model.log_std]
        return parameters
    if not train_log_std and hasattr(model, "log_std"):
        model.log_std.requires_grad_(False)
    return [parameter for parameter in model.parameters() if parameter.requires_grad]


def optimize_rejected_history_preference(
    *,
    init_checkpoint: Path,
    preference_npz: Path,
    device: str,
    steps: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    train_scope: str,
    train_log_std: bool,
    grad_clip_norm: float,
    log_interval: int,
    loss_config: PreferenceLossConfig,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    torch.manual_seed(int(seed))
    np.random.seed(int(seed))
    data = np.load(preference_npz)
    obs_dim = int(data["observation"].shape[1])
    act_dim = int(data["preferred_action"].shape[1])
    model, source_checkpoint = load_actor_critic_checkpoint(init_checkpoint, device=str(resolved_device), obs_dim=obs_dim)
    snippets = load_rejected_history_preference_snippets(
        preference_npz,
        device=next(model.parameters()).device,
        obs_dim=obs_dim,
        hidden_size=int(model.actor_mean.in_features),
        act_dim=act_dim,
    )
    parameters = _trainable_parameters(model, train_scope=train_scope, train_log_std=train_log_std)
    if not parameters:
        raise RuntimeError("no trainable parameters are available for preference optimization")
    before_summary, _ = evaluate_checkpoint(
        checkpoint=CheckpointSpec("before", init_checkpoint),
        corpus_npz=preference_npz,
        device=str(resolved_device),
        loss_config=loss_config,
    )
    optimizer = torch.optim.Adam(parameters, lr=float(learning_rate))
    metrics: list[dict[str, Any]] = []
    total_steps = max(1, int(steps))
    interval = max(1, int(log_interval))
    model.train()
    for step in range(1, total_steps + 1):
        optimizer.zero_grad(set_to_none=True)
        loss = rejected_history_preference_loss(
            model,
            snippets,
            batch_size=batch_size,
            preferred_logprob_margin=loss_config.preferred_logprob_margin,
            wrong_logprob_margin=loss_config.wrong_logprob_margin,
            wrong_preference_coef=loss_config.wrong_preference_coef,
        )
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, max_norm=float(grad_clip_norm))
        optimizer.step()
        if step == 1 or step == total_steps or step % interval == 0:
            metrics.append(
                {
                    "step": int(step),
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
            "run_type": "rejected_history_preference_optimize",
            "init_checkpoint": init_checkpoint,
            "preference_npz": preference_npz,
            "steps": total_steps,
            "batch_size": int(batch_size),
            "learning_rate": float(learning_rate),
            "seed": int(seed),
            "train_scope": train_scope,
            "train_log_std": bool(train_log_std),
            "grad_clip_norm": float(grad_clip_norm),
            "loss_config": asdict(loss_config),
        },
    )
    after_summary, _ = evaluate_checkpoint(
        checkpoint=CheckpointSpec("after", checkpoint_path),
        corpus_npz=preference_npz,
        device=str(resolved_device),
        loss_config=loss_config,
    )
    improvement = float(before_summary["weighted_loss"] - after_summary["weighted_loss"])
    write_csv_rows(run_dir / "train_metrics.csv", metrics)
    write_csv_rows(run_dir / "policy_summary.csv", [before_summary, after_summary])
    summary = {
        "run_type": "rejected_history_preference_optimize",
        "init_checkpoint": init_checkpoint,
        "optimized_checkpoint": checkpoint_path,
        "preference_npz": preference_npz,
        "device": str(resolved_device),
        "steps": total_steps,
        "batch_size": int(batch_size),
        "learning_rate": float(learning_rate),
        "seed": int(seed),
        "train_scope": train_scope,
        "train_log_std": bool(train_log_std),
        "grad_clip_norm": float(grad_clip_norm),
        "loss_config": asdict(loss_config),
        "before_loss": float(before_summary["weighted_loss"]),
        "after_loss": float(after_summary["weighted_loss"]),
        "loss_improvement": improvement,
        "passed_objective_sanity": improvement > 0.0,
        "train_metrics_csv": run_dir / "train_metrics.csv",
        "policy_summary_csv": run_dir / "policy_summary.csv",
        "ppo_or_actor_update_run": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-checkpoint", type=Path, required=True)
    parser.add_argument("--preference-npz", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=17)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=10080)
    parser.add_argument("--train-scope", choices=["all", "actor_coupling"], default="actor_coupling")
    parser.add_argument("--train-log-std", action="store_true")
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--log-interval", type=int, default=10)
    parser.add_argument("--preferred-logprob-margin", type=float, default=0.05)
    parser.add_argument("--wrong-logprob-margin", type=float, default=0.05)
    parser.add_argument("--wrong-preference-coef", type=float, default=1.0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="rejected_history_preference_optimize", seed=args.seed)
    summary = optimize_rejected_history_preference(
        init_checkpoint=args.init_checkpoint,
        preference_npz=args.preference_npz,
        device=args.device,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
        train_scope=args.train_scope,
        train_log_std=args.train_log_std,
        grad_clip_norm=args.grad_clip_norm,
        log_interval=args.log_interval,
        loss_config=PreferenceLossConfig(
            preferred_logprob_margin=args.preferred_logprob_margin,
            wrong_logprob_margin=args.wrong_logprob_margin,
            wrong_preference_coef=args.wrong_preference_coef,
        ),
        run_dir=run_dir,
    )
    print(to_jsonable(summary))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
