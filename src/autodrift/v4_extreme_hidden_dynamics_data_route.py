"""No-training extreme hidden-dynamics history-intervention data route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from torch import nn

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
from autodrift.sequence_command_response_intervention import SEQUENCE_VARIANTS
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import relocate_temporal_snapshot
from autodrift.temporal_action_response_mismatch import TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_boundary_window_retarget import (
    _append_progress,
    parse_bool,
    parse_float_list,
)
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import (
    DEFAULT_HALF_WIDTH_DELTAS,
    DEFAULT_LATERAL_DELTAS,
    DEFAULT_OBSTACLE_TIMING_DELTAS,
    DEFAULT_TARGET_MARGINS,
    WARMUP_MODES,
    _closest_primary_margin,
    _margin_band_counts,
    _snapshot_meta,
    _snapshot_uid,
    _summary_rows,
    _value_counts,
    build_fault_variants,
    build_source_groups,
    collect_warmup_snapshots,
    plan_boundary_candidates,
)
from autodrift.v4_normal_margin_residual_calibration import replay_calibrated_sequence_variant
from autodrift.v4_residual_closed_loop_replay import _load_residual_head


HISTORY_VARIANTS = (
    "reset_hidden_each_step",
    "reset_hidden_then_normal",
    "zero_command_obs",
    "command_shift_obs",
    "response_delay_obs",
)
UNSUPPORTED_HISTORY_VARIANTS = ("wrong_cross_fault_history",)
ONSET_BUCKETS = (
    "preexisting",
    "warmup",
    "pre_emergency",
    "emergency_entry",
    "mid_maneuver",
    "recovery",
)

EXTREME_PLAN_EXTRA_FIELDS = [
    "preferred_fidelity_class",
    "wrong_fidelity_class",
    "fault_onset_bucket",
    "ego_vx_norm",
    "ego_vy_norm",
    "ego_yaw_rate_norm",
]

INTERVENTION_FIELDS = [
    "candidate_id",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "step",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fidelity_class",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fidelity_class",
    "fault_family_pair",
    "fault_onset_bucket",
    "source_axis",
    "boundary_axis",
    "horizon",
    "alpha",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "intervention_variant",
    "supported_intervention",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "intervention_success",
    "intervention_collision",
    "intervention_margin",
    "margin_gap_from_normal",
    "success_drop_from_normal",
    "first_action_l2_from_normal",
    "prefix_l2_mean",
    "prefix_l2_max",
    "terminal_reason",
]

ACCEPTED_FIELDS = [
    "candidate_id",
    "accepted_class",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "step",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fidelity_class",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fidelity_class",
    "fault_family_pair",
    "fault_onset_bucket",
    "source_axis",
    "boundary_axis",
    "horizon",
    "alpha",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "best_gap_variant",
    "best_margin_gap_from_normal",
    "best_action_gap_variant",
    "best_prefix_l2_mean",
    "best_first_action_l2",
    "intervention_collision_count",
    "intervention_success_drop_count",
    "history_sensitive",
    "accepted_reason",
]

MATCHED_PAIR_FIELDS = [
    "pair_id",
    "left_candidate_id",
    "right_candidate_id",
    "left_seed",
    "right_seed",
    "left_fault_family",
    "right_fault_family",
    "left_fidelity_class",
    "right_fidelity_class",
    "left_warmup_mode",
    "right_warmup_mode",
    "left_onset_bucket",
    "right_onset_bucket",
    "ego_response_distance",
    "obstacle_geometry_distance",
    "first_action_l2",
    "normal_margin_gap_abs",
    "pair_type",
]

GATE_SUMMARY_FIELDS = ["gate_name", "value", "threshold", "passed", "notes"]


class IdentityResidualGate(nn.Module):
    """Feature-independent identity gate for no-training residual replay."""

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return torch.ones((features.shape[0], 3), dtype=features.dtype, device=features.device)


def fault_onset_bucket(fault: FaultSpec, *, snapshot_step: int, warmup_steps: int) -> str:
    activation = int(fault.activation_step)
    if activation <= 0:
        return "preexisting"
    if activation <= int(warmup_steps):
        return "warmup"
    if activation <= max(int(warmup_steps) + 10, int(snapshot_step) - 15):
        return "pre_emergency"
    if activation <= int(snapshot_step):
        return "emergency_entry"
    if activation <= int(snapshot_step) + 20:
        return "mid_maneuver"
    return "recovery"


def _m825_snapshot_meta(
    source_group: dict[str, Any],
    snapshot: TemporalSnapshot,
    *,
    source_index: int,
    fault: FaultSpec,
    warmup_steps: int,
) -> dict[str, Any]:
    meta = _snapshot_meta(source_group, snapshot, source_index=source_index)
    obs = np.asarray(snapshot.observation, dtype=np.float32)
    meta.update(
        {
            "preferred_fidelity_class": str(fault.fidelity_class),
            "wrong_fidelity_class": str(NOMINAL_FAULT.fidelity_class),
            "fault_onset_bucket": fault_onset_bucket(
                fault,
                snapshot_step=int(snapshot.step),
                warmup_steps=int(warmup_steps),
            ),
            "ego_vx_norm": float(obs[0]) if obs.shape[0] > 0 else float("nan"),
            "ego_vy_norm": float(obs[1]) if obs.shape[0] > 1 else float("nan"),
            "ego_yaw_rate_norm": float(obs[2]) if obs.shape[0] > 2 else float("nan"),
        }
    )
    return meta


def _normal_ok(row: dict[str, Any]) -> bool:
    margin = _finite_float(row.get("normal_margin"))
    return bool(not parse_bool(row.get("normal_collision", False)) and np.isfinite(margin))


def _intervention_stats(
    interventions: list[dict[str, Any]],
) -> dict[str, Any]:
    supported = [row for row in interventions if parse_bool(row.get("supported_intervention", False))]
    gaps = [
        _finite_float(row.get("margin_gap_from_normal"))
        for row in supported
        if np.isfinite(_finite_float(row.get("margin_gap_from_normal")))
    ]
    prefix = [
        _finite_float(row.get("prefix_l2_mean"))
        for row in supported
        if np.isfinite(_finite_float(row.get("prefix_l2_mean")))
    ]
    first_action = [
        _finite_float(row.get("first_action_l2_from_normal"))
        for row in supported
        if np.isfinite(_finite_float(row.get("first_action_l2_from_normal")))
    ]
    best_gap_row = max(
        supported,
        key=lambda row: _finite_float(row.get("margin_gap_from_normal"), default=-float("inf")),
        default={},
    )
    best_prefix_row = max(
        supported,
        key=lambda row: _finite_float(row.get("prefix_l2_mean"), default=-float("inf")),
        default={},
    )
    return {
        "supported_interventions": int(len(supported)),
        "best_margin_gap_from_normal": max(gaps, default=float("nan")),
        "best_gap_variant": str(best_gap_row.get("intervention_variant", "")),
        "best_prefix_l2_mean": max(prefix, default=float("nan")),
        "best_action_gap_variant": str(best_prefix_row.get("intervention_variant", "")),
        "best_first_action_l2": max(first_action, default=float("nan")),
        "intervention_collision_count": int(
            sum(1 for row in supported if parse_bool(row.get("intervention_collision", False)))
        ),
        "intervention_success_drop_count": int(
            sum(1 for row in supported if parse_bool(row.get("success_drop_from_normal", False)))
        ),
    }


def accepted_history_rows_for_candidate(
    normal_row: dict[str, Any],
    interventions: list[dict[str, Any]],
    *,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    require_action_gap: bool = False,
) -> list[dict[str, Any]]:
    stats = _intervention_stats(interventions)
    margin_gap = _finite_float(stats.get("best_margin_gap_from_normal"))
    prefix_gap = _finite_float(stats.get("best_prefix_l2_mean"))
    first_gap = _finite_float(stats.get("best_first_action_l2"))
    action_gap = max(value for value in (prefix_gap, first_gap) if np.isfinite(value)) if any(
        np.isfinite(value) for value in (prefix_gap, first_gap)
    ) else float("nan")
    history_sensitive = bool(
        np.isfinite(margin_gap)
        and margin_gap >= min(float(primary_margin_gap_threshold), float(mitigation_margin_gap_threshold))
    ) or bool(np.isfinite(action_gap) and action_gap >= float(action_l2_threshold))
    action_pass = bool(not require_action_gap or (np.isfinite(action_gap) and action_gap >= float(action_l2_threshold)))
    base = {
        key: normal_row.get(key, "")
        for key in [
            "candidate_id",
            "source_group_id",
            "snapshot_uid",
            "source_index",
            "seed",
            "step",
            "warmup_mode",
            "preferred_fault",
            "preferred_fault_family",
            "preferred_fidelity_class",
            "wrong_fault",
            "wrong_fault_family",
            "wrong_fidelity_class",
            "fault_family_pair",
            "fault_onset_bucket",
            "source_axis",
            "boundary_axis",
            "horizon",
            "alpha",
            "target_obstacle_body_x",
            "target_obstacle_body_y",
            "target_obstacle_half_width",
            "normal_success",
            "normal_collision",
            "normal_margin",
        ]
    }
    base.update(
        {
            "best_gap_variant": stats["best_gap_variant"],
            "best_margin_gap_from_normal": margin_gap,
            "best_action_gap_variant": stats["best_action_gap_variant"],
            "best_prefix_l2_mean": prefix_gap,
            "best_first_action_l2": first_gap,
            "intervention_collision_count": int(stats["intervention_collision_count"]),
            "intervention_success_drop_count": int(stats["intervention_success_drop_count"]),
            "history_sensitive": history_sensitive,
        }
    )
    accepted: list[dict[str, Any]] = []
    if _normal_ok(normal_row) and np.isfinite(margin_gap) and margin_gap >= float(primary_margin_gap_threshold) and action_pass:
        accepted.append({**base, "accepted_class": "primary_self_id", "accepted_reason": "normal_margin_history_degradation"})
    normal_margin = _finite_float(normal_row.get("normal_margin"))
    if np.isfinite(normal_margin) and np.isfinite(margin_gap) and margin_gap >= float(mitigation_margin_gap_threshold):
        accepted.append({**base, "accepted_class": "mitigation", "accepted_reason": "normal_history_mitigates_worst_intervention"})
    return accepted


def source_diversity_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": int(len(rows)),
        "unique_seed_count": unique_count(rows, "seed"),
        "unique_source_group_count": unique_count(rows, "source_group_id"),
        "unique_source_index_count": unique_count(rows, "source_index"),
        "unique_fault_family_pair_count": unique_count(rows, "fault_family_pair"),
        "unique_fault_family_count": unique_count(rows, "preferred_fault_family"),
        "unique_fidelity_class_count": unique_count(rows, "preferred_fidelity_class"),
        "unique_warmup_mode_count": unique_count(rows, "warmup_mode"),
        "unique_onset_bucket_count": unique_count(rows, "fault_onset_bucket"),
        "unique_boundary_axis_count": unique_count(rows, "boundary_axis"),
        "max_seed_dominance": max_share(rows, "seed"),
        "max_source_group_dominance": max_share(rows, "source_group_id"),
        "max_fault_family_pair_dominance": max_share(rows, "fault_family_pair"),
        "max_fault_family_dominance": max_share(rows, "preferred_fault_family"),
        "max_warmup_mode_dominance": max_share(rows, "warmup_mode"),
        "max_onset_bucket_dominance": max_share(rows, "fault_onset_bucket"),
        "current_model_fault_rows": int(sum(1 for row in rows if row.get("preferred_fidelity_class") == "current_model_fault")),
        "current_model_proxy_rows": int(sum(1 for row in rows if row.get("preferred_fidelity_class") == "current_model_proxy")),
    }


def matched_pair_diversity_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    families = [
        f"{row.get('left_fault_family', '')}->{row.get('right_fault_family', '')}"
        for row in rows
    ]
    fidelity_pairs = [
        f"{row.get('left_fidelity_class', '')}->{row.get('right_fidelity_class', '')}"
        for row in rows
    ]
    seed_pairs = [f"{row.get('left_seed', '')}->{row.get('right_seed', '')}" for row in rows]
    return {
        "rows": int(len(rows)),
        "unique_left_seed_count": unique_count(rows, "left_seed"),
        "unique_right_seed_count": unique_count(rows, "right_seed"),
        "unique_seed_pair_count": int(len(set(seed_pairs))),
        "unique_left_fault_family_count": unique_count(rows, "left_fault_family"),
        "unique_right_fault_family_count": unique_count(rows, "right_fault_family"),
        "unique_fault_family_pair_count": int(len(set(families))),
        "unique_fidelity_pair_count": int(len(set(fidelity_pairs))),
        "unique_left_warmup_mode_count": unique_count(rows, "left_warmup_mode"),
        "unique_right_warmup_mode_count": unique_count(rows, "right_warmup_mode"),
        "unique_onset_pair_count": int(
            len({f"{row.get('left_onset_bucket', '')}->{row.get('right_onset_bucket', '')}" for row in rows})
        ),
        "max_left_seed_dominance": max_share(rows, "left_seed"),
        "max_right_seed_dominance": max_share(rows, "right_seed"),
        "max_left_fault_family_dominance": max_share(rows, "left_fault_family"),
        "max_right_fault_family_dominance": max_share(rows, "right_fault_family"),
    }


def classify_extreme_hidden_dynamics_route(
    *,
    actor_changed: bool,
    residual_changed: bool,
    unsupported_variants: list[str],
    source_snapshots: int,
    replay_errors: int,
    accepted_self_id_rows: list[dict[str, Any]],
    accepted_mitigation_rows: list[dict[str, Any]],
    min_self_id_rows: int,
    min_seeds: int,
    min_source_groups: int,
    min_fault_pairs: int,
    min_warmup_modes: int,
    min_onset_buckets: int,
    max_seed_dominance: float,
    max_source_group_dominance: float,
    max_fault_pair_dominance: float,
    history_sensitive_candidate_rows: int,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_extreme_hidden_dynamics_data_route_contract_violation"
    if int(source_snapshots) <= 0 or (int(replay_errors) > 0 and not accepted_self_id_rows and not accepted_mitigation_rows):
        return "v4_extreme_hidden_dynamics_data_route_sampling_failure"
    accepted = list(accepted_self_id_rows)
    if accepted and source_diversity_metrics(accepted)["current_model_fault_rows"] == 0:
        return "v4_extreme_hidden_dynamics_data_route_proxy_only"
    if int(history_sensitive_candidate_rows) <= 0 and not accepted_self_id_rows and not accepted_mitigation_rows:
        return "v4_extreme_hidden_dynamics_data_route_history_insensitive"
    metrics = source_diversity_metrics(accepted)
    pass_gate = bool(
        len(accepted) >= int(min_self_id_rows)
        and metrics["unique_seed_count"] >= int(min_seeds)
        and metrics["unique_source_group_count"] >= int(min_source_groups)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["unique_warmup_mode_count"] >= int(min_warmup_modes)
        and metrics["unique_onset_bucket_count"] >= int(min_onset_buckets)
        and metrics["max_seed_dominance"] <= float(max_seed_dominance)
        and metrics["max_source_group_dominance"] <= float(max_source_group_dominance)
        and metrics["max_fault_family_pair_dominance"] <= float(max_fault_pair_dominance)
        and not unsupported_variants
    )
    if pass_gate:
        return "v4_extreme_hidden_dynamics_data_route_pass"
    return "v4_extreme_hidden_dynamics_data_route_sparse"


def _intervention_row(
    *,
    normal_meta: dict[str, Any],
    variant: str,
    normal: dict[str, Any],
    result: dict[str, Any] | None,
    supported: bool,
) -> dict[str, Any]:
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    if result is None:
        result = {}
    variant_margin = _finite_float(result.get("min_clearance_margin"))
    margin_gap = normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) else float("nan")
    first_gap = _finite_float(result.get("first_action_l2_from_reference"))
    if not np.isfinite(first_gap):
        first_gap = _finite_float(result.get("first_action_drift_vs_base_normal"))
    return {
        **normal_meta,
        "intervention_variant": variant,
        "supported_intervention": bool(supported),
        "normal_success": parse_bool(normal.get("success", False)),
        "normal_collision": parse_bool(normal.get("collision", False)),
        "normal_margin": normal_margin,
        "intervention_success": parse_bool(result.get("success", False)) if supported else "",
        "intervention_collision": parse_bool(result.get("collision", False)) if supported else "",
        "intervention_margin": variant_margin if supported else "",
        "margin_gap_from_normal": margin_gap if supported else "",
        "success_drop_from_normal": bool(parse_bool(normal.get("success", False)) and not parse_bool(result.get("success", False))) if supported else "",
        "first_action_l2_from_normal": first_gap if supported else "",
        "prefix_l2_mean": _finite_float(result.get("prefix_l2_mean")) if supported else "",
        "prefix_l2_max": _finite_float(result.get("prefix_l2_max")) if supported else "",
        "terminal_reason": str(result.get("terminal_reason", "")) if supported else "unsupported",
    }


def _replay_plan(
    *,
    plan: dict[str, Any],
    snapshot: TemporalSnapshot,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    env_config: Any,
    response_dim: int,
    history_variants: tuple[str, ...],
    unsupported_variants: tuple[str, ...],
    max_continuation_steps: int,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    require_action_gap: bool,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    meta = dict(plan)
    try:
        relocated = relocate_temporal_snapshot(
            snapshot,
            body_longitudinal=float(plan["target_obstacle_body_x"]),
            body_lateral=float(plan["target_obstacle_body_y"]),
            half_width=float(plan["target_obstacle_half_width"]),
        )
    except Exception as exc:
        normal_row = {
            **meta,
            "reconstructed": False,
            "rejection_reason": f"relocation_error:{type(exc).__name__}",
        }
        return normal_row, [], []

    normal, normal_actions = replay_calibrated_sequence_variant(
        model=model,
        residual_head=residual_head,
        calibrator=identity_gate,
        snapshot=relocated,
        env_config=env_config,
        variant="normal",
        horizon=int(plan.get("horizon", 6)),
        response_dim=response_dim,
        reference_actions=None,
        base_reference_actions=None,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(plan.get("alpha", 0.2)),
        device=device,
    )
    normal_row = {
        **meta,
        "reconstructed": True,
        "rejection_reason": "",
        **normal,
        "normal_success": parse_bool(normal.get("success", False)),
        "normal_collision": parse_bool(normal.get("collision", False)),
        "normal_margin": _finite_float(normal.get("min_clearance_margin")),
    }
    intervention_rows: list[dict[str, Any]] = []
    normal_meta = {
        key: normal_row.get(key, "")
        for key in [
            "candidate_id",
            "source_group_id",
            "snapshot_uid",
            "source_index",
            "seed",
            "step",
            "warmup_mode",
            "preferred_fault",
            "preferred_fault_family",
            "preferred_fidelity_class",
            "wrong_fault",
            "wrong_fault_family",
            "wrong_fidelity_class",
            "fault_family_pair",
            "fault_onset_bucket",
            "source_axis",
            "boundary_axis",
            "horizon",
            "alpha",
            "target_obstacle_body_x",
            "target_obstacle_body_y",
            "target_obstacle_half_width",
        ]
    }
    for variant in history_variants:
        result, _ = replay_calibrated_sequence_variant(
            model=model,
            residual_head=residual_head,
            calibrator=identity_gate,
            snapshot=relocated,
            env_config=env_config,
            variant=variant,
            horizon=int(plan.get("horizon", 6)),
            response_dim=response_dim,
            reference_actions=normal_actions,
            base_reference_actions=normal_actions,
            max_continuation_steps=int(max_continuation_steps),
            alpha=float(plan.get("alpha", 0.2)),
            device=device,
        )
        intervention_rows.append(
            _intervention_row(
                normal_meta=normal_meta,
                variant=variant,
                normal=normal,
                result=result,
                supported=True,
            )
        )
    for variant in unsupported_variants:
        intervention_rows.append(
            _intervention_row(
                normal_meta=normal_meta,
                variant=variant,
                normal=normal,
                result=None,
                supported=False,
            )
        )
    accepted = accepted_history_rows_for_candidate(
        normal_row,
        intervention_rows,
        primary_margin_gap_threshold=float(primary_margin_gap_threshold),
        mitigation_margin_gap_threshold=float(mitigation_margin_gap_threshold),
        action_l2_threshold=float(action_l2_threshold),
        require_action_gap=bool(require_action_gap),
    )
    stats = _intervention_stats(intervention_rows)
    normal_row.update(
        {
            "intervention_count": int(stats["supported_interventions"]),
            "unsupported_intervention_count": int(len(unsupported_variants)),
            "best_margin_gap_from_normal": _finite_float(stats["best_margin_gap_from_normal"]),
            "best_gap_variant": stats["best_gap_variant"],
            "best_prefix_l2_mean": _finite_float(stats["best_prefix_l2_mean"]),
            "best_action_gap_variant": stats["best_action_gap_variant"],
            "intervention_collision_count": int(stats["intervention_collision_count"]),
            "intervention_success_drop_count": int(stats["intervention_success_drop_count"]),
        }
    )
    return normal_row, intervention_rows, accepted


def select_balanced_rows(
    rows: list[dict[str, Any]],
    *,
    max_rows_per_seed: int,
    max_rows_per_source_group: int,
    max_rows_per_fault_pair: int,
    max_rows_per_onset_bucket: int,
    max_rows_per_warmup_mode: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("accepted_class", "")),
            str(row.get("preferred_fidelity_class", "")),
            str(row.get("fault_onset_bucket", "")),
            str(row.get("warmup_mode", "")),
            str(row.get("fault_family_pair", "")),
            -_finite_float(row.get("best_margin_gap_from_normal"), default=-1.0),
            -_finite_float(row.get("best_prefix_l2_mean"), default=-1.0),
        ),
    )
    for row in ordered:
        limits = {
            ("seed", str(row.get("seed", ""))): int(max_rows_per_seed),
            ("source_group_id", str(row.get("source_group_id", ""))): int(max_rows_per_source_group),
            ("fault_family_pair", str(row.get("fault_family_pair", ""))): int(max_rows_per_fault_pair),
            ("fault_onset_bucket", str(row.get("fault_onset_bucket", ""))): int(max_rows_per_onset_bucket),
            ("warmup_mode", str(row.get("warmup_mode", ""))): int(max_rows_per_warmup_mode),
        }
        if any(counts.get(key, 0) >= limit for key, limit in limits.items()):
            continue
        selected.append(row)
        for key in limits:
            counts[key] = counts.get(key, 0) + 1
    return selected


def build_matched_action_divergent_rows(
    normal_rows: list[dict[str, Any]],
    *,
    ego_distance_threshold: float,
    obstacle_distance_threshold: float,
    first_action_l2_threshold: float,
    max_pairs: int,
) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in normal_rows
        if parse_bool(row.get("reconstructed", False))
        and not parse_bool(row.get("collision", False))
        and np.isfinite(_finite_float(row.get("first_steer")))
    ]
    output: list[dict[str, Any]] = []
    for left_index, left in enumerate(candidates):
        if len(output) >= int(max_pairs):
            break
        left_action = np.asarray(
            [
                _finite_float(left.get("first_steer"), default=0.0),
                _finite_float(left.get("first_throttle"), default=0.0),
                _finite_float(left.get("first_brake"), default=0.0),
            ],
            dtype=np.float64,
        )
        left_ego = np.asarray(
            [
                _finite_float(left.get("ego_vx_norm"), default=0.0),
                _finite_float(left.get("ego_vy_norm"), default=0.0),
                _finite_float(left.get("ego_yaw_rate_norm"), default=0.0),
            ],
            dtype=np.float64,
        )
        left_geom = np.asarray(
            [
                _finite_float(left.get("target_obstacle_body_x"), default=0.0) / 80.0,
                _finite_float(left.get("target_obstacle_body_y"), default=0.0) / 8.0,
                _finite_float(left.get("target_obstacle_half_width"), default=0.0) / 2.0,
            ],
            dtype=np.float64,
        )
        for right in candidates[left_index + 1 :]:
            if len(output) >= int(max_pairs):
                break
            if str(left.get("preferred_fault_family", "")) == str(right.get("preferred_fault_family", "")):
                continue
            right_ego = np.asarray(
                [
                    _finite_float(right.get("ego_vx_norm"), default=0.0),
                    _finite_float(right.get("ego_vy_norm"), default=0.0),
                    _finite_float(right.get("ego_yaw_rate_norm"), default=0.0),
                ],
                dtype=np.float64,
            )
            right_geom = np.asarray(
                [
                    _finite_float(right.get("target_obstacle_body_x"), default=0.0) / 80.0,
                    _finite_float(right.get("target_obstacle_body_y"), default=0.0) / 8.0,
                    _finite_float(right.get("target_obstacle_half_width"), default=0.0) / 2.0,
                ],
                dtype=np.float64,
            )
            ego_distance = float(np.linalg.norm(left_ego - right_ego))
            obstacle_distance = float(np.linalg.norm(left_geom - right_geom))
            if ego_distance > float(ego_distance_threshold) or obstacle_distance > float(obstacle_distance_threshold):
                continue
            right_action = np.asarray(
                [
                    _finite_float(right.get("first_steer"), default=0.0),
                    _finite_float(right.get("first_throttle"), default=0.0),
                    _finite_float(right.get("first_brake"), default=0.0),
                ],
                dtype=np.float64,
            )
            first_action_l2 = float(np.linalg.norm(left_action - right_action))
            if first_action_l2 < float(first_action_l2_threshold):
                continue
            left_margin = _finite_float(left.get("min_clearance_margin"))
            right_margin = _finite_float(right.get("min_clearance_margin"))
            output.append(
                {
                    "pair_id": len(output),
                    "left_candidate_id": left.get("candidate_id", ""),
                    "right_candidate_id": right.get("candidate_id", ""),
                    "left_seed": left.get("seed", ""),
                    "right_seed": right.get("seed", ""),
                    "left_fault_family": left.get("preferred_fault_family", ""),
                    "right_fault_family": right.get("preferred_fault_family", ""),
                    "left_fidelity_class": left.get("preferred_fidelity_class", ""),
                    "right_fidelity_class": right.get("preferred_fidelity_class", ""),
                    "left_warmup_mode": left.get("warmup_mode", ""),
                    "right_warmup_mode": right.get("warmup_mode", ""),
                    "left_onset_bucket": left.get("fault_onset_bucket", ""),
                    "right_onset_bucket": right.get("fault_onset_bucket", ""),
                    "ego_response_distance": ego_distance,
                    "obstacle_geometry_distance": obstacle_distance,
                    "first_action_l2": first_action_l2,
                    "normal_margin_gap_abs": abs(left_margin - right_margin) if np.isfinite(left_margin) and np.isfinite(right_margin) else float("nan"),
                    "pair_type": "matched_action_divergent_proxy",
                }
            )
    return output


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
            "gate_name": "supported_history_variants",
            "value": summary["supported_history_variants"],
            "threshold": "reset/zero/delayed/shifted variants evaluated",
            "passed": bool(summary["supported_history_variants"]),
            "notes": f"unsupported={summary['unsupported_history_variants']}",
        },
        {
            "gate_name": "current_model_proxy_boundary_logged",
            "value": summary["proxy_rows"],
            "threshold": ">=0 and limitations artifact present",
            "passed": True,
            "notes": "proxy rows are not physical wheel-level claims",
        },
        {
            "gate_name": "primary_self_id_rows",
            "value": summary["accepted_self_id_rows"],
            "threshold": summary["min_self_id_rows"],
            "passed": int(summary["accepted_self_id_rows"]) >= int(summary["min_self_id_rows"]),
            "notes": "data-route evidence only",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M825 cannot promote",
        },
    ]


def _write_proxy_limitations(path: Path, scenario_config: dict[str, Any]) -> None:
    lines = [
        "# M825 Fault Proxy Limitations",
        "",
        "M825 uses only current single-track `VehicleParams` capability changes.",
        "Rows with `fidelity_class=current_model_proxy` are stress proxies for",
        "self-identification mining, not true wheel-level or corner-level fault",
        "physics.",
        "",
        "Allowed claim:",
        "",
        "- no-training evidence about command-response history sensitivity under",
        "  current-model or current-model-proxy capability changes.",
        "",
        "Forbidden claim:",
        "",
        "- physically faithful single-wheel blowout, split-mu, stuck-caliper,",
        "  halfshaft, suspension, or wheel-speed sensor dynamics.",
        "",
        "Future high-fidelity-only faults from the scenario config:",
        "",
        *[f"- {item}" for item in scenario_config.get("future_only_faults", [])],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_extreme_hidden_dynamics_data_route(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    seed_start: int,
    seed_count: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_source_groups: int,
    max_snapshots_per_group: int,
    max_candidates_per_snapshot: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    obstacle_timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    target_margins: tuple[float, ...],
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    require_action_gap: bool,
    min_self_id_rows: int,
    min_seeds: int,
    min_source_groups: int,
    min_fault_pairs: int,
    min_warmup_modes: int,
    min_onset_buckets: int,
    max_seed_dominance: float,
    max_source_group_dominance: float,
    max_fault_pair_dominance: float,
    matched_ego_distance_threshold: float,
    matched_obstacle_distance_threshold: float,
    matched_first_action_l2_threshold: float,
    max_matched_pairs: int,
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
        raise ValueError("M825 data route requires an online recurrent checkpoint")
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

    snapshots_by_uid: dict[str, TemporalSnapshot] = {}
    source_group_rows: list[dict[str, Any]] = []
    warmup_rows: list[dict[str, Any]] = []
    source_result_rows: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []
    normal_rows: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    snapshot_index = 0

    for group in source_groups:
        group_start = time.time()
        fault = fault_by_name[str(group["preferred_fault"])]
        group["preferred_fidelity_class"] = str(fault.fidelity_class)
        group["wrong_fidelity_class"] = str(NOMINAL_FAULT.fidelity_class)
        snapshots, source_row, warmup_row = collect_warmup_snapshots(
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
        source_row.update(
            {
                "preferred_fidelity_class": str(fault.fidelity_class),
                "wrong_fidelity_class": str(NOMINAL_FAULT.fidelity_class),
            }
        )
        warmup_row.update({"preferred_fidelity_class": str(fault.fidelity_class)})
        source_group_rows.append(source_row)
        warmup_rows.append(warmup_row)
        _append_progress(
            progress_path,
            {
                "source_group_id": int(group["source_group_id"]),
                "stage": "collect",
                "snapshots": int(len(snapshots)),
                "fault": fault.name,
                "fault_family": fault.family,
                "fidelity_class": fault.fidelity_class,
                "elapsed_seconds": float(time.time() - group_start),
            },
        )
        for snapshot in snapshots:
            uid = _snapshot_uid(int(group["source_group_id"]), snapshot)
            snapshots_by_uid[uid] = snapshot
            source_meta = _m825_snapshot_meta(
                group,
                snapshot,
                source_index=len(source_result_rows),
                fault=fault,
                warmup_steps=int(warmup_steps),
            )
            source_result, _ = replay_calibrated_sequence_variant(
                model=model,
                residual_head=residual_head,
                calibrator=identity_gate,
                snapshot=snapshot,
                env_config=env_config,
                variant="normal",
                horizon=6,
                response_dim=response_dim,
                reference_actions=None,
                base_reference_actions=None,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=resolved_device,
            )
            source_result_rows.append({**source_meta, **source_result})
            local_plan = plan_boundary_candidates(
                source_meta,
                source_result,
                alpha=float(alpha),
                target_margins=target_margins,
                obstacle_timing_deltas=obstacle_timing_deltas,
                lateral_deltas=lateral_deltas,
                half_width_deltas=half_width_deltas,
                collision_margin_floor=-1e-3,
                safe_margin_ceiling=1e-2,
                diagnostic_safe_margin_ceiling=2e-1,
                max_candidates_per_snapshot=int(max_candidates_per_snapshot),
            )
            for row in local_plan:
                row.update({key: source_meta[key] for key in EXTREME_PLAN_EXTRA_FIELDS})
                row["candidate_id"] = len(plan_rows)
                plan_rows.append(row)

    replay_errors = 0
    for plan in plan_rows:
        candidate_start = time.time()
        snapshot = snapshots_by_uid.get(str(plan["snapshot_uid"]))
        if snapshot is None:
            normal = {**plan, "reconstructed": False, "rejection_reason": "missing_snapshot_uid"}
            interventions: list[dict[str, Any]] = []
            accepted: list[dict[str, Any]] = []
            replay_errors += 1
        else:
            normal, interventions, accepted = _replay_plan(
                plan=plan,
                snapshot=snapshot,
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                env_config=env_config,
                response_dim=response_dim,
                history_variants=HISTORY_VARIANTS,
                unsupported_variants=UNSUPPORTED_HISTORY_VARIANTS,
                max_continuation_steps=int(max_continuation_steps),
                primary_margin_gap_threshold=float(primary_margin_gap_threshold),
                mitigation_margin_gap_threshold=float(mitigation_margin_gap_threshold),
                action_l2_threshold=float(action_l2_threshold),
                require_action_gap=bool(require_action_gap),
                device=resolved_device,
            )
            if not parse_bool(normal.get("reconstructed", False)):
                replay_errors += 1
        normal_rows.append(normal)
        intervention_rows.extend(interventions)
        if accepted:
            accepted_rows.extend(accepted)
        else:
            rejected_rows.append(
                {
                    **{
                        key: normal.get(key, "")
                        for key in [
                            "candidate_id",
                            "source_group_id",
                            "snapshot_uid",
                            "source_index",
                            "seed",
                            "warmup_mode",
                            "preferred_fault_family",
                            "preferred_fidelity_class",
                            "fault_family_pair",
                            "fault_onset_bucket",
                            "boundary_axis",
                        ]
                    },
                    "rejection_reason": "no_history_sensitive_margin_gap",
                    "normal_margin": _finite_float(normal.get("normal_margin")),
                    "best_margin_gap_from_normal": _finite_float(normal.get("best_margin_gap_from_normal")),
                    "best_prefix_l2_mean": _finite_float(normal.get("best_prefix_l2_mean")),
                }
            )
        _append_progress(
            progress_path,
            {
                "candidate_id": int(plan["candidate_id"]),
                "stage": "history_replay",
                "status": "replayed" if parse_bool(normal.get("reconstructed", False)) else str(normal.get("rejection_reason", "")),
                "normal_margin": _finite_float(normal.get("normal_margin")),
                "best_gap": _finite_float(normal.get("best_margin_gap_from_normal")),
                "accepted_rows": int(len(accepted)),
                "elapsed_seconds": float(time.time() - candidate_start),
            },
        )

    accepted_self_id_raw = [row for row in accepted_rows if row.get("accepted_class") == "primary_self_id"]
    accepted_mitigation_raw = [row for row in accepted_rows if row.get("accepted_class") == "mitigation"]
    accepted_self_id = select_balanced_rows(
        accepted_self_id_raw,
        max_rows_per_seed=12,
        max_rows_per_source_group=6,
        max_rows_per_fault_pair=24,
        max_rows_per_onset_bucket=48,
        max_rows_per_warmup_mode=48,
    )
    accepted_mitigation = select_balanced_rows(
        accepted_mitigation_raw,
        max_rows_per_seed=12,
        max_rows_per_source_group=6,
        max_rows_per_fault_pair=24,
        max_rows_per_onset_bucket=48,
        max_rows_per_warmup_mode=48,
    )
    matched_pair_rows = build_matched_action_divergent_rows(
        normal_rows,
        ego_distance_threshold=float(matched_ego_distance_threshold),
        obstacle_distance_threshold=float(matched_obstacle_distance_threshold),
        first_action_l2_threshold=float(matched_first_action_l2_threshold),
        max_pairs=int(max_matched_pairs),
    )
    all_balanced = [*accepted_self_id, *accepted_mitigation]
    diversity_summary = {
        "accepted_all": source_diversity_metrics(all_balanced),
        "accepted_self_id": source_diversity_metrics(accepted_self_id),
        "accepted_mitigation": source_diversity_metrics(accepted_mitigation),
        "matched_action_divergent": matched_pair_diversity_metrics(matched_pair_rows),
        "normal_rows": source_diversity_metrics(normal_rows),
        "intervention_variant_counts": _value_counts(intervention_rows, "intervention_variant"),
        "accepted_self_id_fault_family_counts": _value_counts(accepted_self_id, "preferred_fault_family"),
        "accepted_self_id_onset_counts": _value_counts(accepted_self_id, "fault_onset_bucket"),
        "accepted_self_id_warmup_counts": _value_counts(accepted_self_id, "warmup_mode"),
    }
    history_sensitive_candidate_rows = int(
        sum(
            1
            for row in normal_rows
            if np.isfinite(_finite_float(row.get("best_margin_gap_from_normal")))
            and _finite_float(row.get("best_margin_gap_from_normal")) >= min(
                float(primary_margin_gap_threshold), float(mitigation_margin_gap_threshold)
            )
        )
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_extreme_hidden_dynamics_route(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        unsupported_variants=list(UNSUPPORTED_HISTORY_VARIANTS),
        source_snapshots=int(len(snapshots_by_uid)),
        replay_errors=int(replay_errors),
        accepted_self_id_rows=accepted_self_id,
        accepted_mitigation_rows=accepted_mitigation,
        min_self_id_rows=int(min_self_id_rows),
        min_seeds=int(min_seeds),
        min_source_groups=int(min_source_groups),
        min_fault_pairs=int(min_fault_pairs),
        min_warmup_modes=int(min_warmup_modes),
        min_onset_buckets=int(min_onset_buckets),
        max_seed_dominance=float(max_seed_dominance),
        max_source_group_dominance=float(max_source_group_dominance),
        max_fault_pair_dominance=float(max_fault_pair_dominance),
        history_sensitive_candidate_rows=int(history_sensitive_candidate_rows),
    )

    write_csv_rows(run_dir / "source_rows.csv", source_group_rows)
    write_csv_rows(run_dir / "warmup_probe_rows.csv", warmup_rows)
    write_csv_rows(run_dir / "source_result_rows.csv", source_result_rows)
    write_csv_rows(run_dir / "candidate_plan_rows.csv", plan_rows)
    write_csv_rows(run_dir / "normal_replay_rows.csv", normal_rows)
    write_csv_rows(run_dir / "history_intervention_rows.csv", intervention_rows, fieldnames=INTERVENTION_FIELDS)
    write_csv_rows(run_dir / "accepted_self_id_rows.csv", accepted_self_id, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_mitigation_rows.csv", accepted_mitigation, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "matched_pair_rows.csv", matched_pair_rows, fieldnames=MATCHED_PAIR_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "source_balance_summary.csv", _summary_rows(all_balanced, "seed", label="seed"))
    write_csv_rows(run_dir / "axis_balance_summary.csv", _summary_rows(all_balanced, "boundary_axis", label="axis"))
    write_json(run_dir / "diversity_summary.json", diversity_summary)
    _write_proxy_limitations(run_dir / "fault_proxy_limitations.md", scenario_config)

    current_model_fault_rows = int(diversity_summary["accepted_all"]["current_model_fault_rows"])
    proxy_rows = int(diversity_summary["accepted_all"]["current_model_proxy_rows"])
    summary = {
        "run_type": "v4_extreme_hidden_dynamics_data_route",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "alpha": float(alpha),
        "fault_specs": int(len(fault_specs)),
        "source_groups": int(len(source_groups)),
        "source_rows": int(len(source_group_rows)),
        "source_snapshots": int(len(snapshots_by_uid)),
        "candidate_plan_rows": int(len(plan_rows)),
        "normal_replay_rows": int(len(normal_rows)),
        "history_intervention_rows": int(len(intervention_rows)),
        "supported_history_variants": list(HISTORY_VARIANTS),
        "unsupported_history_variants": list(UNSUPPORTED_HISTORY_VARIANTS),
        "unsupported_history_variant_reason": "wrong_cross_fault_history requires paired hidden-state injection; M825 logs it as unsupported diagnostic instead of faking support",
        "accepted_self_id_raw_rows": int(len(accepted_self_id_raw)),
        "accepted_self_id_rows": int(len(accepted_self_id)),
        "accepted_mitigation_raw_rows": int(len(accepted_mitigation_raw)),
        "accepted_mitigation_rows": int(len(accepted_mitigation)),
        "matched_pair_rows": int(len(matched_pair_rows)),
        "rejected_rows": int(len(rejected_rows)),
        "history_sensitive_candidate_rows": int(history_sensitive_candidate_rows),
        "replay_errors": int(replay_errors),
        "min_self_id_rows": int(min_self_id_rows),
        "current_model_fault_rows": current_model_fault_rows,
        "proxy_rows": proxy_rows,
        "primary_margin_gap_threshold": float(primary_margin_gap_threshold),
        "mitigation_margin_gap_threshold": float(mitigation_margin_gap_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "require_action_gap": bool(require_action_gap),
        "normal_margin_band_counts": _margin_band_counts(normal_rows),
        "normal_boundary_axis_counts": _value_counts(normal_rows, "boundary_axis"),
        "normal_closest_primary_margin": _closest_primary_margin(normal_rows),
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
        "source_rows_csv": run_dir / "source_rows.csv",
        "history_intervention_rows_csv": run_dir / "history_intervention_rows.csv",
        "matched_pair_rows_csv": run_dir / "matched_pair_rows.csv",
        "accepted_self_id_rows_csv": run_dir / "accepted_self_id_rows.csv",
        "accepted_mitigation_rows_csv": run_dir / "accepted_mitigation_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "fault_proxy_limitations_md": run_dir / "fault_proxy_limitations.md",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 extreme hidden-dynamics data route.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--seed-start", type=int, default=None)
    parser.add_argument("--seed-count", type=int, default=12)
    parser.add_argument("--max-base-faults", type=int, default=10)
    parser.add_argument("--max-fault-specs", type=int, default=18)
    parser.add_argument("--max-source-groups", type=int, default=64)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-candidates-per-snapshot", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=24)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--obstacle-timing-deltas", type=parse_float_list, default=DEFAULT_OBSTACLE_TIMING_DELTAS)
    parser.add_argument("--lateral-deltas", type=parse_float_list, default=DEFAULT_LATERAL_DELTAS)
    parser.add_argument("--half-width-deltas", type=parse_float_list, default=DEFAULT_HALF_WIDTH_DELTAS)
    parser.add_argument("--target-margins", type=parse_float_list, default=DEFAULT_TARGET_MARGINS)
    parser.add_argument("--primary-margin-gap-threshold", type=float, default=0.01)
    parser.add_argument("--mitigation-margin-gap-threshold", type=float, default=0.02)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--require-action-gap", action="store_true")
    parser.add_argument("--min-self-id-rows", type=int, default=120)
    parser.add_argument("--min-seeds", type=int, default=16)
    parser.add_argument("--min-source-groups", type=int, default=48)
    parser.add_argument("--min-fault-pairs", type=int, default=8)
    parser.add_argument("--min-warmup-modes", type=int, default=3)
    parser.add_argument("--min-onset-buckets", type=int, default=4)
    parser.add_argument("--max-seed-dominance", type=float, default=0.20)
    parser.add_argument("--max-source-group-dominance", type=float, default=0.08)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.25)
    parser.add_argument("--matched-ego-distance-threshold", type=float, default=0.08)
    parser.add_argument("--matched-obstacle-distance-threshold", type=float, default=0.08)
    parser.add_argument("--matched-first-action-l2-threshold", type=float, default=0.02)
    parser.add_argument("--max-matched-pairs", type=int, default=256)
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
    missing_sequence = [variant for variant in ("command_shift_obs", "response_delay_obs") if variant not in SEQUENCE_VARIANTS]
    if missing_sequence:
        raise RuntimeError(f"sequence intervention variants unavailable: {missing_sequence}")

    summary = run_extreme_hidden_dynamics_data_route(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        seed_start=seed_start,
        seed_count=int(args.seed_count),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_source_groups=int(args.max_source_groups),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_candidates_per_snapshot=int(args.max_candidates_per_snapshot),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        obstacle_timing_deltas=tuple(args.obstacle_timing_deltas),
        lateral_deltas=tuple(args.lateral_deltas),
        half_width_deltas=tuple(args.half_width_deltas),
        target_margins=tuple(args.target_margins),
        primary_margin_gap_threshold=float(args.primary_margin_gap_threshold),
        mitigation_margin_gap_threshold=float(args.mitigation_margin_gap_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        require_action_gap=bool(args.require_action_gap),
        min_self_id_rows=int(args.min_self_id_rows),
        min_seeds=int(args.min_seeds),
        min_source_groups=int(args.min_source_groups),
        min_fault_pairs=int(args.min_fault_pairs),
        min_warmup_modes=int(args.min_warmup_modes),
        min_onset_buckets=int(args.min_onset_buckets),
        max_seed_dominance=float(args.max_seed_dominance),
        max_source_group_dominance=float(args.max_source_group_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
        matched_ego_distance_threshold=float(args.matched_ego_distance_threshold),
        matched_obstacle_distance_threshold=float(args.matched_obstacle_distance_threshold),
        matched_first_action_l2_threshold=float(args.matched_first_action_l2_threshold),
        max_matched_pairs=int(args.max_matched_pairs),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
