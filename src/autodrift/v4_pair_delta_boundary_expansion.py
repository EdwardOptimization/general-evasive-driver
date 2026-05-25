"""No-training pair-delta boundary expansion over underrepresented sources."""

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
    axis_expansion_values,
    axis_initial_values,
    find_adjacent_margin_bracket,
    refine_bracket,
    _replay_parameter,
)
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_wrong_history_pair_mining import (
    BOUNDARY_REPLAY_FIELDS,
    margin_band,
    _source_meta_from_plan,
)
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    read_csv_rows,
    reconstruct_snapshots,
    _as_float,
    _as_int,
)


TARGET_SOURCE_FIELDS = [
    "target_rank",
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
    "target_priority_score",
    "target_priority_reasons",
]

BOUNDARY_EXTRA_FIELDS = [
    "source_target_class",
    "boundary_source_status",
    "target_priority_score",
    "target_priority_reasons",
]

EXPANDED_BOUNDARY_FIELDS = [*BOUNDARY_REPLAY_FIELDS, *BOUNDARY_EXTRA_FIELDS]

PAIRABILITY_FIELDS = [
    "pair_id",
    "left_candidate_id",
    "right_candidate_id",
    "left_source_group_id",
    "right_source_group_id",
    "left_seed",
    "right_seed",
    "left_fault_family",
    "right_fault_family",
    "left_boundary_axis",
    "right_boundary_axis",
    "left_source_target_class",
    "right_source_target_class",
    "left_boundary_source_status",
    "right_boundary_source_status",
    "left_normal_margin",
    "right_normal_margin",
    "normal_margin_gap_abs",
    "obstacle_geometry_distance",
    "first_action_l2",
    "pairability_tier",
    "source_pair_key",
    "fault_pair_key",
]

REJECTED_FIELDS = [
    "source_group_id",
    "step",
    "boundary_axis",
    "rejection_reason",
    "evaluations",
    "source_target_class",
    "boundary_source_status",
    "target_priority_score",
    "target_priority_reasons",
]


def _value_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _first_action(row: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            _finite_float(row.get("first_steer")),
            _finite_float(row.get("first_throttle")),
            _finite_float(row.get("first_brake")),
        ],
        dtype=np.float64,
    )


def _obstacle_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_vec = np.asarray(
        [
            _finite_float(left.get("target_obstacle_body_x")) / 80.0,
            _finite_float(left.get("target_obstacle_body_y")) / 8.0,
            _finite_float(left.get("target_obstacle_half_width")) / 4.0,
        ],
        dtype=np.float64,
    )
    right_vec = np.asarray(
        [
            _finite_float(right.get("target_obstacle_body_x")) / 80.0,
            _finite_float(right.get("target_obstacle_body_y")) / 8.0,
            _finite_float(right.get("target_obstacle_half_width")) / 4.0,
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(left_vec)) or not np.all(np.isfinite(right_vec)):
        return float("inf")
    return float(np.linalg.norm(left_vec - right_vec))


def _active_sets(balanced_pair_delta_rows: list[dict[str, str]]) -> dict[str, set[str]]:
    return {
        "source_group_id": {str(_as_int(row.get("left_source_group_id"))) for row in balanced_pair_delta_rows},
        "seed": {str(_as_int(row.get("left_seed"))) for row in balanced_pair_delta_rows},
        "preferred_fault_family": {str(row.get("left_fault_family", "")) for row in balanced_pair_delta_rows},
    }


def _plan_by_source_group(plan_rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    output: dict[int, dict[str, str]] = {}
    ordered = sorted(
        plan_rows,
        key=lambda row: (
            _as_int(row.get("source_group_id")),
            _as_int(row.get("step")),
            _as_int(row.get("candidate_id")),
        ),
    )
    for row in ordered:
        group_id = _as_int(row.get("source_group_id"))
        if group_id >= 0:
            output.setdefault(group_id, row)
    return output


def _priority_for_source(
    *,
    source_row: dict[str, str],
    plan_row: dict[str, str],
    active: dict[str, set[str]],
    existing_boundary_source_groups: set[str],
) -> tuple[int, list[str], str, str]:
    source_group_id = str(_as_int(source_row.get("source_group_id")))
    seed = str(_as_int(source_row.get("seed")))
    fault_family = str(source_row.get("preferred_fault_family", ""))
    score = 0
    reasons: list[str] = []
    if source_group_id not in active["source_group_id"]:
        score += 100
        reasons.append("not_m850_balanced_left_source")
    if seed not in active["seed"]:
        score += 30
        reasons.append("seed_absent_from_m850_balanced_left")
    if fault_family not in active["preferred_fault_family"]:
        score += 30
        reasons.append("fault_family_absent_from_m850_balanced_left")
    if source_group_id in existing_boundary_source_groups and source_group_id not in active["source_group_id"]:
        score += 10
        reasons.append("existing_m844_boundary_source_not_m850_left")
    if parse_bool(source_row.get("collision", False)):
        score -= 2
        reasons.append("source_probe_collision")
    if not parse_bool(source_row.get("success", False)):
        score -= 1
        reasons.append("source_probe_not_success")

    if source_group_id in active["source_group_id"]:
        source_target_class = "active_set_control_boundary"
        boundary_source_status = "active_set_control_boundary"
    else:
        source_target_class = "new_underrepresented_boundary"
        boundary_source_status = (
            "existing_boundary_recovered"
            if source_group_id in existing_boundary_source_groups
            else "boundary_new_to_m844"
        )
    if not reasons:
        reasons.append("low_priority_control")
    _ = plan_row
    return score, reasons, source_target_class, boundary_source_status


def select_target_source_rows(
    source_rows: list[dict[str, str]],
    plan_rows: list[dict[str, str]],
    balanced_pair_delta_rows: list[dict[str, str]],
    existing_boundary_rows: list[dict[str, str]],
    *,
    max_targets: int,
    max_targets_per_seed: int,
    max_targets_per_fault_family: int,
    max_targets_per_warmup_mode: int,
    max_targets_per_source_group: int,
    active_control_budget: int,
) -> list[dict[str, Any]]:
    """Select source-group/step targets favoring sources absent from M850."""

    active = _active_sets(balanced_pair_delta_rows)
    existing_boundary_source_groups = {str(_as_int(row.get("source_group_id"))) for row in existing_boundary_rows}
    plan_by_group = _plan_by_source_group(plan_rows)
    candidates: list[dict[str, Any]] = []
    for source_row in source_rows:
        source_group_id = _as_int(source_row.get("source_group_id"))
        plan = plan_by_group.get(source_group_id)
        if plan is None:
            continue
        score, reasons, source_target_class, boundary_source_status = _priority_for_source(
            source_row=source_row,
            plan_row=plan,
            active=active,
            existing_boundary_source_groups=existing_boundary_source_groups,
        )
        candidates.append(
            {
                "source_row": source_row,
                "plan_row": plan,
                "priority": score,
                "reasons": reasons,
                "source_target_class": source_target_class,
                "boundary_source_status": boundary_source_status,
            }
        )
    candidates.sort(
        key=lambda item: (
            0 if item["source_target_class"] == "new_underrepresented_boundary" else 1,
            -int(item["priority"]),
            _as_int(item["source_row"].get("seed")),
            str(item["source_row"].get("preferred_fault_family", "")),
            _as_int(item["source_row"].get("source_group_id")),
        )
    )

    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    active_controls = 0
    for item in candidates:
        source = item["source_row"]
        plan = item["plan_row"]
        source_group_id = str(_as_int(source.get("source_group_id")))
        seed = str(_as_int(source.get("seed")))
        fault_family = str(source.get("preferred_fault_family", ""))
        warmup_mode = str(source.get("warmup_mode", ""))
        is_control = item["source_target_class"] == "active_set_control_boundary"
        if is_control:
            if active_controls >= int(active_control_budget):
                continue
            active_controls += 1
        limits = [
            (("source_group_id", source_group_id), int(max_targets_per_source_group)),
            (("seed", seed), int(max_targets_per_seed)),
            (("preferred_fault_family", fault_family), int(max_targets_per_fault_family)),
            (("warmup_mode", warmup_mode), int(max_targets_per_warmup_mode)),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in limits):
            continue
        row = {
            "target_rank": len(selected),
            "source_group_id": _as_int(source.get("source_group_id")),
            "step": _as_int(plan.get("step")),
            "snapshot_uid": str(plan.get("snapshot_uid", "")),
            "source_index": _as_int(plan.get("source_index")),
            "seed": _as_int(source.get("seed")),
            "warmup_mode": warmup_mode,
            "preferred_fault": str(source.get("preferred_fault", "")),
            "preferred_fault_family": fault_family,
            "preferred_fault_severity": str(source.get("preferred_fault_severity", "")),
            "preferred_fidelity_class": str(source.get("preferred_fidelity_class", "")),
            "wrong_fault": str(source.get("wrong_fault", "")),
            "wrong_fault_family": str(source.get("wrong_fault_family", "")),
            "wrong_fidelity_class": str(source.get("wrong_fidelity_class", "")),
            "fault_family_pair": str(source.get("fault_family_pair", "")),
            "fault_onset_bucket": str(plan.get("fault_onset_bucket", "")),
            "source_axis": str(source.get("source_axis", "")),
            "source_obstacle_body_x": _as_float(plan.get("source_obstacle_body_x")),
            "source_obstacle_body_y": _as_float(plan.get("source_obstacle_body_y")),
            "source_obstacle_half_width": _as_float(plan.get("source_obstacle_half_width")),
            "source_target_class": item["source_target_class"],
            "boundary_source_status": item["boundary_source_status"],
            "target_priority_score": int(item["priority"]),
            "target_priority_reasons": ";".join(item["reasons"]),
            "plan_row": plan,
        }
        selected.append(row)
        for key, _limit in limits:
            counts[key] = counts.get(key, 0) + 1
        if len(selected) >= int(max_targets):
            break
    return selected


def build_pairability_projection_rows(
    accepted_boundary_rows: list[dict[str, Any]],
    *,
    min_first_action_l2: float,
    max_obstacle_distance: float,
    diagnostic_max_obstacle_distance: float,
) -> list[dict[str, Any]]:
    """Build cheap pairability projections without sequence replay."""

    rows = [
        row
        for row in accepted_boundary_rows
        if parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and 0.0 <= _finite_float(row.get("min_clearance_margin")) <= 0.05
    ]
    projections: list[dict[str, Any]] = []
    pair_id = 0
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            if _as_int(left.get("source_group_id")) == _as_int(right.get("source_group_id")):
                continue
            obstacle_distance = _obstacle_distance(left, right)
            if obstacle_distance > float(diagnostic_max_obstacle_distance):
                continue
            first_action_l2 = float(np.linalg.norm(_first_action(left) - _first_action(right)))
            if first_action_l2 < float(min_first_action_l2):
                continue
            left_margin = _finite_float(left.get("min_clearance_margin"))
            right_margin = _finite_float(right.get("min_clearance_margin"))
            tier = "primary_0_10" if obstacle_distance <= float(max_obstacle_distance) else "diagnostic_0_20"
            projections.append(
                {
                    "pair_id": pair_id,
                    "left_candidate_id": _as_int(left.get("candidate_id")),
                    "right_candidate_id": _as_int(right.get("candidate_id")),
                    "left_source_group_id": _as_int(left.get("source_group_id")),
                    "right_source_group_id": _as_int(right.get("source_group_id")),
                    "left_seed": _as_int(left.get("seed")),
                    "right_seed": _as_int(right.get("seed")),
                    "left_fault_family": str(left.get("preferred_fault_family", "")),
                    "right_fault_family": str(right.get("preferred_fault_family", "")),
                    "left_boundary_axis": str(left.get("boundary_axis", "")),
                    "right_boundary_axis": str(right.get("boundary_axis", "")),
                    "left_source_target_class": str(left.get("source_target_class", "")),
                    "right_source_target_class": str(right.get("source_target_class", "")),
                    "left_boundary_source_status": str(left.get("boundary_source_status", "")),
                    "right_boundary_source_status": str(right.get("boundary_source_status", "")),
                    "left_normal_margin": left_margin,
                    "right_normal_margin": right_margin,
                    "normal_margin_gap_abs": abs(left_margin - right_margin),
                    "obstacle_geometry_distance": obstacle_distance,
                    "first_action_l2": first_action_l2,
                    "pairability_tier": tier,
                    "source_pair_key": f"{_as_int(left.get('source_group_id'))}->{_as_int(right.get('source_group_id'))}",
                    "fault_pair_key": f"{left.get('preferred_fault_family', '')}->{right.get('preferred_fault_family', '')}",
                }
            )
            pair_id += 1
    projections.sort(
        key=lambda row: (
            0 if row["pairability_tier"] == "primary_0_10" else 1,
            _finite_float(row.get("obstacle_geometry_distance"), default=999.0),
            -_finite_float(row.get("first_action_l2"), default=0.0),
            _as_int(row.get("left_candidate_id")),
            _as_int(row.get("right_candidate_id")),
        )
    )
    for index, row in enumerate(projections):
        row["pair_id"] = int(index)
    return projections


def boundary_diversity_summary(
    *,
    target_rows: list[dict[str, Any]],
    accepted_rows: list[dict[str, Any]],
    pairability_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    primary_pairability = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    underrepresented = [row for row in accepted_rows if row.get("source_target_class") == "new_underrepresented_boundary"]
    return {
        "target_rows": {
            "rows": len(target_rows),
            "unique_seed_count": unique_count(target_rows, "seed"),
            "unique_fault_family_count": unique_count(target_rows, "preferred_fault_family"),
            "unique_source_group_count": unique_count(target_rows, "source_group_id"),
            "source_target_class_counts": _value_counts(target_rows, "source_target_class"),
        },
        "accepted_boundary_rows": {
            "rows": len(accepted_rows),
            "new_underrepresented_boundary_rows": len(underrepresented),
            "unique_seed_count": unique_count(accepted_rows, "seed"),
            "unique_source_group_count": unique_count(accepted_rows, "source_group_id"),
            "unique_fault_family_count": unique_count(accepted_rows, "preferred_fault_family"),
            "unique_boundary_axis_count": unique_count(accepted_rows, "boundary_axis"),
            "max_seed_dominance": max_share(accepted_rows, "seed"),
            "max_source_group_dominance": max_share(accepted_rows, "source_group_id"),
            "boundary_axis_counts": _value_counts(accepted_rows, "boundary_axis"),
            "fault_family_counts": _value_counts(accepted_rows, "preferred_fault_family"),
            "source_target_class_counts": _value_counts(accepted_rows, "source_target_class"),
            "boundary_source_status_counts": _value_counts(accepted_rows, "boundary_source_status"),
        },
        "pairability_projection_rows": {
            "rows": len(pairability_rows),
            "primary_rows": len(primary_pairability),
            "unique_source_group_count": unique_count(primary_pairability, "left_source_group_id"),
            "tier_counts": _value_counts(pairability_rows, "pairability_tier"),
        },
    }


def classify_pair_delta_boundary_expansion(
    *,
    actor_changed: bool,
    residual_changed: bool,
    accepted_rows: list[dict[str, Any]],
    pairability_rows: list[dict[str, Any]],
    strong_min_rows: int,
    sparse_min_rows: int,
    min_new_underrepresented_rows: int,
    sparse_min_new_underrepresented_rows: int,
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
    min_projected_pairable_source_groups: int,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_pair_delta_boundary_expansion_contract_violation"
    primary_pairability = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    underrepresented = [row for row in accepted_rows if row.get("source_target_class") == "new_underrepresented_boundary"]
    if len(accepted_rows) < 24 or len(underrepresented) < 12:
        return "v4_pair_delta_boundary_expansion_all_weak"
    strong = bool(
        len(accepted_rows) >= int(strong_min_rows)
        and len(underrepresented) >= int(min_new_underrepresented_rows)
        and unique_count(accepted_rows, "source_group_id") >= int(min_source_groups)
        and unique_count(accepted_rows, "seed") >= int(min_seeds)
        and unique_count(accepted_rows, "preferred_fault_family") >= int(min_fault_families)
        and unique_count(accepted_rows, "boundary_axis") >= int(min_boundary_axes)
        and max_share(accepted_rows, "source_group_id") <= float(max_source_group_dominance)
        and max_share(accepted_rows, "seed") <= float(max_seed_dominance)
        and len(primary_pairability) >= int(min_pairability_rows)
        and unique_count(primary_pairability, "left_source_group_id") >= int(min_projected_pairable_source_groups)
    )
    if strong:
        return "v4_pair_delta_boundary_expansion_pass"
    sparse = bool(
        len(accepted_rows) >= int(sparse_min_rows)
        and len(underrepresented) >= int(sparse_min_new_underrepresented_rows)
        and unique_count(accepted_rows, "source_group_id") >= int(sparse_min_source_groups)
        and unique_count(accepted_rows, "seed") >= int(sparse_min_seeds)
        and unique_count(accepted_rows, "preferred_fault_family") >= int(sparse_min_fault_families)
        and len(primary_pairability) >= int(sparse_min_pairability_rows)
    )
    if sparse:
        return "v4_pair_delta_boundary_expansion_sparse_useful"
    return "v4_pair_delta_boundary_expansion_source_limited"


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
            "gate_name": "target_source_rows",
            "value": summary["target_source_rows"],
            "threshold": summary["min_target_source_rows"],
            "passed": int(summary["target_source_rows"]) >= int(summary["min_target_source_rows"]),
            "notes": "underrepresented source targeting before boundary replay",
        },
        {
            "gate_name": "accepted_boundary_rows",
            "value": summary["accepted_boundary_rows"],
            "threshold": summary["strong_min_boundary_rows"],
            "passed": int(summary["accepted_boundary_rows"]) >= int(summary["strong_min_boundary_rows"]),
            "notes": "strong boundary expansion row count",
        },
        {
            "gate_name": "new_underrepresented_boundary_rows",
            "value": summary["new_underrepresented_boundary_rows"],
            "threshold": summary["min_new_underrepresented_boundary_rows"],
            "passed": int(summary["new_underrepresented_boundary_rows"]) >= int(summary["min_new_underrepresented_boundary_rows"]),
            "notes": "accepted rows from sources absent from M850 balanced left side",
        },
        {
            "gate_name": "source_group_diversity",
            "value": summary["unique_source_group_count"],
            "threshold": summary["min_source_groups"],
            "passed": int(summary["unique_source_group_count"]) >= int(summary["min_source_groups"]),
            "notes": "expanded source-group coverage",
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
            "notes": "M854 may not run pair-delta sequence replay",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M854 cannot promote",
        },
    ]


def run_pair_delta_boundary_expansion(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    existing_boundary_rows_path: Path,
    balanced_pair_delta_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_targets: int,
    min_target_source_rows: int,
    active_control_budget: int,
    max_targets_per_seed: int,
    max_targets_per_fault_family: int,
    max_targets_per_warmup_mode: int,
    max_targets_per_source_group: int,
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
    timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    max_expansion_attempts: int,
    max_refinement_iterations: int,
    parameter_tolerance: float,
    boundary_margin_threshold: float,
    strict_margin_threshold: float,
    min_first_action_l2: float,
    max_pairability_obstacle_distance: float,
    diagnostic_pairability_obstacle_distance: float,
    strong_min_boundary_rows: int,
    sparse_min_boundary_rows: int,
    min_new_underrepresented_boundary_rows: int,
    sparse_min_new_underrepresented_boundary_rows: int,
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
    min_projected_pairable_source_groups: int,
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
        raise ValueError("M854 boundary expansion requires an online recurrent checkpoint")
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
    existing_boundary_rows = read_csv_rows(existing_boundary_rows_path)
    balanced_pair_delta_rows = read_csv_rows(balanced_pair_delta_rows_path)
    target_rows = select_target_source_rows(
        source_rows,
        plan_rows,
        balanced_pair_delta_rows,
        existing_boundary_rows,
        max_targets=int(max_targets),
        max_targets_per_seed=int(max_targets_per_seed),
        max_targets_per_fault_family=int(max_targets_per_fault_family),
        max_targets_per_warmup_mode=int(max_targets_per_warmup_mode),
        max_targets_per_source_group=int(max_targets_per_source_group),
        active_control_budget=int(active_control_budget),
    )

    request_rows = [
        {
            "left_source_group_id": int(row["source_group_id"]),
            "right_source_group_id": int(row["source_group_id"]),
            "left_step": int(row["step"]),
            "right_step": int(row["step"]),
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

    target_by_key = {(int(row["source_group_id"]), int(row["step"])): row for row in target_rows}
    boundary_rows: list[dict[str, Any]] = []
    accepted_boundary_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = [
        {
            "source_group_id": row.get("source_group_id", ""),
            "step": row.get("step", ""),
            "boundary_axis": "",
            "rejection_reason": row.get("rejection_reason", ""),
            "evaluations": 0,
            "source_target_class": "",
            "boundary_source_status": "",
            "target_priority_score": "",
            "target_priority_reasons": "",
        }
        for row in snapshot_rejections
    ]
    candidate_id = 0
    bracket_id = 0
    for key, snapshot in sorted(snapshots.items()):
        target = target_by_key.get(key)
        if target is None:
            rejected_rows.append(
                {
                    "source_group_id": key[0],
                    "step": key[1],
                    "boundary_axis": "",
                    "rejection_reason": "missing_target_row",
                    "evaluations": 0,
                    "source_target_class": "",
                    "boundary_source_status": "",
                    "target_priority_score": "",
                    "target_priority_reasons": "",
                }
            )
            continue
        plan = dict(target["plan_row"])
        source_meta = _source_meta_from_plan(plan, source_index=_as_int(target.get("source_index")), fault_by_name=fault_by_name, warmup_steps=int(warmup_steps))
        source_meta.update({field: target[field] for field in BOUNDARY_EXTRA_FIELDS})
        for axis in boundary_axes:
            values = axis_initial_values(
                axis,
                body_x=_as_float(plan.get("source_obstacle_body_x")),
                body_y=_as_float(plan.get("source_obstacle_body_y")),
                half_width=_as_float(plan.get("source_obstacle_half_width")),
                timing_deltas=timing_deltas,
                lateral_deltas=lateral_deltas,
                half_width_deltas=half_width_deltas,
            )
            evaluations: list[dict[str, Any]] = []
            seen_values: set[float] = set()
            for value in values:
                key_value = round(float(value), 9)
                if key_value in seen_values:
                    continue
                seen_values.add(key_value)
                result, _actions, _relocated = _replay_parameter(
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
            bracket = find_adjacent_margin_bracket(evaluations)
            if bracket is None:
                for value in axis_expansion_values(
                    axis,
                    body_x=_as_float(plan.get("source_obstacle_body_x")),
                    body_y=_as_float(plan.get("source_obstacle_body_y")),
                    half_width=_as_float(plan.get("source_obstacle_half_width")),
                    max_expansion_attempts=int(max_expansion_attempts),
                ):
                    key_value = round(float(value), 9)
                    if key_value in seen_values:
                        continue
                    seen_values.add(key_value)
                    result, _actions, _relocated = _replay_parameter(
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
                    bracket = find_adjacent_margin_bracket(evaluations)
                    if bracket is not None:
                        break
            if bracket is None:
                rejected_rows.append(
                    {
                        "source_group_id": int(source_meta["source_group_id"]),
                        "step": int(source_meta["step"]),
                        "boundary_axis": axis,
                        "rejection_reason": "no_collision_safe_bracket",
                        "evaluations": int(len(evaluations)),
                        "source_target_class": source_meta["source_target_class"],
                        "boundary_source_status": source_meta["boundary_source_status"],
                        "target_priority_score": source_meta["target_priority_score"],
                        "target_priority_reasons": source_meta["target_priority_reasons"],
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
                primary_margin_threshold=float(boundary_margin_threshold),
                parameter_tolerance=float(parameter_tolerance),
                device=resolved_device,
                start_candidate_id=candidate_id,
            )
            for row in rows:
                margin = _finite_float(row.get("min_clearance_margin"))
                row["horizon"] = int(horizon)
                row["margin_band"] = margin_band(
                    margin,
                    strict_margin_threshold=float(strict_margin_threshold),
                    boundary_margin_threshold=float(boundary_margin_threshold),
                )
            boundary_rows.extend(rows)
            accepted_boundary_rows.extend(accepted_rows)
            for row in accepted_rows:
                margin = _finite_float(row.get("min_clearance_margin"))
                row["horizon"] = int(horizon)
                row["margin_band"] = margin_band(
                    margin,
                    strict_margin_threshold=float(strict_margin_threshold),
                    boundary_margin_threshold=float(boundary_margin_threshold),
                )
            _append_progress(
                progress_path,
                {
                    "stage": "boundary_refine",
                    "source_group_id": int(source_meta["source_group_id"]),
                    "step": int(source_meta["step"]),
                    "boundary_axis": axis,
                    "status": status,
                    "accepted_rows": len(accepted_rows),
                    "rows": len(rows),
                },
            )
            bracket_id += 1

    pairability_rows = build_pairability_projection_rows(
        accepted_boundary_rows,
        min_first_action_l2=float(min_first_action_l2),
        max_obstacle_distance=float(max_pairability_obstacle_distance),
        diagnostic_max_obstacle_distance=float(diagnostic_pairability_obstacle_distance),
    )
    primary_pairability_rows = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    new_underrepresented = [row for row in accepted_boundary_rows if row.get("source_target_class") == "new_underrepresented_boundary"]
    diversity = boundary_diversity_summary(
        target_rows=target_rows,
        accepted_rows=accepted_boundary_rows,
        pairability_rows=pairability_rows,
    )

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_pair_delta_boundary_expansion(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        accepted_rows=accepted_boundary_rows,
        pairability_rows=pairability_rows,
        strong_min_rows=int(strong_min_boundary_rows),
        sparse_min_rows=int(sparse_min_boundary_rows),
        min_new_underrepresented_rows=int(min_new_underrepresented_boundary_rows),
        sparse_min_new_underrepresented_rows=int(sparse_min_new_underrepresented_boundary_rows),
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
        min_projected_pairable_source_groups=int(min_projected_pairable_source_groups),
    )

    write_csv_rows(run_dir / "target_source_rows.csv", [{k: row.get(k, "") for k in TARGET_SOURCE_FIELDS} for row in target_rows], fieldnames=TARGET_SOURCE_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "expanded_boundary_rows.csv", boundary_rows, fieldnames=EXPANDED_BOUNDARY_FIELDS)
    write_csv_rows(run_dir / "accepted_boundary_rows.csv", accepted_boundary_rows, fieldnames=EXPANDED_BOUNDARY_FIELDS)
    write_csv_rows(run_dir / "pairability_projection_rows.csv", pairability_rows, fieldnames=PAIRABILITY_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows, fieldnames=REJECTED_FIELDS)
    write_json(run_dir / "boundary_diversity_summary.json", diversity)
    (run_dir / "fault_proxy_limitations.md").write_text(
        "M854 expands current-model/proxy low-margin boundaries only. It does not establish wheel-level physical fidelity or self-ID proof.\n",
        encoding="utf-8",
    )

    summary = {
        "run_type": "v4_pair_delta_boundary_expansion",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "existing_boundary_rows": existing_boundary_rows_path,
        "balanced_pair_delta_rows": balanced_pair_delta_rows_path,
        "alpha": float(alpha),
        "source_rows_count": len(source_rows),
        "candidate_plan_rows_count": len(plan_rows),
        "target_source_rows": len(target_rows),
        "min_target_source_rows": int(min_target_source_rows),
        "target_unique_seed_count": unique_count(target_rows, "seed"),
        "target_unique_fault_family_count": unique_count(target_rows, "preferred_fault_family"),
        "target_unique_source_group_count": unique_count(target_rows, "source_group_id"),
        "reconstructed_snapshot_rows": len(snapshot_rows),
        "snapshot_rejection_rows": len(snapshot_rejections),
        "expanded_boundary_rows": len(boundary_rows),
        "accepted_boundary_rows": len(accepted_boundary_rows),
        "new_underrepresented_boundary_rows": len(new_underrepresented),
        "unique_source_group_count": unique_count(accepted_boundary_rows, "source_group_id"),
        "unique_seed_count": unique_count(accepted_boundary_rows, "seed"),
        "unique_fault_family_count": unique_count(accepted_boundary_rows, "preferred_fault_family"),
        "unique_boundary_axis_count": unique_count(accepted_boundary_rows, "boundary_axis"),
        "max_source_group_dominance": max_share(accepted_boundary_rows, "source_group_id"),
        "max_seed_dominance": max_share(accepted_boundary_rows, "seed"),
        "pairability_projection_rows": len(primary_pairability_rows),
        "diagnostic_pairability_projection_rows": len(pairability_rows),
        "projected_pairable_source_groups": unique_count(primary_pairability_rows, "left_source_group_id"),
        "strong_min_boundary_rows": int(strong_min_boundary_rows),
        "sparse_min_boundary_rows": int(sparse_min_boundary_rows),
        "min_new_underrepresented_boundary_rows": int(min_new_underrepresented_boundary_rows),
        "sparse_min_new_underrepresented_boundary_rows": int(sparse_min_new_underrepresented_boundary_rows),
        "min_source_groups": int(min_source_groups),
        "sparse_min_source_groups": int(sparse_min_source_groups),
        "min_seeds": int(min_seeds),
        "sparse_min_seeds": int(sparse_min_seeds),
        "min_fault_families": int(min_fault_families),
        "sparse_min_fault_families": int(sparse_min_fault_families),
        "min_boundary_axes": int(min_boundary_axes),
        "max_source_group_dominance_threshold": float(max_source_group_dominance),
        "max_seed_dominance_threshold": float(max_seed_dominance),
        "min_pairability_projection_rows": int(min_pairability_projection_rows),
        "sparse_min_pairability_projection_rows": int(sparse_min_pairability_projection_rows),
        "min_projected_pairable_source_groups": int(min_projected_pairable_source_groups),
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
        "target_source_rows_csv": run_dir / "target_source_rows.csv",
        "expanded_boundary_rows_csv": run_dir / "expanded_boundary_rows.csv",
        "accepted_boundary_rows_csv": run_dir / "accepted_boundary_rows.csv",
        "pairability_projection_rows_csv": run_dir / "pairability_projection_rows.csv",
        "boundary_diversity_summary_json": run_dir / "boundary_diversity_summary.json",
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
    parser = argparse.ArgumentParser(description="Run no-training v4 pair-delta boundary expansion.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--existing-boundary-rows", type=Path, required=True)
    parser.add_argument("--balanced-pair-delta-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-targets", type=int, default=64)
    parser.add_argument("--min-target-source-rows", type=int, default=48)
    parser.add_argument("--active-control-budget", type=int, default=0)
    parser.add_argument("--max-targets-per-seed", type=int, default=8)
    parser.add_argument("--max-targets-per-fault-family", type=int, default=10)
    parser.add_argument("--max-targets-per-warmup-mode", type=int, default=16)
    parser.add_argument("--max-targets-per-source-group", type=int, default=1)
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
    parser.add_argument("--timing-deltas", type=parse_float_list, default=(-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0))
    parser.add_argument("--lateral-deltas", type=parse_float_list, default=(-0.45, -0.25, -0.12, 0.0, 0.12, 0.25, 0.45))
    parser.add_argument("--half-width-deltas", type=parse_float_list, default=(-0.08, -0.04, 0.0, 0.04, 0.08, 0.14))
    parser.add_argument("--max-expansion-attempts", type=int, default=4)
    parser.add_argument("--max-refinement-iterations", type=int, default=10)
    parser.add_argument("--parameter-tolerance", type=float, default=1e-4)
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--strict-margin-threshold", type=float, default=0.02)
    parser.add_argument("--min-first-action-l2", type=float, default=0.014)
    parser.add_argument("--max-pairability-obstacle-distance", type=float, default=0.10)
    parser.add_argument("--diagnostic-pairability-obstacle-distance", type=float, default=0.20)
    parser.add_argument("--strong-min-boundary-rows", type=int, default=80)
    parser.add_argument("--sparse-min-boundary-rows", type=int, default=50)
    parser.add_argument("--min-new-underrepresented-boundary-rows", type=int, default=40)
    parser.add_argument("--sparse-min-new-underrepresented-boundary-rows", type=int, default=24)
    parser.add_argument("--min-source-groups", type=int, default=32)
    parser.add_argument("--sparse-min-source-groups", type=int, default=20)
    parser.add_argument("--min-seeds", type=int, default=8)
    parser.add_argument("--sparse-min-seeds", type=int, default=6)
    parser.add_argument("--min-fault-families", type=int, default=8)
    parser.add_argument("--sparse-min-fault-families", type=int, default=6)
    parser.add_argument("--min-boundary-axes", type=int, default=3)
    parser.add_argument("--max-source-group-dominance", type=float, default=0.08)
    parser.add_argument("--max-seed-dominance", type=float, default=0.20)
    parser.add_argument("--min-pairability-projection-rows", type=int, default=160)
    parser.add_argument("--sparse-min-pairability-projection-rows", type=int, default=80)
    parser.add_argument("--min-projected-pairable-source-groups", type=int, default=16)
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
    summary = run_pair_delta_boundary_expansion(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        existing_boundary_rows_path=args.existing_boundary_rows,
        balanced_pair_delta_rows_path=args.balanced_pair_delta_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_targets=int(args.max_targets),
        min_target_source_rows=int(args.min_target_source_rows),
        active_control_budget=int(args.active_control_budget),
        max_targets_per_seed=int(args.max_targets_per_seed),
        max_targets_per_fault_family=int(args.max_targets_per_fault_family),
        max_targets_per_warmup_mode=int(args.max_targets_per_warmup_mode),
        max_targets_per_source_group=int(args.max_targets_per_source_group),
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
        timing_deltas=tuple(args.timing_deltas),
        lateral_deltas=tuple(args.lateral_deltas),
        half_width_deltas=tuple(args.half_width_deltas),
        max_expansion_attempts=int(args.max_expansion_attempts),
        max_refinement_iterations=int(args.max_refinement_iterations),
        parameter_tolerance=float(args.parameter_tolerance),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        strict_margin_threshold=float(args.strict_margin_threshold),
        min_first_action_l2=float(args.min_first_action_l2),
        max_pairability_obstacle_distance=float(args.max_pairability_obstacle_distance),
        diagnostic_pairability_obstacle_distance=float(args.diagnostic_pairability_obstacle_distance),
        strong_min_boundary_rows=int(args.strong_min_boundary_rows),
        sparse_min_boundary_rows=int(args.sparse_min_boundary_rows),
        min_new_underrepresented_boundary_rows=int(args.min_new_underrepresented_boundary_rows),
        sparse_min_new_underrepresented_boundary_rows=int(args.sparse_min_new_underrepresented_boundary_rows),
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
        min_projected_pairable_source_groups=int(args.min_projected_pairable_source_groups),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
