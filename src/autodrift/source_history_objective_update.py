"""Tiny no-PPO source-history objective-only update probe."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_history_objective_evaluator import (
    DEFAULT_CORRECT_MARGIN,
    DEFAULT_WRONG_COEF,
    DEFAULT_WRONG_MARGIN,
    run_source_history_objective_evaluator,
)
from autodrift.source_history_policy_gate import (
    _bool_text,
    _checkpoint_contract,
    _history_frames_by_id,
    _load_intervention_observations,
    _load_step0_actions,
    _read_csv,
    _replay_hidden,
)
from autodrift.train_ppo import ActorCritic, resolve_device


@dataclass(frozen=True)
class SourceHistoryBatch:
    observations: torch.Tensor
    correct_hidden: torch.Tensor
    wrong_hidden: torch.Tensor
    preferred_actions: torch.Tensor
    rejected_actions: torch.Tensor


def _clone_state_dict(model: ActorCritic) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def _set_actor_mean_trainable_only(model: ActorCritic) -> None:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.actor_mean.parameters():
        parameter.requires_grad_(True)


def _parameter_counts(model: ActorCritic) -> tuple[int, int]:
    trainable = 0
    frozen = 0
    for parameter in model.parameters():
        count = int(parameter.numel())
        if parameter.requires_grad:
            trainable += count
        else:
            frozen += count
    return trainable, frozen


def _state_delta(base: dict[str, torch.Tensor], updated: dict[str, torch.Tensor]) -> dict[str, Any]:
    actor_sq = 0.0
    non_actor_sq = 0.0
    actor_max = 0.0
    non_actor_max = 0.0
    actor_changed = False
    non_actor_changed = False
    changed_names: list[str] = []
    for name, base_tensor in sorted(base.items()):
        updated_tensor = updated[name].detach().cpu()
        delta = updated_tensor - base_tensor
        max_abs = float(torch.max(torch.abs(delta)).item()) if delta.numel() else 0.0
        sq = float(torch.sum(delta.float().pow(2)).item())
        changed = max_abs > 0.0
        if changed:
            changed_names.append(name)
        if name.startswith("actor_mean."):
            actor_sq += sq
            actor_max = max(actor_max, max_abs)
            actor_changed = actor_changed or changed
        else:
            non_actor_sq += sq
            non_actor_max = max(non_actor_max, max_abs)
            non_actor_changed = non_actor_changed or changed
    return {
        "actor_mean_l2": math.sqrt(actor_sq),
        "actor_mean_max_abs": actor_max,
        "non_actor_mean_l2": math.sqrt(non_actor_sq),
        "non_actor_mean_max_abs": non_actor_max,
        "actor_mean_changed": bool(actor_changed),
        "non_actor_mean_changed": bool(non_actor_changed),
        "changed_parameter_names": changed_names,
    }


def _save_checkpoint(
    *,
    checkpoint_data: dict[str, Any],
    model: ActorCritic,
    path: Path,
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = dict(checkpoint_data)
    output["model_state"] = {name: tensor.detach().cpu() for name, tensor in model.state_dict().items()}
    output["metadata"] = {**dict(output.get("metadata", {})), **metadata}
    torch.save(output, path)


def _load_source_history_batch(
    *,
    model: ActorCritic,
    history_run_dir: Path,
    intervention_run_dir: Path,
    device: torch.device,
) -> SourceHistoryBatch:
    history_rows = _read_csv(history_run_dir / "history_frame_rows.csv")
    history_intervention_rows = _read_csv(history_run_dir / "history_intervention_rows.csv")
    wrong_history_rows = _read_csv(history_run_dir / "wrong_history_pair_rows.csv")
    observations_by_id = _load_intervention_observations(intervention_run_dir / "intervention_observations.csv")
    actions_by_key = _load_step0_actions(intervention_run_dir / "intervention_action_sequences.csv")
    frames_by_id = _history_frames_by_id(history_rows)

    valid_wrong_pairs: dict[int, dict[str, str]] = {}
    for row in wrong_history_rows:
        if _bool_text(row.get("same_pair_swap")) and _bool_text(row.get("opposite_condition_swap")):
            valid_wrong_pairs[int(float(row["history_intervention_id"]))] = row

    observations: list[np.ndarray] = []
    correct_hidden: list[torch.Tensor] = []
    wrong_hidden: list[torch.Tensor] = []
    preferred_actions: list[np.ndarray] = []
    rejected_actions: list[np.ndarray] = []

    for row in history_intervention_rows:
        history_intervention_id = int(float(row["history_intervention_id"]))
        intervention_id = int(float(row["intervention_id"]))
        correct_history_id = int(float(row["correct_history_id"]))
        wrong_pair = valid_wrong_pairs.get(history_intervention_id)
        if wrong_pair is None:
            raise ValueError(f"invalid wrong-history pair for history_intervention_id={history_intervention_id}")
        if int(float(wrong_pair["correct_history_id"])) != correct_history_id:
            raise ValueError(f"correct-history mismatch for history_intervention_id={history_intervention_id}")
        wrong_history_id = int(float(wrong_pair["wrong_history_id"]))
        _preferred_candidate_id, preferred_action = actions_by_key[(intervention_id, "preferred")]
        _rejected_candidate_id, rejected_action = actions_by_key[(intervention_id, "rejected")]

        observations.append(observations_by_id[intervention_id])
        preferred_actions.append(preferred_action)
        rejected_actions.append(rejected_action)
        correct_hidden.append(_replay_hidden(model, frames_by_id[correct_history_id], device=device, context=None))
        wrong_hidden.append(_replay_hidden(model, frames_by_id[wrong_history_id], device=device, context=None))

    if not observations:
        raise ValueError("source-history objective update requires at least one row")

    return SourceHistoryBatch(
        observations=torch.as_tensor(np.asarray(observations), dtype=torch.float32, device=device),
        correct_hidden=torch.cat(correct_hidden, dim=0).detach().to(device=device, dtype=torch.float32),
        wrong_hidden=torch.cat(wrong_hidden, dim=0).detach().to(device=device, dtype=torch.float32),
        preferred_actions=torch.as_tensor(np.asarray(preferred_actions), dtype=torch.float32, device=device),
        rejected_actions=torch.as_tensor(np.asarray(rejected_actions), dtype=torch.float32, device=device),
    )


def _source_history_loss(
    model: ActorCritic,
    batch: SourceHistoryBatch,
    *,
    correct_margin: float,
    wrong_margin: float,
    wrong_coef: float,
) -> dict[str, torch.Tensor]:
    dist_correct, _value_correct, _next_correct = model.forward_recurrent(batch.observations, batch.correct_hidden)
    dist_wrong, _value_wrong, _next_wrong = model.forward_recurrent(batch.observations, batch.wrong_hidden)
    logp_cp = dist_correct.log_prob(batch.preferred_actions).sum(dim=-1)
    logp_cr = dist_correct.log_prob(batch.rejected_actions).sum(dim=-1)
    logp_wp = dist_wrong.log_prob(batch.preferred_actions).sum(dim=-1)
    logp_wr = dist_wrong.log_prob(batch.rejected_actions).sum(dim=-1)
    correct_loss = torch.nn.functional.softplus(logp_cr - logp_cp + float(correct_margin))
    wrong_loss = torch.nn.functional.softplus(logp_wp - logp_wr + float(wrong_margin))
    combined = correct_loss + float(wrong_coef) * wrong_loss
    return {
        "loss": combined.mean(),
        "correct_loss": correct_loss.mean(),
        "wrong_loss": wrong_loss.mean(),
        "correct_preference_margin": (logp_cp - logp_cr).mean(),
        "wrong_history_preference_margin": (logp_wr - logp_wp).mean(),
    }


def _write_eval_copy(eval_dir: Path, run_dir: Path, suffix: str) -> dict[str, Any]:
    summary = read_json(eval_dir / "summary.json")
    write_json(run_dir / f"objective_{suffix}.json", summary)
    shutil.copyfile(eval_dir / "source_history_objective_rows.csv", run_dir / f"source_history_objective_rows_{suffix}.csv")
    return summary


def run_source_history_objective_update(
    *,
    checkpoint_path: Path,
    history_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    trainable_scope: str = "actor_mean_only",
    steps: int = 100,
    lr: float = 1e-4,
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
) -> dict[str, Any]:
    if str(trainable_scope) != "actor_mean_only":
        raise ValueError("M1288 only supports trainable_scope=actor_mean_only")
    if int(steps) < 1:
        raise ValueError("steps must be positive")
    if float(lr) <= 0.0:
        raise ValueError("lr must be positive")

    checkpoint_path = Path(checkpoint_path)
    history_run_dir = Path(history_run_dir)
    intervention_run_dir = Path(intervention_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    before_eval_dir = run_dir / "before_eval"
    before_summary = run_source_history_objective_evaluator(
        checkpoint_path=checkpoint_path,
        history_run_dir=history_run_dir,
        intervention_run_dir=intervention_run_dir,
        run_dir=before_eval_dir,
        device=device,
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    before_summary = _write_eval_copy(before_eval_dir, run_dir, "before")

    resolved_device = resolve_device(device)
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(model, checkpoint_data)
    if not contract_ok:
        raise ValueError(f"checkpoint contract violation: {contract_reason}")
    model.eval()
    _set_actor_mean_trainable_only(model)
    trainable_count, frozen_count = _parameter_counts(model)
    base_state = _clone_state_dict(model)
    batch = _load_source_history_batch(
        model=model,
        history_run_dir=history_run_dir,
        intervention_run_dir=intervention_run_dir,
        device=resolved_device,
    )

    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    trace_rows: list[dict[str, Any]] = []
    for step in range(int(steps)):
        optimizer.zero_grad()
        losses = _source_history_loss(
            model,
            batch,
            correct_margin=correct_margin,
            wrong_margin=wrong_margin,
            wrong_coef=wrong_coef,
        )
        losses["loss"].backward()
        optimizer.step()
        trace_rows.append(
            {
                "step": int(step + 1),
                "loss": float(losses["loss"].detach().cpu().item()),
                "correct_loss": float(losses["correct_loss"].detach().cpu().item()),
                "wrong_history_loss": float(losses["wrong_loss"].detach().cpu().item()),
                "correct_preference_margin_mean": float(
                    losses["correct_preference_margin"].detach().cpu().item()
                ),
                "wrong_history_preference_margin_mean": float(
                    losses["wrong_history_preference_margin"].detach().cpu().item()
                ),
            }
        )

    updated_state = _clone_state_dict(model)
    parameter_delta = _state_delta(base_state, updated_state)
    write_csv_rows(run_dir / "train_trace.csv", trace_rows)
    write_json(
        run_dir / "parameter_delta.json",
        {
            **parameter_delta,
            "trainable_scope": str(trainable_scope),
            "trainable_parameter_count": int(trainable_count),
            "frozen_parameter_count": int(frozen_count),
        },
    )

    checkpoint_out = run_dir / "checkpoints" / "raw_objective_update.pt"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        model=model,
        path=checkpoint_out,
        metadata={
            "source_history_objective_update": {
                "run_dir": str(run_dir),
                "trainable_scope": str(trainable_scope),
                "steps": int(steps),
                "lr": float(lr),
                "base_checkpoint": str(checkpoint_path),
            }
        },
    )

    after_eval_dir = run_dir / "after_eval"
    after_summary = run_source_history_objective_evaluator(
        checkpoint_path=checkpoint_out,
        history_run_dir=history_run_dir,
        intervention_run_dir=intervention_run_dir,
        run_dir=after_eval_dir,
        device=device,
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    after_summary = _write_eval_copy(after_eval_dir, run_dir, "after")

    base_combined = _finite_float(before_summary["combined_loss_mean"])
    after_combined = _finite_float(after_summary["combined_loss_mean"])
    base_correct = _finite_float(before_summary["correct_preference_loss_mean"])
    after_correct = _finite_float(after_summary["correct_preference_loss_mean"])
    base_wrong = _finite_float(before_summary["wrong_history_preference_loss_mean"])
    after_wrong = _finite_float(after_summary["wrong_history_preference_loss_mean"])
    combined_delta = float(after_combined - base_combined)
    correct_delta = float(after_correct - base_correct)
    wrong_delta = float(after_wrong - base_wrong)
    finite_before = bool(before_summary.get("exact_objective_finite", False))
    finite_after = bool(after_summary.get("exact_objective_finite", False))
    non_actor_mutation = bool(parameter_delta["non_actor_mean_changed"])
    objective_improved = bool(
        finite_before
        and finite_after
        and combined_delta < 0.0
        and correct_delta <= 0.0
        and wrong_delta <= 0.0
        and not non_actor_mutation
    )
    if not finite_before or not finite_after:
        result_class = "source_history_objective_update_nonfinite"
    elif non_actor_mutation:
        result_class = "source_history_objective_update_contract_artifact"
    elif objective_improved:
        result_class = "source_history_objective_update_exact_loss_improved"
    else:
        result_class = "source_history_objective_update_no_exact_loss_improvement"

    summary = {
        "run_type": "source_history_objective_update",
        "checkpoint": str(checkpoint_path),
        "checkpoint_out": str(checkpoint_out),
        "history_run_dir": str(history_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "trainable_scope": str(trainable_scope),
        "steps": int(steps),
        "lr": float(lr),
        "correct_margin": float(correct_margin),
        "wrong_margin": float(wrong_margin),
        "wrong_coef": float(wrong_coef),
        "row_count": int(before_summary.get("row_count", 0)),
        "finite_before": finite_before,
        "finite_after": finite_after,
        "base_combined_loss_mean": base_combined,
        "after_combined_loss_mean": after_combined,
        "combined_loss_delta": combined_delta,
        "base_correct_preference_loss_mean": base_correct,
        "after_correct_preference_loss_mean": after_correct,
        "correct_preference_loss_delta": correct_delta,
        "base_wrong_history_preference_loss_mean": base_wrong,
        "after_wrong_history_preference_loss_mean": after_wrong,
        "wrong_history_preference_loss_delta": wrong_delta,
        "trainable_parameter_count": int(trainable_count),
        "frozen_parameter_count": int(frozen_count),
        "non_actor_mean_mutation_detected": non_actor_mutation,
        "actor_mean_changed": bool(parameter_delta["actor_mean_changed"]),
        "actor_mean_l2": float(parameter_delta["actor_mean_l2"]),
        "actor_mean_max_abs": float(parameter_delta["actor_mean_max_abs"]),
        "non_actor_mean_l2": float(parameter_delta["non_actor_mean_l2"]),
        "non_actor_mean_max_abs": float(parameter_delta["non_actor_mean_max_abs"]),
        "objective_improved": objective_improved,
        "result_class": result_class,
        "labels_enter_actor_input": False,
        "objective_update_started": True,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "summary_before_json": run_dir / "objective_before.json",
        "summary_after_json": run_dir / "objective_after.json",
        "objective_rows_before_csv": run_dir / "source_history_objective_rows_before.csv",
        "objective_rows_after_csv": run_dir / "source_history_objective_rows_after.csv",
        "train_trace_csv": run_dir / "train_trace.csv",
        "parameter_delta_json": run_dir / "parameter_delta.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny no-PPO source-history objective-only update.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--trainable-scope", type=str, default="actor_mean_only")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--correct-margin", type=float, default=DEFAULT_CORRECT_MARGIN)
    parser.add_argument("--wrong-margin", type=float, default=DEFAULT_WRONG_MARGIN)
    parser.add_argument("--wrong-coef", type=float, default=DEFAULT_WRONG_COEF)
    args = parser.parse_args()
    summary = run_source_history_objective_update(
        checkpoint_path=args.checkpoint,
        history_run_dir=args.history_run_dir,
        intervention_run_dir=args.intervention_run_dir,
        run_dir=args.run_dir,
        device=args.device,
        trainable_scope=args.trainable_scope,
        steps=args.steps,
        lr=args.lr,
        correct_margin=args.correct_margin,
        wrong_margin=args.wrong_margin,
        wrong_coef=args.wrong_coef,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
