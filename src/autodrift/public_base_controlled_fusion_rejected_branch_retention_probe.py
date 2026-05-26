"""Controlled-fusion objective probe with rejected-branch retention."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import (
    run_boundary_outcome_replay_gate,
    validate_corpus_frame,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots
from autodrift.public_base_controlled_fusion_boundary_objective_probe import (
    DEFAULT_BOUNDARY_ALPHAS,
    DEFAULT_TRAIN_ALPHAS,
    LOSS_COEFFICIENTS as BOUNDARY_LOSS_COEFFICIENTS,
    _interpolated_actions,
    is_boundary_near_miss_row,
)
from autodrift.public_base_controlled_fusion_surface_probe import (
    controlled_surface_checksums,
    evaluate_controlled_fusion_alphas,
    set_controlled_fusion_trainable_only,
    _allowed_parameter_anchor_loss,
    _base_actions,
    _clone_state_dict,
    _load_trainable_samples,
    _save_checkpoint,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _parse_float_list, _read_csv_rows
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_BASE_CHECKPOINT = Path("runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt")
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_M267_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_ACTIVE_ROW_IDS = (6, 13, 15, 16)
DEFAULT_REPAIR_ALPHAS = (
    0.005,
    0.010,
    0.020,
    0.035,
    0.050,
    0.0675,
    0.0700,
    0.0725,
    0.0750,
    0.1000,
    0.1250,
    0.1500,
    0.2000,
    0.2500,
)
DEFAULT_LOSS_COEFFICIENTS = {
    **BOUNDARY_LOSS_COEFFICIENTS,
    "rejected_wrong_action_anchor": 25.0,
    "rejected_wrong_separation_floor": 5.0,
    "rejected_wrong_direction_anchor": 5.0,
}


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], Any], seed: int, step: int) -> Any:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed boundary snapshot seed={seed} step={step}")
    return snapshots[key]


def load_rejected_branch_samples(
    *,
    model: ActorCritic,
    corpus_csv: Path,
    env_config_path: Path,
    active_row_ids: tuple[int, ...],
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], list[dict[str, Any]], list[dict[str, Any]]]:
    frame = pd.read_csv(corpus_csv)
    validate_corpus_frame(frame)
    active = frame[frame["row_id"].astype(int).isin([int(row_id) for row_id in active_row_ids])].copy()
    active = active.sort_values("row_id").reset_index(drop=True)
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(active),
        device=device,
    )
    meta_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    normal_obs: list[np.ndarray] = []
    wrong_obs: list[np.ndarray] = []
    normal_hidden: list[torch.Tensor] = []
    wrong_hidden: list[torch.Tensor] = []
    for _, row in active.iterrows():
        try:
            left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
            right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
            relocated = relocate_outcome_snapshot(
                left,
                body_longitudinal=float(row["relocated_obstacle_body_x"]),
                body_lateral=float(row["relocated_obstacle_body_y"]),
                half_width=float(row["relocated_obstacle_half_width"]),
            )
        except Exception as exc:  # pragma: no cover - surfaced in artifact rows
            rejected_rows.append({**row.to_dict(), "rejection_reason": str(exc)})
            continue
        normal_obs.append(np.asarray(relocated.observation, dtype=np.float32))
        wrong_obs.append(np.asarray(relocated.observation, dtype=np.float32))
        normal_hidden.append(relocated.hidden.detach().cpu().reshape(-1))
        wrong_hidden.append(right.hidden.detach().cpu().reshape(-1))
        meta_rows.append(
            {
                "row_id": int(row["row_id"]),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
            }
        )
    if not meta_rows:
        empty_obs = torch.empty((0, model.obs_dim), dtype=torch.float32, device=device)
        empty_hidden = torch.empty((0, model.actor_mean.in_features), dtype=torch.float32, device=device)
        empty_actions = torch.empty((0, 3), dtype=torch.float32, device=device)
        return {
            "normal_obs": empty_obs,
            "wrong_obs": empty_obs,
            "normal_hidden": empty_hidden,
            "wrong_hidden": empty_hidden,
            "normal_actions": empty_actions,
            "wrong_actions": empty_actions,
            "base_direction_norm": torch.empty((0,), dtype=torch.float32, device=device),
            "base_direction_unit": empty_actions,
        }, meta_rows, rejected_rows
    normal_obs_t = torch.as_tensor(np.asarray(normal_obs), dtype=torch.float32, device=device)
    wrong_obs_t = torch.as_tensor(np.asarray(wrong_obs), dtype=torch.float32, device=device)
    normal_hidden_t = torch.stack(normal_hidden).to(device=device, dtype=torch.float32)
    wrong_hidden_t = torch.stack(wrong_hidden).to(device=device, dtype=torch.float32)
    normal_actions = _base_actions(model, normal_obs_t, normal_hidden_t).to(device=device)
    wrong_actions = _base_actions(model, wrong_obs_t, wrong_hidden_t).to(device=device)
    base_direction = wrong_actions - normal_actions
    base_direction_norm = torch.linalg.norm(base_direction, dim=-1)
    base_direction_unit = base_direction / torch.clamp(base_direction_norm.unsqueeze(-1), min=1e-6)
    return {
        "normal_obs": normal_obs_t,
        "wrong_obs": wrong_obs_t,
        "normal_hidden": normal_hidden_t,
        "wrong_hidden": wrong_hidden_t,
        "normal_actions": normal_actions,
        "wrong_actions": wrong_actions,
        "base_direction_norm": base_direction_norm,
        "base_direction_unit": base_direction_unit,
    }, meta_rows, rejected_rows


def rejected_branch_terms(
    *,
    model: ActorCritic,
    rejected_samples: dict[str, torch.Tensor],
    base_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    device = next(model.parameters()).device
    if rejected_samples["normal_obs"].shape[0] == 0:
        zero = torch.zeros((), dtype=torch.float32, device=device)
        return {
            "rejected_wrong_action_anchor": zero,
            "rejected_wrong_separation_floor": zero,
            "rejected_wrong_direction_anchor": zero,
            "rejected_gap_mean": zero,
        }
    normal_actions = _interpolated_actions(
        model,
        rejected_samples["normal_obs"],
        rejected_samples["normal_hidden"],
        base_state=base_state,
        alpha=float(alpha),
    )
    wrong_actions = _interpolated_actions(
        model,
        rejected_samples["wrong_obs"],
        rejected_samples["wrong_hidden"],
        base_state=base_state,
        alpha=float(alpha),
    )
    base_wrong_actions = rejected_samples["wrong_actions"]
    wrong_anchor = torch.mean((wrong_actions - base_wrong_actions).pow(2))
    direction = wrong_actions - normal_actions
    gap = torch.linalg.norm(direction, dim=-1)
    floor = 0.75 * rejected_samples["base_direction_norm"]
    separation = torch.relu(floor - gap).pow(2).mean()
    projection = torch.sum(direction * rejected_samples["base_direction_unit"], dim=-1)
    direction_anchor = torch.relu(floor - projection).pow(2).mean()
    return {
        "rejected_wrong_action_anchor": wrong_anchor,
        "rejected_wrong_separation_floor": separation,
        "rejected_wrong_direction_anchor": direction_anchor,
        "rejected_gap_mean": gap.mean(),
    }


def train_rejected_branch_retention_objective(
    model: ActorCritic,
    samples: dict[str, torch.Tensor],
    rejected_samples: dict[str, torch.Tensor],
    *,
    target_mask: torch.Tensor,
    low_tail_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_weights: torch.Tensor,
    base_state: dict[str, torch.Tensor],
    epochs: int,
    seed: int,
    lr: float,
    train_alphas: tuple[float, ...] = DEFAULT_TRAIN_ALPHAS,
    loss_coefficients: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    coefficients = dict(DEFAULT_LOSS_COEFFICIENTS if loss_coefficients is None else loss_coefficients)
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device
    optimizer = torch.optim.Adam([parameter for parameter in model.parameters() if parameter.requires_grad], lr=float(lr))
    history: list[dict[str, Any]] = []
    base_normal_actions = samples["normal_actions"]
    base_intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    if not train_alphas:
        raise ValueError("train_alphas must contain at least one alpha")

    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        term_values: dict[str, list[torch.Tensor]] = {
            "boundary_deficit_loss": [],
            "boundary_gap_floor_loss": [],
            "normal_retention_hinge": [],
            "normal_anchor_mse": [],
            "intervention_anchor_mse": [],
            "target_action_loss": [],
            "gap_mean": [],
            "rejected_wrong_action_anchor": [],
            "rejected_wrong_separation_floor": [],
            "rejected_wrong_direction_anchor": [],
            "rejected_gap_mean": [],
        }
        for alpha in train_alphas:
            normal_actions = _interpolated_actions(
                model,
                samples["normal_obs"],
                samples["normal_hidden"],
                base_state=base_state,
                alpha=float(alpha),
            )
            intervention_actions = _interpolated_actions(
                model,
                samples["intervention_obs"],
                samples["intervention_hidden"],
                base_state=base_state,
                alpha=float(alpha),
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
                boundary_deficit_loss = torch.relu(low_deficit - 0.01475).pow(2).mean()
                boundary_gap_floor_loss = torch.relu(0.00950 - low_gap).pow(2).mean()
            else:
                boundary_deficit_loss = torch.zeros((), dtype=torch.float32, device=device)
                boundary_gap_floor_loss = torch.zeros((), dtype=torch.float32, device=device)
            normal_delta = normal_actions - base_normal_actions
            normal_drift = torch.linalg.norm(normal_delta, dim=-1)
            normal_row_mse = torch.mean(normal_delta.pow(2), dim=-1)
            normal_retention_hinge = (
                torch.relu(normal_drift - 0.00280).pow(2).mean()
                + torch.relu(normal_row_mse - 0.00000350).pow(2).mean()
            )
            normal_anchor_mse = torch.mean(normal_delta.pow(2))
            intervention_anchor_mse = torch.mean((intervention_actions - base_intervention_actions).pow(2))
            rejected_terms = rejected_branch_terms(
                model=model,
                rejected_samples=rejected_samples,
                base_state=base_state,
                alpha=float(alpha),
            )
            term_values["boundary_deficit_loss"].append(boundary_deficit_loss)
            term_values["boundary_gap_floor_loss"].append(boundary_gap_floor_loss)
            term_values["normal_retention_hinge"].append(normal_retention_hinge)
            term_values["normal_anchor_mse"].append(normal_anchor_mse)
            term_values["intervention_anchor_mse"].append(intervention_anchor_mse)
            term_values["target_action_loss"].append(target_loss)
            term_values["gap_mean"].append(gap.mean())
            for name, value in rejected_terms.items():
                term_values[name].append(value)

        averaged_terms = {
            name: torch.stack(values).mean() if values else torch.zeros((), dtype=torch.float32, device=device)
            for name, values in term_values.items()
        }
        parameter_anchor_loss = _allowed_parameter_anchor_loss(model, base_state, device)
        loss = (
            coefficients["boundary_deficit_loss"] * averaged_terms["boundary_deficit_loss"]
            + coefficients["boundary_gap_floor_loss"] * averaged_terms["boundary_gap_floor_loss"]
            + coefficients["normal_retention_hinge"] * averaged_terms["normal_retention_hinge"]
            + coefficients["normal_anchor_mse"] * averaged_terms["normal_anchor_mse"]
            + coefficients["intervention_anchor_mse"] * averaged_terms["intervention_anchor_mse"]
            + coefficients["target_action_loss"] * averaged_terms["target_action_loss"]
            + coefficients["rejected_wrong_action_anchor"] * averaged_terms["rejected_wrong_action_anchor"]
            + coefficients["rejected_wrong_separation_floor"] * averaged_terms["rejected_wrong_separation_floor"]
            + coefficients["rejected_wrong_direction_anchor"] * averaged_terms["rejected_wrong_direction_anchor"]
            + coefficients["allowed_parameter_anchor"] * parameter_anchor_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                **{name: float(value.detach().item()) for name, value in averaged_terms.items()},
                "allowed_parameter_anchor": float(parameter_anchor_loss.detach().item()),
            }
        )
    return history


def classify_rejected_branch_retention_probe(
    *,
    forbidden_parameter_changed: bool,
    actor_mean_changed: bool,
    fusion_changed: bool,
    reconstruction_success_rate: float,
    active_rejected_rows: int,
    expected_active_rejected_rows: int,
    metadata_missing_rows: int,
    missing_target_keys: int,
    exact_candidate_count: int,
    m267_preflight_pass_count: int,
    candidate_count: int,
    any_tail_lift: bool,
    any_m267_preflight_pass: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(forbidden_parameter_changed) or bool(ppo_used) or bool(promoted):
        return "controlled_fusion_rejected_branch_retention_contract_artifact"
    if int(missing_target_keys) > 0:
        return "controlled_fusion_rejected_branch_retention_target_join_blocked"
    if (
        float(reconstruction_success_rate) < 0.98
        or int(metadata_missing_rows) > 0
        or int(active_rejected_rows) < int(expected_active_rejected_rows)
    ):
        return "controlled_fusion_rejected_branch_retention_reconstruction_blocked"
    if not bool(actor_mean_changed) or not bool(fusion_changed):
        return "controlled_fusion_rejected_branch_retention_no_surface_update"
    if int(candidate_count) > 0:
        return "controlled_fusion_rejected_branch_retention_candidate"
    if int(exact_candidate_count) > 0 and int(m267_preflight_pass_count) == 0:
        return "controlled_fusion_rejected_branch_retention_preflight_failure"
    if bool(any_m267_preflight_pass) and int(exact_candidate_count) == 0:
        return "controlled_fusion_rejected_branch_retention_objective_conflict"
    if bool(any_tail_lift):
        return "controlled_fusion_rejected_branch_retention_trust_region_conflict"
    return "controlled_fusion_rejected_branch_retention_no_candidate"


def _preflight_failed_active_rows(run_dir: Path, candidate_policy: str, active_row_ids: tuple[int, ...]) -> list[int]:
    rows_path = run_dir / "boundary_replay_rows.csv"
    if not rows_path.exists():
        return list(active_row_ids)
    frame = pd.read_csv(rows_path)
    candidate = frame[frame["policy"].astype(str).eq(str(candidate_policy))].copy()
    failed: list[int] = []
    for row_id in active_row_ids:
        row = candidate[candidate["row_id"].astype(int).eq(int(row_id))]
        if row.empty or bool(row.iloc[0].get("wrong_history_success", True)) or not bool(row.iloc[0].get("normal_success", False)):
            failed.append(int(row_id))
    return failed


def run_m267_preflight_for_alphas(
    *,
    checkpoint_data: dict[str, Any],
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    base_checkpoint_path: Path,
    corpus_csv: Path,
    env_config_path: Path,
    alphas: tuple[float, ...],
    active_row_ids: tuple[int, ...],
    run_dir: Path,
    device: str,
) -> list[dict[str, Any]]:
    preflight_rows: list[dict[str, Any]] = []
    checkpoint_dir = run_dir / "preflight_checkpoints"
    for alpha in alphas:
        alpha_text = str(float(alpha)).replace(".", "_")
        candidate_path = checkpoint_dir / f"alpha_{alpha_text}.pt"
        state = {
            name: tensor.detach().cpu()
            for name, tensor in {
                key: base_state[key] + float(alpha) * (raw_state[key] - base_state[key])
                if key.startswith(("actor_mean.", "response_context_fusion.0."))
                else base_state[key].clone()
                for key in base_state
            }.items()
        }
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=state,
            destination=candidate_path,
            objective=f"controlled_fusion_rejected_branch_retention_alpha_{float(alpha):.4f}",
        )
        candidate_label = f"candidate_a{alpha_text}"
        gate_dir = run_dir / "m267_preflight" / f"alpha_{alpha_text}"
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=(
                CheckpointSpec(label="m399_base", path=base_checkpoint_path),
                CheckpointSpec(label=candidate_label, path=candidate_path),
            ),
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=60,
            baseline_policy="m399_base",
            candidate_policy=candidate_label,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        failed_active_rows = _preflight_failed_active_rows(gate_dir, candidate_label, active_row_ids)
        preflight_rows.append(
            {
                "alpha": float(alpha),
                "checkpoint": str(candidate_path),
                "run_dir": str(gate_dir),
                "gate_pass": bool(summary["gate_pass"]) and not failed_active_rows,
                "active_rows_pass": not failed_active_rows,
                "failed_active_rows": " ".join(str(row_id) for row_id in failed_active_rows),
                "rows": int(summary["rows"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "normal_success_delta": float(summary["normal_success_delta"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
            }
        )
    return preflight_rows


def run_rejected_branch_retention_probe(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    m267_corpus_path: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    lr: float,
    train_alphas: tuple[float, ...] = DEFAULT_TRAIN_ALPHAS,
    alphas: tuple[float, ...] = DEFAULT_REPAIR_ALPHAS,
    active_row_ids: tuple[int, ...] = DEFAULT_ACTIVE_ROW_IDS,
    loss_coefficients: dict[str, float] | None = None,
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
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples, meta_rows, rejected_rows = _load_trainable_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    rejected_samples, rejected_meta_rows, rejected_sample_rejects = load_rejected_branch_samples(
        model=model,
        corpus_csv=m267_corpus_path,
        env_config_path=env_config_path,
        active_row_ids=active_row_ids,
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
            train_rows = train_rejected_branch_retention_objective(
                model,
                samples,
                rejected_samples,
                target_mask=target_mask,
                low_tail_mask=low_tail_mask,
                target_actions=target_actions,
                target_weights=target_weights,
                base_state=base_state,
                epochs=epochs,
                seed=seed,
                lr=lr,
                train_alphas=train_alphas,
                loss_coefficients=loss_coefficients,
            )
            raw_state = _clone_state_dict(model)
            m912_summary = read_json(m912_summary_path)
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
    checkpoint_dir = run_dir / "checkpoints"
    if len(meta_rows) > 0 and not missing_target_keys:
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=raw_state,
            destination=checkpoint_dir / "raw_rejected_branch_retention_update.pt",
            objective="controlled_fusion_rejected_branch_retention_raw",
        )
    preflight_rows = (
        run_m267_preflight_for_alphas(
            checkpoint_data=checkpoint_data,
            base_state=base_state,
            raw_state=raw_state,
            base_checkpoint_path=checkpoint_path,
            corpus_csv=m267_corpus_path,
            env_config_path=env_config_path,
            alphas=alphas,
            active_row_ids=active_row_ids,
            run_dir=run_dir,
            device=device,
        )
        if len(meta_rows) > 0 and not missing_target_keys
        else []
    )
    preflight_pass_alphas = {float(row["alpha"]) for row in preflight_rows if bool(row["gate_pass"])}
    candidate_rows = [
        row for row in alpha_rows if bool(row.get("exact_probe_candidate", False)) and float(row.get("alpha")) in preflight_pass_alphas
    ]
    exact_candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    tail_rows = [row for row in alpha_rows if bool(row.get("tail_lift_pass", False))]
    normal_tail_rows = [
        row for row in alpha_rows if bool(row.get("tail_lift_pass", False)) and bool(row.get("normal_retention_pass", False))
    ]
    low_tail_effect_rows = [row for row in alpha_rows if bool(row.get("low_tail_effect_candidate", False))]
    target_tolerance_rows = [row for row in alpha_rows if bool(row.get("target_tolerance_candidate", False))]
    normal_safe_trend_rows = [row for row in alpha_rows if bool(row.get("normal_safe_low_tail_trend", False))]
    m912_summary = read_json(m912_summary_path)
    boundary_near_miss_rows = [
        row
        for row in alpha_rows
        if is_boundary_near_miss_row(
            row,
            near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
            near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
            near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
        )
    ]
    forbidden_changed = bool(base_checksums["forbidden"] != raw_checksums["forbidden"])
    result_class = classify_rejected_branch_retention_probe(
        forbidden_parameter_changed=forbidden_changed,
        actor_mean_changed=bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"]),
        fusion_changed=bool(base_checksums["fusion"] != raw_checksums["fusion"]),
        reconstruction_success_rate=reconstruction_rate,
        active_rejected_rows=len(rejected_meta_rows),
        expected_active_rejected_rows=len(active_row_ids),
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        exact_candidate_count=len(exact_candidate_rows),
        m267_preflight_pass_count=len(preflight_pass_alphas),
        candidate_count=len(candidate_rows),
        any_tail_lift=bool(tail_rows),
        any_m267_preflight_pass=bool(preflight_pass_alphas),
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "target_weight_rows.csv", weight_rows)
    write_csv_rows(run_dir / "active_rejected_branch_rows.csv", rejected_meta_rows)
    write_csv_rows(run_dir / "m267_preflight_summary.csv", preflight_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [
            *rejected_rows,
            *rejected_sample_rejects,
            *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys)),
        ],
    )
    summary = {
        "run_type": "public_base_controlled_fusion_rejected_branch_retention_probe",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "m267_corpus": m267_corpus_path,
        "active_row_ids": list(active_row_ids),
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "active_rejected_rows": int(len(rejected_meta_rows)),
        "expected_active_rejected_rows": int(len(active_row_ids)),
        "metadata_missing_rows": int(metadata_missing_rows),
        "target_rows_count": int(len(target_rows)),
        "joined_target_rows": int(sum(1 for row in weight_rows if bool(row.get("target_available", False)))),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(len(low_tail_rows)),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "train_alphas": [float(alpha) for alpha in train_alphas],
        "alphas": [float(alpha) for alpha in alphas],
        "loss_coefficients": dict(DEFAULT_LOSS_COEFFICIENTS if loss_coefficients is None else loss_coefficients),
        "exact_candidate_alpha_count": int(len(exact_candidate_rows)),
        "exact_candidate_alphas": [float(row.get("alpha")) for row in exact_candidate_rows],
        "m267_preflight_pass_alpha_count": int(len(preflight_pass_alphas)),
        "m267_preflight_pass_alphas": sorted(float(alpha) for alpha in preflight_pass_alphas),
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "strict_candidate_count": int(len(candidate_rows)),
        "low_tail_effect_candidate_count": int(len(low_tail_effect_rows)),
        "target_tolerance_candidate_count": int(len(target_tolerance_rows)),
        "normal_safe_low_tail_trend_count": int(len(normal_safe_trend_rows)),
        "boundary_near_miss_count": int(len(boundary_near_miss_rows)),
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
        "m267_preflight_used": bool(preflight_rows),
        "m880_exact_used": False,
        "replay_used": bool(preflight_rows),
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "target_weight_rows_csv": run_dir / "target_weight_rows.csv",
        "active_rejected_branch_rows_csv": run_dir / "active_rejected_branch_rows.csv",
        "m267_preflight_summary_csv": run_dir / "m267_preflight_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled-fusion rejected-branch retention probe.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--target-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--seed", type=int, default=9490)
    parser.add_argument("--lr", type=float, default=5e-4)
    parser.add_argument("--train-alphas", type=_parse_float_list, default=DEFAULT_TRAIN_ALPHAS)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_REPAIR_ALPHAS)
    parser.add_argument("--active-row-ids", type=lambda raw: tuple(int(item) for item in raw.split(",") if item), default=DEFAULT_ACTIVE_ROW_IDS)
    parser.add_argument("--boundary-deficit-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["boundary_deficit_loss"])
    parser.add_argument("--boundary-gap-floor-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["boundary_gap_floor_loss"])
    parser.add_argument("--normal-retention-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["normal_retention_hinge"])
    parser.add_argument("--normal-anchor-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["normal_anchor_mse"])
    parser.add_argument("--intervention-anchor-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["intervention_anchor_mse"])
    parser.add_argument("--target-action-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["target_action_loss"])
    parser.add_argument(
        "--rejected-wrong-action-anchor-coef",
        type=float,
        default=DEFAULT_LOSS_COEFFICIENTS["rejected_wrong_action_anchor"],
    )
    parser.add_argument(
        "--rejected-wrong-separation-coef",
        type=float,
        default=DEFAULT_LOSS_COEFFICIENTS["rejected_wrong_separation_floor"],
    )
    parser.add_argument(
        "--rejected-wrong-direction-coef",
        type=float,
        default=DEFAULT_LOSS_COEFFICIENTS["rejected_wrong_direction_anchor"],
    )
    parser.add_argument("--parameter-anchor-coef", type=float, default=DEFAULT_LOSS_COEFFICIENTS["allowed_parameter_anchor"])
    args = parser.parse_args()
    loss_coefficients = {
        "boundary_deficit_loss": float(args.boundary_deficit_coef),
        "boundary_gap_floor_loss": float(args.boundary_gap_floor_coef),
        "normal_retention_hinge": float(args.normal_retention_coef),
        "normal_anchor_mse": float(args.normal_anchor_coef),
        "intervention_anchor_mse": float(args.intervention_anchor_coef),
        "target_action_loss": float(args.target_action_coef),
        "rejected_wrong_action_anchor": float(args.rejected_wrong_action_anchor_coef),
        "rejected_wrong_separation_floor": float(args.rejected_wrong_separation_coef),
        "rejected_wrong_direction_anchor": float(args.rejected_wrong_direction_coef),
        "allowed_parameter_anchor": float(args.parameter_anchor_coef),
    }
    summary = run_rejected_branch_retention_probe(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        m267_corpus_path=args.m267_corpus,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        epochs=args.epochs,
        seed=args.seed,
        lr=args.lr,
        train_alphas=tuple(args.train_alphas),
        alphas=tuple(args.alphas),
        active_row_ids=tuple(args.active_row_ids),
        loss_coefficients=loss_coefficients,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
