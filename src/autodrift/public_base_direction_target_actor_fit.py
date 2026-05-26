"""Objective-only actor fit for exported M962 direction targets."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import validate_corpus_frame
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots
from autodrift.public_base_controlled_fusion_surface_probe import _base_actions, _mean, _percentile
from autodrift.public_base_direction_target_export import DEFAULT_RUN_DIR as _EXPORT_RUN_DIR
from autodrift.public_base_low_tail_sequence_target_audit import (
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_CONTRAST_ROWS,
    DEFAULT_POSITIVE_ROWS,
    DEFAULT_SCENARIO_CONFIG,
)
from autodrift.public_base_policy_head_trust_region_probe import (
    _clone_state_dict,
    _parse_float_list,
    _parameter_anchor_loss,
    _save_checkpoint,
    interpolate_actor_mean_state,
    set_actor_mean_trainable_only,
    state_checksums,
)
from autodrift.public_base_replay_constrained_target_feasibility import (
    DEFAULT_ACTIVE_ROW_IDS,
    DEFAULT_ENV_CONFIG,
    DEFAULT_M267_CORPUS,
    _m267_target_preflight,
    _requests,
    _snapshot,
    _summarize_m267_preflight,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import _load_probe_samples, _metadata_missing, _read_csv_rows
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_RUN_DIR = Path("runs/m964_v4_public_base_direction_target_actor_fit")
DEFAULT_ACCEPTED_TARGETS = _EXPORT_RUN_DIR / "accepted_direction_targets.csv"
DEFAULT_FAMILY_CATALOG = _EXPORT_RUN_DIR / "direction_target_family_catalog.csv"
DEFAULT_PROOF_TARGETS = _EXPORT_RUN_DIR / "branch_separated_proof_targets.csv"
DEFAULT_RETENTION_TARGETS = _EXPORT_RUN_DIR / "retention_anchor_targets.csv"
DEFAULT_ALPHAS = (0.05, 0.10, 0.20, 0.50, 1.00)
TARGET_FIT_RELATIVE_IMPROVEMENT = 0.001
ANCHOR_MSE_MEAN_TOLERANCE = 0.000004
ANCHOR_MSE_P95_TOLERANCE = 0.000025


def classify_direction_target_actor_fit(
    *,
    non_actor_mean_changed: bool,
    actor_mean_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_rows: int,
    candidate_count: int,
    target_fit_improved_count: int,
    proof_preflight_pass_count: int,
    retention_pass_count: int,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(non_actor_mean_changed) or bool(ppo_used) or bool(promoted):
        return "direction_target_actor_fit_contract_artifact"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0 or int(missing_target_rows) > 0:
        return "direction_target_actor_fit_reconstruction_blocked"
    if not bool(actor_mean_changed):
        return "direction_target_actor_fit_no_actor_update"
    if int(candidate_count) > 0:
        return "direction_target_actor_fit_candidate"
    if int(target_fit_improved_count) > 0 and int(proof_preflight_pass_count) <= 0:
        return "direction_target_actor_fit_proof_washout"
    if int(target_fit_improved_count) > 0 and int(retention_pass_count) <= 0:
        return "direction_target_actor_fit_retention_regression"
    if int(target_fit_improved_count) > 0:
        return "direction_target_actor_fit_objective_conflict"
    return "direction_target_actor_fit_no_target_fit"


def _meta_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        int(row.get("seed", -1)),
        int(row.get("step", -1)),
        str(row.get("variant", "")),
        str(row.get("source_index", "")),
    )


def _target_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        int(row.get("seed", -1)),
        int(row.get("step", -1)),
        str(row.get("variant", "")),
        str(row.get("source_index", "")),
    )


def _action_tensor(rows: list[dict[str, Any]], prefix: str, device: torch.device) -> torch.Tensor:
    return torch.as_tensor(
        [
            [float(row[f"{prefix}_steer"]), float(row[f"{prefix}_throttle"]), float(row[f"{prefix}_brake"])]
            for row in rows
        ],
        dtype=torch.float32,
        device=device,
    )


def _target_training_tensors(
    *,
    accepted_rows: list[dict[str, Any]],
    meta_rows: list[dict[str, Any]],
    normal_features: torch.Tensor,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[dict[str, Any]], int]:
    meta_index = {_meta_key(row): index for index, row in enumerate(meta_rows)}
    features: list[torch.Tensor] = []
    targets: list[list[float]] = []
    weights: list[float] = []
    matched_rows: list[dict[str, Any]] = []
    missing = 0
    for row in accepted_rows:
        index = meta_index.get(_target_key(row))
        if index is None:
            missing += 1
            continue
        features.append(normal_features[index])
        targets.append([float(row["target_steer"]), float(row["target_throttle"]), float(row["target_brake"])])
        weights.append(float(row.get("target_weight", 1.0)))
        matched_rows.append({**row, "sample_index": int(index)})
    if not features:
        empty_features = torch.empty((0, int(normal_features.shape[1])), dtype=torch.float32, device=device)
        return empty_features, torch.empty((0, 3), dtype=torch.float32, device=device), torch.empty((0,), dtype=torch.float32, device=device), matched_rows, missing
    return (
        torch.stack(features).to(device=device, dtype=torch.float32),
        torch.as_tensor(targets, dtype=torch.float32, device=device),
        torch.as_tensor(weights, dtype=torch.float32, device=device),
        matched_rows,
        missing,
    )


def _retention_training_tensors(
    *,
    retention_rows: list[dict[str, Any]],
    meta_rows: list[dict[str, Any]],
    normal_features: torch.Tensor,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
    meta_index = {_meta_key(row): index for index, row in enumerate(meta_rows)}
    features: list[torch.Tensor] = []
    targets: list[list[float]] = []
    weights: list[float] = []
    missing = 0
    for row in retention_rows:
        index = meta_index.get(_target_key(row))
        if index is None:
            missing += 1
            continue
        features.append(normal_features[index])
        targets.append([float(row["target_steer"]), float(row["target_throttle"]), float(row["target_brake"])])
        weights.append(float(row.get("anchor_weight", 0.5)))
    if not features:
        empty_features = torch.empty((0, int(normal_features.shape[1])), dtype=torch.float32, device=device)
        return empty_features, torch.empty((0, 3), dtype=torch.float32, device=device), torch.empty((0,), dtype=torch.float32, device=device), missing
    return (
        torch.stack(features).to(device=device, dtype=torch.float32),
        torch.as_tensor(targets, dtype=torch.float32, device=device),
        torch.as_tensor(weights, dtype=torch.float32, device=device),
        missing,
    )


def _features_for_obs_hidden(model: ActorCritic, observation: np.ndarray, hidden: torch.Tensor, device: torch.device) -> torch.Tensor:
    obs_t = torch.as_tensor(np.asarray(observation, dtype=np.float32), dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.detach().reshape(1, -1).to(device=device, dtype=torch.float32)
    with torch.no_grad():
        features, _ = model.recurrent_features_tensor(obs_t, hidden_t)
    return features.squeeze(0).detach()


def _proof_training_tensors(
    *,
    model: ActorCritic,
    proof_rows: list[dict[str, Any]],
    m267_corpus_path: Path,
    env_config_path: Path,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
    if not proof_rows:
        return (
            torch.empty((0, model.actor_mean.in_features), dtype=torch.float32, device=device),
            torch.empty((0, 3), dtype=torch.float32, device=device),
            torch.empty((0,), dtype=torch.float32, device=device),
            0,
        )
    frame = pd.read_csv(m267_corpus_path)
    validate_corpus_frame(frame)
    row_ids = sorted({int(row["proof_row_id"]) for row in proof_rows})
    active = frame[frame["row_id"].astype(int).isin(row_ids)].copy().sort_values("row_id").reset_index(drop=True)
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(active),
        device=device,
    )
    feature_by_row_branch: dict[tuple[int, str], torch.Tensor] = {}
    for _, source in active.iterrows():
        left = _snapshot(snapshots, int(source["left_seed"]), int(source["left_step"]))
        right = _snapshot(snapshots, int(source["right_seed"]), int(source["right_step"]))
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(source["relocated_obstacle_body_x"]),
            body_lateral=float(source["relocated_obstacle_body_y"]),
            half_width=float(source["relocated_obstacle_half_width"]),
        )
        row_id = int(source["row_id"])
        feature_by_row_branch[(row_id, "normal")] = _features_for_obs_hidden(
            model,
            relocated.observation,
            relocated.hidden,
            device,
        )
        feature_by_row_branch[(row_id, "wrong_history")] = _features_for_obs_hidden(
            model,
            relocated.observation,
            right.hidden,
            device,
        )
    features: list[torch.Tensor] = []
    targets: list[list[float]] = []
    weights: list[float] = []
    missing = 0
    for row in proof_rows:
        feature = feature_by_row_branch.get((int(row["proof_row_id"]), str(row["branch"])))
        if feature is None:
            missing += 1
            continue
        features.append(feature)
        targets.append([float(row["target_steer"]), float(row["target_throttle"]), float(row["target_brake"])])
        weights.append(2.0 if str(row["branch"]) == "wrong_history" else 1.0)
    if not features:
        return (
            torch.empty((0, model.actor_mean.in_features), dtype=torch.float32, device=device),
            torch.empty((0, 3), dtype=torch.float32, device=device),
            torch.empty((0,), dtype=torch.float32, device=device),
            missing,
        )
    return (
        torch.stack(features).to(device=device, dtype=torch.float32),
        torch.as_tensor(targets, dtype=torch.float32, device=device),
        torch.as_tensor(weights, dtype=torch.float32, device=device),
        missing,
    )


def _weighted_mse(actions: torch.Tensor, targets: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
    if actions.numel() == 0:
        return torch.zeros((), dtype=torch.float32, device=actions.device)
    error = torch.mean((actions - targets).pow(2), dim=-1)
    return (weights * error).sum() / torch.clamp(weights.sum(), min=1.0)


def _anchor_metric_row(
    *,
    alpha: float,
    label: str,
    actions: torch.Tensor,
    targets: torch.Tensor,
    weights: torch.Tensor,
    baseline_mse: float,
) -> dict[str, Any]:
    if actions.numel() == 0:
        return {
            "alpha": float(alpha),
            "metric": label,
            "rows": 0,
            "weighted_mse_mean": float("nan"),
            "unweighted_mse_mean": float("nan"),
            "unweighted_mse_p95": float("nan"),
            "baseline_weighted_mse_mean": float(baseline_mse),
            "improved": False,
            "retention_pass": False,
        }
    per_row = torch.mean((actions - targets).pow(2), dim=-1).detach().cpu().numpy()
    weighted = _weighted_mse(actions, targets, weights)
    return {
        "alpha": float(alpha),
        "metric": label,
        "rows": int(per_row.shape[0]),
        "weighted_mse_mean": float(weighted.detach().item()),
        "unweighted_mse_mean": _mean(per_row),
        "unweighted_mse_p95": _percentile(per_row, 95),
        "baseline_weighted_mse_mean": float(baseline_mse),
        "improved": bool(float(weighted.detach().item()) < float(baseline_mse) * (1.0 - TARGET_FIT_RELATIVE_IMPROVEMENT)),
        "retention_pass": bool(_mean(per_row) <= ANCHOR_MSE_MEAN_TOLERANCE and _percentile(per_row, 95) <= ANCHOR_MSE_P95_TOLERANCE),
    }


def train_direction_target_actor_fit(
    model: ActorCritic,
    *,
    target_features: torch.Tensor,
    target_actions: torch.Tensor,
    target_weights: torch.Tensor,
    proof_features: torch.Tensor,
    proof_actions: torch.Tensor,
    proof_weights: torch.Tensor,
    retention_features: torch.Tensor,
    retention_actions: torch.Tensor,
    retention_weights: torch.Tensor,
    base_state: dict[str, torch.Tensor],
    epochs: int,
    seed: int,
    lr: float,
    direction_coef: float,
    proof_coef: float,
    retention_coef: float,
    parameter_anchor_coef: float,
) -> list[dict[str, Any]]:
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device
    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    history: list[dict[str, Any]] = []
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        target_pred = torch.tanh(model.actor_mean(target_features))
        proof_pred = torch.tanh(model.actor_mean(proof_features))
        retention_pred = torch.tanh(model.actor_mean(retention_features))
        target_loss = _weighted_mse(target_pred, target_actions, target_weights)
        proof_loss = _weighted_mse(proof_pred, proof_actions, proof_weights)
        retention_loss = _weighted_mse(retention_pred, retention_actions, retention_weights)
        parameter_loss = _parameter_anchor_loss(model, base_state, device)
        loss = (
            float(direction_coef) * target_loss
            + float(proof_coef) * proof_loss
            + float(retention_coef) * retention_loss
            + float(parameter_anchor_coef) * parameter_loss
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.actor_mean.parameters(), max_norm=1.0)
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "target_loss": float(target_loss.detach().item()),
                "proof_loss": float(proof_loss.detach().item()),
                "retention_loss": float(retention_loss.detach().item()),
                "parameter_anchor_loss": float(parameter_loss.detach().item()),
            }
        )
    return history


def _alpha_metrics(
    *,
    model: ActorCritic,
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alphas: tuple[float, ...],
    target_features: torch.Tensor,
    target_actions: torch.Tensor,
    target_weights: torch.Tensor,
    proof_features: torch.Tensor,
    proof_actions: torch.Tensor,
    proof_weights: torch.Tensor,
    retention_features: torch.Tensor,
    retention_actions: torch.Tensor,
    retention_weights: torch.Tensor,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    device = next(model.parameters()).device
    original_state = _clone_state_dict(model)
    with torch.no_grad():
        model.load_state_dict({name: tensor.to(device=device) for name, tensor in base_state.items()})
        base_target_mse = float(_weighted_mse(torch.tanh(model.actor_mean(target_features)), target_actions, target_weights).item())
        base_proof_mse = float(_weighted_mse(torch.tanh(model.actor_mean(proof_features)), proof_actions, proof_weights).item())
        base_retention_mse = float(_weighted_mse(torch.tanh(model.actor_mean(retention_features)), retention_actions, retention_weights).item())
    target_rows: list[dict[str, Any]] = []
    proof_rows: list[dict[str, Any]] = []
    retention_rows: list[dict[str, Any]] = []
    try:
        for alpha in alphas:
            alpha_value = float(alpha)
            model.load_state_dict(interpolate_actor_mean_state(base_state, raw_state, alpha_value))
            with torch.no_grad():
                target_pred = torch.tanh(model.actor_mean(target_features))
                proof_pred = torch.tanh(model.actor_mean(proof_features))
                retention_pred = torch.tanh(model.actor_mean(retention_features))
            target_row = _anchor_metric_row(
                alpha=alpha_value,
                label="direction_target_fit",
                actions=target_pred,
                targets=target_actions,
                weights=target_weights,
                baseline_mse=base_target_mse,
            )
            target_row["target_fit_improved"] = bool(target_row["improved"])
            target_rows.append(target_row)
            proof_row = _anchor_metric_row(
                alpha=alpha_value,
                label="proof_anchor",
                actions=proof_pred,
                targets=proof_actions,
                weights=proof_weights,
                baseline_mse=base_proof_mse,
            )
            proof_rows.append(proof_row)
            retention_row = _anchor_metric_row(
                alpha=alpha_value,
                label="retention_anchor",
                actions=retention_pred,
                targets=retention_actions,
                weights=retention_weights,
                baseline_mse=base_retention_mse,
            )
            retention_rows.append(retention_row)
    finally:
        model.load_state_dict({name: tensor.to(device=device) for name, tensor in original_state.items()})
    return target_rows, proof_rows, retention_rows


def _m267_preflight_for_alphas(
    *,
    model: ActorCritic,
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alphas: tuple[float, ...],
    m267_corpus_path: Path,
    env_config_path: Path,
    active_row_ids: tuple[int, ...],
    device: torch.device,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    original_state = _clone_state_dict(model)
    rows: list[dict[str, Any]] = []
    try:
        for alpha in alphas:
            alpha_value = float(alpha)
            family = f"alpha_{alpha_value:.4f}".replace(".", "_")
            model.load_state_dict(interpolate_actor_mean_state(base_state, raw_state, alpha_value))
            preflight_rows = _m267_target_preflight(
                model=model,
                corpus_csv=m267_corpus_path,
                env_config_path=env_config_path,
                active_row_ids=active_row_ids,
                family_names=[family],
                device=device,
                max_continuation_steps=max_continuation_steps,
            )
            for row in _summarize_m267_preflight(preflight_rows):
                rows.append({"alpha": alpha_value, **row})
    finally:
        model.load_state_dict({name: tensor.to(device=device) for name, tensor in original_state.items()})
    return rows


def run_direction_target_actor_fit(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    accepted_targets_path: Path,
    proof_targets_path: Path,
    retention_targets_path: Path,
    m267_corpus_path: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    lr: float,
    alphas: tuple[float, ...],
    active_row_ids: tuple[int, ...],
    max_continuation_steps: int,
    direction_coef: float,
    proof_coef: float,
    retention_coef: float,
    parameter_anchor_coef: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    set_actor_mean_trainable_only(model)
    base_state = _clone_state_dict(model)
    base_checksums = state_checksums(base_state)
    base_model_checksum = model_parameter_checksum(model)
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    accepted_rows = _read_csv_rows(accepted_targets_path)
    proof_rows = _read_csv_rows(proof_targets_path)
    retention_rows = _read_csv_rows(retention_targets_path)
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
    samples = {key: value.to(device=resolved_device, dtype=torch.float32) for key, value in samples_cpu.items()}
    target_features, target_actions, target_weights, matched_target_rows, missing_target_rows = _target_training_tensors(
        accepted_rows=accepted_rows,
        meta_rows=meta_rows,
        normal_features=samples["normal_features"],
        device=resolved_device,
    )
    retention_features, retention_actions, retention_weights, missing_retention_rows = _retention_training_tensors(
        retention_rows=retention_rows,
        meta_rows=meta_rows,
        normal_features=samples["normal_features"],
        device=resolved_device,
    )
    proof_features, proof_actions, proof_weights, missing_proof_rows = _proof_training_tensors(
        model=model,
        proof_rows=proof_rows,
        m267_corpus_path=m267_corpus_path,
        env_config_path=env_config_path,
        device=resolved_device,
    )
    missing_total = int(missing_target_rows + missing_retention_rows + missing_proof_rows)
    training_started = bool(
        len(meta_rows) > 0
        and missing_total == 0
        and target_features.shape[0] > 0
        and proof_features.shape[0] > 0
        and retention_features.shape[0] > 0
    )
    if training_started:
        train_rows = train_direction_target_actor_fit(
            model,
            target_features=target_features,
            target_actions=target_actions,
            target_weights=target_weights,
            proof_features=proof_features,
            proof_actions=proof_actions,
            proof_weights=proof_weights,
            retention_features=retention_features,
            retention_actions=retention_actions,
            retention_weights=retention_weights,
            base_state=base_state,
            epochs=epochs,
            seed=seed,
            lr=lr,
            direction_coef=direction_coef,
            proof_coef=proof_coef,
            retention_coef=retention_coef,
            parameter_anchor_coef=parameter_anchor_coef,
        )
        raw_state = _clone_state_dict(model)
    else:
        train_rows = []
        raw_state = base_state
    target_metric_rows, proof_metric_rows, retention_metric_rows = _alpha_metrics(
        model=model,
        base_state=base_state,
        raw_state=raw_state,
        alphas=alphas,
        target_features=target_features,
        target_actions=target_actions,
        target_weights=target_weights,
        proof_features=proof_features,
        proof_actions=proof_actions,
        proof_weights=proof_weights,
        retention_features=retention_features,
        retention_actions=retention_actions,
        retention_weights=retention_weights,
    )
    m267_rows = _m267_preflight_for_alphas(
        model=model,
        base_state=base_state,
        raw_state=raw_state,
        alphas=alphas,
        m267_corpus_path=m267_corpus_path,
        env_config_path=env_config_path,
        active_row_ids=active_row_ids,
        device=resolved_device,
        max_continuation_steps=max_continuation_steps,
    )
    target_by_alpha = {float(row["alpha"]): row for row in target_metric_rows}
    proof_by_alpha = {float(row["alpha"]): row for row in proof_metric_rows}
    retention_by_alpha = {float(row["alpha"]): row for row in retention_metric_rows}
    m267_by_alpha = {float(row["alpha"]): row for row in m267_rows}
    route_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for alpha in alphas:
        alpha_value = float(alpha)
        target_row = target_by_alpha.get(alpha_value, {})
        proof_row = proof_by_alpha.get(alpha_value, {})
        retention_row = retention_by_alpha.get(alpha_value, {})
        m267_row = m267_by_alpha.get(alpha_value, {})
        target_fit_improved = bool(target_row.get("target_fit_improved", False))
        proof_anchor_pass = bool(proof_row.get("retention_pass", False))
        retention_anchor_pass = bool(retention_row.get("retention_pass", False))
        m267_pass = bool(m267_row.get("gate_pass", False))
        candidate = bool(target_fit_improved and proof_anchor_pass and retention_anchor_pass and m267_pass)
        route = {
            "alpha": alpha_value,
            "target_fit_improved": target_fit_improved,
            "proof_anchor_pass": proof_anchor_pass,
            "retention_anchor_pass": retention_anchor_pass,
            "m267_preflight_pass": m267_pass,
            "actor_fit_candidate": candidate,
            "target_weighted_mse": float(target_row.get("weighted_mse_mean", float("nan"))),
            "proof_weighted_mse": float(proof_row.get("weighted_mse_mean", float("nan"))),
            "retention_weighted_mse": float(retention_row.get("weighted_mse_mean", float("nan"))),
            "m267_success_drop_count": int(m267_row.get("candidate_success_drop_count", 0) or 0),
            "m267_failed_active_rows": str(m267_row.get("failed_active_rows", "")),
        }
        route_rows.append(route)
        if candidate:
            candidate_rows.append(route)
    raw_checksums = state_checksums(raw_state)
    non_actor_mean_changed = bool(base_checksums["non_actor_mean"] != raw_checksums["non_actor_mean"])
    actor_mean_changed = bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"])
    target_fit_improved_count = sum(1 for row in route_rows if bool(row["target_fit_improved"]))
    proof_preflight_pass_count = sum(1 for row in route_rows if bool(row["m267_preflight_pass"]))
    retention_pass_count = sum(1 for row in route_rows if bool(row["retention_anchor_pass"]))
    result_class = classify_direction_target_actor_fit(
        non_actor_mean_changed=non_actor_mean_changed,
        actor_mean_changed=actor_mean_changed,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_rows=missing_total,
        candidate_count=len(candidate_rows),
        target_fit_improved_count=target_fit_improved_count,
        proof_preflight_pass_count=proof_preflight_pass_count,
        retention_pass_count=retention_pass_count,
        ppo_used=False,
        promoted=False,
    )
    if candidate_rows:
        next_blocker = "direction-target replay gate design"
    elif target_fit_improved_count > 0 and proof_preflight_pass_count <= 0:
        next_blocker = "stronger proof-anchor objective design"
    elif target_fit_improved_count > 0 and retention_pass_count <= 0:
        next_blocker = "retention-anchor objective repair"
    elif target_fit_improved_count <= 0:
        next_blocker = "trainable-surface audit"
    else:
        next_blocker = "actor-fit objective conflict audit"
    checkpoint_dir = run_dir / "checkpoints"
    candidate_checkpoint_rows: list[dict[str, Any]] = []
    if training_started:
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=raw_state,
            destination=checkpoint_dir / "raw_actor_mean_update.pt",
            objective="public_base_direction_target_actor_fit_raw",
        )
    for row in candidate_rows:
        alpha_value = float(row["alpha"])
        candidate_state = interpolate_actor_mean_state(base_state, raw_state, alpha_value)
        path = checkpoint_dir / f"alpha_{str(alpha_value).replace('.', '_')}.pt"
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=candidate_state,
            destination=path,
            objective="public_base_direction_target_actor_fit_candidate",
        )
        candidate_checkpoint_rows.append({"alpha": alpha_value, "checkpoint": path})
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "target_fit_metrics.csv", target_metric_rows)
    write_csv_rows(run_dir / "proof_anchor_metrics.csv", proof_metric_rows)
    write_csv_rows(run_dir / "retention_anchor_metrics.csv", retention_metric_rows)
    write_csv_rows(run_dir / "m267_preflight_summary.csv", m267_rows)
    write_csv_rows(run_dir / "route_decision.csv", route_rows)
    write_csv_rows(run_dir / "candidate_checkpoints.csv", candidate_checkpoint_rows)
    write_csv_rows(run_dir / "matched_direction_targets.csv", matched_target_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "public_base_direction_target_actor_fit",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "accepted_targets": accepted_targets_path,
        "proof_targets": proof_targets_path,
        "retention_targets": retention_targets_path,
        "m267_corpus": m267_corpus_path,
        "active_row_ids": list(active_row_ids),
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "accepted_target_rows": int(len(accepted_rows)),
        "matched_target_rows": int(len(matched_target_rows)),
        "proof_anchor_rows": int(proof_features.shape[0]),
        "retention_anchor_rows": int(retention_features.shape[0]),
        "missing_target_rows": int(missing_target_rows),
        "missing_retention_rows": int(missing_retention_rows),
        "missing_proof_rows": int(missing_proof_rows),
        "missing_total": int(missing_total),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "direction_coef": float(direction_coef),
        "proof_coef": float(proof_coef),
        "retention_coef": float(retention_coef),
        "parameter_anchor_coef": float(parameter_anchor_coef),
        "alphas": [float(alpha) for alpha in alphas],
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row["alpha"]) for row in candidate_rows],
        "target_fit_improved_count": int(target_fit_improved_count),
        "proof_preflight_pass_count": int(proof_preflight_pass_count),
        "retention_pass_count": int(retention_pass_count),
        "actor_mean_changed": actor_mean_changed,
        "non_actor_mean_changed": non_actor_mean_changed,
        "feature_backbone_changed": bool(base_checksums["feature_backbone"] != raw_checksums["feature_backbone"]),
        "critic_changed": bool(base_checksums["critic"] != raw_checksums["critic"]),
        "log_std_changed": bool(base_checksums["log_std"] != raw_checksums["log_std"]),
        "base_model_checksum": base_model_checksum,
        "base_checksums": base_checksums,
        "raw_checksums": raw_checksums,
        "training_started": bool(training_started),
        "optimizer_started": bool(training_started),
        "actor_mean_only_training": bool(training_started),
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "private_holdout_used": False,
        "candidate_checkpoints": candidate_checkpoint_rows,
        "result_class": result_class,
        "next_blocker": next_blocker,
        "summary_json": run_dir / "summary.json",
        "target_fit_metrics_csv": run_dir / "target_fit_metrics.csv",
        "proof_anchor_metrics_csv": run_dir / "proof_anchor_metrics.csv",
        "retention_anchor_metrics_csv": run_dir / "retention_anchor_metrics.csv",
        "m267_preflight_summary_csv": run_dir / "m267_preflight_summary.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "candidate_checkpoints_csv": run_dir / "candidate_checkpoints.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_int_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(item) for item in str(raw).split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run objective-only direction-target actor fit.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, default=DEFAULT_POSITIVE_ROWS)
    parser.add_argument("--contrast-rows", type=Path, default=DEFAULT_CONTRAST_ROWS)
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO_CONFIG)
    parser.add_argument("--accepted-targets", type=Path, default=DEFAULT_ACCEPTED_TARGETS)
    parser.add_argument("--proof-targets", type=Path, default=DEFAULT_PROOF_TARGETS)
    parser.add_argument("--retention-targets", type=Path, default=DEFAULT_RETENTION_TARGETS)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--seed", type=int, default=9640)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--active-row-ids", type=_parse_int_tuple, default=DEFAULT_ACTIVE_ROW_IDS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--direction-coef", type=float, default=1.0)
    parser.add_argument("--proof-coef", type=float, default=1.0)
    parser.add_argument("--retention-coef", type=float, default=0.5)
    parser.add_argument("--parameter-anchor-coef", type=float, default=0.01)
    args = parser.parse_args()
    summary = run_direction_target_actor_fit(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        accepted_targets_path=args.accepted_targets,
        proof_targets_path=args.proof_targets,
        retention_targets_path=args.retention_targets,
        m267_corpus_path=args.m267_corpus,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        epochs=args.epochs,
        seed=args.seed,
        lr=args.lr,
        alphas=args.alphas,
        active_row_ids=args.active_row_ids,
        max_continuation_steps=args.max_continuation_steps,
        direction_coef=args.direction_coef,
        proof_coef=args.proof_coef,
        retention_coef=args.retention_coef,
        parameter_anchor_coef=args.parameter_anchor_coef,
    )
    print(f"result_class={summary['result_class']}")
    print(f"candidate_alpha_count={summary['candidate_alpha_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
