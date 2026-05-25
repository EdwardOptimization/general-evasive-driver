"""No-training wrong-cross-fault history intervention replay for v4."""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, FaultSpec, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.sequence_command_response_intervention import corrupt_sequence_observation
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import relocate_temporal_snapshot
from autodrift.temporal_action_response_mismatch import TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_extreme_hidden_dynamics_data_route import (
    IdentityResidualGate,
    HISTORY_VARIANTS,
    fault_onset_bucket,
    matched_pair_diversity_metrics,
)
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import (
    WARMUP_MODES,
    build_fault_variants,
    collect_warmup_snapshots,
)
from autodrift.v4_normal_margin_residual_calibration import calibrated_action_from_hidden
from autodrift.v4_residual_closed_loop_replay import _load_residual_head


WRONG_HISTORY_VARIANT = "wrong_cross_fault_hidden"
REPLAY_VARIANTS = (*HISTORY_VARIANTS, WRONG_HISTORY_VARIANT)

PAIR_SOURCE_FIELDS = [
    "pair_id",
    "left_candidate_id",
    "right_candidate_id",
    "left_source_group_id",
    "right_source_group_id",
    "left_seed",
    "right_seed",
    "left_fault_family",
    "right_fault_family",
    "left_fidelity_class",
    "right_fidelity_class",
    "left_warmup_mode",
    "right_warmup_mode",
    "left_onset_bucket",
    "right_onset_bucket",
    "ego_response_distance",
    "obstacle_geometry_distance",
    "first_action_l2",
    "normal_margin_gap_abs",
]

REPLAY_FIELDS = [
    *PAIR_SOURCE_FIELDS,
    "variant",
    "horizon",
    "alpha",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "variant_success",
    "variant_collision",
    "variant_margin",
    "margin_gap_from_normal",
    "success_drop_from_normal",
    "first_action_l2_vs_normal",
    "prefix_l2_mean_vs_normal",
    "prefix_l2_max_vs_normal",
    "first_action_l2_to_right",
    "normal_left_to_right_first_l2",
    "wrong_history_closer_to_right_action",
    "terminal_reason",
    "steps",
]

ACCEPTED_FIELDS = [
    *PAIR_SOURCE_FIELDS,
    "accepted_class",
    "accepted_reason",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "wrong_success",
    "wrong_collision",
    "wrong_margin",
    "wrong_margin_gap_from_normal",
    "wrong_first_action_l2_vs_normal",
    "wrong_prefix_l2_mean_vs_normal",
    "wrong_history_closer_to_right_action",
    "zero_command_margin_gap",
    "wrong_to_zero_gap_ratio",
]

GATE_SUMMARY_FIELDS = ["gate_name", "value", "threshold", "passed", "notes"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_int(value: Any, default: int = -1) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _action_l2(left: np.ndarray | None, right: np.ndarray | None) -> float:
    if left is None or right is None:
        return float("nan")
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.shape != right_array.shape or not np.all(np.isfinite(left_array)) or not np.all(np.isfinite(right_array)):
        return float("nan")
    return float(np.linalg.norm(left_array - right_array))


def _prefix_l2(actions: list[np.ndarray], reference: list[np.ndarray] | None, horizon: int) -> dict[str, Any]:
    if reference is None:
        return {"prefix_l2_mean": float("nan"), "prefix_l2_max": float("nan"), "prefix_compare_steps": 0}
    steps = min(len(actions), len(reference), int(horizon))
    if steps <= 0:
        return {"prefix_l2_mean": float("nan"), "prefix_l2_max": float("nan"), "prefix_compare_steps": 0}
    values = np.linalg.norm(
        np.asarray(actions[:steps], dtype=np.float64) - np.asarray(reference[:steps], dtype=np.float64),
        axis=1,
    )
    return {
        "prefix_l2_mean": float(np.mean(values)),
        "prefix_l2_max": float(np.max(values)),
        "prefix_compare_steps": int(steps),
    }


def build_pair_source_rows(
    matched_pair_rows: list[dict[str, str]],
    plan_rows: list[dict[str, str]],
    *,
    max_pairs: int,
    max_ego_distance: float,
    max_obstacle_distance: float,
    min_first_action_l2: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    plan_by_id = {str(_as_int(row.get("candidate_id"))): row for row in plan_rows}
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    ordered = sorted(
        matched_pair_rows,
        key=lambda row: (
            str(row.get("left_fault_family", "")),
            str(row.get("right_fault_family", "")),
            _as_float(row.get("ego_response_distance"), default=999.0),
            _as_float(row.get("obstacle_geometry_distance"), default=999.0),
            -_as_float(row.get("first_action_l2"), default=-1.0),
            _as_int(row.get("pair_id"), 0),
        ),
    )
    for row in ordered:
        left_plan = plan_by_id.get(str(_as_int(row.get("left_candidate_id"))))
        right_plan = plan_by_id.get(str(_as_int(row.get("right_candidate_id"))))
        meta = {
            "pair_id": _as_int(row.get("pair_id"), len(selected) + len(rejected)),
            "left_candidate_id": _as_int(row.get("left_candidate_id")),
            "right_candidate_id": _as_int(row.get("right_candidate_id")),
            "left_seed": _as_int(row.get("left_seed")),
            "right_seed": _as_int(row.get("right_seed")),
            "left_fault_family": str(row.get("left_fault_family", "")),
            "right_fault_family": str(row.get("right_fault_family", "")),
            "left_fidelity_class": str(row.get("left_fidelity_class", "")),
            "right_fidelity_class": str(row.get("right_fidelity_class", "")),
            "left_warmup_mode": str(row.get("left_warmup_mode", "")),
            "right_warmup_mode": str(row.get("right_warmup_mode", "")),
            "left_onset_bucket": str(row.get("left_onset_bucket", "")),
            "right_onset_bucket": str(row.get("right_onset_bucket", "")),
            "ego_response_distance": _as_float(row.get("ego_response_distance")),
            "obstacle_geometry_distance": _as_float(row.get("obstacle_geometry_distance")),
            "first_action_l2": _as_float(row.get("first_action_l2")),
            "normal_margin_gap_abs": _as_float(row.get("normal_margin_gap_abs")),
        }
        if left_plan is None or right_plan is None:
            rejected.append({**meta, "rejection_reason": "missing_plan_row"})
            continue
        if str(meta["left_fault_family"]) == str(meta["right_fault_family"]):
            rejected.append({**meta, "rejection_reason": "same_fault_family"})
            continue
        if _as_float(meta["ego_response_distance"], default=999.0) > float(max_ego_distance):
            rejected.append({**meta, "rejection_reason": "ego_distance_too_large"})
            continue
        if _as_float(meta["obstacle_geometry_distance"], default=999.0) > float(max_obstacle_distance):
            rejected.append({**meta, "rejection_reason": "obstacle_distance_too_large"})
            continue
        if _as_float(meta["first_action_l2"], default=0.0) < float(min_first_action_l2):
            rejected.append({**meta, "rejection_reason": "first_action_gap_too_small"})
            continue
        if "future_only" in {str(meta["left_fidelity_class"]), str(meta["right_fidelity_class"])}:
            rejected.append({**meta, "rejection_reason": "future_only_fidelity"})
            continue
        enriched = {
            **meta,
            "left_source_group_id": _as_int(left_plan.get("source_group_id")),
            "right_source_group_id": _as_int(right_plan.get("source_group_id")),
            "left_snapshot_uid": str(left_plan.get("snapshot_uid", "")),
            "right_snapshot_uid": str(right_plan.get("snapshot_uid", "")),
            "left_step": _as_int(left_plan.get("step")),
            "right_step": _as_int(right_plan.get("step")),
            "left_plan": left_plan,
            "right_plan": right_plan,
        }
        limits = {
            ("left_seed", str(enriched["left_seed"])): 64,
            ("right_seed", str(enriched["right_seed"])): 64,
            ("fault_pair", f"{enriched['left_fault_family']}->{enriched['right_fault_family']}"): 32,
            ("warmup_pair", f"{enriched['left_warmup_mode']}->{enriched['right_warmup_mode']}"): 64,
        }
        if any(counts.get(key, 0) >= limit for key, limit in limits.items()):
            rejected.append({**meta, "rejection_reason": "source_balance_limit"})
            continue
        selected.append(enriched)
        for key in limits:
            counts[key] = counts.get(key, 0) + 1
        if len(selected) >= int(max_pairs):
            break
    return selected, rejected


def _source_group_from_source_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "source_group_id": _as_int(row.get("source_group_id")),
        "seed": _as_int(row.get("seed")),
        "warmup_mode": str(row.get("warmup_mode", "")),
        "preferred_fault": str(row.get("preferred_fault", "")),
        "preferred_fault_family": str(row.get("preferred_fault_family", "")),
        "preferred_fault_severity": str(row.get("preferred_fault_severity", "")),
        "wrong_fault": str(row.get("wrong_fault", "nominal")),
        "wrong_fault_family": str(row.get("wrong_fault_family", "nominal")),
        "fault_family_pair": str(row.get("fault_family_pair", "")),
        "source_axis": str(row.get("source_axis", "source_state")),
        "fault_activation_step_delta": _as_int(row.get("fault_activation_step_delta"), 0),
        "fault_severity_delta": _as_float(row.get("fault_severity_delta"), 0.0),
        "fault_param_key": str(row.get("fault_param_key", "")),
        "modified_fault_params_json": str(row.get("modified_fault_params_json", "")),
        "preferred_fidelity_class": str(row.get("preferred_fidelity_class", "")),
        "wrong_fidelity_class": str(row.get("wrong_fidelity_class", "")),
    }


def reconstruct_snapshots(
    *,
    pair_source_rows: list[dict[str, Any]],
    source_rows: list[dict[str, str]],
    fault_by_name: dict[str, FaultSpec],
    model: Any,
    residual_head: nn.Module,
    env_config: Any,
    scenario_config: dict[str, Any],
    alpha: float,
    min_step: int,
    max_steps: int,
    snapshot_stride: int,
    max_snapshots_per_group: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    device: torch.device,
) -> tuple[dict[tuple[int, int], TemporalSnapshot], list[dict[str, Any]], list[dict[str, Any]]]:
    source_by_group = {_as_int(row.get("source_group_id")): row for row in source_rows}
    needed = sorted(
        {
            (int(row["left_source_group_id"]), int(row["left_step"]))
            for row in pair_source_rows
        }
        | {
            (int(row["right_source_group_id"]), int(row["right_step"]))
            for row in pair_source_rows
        }
    )
    needed_by_group: dict[int, set[int]] = {}
    for group_id, step in needed:
        needed_by_group.setdefault(int(group_id), set()).add(int(step))
    snapshots: dict[tuple[int, int], TemporalSnapshot] = {}
    snapshot_rows: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for group_id, steps in sorted(needed_by_group.items()):
        source_row = source_by_group.get(group_id)
        if source_row is None:
            for step in steps:
                rejected.append({"source_group_id": group_id, "step": step, "rejection_reason": "missing_source_row"})
            continue
        source_group = _source_group_from_source_row(source_row)
        fault_name = str(source_group["preferred_fault"])
        fault = fault_by_name.get(fault_name)
        if fault is None:
            for step in steps:
                rejected.append({"source_group_id": group_id, "step": step, "rejection_reason": f"missing_fault:{fault_name}"})
            continue
        collected, _, _ = collect_warmup_snapshots(
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            fault=fault,
            source_group=source_group,
            alpha=float(alpha),
            min_step=int(min_step),
            max_steps=int(max_steps),
            snapshot_stride=int(snapshot_stride),
            max_snapshots_per_group=int(max_snapshots_per_group),
            obstacle_longitudinal_min=float(scenario_config.get("obstacle_longitudinal_min", -14.0)),
            obstacle_longitudinal_max=float(scenario_config.get("obstacle_longitudinal_max", 115.0)),
            history_window_steps=int(scenario_config.get("temporal_history_window_steps", 30)),
            warmup_steps=int(warmup_steps),
            steer_amplitude=float(steer_amplitude),
            brake_amplitude=float(brake_amplitude),
            period_steps=int(warmup_period_steps),
            start_snapshot_id=int(group_id) * int(max_snapshots_per_group),
            device=device,
        )
        by_step = {int(snapshot.step): snapshot for snapshot in collected}
        for step in steps:
            snapshot = by_step.get(int(step))
            if snapshot is None:
                rejected.append({"source_group_id": group_id, "step": step, "rejection_reason": "snapshot_step_not_reconstructed"})
                continue
            snapshots[(int(group_id), int(step))] = snapshot
            snapshot_rows.append(
                {
                    "source_group_id": int(group_id),
                    "step": int(step),
                    "snapshot_id": int(snapshot.snapshot_id),
                    "seed": int(snapshot.seed),
                    "fault": snapshot.fault.name,
                    "fault_family": snapshot.fault.family,
                    "fidelity_class": snapshot.fault.fidelity_class,
                    "warmup_mode": str(source_group["warmup_mode"]),
                    "history_observations": int(len(snapshot.history_observations)),
                }
            )
    return snapshots, snapshot_rows, rejected


def replay_variant_with_hidden(
    *,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    snapshot: TemporalSnapshot,
    env_config: Any,
    variant: str,
    initial_hidden: torch.Tensor,
    horizon: int,
    response_dim: int,
    reference_actions: list[np.ndarray] | None,
    right_reference_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = initial_hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    raw_history: list[np.ndarray] = [obs.copy()]
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for step_index in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        if variant in {"zero_command_obs", "command_shift_obs", "response_delay_obs"}:
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
        action, next_hidden, _base_action, _raw_delta, _calibrated_delta, _gate = calibrated_action_from_hidden(
            model,
            residual_head,
            identity_gate,
            policy_obs,
            hidden,
            alpha=float(alpha),
            device=device,
        )
        actions.append(action)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        raw_history.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else None
    if variant == "normal":
        trajectory_distances = zero_action_trajectory_distances(len(actions))
        prefix = {"prefix_l2_mean": 0.0, "prefix_l2_max": 0.0, "prefix_compare_steps": min(len(actions), int(horizon))}
    else:
        trajectory_distances = action_trajectory_distances(actions, reference_actions)
        prefix = _prefix_l2(actions, reference_actions, int(horizon))
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    first_to_right = _action_l2(first_action, right_reference_actions[0] if right_reference_actions else None)
    first_to_normal = _action_l2(first_action, reference_actions[0] if reference_actions else None)
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
        "first_steer": float(first_action[0]) if first_action is not None else float("nan"),
        "first_throttle": float(first_action[1]) if first_action is not None else float("nan"),
        "first_brake": float(first_action[2]) if first_action is not None else float("nan"),
        "first_action_l2_vs_normal": first_to_normal if variant != "normal" else 0.0,
        "first_action_l2_to_right": first_to_right,
        **trajectory_distances,
        **prefix,
    }, actions


def _row_meta(pair: dict[str, Any]) -> dict[str, Any]:
    return {key: pair.get(key, "") for key in PAIR_SOURCE_FIELDS}


def build_replay_rows_for_pair(
    *,
    pair: dict[str, Any],
    left_snapshot: TemporalSnapshot,
    right_snapshot: TemporalSnapshot,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    env_config: Any,
    response_dim: int,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    left_plan = pair["left_plan"]
    right_plan = pair["right_plan"]
    left_relocated = relocate_temporal_snapshot(
        left_snapshot,
        body_longitudinal=_as_float(left_plan.get("target_obstacle_body_x")),
        body_lateral=_as_float(left_plan.get("target_obstacle_body_y")),
        half_width=_as_float(left_plan.get("target_obstacle_half_width")),
    )
    right_relocated = relocate_temporal_snapshot(
        right_snapshot,
        body_longitudinal=_as_float(right_plan.get("target_obstacle_body_x")),
        body_lateral=_as_float(right_plan.get("target_obstacle_body_y")),
        half_width=_as_float(right_plan.get("target_obstacle_half_width")),
    )
    horizon = _as_int(left_plan.get("horizon"), 6)
    right_normal, right_actions = replay_variant_with_hidden(
        model=model,
        residual_head=residual_head,
        identity_gate=identity_gate,
        snapshot=right_relocated,
        env_config=env_config,
        variant="normal",
        initial_hidden=right_relocated.hidden,
        horizon=horizon,
        response_dim=response_dim,
        reference_actions=None,
        right_reference_actions=None,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(alpha),
        device=device,
    )
    normal, normal_actions = replay_variant_with_hidden(
        model=model,
        residual_head=residual_head,
        identity_gate=identity_gate,
        snapshot=left_relocated,
        env_config=env_config,
        variant="normal",
        initial_hidden=left_relocated.hidden,
        horizon=horizon,
        response_dim=response_dim,
        reference_actions=None,
        right_reference_actions=right_actions,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(alpha),
        device=device,
    )
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    normal_success = parse_bool(normal.get("success", False))
    normal_collision = parse_bool(normal.get("collision", False))
    normal_left_to_right = _action_l2(normal_actions[0] if normal_actions else None, right_actions[0] if right_actions else None)
    variant_hiddens = {
        "reset_hidden_then_normal": model.initial_hidden(1, device),
        "reset_hidden_each_step": model.initial_hidden(1, device),
        "zero_command_obs": left_relocated.hidden,
        "command_shift_obs": left_relocated.hidden,
        "response_delay_obs": left_relocated.hidden,
        WRONG_HISTORY_VARIANT: right_relocated.hidden,
    }
    rows: list[dict[str, Any]] = []
    meta = _row_meta(pair)
    for variant in ("normal", *REPLAY_VARIANTS):
        if variant == "normal":
            result = normal
            actions = normal_actions
        else:
            result, actions = replay_variant_with_hidden(
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                snapshot=left_relocated,
                env_config=env_config,
                variant=variant,
                initial_hidden=variant_hiddens[variant],
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=normal_actions,
                right_reference_actions=right_actions,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=device,
            )
        variant_margin = _finite_float(result.get("min_clearance_margin"))
        margin_gap = normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) else float("nan")
        first_to_right = _finite_float(result.get("first_action_l2_to_right"))
        closer = bool(
            variant == WRONG_HISTORY_VARIANT
            and np.isfinite(first_to_right)
            and np.isfinite(normal_left_to_right)
            and first_to_right < normal_left_to_right
        )
        rows.append(
            {
                **meta,
                "variant": variant,
                "horizon": horizon,
                "alpha": float(alpha),
                "normal_success": normal_success,
                "normal_collision": normal_collision,
                "normal_margin": normal_margin,
                "variant_success": parse_bool(result.get("success", False)),
                "variant_collision": parse_bool(result.get("collision", False)),
                "variant_margin": variant_margin,
                "margin_gap_from_normal": margin_gap if variant != "normal" else 0.0,
                "success_drop_from_normal": bool(normal_success and not parse_bool(result.get("success", False))),
                "first_action_l2_vs_normal": _finite_float(result.get("first_action_l2_vs_normal"), default=0.0),
                "prefix_l2_mean_vs_normal": _finite_float(result.get("prefix_l2_mean"), default=0.0),
                "prefix_l2_max_vs_normal": _finite_float(result.get("prefix_l2_max"), default=0.0),
                "first_action_l2_to_right": first_to_right,
                "normal_left_to_right_first_l2": normal_left_to_right,
                "wrong_history_closer_to_right_action": closer,
                "terminal_reason": str(result.get("terminal_reason", "")),
                "steps": int(result.get("steps", 0)),
            }
        )
    return rows, [{"pair_id": pair["pair_id"], "right_normal_margin": _finite_float(right_normal.get("min_clearance_margin"))}]


def accepted_wrong_history_rows_for_pair(
    pair_rows: list[dict[str, Any]],
    *,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    require_closer_to_right: bool,
) -> list[dict[str, Any]]:
    by_variant = {str(row.get("variant", "")): row for row in pair_rows}
    normal = by_variant.get("normal", {})
    wrong = by_variant.get(WRONG_HISTORY_VARIANT)
    if wrong is None:
        return []
    zero = by_variant.get("zero_command_obs", {})
    normal_margin = _finite_float(normal.get("normal_margin"))
    wrong_margin = _finite_float(wrong.get("variant_margin"))
    wrong_gap = _finite_float(wrong.get("margin_gap_from_normal"))
    wrong_action = max(
        _finite_float(wrong.get("first_action_l2_vs_normal"), default=float("nan")),
        _finite_float(wrong.get("prefix_l2_mean_vs_normal"), default=float("nan")),
    )
    zero_gap = _finite_float(zero.get("margin_gap_from_normal"))
    ratio = wrong_gap / zero_gap if np.isfinite(wrong_gap) and np.isfinite(zero_gap) and abs(zero_gap) > 1e-12 else float("nan")
    closer = parse_bool(wrong.get("wrong_history_closer_to_right_action", False))
    normal_ok = bool(
        not parse_bool(normal.get("normal_collision", False))
        and np.isfinite(normal_margin)
    )
    action_ok = bool(np.isfinite(wrong_action) and wrong_action >= float(action_l2_threshold))
    closer_ok = bool((not require_closer_to_right) or closer)
    base = {
        **_row_meta(wrong),
        "normal_success": parse_bool(normal.get("normal_success", False)),
        "normal_collision": parse_bool(normal.get("normal_collision", False)),
        "normal_margin": normal_margin,
        "wrong_success": parse_bool(wrong.get("variant_success", False)),
        "wrong_collision": parse_bool(wrong.get("variant_collision", False)),
        "wrong_margin": wrong_margin,
        "wrong_margin_gap_from_normal": wrong_gap,
        "wrong_first_action_l2_vs_normal": _finite_float(wrong.get("first_action_l2_vs_normal")),
        "wrong_prefix_l2_mean_vs_normal": _finite_float(wrong.get("prefix_l2_mean_vs_normal")),
        "wrong_history_closer_to_right_action": closer,
        "zero_command_margin_gap": zero_gap,
        "wrong_to_zero_gap_ratio": ratio,
    }
    accepted: list[dict[str, Any]] = []
    if normal_ok and np.isfinite(wrong_gap) and wrong_gap >= float(primary_margin_gap_threshold) and action_ok and closer_ok:
        accepted.append({**base, "accepted_class": "primary_wrong_history", "accepted_reason": "wrong_history_margin_action_degradation"})
    if (
        parse_bool(normal.get("normal_success", False))
        and (parse_bool(wrong.get("variant_collision", False)) or parse_bool(wrong.get("success_drop_from_normal", False)))
        and np.isfinite(wrong_gap)
        and wrong_gap >= float(primary_margin_gap_threshold)
    ):
        accepted.append({**base, "accepted_class": "outcome_wrong_history", "accepted_reason": "wrong_history_outcome_drop"})
    if np.isfinite(normal_margin) and np.isfinite(wrong_gap) and wrong_gap >= float(mitigation_margin_gap_threshold):
        accepted.append({**base, "accepted_class": "mitigation_wrong_history", "accepted_reason": "wrong_history_worse_mitigation_margin"})
    return accepted


def _diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": int(len(rows)),
        "unique_left_seed_count": unique_count(rows, "left_seed"),
        "unique_right_seed_count": unique_count(rows, "right_seed"),
        "unique_fault_family_pair_count": int(
            len({f"{row.get('left_fault_family', '')}->{row.get('right_fault_family', '')}" for row in rows})
        ),
        "unique_warmup_pair_count": int(
            len({f"{row.get('left_warmup_mode', '')}->{row.get('right_warmup_mode', '')}" for row in rows})
        ),
        "unique_onset_pair_count": int(
            len({f"{row.get('left_onset_bucket', '')}->{row.get('right_onset_bucket', '')}" for row in rows})
        ),
        "unique_fidelity_pair_count": int(
            len({f"{row.get('left_fidelity_class', '')}->{row.get('right_fidelity_class', '')}" for row in rows})
        ),
        "max_left_seed_dominance": max_share(rows, "left_seed"),
        "max_right_seed_dominance": max_share(rows, "right_seed"),
        "max_left_fault_family_dominance": max_share(rows, "left_fault_family"),
        "max_right_fault_family_dominance": max_share(rows, "right_fault_family"),
    }


def classify_wrong_history_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    reconstructed_pairs: int,
    selected_pairs: int,
    accepted_primary_rows: list[dict[str, Any]],
    zero_command_accepted_like_rows: int,
    min_primary_rows: int,
    min_left_seeds: int,
    min_right_seeds: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    max_seed_dominance: float,
    max_fault_pair_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_wrong_cross_fault_history_intervention_contract_violation"
    if int(selected_pairs) <= 0 or int(reconstructed_pairs) < max(1, int(0.5 * int(selected_pairs))):
        return "v4_wrong_cross_fault_history_intervention_reconstruction_failure"
    if not accepted_primary_rows and int(zero_command_accepted_like_rows) > 0:
        return "v4_wrong_cross_fault_history_intervention_zero_command_dominated"
    if not accepted_primary_rows:
        return "v4_wrong_cross_fault_history_intervention_history_insensitive"
    metrics = _diversity(accepted_primary_rows)
    passed = bool(
        len(accepted_primary_rows) >= int(min_primary_rows)
        and metrics["unique_left_seed_count"] >= int(min_left_seeds)
        and metrics["unique_right_seed_count"] >= int(min_right_seeds)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["unique_warmup_pair_count"] >= int(min_warmup_pairs)
        and metrics["unique_onset_pair_count"] >= int(min_onset_pairs)
        and metrics["max_left_seed_dominance"] <= float(max_seed_dominance)
        and metrics["max_right_seed_dominance"] <= float(max_seed_dominance)
        and metrics["max_left_fault_family_dominance"] <= float(max_fault_pair_dominance)
        and metrics["max_right_fault_family_dominance"] <= float(max_fault_pair_dominance)
    )
    if passed:
        return "v4_wrong_cross_fault_history_intervention_pass"
    return "v4_wrong_cross_fault_history_intervention_sparse"


def _gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_name": "actor_checksum_unchanged",
            "value": not bool(summary["actor_backbone_changed"]),
            "threshold": "true",
            "passed": not bool(summary["actor_backbone_changed"]),
            "notes": "no actor training allowed",
        },
        {
            "gate_name": "residual_head_checksum_unchanged",
            "value": not bool(summary["residual_head_changed"]),
            "threshold": "true",
            "passed": not bool(summary["residual_head_changed"]),
            "notes": "no residual-head training allowed",
        },
        {
            "gate_name": "wrong_history_primary_rows",
            "value": summary["accepted_primary_wrong_history_rows"],
            "threshold": summary["min_primary_rows"],
            "passed": int(summary["accepted_primary_wrong_history_rows"]) >= int(summary["min_primary_rows"]),
            "notes": "zero-command rows are counted separately",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M828 cannot promote",
        },
    ]


def run_wrong_cross_fault_history_intervention(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    matched_pairs_path: Path,
    candidate_plan_rows_path: Path,
    source_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_pairs: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_snapshots_per_group: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    max_ego_distance: float,
    max_obstacle_distance: float,
    min_first_action_l2: float,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    require_closer_to_right: bool,
    min_primary_rows: int,
    min_left_seeds: int,
    min_right_seeds: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    max_seed_dominance: float,
    max_fault_pair_dominance: float,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M828 wrong-history intervention requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_head.eval()
    for parameter in residual_head.parameters():
        parameter.requires_grad_(False)
    residual_checksum_before = model_parameter_checksum(residual_head)
    identity_gate = IdentityResidualGate().to(resolved_device)
    response_dim = response_feature_dim_for_model(model)

    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    matched_pair_rows = read_csv_rows(matched_pairs_path)
    plan_rows = read_csv_rows(candidate_plan_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    pair_source_rows, pair_rejections = build_pair_source_rows(
        matched_pair_rows,
        plan_rows,
        max_pairs=int(max_pairs),
        max_ego_distance=float(max_ego_distance),
        max_obstacle_distance=float(max_obstacle_distance),
        min_first_action_l2=float(min_first_action_l2),
    )
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=pair_source_rows,
        source_rows=source_rows,
        fault_by_name=fault_by_name,
        model=model,
        residual_head=residual_head,
        env_config=env_config,
        scenario_config=scenario_config,
        alpha=float(alpha),
        min_step=int(min_step),
        max_steps=int(max_steps),
        snapshot_stride=int(snapshot_stride),
        max_snapshots_per_group=int(max_snapshots_per_group),
        warmup_steps=int(warmup_steps),
        steer_amplitude=float(steer_amplitude),
        brake_amplitude=float(brake_amplitude),
        warmup_period_steps=int(warmup_period_steps),
        device=resolved_device,
    )

    replay_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    for pair in pair_source_rows:
        left_key = (int(pair["left_source_group_id"]), int(pair["left_step"]))
        right_key = (int(pair["right_source_group_id"]), int(pair["right_step"]))
        left_snapshot = snapshots.get(left_key)
        right_snapshot = snapshots.get(right_key)
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**_row_meta(pair), "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        try:
            rows, _right_meta = build_replay_rows_for_pair(
                pair=pair,
                left_snapshot=left_snapshot,
                right_snapshot=right_snapshot,
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**_row_meta(pair), "rejection_reason": f"replay_error:{type(exc).__name__}"})
            continue
        replay_rows.extend(rows)
        accepted_rows.extend(
            accepted_wrong_history_rows_for_pair(
                rows,
                primary_margin_gap_threshold=float(primary_margin_gap_threshold),
                mitigation_margin_gap_threshold=float(mitigation_margin_gap_threshold),
                action_l2_threshold=float(action_l2_threshold),
                require_closer_to_right=bool(require_closer_to_right),
            )
        )
        _append_progress(
            progress_path,
            {
                "pair_id": int(pair["pair_id"]),
                "stage": "replay",
                "rows": len(rows),
                "accepted_rows": sum(1 for row in accepted_rows if int(row.get("pair_id", -1)) == int(pair["pair_id"])),
            },
        )

    accepted_primary = [row for row in accepted_rows if row.get("accepted_class") == "primary_wrong_history"]
    accepted_mitigation = [row for row in accepted_rows if row.get("accepted_class") == "mitigation_wrong_history"]
    zero_command_accepted_like = [
        row
        for row in replay_rows
        if row.get("variant") == "zero_command_obs"
        and _finite_float(row.get("margin_gap_from_normal")) >= float(primary_margin_gap_threshold)
        and _finite_float(row.get("first_action_l2_vs_normal")) >= float(action_l2_threshold)
    ]
    reconstructed_pair_ids = {int(row["pair_id"]) for row in replay_rows}
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_wrong_history_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        reconstructed_pairs=len(reconstructed_pair_ids),
        selected_pairs=len(pair_source_rows),
        accepted_primary_rows=accepted_primary,
        zero_command_accepted_like_rows=len(zero_command_accepted_like),
        min_primary_rows=int(min_primary_rows),
        min_left_seeds=int(min_left_seeds),
        min_right_seeds=int(min_right_seeds),
        min_fault_pairs=int(min_fault_pairs),
        min_warmup_pairs=int(min_warmup_pairs),
        min_onset_pairs=int(min_onset_pairs),
        max_seed_dominance=float(max_seed_dominance),
        max_fault_pair_dominance=float(max_fault_pair_dominance),
    )
    diversity_summary = {
        "pair_source_rows": matched_pair_diversity_metrics(pair_source_rows),
        "accepted_primary_wrong_history": _diversity(accepted_primary),
        "accepted_mitigation_wrong_history": _diversity(accepted_mitigation),
        "zero_command_accepted_like": _diversity(zero_command_accepted_like),
    }
    all_rejections = [*pair_rejections, *snapshot_rejections, *replay_rejections]

    write_csv_rows(run_dir / "pair_source_rows.csv", [{k: v for k, v in row.items() if k not in {"left_plan", "right_plan"}} for row in pair_source_rows], fieldnames=PAIR_SOURCE_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "wrong_history_replay_rows.csv", replay_rows, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_wrong_history_rows.csv", accepted_primary, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_mitigation_rows.csv", accepted_mitigation, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "rejected_pair_rows.csv", all_rejections)
    write_json(run_dir / "diversity_summary.json", diversity_summary)
    (run_dir / "fault_proxy_limitations.md").write_text(
        "M828 uses current-model and current-model-proxy faults only. Proxy rows are not true wheel-level physical claims.\n",
        encoding="utf-8",
    )

    summary = {
        "run_type": "v4_wrong_cross_fault_history_intervention",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "matched_pairs": matched_pairs_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "source_rows": source_rows_path,
        "alpha": float(alpha),
        "raw_matched_pair_rows": int(len(matched_pair_rows)),
        "selected_pair_rows": int(len(pair_source_rows)),
        "reconstructed_snapshot_rows": int(len(snapshot_rows)),
        "reconstructed_pairs": int(len(reconstructed_pair_ids)),
        "wrong_history_replay_rows": int(len(replay_rows)),
        "accepted_primary_wrong_history_rows": int(len(accepted_primary)),
        "accepted_mitigation_rows": int(len(accepted_mitigation)),
        "zero_command_accepted_like_rows": int(len(zero_command_accepted_like)),
        "rejected_pair_rows": int(len(all_rejections)),
        "primary_margin_gap_threshold": float(primary_margin_gap_threshold),
        "mitigation_margin_gap_threshold": float(mitigation_margin_gap_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "require_closer_to_right": bool(require_closer_to_right),
        "min_primary_rows": int(min_primary_rows),
        "diversity_summary_json": run_dir / "diversity_summary.json",
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "residual_head_checksum_before": residual_checksum_before,
        "residual_head_checksum_after": residual_checksum_after,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "summary_json": run_dir / "summary.json",
        "pair_source_rows_csv": run_dir / "pair_source_rows.csv",
        "wrong_history_replay_rows_csv": run_dir / "wrong_history_replay_rows.csv",
        "accepted_wrong_history_rows_csv": run_dir / "accepted_wrong_history_rows.csv",
        "accepted_mitigation_rows_csv": run_dir / "accepted_mitigation_rows.csv",
        "rejected_pair_rows_csv": run_dir / "rejected_pair_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training wrong-cross-fault history intervention replay.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--matched-pairs", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-pairs", type=int, default=128)
    parser.add_argument("--max-base-faults", type=int, default=10)
    parser.add_argument("--max-fault-specs", type=int, default=18)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=24)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--max-ego-distance", type=float, default=0.08)
    parser.add_argument("--max-obstacle-distance", type=float, default=0.08)
    parser.add_argument("--min-first-action-l2", type=float, default=0.02)
    parser.add_argument("--primary-margin-gap-threshold", type=float, default=0.01)
    parser.add_argument("--mitigation-margin-gap-threshold", type=float, default=0.02)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--no-require-closer-to-right", action="store_true")
    parser.add_argument("--min-primary-rows", type=int, default=80)
    parser.add_argument("--min-left-seeds", type=int, default=8)
    parser.add_argument("--min-right-seeds", type=int, default=8)
    parser.add_argument("--min-fault-pairs", type=int, default=8)
    parser.add_argument("--min-warmup-pairs", type=int, default=3)
    parser.add_argument("--min-onset-pairs", type=int, default=4)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.30)
    args = parser.parse_args()

    scenario_config = load_scenario_config(args.scenario_config)
    max_steps = int(args.max_steps) if args.max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step = int(args.min_step) if args.min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride = int(args.snapshot_stride) if args.snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    max_continuation_steps = (
        int(args.max_continuation_steps)
        if args.max_continuation_steps is not None
        else int(scenario_config.get("max_continuation_steps", 70))
    )
    summary = run_wrong_cross_fault_history_intervention(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        matched_pairs_path=args.matched_pairs,
        candidate_plan_rows_path=args.candidate_plan_rows,
        source_rows_path=args.source_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_pairs=int(args.max_pairs),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        max_ego_distance=float(args.max_ego_distance),
        max_obstacle_distance=float(args.max_obstacle_distance),
        min_first_action_l2=float(args.min_first_action_l2),
        primary_margin_gap_threshold=float(args.primary_margin_gap_threshold),
        mitigation_margin_gap_threshold=float(args.mitigation_margin_gap_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        require_closer_to_right=not bool(args.no_require_closer_to_right),
        min_primary_rows=int(args.min_primary_rows),
        min_left_seeds=int(args.min_left_seeds),
        min_right_seeds=int(args.min_right_seeds),
        min_fault_pairs=int(args.min_fault_pairs),
        min_warmup_pairs=int(args.min_warmup_pairs),
        min_onset_pairs=int(args.min_onset_pairs),
        max_seed_dominance=float(args.max_seed_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
