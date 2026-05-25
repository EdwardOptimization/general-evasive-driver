"""No-training closer obstacle/source generation from all-safe-wide traces."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_adaptive_boundary_bracketing import BOUNDARY_AXES, _replay_parameter
from autodrift.v4_boundary_new_to_m844_bracket_trace import (
    AXIS_SUMMARY_FIELDS,
    TRACE_FIELDS,
    recommended_next_for_cause,
)
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_wrong_history_pair_mining import BOUNDARY_REPLAY_FIELDS, margin_band, _source_meta_from_plan
from autodrift.v4_pair_delta_boundary_expansion import (
    BOUNDARY_EXTRA_FIELDS,
    build_pairability_projection_rows,
    _plan_by_source_group,
)
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    read_csv_rows,
    reconstruct_snapshots,
    _as_float,
    _as_int,
)


DEFAULT_SAFE_WIDE_DELTAS = (0.15, 0.30, 0.50, 0.75, 1.00)
DEFAULT_SAFE_WIDE_TIMING_DELTAS = (0.50, 1.00, 1.50, 2.00, 3.00)
DEFAULT_SAFE_WIDE_HALF_WIDTH_DELTAS = (0.05, 0.10, 0.16, 0.24, 0.32)
DEFAULT_COLLISION_SIDE_DELTAS = (0.10, 0.20, 0.35, 0.50, 0.75)
DEFAULT_COLLISION_TIMING_DELTAS = (0.25, 0.50, 1.00, 1.50, 2.00)
DEFAULT_COLLISION_HALF_WIDTH_DELTAS = (0.03, 0.06, 0.10, 0.16, 0.24)

GENERATION_PLAN_FIELDS = [
    "generation_id",
    "source_group_id",
    "seed",
    "step",
    "snapshot_uid",
    "source_index",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fault_severity",
    "preferred_fidelity_class",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fidelity_class",
    "fault_family_pair",
    "fault_onset_bucket",
    "source_axis",
    "source_target_class",
    "boundary_source_status",
    "trace_role",
    "trace_cause_class",
    "generation_family",
    "boundary_axis",
    "base_trace_parameter",
    "base_trace_margin",
    "source_parameter",
    "generated_parameter",
    "generation_delta",
    "generation_direction",
    "recommended_next",
]

GENERATED_REPLAY_FIELDS = [
    "generation_id",
    *BOUNDARY_REPLAY_FIELDS,
    *BOUNDARY_EXTRA_FIELDS,
    "trace_role",
    "trace_cause_class",
    "generation_family",
    "base_trace_parameter",
    "base_trace_margin",
    "source_parameter",
    "generated_parameter",
    "generation_delta",
    "generation_direction",
]

SUMMARY_FIELDS = [
    "category",
    "value",
    "rows",
    "accepted_rows",
    "acceptance_rate",
]


def _source_parameter(plan: dict[str, str], axis: str) -> float:
    if axis == "obstacle_timing":
        return _as_float(plan.get("source_obstacle_body_x"))
    if axis == "obstacle_lateral_offset":
        return _as_float(plan.get("source_obstacle_body_y"))
    if axis == "obstacle_half_width":
        return _as_float(plan.get("source_obstacle_half_width"))
    return float("nan")


def _clip_parameter(axis: str, value: float) -> float:
    if axis == "obstacle_timing":
        return max(1.0, float(value))
    if axis == "obstacle_half_width":
        return max(0.05, float(value))
    return float(value)


def _axis_deltas(axis: str, *, cause: str, safe_wide_deltas: tuple[float, ...], safe_wide_timing_deltas: tuple[float, ...], safe_wide_half_width_deltas: tuple[float, ...], collision_side_deltas: tuple[float, ...], collision_timing_deltas: tuple[float, ...], collision_half_width_deltas: tuple[float, ...]) -> tuple[float, ...]:
    if cause == "all_safe_wide":
        if axis == "obstacle_timing":
            return safe_wide_timing_deltas
        if axis == "obstacle_half_width":
            return safe_wide_half_width_deltas
        return safe_wide_deltas
    if axis == "obstacle_timing":
        return collision_timing_deltas
    if axis == "obstacle_half_width":
        return collision_half_width_deltas
    return collision_side_deltas


def _trace_rows_for_axis(trace_rows: list[dict[str, str]], source_group_id: int, step: int, axis: str) -> list[dict[str, str]]:
    return [
        row
        for row in trace_rows
        if _as_int(row.get("source_group_id")) == int(source_group_id)
        and _as_int(row.get("step")) == int(step)
        and row.get("boundary_axis") == axis
    ]


def _direction_toward_lower_margin(rows: list[dict[str, str]], base_row: dict[str, str]) -> float:
    ordered = sorted(
        [row for row in rows if np.isfinite(_finite_float(row.get("min_clearance_margin")))],
        key=lambda row: _finite_float(row.get("parameter_value")),
    )
    if not ordered:
        return 1.0
    base_value = _finite_float(base_row.get("parameter_value"))
    index = min(range(len(ordered)), key=lambda idx: abs(_finite_float(ordered[idx].get("parameter_value")) - base_value))
    if index <= 0:
        return -1.0
    if index >= len(ordered) - 1:
        return 1.0
    left_margin = _finite_float(ordered[index - 1].get("min_clearance_margin"), default=float("inf"))
    right_margin = _finite_float(ordered[index + 1].get("min_clearance_margin"), default=float("inf"))
    return -1.0 if left_margin < right_margin else 1.0


def _base_trace_row(rows: list[dict[str, str]], cause: str) -> dict[str, str] | None:
    if cause == "all_safe_wide":
        safe_rows = [
            row
            for row in rows
            if row.get("outcome_class") == "safe_wide"
            and np.isfinite(_finite_float(row.get("min_clearance_margin")))
        ]
        if not safe_rows:
            return None
        return min(safe_rows, key=lambda row: _finite_float(row.get("min_clearance_margin"), default=999.0))
    if cause == "all_collision_or_negative":
        negative_rows = [
            row
            for row in rows
            if row.get("outcome_class") == "negative"
            and np.isfinite(_finite_float(row.get("min_clearance_margin")))
        ]
        if not negative_rows:
            return None
        return max(negative_rows, key=lambda row: _finite_float(row.get("min_clearance_margin"), default=-999.0))
    return None


def build_generation_plan_rows(
    axis_summary_rows: list[dict[str, str]],
    trace_rows: list[dict[str, str]],
    target_trace_source_rows: list[dict[str, str]],
    candidate_plan_rows: list[dict[str, str]],
    *,
    max_source_axes: int,
    safe_wide_deltas: tuple[float, ...],
    safe_wide_timing_deltas: tuple[float, ...],
    safe_wide_half_width_deltas: tuple[float, ...],
    collision_side_deltas: tuple[float, ...],
    collision_timing_deltas: tuple[float, ...],
    collision_half_width_deltas: tuple[float, ...],
) -> list[dict[str, Any]]:
    """Build generated candidate plans from M857 primary source-axis traces."""

    target_by_key = {(_as_int(row.get("source_group_id")), _as_int(row.get("step"))): row for row in target_trace_source_rows}
    plan_by_group = _plan_by_source_group(candidate_plan_rows)
    selected_axes = [
        row
        for row in axis_summary_rows
        if row.get("trace_role") == "primary_boundary_new_to_m844"
        and row.get("cause_class") in {"all_safe_wide", "all_collision_or_negative"}
    ]
    selected_axes.sort(
        key=lambda row: (
            0 if row.get("cause_class") == "all_safe_wide" else 1,
            _finite_float(row.get("closest_margin_abs"), default=999.0),
            _as_int(row.get("source_group_id")),
            str(row.get("boundary_axis", "")),
        )
    )
    output: list[dict[str, Any]] = []
    seen: set[tuple[int, str, float, str]] = set()
    for axis_row in selected_axes[: int(max_source_axes)]:
        source_group_id = _as_int(axis_row.get("source_group_id"))
        step = _as_int(axis_row.get("step"))
        axis = str(axis_row.get("boundary_axis", ""))
        cause = str(axis_row.get("cause_class", ""))
        target = target_by_key.get((source_group_id, step), {})
        plan = plan_by_group.get(source_group_id, {})
        rows = _trace_rows_for_axis(trace_rows, source_group_id, step, axis)
        base = _base_trace_row(rows, cause)
        if base is None:
            continue
        source_parameter = _source_parameter(plan, axis)
        base_parameter = _finite_float(base.get("parameter_value"))
        if not np.isfinite(source_parameter) or not np.isfinite(base_parameter):
            continue
        if cause == "all_safe_wide":
            direction = _direction_toward_lower_margin(rows, base)
            generation_family = "all_safe_closer_obstacle"
        else:
            direction = np.sign(source_parameter - base_parameter)
            if direction == 0.0:
                direction = -_direction_toward_lower_margin(rows, base)
            generation_family = "all_collision_safer_side"
        deltas = _axis_deltas(
            axis,
            cause=cause,
            safe_wide_deltas=safe_wide_deltas,
            safe_wide_timing_deltas=safe_wide_timing_deltas,
            safe_wide_half_width_deltas=safe_wide_half_width_deltas,
            collision_side_deltas=collision_side_deltas,
            collision_timing_deltas=collision_timing_deltas,
            collision_half_width_deltas=collision_half_width_deltas,
        )
        for delta in deltas:
            generated_parameter = _clip_parameter(axis, base_parameter + float(direction) * float(delta))
            key = (source_group_id, axis, round(generated_parameter, 9), generation_family)
            if key in seen:
                continue
            seen.add(key)
            row = {
                "generation_id": len(output),
                "source_group_id": source_group_id,
                "seed": _as_int(axis_row.get("seed")),
                "step": step,
                "snapshot_uid": str(target.get("snapshot_uid", "")),
                "source_index": _as_int(target.get("source_index")),
                "warmup_mode": str(target.get("warmup_mode", axis_row.get("warmup_mode", ""))),
                "preferred_fault": str(target.get("preferred_fault", "")),
                "preferred_fault_family": str(axis_row.get("preferred_fault_family", target.get("preferred_fault_family", ""))),
                "preferred_fault_severity": str(target.get("preferred_fault_severity", "")),
                "preferred_fidelity_class": str(target.get("preferred_fidelity_class", "")),
                "wrong_fault": str(target.get("wrong_fault", "")),
                "wrong_fault_family": str(target.get("wrong_fault_family", "")),
                "wrong_fidelity_class": str(target.get("wrong_fidelity_class", "")),
                "fault_family_pair": str(target.get("fault_family_pair", "")),
                "fault_onset_bucket": str(target.get("fault_onset_bucket", "")),
                "source_axis": str(target.get("source_axis", "")),
                "source_target_class": str(target.get("source_target_class", "")),
                "boundary_source_status": str(target.get("boundary_source_status", "")),
                "trace_role": str(axis_row.get("trace_role", "")),
                "trace_cause_class": cause,
                "generation_family": generation_family,
                "boundary_axis": axis,
                "base_trace_parameter": base_parameter,
                "base_trace_margin": _finite_float(base.get("min_clearance_margin")),
                "source_parameter": source_parameter,
                "generated_parameter": generated_parameter,
                "generation_delta": float(delta),
                "generation_direction": float(direction),
                "recommended_next": recommended_next_for_cause(cause),
            }
            output.append(row)
    return output


def _is_accepted_generated_boundary(row: dict[str, Any], *, boundary_margin_threshold: float) -> bool:
    margin = _finite_float(row.get("min_clearance_margin"))
    return (
        row.get("trace_role") == "primary_boundary_new_to_m844"
        and parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and np.isfinite(margin)
        and 0.0 <= margin <= float(boundary_margin_threshold)
    )


def _summary_rows(rows: list[dict[str, Any]], accepted_rows: list[dict[str, Any]], key: str, *, category: str) -> list[dict[str, Any]]:
    values = sorted({str(row.get(key, "")) for row in rows})
    output: list[dict[str, Any]] = []
    for value in values:
        subset = [row for row in rows if str(row.get(key, "")) == value]
        accepted = [row for row in accepted_rows if str(row.get(key, "")) == value]
        output.append(
            {
                "category": category,
                "value": value,
                "rows": len(subset),
                "accepted_rows": len(accepted),
                "acceptance_rate": len(accepted) / float(len(subset)) if subset else 0.0,
            }
        )
    return output


def classify_closer_obstacle_generation_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    generation_plan_rows: int,
    primary_source_groups_planned: int,
    primary_seed_count_planned: int,
    primary_fault_family_count_planned: int,
    accepted_rows: list[dict[str, Any]],
    primary_accepted_rows: list[dict[str, Any]],
    pairability_rows: list[dict[str, Any]],
    min_plan_rows: int,
    min_planned_sources: int,
    min_planned_seeds: int,
    min_planned_fault_families: int,
    strong_min_rows: int,
    sparse_min_rows: int,
    strong_min_primary_rows: int,
    sparse_min_primary_rows: int,
    min_source_groups: int,
    sparse_min_source_groups: int,
    min_seeds: int,
    sparse_min_seeds: int,
    min_fault_families: int,
    sparse_min_fault_families: int,
    min_boundary_axes: int,
    max_source_group_dominance: float,
    max_seed_dominance: float,
    min_pairability_rows: int,
    sparse_min_pairability_rows: int,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_closer_obstacle_source_generation_contract_violation"
    if (
        int(generation_plan_rows) < int(min_plan_rows)
        or int(primary_source_groups_planned) < int(min_planned_sources)
        or int(primary_seed_count_planned) < int(min_planned_seeds)
        or int(primary_fault_family_count_planned) < int(min_planned_fault_families)
    ):
        return "v4_closer_obstacle_source_generation_plan_sparse"
    primary_pairability = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    if len(accepted_rows) < 16 or len(primary_accepted_rows) < 12:
        return "v4_closer_obstacle_source_generation_all_weak"
    strong = bool(
        len(accepted_rows) >= int(strong_min_rows)
        and len(primary_accepted_rows) >= int(strong_min_primary_rows)
        and unique_count(primary_accepted_rows, "source_group_id") >= int(min_source_groups)
        and unique_count(primary_accepted_rows, "seed") >= int(min_seeds)
        and unique_count(primary_accepted_rows, "preferred_fault_family") >= int(min_fault_families)
        and unique_count(primary_accepted_rows, "boundary_axis") >= int(min_boundary_axes)
        and max_share(primary_accepted_rows, "source_group_id") <= float(max_source_group_dominance)
        and max_share(primary_accepted_rows, "seed") <= float(max_seed_dominance)
        and len(primary_pairability) >= int(min_pairability_rows)
    )
    if strong:
        return "v4_closer_obstacle_source_generation_pass"
    sparse = bool(
        len(accepted_rows) >= int(sparse_min_rows)
        and len(primary_accepted_rows) >= int(sparse_min_primary_rows)
        and unique_count(primary_accepted_rows, "source_group_id") >= int(sparse_min_source_groups)
        and unique_count(primary_accepted_rows, "seed") >= int(sparse_min_seeds)
        and unique_count(primary_accepted_rows, "preferred_fault_family") >= int(sparse_min_fault_families)
        and len(primary_pairability) >= int(sparse_min_pairability_rows)
    )
    if sparse:
        return "v4_closer_obstacle_source_generation_sparse_useful"
    return "v4_closer_obstacle_source_generation_source_limited"


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
            "gate_name": "generation_plan_rows",
            "value": summary["generation_plan_rows"],
            "threshold": summary["min_generation_plan_rows"],
            "passed": int(summary["generation_plan_rows"]) >= int(summary["min_generation_plan_rows"]),
            "notes": "generated candidate plan coverage",
        },
        {
            "gate_name": "accepted_generated_boundary_rows",
            "value": summary["accepted_generated_boundary_rows"],
            "threshold": summary["strong_min_generated_boundary_rows"],
            "passed": int(summary["accepted_generated_boundary_rows"]) >= int(summary["strong_min_generated_boundary_rows"]),
            "notes": "strong generated boundary row count",
        },
        {
            "gate_name": "accepted_boundary_new_to_m844_rows",
            "value": summary["accepted_boundary_new_to_m844_rows"],
            "threshold": summary["strong_min_boundary_new_to_m844_rows"],
            "passed": int(summary["accepted_boundary_new_to_m844_rows"]) >= int(summary["strong_min_boundary_new_to_m844_rows"]),
            "notes": "primary new-source boundary rows",
        },
        {
            "gate_name": "pairability_projection_rows",
            "value": summary["pairability_projection_rows"],
            "threshold": summary["min_pairability_projection_rows"],
            "passed": int(summary["pairability_projection_rows"]) >= int(summary["min_pairability_projection_rows"]),
            "notes": "cheap projection only; no sequence replay",
        },
        {
            "gate_name": "pair_delta_sequence_replay_blocked",
            "value": not bool(summary["pair_delta_sequence_replay_used"]),
            "threshold": "true",
            "passed": not bool(summary["pair_delta_sequence_replay_used"]),
            "notes": "M860 may not run pair-delta sequence replay",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M860 cannot promote",
        },
    ]


def run_closer_obstacle_source_generation(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    m857_axis_summary_path: Path,
    m857_trace_rows_path: Path,
    m857_target_trace_source_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_source_axes: int,
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
    horizon: int,
    safe_wide_deltas: tuple[float, ...],
    safe_wide_timing_deltas: tuple[float, ...],
    safe_wide_half_width_deltas: tuple[float, ...],
    collision_side_deltas: tuple[float, ...],
    collision_timing_deltas: tuple[float, ...],
    collision_half_width_deltas: tuple[float, ...],
    boundary_margin_threshold: float,
    strict_margin_threshold: float,
    min_first_action_l2: float,
    max_pairability_obstacle_distance: float,
    diagnostic_pairability_obstacle_distance: float,
    min_generation_plan_rows: int,
    min_planned_source_groups: int,
    min_planned_seeds: int,
    min_planned_fault_families: int,
    strong_min_generated_boundary_rows: int,
    sparse_min_generated_boundary_rows: int,
    strong_min_boundary_new_to_m844_rows: int,
    sparse_min_boundary_new_to_m844_rows: int,
    min_source_groups: int,
    sparse_min_source_groups: int,
    min_seeds: int,
    sparse_min_seeds: int,
    min_fault_families: int,
    sparse_min_fault_families: int,
    min_boundary_axes: int,
    max_source_group_dominance: float,
    max_seed_dominance: float,
    min_pairability_projection_rows: int,
    sparse_min_pairability_projection_rows: int,
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
        raise ValueError("M860 closer obstacle generation requires an online recurrent checkpoint")
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
    response_dim = response_feature_dim_for_model(model)

    axis_summary_rows = read_csv_rows(m857_axis_summary_path)
    trace_rows = read_csv_rows(m857_trace_rows_path)
    target_trace_source_rows = read_csv_rows(m857_target_trace_source_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    generation_plan_rows = build_generation_plan_rows(
        axis_summary_rows,
        trace_rows,
        target_trace_source_rows,
        candidate_plan_rows,
        max_source_axes=int(max_source_axes),
        safe_wide_deltas=safe_wide_deltas,
        safe_wide_timing_deltas=safe_wide_timing_deltas,
        safe_wide_half_width_deltas=safe_wide_half_width_deltas,
        collision_side_deltas=collision_side_deltas,
        collision_timing_deltas=collision_timing_deltas,
        collision_half_width_deltas=collision_half_width_deltas,
    )
    request_rows = [
        {
            "left_source_group_id": _as_int(row.get("source_group_id")),
            "right_source_group_id": _as_int(row.get("source_group_id")),
            "left_step": _as_int(row.get("step")),
            "right_step": _as_int(row.get("step")),
        }
        for row in generation_plan_rows
    ]
    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=request_rows,
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
    plan_by_group = _plan_by_source_group(candidate_plan_rows)
    replay_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = [dict(row) for row in snapshot_rejections]
    for plan in generation_plan_rows:
        key = (_as_int(plan.get("source_group_id")), _as_int(plan.get("step")))
        snapshot = snapshots.get(key)
        source_plan = plan_by_group.get(key[0])
        if snapshot is None or source_plan is None:
            rejected_rows.append({"source_group_id": key[0], "step": key[1], "rejection_reason": "missing_snapshot_or_plan"})
            continue
        source_meta = _source_meta_from_plan(source_plan, source_index=_as_int(plan.get("source_index")), fault_by_name=fault_by_name, warmup_steps=int(warmup_steps))
        for extra in (*BOUNDARY_EXTRA_FIELDS, "trace_role", "trace_cause_class", "generation_family"):
            source_meta[extra] = plan.get(extra, "")
        result, _actions, _relocated = _replay_parameter(
            snapshot=snapshot,
            source_meta=source_meta,
            axis=str(plan["boundary_axis"]),
            parameter_value=_as_float(plan.get("generated_parameter")),
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            response_dim=response_dim,
            alpha=float(alpha),
            horizon=int(horizon),
            max_continuation_steps=int(max_continuation_steps),
            device=resolved_device,
        )
        margin = _finite_float(result.get("min_clearance_margin"))
        row = {
            "generation_id": _as_int(plan.get("generation_id")),
            **result,
            "horizon": int(horizon),
            "margin_band": margin_band(
                margin,
                strict_margin_threshold=float(strict_margin_threshold),
                boundary_margin_threshold=float(boundary_margin_threshold),
            ),
            "trace_role": plan.get("trace_role", ""),
            "trace_cause_class": plan.get("trace_cause_class", ""),
            "generation_family": plan.get("generation_family", ""),
            "base_trace_parameter": plan.get("base_trace_parameter", ""),
            "base_trace_margin": plan.get("base_trace_margin", ""),
            "source_parameter": plan.get("source_parameter", ""),
            "generated_parameter": plan.get("generated_parameter", ""),
            "generation_delta": plan.get("generation_delta", ""),
            "generation_direction": plan.get("generation_direction", ""),
        }
        replay_rows.append(row)
        _append_progress(
            progress_path,
            {
                "stage": "generated_replay",
                "generation_id": _as_int(plan.get("generation_id")),
                "source_group_id": key[0],
                "boundary_axis": plan.get("boundary_axis", ""),
                "margin": margin,
            },
        )

    accepted_rows = [
        row
        for row in replay_rows
        if parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and 0.0 <= _finite_float(row.get("min_clearance_margin")) <= float(boundary_margin_threshold)
    ]
    primary_accepted_rows = [
        row
        for row in accepted_rows
        if _is_accepted_generated_boundary(row, boundary_margin_threshold=float(boundary_margin_threshold))
    ]
    pairability_rows = build_pairability_projection_rows(
        primary_accepted_rows,
        min_first_action_l2=float(min_first_action_l2),
        max_obstacle_distance=float(max_pairability_obstacle_distance),
        diagnostic_max_obstacle_distance=float(diagnostic_pairability_obstacle_distance),
    )
    primary_pairability_rows = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    source_summary_rows = [
        *_summary_rows(replay_rows, primary_accepted_rows, "generation_family", category="generation_family"),
        *_summary_rows(replay_rows, primary_accepted_rows, "trace_cause_class", category="trace_cause_class"),
        *_summary_rows(replay_rows, primary_accepted_rows, "boundary_axis", category="boundary_axis"),
        *_summary_rows(replay_rows, primary_accepted_rows, "preferred_fault_family", category="preferred_fault_family"),
    ]
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_closer_obstacle_generation_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        generation_plan_rows=len(generation_plan_rows),
        primary_source_groups_planned=unique_count(generation_plan_rows, "source_group_id"),
        primary_seed_count_planned=unique_count(generation_plan_rows, "seed"),
        primary_fault_family_count_planned=unique_count(generation_plan_rows, "preferred_fault_family"),
        accepted_rows=accepted_rows,
        primary_accepted_rows=primary_accepted_rows,
        pairability_rows=pairability_rows,
        min_plan_rows=int(min_generation_plan_rows),
        min_planned_sources=int(min_planned_source_groups),
        min_planned_seeds=int(min_planned_seeds),
        min_planned_fault_families=int(min_planned_fault_families),
        strong_min_rows=int(strong_min_generated_boundary_rows),
        sparse_min_rows=int(sparse_min_generated_boundary_rows),
        strong_min_primary_rows=int(strong_min_boundary_new_to_m844_rows),
        sparse_min_primary_rows=int(sparse_min_boundary_new_to_m844_rows),
        min_source_groups=int(min_source_groups),
        sparse_min_source_groups=int(sparse_min_source_groups),
        min_seeds=int(min_seeds),
        sparse_min_seeds=int(sparse_min_seeds),
        min_fault_families=int(min_fault_families),
        sparse_min_fault_families=int(sparse_min_fault_families),
        min_boundary_axes=int(min_boundary_axes),
        max_source_group_dominance=float(max_source_group_dominance),
        max_seed_dominance=float(max_seed_dominance),
        min_pairability_rows=int(min_pairability_projection_rows),
        sparse_min_pairability_rows=int(sparse_min_pairability_projection_rows),
    )

    write_csv_rows(run_dir / "generation_plan_rows.csv", generation_plan_rows, fieldnames=GENERATION_PLAN_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "generated_replay_rows.csv", replay_rows, fieldnames=GENERATED_REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_generated_boundary_rows.csv", primary_accepted_rows, fieldnames=GENERATED_REPLAY_FIELDS)
    write_csv_rows(run_dir / "all_accepted_generated_rows.csv", accepted_rows, fieldnames=GENERATED_REPLAY_FIELDS)
    write_csv_rows(run_dir / "pairability_projection_rows.csv", pairability_rows)
    write_csv_rows(run_dir / "source_generation_summary.csv", source_summary_rows, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "v4_closer_obstacle_source_generation",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "m857_axis_summary": m857_axis_summary_path,
        "m857_trace_rows": m857_trace_rows_path,
        "m857_target_trace_source_rows": m857_target_trace_source_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "generation_plan_rows": len(generation_plan_rows),
        "primary_source_groups_planned": unique_count(generation_plan_rows, "source_group_id"),
        "primary_seed_count_planned": unique_count(generation_plan_rows, "seed"),
        "primary_fault_family_count_planned": unique_count(generation_plan_rows, "preferred_fault_family"),
        "generated_replay_rows": len(replay_rows),
        "accepted_generated_boundary_rows": len(primary_accepted_rows),
        "all_accepted_generated_rows": len(accepted_rows),
        "accepted_boundary_new_to_m844_rows": len(primary_accepted_rows),
        "unique_source_group_count": unique_count(primary_accepted_rows, "source_group_id"),
        "unique_seed_count": unique_count(primary_accepted_rows, "seed"),
        "unique_fault_family_count": unique_count(primary_accepted_rows, "preferred_fault_family"),
        "unique_boundary_axis_count": unique_count(primary_accepted_rows, "boundary_axis"),
        "max_source_group_dominance": max_share(primary_accepted_rows, "source_group_id"),
        "max_seed_dominance": max_share(primary_accepted_rows, "seed"),
        "pairability_projection_rows": len(primary_pairability_rows),
        "diagnostic_pairability_projection_rows": len(pairability_rows),
        "snapshot_rejection_rows": len(snapshot_rejections),
        "min_generation_plan_rows": int(min_generation_plan_rows),
        "min_planned_source_groups": int(min_planned_source_groups),
        "min_planned_seeds": int(min_planned_seeds),
        "min_planned_fault_families": int(min_planned_fault_families),
        "strong_min_generated_boundary_rows": int(strong_min_generated_boundary_rows),
        "sparse_min_generated_boundary_rows": int(sparse_min_generated_boundary_rows),
        "strong_min_boundary_new_to_m844_rows": int(strong_min_boundary_new_to_m844_rows),
        "sparse_min_boundary_new_to_m844_rows": int(sparse_min_boundary_new_to_m844_rows),
        "min_pairability_projection_rows": int(min_pairability_projection_rows),
        "sparse_min_pairability_projection_rows": int(sparse_min_pairability_projection_rows),
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "residual_head_checksum_before": residual_checksum_before,
        "residual_head_checksum_after": residual_checksum_after,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "pair_delta_sequence_replay_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": time.time() - start,
        "summary_json": run_dir / "summary.json",
        "generation_plan_rows_csv": run_dir / "generation_plan_rows.csv",
        "generated_replay_rows_csv": run_dir / "generated_replay_rows.csv",
        "accepted_generated_boundary_rows_csv": run_dir / "accepted_generated_boundary_rows.csv",
        "pairability_projection_rows_csv": run_dir / "pairability_projection_rows.csv",
        "source_generation_summary_csv": run_dir / "source_generation_summary.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 closer obstacle/source generation.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--m857-axis-summary", type=Path, required=True)
    parser.add_argument("--m857-trace-rows", type=Path, required=True)
    parser.add_argument("--m857-target-trace-source-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-source-axes", type=int, default=132)
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
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--safe-wide-deltas", type=parse_float_list, default=DEFAULT_SAFE_WIDE_DELTAS)
    parser.add_argument("--safe-wide-timing-deltas", type=parse_float_list, default=DEFAULT_SAFE_WIDE_TIMING_DELTAS)
    parser.add_argument("--safe-wide-half-width-deltas", type=parse_float_list, default=DEFAULT_SAFE_WIDE_HALF_WIDTH_DELTAS)
    parser.add_argument("--collision-side-deltas", type=parse_float_list, default=DEFAULT_COLLISION_SIDE_DELTAS)
    parser.add_argument("--collision-timing-deltas", type=parse_float_list, default=DEFAULT_COLLISION_TIMING_DELTAS)
    parser.add_argument("--collision-half-width-deltas", type=parse_float_list, default=DEFAULT_COLLISION_HALF_WIDTH_DELTAS)
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--strict-margin-threshold", type=float, default=0.02)
    parser.add_argument("--min-first-action-l2", type=float, default=0.014)
    parser.add_argument("--max-pairability-obstacle-distance", type=float, default=0.10)
    parser.add_argument("--diagnostic-pairability-obstacle-distance", type=float, default=0.20)
    parser.add_argument("--min-generation-plan-rows", type=int, default=300)
    parser.add_argument("--min-planned-source-groups", type=int, default=32)
    parser.add_argument("--min-planned-seeds", type=int, default=8)
    parser.add_argument("--min-planned-fault-families", type=int, default=6)
    parser.add_argument("--strong-min-generated-boundary-rows", type=int, default=80)
    parser.add_argument("--sparse-min-generated-boundary-rows", type=int, default=32)
    parser.add_argument("--strong-min-boundary-new-to-m844-rows", type=int, default=60)
    parser.add_argument("--sparse-min-boundary-new-to-m844-rows", type=int, default=24)
    parser.add_argument("--min-source-groups", type=int, default=24)
    parser.add_argument("--sparse-min-source-groups", type=int, default=10)
    parser.add_argument("--min-seeds", type=int, default=8)
    parser.add_argument("--sparse-min-seeds", type=int, default=5)
    parser.add_argument("--min-fault-families", type=int, default=6)
    parser.add_argument("--sparse-min-fault-families", type=int, default=4)
    parser.add_argument("--min-boundary-axes", type=int, default=3)
    parser.add_argument("--max-source-group-dominance", type=float, default=0.10)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--min-pairability-projection-rows", type=int, default=120)
    parser.add_argument("--sparse-min-pairability-projection-rows", type=int, default=40)
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
    summary = run_closer_obstacle_source_generation(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        m857_axis_summary_path=args.m857_axis_summary,
        m857_trace_rows_path=args.m857_trace_rows,
        m857_target_trace_source_rows_path=args.m857_target_trace_source_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_source_axes=int(args.max_source_axes),
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
        horizon=int(args.horizon),
        safe_wide_deltas=tuple(args.safe_wide_deltas),
        safe_wide_timing_deltas=tuple(args.safe_wide_timing_deltas),
        safe_wide_half_width_deltas=tuple(args.safe_wide_half_width_deltas),
        collision_side_deltas=tuple(args.collision_side_deltas),
        collision_timing_deltas=tuple(args.collision_timing_deltas),
        collision_half_width_deltas=tuple(args.collision_half_width_deltas),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        strict_margin_threshold=float(args.strict_margin_threshold),
        min_first_action_l2=float(args.min_first_action_l2),
        max_pairability_obstacle_distance=float(args.max_pairability_obstacle_distance),
        diagnostic_pairability_obstacle_distance=float(args.diagnostic_pairability_obstacle_distance),
        min_generation_plan_rows=int(args.min_generation_plan_rows),
        min_planned_source_groups=int(args.min_planned_source_groups),
        min_planned_seeds=int(args.min_planned_seeds),
        min_planned_fault_families=int(args.min_planned_fault_families),
        strong_min_generated_boundary_rows=int(args.strong_min_generated_boundary_rows),
        sparse_min_generated_boundary_rows=int(args.sparse_min_generated_boundary_rows),
        strong_min_boundary_new_to_m844_rows=int(args.strong_min_boundary_new_to_m844_rows),
        sparse_min_boundary_new_to_m844_rows=int(args.sparse_min_boundary_new_to_m844_rows),
        min_source_groups=int(args.min_source_groups),
        sparse_min_source_groups=int(args.sparse_min_source_groups),
        min_seeds=int(args.min_seeds),
        sparse_min_seeds=int(args.sparse_min_seeds),
        min_fault_families=int(args.min_fault_families),
        sparse_min_fault_families=int(args.sparse_min_fault_families),
        min_boundary_axes=int(args.min_boundary_axes),
        max_source_group_dominance=float(args.max_source_group_dominance),
        max_seed_dominance=float(args.max_seed_dominance),
        min_pairability_projection_rows=int(args.min_pairability_projection_rows),
        sparse_min_pairability_projection_rows=int(args.sparse_min_pairability_projection_rows),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
