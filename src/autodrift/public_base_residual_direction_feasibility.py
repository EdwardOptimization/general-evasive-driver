"""No-training feasibility sweep over existing public-base residual directions."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
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
from autodrift.train_ppo import resolve_device
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_sequence_objective_probe import _load_probe_samples, _metadata_missing, _parse_float_list, _read_csv_rows


DEFAULT_MIX_WEIGHTS = tuple(float(round(index / 10.0, 2)) for index in range(11))
DEFAULT_FEASIBILITY_ALPHAS = (0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.50, 0.75, 1.00)


def evaluate_direction_grid(
    *,
    samples: dict[str, torch.Tensor],
    meta_rows: list[dict[str, Any]],
    delta921_normal: torch.Tensor,
    delta921_intervention: torch.Tensor,
    delta924_normal: torch.Tensor,
    delta924_intervention: torch.Tensor,
    mix_weights: tuple[float, ...],
    alphas: tuple[float, ...],
    target_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_rows: list[dict[str, str]],
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    near_base_low_tail_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from autodrift.public_base_target_regeneration import _key

    target_by_key = {_key(row): row for row in target_rows}
    target_source_labels = [str(target_by_key.get(_key(meta), {}).get("source_label", "")) for meta in meta_rows]
    strict_mask_np = np.asarray([label == "strict_low_tail" for label in target_source_labels], dtype=bool)
    near_mask_np = np.asarray([label == "near_tail_coverage" for label in target_source_labels], dtype=bool)
    target_mask_np = target_mask.detach().cpu().numpy().astype(bool)
    normal_actions = samples["normal_actions"]
    intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    baseline_target_mse = torch.mean((normal_actions[target_mask] - target_actions[target_mask]).pow(2), dim=-1)
    baseline_target_mse_mean = float(baseline_target_mse.mean().detach().item()) if bool(target_mask.any()) else 0.0
    grid_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    for mix_weight in mix_weights:
        weight = float(mix_weight)
        normal_delta = (1.0 - weight) * delta921_normal + weight * delta924_normal
        intervention_delta = (1.0 - weight) * delta921_intervention + weight * delta924_intervention
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
                "mix_weight_m924": weight,
                "mix_weight_m921": float(1.0 - weight),
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
            row["feasible_candidate"] = bool(
                row["normal_retention_pass"] and row["tail_lift_pass"] and row["target_loss_pass"]
            )
            grid_rows.append(row)
            for index, meta in enumerate(meta_rows):
                objective_rows.append(
                    {
                        **meta,
                        "mix_weight_m924": weight,
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
    return grid_rows, objective_rows


def classify_residual_direction_feasibility(
    *,
    actor_backbone_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_keys: int,
    feasible_candidate_count: int,
    any_tail_lift: bool,
    any_normal_retained_tail_lift: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_backbone_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "public_base_residual_direction_feasibility_contract_artifact"
    if int(missing_target_keys) > 0:
        return "public_base_residual_direction_feasibility_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_residual_direction_feasibility_reconstruction_blocked"
    if int(feasible_candidate_count) > 0:
        return "public_base_residual_direction_feasibility_candidate"
    if bool(any_normal_retained_tail_lift):
        return "public_base_residual_direction_feasibility_target_conflict"
    if bool(any_tail_lift):
        return "public_base_residual_direction_feasibility_trust_region_conflict"
    return "public_base_residual_direction_feasibility_no_tail_lift"


def _best_row(rows: list[dict[str, Any]], *, key_fields: tuple[str, ...], filter_key: str | None = None) -> dict[str, Any]:
    filtered = [row for row in rows if filter_key is None or bool(row.get(filter_key, False))]
    if not filtered:
        return {}
    return sorted(filtered, key=lambda row: tuple(float(row.get(field, 0.0)) for field in key_fields))[0]


def run_residual_direction_feasibility(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    m921_residual_head_path: Path,
    m924_residual_head_path: Path,
    run_dir: Path,
    device: str,
    mix_weights: tuple[float, ...] = DEFAULT_MIX_WEIGHTS,
    alphas: tuple[float, ...] = DEFAULT_FEASIBILITY_ALPHAS,
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
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
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
    feature_dim = int(samples["normal_features"].shape[1]) if len(meta_rows) else 0
    if len(meta_rows) == 0:
        weight_rows: list[dict[str, Any]] = []
        missing_target_keys: set[tuple[str, str, str, str]] = set()
        grid_rows: list[dict[str, Any]] = []
        objective_rows: list[dict[str, Any]] = []
    else:
        target_mask, _low_tail_mask, target_actions, _target_weights, weight_rows, missing_target_keys = target_weight_vector(
            meta_rows=meta_rows,
            target_rows=target_rows,
            low_tail_rows=low_tail_rows,
            normal_actions=samples["normal_actions"],
        )
        if missing_target_keys:
            grid_rows = []
            objective_rows = []
        else:
            residual921 = _load_residual_head(m921_residual_head_path, expected_feature_dim=feature_dim, device=resolved_device)
            residual924 = _load_residual_head(m924_residual_head_path, expected_feature_dim=feature_dim, device=resolved_device)
            with torch.no_grad():
                delta921_normal = residual921(samples["normal_features"])
                delta921_intervention = residual921(samples["intervention_features"])
                delta924_normal = residual924(samples["normal_features"])
                delta924_intervention = residual924(samples["intervention_features"])
            grid_rows, objective_rows = evaluate_direction_grid(
                samples=samples,
                meta_rows=meta_rows,
                delta921_normal=delta921_normal,
                delta921_intervention=delta921_intervention,
                delta924_normal=delta924_normal,
                delta924_intervention=delta924_intervention,
                mix_weights=mix_weights,
                alphas=alphas,
                target_mask=target_mask,
                target_actions=target_actions,
                target_rows=target_rows,
                near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
            )
    checksum_after = model_parameter_checksum(model)
    feasible_rows = [row for row in grid_rows if bool(row.get("feasible_candidate", False))]
    tail_rows = [row for row in grid_rows if bool(row.get("tail_lift_pass", False))]
    normal_tail_rows = [
        row for row in grid_rows if bool(row.get("tail_lift_pass", False)) and bool(row.get("normal_retention_pass", False))
    ]
    result_class = classify_residual_direction_feasibility(
        actor_backbone_changed=bool(checksum_before != checksum_after),
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        feasible_candidate_count=len(feasible_rows),
        any_tail_lift=bool(tail_rows),
        any_normal_retained_tail_lift=bool(normal_tail_rows),
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    best_candidate = feasible_rows[0] if feasible_rows else {}
    best_normal_retaining_low_tail = _best_row(
        grid_rows,
        key_fields=("low_tail_fraction", "gap_deficit_mean"),
        filter_key="normal_retention_pass",
    )
    best_tail_lift_nonretaining = _best_row(
        [row for row in tail_rows if not bool(row.get("normal_retention_pass", False))],
        key_fields=("low_tail_fraction", "gap_deficit_mean"),
    )
    normal_boundary = _best_row(
        [row for row in grid_rows if not bool(row.get("normal_retention_pass", False))],
        key_fields=("first_action_drift_from_base_mean", "first_action_drift_from_base_p95"),
    )
    target_boundary = _best_row(
        [row for row in grid_rows if not bool(row.get("target_loss_pass", False))],
        key_fields=("target_action_mse_mean",),
    )
    write_csv_rows(run_dir / "feasibility_grid.csv", grid_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "target_weight_rows.csv", weight_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [*rejected_rows, *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys))],
    )
    summary = {
        "run_type": "public_base_residual_direction_feasibility",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "m921_residual_head": m921_residual_head_path,
        "m924_residual_head": m924_residual_head_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "target_rows_count": int(len(target_rows)),
        "joined_target_rows": int(sum(1 for row in weight_rows if bool(row.get("target_available", False)))),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(len(low_tail_rows)),
        "feature_dim": int(feature_dim),
        "mix_weights": [float(weight) for weight in mix_weights],
        "alphas": [float(alpha) for alpha in alphas],
        "grid_rows": int(len(grid_rows)),
        "feasible_candidate_count": int(len(feasible_rows)),
        "tail_lift_rows": int(len(tail_rows)),
        "normal_retained_tail_lift_rows": int(len(normal_tail_rows)),
        "best_candidate": best_candidate,
        "best_normal_retaining_low_tail_row": best_normal_retaining_low_tail,
        "best_tail_lift_nonretaining_row": best_tail_lift_nonretaining,
        "normal_retention_boundary_row": normal_boundary,
        "target_loss_boundary_row": target_boundary,
        "actor_backbone_changed": bool(checksum_before != checksum_after),
        "base_actor_checksum_before": checksum_before,
        "base_actor_checksum_after": checksum_after,
        "training_started": False,
        "optimizer_started": False,
        "residual_head_fit_started": False,
        "m880_exact_used": False,
        "replay_used": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "feasibility_grid_csv": run_dir / "feasibility_grid.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "target_weight_rows_csv": run_dir / "target_weight_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training public-base residual direction feasibility sweep.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--target-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--m921-residual-head", type=Path, required=True)
    parser.add_argument("--m924-residual-head", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--mix-weights", type=_parse_float_list, default=DEFAULT_MIX_WEIGHTS)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_FEASIBILITY_ALPHAS)
    args = parser.parse_args()
    summary = run_residual_direction_feasibility(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        m921_residual_head_path=args.m921_residual_head,
        m924_residual_head_path=args.m924_residual_head,
        run_dir=args.run_dir,
        device=args.device,
        mix_weights=tuple(args.mix_weights),
        alphas=tuple(args.alphas),
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
