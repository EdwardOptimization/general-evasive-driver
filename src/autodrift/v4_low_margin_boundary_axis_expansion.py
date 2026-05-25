"""Expand v4 low-margin boundary retargeting across source and fault axes."""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import json
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
    FaultSpec,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import (
    _base_half_width,
    _collect_seed_snapshots,
    _find_snapshot,
    relocate_temporal_snapshot,
)
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_boundary_window_retarget import (
    ANCHOR_FIELDS,
    _accepted_rows,
    _anchor_meta,
    _append_progress,
    _normal_alpha_rows,
    _snapshot_obstacle_body,
    parse_bool,
    parse_float_list,
    read_csv_rows,
    select_boundary_anchor_rows,
)
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _load_residual_head,
    replay_residual_sequence_variant,
)


DEFAULT_TARGET_MARGINS = (5e-6, 2.5e-5, 4.5e-5)
DEFAULT_LATERAL_DELTAS = (-0.60, -0.40, -0.25, -0.10, -0.05, 0.05, 0.10, 0.25, 0.40, 0.60)
DEFAULT_STEP_OFFSETS = (-3, -2, -1, 1, 2, 3)
DEFAULT_FAULT_ACTIVATION_DELTAS = (-3, -2, -1, 1, 2, 3)
DEFAULT_FAULT_SEVERITY_DELTAS = (-0.08, -0.04, -0.02, 0.02, 0.04, 0.08)
DEFAULT_DISTANCE_BRACKET_DELTAS = (-0.35, -0.25, -0.15, -0.08, -0.04, 0.04, 0.08, 0.15, 0.25, 0.35)
DEFAULT_HALF_WIDTH_BRACKET_DELTAS = (-0.010, -0.006, -0.003, 0.003, 0.006, 0.010)

GEOMETRY_AXIS_FAMILIES = {
    "obstacle_half_width",
    "obstacle_lateral_offset",
    "bracketed_obstacle_distance",
    "bracketed_obstacle_half_width",
}

FAULT_SEVERITY_KEYS = {
    "mu_scale",
    "cf_scale",
    "cr_scale",
    "max_drive_force_scale",
    "max_brake_force_scale",
    "max_steer_scale",
    "max_steer_rate_scale",
    "drive_tau_scale",
    "steer_tau_scale",
}

AXIS_PLAN_FIELDS = [
    *ANCHOR_FIELDS,
    "candidate_id",
    "retarget_axis",
    "retarget_axis_family",
    "replay_fault_name",
    "source_obstacle_body_x",
    "source_obstacle_body_y",
    "source_obstacle_half_width",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "target_margin_m",
    "obstacle_x_delta_m",
    "obstacle_y_delta_m",
    "half_width_delta_m",
    "source_step",
    "target_step",
    "step_offset",
    "fault_activation_step_delta",
    "fault_severity_delta",
    "fault_param_key",
    "modified_fault_params_json",
    "bracket_round",
    "bracket_parent_candidate_id",
    "plan_reason",
]

AXIS_REPLAY_FIELDS = [
    *AXIS_PLAN_FIELDS,
    "reconstructed",
    "rejection_reason",
    "actual_snapshot_step",
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
    "intervention_success",
    "intervention_collision",
    "intervention_margin",
    "intervention_prefix_l2_mean",
]

SUMMARY_FIELDS = [
    "group",
    "rows",
    "unique_seed_count",
    "unique_source_index_count",
    "unique_fault_pair_count",
    "max_seed_dominance",
    "max_source_index_dominance",
    "max_fault_pair_dominance",
]

BALANCE_FIELDS = [
    "retarget_axis",
    "retarget_axis_family",
    "raw_accepted_rows",
    "balanced_accepted_rows",
    "unique_seed_count",
    "unique_source_index_count",
    "unique_fault_pair_count",
    "max_seed_dominance",
    "max_source_index_dominance",
    "max_fault_pair_dominance",
]

BRACKET_TRACE_FIELDS = [
    "candidate_id",
    "anchor_id",
    "retarget_axis",
    "bracket_round",
    "bracket_parent_candidate_id",
    "source_obstacle_body_x",
    "source_obstacle_half_width",
    "target_obstacle_body_x",
    "target_obstacle_half_width",
    "obstacle_x_delta_m",
    "half_width_delta_m",
    "success",
    "collision",
    "min_clearance_margin",
]


def _fault_pair(row: dict[str, Any]) -> str:
    value = str(row.get("fault_family_pair", "")).strip()
    if value:
        return value
    return f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}"


def _candidate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("anchor_id", "")),
        str(row.get("retarget_axis", "")),
        str(row.get("replay_fault_name", "")),
        str(row.get("target_step", "")),
        f"{_finite_float(row.get('obstacle_x_delta_m'), default=0.0):.8f}",
        f"{_finite_float(row.get('obstacle_y_delta_m'), default=0.0):.8f}",
        f"{_finite_float(row.get('half_width_delta_m'), default=0.0):.8f}",
        str(row.get("fault_param_key", "")),
        f"{_finite_float(row.get('fault_severity_delta'), default=0.0):.8f}",
        str(row.get("fault_activation_step_delta", "")),
    )


def _base_candidate(anchor: dict[str, Any], *, axis: str, family: str, reason: str) -> dict[str, Any]:
    source_step = int(anchor.get("step", -1))
    return {
        **anchor,
        "candidate_id": -1,
        "retarget_axis": axis,
        "retarget_axis_family": family,
        "replay_fault_name": str(anchor.get("preferred_fault", "")),
        "source_obstacle_body_x": float("nan"),
        "source_obstacle_body_y": float("nan"),
        "source_obstacle_half_width": float("nan"),
        "target_obstacle_body_x": float("nan"),
        "target_obstacle_body_y": float("nan"),
        "target_obstacle_half_width": float("nan"),
        "target_margin_m": float("nan"),
        "obstacle_x_delta_m": 0.0,
        "obstacle_y_delta_m": 0.0,
        "half_width_delta_m": 0.0,
        "source_step": source_step,
        "target_step": source_step,
        "step_offset": 0,
        "fault_activation_step_delta": 0,
        "fault_severity_delta": 0.0,
        "fault_param_key": "",
        "modified_fault_params_json": "",
        "bracket_round": 0,
        "bracket_parent_candidate_id": -1,
        "plan_reason": reason,
    }


def _modified_fault_name(base_name: str, *, axis: str, token: str) -> str:
    safe_token = token.replace("+", "p").replace("-", "m").replace(".", "d")
    return f"{base_name}__m807_{axis}_{safe_token}"


def modify_fault_for_axis(base_fault: FaultSpec, row: dict[str, Any]) -> FaultSpec:
    """Return the replay fault requested by an axis candidate."""

    axis = str(row.get("retarget_axis", ""))
    if axis == "fault_activation_step":
        delta = int(row.get("fault_activation_step_delta", 0))
        activation_step = max(0, int(base_fault.activation_step) + delta)
        return replace(
            base_fault,
            name=_modified_fault_name(base_fault.name, axis=axis, token=f"{delta:+d}"),
            activation_step=activation_step,
        )
    if axis == "fault_severity":
        key = str(row.get("fault_param_key", ""))
        if key not in FAULT_SEVERITY_KEYS or key not in base_fault.params:
            raise ValueError(f"cannot severity-sweep {key!r} for fault {base_fault.name!r}")
        delta = float(row.get("fault_severity_delta", 0.0))
        params = dict(base_fault.params)
        params[key] = max(1e-6, float(params[key]) * (1.0 + delta))
        token = f"{key}_{delta:+.3f}"
        return replace(
            base_fault,
            name=_modified_fault_name(base_fault.name, axis=axis, token=token),
            params=params,
        )
    return base_fault


def _candidate_sort_key(row: dict[str, Any]) -> tuple[int, float, float, str]:
    axis_order = {
        "obstacle_half_width": 0,
        "obstacle_lateral_offset": 1,
        "source_step_neighborhood": 2,
        "fault_activation_step": 3,
        "fault_severity": 4,
        "bracketed_obstacle_distance": 5,
        "bracketed_obstacle_half_width": 6,
    }
    return (
        axis_order.get(str(row.get("retarget_axis", "")), 99),
        abs(_finite_float(row.get("half_width_delta_m"), default=0.0)),
        abs(_finite_float(row.get("obstacle_x_delta_m"), default=0.0))
        + abs(_finite_float(row.get("obstacle_y_delta_m"), default=0.0))
        + abs(_finite_float(row.get("fault_severity_delta"), default=0.0)),
        str(row.get("fault_param_key", "")),
    )


def plan_axis_expansion_candidates(
    anchors: list[dict[str, Any]],
    *,
    faults_by_name: dict[str, FaultSpec],
    target_margins: tuple[float, ...] = DEFAULT_TARGET_MARGINS,
    lateral_deltas: tuple[float, ...] = DEFAULT_LATERAL_DELTAS,
    step_offsets: tuple[int, ...] = DEFAULT_STEP_OFFSETS,
    fault_activation_deltas: tuple[int, ...] = DEFAULT_FAULT_ACTIVATION_DELTAS,
    fault_severity_deltas: tuple[float, ...] = DEFAULT_FAULT_SEVERITY_DELTAS,
    distance_bracket_deltas: tuple[float, ...] = DEFAULT_DISTANCE_BRACKET_DELTAS,
    half_width_bracket_deltas: tuple[float, ...] = DEFAULT_HALF_WIDTH_BRACKET_DELTAS,
    max_half_width_delta: float = 1e-2,
    max_candidates_per_anchor: int | None = 48,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for anchor in anchors:
        margin = _finite_float(anchor.get("source_margin"))
        if not np.isfinite(margin):
            continue
        local_rows: list[dict[str, Any]] = []
        if str(anchor.get("anchor_pool")) in {"collision_edge", "safe_edge"}:
            for target_margin in target_margins:
                half_delta = float(margin) - float(target_margin)
                if abs(half_delta) <= float(max_half_width_delta):
                    row = _base_candidate(
                        anchor,
                        axis="obstacle_half_width",
                        family="obstacle_half_width",
                        reason=f"{anchor['anchor_pool']}_half_width_to_target_margin",
                    )
                    row["target_margin_m"] = float(target_margin)
                    row["half_width_delta_m"] = float(half_delta)
                    local_rows.append(row)
        for delta in lateral_deltas:
            row = _base_candidate(
                anchor,
                axis="obstacle_lateral_offset",
                family="obstacle_lateral_offset",
                reason="body_frame_lateral_offset_sweep",
            )
            row["obstacle_y_delta_m"] = float(delta)
            local_rows.append(row)
        for offset in step_offsets:
            row = _base_candidate(
                anchor,
                axis="source_step_neighborhood",
                family="source_step_neighborhood",
                reason="exact_source_step_neighborhood",
            )
            row["step_offset"] = int(offset)
            row["target_step"] = int(anchor.get("step", -1)) + int(offset)
            local_rows.append(row)
        base_fault = faults_by_name.get(str(anchor.get("preferred_fault", "")))
        if base_fault is not None:
            if int(base_fault.activation_step) > 0:
                for delta in fault_activation_deltas:
                    row = _base_candidate(
                        anchor,
                        axis="fault_activation_step",
                        family="fault_activation_step",
                        reason="activation_step_micro_sweep",
                    )
                    row["fault_activation_step_delta"] = int(delta)
                    fault = modify_fault_for_axis(base_fault, row)
                    row["replay_fault_name"] = fault.name
                    row["modified_fault_params_json"] = json.dumps(
                        {
                            "base_activation_step": int(base_fault.activation_step),
                            "target_activation_step": int(fault.activation_step),
                            "params": fault.params,
                        },
                        sort_keys=True,
                    )
                    local_rows.append(row)
            for key in sorted(set(base_fault.params) & FAULT_SEVERITY_KEYS):
                for delta in fault_severity_deltas:
                    row = _base_candidate(
                        anchor,
                        axis="fault_severity",
                        family="fault_severity",
                        reason="fault_param_micro_sweep",
                    )
                    row["fault_param_key"] = key
                    row["fault_severity_delta"] = float(delta)
                    fault = modify_fault_for_axis(base_fault, row)
                    row["replay_fault_name"] = fault.name
                    row["modified_fault_params_json"] = json.dumps(
                        {
                            "base_params": base_fault.params,
                            "target_params": fault.params,
                            "swept_param": key,
                        },
                        sort_keys=True,
                    )
                    local_rows.append(row)
        for delta in distance_bracket_deltas:
            row = _base_candidate(
                anchor,
                axis="bracketed_obstacle_distance",
                family="bracketed_obstacle_distance",
                reason="distance_coarse_bracket",
            )
            row["obstacle_x_delta_m"] = float(delta)
            local_rows.append(row)
        for delta in half_width_bracket_deltas:
            row = _base_candidate(
                anchor,
                axis="bracketed_obstacle_half_width",
                family="bracketed_obstacle_half_width",
                reason="half_width_coarse_bracket",
            )
            row["half_width_delta_m"] = float(delta)
            local_rows.append(row)
        deduped: list[dict[str, Any]] = []
        for row in sorted(local_rows, key=_candidate_sort_key):
            key = _candidate_key(row)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        if max_candidates_per_anchor is not None:
            deduped = deduped[: max(1, int(max_candidates_per_anchor))]
        for row in deduped:
            row["candidate_id"] = len(candidates)
            candidates.append(row)
    return candidates


def _find_exact_snapshot(snapshots: list[Any], *, fault_name: str, step: int) -> Any | None:
    for snapshot in snapshots:
        if str(snapshot.fault.name) == str(fault_name) and int(snapshot.step) == int(step):
            return snapshot
    return None


def _fill_geometry(row: dict[str, Any], snapshot: Any) -> tuple[float, float, float]:
    source_x, source_y = _snapshot_obstacle_body(snapshot)
    source_width = _base_half_width(snapshot)
    target_x = max(1.0, float(source_x) + _finite_float(row.get("obstacle_x_delta_m"), default=0.0))
    target_y = float(source_y) + _finite_float(row.get("obstacle_y_delta_m"), default=0.0)
    target_width = max(0.05, float(source_width) + _finite_float(row.get("half_width_delta_m"), default=0.0))
    row["source_obstacle_body_x"] = float(source_x)
    row["source_obstacle_body_y"] = float(source_y)
    row["source_obstacle_half_width"] = float(source_width)
    row["target_obstacle_body_x"] = float(target_x)
    row["target_obstacle_body_y"] = float(target_y)
    row["target_obstacle_half_width"] = float(target_width)
    return target_x, target_y, target_width


def _accepted_axis_rows(rows: list[dict[str, Any]], *, primary_margin_threshold: float) -> list[dict[str, Any]]:
    return _accepted_rows(rows, primary_margin_threshold=primary_margin_threshold)


def select_axis_balanced_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows_per_seed: int = 20,
    max_rows_per_source_index: int = 12,
    max_rows_per_fault_pair: int = 32,
    max_rows_per_axis: int = 48,
) -> list[dict[str, Any]]:
    """Greedily export accepted rows under source and axis caps."""

    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("retarget_axis", "")),
            str(row.get("fault_family_pair", "")),
            str(row.get("seed", "")),
            abs(_finite_float(row.get("min_clearance_margin"), default=1.0) - 2.5e-5),
            int(float(row.get("candidate_id", 0))),
        ),
    )
    for row in ordered:
        keys = {
            ("seed", str(row.get("seed", ""))): int(max_rows_per_seed),
            ("source_index", str(row.get("source_index", ""))): int(max_rows_per_source_index),
            ("fault_family_pair", _fault_pair(row)): int(max_rows_per_fault_pair),
            ("retarget_axis", str(row.get("retarget_axis", ""))): int(max_rows_per_axis),
        }
        if any(counts.get(key, 0) >= limit for key, limit in keys.items()):
            continue
        selected.append(row)
        for key in keys:
            counts[key] = counts.get(key, 0) + 1
    return selected


def _group_summary(rows: list[dict[str, Any]], key: str, *, group_label: str | None = None) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key, "")), []).append(row)
    output: list[dict[str, Any]] = []
    for group, group_rows in sorted(grouped.items()):
        output.append(
            {
                "group": group if group_label is None else f"{group_label}:{group}",
                "rows": int(len(group_rows)),
                "unique_seed_count": unique_count(group_rows, "seed"),
                "unique_source_index_count": unique_count(group_rows, "source_index"),
                "unique_fault_pair_count": unique_count(group_rows, "fault_family_pair"),
                "max_seed_dominance": max_share(group_rows, "seed"),
                "max_source_index_dominance": max_share(group_rows, "source_index"),
                "max_fault_pair_dominance": max_share(group_rows, "fault_family_pair"),
            }
        )
    return output


def _axis_balance_summary(raw_rows: list[dict[str, Any]], balanced_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = sorted({str(row.get("retarget_axis", "")) for row in [*raw_rows, *balanced_rows]})
    output: list[dict[str, Any]] = []
    for axis in axes:
        raw = [row for row in raw_rows if str(row.get("retarget_axis", "")) == axis]
        balanced = [row for row in balanced_rows if str(row.get("retarget_axis", "")) == axis]
        family = str(raw[0].get("retarget_axis_family", "")) if raw else ""
        output.append(
            {
                "retarget_axis": axis,
                "retarget_axis_family": family,
                "raw_accepted_rows": int(len(raw)),
                "balanced_accepted_rows": int(len(balanced)),
                "unique_seed_count": unique_count(balanced, "seed"),
                "unique_source_index_count": unique_count(balanced, "source_index"),
                "unique_fault_pair_count": unique_count(balanced, "fault_family_pair"),
                "max_seed_dominance": max_share(balanced, "seed"),
                "max_source_index_dominance": max_share(balanced, "source_index"),
                "max_fault_pair_dominance": max_share(balanced, "fault_family_pair"),
            }
        )
    return output


def _axis_minimum_pass(rows: list[dict[str, Any]], *, min_axis_rows: int, min_axes: int) -> bool:
    counts: dict[str, int] = {}
    for row in rows:
        axis = str(row.get("retarget_axis", ""))
        counts[axis] = counts.get(axis, 0) + 1
    return sum(1 for count in counts.values() if count >= int(min_axis_rows)) >= int(min_axes)


def classify_boundary_axis_expansion_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    reconstruction_failures: int,
    accepted_rows: list[dict[str, Any]],
    min_rows: int,
    min_seeds: int,
    min_source_indices: int,
    min_fault_pairs: int,
    min_retarget_axes: int,
    max_seed_dominance: float,
    max_source_index_dominance: float,
    max_fault_pair_dominance: float,
    max_axis_dominance: float,
    min_axis_rows: int = 10,
    min_axes_with_min_rows: int = 3,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_low_margin_boundary_axis_expansion_contract_violation"
    if int(reconstruction_failures) > 0 and not accepted_rows:
        return "v4_low_margin_boundary_axis_expansion_replay_error"
    if not accepted_rows or len(accepted_rows) < int(min_rows):
        return "v4_low_margin_boundary_axis_expansion_sparse"
    families = {str(row.get("retarget_axis_family", "")) for row in accepted_rows}
    if families and families.issubset(GEOMETRY_AXIS_FAMILIES):
        return "v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic"
    if (
        unique_count(accepted_rows, "retarget_axis") < int(min_retarget_axes)
        or max_share(accepted_rows, "retarget_axis") > float(max_axis_dominance)
        or not _axis_minimum_pass(
            accepted_rows,
            min_axis_rows=int(min_axis_rows),
            min_axes=int(min_axes_with_min_rows),
        )
    ):
        return "v4_low_margin_boundary_axis_expansion_axis_concentrated"
    if (
        unique_count(accepted_rows, "seed") < int(min_seeds)
        or unique_count(accepted_rows, "source_index") < int(min_source_indices)
        or unique_count(accepted_rows, "fault_family_pair") < int(min_fault_pairs)
        or max_share(accepted_rows, "seed") > float(max_seed_dominance)
        or max_share(accepted_rows, "source_index") > float(max_source_index_dominance)
        or max_share(accepted_rows, "fault_family_pair") > float(max_fault_pair_dominance)
    ):
        return "v4_low_margin_boundary_axis_expansion_source_concentrated"
    return "v4_low_margin_boundary_axis_expansion_pass"


def _bracket_value(row: dict[str, Any]) -> float:
    axis = str(row.get("retarget_axis", ""))
    if axis == "bracketed_obstacle_distance":
        return _finite_float(row.get("target_obstacle_body_x"))
    if axis == "bracketed_obstacle_half_width":
        return _finite_float(row.get("target_obstacle_half_width"))
    return float("nan")


def plan_next_bracket_candidates(
    replay_rows: list[dict[str, Any]],
    *,
    next_candidate_id: int,
    primary_margin_threshold: float,
    safe_margin_ceiling: float,
    max_bracket_rounds: int,
    seen_keys: set[tuple[str, ...]],
) -> list[dict[str, Any]]:
    """Generate observed-margin bisection candidates for bracketed axes."""

    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for row in replay_rows:
        axis = str(row.get("retarget_axis", ""))
        if axis not in {"bracketed_obstacle_distance", "bracketed_obstacle_half_width"}:
            continue
        if not parse_bool(row.get("reconstructed", False)):
            continue
        bracket_round = int(float(row.get("bracket_round", 0)))
        if bracket_round >= int(max_bracket_rounds):
            continue
        groups.setdefault((str(row.get("anchor_id", "")), axis, bracket_round), []).append(row)

    candidates: list[dict[str, Any]] = []
    for (_anchor_id, axis, bracket_round), rows in sorted(groups.items()):
        ordered = sorted(rows, key=_bracket_value)
        for left, right in zip(ordered, ordered[1:]):
            left_margin = _finite_float(left.get("min_clearance_margin"))
            right_margin = _finite_float(right.get("min_clearance_margin"))
            left_value = _bracket_value(left)
            right_value = _bracket_value(right)
            if not all(np.isfinite(value) for value in (left_margin, right_margin, left_value, right_value)):
                continue
            crosses_zero = left_margin == 0.0 or right_margin == 0.0 or (left_margin < 0.0 < right_margin) or (right_margin < 0.0 < left_margin)
            near_window = min(abs(left_margin), abs(right_margin)) <= float(safe_margin_ceiling)
            if not (crosses_zero or near_window):
                continue
            midpoint = 0.5 * (left_value + right_value)
            candidate = {field: left.get(field, "") for field in AXIS_PLAN_FIELDS}
            candidate["candidate_id"] = int(next_candidate_id + len(candidates))
            candidate["bracket_round"] = int(bracket_round) + 1
            candidate["bracket_parent_candidate_id"] = int(float(left.get("candidate_id", -1)))
            candidate["plan_reason"] = f"{axis}_observed_margin_bisection"
            if axis == "bracketed_obstacle_distance":
                source_x = _finite_float(left.get("source_obstacle_body_x"))
                candidate["obstacle_x_delta_m"] = float(midpoint - source_x)
                candidate["target_obstacle_body_x"] = float(midpoint)
            else:
                source_width = _finite_float(left.get("source_obstacle_half_width"))
                candidate["half_width_delta_m"] = float(midpoint - source_width)
                candidate["target_obstacle_half_width"] = float(midpoint)
            key = _candidate_key(candidate)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            candidates.append(candidate)
            if abs(left_margin) <= float(primary_margin_threshold) or abs(right_margin) <= float(primary_margin_threshold):
                break
    return candidates


def _replay_candidate(
    *,
    plan: dict[str, Any],
    snapshots_by_seed: dict[int, list[Any]],
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    max_continuation_steps: int,
    alpha: float,
    primary_margin_threshold: float,
    device: torch.device,
) -> dict[str, Any]:
    meta = {key: plan.get(key, "") for key in AXIS_PLAN_FIELDS}
    seed = int(plan.get("seed", -1))
    target_step = int(plan.get("target_step", plan.get("step", -1)))
    horizon = int(plan.get("horizon", 0))
    fault_name = str(plan.get("replay_fault_name", plan.get("preferred_fault", "")))
    if str(plan.get("retarget_axis")) == "source_step_neighborhood":
        snapshot = _find_exact_snapshot(snapshots_by_seed.get(seed, []), fault_name=fault_name, step=target_step)
    else:
        snapshot = _find_snapshot(snapshots_by_seed.get(seed, []), fault_name=fault_name, step=target_step)
    if snapshot is None:
        return {
            **meta,
            "reconstructed": False,
            "rejection_reason": "missing_source_snapshot",
            "actual_snapshot_step": "",
        }

    target_x, target_y, target_width = _fill_geometry(plan, snapshot)
    meta = {key: plan.get(key, "") for key in AXIS_PLAN_FIELDS}
    relocated = relocate_temporal_snapshot(
        snapshot,
        body_longitudinal=float(target_x),
        body_lateral=float(target_y),
        half_width=float(target_width),
    )
    normal, normal_actions = replay_residual_sequence_variant(
        model=model,
        residual_head=residual_head,
        snapshot=relocated,
        env_config=env_config,
        variant="normal",
        horizon=horizon,
        response_dim=response_dim,
        reference_actions=None,
        base_reference_actions=None,
        max_continuation_steps=max_continuation_steps,
        alpha=float(alpha),
        device=device,
    )
    replay = {
        **meta,
        "reconstructed": True,
        "rejection_reason": "",
        "actual_snapshot_step": int(snapshot.step),
        **normal,
        "intervention_success": "",
        "intervention_collision": "",
        "intervention_margin": "",
        "intervention_prefix_l2_mean": "",
    }
    replay["variant"] = str(plan.get("variant", ""))
    margin = _finite_float(normal.get("min_clearance_margin"))
    if (
        parse_bool(normal.get("success", False))
        and not parse_bool(normal.get("collision", False))
        and np.isfinite(margin)
        and 0.0 <= margin <= float(primary_margin_threshold)
        and str(plan.get("variant", "")) in SUPPORTED_VARIANTS
    ):
        intervention, _ = replay_residual_sequence_variant(
            model=model,
            residual_head=residual_head,
            snapshot=relocated,
            env_config=env_config,
            variant=str(plan.get("variant")),
            horizon=horizon,
            response_dim=response_dim,
            reference_actions=normal_actions,
            base_reference_actions=normal_actions,
            max_continuation_steps=max_continuation_steps,
            alpha=float(alpha),
            device=device,
        )
        replay["intervention_success"] = bool(intervention.get("success", False))
        replay["intervention_collision"] = bool(intervention.get("collision", False))
        replay["intervention_margin"] = _finite_float(intervention.get("min_clearance_margin"))
        replay["intervention_prefix_l2_mean"] = _finite_float(intervention.get("prefix_l2_mean"))
    return replay


def _build_fault_specs_for_plans(
    *,
    base_faults_by_name: dict[str, FaultSpec],
    plans: list[dict[str, Any]],
) -> dict[str, FaultSpec]:
    specs = dict(base_faults_by_name)
    for row in plans:
        preferred = str(row.get("preferred_fault", ""))
        replay = str(row.get("replay_fault_name", preferred))
        if replay in specs:
            continue
        base = base_faults_by_name.get(preferred)
        if base is None:
            continue
        specs[replay] = modify_fault_for_axis(base, row)
    return specs


def run_boundary_axis_expansion(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    reference_replay_rows_path: Path,
    m804_replay_rows_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    primary_margin_threshold: float,
    collision_margin_floor: float,
    safe_margin_ceiling: float,
    diagnostic_safe_margin_ceiling: float,
    target_margins: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    step_offsets: tuple[int, ...],
    fault_activation_deltas: tuple[int, ...],
    fault_severity_deltas: tuple[float, ...],
    distance_bracket_deltas: tuple[float, ...],
    half_width_bracket_deltas: tuple[float, ...],
    max_half_width_delta: float,
    max_anchors: int | None,
    max_candidates_per_anchor: int | None,
    max_bracket_rounds: int,
    min_rows: int,
    min_seeds: int,
    min_source_indices: int,
    min_fault_pairs: int,
    min_retarget_axes: int,
    max_seed_dominance: float,
    max_source_index_dominance: float,
    max_fault_pair_dominance: float,
    max_axis_dominance: float,
) -> dict[str, Any]:
    del m804_replay_rows_path
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    reference_rows = read_csv_rows(reference_replay_rows_path)
    anchor_rows = select_boundary_anchor_rows(
        reference_rows,
        alpha=float(alpha),
        collision_margin_floor=float(collision_margin_floor),
        safe_margin_ceiling=float(safe_margin_ceiling),
        diagnostic_safe_margin_ceiling=float(diagnostic_safe_margin_ceiling),
        max_anchors=max_anchors,
    )
    scenario_config = load_scenario_config(scenario_config_path)
    base_faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    base_faults_by_name = {fault.name: fault for fault in base_faults}
    initial_plan_rows = plan_axis_expansion_candidates(
        anchor_rows,
        faults_by_name=base_faults_by_name,
        target_margins=target_margins,
        lateral_deltas=lateral_deltas,
        step_offsets=step_offsets,
        fault_activation_deltas=fault_activation_deltas,
        fault_severity_deltas=fault_severity_deltas,
        distance_bracket_deltas=distance_bracket_deltas,
        half_width_bracket_deltas=half_width_bracket_deltas,
        max_half_width_delta=float(max_half_width_delta),
        max_candidates_per_anchor=max_candidates_per_anchor,
    )
    all_plan_rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    seen_plan_keys = {_candidate_key(row) for row in initial_plan_rows}

    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("boundary-axis expansion requires an online recurrent checkpoint")
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
    max_continuation_steps = int(scenario_config.get("max_continuation_steps", 50))

    fault_specs = _build_fault_specs_for_plans(base_faults_by_name=base_faults_by_name, plans=initial_plan_rows)
    fault_names_by_seed: dict[int, set[str]] = {}
    for row in initial_plan_rows:
        seed = int(row.get("seed", -1))
        fault_names_by_seed.setdefault(seed, set()).add(str(row.get("preferred_fault", "")))
        fault_names_by_seed.setdefault(seed, set()).add(str(row.get("replay_fault_name", "")))

    snapshots_by_seed: dict[int, list[Any]] = {}
    for seed, fault_names in sorted(fault_names_by_seed.items()):
        faults = [fault_specs[name] for name in sorted(fault_names) if name in fault_specs]
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(seed),
            config=scenario_config,
            device=resolved_device,
        )

    reconstruction_failures = 0
    pending_rows = list(initial_plan_rows)
    for replay_round in range(max(1, int(max_bracket_rounds) + 1)):
        if not pending_rows:
            break
        current_rows = pending_rows
        pending_rows = []
        for plan in current_rows:
            candidate_start = time.time()
            replay = _replay_candidate(
                plan=plan,
                snapshots_by_seed=snapshots_by_seed,
                model=model,
                residual_head=residual_head,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=max_continuation_steps,
                alpha=float(alpha),
                primary_margin_threshold=float(primary_margin_threshold),
                device=resolved_device,
            )
            if not parse_bool(replay.get("reconstructed", False)):
                reconstruction_failures += 1
            all_plan_rows.append(dict(plan))
            replay_rows.append(replay)
            margin = _finite_float(replay.get("min_clearance_margin"))
            _append_progress(
                progress_path,
                {
                    "candidate_id": int(plan.get("candidate_id", -1)),
                    "anchor_id": int(plan.get("anchor_id", -1)),
                    "retarget_axis": str(plan.get("retarget_axis", "")),
                    "status": "replayed" if parse_bool(replay.get("reconstructed", False)) else str(replay.get("rejection_reason", "")),
                    "margin": margin if np.isfinite(margin) else None,
                    "success": parse_bool(replay.get("success", False)),
                    "collision": parse_bool(replay.get("collision", False)),
                    "elapsed_seconds": time.time() - candidate_start,
                },
            )
        if replay_round < int(max_bracket_rounds):
            pending_rows = plan_next_bracket_candidates(
                replay_rows,
                next_candidate_id=len(all_plan_rows) + len(pending_rows),
                primary_margin_threshold=float(primary_margin_threshold),
                safe_margin_ceiling=float(safe_margin_ceiling),
                max_bracket_rounds=int(max_bracket_rounds),
                seen_keys=seen_plan_keys,
            )

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    accepted_raw = _accepted_axis_rows(replay_rows, primary_margin_threshold=primary_margin_threshold)
    accepted_balanced = select_axis_balanced_rows(accepted_raw)
    rejected = [row for row in replay_rows if row not in accepted_raw]
    bracket_trace = [
        {field: row.get(field, "") for field in BRACKET_TRACE_FIELDS}
        for row in replay_rows
        if str(row.get("retarget_axis", "")).startswith("bracketed_")
    ]
    axis_rows = _axis_balance_summary(accepted_raw, accepted_balanced)
    source_rows = [
        *_group_summary(accepted_balanced, "seed", group_label="seed"),
        *_group_summary(accepted_balanced, "source_index", group_label="source_index"),
        *_group_summary(accepted_balanced, "fault_family_pair", group_label="fault_family_pair"),
    ]
    result_class = classify_boundary_axis_expansion_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        reconstruction_failures=int(reconstruction_failures),
        accepted_rows=accepted_raw,
        min_rows=int(min_rows),
        min_seeds=int(min_seeds),
        min_source_indices=int(min_source_indices),
        min_fault_pairs=int(min_fault_pairs),
        min_retarget_axes=int(min_retarget_axes),
        max_seed_dominance=float(max_seed_dominance),
        max_source_index_dominance=float(max_source_index_dominance),
        max_fault_pair_dominance=float(max_fault_pair_dominance),
        max_axis_dominance=float(max_axis_dominance),
    )

    write_csv_rows(run_dir / "axis_anchor_rows.csv", anchor_rows, fieldnames=ANCHOR_FIELDS)
    write_csv_rows(run_dir / "axis_plan_rows.csv", all_plan_rows, fieldnames=AXIS_PLAN_FIELDS)
    write_csv_rows(run_dir / "axis_replay_rows.csv", replay_rows, fieldnames=AXIS_REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_axis_balanced_rows.csv", accepted_balanced, fieldnames=AXIS_REPLAY_FIELDS)
    write_csv_rows(run_dir / "rejected_axis_candidates.csv", rejected, fieldnames=AXIS_REPLAY_FIELDS)
    write_csv_rows(run_dir / "axis_balance_summary.csv", axis_rows, fieldnames=BALANCE_FIELDS)
    write_csv_rows(run_dir / "source_balance_summary.csv", source_rows, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(run_dir / "bracket_trace_rows.csv", bracket_trace, fieldnames=BRACKET_TRACE_FIELDS)

    summary = {
        "run_type": "v4_low_margin_boundary_axis_expansion",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "reference_replay_rows": reference_replay_rows_path,
        "scenario_config": scenario_config_path,
        "alpha": float(alpha),
        "primary_margin_threshold": float(primary_margin_threshold),
        "anchor_rows": int(len(anchor_rows)),
        "collision_edge_anchor_rows": int(sum(1 for row in anchor_rows if row["anchor_pool"] == "collision_edge")),
        "safe_edge_anchor_rows": int(sum(1 for row in anchor_rows if row["anchor_pool"] == "safe_edge")),
        "diagnostic_safe_anchor_rows": int(sum(1 for row in anchor_rows if row["anchor_pool"] == "diagnostic_safe")),
        "initial_plan_rows": int(len(initial_plan_rows)),
        "axis_plan_rows": int(len(all_plan_rows)),
        "axis_replay_rows": int(len(replay_rows)),
        "reconstruction_failures": int(reconstruction_failures),
        "accepted_axis_raw_rows": int(len(accepted_raw)),
        "accepted_axis_balanced_rows": int(len(accepted_balanced)),
        "raw_unique_accepted_seeds": unique_count(accepted_raw, "seed"),
        "raw_unique_accepted_source_indices": unique_count(accepted_raw, "source_index"),
        "raw_unique_accepted_fault_family_pairs": unique_count(accepted_raw, "fault_family_pair"),
        "raw_unique_accepted_retarget_axes": unique_count(accepted_raw, "retarget_axis"),
        "raw_unique_accepted_retarget_axis_families": unique_count(accepted_raw, "retarget_axis_family"),
        "raw_max_accepted_seed_dominance": max_share(accepted_raw, "seed"),
        "raw_max_accepted_source_index_dominance": max_share(accepted_raw, "source_index"),
        "raw_max_accepted_fault_pair_dominance": max_share(accepted_raw, "fault_family_pair"),
        "raw_max_accepted_retarget_axis_dominance": max_share(accepted_raw, "retarget_axis"),
        "unique_accepted_seeds": unique_count(accepted_balanced, "seed"),
        "unique_accepted_source_indices": unique_count(accepted_balanced, "source_index"),
        "unique_accepted_fault_family_pairs": unique_count(accepted_balanced, "fault_family_pair"),
        "unique_accepted_retarget_axes": unique_count(accepted_balanced, "retarget_axis"),
        "unique_accepted_retarget_axis_families": unique_count(accepted_balanced, "retarget_axis_family"),
        "max_accepted_seed_dominance": max_share(accepted_balanced, "seed"),
        "max_accepted_source_index_dominance": max_share(accepted_balanced, "source_index"),
        "max_accepted_fault_pair_dominance": max_share(accepted_balanced, "fault_family_pair"),
        "max_accepted_retarget_axis_dominance": max_share(accepted_balanced, "retarget_axis"),
        "normal_collision_rate_in_accepted": float(np.mean([1.0 if parse_bool(row.get("collision", False)) else 0.0 for row in accepted_balanced])) if accepted_balanced else 0.0,
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
        "axis_anchor_rows_csv": run_dir / "axis_anchor_rows.csv",
        "axis_plan_rows_csv": run_dir / "axis_plan_rows.csv",
        "axis_replay_rows_csv": run_dir / "axis_replay_rows.csv",
        "accepted_axis_balanced_rows_csv": run_dir / "accepted_axis_balanced_rows.csv",
        "rejected_axis_candidates_csv": run_dir / "rejected_axis_candidates.csv",
        "axis_balance_summary_csv": run_dir / "axis_balance_summary.csv",
        "source_balance_summary_csv": run_dir / "source_balance_summary.csv",
        "bracket_trace_rows_csv": run_dir / "bracket_trace_rows.csv",
        "progress_jsonl": progress_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 low-margin boundary-axis expansion.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--reference-replay-rows", type=Path, required=True)
    parser.add_argument("--m804-replay-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--primary-margin-threshold", type=float, default=5e-5)
    parser.add_argument("--collision-margin-floor", type=float, default=-1e-3)
    parser.add_argument("--safe-margin-ceiling", type=float, default=1e-2)
    parser.add_argument("--diagnostic-safe-margin-ceiling", type=float, default=2e-1)
    parser.add_argument("--target-margins", type=parse_float_list, default=DEFAULT_TARGET_MARGINS)
    parser.add_argument("--lateral-deltas", type=parse_float_list, default=DEFAULT_LATERAL_DELTAS)
    parser.add_argument("--step-offsets", type=parse_float_list, default=DEFAULT_STEP_OFFSETS)
    parser.add_argument("--fault-activation-deltas", type=parse_float_list, default=DEFAULT_FAULT_ACTIVATION_DELTAS)
    parser.add_argument("--fault-severity-deltas", type=parse_float_list, default=DEFAULT_FAULT_SEVERITY_DELTAS)
    parser.add_argument("--distance-bracket-deltas", type=parse_float_list, default=DEFAULT_DISTANCE_BRACKET_DELTAS)
    parser.add_argument("--half-width-bracket-deltas", type=parse_float_list, default=DEFAULT_HALF_WIDTH_BRACKET_DELTAS)
    parser.add_argument("--max-half-width-delta", type=float, default=1e-2)
    parser.add_argument("--max-anchors", type=int, default=None)
    parser.add_argument("--max-candidates-per-anchor", type=int, default=48)
    parser.add_argument("--max-bracket-rounds", type=int, default=2)
    parser.add_argument("--min-rows", type=int, default=80)
    parser.add_argument("--min-seeds", type=int, default=8)
    parser.add_argument("--min-source-indices", type=int, default=8)
    parser.add_argument("--min-fault-pairs", type=int, default=4)
    parser.add_argument("--min-retarget-axes", type=int, default=3)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-source-index-dominance", type=float, default=0.15)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.40)
    parser.add_argument("--max-axis-dominance", type=float, default=0.60)
    args = parser.parse_args()
    summary = run_boundary_axis_expansion(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        reference_replay_rows_path=args.reference_replay_rows,
        m804_replay_rows_path=args.m804_replay_rows,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        primary_margin_threshold=float(args.primary_margin_threshold),
        collision_margin_floor=float(args.collision_margin_floor),
        safe_margin_ceiling=float(args.safe_margin_ceiling),
        diagnostic_safe_margin_ceiling=float(args.diagnostic_safe_margin_ceiling),
        target_margins=tuple(args.target_margins),
        lateral_deltas=tuple(float(value) for value in args.lateral_deltas),
        step_offsets=tuple(int(value) for value in args.step_offsets),
        fault_activation_deltas=tuple(int(value) for value in args.fault_activation_deltas),
        fault_severity_deltas=tuple(float(value) for value in args.fault_severity_deltas),
        distance_bracket_deltas=tuple(float(value) for value in args.distance_bracket_deltas),
        half_width_bracket_deltas=tuple(float(value) for value in args.half_width_bracket_deltas),
        max_half_width_delta=float(args.max_half_width_delta),
        max_anchors=args.max_anchors,
        max_candidates_per_anchor=args.max_candidates_per_anchor,
        max_bracket_rounds=int(args.max_bracket_rounds),
        min_rows=int(args.min_rows),
        min_seeds=int(args.min_seeds),
        min_source_indices=int(args.min_source_indices),
        min_fault_pairs=int(args.min_fault_pairs),
        min_retarget_axes=int(args.min_retarget_axes),
        max_seed_dominance=float(args.max_seed_dominance),
        max_source_index_dominance=float(args.max_source_index_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
        max_axis_dominance=float(args.max_axis_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
