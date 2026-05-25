"""Trace no-bracket causes for M854 boundary-new-to-M844 sources."""

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
from autodrift.v4_adaptive_boundary_bracketing import (
    BOUNDARY_AXES,
    axis_initial_values,
    find_adjacent_margin_bracket,
    _replay_parameter,
)
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_wrong_history_pair_mining import _source_meta_from_plan
from autodrift.v4_pair_delta_boundary_expansion import _plan_by_source_group
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    read_csv_rows,
    reconstruct_snapshots,
    _as_float,
    _as_int,
)


DEFAULT_INITIAL_TIMING_DELTAS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)
DEFAULT_INITIAL_LATERAL_DELTAS = (-0.45, -0.25, -0.12, 0.0, 0.12, 0.25, 0.45)
DEFAULT_INITIAL_HALF_WIDTH_DELTAS = (-0.08, -0.04, 0.0, 0.04, 0.08, 0.14)
DEFAULT_EXTENDED_TIMING_DELTAS = (-4.0, -3.0, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
DEFAULT_EXTENDED_LATERAL_DELTAS = (-1.4, -1.0, -0.7, -0.45, -0.25, -0.12, 0.0, 0.12, 0.25, 0.45, 0.7, 1.0, 1.4)
DEFAULT_EXTENDED_HALF_WIDTH_DELTAS = (-0.20, -0.14, -0.08, -0.04, 0.0, 0.04, 0.08, 0.14, 0.20, 0.28, 0.36)

TRACE_SOURCE_FIELDS = [
    "trace_source_rank",
    "source_group_id",
    "step",
    "snapshot_uid",
    "source_index",
    "seed",
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
    "source_obstacle_body_x",
    "source_obstacle_body_y",
    "source_obstacle_half_width",
    "source_target_class",
    "boundary_source_status",
    "trace_role",
]

TRACE_FIELDS = [
    "trace_id",
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
    "boundary_axis",
    "grid_family",
    "parameter_value",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "reconstructed",
    "rejection_reason",
    "success",
    "collision",
    "terminal_reason",
    "min_clearance_margin",
    "outcome_class",
    "first_steer",
    "first_throttle",
    "first_brake",
]

AXIS_SUMMARY_FIELDS = [
    "source_group_id",
    "seed",
    "step",
    "preferred_fault_family",
    "warmup_mode",
    "source_target_class",
    "boundary_source_status",
    "trace_role",
    "boundary_axis",
    "trace_rows",
    "initial_rows",
    "extended_rows",
    "reconstructed_rows",
    "safe_boundary_rows",
    "safe_wide_rows",
    "negative_rows",
    "ambiguous_rows",
    "has_negative",
    "has_safe_boundary",
    "has_safe_wide",
    "has_ambiguous",
    "min_margin",
    "max_margin",
    "closest_margin_abs",
    "margin_sign_changes",
    "cause_class",
    "recommended_next",
]

SOURCE_SUMMARY_FIELDS = [
    "source_group_id",
    "seed",
    "preferred_fault_family",
    "warmup_mode",
    "source_target_class",
    "boundary_source_status",
    "trace_role",
    "source_axis_rows",
    "dominant_cause",
    "accepted_boundary_found_extended_axes",
    "all_safe_wide_axes",
    "all_collision_or_negative_axes",
    "ambiguous_or_nonfinite_axes",
]

EXPANSION_PLAN_FIELDS = [
    "source_group_id",
    "seed",
    "step",
    "preferred_fault_family",
    "boundary_axis",
    "cause_class",
    "recommended_next",
    "best_parameter_value",
    "best_margin",
    "trace_rows",
]

REJECTED_FIELDS = [
    "source_group_id",
    "step",
    "boundary_axis",
    "rejection_reason",
]


def outcome_class(row: dict[str, Any], *, boundary_margin_threshold: float) -> str:
    """Classify one replay outcome for trace diagnostics."""

    if not parse_bool(row.get("reconstructed", False)):
        return "ambiguous"
    margin = _finite_float(row.get("min_clearance_margin"))
    if not np.isfinite(margin):
        return "ambiguous"
    if parse_bool(row.get("collision", False)) or margin < 0.0:
        return "negative"
    if parse_bool(row.get("success", False)) and 0.0 <= margin <= float(boundary_margin_threshold):
        return "safe_boundary"
    if parse_bool(row.get("success", False)) and margin > float(boundary_margin_threshold):
        return "safe_wide"
    return "ambiguous"


def _sign_changes(rows: list[dict[str, Any]]) -> int:
    ordered = sorted(
        [row for row in rows if np.isfinite(_finite_float(row.get("min_clearance_margin")))],
        key=lambda row: _finite_float(row.get("parameter_value")),
    )
    signs: list[int] = []
    for row in ordered:
        cls = str(row.get("outcome_class", ""))
        if cls == "negative":
            signs.append(-1)
        elif cls in {"safe_boundary", "safe_wide"}:
            signs.append(1)
    return sum(1 for left, right in zip(signs, signs[1:]) if left != right)


def classify_axis_trace(rows: list[dict[str, Any]]) -> str:
    """Classify the primary no-bracket cause for one source-axis trace."""

    if not rows:
        return "insufficient_trace"
    reconstructed = [row for row in rows if parse_bool(row.get("reconstructed", False))]
    if not reconstructed:
        return "reconstruction_error"
    initial = [row for row in reconstructed if row.get("grid_family") == "initial"]
    classes = [str(row.get("outcome_class", "")) for row in reconstructed]
    initial_classes = [str(row.get("outcome_class", "")) for row in initial]
    if "safe_boundary" in initial_classes:
        return "accepted_boundary_found_initial"
    if "safe_boundary" in classes:
        return "accepted_boundary_found_extended"
    if find_adjacent_margin_bracket(initial) is not None:
        return "bracket_found_initial"
    if find_adjacent_margin_bracket(reconstructed) is not None:
        return "bracket_found_extended"
    if classes and all(value == "safe_wide" for value in classes):
        return "all_safe_wide"
    if classes and all(value == "negative" for value in classes):
        return "all_collision_or_negative"
    if "ambiguous" in classes:
        return "ambiguous_or_nonfinite"
    if "negative" in classes and any(value in {"safe_wide", "safe_boundary"} for value in classes):
        return "mixed_no_adjacent_bracket"
    return "insufficient_trace"


def recommended_next_for_cause(cause: str) -> str:
    if cause in {"accepted_boundary_found_extended", "bracket_found_extended"}:
        return "bounded_boundary_expansion"
    if cause in {"accepted_boundary_found_initial", "bracket_found_initial"}:
        return "recover_initial_boundary"
    if cause == "all_safe_wide":
        return "closer_obstacle_or_source_generation"
    if cause == "all_collision_or_negative":
        return "safer_side_bracketing_or_source_step_shift"
    if cause in {"ambiguous_or_nonfinite", "reconstruction_error"}:
        return "trace_quality_audit"
    return "manual_audit"


def _counts(rows: list[dict[str, Any]], cls: str) -> int:
    return sum(1 for row in rows if row.get("outcome_class") == cls)


def summarize_axis_trace(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0] if rows else {}
    margins = [_finite_float(row.get("min_clearance_margin")) for row in rows]
    finite_margins = [value for value in margins if np.isfinite(value)]
    cause = classify_axis_trace(rows)
    return {
        "source_group_id": _as_int(first.get("source_group_id")),
        "seed": _as_int(first.get("seed")),
        "step": _as_int(first.get("step")),
        "preferred_fault_family": str(first.get("preferred_fault_family", "")),
        "warmup_mode": str(first.get("warmup_mode", "")),
        "source_target_class": str(first.get("source_target_class", "")),
        "boundary_source_status": str(first.get("boundary_source_status", "")),
        "trace_role": str(first.get("trace_role", "")),
        "boundary_axis": str(first.get("boundary_axis", "")),
        "trace_rows": len(rows),
        "initial_rows": sum(1 for row in rows if row.get("grid_family") == "initial"),
        "extended_rows": sum(1 for row in rows if row.get("grid_family") == "extended"),
        "reconstructed_rows": sum(1 for row in rows if parse_bool(row.get("reconstructed", False))),
        "safe_boundary_rows": _counts(rows, "safe_boundary"),
        "safe_wide_rows": _counts(rows, "safe_wide"),
        "negative_rows": _counts(rows, "negative"),
        "ambiguous_rows": _counts(rows, "ambiguous"),
        "has_negative": _counts(rows, "negative") > 0,
        "has_safe_boundary": _counts(rows, "safe_boundary") > 0,
        "has_safe_wide": _counts(rows, "safe_wide") > 0,
        "has_ambiguous": _counts(rows, "ambiguous") > 0,
        "min_margin": min(finite_margins) if finite_margins else float("nan"),
        "max_margin": max(finite_margins) if finite_margins else float("nan"),
        "closest_margin_abs": min((abs(value) for value in finite_margins), default=float("nan")),
        "margin_sign_changes": _sign_changes(rows),
        "cause_class": cause,
        "recommended_next": recommended_next_for_cause(cause),
    }


def select_trace_source_rows(
    target_rows: list[dict[str, str]],
    accepted_boundary_rows: list[dict[str, str]],
    *,
    max_primary_sources: int,
    control_existing_boundary_sources: int,
) -> list[dict[str, Any]]:
    """Select boundary-new-to-M844 trace rows with a small recovered control set."""

    accepted_groups = {str(_as_int(row.get("source_group_id"))) for row in accepted_boundary_rows}
    primary = [
        row
        for row in target_rows
        if row.get("boundary_source_status") == "boundary_new_to_m844"
        and row.get("source_target_class") == "new_underrepresented_boundary"
        and str(_as_int(row.get("source_group_id"))) not in accepted_groups
    ]
    controls = [
        row
        for row in target_rows
        if row.get("boundary_source_status") == "existing_boundary_recovered"
        and str(_as_int(row.get("source_group_id"))) in accepted_groups
    ]
    ordered_primary = sorted(
        primary,
        key=lambda row: (
            _as_int(row.get("seed")),
            str(row.get("preferred_fault_family", "")),
            _as_int(row.get("source_group_id")),
        ),
    )[: int(max_primary_sources)]
    ordered_controls = sorted(
        controls,
        key=lambda row: (
            _as_int(row.get("seed")),
            str(row.get("preferred_fault_family", "")),
            _as_int(row.get("source_group_id")),
        ),
    )[: int(control_existing_boundary_sources)]
    output: list[dict[str, Any]] = []
    for index, row in enumerate([*ordered_primary, *ordered_controls]):
        trace_role = "primary_boundary_new_to_m844" if row.get("boundary_source_status") == "boundary_new_to_m844" else "control_existing_boundary_recovered"
        output.append({**row, "trace_source_rank": index, "trace_role": trace_role})
    return output


def _grid_values(
    *,
    axis: str,
    body_x: float,
    body_y: float,
    half_width: float,
    initial_timing_deltas: tuple[float, ...],
    initial_lateral_deltas: tuple[float, ...],
    initial_half_width_deltas: tuple[float, ...],
    extended_timing_deltas: tuple[float, ...],
    extended_lateral_deltas: tuple[float, ...],
    extended_half_width_deltas: tuple[float, ...],
) -> list[tuple[str, float]]:
    initial = axis_initial_values(
        axis,
        body_x=body_x,
        body_y=body_y,
        half_width=half_width,
        timing_deltas=initial_timing_deltas,
        lateral_deltas=initial_lateral_deltas,
        half_width_deltas=initial_half_width_deltas,
    )
    extended = axis_initial_values(
        axis,
        body_x=body_x,
        body_y=body_y,
        half_width=half_width,
        timing_deltas=extended_timing_deltas,
        lateral_deltas=extended_lateral_deltas,
        half_width_deltas=extended_half_width_deltas,
    )
    output: list[tuple[str, float]] = []
    seen: set[float] = set()
    for value in initial:
        key = round(float(value), 9)
        if key not in seen:
            seen.add(key)
            output.append(("initial", float(value)))
    for value in extended:
        key = round(float(value), 9)
        if key not in seen:
            seen.add(key)
            output.append(("extended", float(value)))
    return output


def _source_summary(axis_rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = axis_rows[0] if axis_rows else {}
    cause_counts: dict[str, int] = {}
    for row in axis_rows:
        cause = str(row.get("cause_class", ""))
        cause_counts[cause] = cause_counts.get(cause, 0) + 1
    dominant = max(cause_counts.items(), key=lambda item: (item[1], item[0]))[0] if cause_counts else ""
    return {
        "source_group_id": _as_int(first.get("source_group_id")),
        "seed": _as_int(first.get("seed")),
        "preferred_fault_family": str(first.get("preferred_fault_family", "")),
        "warmup_mode": str(first.get("warmup_mode", "")),
        "source_target_class": str(first.get("source_target_class", "")),
        "boundary_source_status": str(first.get("boundary_source_status", "")),
        "trace_role": str(first.get("trace_role", "")),
        "source_axis_rows": len(axis_rows),
        "dominant_cause": dominant,
        "accepted_boundary_found_extended_axes": cause_counts.get("accepted_boundary_found_extended", 0),
        "all_safe_wide_axes": cause_counts.get("all_safe_wide", 0),
        "all_collision_or_negative_axes": cause_counts.get("all_collision_or_negative", 0),
        "ambiguous_or_nonfinite_axes": cause_counts.get("ambiguous_or_nonfinite", 0),
    }


def _cause_share(axis_rows: list[dict[str, Any]], cause: str) -> float:
    primary = [row for row in axis_rows if row.get("trace_role") == "primary_boundary_new_to_m844"]
    if not primary:
        return 0.0
    return sum(1 for row in primary if row.get("cause_class") == cause) / float(len(primary))


def classify_bracket_trace_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    target_sources: int,
    traced_source_axis_rows: int,
    trace_rows: int,
    cause_classified_share: float,
    axis_summary_rows: list[dict[str, Any]],
    min_target_sources: int,
    min_source_axis_rows: int,
    min_trace_rows: int,
    min_cause_classified_share: float,
    min_extended_accept_axes: int,
    min_extended_accept_source_groups: int,
    min_extended_accept_fault_families: int,
    all_safe_share_threshold: float,
    all_collision_share_threshold: float,
    ambiguous_share_threshold: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_boundary_new_to_m844_bracket_trace_contract_violation"
    if (
        int(target_sources) < int(min_target_sources)
        or int(traced_source_axis_rows) < int(min_source_axis_rows)
        or int(trace_rows) < int(min_trace_rows)
        or float(cause_classified_share) < float(min_cause_classified_share)
    ):
        return "v4_boundary_new_to_m844_bracket_trace_incomplete"
    primary_extended_accepts = [
        row
        for row in axis_summary_rows
        if row.get("trace_role") == "primary_boundary_new_to_m844"
        and row.get("cause_class") == "accepted_boundary_found_extended"
    ]
    if (
        len(primary_extended_accepts) >= int(min_extended_accept_axes)
        and unique_count(primary_extended_accepts, "source_group_id") >= int(min_extended_accept_source_groups)
        and unique_count(primary_extended_accepts, "preferred_fault_family") >= int(min_extended_accept_fault_families)
    ):
        return "v4_boundary_new_to_m844_bracket_trace_actionable_extended_boundary"
    if _cause_share(axis_summary_rows, "all_safe_wide") >= float(all_safe_share_threshold):
        return "v4_boundary_new_to_m844_bracket_trace_all_safe_wide"
    if _cause_share(axis_summary_rows, "all_collision_or_negative") >= float(all_collision_share_threshold):
        return "v4_boundary_new_to_m844_bracket_trace_all_collision_or_negative"
    if _cause_share(axis_summary_rows, "ambiguous_or_nonfinite") >= float(ambiguous_share_threshold):
        return "v4_boundary_new_to_m844_bracket_trace_ambiguous"
    return "v4_boundary_new_to_m844_bracket_trace_mixed_diagnostic"


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
            "gate_name": "target_boundary_new_to_m844_sources",
            "value": summary["target_boundary_new_to_m844_sources"],
            "threshold": summary["min_target_boundary_new_to_m844_sources"],
            "passed": int(summary["target_boundary_new_to_m844_sources"]) >= int(summary["min_target_boundary_new_to_m844_sources"]),
            "notes": "primary target coverage",
        },
        {
            "gate_name": "traced_source_axis_rows",
            "value": summary["traced_source_axis_rows"],
            "threshold": summary["min_traced_source_axis_rows"],
            "passed": int(summary["traced_source_axis_rows"]) >= int(summary["min_traced_source_axis_rows"]),
            "notes": "source-axis traces before route decision",
        },
        {
            "gate_name": "bracket_trace_rows",
            "value": summary["bracket_trace_rows"],
            "threshold": summary["min_bracket_trace_rows"],
            "passed": int(summary["bracket_trace_rows"]) >= int(summary["min_bracket_trace_rows"]),
            "notes": "all evaluated parameters must be retained",
        },
        {
            "gate_name": "cause_classified_source_axis_share",
            "value": summary["cause_classified_source_axis_share"],
            "threshold": summary["min_cause_classified_source_axis_share"],
            "passed": float(summary["cause_classified_source_axis_share"]) >= float(summary["min_cause_classified_source_axis_share"]),
            "notes": "trace rows should support source-axis cause classification",
        },
        {
            "gate_name": "pair_delta_sequence_replay_blocked",
            "value": not bool(summary["pair_delta_sequence_replay_used"]),
            "threshold": "true",
            "passed": not bool(summary["pair_delta_sequence_replay_used"]),
            "notes": "M857 may not run pair-delta sequence replay",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M857 cannot promote",
        },
    ]


def run_boundary_new_to_m844_bracket_trace(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    m854_target_source_rows_path: Path,
    m854_rejected_rows_path: Path,
    m854_accepted_boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_primary_sources: int,
    control_existing_boundary_sources: int,
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
    boundary_axes: tuple[str, ...],
    initial_timing_deltas: tuple[float, ...],
    initial_lateral_deltas: tuple[float, ...],
    initial_half_width_deltas: tuple[float, ...],
    extended_timing_deltas: tuple[float, ...],
    extended_lateral_deltas: tuple[float, ...],
    extended_half_width_deltas: tuple[float, ...],
    boundary_margin_threshold: float,
    min_target_boundary_new_to_m844_sources: int,
    min_traced_source_axis_rows: int,
    min_bracket_trace_rows: int,
    min_cause_classified_source_axis_share: float,
    min_extended_accept_axes: int,
    min_extended_accept_source_groups: int,
    min_extended_accept_fault_families: int,
    all_safe_share_threshold: float,
    all_collision_share_threshold: float,
    ambiguous_share_threshold: float,
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
        raise ValueError("M857 bracket trace requires an online recurrent checkpoint")
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

    source_rows = read_csv_rows(source_rows_path)
    plan_rows = read_csv_rows(candidate_plan_rows_path)
    target_rows_raw = read_csv_rows(m854_target_source_rows_path)
    rejected_rows_raw = read_csv_rows(m854_rejected_rows_path)
    accepted_boundary_rows = read_csv_rows(m854_accepted_boundary_rows_path)
    target_rows = select_trace_source_rows(
        target_rows_raw,
        accepted_boundary_rows,
        max_primary_sources=int(max_primary_sources),
        control_existing_boundary_sources=int(control_existing_boundary_sources),
    )
    plan_by_group = _plan_by_source_group(plan_rows)
    rejected_axes_by_key: dict[tuple[int, int], set[str]] = {}
    for row in rejected_rows_raw:
        if row.get("boundary_source_status") != "boundary_new_to_m844":
            continue
        key = (_as_int(row.get("source_group_id")), _as_int(row.get("step")))
        rejected_axes_by_key.setdefault(key, set()).add(str(row.get("boundary_axis", "")))

    request_rows = [
        {
            "left_source_group_id": _as_int(row.get("source_group_id")),
            "right_source_group_id": _as_int(row.get("source_group_id")),
            "left_step": _as_int(row.get("step")),
            "right_step": _as_int(row.get("step")),
        }
        for row in target_rows
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

    trace_rows: list[dict[str, Any]] = []
    axis_summary_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = [
        {
            "source_group_id": row.get("source_group_id", ""),
            "step": row.get("step", ""),
            "boundary_axis": "",
            "rejection_reason": row.get("rejection_reason", ""),
        }
        for row in snapshot_rejections
    ]
    trace_id = 0
    target_by_key = {(_as_int(row.get("source_group_id")), _as_int(row.get("step"))): row for row in target_rows}
    for key, target in sorted(target_by_key.items()):
        snapshot = snapshots.get(key)
        plan = plan_by_group.get(key[0])
        if snapshot is None or plan is None:
            rejected_rows.append({"source_group_id": key[0], "step": key[1], "boundary_axis": "", "rejection_reason": "missing_snapshot_or_plan"})
            continue
        source_meta = _source_meta_from_plan(plan, source_index=_as_int(target.get("source_index")), fault_by_name=fault_by_name, warmup_steps=int(warmup_steps))
        for extra in ("source_target_class", "boundary_source_status", "trace_role"):
            source_meta[extra] = target.get(extra, "")
        axes = tuple(boundary_axes)
        if target.get("trace_role") == "primary_boundary_new_to_m844":
            rejected_axes = rejected_axes_by_key.get(key)
            if rejected_axes:
                axes = tuple(axis for axis in axes if axis in rejected_axes)
        for axis in axes:
            source_axis_rows: list[dict[str, Any]] = []
            for grid_family, parameter_value in _grid_values(
                axis=axis,
                body_x=_as_float(plan.get("source_obstacle_body_x")),
                body_y=_as_float(plan.get("source_obstacle_body_y")),
                half_width=_as_float(plan.get("source_obstacle_half_width")),
                initial_timing_deltas=initial_timing_deltas,
                initial_lateral_deltas=initial_lateral_deltas,
                initial_half_width_deltas=initial_half_width_deltas,
                extended_timing_deltas=extended_timing_deltas,
                extended_lateral_deltas=extended_lateral_deltas,
                extended_half_width_deltas=extended_half_width_deltas,
            ):
                result, _actions, _relocated = _replay_parameter(
                    snapshot=snapshot,
                    source_meta=source_meta,
                    axis=axis,
                    parameter_value=float(parameter_value),
                    model=model,
                    residual_head=residual_head,
                    env_config=env_config,
                    response_dim=response_dim,
                    alpha=float(alpha),
                    horizon=int(horizon),
                    max_continuation_steps=int(max_continuation_steps),
                    device=resolved_device,
                )
                row = {
                    "trace_id": trace_id,
                    **result,
                    "grid_family": grid_family,
                }
                row["outcome_class"] = outcome_class(row, boundary_margin_threshold=float(boundary_margin_threshold))
                trace_rows.append(row)
                source_axis_rows.append(row)
                trace_id += 1
            axis_summary = summarize_axis_trace(source_axis_rows)
            axis_summary_rows.append(axis_summary)
            _append_progress(
                progress_path,
                {
                    "stage": "trace_axis",
                    "source_group_id": int(key[0]),
                    "step": int(key[1]),
                    "boundary_axis": axis,
                    "cause_class": axis_summary["cause_class"],
                    "trace_rows": len(source_axis_rows),
                },
            )

    source_groups: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in axis_summary_rows:
        source_groups.setdefault((_as_int(row.get("source_group_id")), _as_int(row.get("step"))), []).append(row)
    source_summary_rows = [_source_summary(rows) for _key, rows in sorted(source_groups.items())]
    expansion_plan_rows = []
    for row in axis_summary_rows:
        if row.get("recommended_next") not in {"bounded_boundary_expansion", "recover_initial_boundary"}:
            continue
        matching = [
            trace
            for trace in trace_rows
            if _as_int(trace.get("source_group_id")) == _as_int(row.get("source_group_id"))
            and _as_int(trace.get("step")) == _as_int(row.get("step"))
            and trace.get("boundary_axis") == row.get("boundary_axis")
            and trace.get("outcome_class") in {"safe_boundary", "safe_wide"}
        ]
        matching.sort(key=lambda item: abs(_finite_float(item.get("min_clearance_margin"), default=999.0)))
        best = matching[0] if matching else {}
        expansion_plan_rows.append(
            {
                "source_group_id": row.get("source_group_id", ""),
                "seed": row.get("seed", ""),
                "step": row.get("step", ""),
                "preferred_fault_family": row.get("preferred_fault_family", ""),
                "boundary_axis": row.get("boundary_axis", ""),
                "cause_class": row.get("cause_class", ""),
                "recommended_next": row.get("recommended_next", ""),
                "best_parameter_value": best.get("parameter_value", ""),
                "best_margin": best.get("min_clearance_margin", ""),
                "trace_rows": row.get("trace_rows", ""),
            }
        )

    primary_axis_rows = [row for row in axis_summary_rows if row.get("trace_role") == "primary_boundary_new_to_m844"]
    classified_causes = {
        "bracket_found_initial",
        "bracket_found_extended",
        "accepted_boundary_found_initial",
        "accepted_boundary_found_extended",
        "all_safe_wide",
        "all_collision_or_negative",
        "mixed_no_adjacent_bracket",
        "ambiguous_or_nonfinite",
        "reconstruction_error",
    }
    cause_classified_share = (
        sum(1 for row in primary_axis_rows if row.get("cause_class") in classified_causes) / float(len(primary_axis_rows))
        if primary_axis_rows
        else 0.0
    )
    cause_counts = {cause: sum(1 for row in primary_axis_rows if row.get("cause_class") == cause) for cause in sorted(classified_causes | {"insufficient_trace"})}
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_bracket_trace_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        target_sources=unique_count([row for row in target_rows if row.get("trace_role") == "primary_boundary_new_to_m844"], "source_group_id"),
        traced_source_axis_rows=len(primary_axis_rows),
        trace_rows=len(trace_rows),
        cause_classified_share=float(cause_classified_share),
        axis_summary_rows=axis_summary_rows,
        min_target_sources=int(min_target_boundary_new_to_m844_sources),
        min_source_axis_rows=int(min_traced_source_axis_rows),
        min_trace_rows=int(min_bracket_trace_rows),
        min_cause_classified_share=float(min_cause_classified_source_axis_share),
        min_extended_accept_axes=int(min_extended_accept_axes),
        min_extended_accept_source_groups=int(min_extended_accept_source_groups),
        min_extended_accept_fault_families=int(min_extended_accept_fault_families),
        all_safe_share_threshold=float(all_safe_share_threshold),
        all_collision_share_threshold=float(all_collision_share_threshold),
        ambiguous_share_threshold=float(ambiguous_share_threshold),
    )
    cause_summary = {
        "primary_cause_counts": cause_counts,
        "primary_cause_shares": {
            cause: (count / float(len(primary_axis_rows)) if primary_axis_rows else 0.0)
            for cause, count in cause_counts.items()
        },
        "source_summary_counts": {
            "target_trace_sources": len(target_rows),
            "primary_trace_sources": sum(1 for row in target_rows if row.get("trace_role") == "primary_boundary_new_to_m844"),
            "control_trace_sources": sum(1 for row in target_rows if row.get("trace_role") == "control_existing_boundary_recovered"),
            "primary_axis_rows": len(primary_axis_rows),
            "all_axis_rows": len(axis_summary_rows),
        },
    }

    write_csv_rows(run_dir / "target_trace_source_rows.csv", [{key: row.get(key, "") for key in TRACE_SOURCE_FIELDS} for row in target_rows], fieldnames=TRACE_SOURCE_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "bracket_trace_rows.csv", trace_rows, fieldnames=TRACE_FIELDS)
    write_csv_rows(run_dir / "axis_trace_summary.csv", axis_summary_rows, fieldnames=AXIS_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "source_trace_summary.csv", source_summary_rows, fieldnames=SOURCE_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "candidate_expansion_plan_rows.csv", expansion_plan_rows, fieldnames=EXPANSION_PLAN_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows, fieldnames=REJECTED_FIELDS)
    write_json(run_dir / "cause_summary.json", cause_summary)
    summary = {
        "run_type": "v4_boundary_new_to_m844_bracket_trace",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "m854_target_source_rows": m854_target_source_rows_path,
        "m854_rejected_rows": m854_rejected_rows_path,
        "m854_accepted_boundary_rows": m854_accepted_boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "target_trace_sources": len(target_rows),
        "target_boundary_new_to_m844_sources": sum(1 for row in target_rows if row.get("trace_role") == "primary_boundary_new_to_m844"),
        "control_existing_boundary_sources": sum(1 for row in target_rows if row.get("trace_role") == "control_existing_boundary_recovered"),
        "reconstructed_snapshot_rows": len(snapshot_rows),
        "snapshot_rejection_rows": len(snapshot_rejections),
        "traced_source_axis_rows": len(primary_axis_rows),
        "all_traced_source_axis_rows": len(axis_summary_rows),
        "bracket_trace_rows": len(trace_rows),
        "cause_classified_source_axis_share": float(cause_classified_share),
        "accepted_boundary_found_extended_source_axes": sum(1 for row in primary_axis_rows if row.get("cause_class") == "accepted_boundary_found_extended"),
        "accepted_boundary_found_extended_source_groups": unique_count(
            [row for row in primary_axis_rows if row.get("cause_class") == "accepted_boundary_found_extended"],
            "source_group_id",
        ),
        "accepted_boundary_found_extended_fault_families": unique_count(
            [row for row in primary_axis_rows if row.get("cause_class") == "accepted_boundary_found_extended"],
            "preferred_fault_family",
        ),
        "all_safe_wide_source_axis_share": _cause_share(axis_summary_rows, "all_safe_wide"),
        "all_collision_or_negative_source_axis_share": _cause_share(axis_summary_rows, "all_collision_or_negative"),
        "ambiguous_or_nonfinite_source_axis_share": _cause_share(axis_summary_rows, "ambiguous_or_nonfinite"),
        "mixed_no_adjacent_bracket_source_axis_share": _cause_share(axis_summary_rows, "mixed_no_adjacent_bracket"),
        "max_seed_dominance": max_share(primary_axis_rows, "seed"),
        "max_fault_family_dominance": max_share(primary_axis_rows, "preferred_fault_family"),
        "min_target_boundary_new_to_m844_sources": int(min_target_boundary_new_to_m844_sources),
        "min_traced_source_axis_rows": int(min_traced_source_axis_rows),
        "min_bracket_trace_rows": int(min_bracket_trace_rows),
        "min_cause_classified_source_axis_share": float(min_cause_classified_source_axis_share),
        "min_extended_accept_axes": int(min_extended_accept_axes),
        "min_extended_accept_source_groups": int(min_extended_accept_source_groups),
        "min_extended_accept_fault_families": int(min_extended_accept_fault_families),
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
        "target_trace_source_rows_csv": run_dir / "target_trace_source_rows.csv",
        "bracket_trace_rows_csv": run_dir / "bracket_trace_rows.csv",
        "axis_trace_summary_csv": run_dir / "axis_trace_summary.csv",
        "source_trace_summary_csv": run_dir / "source_trace_summary.csv",
        "cause_summary_json": run_dir / "cause_summary.json",
        "candidate_expansion_plan_rows_csv": run_dir / "candidate_expansion_plan_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_axis_list(value: str) -> tuple[str, ...]:
    axes = tuple(part.strip() for part in str(value).split(",") if part.strip())
    if not axes:
        raise argparse.ArgumentTypeError("expected at least one boundary axis")
    unknown = [axis for axis in axes if axis not in BOUNDARY_AXES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown boundary axes: {unknown}")
    return axes


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace v4 boundary-new-to-M844 no-bracket causes.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--m854-target-source-rows", type=Path, required=True)
    parser.add_argument("--m854-rejected-rows", type=Path, required=True)
    parser.add_argument("--m854-accepted-boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-primary-sources", type=int, default=64)
    parser.add_argument("--control-existing-boundary-sources", type=int, default=8)
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
    parser.add_argument("--boundary-axes", type=_parse_axis_list, default=BOUNDARY_AXES)
    parser.add_argument("--initial-timing-deltas", type=parse_float_list, default=DEFAULT_INITIAL_TIMING_DELTAS)
    parser.add_argument("--initial-lateral-deltas", type=parse_float_list, default=DEFAULT_INITIAL_LATERAL_DELTAS)
    parser.add_argument("--initial-half-width-deltas", type=parse_float_list, default=DEFAULT_INITIAL_HALF_WIDTH_DELTAS)
    parser.add_argument("--extended-timing-deltas", type=parse_float_list, default=DEFAULT_EXTENDED_TIMING_DELTAS)
    parser.add_argument("--extended-lateral-deltas", type=parse_float_list, default=DEFAULT_EXTENDED_LATERAL_DELTAS)
    parser.add_argument("--extended-half-width-deltas", type=parse_float_list, default=DEFAULT_EXTENDED_HALF_WIDTH_DELTAS)
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--min-target-boundary-new-to-m844-sources", type=int, default=40)
    parser.add_argument("--min-traced-source-axis-rows", type=int, default=100)
    parser.add_argument("--min-bracket-trace-rows", type=int, default=1000)
    parser.add_argument("--min-cause-classified-source-axis-share", type=float, default=0.95)
    parser.add_argument("--min-extended-accept-axes", type=int, default=12)
    parser.add_argument("--min-extended-accept-source-groups", type=int, default=6)
    parser.add_argument("--min-extended-accept-fault-families", type=int, default=4)
    parser.add_argument("--all-safe-share-threshold", type=float, default=0.60)
    parser.add_argument("--all-collision-share-threshold", type=float, default=0.60)
    parser.add_argument("--ambiguous-share-threshold", type=float, default=0.20)
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
    summary = run_boundary_new_to_m844_bracket_trace(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        m854_target_source_rows_path=args.m854_target_source_rows,
        m854_rejected_rows_path=args.m854_rejected_rows,
        m854_accepted_boundary_rows_path=args.m854_accepted_boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_primary_sources=int(args.max_primary_sources),
        control_existing_boundary_sources=int(args.control_existing_boundary_sources),
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
        boundary_axes=tuple(args.boundary_axes),
        initial_timing_deltas=tuple(args.initial_timing_deltas),
        initial_lateral_deltas=tuple(args.initial_lateral_deltas),
        initial_half_width_deltas=tuple(args.initial_half_width_deltas),
        extended_timing_deltas=tuple(args.extended_timing_deltas),
        extended_lateral_deltas=tuple(args.extended_lateral_deltas),
        extended_half_width_deltas=tuple(args.extended_half_width_deltas),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        min_target_boundary_new_to_m844_sources=int(args.min_target_boundary_new_to_m844_sources),
        min_traced_source_axis_rows=int(args.min_traced_source_axis_rows),
        min_bracket_trace_rows=int(args.min_bracket_trace_rows),
        min_cause_classified_source_axis_share=float(args.min_cause_classified_source_axis_share),
        min_extended_accept_axes=int(args.min_extended_accept_axes),
        min_extended_accept_source_groups=int(args.min_extended_accept_source_groups),
        min_extended_accept_fault_families=int(args.min_extended_accept_fault_families),
        all_safe_share_threshold=float(args.all_safe_share_threshold),
        all_collision_share_threshold=float(args.all_collision_share_threshold),
        ambiguous_share_threshold=float(args.ambiguous_share_threshold),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
