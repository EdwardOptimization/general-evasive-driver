"""Geometry-first source-step action-divergence enrichment.

This module enriches trace-backed source geometry rows with source-step
history-variant action-distance diagnostics. It does not classify terminal
outcomes, train, replay public gates, run PPO, promote checkpoints, or change
actor inputs.
"""

from __future__ import annotations

import argparse
import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    TracePoint,
    collect_fault_trace_window,
    fault_map_from_config,
    roll_hidden_over_observations,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.forward_geometry_source_miner import DEFAULT_MIN_SOURCE_BODY_X
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import (
    deterministic_action_from_hidden,
    zero_current_response_observation,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.trace_source_geometry_materializer import trace_point_at_step
from autodrift.train_ppo import resolve_device
from autodrift.warmup_latched_outcome_probe import CONTROL_VARIANTS, WARMUP_HISTORY_VARIANTS, source_diversity


DEFAULT_VARIANTS = (
    "normal",
    *CONTROL_VARIANTS,
    *WARMUP_HISTORY_VARIANTS,
)
DEFAULT_SEQUENCE_HORIZON = 8
DEFAULT_MIN_SEQUENCE_ACTION_L2 = 0.025
DEFAULT_MIN_FIRST_ACTION_L2 = 0.014

SOURCE_GEOMETRY_REQUIRED_COLUMNS = (
    "source_geometry_index",
    "seed",
    "reveal_step",
    "source_step",
    "preferred_fault",
    "wrong_fault",
    "capability_pair",
    "preferred_reveal_bucket",
    "source_body_x",
    "source_body_y",
    "source_half_width",
)


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0) if np.isfinite(float(value)) else False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_string_tuple(raw: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in str(raw).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one value")
    return values


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"source geometry rows missing required columns: {missing}")


def prepare_source_geometry_frame(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(frame, SOURCE_GEOMETRY_REQUIRED_COLUMNS)
    output = frame.copy()
    for column in (
        "source_geometry_index",
        "seed",
        "reveal_step",
        "source_step",
        "source_body_x",
        "source_body_y",
        "source_half_width",
    ):
        output[column] = pd.to_numeric(output[column], errors="coerce")
    for column in ("matched_current_pass", "bucketed_current_pass", "matched_or_bucketed_reveal_pass"):
        if column in output.columns:
            output[column] = output[column].map(_bool_value)
        else:
            output[column] = False
    for column in ("wrong_reveal_bucket", "preferred_fault_family", "wrong_fault_family"):
        if column not in output.columns:
            output[column] = ""
    return output


def trace_prefix_to_step(trace: list[TracePoint], source_step: int) -> list[TracePoint]:
    prefix = [point for point in trace if int(point.step) <= int(source_step)]
    if not prefix or int(prefix[-1].step) != int(source_step):
        raise ValueError(f"trace does not contain source_step={int(source_step)}")
    return prefix


def _hidden_at_delay(trace: list[TracePoint], delay: int) -> torch.Tensor:
    index = max(0, len(trace) - 1 - int(delay))
    return trace[index].hidden.detach().clone()


def _hidden_from_recent_window(
    model: Any,
    trace: list[TracePoint],
    *,
    length: int,
    device: torch.device,
) -> torch.Tensor:
    hidden = model.initial_hidden(1, device)
    observations = [point.observation for point in trace[max(0, len(trace) - 1 - int(length)) : -1]]
    return roll_hidden_over_observations(model, hidden, observations, device)


def build_source_step_variant_hiddens(
    *,
    model: Any,
    preferred_trace: list[TracePoint],
    wrong_trace: list[TracePoint],
    source_step: int,
    recent_window_length: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    preferred_prefix = trace_prefix_to_step(preferred_trace, source_step)
    wrong_prefix = trace_prefix_to_step(wrong_trace, source_step)
    preferred_current = preferred_prefix[-1]
    wrong_current = wrong_prefix[-1]
    reset_hidden = model.initial_hidden(1, device)
    recent = max(1, int(recent_window_length))
    common = min(len(preferred_prefix), len(wrong_prefix))
    wrong_start = wrong_prefix[max(0, common - 1 - recent)].hidden.detach().clone() if common else wrong_current.hidden
    preferred_recent_observations = [point.observation for point in preferred_prefix[max(0, len(preferred_prefix) - recent) : -1]]
    return {
        "normal": preferred_current.hidden.detach().clone(),
        "reset_hidden": reset_hidden.detach().clone(),
        "zero_current_response": preferred_current.hidden.detach().clone(),
        "delayed_warmup_history_8": _hidden_at_delay(preferred_prefix, 8),
        "delayed_warmup_history_16": _hidden_at_delay(preferred_prefix, 16),
        "wrong_warmup_history_same_reveal": wrong_current.hidden.detach().clone(),
        "same_recent_wrong_warmup_history": roll_hidden_over_observations(
            model,
            wrong_start,
            preferred_recent_observations,
            device,
        ),
        "warmup_removed": reset_hidden.detach().clone(),
        "warmup_shortened_8": _hidden_from_recent_window(model, preferred_prefix, length=8, device=device),
    }


def _policy_observation_for_variant(observation: np.ndarray, *, variant: str, response_dim: int) -> np.ndarray:
    policy_obs = np.asarray(observation, dtype=np.float32).copy()
    if variant == "zero_current_response":
        policy_obs = zero_current_response_observation(policy_obs, response_dim)
    return policy_obs


def _rollout_actions(
    *,
    model: Any,
    snapshot: TracePoint,
    variant: str,
    initial_hidden: torch.Tensor,
    sequence_horizon: int,
    response_dim: int,
    device: torch.device,
) -> list[np.ndarray]:
    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = initial_hidden.detach().clone()
    actions: list[np.ndarray] = []
    terminated = False
    truncated = False
    for _ in range(max(1, int(sequence_horizon))):
        if terminated or truncated:
            break
        if variant == "reset_hidden":
            hidden = model.initial_hidden(1, device)
        policy_obs = _policy_observation_for_variant(obs, variant=variant, response_dim=response_dim)
        action, next_hidden = deterministic_action_from_hidden(model, policy_obs, hidden, device)
        actions.append(action)
        hidden = next_hidden
        obs, _, terminated, truncated, _ = env.step(action)
    return actions


def evaluate_source_step_variant_actions(
    *,
    model: Any,
    source_snapshot: TracePoint,
    variant: str,
    variant_hidden: torch.Tensor,
    normal_first_action: np.ndarray | None,
    normal_actions: list[np.ndarray] | None,
    sequence_horizon: int,
    response_dim: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    actions = _rollout_actions(
        model=model,
        snapshot=source_snapshot,
        variant=variant,
        initial_hidden=variant_hidden,
        sequence_horizon=sequence_horizon,
        response_dim=response_dim,
        device=device,
    )
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    if normal_first_action is None:
        first_l2 = 0.0
        first_delta = np.zeros(3, dtype=np.float32)
    else:
        first_delta = first_action - np.asarray(normal_first_action, dtype=np.float32)
        first_l2 = float(np.linalg.norm(first_delta))
    distances = zero_action_trajectory_distances(len(actions)) if normal_actions is None else action_trajectory_distances(actions, normal_actions)
    return {
        "variant": variant,
        "variant_time_anchor": "source_step",
        "first_action_l2": float(first_l2),
        "first_steer_delta": float(first_delta[0]),
        "first_throttle_delta": float(first_delta[1]),
        "first_brake_delta": float(first_delta[2]),
        "sequence_action_l2_mean": float(distances["action_trajectory_distance_mean"]),
        "sequence_action_l2_max": float(distances["action_trajectory_distance_max"]),
        "sequence_action_l2_rms": float(distances["action_trajectory_distance_rms"]),
        "sequence_steps": int(distances["action_trajectory_compare_steps"]),
    }, actions


def enrich_source_geometry_row(
    row: pd.Series | dict[str, Any],
    *,
    model: Any,
    preferred_trace: list[TracePoint],
    wrong_trace: list[TracePoint],
    variants: tuple[str, ...] = DEFAULT_VARIANTS,
    recent_window_length: int = 8,
    sequence_horizon: int = DEFAULT_SEQUENCE_HORIZON,
    response_dim: int = 12,
    device: torch.device,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
    min_first_action_l2: float = DEFAULT_MIN_FIRST_ACTION_L2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item = dict(row)
    source_step = int(item["source_step"])
    preferred_prefix = trace_prefix_to_step(preferred_trace, source_step)
    source_snapshot = preferred_prefix[-1]
    variant_hiddens = build_source_step_variant_hiddens(
        model=model,
        preferred_trace=preferred_trace,
        wrong_trace=wrong_trace,
        source_step=source_step,
        recent_window_length=recent_window_length,
        device=device,
    )
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    normal_metrics, normal_actions = evaluate_source_step_variant_actions(
        model=model,
        source_snapshot=source_snapshot,
        variant="normal",
        variant_hidden=variant_hiddens["normal"],
        normal_first_action=None,
        normal_actions=None,
        sequence_horizon=sequence_horizon,
        response_dim=response_dim,
        device=device,
    )
    normal_first = normal_actions[0] if normal_actions else np.full(3, float("nan"), dtype=np.float32)
    for variant in variants:
        if variant not in variant_hiddens:
            rejected_rows.append(
                {
                    "source_geometry_index": item.get("source_geometry_index", ""),
                    "seed": item.get("seed", ""),
                    "source_step": source_step,
                    "variant": variant,
                    "enrichment_rejection_reason": "unknown_variant",
                    "error": f"unknown source-step variant {variant!r}",
                }
            )
            continue
        try:
            if variant == "normal":
                metrics = dict(normal_metrics)
            else:
                metrics, _ = evaluate_source_step_variant_actions(
                    model=model,
                    source_snapshot=source_snapshot,
                    variant=variant,
                    variant_hidden=variant_hiddens[variant],
                    normal_first_action=normal_first,
                    normal_actions=normal_actions,
                    sequence_horizon=sequence_horizon,
                    response_dim=response_dim,
                    device=device,
                )
        except Exception as exc:
            rejected_rows.append(
                {
                    "source_geometry_index": item.get("source_geometry_index", ""),
                    "seed": item.get("seed", ""),
                    "source_step": source_step,
                    "variant": variant,
                    "enrichment_rejection_reason": "action_metric_failed",
                    "error": str(exc),
                }
            )
            continue
        history_variant = variant in WARMUP_HISTORY_VARIANTS
        control_variant = variant in CONTROL_VARIANTS
        action_divergent = bool(
            _finite(metrics.get("sequence_action_l2_mean"), 0.0) >= float(min_sequence_action_l2)
            or _finite(metrics.get("first_action_l2"), 0.0) >= float(min_first_action_l2)
        )
        accepted_rows.append(
            {
                **item,
                **metrics,
                "action_divergent": action_divergent,
                "history_variant": history_variant,
                "control_variant": control_variant,
                "enrichment_rejection_reason": "pass",
            }
        )
    return accepted_rows, rejected_rows


def enrich_source_geometry_rows(
    frame: pd.DataFrame,
    *,
    model: Any,
    trace_for: Callable[[int, str, int], list[TracePoint]],
    variants: tuple[str, ...] = DEFAULT_VARIANTS,
    recent_window_length: int = 8,
    sequence_horizon: int = DEFAULT_SEQUENCE_HORIZON,
    response_dim: int = 12,
    device: torch.device,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
    min_first_action_l2: float = DEFAULT_MIN_FIRST_ACTION_L2,
    max_source_geometry_rows: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_rows = prepare_source_geometry_frame(frame)
    if int(max_source_geometry_rows) > 0:
        source_rows = source_rows.head(int(max_source_geometry_rows)).copy()
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    trace_cache: dict[tuple[int, str, int], list[TracePoint]] = {}

    def cached_trace(seed: int, fault_name: str, reveal_step: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(reveal_step))
        if key not in trace_cache:
            trace_cache[key] = trace_for(int(seed), str(fault_name), int(reveal_step))
        return trace_cache[key]

    for _, row in source_rows.iterrows():
        seed = int(row["seed"])
        reveal_step = int(row["reveal_step"])
        try:
            preferred_trace = cached_trace(seed, str(row["preferred_fault"]), reveal_step)
            wrong_trace = cached_trace(seed, str(row["wrong_fault"]), reveal_step)
            accepted, rejected = enrich_source_geometry_row(
                row,
                model=model,
                preferred_trace=preferred_trace,
                wrong_trace=wrong_trace,
                variants=variants,
                recent_window_length=recent_window_length,
                sequence_horizon=sequence_horizon,
                response_dim=response_dim,
                device=device,
                min_sequence_action_l2=min_sequence_action_l2,
                min_first_action_l2=min_first_action_l2,
            )
            accepted_rows.extend(accepted)
            rejected_rows.extend(rejected)
        except Exception as exc:
            rejected_rows.append(
                {
                    "source_geometry_index": row.get("source_geometry_index", ""),
                    "seed": seed,
                    "source_step": row.get("source_step", ""),
                    "variant": "",
                    "enrichment_rejection_reason": "trace_or_row_enrichment_failed",
                    "error": str(exc),
                }
            )
    return pd.DataFrame(accepted_rows), pd.DataFrame(rejected_rows)


def select_enriched_source_rows(
    frame: pd.DataFrame,
    *,
    max_candidates: int,
    per_seed_cap: int,
    per_capability_pair_cap: int,
    per_reveal_bucket_cap: int,
    per_source_step_cap: int,
    per_variant_cap: int,
    min_source_body_x: float = DEFAULT_MIN_SOURCE_BODY_X,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    candidates = frame.copy()
    for column in ("source_body_x", "first_action_l2", "sequence_action_l2_mean"):
        candidates[column] = pd.to_numeric(candidates[column], errors="coerce")
    candidates = candidates[
        candidates["history_variant"].map(_bool_value)
        & candidates["action_divergent"].map(_bool_value)
        & (candidates["source_body_x"] >= float(min_source_body_x))
    ].copy()
    if candidates.empty:
        return candidates
    candidates["_matched_rank"] = candidates["matched_current_pass"].map(_bool_value) | candidates["bucketed_current_pass"].map(_bool_value)
    candidates["_score"] = (
        candidates["source_body_x"].fillna(0.0) / 10.0
        + candidates["sequence_action_l2_mean"].fillna(0.0) / 0.10
        + candidates["first_action_l2"].fillna(0.0) / 0.10
        + candidates["_matched_rank"].astype(float)
    )
    candidates = candidates.sort_values(
        ["_score", "source_body_x", "sequence_action_l2_mean", "first_action_l2", "seed", "source_step"],
        ascending=[False, False, False, False, True, True],
    )
    caps = {
        "seed": int(per_seed_cap),
        "capability_pair": int(per_capability_pair_cap),
        "preferred_reveal_bucket": int(per_reveal_bucket_cap),
        "source_step": int(per_source_step_cap),
        "variant": int(per_variant_cap),
    }
    counts: dict[str, dict[Any, int]] = {key: {} for key in caps}
    selected_rows: list[dict[str, Any]] = []
    for _, row in candidates.iterrows():
        values = {key: row.get(key) for key in caps}
        if any(caps[key] > 0 and counts[key].get(values[key], 0) >= caps[key] for key in caps):
            continue
        selected_rows.append(dict(row))
        for key, value in values.items():
            counts[key][value] = counts[key].get(value, 0) + 1
        if int(max_candidates) > 0 and len(selected_rows) >= int(max_candidates):
            break
    selected = pd.DataFrame(selected_rows)
    if not selected.empty:
        selected["selected_enriched_rank"] = np.arange(len(selected), dtype=int)
    return selected.reset_index(drop=True)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.to_dict("records") if not frame.empty else []


def _numeric_summary(frame: pd.DataFrame, column: str) -> dict[str, float | None]:
    if column not in frame.columns:
        return {"min": None, "p50": None, "p95": None}
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return {"min": None, "p50": None, "p95": None}
    return {
        "min": float(values.min()),
        "p50": float(values.quantile(0.50)),
        "p95": float(values.quantile(0.95)),
    }


def _group_summary(frame: pd.DataFrame, key: str) -> list[dict[str, Any]]:
    if frame.empty or key not in frame.columns:
        return []
    return [{key: str(value), "rows": int(len(group))} for value, group in frame.groupby(key, observed=True)]


def build_enrichment_summary(
    *,
    enriched: pd.DataFrame,
    selected: pd.DataFrame,
    rejected: pd.DataFrame,
    source_enrichment_started: bool = False,
    actor_parameters_changed: bool = False,
) -> dict[str, Any]:
    sequence = _numeric_summary(enriched, "sequence_action_l2_mean")
    first = _numeric_summary(enriched, "first_action_l2")
    return {
        "run_type": "geometry_first_action_divergence_enrichment",
        "enriched_source_geometry_rows": int(len(enriched)),
        "selected_enriched_rows": int(len(selected)),
        "rejected_rows": int(len(rejected)),
        "sequence_action_l2_mean_min": sequence["min"],
        "sequence_action_l2_mean_p50": sequence["p50"],
        "sequence_action_l2_mean_p95": sequence["p95"],
        "first_action_l2_min": first["min"],
        "first_action_l2_p50": first["p50"],
        "first_action_l2_p95": first["p95"],
        "variant_summary": _group_summary(enriched, "variant"),
        "selected_diversity": source_diversity(_records(selected)),
        "source_enrichment_started": bool(source_enrichment_started),
        "source_materialization_run_started": False,
        "source_mining_started": False,
        "source_preflight_started": False,
        "replay_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_parameters_changed": bool(actor_parameters_changed),
        "actor_input_contract_changed": False,
    }


def write_enrichment_outputs(
    *,
    run_dir: Path,
    enriched: pd.DataFrame,
    selected: pd.DataFrame,
    rejected: pd.DataFrame,
    source_enrichment_started: bool = False,
    actor_parameters_changed: bool = False,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = build_enrichment_summary(
        enriched=enriched,
        selected=selected,
        rejected=rejected,
        source_enrichment_started=source_enrichment_started,
        actor_parameters_changed=actor_parameters_changed,
    )
    summary["enriched_source_geometry_rows_csv"] = run_dir / "enriched_source_geometry_rows.csv"
    summary["selected_enriched_rows_csv"] = run_dir / "selected_enriched_rows.csv"
    summary["rejected_rows_csv"] = run_dir / "rejected_rows.csv"
    summary["variant_summary_csv"] = run_dir / "variant_summary.csv"
    summary["source_diversity_summary_csv"] = run_dir / "source_diversity_summary.csv"
    summary["summary_json"] = run_dir / "summary.json"
    write_csv_rows(run_dir / "enriched_source_geometry_rows.csv", _records(enriched))
    write_csv_rows(run_dir / "selected_enriched_rows.csv", _records(selected))
    write_csv_rows(run_dir / "rejected_rows.csv", _records(rejected))
    write_csv_rows(run_dir / "variant_summary.csv", summary["variant_summary"])
    write_csv_rows(run_dir / "source_diversity_summary.csv", [{"row_set": "selected_enriched_rows", **summary["selected_diversity"]}])
    write_json(run_dir / "summary.json", summary)
    return summary


def run_source_action_divergence_enrichment_from_rows(
    *,
    source_geometry_rows_path: Path,
    model: Any,
    trace_for: Callable[[int, str, int], list[TracePoint]],
    run_dir: Path,
    device: torch.device,
    variants: tuple[str, ...] = DEFAULT_VARIANTS,
    recent_window_length: int = 8,
    sequence_horizon: int = DEFAULT_SEQUENCE_HORIZON,
    response_dim: int = 12,
    max_source_geometry_rows: int = 0,
    max_candidates: int = 128,
    per_seed_cap: int = 24,
    per_capability_pair_cap: int = 12,
    per_reveal_bucket_cap: int = 12,
    per_source_step_cap: int = 24,
    per_variant_cap: int = 48,
    source_enrichment_started: bool = False,
    actor_parameters_changed: bool = False,
) -> dict[str, Any]:
    frame = pd.read_csv(source_geometry_rows_path)
    enriched, rejected = enrich_source_geometry_rows(
        frame,
        model=model,
        trace_for=trace_for,
        variants=variants,
        recent_window_length=recent_window_length,
        sequence_horizon=sequence_horizon,
        response_dim=response_dim,
        device=device,
        max_source_geometry_rows=max_source_geometry_rows,
    )
    selected = select_enriched_source_rows(
        enriched,
        max_candidates=max_candidates,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_reveal_bucket_cap=per_reveal_bucket_cap,
        per_source_step_cap=per_source_step_cap,
        per_variant_cap=per_variant_cap,
    )
    return write_enrichment_outputs(
        run_dir=run_dir,
        enriched=enriched,
        selected=selected,
        rejected=rejected,
        source_enrichment_started=source_enrichment_started,
        actor_parameters_changed=actor_parameters_changed,
    )


def run_source_action_divergence_enrichment(
    *,
    checkpoint_path: Path,
    config_path: Path,
    source_geometry_rows_path: Path,
    run_dir: Path,
    device: str,
    history_length: int,
    variants: tuple[str, ...] = DEFAULT_VARIANTS,
    recent_window_length: int = 8,
    sequence_horizon: int = DEFAULT_SEQUENCE_HORIZON,
    max_source_geometry_rows: int = 0,
    max_candidates: int = 128,
    per_seed_cap: int = 24,
    per_capability_pair_cap: int = 12,
    per_reveal_bucket_cap: int = 12,
    per_source_step_cap: int = 24,
    per_variant_cap: int = 48,
) -> dict[str, Any]:
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    trace_cache: dict[tuple[int, str, int, int], list[TracePoint]] = {}

    def trace_for(seed: int, fault_name: str, reveal_step: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(reveal_step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault_by_name[str(fault_name)],
                seed=int(seed),
                target_step=int(reveal_step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    summary = run_source_action_divergence_enrichment_from_rows(
        source_geometry_rows_path=source_geometry_rows_path,
        model=model,
        trace_for=trace_for,
        run_dir=run_dir,
        device=resolved_device,
        variants=variants,
        recent_window_length=recent_window_length,
        sequence_horizon=sequence_horizon,
        response_dim=response_dim,
        max_source_geometry_rows=max_source_geometry_rows,
        max_candidates=max_candidates,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_reveal_bucket_cap=per_reveal_bucket_cap,
        per_source_step_cap=per_source_step_cap,
        per_variant_cap=per_variant_cap,
        source_enrichment_started=True,
        actor_parameters_changed=str(model_parameter_checksum(model)) != str(checksum_before),
    )
    summary["checkpoint_path"] = str(checkpoint_path)
    summary["config_path"] = str(config_path)
    summary["source_geometry_rows_path"] = str(source_geometry_rows_path)
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--source-geometry-rows", type=Path, required=True)
    parser.add_argument("--variants", type=parse_string_tuple, default=DEFAULT_VARIANTS)
    parser.add_argument("--history-length", type=int, default=56)
    parser.add_argument("--recent-window-length", type=int, default=8)
    parser.add_argument("--sequence-horizon", type=int, default=DEFAULT_SEQUENCE_HORIZON)
    parser.add_argument("--max-source-geometry-rows", type=int, default=0)
    parser.add_argument("--max-candidates", type=int, default=128)
    parser.add_argument("--per-seed-cap", type=int, default=24)
    parser.add_argument("--per-capability-pair-cap", type=int, default=12)
    parser.add_argument("--per-reveal-bucket-cap", type=int, default=12)
    parser.add_argument("--per-source-step-cap", type=int, default=24)
    parser.add_argument("--per-variant-cap", type=int, default=48)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Validate arguments only without loading a checkpoint or running enrichment.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    if args.no_run:
        print("source action-divergence enrichment arguments validated")
        print(f"source_geometry_rows={args.source_geometry_rows}")
        print(f"run_dir={args.run_dir}")
        return
    if args.checkpoint is None or args.config is None:
        raise SystemExit("--checkpoint and --config are required unless --no-run is set")
    summary = run_source_action_divergence_enrichment(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        source_geometry_rows_path=args.source_geometry_rows,
        run_dir=args.run_dir,
        device=args.device,
        history_length=int(args.history_length),
        variants=tuple(args.variants),
        recent_window_length=int(args.recent_window_length),
        sequence_horizon=int(args.sequence_horizon),
        max_source_geometry_rows=int(args.max_source_geometry_rows),
        max_candidates=int(args.max_candidates),
        per_seed_cap=int(args.per_seed_cap),
        per_capability_pair_cap=int(args.per_capability_pair_cap),
        per_reveal_bucket_cap=int(args.per_reveal_bucket_cap),
        per_source_step_cap=int(args.per_source_step_cap),
        per_variant_cap=int(args.per_variant_cap),
    )
    print(f"summary_json={args.run_dir / 'summary.json'}")
    print(f"enriched_source_geometry_rows={summary['enriched_source_geometry_rows']}")
    print(f"selected_enriched_rows={summary['selected_enriched_rows']}")


if __name__ == "__main__":
    main()
