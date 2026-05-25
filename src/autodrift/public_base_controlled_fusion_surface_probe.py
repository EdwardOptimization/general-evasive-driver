"""Controlled fusion-plus-head objective probe for the M399 public base."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.public_base_policy_head_trust_region_probe import (
    DEFAULT_ALPHAS,
    TARGET_MSE_TOLERANCE,
    _clone_state_dict,
    _save_checkpoint,
    _state_checksum,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.public_base_tail_weighted_residual_probe import (
    DEFICIT_LIFT_TARGET,
    LOW_TAIL_DEFICIT_THRESHOLD,
    LOW_TAIL_FRACTION_LIFT_TARGET,
    LOW_TAIL_GAP_THRESHOLD,
    P10_LIFT_TARGET,
    _mean,
    _percentile,
)
from autodrift.public_base_alpha_aware_low_tail_residual_probe import (
    LOW_TAIL_DEFICIT_TARGET,
    LOW_TAIL_GAP_MARGIN,
)
from autodrift.temporal_action_boundary_outcome_miner import _collect_seed_snapshots, _find_snapshot
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import (
    _contrast_lookup,
    _intervention_obs_hidden,
    _metadata_missing,
    _parse_float_list,
    _read_csv_rows,
    _target_gap,
)


ALLOWED_PREFIXES = ("actor_mean.", "response_context_fusion.0.")
DEFAULT_EXTENDED_ALPHAS = (*DEFAULT_ALPHAS, 0.200, 0.350, 0.500, 0.750, 1.000)


def controlled_surface_checksums(state_dict: dict[str, torch.Tensor]) -> dict[str, str]:
    return {
        "full": _state_checksum(state_dict),
        "actor_mean": _state_checksum(state_dict, include_prefixes=("actor_mean.",)),
        "fusion": _state_checksum(state_dict, include_prefixes=("response_context_fusion.0.",)),
        "response_encoder": _state_checksum(state_dict, include_prefixes=("response_encoder.",)),
        "context_encoder": _state_checksum(state_dict, include_prefixes=("context_encoder.",)),
        "online_gru": _state_checksum(state_dict, include_prefixes=("online_gru_cell.",)),
        "critic": _state_checksum(state_dict, include_prefixes=("critic.",)),
        "log_std": _state_checksum(state_dict, include_names=("log_std",)),
        "forbidden": _state_checksum(state_dict, exclude_prefixes=ALLOWED_PREFIXES),
    }


def set_controlled_fusion_trainable_only(model: ActorCritic) -> None:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for name, parameter in model.named_parameters():
        if name.startswith(ALLOWED_PREFIXES):
            parameter.requires_grad_(True)


def interpolate_controlled_surface_state(
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    alpha_value = float(alpha)
    interpolated: dict[str, torch.Tensor] = {}
    for name, base_tensor in base_state.items():
        if name.startswith(ALLOWED_PREFIXES):
            interpolated[name] = base_tensor + alpha_value * (raw_state[name] - base_tensor)
        else:
            interpolated[name] = base_tensor.clone()
    return interpolated


def _features_and_actions(
    model: ActorCritic,
    observations: torch.Tensor,
    hidden: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    features, _ = model.recurrent_features_tensor(observations, hidden)
    return features, torch.tanh(model.actor_mean(features))


def _base_actions(
    model: ActorCritic,
    observations: torch.Tensor,
    hidden: torch.Tensor,
    *,
    batch_size: int = 1024,
) -> torch.Tensor:
    actions: list[torch.Tensor] = []
    with torch.no_grad():
        for start in range(0, observations.shape[0], int(batch_size)):
            end = min(start + int(batch_size), observations.shape[0])
            _features, action = _features_and_actions(model, observations[start:end], hidden[start:end])
            actions.append(action.detach().cpu())
    return torch.cat(actions, dim=0) if actions else torch.empty((0, 3), dtype=torch.float32)


def _load_trainable_samples(
    *,
    model: ActorCritic,
    positive_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    scenario_config: dict[str, Any],
    env_config: Any,
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], list[dict[str, Any]], list[dict[str, Any]]]:
    normal_by_group, _hard_by_group = _contrast_lookup(contrast_rows)
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    response_dim = response_feature_dim_for_model(model)
    snapshots_by_seed: dict[int, list[Any]] = {}
    meta_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    normal_obs: list[np.ndarray] = []
    intervention_obs: list[np.ndarray] = []
    normal_hidden: list[torch.Tensor] = []
    intervention_hidden: list[torch.Tensor] = []
    target_gaps: list[float] = []
    for seed in sorted({int(row.get("seed", -1)) for row in positive_rows if str(row.get("seed", "")).strip()}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(seed),
            config=scenario_config,
            device=device,
        )
    for row in positive_rows:
        group_id = str(row.get("contrast_group_id", ""))
        if normal_by_group.get(group_id) is None:
            rejected_rows.append({**row, "rejection_reason": "missing_normal_row"})
            continue
        if _metadata_missing(row):
            rejected_rows.append({**row, "rejection_reason": "metadata_missing"})
            continue
        seed = int(row.get("seed", -1))
        fault_name = str(row.get("preferred_fault", ""))
        step = int(row.get("step", -1))
        horizon = int(row.get("horizon", 0))
        variant = str(row.get("variant", ""))
        snapshot = _find_snapshot(snapshots_by_seed.get(seed, []), fault_name=fault_name, step=step)
        if snapshot is None:
            rejected_rows.append({**row, "rejection_reason": "missing_source_snapshot"})
            continue
        branch_obs, branch_hidden = _intervention_obs_hidden(
            model,
            observation=snapshot.observation,
            hidden=snapshot.hidden,
            variant=variant,
            horizon=horizon,
            response_dim=response_dim,
            device=device,
        )
        normal_obs.append(np.asarray(snapshot.observation, dtype=np.float32))
        intervention_obs.append(np.asarray(branch_obs, dtype=np.float32))
        normal_hidden.append(snapshot.hidden.detach().cpu().reshape(-1))
        intervention_hidden.append(branch_hidden.detach().cpu().reshape(-1))
        target_gaps.append(_target_gap(row))
        meta_rows.append(
            {
                "contrast_group_id": group_id,
                "source_index": row.get("source_index", ""),
                "seed": seed,
                "step": step,
                "preferred_fault": fault_name,
                "preferred_fault_family": row.get("preferred_fault_family", ""),
                "wrong_fault_family": row.get("wrong_fault_family", ""),
                "fault_family_pair": row.get("fault_family_pair", ""),
                "variant": variant,
                "horizon": horizon,
                "source_pool": row.get("source_pool", ""),
                "claim_boundary_level": row.get("claim_boundary_level", ""),
            }
        )
    if not meta_rows:
        empty_obs = torch.empty((0, model.obs_dim), dtype=torch.float32)
        empty_hidden = torch.empty((0, model.actor_mean.in_features), dtype=torch.float32)
        return {
            "normal_obs": empty_obs,
            "intervention_obs": empty_obs,
            "normal_hidden": empty_hidden,
            "intervention_hidden": empty_hidden,
            "normal_actions": torch.empty((0, 3), dtype=torch.float32),
            "intervention_actions": torch.empty((0, 3), dtype=torch.float32),
            "target_gaps": torch.empty((0,), dtype=torch.float32),
        }, meta_rows, rejected_rows
    normal_obs_t = torch.as_tensor(np.asarray(normal_obs), dtype=torch.float32, device=device)
    intervention_obs_t = torch.as_tensor(np.asarray(intervention_obs), dtype=torch.float32, device=device)
    normal_hidden_t = torch.stack(normal_hidden).to(device=device, dtype=torch.float32)
    intervention_hidden_t = torch.stack(intervention_hidden).to(device=device, dtype=torch.float32)
    return {
        "normal_obs": normal_obs_t,
        "intervention_obs": intervention_obs_t,
        "normal_hidden": normal_hidden_t,
        "intervention_hidden": intervention_hidden_t,
        "normal_actions": _base_actions(model, normal_obs_t, normal_hidden_t).to(device=device),
        "intervention_actions": _base_actions(model, intervention_obs_t, intervention_hidden_t).to(device=device),
        "target_gaps": torch.as_tensor(target_gaps, dtype=torch.float32, device=device),
    }, meta_rows, rejected_rows


def _allowed_parameter_anchor_loss(
    model: ActorCritic,
    base_state: dict[str, torch.Tensor],
    device: torch.device,
) -> torch.Tensor:
    loss = torch.zeros((), dtype=torch.float32, device=device)
    count = 0
    for name, parameter in model.named_parameters():
        if name.startswith(ALLOWED_PREFIXES):
            loss = loss + torch.mean((parameter - base_state[name].to(device=device, dtype=torch.float32)).pow(2))
            count += 1
    return loss / max(count, 1)


def train_controlled_fusion_surface(
    model: ActorCritic,
    samples: dict[str, torch.Tensor],
    *,
    target_mask: torch.Tensor,
    low_tail_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_weights: torch.Tensor,
    base_state: dict[str, torch.Tensor],
    epochs: int,
    seed: int,
    lr: float,
    target_action_coef: float = 0.10,
    low_tail_gap_floor_coef: float = 10.0,
    low_tail_deficit_coef: float = 6.0,
    normal_retention_coef: float = 12.0,
    intervention_anchor_coef: float = 0.50,
    parameter_anchor_coef: float = 0.001,
) -> list[dict[str, Any]]:
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device
    optimizer = torch.optim.Adam([parameter for parameter in model.parameters() if parameter.requires_grad], lr=float(lr))
    history: list[dict[str, Any]] = []
    base_normal_actions = samples["normal_actions"]
    base_intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        _normal_features, normal_actions = _features_and_actions(
            model,
            samples["normal_obs"],
            samples["normal_hidden"],
        )
        _intervention_features, intervention_actions = _features_and_actions(
            model,
            samples["intervention_obs"],
            samples["intervention_hidden"],
        )
        if bool(target_mask.any()):
            target_error = torch.mean((normal_actions[target_mask] - target_actions[target_mask]).pow(2), dim=-1)
            target_loss = (target_weights[target_mask] * target_error).sum() / torch.clamp(
                target_weights[target_mask].sum(), min=1.0
            )
        else:
            target_loss = torch.zeros((), dtype=torch.float32, device=device)
        gap = torch.linalg.norm(intervention_actions - normal_actions, dim=-1)
        if bool(low_tail_mask.any()):
            low_gap = gap[low_tail_mask]
            low_deficit = torch.relu(target_gaps[low_tail_mask] - low_gap)
            low_tail_gap_floor_loss = torch.relu(
                float(LOW_TAIL_GAP_THRESHOLD + LOW_TAIL_GAP_MARGIN) - low_gap
            ).pow(2).mean()
            low_tail_deficit_loss = torch.relu(low_deficit - float(LOW_TAIL_DEFICIT_TARGET)).pow(2).mean()
        else:
            low_tail_gap_floor_loss = torch.zeros((), dtype=torch.float32, device=device)
            low_tail_deficit_loss = torch.zeros((), dtype=torch.float32, device=device)
        normal_retention_loss = torch.mean((normal_actions - base_normal_actions).pow(2))
        intervention_anchor_loss = torch.mean((intervention_actions - base_intervention_actions).pow(2))
        parameter_anchor_loss = _allowed_parameter_anchor_loss(model, base_state, device)
        loss = (
            float(target_action_coef) * target_loss
            + float(low_tail_gap_floor_coef) * low_tail_gap_floor_loss
            + float(low_tail_deficit_coef) * low_tail_deficit_loss
            + float(normal_retention_coef) * normal_retention_loss
            + float(intervention_anchor_coef) * intervention_anchor_loss
            + float(parameter_anchor_coef) * parameter_anchor_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "target_loss": float(target_loss.detach().item()),
                "low_tail_gap_floor_loss": float(low_tail_gap_floor_loss.detach().item()),
                "low_tail_deficit_loss": float(low_tail_deficit_loss.detach().item()),
                "normal_retention_loss": float(normal_retention_loss.detach().item()),
                "intervention_anchor_loss": float(intervention_anchor_loss.detach().item()),
                "parameter_anchor_loss": float(parameter_anchor_loss.detach().item()),
                "gap_mean": float(gap.detach().mean().item()),
            }
        )
    return history


def evaluate_controlled_fusion_alphas(
    model: ActorCritic,
    *,
    samples: dict[str, torch.Tensor],
    meta_rows: list[dict[str, Any]],
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alphas: tuple[float, ...],
    target_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_rows: list[dict[str, str]],
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    near_base_low_tail_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from autodrift.public_base_target_regeneration import _key

    device = next(model.parameters()).device
    target_by_key = {_key(row): row for row in target_rows}
    target_source_labels = [str(target_by_key.get(_key(meta), {}).get("source_label", "")) for meta in meta_rows]
    strict_mask_np = np.asarray([label == "strict_low_tail" for label in target_source_labels], dtype=bool)
    near_mask_np = np.asarray([label == "near_tail_coverage" for label in target_source_labels], dtype=bool)
    target_mask_np = target_mask.detach().cpu().numpy().astype(bool)
    base_normal_actions = samples["normal_actions"]
    base_intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    baseline_target_mse = torch.mean((base_normal_actions[target_mask] - target_actions[target_mask]).pow(2), dim=-1)
    baseline_target_mse_mean = float(baseline_target_mse.mean().detach().item()) if bool(target_mask.any()) else 0.0
    alpha_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    original_state = _clone_state_dict(model)
    try:
        for alpha in alphas:
            alpha_value = float(alpha)
            model.load_state_dict(interpolate_controlled_surface_state(base_state, raw_state, alpha_value))
            with torch.no_grad():
                _normal_features, adjusted_normal = _features_and_actions(
                    model,
                    samples["normal_obs"],
                    samples["normal_hidden"],
                )
                _intervention_features, adjusted_intervention = _features_and_actions(
                    model,
                    samples["intervention_obs"],
                    samples["intervention_hidden"],
                )
            normal_drift = torch.linalg.norm(adjusted_normal - base_normal_actions, dim=-1).detach().cpu().numpy()
            normal_anchor_mse = torch.mean((adjusted_normal - base_normal_actions).pow(2), dim=-1).detach().cpu().numpy()
            gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1).detach().cpu().numpy()
            target = target_gaps.detach().cpu().numpy()
            gap_deficit = np.maximum(0.0, target - gap)
            low_tail_after = (gap < float(LOW_TAIL_GAP_THRESHOLD)) | (gap_deficit > float(LOW_TAIL_DEFICIT_THRESHOLD))
            target_mse_all = torch.mean((adjusted_normal - target_actions).pow(2), dim=-1).detach().cpu().numpy()
            target_mse = target_mse_all[target_mask_np]
            strict_target_mse = target_mse_all[target_mask_np & strict_mask_np]
            near_target_mse = target_mse_all[target_mask_np & near_mask_np]
            row = {
                "alpha": alpha_value,
                "sample_count": int(gap.shape[0]),
                "target_rows": int(np.sum(target_mask_np)),
                "normal_anchor_mse_mean": _mean(normal_anchor_mse),
                "normal_anchor_mse_p95": _percentile(normal_anchor_mse, 95),
                "first_action_drift_from_base_mean": _mean(normal_drift),
                "first_action_drift_from_base_p95": _percentile(normal_drift, 95),
                "normal_intervention_gap_mean": _mean(gap),
                "normal_intervention_gap_p10": _percentile(gap, 10),
                "gap_deficit_mean": _mean(gap_deficit),
                "gap_deficit_p95": _percentile(gap_deficit, 95),
                "low_tail_rows": int(np.sum(low_tail_after)),
                "low_tail_fraction": float(np.mean(low_tail_after.astype(np.float32))) if low_tail_after.size else 0.0,
                "target_action_mse_mean": _mean(target_mse),
                "strict_target_action_mse_mean": _mean(strict_target_mse),
                "near_tail_target_action_mse_mean": _mean(near_target_mse),
                "baseline_target_action_mse_mean": baseline_target_mse_mean,
            }
            row["normal_retention_pass"] = bool(
                row["normal_anchor_mse_mean"] <= 0.000004
                and row["normal_anchor_mse_p95"] <= 0.000025
                and row["first_action_drift_from_base_mean"] <= 0.003
                and row["first_action_drift_from_base_p95"] <= 0.008
            )
            row["tail_lift_pass"] = bool(
                row["normal_intervention_gap_p10"] >= float(near_base_gap_p10) + P10_LIFT_TARGET
                and row["gap_deficit_mean"] <= float(near_base_gap_deficit_mean) - DEFICIT_LIFT_TARGET
                and row["low_tail_fraction"] <= float(near_base_low_tail_fraction) - LOW_TAIL_FRACTION_LIFT_TARGET
            )
            row["target_loss_pass"] = bool(
                row["target_action_mse_mean"] < baseline_target_mse_mean
                and row["strict_target_action_mse_mean"] < baseline_target_mse_mean
            )
            row["target_tolerance_pass"] = bool(
                row["target_action_mse_mean"] <= baseline_target_mse_mean + TARGET_MSE_TOLERANCE
                and row["strict_target_action_mse_mean"] <= baseline_target_mse_mean + TARGET_MSE_TOLERANCE
            )
            row["exact_probe_candidate"] = bool(
                row["normal_retention_pass"] and row["tail_lift_pass"] and row["target_loss_pass"]
            )
            row["strict_candidate"] = bool(row["exact_probe_candidate"])
            row["low_tail_effect_candidate"] = bool(row["normal_retention_pass"] and row["tail_lift_pass"])
            row["target_tolerance_candidate"] = bool(
                row["normal_retention_pass"] and row["tail_lift_pass"] and row["target_tolerance_pass"]
            )
            row["normal_safe_low_tail_trend"] = bool(
                row["normal_retention_pass"]
                and row["low_tail_fraction"] < float(near_base_low_tail_fraction)
                and row["gap_deficit_mean"] < float(near_base_gap_deficit_mean)
            )
            alpha_rows.append(row)
            for index, meta in enumerate(meta_rows):
                objective_rows.append(
                    {
                        **meta,
                        "alpha": alpha_value,
                        "normal_anchor_mse": float(normal_anchor_mse[index]),
                        "first_action_drift_from_base": float(normal_drift[index]),
                        "normal_intervention_gap": float(gap[index]),
                        "target_gap": float(target[index]),
                        "gap_deficit": float(gap_deficit[index]),
                        "low_tail_after": bool(low_tail_after[index]),
                        "target_available": bool(target_mask_np[index]),
                        "source_label": target_source_labels[index],
                        "target_action_mse": float(target_mse_all[index]) if target_mask_np[index] else "",
                    }
                )
    finally:
        model.load_state_dict({name: tensor.to(device=device) for name, tensor in original_state.items()})
    return alpha_rows, objective_rows


def classify_controlled_fusion_surface_probe(
    *,
    forbidden_parameter_changed: bool,
    actor_mean_changed: bool,
    fusion_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_keys: int,
    candidate_count: int,
    any_tail_lift: bool,
    any_normal_retained_tail_lift: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(forbidden_parameter_changed) or bool(ppo_used) or bool(promoted):
        return "public_base_controlled_fusion_surface_probe_contract_artifact"
    if int(missing_target_keys) > 0:
        return "public_base_controlled_fusion_surface_probe_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_controlled_fusion_surface_probe_reconstruction_blocked"
    if not bool(actor_mean_changed) or not bool(fusion_changed):
        return "public_base_controlled_fusion_surface_probe_no_surface_update"
    if int(candidate_count) > 0:
        return "public_base_controlled_fusion_surface_probe_candidate"
    if bool(any_normal_retained_tail_lift):
        return "public_base_controlled_fusion_surface_probe_target_conflict"
    if bool(any_tail_lift):
        return "public_base_controlled_fusion_surface_probe_trust_region_conflict"
    return "public_base_controlled_fusion_surface_probe_no_tail_lift"


def run_controlled_fusion_surface_probe(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    alphas: tuple[float, ...] = DEFAULT_EXTENDED_ALPHAS,
    lr: float = 5e-4,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    set_controlled_fusion_trainable_only(model)
    base_state = _clone_state_dict(model)
    base_checksums = controlled_surface_checksums(base_state)
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    m912_summary = read_json(m912_summary_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples, meta_rows, rejected_rows = _load_trainable_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    if len(meta_rows) == 0:
        target_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        target_actions = torch.empty((0, 3), dtype=torch.float32, device=resolved_device)
        weight_rows: list[dict[str, Any]] = []
        missing_target_keys: set[tuple[str, str, str, str]] = set()
        train_rows: list[dict[str, Any]] = []
        alpha_rows: list[dict[str, Any]] = []
        objective_rows: list[dict[str, Any]] = []
        raw_state = base_state
    else:
        target_mask, low_tail_mask, target_actions, target_weights, weight_rows, missing_target_keys = target_weight_vector(
            meta_rows=meta_rows,
            target_rows=target_rows,
            low_tail_rows=low_tail_rows,
            normal_actions=samples["normal_actions"],
        )
        if missing_target_keys:
            train_rows = []
            alpha_rows = []
            objective_rows = []
            raw_state = base_state
        else:
            train_rows = train_controlled_fusion_surface(
                model,
                samples,
                target_mask=target_mask,
                low_tail_mask=low_tail_mask,
                target_actions=target_actions,
                target_weights=target_weights,
                base_state=base_state,
                epochs=epochs,
                seed=seed,
                lr=lr,
            )
            raw_state = _clone_state_dict(model)
            alpha_rows, objective_rows = evaluate_controlled_fusion_alphas(
                model,
                samples=samples,
                meta_rows=meta_rows,
                base_state=base_state,
                raw_state=raw_state,
                alphas=alphas,
                target_mask=target_mask,
                target_actions=target_actions,
                target_rows=target_rows,
                near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
            )
    raw_checksums = controlled_surface_checksums(raw_state)
    candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    tail_rows = [row for row in alpha_rows if bool(row.get("tail_lift_pass", False))]
    normal_tail_rows = [
        row for row in alpha_rows if bool(row.get("tail_lift_pass", False)) and bool(row.get("normal_retention_pass", False))
    ]
    low_tail_effect_rows = [row for row in alpha_rows if bool(row.get("low_tail_effect_candidate", False))]
    target_tolerance_rows = [row for row in alpha_rows if bool(row.get("target_tolerance_candidate", False))]
    normal_safe_trend_rows = [row for row in alpha_rows if bool(row.get("normal_safe_low_tail_trend", False))]
    forbidden_changed = bool(base_checksums["forbidden"] != raw_checksums["forbidden"])
    result_class = classify_controlled_fusion_surface_probe(
        forbidden_parameter_changed=forbidden_changed,
        actor_mean_changed=bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"]),
        fusion_changed=bool(base_checksums["fusion"] != raw_checksums["fusion"]),
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        candidate_count=len(candidate_rows),
        any_tail_lift=bool(tail_rows),
        any_normal_retained_tail_lift=bool(normal_tail_rows),
        ppo_used=False,
        promoted=False,
    )
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_normal_retaining = min(
        [row for row in alpha_rows if bool(row.get("normal_retention_pass", False))],
        key=lambda row: (float(row.get("low_tail_fraction", 1.0)), float(row.get("gap_deficit_mean", 1.0))),
        default={},
    )
    best_tail_lift_nonretaining = min(
        [row for row in tail_rows if not bool(row.get("normal_retention_pass", False))],
        key=lambda row: (float(row.get("low_tail_fraction", 1.0)), float(row.get("gap_deficit_mean", 1.0))),
        default={},
    )
    checkpoint_dir = run_dir / "checkpoints"
    if len(meta_rows) > 0 and not missing_target_keys:
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=raw_state,
            destination=checkpoint_dir / "raw_controlled_fusion_update.pt",
            objective="public_base_controlled_fusion_surface_probe_raw",
        )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "target_weight_rows.csv", weight_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [*rejected_rows, *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys))],
    )
    summary = {
        "run_type": "public_base_controlled_fusion_surface_probe",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "target_rows_count": int(len(target_rows)),
        "joined_target_rows": int(sum(1 for row in weight_rows if bool(row.get("target_available", False)))),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(len(low_tail_rows)),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "alphas": [float(alpha) for alpha in alphas],
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "strict_candidate_count": int(len(candidate_rows)),
        "low_tail_effect_candidate_count": int(len(low_tail_effect_rows)),
        "target_tolerance_candidate_count": int(len(target_tolerance_rows)),
        "normal_safe_low_tail_trend_count": int(len(normal_safe_trend_rows)),
        "low_tail_effect_candidate_alphas": [float(row.get("alpha")) for row in low_tail_effect_rows],
        "target_tolerance_candidate_alphas": [float(row.get("alpha")) for row in target_tolerance_rows],
        "normal_safe_low_tail_trend_alphas": [float(row.get("alpha")) for row in normal_safe_trend_rows],
        "best_candidate": best_candidate,
        "best_normal_retaining_row": best_normal_retaining,
        "best_tail_lift_nonretaining_row": best_tail_lift_nonretaining,
        "actor_mean_changed": bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"]),
        "fusion_changed": bool(base_checksums["fusion"] != raw_checksums["fusion"]),
        "response_encoder_changed": bool(base_checksums["response_encoder"] != raw_checksums["response_encoder"]),
        "context_encoder_changed": bool(base_checksums["context_encoder"] != raw_checksums["context_encoder"]),
        "online_gru_changed": bool(base_checksums["online_gru"] != raw_checksums["online_gru"]),
        "critic_changed": bool(base_checksums["critic"] != raw_checksums["critic"]),
        "log_std_changed": bool(base_checksums["log_std"] != raw_checksums["log_std"]),
        "forbidden_parameter_changed": forbidden_changed,
        "base_checksums": base_checksums,
        "raw_checksums": raw_checksums,
        "training_started": bool(len(meta_rows) > 0 and not missing_target_keys),
        "optimizer_started": bool(len(meta_rows) > 0 and not missing_target_keys),
        "m880_exact_used": False,
        "replay_used": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "target_weight_rows_csv": run_dir / "target_weight_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled fusion-plus-head public-base probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--target-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--seed", type=int, default=9370)
    parser.add_argument("--lr", type=float, default=5e-4)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_EXTENDED_ALPHAS)
    args = parser.parse_args()
    summary = run_controlled_fusion_surface_probe(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        run_dir=args.run_dir,
        device=args.device,
        epochs=args.epochs,
        seed=args.seed,
        alphas=tuple(args.alphas),
        lr=args.lr,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
