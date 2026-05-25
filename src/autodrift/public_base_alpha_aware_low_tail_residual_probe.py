"""Alpha-aware low-tail residual-head probe for the M399 public base."""

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
from autodrift.public_base_regenerated_target_residual_probe import (
    regenerated_alpha_metrics,
    target_weight_vector,
)
from autodrift.public_base_tail_weighted_residual_probe import (
    DEFAULT_ALPHAS,
    LOW_TAIL_DEFICIT_THRESHOLD,
    LOW_TAIL_GAP_THRESHOLD,
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


DEFAULT_TRAIN_ALPHAS = (0.20, 0.35)
LOW_TAIL_GAP_MARGIN = 0.004
LOW_TAIL_DEFICIT_TARGET = 0.014
FRACTION_SURROGATE_TEMPERATURE = 0.004


def low_tail_alpha_loss(
    *,
    gap: torch.Tensor,
    target_gaps: torch.Tensor,
    low_tail_mask: torch.Tensor,
    gap_floor: float = LOW_TAIL_GAP_THRESHOLD + LOW_TAIL_GAP_MARGIN,
    deficit_target: float = LOW_TAIL_DEFICIT_TARGET,
    temperature: float = FRACTION_SURROGATE_TEMPERATURE,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if not bool(low_tail_mask.any()):
        zero = torch.zeros((), dtype=torch.float32, device=gap.device)
        return zero, zero, zero
    low_gap = gap[low_tail_mask]
    low_deficit = torch.relu(target_gaps[low_tail_mask] - low_gap)
    gap_floor_loss = torch.relu(float(gap_floor) - low_gap).pow(2).mean()
    deficit_loss = torch.relu(low_deficit - float(deficit_target)).pow(2).mean()
    temp = max(float(temperature), 1e-6)
    gap_fraction_surrogate = torch.sigmoid((float(gap_floor) - low_gap) / temp)
    deficit_fraction_surrogate = torch.sigmoid((low_deficit - float(LOW_TAIL_DEFICIT_THRESHOLD)) / temp)
    fraction_surrogate = torch.mean(gap_fraction_surrogate + deficit_fraction_surrogate)
    return gap_floor_loss, deficit_loss, fraction_surrogate


def train_alpha_aware_low_tail_residual_head(
    samples: dict[str, torch.Tensor],
    *,
    target_mask: torch.Tensor,
    low_tail_mask: torch.Tensor,
    target_actions: torch.Tensor,
    target_weights: torch.Tensor,
    epochs: int,
    seed: int,
    lr: float,
    train_alphas: tuple[float, ...] = DEFAULT_TRAIN_ALPHAS,
    low_tail_gap_floor_coef: float = 3.0,
    low_tail_deficit_coef: float = 2.0,
    low_tail_fraction_surrogate_coef: float = 1.0,
    target_action_coef: float = 0.5,
    normal_anchor_coef: float = 4.0,
    intervention_anchor_coef: float = 0.5,
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
    alphas = tuple(float(alpha) for alpha in train_alphas)
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        normal_delta = head(normal_features)
        intervention_delta = head(intervention_features)
        total_target_loss = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        total_gap_floor_loss = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        total_deficit_loss = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        total_fraction_surrogate = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        total_normal_anchor = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        total_intervention_anchor = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
        total_gap_mean = 0.0
        for alpha in alphas:
            adjusted_normal = torch.clamp(normal_actions + float(alpha) * normal_delta, -1.0, 1.0)
            adjusted_intervention = torch.clamp(intervention_actions + float(alpha) * intervention_delta, -1.0, 1.0)
            if bool(target_mask.any()):
                target_error = torch.mean((adjusted_normal[target_mask] - target_actions[target_mask]).pow(2), dim=-1)
                target_loss = (target_weights[target_mask] * target_error).sum() / torch.clamp(
                    target_weights[target_mask].sum(), min=1.0
                )
            else:
                target_loss = torch.zeros((), dtype=torch.float32, device=normal_actions.device)
            gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1)
            gap_floor_loss, deficit_loss, fraction_surrogate = low_tail_alpha_loss(
                gap=gap,
                target_gaps=target_gaps,
                low_tail_mask=low_tail_mask,
            )
            total_target_loss = total_target_loss + target_loss
            total_gap_floor_loss = total_gap_floor_loss + gap_floor_loss
            total_deficit_loss = total_deficit_loss + deficit_loss
            total_fraction_surrogate = total_fraction_surrogate + fraction_surrogate
            total_normal_anchor = total_normal_anchor + torch.mean((adjusted_normal - normal_actions).pow(2))
            total_intervention_anchor = total_intervention_anchor + torch.mean(
                (adjusted_intervention - intervention_actions).pow(2)
            )
            total_gap_mean += float(gap.detach().mean().item())
        denom = float(max(len(alphas), 1))
        target_loss = total_target_loss / denom
        gap_floor_loss = total_gap_floor_loss / denom
        deficit_loss = total_deficit_loss / denom
        fraction_surrogate = total_fraction_surrogate / denom
        normal_anchor_loss = total_normal_anchor / denom
        intervention_anchor_loss = total_intervention_anchor / denom
        loss = (
            float(low_tail_gap_floor_coef) * gap_floor_loss
            + float(low_tail_deficit_coef) * deficit_loss
            + float(low_tail_fraction_surrogate_coef) * fraction_surrogate
            + float(target_action_coef) * target_loss
            + float(normal_anchor_coef) * normal_anchor_loss
            + float(intervention_anchor_coef) * intervention_anchor_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "target_loss": float(target_loss.detach().item()),
                "low_tail_gap_floor_loss": float(gap_floor_loss.detach().item()),
                "low_tail_deficit_loss": float(deficit_loss.detach().item()),
                "low_tail_fraction_surrogate": float(fraction_surrogate.detach().item()),
                "normal_anchor_loss": float(normal_anchor_loss.detach().item()),
                "intervention_anchor_loss": float(intervention_anchor_loss.detach().item()),
                "train_gap_mean": float(total_gap_mean / denom),
            }
        )
    return head, history


def classify_alpha_aware_low_tail_probe(
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
        return "public_base_alpha_aware_low_tail_probe_contract_artifact"
    if int(missing_target_keys) > 0:
        return "public_base_alpha_aware_low_tail_probe_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_alpha_aware_low_tail_probe_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "public_base_alpha_aware_low_tail_probe_candidate"
    return "public_base_alpha_aware_low_tail_probe_no_candidate"


def _best_normal_retaining_tail_alpha(alpha_rows: list[dict[str, Any]]) -> dict[str, Any]:
    normal_rows = [row for row in alpha_rows if bool(row.get("normal_retention_pass", False))]
    if not normal_rows:
        return {}
    return min(
        normal_rows,
        key=lambda row: (
            float(row.get("low_tail_fraction", float("inf"))),
            float(row.get("gap_deficit_mean", float("inf"))),
            -float(row.get("normal_intervention_gap_p10", 0.0)),
        ),
    )


def run_alpha_aware_low_tail_residual_probe(
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
    train_alphas: tuple[float, ...] = DEFAULT_TRAIN_ALPHAS,
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
        target_actions = torch.empty((0, 3), dtype=torch.float32, device=resolved_device)
        weight_rows: list[dict[str, Any]] = []
        missing_target_keys: set[tuple[str, str, str, str]] = {
            (
                str(row.get("contrast_group_id", "")),
                str(row.get("source_index", "")),
                str(row.get("variant", "")),
                str(row.get("horizon", "")),
            )
            for row in target_rows
        }
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
            head, train_rows = train_alpha_aware_low_tail_residual_head(
                samples=samples,
                target_mask=target_mask,
                low_tail_mask=low_tail_mask,
                target_actions=target_actions,
                target_weights=target_weights,
                epochs=epochs,
                seed=seed,
                lr=lr,
                train_alphas=train_alphas,
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
                    "train_alphas": [float(alpha) for alpha in train_alphas],
                    "objective": "public_base_alpha_aware_low_tail_residual_probe",
                },
                run_dir / "residual_head.pt",
            )
    checksum_after = model_parameter_checksum(model)
    candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_normal_tail = _best_normal_retaining_tail_alpha(alpha_rows)
    result_class = classify_alpha_aware_low_tail_probe(
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
    summary = {
        "run_type": "public_base_alpha_aware_low_tail_residual_probe",
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
        "low_tail_rows_count": int(len(low_tail_rows)),
        "residual_parameter_count": int(residual_parameter_count),
        "epochs": int(epochs),
        "seed": int(seed),
        "train_alphas": [float(alpha) for alpha in train_alphas],
        "alphas": [float(alpha) for alpha in alphas],
        "low_tail_gap_floor": float(LOW_TAIL_GAP_THRESHOLD + LOW_TAIL_GAP_MARGIN),
        "low_tail_deficit_target": float(LOW_TAIL_DEFICIT_TARGET),
        "near_base_gap_p10": float(m912_summary["near_base_gap_p10"]),
        "near_base_gap_deficit_mean": float(m912_summary["near_base_gap_deficit_mean"]),
        "near_base_low_tail_fraction": float(m912_summary["low_tail_fraction"]),
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "best_candidate": best_candidate,
        "best_normal_retaining_tail_alpha": best_normal_tail,
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
    parser = argparse.ArgumentParser(description="Run M399 alpha-aware low-tail residual-head probe.")
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
    parser.add_argument("--seed", type=int, default=9240)
    parser.add_argument("--train-alphas", type=_parse_float_list, default=DEFAULT_TRAIN_ALPHAS)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--lr", type=float, default=3e-3)
    args = parser.parse_args()
    summary = run_alpha_aware_low_tail_residual_probe(
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
        train_alphas=tuple(args.train_alphas),
        alphas=tuple(args.alphas),
        lr=args.lr,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
