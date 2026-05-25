"""No-training boundary-preserving pair-delta refresh for missing seeds."""

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
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import relocate_temporal_snapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_extreme_hidden_dynamics_data_route import IdentityResidualGate
from autodrift.v4_generated_boundary_pair_delta_coverage_expansion import (
    COVERAGE_ACCEPTED_FIELDS,
    COVERAGE_SEQUENCE_FIELDS,
    _coverage_meta,
    _strip_plans,
    balance_coverage_pair_delta_rows,
    pair_rows_from_target_rows,
)
from autodrift.v4_generated_boundary_pair_delta_refresh import _extended_sequence_diversity, _m867_acceptance_class
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_sequence_effectiveness_probe import (
    accepted_sequence_effective_rows_for_pair,
    replay_normal,
    replay_sequence_effectiveness_pair,
)
from autodrift.v4_pair_delta_focused_source_balanced_mining import COMPONENT_DIRECTIONS, PAIR_DELTA_DIRECTIONS, split_source_aware
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _as_int,
    read_csv_rows,
    reconstruct_snapshots,
)


MISSING_ACCEPTED_SEEDS = ("78048", "78055", "78057")

M873_EXTRA_FIELDS = [
    "normal_boundary_source",
    "normal_candidate_id",
    "normal_boundary_class",
    "retarget_axis",
    "retarget_delta",
    "retarget_target_body_x",
    "retarget_target_body_y",
    "retarget_target_half_width",
    "target_rank",
    "target_seed",
    "target_best_abs_margin_delta",
    "target_best_direction",
    "target_best_hold_steps",
    "target_best_epsilon_l2",
]
NORMAL_BOUNDARY_FIELDS = [
    *M873_EXTRA_FIELDS,
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
    "left_step",
    "right_step",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "normal_return",
    "terminal_reason",
    "steps",
]
M873_SEQUENCE_FIELDS = [*COVERAGE_SEQUENCE_FIELDS, *[field for field in M873_EXTRA_FIELDS if field not in COVERAGE_SEQUENCE_FIELDS]]
M873_ACCEPTED_FIELDS = [*COVERAGE_ACCEPTED_FIELDS, *[field for field in M873_EXTRA_FIELDS if field not in COVERAGE_ACCEPTED_FIELDS]]
M873_SPLIT_FIELDS = [*M873_ACCEPTED_FIELDS, "split"]


def classify_normal_boundary_row(
    *,
    success: bool,
    collision: bool,
    margin: float,
    boundary_margin_threshold: float,
) -> str:
    """Classify a normal-only replay row before pair-delta replay."""

    if not np.isfinite(margin):
        return "nonfinite"
    if bool(success) and not bool(collision) and 0.0 <= float(margin) <= float(boundary_margin_threshold):
        return "accepted_window"
    if bool(success) and not bool(collision) and float(margin) > float(boundary_margin_threshold):
        return "wide_safe"
    return "collision_or_negative"


def retargeted_left_plan(pair: dict[str, Any], *, axis: str, delta: float) -> tuple[dict[str, Any], dict[str, float]]:
    left_plan = dict(pair["left_plan"])
    base_x = _finite_float(left_plan.get("target_obstacle_body_x"))
    base_y = _finite_float(left_plan.get("target_obstacle_body_y"))
    base_width = _finite_float(left_plan.get("target_obstacle_half_width"))
    body_x = base_x
    body_y = base_y
    half_width = base_width
    if axis == "obstacle_lateral_offset":
        body_y = base_y + float(delta)
    elif axis == "obstacle_timing":
        body_x = max(1.0, base_x + float(delta))
    elif axis == "obstacle_half_width":
        half_width = max(0.1, base_width + float(delta))
    else:
        raise ValueError(f"unsupported retarget axis: {axis}")
    left_plan["target_obstacle_body_x"] = float(body_x)
    left_plan["target_obstacle_body_y"] = float(body_y)
    left_plan["target_obstacle_half_width"] = float(half_width)
    return left_plan, {
        "retarget_target_body_x": float(body_x),
        "retarget_target_body_y": float(body_y),
        "retarget_target_half_width": float(half_width),
    }


def make_normal_candidate_pair(
    pair: dict[str, Any],
    *,
    normal_candidate_id: int,
    axis: str,
    delta: float,
    source: str,
) -> dict[str, Any]:
    left_plan, target = retargeted_left_plan(pair, axis=axis, delta=float(delta))
    return {
        **pair,
        "pair_id": int(pair["pair_id"]) * 10000 + int(normal_candidate_id),
        "normal_candidate_id": int(normal_candidate_id),
        "normal_boundary_source": source,
        "normal_boundary_class": "",
        "retarget_axis": axis,
        "retarget_delta": float(delta),
        **target,
        "left_plan": left_plan,
    }


def _normal_meta(pair: dict[str, Any]) -> dict[str, Any]:
    return {key: pair.get(key, "") for key in M873_EXTRA_FIELDS}


def evaluate_normal_candidate(
    *,
    pair: dict[str, Any],
    left_snapshot: Any,
    model: Any,
    residual_head: Any,
    identity_gate: Any,
    env_config: Any,
    max_continuation_steps: int,
    alpha: float,
    boundary_margin_threshold: float,
    device: Any,
) -> dict[str, Any]:
    left_plan = pair["left_plan"]
    relocated = relocate_temporal_snapshot(
        left_snapshot,
        body_longitudinal=_finite_float(left_plan.get("target_obstacle_body_x")),
        body_lateral=_finite_float(left_plan.get("target_obstacle_body_y")),
        half_width=_finite_float(left_plan.get("target_obstacle_half_width")),
    )
    normal, _actions = replay_normal(
        model=model,
        residual_head=residual_head,
        identity_gate=identity_gate,
        snapshot=relocated,
        env_config=env_config,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(alpha),
        device=device,
    )
    margin = _finite_float(normal.get("min_clearance_margin"))
    success = parse_bool(normal.get("success", False))
    collision = parse_bool(normal.get("collision", False))
    boundary_class = classify_normal_boundary_row(
        success=success,
        collision=collision,
        margin=margin,
        boundary_margin_threshold=float(boundary_margin_threshold),
    )
    pair["normal_boundary_class"] = boundary_class
    return {
        **_normal_meta(pair),
        **{key: pair.get(key, "") for key in NORMAL_BOUNDARY_FIELDS if key in pair},
        "normal_boundary_class": boundary_class,
        "normal_success": success,
        "normal_collision": collision,
        "normal_margin": margin,
        "normal_return": _finite_float(normal.get("return")),
        "terminal_reason": str(normal.get("terminal_reason", "")),
        "steps": _as_int(normal.get("steps"), 0),
    }


def _retarget_param(row: dict[str, Any]) -> float:
    axis = str(row.get("retarget_axis", ""))
    if axis == "obstacle_lateral_offset":
        return _finite_float(row.get("retarget_target_body_y"))
    if axis == "obstacle_timing":
        return _finite_float(row.get("retarget_target_body_x"))
    if axis == "obstacle_half_width":
        return _finite_float(row.get("retarget_target_half_width"))
    return float("nan")


def _delta_from_param(pair: dict[str, Any], *, axis: str, param: float) -> float:
    left_plan = pair["left_plan"]
    if axis == "obstacle_lateral_offset":
        return float(param) - _finite_float(left_plan.get("target_obstacle_body_y"))
    if axis == "obstacle_timing":
        return float(param) - _finite_float(left_plan.get("target_obstacle_body_x"))
    if axis == "obstacle_half_width":
        return float(param) - _finite_float(left_plan.get("target_obstacle_half_width"))
    raise ValueError(f"unsupported retarget axis: {axis}")


def select_normal_boundary_candidates(
    rows_and_pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    max_rows: int,
    max_rows_per_seed: int,
    max_rows_per_axis: int,
) -> list[dict[str, Any]]:
    """Select accepted normal-window candidates with seed/axis balance."""

    accepted = [
        (row, pair)
        for row, pair in rows_and_pairs
        if str(row.get("normal_boundary_class", "")) == "accepted_window"
    ]
    ordered = sorted(
        accepted,
        key=lambda item: (
            _finite_float(item[0].get("normal_margin"), default=999.0),
            str(item[0].get("left_seed", "")),
            str(item[0].get("retarget_axis", "")),
            _as_int(item[0].get("normal_candidate_id")),
        ),
    )
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    for row, pair in ordered:
        keys = [
            (("left_seed", str(row.get("left_seed", ""))), int(max_rows_per_seed)),
            (("retarget_axis", str(row.get("retarget_axis", ""))), int(max_rows_per_axis)),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in keys):
            continue
        selected.append(pair)
        for key, _limit in keys:
            counts[key] = counts.get(key, 0) + 1
        if len(selected) >= int(max_rows):
            break
    return selected


def _dominance(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row.get(key, ""))] = counts.get(str(row.get(key, "")), 0) + 1
    return max(counts.values(), default=0) / float(len(rows))


def _normal_boundary_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "unique_left_seed_count": len({str(row.get("left_seed", "")) for row in rows}),
        "unique_left_source_group_count": len({str(row.get("left_source_group_id", "")) for row in rows}),
        "unique_left_fault_family_count": len({str(row.get("left_fault_family", "")) for row in rows}),
        "unique_retarget_axis_count": len({str(row.get("retarget_axis", "")) for row in rows}),
        "max_left_seed_dominance": _dominance(rows, "left_seed"),
        "max_retarget_axis_dominance": _dominance(rows, "retarget_axis"),
    }


def classify_boundary_preserving_refresh(
    *,
    actor_changed: bool,
    residual_changed: bool,
    target_weak_seed_rows: int,
    normal_boundary_candidate_rows: list[dict[str, Any]],
    pair_delta_sequence_rows: list[dict[str, Any]],
    new_accepted_pair_delta_rows: list[dict[str, Any]],
    balanced_pair_delta_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    min_target_rows: int,
    min_normal_boundary_rows: int,
    min_normal_boundary_seeds: int,
    min_new_accepted_rows: int,
    min_balanced_rows: int,
    min_balanced_seeds: int,
    min_balanced_sources: int,
    min_balanced_fault_families: int,
    min_balanced_fault_pairs: int,
    max_seed_dominance: float,
    max_direction_dominance: float,
    max_axis_pair_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_boundary_preserving_missing_seed_pair_delta_refresh_contract_violation"
    normal_metrics = _normal_boundary_diversity(normal_boundary_candidate_rows)
    if (
        int(target_weak_seed_rows) < int(min_target_rows)
        or len(normal_boundary_candidate_rows) < int(min_normal_boundary_rows)
        or normal_metrics["unique_left_seed_count"] < int(min_normal_boundary_seeds)
        or not pair_delta_sequence_rows
    ):
        return "v4_boundary_preserving_missing_seed_pair_delta_refresh_normal_boundary_limited"
    balanced_metrics = _extended_sequence_diversity(balanced_pair_delta_rows)
    primary = bool(
        len(new_accepted_pair_delta_rows) >= int(min_new_accepted_rows)
        and len(balanced_pair_delta_rows) >= int(min_balanced_rows)
        and balanced_metrics["unique_left_seed_count"] >= int(min_balanced_seeds)
        and balanced_metrics["unique_left_source_group_count"] >= int(min_balanced_sources)
        and balanced_metrics["unique_left_fault_family_count"] >= int(min_balanced_fault_families)
        and balanced_metrics["unique_fault_family_pair_count"] >= int(min_balanced_fault_pairs)
        and balanced_metrics["unique_direction_count"] >= 2
        and balanced_metrics["unique_axis_pair_count"] >= 2
        and balanced_metrics["max_left_seed_dominance"] <= float(max_seed_dominance)
        and balanced_metrics["max_direction_dominance"] <= float(max_direction_dominance)
        and balanced_metrics["max_axis_pair_dominance"] <= float(max_axis_pair_dominance)
    )
    if primary:
        return "v4_boundary_preserving_missing_seed_pair_delta_refresh_pass"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in pair_delta_sequence_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in pair_delta_sequence_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    if len(new_accepted_pair_delta_rows) < 10 and ((not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0):
        return "v4_boundary_preserving_missing_seed_pair_delta_refresh_all_weak"
    return "v4_boundary_preserving_missing_seed_pair_delta_refresh_source_limited"


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
            "gate_name": "normal_boundary_candidate_rows",
            "value": summary["normal_boundary_candidate_rows"],
            "threshold": summary["min_normal_boundary_rows"],
            "passed": int(summary["normal_boundary_candidate_rows"]) >= int(summary["min_normal_boundary_rows"]),
            "notes": "normal branch must be accepted before pair-delta replay",
        },
        {
            "gate_name": "normal_boundary_seed_diversity",
            "value": summary["normal_boundary_unique_left_seed_count"],
            "threshold": summary["min_normal_boundary_seeds"],
            "passed": int(summary["normal_boundary_unique_left_seed_count"]) >= int(summary["min_normal_boundary_seeds"]),
            "notes": "missing-seed boundary coverage",
        },
        {
            "gate_name": "new_accepted_pair_delta_rows",
            "value": summary["new_accepted_pair_delta_rows"],
            "threshold": summary["min_new_accepted_rows"],
            "passed": int(summary["new_accepted_pair_delta_rows"]) >= int(summary["min_new_accepted_rows"]),
            "notes": "new pair-delta outcome evidence",
        },
        {
            "gate_name": "balanced_left_seed_diversity",
            "value": summary["balanced_unique_left_seed_count"],
            "threshold": summary["min_balanced_seeds"],
            "passed": int(summary["balanced_unique_left_seed_count"]) >= int(summary["min_balanced_seeds"]),
            "notes": "balanced accepted pair-delta coverage",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M873 cannot promote",
        },
    ]


def run_boundary_preserving_refresh(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    target_weak_seed_rows_path: Path,
    combined_boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    existing_accepted_pair_delta_rows_path: Path | None,
    run_dir: Path,
    device: str,
    alpha: float,
    max_targets_per_seed: int,
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
    lateral_deltas: tuple[float, ...],
    timing_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    max_refine_iters: int,
    epsilon_grid: tuple[float, ...],
    hold_steps_grid: tuple[int, ...],
    boundary_margin_threshold: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
    min_target_rows: int,
    min_normal_boundary_rows: int,
    min_normal_boundary_seeds: int,
    min_new_accepted_rows: int,
    min_balanced_rows: int,
    min_balanced_seeds: int,
    min_balanced_sources: int,
    min_balanced_fault_families: int,
    min_balanced_fault_pairs: int,
    max_seed_dominance: float,
    max_direction_dominance: float,
    max_axis_pair_dominance: float,
    max_pair_delta_candidates: int,
    max_normal_rows_per_seed: int,
    max_normal_rows_per_axis: int,
    max_balanced_rows: int,
    max_rows_per_left_seed: int,
    max_rows_per_left_source_group: int,
    max_rows_per_fault_family_pair: int,
    max_rows_per_direction: int,
    max_rows_per_axis_pair: int,
    component_control_max_pairs: int,
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
        raise ValueError("M873 boundary-preserving refresh requires an online recurrent checkpoint")
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

    target_rows_all = read_csv_rows(target_weak_seed_rows_path)
    target_rows: list[dict[str, Any]] = []
    counts_by_seed: dict[str, int] = {}
    for row in target_rows_all:
        seed = str(row.get("left_seed", ""))
        if seed not in MISSING_ACCEPTED_SEEDS:
            continue
        if counts_by_seed.get(seed, 0) >= int(max_targets_per_seed):
            continue
        target_rows.append(row)
        counts_by_seed[seed] = counts_by_seed.get(seed, 0) + 1
    combined_boundary_rows = read_csv_rows(combined_boundary_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    _candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    existing_accepted_rows = (
        [{**row, "coverage_source": row.get("coverage_source") or "existing_pair_delta"} for row in read_csv_rows(existing_accepted_pair_delta_rows_path)]
        if existing_accepted_pair_delta_rows_path is not None and existing_accepted_pair_delta_rows_path.exists()
        else []
    )
    target_pair_rows, target_rejections = pair_rows_from_target_rows(
        target_rows,
        combined_boundary_rows,
        boundary_margin_threshold=float(boundary_margin_threshold),
    )

    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=[
            {
                "left_source_group_id": int(row["left_source_group_id"]),
                "right_source_group_id": int(row["right_source_group_id"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
            }
            for row in target_pair_rows
        ],
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

    normal_trace_rows: list[dict[str, Any]] = []
    accepted_rows_and_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    normal_rejections: list[dict[str, Any]] = []
    candidate_id = 0
    axes_and_deltas = (
        ("obstacle_lateral_offset", tuple(float(value) for value in lateral_deltas)),
        ("obstacle_timing", tuple(float(value) for value in timing_deltas)),
        ("obstacle_half_width", tuple(float(value) for value in half_width_deltas)),
    )
    for pair in target_pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        if left_snapshot is None:
            normal_rejections.append({**_strip_plans(pair), "rejection_reason": "missing_left_snapshot"})
            continue
        axis_rows: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}

        def eval_candidate(axis: str, delta: float, source: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
            nonlocal candidate_id
            candidate_id += 1
            candidate = make_normal_candidate_pair(
                pair,
                normal_candidate_id=int(candidate_id),
                axis=axis,
                delta=float(delta),
                source=source,
            )
            try:
                row = evaluate_normal_candidate(
                    pair=candidate,
                    left_snapshot=left_snapshot,
                    model=model,
                    residual_head=residual_head,
                    identity_gate=identity_gate,
                    env_config=env_config,
                    max_continuation_steps=int(max_continuation_steps),
                    alpha=float(alpha),
                    boundary_margin_threshold=float(boundary_margin_threshold),
                    device=resolved_device,
                )
            except Exception as exc:
                normal_rejections.append({**_strip_plans(candidate), "rejection_reason": f"normal_boundary_error:{type(exc).__name__}"})
                return None
            normal_trace_rows.append(row)
            if str(row.get("normal_boundary_class", "")) == "accepted_window":
                accepted_rows_and_pairs.append((row, candidate))
            _append_progress(progress_path, {"stage": "normal_boundary", "candidate_id": int(candidate_id), "class": row["normal_boundary_class"]})
            return row, candidate

        for axis, deltas in axes_and_deltas:
            evaluated: list[tuple[dict[str, Any], dict[str, Any]]] = []
            seen_params: set[float] = set()
            for delta in deltas:
                result = eval_candidate(axis, float(delta), "initial_grid")
                if result is None:
                    continue
                row, _candidate = result
                param = _retarget_param(row)
                if np.isfinite(param):
                    seen_params.add(round(float(param), 9))
                evaluated.append(result)
            evaluated.sort(key=lambda item: _retarget_param(item[0]))
            axis_rows[axis] = evaluated
            for left, right in zip(evaluated, evaluated[1:]):
                left_class = str(left[0].get("normal_boundary_class", ""))
                right_class = str(right[0].get("normal_boundary_class", ""))
                classes = {left_class, right_class}
                if "wide_safe" not in classes or "collision_or_negative" not in classes:
                    continue
                lo = _retarget_param(left[0])
                hi = _retarget_param(right[0])
                if not np.isfinite(lo) or not np.isfinite(hi) or lo == hi:
                    continue
                for _iter_index in range(int(max_refine_iters)):
                    mid = 0.5 * (float(lo) + float(hi))
                    rounded = round(mid, 9)
                    if rounded in seen_params:
                        break
                    seen_params.add(rounded)
                    delta = _delta_from_param(pair, axis=axis, param=mid)
                    refined = eval_candidate(axis, float(delta), "bracket_refine")
                    if refined is None:
                        break
                    refined_row, _refined_candidate = refined
                    refined_class = str(refined_row.get("normal_boundary_class", ""))
                    if refined_class == "accepted_window":
                        break
                    if refined_class == "wide_safe":
                        if left_class == "wide_safe":
                            lo = mid
                        else:
                            hi = mid
                    elif refined_class == "collision_or_negative":
                        if left_class == "collision_or_negative":
                            lo = mid
                        else:
                            hi = mid
                    else:
                        break

    normal_boundary_candidate_rows = [row for row, _pair in accepted_rows_and_pairs]
    pair_delta_candidates = select_normal_boundary_candidates(
        accepted_rows_and_pairs,
        max_rows=int(max_pair_delta_candidates),
        max_rows_per_seed=int(max_normal_rows_per_seed),
        max_rows_per_axis=int(max_normal_rows_per_axis),
    )

    sequence_rows: list[dict[str, Any]] = []
    new_accepted_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    pair_by_id: dict[str, dict[str, Any]] = {}
    for pair in pair_delta_candidates:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**_strip_plans(pair), "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        pair_by_id[str(pair["pair_id"])] = pair
        try:
            rows = replay_sequence_effectiveness_pair(
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
                hold_steps_grid=tuple(int(value) for value in hold_steps_grid),
                directions=PAIR_DELTA_DIRECTIONS,
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**_strip_plans(pair), "rejection_reason": f"pair_delta_replay_error:{type(exc).__name__}"})
            continue
        meta = {**_coverage_meta(pair, source="m873_boundary_preserving"), **_normal_meta(pair)}
        for row in rows:
            sequence_rows.append({**row, **meta})
        accepted = accepted_sequence_effective_rows_for_pair(
            rows,
            boundary_margin_threshold=float(boundary_margin_threshold),
            margin_delta_threshold=float(margin_delta_threshold),
            action_l2_threshold=float(action_l2_threshold),
        )
        new_accepted_rows.extend({**_m867_acceptance_class(row), **meta} for row in accepted if str(row.get("direction_family", "")) == "pair_delta")
        _append_progress(progress_path, {"stage": "pair_delta_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)})

    combined_accepted_rows = [*existing_accepted_rows, *new_accepted_rows]
    balanced_rows = balance_coverage_pair_delta_rows(
        combined_accepted_rows,
        max_rows=int(max_balanced_rows),
        max_rows_per_left_seed=int(max_rows_per_left_seed),
        max_rows_per_left_source_group=int(max_rows_per_left_source_group),
        max_rows_per_fault_family_pair=int(max_rows_per_fault_family_pair),
        max_rows_per_direction=int(max_rows_per_direction),
        max_rows_per_axis_pair=int(max_rows_per_axis_pair),
    )
    train_rows, eval_rows, holdout_rows = split_source_aware(balanced_rows)

    component_control_rows: list[dict[str, Any]] = []
    component_pair_ids: list[str] = []
    for row in new_accepted_rows:
        pair_id = str(row.get("pair_id", ""))
        if pair_id and pair_id not in component_pair_ids:
            component_pair_ids.append(pair_id)
        if len(component_pair_ids) >= int(component_control_max_pairs):
            break
    for pair_id in component_pair_ids:
        pair = pair_by_id.get(pair_id)
        if pair is None:
            continue
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            continue
        try:
            rows = replay_sequence_effectiveness_pair(
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
                hold_steps_grid=tuple(int(value) for value in hold_steps_grid),
                directions=COMPONENT_DIRECTIONS,
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**_strip_plans(pair), "rejection_reason": f"component_control_error:{type(exc).__name__}"})
            continue
        meta = {**_coverage_meta(pair, source="m873_component_control"), **_normal_meta(pair)}
        component_control_rows.extend({**row, **meta} for row in rows)

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_boundary_preserving_refresh(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        target_weak_seed_rows=len(target_rows),
        normal_boundary_candidate_rows=normal_boundary_candidate_rows,
        pair_delta_sequence_rows=sequence_rows,
        new_accepted_pair_delta_rows=new_accepted_rows,
        balanced_pair_delta_rows=balanced_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        min_target_rows=int(min_target_rows),
        min_normal_boundary_rows=int(min_normal_boundary_rows),
        min_normal_boundary_seeds=int(min_normal_boundary_seeds),
        min_new_accepted_rows=int(min_new_accepted_rows),
        min_balanced_rows=int(min_balanced_rows),
        min_balanced_seeds=int(min_balanced_seeds),
        min_balanced_sources=int(min_balanced_sources),
        min_balanced_fault_families=int(min_balanced_fault_families),
        min_balanced_fault_pairs=int(min_balanced_fault_pairs),
        max_seed_dominance=float(max_seed_dominance),
        max_direction_dominance=float(max_direction_dominance),
        max_axis_pair_dominance=float(max_axis_pair_dominance),
    )

    normal_metrics = _normal_boundary_diversity(normal_boundary_candidate_rows)
    balanced_metrics = _extended_sequence_diversity(balanced_rows)
    new_metrics = _extended_sequence_diversity(new_accepted_rows)
    sequence_metrics = _extended_sequence_diversity(sequence_rows)
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in sequence_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    diversity_summary = {
        "normal_boundary_candidate": normal_metrics,
        "pair_delta_sequence": sequence_metrics,
        "new_accepted_pair_delta": new_metrics,
        "combined_accepted_pair_delta": _extended_sequence_diversity(combined_accepted_rows),
        "balanced_pair_delta": balanced_metrics,
        "component_control_rows": _extended_sequence_diversity(component_control_rows),
        "train_public": _extended_sequence_diversity(train_rows),
        "eval_public": _extended_sequence_diversity(eval_rows),
        "source_holdout_public": _extended_sequence_diversity(holdout_rows),
    }

    write_csv_rows(run_dir / "target_weak_seed_rows.csv", target_rows)
    write_csv_rows(run_dir / "normal_boundary_trace_rows.csv", normal_trace_rows, fieldnames=NORMAL_BOUNDARY_FIELDS)
    write_csv_rows(run_dir / "normal_boundary_candidate_rows.csv", normal_boundary_candidate_rows, fieldnames=NORMAL_BOUNDARY_FIELDS)
    write_csv_rows(run_dir / "normal_boundary_rejected_rows.csv", [*target_rejections, *snapshot_rejections, *normal_rejections])
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "pair_delta_candidate_rows.csv", [_strip_plans(row) for row in pair_delta_candidates])
    write_csv_rows(run_dir / "pair_delta_sequence_rows.csv", sequence_rows, fieldnames=M873_SEQUENCE_FIELDS)
    write_csv_rows(run_dir / "new_accepted_pair_delta_rows.csv", new_accepted_rows, fieldnames=M873_ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_pair_delta_rows.csv", combined_accepted_rows, fieldnames=M873_ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "balanced_pair_delta_rows.csv", balanced_rows, fieldnames=M873_ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "component_control_rows.csv", component_control_rows, fieldnames=M873_SEQUENCE_FIELDS)
    write_csv_rows(run_dir / "train_public_rows.csv", train_rows, fieldnames=M873_SPLIT_FIELDS)
    write_csv_rows(run_dir / "eval_public_rows.csv", eval_rows, fieldnames=M873_SPLIT_FIELDS)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", holdout_rows, fieldnames=M873_SPLIT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", [*target_rejections, *snapshot_rejections, *normal_rejections, *replay_rejections])
    write_json(run_dir / "normal_boundary_summary.json", normal_metrics)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    summary = {
        "run_type": "v4_boundary_preserving_missing_seed_pair_delta_refresh",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "target_weak_seed_rows_path": target_weak_seed_rows_path,
        "combined_boundary_rows": combined_boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "existing_accepted_pair_delta_rows": existing_accepted_pair_delta_rows_path,
        "alpha": float(alpha),
        "target_weak_seed_rows": int(len(target_rows)),
        "target_pair_rows": int(len(target_pair_rows)),
        "normal_boundary_trace_rows": int(len(normal_trace_rows)),
        "normal_boundary_candidate_rows": int(len(normal_boundary_candidate_rows)),
        "normal_boundary_unique_left_seed_count": int(normal_metrics["unique_left_seed_count"]),
        "normal_boundary_unique_retarget_axis_count": int(normal_metrics["unique_retarget_axis_count"]),
        "normal_boundary_max_left_seed_dominance": float(normal_metrics["max_left_seed_dominance"]),
        "pair_delta_candidate_rows": int(len(pair_delta_candidates)),
        "pair_delta_sequence_rows": int(len(sequence_rows)),
        "new_accepted_pair_delta_rows": int(len(new_accepted_rows)),
        "new_accepted_unique_left_seed_count": int(new_metrics["unique_left_seed_count"]),
        "existing_accepted_pair_delta_rows": int(len(existing_accepted_rows)),
        "accepted_pair_delta_rows": int(len(combined_accepted_rows)),
        "balanced_pair_delta_rows": int(len(balanced_rows)),
        "balanced_unique_left_seed_count": int(balanced_metrics["unique_left_seed_count"]),
        "balanced_unique_left_source_group_count": int(balanced_metrics["unique_left_source_group_count"]),
        "balanced_unique_left_fault_family_count": int(balanced_metrics["unique_left_fault_family_count"]),
        "balanced_unique_fault_family_pair_count": int(balanced_metrics["unique_fault_family_pair_count"]),
        "balanced_unique_direction_count": int(balanced_metrics["unique_direction_count"]),
        "balanced_unique_axis_pair_count": int(balanced_metrics["unique_axis_pair_count"]),
        "balanced_max_left_seed_dominance": float(balanced_metrics["max_left_seed_dominance"]),
        "balanced_max_direction_dominance": float(balanced_metrics["max_direction_dominance"]),
        "balanced_max_axis_pair_dominance": float(balanced_metrics["max_axis_pair_dominance"]),
        "component_control_rows": int(len(component_control_rows)),
        "train_public_rows": int(len(train_rows)),
        "eval_public_rows": int(len(eval_rows)),
        "source_holdout_public_rows": int(len(holdout_rows)),
        "max_abs_margin_delta": max_abs_margin_delta,
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "hold_steps_grid": list(int(value) for value in hold_steps_grid),
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "min_target_rows": int(min_target_rows),
        "min_normal_boundary_rows": int(min_normal_boundary_rows),
        "min_normal_boundary_seeds": int(min_normal_boundary_seeds),
        "min_new_accepted_rows": int(min_new_accepted_rows),
        "min_balanced_rows": int(min_balanced_rows),
        "min_balanced_seeds": int(min_balanced_seeds),
        "min_balanced_sources": int(min_balanced_sources),
        "min_balanced_fault_families": int(min_balanced_fault_families),
        "min_balanced_fault_pairs": int(min_balanced_fault_pairs),
        "max_seed_dominance_threshold": float(max_seed_dominance),
        "max_direction_dominance_threshold": float(max_direction_dominance),
        "max_axis_pair_dominance_threshold": float(max_axis_pair_dominance),
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
        "normal_boundary_candidate_rows_csv": run_dir / "normal_boundary_candidate_rows.csv",
        "pair_delta_sequence_rows_csv": run_dir / "pair_delta_sequence_rows.csv",
        "new_accepted_pair_delta_rows_csv": run_dir / "new_accepted_pair_delta_rows.csv",
        "accepted_pair_delta_rows_csv": run_dir / "accepted_pair_delta_rows.csv",
        "balanced_pair_delta_rows_csv": run_dir / "balanced_pair_delta_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 boundary-preserving missing-seed pair-delta refresh.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--target-weak-seed-rows", type=Path, required=True)
    parser.add_argument("--combined-boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--existing-accepted-pair-delta-rows", type=Path, default=Path("runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/accepted_pair_delta_rows.csv"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-targets-per-seed", type=int, default=8)
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
    parser.add_argument("--lateral-deltas", type=str, default="-0.20,-0.10,-0.05,0.0,0.05,0.10,0.20")
    parser.add_argument("--timing-deltas", type=str, default="-1.00,-0.50,-0.25,0.0,0.25,0.50")
    parser.add_argument("--half-width-deltas", type=str, default="-0.10,-0.05,0.0,0.05,0.10,0.20")
    parser.add_argument("--max-refine-iters", type=int, default=8)
    parser.add_argument("--epsilon-l2-grid", type=str, default="0.075,0.10,0.125")
    parser.add_argument("--hold-steps-grid", type=str, default="6,8,10")
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.03)
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--min-target-rows", type=int, default=24)
    parser.add_argument("--min-normal-boundary-rows", type=int, default=24)
    parser.add_argument("--min-normal-boundary-seeds", type=int, default=3)
    parser.add_argument("--min-new-accepted-rows", type=int, default=24)
    parser.add_argument("--min-balanced-rows", type=int, default=36)
    parser.add_argument("--min-balanced-seeds", type=int, default=3)
    parser.add_argument("--min-balanced-sources", type=int, default=6)
    parser.add_argument("--min-balanced-fault-families", type=int, default=5)
    parser.add_argument("--min-balanced-fault-pairs", type=int, default=8)
    parser.add_argument("--max-seed-dominance", type=float, default=0.45)
    parser.add_argument("--max-direction-dominance", type=float, default=0.65)
    parser.add_argument("--max-axis-pair-dominance", type=float, default=0.85)
    parser.add_argument("--max-pair-delta-candidates", type=int, default=60)
    parser.add_argument("--max-normal-rows-per-seed", type=int, default=24)
    parser.add_argument("--max-normal-rows-per-axis", type=int, default=24)
    parser.add_argument("--max-balanced-rows", type=int, default=96)
    parser.add_argument("--max-rows-per-left-seed", type=int, default=20)
    parser.add_argument("--max-rows-per-left-source-group", type=int, default=8)
    parser.add_argument("--max-rows-per-fault-family-pair", type=int, default=8)
    parser.add_argument("--max-rows-per-direction", type=int, default=48)
    parser.add_argument("--max-rows-per-axis-pair", type=int, default=48)
    parser.add_argument("--component-control-max-pairs", type=int, default=16)
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
    summary = run_boundary_preserving_refresh(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        target_weak_seed_rows_path=args.target_weak_seed_rows,
        combined_boundary_rows_path=args.combined_boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        existing_accepted_pair_delta_rows_path=args.existing_accepted_pair_delta_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_targets_per_seed=int(args.max_targets_per_seed),
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
        lateral_deltas=tuple(parse_float_list(args.lateral_deltas)),
        timing_deltas=tuple(parse_float_list(args.timing_deltas)),
        half_width_deltas=tuple(parse_float_list(args.half_width_deltas)),
        max_refine_iters=int(args.max_refine_iters),
        epsilon_grid=tuple(parse_float_list(args.epsilon_l2_grid)),
        hold_steps_grid=tuple(int(value) for value in parse_float_list(args.hold_steps_grid)),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        margin_delta_threshold=float(args.margin_delta_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        min_target_rows=int(args.min_target_rows),
        min_normal_boundary_rows=int(args.min_normal_boundary_rows),
        min_normal_boundary_seeds=int(args.min_normal_boundary_seeds),
        min_new_accepted_rows=int(args.min_new_accepted_rows),
        min_balanced_rows=int(args.min_balanced_rows),
        min_balanced_seeds=int(args.min_balanced_seeds),
        min_balanced_sources=int(args.min_balanced_sources),
        min_balanced_fault_families=int(args.min_balanced_fault_families),
        min_balanced_fault_pairs=int(args.min_balanced_fault_pairs),
        max_seed_dominance=float(args.max_seed_dominance),
        max_direction_dominance=float(args.max_direction_dominance),
        max_axis_pair_dominance=float(args.max_axis_pair_dominance),
        max_pair_delta_candidates=int(args.max_pair_delta_candidates),
        max_normal_rows_per_seed=int(args.max_normal_rows_per_seed),
        max_normal_rows_per_axis=int(args.max_normal_rows_per_axis),
        max_balanced_rows=int(args.max_balanced_rows),
        max_rows_per_left_seed=int(args.max_rows_per_left_seed),
        max_rows_per_left_source_group=int(args.max_rows_per_left_source_group),
        max_rows_per_fault_family_pair=int(args.max_rows_per_fault_family_pair),
        max_rows_per_direction=int(args.max_rows_per_direction),
        max_rows_per_axis_pair=int(args.max_rows_per_axis_pair),
        component_control_max_pairs=int(args.component_control_max_pairs),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
