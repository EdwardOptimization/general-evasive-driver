"""No-training residual component sensitivity probe for M792."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

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
from autodrift.v4_sequence_objective_probe import ResidualHead


DEFAULT_ALPHAS = (0.0, 0.125, 0.15, 0.2)
ACTIVE_BOUNDARY_SEED = 77025
ACTIVE_BOUNDARY_SOURCE_INDEX = 12
ACTIVE_BOUNDARY_STEP = 24
M780_ALPHA_0125_GAP_MEAN = 0.044046541597433105
M786_ALPHA_015_GAP_MEAN = 0.04339739074330833
M786_ALPHA_015_ACTIVE_MARGIN = 2.8245982635066724e-05


@dataclass(frozen=True)
class MaskSpec:
    name: str
    mask: tuple[float, float, float]
    aliases: tuple[str, ...] = ()

    @property
    def aliases_text(self) -> str:
        return "|".join(self.aliases)


DEFAULT_MASKS: tuple[MaskSpec, ...] = (
    MaskSpec("none", (0.0, 0.0, 0.0)),
    MaskSpec("all", (1.0, 1.0, 1.0)),
    MaskSpec("steer_only", (1.0, 0.0, 0.0)),
    MaskSpec("throttle_only", (0.0, 1.0, 0.0)),
    MaskSpec("brake_only", (0.0, 0.0, 1.0)),
    MaskSpec("throttle_brake", (0.0, 1.0, 1.0), aliases=("no_steer",)),
    MaskSpec("steer_brake", (1.0, 0.0, 1.0), aliases=("no_throttle",)),
    MaskSpec("steer_throttle", (1.0, 1.0, 0.0), aliases=("no_brake",)),
)
MASKS_BY_NAME = {
    name: spec
    for spec in DEFAULT_MASKS
    for name in (spec.name, *spec.aliases)
}


def _parse_mask_names(raw: str | None) -> tuple[MaskSpec, ...]:
    if raw is None or not str(raw).strip():
        return DEFAULT_MASKS
    selected: list[MaskSpec] = []
    seen: set[str] = set()
    for part in str(raw).split(","):
        name = part.strip()
        if not name:
            continue
        if name not in MASKS_BY_NAME:
            raise argparse.ArgumentTypeError(f"unknown mask '{name}'")
        spec = MASKS_BY_NAME[name]
        if spec.name not in seen:
            selected.append(spec)
            seen.add(spec.name)
    if not selected:
        raise argparse.ArgumentTypeError("expected at least one mask name")
    return tuple(selected)


def _active_boundary_key(row: dict[str, Any]) -> bool:
    return (
        int(row.get("seed", -1)) == ACTIVE_BOUNDARY_SEED
        and int(row.get("source_index", -1)) == ACTIVE_BOUNDARY_SOURCE_INDEX
        and int(row.get("step", -1)) == ACTIVE_BOUNDARY_STEP
    )


def _strict_normal_pass(row: dict[str, Any]) -> bool:
    return bool(
        float(row.get("normal_success_rate", 0.0)) >= 0.999999
        and float(row.get("normal_collision_rate", 1.0)) <= 1e-12
    )


def masked_residual_action_from_hidden(
    model: ActorCritic,
    residual_head: ResidualHead,
    observation: np.ndarray,
    hidden: torch.Tensor,
    *,
    mask: np.ndarray,
    alpha: float,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor, np.ndarray, np.ndarray, np.ndarray]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    mask_t = torch.as_tensor(mask, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.no_grad():
        features, next_hidden = model.recurrent_features_tensor(obs_t, hidden_t)
        base_action = torch.tanh(model.actor_mean(features))
        raw_delta = residual_head(features)
        masked_delta = mask_t * raw_delta
        action = torch.clamp(base_action + float(alpha) * masked_delta, -1.0, 1.0)
    return (
        action.squeeze(0).detach().cpu().numpy().astype(np.float32),
        next_hidden.detach(),
        base_action.squeeze(0).detach().cpu().numpy().astype(np.float32),
        raw_delta.squeeze(0).detach().cpu().numpy().astype(np.float32),
        masked_delta.squeeze(0).detach().cpu().numpy().astype(np.float32),
    )


def replay_masked_residual_sequence_variant(
    *,
    model: ActorCritic,
    residual_head: ResidualHead,
    snapshot: Any,
    env_config: Any,
    variant: str,
    horizon: int,
    response_dim: int,
    reference_actions: list[np.ndarray] | None,
    base_reference_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    alpha: float,
    mask: np.ndarray,
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
    masked_deltas: list[np.ndarray] = []
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
        action, next_hidden, _base_action, raw_delta, masked_delta = masked_residual_action_from_hidden(
            model,
            residual_head,
            policy_obs,
            hidden,
            mask=mask,
            alpha=float(alpha),
            device=device,
        )
        actions.append(action)
        raw_deltas.append(raw_delta)
        masked_deltas.append(masked_delta)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        raw_history.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_raw_delta = raw_deltas[0] if raw_deltas else np.full(3, float("nan"), dtype=np.float32)
    first_masked_delta = masked_deltas[0] if masked_deltas else np.full(3, float("nan"), dtype=np.float32)
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
    raw_array = np.asarray(raw_deltas, dtype=np.float32) if raw_deltas else np.empty((0, 3), dtype=np.float32)
    masked_array = np.asarray(masked_deltas, dtype=np.float32) if masked_deltas else np.empty((0, 3), dtype=np.float32)
    raw_norms = [float(np.linalg.norm(delta)) for delta in raw_deltas]
    masked_norms = [float(np.linalg.norm(delta)) for delta in masked_deltas]
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
        "first_raw_residual_steer": float(first_raw_delta[0]),
        "first_raw_residual_throttle": float(first_raw_delta[1]),
        "first_raw_residual_brake": float(first_raw_delta[2]),
        "first_masked_residual_steer": float(first_masked_delta[0]),
        "first_masked_residual_throttle": float(first_masked_delta[1]),
        "first_masked_residual_brake": float(first_masked_delta[2]),
        "raw_residual_l2_mean": _mean(raw_norms),
        "raw_residual_l2_max": max(_finite_values(raw_norms), default=float("nan")),
        "masked_residual_l2_mean": _mean(masked_norms),
        "masked_residual_l2_max": max(_finite_values(masked_norms), default=float("nan")),
        "raw_residual_abs_mean_steer": float(np.mean(np.abs(raw_array[:, 0]))) if raw_array.size else float("nan"),
        "raw_residual_abs_mean_throttle": float(np.mean(np.abs(raw_array[:, 1]))) if raw_array.size else float("nan"),
        "raw_residual_abs_mean_brake": float(np.mean(np.abs(raw_array[:, 2]))) if raw_array.size else float("nan"),
        "masked_residual_abs_mean_steer": float(np.mean(np.abs(masked_array[:, 0]))) if masked_array.size else float("nan"),
        "masked_residual_abs_mean_throttle": float(np.mean(np.abs(masked_array[:, 1]))) if masked_array.size else float("nan"),
        "masked_residual_abs_mean_brake": float(np.mean(np.abs(masked_array[:, 2]))) if masked_array.size else float("nan"),
        **trajectory_distances,
        **prefix_distances,
        "first_action_drift_vs_base_normal": float(base_reference_distances["first_action_l2_from_reference"]),
        "prefix_l2_mean_vs_base_normal": float(base_reference_distances["prefix_l2_mean"]),
        "prefix_l2_max_vs_base_normal": float(base_reference_distances["prefix_l2_max"]),
    }, actions


def _mask_alpha_summary_rows(objective_rows: list[dict[str, Any]], *, masks: tuple[MaskSpec, ...], alphas: tuple[float, ...]) -> list[dict[str, Any]]:
    base_rows = [row for row in objective_rows if str(row["mask_name"]) == "none" and float(row["alpha"]) == 0.0]
    base_by_group = {str(row["contrast_group_id"]): row for row in base_rows}
    base_gap = _mean([_finite_float(row.get("intervention_prefix_l2_mean")) for row in base_rows])
    base_gap_p10 = _percentile([_finite_float(row.get("intervention_prefix_l2_mean")) for row in base_rows], 10)
    base_margin_gap = _mean([_finite_float(row.get("margin_gap_from_normal")) for row in base_rows])
    rows: list[dict[str, Any]] = []
    for spec in masks:
        for alpha in alphas:
            subset = [
                row
                for row in objective_rows
                if str(row.get("mask_name")) == spec.name and float(row.get("alpha", 0.0)) == float(alpha)
            ]
            if not subset:
                continue
            normal_success = _mean([1.0 if _bool(row.get("normal_success")) else 0.0 for row in subset])
            normal_collision = _mean([1.0 if _bool(row.get("normal_collision")) else 0.0 for row in subset])
            normal_first_drift: list[float] = []
            outcome_retained: list[float] = []
            for row in subset:
                base = base_by_group.get(str(row["contrast_group_id"]))
                if base is None:
                    continue
                normal_first_drift.append(_finite_float(row.get("normal_first_action_drift_vs_base")))
                base_margin_gap_row = _finite_float(base.get("margin_gap_from_normal"))
                margin_gap = _finite_float(row.get("margin_gap_from_normal"))
                if np.isfinite(base_margin_gap_row) and np.isfinite(margin_gap):
                    outcome_retained.append(1.0 if margin_gap + 0.005 >= base_margin_gap_row else 0.0)
            active = [row for row in subset if _active_boundary_key(row)]
            active_margins = [_finite_float(row.get("normal_margin")) for row in active]
            active_min_margin = min(_finite_values(active_margins), default=float("nan"))
            intervention_gap_values = [_finite_float(row.get("intervention_prefix_l2_mean")) for row in subset]
            margin_gap_values = [_finite_float(row.get("margin_gap_from_normal")) for row in subset]
            strict_normal_pass = bool(normal_success >= 0.999999 and normal_collision <= 1e-12)
            gap_mean = _mean(intervention_gap_values)
            actionable = bool(
                strict_normal_pass
                and np.isfinite(gap_mean)
                and gap_mean > M786_ALPHA_015_GAP_MEAN
                and np.isfinite(active_min_margin)
                and active_min_margin + 1e-12 >= M786_ALPHA_015_ACTIVE_MARGIN
            )
            strong_actionable = bool(
                actionable
                and abs(float(alpha) - 0.2) <= 1e-12
                and gap_mean + 1e-12 >= M780_ALPHA_0125_GAP_MEAN
            )
            rows.append(
                {
                    "mask_name": spec.name,
                    "mask_aliases": spec.aliases_text,
                    "mask_steer": float(spec.mask[0]),
                    "mask_throttle": float(spec.mask[1]),
                    "mask_brake": float(spec.mask[2]),
                    "alpha": float(alpha),
                    "sample_count": int(len(subset)),
                    "normal_success_rate": normal_success,
                    "normal_collision_rate": normal_collision,
                    "strict_normal_retention_pass": strict_normal_pass,
                    "intervention_action_gap_mean": gap_mean,
                    "intervention_action_gap_p10": _percentile(intervention_gap_values, 10),
                    "base_intervention_action_gap_mean": base_gap,
                    "base_intervention_action_gap_p10": base_gap_p10,
                    "normal_minus_intervention_margin_gap_mean": _mean(margin_gap_values),
                    "base_margin_gap_mean": base_margin_gap,
                    "outcome_sensitivity_retention_rate": _mean(outcome_retained),
                    "active_source_rows": int(len(active)),
                    "active_source_min_margin": active_min_margin,
                    "active_source_collision_count": int(sum(1 for row in active if _bool(row.get("normal_collision")))),
                    "normal_first_action_drift_mean_vs_base": _mean(normal_first_drift),
                    "masked_residual_abs_mean_steer": _mean([_finite_float(row.get("normal_masked_residual_abs_mean_steer")) for row in subset]),
                    "masked_residual_abs_mean_throttle": _mean([_finite_float(row.get("normal_masked_residual_abs_mean_throttle")) for row in subset]),
                    "masked_residual_abs_mean_brake": _mean([_finite_float(row.get("normal_masked_residual_abs_mean_brake")) for row in subset]),
                    "m786_alpha_015_gap_reference": M786_ALPHA_015_GAP_MEAN,
                    "m786_alpha_015_active_margin_reference": M786_ALPHA_015_ACTIVE_MARGIN,
                    "m780_alpha_0125_gap_reference": M780_ALPHA_0125_GAP_MEAN,
                    "component_actionable_pareto": actionable,
                    "component_strong_actionable_pareto": strong_actionable,
                }
            )
    return rows


def _classify_component_roles(mask_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (str(row["mask_name"]), float(row["alpha"])): row
        for row in mask_rows
    }
    all_row = by_key.get(("all", 0.2), {})
    rows: list[dict[str, Any]] = []
    component_masks = {
        "steer": ("steer_only", "steer_brake", "steer_throttle", "throttle_brake"),
        "throttle": ("throttle_only", "steer_throttle", "throttle_brake", "steer_brake"),
        "brake": ("brake_only", "steer_brake", "throttle_brake", "steer_throttle"),
    }
    for component, (only_name, with_a_name, with_b_name, without_name) in component_masks.items():
        only = by_key.get((only_name, 0.2), {})
        without = by_key.get((without_name, 0.2), {})
        base_gap = _finite_float(all_row.get("base_intervention_action_gap_mean"), default=0.0)
        useful_candidates = [
            by_key.get((only_name, 0.2), {}),
            by_key.get((with_a_name, 0.2), {}),
            by_key.get((with_b_name, 0.2), {}),
        ]
        useful_gap = max(
            [_finite_float(row.get("intervention_action_gap_mean")) for row in useful_candidates],
            default=float("nan"),
        )
        only_gap = _finite_float(only.get("intervention_action_gap_mean"))
        without_gap = _finite_float(without.get("intervention_action_gap_mean"))
        useful_only = bool(np.isfinite(only_gap) and only_gap > base_gap + 0.001)
        useful_combo = bool(
            np.isfinite(useful_gap)
            and np.isfinite(without_gap)
            and useful_gap > base_gap + 0.001
            and useful_gap > without_gap + 0.001
        )
        harmful = bool(
            int(float(all_row.get("active_source_collision_count", 0) or 0)) > 0
            and _bool(without.get("strict_normal_retention_pass", False))
            and _finite_float(only.get("active_source_min_margin"), default=1.0)
            < _finite_float(without.get("active_source_min_margin"), default=-1.0) - 1e-5
        )
        useful = bool(useful_only or useful_combo)
        rows.append(
            {
                "component": component,
                "only_mask": only_name,
                "without_mask": without_name,
                "all_alpha_02_active_margin": _finite_float(all_row.get("active_source_min_margin")),
                "only_alpha_02_active_margin": _finite_float(only.get("active_source_min_margin")),
                "without_alpha_02_active_margin": _finite_float(without.get("active_source_min_margin")),
                "only_alpha_02_gap_mean": only_gap,
                "without_alpha_02_gap_mean": without_gap,
                "best_with_component_alpha_02_gap_mean": useful_gap,
                "useful_component_only_evidence": useful_only,
                "useful_component_combo_evidence": useful_combo,
                "harmful_component_evidence": harmful,
                "useful_component_evidence": useful,
            }
        )
    return rows


def classify_v4_residual_component_sensitivity(
    *,
    actor_changed: bool,
    residual_changed: bool,
    optimizer_started: bool,
    ppo_used: bool,
    promoted: bool,
    metadata_missing_rows: int,
    reconstruction_success_rate: float,
    actionable_count: int,
    attribution_count: int,
) -> str:
    if (
        bool(actor_changed)
        or bool(residual_changed)
        or bool(optimizer_started)
        or bool(ppo_used)
        or bool(promoted)
        or int(metadata_missing_rows) > 0
    ):
        return "v4_residual_component_sensitivity_metadata_artifact"
    if float(reconstruction_success_rate) < 0.98:
        return "v4_residual_component_sensitivity_replay_blocked"
    if int(actionable_count) > 0:
        return "v4_residual_component_sensitivity_actionable_pareto"
    if int(attribution_count) > 0:
        return "v4_residual_component_sensitivity_attribution_found"
    return "v4_residual_component_sensitivity_no_component_signal"


def run_v4_residual_component_sensitivity(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    masks: tuple[MaskSpec, ...] = DEFAULT_MASKS,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
    max_rows: int | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("component sensitivity requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    feature_dim = int(model.actor_mean.in_features)
    residual_head = _load_residual_head(residual_head_path, expected_feature_dim=feature_dim, device=resolved_device)
    actor_checksum_before = model_parameter_checksum(model)
    residual_checksum_before = model_parameter_checksum(residual_head)
    positives = _read_csv_rows(positive_rows_path)
    if max_rows is not None:
        positives = positives[: max(0, int(max_rows))]
    contrast_rows = _read_csv_rows(contrast_rows_path)
    hard_available_by_group = {
        str(row.get("contrast_group_id", "")): True
        for row in contrast_rows
        if str(row.get("contrast_role", "")) == "hard_negative_action_only"
    }
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    response_dim = response_feature_dim_for_model(model)
    max_continuation_steps = int(scenario_config.get("max_continuation_steps", 50))
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    snapshots_by_seed: dict[int, list[Any]] = {}
    for seed in sorted({int(row.get("seed", -1)) for row in positives if str(row.get("seed", "")).strip()}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(seed),
            config=scenario_config,
            device=resolved_device,
        )
    replay_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for row in positives:
        meta = _source_meta(row)
        if _metadata_missing(row):
            rejected_rows.append({**meta, "rejection_reason": "metadata_missing"})
            continue
        variant = str(row.get("variant", ""))
        if variant not in SUPPORTED_VARIANTS:
            rejected_rows.append({**meta, "rejection_reason": f"unsupported_variant:{variant}"})
            continue
        seed = int(row["seed"])
        step = int(row["step"])
        horizon = int(row["horizon"])
        snapshot = _find_snapshot(snapshots_by_seed.get(seed, []), fault_name=str(row["preferred_fault"]), step=step)
        if snapshot is None:
            rejected_rows.append({**meta, "rejection_reason": "missing_source_snapshot"})
            continue
        base_normal_actions: list[np.ndarray] | None = None
        normal_by_key: dict[tuple[str, float], dict[str, Any]] = {}
        normal_actions_by_key: dict[tuple[str, float], list[np.ndarray]] = {}
        intervention_by_key: dict[tuple[str, float], dict[str, Any]] = {}
        for spec in masks:
            mask_array = np.asarray(spec.mask, dtype=np.float32)
            for alpha in alphas:
                normal, normal_actions = replay_masked_residual_sequence_variant(
                    model=model,
                    residual_head=residual_head,
                    snapshot=snapshot,
                    env_config=env_config,
                    variant="normal",
                    horizon=horizon,
                    response_dim=response_dim,
                    reference_actions=None,
                    base_reference_actions=base_normal_actions,
                    max_continuation_steps=max_continuation_steps,
                    alpha=float(alpha),
                    mask=mask_array,
                    device=resolved_device,
                )
                if spec.name == "none" and float(alpha) == 0.0:
                    base_normal_actions = normal_actions
                    normal["first_action_drift_vs_base_normal"] = 0.0
                    normal["prefix_l2_mean_vs_base_normal"] = 0.0
                    normal["prefix_l2_max_vs_base_normal"] = 0.0
                normal_by_key[(spec.name, float(alpha))] = normal
                normal_actions_by_key[(spec.name, float(alpha))] = normal_actions
                replay_rows.append(
                    {
                        **meta,
                        **normal,
                        "mask_name": spec.name,
                        "mask_aliases": spec.aliases_text,
                        "mask_steer": float(spec.mask[0]),
                        "mask_throttle": float(spec.mask[1]),
                        "mask_brake": float(spec.mask[2]),
                        "branch": "normal",
                        "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False)),
                    }
                )
        if base_normal_actions is None:
            rejected_rows.append({**meta, "rejection_reason": "missing_base_normal_actions"})
            continue
        for spec in masks:
            mask_array = np.asarray(spec.mask, dtype=np.float32)
            for alpha in alphas:
                key = (spec.name, float(alpha))
                intervention, _ = replay_masked_residual_sequence_variant(
                    model=model,
                    residual_head=residual_head,
                    snapshot=snapshot,
                    env_config=env_config,
                    variant=variant,
                    horizon=horizon,
                    response_dim=response_dim,
                    reference_actions=normal_actions_by_key[key],
                    base_reference_actions=base_normal_actions,
                    max_continuation_steps=max_continuation_steps,
                    alpha=float(alpha),
                    mask=mask_array,
                    device=resolved_device,
                )
                intervention_by_key[key] = intervention
                replay_rows.append(
                    {
                        **meta,
                        **intervention,
                        "mask_name": spec.name,
                        "mask_aliases": spec.aliases_text,
                        "mask_steer": float(spec.mask[0]),
                        "mask_throttle": float(spec.mask[1]),
                        "mask_brake": float(spec.mask[2]),
                        "branch": "intervention",
                        "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False)),
                    }
                )
        for spec in masks:
            for alpha in alphas:
                key = (spec.name, float(alpha))
                normal = normal_by_key[key]
                intervention = intervention_by_key[key]
                normal_margin = _finite_float(normal.get("min_clearance_margin"))
                intervention_margin = _finite_float(intervention.get("min_clearance_margin"))
                margin_gap = normal_margin - intervention_margin if np.isfinite(normal_margin) and np.isfinite(intervention_margin) else float("nan")
                objective_rows.append(
                    {
                        **meta,
                        "mask_name": spec.name,
                        "mask_aliases": spec.aliases_text,
                        "mask_steer": float(spec.mask[0]),
                        "mask_throttle": float(spec.mask[1]),
                        "mask_brake": float(spec.mask[2]),
                        "alpha": float(alpha),
                        "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False)),
                        "normal_success": bool(normal.get("success", False)),
                        "normal_collision": bool(normal.get("collision", False)),
                        "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                        "normal_margin": normal_margin,
                        "normal_first_action_drift_vs_base": _finite_float(normal.get("first_action_drift_vs_base_normal"), default=0.0),
                        "normal_prefix_l2_mean_vs_base": _finite_float(normal.get("prefix_l2_mean_vs_base_normal"), default=0.0),
                        "normal_masked_residual_abs_mean_steer": _finite_float(normal.get("masked_residual_abs_mean_steer")),
                        "normal_masked_residual_abs_mean_throttle": _finite_float(normal.get("masked_residual_abs_mean_throttle")),
                        "normal_masked_residual_abs_mean_brake": _finite_float(normal.get("masked_residual_abs_mean_brake")),
                        "normal_first_raw_residual_steer": _finite_float(normal.get("first_raw_residual_steer")),
                        "normal_first_raw_residual_throttle": _finite_float(normal.get("first_raw_residual_throttle")),
                        "normal_first_raw_residual_brake": _finite_float(normal.get("first_raw_residual_brake")),
                        "normal_first_masked_residual_steer": _finite_float(normal.get("first_masked_residual_steer")),
                        "normal_first_masked_residual_throttle": _finite_float(normal.get("first_masked_residual_throttle")),
                        "normal_first_masked_residual_brake": _finite_float(normal.get("first_masked_residual_brake")),
                        "normal_first_steer": _finite_float(normal.get("first_steer")),
                        "normal_first_throttle": _finite_float(normal.get("first_throttle")),
                        "normal_first_brake": _finite_float(normal.get("first_brake")),
                        "intervention_success": bool(intervention.get("success", False)),
                        "intervention_collision": bool(intervention.get("collision", False)),
                        "intervention_terminal_reason": str(intervention.get("terminal_reason", "")),
                        "intervention_margin": intervention_margin,
                        "margin_gap_from_normal": margin_gap,
                        "intervention_first_action_l2_from_normal": _finite_float(intervention.get("first_action_l2_from_reference")),
                        "intervention_prefix_l2_mean": _finite_float(intervention.get("prefix_l2_mean")),
                        "intervention_prefix_l2_max": _finite_float(intervention.get("prefix_l2_max")),
                        "intervention_trajectory_l2_mean": _finite_float(intervention.get("action_trajectory_distance_mean")),
                        "intervention_trajectory_l2_max": _finite_float(intervention.get("action_trajectory_distance_max")),
                        "intervention_first_raw_residual_steer": _finite_float(intervention.get("first_raw_residual_steer")),
                        "intervention_first_raw_residual_throttle": _finite_float(intervention.get("first_raw_residual_throttle")),
                        "intervention_first_raw_residual_brake": _finite_float(intervention.get("first_raw_residual_brake")),
                        "intervention_first_masked_residual_steer": _finite_float(intervention.get("first_masked_residual_steer")),
                        "intervention_first_masked_residual_throttle": _finite_float(intervention.get("first_masked_residual_throttle")),
                        "intervention_first_masked_residual_brake": _finite_float(intervention.get("first_masked_residual_brake")),
                    }
                )
    reconstructed_groups = {str(row["contrast_group_id"]) for row in objective_rows}
    reconstruction_rate = float(len(reconstructed_groups) / max(len(positives), 1))
    mask_alpha_rows = _mask_alpha_summary_rows(objective_rows, masks=masks, alphas=alphas)
    component_role_rows = _classify_component_roles(mask_alpha_rows)
    active_source_rows = [row for row in objective_rows if _active_boundary_key(row)]
    actionable_rows = [row for row in mask_alpha_rows if _bool(row.get("component_actionable_pareto"))]
    attribution_rows = [
        row for row in component_role_rows
        if _bool(row.get("harmful_component_evidence")) or _bool(row.get("useful_component_evidence"))
    ]
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_v4_residual_component_sensitivity(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        optimizer_started=False,
        ppo_used=False,
        promoted=False,
        metadata_missing_rows=metadata_missing_rows,
        reconstruction_success_rate=reconstruction_rate,
        actionable_count=len(actionable_rows),
        attribution_count=len(attribution_rows),
    )
    write_csv_rows(run_dir / "component_replay_rows.csv", replay_rows)
    write_csv_rows(run_dir / "component_objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "mask_alpha_metrics.csv", mask_alpha_rows)
    write_csv_rows(run_dir / "active_source_metrics.csv", active_source_rows)
    write_csv_rows(run_dir / "component_role_metrics.csv", component_role_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "v4_residual_component_sensitivity",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(reconstructed_groups)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "rejected_rows": int(len(rejected_rows)),
        "component_replay_rows": int(len(replay_rows)),
        "component_objective_rows": int(len(objective_rows)),
        "active_source_rows": int(len(active_source_rows)),
        "masks": [spec.name for spec in masks],
        "mask_aliases": {spec.name: list(spec.aliases) for spec in masks if spec.aliases},
        "alphas": [float(alpha) for alpha in alphas],
        "actionable_mask_count": int(len(actionable_rows)),
        "actionable_masks": [
            {"mask_name": row["mask_name"], "alpha": row["alpha"]}
            for row in actionable_rows
        ],
        "attribution_component_count": int(len(attribution_rows)),
        "attribution_components": [
            str(row.get("component", ""))
            for row in attribution_rows
        ],
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "base_residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_residual_head_checksum_before": residual_checksum_before,
        "base_residual_head_checksum_after": residual_checksum_after,
        "optimizer_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "mask_alpha_metrics_csv": run_dir / "mask_alpha_metrics.csv",
        "component_replay_rows_csv": run_dir / "component_replay_rows.csv",
        "component_objective_rows_csv": run_dir / "component_objective_rows.csv",
        "active_source_metrics_csv": run_dir / "active_source_metrics.csv",
        "component_role_metrics_csv": run_dir / "component_role_metrics.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training M761 residual component sensitivity probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--masks", type=_parse_mask_names, default=DEFAULT_MASKS)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    summary = run_v4_residual_component_sensitivity(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        masks=tuple(args.masks),
        alphas=tuple(args.alphas),
        max_rows=args.max_rows,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
