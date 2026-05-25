"""Residual-only tail-weighted probe for M399 public-base low-tail rows."""

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
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import (
    ResidualHead,
    _load_probe_samples,
    _metadata_missing,
    _parse_float_list,
    _read_csv_rows,
)


DEFAULT_ALPHAS = (0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00)
LOW_TAIL_GAP_THRESHOLD = 0.021141
LOW_TAIL_DEFICIT_THRESHOLD = 0.02
P10_LIFT_TARGET = 0.004
DEFICIT_LIFT_TARGET = 0.002
LOW_TAIL_FRACTION_LIFT_TARGET = 0.05


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _mean(values: np.ndarray | list[float]) -> float:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def _percentile(values: np.ndarray | list[float], percentile: float) -> float:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    return float(np.percentile(arr, percentile)) if arr.size else float("nan")


def _key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("contrast_group_id", "")),
        str(row.get("source_index", "")),
        str(row.get("variant", "")),
        str(row.get("horizon", "")),
    )


def _near_base_deficit_map(rows: list[dict[str, str]], *, near_base_alpha: float) -> dict[tuple[str, str, str, str], float]:
    out: dict[tuple[str, str, str, str], float] = {}
    for row in rows:
        if math.isclose(_as_float(row.get("alpha")), float(near_base_alpha), rel_tol=0.0, abs_tol=1e-9):
            out[_key(row)] = max(_as_float(row.get("gap_deficit")), 0.0)
    return out


def _tail_weight(
    *,
    base_weight: float,
    low_tail: bool,
    deficit: float,
) -> float:
    deficit_bonus = float(np.clip(50.0 * max(float(deficit), 0.0), 0.0, 3.0))
    value = float(base_weight) * (1.0 + (4.0 if low_tail else 0.0) + deficit_bonus)
    return float(np.clip(value, 1.0, 8.0))


def tail_weight_vector(
    *,
    meta_rows: list[dict[str, Any]],
    base_weights: torch.Tensor,
    low_tail_rows: list[dict[str, str]],
    near_base_deficits: dict[tuple[str, str, str, str], float],
) -> tuple[torch.Tensor, torch.Tensor, list[dict[str, Any]], set[tuple[str, str, str, str]]]:
    low_tail_keys = {_key(row) for row in low_tail_rows}
    meta_keys = {_key(row) for row in meta_rows}
    missing_low_tail_keys = low_tail_keys - meta_keys
    weights: list[float] = []
    mask: list[bool] = []
    weight_rows: list[dict[str, Any]] = []
    for index, meta in enumerate(meta_rows):
        key = _key(meta)
        is_low_tail = key in low_tail_keys
        deficit = near_base_deficits.get(key, 0.0)
        weight = _tail_weight(
            base_weight=float(base_weights[index].detach().cpu().item()),
            low_tail=is_low_tail,
            deficit=deficit,
        )
        weights.append(weight)
        mask.append(is_low_tail)
        weight_rows.append(
            {
                **{name: meta.get(name, "") for name in ("contrast_group_id", "source_index", "variant", "horizon")},
                "low_tail": is_low_tail,
                "near_base_gap_deficit": deficit,
                "tail_weight": weight,
            }
        )
    return (
        torch.as_tensor(weights, dtype=torch.float32, device=base_weights.device),
        torch.as_tensor(mask, dtype=torch.bool, device=base_weights.device),
        weight_rows,
        missing_low_tail_keys,
    )


def train_tail_weighted_residual_head(
    samples: dict[str, torch.Tensor],
    *,
    tail_weights: torch.Tensor,
    low_tail_mask: torch.Tensor,
    epochs: int,
    seed: int,
    lr: float,
    floor_gap: float,
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
    hard_gaps = samples["hard_gaps"]
    hard_available = samples["hard_available"]
    low_tail_count = int(low_tail_mask.sum().item())
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        normal_delta = head(normal_features)
        intervention_delta = head(intervention_features)
        normal_zero_loss = normal_delta.pow(2).mean()
        adjusted_normal = normal_actions + normal_delta
        adjusted_intervention = intervention_actions + intervention_delta
        gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1)
        tail_gap_loss = (tail_weights * torch.relu(target_gaps - gap).pow(2)).sum() / torch.clamp(
            tail_weights.sum(), min=1.0
        )
        if low_tail_count > 0:
            low_tail_weights = tail_weights[low_tail_mask]
            low_tail_floor_loss = (
                low_tail_weights * torch.relu(float(floor_gap) - gap[low_tail_mask]).pow(2)
            ).sum() / torch.clamp(low_tail_weights.sum(), min=1.0)
        else:
            low_tail_floor_loss = torch.zeros((), dtype=torch.float32, device=gap.device)
        intervention_anchor_loss = intervention_delta.pow(2).mean()
        hard_terms = torch.relu(hard_gaps - gap + 0.005).pow(2) * hard_available
        hard_loss = hard_terms.sum() / torch.clamp(hard_available.sum(), min=1.0)
        loss = (
            3.0 * normal_zero_loss
            + tail_gap_loss
            + low_tail_floor_loss
            + 0.25 * intervention_anchor_loss
            + 0.10 * hard_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "normal_zero_loss": float(normal_zero_loss.detach().item()),
                "tail_gap_loss": float(tail_gap_loss.detach().item()),
                "low_tail_floor_loss": float(low_tail_floor_loss.detach().item()),
                "intervention_anchor_loss": float(intervention_anchor_loss.detach().item()),
                "hard_negative_loss": float(hard_loss.detach().item()),
                "gap_mean": float(gap.detach().mean().item()),
            }
        )
    return head, history


def tail_alpha_metrics(
    *,
    samples: dict[str, torch.Tensor],
    meta_rows: list[dict[str, Any]],
    head: ResidualHead,
    alphas: tuple[float, ...],
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    near_base_low_tail_fraction: float,
    low_tail_gap_threshold: float,
    low_tail_deficit_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with torch.no_grad():
        normal_delta = head(samples["normal_features"])
        intervention_delta = head(samples["intervention_features"])
    alpha_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    normal_actions = samples["normal_actions"]
    intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    for alpha in alphas:
        alpha_value = float(alpha)
        adjusted_normal = torch.clamp(normal_actions + alpha_value * normal_delta, -1.0, 1.0)
        adjusted_intervention = torch.clamp(intervention_actions + alpha_value * intervention_delta, -1.0, 1.0)
        normal_drift = torch.linalg.norm(adjusted_normal - normal_actions, dim=-1).cpu().numpy()
        normal_anchor_mse = torch.mean((adjusted_normal - normal_actions).pow(2), dim=-1).cpu().numpy()
        gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1).cpu().numpy()
        target = target_gaps.cpu().numpy()
        gap_deficit = np.maximum(0.0, target - gap)
        low_tail_after = (gap < float(low_tail_gap_threshold)) | (gap_deficit > float(low_tail_deficit_threshold))
        row = {
            "alpha": alpha_value,
            "sample_count": int(gap.shape[0]),
            "normal_anchor_mse_mean": _mean(normal_anchor_mse),
            "normal_anchor_mse_p95": _percentile(normal_anchor_mse, 95),
            "first_action_drift_from_base_mean": _mean(normal_drift),
            "first_action_drift_from_base_p95": _percentile(normal_drift, 95),
            "normal_intervention_gap_mean": _mean(gap),
            "normal_intervention_gap_p10": _percentile(gap, 10),
            "gap_deficit_mean": _mean(gap_deficit),
            "gap_deficit_p95": _percentile(gap_deficit, 95),
            "target_gap_mean": _mean(target),
            "low_tail_rows": int(np.sum(low_tail_after)),
            "low_tail_fraction": float(np.mean(low_tail_after.astype(np.float32))) if low_tail_after.size else 0.0,
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
        row["exact_probe_candidate"] = bool(row["normal_retention_pass"] and row["tail_lift_pass"])
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
                }
            )
    return alpha_rows, objective_rows


def classify_tail_weighted_probe(
    *,
    actor_backbone_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_low_tail_keys: int,
    candidate_count: int,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_backbone_changed) or bool(ppo_used) or bool(promoted):
        return "public_base_tail_weighted_probe_contract_artifact"
    if int(missing_low_tail_keys) > 0:
        return "public_base_tail_weighted_probe_low_tail_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_tail_weighted_probe_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "public_base_tail_weighted_probe_candidate"
    return "public_base_tail_weighted_probe_no_candidate"


def run_tail_weighted_residual_probe(
    *,
    checkpoint_path: Path,
    corpus_summary_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    low_tail_rows_path: Path,
    m912_summary_path: Path,
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
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    m909_rows = _read_csv_rows(m909_objective_rows_path)
    m912_summary = read_json(m912_summary_path)
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
    near_base_alpha = float(m912_summary.get("near_base_alpha", 0.02))
    near_base_deficits = _near_base_deficit_map(m909_rows, near_base_alpha=near_base_alpha)
    if len(meta_rows) == 0:
        tail_weights = torch.empty((0,), dtype=torch.float32, device=resolved_device)
        low_tail_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        weight_rows: list[dict[str, Any]] = []
        missing_low_tail_keys: set[tuple[str, str, str, str]] = {_key(row) for row in low_tail_rows}
        train_rows: list[dict[str, Any]] = []
        alpha_rows: list[dict[str, Any]] = []
        objective_rows: list[dict[str, Any]] = []
        residual_parameter_count = 0
    else:
        tail_weights, low_tail_mask, weight_rows, missing_low_tail_keys = tail_weight_vector(
            meta_rows=meta_rows,
            base_weights=samples["outcome_weights"].to(resolved_device),
            low_tail_rows=low_tail_rows,
            near_base_deficits=near_base_deficits,
        )
        if missing_low_tail_keys:
            train_rows = []
            alpha_rows = []
            objective_rows = []
            residual_parameter_count = 0
        else:
            head, train_rows = train_tail_weighted_residual_head(
                samples=samples,
                tail_weights=tail_weights,
                low_tail_mask=low_tail_mask,
                epochs=epochs,
                seed=seed,
                lr=lr,
                floor_gap=LOW_TAIL_GAP_THRESHOLD,
            )
            residual_parameter_count = int(sum(parameter.numel() for parameter in head.parameters()))
            alpha_rows, objective_rows = tail_alpha_metrics(
                samples=samples,
                meta_rows=meta_rows,
                head=head,
                alphas=alphas,
                near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
                low_tail_gap_threshold=LOW_TAIL_GAP_THRESHOLD,
                low_tail_deficit_threshold=LOW_TAIL_DEFICIT_THRESHOLD,
            )
            torch.save(
                {
                    "state_dict": head.state_dict(),
                    "feature_dim": int(samples["normal_features"].shape[1]),
                    "max_residual": float(head.max_residual),
                    "seed": int(seed),
                    "objective": "public_base_tail_weighted_residual_probe",
                },
                run_dir / "residual_head.pt",
            )
    checksum_after = model_parameter_checksum(model)
    candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_tail_row = min(alpha_rows, key=lambda row: float(row.get("low_tail_fraction", float("inf"))), default={})
    result_class = classify_tail_weighted_probe(
        actor_backbone_changed=bool(checksum_before != checksum_after),
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_low_tail_keys=len(missing_low_tail_keys),
        candidate_count=len(candidate_rows),
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "tail_weight_rows.csv", weight_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [*rejected_rows, *({"rejection_reason": "missing_low_tail_join", "key": str(key)} for key in sorted(missing_low_tail_keys))],
    )
    summary = {
        "run_type": "public_base_tail_weighted_residual_probe",
        "checkpoint": checkpoint_path,
        "corpus_summary": corpus_summary_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "low_tail_rows_input": low_tail_rows_path,
        "m912_summary": m912_summary_path,
        "m909_objective_rows": m909_objective_rows_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "rejected_rows": int(len(rejected_rows) + len(missing_low_tail_keys)),
        "missing_low_tail_keys": int(len(missing_low_tail_keys)),
        "residual_parameter_count": int(residual_parameter_count),
        "epochs": int(epochs),
        "seed": int(seed),
        "alphas": [float(alpha) for alpha in alphas],
        "near_base_alpha": near_base_alpha,
        "near_base_gap_p10": float(m912_summary["near_base_gap_p10"]),
        "near_base_gap_deficit_mean": float(m912_summary["near_base_gap_deficit_mean"]),
        "near_base_low_tail_fraction": float(m912_summary["low_tail_fraction"]),
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "best_candidate": best_candidate,
        "best_tail_alpha": best_tail_row,
        "actor_backbone_changed": bool(checksum_before != checksum_after),
        "base_actor_checksum_before": checksum_before,
        "base_actor_checksum_after": checksum_after,
        "training_started": bool(len(meta_rows) > 0 and not missing_low_tail_keys),
        "optimizer_started": bool(len(meta_rows) > 0 and not missing_low_tail_keys),
        "residual_only_training": bool(len(meta_rows) > 0 and not missing_low_tail_keys),
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "tail_weight_rows_csv": run_dir / "tail_weight_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "residual_head_pt": run_dir / "residual_head.pt",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M399 public-base tail-weighted residual probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus-summary", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--m909-objective-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9140)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--lr", type=float, default=3e-3)
    args = parser.parse_args()
    summary = run_tail_weighted_residual_probe(
        checkpoint_path=args.checkpoint,
        corpus_summary_path=args.corpus_summary,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        low_tail_rows_path=args.low_tail_rows,
        m912_summary_path=args.m912_summary,
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
