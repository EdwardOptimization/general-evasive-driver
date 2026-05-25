"""No-training refinement for M860 generated boundary brackets."""

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
from autodrift.v4_adaptive_boundary_bracketing import _replay_parameter
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool
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


BRACKET_SEED_FIELDS = [
    "bracket_id",
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
    "bracket_source_class",
    "negative_generation_id",
    "negative_parameter",
    "negative_margin",
    "positive_generation_id",
    "positive_parameter",
    "positive_margin",
    "bracket_parameter_gap",
    "bracket_margin_gap",
]

REFINEMENT_FIELDS = [
    "refined_candidate_id",
    "bracket_id",
    "refinement_iter",
    *BOUNDARY_REPLAY_FIELDS,
    *BOUNDARY_EXTRA_FIELDS,
    "trace_role",
    "trace_cause_class",
    "generation_family",
    "bracket_source_class",
    "negative_parameter_before",
    "negative_margin_before",
    "positive_parameter_before",
    "positive_margin_before",
    "accepted_refined",
    "duplicate_m860_accepted",
]

SUMMARY_FIELDS = [
    "category",
    "value",
    "rows",
    "accepted_rows",
    "acceptance_rate",
]


def _margin(row: dict[str, Any]) -> float:
    return _finite_float(row.get("min_clearance_margin"))


def _is_negative(row: dict[str, Any]) -> bool:
    margin = _margin(row)
    return parse_bool(row.get("collision", False)) or (np.isfinite(margin) and margin < 0.0)


def _is_positive(row: dict[str, Any]) -> bool:
    margin = _margin(row)
    return (
        parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and np.isfinite(margin)
        and margin > 0.0
    )


def _is_boundary(row: dict[str, Any], *, boundary_margin_threshold: float) -> bool:
    margin = _margin(row)
    return (
        parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and np.isfinite(margin)
        and 0.0 <= margin <= float(boundary_margin_threshold)
    )


def _axis_parameter_tolerance(axis: str, *, lateral: float, timing: float, half_width: float) -> float:
    if axis == "obstacle_lateral_offset":
        return float(lateral)
    if axis == "obstacle_timing":
        return float(timing)
    if axis == "obstacle_half_width":
        return float(half_width)
    return float(lateral)


def _group_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        _as_int(row.get("source_group_id")),
        _as_int(row.get("step")),
        str(row.get("boundary_axis", "")),
        str(row.get("generation_family", "")),
    )


def _m860_accepted_group_keys(accepted_rows: list[dict[str, str]], *, boundary_margin_threshold: float) -> set[tuple[int, int, str, str]]:
    return {
        _group_key(row)
        for row in accepted_rows
        if _is_boundary(row, boundary_margin_threshold=float(boundary_margin_threshold))
    }


def _candidate_generated_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("trace_role") == "primary_boundary_new_to_m844"
        and row.get("generation_family") == "all_safe_closer_obstacle"
        and row.get("source_target_class") == "new_underrepresented_boundary"
        and row.get("boundary_source_status") == "boundary_new_to_m844"
        and np.isfinite(_margin(row))
    ]


def _adjacent_generated_bracket(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str]] | None:
    ordered = sorted(rows, key=lambda row: _as_float(row.get("parameter_value", row.get("generated_parameter"))))
    candidates: list[tuple[float, dict[str, str], dict[str, str]]] = []
    for left, right in zip(ordered, ordered[1:]):
        if _is_negative(left) and _is_positive(right):
            candidates.append((abs(_margin(right) - _margin(left)), left, right))
        elif _is_positive(left) and _is_negative(right):
            candidates.append((abs(_margin(left) - _margin(right)), right, left))
    if not candidates:
        return None
    _gap, negative, positive = min(candidates, key=lambda item: item[0])
    return negative, positive


def build_bracket_seed_rows(
    generated_replay_rows: list[dict[str, str]],
    m860_accepted_rows: list[dict[str, str]],
    *,
    boundary_margin_threshold: float,
    max_brackets: int,
) -> list[dict[str, Any]]:
    """Select same-source generated wide/negative brackets for refinement."""

    accepted_keys = _m860_accepted_group_keys(
        m860_accepted_rows,
        boundary_margin_threshold=float(boundary_margin_threshold),
    )
    groups: dict[tuple[int, int, str, str], list[dict[str, str]]] = {}
    for row in _candidate_generated_rows(generated_replay_rows):
        groups.setdefault(_group_key(row), []).append(row)

    output: list[dict[str, Any]] = []
    for key, rows in groups.items():
        bracket = _adjacent_generated_bracket(rows)
        if bracket is None:
            continue
        negative, positive = bracket
        bracket_source_class = "m860_boundary_already_present" if key in accepted_keys else "no_m860_boundary"
        base = positive if _margin(positive) <= _margin(negative) else negative
        row = {
            "bracket_id": len(output),
            "source_group_id": _as_int(base.get("source_group_id")),
            "seed": _as_int(base.get("seed")),
            "step": _as_int(base.get("step")),
            "snapshot_uid": str(base.get("snapshot_uid", "")),
            "source_index": _as_int(base.get("source_index")),
            "warmup_mode": str(base.get("warmup_mode", "")),
            "preferred_fault": str(base.get("preferred_fault", "")),
            "preferred_fault_family": str(base.get("preferred_fault_family", "")),
            "preferred_fault_severity": str(base.get("preferred_fault_severity", "")),
            "preferred_fidelity_class": str(base.get("preferred_fidelity_class", "")),
            "wrong_fault": str(base.get("wrong_fault", "")),
            "wrong_fault_family": str(base.get("wrong_fault_family", "")),
            "wrong_fidelity_class": str(base.get("wrong_fidelity_class", "")),
            "fault_family_pair": str(base.get("fault_family_pair", "")),
            "fault_onset_bucket": str(base.get("fault_onset_bucket", "")),
            "source_axis": str(base.get("source_axis", "")),
            "source_target_class": str(base.get("source_target_class", "")),
            "boundary_source_status": str(base.get("boundary_source_status", "")),
            "trace_role": str(base.get("trace_role", "")),
            "trace_cause_class": str(base.get("trace_cause_class", "")),
            "generation_family": str(base.get("generation_family", "")),
            "boundary_axis": str(base.get("boundary_axis", "")),
            "bracket_source_class": bracket_source_class,
            "negative_generation_id": _as_int(negative.get("generation_id")),
            "negative_parameter": _as_float(negative.get("parameter_value", negative.get("generated_parameter"))),
            "negative_margin": _margin(negative),
            "positive_generation_id": _as_int(positive.get("generation_id")),
            "positive_parameter": _as_float(positive.get("parameter_value", positive.get("generated_parameter"))),
            "positive_margin": _margin(positive),
            "bracket_parameter_gap": abs(
                _as_float(positive.get("parameter_value", positive.get("generated_parameter")))
                - _as_float(negative.get("parameter_value", negative.get("generated_parameter")))
            ),
            "bracket_margin_gap": abs(_margin(positive) - _margin(negative)),
        }
        output.append(row)
    output.sort(
        key=lambda row: (
            0 if row["bracket_source_class"] == "no_m860_boundary" else 1,
            _finite_float(row.get("bracket_margin_gap"), default=999.0),
            _as_int(row.get("source_group_id")),
            str(row.get("boundary_axis", "")),
        )
    )
    output = output[: int(max_brackets)]
    for index, row in enumerate(output):
        row["bracket_id"] = int(index)
    return output


def _duplicate_m860_accepted(
    row: dict[str, Any],
    m860_accepted_rows: list[dict[str, str]],
    *,
    lateral_tolerance: float,
    timing_tolerance: float,
    half_width_tolerance: float,
) -> bool:
    axis = str(row.get("boundary_axis", ""))
    tolerance = _axis_parameter_tolerance(
        axis,
        lateral=float(lateral_tolerance),
        timing=float(timing_tolerance),
        half_width=float(half_width_tolerance),
    )
    parameter = _as_float(row.get("parameter_value"))
    for accepted in m860_accepted_rows:
        if _as_int(accepted.get("source_group_id")) != _as_int(row.get("source_group_id")):
            continue
        if _as_int(accepted.get("step")) != _as_int(row.get("step")):
            continue
        if str(accepted.get("boundary_axis", "")) != axis:
            continue
        accepted_parameter = _as_float(accepted.get("parameter_value", accepted.get("generated_parameter")))
        if np.isfinite(parameter) and np.isfinite(accepted_parameter) and abs(parameter - accepted_parameter) <= tolerance:
            return True
    return False


def refine_generated_bracket(
    *,
    bracket: dict[str, Any],
    snapshot: Any,
    source_meta: dict[str, Any],
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    max_refinement_iterations: int,
    boundary_margin_threshold: float,
    strict_margin_threshold: float,
    lateral_tolerance: float,
    timing_tolerance: float,
    half_width_tolerance: float,
    m860_accepted_rows: list[dict[str, str]],
    start_candidate_id: int,
    device: Any,
) -> tuple[list[dict[str, Any]], int, str]:
    """Bisect a generated wide/negative bracket without mutating model weights."""

    axis = str(bracket["boundary_axis"])
    parameter_tolerance = _axis_parameter_tolerance(
        axis,
        lateral=float(lateral_tolerance),
        timing=float(timing_tolerance),
        half_width=float(half_width_tolerance),
    )
    negative_endpoint = {
        "parameter_value": float(bracket["negative_parameter"]),
        "min_clearance_margin": float(bracket["negative_margin"]),
        "success": False,
        "collision": True,
    }
    positive_endpoint = {
        "parameter_value": float(bracket["positive_parameter"]),
        "min_clearance_margin": float(bracket["positive_margin"]),
        "success": True,
        "collision": False,
    }
    rows: list[dict[str, Any]] = []
    status = "max_iterations"
    for iteration in range(int(max_refinement_iterations)):
        neg_param = float(negative_endpoint["parameter_value"])
        pos_param = float(positive_endpoint["parameter_value"])
        if abs(pos_param - neg_param) <= float(parameter_tolerance):
            status = "parameter_tolerance"
            break
        midpoint = 0.5 * (neg_param + pos_param)
        result, _actions, _relocated = _replay_parameter(
            snapshot=snapshot,
            source_meta=source_meta,
            axis=axis,
            parameter_value=midpoint,
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            response_dim=int(response_dim),
            alpha=float(alpha),
            horizon=int(horizon),
            max_continuation_steps=int(max_continuation_steps),
            device=device,
        )
        margin = _margin(result)
        accepted = _is_boundary(result, boundary_margin_threshold=float(boundary_margin_threshold))
        duplicate = _duplicate_m860_accepted(
            result,
            m860_accepted_rows,
            lateral_tolerance=float(lateral_tolerance),
            timing_tolerance=float(timing_tolerance),
            half_width_tolerance=float(half_width_tolerance),
        )
        row = {
            "refined_candidate_id": int(start_candidate_id + len(rows)),
            "bracket_id": _as_int(bracket.get("bracket_id")),
            "refinement_iter": int(iteration),
            **result,
            "horizon": int(horizon),
            "margin_band": margin_band(
                margin,
                strict_margin_threshold=float(strict_margin_threshold),
                boundary_margin_threshold=float(boundary_margin_threshold),
            ),
            "source_target_class": bracket.get("source_target_class", ""),
            "boundary_source_status": bracket.get("boundary_source_status", ""),
            "trace_role": bracket.get("trace_role", ""),
            "trace_cause_class": bracket.get("trace_cause_class", ""),
            "generation_family": bracket.get("generation_family", ""),
            "bracket_source_class": bracket.get("bracket_source_class", ""),
            "negative_parameter_before": neg_param,
            "negative_margin_before": _margin(negative_endpoint),
            "positive_parameter_before": pos_param,
            "positive_margin_before": _margin(positive_endpoint),
            "accepted_refined": bool(accepted and not duplicate),
            "duplicate_m860_accepted": bool(duplicate),
        }
        rows.append(row)
        if not parse_bool(result.get("reconstructed", False)) or not np.isfinite(margin):
            status = "replay_error"
            break
        if _is_negative(result):
            negative_endpoint = result
        elif _is_positive(result):
            positive_endpoint = result
            if accepted and not duplicate:
                status = "accepted"
        else:
            status = "ambiguous_outcome"
            break
    return rows, start_candidate_id + len(rows), status


def _combined_rows(
    m860_accepted_rows: list[dict[str, str]],
    accepted_refined_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str, float]] = set()
    for row in m860_accepted_rows:
        parameter = _as_float(row.get("parameter_value", row.get("generated_parameter")))
        key = (_as_int(row.get("source_group_id")), _as_int(row.get("step")), str(row.get("boundary_axis", "")), round(parameter, 9))
        if key in seen:
            continue
        seen.add(key)
        output.append({"combined_source": "m860_generated", **row})
    for row in accepted_refined_rows:
        parameter = _as_float(row.get("parameter_value"))
        key = (_as_int(row.get("source_group_id")), _as_int(row.get("step")), str(row.get("boundary_axis", "")), round(parameter, 9))
        if key in seen:
            continue
        seen.add(key)
        output.append({"combined_source": "m864_refined", **row})
    return output


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


def classify_generated_boundary_refinement_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    bracket_seed_rows: int,
    no_m860_boundary_bracket_seed_rows: int,
    unique_bracket_source_group_count: int,
    unique_bracket_seed_count: int,
    accepted_refined_rows: list[dict[str, Any]],
    accepted_no_m860_rows: list[dict[str, Any]],
    combined_rows: list[dict[str, Any]],
    pairability_rows: list[dict[str, Any]],
    min_bracket_seed_rows: int,
    min_no_m860_bracket_seed_rows: int,
    min_bracket_source_groups: int,
    min_bracket_seeds: int,
    min_refined_rows: int,
    min_no_m860_refined_rows: int,
    min_refined_source_groups: int,
    sparse_combined_rows: int,
    sparse_combined_boundary_new_rows: int,
    sparse_combined_source_groups: int,
    sparse_combined_seeds: int,
    sparse_combined_fault_families: int,
    sparse_pairability_rows: int,
    strong_combined_rows: int,
    strong_combined_boundary_new_rows: int,
    strong_combined_source_groups: int,
    strong_combined_seeds: int,
    strong_combined_fault_families: int,
    strong_pairability_rows: int,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_generated_boundary_refinement_contract_violation"
    if (
        int(bracket_seed_rows) < int(min_bracket_seed_rows)
        or int(no_m860_boundary_bracket_seed_rows) < int(min_no_m860_bracket_seed_rows)
        or int(unique_bracket_source_group_count) < int(min_bracket_source_groups)
        or int(unique_bracket_seed_count) < int(min_bracket_seeds)
    ):
        return "v4_generated_boundary_refinement_bracket_sparse"
    if len(accepted_refined_rows) < int(min_refined_rows) or len(accepted_no_m860_rows) < int(min_no_m860_refined_rows):
        return "v4_generated_boundary_refinement_all_weak"
    if unique_count(accepted_refined_rows, "source_group_id") < int(min_refined_source_groups):
        return "v4_generated_boundary_refinement_refined_source_limited"
    primary_pairability = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    boundary_new = [row for row in combined_rows if row.get("boundary_source_status") == "boundary_new_to_m844"]
    strong = bool(
        len(combined_rows) >= int(strong_combined_rows)
        and len(boundary_new) >= int(strong_combined_boundary_new_rows)
        and unique_count(combined_rows, "source_group_id") >= int(strong_combined_source_groups)
        and unique_count(combined_rows, "seed") >= int(strong_combined_seeds)
        and unique_count(combined_rows, "preferred_fault_family") >= int(strong_combined_fault_families)
        and len(primary_pairability) >= int(strong_pairability_rows)
    )
    if strong:
        return "v4_generated_boundary_refinement_pass"
    sparse = bool(
        len(combined_rows) >= int(sparse_combined_rows)
        and len(boundary_new) >= int(sparse_combined_boundary_new_rows)
        and unique_count(combined_rows, "source_group_id") >= int(sparse_combined_source_groups)
        and unique_count(combined_rows, "seed") >= int(sparse_combined_seeds)
        and unique_count(combined_rows, "preferred_fault_family") >= int(sparse_combined_fault_families)
        and len(primary_pairability) >= int(sparse_pairability_rows)
    )
    if sparse:
        return "v4_generated_boundary_refinement_sparse_useful"
    return "v4_generated_boundary_refinement_combined_source_limited"


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
            "gate_name": "bracket_seed_rows",
            "value": summary["bracket_seed_rows"],
            "threshold": summary["min_bracket_seed_rows"],
            "passed": int(summary["bracket_seed_rows"]) >= int(summary["min_bracket_seed_rows"]),
            "notes": "generated wide-negative bracket coverage",
        },
        {
            "gate_name": "accepted_refined_boundary_rows",
            "value": summary["accepted_refined_boundary_rows"],
            "threshold": summary["min_accepted_refined_boundary_rows"],
            "passed": int(summary["accepted_refined_boundary_rows"]) >= int(summary["min_accepted_refined_boundary_rows"]),
            "notes": "refined-only accepted rows",
        },
        {
            "gate_name": "combined_generated_boundary_rows",
            "value": summary["combined_generated_boundary_rows"],
            "threshold": summary["sparse_combined_generated_boundary_rows"],
            "passed": int(summary["combined_generated_boundary_rows"]) >= int(summary["sparse_combined_generated_boundary_rows"]),
            "notes": "M860 accepted plus unique M864 refined rows",
        },
        {
            "gate_name": "combined_pairability_projection_rows",
            "value": summary["combined_pairability_projection_rows"],
            "threshold": summary["sparse_combined_pairability_projection_rows"],
            "passed": int(summary["combined_pairability_projection_rows"]) >= int(summary["sparse_combined_pairability_projection_rows"]),
            "notes": "cheap projection only; no sequence replay",
        },
        {
            "gate_name": "pair_delta_sequence_replay_blocked",
            "value": not bool(summary["pair_delta_sequence_replay_used"]),
            "threshold": "true",
            "passed": not bool(summary["pair_delta_sequence_replay_used"]),
            "notes": "M864 may not run pair-delta sequence replay",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M864 cannot promote",
        },
    ]


def run_generated_boundary_refinement(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    m860_generation_plan_rows_path: Path,
    m860_generated_replay_rows_path: Path,
    m860_accepted_boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_brackets: int,
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
    horizon: int,
    max_continuation_steps: int,
    max_refinement_iterations: int,
    boundary_margin_threshold: float,
    strict_margin_threshold: float,
    lateral_tolerance: float,
    timing_tolerance: float,
    half_width_tolerance: float,
    min_first_action_l2: float,
    max_pairability_obstacle_distance: float,
    diagnostic_pairability_obstacle_distance: float,
    min_bracket_seed_rows: int,
    min_no_m860_bracket_seed_rows: int,
    min_bracket_source_groups: int,
    min_bracket_seeds: int,
    min_accepted_refined_boundary_rows: int,
    min_accepted_no_m860_boundary_rows: int,
    min_refined_source_groups: int,
    sparse_combined_generated_boundary_rows: int,
    sparse_combined_boundary_new_to_m844_rows: int,
    sparse_combined_source_groups: int,
    sparse_combined_seeds: int,
    sparse_combined_fault_families: int,
    sparse_combined_pairability_projection_rows: int,
    strong_combined_generated_boundary_rows: int,
    strong_combined_boundary_new_to_m844_rows: int,
    strong_combined_source_groups: int,
    strong_combined_seeds: int,
    strong_combined_fault_families: int,
    strong_combined_pairability_projection_rows: int,
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
        raise ValueError("M864 generated boundary refinement requires an online recurrent checkpoint")
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

    _generation_plan_rows = read_csv_rows(m860_generation_plan_rows_path)
    generated_replay_rows = read_csv_rows(m860_generated_replay_rows_path)
    m860_accepted_rows = read_csv_rows(m860_accepted_boundary_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    bracket_seed_rows = build_bracket_seed_rows(
        generated_replay_rows,
        m860_accepted_rows,
        boundary_margin_threshold=float(boundary_margin_threshold),
        max_brackets=int(max_brackets),
    )
    request_rows = [
        {
            "left_source_group_id": _as_int(row.get("source_group_id")),
            "right_source_group_id": _as_int(row.get("source_group_id")),
            "left_step": _as_int(row.get("step")),
            "right_step": _as_int(row.get("step")),
        }
        for row in bracket_seed_rows
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
    refinement_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = [dict(row) for row in snapshot_rejections]
    next_candidate_id = 0
    bracket_status_rows: list[dict[str, Any]] = []
    for bracket in bracket_seed_rows:
        key = (_as_int(bracket.get("source_group_id")), _as_int(bracket.get("step")))
        snapshot = snapshots.get(key)
        source_plan = plan_by_group.get(key[0])
        if snapshot is None or source_plan is None:
            rejected_rows.append({"source_group_id": key[0], "step": key[1], "rejection_reason": "missing_snapshot_or_plan"})
            bracket_status_rows.append({**bracket, "refinement_status": "missing_snapshot_or_plan", "refinement_rows": 0})
            continue
        source_meta = _source_meta_from_plan(
            source_plan,
            source_index=_as_int(bracket.get("source_index")),
            fault_by_name=fault_by_name,
            warmup_steps=int(warmup_steps),
        )
        for extra in (*BOUNDARY_EXTRA_FIELDS, "trace_role", "trace_cause_class", "generation_family", "bracket_source_class"):
            source_meta[extra] = bracket.get(extra, "")
        rows, next_candidate_id, status = refine_generated_bracket(
            bracket=bracket,
            snapshot=snapshot,
            source_meta=source_meta,
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            response_dim=response_dim,
            alpha=float(alpha),
            horizon=int(horizon),
            max_continuation_steps=int(max_continuation_steps),
            max_refinement_iterations=int(max_refinement_iterations),
            boundary_margin_threshold=float(boundary_margin_threshold),
            strict_margin_threshold=float(strict_margin_threshold),
            lateral_tolerance=float(lateral_tolerance),
            timing_tolerance=float(timing_tolerance),
            half_width_tolerance=float(half_width_tolerance),
            m860_accepted_rows=m860_accepted_rows,
            start_candidate_id=next_candidate_id,
            device=resolved_device,
        )
        refinement_rows.extend(rows)
        bracket_status_rows.append({**bracket, "refinement_status": status, "refinement_rows": len(rows)})
        _append_progress(
            progress_path,
            {
                "stage": "refined_bracket",
                "bracket_id": _as_int(bracket.get("bracket_id")),
                "source_group_id": key[0],
                "boundary_axis": bracket.get("boundary_axis", ""),
                "status": status,
                "rows": len(rows),
            },
        )

    accepted_refined_rows = [
        row
        for row in refinement_rows
        if parse_bool(row.get("accepted_refined", False))
        and not parse_bool(row.get("duplicate_m860_accepted", False))
    ]
    accepted_no_m860_rows = [
        row for row in accepted_refined_rows if row.get("bracket_source_class") == "no_m860_boundary"
    ]
    combined_rows = _combined_rows(m860_accepted_rows, accepted_refined_rows)
    pairability_rows = build_pairability_projection_rows(
        combined_rows,
        min_first_action_l2=float(min_first_action_l2),
        max_obstacle_distance=float(max_pairability_obstacle_distance),
        diagnostic_max_obstacle_distance=float(diagnostic_pairability_obstacle_distance),
    )
    primary_pairability_rows = [row for row in pairability_rows if row.get("pairability_tier") == "primary_0_10"]
    no_m860_bracket_rows = [
        row for row in bracket_seed_rows if row.get("bracket_source_class") == "no_m860_boundary"
    ]
    refinement_summary_rows = [
        *_summary_rows(refinement_rows, accepted_refined_rows, "bracket_source_class", category="bracket_source_class"),
        *_summary_rows(refinement_rows, accepted_refined_rows, "boundary_axis", category="boundary_axis"),
        *_summary_rows(refinement_rows, accepted_refined_rows, "preferred_fault_family", category="preferred_fault_family"),
        *_summary_rows(bracket_status_rows, accepted_refined_rows, "refinement_status", category="refinement_status"),
    ]
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_generated_boundary_refinement_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        bracket_seed_rows=len(bracket_seed_rows),
        no_m860_boundary_bracket_seed_rows=len(no_m860_bracket_rows),
        unique_bracket_source_group_count=unique_count(bracket_seed_rows, "source_group_id"),
        unique_bracket_seed_count=unique_count(bracket_seed_rows, "seed"),
        accepted_refined_rows=accepted_refined_rows,
        accepted_no_m860_rows=accepted_no_m860_rows,
        combined_rows=combined_rows,
        pairability_rows=pairability_rows,
        min_bracket_seed_rows=int(min_bracket_seed_rows),
        min_no_m860_bracket_seed_rows=int(min_no_m860_bracket_seed_rows),
        min_bracket_source_groups=int(min_bracket_source_groups),
        min_bracket_seeds=int(min_bracket_seeds),
        min_refined_rows=int(min_accepted_refined_boundary_rows),
        min_no_m860_refined_rows=int(min_accepted_no_m860_boundary_rows),
        min_refined_source_groups=int(min_refined_source_groups),
        sparse_combined_rows=int(sparse_combined_generated_boundary_rows),
        sparse_combined_boundary_new_rows=int(sparse_combined_boundary_new_to_m844_rows),
        sparse_combined_source_groups=int(sparse_combined_source_groups),
        sparse_combined_seeds=int(sparse_combined_seeds),
        sparse_combined_fault_families=int(sparse_combined_fault_families),
        sparse_pairability_rows=int(sparse_combined_pairability_projection_rows),
        strong_combined_rows=int(strong_combined_generated_boundary_rows),
        strong_combined_boundary_new_rows=int(strong_combined_boundary_new_to_m844_rows),
        strong_combined_source_groups=int(strong_combined_source_groups),
        strong_combined_seeds=int(strong_combined_seeds),
        strong_combined_fault_families=int(strong_combined_fault_families),
        strong_pairability_rows=int(strong_combined_pairability_projection_rows),
    )

    write_csv_rows(run_dir / "bracket_seed_rows.csv", bracket_seed_rows, fieldnames=BRACKET_SEED_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "refinement_rows.csv", refinement_rows, fieldnames=REFINEMENT_FIELDS)
    write_csv_rows(run_dir / "accepted_refined_boundary_rows.csv", accepted_refined_rows, fieldnames=REFINEMENT_FIELDS)
    write_csv_rows(run_dir / "combined_generated_boundary_rows.csv", combined_rows)
    write_csv_rows(run_dir / "pairability_projection_rows.csv", pairability_rows)
    write_csv_rows(run_dir / "refinement_summary.csv", refinement_summary_rows, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(run_dir / "bracket_status_rows.csv", bracket_status_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    combined_boundary_new = [row for row in combined_rows if row.get("boundary_source_status") == "boundary_new_to_m844"]
    summary = {
        "run_type": "v4_generated_boundary_refinement",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "m860_generation_plan_rows": m860_generation_plan_rows_path,
        "m860_generated_replay_rows": m860_generated_replay_rows_path,
        "m860_accepted_boundary_rows": m860_accepted_boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "bracket_seed_rows": len(bracket_seed_rows),
        "no_m860_boundary_bracket_seed_rows": len(no_m860_bracket_rows),
        "unique_bracket_source_group_count": unique_count(bracket_seed_rows, "source_group_id"),
        "unique_bracket_seed_count": unique_count(bracket_seed_rows, "seed"),
        "unique_bracket_fault_family_count": unique_count(bracket_seed_rows, "preferred_fault_family"),
        "reconstructed_snapshot_rows": len(snapshot_rows),
        "snapshot_rejection_rows": len(snapshot_rejections),
        "refinement_rows": len(refinement_rows),
        "accepted_refined_boundary_rows": len(accepted_refined_rows),
        "accepted_no_m860_boundary_rows": len(accepted_no_m860_rows),
        "unique_refined_source_group_count": unique_count(accepted_refined_rows, "source_group_id"),
        "unique_refined_seed_count": unique_count(accepted_refined_rows, "seed"),
        "unique_refined_fault_family_count": unique_count(accepted_refined_rows, "preferred_fault_family"),
        "combined_generated_boundary_rows": len(combined_rows),
        "combined_boundary_new_to_m844_rows": len(combined_boundary_new),
        "combined_unique_source_group_count": unique_count(combined_rows, "source_group_id"),
        "combined_unique_seed_count": unique_count(combined_rows, "seed"),
        "combined_unique_fault_family_count": unique_count(combined_rows, "preferred_fault_family"),
        "combined_pairability_projection_rows": len(primary_pairability_rows),
        "combined_diagnostic_pairability_projection_rows": len(pairability_rows),
        "combined_max_source_group_dominance": max_share(combined_rows, "source_group_id"),
        "combined_max_seed_dominance": max_share(combined_rows, "seed"),
        "min_bracket_seed_rows": int(min_bracket_seed_rows),
        "min_no_m860_bracket_seed_rows": int(min_no_m860_bracket_seed_rows),
        "min_bracket_source_groups": int(min_bracket_source_groups),
        "min_bracket_seeds": int(min_bracket_seeds),
        "min_accepted_refined_boundary_rows": int(min_accepted_refined_boundary_rows),
        "min_accepted_no_m860_boundary_rows": int(min_accepted_no_m860_boundary_rows),
        "min_refined_source_groups": int(min_refined_source_groups),
        "sparse_combined_generated_boundary_rows": int(sparse_combined_generated_boundary_rows),
        "sparse_combined_boundary_new_to_m844_rows": int(sparse_combined_boundary_new_to_m844_rows),
        "sparse_combined_source_groups": int(sparse_combined_source_groups),
        "sparse_combined_seeds": int(sparse_combined_seeds),
        "sparse_combined_fault_families": int(sparse_combined_fault_families),
        "sparse_combined_pairability_projection_rows": int(sparse_combined_pairability_projection_rows),
        "strong_combined_generated_boundary_rows": int(strong_combined_generated_boundary_rows),
        "strong_combined_boundary_new_to_m844_rows": int(strong_combined_boundary_new_to_m844_rows),
        "strong_combined_source_groups": int(strong_combined_source_groups),
        "strong_combined_seeds": int(strong_combined_seeds),
        "strong_combined_fault_families": int(strong_combined_fault_families),
        "strong_combined_pairability_projection_rows": int(strong_combined_pairability_projection_rows),
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
        "bracket_seed_rows_csv": run_dir / "bracket_seed_rows.csv",
        "refinement_rows_csv": run_dir / "refinement_rows.csv",
        "accepted_refined_boundary_rows_csv": run_dir / "accepted_refined_boundary_rows.csv",
        "combined_generated_boundary_rows_csv": run_dir / "combined_generated_boundary_rows.csv",
        "pairability_projection_rows_csv": run_dir / "pairability_projection_rows.csv",
        "refinement_summary_csv": run_dir / "refinement_summary.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 generated boundary refinement.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--m860-generation-plan-rows", type=Path, required=True)
    parser.add_argument("--m860-generated-replay-rows", type=Path, required=True)
    parser.add_argument("--m860-accepted-boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-brackets", type=int, default=64)
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
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--max-refinement-iterations", type=int, default=6)
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--strict-margin-threshold", type=float, default=0.02)
    parser.add_argument("--lateral-tolerance", type=float, default=0.01)
    parser.add_argument("--timing-tolerance", type=float, default=0.05)
    parser.add_argument("--half-width-tolerance", type=float, default=0.005)
    parser.add_argument("--min-first-action-l2", type=float, default=0.014)
    parser.add_argument("--max-pairability-obstacle-distance", type=float, default=0.10)
    parser.add_argument("--diagnostic-pairability-obstacle-distance", type=float, default=0.20)
    parser.add_argument("--min-bracket-seed-rows", type=int, default=10)
    parser.add_argument("--min-no-m860-bracket-seed-rows", type=int, default=10)
    parser.add_argument("--min-bracket-source-groups", type=int, default=10)
    parser.add_argument("--min-bracket-seeds", type=int, default=3)
    parser.add_argument("--min-accepted-refined-boundary-rows", type=int, default=8)
    parser.add_argument("--min-accepted-no-m860-boundary-rows", type=int, default=6)
    parser.add_argument("--min-refined-source-groups", type=int, default=6)
    parser.add_argument("--sparse-combined-generated-boundary-rows", type=int, default=32)
    parser.add_argument("--sparse-combined-boundary-new-to-m844-rows", type=int, default=24)
    parser.add_argument("--sparse-combined-source-groups", type=int, default=20)
    parser.add_argument("--sparse-combined-seeds", type=int, default=5)
    parser.add_argument("--sparse-combined-fault-families", type=int, default=8)
    parser.add_argument("--sparse-combined-pairability-projection-rows", type=int, default=40)
    parser.add_argument("--strong-combined-generated-boundary-rows", type=int, default=60)
    parser.add_argument("--strong-combined-boundary-new-to-m844-rows", type=int, default=48)
    parser.add_argument("--strong-combined-source-groups", type=int, default=32)
    parser.add_argument("--strong-combined-seeds", type=int, default=8)
    parser.add_argument("--strong-combined-fault-families", type=int, default=8)
    parser.add_argument("--strong-combined-pairability-projection-rows", type=int, default=100)
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
    summary = run_generated_boundary_refinement(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        m860_generation_plan_rows_path=args.m860_generation_plan_rows,
        m860_generated_replay_rows_path=args.m860_generated_replay_rows,
        m860_accepted_boundary_rows_path=args.m860_accepted_boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_brackets=int(args.max_brackets),
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
        horizon=int(args.horizon),
        max_continuation_steps=max_continuation_steps,
        max_refinement_iterations=int(args.max_refinement_iterations),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        strict_margin_threshold=float(args.strict_margin_threshold),
        lateral_tolerance=float(args.lateral_tolerance),
        timing_tolerance=float(args.timing_tolerance),
        half_width_tolerance=float(args.half_width_tolerance),
        min_first_action_l2=float(args.min_first_action_l2),
        max_pairability_obstacle_distance=float(args.max_pairability_obstacle_distance),
        diagnostic_pairability_obstacle_distance=float(args.diagnostic_pairability_obstacle_distance),
        min_bracket_seed_rows=int(args.min_bracket_seed_rows),
        min_no_m860_bracket_seed_rows=int(args.min_no_m860_bracket_seed_rows),
        min_bracket_source_groups=int(args.min_bracket_source_groups),
        min_bracket_seeds=int(args.min_bracket_seeds),
        min_accepted_refined_boundary_rows=int(args.min_accepted_refined_boundary_rows),
        min_accepted_no_m860_boundary_rows=int(args.min_accepted_no_m860_boundary_rows),
        min_refined_source_groups=int(args.min_refined_source_groups),
        sparse_combined_generated_boundary_rows=int(args.sparse_combined_generated_boundary_rows),
        sparse_combined_boundary_new_to_m844_rows=int(args.sparse_combined_boundary_new_to_m844_rows),
        sparse_combined_source_groups=int(args.sparse_combined_source_groups),
        sparse_combined_seeds=int(args.sparse_combined_seeds),
        sparse_combined_fault_families=int(args.sparse_combined_fault_families),
        sparse_combined_pairability_projection_rows=int(args.sparse_combined_pairability_projection_rows),
        strong_combined_generated_boundary_rows=int(args.strong_combined_generated_boundary_rows),
        strong_combined_boundary_new_to_m844_rows=int(args.strong_combined_boundary_new_to_m844_rows),
        strong_combined_source_groups=int(args.strong_combined_source_groups),
        strong_combined_seeds=int(args.strong_combined_seeds),
        strong_combined_fault_families=int(args.strong_combined_fault_families),
        strong_combined_pairability_projection_rows=int(args.strong_combined_pairability_projection_rows),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
