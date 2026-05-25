"""Actor-mean-only trust-region probe for the M399 public base."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.public_base_alpha_aware_low_tail_residual_probe import (
    LOW_TAIL_DEFICIT_TARGET,
    LOW_TAIL_GAP_MARGIN,
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
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import _load_probe_samples, _metadata_missing, _parse_float_list, _read_csv_rows


DEFAULT_ALPHAS = (0.001, 0.002, 0.005, 0.010, 0.020, 0.050, 0.100)
TARGET_MSE_TOLERANCE = 0.000005
FEATURE_BACKBONE_PREFIXES = (
    "shared.",
    "frame_encoder.",
    "temporal_gru.",
    "online_gru_cell.",
    "response_encoder.",
    "context_encoder.",
    "response_context_fusion.",
    "privileged_encoder.",
    "privileged_residual.",
    "sequence_tail.",
    "response_prediction_head.",
)


def _state_checksum(
    state_dict: dict[str, torch.Tensor],
    *,
    include_prefixes: tuple[str, ...] | None = None,
    include_names: tuple[str, ...] | None = None,
    exclude_prefixes: tuple[str, ...] = (),
    exclude_names: tuple[str, ...] = (),
) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(state_dict.items()):
        if include_prefixes is not None and not any(name.startswith(prefix) for prefix in include_prefixes):
            continue
        if include_names is not None and name not in include_names:
            continue
        if any(name.startswith(prefix) for prefix in exclude_prefixes) or name in exclude_names:
            continue
        digest.update(name.encode("utf-8"))
        array = tensor.detach().cpu().contiguous().numpy()
        digest.update(str(array.dtype).encode("utf-8"))
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
    return digest.hexdigest()


def _clone_state_dict(model: ActorCritic) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def state_checksums(state_dict: dict[str, torch.Tensor]) -> dict[str, str]:
    return {
        "full": _state_checksum(state_dict),
        "actor_mean": _state_checksum(state_dict, include_prefixes=("actor_mean.",)),
        "feature_backbone": _state_checksum(state_dict, include_prefixes=FEATURE_BACKBONE_PREFIXES),
        "critic": _state_checksum(state_dict, include_prefixes=("critic.",)),
        "log_std": _state_checksum(state_dict, include_names=("log_std",)),
        "non_actor_mean": _state_checksum(state_dict, exclude_prefixes=("actor_mean.",)),
    }


def set_actor_mean_trainable_only(model: ActorCritic) -> None:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.actor_mean.parameters():
        parameter.requires_grad_(True)


def interpolate_actor_mean_state(
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    alpha_value = float(alpha)
    interpolated: dict[str, torch.Tensor] = {}
    for name, base_tensor in base_state.items():
        if name.startswith("actor_mean."):
            interpolated[name] = base_tensor + alpha_value * (raw_state[name] - base_tensor)
        else:
            interpolated[name] = base_tensor.clone()
    return interpolated


def _move_samples(samples: dict[str, torch.Tensor], device: torch.device) -> dict[str, torch.Tensor]:
    return {name: tensor.to(device=device, dtype=torch.float32) for name, tensor in samples.items()}


def _parameter_anchor_loss(model: ActorCritic, base_state: dict[str, torch.Tensor], device: torch.device) -> torch.Tensor:
    loss = torch.zeros((), dtype=torch.float32, device=device)
    count = 0
    for name, parameter in model.actor_mean.named_parameters():
        key = f"actor_mean.{name}"
        base_tensor = base_state[key].to(device=device, dtype=torch.float32)
        loss = loss + torch.mean((parameter - base_tensor).pow(2))
        count += 1
    return loss / max(count, 1)


def train_policy_head_trust_region(
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
    target_action_coef: float = 0.5,
    low_tail_gap_floor_coef: float = 2.0,
    low_tail_deficit_coef: float = 1.0,
    normal_retention_coef: float = 8.0,
    intervention_anchor_coef: float = 1.0,
    parameter_anchor_coef: float = 0.01,
) -> list[dict[str, Any]]:
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device
    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    normal_features = samples["normal_features"]
    intervention_features = samples["intervention_features"]
    base_normal_actions = samples["normal_actions"]
    base_intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    history: list[dict[str, Any]] = []
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        normal_actions = torch.tanh(model.actor_mean(normal_features))
        intervention_actions = torch.tanh(model.actor_mean(intervention_features))
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
        parameter_anchor_loss = _parameter_anchor_loss(model, base_state, device)
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


def evaluate_policy_head_alphas(
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
            model.load_state_dict(interpolate_actor_mean_state(base_state, raw_state, alpha_value))
            with torch.no_grad():
                adjusted_normal = torch.tanh(model.actor_mean(samples["normal_features"]))
                adjusted_intervention = torch.tanh(model.actor_mean(samples["intervention_features"]))
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


def classify_policy_head_trust_region_probe(
    *,
    non_actor_mean_changed: bool,
    actor_mean_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_keys: int,
    candidate_count: int,
    any_tail_lift: bool,
    any_normal_retained_tail_lift: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(non_actor_mean_changed) or bool(ppo_used) or bool(promoted):
        return "public_base_policy_head_trust_region_probe_contract_artifact"
    if int(missing_target_keys) > 0:
        return "public_base_policy_head_trust_region_probe_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_policy_head_trust_region_probe_reconstruction_blocked"
    if not bool(actor_mean_changed):
        return "public_base_policy_head_trust_region_probe_no_actor_update"
    if int(candidate_count) > 0:
        return "public_base_policy_head_trust_region_probe_candidate"
    if bool(any_normal_retained_tail_lift):
        return "public_base_policy_head_trust_region_probe_target_conflict"
    if bool(any_tail_lift):
        return "public_base_policy_head_trust_region_probe_trust_region_conflict"
    return "public_base_policy_head_trust_region_probe_no_tail_lift"


def _best_row(rows: list[dict[str, Any]], *, key_fields: tuple[str, ...], filter_key: str | None = None) -> dict[str, Any]:
    filtered = [row for row in rows if filter_key is None or bool(row.get(filter_key, False))]
    if not filtered:
        return {}
    return sorted(filtered, key=lambda row: tuple(float(row.get(field, 0.0)) for field in key_fields))[0]


def _save_checkpoint(
    *,
    checkpoint_data: dict[str, Any],
    state_dict: dict[str, torch.Tensor],
    destination: Path,
    objective: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = dict(checkpoint_data)
    output["model_state"] = {name: tensor.detach().cpu() for name, tensor in state_dict.items()}
    config = dict(output.get("config", {}))
    config["objective"] = objective
    output["config"] = config
    torch.save(output, destination)


def run_policy_head_trust_region_probe(
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
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
    lr: float = 3e-4,
    target_action_coef: float = 0.5,
    low_tail_gap_floor_coef: float = 2.0,
    low_tail_deficit_coef: float = 1.0,
    normal_retention_coef: float = 8.0,
    intervention_anchor_coef: float = 1.0,
    parameter_anchor_coef: float = 0.01,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    set_actor_mean_trainable_only(model)
    base_state = _clone_state_dict(model)
    base_checksums = state_checksums(base_state)
    base_model_checksum = model_parameter_checksum(model)
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    m912_summary = read_json(m912_summary_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples_cpu, meta_rows, rejected_rows = _load_probe_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    samples = _move_samples(samples_cpu, resolved_device)
    if len(meta_rows) == 0:
        target_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        low_tail_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        target_actions = torch.empty((0, 3), dtype=torch.float32, device=resolved_device)
        target_weights = torch.empty((0,), dtype=torch.float32, device=resolved_device)
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
            train_rows = train_policy_head_trust_region(
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
                target_action_coef=target_action_coef,
                low_tail_gap_floor_coef=low_tail_gap_floor_coef,
                low_tail_deficit_coef=low_tail_deficit_coef,
                normal_retention_coef=normal_retention_coef,
                intervention_anchor_coef=intervention_anchor_coef,
                parameter_anchor_coef=parameter_anchor_coef,
            )
            raw_state = _clone_state_dict(model)
            alpha_rows, objective_rows = evaluate_policy_head_alphas(
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
    raw_checksums = state_checksums(raw_state)
    candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    tail_rows = [row for row in alpha_rows if bool(row.get("tail_lift_pass", False))]
    normal_tail_rows = [
        row for row in alpha_rows if bool(row.get("tail_lift_pass", False)) and bool(row.get("normal_retention_pass", False))
    ]
    low_tail_effect_rows = [row for row in alpha_rows if bool(row.get("low_tail_effect_candidate", False))]
    target_tolerance_rows = [row for row in alpha_rows if bool(row.get("target_tolerance_candidate", False))]
    normal_safe_trend_rows = [row for row in alpha_rows if bool(row.get("normal_safe_low_tail_trend", False))]
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_normal_retaining_low_tail = _best_row(
        alpha_rows,
        key_fields=("low_tail_fraction", "gap_deficit_mean"),
        filter_key="normal_retention_pass",
    )
    best_tail_lift_nonretaining = _best_row(
        [row for row in tail_rows if not bool(row.get("normal_retention_pass", False))],
        key_fields=("low_tail_fraction", "gap_deficit_mean"),
    )
    candidate_checkpoint_rows: list[dict[str, Any]] = []
    checkpoint_dir = run_dir / "checkpoints"
    for row in candidate_rows:
        alpha_value = float(row["alpha"])
        candidate_state = interpolate_actor_mean_state(base_state, raw_state, alpha_value)
        path = checkpoint_dir / f"alpha_{str(alpha_value).replace('.', '_')}.pt"
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=candidate_state,
            destination=path,
            objective="public_base_policy_head_trust_region_probe_candidate",
        )
        candidate_checkpoint_rows.append({"alpha": alpha_value, "checkpoint": path})
    if len(meta_rows) > 0 and not missing_target_keys:
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=raw_state,
            destination=checkpoint_dir / "raw_actor_mean_update.pt",
            objective="public_base_policy_head_trust_region_probe_raw",
        )
    non_actor_mean_changed = bool(base_checksums["non_actor_mean"] != raw_checksums["non_actor_mean"])
    actor_mean_changed = bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"])
    result_class = classify_policy_head_trust_region_probe(
        non_actor_mean_changed=non_actor_mean_changed,
        actor_mean_changed=actor_mean_changed,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        candidate_count=len(candidate_rows),
        any_tail_lift=bool(tail_rows),
        any_normal_retained_tail_lift=bool(normal_tail_rows),
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "target_weight_rows.csv", weight_rows)
    write_csv_rows(run_dir / "candidate_checkpoints.csv", candidate_checkpoint_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [*rejected_rows, *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys))],
    )
    target_count = int(target_mask.sum().item()) if len(meta_rows) else 0
    strict_target_count = sum(1 for row in target_rows if str(row.get("source_label", "")) == "strict_low_tail")
    near_tail_target_count = sum(1 for row in target_rows if str(row.get("source_label", "")) == "near_tail_coverage")
    summary = {
        "run_type": "public_base_policy_head_trust_region_probe",
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
        "joined_target_rows": target_count,
        "strict_target_rows": int(strict_target_count),
        "near_tail_target_rows": int(near_tail_target_count),
        "low_tail_rows_count": int(len(low_tail_rows)),
        "missing_target_keys": int(len(missing_target_keys)),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "target_action_coef": float(target_action_coef),
        "low_tail_gap_floor_coef": float(low_tail_gap_floor_coef),
        "low_tail_deficit_coef": float(low_tail_deficit_coef),
        "normal_retention_coef": float(normal_retention_coef),
        "intervention_anchor_coef": float(intervention_anchor_coef),
        "parameter_anchor_coef": float(parameter_anchor_coef),
        "alphas": [float(alpha) for alpha in alphas],
        "near_base_gap_p10": float(m912_summary["near_base_gap_p10"]),
        "near_base_gap_deficit_mean": float(m912_summary["near_base_gap_deficit_mean"]),
        "near_base_low_tail_fraction": float(m912_summary["low_tail_fraction"]),
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
        "best_normal_retaining_low_tail_row": best_normal_retaining_low_tail,
        "best_tail_lift_nonretaining_row": best_tail_lift_nonretaining,
        "actor_mean_changed": actor_mean_changed,
        "feature_backbone_changed": bool(base_checksums["feature_backbone"] != raw_checksums["feature_backbone"]),
        "critic_changed": bool(base_checksums["critic"] != raw_checksums["critic"]),
        "log_std_changed": bool(base_checksums["log_std"] != raw_checksums["log_std"]),
        "non_actor_mean_changed": non_actor_mean_changed,
        "base_model_checksum": base_model_checksum,
        "base_checksums": base_checksums,
        "raw_checksums": raw_checksums,
        "training_started": bool(len(meta_rows) > 0 and not missing_target_keys),
        "optimizer_started": bool(len(meta_rows) > 0 and not missing_target_keys),
        "actor_mean_only_training": bool(len(meta_rows) > 0 and not missing_target_keys),
        "m880_exact_used": False,
        "replay_used": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "candidate_checkpoints": candidate_checkpoint_rows,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "target_weight_rows_csv": run_dir / "target_weight_rows.csv",
        "candidate_checkpoints_csv": run_dir / "candidate_checkpoints.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run actor_mean-only public-base trust-region probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--target-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9300)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--target-action-coef", type=float, default=0.5)
    parser.add_argument("--low-tail-gap-floor-coef", type=float, default=2.0)
    parser.add_argument("--low-tail-deficit-coef", type=float, default=1.0)
    parser.add_argument("--normal-retention-coef", type=float, default=8.0)
    parser.add_argument("--intervention-anchor-coef", type=float, default=1.0)
    parser.add_argument("--parameter-anchor-coef", type=float, default=0.01)
    args = parser.parse_args()
    summary = run_policy_head_trust_region_probe(
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
        target_action_coef=args.target_action_coef,
        low_tail_gap_floor_coef=args.low_tail_gap_floor_coef,
        low_tail_deficit_coef=args.low_tail_deficit_coef,
        normal_retention_coef=args.normal_retention_coef,
        intervention_anchor_coef=args.intervention_anchor_coef,
        parameter_anchor_coef=args.parameter_anchor_coef,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
