"""No-training source-diverse low-margin data route for v4 residual replay."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    FaultSpec,
    _frame_info,
    _terminal_reason,
    apply_fault_to_env,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import (
    _base_half_width,
    relocate_temporal_snapshot,
)
from autodrift.temporal_action_response_mismatch import DELAY_STEPS, TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_boundary_axis_expansion import (
    FAULT_SEVERITY_KEYS,
    modify_fault_for_axis,
)
from autodrift.v4_low_margin_boundary_window_retarget import (
    _append_progress,
    _snapshot_obstacle_body,
    parse_bool,
    parse_float_list,
)
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _load_residual_head,
    replay_residual_sequence_variant,
    residual_action_from_hidden,
)


WARMUP_MODES = (
    "natural_policy",
    "steer_pulse_left_right",
    "brake_tap",
    "combined_micro_probe",
)

DEFAULT_OBSTACLE_TIMING_DELTAS = (-0.35, -0.15, 0.15, 0.35)
DEFAULT_LATERAL_DELTAS = (-0.40, -0.20, -0.08, 0.08, 0.20, 0.40)
DEFAULT_HALF_WIDTH_DELTAS = (-0.010, -0.006, -0.003, 0.003, 0.006, 0.010)
DEFAULT_TARGET_MARGINS = (5e-6, 2.5e-5, 4.5e-5)

SOURCE_GROUP_FIELDS = [
    "source_group_id",
    "seed",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fault_severity",
    "wrong_fault",
    "wrong_fault_family",
    "fault_family_pair",
    "source_axis",
    "fault_activation_step_delta",
    "fault_severity_delta",
    "fault_param_key",
    "modified_fault_params_json",
    "snapshots_collected",
    "terminal_reason",
    "success",
    "collision",
    "probe_steps",
    "probe_steer_abs_sum",
    "probe_brake_sum",
    "warmup_artifact",
]

WARMUP_PROBE_FIELDS = [
    "source_group_id",
    "seed",
    "warmup_mode",
    "preferred_fault",
    "probe_steps",
    "probe_steer_abs_sum",
    "probe_brake_sum",
    "min_probe_obstacle_distance",
    "terminal_reason",
    "collision",
    "off_road",
    "spin_out",
    "warmup_artifact",
]

PLAN_FIELDS = [
    "candidate_id",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "step",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fault_severity",
    "wrong_fault",
    "wrong_fault_family",
    "fault_family_pair",
    "source_axis",
    "boundary_axis",
    "horizon",
    "alpha",
    "source_margin",
    "source_success",
    "source_collision",
    "source_terminal_reason",
    "source_obstacle_body_x",
    "source_obstacle_body_y",
    "source_obstacle_half_width",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "obstacle_timing_delta",
    "obstacle_lateral_delta",
    "obstacle_half_width_delta",
    "fault_activation_step_delta",
    "fault_severity_delta",
    "fault_param_key",
    "road_curvature_bucket",
    "initial_speed_bucket",
    "plan_reason",
]

REPLAY_FIELDS = [
    *PLAN_FIELDS,
    "reconstructed",
    "rejection_reason",
    "steps",
    "return",
    "terminated",
    "truncated",
    "success",
    "collision",
    "off_road",
    "spin_out",
    "terminal_reason",
    "obstacle_completed",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "beta_abs_peak",
    "first_steer",
    "first_throttle",
    "first_brake",
    "first_residual_steer",
    "first_residual_throttle",
    "first_residual_brake",
    "residual_l2_mean",
    "residual_l2_max",
    "intervention_count",
    "intervention_collision_count",
    "intervention_min_margin",
    "intervention_any_collision",
]

INTERVENTION_FIELDS = [
    *PLAN_FIELDS,
    "intervention_variant",
    "intervention_success",
    "intervention_collision",
    "intervention_margin",
    "intervention_prefix_l2_mean",
]

SUMMARY_FIELDS = [
    "group",
    "rows",
    "unique_seed_count",
    "unique_source_group_count",
    "unique_source_index_count",
    "unique_fault_pair_count",
    "unique_warmup_mode_count",
    "unique_boundary_axis_count",
    "max_seed_dominance",
    "max_source_group_dominance",
    "max_fault_pair_dominance",
    "max_boundary_axis_dominance",
]


def _parse_int_list(raw: str) -> tuple[int, ...]:
    values = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated integer")
    return tuple(int(value) for value in values)


def _fault_pair(row: dict[str, Any]) -> str:
    value = str(row.get("fault_family_pair", "")).strip()
    if value:
        return value
    return f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}"


def _dominance(rows: list[dict[str, Any]], key: str) -> float:
    return max_share(rows, key)


def _bucket(value: float, width: float) -> str:
    if not np.isfinite(float(value)) or float(width) <= 0.0:
        return "missing"
    return str(int(np.floor(float(value) / float(width))))


def warmup_action_delta(
    mode: str,
    *,
    step_index: int,
    steer_amplitude: float,
    brake_amplitude: float,
    period_steps: int,
) -> np.ndarray:
    """Return a bounded data-generation action perturbation."""

    if mode not in WARMUP_MODES:
        raise ValueError(f"unknown warmup mode: {mode}")
    if mode == "natural_policy":
        return np.zeros(3, dtype=np.float32)
    period = max(1, int(period_steps))
    phase = 2.0 * np.pi * (int(step_index) % period) / float(period)
    steer = 0.0
    brake = 0.0
    if mode in {"steer_pulse_left_right", "combined_micro_probe"}:
        steer = float(steer_amplitude) * float(np.sin(phase))
    if mode in {"brake_tap", "combined_micro_probe"}:
        brake = float(brake_amplitude) if (int(step_index) // period) % 2 == 0 else 0.0
    return np.asarray([steer, 0.0, brake], dtype=np.float32)


def _apply_warmup(action: np.ndarray, delta: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(action, dtype=np.float32) + np.asarray(delta, dtype=np.float32), -1.0, 1.0).astype(np.float32)


def _source_axis_for_fault(base_name: str, fault: FaultSpec) -> tuple[str, int, float, str]:
    if "__m811_fault_activation_step_" in fault.name:
        token = fault.name.split("__m811_fault_activation_step_", 1)[1]
        return "fault_activation_step", int(token.replace("p", "+").replace("m", "-")), 0.0, ""
    if "__m811_fault_severity_" in fault.name:
        token = fault.name.split("__m811_fault_severity_", 1)[1]
        key, raw_delta = token.rsplit("_", 1)
        return "fault_severity", 0, float(raw_delta.replace("p", "+").replace("m", "-").replace("d", ".")), key
    return "base_fault", 0, 0.0, ""


def _renamed_fault(fault: FaultSpec, *, prefix: str) -> FaultSpec:
    if "__m807_" not in fault.name:
        return fault
    return FaultSpec(
        name=fault.name.replace("__m807_", f"__{prefix}_"),
        family=fault.family,
        severity=fault.severity,
        activation_step=fault.activation_step,
        params=fault.params,
        fidelity_class=fault.fidelity_class,
    )


def build_fault_variants(
    faults: list[FaultSpec],
    *,
    max_base_faults: int,
    max_fault_specs: int,
    activation_deltas: tuple[int, ...],
    severity_deltas: tuple[float, ...],
) -> list[FaultSpec]:
    """Build a capped, source-diverse fault list with explicit provenance."""

    by_family: dict[str, list[FaultSpec]] = {}
    for fault in faults:
        by_family.setdefault(fault.family, []).append(fault)
    base_faults: list[FaultSpec] = []
    families = sorted(by_family)
    while len(base_faults) < int(max_base_faults):
        progressed = False
        for family in families:
            rows = by_family[family]
            index = sum(1 for item in base_faults if item.family == family)
            if index >= len(rows):
                continue
            base_faults.append(rows[index])
            progressed = True
            if len(base_faults) >= int(max_base_faults):
                break
        if not progressed:
            break
    output: list[FaultSpec] = []
    seen: set[str] = set()

    def add_fault(fault: FaultSpec) -> None:
        if len(output) >= int(max_fault_specs) or fault.name in seen:
            return
        output.append(fault)
        seen.add(fault.name)

    for fault in base_faults:
        add_fault(fault)
    variant_lists: list[list[FaultSpec]] = []
    for fault in base_faults:
        activation_variants: list[FaultSpec] = []
        severity_variants: list[FaultSpec] = []
        if int(fault.activation_step) > 0:
            for delta in activation_deltas:
                activation_variants.append(
                    _renamed_fault(
                        modify_fault_for_axis(
                            fault,
                            {
                                "retarget_axis": "fault_activation_step",
                                "fault_activation_step_delta": int(delta),
                            },
                        ),
                        prefix="m811",
                    )
                )
        key = next((item for item in sorted(fault.params) if item in FAULT_SEVERITY_KEYS), "")
        if key:
            for delta in severity_deltas:
                severity_variants.append(
                    _renamed_fault(
                        modify_fault_for_axis(
                            fault,
                            {
                                "retarget_axis": "fault_severity",
                                "fault_param_key": key,
                                "fault_severity_delta": float(delta),
                            },
                        ),
                        prefix="m811",
                    )
                )
        variants: list[FaultSpec] = []
        max_axis_variants = max(len(activation_variants), len(severity_variants))
        for variant_index in range(max_axis_variants):
            if variant_index < len(activation_variants):
                variants.append(activation_variants[variant_index])
            if variant_index < len(severity_variants):
                variants.append(severity_variants[variant_index])
        variant_lists.append(variants)
    max_variant_count = max((len(variants) for variants in variant_lists), default=0)
    for variant_index in range(max_variant_count):
        for variants in variant_lists:
            if variant_index < len(variants):
                add_fault(variants[variant_index])
            if len(output) >= int(max_fault_specs):
                break
        if len(output) >= int(max_fault_specs):
            break
    return output


def build_source_groups(
    *,
    seed_start: int,
    seed_count: int,
    fault_specs: list[FaultSpec],
    warmup_modes: tuple[str, ...],
    max_source_groups: int,
) -> list[dict[str, Any]]:
    seeds = list(range(int(seed_start), int(seed_start) + int(seed_count)))
    remaining = [(seed, fault, mode) for seed in seeds for fault in fault_specs for mode in warmup_modes]
    groups: list[dict[str, Any]] = []
    seed_counts: dict[int, int] = {}
    family_counts: dict[str, int] = {}
    fault_counts: dict[str, int] = {}
    mode_counts: dict[str, int] = {}
    while remaining and len(groups) < max(1, int(max_source_groups)):
        remaining.sort(
            key=lambda item: (
                seed_counts.get(int(item[0]), 0),
                family_counts.get(str(item[1].family), 0),
                fault_counts.get(str(item[1].name), 0),
                mode_counts.get(str(item[2]), 0),
                int(item[0]),
                str(item[1].family),
                str(item[1].name),
                str(item[2]),
            )
        )
        seed, fault, mode = remaining.pop(0)
        source_axis, activation_delta, severity_delta, severity_key = _source_axis_for_fault(fault.name, fault)
        group = {
            "source_group_id": len(groups),
            "seed": int(seed),
            "warmup_mode": str(mode),
            "preferred_fault": fault.name,
            "preferred_fault_family": fault.family,
            "preferred_fault_severity": fault.severity,
            "wrong_fault": "nominal",
            "wrong_fault_family": "nominal",
            "fault_family_pair": f"{fault.family}->nominal",
            "source_axis": source_axis if source_axis != "base_fault" else ("warmup_probe_mode" if mode != "natural_policy" else "source_state"),
            "fault_activation_step_delta": int(activation_delta),
            "fault_severity_delta": float(severity_delta),
            "fault_param_key": severity_key,
            "modified_fault_params_json": json.dumps(
                {
                    "activation_step": int(fault.activation_step),
                    "params": fault.params,
                    "fidelity_class": fault.fidelity_class,
                },
                sort_keys=True,
            ),
        }
        groups.append(group)
        seed_counts[int(seed)] = seed_counts.get(int(seed), 0) + 1
        family_counts[str(fault.family)] = family_counts.get(str(fault.family), 0) + 1
        fault_counts[str(fault.name)] = fault_counts.get(str(fault.name), 0) + 1
        mode_counts[str(mode)] = mode_counts.get(str(mode), 0) + 1
    return groups


def _obstacle_lateral_offset(snapshot: TemporalSnapshot) -> float:
    try:
        obstacle_path = snapshot.env._obstacle_path_features(
            snapshot.env.track.frame(snapshot.env.state.x, snapshot.env.state.y, snapshot.env.state.psi)
        )
        return float(obstacle_path[1] * snapshot.env.config.track_width)
    except Exception:
        return float(snapshot.obstacle_lateral_offset)


def collect_warmup_snapshots(
    *,
    model: Any,
    residual_head: Any,
    env_config: Any,
    fault: FaultSpec,
    source_group: dict[str, Any],
    alpha: float,
    min_step: int,
    max_steps: int,
    snapshot_stride: int,
    max_snapshots_per_group: int,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
    history_window_steps: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    period_steps: int,
    start_snapshot_id: int,
    device: torch.device,
) -> tuple[list[TemporalSnapshot], dict[str, Any], dict[str, Any]]:
    env = AutoDriftEnv(env_config)
    seed = int(source_group["seed"])
    warmup_mode = str(source_group["warmup_mode"])
    scenario_id = f"m811_seed{seed}_{fault.name}_{warmup_mode}"
    snapshots: list[TemporalSnapshot] = []
    obs, info = env.reset(seed=seed)
    hidden = model.initial_hidden(1, device)
    fault_applied = False
    if int(fault.activation_step) <= 0:
        apply_fault_to_env(env, fault)
        fault_applied = True
        info = _frame_info(env)

    observation_by_step: dict[int, np.ndarray] = {}
    hidden_by_step: dict[int, torch.Tensor] = {}
    probe_steps = 0
    probe_steer_abs_sum = 0.0
    probe_brake_sum = 0.0
    min_probe_obstacle_distance = float("inf")
    terminated = False
    truncated = False
    while not (terminated or truncated) and int(env.step_count) < int(max_steps):
        step = int(env.step_count)
        if not fault_applied and step >= int(fault.activation_step):
            apply_fault_to_env(env, fault)
            fault_applied = True
            info = _frame_info(env)
        observation_by_step[step] = np.asarray(obs, dtype=np.float32).copy()
        hidden_by_step[step] = hidden.detach().clone()
        obstacle_distance = _finite_float(info.get("obstacle_distance"))
        if (
            step >= int(min_step)
            and step % max(1, int(snapshot_stride)) == 0
            and len(snapshots) < int(max_snapshots_per_group)
            and np.isfinite(obstacle_distance)
            and float(obstacle_longitudinal_min) <= obstacle_distance <= float(obstacle_longitudinal_max)
        ):
            history_start = max(0, step - int(history_window_steps))
            history_steps = tuple(item for item in range(history_start, step) if item in observation_by_step)
            history_observations = tuple(observation_by_step[item].copy() for item in history_steps)
            history_start_hidden = hidden_by_step.get(history_start, hidden_by_step[min(hidden_by_step)])
            delayed_hiddens = {
                int(delay): hidden_by_step[step - int(delay)].detach().clone()
                for delay in DELAY_STEPS
                if step - int(delay) in hidden_by_step
            }
            pre_fault_hidden = None
            if int(fault.activation_step) > 0 and step > int(fault.activation_step):
                pre_fault_step = max(0, int(fault.activation_step) - 1)
                if pre_fault_step in hidden_by_step:
                    pre_fault_hidden = hidden_by_step[pre_fault_step].detach().clone()
            obstacle_path_lateral = float(env._obstacle_path_features(env.track.frame(env.state.x, env.state.y, env.state.psi))[1] * env.config.track_width)
            snapshots.append(
                TemporalSnapshot(
                    snapshot_id=start_snapshot_id + len(snapshots),
                    scenario_id=scenario_id,
                    seed=seed,
                    fault=fault,
                    step=step,
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=hidden.detach().clone(),
                    env=copy.deepcopy(env),
                    info=dict(info),
                    obstacle_distance=obstacle_distance,
                    obstacle_lateral_offset=obstacle_path_lateral,
                    history_steps=history_steps,
                    history_observations=history_observations,
                    history_start_hidden=history_start_hidden.detach().clone(),
                    delayed_hiddens=delayed_hiddens,
                    pre_fault_hidden=pre_fault_hidden,
                )
            )
        action, next_hidden, _, _ = residual_action_from_hidden(
            model,
            residual_head,
            np.asarray(obs, dtype=np.float32),
            hidden,
            alpha=float(alpha),
            device=device,
        )
        if int(step) < int(warmup_steps):
            delta = warmup_action_delta(
                warmup_mode,
                step_index=step,
                steer_amplitude=float(steer_amplitude),
                brake_amplitude=float(brake_amplitude),
                period_steps=int(period_steps),
            )
            if np.any(np.abs(delta) > 0.0):
                probe_steps += 1
                probe_steer_abs_sum += float(abs(delta[0]))
                probe_brake_sum += float(max(delta[2], 0.0))
                if np.isfinite(obstacle_distance):
                    min_probe_obstacle_distance = min(min_probe_obstacle_distance, float(obstacle_distance))
                action = _apply_warmup(action, delta)
        obs, _, terminated, truncated, info = env.step(action)
        hidden = next_hidden

    terminal_reason = _terminal_reason(info, terminated, truncated)
    beta = _finite_float(info.get("beta"))
    warmup_artifact = bool(
        warmup_mode != "natural_policy"
        and int(probe_steps) > 0
        and (bool(info.get("collision", False)) or terminal_reason == "off_road" or (np.isfinite(beta) and abs(beta) > 1.2))
        and int(env.step_count) <= int(warmup_steps) + 5
    )
    source_row = {
        **source_group,
        "snapshots_collected": int(len(snapshots)),
        "terminal_reason": terminal_reason,
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "probe_steps": int(probe_steps),
        "probe_steer_abs_sum": float(probe_steer_abs_sum),
        "probe_brake_sum": float(probe_brake_sum),
        "warmup_artifact": bool(warmup_artifact),
    }
    probe_row = {
        "source_group_id": int(source_group["source_group_id"]),
        "seed": seed,
        "warmup_mode": warmup_mode,
        "preferred_fault": fault.name,
        "probe_steps": int(probe_steps),
        "probe_steer_abs_sum": float(probe_steer_abs_sum),
        "probe_brake_sum": float(probe_brake_sum),
        "min_probe_obstacle_distance": float(min_probe_obstacle_distance) if np.isfinite(min_probe_obstacle_distance) else float("nan"),
        "terminal_reason": terminal_reason,
        "collision": bool(info.get("collision", False)),
        "off_road": terminal_reason == "off_road",
        "spin_out": bool(np.isfinite(beta) and abs(beta) > 1.2),
        "warmup_artifact": bool(warmup_artifact),
    }
    env.close()
    return snapshots, source_row, probe_row


def _snapshot_uid(source_group_id: int, snapshot: TemporalSnapshot) -> str:
    return f"{int(source_group_id)}:{int(snapshot.snapshot_id)}:{int(snapshot.step)}"


def _snapshot_meta(source_group: dict[str, Any], snapshot: TemporalSnapshot, *, source_index: int) -> dict[str, Any]:
    body_x, body_y = _snapshot_obstacle_body(snapshot)
    half_width = _base_half_width(snapshot)
    obs = np.asarray(snapshot.observation, dtype=np.float32)
    vx = float(obs[0] * 20.0) if obs.shape[0] > 0 else float("nan")
    curvature_bucket = "current_track"
    return {
        "source_group_id": int(source_group["source_group_id"]),
        "snapshot_uid": _snapshot_uid(int(source_group["source_group_id"]), snapshot),
        "source_index": int(source_index),
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "warmup_mode": str(source_group["warmup_mode"]),
        "preferred_fault": str(source_group["preferred_fault"]),
        "preferred_fault_family": str(source_group["preferred_fault_family"]),
        "preferred_fault_severity": str(source_group["preferred_fault_severity"]),
        "wrong_fault": str(source_group["wrong_fault"]),
        "wrong_fault_family": str(source_group["wrong_fault_family"]),
        "fault_family_pair": str(source_group["fault_family_pair"]),
        "source_axis": str(source_group["source_axis"]),
        "horizon": 6,
        "source_obstacle_body_x": float(body_x),
        "source_obstacle_body_y": float(body_y),
        "source_obstacle_half_width": float(half_width),
        "fault_activation_step_delta": int(source_group.get("fault_activation_step_delta", 0)),
        "fault_severity_delta": float(source_group.get("fault_severity_delta", 0.0)),
        "fault_param_key": str(source_group.get("fault_param_key", "")),
        "road_curvature_bucket": curvature_bucket,
        "initial_speed_bucket": _bucket(vx, 5.0),
    }


def _edge_pool(result: dict[str, Any], *, collision_margin_floor: float, safe_margin_ceiling: float, diagnostic_safe_margin_ceiling: float) -> str:
    margin = _finite_float(result.get("min_clearance_margin"))
    if not np.isfinite(margin):
        return ""
    if parse_bool(result.get("collision", False)) and float(collision_margin_floor) <= margin < 0.0:
        return "collision_edge"
    if parse_bool(result.get("success", False)) and not parse_bool(result.get("collision", False)) and 0.0 < margin <= float(safe_margin_ceiling):
        return "safe_edge"
    if (
        parse_bool(result.get("success", False))
        and not parse_bool(result.get("collision", False))
        and float(safe_margin_ceiling) < margin <= float(diagnostic_safe_margin_ceiling)
    ):
        return "diagnostic_safe"
    return ""


def plan_boundary_candidates(
    snapshot_meta: dict[str, Any],
    source_result: dict[str, Any],
    *,
    alpha: float,
    target_margins: tuple[float, ...],
    obstacle_timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    collision_margin_floor: float,
    safe_margin_ceiling: float,
    diagnostic_safe_margin_ceiling: float,
    max_candidates_per_snapshot: int,
) -> list[dict[str, Any]]:
    margin = _finite_float(source_result.get("min_clearance_margin"))
    pool = _edge_pool(
        source_result,
        collision_margin_floor=collision_margin_floor,
        safe_margin_ceiling=safe_margin_ceiling,
        diagnostic_safe_margin_ceiling=diagnostic_safe_margin_ceiling,
    )
    base = {
        **snapshot_meta,
        "candidate_id": -1,
        "alpha": float(alpha),
        "source_margin": margin,
        "source_success": parse_bool(source_result.get("success", False)),
        "source_collision": parse_bool(source_result.get("collision", False)),
        "source_terminal_reason": str(source_result.get("terminal_reason", "")),
        "target_obstacle_body_x": float(snapshot_meta["source_obstacle_body_x"]),
        "target_obstacle_body_y": float(snapshot_meta["source_obstacle_body_y"]),
        "target_obstacle_half_width": float(snapshot_meta["source_obstacle_half_width"]),
        "obstacle_timing_delta": 0.0,
        "obstacle_lateral_delta": 0.0,
        "obstacle_half_width_delta": 0.0,
    }
    rows: list[dict[str, Any]] = []
    identity_axis = str(snapshot_meta.get("source_axis", "source_state"))
    rows.append({**base, "boundary_axis": identity_axis, "plan_reason": f"source_identity_{pool or 'unbucketed'}"})
    if pool in {"collision_edge", "safe_edge"} and np.isfinite(margin):
        for target_margin in target_margins:
            width_delta = float(margin) - float(target_margin)
            rows.append(
                {
                    **base,
                    "boundary_axis": "obstacle_half_width",
                    "target_obstacle_half_width": max(0.05, float(base["target_obstacle_half_width"]) + width_delta),
                    "obstacle_half_width_delta": float(width_delta),
                    "plan_reason": f"{pool}_half_width_to_target",
                }
            )
    for delta in obstacle_timing_deltas:
        rows.append(
            {
                **base,
                "boundary_axis": "obstacle_timing",
                "target_obstacle_body_x": max(1.0, float(base["target_obstacle_body_x"]) + float(delta)),
                "obstacle_timing_delta": float(delta),
                "plan_reason": "source_group_obstacle_timing",
            }
        )
    for delta in lateral_deltas:
        rows.append(
            {
                **base,
                "boundary_axis": "obstacle_lateral_offset",
                "target_obstacle_body_y": float(base["target_obstacle_body_y"]) + float(delta),
                "obstacle_lateral_delta": float(delta),
                "plan_reason": "source_group_lateral_offset",
            }
        )
    for delta in half_width_deltas:
        rows.append(
            {
                **base,
                "boundary_axis": "obstacle_half_width",
                "target_obstacle_half_width": max(0.05, float(base["target_obstacle_half_width"]) + float(delta)),
                "obstacle_half_width_delta": float(delta),
                "plan_reason": "source_group_half_width_bracket",
            }
        )
    rows.sort(
        key=lambda row: (
            0 if str(row["boundary_axis"]) == identity_axis else 1,
            abs(_finite_float(row.get("obstacle_half_width_delta"), default=0.0)),
            abs(_finite_float(row.get("obstacle_timing_delta"), default=0.0))
            + abs(_finite_float(row.get("obstacle_lateral_delta"), default=0.0)),
            str(row["boundary_axis"]),
        )
    )
    return rows[: max(1, int(max_candidates_per_snapshot))]


def _accepted(rows: list[dict[str, Any]], *, primary_margin_threshold: float) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        margin = _finite_float(row.get("min_clearance_margin"))
        if (
            parse_bool(row.get("reconstructed", False))
            and parse_bool(row.get("success", False))
            and not parse_bool(row.get("collision", False))
            and np.isfinite(margin)
            and 0.0 <= margin <= float(primary_margin_threshold)
        ):
            output.append(row)
    return output


def select_source_balanced_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows_per_seed: int,
    max_rows_per_source_group: int,
    max_rows_per_fault_pair: int,
    max_rows_per_boundary_axis: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("boundary_axis", "")),
            str(row.get("warmup_mode", "")),
            str(row.get("fault_family_pair", "")),
            str(row.get("seed", "")),
            abs(_finite_float(row.get("min_clearance_margin"), default=1.0) - 2.5e-5),
            int(float(row.get("candidate_id", 0))),
        ),
    )
    for row in ordered:
        keys = {
            ("seed", str(row.get("seed", ""))): int(max_rows_per_seed),
            ("source_group_id", str(row.get("source_group_id", ""))): int(max_rows_per_source_group),
            ("fault_family_pair", _fault_pair(row)): int(max_rows_per_fault_pair),
            ("boundary_axis", str(row.get("boundary_axis", ""))): int(max_rows_per_boundary_axis),
        }
        if any(counts.get(key, 0) >= limit for key, limit in keys.items()):
            continue
        selected.append(row)
        for key in keys:
            counts[key] = counts.get(key, 0) + 1
    return selected


def _summary_rows(rows: list[dict[str, Any]], key: str, *, label: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key, "")), []).append(row)
    output: list[dict[str, Any]] = []
    for value, group_rows in sorted(grouped.items()):
        output.append(
            {
                "group": f"{label}:{value}",
                "rows": len(group_rows),
                "unique_seed_count": unique_count(group_rows, "seed"),
                "unique_source_group_count": unique_count(group_rows, "source_group_id"),
                "unique_source_index_count": unique_count(group_rows, "source_index"),
                "unique_fault_pair_count": unique_count(group_rows, "fault_family_pair"),
                "unique_warmup_mode_count": unique_count(group_rows, "warmup_mode"),
                "unique_boundary_axis_count": unique_count(group_rows, "boundary_axis"),
                "max_seed_dominance": _dominance(group_rows, "seed"),
                "max_source_group_dominance": _dominance(group_rows, "source_group_id"),
                "max_fault_pair_dominance": _dominance(group_rows, "fault_family_pair"),
                "max_boundary_axis_dominance": _dominance(group_rows, "boundary_axis"),
            }
        )
    return output


def _axis_minimum_pass(rows: list[dict[str, Any]], *, min_axis_rows: int, min_axes: int) -> bool:
    counts: dict[str, int] = {}
    for row in rows:
        axis = str(row.get("boundary_axis", ""))
        counts[axis] = counts.get(axis, 0) + 1
    return sum(1 for value in counts.values() if value >= int(min_axis_rows)) >= int(min_axes)


def _value_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _margin_band_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    bands = {
        "collision_negative": 0,
        "primary_0_to_5e-5": 0,
        "near_5e-5_to_1e-3": 0,
        "near_1e-3_to_1e-2": 0,
        "wide_1e-2_to_5e-2": 0,
        "wide_over_5e-2": 0,
        "nonfinite": 0,
    }
    for row in rows:
        margin = _finite_float(row.get("min_clearance_margin"))
        if not np.isfinite(margin):
            bands["nonfinite"] += 1
        elif margin < 0.0:
            bands["collision_negative"] += 1
        elif margin <= 5e-5:
            bands["primary_0_to_5e-5"] += 1
        elif margin <= 1e-3:
            bands["near_5e-5_to_1e-3"] += 1
        elif margin <= 1e-2:
            bands["near_1e-3_to_1e-2"] += 1
        elif margin <= 5e-2:
            bands["wide_1e-2_to_5e-2"] += 1
        else:
            bands["wide_over_5e-2"] += 1
    return bands


def _closest_primary_margin(rows: list[dict[str, Any]], *, target: float = 2.5e-5) -> dict[str, Any]:
    best_row: dict[str, Any] | None = None
    best_distance = float("inf")
    best_margin = float("nan")
    for row in rows:
        margin = _finite_float(row.get("min_clearance_margin"))
        if not np.isfinite(margin):
            continue
        distance = abs(float(margin) - float(target))
        if distance < best_distance:
            best_row = row
            best_distance = distance
            best_margin = margin
    if best_row is None:
        return {}
    return {
        "margin": float(best_margin),
        "distance_to_target": float(best_distance),
        "candidate_id": best_row.get("candidate_id", ""),
        "seed": best_row.get("seed", ""),
        "source_group_id": best_row.get("source_group_id", ""),
        "source_index": best_row.get("source_index", ""),
        "warmup_mode": best_row.get("warmup_mode", ""),
        "fault_family_pair": best_row.get("fault_family_pair", ""),
        "boundary_axis": best_row.get("boundary_axis", ""),
        "plan_reason": best_row.get("plan_reason", ""),
    }


def classify_new_data_route_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    warmup_artifact_rows: int,
    replay_errors: int,
    accepted_rows: list[dict[str, Any]],
    min_rows: int,
    min_seeds: int,
    min_source_groups: int,
    min_source_indices: int,
    min_fault_pairs: int,
    min_warmup_modes: int,
    min_boundary_axes: int,
    max_seed_dominance: float,
    max_source_group_dominance: float,
    max_fault_pair_dominance: float,
    max_boundary_axis_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_low_margin_new_data_route_contract_violation"
    if int(warmup_artifact_rows) > 0:
        return "v4_low_margin_new_data_route_warmup_probe_artifact"
    if int(replay_errors) > 0 and not accepted_rows:
        return "v4_low_margin_new_data_route_replay_error"
    if not accepted_rows or len(accepted_rows) < int(min_rows):
        return "v4_low_margin_new_data_route_sparse"
    if (
        unique_count(accepted_rows, "boundary_axis") < int(min_boundary_axes)
        or max_share(accepted_rows, "boundary_axis") > float(max_boundary_axis_dominance)
        or not _axis_minimum_pass(accepted_rows, min_axis_rows=10, min_axes=3)
    ):
        return "v4_low_margin_new_data_route_axis_concentrated"
    if (
        unique_count(accepted_rows, "seed") < int(min_seeds)
        or unique_count(accepted_rows, "source_group_id") < int(min_source_groups)
        or unique_count(accepted_rows, "source_index") < int(min_source_indices)
        or unique_count(accepted_rows, "fault_family_pair") < int(min_fault_pairs)
        or unique_count(accepted_rows, "warmup_mode") < int(min_warmup_modes)
        or max_share(accepted_rows, "seed") > float(max_seed_dominance)
        or max_share(accepted_rows, "source_group_id") > float(max_source_group_dominance)
        or max_share(accepted_rows, "fault_family_pair") > float(max_fault_pair_dominance)
    ):
        return "v4_low_margin_new_data_route_source_concentrated"
    return "v4_low_margin_new_data_route_pass"


def _replay_plan(
    *,
    plan: dict[str, Any],
    snapshot: TemporalSnapshot,
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    max_continuation_steps: int,
    primary_margin_threshold: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    meta = {field: plan.get(field, "") for field in PLAN_FIELDS}
    try:
        relocated = relocate_temporal_snapshot(
            snapshot,
            body_longitudinal=float(plan["target_obstacle_body_x"]),
            body_lateral=float(plan["target_obstacle_body_y"]),
            half_width=float(plan["target_obstacle_half_width"]),
        )
    except Exception as exc:
        return {
            **meta,
            "reconstructed": False,
            "rejection_reason": f"relocation_error:{type(exc).__name__}",
        }, []
    normal, normal_actions = replay_residual_sequence_variant(
        model=model,
        residual_head=residual_head,
        snapshot=relocated,
        env_config=env_config,
        variant="normal",
        horizon=int(plan.get("horizon", 6)),
        response_dim=response_dim,
        reference_actions=None,
        base_reference_actions=None,
        max_continuation_steps=max_continuation_steps,
        alpha=float(plan.get("alpha", 0.2)),
        device=device,
    )
    replay = {
        **meta,
        "reconstructed": True,
        "rejection_reason": "",
        **normal,
        "intervention_count": 0,
        "intervention_collision_count": 0,
        "intervention_min_margin": "",
        "intervention_any_collision": "",
    }
    margin = _finite_float(normal.get("min_clearance_margin"))
    interventions: list[dict[str, Any]] = []
    if (
        parse_bool(normal.get("success", False))
        and not parse_bool(normal.get("collision", False))
        and np.isfinite(margin)
        and 0.0 <= margin <= float(primary_margin_threshold)
    ):
        margins: list[float] = []
        collisions = 0
        for variant in sorted(SUPPORTED_VARIANTS):
            result, _ = replay_residual_sequence_variant(
                model=model,
                residual_head=residual_head,
                snapshot=relocated,
                env_config=env_config,
                variant=variant,
                horizon=int(plan.get("horizon", 6)),
                response_dim=response_dim,
                reference_actions=normal_actions,
                base_reference_actions=normal_actions,
                max_continuation_steps=max_continuation_steps,
                alpha=float(plan.get("alpha", 0.2)),
                device=device,
            )
            intervention_margin = _finite_float(result.get("min_clearance_margin"))
            if np.isfinite(intervention_margin):
                margins.append(intervention_margin)
            if parse_bool(result.get("collision", False)):
                collisions += 1
            interventions.append(
                {
                    **meta,
                    "intervention_variant": variant,
                    "intervention_success": parse_bool(result.get("success", False)),
                    "intervention_collision": parse_bool(result.get("collision", False)),
                    "intervention_margin": intervention_margin,
                    "intervention_prefix_l2_mean": _finite_float(result.get("prefix_l2_mean")),
                }
            )
        replay["intervention_count"] = len(interventions)
        replay["intervention_collision_count"] = int(collisions)
        replay["intervention_min_margin"] = min(margins) if margins else float("nan")
        replay["intervention_any_collision"] = bool(collisions > 0)
    return replay, interventions


def _write_proxy_limitations(path: Path, config: dict[str, Any]) -> None:
    future_only = config.get("future_only_faults", [])
    lines = [
        "# M811 Fault Proxy Limitations",
        "",
        "M811 uses the current single-track vehicle model and current-model or",
        "current-model-proxy `VehicleParams` faults only.",
        "",
        "Allowed claim:",
        "",
        "- closed-loop capability-envelope stress under current-model/proxy faults.",
        "",
        "Forbidden claim:",
        "",
        "- physically faithful single-wheel, split-mu, halfshaft, stuck-caliper,",
        "  suspension, tire-temperature, or wheel-speed failure dynamics.",
        "",
        "Future high-fidelity-only faults listed by the scenario config:",
        "",
        *[f"- {item}" for item in future_only],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_new_data_route(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    primary_margin_threshold: float,
    collision_margin_floor: float,
    safe_margin_ceiling: float,
    diagnostic_safe_margin_ceiling: float,
    seed_start: int,
    seed_count: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_source_groups: int,
    max_snapshots_per_group: int,
    max_candidates_per_snapshot: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    obstacle_timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    target_margins: tuple[float, ...],
    min_rows: int,
    min_seeds: int,
    min_source_groups: int,
    min_source_indices: int,
    min_fault_pairs: int,
    min_warmup_modes: int,
    min_boundary_axes: int,
    max_seed_dominance: float,
    max_source_group_dominance: float,
    max_fault_pair_dominance: float,
    max_boundary_axis_dominance: float,
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
        raise ValueError("M811 new data route requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_checksum_before = model_parameter_checksum(residual_head)
    response_dim = response_feature_dim_for_model(model)

    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    source_groups = build_source_groups(
        seed_start=int(seed_start),
        seed_count=int(seed_count),
        fault_specs=fault_specs,
        warmup_modes=WARMUP_MODES,
        max_source_groups=int(max_source_groups),
    )
    snapshots_by_uid: dict[str, TemporalSnapshot] = {}
    source_group_rows: list[dict[str, Any]] = []
    warmup_rows: list[dict[str, Any]] = []
    source_result_rows: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    snapshot_index = 0

    for group in source_groups:
        group_start = time.time()
        fault = fault_by_name[str(group["preferred_fault"])]
        snapshots, source_row, probe_row = collect_warmup_snapshots(
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            fault=fault,
            source_group=group,
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
            start_snapshot_id=snapshot_index,
            device=resolved_device,
        )
        snapshot_index += len(snapshots)
        source_group_rows.append(source_row)
        warmup_rows.append(probe_row)
        _append_progress(
            progress_path,
            {
                "source_group_id": int(group["source_group_id"]),
                "stage": "collect",
                "snapshots": len(snapshots),
                "warmup_artifact": parse_bool(source_row.get("warmup_artifact", False)),
                "elapsed_seconds": time.time() - group_start,
            },
        )
        for snapshot in snapshots:
            uid = _snapshot_uid(int(group["source_group_id"]), snapshot)
            snapshots_by_uid[uid] = snapshot
            source_meta = _snapshot_meta(group, snapshot, source_index=len(source_result_rows))
            source_result, _ = replay_residual_sequence_variant(
                model=model,
                residual_head=residual_head,
                snapshot=snapshot,
                env_config=env_config,
                variant="normal",
                horizon=6,
                response_dim=response_dim,
                reference_actions=None,
                base_reference_actions=None,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=resolved_device,
            )
            source_result_rows.append({**source_meta, **source_result})
            local_plan = plan_boundary_candidates(
                source_meta,
                source_result,
                alpha=float(alpha),
                target_margins=target_margins,
                obstacle_timing_deltas=obstacle_timing_deltas,
                lateral_deltas=lateral_deltas,
                half_width_deltas=half_width_deltas,
                collision_margin_floor=float(collision_margin_floor),
                safe_margin_ceiling=float(safe_margin_ceiling),
                diagnostic_safe_margin_ceiling=float(diagnostic_safe_margin_ceiling),
                max_candidates_per_snapshot=int(max_candidates_per_snapshot),
            )
            for row in local_plan:
                row["candidate_id"] = len(plan_rows)
                plan_rows.append(row)

    replay_errors = 0
    for plan in plan_rows:
        candidate_start = time.time()
        snapshot = snapshots_by_uid.get(str(plan["snapshot_uid"]))
        if snapshot is None:
            replay = {**{field: plan.get(field, "") for field in PLAN_FIELDS}, "reconstructed": False, "rejection_reason": "missing_snapshot_uid"}
            interventions = []
            replay_errors += 1
        else:
            replay, interventions = _replay_plan(
                plan=plan,
                snapshot=snapshot,
                model=model,
                residual_head=residual_head,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=int(max_continuation_steps),
                primary_margin_threshold=float(primary_margin_threshold),
                device=resolved_device,
            )
            if not parse_bool(replay.get("reconstructed", False)):
                replay_errors += 1
        replay_rows.append(replay)
        intervention_rows.extend(interventions)
        margin = _finite_float(replay.get("min_clearance_margin"))
        _append_progress(
            progress_path,
            {
                "candidate_id": int(plan["candidate_id"]),
                "source_group_id": int(plan["source_group_id"]),
                "stage": "replay",
                "boundary_axis": str(plan["boundary_axis"]),
                "status": "replayed" if parse_bool(replay.get("reconstructed", False)) else str(replay.get("rejection_reason", "")),
                "margin": margin if np.isfinite(margin) else None,
                "success": parse_bool(replay.get("success", False)),
                "collision": parse_bool(replay.get("collision", False)),
                "elapsed_seconds": time.time() - candidate_start,
            },
        )

    accepted_raw = _accepted(replay_rows, primary_margin_threshold=primary_margin_threshold)
    accepted = select_source_balanced_rows(
        accepted_raw,
        max_rows_per_seed=20,
        max_rows_per_source_group=8,
        max_rows_per_fault_pair=32,
        max_rows_per_boundary_axis=48,
    )
    source_summary = [
        *_summary_rows(accepted, "seed", label="seed"),
        *_summary_rows(accepted, "source_group_id", label="source_group"),
        *_summary_rows(accepted, "fault_family_pair", label="fault_pair"),
        *_summary_rows(accepted, "warmup_mode", label="warmup"),
    ]
    axis_summary = _summary_rows(accepted, "boundary_axis", label="axis")
    warmup_artifact_rows = sum(1 for row in warmup_rows if parse_bool(row.get("warmup_artifact", False)))
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_new_data_route_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        warmup_artifact_rows=int(warmup_artifact_rows),
        replay_errors=int(replay_errors),
        accepted_rows=accepted,
        min_rows=int(min_rows),
        min_seeds=int(min_seeds),
        min_source_groups=int(min_source_groups),
        min_source_indices=int(min_source_indices),
        min_fault_pairs=int(min_fault_pairs),
        min_warmup_modes=int(min_warmup_modes),
        min_boundary_axes=int(min_boundary_axes),
        max_seed_dominance=float(max_seed_dominance),
        max_source_group_dominance=float(max_source_group_dominance),
        max_fault_pair_dominance=float(max_fault_pair_dominance),
        max_boundary_axis_dominance=float(max_boundary_axis_dominance),
    )

    write_csv_rows(run_dir / "source_group_rows.csv", source_group_rows, fieldnames=SOURCE_GROUP_FIELDS)
    write_csv_rows(run_dir / "warmup_probe_rows.csv", warmup_rows, fieldnames=WARMUP_PROBE_FIELDS)
    write_csv_rows(run_dir / "source_result_rows.csv", source_result_rows)
    write_csv_rows(run_dir / "boundary_search_plan_rows.csv", plan_rows, fieldnames=PLAN_FIELDS)
    write_csv_rows(run_dir / "boundary_search_replay_rows.csv", replay_rows, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_primary_rows.csv", accepted, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "intervention_replay_rows.csv", intervention_rows, fieldnames=INTERVENTION_FIELDS)
    write_csv_rows(run_dir / "source_balance_summary.csv", source_summary, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(run_dir / "axis_balance_summary.csv", axis_summary, fieldnames=SUMMARY_FIELDS)
    _write_proxy_limitations(run_dir / "fault_proxy_limitations.md", scenario_config)

    normal_collision_rate = (
        float(np.mean([1.0 if parse_bool(row.get("collision", False)) else 0.0 for row in accepted]))
        if accepted
        else 0.0
    )
    summary = {
        "run_type": "v4_low_margin_new_data_route",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "alpha": float(alpha),
        "primary_margin_threshold": float(primary_margin_threshold),
        "fault_specs": int(len(fault_specs)),
        "source_groups": int(len(source_groups)),
        "source_group_rows": int(len(source_group_rows)),
        "warmup_probe_rows": int(len(warmup_rows)),
        "warmup_artifact_rows": int(warmup_artifact_rows),
        "source_snapshots": int(len(snapshots_by_uid)),
        "source_result_rows": int(len(source_result_rows)),
        "boundary_search_plan_rows": int(len(plan_rows)),
        "boundary_search_replay_rows": int(len(replay_rows)),
        "replay_errors": int(replay_errors),
        "accepted_primary_raw_rows": int(len(accepted_raw)),
        "accepted_primary_rows": int(len(accepted)),
        "unique_accepted_seeds": unique_count(accepted, "seed"),
        "unique_accepted_source_groups": unique_count(accepted, "source_group_id"),
        "unique_accepted_source_indices": unique_count(accepted, "source_index"),
        "unique_accepted_fault_family_pairs": unique_count(accepted, "fault_family_pair"),
        "unique_accepted_warmup_modes": unique_count(accepted, "warmup_mode"),
        "unique_accepted_boundary_axes": unique_count(accepted, "boundary_axis"),
        "max_accepted_seed_dominance": max_share(accepted, "seed"),
        "max_accepted_source_group_dominance": max_share(accepted, "source_group_id"),
        "max_accepted_fault_pair_dominance": max_share(accepted, "fault_family_pair"),
        "max_accepted_boundary_axis_dominance": max_share(accepted, "boundary_axis"),
        "normal_collision_rate_in_accepted": normal_collision_rate,
        "replay_margin_band_counts": _margin_band_counts(replay_rows),
        "replay_boundary_axis_counts": _value_counts(replay_rows, "boundary_axis"),
        "replay_closest_primary_margin": _closest_primary_margin(replay_rows),
        "intervention_replay_rows": int(len(intervention_rows)),
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
        "source_group_rows_csv": run_dir / "source_group_rows.csv",
        "warmup_probe_rows_csv": run_dir / "warmup_probe_rows.csv",
        "source_result_rows_csv": run_dir / "source_result_rows.csv",
        "boundary_search_plan_rows_csv": run_dir / "boundary_search_plan_rows.csv",
        "boundary_search_replay_rows_csv": run_dir / "boundary_search_replay_rows.csv",
        "accepted_primary_rows_csv": run_dir / "accepted_primary_rows.csv",
        "intervention_replay_rows_csv": run_dir / "intervention_replay_rows.csv",
        "source_balance_summary_csv": run_dir / "source_balance_summary.csv",
        "axis_balance_summary_csv": run_dir / "axis_balance_summary.csv",
        "fault_proxy_limitations_md": run_dir / "fault_proxy_limitations.md",
        "progress_jsonl": progress_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 low-margin new data route.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--primary-margin-threshold", type=float, default=5e-5)
    parser.add_argument("--collision-margin-floor", type=float, default=-1e-3)
    parser.add_argument("--safe-margin-ceiling", type=float, default=1e-2)
    parser.add_argument("--diagnostic-safe-margin-ceiling", type=float, default=2e-1)
    parser.add_argument("--seed-start", type=int, default=None)
    parser.add_argument("--seed-count", type=int, default=12)
    parser.add_argument("--max-base-faults", type=int, default=8)
    parser.add_argument("--max-fault-specs", type=int, default=14)
    parser.add_argument("--max-source-groups", type=int, default=96)
    parser.add_argument("--max-snapshots-per-group", type=int, default=2)
    parser.add_argument("--max-candidates-per-snapshot", type=int, default=14)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=20)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--obstacle-timing-deltas", type=parse_float_list, default=DEFAULT_OBSTACLE_TIMING_DELTAS)
    parser.add_argument("--lateral-deltas", type=parse_float_list, default=DEFAULT_LATERAL_DELTAS)
    parser.add_argument("--half-width-deltas", type=parse_float_list, default=DEFAULT_HALF_WIDTH_DELTAS)
    parser.add_argument("--target-margins", type=parse_float_list, default=DEFAULT_TARGET_MARGINS)
    parser.add_argument("--min-rows", type=int, default=80)
    parser.add_argument("--min-seeds", type=int, default=8)
    parser.add_argument("--min-source-groups", type=int, default=16)
    parser.add_argument("--min-source-indices", type=int, default=8)
    parser.add_argument("--min-fault-pairs", type=int, default=4)
    parser.add_argument("--min-warmup-modes", type=int, default=2)
    parser.add_argument("--min-boundary-axes", type=int, default=3)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-source-group-dominance", type=float, default=0.15)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.40)
    parser.add_argument("--max-boundary-axis-dominance", type=float, default=0.60)
    args = parser.parse_args()
    scenario_config = load_scenario_config(args.scenario_config)
    seed_start = int(args.seed_start) if args.seed_start is not None else int(scenario_config.get("low_margin_refresh_targets", {}).get("seed_start", 78048))
    max_steps = int(args.max_steps) if args.max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step = int(args.min_step) if args.min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride = int(args.snapshot_stride) if args.snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    max_continuation_steps = (
        int(args.max_continuation_steps)
        if args.max_continuation_steps is not None
        else int(scenario_config.get("max_continuation_steps", 70))
    )
    summary = run_new_data_route(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        primary_margin_threshold=float(args.primary_margin_threshold),
        collision_margin_floor=float(args.collision_margin_floor),
        safe_margin_ceiling=float(args.safe_margin_ceiling),
        diagnostic_safe_margin_ceiling=float(args.diagnostic_safe_margin_ceiling),
        seed_start=seed_start,
        seed_count=int(args.seed_count),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_source_groups=int(args.max_source_groups),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_candidates_per_snapshot=int(args.max_candidates_per_snapshot),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        obstacle_timing_deltas=tuple(args.obstacle_timing_deltas),
        lateral_deltas=tuple(args.lateral_deltas),
        half_width_deltas=tuple(args.half_width_deltas),
        target_margins=tuple(args.target_margins),
        min_rows=int(args.min_rows),
        min_seeds=int(args.min_seeds),
        min_source_groups=int(args.min_source_groups),
        min_source_indices=int(args.min_source_indices),
        min_fault_pairs=int(args.min_fault_pairs),
        min_warmup_modes=int(args.min_warmup_modes),
        min_boundary_axes=int(args.min_boundary_axes),
        max_seed_dominance=float(args.max_seed_dominance),
        max_source_group_dominance=float(args.max_source_group_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
        max_boundary_axis_dominance=float(args.max_boundary_axis_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
