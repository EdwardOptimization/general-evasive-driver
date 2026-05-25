"""Boundary-alpha controlled-fusion objective probe for the M399 public base."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.public_base_controlled_fusion_raw_direction_feasibility import DEFAULT_BOUNDARY_ALPHAS
from autodrift.public_base_controlled_fusion_surface_probe import (
    controlled_surface_checksums,
    evaluate_controlled_fusion_alphas,
    set_controlled_fusion_trainable_only,
    _allowed_parameter_anchor_loss,
    _clone_state_dict,
    _load_trainable_samples,
)
from autodrift.public_base_policy_head_trust_region_probe import (
    TARGET_MSE_TOLERANCE,
    _save_checkpoint,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.public_base_tail_weighted_residual_probe import (
    DEFICIT_LIFT_TARGET,
    LOW_TAIL_FRACTION_LIFT_TARGET,
    P10_LIFT_TARGET,
)
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _parse_float_list, _read_csv_rows


DEFAULT_TRAIN_ALPHAS = (0.125, 0.150, 0.175)
BOUNDARY_DEFICIT_TARGET = 0.01475
BOUNDARY_GAP_FLOOR = 0.00950
BOUNDARY_NEAR_MISS_DEFICIT_LIFT = 0.0015
NORMAL_DRIFT_HINGE = 0.00280
NORMAL_ROW_MSE_HINGE = 0.00000350

LOSS_COEFFICIENTS = {
    "boundary_deficit_loss": 12.0,
    "boundary_gap_floor_loss": 10.0,
    "normal_retention_hinge": 10.0,
    "normal_anchor_mse": 2.0,
    "intervention_anchor_mse": 0.5,
    "target_action_loss": 0.05,
    "allowed_parameter_anchor": 0.001,
}


def _device_base_tensor(base_state: dict[str, torch.Tensor], name: str, device: torch.device) -> torch.Tensor:
    return base_state[name].to(device=device, dtype=torch.float32)


def _effective_linear_parameters(
    *,
    model: ActorCritic,
    base_state: dict[str, torch.Tensor],
    layer_name: str,
    alpha: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    device = next(model.parameters()).device
    if layer_name == "response_context_fusion.0":
        assert model.response_context_fusion is not None
        layer = model.response_context_fusion[0]
    elif layer_name == "actor_mean":
        layer = model.actor_mean
    else:
        raise ValueError(f"unsupported controlled-fusion layer: {layer_name}")
    base_weight = _device_base_tensor(base_state, f"{layer_name}.weight", device)
    base_bias = _device_base_tensor(base_state, f"{layer_name}.bias", device)
    alpha_value = float(alpha)
    weight = base_weight + alpha_value * (layer.weight - base_weight)
    bias = base_bias + alpha_value * (layer.bias - base_bias)
    return weight, bias


def _fusion_input(model: ActorCritic, observations: torch.Tensor, hidden: torch.Tensor) -> torch.Tensor:
    if model.privileged_encoder is not None or model.privileged_residual is not None:
        raise RuntimeError("M940 boundary objective is only registered for the non-privileged P0 actor")
    assert model.response_encoder is not None
    assert model.context_encoder is not None
    assert model.online_gru_cell is not None
    response_indices = torch.as_tensor(model.response_feature_indices, dtype=torch.long, device=observations.device)
    context_indices = torch.as_tensor(model.context_feature_indices, dtype=torch.long, device=observations.device)
    response_obs = observations.index_select(dim=-1, index=response_indices)
    context_obs = observations.index_select(dim=-1, index=context_indices)
    response_encoded = model.response_encoder(response_obs)
    context_encoded = model.context_encoder(context_obs)
    next_hidden = model.online_gru_cell(response_encoded, hidden)
    return torch.cat([next_hidden, context_encoded, next_hidden * context_encoded], dim=-1)


def _interpolated_actions(
    model: ActorCritic,
    observations: torch.Tensor,
    hidden: torch.Tensor,
    *,
    base_state: dict[str, torch.Tensor],
    alpha: float,
) -> torch.Tensor:
    fusion_weight, fusion_bias = _effective_linear_parameters(
        model=model,
        base_state=base_state,
        layer_name="response_context_fusion.0",
        alpha=alpha,
    )
    actor_weight, actor_bias = _effective_linear_parameters(
        model=model,
        base_state=base_state,
        layer_name="actor_mean",
        alpha=alpha,
    )
    fused = torch.tanh(F.linear(_fusion_input(model, observations, hidden), fusion_weight, fusion_bias))
    return torch.tanh(F.linear(fused, actor_weight, actor_bias))


def train_controlled_fusion_boundary_objective(
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
    train_alphas: tuple[float, ...] = DEFAULT_TRAIN_ALPHAS,
) -> list[dict[str, Any]]:
    torch.manual_seed(int(seed))
    device = next(model.parameters()).device
    optimizer = torch.optim.Adam([parameter for parameter in model.parameters() if parameter.requires_grad], lr=float(lr))
    history: list[dict[str, Any]] = []
    base_normal_actions = samples["normal_actions"]
    base_intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    if not train_alphas:
        raise ValueError("train_alphas must contain at least one boundary alpha")

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
                boundary_deficit_loss = torch.relu(low_deficit - float(BOUNDARY_DEFICIT_TARGET)).pow(2).mean()
                boundary_gap_floor_loss = torch.relu(float(BOUNDARY_GAP_FLOOR) - low_gap).pow(2).mean()
            else:
                boundary_deficit_loss = torch.zeros((), dtype=torch.float32, device=device)
                boundary_gap_floor_loss = torch.zeros((), dtype=torch.float32, device=device)
            normal_delta = normal_actions - base_normal_actions
            normal_drift = torch.linalg.norm(normal_delta, dim=-1)
            normal_row_mse = torch.mean(normal_delta.pow(2), dim=-1)
            normal_retention_hinge = (
                torch.relu(normal_drift - float(NORMAL_DRIFT_HINGE)).pow(2).mean()
                + torch.relu(normal_row_mse - float(NORMAL_ROW_MSE_HINGE)).pow(2).mean()
            )
            normal_anchor_mse = torch.mean(normal_delta.pow(2))
            intervention_anchor_mse = torch.mean((intervention_actions - base_intervention_actions).pow(2))
            term_values["boundary_deficit_loss"].append(boundary_deficit_loss)
            term_values["boundary_gap_floor_loss"].append(boundary_gap_floor_loss)
            term_values["normal_retention_hinge"].append(normal_retention_hinge)
            term_values["normal_anchor_mse"].append(normal_anchor_mse)
            term_values["intervention_anchor_mse"].append(intervention_anchor_mse)
            term_values["target_action_loss"].append(target_loss)
            term_values["gap_mean"].append(gap.mean())

        averaged_terms = {
            name: torch.stack(values).mean() if values else torch.zeros((), dtype=torch.float32, device=device)
            for name, values in term_values.items()
        }
        parameter_anchor_loss = _allowed_parameter_anchor_loss(model, base_state, device)
        loss = (
            LOSS_COEFFICIENTS["boundary_deficit_loss"] * averaged_terms["boundary_deficit_loss"]
            + LOSS_COEFFICIENTS["boundary_gap_floor_loss"] * averaged_terms["boundary_gap_floor_loss"]
            + LOSS_COEFFICIENTS["normal_retention_hinge"] * averaged_terms["normal_retention_hinge"]
            + LOSS_COEFFICIENTS["normal_anchor_mse"] * averaged_terms["normal_anchor_mse"]
            + LOSS_COEFFICIENTS["intervention_anchor_mse"] * averaged_terms["intervention_anchor_mse"]
            + LOSS_COEFFICIENTS["target_action_loss"] * averaged_terms["target_action_loss"]
            + LOSS_COEFFICIENTS["allowed_parameter_anchor"] * parameter_anchor_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "boundary_deficit_loss": float(averaged_terms["boundary_deficit_loss"].detach().item()),
                "boundary_gap_floor_loss": float(averaged_terms["boundary_gap_floor_loss"].detach().item()),
                "normal_retention_hinge": float(averaged_terms["normal_retention_hinge"].detach().item()),
                "normal_anchor_mse": float(averaged_terms["normal_anchor_mse"].detach().item()),
                "intervention_anchor_mse": float(averaged_terms["intervention_anchor_mse"].detach().item()),
                "target_action_loss": float(averaged_terms["target_action_loss"].detach().item()),
                "allowed_parameter_anchor": float(parameter_anchor_loss.detach().item()),
                "gap_mean": float(averaged_terms["gap_mean"].detach().item()),
            }
        )
    return history


def is_boundary_near_miss_row(
    row: dict[str, Any],
    *,
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    near_base_low_tail_fraction: float,
) -> bool:
    return bool(
        row.get("normal_retention_pass", False)
        and float(row.get("normal_intervention_gap_p10", 0.0)) >= float(near_base_gap_p10) + P10_LIFT_TARGET
        and float(row.get("low_tail_fraction", 1.0))
        <= float(near_base_low_tail_fraction) - LOW_TAIL_FRACTION_LIFT_TARGET
        and float(row.get("gap_deficit_mean", 1.0))
        <= float(near_base_gap_deficit_mean) - BOUNDARY_NEAR_MISS_DEFICIT_LIFT
    )


def classify_controlled_fusion_boundary_objective_probe(
    *,
    forbidden_parameter_changed: bool,
    actor_mean_changed: bool,
    fusion_changed: bool,
    boundary_interpolation_used: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_keys: int,
    candidate_count: int,
    low_tail_effect_candidate_count: int,
    boundary_near_miss_count: int,
    any_tail_lift: bool,
    any_normal_retained_tail_lift: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(forbidden_parameter_changed) or not bool(boundary_interpolation_used) or bool(ppo_used) or bool(promoted):
        return "public_base_controlled_fusion_boundary_objective_contract_artifact"
    if int(missing_target_keys) > 0:
        return "public_base_controlled_fusion_boundary_objective_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_controlled_fusion_boundary_objective_reconstruction_blocked"
    if not bool(actor_mean_changed) or not bool(fusion_changed):
        return "public_base_controlled_fusion_boundary_objective_no_surface_update"
    if int(candidate_count) > 0:
        return "public_base_controlled_fusion_boundary_objective_candidate"
    if int(low_tail_effect_candidate_count) > 0 or bool(any_normal_retained_tail_lift):
        return "public_base_controlled_fusion_boundary_objective_target_conflict"
    if int(boundary_near_miss_count) > 0:
        return "public_base_controlled_fusion_boundary_objective_boundary_near_miss"
    if bool(any_tail_lift):
        return "public_base_controlled_fusion_boundary_objective_trust_region_conflict"
    return "public_base_controlled_fusion_boundary_objective_no_tail_lift"


def run_controlled_fusion_boundary_objective_probe(
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
    lr: float,
    train_alphas: tuple[float, ...] = DEFAULT_TRAIN_ALPHAS,
    alphas: tuple[float, ...] = DEFAULT_BOUNDARY_ALPHAS,
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
    missing_target_keys: set[tuple[str, str, str, str]]
    if len(meta_rows) == 0:
        target_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        target_actions = torch.empty((0, 3), dtype=torch.float32, device=resolved_device)
        weight_rows: list[dict[str, Any]] = []
        missing_target_keys = set()
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
            train_rows = train_controlled_fusion_boundary_objective(
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
                train_alphas=train_alphas,
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
    boundary_interpolation_used = bool(train_alphas)
    result_class = classify_controlled_fusion_boundary_objective_probe(
        forbidden_parameter_changed=forbidden_changed,
        actor_mean_changed=bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"]),
        fusion_changed=bool(base_checksums["fusion"] != raw_checksums["fusion"]),
        boundary_interpolation_used=boundary_interpolation_used,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        candidate_count=len(candidate_rows),
        low_tail_effect_candidate_count=len(low_tail_effect_rows),
        boundary_near_miss_count=len(boundary_near_miss_rows),
        any_tail_lift=bool(tail_rows),
        any_normal_retained_tail_lift=bool(normal_tail_rows),
        ppo_used=False,
        promoted=False,
    )
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_boundary_near_miss = boundary_near_miss_rows[0] if boundary_near_miss_rows else {}
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
            destination=checkpoint_dir / "raw_boundary_objective_update.pt",
            objective="public_base_controlled_fusion_boundary_objective_raw",
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
        "run_type": "public_base_controlled_fusion_boundary_objective_probe",
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
        "train_alphas": [float(alpha) for alpha in train_alphas],
        "alphas": [float(alpha) for alpha in alphas],
        "boundary_deficit_target": float(BOUNDARY_DEFICIT_TARGET),
        "boundary_gap_floor": float(BOUNDARY_GAP_FLOOR),
        "normal_drift_hinge": float(NORMAL_DRIFT_HINGE),
        "normal_row_mse_hinge": float(NORMAL_ROW_MSE_HINGE),
        "loss_coefficients": LOSS_COEFFICIENTS,
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "strict_candidate_count": int(len(candidate_rows)),
        "low_tail_effect_candidate_count": int(len(low_tail_effect_rows)),
        "target_tolerance_candidate_count": int(len(target_tolerance_rows)),
        "normal_safe_low_tail_trend_count": int(len(normal_safe_trend_rows)),
        "boundary_near_miss_count": int(len(boundary_near_miss_rows)),
        "low_tail_effect_candidate_alphas": [float(row.get("alpha")) for row in low_tail_effect_rows],
        "target_tolerance_candidate_alphas": [float(row.get("alpha")) for row in target_tolerance_rows],
        "normal_safe_low_tail_trend_alphas": [float(row.get("alpha")) for row in normal_safe_trend_rows],
        "boundary_near_miss_alphas": [float(row.get("alpha")) for row in boundary_near_miss_rows],
        "best_candidate": best_candidate,
        "best_boundary_near_miss_row": best_boundary_near_miss,
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
        "boundary_interpolation_used": boundary_interpolation_used,
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
    parser = argparse.ArgumentParser(description="Run boundary-alpha controlled-fusion public-base probe.")
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
    parser.add_argument("--seed", type=int, default=9400)
    parser.add_argument("--lr", type=float, default=5e-4)
    parser.add_argument("--train-alphas", type=_parse_float_list, default=DEFAULT_TRAIN_ALPHAS)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_BOUNDARY_ALPHAS)
    args = parser.parse_args()
    summary = run_controlled_fusion_boundary_objective_probe(
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
        lr=args.lr,
        train_alphas=tuple(args.train_alphas),
        alphas=tuple(args.alphas),
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
