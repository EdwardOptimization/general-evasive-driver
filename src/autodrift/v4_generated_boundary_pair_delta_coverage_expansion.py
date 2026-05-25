"""No-training accepted pair-delta coverage expansion over M867 rows."""

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
from autodrift.train_ppo import resolve_device
from autodrift.v4_extreme_hidden_dynamics_data_route import IdentityResidualGate
from autodrift.v4_generated_boundary_pair_delta_refresh import (
    _boundary_rows_for_m867,
    _extended_sequence_diversity,
    _m867_acceptance_class,
    _max_axis_pair_share,
    balance_generated_pair_delta_rows,
)
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_sequence_effectiveness_probe import (
    ACCEPTED_FIELDS,
    SEQUENCE_EFFECTIVENESS_FIELDS,
    accepted_sequence_effective_rows_for_pair,
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

COVERAGE_EXTRA_FIELDS = [
    "coverage_source",
    "target_rank",
    "target_seed",
    "target_best_abs_margin_delta",
    "target_best_direction",
    "target_best_hold_steps",
    "target_best_epsilon_l2",
    "retarget_axis",
    "retarget_delta",
    "retarget_candidate_id",
    "retarget_target_body_x",
    "retarget_target_body_y",
    "retarget_target_half_width",
]
COVERAGE_ACCEPTED_FIELDS = [*ACCEPTED_FIELDS, *COVERAGE_EXTRA_FIELDS]
COVERAGE_SEQUENCE_FIELDS = [*SEQUENCE_EFFECTIVENESS_FIELDS, *COVERAGE_EXTRA_FIELDS]
SPLIT_FIELDS = [*COVERAGE_ACCEPTED_FIELDS, "split"]


def _pair_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("pair_id", "")), str(row.get("left_seed", "")))


def select_target_weak_seed_rows(
    sequence_rows: list[dict[str, str]],
    *,
    missing_seeds: tuple[str, ...] = MISSING_ACCEPTED_SEEDS,
    max_targets_per_seed: int,
    max_normal_margin: float,
) -> list[dict[str, Any]]:
    """Select strongest weak non-accepted pair-delta rows for missing seeds."""

    best_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sequence_rows:
        left_seed = str(row.get("left_seed", ""))
        if left_seed not in missing_seeds:
            continue
        normal_margin = _finite_float(row.get("normal_margin"))
        if not (
            parse_bool(row.get("normal_success", False))
            and not parse_bool(row.get("normal_collision", False))
            and np.isfinite(normal_margin)
            and 0.0 <= normal_margin <= float(max_normal_margin)
        ):
            continue
        key = _pair_key(row)
        existing = best_by_pair.get(key)
        current_abs = _finite_float(row.get("abs_margin_delta"), default=-1.0)
        existing_abs = _finite_float(existing.get("abs_margin_delta"), default=-1.0) if existing is not None else -1.0
        if existing is None or current_abs > existing_abs:
            best_by_pair[key] = row
    by_seed: dict[str, list[dict[str, Any]]] = {seed: [] for seed in missing_seeds}
    for row in best_by_pair.values():
        by_seed.setdefault(str(row.get("left_seed", "")), []).append(row)
    selected: list[dict[str, Any]] = []
    for seed in missing_seeds:
        ordered = sorted(
            by_seed.get(seed, []),
            key=lambda row: (
                -_finite_float(row.get("abs_margin_delta"), default=0.0),
                _finite_float(row.get("normal_margin"), default=999.0),
                _as_int(row.get("pair_id")),
            ),
        )
        for rank, row in enumerate(ordered[: int(max_targets_per_seed)]):
            selected.append(
                {
                    **row,
                    "target_rank": int(rank),
                    "target_seed": seed,
                    "target_best_abs_margin_delta": _finite_float(row.get("abs_margin_delta"), default=0.0),
                    "target_best_direction": str(row.get("direction", "")),
                    "target_best_hold_steps": _as_int(row.get("hold_steps")),
                    "target_best_epsilon_l2": _finite_float(row.get("epsilon_l2"), default=0.0),
                }
            )
    return selected


def _boundary_by_candidate_id(boundary_rows: list[dict[str, str]], *, boundary_margin_threshold: float) -> dict[str, dict[str, Any]]:
    rows = _boundary_rows_for_m867(boundary_rows, boundary_margin_threshold=float(boundary_margin_threshold))
    return {str(_as_int(row.get("candidate_id"))): row for row in rows}


def pair_rows_from_target_rows(
    target_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, str]],
    *,
    boundary_margin_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    boundary_by_id = _boundary_by_candidate_id(boundary_rows, boundary_margin_threshold=float(boundary_margin_threshold))
    pairs: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for target in target_rows:
        left_plan = boundary_by_id.get(str(_as_int(target.get("left_candidate_id"))))
        right_plan = boundary_by_id.get(str(_as_int(target.get("right_candidate_id"))))
        if left_plan is None or right_plan is None:
            rejected.append({**target, "rejection_reason": "missing_boundary_plan"})
            continue
        pairs.append(
            {
                "pair_id": _as_int(target.get("pair_id")),
                "left_candidate_id": _as_int(target.get("left_candidate_id")),
                "right_candidate_id": _as_int(target.get("right_candidate_id")),
                "left_source_group_id": _as_int(target.get("left_source_group_id")),
                "right_source_group_id": _as_int(target.get("right_source_group_id")),
                "left_seed": _as_int(target.get("left_seed")),
                "right_seed": _as_int(target.get("right_seed")),
                "left_fault_family": str(target.get("left_fault_family", "")),
                "right_fault_family": str(target.get("right_fault_family", "")),
                "left_fidelity_class": str(target.get("left_fidelity_class", "")),
                "right_fidelity_class": str(target.get("right_fidelity_class", "")),
                "left_warmup_mode": str(target.get("left_warmup_mode", "")),
                "right_warmup_mode": str(target.get("right_warmup_mode", "")),
                "left_onset_bucket": str(target.get("left_onset_bucket", "")),
                "right_onset_bucket": str(target.get("right_onset_bucket", "")),
                "ego_response_distance": _finite_float(target.get("ego_response_distance"), default=0.0),
                "obstacle_geometry_distance": _finite_float(target.get("obstacle_geometry_distance"), default=0.0),
                "first_action_l2": _finite_float(target.get("first_action_l2"), default=0.0),
                "normal_margin_gap_abs": _finite_float(target.get("normal_margin_gap_abs"), default=0.0),
                "left_normal_margin": _finite_float(target.get("left_normal_margin"), default=float("nan")),
                "right_normal_margin": _finite_float(target.get("right_normal_margin"), default=float("nan")),
                "left_boundary_axis": str(target.get("left_boundary_axis", "")),
                "right_boundary_axis": str(target.get("right_boundary_axis", "")),
                "left_margin_band": str(target.get("left_margin_band", "")),
                "right_margin_band": str(target.get("right_margin_band", "")),
                "pair_rank_score": str(target.get("pair_rank_score", "")),
                "left_step": _as_int(target.get("left_step")),
                "right_step": _as_int(target.get("right_step")),
                "target_rank": _as_int(target.get("target_rank")),
                "target_seed": str(target.get("target_seed", "")),
                "target_best_abs_margin_delta": _finite_float(target.get("target_best_abs_margin_delta"), default=0.0),
                "target_best_direction": str(target.get("target_best_direction", "")),
                "target_best_hold_steps": _as_int(target.get("target_best_hold_steps")),
                "target_best_epsilon_l2": _finite_float(target.get("target_best_epsilon_l2"), default=0.0),
                "left_plan": left_plan,
                "right_plan": right_plan,
            }
        )
    return pairs, rejected


def retarget_candidate_rows(
    pair_rows: list[dict[str, Any]],
    *,
    lateral_deltas: tuple[float, ...],
    timing_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    max_retargets_per_target: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    candidate_id = 0
    for pair in pair_rows:
        left_plan = pair["left_plan"]
        base_x = _finite_float(left_plan.get("target_obstacle_body_x"))
        base_y = _finite_float(left_plan.get("target_obstacle_body_y"))
        base_width = _finite_float(left_plan.get("target_obstacle_half_width"))
        candidates: list[tuple[str, float, float, float, float]] = []
        for delta in lateral_deltas:
            candidates.append(("obstacle_lateral_offset", float(delta), base_x, base_y + float(delta), base_width))
        for delta in timing_deltas:
            candidates.append(("obstacle_timing", float(delta), max(1.0, base_x + float(delta)), base_y, base_width))
        for delta in half_width_deltas:
            candidates.append(("obstacle_half_width", float(delta), base_x, base_y, max(0.1, base_width + float(delta))))
        for axis, delta, body_x, body_y, half_width in candidates[: int(max_retargets_per_target)]:
            left_retargeted = dict(left_plan)
            left_retargeted["target_obstacle_body_x"] = float(body_x)
            left_retargeted["target_obstacle_body_y"] = float(body_y)
            left_retargeted["target_obstacle_half_width"] = float(half_width)
            output.append(
                {
                    **pair,
                    "pair_id": int(pair["pair_id"]) * 1000 + candidate_id,
                    "retarget_candidate_id": int(candidate_id),
                    "retarget_axis": axis,
                    "retarget_delta": float(delta),
                    "retarget_target_body_x": float(body_x),
                    "retarget_target_body_y": float(body_y),
                    "retarget_target_half_width": float(half_width),
                    "left_plan": left_retargeted,
                }
            )
            candidate_id += 1
    return output


def _coverage_key(row: dict[str, Any], key: str) -> str:
    if key == "axis_pair":
        return f"{row.get('left_boundary_axis', '')}->{row.get('right_boundary_axis', '')}"
    return str(row.get(key, ""))


def balance_coverage_pair_delta_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows: int,
    max_rows_per_left_seed: int,
    max_rows_per_left_source_group: int,
    max_rows_per_fault_family_pair: int,
    max_rows_per_direction: int,
    max_rows_per_axis_pair: int,
) -> list[dict[str, Any]]:
    """Balance accepted rows by seed, source, direction, and axis pair."""

    remaining = sorted(
        rows,
        key=lambda row: (
            -_finite_float(row.get("abs_margin_delta"), default=0.0),
            str(row.get("coverage_source", "")),
            _as_int(row.get("pair_id")),
            str(row.get("direction", "")),
        ),
    )
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}

    def caps(row: dict[str, Any]) -> list[tuple[tuple[str, str], int]]:
        return [
            (("left_seed", _coverage_key(row, "left_seed")), int(max_rows_per_left_seed)),
            (("left_source_group_id", _coverage_key(row, "left_source_group_id")), int(max_rows_per_left_source_group)),
            (("fault_family_pair", f"{row.get('left_fault_family', '')}->{row.get('right_fault_family', '')}"), int(max_rows_per_fault_family_pair)),
            (("direction", _coverage_key(row, "direction")), int(max_rows_per_direction)),
            (("axis_pair", _coverage_key(row, "axis_pair")), int(max_rows_per_axis_pair)),
        ]

    while remaining and len(selected) < int(max_rows):
        candidates = [row for row in remaining if not any(counts.get(key, 0) >= limit for key, limit in caps(row))]
        if not candidates:
            break
        row = min(
            candidates,
            key=lambda item: (
                counts.get(("left_seed", _coverage_key(item, "left_seed")), 0),
                counts.get(("direction", _coverage_key(item, "direction")), 0),
                counts.get(("axis_pair", _coverage_key(item, "axis_pair")), 0),
                counts.get(("left_source_group_id", _coverage_key(item, "left_source_group_id")), 0),
                -_finite_float(item.get("abs_margin_delta"), default=0.0),
            ),
        )
        remaining.remove(row)
        selected.append(row)
        for key, _limit in caps(row):
            counts[key] = counts.get(key, 0) + 1
    return selected


def classify_coverage_expansion(
    *,
    actor_changed: bool,
    residual_changed: bool,
    target_weak_seed_rows: list[dict[str, Any]],
    retarget_candidate_rows_count: int,
    retarget_replay_rows_count: int,
    pair_delta_sequence_rows: list[dict[str, Any]],
    accepted_pair_delta_rows: list[dict[str, Any]],
    balanced_pair_delta_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    min_target_rows: int,
    min_target_seeds: int,
    min_retarget_candidates: int,
    min_accepted_rows: int,
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
        return "v4_generated_boundary_pair_delta_coverage_expansion_contract_violation"
    target_seeds = {str(row.get("left_seed", "")) for row in target_weak_seed_rows}
    if (
        len(target_weak_seed_rows) < int(min_target_rows)
        or len(target_seeds) < int(min_target_seeds)
        or int(retarget_candidate_rows_count) < int(min_retarget_candidates)
        or int(retarget_replay_rows_count) <= 0
        or not pair_delta_sequence_rows
    ):
        return "v4_generated_boundary_pair_delta_coverage_expansion_construction_failed"
    metrics = _extended_sequence_diversity(balanced_pair_delta_rows)
    primary = bool(
        len(accepted_pair_delta_rows) >= int(min_accepted_rows)
        and len(balanced_pair_delta_rows) >= int(min_balanced_rows)
        and metrics["unique_left_seed_count"] >= int(min_balanced_seeds)
        and metrics["unique_left_source_group_count"] >= int(min_balanced_sources)
        and metrics["unique_left_fault_family_count"] >= int(min_balanced_fault_families)
        and metrics["unique_fault_family_pair_count"] >= int(min_balanced_fault_pairs)
        and metrics["unique_direction_count"] >= 2
        and metrics["unique_axis_pair_count"] >= 2
        and metrics["max_left_seed_dominance"] <= float(max_seed_dominance)
        and metrics["max_direction_dominance"] <= float(max_direction_dominance)
        and metrics["max_axis_pair_dominance"] <= float(max_axis_pair_dominance)
    )
    if primary:
        return "v4_generated_boundary_pair_delta_coverage_expansion_pass"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in pair_delta_sequence_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in pair_delta_sequence_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    new_rows = [row for row in accepted_pair_delta_rows if str(row.get("coverage_source", "")) == "m870_retarget"]
    if len(new_rows) < 10 and ((not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0):
        return "v4_generated_boundary_pair_delta_coverage_expansion_all_weak"
    return "v4_generated_boundary_pair_delta_coverage_expansion_source_limited"


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
            "gate_name": "target_weak_seed_rows",
            "value": summary["target_weak_seed_rows"],
            "threshold": summary["min_target_rows"],
            "passed": int(summary["target_weak_seed_rows"]) >= int(summary["min_target_rows"]),
            "notes": "missing accepted seeds must be targeted",
        },
        {
            "gate_name": "retarget_candidate_rows",
            "value": summary["retarget_candidate_rows"],
            "threshold": summary["min_retarget_candidates"],
            "passed": int(summary["retarget_candidate_rows"]) >= int(summary["min_retarget_candidates"]),
            "notes": "bounded obstacle retargeting candidates",
        },
        {
            "gate_name": "balanced_left_seed_diversity",
            "value": summary["balanced_unique_left_seed_count"],
            "threshold": summary["min_balanced_seeds"],
            "passed": int(summary["balanced_unique_left_seed_count"]) >= int(summary["min_balanced_seeds"]),
            "notes": "primary accepted coverage gate",
        },
        {
            "gate_name": "balanced_pair_delta_rows",
            "value": summary["balanced_pair_delta_rows"],
            "threshold": summary["min_balanced_rows"],
            "passed": int(summary["balanced_pair_delta_rows"]) >= int(summary["min_balanced_rows"]),
            "notes": "component rows cannot satisfy this gate",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M870 cannot promote",
        },
    ]


def run_coverage_expansion(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    m867_pair_delta_sequence_rows_path: Path,
    m867_accepted_pair_delta_rows_path: Path,
    m867_balanced_pair_delta_rows_path: Path,
    combined_boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_targets_per_seed: int,
    max_retargets_per_target: int,
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
    hold_steps_grid: tuple[int, ...],
    lateral_deltas: tuple[float, ...],
    timing_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    boundary_margin_threshold: float,
    target_normal_margin_threshold: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
    min_target_rows: int,
    min_target_seeds: int,
    min_retarget_candidates: int,
    min_accepted_rows: int,
    min_balanced_rows: int,
    min_balanced_seeds: int,
    min_balanced_sources: int,
    min_balanced_fault_families: int,
    min_balanced_fault_pairs: int,
    max_seed_dominance: float,
    max_direction_dominance: float,
    max_axis_pair_dominance: float,
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
        raise ValueError("M870 coverage expansion requires an online recurrent checkpoint")
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

    m867_sequence_rows = read_csv_rows(m867_pair_delta_sequence_rows_path)
    m867_accepted_rows = [{**row, "coverage_source": "m867_existing"} for row in read_csv_rows(m867_accepted_pair_delta_rows_path)]
    m867_balanced_rows = read_csv_rows(m867_balanced_pair_delta_rows_path)
    combined_boundary_rows = read_csv_rows(combined_boundary_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)

    existing_rebalanced = balance_coverage_pair_delta_rows(
        m867_accepted_rows,
        max_rows=int(max_balanced_rows),
        max_rows_per_left_seed=int(max_rows_per_left_seed),
        max_rows_per_left_source_group=int(max_rows_per_left_source_group),
        max_rows_per_fault_family_pair=int(max_rows_per_fault_family_pair),
        max_rows_per_direction=int(max_rows_per_direction),
        max_rows_per_axis_pair=int(max_rows_per_axis_pair),
    )
    target_rows = select_target_weak_seed_rows(
        m867_sequence_rows,
        max_targets_per_seed=int(max_targets_per_seed),
        max_normal_margin=float(target_normal_margin_threshold),
    )
    target_pair_rows, target_rejections = pair_rows_from_target_rows(
        target_rows,
        combined_boundary_rows,
        boundary_margin_threshold=float(boundary_margin_threshold),
    )
    retarget_rows = retarget_candidate_rows(
        target_pair_rows,
        lateral_deltas=tuple(float(value) for value in lateral_deltas),
        timing_deltas=tuple(float(value) for value in timing_deltas),
        half_width_deltas=tuple(float(value) for value in half_width_deltas),
        max_retargets_per_target=int(max_retargets_per_target),
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

    sequence_rows: list[dict[str, Any]] = []
    new_accepted_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    retarget_pairs_by_id: dict[str, dict[str, Any]] = {}
    for pair in retarget_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**_strip_plans(pair), "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        retarget_pairs_by_id[str(pair["pair_id"])] = pair
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
        meta = _coverage_meta(pair, source="m870_retarget")
        for row in rows:
            sequence_rows.append({**row, **meta})
        accepted = accepted_sequence_effective_rows_for_pair(
            rows,
            boundary_margin_threshold=float(boundary_margin_threshold),
            margin_delta_threshold=float(margin_delta_threshold),
            action_l2_threshold=float(action_l2_threshold),
        )
        new_accepted_rows.extend({**_m867_acceptance_class(row), **meta} for row in accepted if str(row.get("direction_family", "")) == "pair_delta")
        _append_progress(progress_path, {"stage": "coverage_retarget_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)})

    combined_accepted_rows = [*m867_accepted_rows, *new_accepted_rows]
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
        pair = retarget_pairs_by_id.get(pair_id)
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
        meta = _coverage_meta(pair, source="m870_component_control")
        component_control_rows.extend({**row, **meta} for row in rows)

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_coverage_expansion(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        target_weak_seed_rows=target_rows,
        retarget_candidate_rows_count=len(retarget_rows),
        retarget_replay_rows_count=len(sequence_rows),
        pair_delta_sequence_rows=sequence_rows,
        accepted_pair_delta_rows=combined_accepted_rows,
        balanced_pair_delta_rows=balanced_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        min_target_rows=int(min_target_rows),
        min_target_seeds=int(min_target_seeds),
        min_retarget_candidates=int(min_retarget_candidates),
        min_accepted_rows=int(min_accepted_rows),
        min_balanced_rows=int(min_balanced_rows),
        min_balanced_seeds=int(min_balanced_seeds),
        min_balanced_sources=int(min_balanced_sources),
        min_balanced_fault_families=int(min_balanced_fault_families),
        min_balanced_fault_pairs=int(min_balanced_fault_pairs),
        max_seed_dominance=float(max_seed_dominance),
        max_direction_dominance=float(max_direction_dominance),
        max_axis_pair_dominance=float(max_axis_pair_dominance),
    )

    diversity_summary = {
        "m867_existing_accepted": _extended_sequence_diversity(m867_accepted_rows),
        "existing_rebalanced": _extended_sequence_diversity(existing_rebalanced),
        "target_weak_seed_rows": _extended_sequence_diversity(target_rows),
        "retarget_candidate_rows": _extended_sequence_diversity(retarget_rows),
        "retarget_pair_delta_sequence_rows": _extended_sequence_diversity(sequence_rows),
        "new_accepted_pair_delta": _extended_sequence_diversity(new_accepted_rows),
        "combined_accepted_pair_delta": _extended_sequence_diversity(combined_accepted_rows),
        "balanced_pair_delta": _extended_sequence_diversity(balanced_rows),
        "component_control_rows": _extended_sequence_diversity(component_control_rows),
        "train_public": _extended_sequence_diversity(train_rows),
        "eval_public": _extended_sequence_diversity(eval_rows),
        "source_holdout_public": _extended_sequence_diversity(holdout_rows),
    }
    balanced_metrics = diversity_summary["balanced_pair_delta"]
    target_metrics = diversity_summary["target_weak_seed_rows"]
    new_metrics = diversity_summary["new_accepted_pair_delta"]
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in sequence_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )

    write_csv_rows(run_dir / "existing_rebalanced_pair_delta_rows.csv", existing_rebalanced, fieldnames=COVERAGE_ACCEPTED_FIELDS)
    write_json(run_dir / "existing_rebalance_summary.json", diversity_summary["existing_rebalanced"])
    write_csv_rows(run_dir / "target_weak_seed_rows.csv", target_rows)
    write_csv_rows(run_dir / "retarget_candidate_rows.csv", [_strip_plans(row) for row in retarget_rows])
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "retarget_replay_rows.csv", sequence_rows, fieldnames=COVERAGE_SEQUENCE_FIELDS)
    write_csv_rows(run_dir / "pair_delta_sequence_rows.csv", sequence_rows, fieldnames=COVERAGE_SEQUENCE_FIELDS)
    write_csv_rows(run_dir / "new_accepted_pair_delta_rows.csv", new_accepted_rows, fieldnames=COVERAGE_ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_pair_delta_rows.csv", combined_accepted_rows, fieldnames=COVERAGE_ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "balanced_pair_delta_rows.csv", balanced_rows, fieldnames=COVERAGE_ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "component_control_rows.csv", component_control_rows, fieldnames=COVERAGE_SEQUENCE_FIELDS)
    write_csv_rows(run_dir / "train_public_rows.csv", train_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "eval_public_rows.csv", eval_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", holdout_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", [*target_rejections, *snapshot_rejections, *replay_rejections])
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    summary = {
        "run_type": "v4_generated_boundary_pair_delta_coverage_expansion",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "m867_pair_delta_sequence_rows": m867_pair_delta_sequence_rows_path,
        "m867_accepted_pair_delta_rows": m867_accepted_pair_delta_rows_path,
        "m867_balanced_pair_delta_rows": m867_balanced_pair_delta_rows_path,
        "combined_boundary_rows": combined_boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "hold_steps_grid": list(int(value) for value in hold_steps_grid),
        "m867_sequence_rows": int(len(m867_sequence_rows)),
        "m867_existing_accepted_rows": int(len(m867_accepted_rows)),
        "m867_existing_balanced_rows": int(len(m867_balanced_rows)),
        "existing_rebalanced_pair_delta_rows": int(len(existing_rebalanced)),
        "target_weak_seed_rows": int(len(target_rows)),
        "target_unique_left_seed_count": int(target_metrics["unique_left_seed_count"]),
        "retarget_candidate_rows": int(len(retarget_rows)),
        "retarget_replay_rows": int(len(sequence_rows)),
        "pair_delta_sequence_rows": int(len(sequence_rows)),
        "new_accepted_pair_delta_rows": int(len(new_accepted_rows)),
        "new_accepted_unique_left_seed_count": int(new_metrics["unique_left_seed_count"]),
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
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "target_normal_margin_threshold": float(target_normal_margin_threshold),
        "min_target_rows": int(min_target_rows),
        "min_target_seeds": int(min_target_seeds),
        "min_retarget_candidates": int(min_retarget_candidates),
        "min_accepted_rows": int(min_accepted_rows),
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
        "existing_rebalanced_pair_delta_rows_csv": run_dir / "existing_rebalanced_pair_delta_rows.csv",
        "existing_rebalance_summary_json": run_dir / "existing_rebalance_summary.json",
        "target_weak_seed_rows_csv": run_dir / "target_weak_seed_rows.csv",
        "retarget_candidate_rows_csv": run_dir / "retarget_candidate_rows.csv",
        "retarget_replay_rows_csv": run_dir / "retarget_replay_rows.csv",
        "pair_delta_sequence_rows_csv": run_dir / "pair_delta_sequence_rows.csv",
        "accepted_pair_delta_rows_csv": run_dir / "accepted_pair_delta_rows.csv",
        "balanced_pair_delta_rows_csv": run_dir / "balanced_pair_delta_rows.csv",
        "component_control_rows_csv": run_dir / "component_control_rows.csv",
        "train_public_rows_csv": run_dir / "train_public_rows.csv",
        "eval_public_rows_csv": run_dir / "eval_public_rows.csv",
        "source_holdout_public_rows_csv": run_dir / "source_holdout_public_rows.csv",
        "diversity_summary_json": run_dir / "diversity_summary.json",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def _coverage_meta(pair: dict[str, Any], *, source: str) -> dict[str, Any]:
    return {key: pair.get(key, "") for key in COVERAGE_EXTRA_FIELDS} | {"coverage_source": source}


def _strip_plans(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"left_plan", "right_plan"} and not key.startswith("_")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 generated-boundary pair-delta coverage expansion.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--m867-pair-delta-sequence-rows", type=Path, required=True)
    parser.add_argument("--m867-accepted-pair-delta-rows", type=Path, required=True)
    parser.add_argument("--m867-balanced-pair-delta-rows", type=Path, required=True)
    parser.add_argument("--combined-boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-targets-per-seed", type=int, default=8)
    parser.add_argument("--max-retargets-per-target", type=int, default=6)
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
    parser.add_argument("--epsilon-l2-grid", type=str, default="0.075,0.10,0.125")
    parser.add_argument("--hold-steps-grid", type=str, default="6,8,10")
    parser.add_argument("--lateral-deltas", type=str, default="-0.20,-0.10,0.10")
    parser.add_argument("--timing-deltas", type=str, default="-1.00,-0.50")
    parser.add_argument("--half-width-deltas", type=str, default="0.10")
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.03)
    parser.add_argument("--target-normal-margin-threshold", type=float, default=0.03)
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--min-target-rows", type=int, default=24)
    parser.add_argument("--min-target-seeds", type=int, default=3)
    parser.add_argument("--min-retarget-candidates", type=int, default=96)
    parser.add_argument("--min-accepted-rows", type=int, default=60)
    parser.add_argument("--min-balanced-rows", type=int, default=36)
    parser.add_argument("--min-balanced-seeds", type=int, default=3)
    parser.add_argument("--min-balanced-sources", type=int, default=6)
    parser.add_argument("--min-balanced-fault-families", type=int, default=5)
    parser.add_argument("--min-balanced-fault-pairs", type=int, default=8)
    parser.add_argument("--max-seed-dominance", type=float, default=0.45)
    parser.add_argument("--max-direction-dominance", type=float, default=0.65)
    parser.add_argument("--max-axis-pair-dominance", type=float, default=0.85)
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
    summary = run_coverage_expansion(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        m867_pair_delta_sequence_rows_path=args.m867_pair_delta_sequence_rows,
        m867_accepted_pair_delta_rows_path=args.m867_accepted_pair_delta_rows,
        m867_balanced_pair_delta_rows_path=args.m867_balanced_pair_delta_rows,
        combined_boundary_rows_path=args.combined_boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_targets_per_seed=int(args.max_targets_per_seed),
        max_retargets_per_target=int(args.max_retargets_per_target),
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
        hold_steps_grid=tuple(int(value) for value in parse_float_list(args.hold_steps_grid)),
        lateral_deltas=tuple(parse_float_list(args.lateral_deltas)),
        timing_deltas=tuple(parse_float_list(args.timing_deltas)),
        half_width_deltas=tuple(parse_float_list(args.half_width_deltas)),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        target_normal_margin_threshold=float(args.target_normal_margin_threshold),
        margin_delta_threshold=float(args.margin_delta_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        min_target_rows=int(args.min_target_rows),
        min_target_seeds=int(args.min_target_seeds),
        min_retarget_candidates=int(args.min_retarget_candidates),
        min_accepted_rows=int(args.min_accepted_rows),
        min_balanced_rows=int(args.min_balanced_rows),
        min_balanced_seeds=int(args.min_balanced_seeds),
        min_balanced_sources=int(args.min_balanced_sources),
        min_balanced_fault_families=int(args.min_balanced_fault_families),
        min_balanced_fault_pairs=int(args.min_balanced_fault_pairs),
        max_seed_dominance=float(args.max_seed_dominance),
        max_direction_dominance=float(args.max_direction_dominance),
        max_axis_pair_dominance=float(args.max_axis_pair_dominance),
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
