"""No-training near-boundary wrong-history pair mining for v4."""

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
from autodrift.v4_extreme_hidden_dynamics_data_route import IdentityResidualGate, fault_onset_bucket
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    ACCEPTED_FIELDS,
    GATE_SUMMARY_FIELDS,
    PAIR_SOURCE_FIELDS,
    REPLAY_FIELDS,
    accepted_wrong_history_rows_for_pair,
    build_replay_rows_for_pair,
    read_csv_rows,
    reconstruct_snapshots,
    _as_float,
    _as_int,
    _diversity,
)


BOUNDARY_SOURCE_FIELDS = [
    "source_group_id",
    "step",
    "snapshot_id",
    "seed",
    "fault",
    "fault_family",
    "fidelity_class",
    "warmup_mode",
    "history_observations",
]

BOUNDARY_REPLAY_FIELDS = [
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
    "preferred_fault_severity",
    "preferred_fidelity_class",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fidelity_class",
    "fault_family_pair",
    "fault_onset_bucket",
    "source_axis",
    "boundary_axis",
    "horizon",
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
    "success",
    "collision",
    "terminal_reason",
    "min_clearance_margin",
    "first_steer",
    "first_throttle",
    "first_brake",
    "first_action_l2_from_reference",
    "prefix_l2_mean",
    "accepted_primary",
    "margin_band",
]

NEAR_BOUNDARY_PAIR_FIELDS = [
    *PAIR_SOURCE_FIELDS,
    "left_normal_margin",
    "right_normal_margin",
    "left_boundary_axis",
    "right_boundary_axis",
    "left_margin_band",
    "right_margin_band",
    "pair_rank_score",
]

REJECTED_BOUNDARY_FIELDS = [
    "source_group_id",
    "step",
    "boundary_axis",
    "rejection_reason",
    "evaluations",
]

REJECTED_PAIR_FIELDS = [
    *NEAR_BOUNDARY_PAIR_FIELDS,
    "rejection_reason",
]


def _bool(value: Any) -> bool:
    return parse_bool(value)


def margin_band(margin: float, *, strict_margin_threshold: float, boundary_margin_threshold: float) -> str:
    if not np.isfinite(margin):
        return "nonfinite"
    if margin < 0.0:
        return "collision_or_negative"
    if margin <= 0.005:
        return "ultra_strict_0_005"
    if margin <= float(strict_margin_threshold):
        return "strict"
    if margin <= float(boundary_margin_threshold):
        return "boundary"
    return "wide"


def source_requests_from_plan_rows(
    plan_rows: list[dict[str, str]],
    *,
    max_source_snapshots: int,
) -> list[dict[str, Any]]:
    """Return unique source-group/step reconstruction requests from M825 plans."""

    by_key: dict[tuple[int, int], dict[str, str]] = {}
    for row in plan_rows:
        key = (_as_int(row.get("source_group_id")), _as_int(row.get("step")))
        if key[0] < 0 or key[1] < 0:
            continue
        by_key.setdefault(key, row)
    requests: list[dict[str, Any]] = []
    for index, ((source_group_id, step), row) in enumerate(sorted(by_key.items())):
        if index >= int(max_source_snapshots):
            break
        requests.append(
            {
                "pair_id": index,
                "left_source_group_id": source_group_id,
                "right_source_group_id": source_group_id,
                "left_step": step,
                "right_step": step,
                "left_plan": row,
                "right_plan": row,
            }
        )
    return requests


def _plan_by_source_step(plan_rows: list[dict[str, str]]) -> dict[tuple[int, int], dict[str, str]]:
    output: dict[tuple[int, int], dict[str, str]] = {}
    for row in plan_rows:
        key = (_as_int(row.get("source_group_id")), _as_int(row.get("step")))
        output.setdefault(key, row)
    return output


def _source_meta_from_plan(plan: dict[str, str], *, source_index: int, fault_by_name: dict[str, Any], warmup_steps: int) -> dict[str, Any]:
    fault = fault_by_name.get(str(plan.get("preferred_fault", "")))
    onset = str(plan.get("fault_onset_bucket", ""))
    if fault is not None and not onset:
        onset = fault_onset_bucket(fault, snapshot_step=_as_int(plan.get("step")), warmup_steps=int(warmup_steps))
    return {
        "source_group_id": _as_int(plan.get("source_group_id")),
        "snapshot_uid": str(plan.get("snapshot_uid", "")),
        "source_index": int(source_index),
        "seed": _as_int(plan.get("seed")),
        "step": _as_int(plan.get("step")),
        "warmup_mode": str(plan.get("warmup_mode", "")),
        "preferred_fault": str(plan.get("preferred_fault", "")),
        "preferred_fault_family": str(plan.get("preferred_fault_family", "")),
        "preferred_fault_severity": str(plan.get("preferred_fault_severity", "")),
        "preferred_fidelity_class": str(plan.get("preferred_fidelity_class", "")),
        "wrong_fault": str(plan.get("wrong_fault", "")),
        "wrong_fault_family": str(plan.get("wrong_fault_family", "")),
        "wrong_fidelity_class": str(plan.get("wrong_fidelity_class", "")),
        "fault_family_pair": str(plan.get("fault_family_pair", "")),
        "fault_onset_bucket": onset,
        "source_axis": str(plan.get("source_axis", "")),
        "horizon": _as_int(plan.get("horizon"), 6),
        "ego_vx_norm": _as_float(plan.get("ego_vx_norm")),
        "ego_vy_norm": _as_float(plan.get("ego_vy_norm")),
        "ego_yaw_rate_norm": _as_float(plan.get("ego_yaw_rate_norm")),
    }


def _action_from_row(row: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            _finite_float(row.get("first_steer")),
            _finite_float(row.get("first_throttle")),
            _finite_float(row.get("first_brake")),
        ],
        dtype=np.float64,
    )


def _visible_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_vec = np.asarray(
        [
            _finite_float(left.get("ego_vx_norm")),
            _finite_float(left.get("ego_vy_norm")),
            _finite_float(left.get("ego_yaw_rate_norm")),
        ],
        dtype=np.float64,
    )
    right_vec = np.asarray(
        [
            _finite_float(right.get("ego_vx_norm")),
            _finite_float(right.get("ego_vy_norm")),
            _finite_float(right.get("ego_yaw_rate_norm")),
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(left_vec)) or not np.all(np.isfinite(right_vec)):
        return float("inf")
    return float(np.linalg.norm(left_vec - right_vec))


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


def _pair_candidate(
    *,
    pair_id: int,
    left: dict[str, Any],
    right: dict[str, Any],
    strict_margin_threshold: float,
    boundary_margin_threshold: float,
) -> dict[str, Any]:
    first_action_l2 = float(np.linalg.norm(_action_from_row(left) - _action_from_row(right)))
    left_margin = _finite_float(left.get("min_clearance_margin"))
    right_margin = _finite_float(right.get("min_clearance_margin"))
    ego_distance = _visible_distance(left, right)
    obstacle_distance = _obstacle_distance(left, right)
    score = (
        max(left_margin, right_margin) if np.isfinite(left_margin) and np.isfinite(right_margin) else 999.0,
        -first_action_l2,
        ego_distance,
        obstacle_distance,
        int(left.get("candidate_id", 0)),
        int(right.get("candidate_id", 0)),
    )
    return {
        "pair_id": int(pair_id),
        "left_candidate_id": _as_int(left.get("candidate_id")),
        "right_candidate_id": _as_int(right.get("candidate_id")),
        "left_source_group_id": _as_int(left.get("source_group_id")),
        "right_source_group_id": _as_int(right.get("source_group_id")),
        "left_seed": _as_int(left.get("seed")),
        "right_seed": _as_int(right.get("seed")),
        "left_fault_family": str(left.get("preferred_fault_family", "")),
        "right_fault_family": str(right.get("preferred_fault_family", "")),
        "left_fidelity_class": str(left.get("preferred_fidelity_class", "")),
        "right_fidelity_class": str(right.get("preferred_fidelity_class", "")),
        "left_warmup_mode": str(left.get("warmup_mode", "")),
        "right_warmup_mode": str(right.get("warmup_mode", "")),
        "left_onset_bucket": str(left.get("fault_onset_bucket", "")),
        "right_onset_bucket": str(right.get("fault_onset_bucket", "")),
        "ego_response_distance": ego_distance,
        "obstacle_geometry_distance": obstacle_distance,
        "first_action_l2": first_action_l2,
        "normal_margin_gap_abs": abs(left_margin - right_margin) if np.isfinite(left_margin) and np.isfinite(right_margin) else float("nan"),
        "left_normal_margin": left_margin,
        "right_normal_margin": right_margin,
        "left_boundary_axis": str(left.get("boundary_axis", "")),
        "right_boundary_axis": str(right.get("boundary_axis", "")),
        "left_margin_band": margin_band(
            left_margin,
            strict_margin_threshold=float(strict_margin_threshold),
            boundary_margin_threshold=float(boundary_margin_threshold),
        ),
        "right_margin_band": margin_band(
            right_margin,
            strict_margin_threshold=float(strict_margin_threshold),
            boundary_margin_threshold=float(boundary_margin_threshold),
        ),
        "pair_rank_score": repr(score),
        "left_step": _as_int(left.get("step")),
        "right_step": _as_int(right.get("step")),
        "left_plan": left,
        "right_plan": right,
    }


def build_near_boundary_pairs(
    boundary_rows: list[dict[str, Any]],
    *,
    max_pairs: int,
    max_ego_distance: float,
    max_obstacle_distance: float,
    min_first_action_l2: float,
    strict_margin_threshold: float,
    boundary_margin_threshold: float,
    max_rows_per_seed: int,
    max_rows_per_source_group: int,
    max_rows_per_fault_pair: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    pair_id = 0
    rows = [
        row
        for row in boundary_rows
        if _bool(row.get("success", False))
        and not _bool(row.get("collision", False))
        and 0.0 <= _finite_float(row.get("min_clearance_margin")) <= float(boundary_margin_threshold)
    ]
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            pair = _pair_candidate(
                pair_id=pair_id,
                left=left,
                right=right,
                strict_margin_threshold=float(strict_margin_threshold),
                boundary_margin_threshold=float(boundary_margin_threshold),
            )
            pair_id += 1
            reason = ""
            if pair["left_fault_family"] == pair["right_fault_family"]:
                reason = "same_fault_family"
            elif "future_only" in {pair["left_fidelity_class"], pair["right_fidelity_class"]}:
                reason = "future_only_fidelity"
            elif _finite_float(pair["ego_response_distance"], default=999.0) > float(max_ego_distance):
                reason = "visible_distance_too_large"
            elif _finite_float(pair["obstacle_geometry_distance"], default=999.0) > float(max_obstacle_distance):
                reason = "obstacle_distance_too_large"
            elif _finite_float(pair["first_action_l2"], default=0.0) < float(min_first_action_l2):
                reason = "action_gap_too_small"
            if reason:
                rejected.append({**{key: pair.get(key, "") for key in NEAR_BOUNDARY_PAIR_FIELDS}, "rejection_reason": reason})
                continue
            candidates.append(pair)
    candidates.sort(
        key=lambda row: (
            0 if str(row.get("left_margin_band")) == "ultra_strict_0_005" or str(row.get("right_margin_band")) == "ultra_strict_0_005" else 1,
            max(_finite_float(row.get("left_normal_margin")), _finite_float(row.get("right_normal_margin"))),
            -_finite_float(row.get("first_action_l2"), default=0.0),
            _finite_float(row.get("ego_response_distance"), default=999.0),
            _finite_float(row.get("obstacle_geometry_distance"), default=999.0),
        )
    )
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    for pair in candidates:
        fault_pair = f"{pair['left_fault_family']}->{pair['right_fault_family']}"
        keys = [
            (("left_seed", str(pair["left_seed"])), int(max_rows_per_seed)),
            (("right_seed", str(pair["right_seed"])), int(max_rows_per_seed)),
            (("left_source_group_id", str(pair["left_source_group_id"])), int(max_rows_per_source_group)),
            (("right_source_group_id", str(pair["right_source_group_id"])), int(max_rows_per_source_group)),
            (("fault_pair", fault_pair), int(max_rows_per_fault_pair)),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in keys):
            rejected.append({**{key: pair.get(key, "") for key in NEAR_BOUNDARY_PAIR_FIELDS}, "rejection_reason": "source_balance_limit"})
            continue
        selected.append(pair)
        for key, _limit in keys:
            counts[key] = counts.get(key, 0) + 1
        if len(selected) >= int(max_pairs):
            break
    return selected, rejected


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
            "gate_name": "near_boundary_pair_rows",
            "value": summary["near_boundary_pair_rows"],
            "threshold": summary["min_pair_rows"],
            "passed": int(summary["near_boundary_pair_rows"]) >= int(summary["min_pair_rows"]),
            "notes": "pairs are mined after boundary bracketing",
        },
        {
            "gate_name": "primary_wrong_history_rows",
            "value": summary["accepted_primary_wrong_history_rows"],
            "threshold": summary["min_primary_rows"],
            "passed": int(summary["accepted_primary_wrong_history_rows"]) >= int(summary["min_primary_rows"]),
            "notes": "zero-command evidence counted separately",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M832 cannot promote",
        },
    ]


def _classification(
    *,
    actor_changed: bool,
    residual_changed: bool,
    boundary_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    accepted_primary: list[dict[str, Any]],
    zero_command_accepted_like: list[dict[str, Any]],
    min_pair_rows: int,
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
        return "v4_near_boundary_wrong_history_pair_mining_contract_violation"
    if not boundary_rows:
        return "v4_near_boundary_wrong_history_pair_mining_boundary_sparse"
    if len(pair_rows) < int(min_pair_rows):
        return "v4_near_boundary_wrong_history_pair_mining_pair_sparse"
    if not accepted_primary and zero_command_accepted_like:
        return "v4_near_boundary_wrong_history_pair_mining_zero_command_dominated"
    if not accepted_primary:
        return "v4_near_boundary_wrong_history_pair_mining_history_insensitive"
    metrics = _diversity(accepted_primary)
    passed = bool(
        len(accepted_primary) >= int(min_primary_rows)
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
        return "v4_near_boundary_wrong_history_pair_mining_pass"
    return "v4_near_boundary_wrong_history_pair_mining_sparse_positive"


def run_near_boundary_wrong_history_pair_mining(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_source_snapshots: int,
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
    max_ego_distance: float,
    max_obstacle_distance: float,
    min_first_action_l2: float,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    min_pair_rows: int,
    min_primary_rows: int,
    min_left_seeds: int,
    min_right_seeds: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    max_seed_dominance: float,
    max_source_group_dominance: float,
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
        raise ValueError("M832 near-boundary wrong-history mining requires an online recurrent checkpoint")
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
    identity_gate = IdentityResidualGate().to(resolved_device)

    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    source_rows = read_csv_rows(source_rows_path)
    plan_rows = read_csv_rows(candidate_plan_rows_path)
    requests = source_requests_from_plan_rows(plan_rows, max_source_snapshots=int(max_source_snapshots))
    plan_by_key = _plan_by_source_step(plan_rows)
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=requests,
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

    boundary_rows: list[dict[str, Any]] = []
    accepted_boundary_rows: list[dict[str, Any]] = []
    rejected_boundary_rows: list[dict[str, Any]] = [copy.deepcopy(row) for row in snapshot_rejections]
    bracket_id = 0
    candidate_id = 0
    source_index = 0
    for key, snapshot in sorted(snapshots.items()):
        plan = plan_by_key.get(key)
        if plan is None:
            rejected_boundary_rows.append({"source_group_id": key[0], "step": key[1], "boundary_axis": "", "rejection_reason": "missing_plan_row", "evaluations": 0})
            continue
        source_meta = _source_meta_from_plan(plan, source_index=source_index, fault_by_name=fault_by_name, warmup_steps=int(warmup_steps))
        source_index += 1
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
                rejected_boundary_rows.append(
                    {
                        "source_group_id": int(source_meta["source_group_id"]),
                        "step": int(source_meta["step"]),
                        "boundary_axis": axis,
                        "rejection_reason": "no_collision_safe_bracket",
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
            for row in accepted_rows:
                margin = _finite_float(row.get("min_clearance_margin"))
                row["horizon"] = int(horizon)
                row["margin_band"] = margin_band(
                    margin,
                    strict_margin_threshold=float(strict_margin_threshold),
                    boundary_margin_threshold=float(boundary_margin_threshold),
                )
            accepted_boundary_rows.extend(accepted_rows)
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

    near_pairs, rejected_pairs = build_near_boundary_pairs(
        accepted_boundary_rows,
        max_pairs=int(max_pairs),
        max_ego_distance=float(max_ego_distance),
        max_obstacle_distance=float(max_obstacle_distance),
        min_first_action_l2=float(min_first_action_l2),
        strict_margin_threshold=float(strict_margin_threshold),
        boundary_margin_threshold=float(boundary_margin_threshold),
        max_rows_per_seed=max(1, int(np.floor(float(max_seed_dominance) * float(max_pairs)))),
        max_rows_per_source_group=max(1, int(np.floor(float(max_source_group_dominance) * float(max_pairs)))),
        max_rows_per_fault_pair=max(1, int(np.floor(float(max_fault_pair_dominance) * float(max_pairs)))),
    )

    replay_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    for pair in near_pairs:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**{key: pair.get(key, "") for key in NEAR_BOUNDARY_PAIR_FIELDS}, "rejection_reason": "missing_reconstructed_snapshot"})
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
            replay_rejections.append({**{key: pair.get(key, "") for key in NEAR_BOUNDARY_PAIR_FIELDS}, "rejection_reason": f"replay_error:{type(exc).__name__}"})
            continue
        replay_rows.extend(rows)
        accepted_rows.extend(
            accepted_wrong_history_rows_for_pair(
                rows,
                primary_margin_gap_threshold=float(primary_margin_gap_threshold),
                mitigation_margin_gap_threshold=float(mitigation_margin_gap_threshold),
                action_l2_threshold=float(action_l2_threshold),
                require_closer_to_right=True,
            )
        )
        _append_progress(
            progress_path,
            {
                "stage": "wrong_history_replay",
                "pair_id": int(pair["pair_id"]),
                "rows": len(rows),
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

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = _classification(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        boundary_rows=accepted_boundary_rows,
        pair_rows=near_pairs,
        accepted_primary=accepted_primary,
        zero_command_accepted_like=zero_command_accepted_like,
        min_pair_rows=int(min_pair_rows),
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
        "accepted_boundary_rows": {
            "rows": int(len(accepted_boundary_rows)),
            "unique_seed_count": unique_count(accepted_boundary_rows, "seed"),
            "unique_source_group_count": unique_count(accepted_boundary_rows, "source_group_id"),
            "unique_fault_family_pair_count": unique_count(accepted_boundary_rows, "fault_family_pair"),
            "unique_warmup_mode_count": unique_count(accepted_boundary_rows, "warmup_mode"),
            "unique_boundary_axis_count": unique_count(accepted_boundary_rows, "boundary_axis"),
            "max_seed_dominance": max_share(accepted_boundary_rows, "seed"),
            "max_source_group_dominance": max_share(accepted_boundary_rows, "source_group_id"),
            "max_fault_pair_dominance": max_share(accepted_boundary_rows, "fault_family_pair"),
            "max_boundary_axis_dominance": max_share(accepted_boundary_rows, "boundary_axis"),
        },
        "near_boundary_pairs": _diversity(near_pairs),
        "accepted_primary_wrong_history": _diversity(accepted_primary),
        "accepted_mitigation_wrong_history": _diversity(accepted_mitigation),
        "zero_command_accepted_like": _diversity(zero_command_accepted_like),
    }

    all_pair_rejections = [*rejected_pairs, *replay_rejections]
    write_csv_rows(run_dir / "boundary_source_rows.csv", snapshot_rows, fieldnames=BOUNDARY_SOURCE_FIELDS)
    write_csv_rows(run_dir / "boundary_replay_rows.csv", boundary_rows, fieldnames=BOUNDARY_REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_boundary_rows.csv", accepted_boundary_rows, fieldnames=BOUNDARY_REPLAY_FIELDS)
    write_csv_rows(run_dir / "near_boundary_pair_rows.csv", [{k: row.get(k, "") for k in NEAR_BOUNDARY_PAIR_FIELDS} for row in near_pairs], fieldnames=NEAR_BOUNDARY_PAIR_FIELDS)
    write_csv_rows(run_dir / "wrong_history_replay_rows.csv", replay_rows, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_primary_wrong_history_rows.csv", accepted_primary, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_mitigation_rows.csv", accepted_mitigation, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "rejected_boundary_rows.csv", rejected_boundary_rows, fieldnames=REJECTED_BOUNDARY_FIELDS)
    write_csv_rows(run_dir / "rejected_pair_rows.csv", all_pair_rejections, fieldnames=REJECTED_PAIR_FIELDS)
    write_json(run_dir / "diversity_summary.json", diversity_summary)
    (run_dir / "fault_proxy_limitations.md").write_text(
        "M832 uses current-model and current-model-proxy faults only. Proxy rows are not true wheel-level physical claims.\n",
        encoding="utf-8",
    )

    boundary_margins = [_finite_float(row.get("min_clearance_margin")) for row in accepted_boundary_rows]
    summary = {
        "run_type": "v4_near_boundary_wrong_history_pair_mining",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "max_source_snapshots": int(max_source_snapshots),
        "source_requests": int(len(requests)),
        "reconstructed_snapshot_rows": int(len(snapshot_rows)),
        "boundary_replay_rows": int(len(boundary_rows)),
        "accepted_boundary_rows": int(len(accepted_boundary_rows)),
        "boundary_margin_min": float(np.min(boundary_margins)) if boundary_margins else None,
        "boundary_margin_median": float(np.median(boundary_margins)) if boundary_margins else None,
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "strict_margin_threshold": float(strict_margin_threshold),
        "near_boundary_pair_rows": int(len(near_pairs)),
        "wrong_history_replay_rows": int(len(replay_rows)),
        "accepted_primary_wrong_history_rows": int(len(accepted_primary)),
        "accepted_mitigation_rows": int(len(accepted_mitigation)),
        "zero_command_accepted_like_rows": int(len(zero_command_accepted_like)),
        "rejected_boundary_rows": int(len(rejected_boundary_rows)),
        "rejected_pair_rows": int(len(all_pair_rejections)),
        "min_pair_rows": int(min_pair_rows),
        "min_primary_rows": int(min_primary_rows),
        "primary_margin_gap_threshold": float(primary_margin_gap_threshold),
        "mitigation_margin_gap_threshold": float(mitigation_margin_gap_threshold),
        "action_l2_threshold": float(action_l2_threshold),
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
        "boundary_source_rows_csv": run_dir / "boundary_source_rows.csv",
        "boundary_replay_rows_csv": run_dir / "boundary_replay_rows.csv",
        "accepted_boundary_rows_csv": run_dir / "accepted_boundary_rows.csv",
        "near_boundary_pair_rows_csv": run_dir / "near_boundary_pair_rows.csv",
        "wrong_history_replay_rows_csv": run_dir / "wrong_history_replay_rows.csv",
        "accepted_primary_wrong_history_rows_csv": run_dir / "accepted_primary_wrong_history_rows.csv",
        "accepted_mitigation_rows_csv": run_dir / "accepted_mitigation_rows.csv",
        "rejected_boundary_rows_csv": run_dir / "rejected_boundary_rows.csv",
        "rejected_pair_rows_csv": run_dir / "rejected_pair_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "fault_proxy_limitations_md": run_dir / "fault_proxy_limitations.md",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_axis_list(value: str) -> tuple[str, ...]:
    axes = tuple(part.strip() for part in str(value).split(",") if part.strip())
    unknown = [axis for axis in axes if axis not in BOUNDARY_AXES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown boundary axes: {unknown}")
    return axes


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 near-boundary wrong-history pair mining.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-source-snapshots", type=int, default=64)
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
    parser.add_argument("--max-ego-distance", type=float, default=0.25)
    parser.add_argument("--max-obstacle-distance", type=float, default=0.08)
    parser.add_argument("--min-first-action-l2", type=float, default=0.014)
    parser.add_argument("--primary-margin-gap-threshold", type=float, default=0.01)
    parser.add_argument("--mitigation-margin-gap-threshold", type=float, default=0.02)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--min-pair-rows", type=int, default=80)
    parser.add_argument("--min-primary-rows", type=int, default=80)
    parser.add_argument("--min-left-seeds", type=int, default=8)
    parser.add_argument("--min-right-seeds", type=int, default=8)
    parser.add_argument("--min-fault-pairs", type=int, default=6)
    parser.add_argument("--min-warmup-pairs", type=int, default=2)
    parser.add_argument("--min-onset-pairs", type=int, default=3)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-source-group-dominance", type=float, default=0.15)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.35)
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
    summary = run_near_boundary_wrong_history_pair_mining(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_source_snapshots=int(args.max_source_snapshots),
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
        max_ego_distance=float(args.max_ego_distance),
        max_obstacle_distance=float(args.max_obstacle_distance),
        min_first_action_l2=float(args.min_first_action_l2),
        primary_margin_gap_threshold=float(args.primary_margin_gap_threshold),
        mitigation_margin_gap_threshold=float(args.mitigation_margin_gap_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        min_pair_rows=int(args.min_pair_rows),
        min_primary_rows=int(args.min_primary_rows),
        min_left_seeds=int(args.min_left_seeds),
        min_right_seeds=int(args.min_right_seeds),
        min_fault_pairs=int(args.min_fault_pairs),
        min_warmup_pairs=int(args.min_warmup_pairs),
        min_onset_pairs=int(args.min_onset_pairs),
        max_seed_dominance=float(args.max_seed_dominance),
        max_source_group_dominance=float(args.max_source_group_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
