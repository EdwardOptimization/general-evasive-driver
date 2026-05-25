"""Normal-margin-aware calibration for the frozen M761 residual head."""

from __future__ import annotations

import argparse
import copy
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
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.sequence_command_response_intervention import corrupt_sequence_observation
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _collect_seed_snapshots, _find_snapshot
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _alpha_summary_rows,
    _bool,
    _finite_values,
    _load_residual_head,
    _mean,
    _metadata_missing,
    _parse_float_list,
    _percentile,
    _prefix_distance_stats,
    _read_csv_rows,
    _source_meta,
)
from autodrift.v4_sequence_objective_probe import _load_probe_samples


DEFAULT_ALPHAS = (0.0, 0.125, 0.15, 0.2)
ACTIVE_BOUNDARY_SEED = 77025
ACTIVE_BOUNDARY_SOURCE_INDEX = 12
ACTIVE_BOUNDARY_STEP = 24


class ResidualGate(nn.Module):
    """Small scalar gate over deployable actor features."""

    def __init__(self, feature_dim: int, hidden_dim: int = 32) -> None:
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.hidden_dim = int(hidden_dim)
        self.net = nn.Sequential(
            nn.Linear(self.feature_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.net(features))


def _nonfinite_to(value: float, default: float) -> float:
    return float(value) if np.isfinite(float(value)) else float(default)


def _active_boundary_key(row: dict[str, Any]) -> bool:
    return (
        int(row.get("seed", -1)) == ACTIVE_BOUNDARY_SEED
        and int(row.get("source_index", -1)) == ACTIVE_BOUNDARY_SOURCE_INDEX
        and int(row.get("step", -1)) == ACTIVE_BOUNDARY_STEP
    )


def _filter_supported_positives(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    supported: list[dict[str, str]] = []
    rejected: list[dict[str, Any]] = []
    for row in rows:
        meta = _source_meta(row)
        if _metadata_missing(row):
            rejected.append({**meta, "rejection_reason": "metadata_missing"})
            continue
        variant = str(row.get("variant", ""))
        if variant not in SUPPORTED_VARIANTS:
            rejected.append({**meta, "rejection_reason": f"unsupported_variant:{variant}"})
            continue
        supported.append(row)
    return supported, rejected


def _parent_margin_lookup(parent_replay_rows_path: Path) -> tuple[dict[str, float], float]:
    rows = _read_csv_rows(parent_replay_rows_path)
    base_normal_margin_by_group: dict[str, float] = {}
    active_alpha_0125_margin = float("nan")
    for row in rows:
        if str(row.get("branch", "")) != "normal":
            continue
        if float(row.get("alpha", 0.0)) == 0.0:
            base_normal_margin_by_group[str(row.get("contrast_group_id", ""))] = _finite_float(
                row.get("min_clearance_margin")
            )
        if float(row.get("alpha", 0.0)) == 0.125 and _active_boundary_key(row):
            margin = _finite_float(row.get("min_clearance_margin"))
            active_alpha_0125_margin = min(active_alpha_0125_margin, margin) if np.isfinite(active_alpha_0125_margin) else margin
    return base_normal_margin_by_group, active_alpha_0125_margin


def _margin_tensor(
    meta_rows: list[dict[str, Any]],
    base_normal_margin_by_group: dict[str, float],
) -> torch.Tensor:
    values = [
        _nonfinite_to(base_normal_margin_by_group.get(str(row.get("contrast_group_id", "")), float("nan")), 1.0)
        for row in meta_rows
    ]
    return torch.as_tensor(values, dtype=torch.float32)


def _boundary_mask_tensor(meta_rows: list[dict[str, Any]]) -> torch.Tensor:
    return torch.as_tensor([1.0 if _active_boundary_key(row) else 0.0 for row in meta_rows], dtype=torch.float32)


def _train_calibrator(
    *,
    samples: dict[str, torch.Tensor],
    meta_rows: list[dict[str, Any]],
    residual_head: nn.Module,
    base_normal_margin_by_group: dict[str, float],
    epochs: int,
    seed: int,
    lr: float,
    alpha_train: float,
    margin_reference: float,
    margin_weight_max: float,
    gap_lift: float,
    intervention_gate_floor: float,
) -> tuple[ResidualGate, list[dict[str, Any]]]:
    torch.manual_seed(int(seed))
    feature_dim = int(samples["normal_features"].shape[1])
    calibrator = ResidualGate(feature_dim=feature_dim)
    optimizer = torch.optim.Adam(calibrator.parameters(), lr=float(lr))
    normal_features = samples["normal_features"]
    intervention_features = samples["intervention_features"]
    normal_actions = samples["normal_actions"]
    intervention_actions = samples["intervention_actions"]
    outcome_weights = samples["outcome_weights"]
    hard_gaps = samples["hard_gaps"]
    hard_available = samples["hard_available"]
    margins = _margin_tensor(meta_rows, base_normal_margin_by_group)
    boundary_mask = _boundary_mask_tensor(meta_rows)
    with torch.no_grad():
        normal_delta = residual_head(normal_features)
        intervention_delta = residual_head(intervention_features)
        base_gap = torch.linalg.norm(intervention_actions - normal_actions, dim=-1)
        target_gap = torch.clamp(base_gap + float(gap_lift), max=0.08)
        safe_margin = torch.clamp(torch.nan_to_num(margins, nan=1.0, posinf=1.0, neginf=1e-5), min=1e-5)
        margin_weights = 1.0 + torch.clamp(float(margin_reference) / safe_margin, min=0.0, max=float(margin_weight_max))
    history: list[dict[str, Any]] = []
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        gate_normal = calibrator(normal_features).squeeze(-1)
        gate_intervention = calibrator(intervention_features).squeeze(-1)
        scaled_normal_delta = gate_normal.unsqueeze(-1) * normal_delta
        scaled_intervention_delta = gate_intervention.unsqueeze(-1) * intervention_delta
        normal_suppression = (margin_weights * torch.sum(scaled_normal_delta.pow(2), dim=-1)).mean()
        if float(boundary_mask.sum().item()) > 0.0:
            boundary_guard = (
                boundary_mask * torch.sum(scaled_normal_delta.pow(2), dim=-1)
            ).sum() / torch.clamp(boundary_mask.sum(), min=1.0)
        else:
            boundary_guard = torch.zeros((), dtype=torch.float32)
        adjusted_normal = torch.clamp(normal_actions + float(alpha_train) * scaled_normal_delta, -1.0, 1.0)
        adjusted_intervention = torch.clamp(
            intervention_actions + float(alpha_train) * scaled_intervention_delta,
            -1.0,
            1.0,
        )
        calibrated_gap = torch.linalg.norm(adjusted_intervention - adjusted_normal, dim=-1)
        gap_loss = (outcome_weights * torch.relu(target_gap - calibrated_gap).pow(2)).mean()
        gate_floor_loss = torch.relu(float(intervention_gate_floor) - gate_intervention).pow(2).mean()
        hard_terms = torch.relu(hard_gaps - calibrated_gap + 0.005).pow(2) * hard_available
        hard_loss = hard_terms.sum() / torch.clamp(hard_available.sum(), min=1.0)
        l2_loss = torch.zeros((), dtype=torch.float32)
        for parameter in calibrator.parameters():
            l2_loss = l2_loss + parameter.pow(2).mean()
        loss = (
            2.0 * normal_suppression
            + 4.0 * boundary_guard
            + 1.0 * gap_loss
            + 0.25 * gate_floor_loss
            + 0.10 * hard_loss
            + 1e-4 * l2_loss
        )
        loss.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(loss.detach().item()),
                "normal_margin_suppression_loss": float(normal_suppression.detach().item()),
                "boundary_guard_loss": float(boundary_guard.detach().item()),
                "gap_loss": float(gap_loss.detach().item()),
                "intervention_gate_floor_loss": float(gate_floor_loss.detach().item()),
                "hard_negative_loss": float(hard_loss.detach().item()),
                "l2_loss": float(l2_loss.detach().item()),
                "gate_normal_mean": float(gate_normal.detach().mean().item()),
                "gate_intervention_mean": float(gate_intervention.detach().mean().item()),
                "calibrated_gap_mean": float(calibrated_gap.detach().mean().item()),
            }
        )
    calibrator.eval()
    return calibrator, history


def calibrated_action_from_hidden(
    model: ActorCritic,
    residual_head: nn.Module,
    calibrator: ResidualGate,
    observation: np.ndarray,
    hidden: torch.Tensor,
    *,
    alpha: float,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor, np.ndarray, np.ndarray, np.ndarray, float]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        features, next_hidden = model.recurrent_features_tensor(obs_t, hidden_t)
        base_action = torch.tanh(model.actor_mean(features))
        raw_delta = residual_head(features)
        gate = calibrator(features)
        calibrated_delta = gate * raw_delta
        action = torch.clamp(base_action + float(alpha) * calibrated_delta, -1.0, 1.0)
    return (
        action.squeeze(0).detach().cpu().numpy().astype(np.float32),
        next_hidden.detach(),
        base_action.squeeze(0).detach().cpu().numpy().astype(np.float32),
        raw_delta.squeeze(0).detach().cpu().numpy().astype(np.float32),
        calibrated_delta.squeeze(0).detach().cpu().numpy().astype(np.float32),
        float(gate.squeeze().detach().cpu().item()),
    )


def replay_calibrated_sequence_variant(
    *,
    model: ActorCritic,
    residual_head: nn.Module,
    calibrator: ResidualGate,
    snapshot: Any,
    env_config: Any,
    variant: str,
    horizon: int,
    response_dim: int,
    reference_actions: list[np.ndarray] | None,
    base_reference_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = snapshot.hidden.detach().clone()
    if variant in {"reset_hidden_then_normal", "reset_hidden_each_step"}:
        hidden = model.initial_hidden(1, device)
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    raw_history: list[np.ndarray] = [np.asarray(obs, dtype=np.float32).copy()]
    actions: list[np.ndarray] = []
    raw_deltas: list[np.ndarray] = []
    calibrated_deltas: list[np.ndarray] = []
    gates: list[float] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for step_index in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        if variant not in {"normal", "reset_hidden_then_normal", "reset_hidden_each_step"}:
            policy_obs = corrupt_sequence_observation(
                policy_obs,
                variant=variant,
                step_index=step_index,
                horizon=int(horizon),
                raw_history=raw_history,
                response_dim=response_dim,
            )
        if variant == "reset_hidden_each_step" and step_index < int(horizon):
            hidden = model.initial_hidden(1, device)
        action, next_hidden, _base_action, raw_delta, calibrated_delta, gate = calibrated_action_from_hidden(
            model,
            residual_head,
            calibrator,
            policy_obs,
            hidden,
            alpha=float(alpha),
            device=device,
        )
        actions.append(action)
        raw_deltas.append(raw_delta)
        calibrated_deltas.append(calibrated_delta)
        gates.append(gate)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        raw_history.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_raw_delta = raw_deltas[0] if raw_deltas else np.full(3, float("nan"), dtype=np.float32)
    first_calibrated_delta = calibrated_deltas[0] if calibrated_deltas else np.full(3, float("nan"), dtype=np.float32)
    if reference_actions is None:
        trajectory_distances = zero_action_trajectory_distances(len(actions))
        prefix_distances = {
            "prefix_l2_mean": 0.0,
            "prefix_l2_max": 0.0,
            "prefix_compare_steps": min(len(actions), int(horizon)),
            "first_action_l2_from_reference": 0.0,
        }
    else:
        trajectory_distances = action_trajectory_distances(actions, reference_actions)
        prefix_distances = _prefix_distance_stats(actions, reference_actions, int(horizon))
    base_reference_distances = _prefix_distance_stats(actions, base_reference_actions, int(max(horizon, 1)))
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    raw_norms = [float(np.linalg.norm(delta)) for delta in raw_deltas]
    calibrated_norms = [float(np.linalg.norm(delta)) for delta in calibrated_deltas]
    return {
        "variant": variant,
        "horizon": int(horizon),
        "alpha": float(alpha),
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": _finite_float(info.get("min_obstacle_clearance")),
        "obstacle_collision_radius": _finite_float(info.get("obstacle_collision_radius")),
        "min_clearance_margin": _finite_float(info.get("min_clearance_margin")),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
        "first_gate": float(gates[0]) if gates else float("nan"),
        "gate_mean": _mean(gates),
        "gate_p10": _percentile(gates, 10),
        "gate_p90": _percentile(gates, 90),
        "first_raw_residual_steer": float(first_raw_delta[0]),
        "first_raw_residual_throttle": float(first_raw_delta[1]),
        "first_raw_residual_brake": float(first_raw_delta[2]),
        "first_residual_steer": float(first_calibrated_delta[0]),
        "first_residual_throttle": float(first_calibrated_delta[1]),
        "first_residual_brake": float(first_calibrated_delta[2]),
        "raw_residual_l2_mean": _mean(raw_norms),
        "raw_residual_l2_max": max(_finite_values(raw_norms), default=float("nan")),
        "residual_l2_mean": _mean(calibrated_norms),
        "residual_l2_max": max(_finite_values(calibrated_norms), default=float("nan")),
        **trajectory_distances,
        **prefix_distances,
        "first_action_drift_vs_base_normal": float(base_reference_distances["first_action_l2_from_reference"]),
        "prefix_l2_mean_vs_base_normal": float(base_reference_distances["prefix_l2_mean"]),
        "prefix_l2_max_vs_base_normal": float(base_reference_distances["prefix_l2_max"]),
    }, actions


def _augment_alpha_rows(
    alpha_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    *,
    active_alpha_0125_margin: float,
) -> list[dict[str, Any]]:
    augmented: list[dict[str, Any]] = []
    for row in alpha_rows:
        alpha = float(row.get("alpha", 0.0))
        subset = [item for item in objective_rows if float(item.get("alpha", 0.0)) == alpha]
        active = [item for item in subset if _active_boundary_key(item)]
        active_margins = [_finite_float(item.get("normal_margin")) for item in active]
        active_collisions = [1.0 if _bool(item.get("normal_collision")) else 0.0 for item in active]
        active_min_margin = min(_finite_values(active_margins), default=float("nan"))
        strict_normal_pass = bool(
            float(row.get("normal_success_rate", 0.0)) >= 0.999999
            and float(row.get("normal_collision_rate", 1.0)) <= 1e-12
        )
        active_margin_pass = bool(
            np.isfinite(active_min_margin)
            and (
                not np.isfinite(active_alpha_0125_margin)
                or active_min_margin + 1e-12 >= float(active_alpha_0125_margin)
            )
        )
        new_row = {
            **row,
            "strict_normal_retention_pass": strict_normal_pass,
            "active_source_rows": int(len(active)),
            "active_source_collision_count": int(sum(active_collisions)),
            "active_source_min_margin": active_min_margin,
            "parent_alpha_0125_active_source_margin": active_alpha_0125_margin,
            "active_source_margin_pass_vs_parent": active_margin_pass,
        }
        new_row["normal_margin_calibration_candidate"] = bool(
            strict_normal_pass
            and _bool(row.get("closed_loop_gap_pass", False))
            and active_margin_pass
        )
        augmented.append(new_row)
    return augmented


def classify_v4_normal_margin_calibration(
    *,
    actor_changed: bool,
    residual_changed: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    candidate_count: int,
    any_gap_lift: bool,
    any_normal_regression: bool,
    calibrator_collapse: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if (
        bool(actor_changed)
        or bool(residual_changed)
        or bool(ppo_used)
        or bool(promoted)
        or int(metadata_missing_rows) > 0
    ):
        return "v4_normal_margin_calibration_metadata_artifact"
    if float(reconstruction_success_rate) < 0.98:
        return "v4_normal_margin_calibration_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "v4_normal_margin_calibration_candidate"
    if bool(calibrator_collapse):
        return "v4_normal_margin_calibration_collapsed"
    if bool(any_gap_lift) and bool(any_normal_regression):
        return "v4_normal_margin_calibration_normal_regression"
    return "v4_normal_margin_calibration_no_gap_lift"


def run_v4_normal_margin_residual_calibration(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    parent_replay_rows_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    lr: float,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
    max_rows: int | None = None,
    alpha_train: float = 0.2,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("normal-margin calibration requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    feature_dim = int(model.actor_mean.in_features)
    residual_head = _load_residual_head(residual_head_path, expected_feature_dim=feature_dim, device=resolved_device)
    actor_checksum_before = model_parameter_checksum(model)
    residual_checksum_before = model_parameter_checksum(residual_head)
    all_positives = _read_csv_rows(positive_rows_path)
    if max_rows is not None:
        all_positives = all_positives[: max(0, int(max_rows))]
    supported_positives, upfront_rejected_rows = _filter_supported_positives(all_positives)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    metadata_missing_rows = sum(1 for row in all_positives if _metadata_missing(row))
    base_normal_margin_by_group, active_alpha_0125_margin = _parent_margin_lookup(parent_replay_rows_path)
    samples, meta_rows, sample_rejected_rows = _load_probe_samples(
        model=model,
        positive_rows=supported_positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    rejected_rows = [*upfront_rejected_rows, *sample_rejected_rows]
    if len(meta_rows) == 0:
        calibrator = ResidualGate(feature_dim=feature_dim)
        train_rows: list[dict[str, Any]] = []
    else:
        calibrator, train_rows = _train_calibrator(
            samples=samples,
            meta_rows=meta_rows,
            residual_head=residual_head,
            base_normal_margin_by_group=base_normal_margin_by_group,
            epochs=epochs,
            seed=seed,
            lr=lr,
            alpha_train=alpha_train,
            margin_reference=0.001,
            margin_weight_max=50.0,
            gap_lift=0.002,
            intervention_gate_floor=0.5,
        )
    torch.save(
        {
            "state_dict": calibrator.state_dict(),
            "feature_dim": int(feature_dim),
            "hidden_dim": int(calibrator.hidden_dim),
            "seed": int(seed),
            "alpha_train": float(alpha_train),
            "checkpoint": str(checkpoint_path),
            "residual_head": str(residual_head_path),
        },
        run_dir / "calibrator.pt",
    )
    response_dim = response_feature_dim_for_model(model)
    max_continuation_steps = int(scenario_config.get("max_continuation_steps", 50))
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    snapshots_by_seed: dict[int, list[Any]] = {}
    for row_seed in sorted({int(row.get("seed", -1)) for row in supported_positives if str(row.get("seed", "")).strip()}):
        snapshots_by_seed[row_seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(row_seed),
            config=scenario_config,
            device=resolved_device,
        )
    hard_available_by_group = {
        str(row.get("contrast_group_id", "")): True
        for row in contrast_rows
        if str(row.get("contrast_role", "")) == "hard_negative_action_only"
    }
    replay_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    for row in supported_positives:
        meta = _source_meta(row)
        seed_value = int(row["seed"])
        step = int(row["step"])
        horizon = int(row["horizon"])
        snapshot = _find_snapshot(snapshots_by_seed.get(seed_value, []), fault_name=str(row["preferred_fault"]), step=step)
        if snapshot is None:
            rejected_rows.append({**meta, "rejection_reason": "missing_source_snapshot"})
            continue
        base_normal_actions: list[np.ndarray] | None = None
        normal_by_alpha: dict[float, dict[str, Any]] = {}
        normal_actions_by_alpha: dict[float, list[np.ndarray]] = {}
        intervention_by_alpha: dict[float, dict[str, Any]] = {}
        for alpha in alphas:
            normal, normal_actions = replay_calibrated_sequence_variant(
                model=model,
                residual_head=residual_head,
                calibrator=calibrator,
                snapshot=snapshot,
                env_config=env_config,
                variant="normal",
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=None,
                base_reference_actions=base_normal_actions,
                max_continuation_steps=max_continuation_steps,
                alpha=float(alpha),
                device=resolved_device,
            )
            if float(alpha) == 0.0:
                base_normal_actions = normal_actions
                normal["first_action_drift_vs_base_normal"] = 0.0
                normal["prefix_l2_mean_vs_base_normal"] = 0.0
                normal["prefix_l2_max_vs_base_normal"] = 0.0
            normal_by_alpha[float(alpha)] = normal
            normal_actions_by_alpha[float(alpha)] = normal_actions
            replay_rows.append({**meta, **normal, "branch": "normal", "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False))})
        if base_normal_actions is None:
            rejected_rows.append({**meta, "rejection_reason": "missing_base_normal_actions"})
            continue
        for alpha in alphas:
            intervention, _ = replay_calibrated_sequence_variant(
                model=model,
                residual_head=residual_head,
                calibrator=calibrator,
                snapshot=snapshot,
                env_config=env_config,
                variant=str(row["variant"]),
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=normal_actions_by_alpha[float(alpha)],
                base_reference_actions=base_normal_actions,
                max_continuation_steps=max_continuation_steps,
                alpha=float(alpha),
                device=resolved_device,
            )
            intervention_by_alpha[float(alpha)] = intervention
            replay_rows.append({**meta, **intervention, "branch": "intervention", "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False))})
        for alpha in alphas:
            normal = normal_by_alpha[float(alpha)]
            intervention = intervention_by_alpha[float(alpha)]
            normal_margin = _finite_float(normal.get("min_clearance_margin"))
            intervention_margin = _finite_float(intervention.get("min_clearance_margin"))
            margin_gap = normal_margin - intervention_margin if np.isfinite(normal_margin) and np.isfinite(intervention_margin) else float("nan")
            objective_rows.append(
                {
                    **meta,
                    "alpha": float(alpha),
                    "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False)),
                    "normal_success": bool(normal.get("success", False)),
                    "normal_collision": bool(normal.get("collision", False)),
                    "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                    "normal_margin": normal_margin,
                    "normal_gate_mean": _finite_float(normal.get("gate_mean")),
                    "normal_first_gate": _finite_float(normal.get("first_gate")),
                    "normal_first_action_drift_vs_base": _finite_float(normal.get("first_action_drift_vs_base_normal"), default=0.0),
                    "normal_prefix_l2_mean_vs_base": _finite_float(normal.get("prefix_l2_mean_vs_base_normal"), default=0.0),
                    "intervention_success": bool(intervention.get("success", False)),
                    "intervention_collision": bool(intervention.get("collision", False)),
                    "intervention_terminal_reason": str(intervention.get("terminal_reason", "")),
                    "intervention_margin": intervention_margin,
                    "intervention_gate_mean": _finite_float(intervention.get("gate_mean")),
                    "intervention_first_gate": _finite_float(intervention.get("first_gate")),
                    "margin_gap_from_normal": margin_gap,
                    "intervention_first_action_l2_from_normal": _finite_float(intervention.get("first_action_l2_from_reference")),
                    "intervention_prefix_l2_mean": _finite_float(intervention.get("prefix_l2_mean")),
                    "intervention_prefix_l2_max": _finite_float(intervention.get("prefix_l2_max")),
                    "intervention_trajectory_l2_mean": _finite_float(intervention.get("action_trajectory_distance_mean")),
                    "intervention_trajectory_l2_max": _finite_float(intervention.get("action_trajectory_distance_max")),
                }
            )
    reconstruction_rate = float(len({str(row["contrast_group_id"]) for row in objective_rows}) / max(len(all_positives), 1))
    alpha_rows = _augment_alpha_rows(
        _alpha_summary_rows(objective_rows, alphas=alphas),
        objective_rows,
        active_alpha_0125_margin=active_alpha_0125_margin,
    )
    candidate_rows = [row for row in alpha_rows if _bool(row.get("normal_margin_calibration_candidate", False))]
    any_gap_lift = any(_bool(row.get("closed_loop_gap_pass", False)) for row in alpha_rows)
    any_normal_regression = any(not _bool(row.get("strict_normal_retention_pass", False)) for row in alpha_rows if float(row.get("alpha", 0.0)) > 0.0)
    calibrator_collapse = bool(
        alpha_rows
        and max(float(row.get("intervention_action_gap_mean_vs_normal", 0.0)) for row in alpha_rows) <= float(alpha_rows[0].get("base_intervention_action_gap_mean", 0.0)) + 0.001
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    calibrator_checksum = model_parameter_checksum(calibrator)
    result_class = classify_v4_normal_margin_calibration(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        candidate_count=len(candidate_rows),
        any_gap_lift=any_gap_lift,
        any_normal_regression=any_normal_regression,
        calibrator_collapse=calibrator_collapse,
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "training_metrics.csv", train_rows)
    write_csv_rows(run_dir / "calibration_metrics.csv", train_rows[-1:] if train_rows else [])
    write_csv_rows(run_dir / "replay_rows.csv", replay_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "v4_normal_margin_residual_calibration",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "parent_replay_rows": parent_replay_rows_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "positive_rows": int(len(all_positives)),
        "supported_positive_rows": int(len(supported_positives)),
        "reconstructed_rows": int(len({str(row["contrast_group_id"]) for row in objective_rows})),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "rejected_rows": int(len(rejected_rows)),
        "replay_rows": int(len(replay_rows)),
        "objective_rows": int(len(objective_rows)),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "alpha_train": float(alpha_train),
        "alphas": [float(alpha) for alpha in alphas],
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "best_candidate": candidate_rows[0] if candidate_rows else {},
        "active_alpha_0125_margin_reference": active_alpha_0125_margin,
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "base_residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_residual_head_checksum_before": residual_checksum_before,
        "base_residual_head_checksum_after": residual_checksum_after,
        "calibrator_checksum": calibrator_checksum,
        "calibrator_parameter_count": int(sum(parameter.numel() for parameter in calibrator.parameters())),
        "optimizer_started": bool(len(meta_rows) > 0),
        "training_started": bool(len(meta_rows) > 0),
        "optimizer_updates_only_calibrator": True,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "calibration_metrics_csv": run_dir / "calibration_metrics.csv",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "replay_rows_csv": run_dir / "replay_rows.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "calibrator_pt": run_dir / "calibrator.pt",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a no-PPO normal-margin-aware residual calibration probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--parent-replay-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--seed", type=int, default=7830)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--alpha-train", type=float, default=0.2)
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    summary = run_v4_normal_margin_residual_calibration(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        parent_replay_rows_path=args.parent_replay_rows,
        run_dir=args.run_dir,
        device=args.device,
        epochs=args.epochs,
        seed=args.seed,
        lr=args.lr,
        alphas=tuple(args.alphas),
        max_rows=args.max_rows,
        alpha_train=args.alpha_train,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
