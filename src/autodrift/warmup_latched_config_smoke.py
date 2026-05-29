"""No-training warmup-latched source/config smoke."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    collect_fault_trace_window,
    fault_map_from_config,
)
from autodrift.causal_history_source_miner import (
    hidden_l2,
    history_window_l2,
    numeric_summary,
    observation_distance_metrics,
    passes_matched_current,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import FaultSpec, PairingRule, load_scenario_config
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device


MATCH_THRESHOLDS = {
    "ego_response_l2": 0.08,
    "actuator_state_l2": 0.05,
    "previous_command_l2": 0.05,
    "scene_context_l2": 0.10,
    "obstacle_position_l2": 0.10,
    "road_boundary_l2": 0.12,
}


def parse_int_list(text: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    if any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("steps must be positive")
    return values


def bucket(value: float, width: float) -> str:
    if not np.isfinite(float(value)):
        return "nan"
    return str(int(np.floor(float(value) / float(width))))


def reveal_bucket_key(observation: np.ndarray, info: dict[str, Any]) -> str:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    vx = float(obs[0] * 20.0) if obs.shape[0] > 0 else float("nan")
    yaw_rate = float(obs[2] * 2.5) if obs.shape[0] > 2 else float("nan")
    steer = float(obs[5]) if obs.shape[0] > 5 else float("nan")
    obstacle_distance = float(info.get("obstacle_distance", float("nan")))
    obstacle_lateral = float(info.get("obstacle_lateral_offset", float("nan")))
    return "|".join(
        (
            f"vx{bucket(vx, 2.0)}",
            f"yaw{bucket(yaw_rate, 0.375)}",
            f"steer{bucket(steer, 0.05)}",
            f"ox{bucket(obstacle_distance, 4.0)}",
            f"oy{bucket(obstacle_lateral, 0.5)}",
        )
    )


def fault_evidence_steps(fault: FaultSpec, reveal_step: int) -> int:
    return max(0, int(reveal_step) - int(fault.activation_step))


def _rule_fault_pairs(
    faults_by_family: dict[str, list[FaultSpec]],
    rules: list[PairingRule],
) -> list[tuple[FaultSpec, FaultSpec, str]]:
    pairs: list[tuple[FaultSpec, FaultSpec, str]] = []
    for rule in rules:
        preferred_faults = faults_by_family.get(rule.preferred_family, [])
        wrong_faults = faults_by_family.get(rule.wrong_family, [])
        for preferred in preferred_faults:
            if rule.preferred_severities and preferred.severity not in rule.preferred_severities:
                continue
            for wrong in wrong_faults:
                if rule.wrong_severities and wrong.severity not in rule.wrong_severities:
                    continue
                pairs.append((preferred, wrong, f"{rule.preferred_family}->{rule.wrong_family}"))
    return pairs


def source_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "unique_source_seeds": 0,
            "unique_capability_pairs": 0,
            "unique_reveal_buckets": 0,
            "max_single_seed_share": None,
            "max_single_capability_pair_share": None,
        }
    frame = pd.DataFrame(rows)
    seed_counts = frame["seed"].value_counts()
    pair_counts = frame["capability_pair"].value_counts()
    return {
        "rows": int(len(frame)),
        "unique_source_seeds": int(frame["seed"].nunique()),
        "unique_capability_pairs": int(frame["capability_pair"].nunique()),
        "unique_reveal_buckets": int(frame["preferred_reveal_bucket"].nunique()),
        "unique_preferred_fault_families": int(frame["preferred_fault_family"].nunique()),
        "unique_wrong_fault_families": int(frame["wrong_fault_family"].nunique()),
        "max_single_seed_share": float(seed_counts.max() / len(frame)),
        "max_single_capability_pair_share": float(pair_counts.max() / len(frame)),
    }


def _trace_bool_count(trace: list[Any], key: str) -> int:
    return int(sum(1 for point in trace if bool(point.info.get(key, False))))


def _trace_bool_any(trace: list[Any], key: str) -> bool:
    return bool(any(bool(point.info.get(key, False)) for point in trace))


def _trace_current_value(trace: list[Any], key: str) -> float:
    if not trace:
        return float("nan")
    value = trace[-1].info.get(key, float("nan"))
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _history_segment_l2(
    left_trace: list[Any],
    right_trace: list[Any],
    start: int,
    stop: int | None,
) -> float:
    left = [np.asarray(point.observation, dtype=np.float32).reshape(-1)[start:stop] for point in left_trace]
    right = [np.asarray(point.observation, dtype=np.float32).reshape(-1)[start:stop] for point in right_trace]
    return history_window_l2(left, right)


def warmup_gate_pair_metrics(preferred_trace: list[Any], wrong_trace: list[Any]) -> dict[str, Any]:
    preferred_history = preferred_trace[:-1]
    wrong_history = wrong_trace[:-1]
    preferred_visible_steps = _trace_bool_count(preferred_history, "warmup_gate_visible")
    wrong_visible_steps = _trace_bool_count(wrong_history, "warmup_gate_visible")
    return {
        "warmup_response_history_l2": _history_segment_l2(preferred_history, wrong_history, 0, 9),
        "warmup_action_history_l2": _history_segment_l2(preferred_history, wrong_history, 9, 12),
        "warmup_context_history_l2": _history_segment_l2(preferred_history, wrong_history, 12, None),
        "preferred_warmup_gate_active_steps": _trace_bool_count(preferred_history, "warmup_gate_active"),
        "wrong_warmup_gate_active_steps": _trace_bool_count(wrong_history, "warmup_gate_active"),
        "preferred_warmup_gate_visible_steps": preferred_visible_steps,
        "wrong_warmup_gate_visible_steps": wrong_visible_steps,
        "warmup_gate_visible_step_delta": int(preferred_visible_steps - wrong_visible_steps),
        "preferred_warmup_gate_passed": _trace_bool_any(preferred_trace, "warmup_gate_passed"),
        "wrong_warmup_gate_passed": _trace_bool_any(wrong_trace, "warmup_gate_passed"),
        "preferred_warmup_gate_collision": _trace_bool_any(preferred_trace, "warmup_gate_collision"),
        "wrong_warmup_gate_collision": _trace_bool_any(wrong_trace, "warmup_gate_collision"),
        "preferred_warmup_gate_clearance_margin": _trace_current_value(preferred_trace, "warmup_gate_clearance_margin"),
        "wrong_warmup_gate_clearance_margin": _trace_current_value(wrong_trace, "warmup_gate_clearance_margin"),
        "preferred_warmup_gate_min_clearance": _trace_current_value(preferred_trace, "warmup_gate_min_clearance"),
        "wrong_warmup_gate_min_clearance": _trace_current_value(wrong_trace, "warmup_gate_min_clearance"),
        "preferred_current_active_obstacle_body_x": _trace_current_value(preferred_trace, "active_obstacle_body_x"),
        "wrong_current_active_obstacle_body_x": _trace_current_value(wrong_trace, "active_obstacle_body_x"),
    }


def warmup_gate_clearance_margin_band(value: float) -> str:
    margin = float(value)
    if not np.isfinite(margin):
        return "nonfinite"
    if margin < 0.0:
        return "collision_negative"
    if margin < 0.25:
        return "clear_0p00_0p25"
    if margin < 1.0:
        return "clear_0p25_1p00"
    return "clear_gt_1p00"


def warmup_gate_source_stratum_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    preferred_margin = float(metrics.get("preferred_warmup_gate_clearance_margin", float("nan")))
    wrong_margin = float(metrics.get("wrong_warmup_gate_clearance_margin", float("nan")))
    finite_margins = [value for value in (preferred_margin, wrong_margin) if np.isfinite(value)]
    min_margin = min(finite_margins) if finite_margins else float("nan")
    collision = bool(
        metrics.get("preferred_warmup_gate_collision", False)
        or metrics.get("wrong_warmup_gate_collision", False)
        or (np.isfinite(min_margin) and min_margin < 0.0)
    )
    if collision:
        stratum = "collision"
    elif np.isfinite(min_margin) and min_margin < 0.25:
        stratum = "clear_low_margin"
    else:
        stratum = "clear"
    return {
        "warmup_gate_collision_source": collision,
        "warmup_gate_collision_stratum": stratum,
        "warmup_gate_clearance_margin_min": min_margin,
        "warmup_gate_clearance_margin_band": warmup_gate_clearance_margin_band(min_margin),
    }


def warmup_gate_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "warmup_gate_visible_rows": 0,
            "warmup_evidence_rows": 0,
            "warmup_gate_collision_rows": 0,
            "warmup_gate_collision_share": None,
            "warmup_response_history_l2": numeric_summary([]),
            "warmup_action_history_l2": numeric_summary([]),
        }
    visible_rows = [
        row
        for row in rows
        if int(row.get("preferred_warmup_gate_visible_steps", 0)) > 0
        or int(row.get("wrong_warmup_gate_visible_steps", 0)) > 0
    ]
    evidence_rows = [
        row
        for row in visible_rows
        if float(row.get("warmup_response_history_l2", 0.0)) > 0.0
        or float(row.get("warmup_action_history_l2", 0.0)) > 0.0
    ]
    collision_rows = [
        row
        for row in rows
        if bool(row.get("preferred_warmup_gate_collision", False)) or bool(row.get("wrong_warmup_gate_collision", False))
    ]
    return {
        "rows": int(len(rows)),
        "warmup_gate_visible_rows": int(len(visible_rows)),
        "warmup_evidence_rows": int(len(evidence_rows)),
        "warmup_gate_collision_rows": int(len(collision_rows)),
        "warmup_gate_collision_share": float(len(collision_rows) / len(rows)),
        "preferred_warmup_gate_passed_rows": int(
            sum(1 for row in rows if bool(row.get("preferred_warmup_gate_passed", False)))
        ),
        "wrong_warmup_gate_passed_rows": int(
            sum(1 for row in rows if bool(row.get("wrong_warmup_gate_passed", False)))
        ),
        "warmup_response_history_l2": numeric_summary(
            [float(row.get("warmup_response_history_l2", float("nan"))) for row in rows]
        ),
        "warmup_action_history_l2": numeric_summary(
            [float(row.get("warmup_action_history_l2", float("nan"))) for row in rows]
        ),
        "warmup_context_history_l2": numeric_summary(
            [float(row.get("warmup_context_history_l2", float("nan"))) for row in rows]
        ),
        "preferred_warmup_gate_visible_steps": numeric_summary(
            [float(row.get("preferred_warmup_gate_visible_steps", float("nan"))) for row in rows]
        ),
        "wrong_warmup_gate_visible_steps": numeric_summary(
            [float(row.get("wrong_warmup_gate_visible_steps", float("nan"))) for row in rows]
        ),
        "preferred_warmup_gate_clearance_margin": numeric_summary(
            [float(row.get("preferred_warmup_gate_clearance_margin", float("nan"))) for row in rows]
        ),
        "wrong_warmup_gate_clearance_margin": numeric_summary(
            [float(row.get("wrong_warmup_gate_clearance_margin", float("nan"))) for row in rows]
        ),
    }


def warmup_gate_strata_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    output: list[dict[str, Any]] = []
    for stratum, group in frame.groupby("warmup_gate_collision_stratum", observed=True):
        output.append(
            {
                "warmup_gate_collision_stratum": str(stratum),
                "rows": int(len(group)),
                "matched_current_rows": int(group["matched_current_pass"].astype(bool).sum()),
                "bucketed_current_rows": int(group["bucketed_current_pass"].astype(bool).sum()),
                "matched_or_bucketed_rows": int(group["matched_or_bucketed_reveal_pass"].astype(bool).sum()),
                "unique_seeds": int(group["seed"].nunique()),
                "unique_capability_pairs": int(group["capability_pair"].nunique()),
                "unique_reveal_buckets": int(group["preferred_reveal_bucket"].nunique()),
                "warmup_response_history_l2_mean": float(group["warmup_response_history_l2"].astype(float).mean()),
                "warmup_action_history_l2_mean": float(group["warmup_action_history_l2"].astype(float).mean()),
                "clearance_margin_min_mean": float(group["warmup_gate_clearance_margin_min"].astype(float).mean()),
            }
        )
    return output


def summarize_groups(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    output: list[dict[str, Any]] = []
    for group_key, group in frame.groupby(list(keys), observed=True):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        item = {key: value for key, value in zip(keys, group_key, strict=True)}
        item.update(
            {
                "rows": int(len(group)),
                "matched_current_rows": int(group["matched_current_pass"].astype(bool).sum()),
                "bucketed_current_rows": int(group["bucketed_current_pass"].astype(bool).sum()),
                "matched_or_bucketed_rows": int(group["matched_or_bucketed_reveal_pass"].astype(bool).sum()),
                "unique_seeds": int(group["seed"].nunique()),
                "unique_reveal_buckets": int(group["preferred_reveal_bucket"].nunique()),
                "warmup_history_l2_mean": float(group["warmup_history_l2"].astype(float).mean()),
                "warmup_response_history_l2_mean": float(group["warmup_response_history_l2"].astype(float).mean()),
                "warmup_action_history_l2_mean": float(group["warmup_action_history_l2"].astype(float).mean()),
                "warmup_gate_visible_rows": int(
                    (
                        (group["preferred_warmup_gate_visible_steps"].astype(int) > 0)
                        | (group["wrong_warmup_gate_visible_steps"].astype(int) > 0)
                    ).sum()
                ),
                "current_hidden_l2_mean": float(group["current_hidden_l2"].astype(float).mean()),
            }
        )
        output.append(item)
    return output


def classify_warmup_smoke_result(
    *,
    source_rows: int,
    matched_or_bucketed_rows: int,
    unique_source_seeds: int,
    unique_capability_pairs: int,
    unique_reveal_buckets: int,
    finite_metric_rows: int,
    actor_parameters_changed: bool,
) -> str:
    if actor_parameters_changed:
        return "warmup_latched_contract_violation"
    if source_rows <= 0:
        return "warmup_latched_no_rows"
    if finite_metric_rows < source_rows:
        return "warmup_latched_nonfinite_metrics"
    structural_pass = (
        int(source_rows) >= 512
        and int(matched_or_bucketed_rows) >= 160
        and int(unique_source_seeds) >= 24
        and int(unique_capability_pairs) >= 8
        and int(unique_reveal_buckets) >= 8
    )
    return "warmup_latched_structural_pass" if structural_pass else "warmup_latched_structural_sparse"


def run_warmup_latched_config_smoke(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    reveal_steps: tuple[int, ...],
    history_length: int,
    min_warmup_evidence_steps: int,
    max_source_rows: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    faults = list(fault_by_name.values())
    faults_by_family: dict[str, list[FaultSpec]] = {}
    for fault in faults:
        faults_by_family.setdefault(str(fault.family), []).append(fault)
    pair_specs = _rule_fault_pairs(faults_by_family, list(config.get("pairing_rules", [])))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    trace_cache: dict[tuple[int, str, int, int], Any] = {}

    def trace_for(seed: int, fault: FaultSpec, reveal_step: int) -> Any:
        key = (int(seed), str(fault.name), int(reveal_step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault,
                seed=int(seed),
                target_step=int(reveal_step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    source_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    seeds = range(int(seed_start), int(seed_start) + int(seed_count))
    for seed in seeds:
        for reveal_step in reveal_steps:
            for preferred_fault, wrong_fault, capability_pair in pair_specs:
                if fault_evidence_steps(preferred_fault, reveal_step) < int(min_warmup_evidence_steps):
                    rejected_rows.append(
                        {
                            "seed": int(seed),
                            "reveal_step": int(reveal_step),
                            "preferred_fault": preferred_fault.name,
                            "wrong_fault": wrong_fault.name,
                            "capability_pair": capability_pair,
                            "rejection_reason": "preferred_fault_insufficient_warmup_evidence",
                        }
                    )
                    continue
                if fault_evidence_steps(wrong_fault, reveal_step) < int(min_warmup_evidence_steps):
                    rejected_rows.append(
                        {
                            "seed": int(seed),
                            "reveal_step": int(reveal_step),
                            "preferred_fault": preferred_fault.name,
                            "wrong_fault": wrong_fault.name,
                            "capability_pair": capability_pair,
                            "rejection_reason": "wrong_fault_insufficient_warmup_evidence",
                        }
                    )
                    continue
                try:
                    preferred_trace = trace_for(seed, preferred_fault, reveal_step)
                    wrong_trace = trace_for(seed, wrong_fault, reveal_step)
                except Exception as exc:  # pragma: no cover - surfaced in artifacts.
                    rejected_rows.append(
                        {
                            "seed": int(seed),
                            "reveal_step": int(reveal_step),
                            "preferred_fault": preferred_fault.name,
                            "wrong_fault": wrong_fault.name,
                            "capability_pair": capability_pair,
                            "rejection_reason": "trace_reconstruction_failed",
                            "error": str(exc),
                        }
                    )
                    continue
                preferred_current = preferred_trace[-1]
                wrong_current = wrong_trace[-1]
                current_metrics = observation_distance_metrics(preferred_current.observation, wrong_current.observation)
                matched_current = passes_matched_current(current_metrics, MATCH_THRESHOLDS)
                preferred_bucket = reveal_bucket_key(preferred_current.observation, preferred_current.info)
                wrong_bucket = reveal_bucket_key(wrong_current.observation, wrong_current.info)
                bucketed_current = preferred_bucket == wrong_bucket
                warmup_history_l2 = history_window_l2(
                    [point.observation for point in preferred_trace[:-1]],
                    [point.observation for point in wrong_trace[:-1]],
                )
                warmup_gate_metrics = warmup_gate_pair_metrics(preferred_trace, wrong_trace)
                row = {
                    "source_index": int(len(source_rows)),
                    "seed": int(seed),
                    "reveal_step": int(reveal_step),
                    "history_length": int(history_length),
                    "preferred_fault": preferred_fault.name,
                    "preferred_fault_family": preferred_fault.family,
                    "preferred_fault_severity": preferred_fault.severity,
                    "preferred_fault_activation_step": int(preferred_fault.activation_step),
                    "preferred_warmup_evidence_steps": int(fault_evidence_steps(preferred_fault, reveal_step)),
                    "wrong_fault": wrong_fault.name,
                    "wrong_fault_family": wrong_fault.family,
                    "wrong_fault_severity": wrong_fault.severity,
                    "wrong_fault_activation_step": int(wrong_fault.activation_step),
                    "wrong_warmup_evidence_steps": int(fault_evidence_steps(wrong_fault, reveal_step)),
                    "capability_pair": capability_pair,
                    "preferred_reveal_bucket": preferred_bucket,
                    "wrong_reveal_bucket": wrong_bucket,
                    "matched_current_pass": bool(matched_current),
                    "bucketed_current_pass": bool(bucketed_current),
                    "matched_or_bucketed_reveal_pass": bool(matched_current or bucketed_current),
                    "warmup_history_l2": warmup_history_l2,
                    "current_hidden_l2": hidden_l2(preferred_current.hidden, wrong_current.hidden),
                    **warmup_gate_metrics,
                    **warmup_gate_source_stratum_metrics(warmup_gate_metrics),
                    **current_metrics,
                }
                source_rows.append(row)
                if int(max_source_rows) > 0 and len(source_rows) >= int(max_source_rows):
                    break
            if int(max_source_rows) > 0 and len(source_rows) >= int(max_source_rows):
                break
        if int(max_source_rows) > 0 and len(source_rows) >= int(max_source_rows):
            break

    checksum_after = model_parameter_checksum(model)
    actor_parameters_changed = bool(str(checksum_after) != str(checksum_before))
    finite_metric_rows = [
        row
        for row in source_rows
        if all(
            np.isfinite(float(row.get(key, float("nan"))))
            for key in (
                "ego_response_l2",
                "actuator_state_l2",
                "previous_command_l2",
                "scene_context_l2",
                "obstacle_position_l2",
                "road_boundary_l2",
                "warmup_history_l2",
                "warmup_response_history_l2",
                "warmup_action_history_l2",
                "current_hidden_l2",
            )
        )
    ]
    matched_or_bucketed_rows = [row for row in source_rows if bool(row.get("matched_or_bucketed_reveal_pass", False))]
    diversity = source_diversity(source_rows)
    matched_diversity = source_diversity(matched_or_bucketed_rows)
    result_class = classify_warmup_smoke_result(
        source_rows=len(source_rows),
        matched_or_bucketed_rows=len(matched_or_bucketed_rows),
        unique_source_seeds=int(diversity["unique_source_seeds"]),
        unique_capability_pairs=int(diversity["unique_capability_pairs"]),
        unique_reveal_buckets=int(diversity["unique_reveal_buckets"]),
        finite_metric_rows=len(finite_metric_rows),
        actor_parameters_changed=actor_parameters_changed,
    )
    distance_metrics = [
        "ego_response_l2",
        "actuator_state_l2",
        "previous_command_l2",
        "road_boundary_l2",
        "obstacle_position_l2",
        "scene_context_l2",
        "full_observation_l2",
        "warmup_history_l2",
        "warmup_response_history_l2",
        "warmup_action_history_l2",
        "warmup_context_history_l2",
        "current_hidden_l2",
    ]
    distance_summary = [
        {"metric": key, **numeric_summary([float(row.get(key, float("nan"))) for row in source_rows])}
        for key in distance_metrics
    ]
    capability_pair_summary = summarize_groups(source_rows, ("capability_pair",))
    reveal_step_summary = summarize_groups(source_rows, ("reveal_step",))
    reveal_bucket_summary = summarize_groups(source_rows, ("preferred_reveal_bucket",))
    warmup_diagnostics = warmup_gate_diagnostics(source_rows)
    matched_warmup_diagnostics = warmup_gate_diagnostics(matched_or_bucketed_rows)
    warmup_strata_summary = warmup_gate_strata_summary(source_rows)
    matched_warmup_strata_summary = warmup_gate_strata_summary(matched_or_bucketed_rows)

    write_csv_rows(run_dir / "warmup_reveal_rows.csv", source_rows)
    write_csv_rows(run_dir / "matched_or_bucketed_rows.csv", matched_or_bucketed_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "distance_summary.csv", distance_summary)
    write_csv_rows(run_dir / "capability_pair_summary.csv", capability_pair_summary)
    write_csv_rows(run_dir / "reveal_step_summary.csv", reveal_step_summary)
    write_csv_rows(run_dir / "reveal_bucket_summary.csv", reveal_bucket_summary)
    write_csv_rows(run_dir / "warmup_gate_strata_summary.csv", warmup_strata_summary)
    write_csv_rows(run_dir / "matched_warmup_gate_strata_summary.csv", matched_warmup_strata_summary)
    summary = {
        "run_type": "warmup_latched_config_smoke",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "reveal_steps": reveal_steps,
        "history_length": int(history_length),
        "min_warmup_evidence_steps": int(min_warmup_evidence_steps),
        "max_source_rows": int(max_source_rows),
        "source_rows": int(len(source_rows)),
        "matched_current_rows": int(sum(1 for row in source_rows if bool(row.get("matched_current_pass", False)))),
        "bucketed_current_rows": int(sum(1 for row in source_rows if bool(row.get("bucketed_current_pass", False)))),
        "matched_or_bucketed_reveal_rows": int(len(matched_or_bucketed_rows)),
        "finite_metric_rows": int(len(finite_metric_rows)),
        "rejected_rows": int(len(rejected_rows)),
        "source_diversity": diversity,
        "matched_or_bucketed_diversity": matched_diversity,
        "distance_summary": distance_summary,
        "warmup_gate_diagnostics": warmup_diagnostics,
        "matched_or_bucketed_warmup_gate_diagnostics": matched_warmup_diagnostics,
        "warmup_gate_strata_summary": warmup_strata_summary,
        "matched_or_bucketed_warmup_gate_strata_summary": matched_warmup_strata_summary,
        "result_class": result_class,
        "structural_smoke_pass": result_class == "warmup_latched_structural_pass",
        "actor_parameters_changed": actor_parameters_changed,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
        "warmup_reveal_rows_csv": run_dir / "warmup_reveal_rows.csv",
        "matched_or_bucketed_rows_csv": run_dir / "matched_or_bucketed_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "distance_summary_csv": run_dir / "distance_summary.csv",
        "capability_pair_summary_csv": run_dir / "capability_pair_summary.csv",
        "reveal_step_summary_csv": run_dir / "reveal_step_summary.csv",
        "reveal_bucket_summary_csv": run_dir / "reveal_bucket_summary.csv",
        "warmup_gate_strata_summary_csv": run_dir / "warmup_gate_strata_summary.csv",
        "matched_warmup_gate_strata_summary_csv": run_dir / "matched_warmup_gate_strata_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training warmup-latched source/config smoke.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=139400)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--reveal-steps", type=parse_int_list, default=(48, 56, 64, 72))
    parser.add_argument("--history-length", type=int, default=36)
    parser.add_argument("--min-warmup-evidence-steps", type=int, default=8)
    parser.add_argument("--max-source-rows", type=int, default=4096)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="warmup_latched_config_smoke")
    summary = run_warmup_latched_config_smoke(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        reveal_steps=tuple(args.reveal_steps),
        history_length=args.history_length,
        min_warmup_evidence_steps=args.min_warmup_evidence_steps,
        max_source_rows=args.max_source_rows,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
