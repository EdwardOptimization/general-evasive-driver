"""Frozen-M399 residual-head probe using regenerated public-base targets."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.public_base_target_regeneration import _as_float, _key
from autodrift.public_base_tail_weighted_residual_probe import (
    DEFAULT_ALPHAS,
    DEFICIT_LIFT_TARGET,
    LOW_TAIL_DEFICIT_THRESHOLD,
    LOW_TAIL_FRACTION_LIFT_TARGET,
    LOW_TAIL_GAP_THRESHOLD,
    P10_LIFT_TARGET,
    _mean,
    _percentile,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import (
    ResidualHead,
    _load_probe_samples,
    _metadata_missing,
    _parse_float_list,
    _read_csv_rows,
)


STRICT_TARGET_WEIGHT = 2.0
NEAR_TAIL_TARGET_WEIGHT = 0.75


def target_weight_vector(
    *,
    meta_rows: list[dict[str, Any]],
    target_rows: list[dict[str, str]],
    low_tail_rows: list[dict[str, str]],
    normal_actions: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, list[dict[str, Any]], set[tuple[str, str, str, str]]]:
    target_by_key = {_key(row): row for row in target_rows}
    low_tail_keys = {_key(row) for row in low_tail_rows}
    meta_keys = {_key(row) for row in meta_rows}
    missing_target_keys = set(target_by_key) - meta_keys
    target_mask: list[bool] = []
    low_tail_mask: list[bool] = []
    target_actions: list[list[float]] = []
    weights: list[float] = []
    weight_rows: list[dict[str, Any]] = []
    for index, meta in enumerate(meta_rows):
        key = _key(meta)
        target = target_by_key.get(key)
        low_tail = key in low_tail_keys
        if target is None:
            base_action = normal_actions[index].detach().cpu().numpy()
            target_mask.append(False)
            target_actions.append([float(base_action[0]), float(base_action[1]), float(base_action[2])])
            weights.append(0.0)
            source_label = ""
        else:
            target_mask.append(True)
            source_label = str(target.get("source_label", "near_tail_coverage"))
            target_actions.append(
                [
                    _as_float(target.get("target_steer")),
                    _as_float(target.get("target_throttle")),
                    _as_float(target.get("target_brake")),
                ]
            )
            weights.append(STRICT_TARGET_WEIGHT if source_label == "strict_low_tail" else NEAR_TAIL_TARGET_WEIGHT)
        low_tail_mask.append(low_tail)
        weight_rows.append(
            {
                **{name: meta.get(name, "") for name in ("contrast_group_id", "source_index", "variant", "horizon")},
                "target_available": target is not None,
                "low_tail": low_tail,
                "source_label": source_label,
                "target_weight": weights[-1],
            }
        )
    device = normal_actions.device
    return (
        torch.as_tensor(target_mask, dtype=torch.bool, device=device),
        torch.as_tensor(low_tail_mask, dtype=torch.bool, device=device),
        torch.as_tensor(target_actions, dtype=torch.float32, device=device),
        torch.as_tensor(weights, dtype=torch.float32, device=device),
        weight_rows,
        missing_target_keys,
    )


def train_regenerated_target_residual_head(
    samples: dict[str, torch.Tensor],
    *,
    target_mask: torch.Tensor,
    low_tail_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_weights: torch.Tensor,
    epochs: int,
    seed: int,
    lr: float,
) -> tuple[ResidualHead, list[dict[str, Any]]]:
    torch.manual_seed(int(seed))
    feature_dim = int(samples["normal_features"].shape[1])
    head = ResidualHead(feature_dim=feature_dim)
    optimizer = torch.optim.Adam(head.parameters(), lr=float(lr))
    history: list[dict[str, Any]] = []
    normal_features = samples["normal_features"]
    intervention_features = samples["intervention_features"]
    normal_actions = samples["normal_actions"]
    intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        normal_delta = head(normal_features)
        intervention_delta = head(intervention_features)
        adjusted_normal = torch.clamp(normal_actions + normal_delta, -1.0, 1.0)
        adjusted_intervention = torch.clamp(intervention_actions + intervention_delta, -1.0, 1.0)
        normal_zero_loss = normal_delta.pow(2).mean()
        intervention_anchor_loss = intervention_delta.pow(2).mean()
        if bool(target_mask.any()):
            target_error = torch.mean((adjusted_normal[target_mask] - target_actions[target_mask]).pow(2), dim=-1)
            target_loss = (target_weights[target_mask] * target_error).sum() / torch.clamp(
                target_weights[target_mask].sum(), min=1.0
            )
        else:
            target_loss = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1)
        gap_deficit_loss = torch.relu(target_gaps - gap).pow(2).mean()
        if bool(low_tail_mask.any()):
            low_tail_floor_loss = torch.relu(float(LOW_TAIL_GAP_THRESHOLD) - gap[low_tail_mask]).pow(2).mean()
        else:
            low_tail_floor_loss = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        loss = (
            target_loss
            + 3.0 * normal_zero_loss
            + gap_deficit_loss
            + low_tail_floor_loss
            + 0.25 * intervention_anchor_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "target_loss": float(target_loss.detach().item()),
                "normal_zero_loss": float(normal_zero_loss.detach().item()),
                "gap_deficit_loss": float(gap_deficit_loss.detach().item()),
                "low_tail_floor_loss": float(low_tail_floor_loss.detach().item()),
                "intervention_anchor_loss": float(intervention_anchor_loss.detach().item()),
                "gap_mean": float(gap.detach().mean().item()),
            }
        )
    return head, history


def regenerated_alpha_metrics(
    *,
    samples: dict[str, torch.Tensor],
    meta_rows: list[dict[str, Any]],
    head: ResidualHead,
    alphas: tuple[float, ...],
    target_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_rows: list[dict[str, str]],
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    near_base_low_tail_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_by_key = {_key(row): row for row in target_rows}
    with torch.no_grad():
        normal_delta = head(samples["normal_features"])
        intervention_delta = head(samples["intervention_features"])
    alpha_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    normal_actions = samples["normal_actions"]
    intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    baseline_target_mse = torch.mean((normal_actions[target_mask] - target_actions[target_mask]).pow(2), dim=-1)
    baseline_target_mse_mean = float(baseline_target_mse.mean().detach().item()) if bool(target_mask.any()) else 0.0
    target_source_labels = [str(target_by_key.get(_key(meta), {}).get("source_label", "")) for meta in meta_rows]
    strict_mask_np = np.asarray([label == "strict_low_tail" for label in target_source_labels], dtype=bool)
    near_mask_np = np.asarray([label == "near_tail_coverage" for label in target_source_labels], dtype=bool)
    target_mask_np = target_mask.detach().cpu().numpy().astype(bool)
    for alpha in alphas:
        alpha_value = float(alpha)
        adjusted_normal = torch.clamp(normal_actions + alpha_value * normal_delta, -1.0, 1.0)
        adjusted_intervention = torch.clamp(intervention_actions + alpha_value * intervention_delta, -1.0, 1.0)
        normal_drift = torch.linalg.norm(adjusted_normal - normal_actions, dim=-1).cpu().numpy()
        normal_anchor_mse = torch.mean((adjusted_normal - normal_actions).pow(2), dim=-1).cpu().numpy()
        gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1).cpu().numpy()
        target = target_gaps.cpu().numpy()
        gap_deficit = np.maximum(0.0, target - gap)
        low_tail_after = (gap < float(LOW_TAIL_GAP_THRESHOLD)) | (gap_deficit > float(LOW_TAIL_DEFICIT_THRESHOLD))
        target_mse_all = torch.mean((adjusted_normal - target_actions).pow(2), dim=-1).cpu().numpy()
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
        row["target_loss_pass"] = bool(row["target_action_mse_mean"] < baseline_target_mse_mean)
        row["exact_probe_candidate"] = bool(row["normal_retention_pass"] and row["tail_lift_pass"] and row["target_loss_pass"])
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
    return alpha_rows, objective_rows


def classify_regenerated_target_residual_probe(
    *,
    actor_backbone_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_keys: int,
    candidate_count: int,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_backbone_changed) or bool(ppo_used) or bool(promoted):
        return "public_base_regenerated_target_probe_contract_artifact"
    if int(missing_target_keys) > 0:
        return "public_base_regenerated_target_probe_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_regenerated_target_probe_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "public_base_regenerated_target_probe_candidate"
    return "public_base_regenerated_target_probe_no_candidate"


def run_regenerated_target_residual_probe(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    regenerated_target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    m909_objective_rows_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
    lr: float = 3e-3,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    checksum_before = model_parameter_checksum(model)
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(regenerated_target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    m912_summary = read_json(m912_summary_path)
    m909_objective_rows = _read_csv_rows(m909_objective_rows_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples, meta_rows, rejected_rows = _load_probe_samples(
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
        low_tail_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        target_actions = torch.empty((0, 3), dtype=torch.float32, device=resolved_device)
        target_weights = torch.empty((0,), dtype=torch.float32, device=resolved_device)
        weight_rows: list[dict[str, Any]] = []
        missing_target_keys: set[tuple[str, str, str, str]] = {_key(row) for row in target_rows}
        train_rows: list[dict[str, Any]] = []
        alpha_rows: list[dict[str, Any]] = []
        objective_rows: list[dict[str, Any]] = []
        residual_parameter_count = 0
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
            residual_parameter_count = 0
        else:
            head, train_rows = train_regenerated_target_residual_head(
                samples=samples,
                target_mask=target_mask,
                low_tail_mask=low_tail_mask,
                target_actions=target_actions,
                target_weights=target_weights,
                epochs=epochs,
                seed=seed,
                lr=lr,
            )
            residual_parameter_count = int(sum(parameter.numel() for parameter in head.parameters()))
            alpha_rows, objective_rows = regenerated_alpha_metrics(
                samples=samples,
                meta_rows=meta_rows,
                head=head,
                alphas=alphas,
                target_mask=target_mask,
                target_actions=target_actions,
                target_rows=target_rows,
                near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
            )
            torch.save(
                {
                    "state_dict": head.state_dict(),
                    "feature_dim": int(samples["normal_features"].shape[1]),
                    "max_residual": float(head.max_residual),
                    "seed": int(seed),
                    "objective": "public_base_regenerated_target_residual_probe",
                },
                run_dir / "residual_head.pt",
            )
    checksum_after = model_parameter_checksum(model)
    candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_target_row = min(alpha_rows, key=lambda row: float(row.get("target_action_mse_mean", float("inf"))), default={})
    result_class = classify_regenerated_target_residual_probe(
        actor_backbone_changed=bool(checksum_before != checksum_after),
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        candidate_count=len(candidate_rows),
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "target_weight_rows.csv", weight_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [*rejected_rows, *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys))],
    )
    target_count = int(target_mask.sum().item()) if len(meta_rows) else 0
    strict_target_count = sum(1 for row in target_rows if str(row.get("source_label", "")) == "strict_low_tail")
    near_tail_target_count = sum(1 for row in target_rows if str(row.get("source_label", "")) == "near_tail_coverage")
    summary = {
        "run_type": "public_base_regenerated_target_residual_probe",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "regenerated_target_rows": regenerated_target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "m909_objective_rows": m909_objective_rows_path,
        "m909_objective_rows_count": int(len(m909_objective_rows)),
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "rejected_rows": int(len(rejected_rows) + len(missing_target_keys)),
        "missing_target_keys": int(len(missing_target_keys)),
        "regenerated_target_rows_count": int(len(target_rows)),
        "joined_target_rows": target_count,
        "strict_target_rows": int(strict_target_count),
        "near_tail_target_rows": int(near_tail_target_count),
        "residual_parameter_count": int(residual_parameter_count),
        "epochs": int(epochs),
        "seed": int(seed),
        "alphas": [float(alpha) for alpha in alphas],
        "near_base_gap_p10": float(m912_summary["near_base_gap_p10"]),
        "near_base_gap_deficit_mean": float(m912_summary["near_base_gap_deficit_mean"]),
        "near_base_low_tail_fraction": float(m912_summary["low_tail_fraction"]),
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "best_candidate": best_candidate,
        "best_target_alpha": best_target_row,
        "actor_backbone_changed": bool(checksum_before != checksum_after),
        "base_actor_checksum_before": checksum_before,
        "base_actor_checksum_after": checksum_after,
        "training_started": bool(len(meta_rows) > 0 and not missing_target_keys),
        "optimizer_started": bool(len(meta_rows) > 0 and not missing_target_keys),
        "residual_only_training": bool(len(meta_rows) > 0 and not missing_target_keys),
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
        "residual_head_pt": run_dir / "residual_head.pt",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M399 regenerated-target residual-head probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--regenerated-target-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--m909-objective-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9210)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--lr", type=float, default=3e-3)
    args = parser.parse_args()
    summary = run_regenerated_target_residual_probe(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        regenerated_target_rows_path=args.regenerated_target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        m909_objective_rows_path=args.m909_objective_rows,
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
