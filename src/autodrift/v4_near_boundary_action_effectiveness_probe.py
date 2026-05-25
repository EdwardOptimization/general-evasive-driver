"""No-training first-action effectiveness probe for v4 near-boundary pairs."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import relocate_temporal_snapshot
from autodrift.temporal_action_response_mismatch import TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_extreme_hidden_dynamics_data_route import IdentityResidualGate
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_normal_margin_residual_calibration import calibrated_action_from_hidden
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _action_l2,
    _as_float,
    _as_int,
    _diversity,
    _prefix_l2,
    read_csv_rows,
    reconstruct_snapshots,
)
from autodrift.v4_full_wrong_history_response_intervention import (
    PAIR_FIELDS,
    _pair_rows_from_inputs,
    _snapshot_requests,
)


BASE_DIRECTIONS = (
    "pair_delta_positive",
    "pair_delta_negative",
    "steer_positive",
    "steer_negative",
    "throttle_positive",
    "throttle_negative",
    "brake_positive",
    "brake_negative",
)

ACTION_EFFECTIVENESS_FIELDS = [
    *PAIR_FIELDS,
    "direction",
    "direction_family",
    "epsilon_l2",
    "requested_delta_steer",
    "requested_delta_throttle",
    "requested_delta_brake",
    "effective_delta_steer",
    "effective_delta_throttle",
    "effective_delta_brake",
    "requested_delta_l2",
    "effective_delta_l2_after_clip",
    "clip_fraction",
    "severe_clip",
    "normal_first_steer",
    "normal_first_throttle",
    "normal_first_brake",
    "right_first_steer",
    "right_first_throttle",
    "right_first_brake",
    "override_first_steer",
    "override_first_throttle",
    "override_first_brake",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "override_success",
    "override_collision",
    "override_margin",
    "margin_delta",
    "abs_margin_delta",
    "degradation_margin_delta",
    "improvement_margin_delta",
    "success_flip",
    "collision_flip",
    "collision_flip_to_collision",
    "collision_flip_to_success",
    "first_action_l2_vs_normal",
    "prefix_l2_mean_vs_normal",
    "prefix_l2_max_vs_normal",
    "terminal_reason",
    "steps",
]

ACCEPTED_FIELDS = [
    *PAIR_FIELDS,
    "accepted_class",
    "accepted_reason",
    "direction",
    "direction_family",
    "epsilon_l2",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "override_success",
    "override_collision",
    "override_margin",
    "margin_delta",
    "abs_margin_delta",
    "degradation_margin_delta",
    "improvement_margin_delta",
    "success_flip",
    "collision_flip",
    "effective_delta_l2_after_clip",
    "clip_fraction",
    "severe_clip",
]

DIRECTION_SUMMARY_FIELDS = [
    "direction",
    "direction_family",
    "rows",
    "accepted_rows",
    "accepted_degradation_rows",
    "accepted_improvement_rows",
    "success_flip_rows",
    "collision_flip_rows",
    "max_abs_margin_delta",
    "max_degradation_margin_delta",
    "max_improvement_margin_delta",
    "mean_abs_margin_delta",
    "mean_effective_delta_l2",
    "max_effective_delta_l2",
    "severe_clip_rows",
]


def _action_array(values: Any) -> np.ndarray:
    return np.asarray(values, dtype=np.float64).reshape(-1)


def direction_family(direction: str) -> str:
    if direction.startswith("pair_delta"):
        return "pair_delta"
    if direction.startswith("steer"):
        return "steer_axis"
    if direction.startswith("throttle"):
        return "throttle_axis"
    if direction.startswith("brake"):
        return "brake_axis"
    return "other"


def unit_direction_vector(direction: str, pair_delta_unit: np.ndarray | None = None) -> np.ndarray | None:
    """Return a normalized action direction for the 3D steer/throttle/brake action."""

    if direction == "pair_delta_positive":
        return None if pair_delta_unit is None else np.asarray(pair_delta_unit, dtype=np.float64)
    if direction == "pair_delta_negative":
        return None if pair_delta_unit is None else -np.asarray(pair_delta_unit, dtype=np.float64)
    mapping = {
        "steer_positive": np.asarray([1.0, 0.0, 0.0], dtype=np.float64),
        "steer_negative": np.asarray([-1.0, 0.0, 0.0], dtype=np.float64),
        "throttle_positive": np.asarray([0.0, 1.0, 0.0], dtype=np.float64),
        "throttle_negative": np.asarray([0.0, -1.0, 0.0], dtype=np.float64),
        "brake_positive": np.asarray([0.0, 0.0, 1.0], dtype=np.float64),
        "brake_negative": np.asarray([0.0, 0.0, -1.0], dtype=np.float64),
    }
    return mapping.get(direction)


def normalized_pair_delta(left_action: np.ndarray, right_action: np.ndarray, *, min_norm: float = 1.0e-9) -> np.ndarray | None:
    delta = _action_array(right_action) - _action_array(left_action)
    norm = float(np.linalg.norm(delta))
    if not np.isfinite(norm) or norm < float(min_norm):
        return None
    return delta / norm


def clipped_override_action(
    normal_action: np.ndarray,
    direction_unit: np.ndarray,
    epsilon_l2: float,
    *,
    low: np.ndarray,
    high: np.ndarray,
) -> dict[str, Any]:
    """Return requested/effective deltas and clipped action for a local override."""

    normal = _action_array(normal_action)
    direction = _action_array(direction_unit)
    direction_norm = float(np.linalg.norm(direction))
    if not np.isfinite(direction_norm) or direction_norm <= 0.0:
        raise ValueError("override direction must have positive finite norm")
    direction = direction / direction_norm
    requested_delta = direction * float(epsilon_l2)
    requested_action = normal + requested_delta
    clipped_action = np.clip(requested_action, np.asarray(low, dtype=np.float64), np.asarray(high, dtype=np.float64))
    effective_delta = clipped_action - normal
    requested_l2 = float(np.linalg.norm(requested_delta))
    effective_l2 = float(np.linalg.norm(effective_delta))
    clip_l2 = float(np.linalg.norm(clipped_action - requested_action))
    clip_fraction = float(clip_l2 / requested_l2) if requested_l2 > 0.0 else 0.0
    return {
        "requested_delta": requested_delta,
        "effective_delta": effective_delta,
        "requested_delta_l2": requested_l2,
        "effective_delta_l2_after_clip": effective_l2,
        "clip_fraction": clip_fraction,
        "severe_clip": bool(clip_fraction > 0.25),
        "override_action": clipped_action.astype(np.float32),
    }


def _policy_first_action(
    *,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    snapshot: TemporalSnapshot,
    alpha: float,
    device: torch.device,
) -> np.ndarray:
    action, _next_hidden, _base_action, _raw_delta, _calibrated_delta, _gate = calibrated_action_from_hidden(
        model,
        residual_head,
        identity_gate,
        np.asarray(snapshot.observation, dtype=np.float32),
        snapshot.hidden.detach().clone(),
        alpha=float(alpha),
        device=device,
    )
    return np.asarray(action, dtype=np.float64)


def replay_first_action_override(
    *,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    snapshot: TemporalSnapshot,
    env_config: Any,
    override_action: np.ndarray | None,
    horizon: int,
    reference_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    """Replay a snapshot, optionally replacing only the first executed action."""

    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = snapshot.hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for step_index in range(max_steps):
        action, next_hidden, _base_action, _raw_delta, _calibrated_delta, _gate = calibrated_action_from_hidden(
            model,
            residual_head,
            identity_gate,
            obs,
            hidden,
            alpha=float(alpha),
            device=device,
        )
        if step_index == 0 and override_action is not None:
            action = np.asarray(override_action, dtype=np.float32)
        actions.append(np.asarray(action, dtype=np.float32))
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    if override_action is None:
        trajectory_distances = zero_action_trajectory_distances(len(actions))
        prefix = {"prefix_l2_mean": 0.0, "prefix_l2_max": 0.0, "prefix_compare_steps": min(len(actions), int(horizon))}
    else:
        trajectory_distances = action_trajectory_distances(actions, reference_actions)
        prefix = _prefix_l2(actions, reference_actions, int(horizon))
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    return {
        "horizon": int(horizon),
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "terminal_reason": terminal_reason(info, terminated, truncated, env_config),
        "min_clearance_margin": _finite_float(info.get("min_clearance_margin")),
        "beta_abs_peak": beta_abs_peak,
        **trajectory_distances,
        **prefix,
    }, actions


def _meta(pair: dict[str, Any]) -> dict[str, Any]:
    return {key: pair.get(key, "") for key in PAIR_FIELDS}


def replay_action_effectiveness_pair(
    *,
    pair: dict[str, Any],
    left_snapshot: TemporalSnapshot,
    right_snapshot: TemporalSnapshot,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    env_config: Any,
    max_continuation_steps: int,
    alpha: float,
    epsilon_grid: tuple[float, ...],
    directions: tuple[str, ...],
    device: torch.device,
) -> list[dict[str, Any]]:
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
    normal, normal_actions = replay_first_action_override(
        model=model,
        residual_head=residual_head,
        identity_gate=identity_gate,
        snapshot=left_relocated,
        env_config=env_config,
        override_action=None,
        horizon=horizon,
        reference_actions=None,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(alpha),
        device=device,
    )
    if not normal_actions:
        return []
    normal_first = np.asarray(normal_actions[0], dtype=np.float64)
    right_first = _policy_first_action(
        model=model,
        residual_head=residual_head,
        identity_gate=identity_gate,
        snapshot=right_relocated,
        alpha=float(alpha),
        device=device,
    )
    pair_unit = normalized_pair_delta(normal_first, right_first)
    action_low = np.asarray(left_relocated.env.action_space.low, dtype=np.float64)
    action_high = np.asarray(left_relocated.env.action_space.high, dtype=np.float64)
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    normal_success = parse_bool(normal.get("success", False))
    normal_collision = parse_bool(normal.get("collision", False))
    rows: list[dict[str, Any]] = []
    meta = _meta(pair)
    for direction in directions:
        unit = unit_direction_vector(direction, pair_unit)
        if unit is None:
            continue
        for epsilon in epsilon_grid:
            override = clipped_override_action(
                normal_first,
                unit,
                float(epsilon),
                low=action_low,
                high=action_high,
            )
            result, override_actions = replay_first_action_override(
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                snapshot=left_relocated,
                env_config=env_config,
                override_action=override["override_action"],
                horizon=horizon,
                reference_actions=normal_actions,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=device,
            )
            override_margin = _finite_float(result.get("min_clearance_margin"))
            margin_delta = (
                override_margin - normal_margin
                if np.isfinite(override_margin) and np.isfinite(normal_margin)
                else float("nan")
            )
            override_success = parse_bool(result.get("success", False))
            override_collision = parse_bool(result.get("collision", False))
            prefix = _prefix_l2(override_actions, normal_actions, horizon)
            effective_delta = np.asarray(override["effective_delta"], dtype=np.float64)
            requested_delta = np.asarray(override["requested_delta"], dtype=np.float64)
            override_action = np.asarray(override["override_action"], dtype=np.float64)
            rows.append(
                {
                    **meta,
                    "direction": direction,
                    "direction_family": direction_family(direction),
                    "epsilon_l2": float(epsilon),
                    "requested_delta_steer": float(requested_delta[0]),
                    "requested_delta_throttle": float(requested_delta[1]),
                    "requested_delta_brake": float(requested_delta[2]),
                    "effective_delta_steer": float(effective_delta[0]),
                    "effective_delta_throttle": float(effective_delta[1]),
                    "effective_delta_brake": float(effective_delta[2]),
                    "requested_delta_l2": float(override["requested_delta_l2"]),
                    "effective_delta_l2_after_clip": float(override["effective_delta_l2_after_clip"]),
                    "clip_fraction": float(override["clip_fraction"]),
                    "severe_clip": bool(override["severe_clip"]),
                    "normal_first_steer": float(normal_first[0]),
                    "normal_first_throttle": float(normal_first[1]),
                    "normal_first_brake": float(normal_first[2]),
                    "right_first_steer": float(right_first[0]),
                    "right_first_throttle": float(right_first[1]),
                    "right_first_brake": float(right_first[2]),
                    "override_first_steer": float(override_action[0]),
                    "override_first_throttle": float(override_action[1]),
                    "override_first_brake": float(override_action[2]),
                    "normal_success": normal_success,
                    "normal_collision": normal_collision,
                    "normal_margin": normal_margin,
                    "override_success": override_success,
                    "override_collision": override_collision,
                    "override_margin": override_margin,
                    "margin_delta": margin_delta,
                    "abs_margin_delta": abs(margin_delta) if np.isfinite(margin_delta) else float("nan"),
                    "degradation_margin_delta": -margin_delta if np.isfinite(margin_delta) and margin_delta < 0.0 else 0.0,
                    "improvement_margin_delta": margin_delta if np.isfinite(margin_delta) and margin_delta > 0.0 else 0.0,
                    "success_flip": bool(normal_success != override_success),
                    "collision_flip": bool(normal_collision != override_collision),
                    "collision_flip_to_collision": bool((not normal_collision) and override_collision),
                    "collision_flip_to_success": bool(normal_collision and (not override_collision)),
                    "first_action_l2_vs_normal": _action_l2(override_action, normal_first),
                    "prefix_l2_mean_vs_normal": _finite_float(prefix.get("prefix_l2_mean"), default=0.0),
                    "prefix_l2_max_vs_normal": _finite_float(prefix.get("prefix_l2_max"), default=0.0),
                    "terminal_reason": str(result.get("terminal_reason", "")),
                    "steps": int(result.get("steps", 0)),
                }
            )
    return rows


def accepted_action_effective_rows_for_pair(
    rows: list[dict[str, Any]],
    *,
    boundary_margin_threshold: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for row in rows:
        normal_margin = _finite_float(row.get("normal_margin"))
        normal_ok = (
            parse_bool(row.get("normal_success", False))
            and not parse_bool(row.get("normal_collision", False))
            and np.isfinite(normal_margin)
            and 0.0 <= normal_margin <= float(boundary_margin_threshold)
        )
        action_ok = _finite_float(row.get("effective_delta_l2_after_clip")) >= float(action_l2_threshold)
        abs_delta = _finite_float(row.get("abs_margin_delta"))
        degradation = _finite_float(row.get("degradation_margin_delta"), default=0.0)
        improvement = _finite_float(row.get("improvement_margin_delta"), default=0.0)
        success_flip = parse_bool(row.get("success_flip", False))
        collision_flip = parse_bool(row.get("collision_flip", False))
        if not normal_ok or not action_ok:
            continue
        if not (np.isfinite(abs_delta) and abs_delta >= float(margin_delta_threshold)) and not success_flip and not collision_flip:
            continue
        accepted_class = "outcome_flip"
        reason = "success_or_collision_flip"
        if parse_bool(row.get("collision_flip_to_collision", False)) or degradation >= float(margin_delta_threshold):
            accepted_class = "directional_degradation"
            reason = "override_worsens_margin_or_collision"
        elif parse_bool(row.get("collision_flip_to_success", False)) or improvement >= float(margin_delta_threshold):
            accepted_class = "directional_improvement"
            reason = "override_improves_margin_or_collision"
        accepted.append(
            {
                **{key: row.get(key, "") for key in PAIR_FIELDS},
                "accepted_class": accepted_class,
                "accepted_reason": reason,
                "direction": row.get("direction", ""),
                "direction_family": row.get("direction_family", ""),
                "epsilon_l2": _finite_float(row.get("epsilon_l2")),
                "normal_success": parse_bool(row.get("normal_success", False)),
                "normal_collision": parse_bool(row.get("normal_collision", False)),
                "normal_margin": normal_margin,
                "override_success": parse_bool(row.get("override_success", False)),
                "override_collision": parse_bool(row.get("override_collision", False)),
                "override_margin": _finite_float(row.get("override_margin")),
                "margin_delta": _finite_float(row.get("margin_delta")),
                "abs_margin_delta": abs_delta,
                "degradation_margin_delta": degradation,
                "improvement_margin_delta": improvement,
                "success_flip": success_flip,
                "collision_flip": collision_flip,
                "effective_delta_l2_after_clip": _finite_float(row.get("effective_delta_l2_after_clip")),
                "clip_fraction": _finite_float(row.get("clip_fraction")),
                "severe_clip": parse_bool(row.get("severe_clip", False)),
            }
        )
    return accepted


def _direction_summary(rows: list[dict[str, Any]], accepted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    accepted_by_direction: dict[str, list[dict[str, Any]]] = {}
    for row in accepted_rows:
        accepted_by_direction.setdefault(str(row.get("direction", "")), []).append(row)
    for direction in BASE_DIRECTIONS:
        subset = [row for row in rows if str(row.get("direction", "")) == direction]
        accepted_subset = accepted_by_direction.get(direction, [])
        abs_values = [_finite_float(row.get("abs_margin_delta")) for row in subset if np.isfinite(_finite_float(row.get("abs_margin_delta")))]
        degradation_values = [
            _finite_float(row.get("degradation_margin_delta"), default=0.0)
            for row in subset
            if np.isfinite(_finite_float(row.get("degradation_margin_delta"), default=float("nan")))
        ]
        improvement_values = [
            _finite_float(row.get("improvement_margin_delta"), default=0.0)
            for row in subset
            if np.isfinite(_finite_float(row.get("improvement_margin_delta"), default=float("nan")))
        ]
        deltas = [
            _finite_float(row.get("effective_delta_l2_after_clip"))
            for row in subset
            if np.isfinite(_finite_float(row.get("effective_delta_l2_after_clip")))
        ]
        output.append(
            {
                "direction": direction,
                "direction_family": direction_family(direction),
                "rows": int(len(subset)),
                "accepted_rows": int(len(accepted_subset)),
                "accepted_degradation_rows": int(sum(1 for row in accepted_subset if row.get("accepted_class") == "directional_degradation")),
                "accepted_improvement_rows": int(sum(1 for row in accepted_subset if row.get("accepted_class") == "directional_improvement")),
                "success_flip_rows": int(sum(1 for row in subset if parse_bool(row.get("success_flip", False)))),
                "collision_flip_rows": int(sum(1 for row in subset if parse_bool(row.get("collision_flip", False)))),
                "max_abs_margin_delta": max(abs_values, default=float("nan")),
                "max_degradation_margin_delta": max(degradation_values, default=float("nan")),
                "max_improvement_margin_delta": max(improvement_values, default=float("nan")),
                "mean_abs_margin_delta": float(np.mean(abs_values)) if abs_values else float("nan"),
                "mean_effective_delta_l2": float(np.mean(deltas)) if deltas else float("nan"),
                "max_effective_delta_l2": max(deltas, default=float("nan")),
                "severe_clip_rows": int(sum(1 for row in subset if parse_bool(row.get("severe_clip", False)))),
            }
        )
    return output


def _best_direction_by_pair(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("pair_id", ""))
        value = _finite_float(row.get("abs_margin_delta"), default=-1.0)
        existing = best.get(key)
        if existing is None or value > _finite_float(existing.get("abs_margin_delta"), default=-1.0):
            best[key] = row
    return [best[key] for key in sorted(best, key=lambda item: _as_int(item, 0))]


def _action_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = _diversity(rows)
    output.update(
        {
            "unique_left_source_group_count": unique_count(rows, "left_source_group_id"),
            "unique_left_fault_family_count": unique_count(rows, "left_fault_family"),
            "unique_direction_family_count": unique_count(rows, "direction_family"),
            "max_left_source_group_dominance": max_share(rows, "left_source_group_id"),
            "max_direction_family_dominance": max_share(rows, "direction_family"),
        }
    )
    return output


def classify_action_effectiveness_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    selected_pairs: int,
    reconstructed_snapshots: int,
    accepted_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    min_primary_rows: int,
    min_sparse_rows: int,
    min_left_sources: int,
    min_fault_families: int,
    min_direction_families: int,
    max_source_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_near_boundary_action_effectiveness_contract_violation"
    if int(selected_pairs) <= 0 or int(reconstructed_snapshots) <= 0:
        return "v4_near_boundary_action_effectiveness_reconstruction_failure"
    accepted_nonclip = [row for row in accepted_rows if not parse_bool(row.get("severe_clip", False))]
    if accepted_rows and not accepted_nonclip:
        return "v4_near_boundary_action_effectiveness_clip_dominated"
    metrics = _action_diversity(accepted_nonclip)
    strong = bool(
        len(accepted_nonclip) >= int(min_primary_rows)
        and metrics["unique_left_source_group_count"] >= int(min_left_sources)
        and metrics["unique_left_fault_family_count"] >= int(min_fault_families)
        and metrics["unique_direction_family_count"] >= int(min_direction_families)
        and metrics["max_left_source_group_dominance"] <= float(max_source_dominance)
    )
    if strong:
        return "v4_near_boundary_action_effectiveness_pass"
    if len(accepted_nonclip) >= int(min_sparse_rows):
        return "v4_near_boundary_action_effectiveness_sparse_diagnostic"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in all_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in all_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    if (not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0:
        return "v4_near_boundary_action_effectiveness_first_step_insensitive"
    return "v4_near_boundary_action_effectiveness_very_sparse_diagnostic"


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
            "gate_name": "primary_action_effective_rows",
            "value": summary["accepted_primary_action_effective_rows"],
            "threshold": summary["min_primary_rows"],
            "passed": int(summary["accepted_primary_action_effective_rows"]) >= int(summary["min_primary_rows"]),
            "notes": "direct override evidence is controllability only",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M838 cannot promote",
        },
    ]


def run_near_boundary_action_effectiveness_probe(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    near_boundary_pairs_path: Path,
    accepted_boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
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
    epsilon_grid: tuple[float, ...],
    boundary_margin_threshold: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
    min_primary_rows: int,
    min_sparse_rows: int,
    min_left_sources: int,
    min_fault_families: int,
    min_direction_families: int,
    max_source_dominance: float,
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
        raise ValueError("M838 action-effectiveness probe requires an online recurrent checkpoint")
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

    pair_rows_raw = read_csv_rows(near_boundary_pairs_path)
    accepted_boundary_rows = read_csv_rows(accepted_boundary_rows_path)
    pair_rows, pair_rejections = _pair_rows_from_inputs(pair_rows_raw, accepted_boundary_rows, max_pairs=int(max_pairs))
    requests = _snapshot_requests(pair_rows)
    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=requests,
        source_rows=read_csv_rows(source_rows_path),
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
    for pair in pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**_meta(pair), "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        try:
            rows = replay_action_effectiveness_pair(
                pair=pair,
                left_snapshot=left_snapshot,
                right_snapshot=right_snapshot,
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                env_config=env_config,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                epsilon_grid=tuple(float(value) for value in epsilon_grid),
                directions=BASE_DIRECTIONS,
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**_meta(pair), "rejection_reason": f"replay_error:{type(exc).__name__}"})
            continue
        replay_rows.extend(rows)
        accepted_rows.extend(
            accepted_action_effective_rows_for_pair(
                rows,
                boundary_margin_threshold=float(boundary_margin_threshold),
                margin_delta_threshold=float(margin_delta_threshold),
                action_l2_threshold=float(action_l2_threshold),
            )
        )
        _append_progress(
            progress_path,
            {"stage": "action_effectiveness_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)},
        )

    direction_summary = _direction_summary(replay_rows, accepted_rows)
    best_rows = _best_direction_by_pair(replay_rows)
    accepted_degradation = [row for row in accepted_rows if row.get("accepted_class") == "directional_degradation"]
    accepted_improvement = [row for row in accepted_rows if row.get("accepted_class") == "directional_improvement"]
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in replay_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    max_degradation_margin_delta = max(
        (
            _finite_float(row.get("degradation_margin_delta"), default=0.0)
            for row in replay_rows
            if np.isfinite(_finite_float(row.get("degradation_margin_delta"), default=float("nan")))
        ),
        default=float("nan"),
    )
    max_improvement_margin_delta = max(
        (
            _finite_float(row.get("improvement_margin_delta"), default=0.0)
            for row in replay_rows
            if np.isfinite(_finite_float(row.get("improvement_margin_delta"), default=float("nan")))
        ),
        default=float("nan"),
    )
    success_flip_rows = [row for row in replay_rows if parse_bool(row.get("success_flip", False))]
    collision_flip_rows = [row for row in replay_rows if parse_bool(row.get("collision_flip", False))]
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_action_effectiveness_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        selected_pairs=len(pair_rows),
        reconstructed_snapshots=len(snapshot_rows),
        accepted_rows=accepted_rows,
        all_rows=replay_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        min_primary_rows=int(min_primary_rows),
        min_sparse_rows=int(min_sparse_rows),
        min_left_sources=int(min_left_sources),
        min_fault_families=int(min_fault_families),
        min_direction_families=int(min_direction_families),
        max_source_dominance=float(max_source_dominance),
    )
    diversity_summary = {
        "input_pairs": _diversity(pair_rows),
        "accepted_primary_action_effective": _action_diversity(accepted_rows),
        "accepted_directional_degradation": _action_diversity(accepted_degradation),
        "accepted_directional_improvement": _action_diversity(accepted_improvement),
        "success_flip": _action_diversity(success_flip_rows),
        "collision_flip": _action_diversity(collision_flip_rows),
    }
    all_rejections = [*pair_rejections, *snapshot_rejections, *replay_rejections]

    write_csv_rows(run_dir / "action_effectiveness_pair_rows.csv", [{key: row.get(key, "") for key in PAIR_FIELDS} for row in pair_rows], fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "action_effectiveness_rows.csv", replay_rows, fieldnames=ACTION_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "accepted_action_effective_rows.csv", accepted_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "best_direction_by_pair.csv", best_rows, fieldnames=ACTION_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "direction_summary.csv", direction_summary, fieldnames=DIRECTION_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", all_rejections)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    summary = {
        "run_type": "v4_near_boundary_action_effectiveness_probe",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "near_boundary_pairs": near_boundary_pairs_path,
        "accepted_boundary_rows": accepted_boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "raw_pair_rows": int(len(pair_rows_raw)),
        "selected_pair_rows": int(len(pair_rows)),
        "unique_snapshot_rows": int(len(snapshot_rows)),
        "action_effectiveness_rows": int(len(replay_rows)),
        "accepted_primary_action_effective_rows": int(len(accepted_rows)),
        "accepted_directional_degradation_rows": int(len(accepted_degradation)),
        "accepted_directional_improvement_rows": int(len(accepted_improvement)),
        "success_flip_rows": int(len(success_flip_rows)),
        "collision_flip_rows": int(len(collision_flip_rows)),
        "rejected_rows": int(len(all_rejections)),
        "max_abs_margin_delta": max_abs_margin_delta,
        "max_degradation_margin_delta": max_degradation_margin_delta,
        "max_improvement_margin_delta": max_improvement_margin_delta,
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "min_primary_rows": int(min_primary_rows),
        "min_sparse_rows": int(min_sparse_rows),
        "min_left_sources": int(min_left_sources),
        "min_fault_families": int(min_fault_families),
        "min_direction_families": int(min_direction_families),
        "max_source_dominance": float(max_source_dominance),
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
        "action_effectiveness_pair_rows_csv": run_dir / "action_effectiveness_pair_rows.csv",
        "action_effectiveness_rows_csv": run_dir / "action_effectiveness_rows.csv",
        "accepted_action_effective_rows_csv": run_dir / "accepted_action_effective_rows.csv",
        "best_direction_by_pair_csv": run_dir / "best_direction_by_pair.csv",
        "direction_summary_csv": run_dir / "direction_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 near-boundary first-action effectiveness probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--near-boundary-pairs", type=Path, required=True)
    parser.add_argument("--accepted-boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-pairs", type=int, default=160)
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
    parser.add_argument("--epsilon-l2-grid", type=str, default="0.014,0.025,0.05,0.075")
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--min-primary-rows", type=int, default=40)
    parser.add_argument("--min-sparse-rows", type=int, default=10)
    parser.add_argument("--min-left-sources", type=int, default=8)
    parser.add_argument("--min-fault-families", type=int, default=5)
    parser.add_argument("--min-direction-families", type=int, default=2)
    parser.add_argument("--max-source-dominance", type=float, default=0.30)
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
    summary = run_near_boundary_action_effectiveness_probe(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        near_boundary_pairs_path=args.near_boundary_pairs,
        accepted_boundary_rows_path=args.accepted_boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
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
        epsilon_grid=tuple(parse_float_list(args.epsilon_l2_grid)),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        margin_delta_threshold=float(args.margin_delta_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        min_primary_rows=int(args.min_primary_rows),
        min_sparse_rows=int(args.min_sparse_rows),
        min_left_sources=int(args.min_left_sources),
        min_fault_families=int(args.min_fault_families),
        min_direction_families=int(args.min_direction_families),
        max_source_dominance=float(args.max_source_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
