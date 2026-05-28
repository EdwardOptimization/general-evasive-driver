"""Bounded no-PPO pair-group update for materialized source histories."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import math
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.materialized_source_history_objective_evaluator import (
    DEFAULT_CORRECT_MARGIN,
    DEFAULT_WRONG_COEF,
    DEFAULT_WRONG_MARGIN,
    _action_from_row,
    _history_frames_by_id,
    _int_text,
    _read_csv,
    _replay_hidden,
    _source_pair_by_id,
    _valid_wrong_pair,
    evaluate_materialized_source_history_objective,
)
from autodrift.materialized_source_history_pair_group_metrics import run_pair_group_metrics
from autodrift.source_history_policy_gate import _checkpoint_contract, project_history_frame
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_TRAINABLE_SCOPE = "response_context_fusion_plus_actor_mean"
DEFAULT_TRAIN_FOLDS = "0,1,2,3"
DEFAULT_EVAL_FOLD = 4
DEFAULT_STEPS = 200
DEFAULT_LR = 1e-4
DEFAULT_GROUP_MARGIN = 0.05
DEFAULT_GROUP_MIN_COEF = 1.0
DEFAULT_GROUP_BALANCE_COEF = 0.05
DEFAULT_TRUST_COEF = 1e-3

ALLOWED_PARAMETER_NAMES = {
    "response_context_fusion.0.weight",
    "response_context_fusion.0.bias",
    "actor_mean.weight",
    "actor_mean.bias",
}


@dataclass(frozen=True)
class MaterializedPairGroupBatch:
    observations: torch.Tensor
    correct_hidden: torch.Tensor
    wrong_hidden: torch.Tensor
    preferred_actions: torch.Tensor
    rejected_actions: torch.Tensor
    folds: tuple[int, ...]
    group_keys: tuple[str, ...]
    train_mask: torch.Tensor
    train_group_indices: tuple[torch.Tensor, ...]
    train_two_row_group_indices: tuple[torch.Tensor, ...]


def _clone_state_dict(model: ActorCritic) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def _parse_folds(text: str) -> tuple[int, ...]:
    folds = tuple(int(item.strip()) for item in str(text).split(",") if item.strip())
    if not folds:
        raise ValueError("train_folds must contain at least one fold")
    return folds


def _set_trainable_scope(model: ActorCritic, trainable_scope: str) -> list[torch.nn.Parameter]:
    if str(trainable_scope) != DEFAULT_TRAINABLE_SCOPE:
        raise ValueError(f"M1346 only supports trainable_scope={DEFAULT_TRAINABLE_SCOPE}")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    parameters: list[torch.nn.Parameter] = []
    for name, parameter in model.named_parameters():
        if name in ALLOWED_PARAMETER_NAMES:
            parameter.requires_grad_(True)
            parameters.append(parameter)
    missing = sorted(ALLOWED_PARAMETER_NAMES - {name for name, _parameter in model.named_parameters()})
    if missing:
        raise ValueError("checkpoint is missing allowed trainable parameters: " + ", ".join(missing))
    return parameters


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
    allowed_sq = 0.0
    forbidden_sq = 0.0
    allowed_max = 0.0
    forbidden_max = 0.0
    log_std_sq = 0.0
    changed_names: list[str] = []
    forbidden_changed_names: list[str] = []
    per_parameter_rows: list[dict[str, Any]] = []
    for name, base_tensor in sorted(base.items()):
        updated_tensor = updated[name].detach().cpu()
        delta = updated_tensor - base_tensor
        max_abs = float(torch.max(torch.abs(delta)).item()) if delta.numel() else 0.0
        l2 = float(torch.linalg.vector_norm(delta.float()).item()) if delta.numel() else 0.0
        changed = max_abs > 1e-12
        if changed:
            changed_names.append(name)
        if name == "log_std":
            log_std_sq += float(torch.sum(delta.float().pow(2)).item())
        if name in ALLOWED_PARAMETER_NAMES:
            allowed_sq += float(torch.sum(delta.float().pow(2)).item())
            allowed_max = max(allowed_max, max_abs)
        else:
            forbidden_sq += float(torch.sum(delta.float().pow(2)).item())
            forbidden_max = max(forbidden_max, max_abs)
            if changed:
                forbidden_changed_names.append(name)
        per_parameter_rows.append(
            {
                "parameter": name,
                "allowed_trainable": bool(name in ALLOWED_PARAMETER_NAMES),
                "l2": l2,
                "max_abs": max_abs,
                "changed": bool(changed),
            }
        )
    return {
        "allowed_parameter_l2": math.sqrt(allowed_sq),
        "allowed_parameter_max_abs": allowed_max,
        "forbidden_parameter_l2": math.sqrt(forbidden_sq),
        "forbidden_parameter_max_abs": forbidden_max,
        "log_std_l2": math.sqrt(log_std_sq),
        "allowed_parameters_changed": bool(allowed_max > 1e-12),
        "forbidden_parameter_mutation_detected": bool(forbidden_max > 1e-12),
        "changed_parameter_names": changed_names,
        "forbidden_changed_parameter_names": forbidden_changed_names,
        "per_parameter_rows": per_parameter_rows,
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


def _group_key(row: dict[str, str]) -> str:
    return f"{row.get('source_identity', '')}|{row.get('probe_template', '')}"


def _group_indices(keys: tuple[str, ...], mask: torch.Tensor, *, device: torch.device) -> tuple[torch.Tensor, ...]:
    grouped: dict[str, list[int]] = {}
    mask_np = mask.detach().cpu().numpy().astype(bool)
    for index, key in enumerate(keys):
        if mask_np[index]:
            grouped.setdefault(key, []).append(index)
    return tuple(
        torch.as_tensor(indices, dtype=torch.long, device=device)
        for _key, indices in sorted(grouped.items())
        if indices
    )


def _load_materialized_pair_group_batch(
    *,
    model: ActorCritic,
    corpus_run_dir: Path,
    device: torch.device,
    train_folds: tuple[int, ...],
) -> MaterializedPairGroupBatch:
    source_rows = _read_csv(Path(corpus_run_dir) / "active_source_pair_rows.csv")
    frame_rows = _read_csv(Path(corpus_run_dir) / "active_history_frame_rows.csv")
    intervention_rows = _read_csv(Path(corpus_run_dir) / "active_history_intervention_rows.csv")
    wrong_rows = _read_csv(Path(corpus_run_dir) / "active_wrong_history_pair_rows.csv")

    source_by_pair = _source_pair_by_id(source_rows)
    frames_by_id = _history_frames_by_id(frame_rows)
    wrong_by_intervention = {
        _int_text(row["history_intervention_id"]): row
        for row in wrong_rows
        if _valid_wrong_pair(row)
    }

    observations: list[np.ndarray] = []
    correct_hidden: list[torch.Tensor] = []
    wrong_hidden: list[torch.Tensor] = []
    preferred_actions: list[np.ndarray] = []
    rejected_actions: list[np.ndarray] = []
    folds: list[int] = []
    group_keys: list[str] = []

    for row in intervention_rows:
        history_intervention_id = _int_text(row["history_intervention_id"])
        pair_id = _int_text(row["pair_id"])
        source_pair = source_by_pair.get(pair_id)
        wrong_row = wrong_by_intervention.get(history_intervention_id)
        if source_pair is None:
            raise ValueError(f"missing source pair for pair_id={pair_id}")
        if wrong_row is None:
            raise ValueError(f"missing valid wrong-history pair for history_intervention_id={history_intervention_id}")
        correct_history_id = _int_text(row["correct_history_id"])
        wrong_history_id = _int_text(wrong_row["wrong_history_id"])
        if _int_text(wrong_row["correct_history_id"]) != correct_history_id:
            raise ValueError(f"correct-history mismatch for history_intervention_id={history_intervention_id}")
        if str(row.get("source_identity", "")) != str(wrong_row.get("source_identity", "")):
            raise ValueError(f"source identity mismatch for history_intervention_id={history_intervention_id}")
        correct_frames = frames_by_id.get(correct_history_id, [])
        wrong_frames = frames_by_id.get(wrong_history_id, [])
        if not correct_frames:
            raise ValueError(f"missing correct frames for history_id={correct_history_id}")
        if not wrong_frames:
            raise ValueError(f"missing wrong frames for history_id={wrong_history_id}")

        observations.append(project_history_frame(correct_frames[-1]))
        correct_hidden.append(_replay_hidden(model, correct_frames, device=device))
        wrong_hidden.append(_replay_hidden(model, wrong_frames, device=device))
        preferred_actions.append(_action_from_row(row, "preferred"))
        rejected_actions.append(_action_from_row(row, "rejected"))
        folds.append(_int_text(source_pair.get("fold", 0)))
        group_keys.append(_group_key(row))

    if not observations:
        raise ValueError("materialized pair-group update requires at least one objective row")

    train_fold_set = set(int(fold) for fold in train_folds)
    train_mask_np = np.asarray([fold in train_fold_set for fold in folds], dtype=bool)
    if not bool(np.any(train_mask_np)):
        raise ValueError(f"no rows match train_folds={train_folds}")
    train_mask = torch.as_tensor(train_mask_np, dtype=torch.bool, device=device)
    key_tuple = tuple(group_keys)
    train_groups = _group_indices(key_tuple, train_mask, device=device)
    two_row_groups = tuple(indices for indices in train_groups if int(indices.numel()) == 2)

    return MaterializedPairGroupBatch(
        observations=torch.as_tensor(np.asarray(observations), dtype=torch.float32, device=device),
        correct_hidden=torch.cat(correct_hidden, dim=0).detach().to(device=device, dtype=torch.float32),
        wrong_hidden=torch.cat(wrong_hidden, dim=0).detach().to(device=device, dtype=torch.float32),
        preferred_actions=torch.as_tensor(np.asarray(preferred_actions), dtype=torch.float32, device=device),
        rejected_actions=torch.as_tensor(np.asarray(rejected_actions), dtype=torch.float32, device=device),
        folds=tuple(folds),
        group_keys=key_tuple,
        train_mask=train_mask,
        train_group_indices=train_groups,
        train_two_row_group_indices=two_row_groups,
    )


def _pair_group_losses(
    model: ActorCritic,
    batch: MaterializedPairGroupBatch,
    *,
    correct_margin: float,
    wrong_margin: float,
    wrong_coef: float,
    group_margin: float,
    group_min_coef: float,
    group_balance_coef: float,
    trust_coef: float,
    base_state: dict[str, torch.Tensor],
) -> dict[str, torch.Tensor]:
    dist_correct, _value_correct, _next_correct = model.forward_recurrent(batch.observations, batch.correct_hidden)
    dist_wrong, _value_wrong, _next_wrong = model.forward_recurrent(batch.observations, batch.wrong_hidden)
    logp_cp = dist_correct.log_prob(batch.preferred_actions).sum(dim=-1)
    logp_cr = dist_correct.log_prob(batch.rejected_actions).sum(dim=-1)
    logp_wp = dist_wrong.log_prob(batch.preferred_actions).sum(dim=-1)
    logp_wr = dist_wrong.log_prob(batch.rejected_actions).sum(dim=-1)
    correct_pref_margin = logp_cp - logp_cr
    wrong_pref_margin = logp_wr - logp_wp
    correct_loss = F.softplus(logp_cr - logp_cp + float(correct_margin))
    wrong_loss = F.softplus(logp_wp - logp_wr + float(wrong_margin))
    row_loss = correct_loss + float(wrong_coef) * wrong_loss
    joint_margin = torch.minimum(correct_pref_margin, wrong_pref_margin)
    train_mask = batch.train_mask

    group_min_values = [torch.min(joint_margin[indices]) for indices in batch.train_group_indices]
    if group_min_values:
        group_min_tensor = torch.stack(group_min_values)
        group_min_loss = F.softplus(float(group_margin) - group_min_tensor).mean()
        group_min_mean = group_min_tensor.mean()
    else:
        group_min_loss = row_loss.new_tensor(0.0)
        group_min_mean = row_loss.new_tensor(float("nan"))

    balance_values = [
        torch.abs(joint_margin[indices[0]] - joint_margin[indices[1]])
        for indices in batch.train_two_row_group_indices
    ]
    if balance_values:
        group_balance = torch.stack(balance_values).mean()
    else:
        group_balance = row_loss.new_tensor(0.0)

    trust_terms: list[torch.Tensor] = []
    for name, parameter in model.named_parameters():
        if name in ALLOWED_PARAMETER_NAMES:
            base_tensor = base_state[name].to(device=parameter.device, dtype=parameter.dtype)
            trust_terms.append(torch.square(parameter - base_tensor).mean())
    trust_loss = torch.stack(trust_terms).mean() if trust_terms else row_loss.new_tensor(0.0)
    train_row_loss = row_loss[train_mask].mean()
    loss = (
        train_row_loss
        + float(group_min_coef) * group_min_loss
        + float(group_balance_coef) * group_balance
        + float(trust_coef) * trust_loss
    )
    return {
        "loss": loss,
        "train_row_loss": train_row_loss,
        "train_correct_loss": correct_loss[train_mask].mean(),
        "train_wrong_loss": wrong_loss[train_mask].mean(),
        "train_correct_margin_mean": correct_pref_margin[train_mask].mean(),
        "train_wrong_margin_mean": wrong_pref_margin[train_mask].mean(),
        "train_joint_margin_mean": joint_margin[train_mask].mean(),
        "train_group_min_margin_mean": group_min_mean,
        "group_min_loss": group_min_loss,
        "group_balance_loss": group_balance,
        "trust_loss": trust_loss,
    }


def _copy_objective_outputs(eval_dir: Path, run_dir: Path, suffix: str) -> dict[str, Any]:
    src_summary = eval_dir / "summary.json"
    dst_summary = run_dir / f"objective_{suffix}.json"
    shutil.copyfile(src_summary, dst_summary)
    shutil.copyfile(
        eval_dir / "materialized_source_history_objective_rows.csv",
        run_dir / f"materialized_source_history_objective_rows_{suffix}.csv",
    )
    shutil.copyfile(eval_dir / "family_summary.csv", run_dir / f"family_summary_{suffix}.csv")
    shutil.copyfile(eval_dir / "fold_summary.csv", run_dir / f"fold_summary_{suffix}.csv")
    import json

    with dst_summary.open(encoding="utf-8") as handle:
        return json.load(handle)


def _run_group_metrics(eval_dir: Path, run_dir: Path, suffix: str) -> dict[str, Any]:
    group_dir = run_dir / f"group_metrics_{suffix}"
    summary = run_pair_group_metrics(
        rows_path=eval_dir / "materialized_source_history_objective_rows.csv",
        run_dir=group_dir,
    )
    shutil.copyfile(group_dir / "summary.json", run_dir / f"group_metrics_{suffix}.json")
    shutil.copyfile(group_dir / "group_rows.csv", run_dir / f"group_rows_{suffix}.csv")
    shutil.copyfile(group_dir / "family_group_summary.csv", run_dir / f"family_group_summary_{suffix}.csv")
    shutil.copyfile(group_dir / "fold_group_summary.csv", run_dir / f"fold_group_summary_{suffix}.csv")
    return summary


def _count_csv_rows(path: Path | None) -> int:
    if path is None or not Path(path).exists():
        return 0
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def _fold_group_min_mean(path: Path, eval_fold: int) -> float:
    if not Path(path).exists():
        return float("nan")
    for row in _read_csv(Path(path)):
        if str(row.get("fold", "")) == str(int(eval_fold)):
            return _finite_float(row.get("group_min_joint_margin_mean"))
    return float("nan")


def _finite_summary(summary: dict[str, Any], keys: list[str]) -> bool:
    return all(math.isfinite(_finite_float(summary.get(key))) for key in keys)


def run_materialized_source_history_pair_group_update(
    *,
    checkpoint_path: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    row_metrics_path: Path | None = None,
    device: str = "auto",
    trainable_scope: str = DEFAULT_TRAINABLE_SCOPE,
    train_folds: str = DEFAULT_TRAIN_FOLDS,
    eval_fold: int = DEFAULT_EVAL_FOLD,
    steps: int = DEFAULT_STEPS,
    lr: float = DEFAULT_LR,
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
    group_margin: float = DEFAULT_GROUP_MARGIN,
    group_min_coef: float = DEFAULT_GROUP_MIN_COEF,
    group_balance_coef: float = DEFAULT_GROUP_BALANCE_COEF,
    trust_coef: float = DEFAULT_TRUST_COEF,
) -> dict[str, Any]:
    if int(steps) < 1:
        raise ValueError("steps must be positive")
    if float(lr) <= 0.0:
        raise ValueError("lr must be positive")
    checkpoint_path = Path(checkpoint_path)
    corpus_run_dir = Path(corpus_run_dir)
    run_dir = Path(run_dir)
    row_metrics_path = None if row_metrics_path is None else Path(row_metrics_path)
    train_fold_values = _parse_folds(train_folds)
    run_dir.mkdir(parents=True, exist_ok=True)

    before_eval_dir = run_dir / "before_eval"
    before_summary = evaluate_materialized_source_history_objective(
        checkpoint_path=checkpoint_path,
        corpus_run_dir=corpus_run_dir,
        run_dir=before_eval_dir,
        device=device,
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    before_summary = _copy_objective_outputs(before_eval_dir, run_dir, "before")
    before_group_summary = _run_group_metrics(before_eval_dir, run_dir, "before")

    resolved_device = resolve_device(device)
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(model, checkpoint_data)
    if not contract_ok:
        raise ValueError(f"checkpoint contract violation: {contract_reason}")
    model.eval()
    trainable_parameters = _set_trainable_scope(model, trainable_scope)
    trainable_count, frozen_count = _parameter_counts(model)
    base_state = _clone_state_dict(model)
    batch = _load_materialized_pair_group_batch(
        model=model,
        corpus_run_dir=corpus_run_dir,
        device=resolved_device,
        train_folds=train_fold_values,
    )

    optimizer = torch.optim.Adam(trainable_parameters, lr=float(lr))
    trace_rows: list[dict[str, Any]] = []
    for step in range(int(steps)):
        optimizer.zero_grad()
        losses = _pair_group_losses(
            model,
            batch,
            correct_margin=correct_margin,
            wrong_margin=wrong_margin,
            wrong_coef=wrong_coef,
            group_margin=group_margin,
            group_min_coef=group_min_coef,
            group_balance_coef=group_balance_coef,
            trust_coef=trust_coef,
            base_state=base_state,
        )
        losses["loss"].backward()
        optimizer.step()
        trace_rows.append(
            {
                "step": int(step + 1),
                "loss": float(losses["loss"].detach().cpu().item()),
                "train_row_loss": float(losses["train_row_loss"].detach().cpu().item()),
                "train_correct_loss": float(losses["train_correct_loss"].detach().cpu().item()),
                "train_wrong_loss": float(losses["train_wrong_loss"].detach().cpu().item()),
                "train_correct_margin_mean": float(losses["train_correct_margin_mean"].detach().cpu().item()),
                "train_wrong_margin_mean": float(losses["train_wrong_margin_mean"].detach().cpu().item()),
                "train_joint_margin_mean": float(losses["train_joint_margin_mean"].detach().cpu().item()),
                "train_group_min_margin_mean": float(losses["train_group_min_margin_mean"].detach().cpu().item()),
                "group_min_loss": float(losses["group_min_loss"].detach().cpu().item()),
                "group_balance_loss": float(losses["group_balance_loss"].detach().cpu().item()),
                "trust_loss": float(losses["trust_loss"].detach().cpu().item()),
            }
        )

    updated_state = _clone_state_dict(model)
    parameter_delta = _state_delta(base_state, updated_state)
    write_csv_rows(run_dir / "train_trace.csv", trace_rows)
    write_csv_rows(run_dir / "parameter_delta_rows.csv", parameter_delta["per_parameter_rows"])
    write_json(
        run_dir / "parameter_delta.json",
        {
            key: value
            for key, value in parameter_delta.items()
            if key != "per_parameter_rows"
        }
        | {
            "trainable_scope": str(trainable_scope),
            "trainable_parameter_count": int(trainable_count),
            "frozen_parameter_count": int(frozen_count),
        },
    )

    checkpoint_out = run_dir / "checkpoints" / "raw_pair_group_update.pt"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        model=model,
        path=checkpoint_out,
        metadata={
            "materialized_source_history_pair_group_update": {
                "run_dir": str(run_dir),
                "trainable_scope": str(trainable_scope),
                "steps": int(steps),
                "lr": float(lr),
                "base_checkpoint": str(checkpoint_path),
            }
        },
    )

    after_eval_dir = run_dir / "after_eval"
    after_summary = evaluate_materialized_source_history_objective(
        checkpoint_path=checkpoint_out,
        corpus_run_dir=corpus_run_dir,
        run_dir=after_eval_dir,
        device=device,
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    after_summary = _copy_objective_outputs(after_eval_dir, run_dir, "after")
    after_group_summary = _run_group_metrics(after_eval_dir, run_dir, "after")

    before_group_mean = _finite_float(before_group_summary.get("group_min_joint_margin_mean"))
    after_group_mean = _finite_float(after_group_summary.get("group_min_joint_margin_mean"))
    before_eval_fold_mean = _fold_group_min_mean(run_dir / "fold_group_summary_before.csv", int(eval_fold))
    after_eval_fold_mean = _fold_group_min_mean(run_dir / "fold_group_summary_after.csv", int(eval_fold))
    group_delta = float(after_group_mean - before_group_mean)
    eval_fold_delta = float(after_eval_fold_mean - before_eval_fold_mean)
    conflict_before = int(before_group_summary.get("group_one_sided_conflict_count", 0))
    conflict_after = int(after_group_summary.get("group_one_sided_conflict_count", 0))
    conflict_delta = int(conflict_after - conflict_before)

    exact_finite_before = bool(before_summary.get("exact_objective_finite", False))
    exact_finite_after = bool(after_summary.get("exact_objective_finite", False))
    group_finite_before = _finite_summary(before_group_summary, ["group_min_joint_margin_mean"])
    group_finite_after = _finite_summary(after_group_summary, ["group_min_joint_margin_mean"])
    eval_fold_available = bool(math.isfinite(before_eval_fold_mean) and math.isfinite(after_eval_fold_mean))
    eval_fold_no_regression = bool((not eval_fold_available) or after_eval_fold_mean + 1e-12 >= before_eval_fold_mean)
    forbidden_mutation = bool(parameter_delta["forbidden_parameter_mutation_detected"])
    group_metric_improved = bool(
        exact_finite_before
        and exact_finite_after
        and group_finite_before
        and group_finite_after
        and group_delta > 0.0
        and eval_fold_no_regression
        and not forbidden_mutation
    )
    if forbidden_mutation:
        result_class = "materialized_source_history_pair_group_update_mutation_failure"
    elif not (exact_finite_before and exact_finite_after and group_finite_before and group_finite_after):
        result_class = "materialized_source_history_pair_group_update_nonfinite"
    elif not eval_fold_no_regression:
        result_class = "materialized_source_history_pair_group_update_eval_fold_regression"
    elif group_metric_improved:
        result_class = "materialized_source_history_pair_group_update_group_metric_improved"
    else:
        result_class = "materialized_source_history_pair_group_update_no_group_metric_improvement"

    summary = {
        "run_type": "materialized_source_history_pair_group_update",
        "result_class": result_class,
        "checkpoint": str(checkpoint_path),
        "checkpoint_out": str(checkpoint_out),
        "corpus_run_dir": str(corpus_run_dir),
        "input_row_metrics": None if row_metrics_path is None else str(row_metrics_path),
        "input_row_metrics_row_count": int(_count_csv_rows(row_metrics_path)),
        "device": str(resolved_device),
        "checkpoint_contract": contract_reason,
        "trainable_scope": str(trainable_scope),
        "train_folds": [int(fold) for fold in train_fold_values],
        "eval_fold": int(eval_fold),
        "steps": int(steps),
        "lr": float(lr),
        "correct_margin": float(correct_margin),
        "wrong_margin": float(wrong_margin),
        "wrong_coef": float(wrong_coef),
        "group_margin": float(group_margin),
        "group_min_coef": float(group_min_coef),
        "group_balance_coef": float(group_balance_coef),
        "trust_coef": float(trust_coef),
        "row_count": int(before_summary.get("row_count", 0)),
        "group_count": int(before_group_summary.get("group_count", 0)),
        "train_row_count": int(batch.train_mask.detach().cpu().sum().item()),
        "train_group_count": int(len(batch.train_group_indices)),
        "train_two_row_group_count": int(len(batch.train_two_row_group_indices)),
        "finite_before": bool(exact_finite_before and group_finite_before),
        "finite_after": bool(exact_finite_after and group_finite_after),
        "base_combined_loss_mean": _finite_float(before_summary.get("combined_loss_mean")),
        "after_combined_loss_mean": _finite_float(after_summary.get("combined_loss_mean")),
        "combined_loss_delta": float(
            _finite_float(after_summary.get("combined_loss_mean"))
            - _finite_float(before_summary.get("combined_loss_mean"))
        ),
        "base_group_min_joint_margin_mean": before_group_mean,
        "after_group_min_joint_margin_mean": after_group_mean,
        "full_group_min_joint_margin_delta": group_delta,
        "eval_fold_group_min_joint_margin_mean_before": before_eval_fold_mean,
        "eval_fold_group_min_joint_margin_mean_after": after_eval_fold_mean,
        "eval_fold_group_min_joint_margin_delta": eval_fold_delta,
        "eval_fold_available": bool(eval_fold_available),
        "eval_fold_no_regression": bool(eval_fold_no_regression),
        "group_one_sided_conflict_count_before": int(conflict_before),
        "group_one_sided_conflict_count_after": int(conflict_after),
        "group_one_sided_conflict_delta": int(conflict_delta),
        "group_one_sided_conflict_no_improvement_audited": bool(conflict_delta >= 0),
        "group_metric_improved": bool(group_metric_improved),
        "trainable_parameter_count": int(trainable_count),
        "frozen_parameter_count": int(frozen_count),
        "allowed_parameter_l2": float(parameter_delta["allowed_parameter_l2"]),
        "allowed_parameter_max_abs": float(parameter_delta["allowed_parameter_max_abs"]),
        "forbidden_parameter_l2": float(parameter_delta["forbidden_parameter_l2"]),
        "forbidden_parameter_max_abs": float(parameter_delta["forbidden_parameter_max_abs"]),
        "log_std_l2": float(parameter_delta["log_std_l2"]),
        "allowed_parameters_changed": bool(parameter_delta["allowed_parameters_changed"]),
        "forbidden_parameter_mutation_detected": forbidden_mutation,
        "changed_parameter_names": parameter_delta["changed_parameter_names"],
        "forbidden_changed_parameter_names": parameter_delta["forbidden_changed_parameter_names"],
        "labels_enter_actor_input": False,
        "objective_update_started": True,
        "actor_update_used": True,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "summary_before_json": run_dir / "objective_before.json",
        "summary_after_json": run_dir / "objective_after.json",
        "group_summary_before_json": run_dir / "group_metrics_before.json",
        "group_summary_after_json": run_dir / "group_metrics_after.json",
        "objective_rows_before_csv": run_dir / "materialized_source_history_objective_rows_before.csv",
        "objective_rows_after_csv": run_dir / "materialized_source_history_objective_rows_after.csv",
        "group_rows_before_csv": run_dir / "group_rows_before.csv",
        "group_rows_after_csv": run_dir / "group_rows_after.csv",
        "train_trace_csv": run_dir / "train_trace.csv",
        "parameter_delta_json": run_dir / "parameter_delta.json",
        "parameter_delta_rows_csv": run_dir / "parameter_delta_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus-run-dir", type=Path, required=True)
    parser.add_argument("--row-metrics", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--trainable-scope", type=str, default=DEFAULT_TRAINABLE_SCOPE)
    parser.add_argument("--train-folds", type=str, default=DEFAULT_TRAIN_FOLDS)
    parser.add_argument("--eval-fold", type=int, default=DEFAULT_EVAL_FOLD)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--correct-margin", type=float, default=DEFAULT_CORRECT_MARGIN)
    parser.add_argument("--wrong-margin", type=float, default=DEFAULT_WRONG_MARGIN)
    parser.add_argument("--wrong-coef", type=float, default=DEFAULT_WRONG_COEF)
    parser.add_argument("--group-margin", type=float, default=DEFAULT_GROUP_MARGIN)
    parser.add_argument("--group-min-coef", type=float, default=DEFAULT_GROUP_MIN_COEF)
    parser.add_argument("--group-balance-coef", type=float, default=DEFAULT_GROUP_BALANCE_COEF)
    parser.add_argument("--trust-coef", type=float, default=DEFAULT_TRUST_COEF)
    args = parser.parse_args()
    summary = run_materialized_source_history_pair_group_update(
        checkpoint_path=args.checkpoint,
        corpus_run_dir=args.corpus_run_dir,
        row_metrics_path=args.row_metrics,
        run_dir=args.run_dir,
        device=args.device,
        trainable_scope=args.trainable_scope,
        train_folds=args.train_folds,
        eval_fold=args.eval_fold,
        steps=args.steps,
        lr=args.lr,
        correct_margin=args.correct_margin,
        wrong_margin=args.wrong_margin,
        wrong_coef=args.wrong_coef,
        group_margin=args.group_margin,
        group_min_coef=args.group_min_coef,
        group_balance_coef=args.group_balance_coef,
        trust_coef=args.trust_coef,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
