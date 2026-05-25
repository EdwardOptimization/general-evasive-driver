"""No-training pair-delta-focused source-balanced mining."""

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
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _as_float,
    _as_int,
    read_csv_rows,
    reconstruct_snapshots,
)
from autodrift.v4_full_wrong_history_response_intervention import PAIR_FIELDS, _snapshot_requests
from autodrift.v4_near_boundary_sequence_effectiveness_probe import (
    ACCEPTED_FIELDS,
    BASE_DIRECTIONS,
    DIRECTION_HOLD_SUMMARY_FIELDS,
    SEQUENCE_EFFECTIVENESS_FIELDS,
    accepted_sequence_effective_rows_for_pair,
    replay_sequence_effectiveness_pair,
    _best_sequence_by_pair,
    _direction_hold_summary,
    _sequence_diversity,
)


SPLIT_FIELDS = [*ACCEPTED_FIELDS, "split"]
PAIR_DELTA_DIRECTIONS = ("pair_delta_positive", "pair_delta_negative")
COMPONENT_DIRECTIONS = (
    "steer_positive",
    "steer_negative",
    "throttle_positive",
    "throttle_negative",
    "brake_positive",
    "brake_negative",
)


def _boundary_action(row: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            _finite_float(row.get("first_steer")),
            _finite_float(row.get("first_throttle")),
            _finite_float(row.get("first_brake")),
        ],
        dtype=np.float64,
    )


def _boundary_obstacle_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
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


def _source_pair_key(pair: dict[str, Any]) -> str:
    return f"{pair.get('left_source_group_id', '')}->{pair.get('right_source_group_id', '')}"


def _fault_pair_key(pair: dict[str, Any]) -> str:
    return f"{pair.get('left_fault_family', '')}->{pair.get('right_fault_family', '')}"


def _pair_candidate_from_boundary(pair_id: int, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_action = _boundary_action(left)
    right_action = _boundary_action(right)
    first_action_l2 = float(np.linalg.norm(left_action - right_action))
    left_margin = _finite_float(left.get("min_clearance_margin"))
    right_margin = _finite_float(right.get("min_clearance_margin"))
    obstacle_distance = _boundary_obstacle_distance(left, right)
    score = (
        obstacle_distance,
        abs(left_margin - right_margin) if np.isfinite(left_margin) and np.isfinite(right_margin) else 999.0,
        -first_action_l2,
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
        "left_plan": left,
        "right_plan": right,
    }


def build_cross_source_pair_rows_from_boundary(
    boundary_rows: list[dict[str, str]],
    *,
    max_pairs: int,
    boundary_margin_threshold: float,
    min_first_action_l2: float,
    max_obstacle_distance: float,
    max_pairs_per_left_source_group: int,
    max_pairs_per_right_source_group: int,
    max_pairs_per_left_seed: int,
    max_pairs_per_fault_family_pair: int,
    max_pairs_per_left_fault_family: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Build real cross-source near-boundary pairs from boundary rows."""

    rows = [
        row
        for row in boundary_rows
        if parse_bool(row.get("accepted_primary", True))
        and parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and 0.0 <= _finite_float(row.get("min_clearance_margin")) <= float(boundary_margin_threshold)
    ]
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    pair_id = 0
    for left_index, left in enumerate(rows):
        for right in rows:
            if left is right:
                continue
            if _as_int(left.get("candidate_id")) == _as_int(right.get("candidate_id")):
                continue
            pair = _pair_candidate_from_boundary(pair_id, left, right)
            pair_id += 1
            reason = ""
            if pair["left_source_group_id"] == pair["right_source_group_id"]:
                reason = "same_source_group"
            elif pair["left_fault_family"] == pair["right_fault_family"] and pair["left_seed"] == pair["right_seed"]:
                reason = "same_fault_family_and_seed"
            elif "future_only" in {str(pair["left_fidelity_class"]), str(pair["right_fidelity_class"])}:
                reason = "future_only_fidelity"
            elif _finite_float(pair["first_action_l2"], default=0.0) < float(min_first_action_l2):
                reason = "first_action_gap_too_small"
            elif _finite_float(pair["obstacle_geometry_distance"], default=999.0) > float(max_obstacle_distance):
                reason = "obstacle_distance_too_large"
            if reason:
                rejected.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": reason})
                continue
            candidates.append(pair)
    candidates.sort(
        key=lambda row: (
            _finite_float(row.get("obstacle_geometry_distance"), default=999.0),
            _finite_float(row.get("normal_margin_gap_abs"), default=999.0),
            -_finite_float(row.get("first_action_l2"), default=0.0),
            _as_int(row.get("left_candidate_id")),
            _as_int(row.get("right_candidate_id")),
        )
    )
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    for pair in candidates:
        keys = [
            (("left_source_group_id", str(pair["left_source_group_id"])), int(max_pairs_per_left_source_group)),
            (("right_source_group_id", str(pair["right_source_group_id"])), int(max_pairs_per_right_source_group)),
            (("left_seed", str(pair["left_seed"])), int(max_pairs_per_left_seed)),
            (("left_fault_family", str(pair["left_fault_family"])), int(max_pairs_per_left_fault_family)),
            (("fault_family_pair", _fault_pair_key(pair)), int(max_pairs_per_fault_family_pair)),
            (("source_pair", _source_pair_key(pair)), 1),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in keys):
            rejected.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": "source_balance_limit"})
            continue
        selected.append(pair)
        for key, _limit in keys:
            counts[key] = counts.get(key, 0) + 1
        if len(selected) >= int(max_pairs):
            break
    return candidates, selected, rejected


def split_source_aware(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministically split accepted rows by left source group."""

    groups = sorted({str(row.get("left_source_group_id", "")) for row in rows})
    if not groups:
        return [], [], []
    train_groups: set[str] = set()
    eval_groups: set[str] = set()
    holdout_groups: set[str] = set()
    for index, group in enumerate(groups):
        if len(groups) >= 5 and index % 5 == 0:
            holdout_groups.add(group)
        elif len(groups) >= 3 and index % 5 == 1:
            eval_groups.add(group)
        else:
            train_groups.add(group)
    if not train_groups and groups:
        train_groups.add(groups[-1])
        eval_groups.discard(groups[-1])
        holdout_groups.discard(groups[-1])

    def tagged(subset: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
        return [{**row, "split": split} for row in subset]

    train = [row for row in rows if str(row.get("left_source_group_id", "")) in train_groups]
    eval_rows = [row for row in rows if str(row.get("left_source_group_id", "")) in eval_groups]
    holdout = [row for row in rows if str(row.get("left_source_group_id", "")) in holdout_groups]
    return tagged(train, "train_public"), tagged(eval_rows, "eval_public"), tagged(holdout, "source_holdout_public")


def pair_rows_from_candidate_rows(
    pair_candidate_rows: list[dict[str, str]],
    boundary_rows: list[dict[str, str]],
    *,
    max_replay_pairs: int,
    min_first_action_l2: float,
    max_pairs_per_left_source_group: int,
    max_pairs_per_right_source_group: int,
    max_pairs_per_left_seed: int,
    max_pairs_per_fault_family_pair: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Hydrate M847 pair candidates with left/right boundary plans."""

    boundary_by_id = {str(_as_int(row.get("candidate_id"))): row for row in boundary_rows}
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    ordered = sorted(
        pair_candidate_rows,
        key=lambda row: (
            _finite_float(row.get("obstacle_geometry_distance"), default=999.0),
            _finite_float(row.get("normal_margin_gap_abs"), default=999.0),
            -_finite_float(row.get("first_action_l2"), default=0.0),
            _as_int(row.get("pair_id")),
        ),
    )
    for row in ordered:
        base = {key: row.get(key, "") for key in PAIR_FIELDS}
        left_plan = boundary_by_id.get(str(_as_int(row.get("left_candidate_id"))))
        right_plan = boundary_by_id.get(str(_as_int(row.get("right_candidate_id"))))
        if left_plan is None or right_plan is None:
            rejected.append({**base, "rejection_reason": "missing_boundary_plan"})
            continue
        if _finite_float(row.get("first_action_l2"), default=0.0) < float(min_first_action_l2):
            rejected.append({**base, "rejection_reason": "first_action_gap_too_small"})
            continue
        keys = [
            (("left_source_group_id", str(row.get("left_source_group_id", ""))), int(max_pairs_per_left_source_group)),
            (("right_source_group_id", str(row.get("right_source_group_id", ""))), int(max_pairs_per_right_source_group)),
            (("left_seed", str(row.get("left_seed", ""))), int(max_pairs_per_left_seed)),
            (("fault_family_pair", _fault_pair_key(row)), int(max_pairs_per_fault_family_pair)),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in keys):
            rejected.append({**base, "rejection_reason": "source_balance_limit"})
            continue
        selected.append(
            {
                **base,
                "left_step": _as_int(left_plan.get("step")),
                "right_step": _as_int(right_plan.get("step")),
                "left_plan": left_plan,
                "right_plan": right_plan,
            }
        )
        for key, _limit in keys:
            counts[key] = counts.get(key, 0) + 1
        if len(selected) >= int(max_replay_pairs):
            break
    return selected, rejected


def balance_pair_delta_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows_per_left_source_group: int,
    max_rows_per_left_seed: int,
    max_rows_per_left_fault_family: int,
    max_rows_per_fault_family_pair: int,
    max_rows_per_direction: int,
) -> list[dict[str, Any]]:
    """Select source-balanced accepted pair-delta rows."""

    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("left_source_group_id", "")),
            str(row.get("left_seed", "")),
            str(row.get("left_fault_family", "")),
            -_finite_float(row.get("abs_margin_delta"), default=0.0),
            _as_int(row.get("pair_id")),
            str(row.get("direction", "")),
            _as_int(row.get("hold_steps")),
        ),
    )
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    for row in ordered:
        keys = [
            (("left_source_group_id", str(row.get("left_source_group_id", ""))), int(max_rows_per_left_source_group)),
            (("left_seed", str(row.get("left_seed", ""))), int(max_rows_per_left_seed)),
            (("left_fault_family", str(row.get("left_fault_family", ""))), int(max_rows_per_left_fault_family)),
            (("fault_family_pair", _fault_pair_key(row)), int(max_rows_per_fault_family_pair)),
            (("direction", str(row.get("direction", ""))), int(max_rows_per_direction)),
        ]
        if any(counts.get(key, 0) >= limit for key, limit in keys):
            continue
        selected.append(row)
        for key, _limit in keys:
            counts[key] = counts.get(key, 0) + 1
    return selected


def classify_pair_delta_focused_mining(
    *,
    actor_changed: bool,
    residual_changed: bool,
    accepted_pair_delta_rows: list[dict[str, Any]],
    balanced_pair_delta_rows: list[dict[str, Any]],
    all_pair_delta_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
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
        return "v4_pair_delta_focused_source_balanced_mining_contract_violation"
    metrics = _sequence_diversity(balanced_pair_delta_rows)
    directions = {str(row.get("direction", "")) for row in balanced_pair_delta_rows}
    max_direction_share = _max_share(balanced_pair_delta_rows, "direction")
    strong = bool(
        len(balanced_pair_delta_rows) >= int(strong_min_rows)
        and metrics["unique_left_source_group_count"] >= int(min_left_sources)
        and metrics["unique_left_seed_count"] >= int(min_left_seeds)
        and metrics["unique_left_fault_family_count"] >= int(min_left_fault_families)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["unique_hold_steps_count"] >= int(min_hold_steps)
        and len(directions) >= 2
        and metrics["max_left_source_group_dominance"] <= float(max_left_source_dominance)
        and metrics["max_left_seed_dominance"] <= float(max_left_seed_dominance)
        and max_direction_share <= float(max_direction_dominance)
    )
    if strong:
        return "v4_pair_delta_focused_source_balanced_mining_pass"
    sparse = bool(
        len(balanced_pair_delta_rows) >= int(sparse_min_rows)
        and metrics["unique_left_source_group_count"] >= 5
        and metrics["unique_left_seed_count"] >= 3
        and metrics["unique_left_fault_family_count"] >= 3
        and metrics["unique_fault_family_pair_count"] >= 6
    )
    if sparse:
        return "v4_pair_delta_focused_source_balanced_mining_sparse_pair_delta_positive"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in all_pair_delta_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in all_pair_delta_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    if len(accepted_pair_delta_rows) < 10 and ((not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0):
        return "v4_pair_delta_focused_source_balanced_mining_all_weak"
    return "v4_pair_delta_focused_source_balanced_mining_source_limited"


def _max_share(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values(), default=0) / float(len(rows))


def classify_cross_source_pair_refresh(
    *,
    actor_changed: bool,
    residual_changed: bool,
    paired_candidate_rows: int,
    reconstructed_pair_rows: int,
    accepted_rows: list[dict[str, Any]],
    accepted_pair_delta_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
    min_pair_candidate_rows: int,
    min_reconstructed_pair_rows: int,
    min_pair_delta_rows: int,
    min_left_sources: int,
    min_left_seeds: int,
    min_left_fault_families: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    min_hold_steps: int,
    min_direction_families: int,
    max_left_source_dominance: float,
    max_left_seed_dominance: float,
    max_direction_family_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_cross_source_sequence_effective_pair_refresh_contract_violation"
    pair_delta_sequence_rows = sum(1 for row in all_rows if str(row.get("direction_family", "")) == "pair_delta")
    if (
        int(paired_candidate_rows) < int(min_pair_candidate_rows)
        or int(reconstructed_pair_rows) < int(min_reconstructed_pair_rows)
        or int(pair_delta_sequence_rows) <= 0
    ):
        return "v4_cross_source_sequence_effective_pair_refresh_pair_construction_failed"
    metrics = _sequence_diversity(accepted_rows)
    strong = bool(
        len(accepted_rows) >= int(strong_min_rows)
        and len(accepted_pair_delta_rows) >= int(min_pair_delta_rows)
        and metrics["unique_left_source_group_count"] >= int(min_left_sources)
        and metrics["unique_left_seed_count"] >= int(min_left_seeds)
        and metrics["unique_left_fault_family_count"] >= int(min_left_fault_families)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["unique_warmup_pair_count"] >= int(min_warmup_pairs)
        and metrics["unique_onset_pair_count"] >= int(min_onset_pairs)
        and metrics["unique_hold_steps_count"] >= int(min_hold_steps)
        and metrics["unique_direction_family_count"] >= int(min_direction_families)
        and metrics["max_left_source_group_dominance"] <= float(max_left_source_dominance)
        and metrics["max_left_seed_dominance"] <= float(max_left_seed_dominance)
        and metrics["max_direction_family_dominance"] <= float(max_direction_family_dominance)
    )
    if strong:
        return "v4_cross_source_sequence_effective_pair_refresh_pass"
    sparse_pair_positive = bool(
        len(accepted_rows) >= int(sparse_min_rows)
        and len(accepted_pair_delta_rows) >= 10
        and metrics["unique_left_source_group_count"] >= 6
        and metrics["unique_fault_family_pair_count"] >= 4
    )
    if sparse_pair_positive:
        return "v4_cross_source_sequence_effective_pair_refresh_sparse_pair_positive"
    if len(accepted_rows) >= int(sparse_min_rows) and len(accepted_pair_delta_rows) < 10:
        return "v4_cross_source_sequence_effective_pair_refresh_component_only_positive"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in all_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in all_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    if len(accepted_rows) < int(sparse_min_rows) and ((not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0):
        return "v4_cross_source_sequence_effective_pair_refresh_all_weak"
    return "v4_cross_source_sequence_effective_pair_refresh_source_limited"


def _cross_source_gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
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
            "gate_name": "paired_candidate_rows",
            "value": summary["paired_candidate_rows"],
            "threshold": summary["min_pair_candidate_rows"],
            "passed": int(summary["paired_candidate_rows"]) >= int(summary["min_pair_candidate_rows"]),
            "notes": "real cross-source pairs are required",
        },
        {
            "gate_name": "pair_delta_sequence_rows",
            "value": summary["pair_delta_sequence_rows"],
            "threshold": ">0",
            "passed": int(summary["pair_delta_sequence_rows"]) > 0,
            "notes": "M847 must not degenerate into self-pair component-only scans",
        },
        {
            "gate_name": "accepted_pair_delta_rows",
            "value": summary["accepted_pair_delta_sequence_effective_rows"],
            "threshold": summary["min_pair_delta_rows"],
            "passed": int(summary["accepted_pair_delta_sequence_effective_rows"]) >= int(summary["min_pair_delta_rows"]),
            "notes": "pair-delta rows are controllability diagnostics only",
        },
        {
            "gate_name": "primary_sequence_effective_rows",
            "value": summary["accepted_primary_sequence_effective_rows"],
            "threshold": summary["strong_min_rows"],
            "passed": int(summary["accepted_primary_sequence_effective_rows"]) >= int(summary["strong_min_rows"]),
            "notes": "direct sequence override evidence is controllability only",
        },
        {
            "gate_name": "source_diversity",
            "value": summary["unique_left_source_group_count"],
            "threshold": summary["min_left_sources"],
            "passed": int(summary["unique_left_source_group_count"]) >= int(summary["min_left_sources"]),
            "notes": "M847 target is source-diverse paired coverage",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M847 cannot promote",
        },
    ]


def run_cross_source_sequence_effective_pair_refresh(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    boundary_rows_path: Path,
    reconstructed_snapshot_rows_path: Path,
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
    max_obstacle_distance: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
    min_pair_candidate_rows: int,
    min_reconstructed_pair_rows: int,
    min_pair_delta_rows: int,
    min_left_sources: int,
    min_left_seeds: int,
    min_left_fault_families: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    min_hold_steps: int,
    min_direction_families: int,
    max_left_source_dominance: float,
    max_left_seed_dominance: float,
    max_direction_family_dominance: float,
    max_pairs_per_left_source_group: int,
    max_pairs_per_right_source_group: int,
    max_pairs_per_left_seed: int,
    max_pairs_per_fault_family_pair: int,
    max_pairs_per_left_fault_family: int,
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
        raise ValueError("M847 pair refresh requires an online recurrent checkpoint")
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

    boundary_rows_raw = read_csv_rows(boundary_rows_path)
    previous_reconstructed_snapshot_rows = read_csv_rows(reconstructed_snapshot_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    boundary_rows = [
        row
        for row in boundary_rows_raw
        if parse_bool(row.get("accepted_primary", True))
        and parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and _finite_float(row.get("min_clearance_margin")) <= float(boundary_margin_threshold)
    ]
    pair_candidate_rows, pair_rows, pair_rejections = build_cross_source_pair_rows_from_boundary(
        boundary_rows,
        max_pairs=int(max_pairs),
        boundary_margin_threshold=float(boundary_margin_threshold),
        min_first_action_l2=float(action_l2_threshold),
        max_obstacle_distance=float(max_obstacle_distance),
        max_pairs_per_left_source_group=int(max_pairs_per_left_source_group),
        max_pairs_per_right_source_group=int(max_pairs_per_right_source_group),
        max_pairs_per_left_seed=int(max_pairs_per_left_seed),
        max_pairs_per_fault_family_pair=int(max_pairs_per_fault_family_pair),
        max_pairs_per_left_fault_family=int(max_pairs_per_left_fault_family),
    )
    requests = _snapshot_requests(pair_rows)
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

    replay_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    reconstructed_pair_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    for pair in pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        reconstructed_pair_rows.append({key: pair.get(key, "") for key in PAIR_FIELDS})
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
                directions=BASE_DIRECTIONS,
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": f"replay_error:{type(exc).__name__}"})
            continue
        replay_rows.extend(rows)
        accepted_rows.extend(
            accepted_sequence_effective_rows_for_pair(
                rows,
                boundary_margin_threshold=float(boundary_margin_threshold),
                margin_delta_threshold=float(margin_delta_threshold),
                action_l2_threshold=float(action_l2_threshold),
            )
        )
        _append_progress(progress_path, {"stage": "cross_source_sequence_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)})

    train_rows, eval_rows, holdout_rows = split_source_aware(accepted_rows)
    accepted_pair_delta = [row for row in accepted_rows if str(row.get("direction_family", "")) == "pair_delta"]
    accepted_degradation = [row for row in accepted_rows if row.get("accepted_class") == "directional_degradation"]
    accepted_improvement = [row for row in accepted_rows if row.get("accepted_class") == "directional_improvement"]
    pair_delta_sequence_rows = [row for row in replay_rows if str(row.get("direction_family", "")) == "pair_delta"]
    success_flip_rows = [row for row in replay_rows if parse_bool(row.get("success_flip", False))]
    collision_flip_rows = [row for row in replay_rows if parse_bool(row.get("collision_flip", False))]
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in replay_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    max_degradation_margin_delta = max(
        (
            _finite_float(row.get("degradation_margin_delta"), default=0.0)
            for row in replay_rows
            if np.isfinite(_finite_float(row.get("degradation_margin_delta"), default=float("nan")))
        ),
        default=float("nan"),
    )
    max_improvement_margin_delta = max(
        (
            _finite_float(row.get("improvement_margin_delta"), default=0.0)
            for row in replay_rows
            if np.isfinite(_finite_float(row.get("improvement_margin_delta"), default=float("nan")))
        ),
        default=float("nan"),
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_cross_source_pair_refresh(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        paired_candidate_rows=len(pair_rows),
        reconstructed_pair_rows=len(reconstructed_pair_rows),
        accepted_rows=accepted_rows,
        accepted_pair_delta_rows=accepted_pair_delta,
        all_rows=replay_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        strong_min_rows=int(strong_min_rows),
        sparse_min_rows=int(sparse_min_rows),
        min_pair_candidate_rows=int(min_pair_candidate_rows),
        min_reconstructed_pair_rows=int(min_reconstructed_pair_rows),
        min_pair_delta_rows=int(min_pair_delta_rows),
        min_left_sources=int(min_left_sources),
        min_left_seeds=int(min_left_seeds),
        min_left_fault_families=int(min_left_fault_families),
        min_fault_pairs=int(min_fault_pairs),
        min_warmup_pairs=int(min_warmup_pairs),
        min_onset_pairs=int(min_onset_pairs),
        min_hold_steps=int(min_hold_steps),
        min_direction_families=int(min_direction_families),
        max_left_source_dominance=float(max_left_source_dominance),
        max_left_seed_dominance=float(max_left_seed_dominance),
        max_direction_family_dominance=float(max_direction_family_dominance),
    )
    diversity_summary = {
        "pair_candidate_rows": _sequence_diversity(pair_candidate_rows),
        "balanced_pair_rows": _sequence_diversity(pair_rows),
        "pair_delta_sequence_rows": _sequence_diversity(pair_delta_sequence_rows),
        "boundary_rows": _sequence_diversity(pair_rows),
        "accepted_primary_sequence_effective": _sequence_diversity(accepted_rows),
        "accepted_pair_delta_sequence_effective": _sequence_diversity(accepted_pair_delta),
        "accepted_directional_degradation": _sequence_diversity(accepted_degradation),
        "accepted_directional_improvement": _sequence_diversity(accepted_improvement),
        "train_public": _sequence_diversity(train_rows),
        "eval_public": _sequence_diversity(eval_rows),
        "source_holdout_public": _sequence_diversity(holdout_rows),
    }
    all_rejections = [*pair_rejections, *snapshot_rejections, *replay_rejections]
    direction_hold_summary = _direction_hold_summary(replay_rows, accepted_rows, tuple(int(value) for value in hold_steps_grid))
    best_rows = _best_sequence_by_pair(replay_rows)

    write_csv_rows(run_dir / "pair_candidate_rows.csv", pair_candidate_rows, fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "balanced_pair_rows.csv", pair_rows, fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "reconstructed_pair_rows.csv", reconstructed_pair_rows, fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "sequence_effective_rows.csv", replay_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "accepted_sequence_effective_rows.csv", accepted_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_pair_delta_rows.csv", accepted_pair_delta, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "best_sequence_by_pair.csv", best_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "direction_hold_summary.csv", direction_hold_summary, fieldnames=DIRECTION_HOLD_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "train_public_rows.csv", train_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "eval_public_rows.csv", eval_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", holdout_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", all_rejections)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    accepted_metrics = diversity_summary["accepted_primary_sequence_effective"]
    summary = {
        "run_type": "v4_cross_source_sequence_effective_pair_refresh",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "boundary_rows": boundary_rows_path,
        "reconstructed_snapshot_rows_input": reconstructed_snapshot_rows_path,
        "alpha": float(alpha),
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "hold_steps_grid": list(int(value) for value in hold_steps_grid),
        "source_rows_count": int(len(source_rows)),
        "candidate_plan_rows_count": int(len(candidate_plan_rows)),
        "previous_reconstructed_snapshot_rows_count": int(len(previous_reconstructed_snapshot_rows)),
        "boundary_source_rows": int(len(boundary_rows)),
        "pair_candidate_rows": int(len(pair_candidate_rows)),
        "paired_candidate_rows": int(len(pair_rows)),
        "balanced_pair_rows": int(len(pair_rows)),
        "reconstructed_pair_rows": int(len(reconstructed_pair_rows)),
        "reconstructed_snapshot_rows": int(len(snapshot_rows)),
        "sequence_effective_rows": int(len(replay_rows)),
        "pair_delta_sequence_rows": int(len(pair_delta_sequence_rows)),
        "accepted_primary_sequence_effective_rows": int(len(accepted_rows)),
        "accepted_pair_delta_sequence_effective_rows": int(len(accepted_pair_delta)),
        "accepted_directional_degradation_rows": int(len(accepted_degradation)),
        "accepted_directional_improvement_rows": int(len(accepted_improvement)),
        "success_flip_rows": int(len(success_flip_rows)),
        "collision_flip_rows": int(len(collision_flip_rows)),
        "train_public_rows": int(len(train_rows)),
        "eval_public_rows": int(len(eval_rows)),
        "source_holdout_public_rows": int(len(holdout_rows)),
        "unique_left_source_group_count": int(accepted_metrics["unique_left_source_group_count"]),
        "unique_left_seed_count": int(accepted_metrics["unique_left_seed_count"]),
        "unique_left_fault_family_count": int(accepted_metrics["unique_left_fault_family_count"]),
        "unique_fault_family_pair_count": int(accepted_metrics["unique_fault_family_pair_count"]),
        "max_left_source_group_dominance": float(accepted_metrics["max_left_source_group_dominance"]),
        "max_left_seed_dominance": float(accepted_metrics["max_left_seed_dominance"]),
        "max_direction_family_dominance": float(accepted_metrics["max_direction_family_dominance"]),
        "max_abs_margin_delta": max_abs_margin_delta,
        "max_degradation_margin_delta": max_degradation_margin_delta,
        "max_improvement_margin_delta": max_improvement_margin_delta,
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "max_obstacle_distance": float(max_obstacle_distance),
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "strong_min_rows": int(strong_min_rows),
        "sparse_min_rows": int(sparse_min_rows),
        "min_pair_candidate_rows": int(min_pair_candidate_rows),
        "min_reconstructed_pair_rows": int(min_reconstructed_pair_rows),
        "min_pair_delta_rows": int(min_pair_delta_rows),
        "min_left_sources": int(min_left_sources),
        "min_left_seeds": int(min_left_seeds),
        "min_left_fault_families": int(min_left_fault_families),
        "min_fault_pairs": int(min_fault_pairs),
        "min_warmup_pairs": int(min_warmup_pairs),
        "min_onset_pairs": int(min_onset_pairs),
        "min_hold_steps": int(min_hold_steps),
        "min_direction_families": int(min_direction_families),
        "max_left_source_dominance_threshold": float(max_left_source_dominance),
        "max_left_seed_dominance_threshold": float(max_left_seed_dominance),
        "max_direction_family_dominance_threshold": float(max_direction_family_dominance),
        "max_pairs_per_left_source_group": int(max_pairs_per_left_source_group),
        "max_pairs_per_right_source_group": int(max_pairs_per_right_source_group),
        "max_pairs_per_left_seed": int(max_pairs_per_left_seed),
        "max_pairs_per_fault_family_pair": int(max_pairs_per_fault_family_pair),
        "max_pairs_per_left_fault_family": int(max_pairs_per_left_fault_family),
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
        "pair_candidate_rows_csv": run_dir / "pair_candidate_rows.csv",
        "balanced_pair_rows_csv": run_dir / "balanced_pair_rows.csv",
        "reconstructed_pair_rows_csv": run_dir / "reconstructed_pair_rows.csv",
        "reconstructed_snapshot_rows_csv": run_dir / "reconstructed_snapshot_rows.csv",
        "sequence_effective_rows_csv": run_dir / "sequence_effective_rows.csv",
        "accepted_sequence_effective_rows_csv": run_dir / "accepted_sequence_effective_rows.csv",
        "accepted_pair_delta_rows_csv": run_dir / "accepted_pair_delta_rows.csv",
        "train_public_rows_csv": run_dir / "train_public_rows.csv",
        "eval_public_rows_csv": run_dir / "eval_public_rows.csv",
        "source_holdout_public_rows_csv": run_dir / "source_holdout_public_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _cross_source_gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def _pair_delta_gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
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
            "gate_name": "source_diversity",
            "value": summary["balanced_unique_left_source_group_count"],
            "threshold": summary["min_left_sources"],
            "passed": int(summary["balanced_unique_left_source_group_count"]) >= int(summary["min_left_sources"]),
            "notes": "strong pair-delta source diversity gate",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M850 cannot promote",
        },
    ]


def run_pair_delta_focused_source_balanced_mining(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    pair_candidate_rows_path: Path,
    boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_replay_pairs: int,
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
    margin_delta_threshold: float,
    action_l2_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
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
    max_rows_per_left_source_group: int,
    max_rows_per_left_seed: int,
    max_rows_per_left_fault_family: int,
    max_rows_per_fault_family_pair: int,
    max_rows_per_direction: int,
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
        raise ValueError("M850 pair-delta mining requires an online recurrent checkpoint")
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

    pair_candidate_rows_raw = read_csv_rows(pair_candidate_rows_path)
    boundary_rows = read_csv_rows(boundary_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    pair_rows, pair_rejections = pair_rows_from_candidate_rows(
        pair_candidate_rows_raw,
        boundary_rows,
        max_replay_pairs=int(max_replay_pairs),
        min_first_action_l2=float(action_l2_threshold),
        max_pairs_per_left_source_group=int(max_pairs_per_left_source_group),
        max_pairs_per_right_source_group=int(max_pairs_per_right_source_group),
        max_pairs_per_left_seed=int(max_pairs_per_left_seed),
        max_pairs_per_fault_family_pair=int(max_pairs_per_fault_family_pair),
    )
    requests = _snapshot_requests(pair_rows)
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
    replayable_pair_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    replayable_pairs_by_id: dict[str, dict[str, Any]] = {}
    for pair in pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        replayable_pair_rows.append({key: pair.get(key, "") for key in PAIR_FIELDS})
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
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": f"pair_delta_replay_error:{type(exc).__name__}"})
            continue
        pair_delta_rows.extend(rows)
        accepted_pair_delta_rows.extend(
            accepted_sequence_effective_rows_for_pair(
                rows,
                boundary_margin_threshold=float(boundary_margin_threshold),
                margin_delta_threshold=float(margin_delta_threshold),
                action_l2_threshold=float(action_l2_threshold),
            )
        )
        _append_progress(progress_path, {"stage": "pair_delta_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)})

    balanced_pair_delta_rows = balance_pair_delta_rows(
        accepted_pair_delta_rows,
        max_rows_per_left_source_group=int(max_rows_per_left_source_group),
        max_rows_per_left_seed=int(max_rows_per_left_seed),
        max_rows_per_left_fault_family=int(max_rows_per_left_fault_family),
        max_rows_per_fault_family_pair=int(max_rows_per_fault_family_pair),
        max_rows_per_direction=int(max_rows_per_direction),
    )

    component_control_rows: list[dict[str, Any]] = []
    component_pair_ids = []
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
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": f"component_control_error:{type(exc).__name__}"})

    train_rows, eval_rows, holdout_rows = split_source_aware(balanced_pair_delta_rows)
    accepted_degradation = [row for row in accepted_pair_delta_rows if row.get("accepted_class") == "directional_degradation"]
    accepted_improvement = [row for row in accepted_pair_delta_rows if row.get("accepted_class") == "directional_improvement"]
    success_flip_rows = [row for row in pair_delta_rows if parse_bool(row.get("success_flip", False))]
    collision_flip_rows = [row for row in pair_delta_rows if parse_bool(row.get("collision_flip", False))]
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in pair_delta_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_pair_delta_focused_mining(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        accepted_pair_delta_rows=accepted_pair_delta_rows,
        balanced_pair_delta_rows=balanced_pair_delta_rows,
        all_pair_delta_rows=pair_delta_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        strong_min_rows=int(strong_min_rows),
        sparse_min_rows=int(sparse_min_rows),
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
        "pair_candidate_rows": _sequence_diversity(pair_candidate_rows_raw),
        "replay_pair_rows": _sequence_diversity(pair_rows),
        "pair_delta_sequence_rows": _sequence_diversity(pair_delta_rows),
        "accepted_pair_delta": _sequence_diversity(accepted_pair_delta_rows),
        "balanced_pair_delta": _sequence_diversity(balanced_pair_delta_rows),
        "component_control_rows": _sequence_diversity(component_control_rows),
        "train_public": _sequence_diversity(train_rows),
        "eval_public": _sequence_diversity(eval_rows),
        "source_holdout_public": _sequence_diversity(holdout_rows),
    }
    balanced_metrics = diversity_summary["balanced_pair_delta"]
    accepted_metrics = diversity_summary["accepted_pair_delta"]
    all_rejections = [*pair_rejections, *snapshot_rejections, *replay_rejections]

    write_csv_rows(run_dir / "replay_pair_rows.csv", pair_rows, fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "reconstructed_pair_rows.csv", replayable_pair_rows, fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "pair_delta_sequence_rows.csv", pair_delta_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "accepted_pair_delta_rows.csv", accepted_pair_delta_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "balanced_pair_delta_rows.csv", balanced_pair_delta_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "component_control_rows.csv", component_control_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "train_public_rows.csv", train_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "eval_public_rows.csv", eval_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", holdout_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", all_rejections)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    summary = {
        "run_type": "v4_pair_delta_focused_source_balanced_mining",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "pair_candidate_rows": pair_candidate_rows_path,
        "boundary_rows": boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "hold_steps_grid": list(int(value) for value in hold_steps_grid),
        "pair_candidate_rows_count": int(len(pair_candidate_rows_raw)),
        "replay_pair_rows": int(len(pair_rows)),
        "reconstructed_pair_rows": int(len(replayable_pair_rows)),
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
        "accepted_unique_left_source_group_count": int(accepted_metrics["unique_left_source_group_count"]),
        "balanced_unique_left_source_group_count": int(balanced_metrics["unique_left_source_group_count"]),
        "balanced_unique_left_seed_count": int(balanced_metrics["unique_left_seed_count"]),
        "balanced_unique_left_fault_family_count": int(balanced_metrics["unique_left_fault_family_count"]),
        "balanced_unique_fault_family_pair_count": int(balanced_metrics["unique_fault_family_pair_count"]),
        "balanced_max_left_source_group_dominance": float(balanced_metrics["max_left_source_group_dominance"]),
        "balanced_max_left_seed_dominance": float(balanced_metrics["max_left_seed_dominance"]),
        "balanced_max_direction_dominance": float(_max_share(balanced_pair_delta_rows, "direction")),
        "max_abs_margin_delta": max_abs_margin_delta,
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "strong_min_rows": int(strong_min_rows),
        "sparse_min_rows": int(sparse_min_rows),
        "min_left_sources": int(min_left_sources),
        "min_left_seeds": int(min_left_seeds),
        "min_left_fault_families": int(min_left_fault_families),
        "min_fault_pairs": int(min_fault_pairs),
        "min_hold_steps": int(min_hold_steps),
        "max_left_source_dominance_threshold": float(max_left_source_dominance),
        "max_left_seed_dominance_threshold": float(max_left_seed_dominance),
        "max_direction_dominance_threshold": float(max_direction_dominance),
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
        "pair_delta_sequence_rows_csv": run_dir / "pair_delta_sequence_rows.csv",
        "accepted_pair_delta_rows_csv": run_dir / "accepted_pair_delta_rows.csv",
        "balanced_pair_delta_rows_csv": run_dir / "balanced_pair_delta_rows.csv",
        "component_control_rows_csv": run_dir / "component_control_rows.csv",
        "train_public_rows_csv": run_dir / "train_public_rows.csv",
        "eval_public_rows_csv": run_dir / "eval_public_rows.csv",
        "source_holdout_public_rows_csv": run_dir / "source_holdout_public_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _pair_delta_gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 pair-delta-focused source-balanced mining.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--pair-candidate-rows", type=Path, required=True)
    parser.add_argument("--boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-replay-pairs", type=int, default=160)
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
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--strong-min-rows", type=int, default=60)
    parser.add_argument("--sparse-min-rows", type=int, default=30)
    parser.add_argument("--min-left-sources", type=int, default=8)
    parser.add_argument("--min-left-seeds", type=int, default=4)
    parser.add_argument("--min-left-fault-families", type=int, default=5)
    parser.add_argument("--min-fault-pairs", type=int, default=10)
    parser.add_argument("--min-hold-steps", type=int, default=2)
    parser.add_argument("--max-left-source-dominance", type=float, default=0.30)
    parser.add_argument("--max-left-seed-dominance", type=float, default=0.35)
    parser.add_argument("--max-direction-dominance", type=float, default=0.60)
    parser.add_argument("--max-pairs-per-left-source-group", type=int, default=24)
    parser.add_argument("--max-pairs-per-right-source-group", type=int, default=24)
    parser.add_argument("--max-pairs-per-left-seed", type=int, default=64)
    parser.add_argument("--max-pairs-per-fault-family-pair", type=int, default=32)
    parser.add_argument("--max-rows-per-left-source-group", type=int, default=8)
    parser.add_argument("--max-rows-per-left-seed", type=int, default=16)
    parser.add_argument("--max-rows-per-left-fault-family", type=int, default=16)
    parser.add_argument("--max-rows-per-fault-family-pair", type=int, default=8)
    parser.add_argument("--max-rows-per-direction", type=int, default=24)
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
    summary = run_pair_delta_focused_source_balanced_mining(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        pair_candidate_rows_path=args.pair_candidate_rows,
        boundary_rows_path=args.boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_replay_pairs=int(args.max_replay_pairs),
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
        margin_delta_threshold=float(args.margin_delta_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        strong_min_rows=int(args.strong_min_rows),
        sparse_min_rows=int(args.sparse_min_rows),
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
        max_rows_per_left_source_group=int(args.max_rows_per_left_source_group),
        max_rows_per_left_seed=int(args.max_rows_per_left_seed),
        max_rows_per_left_fault_family=int(args.max_rows_per_left_fault_family),
        max_rows_per_fault_family_pair=int(args.max_rows_per_fault_family_pair),
        max_rows_per_direction=int(args.max_rows_per_direction),
        component_control_max_pairs=int(args.component_control_max_pairs),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
