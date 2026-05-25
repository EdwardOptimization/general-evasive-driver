"""No-training adaptive boundary bracketing for v4 low-margin rows."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    _terminal_reason,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import (
    _base_half_width,
    relocate_temporal_snapshot,
)
from autodrift.temporal_action_response_mismatch import TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_boundary_window_retarget import (
    _append_progress,
    _snapshot_obstacle_body,
    parse_bool,
    parse_float_list,
)
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import (
    DEFAULT_HALF_WIDTH_DELTAS,
    DEFAULT_LATERAL_DELTAS,
    DEFAULT_OBSTACLE_TIMING_DELTAS,
    SOURCE_GROUP_FIELDS,
    SUMMARY_FIELDS,
    WARMUP_MODES,
    WARMUP_PROBE_FIELDS,
    _summary_rows,
    _value_counts,
    build_fault_variants,
    build_source_groups,
    collect_warmup_snapshots,
)
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _load_residual_head,
    replay_residual_sequence_variant,
)


BOUNDARY_AXES = ("obstacle_lateral_offset", "obstacle_timing", "obstacle_half_width")

BRACKET_SEED_FIELDS = [
    "bracket_id",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "step",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "wrong_fault_family",
    "fault_family_pair",
    "source_axis",
    "boundary_axis",
    "status",
    "initial_evaluations",
    "negative_parameter",
    "negative_margin",
    "positive_parameter",
    "positive_margin",
    "bracket_parameter_gap",
    "bracket_margin_gap",
    "failure_reason",
]

REFINEMENT_FIELDS = [
    "candidate_id",
    "bracket_id",
    "refinement_iter",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "step",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "wrong_fault_family",
    "fault_family_pair",
    "source_axis",
    "boundary_axis",
    "parameter_value",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "negative_parameter_before",
    "negative_margin_before",
    "positive_parameter_before",
    "positive_margin_before",
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
    "accepted_primary",
]

INTERVENTION_FIELDS = [
    "candidate_id",
    "bracket_id",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "warmup_mode",
    "fault_family_pair",
    "boundary_axis",
    "parameter_value",
    "intervention_variant",
    "intervention_success",
    "intervention_collision",
    "intervention_margin",
    "intervention_prefix_l2_mean",
]

FAILURE_FIELDS = [
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "warmup_mode",
    "fault_family_pair",
    "boundary_axis",
    "failure_reason",
    "evaluations",
]


def axis_initial_values(
    axis: str,
    *,
    body_x: float,
    body_y: float,
    half_width: float,
    timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
) -> list[float]:
    """Return sorted unique initial parameter values for an axis."""

    if axis == "obstacle_timing":
        values = [float(body_x), *[float(body_x) + float(delta) for delta in timing_deltas]]
        return sorted({max(1.0, value) for value in values})
    if axis == "obstacle_lateral_offset":
        values = [float(body_y), *[float(body_y) + float(delta) for delta in lateral_deltas]]
        return sorted(set(values))
    if axis == "obstacle_half_width":
        values = [float(half_width), *[float(half_width) + float(delta) for delta in half_width_deltas]]
        return sorted({max(0.05, value) for value in values})
    raise ValueError(f"unknown boundary axis: {axis}")


def axis_expansion_values(
    axis: str,
    *,
    body_x: float,
    body_y: float,
    half_width: float,
    max_expansion_attempts: int,
) -> list[float]:
    """Return bounded expansion values used only when initial candidates do not bracket."""

    steps = list(range(1, max(1, int(max_expansion_attempts)) + 1))
    if axis == "obstacle_timing":
        values = [float(body_x) + sign * 0.5 * step for step in steps for sign in (-1.0, 1.0)]
        return sorted({max(1.0, value) for value in values})
    if axis == "obstacle_lateral_offset":
        values = [float(body_y) + sign * 0.35 * step for step in steps for sign in (-1.0, 1.0)]
        return sorted(set(values))
    if axis == "obstacle_half_width":
        values = [float(half_width) + sign * 0.02 * step for step in steps for sign in (-1.0, 1.0)]
        return sorted({max(0.05, value) for value in values})
    raise ValueError(f"unknown boundary axis: {axis}")


def axis_targets(
    snapshot: TemporalSnapshot,
    axis: str,
    parameter_value: float,
) -> tuple[float, float, float]:
    body_x, body_y = _snapshot_obstacle_body(snapshot)
    half_width = _base_half_width(snapshot)
    if axis == "obstacle_timing":
        body_x = float(parameter_value)
    elif axis == "obstacle_lateral_offset":
        body_y = float(parameter_value)
    elif axis == "obstacle_half_width":
        half_width = float(parameter_value)
    else:
        raise ValueError(f"unknown boundary axis: {axis}")
    return float(body_x), float(body_y), max(0.05, float(half_width))


def _snapshot_uid(source_group_id: int, snapshot: TemporalSnapshot) -> str:
    return f"{int(source_group_id)}:{int(snapshot.snapshot_id)}:{int(snapshot.step)}"


def _source_meta(source_group: dict[str, Any], snapshot: TemporalSnapshot, *, source_index: int) -> dict[str, Any]:
    return {
        "source_group_id": int(source_group["source_group_id"]),
        "snapshot_uid": _snapshot_uid(int(source_group["source_group_id"]), snapshot),
        "source_index": int(source_index),
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "warmup_mode": str(source_group["warmup_mode"]),
        "preferred_fault": str(source_group["preferred_fault"]),
        "preferred_fault_family": str(source_group["preferred_fault_family"]),
        "wrong_fault_family": str(source_group["wrong_fault_family"]),
        "fault_family_pair": str(source_group["fault_family_pair"]),
        "source_axis": str(source_group["source_axis"]),
    }


def _result_margin(row: dict[str, Any]) -> float:
    return _finite_float(row.get("min_clearance_margin"))


def _is_negative(row: dict[str, Any]) -> bool:
    margin = _result_margin(row)
    return parse_bool(row.get("collision", False)) or (np.isfinite(margin) and margin < 0.0)


def _is_safe_positive(row: dict[str, Any]) -> bool:
    margin = _result_margin(row)
    return (
        parse_bool(row.get("reconstructed", False))
        and parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and np.isfinite(margin)
        and margin > 0.0
    )


def accepted_primary(row: dict[str, Any], *, primary_margin_threshold: float) -> bool:
    margin = _result_margin(row)
    return (
        parse_bool(row.get("reconstructed", False))
        and parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and np.isfinite(margin)
        and 0.0 <= margin <= float(primary_margin_threshold)
    )


def find_adjacent_margin_bracket(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Find the tightest adjacent sign-change bracket in parameter order."""

    ordered = sorted(
        [row for row in rows if parse_bool(row.get("reconstructed", False)) and np.isfinite(_result_margin(row))],
        key=lambda row: float(row["parameter_value"]),
    )
    candidates: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for left, right in zip(ordered, ordered[1:]):
        left_neg = _is_negative(left)
        right_neg = _is_negative(right)
        left_pos = _is_safe_positive(left)
        right_pos = _is_safe_positive(right)
        if left_neg and right_pos:
            candidates.append((abs(_result_margin(right) - _result_margin(left)), left, right))
        elif left_pos and right_neg:
            candidates.append((abs(_result_margin(left) - _result_margin(right)), right, left))
    if not candidates:
        return None
    _, negative, positive = min(candidates, key=lambda item: item[0])
    return negative, positive


def _replay_parameter(
    *,
    snapshot: TemporalSnapshot,
    source_meta: dict[str, Any],
    axis: str,
    parameter_value: float,
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], Any, TemporalSnapshot | None]:
    target_x, target_y, target_half_width = axis_targets(snapshot, axis, parameter_value)
    meta = {
        **source_meta,
        "boundary_axis": axis,
        "parameter_value": float(parameter_value),
        "target_obstacle_body_x": float(target_x),
        "target_obstacle_body_y": float(target_y),
        "target_obstacle_half_width": float(target_half_width),
    }
    try:
        relocated = relocate_temporal_snapshot(
            snapshot,
            body_longitudinal=float(target_x),
            body_lateral=float(target_y),
            half_width=float(target_half_width),
        )
    except Exception as exc:
        return {
            **meta,
            "reconstructed": False,
            "rejection_reason": f"relocation_error:{type(exc).__name__}",
        }, None, None
    result, actions = replay_residual_sequence_variant(
        model=model,
        residual_head=residual_head,
        snapshot=relocated,
        env_config=env_config,
        variant="normal",
        horizon=int(horizon),
        response_dim=response_dim,
        reference_actions=None,
        base_reference_actions=None,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(alpha),
        device=device,
    )
    return {
        **meta,
        "reconstructed": True,
        "rejection_reason": "",
        **result,
    }, actions, relocated


def _bracket_seed_row(
    *,
    bracket_id: int,
    source_meta: dict[str, Any],
    axis: str,
    evaluations: list[dict[str, Any]],
    bracket: tuple[dict[str, Any], dict[str, Any]] | None,
    failure_reason: str = "",
) -> dict[str, Any]:
    base = {
        **source_meta,
        "bracket_id": int(bracket_id),
        "boundary_axis": axis,
        "initial_evaluations": int(len(evaluations)),
        "failure_reason": failure_reason,
    }
    if bracket is None:
        return {
            **base,
            "status": "failed",
            "negative_parameter": "",
            "negative_margin": "",
            "positive_parameter": "",
            "positive_margin": "",
            "bracket_parameter_gap": "",
            "bracket_margin_gap": "",
        }
    negative, positive = bracket
    return {
        **base,
        "status": "valid",
        "negative_parameter": float(negative["parameter_value"]),
        "negative_margin": _result_margin(negative),
        "positive_parameter": float(positive["parameter_value"]),
        "positive_margin": _result_margin(positive),
        "bracket_parameter_gap": abs(float(positive["parameter_value"]) - float(negative["parameter_value"])),
        "bracket_margin_gap": abs(_result_margin(positive) - _result_margin(negative)),
    }


def refine_bracket(
    *,
    bracket_id: int,
    snapshot: TemporalSnapshot,
    source_meta: dict[str, Any],
    axis: str,
    negative: dict[str, Any],
    positive: dict[str, Any],
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    max_refinement_iterations: int,
    primary_margin_threshold: float,
    parameter_tolerance: float,
    device: torch.device,
    start_candidate_id: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, str]:
    rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    negative_endpoint = copy.deepcopy(negative)
    positive_endpoint = copy.deepcopy(positive)
    status = "max_iterations"
    for iteration in range(int(max_refinement_iterations)):
        neg_param = float(negative_endpoint["parameter_value"])
        pos_param = float(positive_endpoint["parameter_value"])
        if abs(pos_param - neg_param) <= float(parameter_tolerance):
            status = "parameter_tolerance"
            break
        midpoint = 0.5 * (neg_param + pos_param)
        result, _, _ = _replay_parameter(
            snapshot=snapshot,
            source_meta=source_meta,
            axis=axis,
            parameter_value=midpoint,
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            response_dim=response_dim,
            alpha=float(alpha),
            horizon=int(horizon),
            max_continuation_steps=int(max_continuation_steps),
            device=device,
        )
        row = {
            "candidate_id": int(start_candidate_id + len(rows)),
            "bracket_id": int(bracket_id),
            "refinement_iter": int(iteration),
            **result,
            "negative_parameter_before": neg_param,
            "negative_margin_before": _result_margin(negative_endpoint),
            "positive_parameter_before": pos_param,
            "positive_margin_before": _result_margin(positive_endpoint),
            "accepted_primary": accepted_primary(result, primary_margin_threshold=float(primary_margin_threshold)),
        }
        rows.append(row)
        if parse_bool(row["accepted_primary"]):
            accepted_rows.append(row)
            status = "accepted"
            break
        if not parse_bool(result.get("reconstructed", False)) or not np.isfinite(_result_margin(result)):
            status = "replay_error"
            break
        if _is_negative(result):
            negative_endpoint = result
        elif _is_safe_positive(result):
            positive_endpoint = result
        else:
            status = "ambiguous_outcome"
            break
    return rows, accepted_rows, start_candidate_id + len(rows), status


def classify_adaptive_bracketing_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    warmup_artifact_rows: int,
    replay_errors: int,
    brackets_valid: int,
    bracket_nonmonotone_count: int,
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
        return "v4_adaptive_boundary_bracketing_contract_violation"
    if int(warmup_artifact_rows) > 0:
        return "v4_adaptive_boundary_bracketing_warmup_artifact"
    if int(replay_errors) > 0 and not accepted_rows:
        return "v4_adaptive_boundary_bracketing_replay_error"
    if int(brackets_valid) <= 0:
        return "v4_adaptive_boundary_bracketing_bracket_sparse"
    if int(bracket_nonmonotone_count) > int(brackets_valid) // 2 and not accepted_rows:
        return "v4_adaptive_boundary_bracketing_nonmonotone"
    if not accepted_rows or len(accepted_rows) < int(min_rows):
        return "v4_adaptive_boundary_bracketing_sparse"
    axis_counts: dict[str, int] = {}
    for row in accepted_rows:
        axis = str(row.get("boundary_axis", ""))
        axis_counts[axis] = axis_counts.get(axis, 0) + 1
    axes_with_min_rows = sum(1 for value in axis_counts.values() if value >= 10)
    if (
        unique_count(accepted_rows, "boundary_axis") < int(min_boundary_axes)
        or max_share(accepted_rows, "boundary_axis") > float(max_boundary_axis_dominance)
        or axes_with_min_rows < int(min_boundary_axes)
    ):
        return "v4_adaptive_boundary_bracketing_axis_concentrated"
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
        return "v4_adaptive_boundary_bracketing_source_concentrated"
    return "v4_adaptive_boundary_bracketing_pass"


def select_adaptive_balanced_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows_per_seed: int,
    max_rows_per_source_group: int,
    max_rows_per_fault_pair: int,
    max_rows_per_boundary_axis: int,
    target_margin: float = 2.5e-5,
) -> list[dict[str, Any]]:
    """Greedily select rows while prioritizing underrepresented sources and axes."""

    remaining = list(rows)
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    while remaining:
        remaining.sort(
            key=lambda row: (
                counts.get(("boundary_axis", str(row.get("boundary_axis", ""))), 0),
                counts.get(("seed", str(row.get("seed", ""))), 0),
                counts.get(("fault_family_pair", str(row.get("fault_family_pair", ""))), 0),
                counts.get(("source_group_id", str(row.get("source_group_id", ""))), 0),
                abs(_finite_float(row.get("min_clearance_margin"), default=1.0) - float(target_margin)),
                int(float(row.get("candidate_id", 0))),
            )
        )
        selected_index = -1
        selected_keys: list[tuple[tuple[str, str], int]] = []
        for index, row in enumerate(remaining):
            keys = [
                (("seed", str(row.get("seed", ""))), int(max_rows_per_seed)),
                (("source_group_id", str(row.get("source_group_id", ""))), int(max_rows_per_source_group)),
                (("fault_family_pair", str(row.get("fault_family_pair", ""))), int(max_rows_per_fault_pair)),
                (("boundary_axis", str(row.get("boundary_axis", ""))), int(max_rows_per_boundary_axis)),
            ]
            if all(counts.get(key, 0) < limit for key, limit in keys):
                selected_index = index
                selected_keys = keys
                break
        if selected_index < 0:
            break
        row = remaining.pop(selected_index)
        selected.append(row)
        for key, _ in selected_keys:
            counts[key] = counts.get(key, 0) + 1
    return selected


def run_adaptive_bracketing(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    primary_margin_threshold: float,
    seed_start: int,
    seed_count: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_source_groups: int,
    max_snapshots_per_group: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    horizon: int,
    boundary_axes: tuple[str, ...],
    timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    max_expansion_attempts: int,
    max_refinement_iterations: int,
    parameter_tolerance: float,
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
        raise ValueError("M814 adaptive bracketing requires an online recurrent checkpoint")
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

    source_group_rows: list[dict[str, Any]] = []
    warmup_rows: list[dict[str, Any]] = []
    bracket_seed_rows: list[dict[str, Any]] = []
    refinement_rows: list[dict[str, Any]] = []
    accepted_raw: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    bracket_failure_rows: list[dict[str, Any]] = []
    replay_errors = 0
    bracket_id = 0
    candidate_id = 0
    snapshot_index = 0
    source_index_counter = 0
    status_counts: dict[str, int] = {}

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
            source_meta = _source_meta(group, snapshot, source_index=source_index_counter)
            source_index_counter += 1
            body_x, body_y = _snapshot_obstacle_body(snapshot)
            half_width = _base_half_width(snapshot)
            for axis in boundary_axes:
                if axis not in BOUNDARY_AXES:
                    continue
                values = axis_initial_values(
                    axis,
                    body_x=body_x,
                    body_y=body_y,
                    half_width=half_width,
                    timing_deltas=timing_deltas,
                    lateral_deltas=lateral_deltas,
                    half_width_deltas=half_width_deltas,
                )
                evaluations: list[dict[str, Any]] = []
                seen_values: set[float] = set()
                for value in values:
                    key = round(float(value), 9)
                    if key in seen_values:
                        continue
                    seen_values.add(key)
                    result, _, _ = _replay_parameter(
                        snapshot=snapshot,
                        source_meta=source_meta,
                        axis=axis,
                        parameter_value=float(value),
                        model=model,
                        residual_head=residual_head,
                        env_config=env_config,
                        response_dim=response_dim,
                        alpha=float(alpha),
                        horizon=int(horizon),
                        max_continuation_steps=int(max_continuation_steps),
                        device=resolved_device,
                    )
                    evaluations.append(result)
                    if not parse_bool(result.get("reconstructed", False)):
                        replay_errors += 1
                bracket = find_adjacent_margin_bracket(evaluations)
                if bracket is None:
                    for value in axis_expansion_values(
                        axis,
                        body_x=body_x,
                        body_y=body_y,
                        half_width=half_width,
                        max_expansion_attempts=int(max_expansion_attempts),
                    ):
                        key = round(float(value), 9)
                        if key in seen_values:
                            continue
                        seen_values.add(key)
                        result, _, _ = _replay_parameter(
                            snapshot=snapshot,
                            source_meta=source_meta,
                            axis=axis,
                            parameter_value=float(value),
                            model=model,
                            residual_head=residual_head,
                            env_config=env_config,
                            response_dim=response_dim,
                            alpha=float(alpha),
                            horizon=int(horizon),
                            max_continuation_steps=int(max_continuation_steps),
                            device=resolved_device,
                        )
                        evaluations.append(result)
                        if not parse_bool(result.get("reconstructed", False)):
                            replay_errors += 1
                        bracket = find_adjacent_margin_bracket(evaluations)
                        if bracket is not None:
                            break
                failure_reason = "" if bracket is not None else "no_collision_safe_bracket"
                bracket_seed_rows.append(
                    _bracket_seed_row(
                        bracket_id=bracket_id,
                        source_meta=source_meta,
                        axis=axis,
                        evaluations=evaluations,
                        bracket=bracket,
                        failure_reason=failure_reason,
                    )
                )
                if bracket is None:
                    bracket_failure_rows.append(
                        {
                            **source_meta,
                            "boundary_axis": axis,
                            "failure_reason": failure_reason,
                            "evaluations": int(len(evaluations)),
                        }
                    )
                    bracket_id += 1
                    continue
                negative, positive = bracket
                rows, accepted_rows, candidate_id, status = refine_bracket(
                    bracket_id=bracket_id,
                    snapshot=snapshot,
                    source_meta=source_meta,
                    axis=axis,
                    negative=negative,
                    positive=positive,
                    model=model,
                    residual_head=residual_head,
                    env_config=env_config,
                    response_dim=response_dim,
                    alpha=float(alpha),
                    horizon=int(horizon),
                    max_continuation_steps=int(max_continuation_steps),
                    max_refinement_iterations=int(max_refinement_iterations),
                    primary_margin_threshold=float(primary_margin_threshold),
                    parameter_tolerance=float(parameter_tolerance),
                    device=resolved_device,
                    start_candidate_id=candidate_id,
                )
                status_counts[status] = status_counts.get(status, 0) + 1
                refinement_rows.extend(rows)
                accepted_raw.extend(accepted_rows)
                for accepted in accepted_rows:
                    relocated = relocate_temporal_snapshot(
                        snapshot,
                        body_longitudinal=float(accepted["target_obstacle_body_x"]),
                        body_lateral=float(accepted["target_obstacle_body_y"]),
                        half_width=float(accepted["target_obstacle_half_width"]),
                    )
                    normal_result, normal_actions = replay_residual_sequence_variant(
                        model=model,
                        residual_head=residual_head,
                        snapshot=relocated,
                        env_config=env_config,
                        variant="normal",
                        horizon=int(horizon),
                        response_dim=response_dim,
                        reference_actions=None,
                        base_reference_actions=None,
                        max_continuation_steps=int(max_continuation_steps),
                        alpha=float(alpha),
                        device=resolved_device,
                    )
                    _ = normal_result
                    for variant in sorted(SUPPORTED_VARIANTS):
                        result, _ = replay_residual_sequence_variant(
                            model=model,
                            residual_head=residual_head,
                            snapshot=relocated,
                            env_config=env_config,
                            variant=variant,
                            horizon=int(horizon),
                            response_dim=response_dim,
                            reference_actions=normal_actions,
                            base_reference_actions=normal_actions,
                            max_continuation_steps=int(max_continuation_steps),
                            alpha=float(alpha),
                            device=resolved_device,
                        )
                        intervention_rows.append(
                            {
                                "candidate_id": int(accepted["candidate_id"]),
                                "bracket_id": int(bracket_id),
                                "source_group_id": int(source_meta["source_group_id"]),
                                "snapshot_uid": source_meta["snapshot_uid"],
                                "source_index": int(source_meta["source_index"]),
                                "seed": int(source_meta["seed"]),
                                "warmup_mode": source_meta["warmup_mode"],
                                "fault_family_pair": source_meta["fault_family_pair"],
                                "boundary_axis": axis,
                                "parameter_value": float(accepted["parameter_value"]),
                                "intervention_variant": variant,
                                "intervention_success": parse_bool(result.get("success", False)),
                                "intervention_collision": parse_bool(result.get("collision", False)),
                                "intervention_margin": _finite_float(result.get("min_clearance_margin")),
                                "intervention_prefix_l2_mean": _finite_float(result.get("prefix_l2_mean")),
                            }
                        )
                _append_progress(
                    progress_path,
                    {
                        "source_group_id": int(group["source_group_id"]),
                        "snapshot_uid": source_meta["snapshot_uid"],
                        "bracket_id": int(bracket_id),
                        "stage": "refine",
                        "boundary_axis": axis,
                        "status": status,
                        "refinement_rows": len(rows),
                        "accepted_rows": len(accepted_rows),
                    },
                )
                bracket_id += 1

    accepted = select_adaptive_balanced_rows(
        accepted_raw,
        max_rows_per_seed=max(1, int(np.floor(float(max_seed_dominance) * float(min_rows)))),
        max_rows_per_source_group=max(1, int(np.floor(float(max_source_group_dominance) * float(min_rows)))),
        max_rows_per_fault_pair=max(1, int(np.floor(float(max_fault_pair_dominance) * float(min_rows)))),
        max_rows_per_boundary_axis=max(1, int(np.floor(float(max_boundary_axis_dominance) * float(min_rows)))),
    )
    warmup_artifact_rows = sum(1 for row in warmup_rows if parse_bool(row.get("warmup_artifact", False)))
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    brackets_valid = sum(1 for row in bracket_seed_rows if str(row.get("status", "")) == "valid")
    bracket_nonmonotone_count = int(status_counts.get("ambiguous_outcome", 0))
    result_class = classify_adaptive_bracketing_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        warmup_artifact_rows=int(warmup_artifact_rows),
        replay_errors=int(replay_errors),
        brackets_valid=int(brackets_valid),
        bracket_nonmonotone_count=int(bracket_nonmonotone_count),
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

    source_summary = [
        *_summary_rows(accepted, "seed", label="seed"),
        *_summary_rows(accepted, "source_group_id", label="source_group"),
        *_summary_rows(accepted, "fault_family_pair", label="fault_pair"),
        *_summary_rows(accepted, "warmup_mode", label="warmup"),
    ]
    axis_summary = _summary_rows(accepted, "boundary_axis", label="axis")

    write_csv_rows(run_dir / "source_group_rows.csv", source_group_rows, fieldnames=SOURCE_GROUP_FIELDS)
    write_csv_rows(run_dir / "warmup_probe_rows.csv", warmup_rows, fieldnames=WARMUP_PROBE_FIELDS)
    write_csv_rows(run_dir / "bracket_seed_rows.csv", bracket_seed_rows, fieldnames=BRACKET_SEED_FIELDS)
    write_csv_rows(run_dir / "bracket_refinement_rows.csv", refinement_rows, fieldnames=REFINEMENT_FIELDS)
    write_csv_rows(run_dir / "accepted_primary_rows.csv", accepted, fieldnames=REFINEMENT_FIELDS)
    write_csv_rows(run_dir / "intervention_replay_rows.csv", intervention_rows, fieldnames=INTERVENTION_FIELDS)
    write_csv_rows(run_dir / "source_balance_summary.csv", source_summary, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(run_dir / "axis_balance_summary.csv", axis_summary, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(run_dir / "bracket_failure_rows.csv", bracket_failure_rows, fieldnames=FAILURE_FIELDS)
    fault_limitations = run_dir / "fault_proxy_limitations.md"
    fault_limitations.write_text(
        "\n".join(
            [
                "# M814 Fault Proxy Limitations",
                "",
                "M814 uses current single-track current-model/proxy faults only.",
                "It must not be described as faithful wheel-level blowout, split-mu,",
                "halfshaft, stuck-caliper, suspension, tire-temperature, or wheel-speed physics.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    summary = {
        "run_type": "v4_adaptive_boundary_bracketing",
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
        "brackets_attempted": int(len(bracket_seed_rows)),
        "brackets_valid": int(brackets_valid),
        "brackets_refined": int(sum(status_counts.values())),
        "bracket_status_counts": dict(sorted(status_counts.items())),
        "bracket_nonmonotone_count": int(bracket_nonmonotone_count),
        "bracket_expansion_fail_count": int(len(bracket_failure_rows)),
        "bracket_refinement_rows": int(len(refinement_rows)),
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
        "accepted_boundary_axis_counts": _value_counts(accepted, "boundary_axis"),
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
        "bracket_seed_rows_csv": run_dir / "bracket_seed_rows.csv",
        "bracket_refinement_rows_csv": run_dir / "bracket_refinement_rows.csv",
        "accepted_primary_rows_csv": run_dir / "accepted_primary_rows.csv",
        "intervention_replay_rows_csv": run_dir / "intervention_replay_rows.csv",
        "source_balance_summary_csv": run_dir / "source_balance_summary.csv",
        "axis_balance_summary_csv": run_dir / "axis_balance_summary.csv",
        "bracket_failure_rows_csv": run_dir / "bracket_failure_rows.csv",
        "fault_proxy_limitations_md": fault_limitations,
        "progress_jsonl": progress_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_axis_list(raw: str) -> tuple[str, ...]:
    axes = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    if not axes:
        raise argparse.ArgumentTypeError("expected at least one boundary axis")
    unknown = [axis for axis in axes if axis not in BOUNDARY_AXES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown boundary axes: {unknown}")
    return axes


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 adaptive boundary bracketing.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--primary-margin-threshold", type=float, default=5e-5)
    parser.add_argument("--seed-start", type=int, default=None)
    parser.add_argument("--seed-count", type=int, default=12)
    parser.add_argument("--max-base-faults", type=int, default=8)
    parser.add_argument("--max-fault-specs", type=int, default=14)
    parser.add_argument("--max-source-groups", type=int, default=96)
    parser.add_argument("--max-snapshots-per-group", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=20)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--boundary-axes", type=_parse_axis_list, default=BOUNDARY_AXES)
    parser.add_argument("--timing-deltas", type=parse_float_list, default=DEFAULT_OBSTACLE_TIMING_DELTAS)
    parser.add_argument("--lateral-deltas", type=parse_float_list, default=DEFAULT_LATERAL_DELTAS)
    parser.add_argument("--half-width-deltas", type=parse_float_list, default=DEFAULT_HALF_WIDTH_DELTAS)
    parser.add_argument("--max-expansion-attempts", type=int, default=6)
    parser.add_argument("--max-refinement-iterations", type=int, default=12)
    parser.add_argument("--parameter-tolerance", type=float, default=1e-4)
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
    summary = run_adaptive_bracketing(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        primary_margin_threshold=float(args.primary_margin_threshold),
        seed_start=seed_start,
        seed_count=int(args.seed_count),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_source_groups=int(args.max_source_groups),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        horizon=int(args.horizon),
        boundary_axes=tuple(args.boundary_axes),
        timing_deltas=tuple(args.timing_deltas),
        lateral_deltas=tuple(args.lateral_deltas),
        half_width_deltas=tuple(args.half_width_deltas),
        max_expansion_attempts=int(args.max_expansion_attempts),
        max_refinement_iterations=int(args.max_refinement_iterations),
        parameter_tolerance=float(args.parameter_tolerance),
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
