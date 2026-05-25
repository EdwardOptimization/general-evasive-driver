"""No-training pair-delta refresh over M864 generated boundary rows."""

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
from autodrift.v4_full_wrong_history_response_intervention import PAIR_FIELDS, _snapshot_requests
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_sequence_effectiveness_probe import (
    ACCEPTED_FIELDS,
    DIRECTION_HOLD_SUMMARY_FIELDS,
    SEQUENCE_EFFECTIVENESS_FIELDS,
    _direction_hold_summary,
    _sequence_diversity,
    accepted_sequence_effective_rows_for_pair,
    replay_sequence_effectiveness_pair,
)
from autodrift.v4_pair_delta_focused_source_balanced_mining import (
    COMPONENT_DIRECTIONS,
    PAIR_DELTA_DIRECTIONS,
    split_source_aware,
    _boundary_action,
    _boundary_obstacle_distance,
    _fault_pair_key,
    _max_share,
    _source_pair_key,
)
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _as_int,
    read_csv_rows,
    reconstruct_snapshots,
)


SPLIT_FIELDS = [*ACCEPTED_FIELDS, "split"]

PAIR_CANDIDATE_FIELDS = [
    *PAIR_FIELDS,
    "pairability_tier",
    "source_pair_key",
    "fault_pair_key",
    "boundary_axis_pair",
    "different_fault_family",
    "different_seed",
    "selected_for_replay",
]

REJECTION_FIELDS = [*PAIR_CANDIDATE_FIELDS, "rejection_reason"]


def _accepted_primary_or_blank(row: dict[str, Any]) -> bool:
    value = row.get("accepted_primary", "")
    if str(value).strip() == "":
        return True
    return parse_bool(value)


def _boundary_rows_for_m867(
    boundary_rows: list[dict[str, str]],
    *,
    boundary_margin_threshold: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(boundary_rows):
        margin = _finite_float(row.get("min_clearance_margin"))
        if not (
            _accepted_primary_or_blank(row)
            and parse_bool(row.get("success", False))
            and not parse_bool(row.get("collision", False))
            and str(row.get("boundary_source_status", "")) == "boundary_new_to_m844"
            and np.isfinite(margin)
            and 0.0 <= margin <= float(boundary_margin_threshold)
        ):
            continue
        copied = dict(row)
        copied["candidate_id"] = str(row.get("candidate_id") or index)
        copied["m867_boundary_row_index"] = int(index)
        rows.append(copied)
    return rows


def _pairability_tier(distance: float, *, primary_max_obstacle_distance: float, diagnostic_max_obstacle_distance: float) -> str:
    if np.isfinite(distance) and distance <= float(primary_max_obstacle_distance):
        return "primary_0_10"
    if np.isfinite(distance) and distance <= float(diagnostic_max_obstacle_distance):
        return "diagnostic_0_20"
    return "outside_0_20"


def _pair_candidate_from_generated_boundary(
    pair_id: int,
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    primary_max_obstacle_distance: float,
    diagnostic_max_obstacle_distance: float,
) -> dict[str, Any]:
    left_action = _boundary_action(left)
    right_action = _boundary_action(right)
    first_action_l2 = float(np.linalg.norm(left_action - right_action))
    left_margin = _finite_float(left.get("min_clearance_margin"))
    right_margin = _finite_float(right.get("min_clearance_margin"))
    obstacle_distance = _boundary_obstacle_distance(left, right)
    tier = _pairability_tier(
        obstacle_distance,
        primary_max_obstacle_distance=float(primary_max_obstacle_distance),
        diagnostic_max_obstacle_distance=float(diagnostic_max_obstacle_distance),
    )
    fault_pair = f"{left.get('preferred_fault_family', '')}->{right.get('preferred_fault_family', '')}"
    source_pair = f"{left.get('source_group_id', '')}->{right.get('source_group_id', '')}"
    axis_pair = f"{left.get('boundary_axis', '')}->{right.get('boundary_axis', '')}"
    different_fault = str(left.get("preferred_fault_family", "")) != str(right.get("preferred_fault_family", ""))
    different_seed = str(left.get("seed", "")) != str(right.get("seed", ""))
    tier_rank = 0 if tier == "primary_0_10" else 1
    score = (
        tier_rank,
        0 if different_fault else 1,
        0 if different_seed else 1,
        -first_action_l2,
        obstacle_distance if np.isfinite(obstacle_distance) else 999.0,
        abs(left_margin - right_margin) if np.isfinite(left_margin) and np.isfinite(right_margin) else 999.0,
        _as_int(left.get("m867_boundary_row_index")),
        _as_int(right.get("m867_boundary_row_index")),
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
        "ego_response_distance": float(abs(_as_int(left.get("step")) - _as_int(right.get("step")))),
        "obstacle_geometry_distance": obstacle_distance,
        "first_action_l2": first_action_l2,
        "normal_margin_gap_abs": abs(left_margin - right_margin) if np.isfinite(left_margin) and np.isfinite(right_margin) else float("nan"),
        "left_normal_margin": left_margin,
        "right_normal_margin": right_margin,
        "left_boundary_axis": str(left.get("boundary_axis", "")),
        "right_boundary_axis": str(right.get("boundary_axis", "")),
        "left_margin_band": str(left.get("margin_band", "")),
        "right_margin_band": str(right.get("margin_band", "")),
        "pair_rank_score": repr(score),
        "left_step": _as_int(left.get("step")),
        "right_step": _as_int(right.get("step")),
        "pairability_tier": tier,
        "source_pair_key": source_pair,
        "fault_pair_key": fault_pair,
        "boundary_axis_pair": axis_pair,
        "different_fault_family": bool(different_fault),
        "different_seed": bool(different_seed),
        "selected_for_replay": False,
        "_pair_rank_tuple": score,
        "left_plan": left,
        "right_plan": right,
    }


def build_generated_boundary_pair_candidates(
    boundary_rows: list[dict[str, str]],
    *,
    max_pairs: int,
    boundary_margin_threshold: float,
    min_first_action_l2: float,
    primary_max_obstacle_distance: float,
    diagnostic_max_obstacle_distance: float,
    max_pairs_per_left_source_group: int,
    max_pairs_per_right_source_group: int,
    max_pairs_per_left_seed: int,
    max_pairs_per_fault_family_pair: int,
    max_pairs_per_left_fault_family: int,
    max_pairs_per_boundary_axis_pair: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Build and source-balance M864 generated-boundary pair candidates."""

    rows = _boundary_rows_for_m867(boundary_rows, boundary_margin_threshold=float(boundary_margin_threshold))
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    pair_id = 0
    for left in rows:
        for right in rows:
            if left is right:
                continue
            pair = _pair_candidate_from_generated_boundary(
                pair_id,
                left,
                right,
                primary_max_obstacle_distance=float(primary_max_obstacle_distance),
                diagnostic_max_obstacle_distance=float(diagnostic_max_obstacle_distance),
            )
            pair_id += 1
            reason = ""
            if pair["left_source_group_id"] == pair["right_source_group_id"]:
                reason = "same_source_group"
            elif _finite_float(pair.get("first_action_l2"), default=0.0) < float(min_first_action_l2):
                reason = "first_action_gap_too_small"
            elif str(pair.get("pairability_tier", "")) == "outside_0_20":
                reason = "obstacle_distance_too_large"
            if reason:
                rejected.append({**{key: pair.get(key, "") for key in PAIR_CANDIDATE_FIELDS}, "rejection_reason": reason})
                continue
            candidates.append(pair)
    candidates.sort(key=lambda row: row.get("_pair_rank_tuple", ()))

    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}

    def cap_keys(pair: dict[str, Any]) -> list[tuple[tuple[str, str], int]]:
        return [
            (("left_source_group_id", str(pair["left_source_group_id"])), int(max_pairs_per_left_source_group)),
            (("right_source_group_id", str(pair["right_source_group_id"])), int(max_pairs_per_right_source_group)),
            (("left_seed", str(pair["left_seed"])), int(max_pairs_per_left_seed)),
            (("left_fault_family", str(pair["left_fault_family"])), int(max_pairs_per_left_fault_family)),
            (("fault_family_pair", _fault_pair_key(pair)), int(max_pairs_per_fault_family_pair)),
            (("boundary_axis_pair", str(pair["boundary_axis_pair"])), int(max_pairs_per_boundary_axis_pair)),
            (("source_pair", _source_pair_key(pair)), 1),
        ]

    def cap_ok(pair: dict[str, Any]) -> bool:
        return not any(counts.get(key, 0) >= limit for key, limit in cap_keys(pair))

    remaining = list(candidates)
    while remaining and len(selected) < int(max_pairs):
        selectable = [pair for pair in remaining if cap_ok(pair)]
        if not selectable:
            break
        pair = min(
            selectable,
            key=lambda row: (
                counts.get(("left_seed", str(row["left_seed"])), 0),
                counts.get(("left_source_group_id", str(row["left_source_group_id"])), 0),
                counts.get(("left_fault_family", str(row["left_fault_family"])), 0),
                counts.get(("fault_family_pair", _fault_pair_key(row)), 0),
                row.get("_pair_rank_tuple", ()),
            ),
        )
        remaining.remove(pair)
        pair["selected_for_replay"] = True
        selected.append(pair)
        for key, _limit in cap_keys(pair):
            counts[key] = counts.get(key, 0) + 1
    for pair in remaining:
        reason = "max_pairs_limit" if len(selected) >= int(max_pairs) else "source_balance_limit"
        rejected.append({**{key: pair.get(key, "") for key in PAIR_CANDIDATE_FIELDS}, "rejection_reason": reason})
    return candidates, selected, rejected


def balance_generated_pair_delta_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows_per_left_source_group: int,
    max_rows_per_left_seed: int,
    max_rows_per_left_fault_family: int,
    max_rows_per_fault_family_pair: int,
    max_rows_per_direction: int,
    max_rows_per_axis_pair: int,
) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("left_source_group_id", "")),
            str(row.get("left_seed", "")),
            str(row.get("left_fault_family", "")),
            str(row.get("direction", "")),
            -_finite_float(row.get("abs_margin_delta"), default=0.0),
            _as_int(row.get("pair_id")),
            _as_int(row.get("hold_steps")),
        ),
    )
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    for row in ordered:
        axis_pair = f"{row.get('left_boundary_axis', '')}->{row.get('right_boundary_axis', '')}"
        keys = [
            (("left_source_group_id", str(row.get("left_source_group_id", ""))), int(max_rows_per_left_source_group)),
            (("left_seed", str(row.get("left_seed", ""))), int(max_rows_per_left_seed)),
            (("left_fault_family", str(row.get("left_fault_family", ""))), int(max_rows_per_left_fault_family)),
            (("fault_family_pair", _fault_pair_key(row)), int(max_rows_per_fault_family_pair)),
            (("direction", str(row.get("direction", ""))), int(max_rows_per_direction)),
            (("axis_pair", axis_pair), int(max_rows_per_axis_pair)),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in keys):
            continue
        selected.append(row)
        for key, _limit in keys:
            counts[key] = counts.get(key, 0) + 1
    return selected


def _m867_acceptance_class(row: dict[str, Any]) -> dict[str, Any]:
    accepted_class = str(row.get("accepted_class", ""))
    mapped = "pair_delta_outcome_flip"
    if accepted_class == "directional_degradation":
        mapped = "pair_delta_degradation"
    elif accepted_class == "directional_improvement":
        mapped = "pair_delta_improvement"
    return {**row, "accepted_class": mapped}


def _extended_sequence_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = _sequence_diversity(rows)
    metrics.update(
        {
            "unique_direction_count": len({str(row.get("direction", "")) for row in rows}),
            "max_direction_dominance": _max_share(rows, "direction"),
            "unique_axis_pair_count": len({f"{row.get('left_boundary_axis', '')}->{row.get('right_boundary_axis', '')}" for row in rows}),
            "max_axis_pair_dominance": _max_axis_pair_share(rows),
        }
    )
    return metrics


def _max_axis_pair_share(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    counts: dict[str, int] = {}
    for row in rows:
        key = f"{row.get('left_boundary_axis', '')}->{row.get('right_boundary_axis', '')}"
        counts[key] = counts.get(key, 0) + 1
    return max(counts.values(), default=0) / float(len(rows))


def classify_generated_boundary_pair_delta_refresh(
    *,
    actor_changed: bool,
    residual_changed: bool,
    pair_candidate_rows: int,
    selected_replay_pairs: int,
    pair_delta_sequence_rows: list[dict[str, Any]],
    accepted_pair_delta_rows: list[dict[str, Any]],
    balanced_pair_delta_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
    min_pair_candidate_rows: int,
    min_selected_replay_pairs: int,
    min_left_sources: int,
    min_left_seeds: int,
    min_left_fault_families: int,
    min_fault_pairs: int,
    min_hold_steps: int,
    max_left_source_dominance: float,
    max_left_seed_dominance: float,
    max_direction_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_generated_boundary_pair_delta_refresh_contract_violation"
    if (
        int(pair_candidate_rows) < int(min_pair_candidate_rows)
        or int(selected_replay_pairs) < int(min_selected_replay_pairs)
        or not pair_delta_sequence_rows
    ):
        return "v4_generated_boundary_pair_delta_refresh_pair_construction_failed"
    metrics = _extended_sequence_diversity(balanced_pair_delta_rows)
    strong = bool(
        len(balanced_pair_delta_rows) >= int(strong_min_rows)
        and metrics["unique_left_source_group_count"] >= int(min_left_sources)
        and metrics["unique_left_seed_count"] >= int(min_left_seeds)
        and metrics["unique_left_fault_family_count"] >= int(min_left_fault_families)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["unique_hold_steps_count"] >= int(min_hold_steps)
        and metrics["unique_direction_count"] >= 2
        and metrics["max_left_source_group_dominance"] <= float(max_left_source_dominance)
        and metrics["max_left_seed_dominance"] <= float(max_left_seed_dominance)
        and metrics["max_direction_dominance"] <= float(max_direction_dominance)
    )
    if strong:
        return "v4_generated_boundary_pair_delta_refresh_pass"
    sparse = bool(
        len(balanced_pair_delta_rows) >= int(sparse_min_rows)
        and metrics["unique_left_source_group_count"] >= 5
        and metrics["unique_left_seed_count"] >= 3
        and metrics["unique_left_fault_family_count"] >= 3
        and metrics["unique_fault_family_pair_count"] >= 6
    )
    if sparse:
        return "v4_generated_boundary_pair_delta_refresh_sparse_pair_delta_positive"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in pair_delta_sequence_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in pair_delta_sequence_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    if len(accepted_pair_delta_rows) < 10 and ((not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0):
        return "v4_generated_boundary_pair_delta_refresh_all_weak"
    return "v4_generated_boundary_pair_delta_refresh_source_limited"


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
            "gate_name": "pair_candidate_rows",
            "value": summary["pair_candidate_rows"],
            "threshold": summary["min_pair_candidate_rows"],
            "passed": int(summary["pair_candidate_rows"]) >= int(summary["min_pair_candidate_rows"]),
            "notes": "M864 generated boundary rows must produce enough raw pair candidates",
        },
        {
            "gate_name": "selected_replay_pairs",
            "value": summary["selected_replay_pairs"],
            "threshold": summary["min_selected_replay_pairs"],
            "passed": int(summary["selected_replay_pairs"]) >= int(summary["min_selected_replay_pairs"]),
            "notes": "source-aware selected replay pairs",
        },
        {
            "gate_name": "selected_left_source_diversity",
            "value": summary["selected_unique_left_source_group_count"],
            "threshold": summary["candidate_min_left_sources"],
            "passed": int(summary["selected_unique_left_source_group_count"]) >= int(summary["candidate_min_left_sources"]),
            "notes": "M867 design candidate-selection diversity gate",
        },
        {
            "gate_name": "selected_left_seed_diversity",
            "value": summary["selected_unique_left_seed_count"],
            "threshold": summary["candidate_min_left_seeds"],
            "passed": int(summary["selected_unique_left_seed_count"]) >= int(summary["candidate_min_left_seeds"]),
            "notes": "M867 design candidate-selection diversity gate",
        },
        {
            "gate_name": "selected_left_fault_family_diversity",
            "value": summary["selected_unique_left_fault_family_count"],
            "threshold": summary["candidate_min_left_fault_families"],
            "passed": int(summary["selected_unique_left_fault_family_count"]) >= int(summary["candidate_min_left_fault_families"]),
            "notes": "M867 design candidate-selection diversity gate",
        },
        {
            "gate_name": "accepted_pair_delta_rows",
            "value": summary["accepted_pair_delta_rows"],
            "threshold": summary["sparse_min_rows"],
            "passed": int(summary["accepted_pair_delta_rows"]) >= int(summary["sparse_min_rows"]),
            "notes": "component rows cannot satisfy this gate",
        },
        {
            "gate_name": "balanced_pair_delta_rows",
            "value": summary["balanced_pair_delta_rows"],
            "threshold": summary["sparse_min_rows"],
            "passed": int(summary["balanced_pair_delta_rows"]) >= int(summary["sparse_min_rows"]),
            "notes": "post-acceptance source-balanced pair-delta rows",
        },
        {
            "gate_name": "component_controls_not_primary",
            "value": True,
            "threshold": "true",
            "passed": True,
            "notes": "component-control rows are written only as diagnostics",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M867 cannot train or promote",
        },
    ]


def run_generated_boundary_pair_delta_refresh(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    combined_boundary_rows_path: Path,
    pairability_projection_rows_path: Path,
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
    hold_steps_grid: tuple[int, ...],
    boundary_margin_threshold: float,
    primary_max_obstacle_distance: float,
    diagnostic_max_obstacle_distance: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
    min_pair_candidate_rows: int,
    min_selected_replay_pairs: int,
    min_left_sources: int,
    min_left_seeds: int,
    min_left_fault_families: int,
    min_fault_pairs: int,
    min_hold_steps: int,
    max_left_source_dominance: float,
    max_left_seed_dominance: float,
    max_direction_dominance: float,
    max_pairs_per_left_source_group: int,
    max_pairs_per_right_source_group: int,
    max_pairs_per_left_seed: int,
    max_pairs_per_fault_family_pair: int,
    max_pairs_per_left_fault_family: int,
    max_pairs_per_boundary_axis_pair: int,
    max_rows_per_left_source_group: int,
    max_rows_per_left_seed: int,
    max_rows_per_left_fault_family: int,
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
        raise ValueError("M867 generated boundary pair-delta refresh requires an online recurrent checkpoint")
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

    combined_boundary_rows = read_csv_rows(combined_boundary_rows_path)
    pairability_projection_rows = read_csv_rows(pairability_projection_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    boundary_rows = _boundary_rows_for_m867(
        combined_boundary_rows,
        boundary_margin_threshold=float(boundary_margin_threshold),
    )
    pair_candidate_rows, replay_pair_rows, pair_rejections = build_generated_boundary_pair_candidates(
        combined_boundary_rows,
        max_pairs=int(max_pairs),
        boundary_margin_threshold=float(boundary_margin_threshold),
        min_first_action_l2=float(action_l2_threshold),
        primary_max_obstacle_distance=float(primary_max_obstacle_distance),
        diagnostic_max_obstacle_distance=float(diagnostic_max_obstacle_distance),
        max_pairs_per_left_source_group=int(max_pairs_per_left_source_group),
        max_pairs_per_right_source_group=int(max_pairs_per_right_source_group),
        max_pairs_per_left_seed=int(max_pairs_per_left_seed),
        max_pairs_per_fault_family_pair=int(max_pairs_per_fault_family_pair),
        max_pairs_per_left_fault_family=int(max_pairs_per_left_fault_family),
        max_pairs_per_boundary_axis_pair=int(max_pairs_per_boundary_axis_pair),
    )

    requests = _snapshot_requests(replay_pair_rows)
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

    pair_delta_rows: list[dict[str, Any]] = []
    accepted_pair_delta_rows: list[dict[str, Any]] = []
    reconstructed_pair_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    replayable_pairs_by_id: dict[str, dict[str, Any]] = {}
    for pair in replay_pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_CANDIDATE_FIELDS}, "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        reconstructed_pair_rows.append({key: pair.get(key, "") for key in PAIR_CANDIDATE_FIELDS})
        replayable_pairs_by_id[str(pair["pair_id"])] = pair
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
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_CANDIDATE_FIELDS}, "rejection_reason": f"pair_delta_replay_error:{type(exc).__name__}"})
            continue
        pair_delta_rows.extend(rows)
        accepted_pair_delta_rows.extend(
            _m867_acceptance_class(row)
            for row in accepted_sequence_effective_rows_for_pair(
                rows,
                boundary_margin_threshold=float(boundary_margin_threshold),
                margin_delta_threshold=float(margin_delta_threshold),
                action_l2_threshold=float(action_l2_threshold),
            )
            if str(row.get("direction_family", "")) == "pair_delta"
        )
        _append_progress(progress_path, {"stage": "pair_delta_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)})

    balanced_pair_delta_rows = balance_generated_pair_delta_rows(
        accepted_pair_delta_rows,
        max_rows_per_left_source_group=int(max_rows_per_left_source_group),
        max_rows_per_left_seed=int(max_rows_per_left_seed),
        max_rows_per_left_fault_family=int(max_rows_per_left_fault_family),
        max_rows_per_fault_family_pair=int(max_rows_per_fault_family_pair),
        max_rows_per_direction=int(max_rows_per_direction),
        max_rows_per_axis_pair=int(max_rows_per_axis_pair),
    )

    component_control_rows: list[dict[str, Any]] = []
    component_pair_ids: list[str] = []
    for row in balanced_pair_delta_rows:
        pair_id = str(row.get("pair_id", ""))
        if pair_id and pair_id not in component_pair_ids:
            component_pair_ids.append(pair_id)
        if len(component_pair_ids) >= int(component_control_max_pairs):
            break
    for pair_id in component_pair_ids:
        pair = replayable_pairs_by_id.get(pair_id)
        if pair is None:
            continue
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            continue
        try:
            component_control_rows.extend(
                replay_sequence_effectiveness_pair(
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
            )
        except Exception as exc:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_CANDIDATE_FIELDS}, "rejection_reason": f"component_control_error:{type(exc).__name__}"})

    train_rows, eval_rows, holdout_rows = split_source_aware(balanced_pair_delta_rows)
    accepted_degradation = [row for row in accepted_pair_delta_rows if row.get("accepted_class") == "pair_delta_degradation"]
    accepted_improvement = [row for row in accepted_pair_delta_rows if row.get("accepted_class") == "pair_delta_improvement"]
    success_flip_rows = [row for row in pair_delta_rows if parse_bool(row.get("success_flip", False))]
    collision_flip_rows = [row for row in pair_delta_rows if parse_bool(row.get("collision_flip", False))]
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in pair_delta_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_generated_boundary_pair_delta_refresh(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        pair_candidate_rows=len(pair_candidate_rows),
        selected_replay_pairs=len(replay_pair_rows),
        pair_delta_sequence_rows=pair_delta_rows,
        accepted_pair_delta_rows=accepted_pair_delta_rows,
        balanced_pair_delta_rows=balanced_pair_delta_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        strong_min_rows=int(strong_min_rows),
        sparse_min_rows=int(sparse_min_rows),
        min_pair_candidate_rows=int(min_pair_candidate_rows),
        min_selected_replay_pairs=int(min_selected_replay_pairs),
        min_left_sources=int(min_left_sources),
        min_left_seeds=int(min_left_seeds),
        min_left_fault_families=int(min_left_fault_families),
        min_fault_pairs=int(min_fault_pairs),
        min_hold_steps=int(min_hold_steps),
        max_left_source_dominance=float(max_left_source_dominance),
        max_left_seed_dominance=float(max_left_seed_dominance),
        max_direction_dominance=float(max_direction_dominance),
    )

    diversity_summary = {
        "boundary_rows": _extended_sequence_diversity(
            [
                {
                    "left_source_group_id": row.get("source_group_id", ""),
                    "left_seed": row.get("seed", ""),
                    "left_fault_family": row.get("preferred_fault_family", ""),
                    "right_fault_family": row.get("wrong_fault_family", ""),
                    "left_boundary_axis": row.get("boundary_axis", ""),
                    "right_boundary_axis": row.get("boundary_axis", ""),
                }
                for row in boundary_rows
            ]
        ),
        "pair_candidate_rows": _extended_sequence_diversity(pair_candidate_rows),
        "selected_replay_pairs": _extended_sequence_diversity(replay_pair_rows),
        "pair_delta_sequence_rows": _extended_sequence_diversity(pair_delta_rows),
        "accepted_pair_delta": _extended_sequence_diversity(accepted_pair_delta_rows),
        "balanced_pair_delta": _extended_sequence_diversity(balanced_pair_delta_rows),
        "component_control_rows": _extended_sequence_diversity(component_control_rows),
        "train_public": _extended_sequence_diversity(train_rows),
        "eval_public": _extended_sequence_diversity(eval_rows),
        "source_holdout_public": _extended_sequence_diversity(holdout_rows),
    }
    balanced_metrics = diversity_summary["balanced_pair_delta"]
    accepted_metrics = diversity_summary["accepted_pair_delta"]
    selected_metrics = diversity_summary["selected_replay_pairs"]
    all_rejections = [*pair_rejections, *snapshot_rejections, *replay_rejections]
    direction_hold_summary = _direction_hold_summary(pair_delta_rows, accepted_pair_delta_rows, tuple(int(value) for value in hold_steps_grid))

    write_csv_rows(run_dir / "pair_candidate_rows.csv", pair_candidate_rows, fieldnames=PAIR_CANDIDATE_FIELDS)
    write_csv_rows(run_dir / "replay_pair_rows.csv", replay_pair_rows, fieldnames=PAIR_CANDIDATE_FIELDS)
    write_csv_rows(run_dir / "reconstructed_pair_rows.csv", reconstructed_pair_rows, fieldnames=PAIR_CANDIDATE_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "pair_delta_sequence_rows.csv", pair_delta_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "accepted_pair_delta_rows.csv", accepted_pair_delta_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "balanced_pair_delta_rows.csv", balanced_pair_delta_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "component_control_rows.csv", component_control_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "direction_hold_summary.csv", direction_hold_summary, fieldnames=DIRECTION_HOLD_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "train_public_rows.csv", train_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "eval_public_rows.csv", eval_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", holdout_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", all_rejections, fieldnames=REJECTION_FIELDS)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    summary = {
        "run_type": "v4_generated_boundary_pair_delta_refresh",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "combined_boundary_rows": combined_boundary_rows_path,
        "pairability_projection_rows": pairability_projection_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "hold_steps_grid": list(int(value) for value in hold_steps_grid),
        "combined_boundary_rows_count": int(len(combined_boundary_rows)),
        "boundary_source_rows": int(len(boundary_rows)),
        "pairability_projection_rows_count": int(len(pairability_projection_rows)),
        "source_rows_count": int(len(source_rows)),
        "candidate_plan_rows_count": int(len(candidate_plan_rows)),
        "pair_candidate_rows": int(len(pair_candidate_rows)),
        "selected_replay_pairs": int(len(replay_pair_rows)),
        "reconstructed_pair_rows": int(len(reconstructed_pair_rows)),
        "reconstructed_snapshot_rows": int(len(snapshot_rows)),
        "pair_delta_sequence_rows": int(len(pair_delta_rows)),
        "accepted_pair_delta_rows": int(len(accepted_pair_delta_rows)),
        "balanced_pair_delta_rows": int(len(balanced_pair_delta_rows)),
        "accepted_pair_delta_degradation_rows": int(len(accepted_degradation)),
        "accepted_pair_delta_improvement_rows": int(len(accepted_improvement)),
        "pair_delta_success_flip_rows": int(len(success_flip_rows)),
        "pair_delta_collision_flip_rows": int(len(collision_flip_rows)),
        "component_control_rows": int(len(component_control_rows)),
        "train_public_rows": int(len(train_rows)),
        "eval_public_rows": int(len(eval_rows)),
        "source_holdout_public_rows": int(len(holdout_rows)),
        "selected_unique_left_source_group_count": int(selected_metrics["unique_left_source_group_count"]),
        "selected_unique_left_seed_count": int(selected_metrics["unique_left_seed_count"]),
        "selected_unique_left_fault_family_count": int(selected_metrics["unique_left_fault_family_count"]),
        "accepted_unique_left_source_group_count": int(accepted_metrics["unique_left_source_group_count"]),
        "balanced_unique_left_source_group_count": int(balanced_metrics["unique_left_source_group_count"]),
        "balanced_unique_left_seed_count": int(balanced_metrics["unique_left_seed_count"]),
        "balanced_unique_left_fault_family_count": int(balanced_metrics["unique_left_fault_family_count"]),
        "balanced_unique_fault_family_pair_count": int(balanced_metrics["unique_fault_family_pair_count"]),
        "balanced_unique_hold_steps_count": int(balanced_metrics["unique_hold_steps_count"]),
        "balanced_unique_direction_count": int(balanced_metrics["unique_direction_count"]),
        "balanced_unique_axis_pair_count": int(balanced_metrics["unique_axis_pair_count"]),
        "balanced_max_left_source_group_dominance": float(balanced_metrics["max_left_source_group_dominance"]),
        "balanced_max_left_seed_dominance": float(balanced_metrics["max_left_seed_dominance"]),
        "balanced_max_direction_dominance": float(balanced_metrics["max_direction_dominance"]),
        "balanced_max_axis_pair_dominance": float(balanced_metrics["max_axis_pair_dominance"]),
        "max_abs_margin_delta": max_abs_margin_delta,
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "primary_max_obstacle_distance": float(primary_max_obstacle_distance),
        "diagnostic_max_obstacle_distance": float(diagnostic_max_obstacle_distance),
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "strong_min_rows": int(strong_min_rows),
        "sparse_min_rows": int(sparse_min_rows),
        "min_pair_candidate_rows": int(min_pair_candidate_rows),
        "min_selected_replay_pairs": int(min_selected_replay_pairs),
        "candidate_min_left_sources": 16,
        "candidate_min_left_seeds": 5,
        "candidate_min_left_fault_families": 8,
        "min_left_sources": int(min_left_sources),
        "min_left_seeds": int(min_left_seeds),
        "min_left_fault_families": int(min_left_fault_families),
        "min_fault_pairs": int(min_fault_pairs),
        "min_hold_steps": int(min_hold_steps),
        "max_left_source_dominance_threshold": float(max_left_source_dominance),
        "max_left_seed_dominance_threshold": float(max_left_seed_dominance),
        "max_direction_dominance_threshold": float(max_direction_dominance),
        "max_pairs_per_left_source_group": int(max_pairs_per_left_source_group),
        "max_pairs_per_right_source_group": int(max_pairs_per_right_source_group),
        "max_pairs_per_left_seed": int(max_pairs_per_left_seed),
        "max_pairs_per_fault_family_pair": int(max_pairs_per_fault_family_pair),
        "max_pairs_per_left_fault_family": int(max_pairs_per_left_fault_family),
        "max_pairs_per_boundary_axis_pair": int(max_pairs_per_boundary_axis_pair),
        "max_rows_per_left_source_group": int(max_rows_per_left_source_group),
        "max_rows_per_left_seed": int(max_rows_per_left_seed),
        "max_rows_per_left_fault_family": int(max_rows_per_left_fault_family),
        "max_rows_per_fault_family_pair": int(max_rows_per_fault_family_pair),
        "max_rows_per_direction": int(max_rows_per_direction),
        "max_rows_per_axis_pair": int(max_rows_per_axis_pair),
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
        "pair_candidate_rows_csv": run_dir / "pair_candidate_rows.csv",
        "replay_pair_rows_csv": run_dir / "replay_pair_rows.csv",
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 generated-boundary pair-delta refresh.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--combined-boundary-rows", type=Path, required=True)
    parser.add_argument("--pairability-projection-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-pairs", type=int, default=180)
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
    parser.add_argument("--epsilon-l2-grid", type=str, default="0.025,0.05,0.075")
    parser.add_argument("--hold-steps-grid", type=str, default="4,6")
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--primary-max-obstacle-distance", type=float, default=0.10)
    parser.add_argument("--diagnostic-max-obstacle-distance", type=float, default=0.20)
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--strong-min-rows", type=int, default=60)
    parser.add_argument("--sparse-min-rows", type=int, default=30)
    parser.add_argument("--min-pair-candidate-rows", type=int, default=120)
    parser.add_argument("--min-selected-replay-pairs", type=int, default=80)
    parser.add_argument("--min-left-sources", type=int, default=8)
    parser.add_argument("--min-left-seeds", type=int, default=4)
    parser.add_argument("--min-left-fault-families", type=int, default=5)
    parser.add_argument("--min-fault-pairs", type=int, default=10)
    parser.add_argument("--min-hold-steps", type=int, default=2)
    parser.add_argument("--max-left-source-dominance", type=float, default=0.30)
    parser.add_argument("--max-left-seed-dominance", type=float, default=0.40)
    parser.add_argument("--max-direction-dominance", type=float, default=0.60)
    parser.add_argument("--max-pairs-per-left-source-group", type=int, default=12)
    parser.add_argument("--max-pairs-per-right-source-group", type=int, default=12)
    parser.add_argument("--max-pairs-per-left-seed", type=int, default=48)
    parser.add_argument("--max-pairs-per-fault-family-pair", type=int, default=16)
    parser.add_argument("--max-pairs-per-left-fault-family", type=int, default=48)
    parser.add_argument("--max-pairs-per-boundary-axis-pair", type=int, default=64)
    parser.add_argument("--max-rows-per-left-source-group", type=int, default=8)
    parser.add_argument("--max-rows-per-left-seed", type=int, default=16)
    parser.add_argument("--max-rows-per-left-fault-family", type=int, default=16)
    parser.add_argument("--max-rows-per-fault-family-pair", type=int, default=8)
    parser.add_argument("--max-rows-per-direction", type=int, default=24)
    parser.add_argument("--max-rows-per-axis-pair", type=int, default=32)
    parser.add_argument("--component-control-max-pairs", type=int, default=32)
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
    summary = run_generated_boundary_pair_delta_refresh(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        combined_boundary_rows_path=args.combined_boundary_rows,
        pairability_projection_rows_path=args.pairability_projection_rows,
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
        hold_steps_grid=tuple(int(value) for value in parse_float_list(args.hold_steps_grid)),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        primary_max_obstacle_distance=float(args.primary_max_obstacle_distance),
        diagnostic_max_obstacle_distance=float(args.diagnostic_max_obstacle_distance),
        margin_delta_threshold=float(args.margin_delta_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        strong_min_rows=int(args.strong_min_rows),
        sparse_min_rows=int(args.sparse_min_rows),
        min_pair_candidate_rows=int(args.min_pair_candidate_rows),
        min_selected_replay_pairs=int(args.min_selected_replay_pairs),
        min_left_sources=int(args.min_left_sources),
        min_left_seeds=int(args.min_left_seeds),
        min_left_fault_families=int(args.min_left_fault_families),
        min_fault_pairs=int(args.min_fault_pairs),
        min_hold_steps=int(args.min_hold_steps),
        max_left_source_dominance=float(args.max_left_source_dominance),
        max_left_seed_dominance=float(args.max_left_seed_dominance),
        max_direction_dominance=float(args.max_direction_dominance),
        max_pairs_per_left_source_group=int(args.max_pairs_per_left_source_group),
        max_pairs_per_right_source_group=int(args.max_pairs_per_right_source_group),
        max_pairs_per_left_seed=int(args.max_pairs_per_left_seed),
        max_pairs_per_fault_family_pair=int(args.max_pairs_per_fault_family_pair),
        max_pairs_per_left_fault_family=int(args.max_pairs_per_left_fault_family),
        max_pairs_per_boundary_axis_pair=int(args.max_pairs_per_boundary_axis_pair),
        max_rows_per_left_source_group=int(args.max_rows_per_left_source_group),
        max_rows_per_left_seed=int(args.max_rows_per_left_seed),
        max_rows_per_left_fault_family=int(args.max_rows_per_left_fault_family),
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
