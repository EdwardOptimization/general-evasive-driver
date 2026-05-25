"""Tiny no-PPO actor-coupling probe for enriched pair-delta objective rows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.actor_coupling_optimize import actor_coupling_trainable_parameters
from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_enriched_pair_delta_objective_sanity import action_vector, pair_requests, row_weight
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _as_int,
    read_csv_rows,
    reconstruct_snapshots,
)


SPLIT_NAMES = (
    "objective_train_public",
    "objective_eval_public",
    "source_holdout_public",
    "new_signature_holdout_public",
)


@dataclass(frozen=True)
class PairDeltaTensorCorpus:
    observations: torch.Tensor
    hiddens: torch.Tensor
    normal_actions: torch.Tensor
    override_actions: torch.Tensor
    weights: torch.Tensor
    is_improvement: torch.Tensor
    split_labels: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]

    def mask(self, split: str) -> torch.Tensor:
        return torch.as_tensor([label == split for label in self.split_labels], dtype=torch.bool, device=self.observations.device)


def pair_delta_preference_components(
    *,
    normal_logp: torch.Tensor,
    override_logp: torch.Tensor,
    is_improvement: torch.Tensor,
    weights: torch.Tensor,
    margin: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return unweighted and weighted pair-delta losses per row."""
    improvement_loss = torch.nn.functional.softplus(normal_logp - override_logp + float(margin))
    degradation_loss = torch.nn.functional.softplus(override_logp - normal_logp + float(margin))
    unweighted = torch.where(is_improvement, improvement_loss, degradation_loss)
    return unweighted, unweighted * weights


def interpolate_state_dict(
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    mixed: dict[str, torch.Tensor] = {}
    for key, base_value in base_state.items():
        raw_value = raw_state[key]
        if torch.is_floating_point(base_value):
            mixed[key] = base_value + float(alpha) * (raw_value - base_value)
        else:
            mixed[key] = base_value.clone()
    return mixed


def classify_enriched_pair_delta_objective_only_probe(
    *,
    tensor_rows_reconstructed: int,
    expected_rows: int,
    missing_tensor_count: int,
    training_nonfinite: bool,
    actor_input_contract_changed: bool,
    residual_head_changed: bool,
    ppo_used: bool,
    promoted: bool,
    exact_losses_finite: bool,
    raw_train_improved: bool,
    exact_admissible_alpha_count: int,
) -> str:
    if bool(ppo_used) or bool(promoted) or bool(actor_input_contract_changed) or bool(residual_head_changed):
        return "v4_enriched_pair_delta_objective_only_probe_contract_violation"
    if int(tensor_rows_reconstructed) != int(expected_rows) or int(missing_tensor_count) > 0:
        return "v4_enriched_pair_delta_objective_only_probe_reconstruction_blocked"
    if bool(training_nonfinite) or not bool(exact_losses_finite):
        return "v4_enriched_pair_delta_objective_only_probe_training_instability"
    if int(exact_admissible_alpha_count) > 0:
        return "v4_enriched_pair_delta_objective_only_probe_exact_admissible"
    if bool(raw_train_improved):
        return "v4_enriched_pair_delta_objective_only_probe_exact_holdout_regression"
    return "v4_enriched_pair_delta_objective_only_probe_no_train_improvement"


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.mean(finite)) if finite else float("nan")


def _max(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.max(finite)) if finite else float("nan")


def _load_split_rows(
    *,
    objective_train_rows_path: Path,
    objective_eval_rows_path: Path,
    source_holdout_rows_path: Path,
    new_signature_holdout_rows_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "objective_train_public": read_csv_rows(objective_train_rows_path),
        "objective_eval_public": read_csv_rows(objective_eval_rows_path),
        "source_holdout_public": read_csv_rows(source_holdout_rows_path),
        "new_signature_holdout_public": read_csv_rows(new_signature_holdout_rows_path),
    }


def _flatten_rows(rows_by_split: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, split_rows in rows_by_split.items():
        for row in split_rows:
            rows.append({**row, "split": str(row.get("split", "")) or split})
    return rows


def _build_tensor_corpus(
    *,
    rows: list[dict[str, Any]],
    snapshots: dict[tuple[int, int], Any],
    device: torch.device,
) -> tuple[PairDeltaTensorCorpus | None, list[dict[str, Any]]]:
    observations: list[np.ndarray] = []
    hiddens: list[np.ndarray] = []
    normal_actions: list[np.ndarray] = []
    override_actions: list[np.ndarray] = []
    weights: list[float] = []
    is_improvement: list[bool] = []
    split_labels: list[str] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for row in rows:
        key = (_as_int(row.get("left_source_group_id")), _as_int(row.get("left_step")))
        snapshot = snapshots.get(key)
        if snapshot is None:
            rejected_rows.append({**row, "rejection_reason": "missing_left_snapshot"})
            continue
        normal_action = action_vector(row, "normal_first")
        override_action = action_vector(row, "first_override")
        if not np.all(np.isfinite(normal_action)) or not np.all(np.isfinite(override_action)):
            rejected_rows.append({**row, "rejection_reason": "nonfinite_action_target"})
            continue
        accepted_class = str(row.get("accepted_class", ""))
        if accepted_class not in {"pair_delta_improvement", "pair_delta_degradation"}:
            rejected_rows.append({**row, "rejection_reason": f"unsupported_accepted_class:{accepted_class}"})
            continue
        observations.append(np.asarray(snapshot.observation, dtype=np.float32))
        hiddens.append(snapshot.hidden.detach().cpu().numpy().astype(np.float32).reshape(-1))
        normal_actions.append(normal_action.astype(np.float32))
        override_actions.append(override_action.astype(np.float32))
        weights.append(float(row_weight(row)))
        is_improvement.append(accepted_class == "pair_delta_improvement")
        split_labels.append(str(row.get("split", "")))
        accepted_rows.append(row)
    if not observations:
        return None, rejected_rows
    corpus = PairDeltaTensorCorpus(
        observations=torch.as_tensor(np.stack(observations), dtype=torch.float32, device=device),
        hiddens=torch.as_tensor(np.stack(hiddens), dtype=torch.float32, device=device),
        normal_actions=torch.as_tensor(np.stack(normal_actions), dtype=torch.float32, device=device),
        override_actions=torch.as_tensor(np.stack(override_actions), dtype=torch.float32, device=device),
        weights=torch.as_tensor(np.asarray(weights), dtype=torch.float32, device=device),
        is_improvement=torch.as_tensor(np.asarray(is_improvement), dtype=torch.bool, device=device),
        split_labels=tuple(split_labels),
        rows=tuple(accepted_rows),
    )
    return corpus, rejected_rows


def _log_prob_pair(model: Any, corpus: PairDeltaTensorCorpus, indices: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor]:
    if indices is None:
        observations = corpus.observations
        hiddens = corpus.hiddens
        normal_actions = corpus.normal_actions
        override_actions = corpus.override_actions
    else:
        observations = corpus.observations.index_select(0, indices)
        hiddens = corpus.hiddens.index_select(0, indices)
        normal_actions = corpus.normal_actions.index_select(0, indices)
        override_actions = corpus.override_actions.index_select(0, indices)
    normal_logp, _entropy, _value = model.evaluate_actions_recurrent(observations, normal_actions, hiddens)
    override_logp, _entropy, _value = model.evaluate_actions_recurrent(observations, override_actions, hiddens)
    return normal_logp, override_logp


def _action_mean(model: Any, observations: torch.Tensor, hiddens: torch.Tensor) -> torch.Tensor:
    dist, _value, _next_hidden = model.forward_recurrent(observations, hiddens)
    return torch.tanh(dist.mean)


def _split_metrics(
    *,
    model: Any,
    corpus: PairDeltaTensorCorpus,
    margin: float,
    candidate_name: str,
    alpha: float | str,
) -> list[dict[str, Any]]:
    model.eval()
    with torch.no_grad():
        normal_logp, override_logp = _log_prob_pair(model, corpus)
        unweighted_loss, weighted_loss = pair_delta_preference_components(
            normal_logp=normal_logp,
            override_logp=override_logp,
            is_improvement=corpus.is_improvement,
            weights=corpus.weights,
            margin=float(margin),
        )
        finite = torch.isfinite(weighted_loss) & torch.isfinite(unweighted_loss)
        rows: list[dict[str, Any]] = []
        for split in SPLIT_NAMES:
            mask = corpus.mask(split)
            count = int(mask.sum().item())
            if count == 0:
                rows.append(
                    {
                        "candidate": candidate_name,
                        "alpha": alpha,
                        "split": split,
                        "rows": 0,
                        "weighted_loss_mean": float("nan"),
                        "unweighted_loss_mean": float("nan"),
                        "normal_logp_mean": float("nan"),
                        "override_logp_mean": float("nan"),
                        "logp_gap_mean": float("nan"),
                        "weight_mean": float("nan"),
                        "finite": False,
                        "improvement_rows": 0,
                        "degradation_rows": 0,
                    }
                )
                continue
            split_weighted = weighted_loss[mask].detach().cpu().numpy().astype(float).tolist()
            split_unweighted = unweighted_loss[mask].detach().cpu().numpy().astype(float).tolist()
            split_normal = normal_logp[mask].detach().cpu().numpy().astype(float).tolist()
            split_override = override_logp[mask].detach().cpu().numpy().astype(float).tolist()
            split_weights = corpus.weights[mask].detach().cpu().numpy().astype(float).tolist()
            split_improvement = corpus.is_improvement[mask]
            rows.append(
                {
                    "candidate": candidate_name,
                    "alpha": alpha,
                    "split": split,
                    "rows": count,
                    "weighted_loss_mean": _mean(split_weighted),
                    "unweighted_loss_mean": _mean(split_unweighted),
                    "normal_logp_mean": _mean(split_normal),
                    "override_logp_mean": _mean(split_override),
                    "logp_gap_mean": _mean([float(o - n) for n, o in zip(split_normal, split_override)]),
                    "weight_mean": _mean(split_weights),
                    "finite": bool(finite[mask].all().item()),
                    "improvement_rows": int(split_improvement.sum().item()),
                    "degradation_rows": int(count - int(split_improvement.sum().item())),
                }
            )
        return rows


def _metrics_by_split(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("split", "")): row for row in rows}


def _candidate_summary(
    *,
    candidate_name: str,
    alpha: float | str,
    split_rows: list[dict[str, Any]],
    base_by_split: dict[str, dict[str, Any]],
    tolerance: float,
    ppo_used: bool,
    promoted: bool,
    actor_input_contract_changed: bool,
    residual_head_changed: bool,
) -> dict[str, Any]:
    by_split = _metrics_by_split(split_rows)
    train_delta = float(by_split["objective_train_public"]["weighted_loss_mean"]) - float(
        base_by_split["objective_train_public"]["weighted_loss_mean"]
    )
    holdout_regressions = [
        float(by_split[split]["weighted_loss_mean"]) - float(base_by_split[split]["weighted_loss_mean"])
        for split in ("objective_eval_public", "source_holdout_public", "new_signature_holdout_public")
    ]
    exact_losses_finite = all(bool(row.get("finite", False)) for row in split_rows)
    max_holdout_regression = _max(holdout_regressions)
    is_nonzero_interpolation = (
        candidate_name == "interpolation"
        and isinstance(alpha, (float, int))
        and float(alpha) > 0.0
    )
    exact_admissible = (
        is_nonzero_interpolation
        and bool(exact_losses_finite)
        and train_delta < 0.0
        and max_holdout_regression <= float(tolerance)
        and not bool(ppo_used)
        and not bool(promoted)
        and not bool(actor_input_contract_changed)
        and not bool(residual_head_changed)
    )
    return {
        "candidate": candidate_name,
        "alpha": alpha,
        "train_weighted_loss_delta": train_delta,
        "train_improved": train_delta < 0.0,
        "objective_eval_regression": holdout_regressions[0],
        "source_holdout_regression": holdout_regressions[1],
        "new_signature_holdout_regression": holdout_regressions[2],
        "max_holdout_regression": max_holdout_regression,
        "exact_losses_finite": exact_losses_finite,
        "exact_holdout_regression_tolerance": float(tolerance),
        "exact_admissible": exact_admissible,
    }


def _action_drift_rows(
    *,
    model: Any,
    corpus: PairDeltaTensorCorpus,
    reference_actions: torch.Tensor,
    candidate_name: str,
    alpha: float | str,
) -> list[dict[str, Any]]:
    model.eval()
    with torch.no_grad():
        actions = _action_mean(model, corpus.observations, corpus.hiddens)
        l2 = torch.linalg.vector_norm(actions - reference_actions, dim=-1)
        mse = torch.square(actions - reference_actions).mean(dim=-1)
        rows: list[dict[str, Any]] = []
        for split in ("all", *SPLIT_NAMES):
            if split == "all":
                mask = torch.ones_like(l2, dtype=torch.bool)
            else:
                mask = corpus.mask(split)
            if int(mask.sum().item()) == 0:
                continue
            split_l2 = l2[mask].detach().cpu().numpy().astype(float).tolist()
            split_mse = mse[mask].detach().cpu().numpy().astype(float).tolist()
            rows.append(
                {
                    "candidate": candidate_name,
                    "alpha": alpha,
                    "split": split,
                    "rows": int(mask.sum().item()),
                    "action_l2_mean": _mean(split_l2),
                    "action_l2_max": _max(split_l2),
                    "action_mse_mean": _mean(split_mse),
                }
            )
        return rows


def _parameter_anchor_loss(trainable_parameters: list[torch.Tensor], reference_parameters: list[torch.Tensor]) -> torch.Tensor:
    losses = [torch.square(parameter - reference).mean() for parameter, reference in zip(trainable_parameters, reference_parameters)]
    if not losses:
        return torch.tensor(0.0)
    return torch.stack(losses).mean()


def _checkpoint_name_for_alpha(alpha: float) -> str:
    return f"alpha_{str(alpha).replace('.', '_')}.pt"


def run_objective_only_probe(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    source_rows_path: Path,
    objective_train_rows_path: Path,
    objective_eval_rows_path: Path,
    source_holdout_rows_path: Path,
    new_signature_holdout_rows_path: Path,
    run_dir: Path,
    device: str,
    margin: float,
    alpha: float,
    max_base_faults: int,
    max_fault_specs: int,
    max_snapshots_per_group: int,
    max_steps: int | None,
    min_step: int | None,
    snapshot_stride: int | None,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    steps: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    grad_clip_norm: float,
    log_interval: int,
    action_anchor_coef: float,
    parameter_anchor_coef: float,
    exact_holdout_regression_tolerance: float,
    interpolation_alphas: tuple[float, ...],
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = run_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    torch.manual_seed(int(seed))
    np.random.seed(int(seed))

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    model, source_checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    reference_model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    reference_model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M886 objective-only probe requires an online recurrent checkpoint")
    for parameter in reference_model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    base_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_head.eval()
    for parameter in residual_head.parameters():
        parameter.requires_grad_(False)
    residual_checksum_before = model_parameter_checksum(residual_head)

    rows_by_split = _load_split_rows(
        objective_train_rows_path=objective_train_rows_path,
        objective_eval_rows_path=objective_eval_rows_path,
        source_holdout_rows_path=source_holdout_rows_path,
        new_signature_holdout_rows_path=new_signature_holdout_rows_path,
    )
    rows = _flatten_rows(rows_by_split)
    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    max_steps_resolved = int(max_steps) if max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step_resolved = int(min_step) if min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride_resolved = int(snapshot_stride) if snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=pair_requests(rows),
        source_rows=read_csv_rows(source_rows_path),
        fault_by_name=fault_by_name,
        model=reference_model,
        residual_head=residual_head,
        env_config=env_config,
        scenario_config=scenario_config,
        alpha=float(alpha),
        min_step=min_step_resolved,
        max_steps=max_steps_resolved,
        snapshot_stride=snapshot_stride_resolved,
        max_snapshots_per_group=int(max_snapshots_per_group),
        warmup_steps=int(warmup_steps),
        steer_amplitude=float(steer_amplitude),
        brake_amplitude=float(brake_amplitude),
        warmup_period_steps=int(warmup_period_steps),
        device=resolved_device,
    )
    corpus, rejected_rows = _build_tensor_corpus(rows=rows, snapshots=snapshots, device=resolved_device)
    expected_rows = sum(len(split_rows) for split_rows in rows_by_split.values())
    if corpus is None:
        summary = {
            "run_type": "v4_enriched_pair_delta_objective_only_probe",
            "result_class": "v4_enriched_pair_delta_objective_only_probe_reconstruction_blocked",
            "expected_rows": expected_rows,
            "tensor_rows_reconstructed": 0,
            "missing_tensor_count": len(rejected_rows),
            "ppo_used": False,
            "promoted": False,
            "elapsed_seconds": float(time.time() - start),
        }
        write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
        write_json(run_dir / "summary.json", summary)
        return summary

    for parameter in model.parameters():
        parameter.requires_grad_(False)
    trainable_parameters = actor_coupling_trainable_parameters(model)
    reference_trainable_parameters = [parameter.detach().clone() for parameter in actor_coupling_trainable_parameters(reference_model)]
    for parameter in trainable_parameters:
        parameter.requires_grad_(True)
    optimizer = torch.optim.Adam(trainable_parameters, lr=float(learning_rate))

    with torch.no_grad():
        reference_actions = _action_mean(reference_model, corpus.observations, corpus.hiddens).detach()
    base_split_rows = _split_metrics(model=reference_model, corpus=corpus, margin=float(margin), candidate_name="base", alpha=0.0)
    base_by_split = _metrics_by_split(base_split_rows)
    train_indices = torch.nonzero(corpus.mask("objective_train_public"), as_tuple=False).squeeze(1)
    if int(train_indices.numel()) == 0:
        raise ValueError("M886 objective-only probe has no objective_train_public rows")

    rng = np.random.default_rng(int(seed) + 103)
    train_metric_rows: list[dict[str, Any]] = []
    training_nonfinite = False
    total_steps = max(1, int(steps))
    interval = max(1, int(log_interval))
    model.train()
    for step in range(1, total_steps + 1):
        if int(batch_size) > 0 and int(batch_size) < int(train_indices.numel()):
            chosen = rng.choice(train_indices.detach().cpu().numpy(), size=int(batch_size), replace=False)
            batch_indices = torch.as_tensor(chosen, dtype=torch.long, device=resolved_device)
        else:
            batch_indices = train_indices
        normal_logp, override_logp = _log_prob_pair(model, corpus, batch_indices)
        _, weighted_loss = pair_delta_preference_components(
            normal_logp=normal_logp,
            override_logp=override_logp,
            is_improvement=corpus.is_improvement.index_select(0, batch_indices),
            weights=corpus.weights.index_select(0, batch_indices),
            margin=float(margin),
        )
        preference_loss = weighted_loss.mean()
        action_anchor_loss = torch.square(_action_mean(model, corpus.observations, corpus.hiddens) - reference_actions).mean()
        parameter_anchor_loss = _parameter_anchor_loss(trainable_parameters, reference_trainable_parameters).to(resolved_device)
        loss = preference_loss + float(action_anchor_coef) * action_anchor_loss + float(parameter_anchor_coef) * parameter_anchor_loss
        if not torch.isfinite(loss):
            training_nonfinite = True
            break
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = nn.utils.clip_grad_norm_(trainable_parameters, float(grad_clip_norm))
        optimizer.step()
        if step == 1 or step == total_steps or step % interval == 0:
            train_metric_rows.append(
                {
                    "step": int(step),
                    "loss": float(loss.detach().cpu().item()),
                    "preference_loss": float(preference_loss.detach().cpu().item()),
                    "action_anchor_loss": float(action_anchor_loss.detach().cpu().item()),
                    "parameter_anchor_loss": float(parameter_anchor_loss.detach().cpu().item()),
                    "grad_norm": float(grad_norm.detach().cpu().item() if isinstance(grad_norm, torch.Tensor) else grad_norm),
                    "batch_size": int(batch_indices.numel()),
                    "learning_rate": float(learning_rate),
                }
            )

    raw_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    raw_checkpoint = checkpoint_dir / "raw_candidate.pt"
    save_checkpoint_like(
        model=model,
        source_checkpoint=source_checkpoint,
        path=raw_checkpoint,
        metadata={
            "run_type": "v4_enriched_pair_delta_objective_only_probe",
            "candidate": "raw_candidate",
            "init_checkpoint": checkpoint_path,
            "steps": total_steps,
            "learning_rate": float(learning_rate),
            "train_scope": "actor_coupling",
            "ppo_used": False,
            "promoted": False,
        },
    )
    actor_checksum_raw = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    actor_input_contract_changed = False
    residual_head_changed = bool(residual_checksum_before != residual_checksum_after)

    exact_rows: list[dict[str, Any]] = list(base_split_rows)
    action_drift_rows: list[dict[str, Any]] = _action_drift_rows(
        model=reference_model,
        corpus=corpus,
        reference_actions=reference_actions,
        candidate_name="base",
        alpha=0.0,
    )
    candidate_rows: list[dict[str, Any]] = []
    raw_split_rows = _split_metrics(model=model, corpus=corpus, margin=float(margin), candidate_name="raw_candidate", alpha="raw")
    exact_rows.extend(raw_split_rows)
    action_drift_rows.extend(
        _action_drift_rows(model=model, corpus=corpus, reference_actions=reference_actions, candidate_name="raw_candidate", alpha="raw")
    )
    candidate_rows.append(
        _candidate_summary(
            candidate_name="raw_candidate",
            alpha="raw",
            split_rows=raw_split_rows,
            base_by_split=base_by_split,
            tolerance=float(exact_holdout_regression_tolerance),
            ppo_used=False,
            promoted=False,
            actor_input_contract_changed=actor_input_contract_changed,
            residual_head_changed=residual_head_changed,
        )
    )

    interpolation_rows: list[dict[str, Any]] = []
    for interpolation_alpha in interpolation_alphas:
        candidate_model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
        candidate_model.load_state_dict(interpolate_state_dict(base_state, raw_state, float(interpolation_alpha)))
        candidate_model.eval()
        split_rows = _split_metrics(
            model=candidate_model,
            corpus=corpus,
            margin=float(margin),
            candidate_name="interpolation",
            alpha=float(interpolation_alpha),
        )
        exact_rows.extend(split_rows)
        summary_row = _candidate_summary(
            candidate_name="interpolation",
            alpha=float(interpolation_alpha),
            split_rows=split_rows,
            base_by_split=base_by_split,
            tolerance=float(exact_holdout_regression_tolerance),
            ppo_used=False,
            promoted=False,
            actor_input_contract_changed=actor_input_contract_changed,
            residual_head_changed=residual_head_changed,
        )
        interpolation_rows.append(summary_row)
        action_drift_rows.extend(
            _action_drift_rows(
                model=candidate_model,
                corpus=corpus,
                reference_actions=reference_actions,
                candidate_name="interpolation",
                alpha=float(interpolation_alpha),
            )
        )
        if float(interpolation_alpha) > 0.0:
            save_checkpoint_like(
                model=candidate_model,
                source_checkpoint=source_checkpoint,
                path=checkpoint_dir / _checkpoint_name_for_alpha(float(interpolation_alpha)),
                metadata={
                    "run_type": "v4_enriched_pair_delta_objective_only_probe",
                    "candidate": "interpolation",
                    "alpha": float(interpolation_alpha),
                    "raw_checkpoint": raw_checkpoint,
                    "init_checkpoint": checkpoint_path,
                    "ppo_used": False,
                    "promoted": False,
                },
            )

    candidate_rows.extend(interpolation_rows)
    all_weighted_losses = [
        _finite_float(row.get("weighted_loss_mean"))
        for row in exact_rows
        if str(row.get("candidate", "")) in {"base", "raw_candidate", "interpolation"}
    ]
    raw_train_delta = float(candidate_rows[0]["train_weighted_loss_delta"]) if candidate_rows else float("nan")
    exact_admissible_rows = [row for row in interpolation_rows if bool(row.get("exact_admissible", False))]
    best_exact = min(exact_admissible_rows, key=lambda row: float(row["train_weighted_loss_delta"])) if exact_admissible_rows else None
    exact_losses_finite = all(np.isfinite(value) for value in all_weighted_losses)
    result_class = classify_enriched_pair_delta_objective_only_probe(
        tensor_rows_reconstructed=len(corpus.rows),
        expected_rows=expected_rows,
        missing_tensor_count=len(rejected_rows),
        training_nonfinite=training_nonfinite,
        actor_input_contract_changed=actor_input_contract_changed,
        residual_head_changed=residual_head_changed,
        ppo_used=False,
        promoted=False,
        exact_losses_finite=exact_losses_finite,
        raw_train_improved=raw_train_delta < 0.0,
        exact_admissible_alpha_count=len(exact_admissible_rows),
    )
    gate_rows = [
        {
            "gate_name": "ppo_blocked",
            "value": True,
            "threshold": "true",
            "passed": True,
            "notes": "M886 does not call PPO rollout or PPO update",
        },
        {
            "gate_name": "residual_head_unchanged",
            "value": not residual_head_changed,
            "threshold": "true",
            "passed": not residual_head_changed,
            "notes": "M761 residual head is loaded frozen for tensor reconstruction only",
        },
        {
            "gate_name": "tensor_rows_reconstructed",
            "value": len(corpus.rows),
            "threshold": expected_rows,
            "passed": len(corpus.rows) == expected_rows,
            "notes": "all enriched rows need actor observation and recurrent hidden tensors",
        },
        {
            "gate_name": "exact_admissible_nonzero_alpha",
            "value": len(exact_admissible_rows),
            "threshold": ">=1",
            "passed": len(exact_admissible_rows) >= 1,
            "notes": "candidate must improve train and preserve exact holdouts",
        },
        {
            "gate_name": "promotion_blocked",
            "value": True,
            "threshold": "true",
            "passed": True,
            "notes": "M886 is not a promotion milestone",
        },
    ]
    summary = {
        "run_type": "v4_enriched_pair_delta_objective_only_probe",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "source_rows": source_rows_path,
        "run_dir": run_dir,
        "raw_checkpoint": raw_checkpoint,
        "expected_rows": expected_rows,
        "tensor_rows_reconstructed": len(corpus.rows),
        "missing_tensor_count": len(rejected_rows),
        "snapshot_rows": len(snapshot_rows),
        "snapshot_rejections": len(snapshot_rejections),
        "steps": total_steps,
        "batch_size": int(batch_size),
        "learning_rate": float(learning_rate),
        "seed": int(seed),
        "train_scope": "actor_coupling",
        "margin": float(margin),
        "action_anchor_coef": float(action_anchor_coef),
        "parameter_anchor_coef": float(parameter_anchor_coef),
        "exact_holdout_regression_tolerance": float(exact_holdout_regression_tolerance),
        "interpolation_alphas": list(interpolation_alphas),
        "raw_train_weighted_loss_delta": raw_train_delta,
        "exact_admissible_alpha_count": len(exact_admissible_rows),
        "best_exact_admissible_alpha": None if best_exact is None else best_exact["alpha"],
        "best_exact_admissible_train_delta": None if best_exact is None else best_exact["train_weighted_loss_delta"],
        "exact_losses_finite": exact_losses_finite,
        "training_nonfinite": training_nonfinite,
        "actor_checksum_before": actor_checksum_before,
        "actor_checksum_raw": actor_checksum_raw,
        "residual_checksum_before": residual_checksum_before,
        "residual_checksum_after": residual_checksum_after,
        "actor_input_contract_changed": actor_input_contract_changed,
        "residual_head_changed": residual_head_changed,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "candidate_metrics_csv": run_dir / "candidate_metrics.csv",
        "interpolation_metrics_csv": run_dir / "interpolation_metrics.csv",
        "exact_objective_by_split_csv": run_dir / "exact_objective_by_split.csv",
        "action_drift_metrics_csv": run_dir / "action_drift_metrics.csv",
        "train_metrics_csv": run_dir / "train_metrics.csv",
        "reconstructed_snapshot_rows_csv": run_dir / "reconstructed_snapshot_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "elapsed_seconds": float(time.time() - start),
    }
    write_csv_rows(run_dir / "train_metrics.csv", train_metric_rows)
    write_csv_rows(run_dir / "candidate_metrics.csv", candidate_rows)
    write_csv_rows(run_dir / "interpolation_metrics.csv", interpolation_rows)
    write_csv_rows(run_dir / "exact_objective_by_split.csv", exact_rows)
    write_csv_rows(run_dir / "action_drift_metrics.csv", action_drift_rows)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "gate_summary.csv", gate_rows, fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_alphas(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tiny no-PPO enriched pair-delta objective-only probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--objective-train-rows", type=Path, required=True)
    parser.add_argument("--objective-eval-rows", type=Path, required=True)
    parser.add_argument("--source-holdout-rows", type=Path, required=True)
    parser.add_argument("--new-signature-holdout-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--margin", type=float, default=0.05)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-base-faults", type=int, default=10)
    parser.add_argument("--max-fault-specs", type=int, default=18)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=24)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--steps", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=10886)
    parser.add_argument("--grad-clip-norm", type=float, default=0.5)
    parser.add_argument("--log-interval", type=int, default=8)
    parser.add_argument("--action-anchor-coef", type=float, default=0.1)
    parser.add_argument("--parameter-anchor-coef", type=float, default=1e-4)
    parser.add_argument("--exact-holdout-regression-tolerance", type=float, default=1e-4)
    parser.add_argument("--interpolation-alphas", type=str, default="0.0,0.001,0.0025,0.005,0.01,0.02,0.05,0.10")
    args = parser.parse_args()
    summary = run_objective_only_probe(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        source_rows_path=args.source_rows,
        objective_train_rows_path=args.objective_train_rows,
        objective_eval_rows_path=args.objective_eval_rows,
        source_holdout_rows_path=args.source_holdout_rows,
        new_signature_holdout_rows_path=args.new_signature_holdout_rows,
        run_dir=args.run_dir,
        device=args.device,
        margin=float(args.margin),
        alpha=float(args.alpha),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=args.max_steps,
        min_step=args.min_step,
        snapshot_stride=args.snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        steps=int(args.steps),
        batch_size=int(args.batch_size),
        learning_rate=float(args.learning_rate),
        seed=int(args.seed),
        grad_clip_norm=float(args.grad_clip_norm),
        log_interval=int(args.log_interval),
        action_anchor_coef=float(args.action_anchor_coef),
        parameter_anchor_coef=float(args.parameter_anchor_coef),
        exact_holdout_regression_tolerance=float(args.exact_holdout_regression_tolerance),
        interpolation_alphas=_parse_alphas(args.interpolation_alphas),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
