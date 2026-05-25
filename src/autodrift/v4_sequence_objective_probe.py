"""No-PPO residual objective probe for the M755/M758 v4 sequence corpus."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.sequence_command_response_intervention import corrupt_sequence_observation
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _collect_seed_snapshots, _find_snapshot
from autodrift.train_ppo import ActorCritic, resolve_device


ACTION_FIELDS = ("first_steer", "first_throttle", "first_brake")
DEFAULT_ALPHAS = (0.02, 0.05, 0.10, 0.20, 0.50, 1.00)
BASE_GAP_MEAN = 0.024908
BASE_GAP_P10 = 0.021141
BASE_GAP_DEFICIT_MEAN = 0.016809


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_float_list(raw: str) -> tuple[float, ...]:
    parts = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("expected at least one comma-separated alpha")
    return tuple(float(part) for part in parts)


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _finite_values(values: np.ndarray | list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    return arr[np.isfinite(arr)]


def _mean(values: np.ndarray | list[float]) -> float:
    finite = _finite_values(values)
    return float(np.mean(finite)) if finite.size else float("nan")


def _percentile(values: np.ndarray | list[float], percentile: float) -> float:
    finite = _finite_values(values)
    return float(np.percentile(finite, percentile)) if finite.size else float("nan")


def _vector(row: dict[str, Any], fields: tuple[str, ...] = ACTION_FIELDS) -> np.ndarray:
    return np.asarray([_finite_float(row.get(field)) for field in fields], dtype=np.float32)


def _target_gap(row: dict[str, Any]) -> float:
    return float(np.clip(_finite_float(row.get("prefix_l2_mean"), default=0.0), 0.02, 0.06))


def _outcome_weight(row: dict[str, Any]) -> float:
    margin_gap = max(_finite_float(row.get("margin_gap_from_normal"), default=0.0), 0.0)
    horizon = max(_finite_float(row.get("horizon"), default=1.0), 1.0)
    variant_weight = 1.0 if str(row.get("variant", "")) == "zero_command_obs" else 0.75
    return float(np.clip(1.0 + 10.0 * margin_gap + 0.05 * min(horizon, 8.0), 1.0, 3.0) * variant_weight)


def _metadata_missing(row: dict[str, Any]) -> bool:
    required = (
        "source_index",
        "seed",
        "step",
        "preferred_fault",
        "variant",
        "horizon",
        "source_kind",
        "source_pool",
        "claim_boundary_level",
        "contrast_group_id",
    )
    return any(not str(row.get(field, "")).strip() for field in required)


def _contrast_lookup(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    normal_rows: dict[str, dict[str, Any]] = {}
    hard_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        group_id = str(row.get("contrast_group_id", ""))
        role = str(row.get("contrast_role", ""))
        if role == "normal":
            normal_rows.setdefault(group_id, row)
        elif role == "hard_negative_action_only":
            hard_rows.setdefault(group_id, []).append(row)
    return normal_rows, hard_rows


class ResidualHead(nn.Module):
    def __init__(self, feature_dim: int, hidden_dim: int = 64, max_residual: float = 0.04) -> None:
        super().__init__()
        self.max_residual = float(max_residual)
        self.net = nn.Sequential(
            nn.Linear(int(feature_dim), int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), 3),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.max_residual * torch.tanh(self.net(features))


def classify_v4_sequence_objective_probe(
    *,
    actor_backbone_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    candidate_count: int,
    any_gap_lift: bool,
    any_normal_drift: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_backbone_changed) or bool(ppo_used) or bool(promoted) or int(metadata_missing_rows) > 0:
        return "v4_sequence_objective_probe_metadata_artifact"
    if float(reconstruction_success_rate) < 0.98:
        return "v4_sequence_objective_probe_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "v4_sequence_objective_probe_candidate"
    if bool(any_gap_lift) and bool(any_normal_drift):
        return "v4_sequence_objective_probe_normal_drift"
    return "v4_sequence_objective_probe_no_gap_lift"


def _branch_feature_action(
    model: ActorCritic,
    *,
    observation: np.ndarray,
    hidden: torch.Tensor,
    device: torch.device,
) -> tuple[torch.Tensor, np.ndarray]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        features, _ = model.recurrent_features_tensor(obs_t, hidden_t)
        action = torch.tanh(model.actor_mean(features))
    return features.squeeze(0).detach().cpu(), action.squeeze(0).detach().cpu().numpy().astype(np.float32)


def _intervention_obs_hidden(
    model: ActorCritic,
    *,
    observation: np.ndarray,
    hidden: torch.Tensor,
    variant: str,
    horizon: int,
    response_dim: int,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor]:
    obs = np.asarray(observation, dtype=np.float32).copy()
    branch_hidden = hidden.detach().clone()
    if variant in {"zero_command_obs", "command_shift_obs", "response_delay_obs"}:
        obs = corrupt_sequence_observation(
            obs,
            variant=variant,
            step_index=0,
            horizon=int(horizon),
            raw_history=[np.asarray(observation, dtype=np.float32).copy()],
            response_dim=response_dim,
        )
    if variant in {"reset_hidden_then_normal", "reset_hidden_each_step"}:
        branch_hidden = model.initial_hidden(1, device).detach().cpu()
    return obs, branch_hidden


def _load_probe_samples(
    *,
    model: ActorCritic,
    positive_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    scenario_config: dict[str, Any],
    env_config: Any,
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], list[dict[str, Any]], list[dict[str, Any]]]:
    normal_by_group, hard_by_group = _contrast_lookup(contrast_rows)
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    response_dim = response_feature_dim_for_model(model)
    snapshots_by_seed: dict[int, list[Any]] = {}
    metric_meta: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    normal_features: list[torch.Tensor] = []
    intervention_features: list[torch.Tensor] = []
    normal_actions: list[np.ndarray] = []
    intervention_actions: list[np.ndarray] = []
    normal_base_actions: list[np.ndarray] = []
    intervention_base_actions: list[np.ndarray] = []
    target_gaps: list[float] = []
    outcome_weights: list[float] = []
    hard_gaps: list[float] = []
    hard_available: list[float] = []
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
        normal_row = normal_by_group.get(group_id)
        if normal_row is None:
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
        normal_feature, normal_action = _branch_feature_action(
            model,
            observation=snapshot.observation,
            hidden=snapshot.hidden,
            device=device,
        )
        intervention_obs, intervention_hidden = _intervention_obs_hidden(
            model,
            observation=snapshot.observation,
            hidden=snapshot.hidden,
            variant=variant,
            horizon=horizon,
            response_dim=response_dim,
            device=device,
        )
        intervention_feature, intervention_action = _branch_feature_action(
            model,
            observation=intervention_obs,
            hidden=intervention_hidden,
            device=device,
        )
        hard_rows = hard_by_group.get(group_id, [])
        hard_gap_values = [
            float(np.linalg.norm(_vector(item) - _vector(normal_row)))
            for item in hard_rows
            if np.all(np.isfinite(_vector(item))) and np.all(np.isfinite(_vector(normal_row)))
        ]
        normal_features.append(normal_feature)
        intervention_features.append(intervention_feature)
        normal_actions.append(normal_action)
        intervention_actions.append(intervention_action)
        normal_base_actions.append(_vector(normal_row))
        intervention_base_actions.append(_vector(row))
        target_gaps.append(_target_gap(row))
        outcome_weights.append(_outcome_weight(row))
        hard_gaps.append(max(hard_gap_values) if hard_gap_values else 0.0)
        hard_available.append(1.0 if hard_gap_values else 0.0)
        metric_meta.append(
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
                "hard_negative_available": bool(hard_gap_values),
            }
        )
    if not metric_meta:
        empty = torch.empty((0, model.actor_mean.in_features), dtype=torch.float32)
        return {
            "normal_features": empty,
            "intervention_features": empty,
            "normal_actions": torch.empty((0, 3), dtype=torch.float32),
            "intervention_actions": torch.empty((0, 3), dtype=torch.float32),
            "normal_base_actions": torch.empty((0, 3), dtype=torch.float32),
            "intervention_base_actions": torch.empty((0, 3), dtype=torch.float32),
            "target_gaps": torch.empty((0,), dtype=torch.float32),
            "outcome_weights": torch.empty((0,), dtype=torch.float32),
            "hard_gaps": torch.empty((0,), dtype=torch.float32),
            "hard_available": torch.empty((0,), dtype=torch.float32),
        }, metric_meta, rejected_rows
    return {
        "normal_features": torch.stack(normal_features).to(dtype=torch.float32),
        "intervention_features": torch.stack(intervention_features).to(dtype=torch.float32),
        "normal_actions": torch.as_tensor(np.asarray(normal_actions), dtype=torch.float32),
        "intervention_actions": torch.as_tensor(np.asarray(intervention_actions), dtype=torch.float32),
        "normal_base_actions": torch.as_tensor(np.asarray(normal_base_actions), dtype=torch.float32),
        "intervention_base_actions": torch.as_tensor(np.asarray(intervention_base_actions), dtype=torch.float32),
        "target_gaps": torch.as_tensor(target_gaps, dtype=torch.float32),
        "outcome_weights": torch.as_tensor(outcome_weights, dtype=torch.float32),
        "hard_gaps": torch.as_tensor(hard_gaps, dtype=torch.float32),
        "hard_available": torch.as_tensor(hard_available, dtype=torch.float32),
    }, metric_meta, rejected_rows


def _train_residual_head(
    samples: dict[str, torch.Tensor],
    *,
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
    weights = samples["outcome_weights"]
    hard_gaps = samples["hard_gaps"]
    hard_available = samples["hard_available"]
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        normal_delta = head(normal_features)
        intervention_delta = head(intervention_features)
        normal_residual_loss = normal_delta.pow(2).mean()
        gap = torch.linalg.norm((intervention_actions + intervention_delta) - (normal_actions + normal_delta), dim=-1)
        gap_loss = (weights * torch.relu(target_gaps - gap).pow(2)).mean()
        intervention_anchor_loss = intervention_delta.pow(2).mean()
        hard_terms = torch.relu(hard_gaps - gap + 0.005).pow(2) * hard_available
        hard_loss = hard_terms.sum() / torch.clamp(hard_available.sum(), min=1.0)
        loss = 2.0 * normal_residual_loss + gap_loss + 0.25 * intervention_anchor_loss + 0.10 * hard_loss
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "normal_zero_loss": float(normal_residual_loss.detach().item()),
                "gap_loss": float(gap_loss.detach().item()),
                "intervention_anchor_loss": float(intervention_anchor_loss.detach().item()),
                "hard_negative_loss": float(hard_loss.detach().item()),
                "gap_mean": float(gap.detach().mean().item()),
            }
        )
    return head, history


def _alpha_metrics(
    *,
    samples: dict[str, torch.Tensor],
    meta_rows: list[dict[str, Any]],
    head: ResidualHead,
    alphas: tuple[float, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with torch.no_grad():
        normal_delta = head(samples["normal_features"])
        intervention_delta = head(samples["intervention_features"])
    alpha_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    normal_actions = samples["normal_actions"]
    intervention_actions = samples["intervention_actions"]
    target_gaps = samples["target_gaps"]
    hard_gaps = samples["hard_gaps"]
    hard_available = samples["hard_available"]
    for alpha in alphas:
        alpha_value = float(alpha)
        adjusted_normal = torch.clamp(normal_actions + alpha_value * normal_delta, -1.0, 1.0)
        adjusted_intervention = torch.clamp(intervention_actions + alpha_value * intervention_delta, -1.0, 1.0)
        normal_drift = torch.linalg.norm(adjusted_normal - normal_actions, dim=-1).cpu().numpy()
        normal_anchor_mse = torch.mean((adjusted_normal - normal_actions).pow(2), dim=-1).cpu().numpy()
        gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1).cpu().numpy()
        target = target_gaps.cpu().numpy()
        gap_deficit = np.maximum(0.0, target - gap)
        hard_loss = (
            np.maximum(0.0, hard_gaps.cpu().numpy() - gap + 0.005) ** 2
        )
        hard_mask = hard_available.cpu().numpy().astype(bool)
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
            "hard_negative_available_fraction": float(np.mean(hard_mask.astype(np.float32))) if hard_mask.size else 0.0,
            "hard_negative_calibration_loss_mean": _mean(hard_loss[hard_mask]) if hard_mask.any() else 0.0,
        }
        row["normal_retention_pass"] = bool(
            row["normal_anchor_mse_mean"] <= 0.000004
            and row["normal_anchor_mse_p95"] <= 0.000025
            and row["first_action_drift_from_base_mean"] <= 0.003
            and row["first_action_drift_from_base_p95"] <= 0.008
        )
        row["gap_lift_pass"] = bool(
            row["normal_intervention_gap_mean"] >= BASE_GAP_MEAN + 0.003
            and row["normal_intervention_gap_p10"] >= BASE_GAP_P10
            and row["gap_deficit_mean"] <= BASE_GAP_DEFICIT_MEAN - 0.002
        )
        row["exact_probe_candidate"] = bool(row["normal_retention_pass"] and row["gap_lift_pass"])
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
                    "hard_negative_calibration_loss": float(hard_loss[index]) if hard_mask[index] else 0.0,
                }
            )
    return alpha_rows, objective_rows


def run_v4_sequence_objective_probe(
    *,
    checkpoint_path: Path,
    corpus_summary_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
    lr: float = 3e-3,
    max_rows: int | None = None,
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
    if max_rows is not None:
        positives = positives[: max(0, int(max_rows))]
    contrast_rows = _read_csv_rows(contrast_rows_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples, meta_rows, rejected_rows = _load_probe_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    if len(meta_rows) == 0:
        alpha_rows: list[dict[str, Any]] = []
        objective_rows: list[dict[str, Any]] = []
        train_rows: list[dict[str, Any]] = []
        residual_parameter_count = 0
    else:
        head, train_rows = _train_residual_head(samples, epochs=epochs, seed=seed, lr=lr)
        residual_parameter_count = int(sum(parameter.numel() for parameter in head.parameters()))
        alpha_rows, objective_rows = _alpha_metrics(samples=samples, meta_rows=meta_rows, head=head, alphas=alphas)
        torch.save(
            {
                "state_dict": head.state_dict(),
                "feature_dim": int(samples["normal_features"].shape[1]),
                "max_residual": float(head.max_residual),
                "seed": int(seed),
            },
            run_dir / "residual_head.pt",
        )
    checksum_after = model_parameter_checksum(model)
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    candidate_rows = [row for row in alpha_rows if _bool(row.get("exact_probe_candidate", False))]
    any_gap_lift = any(_bool(row.get("gap_lift_pass", False)) for row in alpha_rows)
    any_normal_drift = any(not _bool(row.get("normal_retention_pass", False)) for row in alpha_rows)
    result_class = classify_v4_sequence_objective_probe(
        actor_backbone_changed=bool(checksum_before != checksum_after),
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        candidate_count=len(candidate_rows),
        any_gap_lift=any_gap_lift,
        any_normal_drift=any_normal_drift,
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_gap_row = max(alpha_rows, key=lambda row: float(row.get("normal_intervention_gap_mean", float("-inf"))), default={})
    summary = {
        "run_type": "v4_sequence_objective_probe",
        "checkpoint": checkpoint_path,
        "corpus_summary": corpus_summary_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "rejected_rows": int(len(rejected_rows)),
        "residual_parameter_count": int(residual_parameter_count),
        "epochs": int(epochs),
        "seed": int(seed),
        "alphas": [float(alpha) for alpha in alphas],
        "base_gap_mean": BASE_GAP_MEAN,
        "base_gap_p10": BASE_GAP_P10,
        "base_gap_deficit_mean": BASE_GAP_DEFICIT_MEAN,
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "best_candidate": best_candidate,
        "best_gap_alpha": best_gap_row,
        "actor_backbone_changed": bool(checksum_before != checksum_after),
        "base_actor_checksum_before": checksum_before,
        "base_actor_checksum_after": checksum_after,
        "training_started": bool(len(meta_rows) > 0),
        "optimizer_started": bool(len(meta_rows) > 0),
        "residual_only_training": True,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "residual_head_pt": run_dir / "residual_head.pt",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a no-PPO v4 residual objective probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus-summary", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7610)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    summary = run_v4_sequence_objective_probe(
        checkpoint_path=args.checkpoint,
        corpus_summary_path=args.corpus_summary,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        epochs=args.epochs,
        seed=args.seed,
        alphas=tuple(args.alphas),
        lr=args.lr,
        max_rows=args.max_rows,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
