"""No-training bounded relocation replay probe for warmup-history rows."""

from __future__ import annotations

import argparse
import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    TracePoint,
    collect_fault_trace_window,
    fault_map_from_config,
)
from autodrift.causal_history_candidate_outcome_probe import replay_probe_variant
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.warmup_latched_outcome_probe import (
    CONTROL_VARIANTS,
    WARMUP_HISTORY_VARIANTS,
    build_warmup_variant_hiddens,
    source_diversity,
)
from autodrift.wrong_history_boundary_relocation_surface import (
    obstacle_body_geometry,
    relocate_outcome_snapshot,
)


DEFAULT_MIN_SEQUENCE_ACTION_L2 = 0.025
DEFAULT_MIN_MARGIN_GAP = 0.02
DEFAULT_MIN_BODY_X = 2.0
DEFAULT_MIN_HALF_WIDTH = 0.05
DEFAULT_MIN_SOURCE_BODY_X = 4.0
DEFAULT_PER_SEED_CAP = 24
DEFAULT_PER_REVEAL_BUCKET_CAP = 12
DEFAULT_PER_VARIANT_CAP = 48
DEFAULT_CANDIDATE_STEP_COLUMN = "reveal_step"


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


def _source_key(row: pd.Series | dict[str, Any]) -> str:
    if "selected_index" in row and str(row.get("selected_index", "")) != "":
        return f"selected:{row.get('selected_index')}"
    return "|".join(
        str(row.get(column, ""))
        for column in ("source_index", "seed", "reveal_step", "preferred_fault", "wrong_fault")
    )


def candidate_step_for_row(row: pd.Series | dict[str, Any], candidate_step_column: str) -> int:
    if candidate_step_column not in row:
        raise ValueError(f"candidate step column not found: {candidate_step_column}")
    value = row.get(candidate_step_column)
    if pd.isna(value):
        raise ValueError(f"candidate step column is not finite: {candidate_step_column}")
    return int(value)


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"candidate rows missing required columns: {missing}")


def prepare_candidate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = (
        "seed",
        "reveal_step",
        "preferred_fault",
        "wrong_fault",
        "variant",
        "capability_pair",
        "preferred_reveal_bucket",
        "sequence_action_l2_mean",
        "body_longitudinal_offset",
        "body_lateral_offset",
        "half_width_inflation",
    )
    _require_columns(frame, required)
    output = frame.copy()
    if "margin_gap" not in output.columns:
        output["margin_gap"] = 0.0
    for column in (
        "sequence_action_l2_mean",
        "margin_gap",
        "normal_margin",
        "variant_margin",
        "body_longitudinal_offset",
        "body_lateral_offset",
        "half_width_inflation",
        "proxy_normal_margin",
    ):
        if column in output.columns:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    for column in ("matched_current_pass", "bucketed_current_pass", "proxy_preferred_normal_margin"):
        if column in output.columns:
            output[column] = output[column].map(_bool_value)
    output["history_variant"] = output["variant"].astype(str).isin(WARMUP_HISTORY_VARIANTS)
    output["control_variant"] = output["variant"].astype(str).isin(CONTROL_VARIANTS)
    output["source_key"] = [_source_key(row) for _, row in output.iterrows()]
    return output


def select_replay_candidates(
    frame: pd.DataFrame,
    *,
    max_candidate_rows: int,
    per_capability_pair_cap: int,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
) -> pd.DataFrame:
    candidates = prepare_candidate_frame(frame)
    candidates = candidates[
        candidates["history_variant"]
        & (candidates["sequence_action_l2_mean"] >= float(min_sequence_action_l2))
    ].copy()
    if candidates.empty:
        return candidates
    candidates["_preferred_proxy_rank"] = (
        candidates["proxy_preferred_normal_margin"].astype(bool)
        if "proxy_preferred_normal_margin" in candidates.columns
        else False
    )
    candidates["_nonnegative_margin_gap_rank"] = candidates["margin_gap"] >= 0.0
    candidates["_score"] = (
        candidates["sequence_action_l2_mean"].fillna(0.0) / 0.10
        + candidates["margin_gap"].fillna(0.0).clip(lower=0.0) / 0.02
        + candidates["_preferred_proxy_rank"].astype(float)
        + 0.25 * candidates["_nonnegative_margin_gap_rank"].astype(float)
    )
    candidates = candidates.sort_values(
        ["_score", "sequence_action_l2_mean", "margin_gap", "seed", "reveal_step"],
        ascending=[False, False, False, True, True],
    )
    selected_groups: list[pd.DataFrame] = []
    for _, group in candidates.groupby("capability_pair", observed=True):
        selected_groups.append(group.head(max(1, int(per_capability_pair_cap))))
    if not selected_groups:
        return candidates.head(0)
    selected = pd.concat(selected_groups, ignore_index=True).sort_values("_score", ascending=False)
    if int(max_candidate_rows) > 0:
        selected = selected.head(int(max_candidate_rows))
    selected["selected_replay_rank"] = np.arange(len(selected), dtype=int)
    return selected.reset_index(drop=True)


def bounded_relocation_geometry(
    *,
    source_body_x: float,
    source_body_y: float,
    source_half_width: float,
    body_longitudinal_offset: float,
    body_lateral_offset: float,
    half_width_inflation: float,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> dict[str, float]:
    raw_body_x = float(source_body_x) + float(body_longitudinal_offset)
    raw_half_width = float(source_half_width) + float(half_width_inflation)
    body_x = max(float(min_body_x), raw_body_x)
    half_width = max(float(min_half_width), raw_half_width)
    return {
        "raw_relocated_body_x": float(raw_body_x),
        "relocated_body_x": float(body_x),
        "relocated_body_y": float(source_body_y) + float(body_lateral_offset),
        "raw_relocated_half_width": float(raw_half_width),
        "relocated_half_width": float(half_width),
        "relocation_body_x_clipped": bool(raw_body_x <= float(min_body_x) + 1e-6),
        "relocation_half_width_clipped": bool(raw_half_width <= float(min_half_width) + 1e-6),
    }


def classify_actual_replay_result(
    *,
    variant: str,
    normal_success: bool,
    variant_success: bool,
    normal_margin: float,
    variant_margin: float,
    sequence_action_l2_mean: float,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
    min_margin_gap: float = DEFAULT_MIN_MARGIN_GAP,
) -> dict[str, Any]:
    normal_viable = bool(normal_success and np.isfinite(normal_margin) and normal_margin >= 0.0)
    success_drop = bool(normal_success and not variant_success)
    margin_gap = (
        float(normal_margin) - float(variant_margin)
        if np.isfinite(normal_margin) and np.isfinite(variant_margin)
        else float("nan")
    )
    sequence_action_critical = bool(float(sequence_action_l2_mean) >= float(min_sequence_action_l2))
    outcome_critical = bool(
        normal_viable
        and sequence_action_critical
        and (success_drop or (np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap)))
    )
    history_positive = bool(outcome_critical and str(variant) in WARMUP_HISTORY_VARIANTS)
    control_positive = bool(outcome_critical and str(variant) in CONTROL_VARIANTS)
    return {
        "normal_viable": normal_viable,
        "success_drop": success_drop,
        "margin_gap": margin_gap,
        "sequence_action_critical": sequence_action_critical,
        "outcome_critical": outcome_critical,
        "history_positive": history_positive,
        "control_positive": control_positive,
    }


def classify_relocation_geometry(
    *,
    source_body_x: float,
    source_body_y: float,
    source_half_width: float,
    body_longitudinal_offset: float,
    body_lateral_offset: float,
    half_width_inflation: float,
    min_source_body_x: float = DEFAULT_MIN_SOURCE_BODY_X,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> dict[str, Any]:
    geometry = bounded_relocation_geometry(
        source_body_x=source_body_x,
        source_body_y=source_body_y,
        source_half_width=source_half_width,
        body_longitudinal_offset=body_longitudinal_offset,
        body_lateral_offset=body_lateral_offset,
        half_width_inflation=half_width_inflation,
        min_body_x=min_body_x,
        min_half_width=min_half_width,
    )
    values = [
        source_body_x,
        source_body_y,
        source_half_width,
        body_longitudinal_offset,
        body_lateral_offset,
        half_width_inflation,
        geometry["relocated_body_x"],
        geometry["relocated_body_y"],
        geometry["relocated_half_width"],
    ]
    finite_geometry = all(np.isfinite(float(value)) for value in values)
    reasons: list[str] = []
    if not finite_geometry:
        reasons.append("nonfinite_geometry")
    if finite_geometry and float(source_body_x) < float(min_source_body_x):
        reasons.append("source_body_x_too_close")
    if bool(geometry["relocation_body_x_clipped"]):
        reasons.append("relocation_body_x_clipped")
    if finite_geometry and float(source_half_width) < float(min_half_width):
        reasons.append("source_half_width_too_small")
    if bool(geometry["relocation_half_width_clipped"]):
        reasons.append("relocation_half_width_clipped")
    return {
        "source_body_x": float(source_body_x),
        "source_body_y": float(source_body_y),
        "source_half_width": float(source_half_width),
        **geometry,
        "geometry_pass": not reasons,
        "geometry_rejection_reason": "pass" if not reasons else "|".join(reasons),
    }


def geometry_preflight_frame(
    frame: pd.DataFrame,
    *,
    min_source_body_x: float = DEFAULT_MIN_SOURCE_BODY_X,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> pd.DataFrame:
    _require_columns(frame, ("source_body_x", "source_body_y", "source_half_width"))
    candidates = prepare_candidate_frame(frame)
    for column in ("source_body_x", "source_body_y", "source_half_width"):
        candidates[column] = pd.to_numeric(candidates[column], errors="coerce")
    rows: list[dict[str, Any]] = []
    for _, row in candidates.iterrows():
        output = dict(row)
        output.update(
            classify_relocation_geometry(
                source_body_x=_finite(row.get("source_body_x")),
                source_body_y=_finite(row.get("source_body_y")),
                source_half_width=_finite(row.get("source_half_width")),
                body_longitudinal_offset=_finite(row.get("body_longitudinal_offset")),
                body_lateral_offset=_finite(row.get("body_lateral_offset")),
                half_width_inflation=_finite(row.get("half_width_inflation")),
                min_source_body_x=min_source_body_x,
                min_body_x=min_body_x,
                min_half_width=min_half_width,
            )
        )
        rows.append(output)
    return pd.DataFrame(rows)


def _cap_allows(counts: dict[Any, int], key: Any, cap: int) -> bool:
    return int(cap) <= 0 or counts.get(key, 0) < int(cap)


def select_geometry_aware_replay_candidates(
    preflight: pd.DataFrame,
    *,
    max_candidate_rows: int,
    per_seed_cap: int = DEFAULT_PER_SEED_CAP,
    per_capability_pair_cap: int = 12,
    per_reveal_bucket_cap: int = DEFAULT_PER_REVEAL_BUCKET_CAP,
    per_variant_cap: int = DEFAULT_PER_VARIANT_CAP,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
) -> pd.DataFrame:
    if preflight.empty:
        return preflight.copy()
    frame = preflight.copy()
    if "history_variant" not in frame.columns:
        frame["history_variant"] = frame["variant"].astype(str).isin(WARMUP_HISTORY_VARIANTS)
    frame["geometry_pass"] = frame["geometry_pass"].map(_bool_value)
    frame["sequence_action_l2_mean"] = pd.to_numeric(frame["sequence_action_l2_mean"], errors="coerce")
    candidates = frame[
        frame["geometry_pass"]
        & frame["history_variant"].astype(bool)
        & (frame["sequence_action_l2_mean"] >= float(min_sequence_action_l2))
    ].copy()
    if candidates.empty:
        return candidates
    candidates["_preferred_proxy_rank"] = (
        candidates["proxy_preferred_normal_margin"].map(_bool_value)
        if "proxy_preferred_normal_margin" in candidates.columns
        else False
    )
    candidates["_nonnegative_margin_gap_rank"] = pd.to_numeric(
        candidates.get("margin_gap", 0.0), errors="coerce"
    ).fillna(0.0) >= 0.0
    candidates["_score"] = (
        candidates["sequence_action_l2_mean"].fillna(0.0) / 0.10
        + pd.to_numeric(candidates.get("margin_gap", 0.0), errors="coerce").fillna(0.0).clip(lower=0.0) / 0.02
        + candidates["_preferred_proxy_rank"].astype(float)
        + 0.25 * candidates["_nonnegative_margin_gap_rank"].astype(float)
    )
    candidates = candidates.sort_values(
        ["_score", "source_body_x", "sequence_action_l2_mean", "seed", "reveal_step"],
        ascending=[False, False, False, True, True],
    )
    selected_rows: list[dict[str, Any]] = []
    seed_counts: dict[Any, int] = {}
    pair_counts: dict[Any, int] = {}
    bucket_counts: dict[Any, int] = {}
    variant_counts: dict[Any, int] = {}
    for _, row in candidates.iterrows():
        seed = row.get("seed")
        pair = row.get("capability_pair")
        bucket = row.get("preferred_reveal_bucket")
        variant = row.get("variant")
        if not (
            _cap_allows(seed_counts, seed, per_seed_cap)
            and _cap_allows(pair_counts, pair, per_capability_pair_cap)
            and _cap_allows(bucket_counts, bucket, per_reveal_bucket_cap)
            and _cap_allows(variant_counts, variant, per_variant_cap)
        ):
            continue
        selected_rows.append(dict(row))
        seed_counts[seed] = seed_counts.get(seed, 0) + 1
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        variant_counts[variant] = variant_counts.get(variant, 0) + 1
        if int(max_candidate_rows) > 0 and len(selected_rows) >= int(max_candidate_rows):
            break
    selected = pd.DataFrame(selected_rows)
    if not selected.empty:
        selected["selected_replay_rank"] = np.arange(len(selected), dtype=int)
    return selected.reset_index(drop=True)


def _numeric_summary(series: pd.Series) -> dict[str, float | None]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return {"min": None, "p50": None, "p95": None}
    return {
        "min": float(numeric.min()),
        "p50": float(numeric.quantile(0.50)),
        "p95": float(numeric.quantile(0.95)),
    }


def build_geometry_preflight_summary(
    *,
    preflight_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    preflight = pd.DataFrame(preflight_rows)
    selected = pd.DataFrame(selected_rows)
    geometry_pass = preflight[preflight["geometry_pass"].astype(bool)] if "geometry_pass" in preflight else preflight
    history_candidates = (
        preflight[preflight["history_variant"].astype(bool)] if "history_variant" in preflight else preflight
    )
    clipped_share = (
        float(selected["relocation_body_x_clipped"].astype(bool).mean())
        if not selected.empty and "relocation_body_x_clipped" in selected
        else 0.0
    )
    reason_counts = (
        preflight["geometry_rejection_reason"].value_counts(dropna=False).to_dict()
        if "geometry_rejection_reason" in preflight
        else {}
    )
    source_body_x = _numeric_summary(selected["source_body_x"]) if "source_body_x" in selected else _numeric_summary(pd.Series(dtype=float))
    return {
        "run_type": "geometry_aware_replay_selector_preflight",
        "input_rows": int(len(preflight_rows)),
        "history_candidate_rows": int(len(history_candidates)),
        "geometry_pass_rows": int(len(geometry_pass)),
        "selected_candidate_rows": int(len(selected_rows)),
        "rejected_rows": int(len(rejected_rows)),
        "rejected_reason_counts": {str(key): int(value) for key, value in reason_counts.items()},
        "selected_diversity": source_diversity(selected_rows),
        "geometry_pass_diversity": source_diversity(_records(geometry_pass)),
        "relocation_clipped_share": clipped_share,
        "source_body_x_min": source_body_x["min"],
        "source_body_x_p50": source_body_x["p50"],
        "source_body_x_p95": source_body_x["p95"],
        "replay_started": False,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
    }


def write_geometry_preflight_outputs(
    *,
    run_dir: Path,
    preflight: pd.DataFrame,
    selected: pd.DataFrame,
    rejected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    preflight_records = _records(preflight)
    selected_records = _records(selected)
    summary = build_geometry_preflight_summary(
        preflight_rows=preflight_records,
        selected_rows=selected_records,
        rejected_rows=rejected_rows,
    )
    summary["run_type"] = "geometry_aware_preflight_only_probe"
    summary["source_preflight_started"] = True
    summary["geometry_preflight_rows_csv"] = run_dir / "geometry_preflight_rows.csv"
    summary["selected_candidate_rows_csv"] = run_dir / "selected_candidate_rows.csv"
    summary["geometry_rejected_rows_csv"] = run_dir / "geometry_rejected_rows.csv"
    summary["source_diversity_summary_csv"] = run_dir / "source_diversity_summary.csv"
    summary["summary_json"] = run_dir / "summary.json"
    source_diversity_summary = [
        {"row_set": "geometry_preflight_rows", **source_diversity(preflight_records)},
        {"row_set": "selected_candidate_rows", **source_diversity(selected_records)},
    ]
    write_csv_rows(run_dir / "geometry_preflight_rows.csv", preflight_records)
    write_csv_rows(run_dir / "selected_candidate_rows.csv", selected_records)
    write_csv_rows(run_dir / "geometry_rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "source_diversity_summary.csv", source_diversity_summary)
    write_json(run_dir / "summary.json", summary)
    return summary


def _trace_to_outcome_snapshot(point: TracePoint) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=int(point.seed),
        step=int(point.step),
        observation=np.asarray(point.observation, dtype=np.float32).copy(),
        hidden=point.hidden.detach().clone(),
        env=copy.deepcopy(point.env),
        info=dict(point.info),
    )


def _outcome_to_trace(snapshot: OutcomeSnapshot, *, fault: Any) -> TracePoint:
    return TracePoint(
        seed=int(snapshot.seed),
        fault=fault,
        step=int(snapshot.step),
        observation=np.asarray(snapshot.observation, dtype=np.float32).copy(),
        hidden=snapshot.hidden.detach().clone(),
        env=copy.deepcopy(snapshot.env),
        info=dict(snapshot.info),
    )


def relocate_trace_point(
    point: TracePoint,
    *,
    body_longitudinal_offset: float,
    body_lateral_offset: float,
    half_width_inflation: float,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> tuple[TracePoint, dict[str, float]]:
    snapshot = _trace_to_outcome_snapshot(point)
    source_x, source_y, source_half_width = obstacle_body_geometry(snapshot)
    geometry = bounded_relocation_geometry(
        source_body_x=source_x,
        source_body_y=source_y,
        source_half_width=source_half_width,
        body_longitudinal_offset=body_longitudinal_offset,
        body_lateral_offset=body_lateral_offset,
        half_width_inflation=half_width_inflation,
        min_body_x=min_body_x,
        min_half_width=min_half_width,
    )
    relocated = relocate_outcome_snapshot(
        snapshot,
        body_longitudinal=geometry["relocated_body_x"],
        body_lateral=geometry["relocated_body_y"],
        half_width=geometry["relocated_half_width"],
    )
    return _outcome_to_trace(relocated, fault=point.fault), {
        "source_body_x": float(source_x),
        "source_body_y": float(source_y),
        "source_half_width": float(source_half_width),
        **geometry,
    }


def geometry_preflight_from_trace_candidates(
    candidates: pd.DataFrame,
    *,
    trace_for: Callable[[int, str, int], list[TracePoint]],
    candidate_step_column: str = DEFAULT_CANDIDATE_STEP_COLUMN,
    min_source_body_x: float = DEFAULT_MIN_SOURCE_BODY_X,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if candidate_step_column not in candidates.columns:
        raise ValueError(f"candidate step column not found: {candidate_step_column}")
    preflight_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for preflight_index, row in candidates.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        reveal_step = int(row["reveal_step"])
        candidate_step = candidate_step_for_row(row, candidate_step_column)
        preferred_fault = str(row["preferred_fault"])
        try:
            preferred_trace = trace_for(seed, preferred_fault, candidate_step)
            snapshot = _trace_to_outcome_snapshot(preferred_trace[-1])
            source_x, source_y, source_half_width = obstacle_body_geometry(snapshot)
            preflight = classify_relocation_geometry(
                source_body_x=source_x,
                source_body_y=source_y,
                source_half_width=source_half_width,
                body_longitudinal_offset=float(row["body_longitudinal_offset"]),
                body_lateral_offset=float(row["body_lateral_offset"]),
                half_width_inflation=float(row["half_width_inflation"]),
                min_source_body_x=min_source_body_x,
                min_body_x=min_body_x,
                min_half_width=min_half_width,
            )
        except Exception as exc:  # pragma: no cover - surfaced in artifacts.
            rejected_rows.append(
                {
                    "preflight_index": int(preflight_index),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "candidate_step": int(candidate_step),
                    "candidate_step_column": str(candidate_step_column),
                    "preferred_fault": preferred_fault,
                    "variant": str(row.get("variant", "")),
                    "geometry_rejection_reason": "trace_or_geometry_failed",
                    "error": str(exc),
                }
            )
            continue
        output = dict(row)
        output["preflight_index"] = int(preflight_index)
        output["reveal_step"] = reveal_step
        output["candidate_step"] = int(candidate_step)
        output["candidate_step_column"] = str(candidate_step_column)
        output.update(preflight)
        preflight_rows.append(output)
    return pd.DataFrame(preflight_rows), rejected_rows


def summarize_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    output: list[dict[str, Any]] = []
    for value, group in frame.groupby(key, observed=True):
        output.append(
            {
                key: str(value),
                "rows": int(len(group)),
                "history_positive_rows": int(group["history_positive"].astype(bool).sum())
                if "history_positive" in group.columns
                else 0,
                "control_positive_rows": int(group["control_positive"].astype(bool).sum())
                if "control_positive" in group.columns
                else 0,
                "outcome_critical_rows": int(group["outcome_critical"].astype(bool).sum())
                if "outcome_critical" in group.columns
                else 0,
                "unique_source_seeds": int(group["seed"].nunique()) if "seed" in group.columns else 0,
                "unique_capability_pairs": int(group["capability_pair"].nunique())
                if "capability_pair" in group.columns
                else 0,
                "unique_reveal_buckets": int(group["preferred_reveal_bucket"].nunique())
                if "preferred_reveal_bucket" in group.columns
                else 0,
            }
        )
    return output


def build_replay_summary(
    *,
    run_dir: Path,
    candidate_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    actor_parameters_changed: bool,
    min_margin_gap: float,
    min_sequence_action_l2: float,
) -> dict[str, Any]:
    history_positive = [row for row in replay_rows if bool(row.get("history_positive", False))]
    control_positive = [row for row in replay_rows if bool(row.get("control_positive", False))]
    normal_failed = [
        row
        for row in replay_rows
        if (not bool(row.get("normal_success", False))) or _finite(row.get("normal_margin")) < 0.0
    ]
    result_class = "bounded_relocation_replay_positive" if history_positive else "bounded_relocation_replay_no_history_positive"
    return {
        "run_type": "bounded_relocation_replay_probe",
        "selected_candidate_rows": int(len(candidate_rows)),
        "actual_replay_rows": int(len(replay_rows)),
        "history_positive_rows": int(len(history_positive)),
        "control_positive_rows": int(len(control_positive)),
        "normal_failed_rows": int(len(normal_failed)),
        "rejected_rows": int(len(rejected_rows)),
        "min_margin_gap": float(min_margin_gap),
        "min_sequence_action_l2": float(min_sequence_action_l2),
        "selected_candidate_diversity": source_diversity(candidate_rows),
        "actual_replay_diversity": source_diversity(replay_rows),
        "history_positive_diversity": source_diversity(history_positive),
        "control_positive_diversity": source_diversity(control_positive),
        "variant_summary": summarize_rows(replay_rows, "variant"),
        "relocation_summary": summarize_rows(replay_rows, "relocation_key"),
        "result_class": result_class,
        "replay_started": True,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_parameters_changed": bool(actor_parameters_changed),
        "actor_input_contract_changed": False,
        "selected_candidate_rows_csv": run_dir / "selected_candidate_rows.csv",
        "actual_replay_rows_csv": run_dir / "actual_replay_rows.csv",
        "history_positive_rows_csv": run_dir / "history_positive_rows.csv",
        "control_positive_rows_csv": run_dir / "control_positive_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "source_diversity_summary_csv": run_dir / "source_diversity_summary.csv",
        "relocation_summary_csv": run_dir / "relocation_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.to_dict("records") if not frame.empty else []


def _history_candidate_pool(frame: pd.DataFrame, *, min_sequence_action_l2: float) -> pd.DataFrame:
    candidate_pool = prepare_candidate_frame(frame)
    return candidate_pool[
        candidate_pool["history_variant"]
        & (candidate_pool["sequence_action_l2_mean"] >= float(min_sequence_action_l2))
    ].copy()


def run_geometry_preflight_only_probe(
    *,
    checkpoint_path: Path,
    config_path: Path,
    candidate_rows_path: Path,
    max_candidate_rows: int,
    per_seed_cap: int,
    per_capability_pair_cap: int,
    per_reveal_bucket_cap: int,
    per_variant_cap: int,
    history_length: int,
    min_sequence_action_l2: float,
    min_source_body_x: float,
    candidate_step_column: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    frame = pd.read_csv(candidate_rows_path)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    trace_cache: dict[tuple[int, str, int, int], list[TracePoint]] = {}

    def trace_for(seed: int, fault_name: str, step: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault_by_name[str(fault_name)],
                seed=int(seed),
                target_step=int(step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    candidate_pool = _history_candidate_pool(frame, min_sequence_action_l2=min_sequence_action_l2)
    preflight, rejected_rows = geometry_preflight_from_trace_candidates(
        candidate_pool,
        trace_for=trace_for,
        candidate_step_column=candidate_step_column,
        min_source_body_x=min_source_body_x,
    )
    selected = select_geometry_aware_replay_candidates(
        preflight,
        max_candidate_rows=max_candidate_rows,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_reveal_bucket_cap=per_reveal_bucket_cap,
        per_variant_cap=per_variant_cap,
        min_sequence_action_l2=min_sequence_action_l2,
    )
    summary = write_geometry_preflight_outputs(
        run_dir=run_dir,
        preflight=preflight,
        selected=selected,
        rejected_rows=rejected_rows,
    )
    summary["checkpoint_path"] = str(checkpoint_path)
    summary["config_path"] = str(config_path)
    summary["candidate_rows_path"] = str(candidate_rows_path)
    summary["candidate_step_column"] = str(candidate_step_column)
    summary["actor_parameters_changed"] = False
    write_json(run_dir / "summary.json", summary)
    return summary


def run_bounded_relocation_replay_probe(
    *,
    checkpoint_path: Path,
    config_path: Path,
    candidate_rows_path: Path,
    max_candidate_rows: int,
    per_capability_pair_cap: int,
    history_length: int,
    recent_window_length: int,
    max_continuation_steps: int,
    min_margin_gap: float,
    min_sequence_action_l2: float,
    geometry_aware_selector: bool,
    min_source_body_x: float,
    candidate_step_column: str,
    per_seed_cap: int,
    per_reveal_bucket_cap: int,
    per_variant_cap: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(candidate_rows_path)
    selected = pd.DataFrame()
    preflight_frame = pd.DataFrame()
    geometry_rejected_rows: list[dict[str, Any]] = []
    if not geometry_aware_selector:
        selected = select_replay_candidates(
            frame,
            max_candidate_rows=max_candidate_rows,
            per_capability_pair_cap=per_capability_pair_cap,
            min_sequence_action_l2=min_sequence_action_l2,
        )
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    trace_cache: dict[tuple[int, str, int, int], list[TracePoint]] = {}

    def trace_for(seed: int, fault_name: str, step: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault_by_name[str(fault_name)],
                seed=int(seed),
                target_step=int(step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    if geometry_aware_selector:
        candidate_pool = _history_candidate_pool(frame, min_sequence_action_l2=min_sequence_action_l2)
        preflight_frame, geometry_rejected_rows = geometry_preflight_from_trace_candidates(
            candidate_pool,
            trace_for=trace_for,
            candidate_step_column=candidate_step_column,
            min_source_body_x=min_source_body_x,
        )
        selected = select_geometry_aware_replay_candidates(
            preflight_frame,
            max_candidate_rows=max_candidate_rows,
            per_seed_cap=per_seed_cap,
            per_capability_pair_cap=per_capability_pair_cap,
            per_reveal_bucket_cap=per_reveal_bucket_cap,
            per_variant_cap=per_variant_cap,
            min_sequence_action_l2=min_sequence_action_l2,
        )

    replay_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for selected_index, row in selected.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        reveal_step = int(row["reveal_step"])
        candidate_step = candidate_step_for_row(row, candidate_step_column)
        preferred_fault = str(row["preferred_fault"])
        wrong_fault = str(row["wrong_fault"])
        requested_variant = str(row["variant"])
        variants = tuple(dict.fromkeys((requested_variant, "reset_hidden", "zero_current_response")))
        try:
            preferred_trace = trace_for(seed, preferred_fault, candidate_step)
            wrong_trace = trace_for(seed, wrong_fault, candidate_step)
            relocated_point, relocation = relocate_trace_point(
                preferred_trace[-1],
                body_longitudinal_offset=float(row["body_longitudinal_offset"]),
                body_lateral_offset=float(row["body_lateral_offset"]),
                half_width_inflation=float(row["half_width_inflation"]),
            )
            variant_hiddens = build_warmup_variant_hiddens(
                model=model,
                preferred_trace=preferred_trace,
                wrong_trace=wrong_trace,
                recent_window_length=recent_window_length,
                device=resolved_device,
            )
        except Exception as exc:  # pragma: no cover - surfaced in artifacts.
            rejected_rows.append(
                {
                    "selected_index": int(selected_index),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "candidate_step": int(candidate_step),
                    "candidate_step_column": str(candidate_step_column),
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "variant": requested_variant,
                    "rejection_reason": "trace_or_relocation_failed",
                    "error": str(exc),
                }
            )
            continue

        normal, normal_actions = replay_probe_variant(
            model=model,
            snapshot=relocated_point,
            variant="normal",
            initial_hidden=relocated_point.hidden,
            max_continuation_steps=max_continuation_steps,
            normal_first_action=None,
            normal_actions=None,
            response_dim=response_dim,
            device=resolved_device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        normal_margin = _finite(normal.get("min_clearance_margin"))
        normal_success = bool(normal.get("success", False))
        relocation_key = (
            f"x={relocation['relocated_body_x']:.3f}|"
            f"y={relocation['relocated_body_y']:.3f}|"
            f"w={relocation['relocated_half_width']:.3f}"
        )
        for variant in variants:
            hidden = variant_hiddens.get(variant, relocated_point.hidden).detach().clone()
            result, _ = replay_probe_variant(
                model=model,
                snapshot=relocated_point,
                variant=variant,
                initial_hidden=hidden,
                max_continuation_steps=max_continuation_steps,
                normal_first_action=normal_first_action,
                normal_actions=normal_actions,
                response_dim=response_dim,
                device=resolved_device,
            )
            variant_margin = _finite(result.get("min_clearance_margin"))
            classification = classify_actual_replay_result(
                variant=variant,
                normal_success=normal_success,
                variant_success=bool(result.get("success", False)),
                normal_margin=normal_margin,
                variant_margin=variant_margin,
                sequence_action_l2_mean=_finite(result.get("action_trajectory_distance_mean"), 0.0),
                min_sequence_action_l2=min_sequence_action_l2,
                min_margin_gap=min_margin_gap,
            )
            replay_rows.append(
                {
                    "selected_index": int(selected_index),
                    "source_index": int(row.get("source_index", selected_index)),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "candidate_step": int(candidate_step),
                    "candidate_step_column": str(candidate_step_column),
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "capability_pair": str(row.get("capability_pair", "")),
                    "preferred_reveal_bucket": str(row.get("preferred_reveal_bucket", "")),
                    "variant": variant,
                    "normal_success": normal_success,
                    "variant_success": bool(result.get("success", False)),
                    "normal_margin": normal_margin,
                    "variant_margin": variant_margin,
                    "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                    "variant_terminal_reason": str(result.get("terminal_reason", "")),
                    "first_action_l2": _finite(result.get("first_action_distance"), 0.0),
                    "sequence_action_l2_mean": _finite(result.get("action_trajectory_distance_mean"), 0.0),
                    "sequence_action_l2_max": _finite(result.get("action_trajectory_distance_max"), 0.0),
                    "relocation_key": relocation_key,
                    **relocation,
                    **classification,
                }
            )

    candidate_records = _records(selected)
    preflight_records = _records(preflight_frame)
    history_positive = [row for row in replay_rows if bool(row.get("history_positive", False))]
    control_positive = [row for row in replay_rows if bool(row.get("control_positive", False))]
    variant_summary = summarize_rows(replay_rows, "variant")
    relocation_summary = summarize_rows(replay_rows, "relocation_key")
    source_diversity_summary = [
        {"row_set": "geometry_preflight_rows", **source_diversity(preflight_records)},
        {"row_set": "selected_candidate_rows", **source_diversity(candidate_records)},
        {"row_set": "actual_replay_rows", **source_diversity(replay_rows)},
        {"row_set": "history_positive_rows", **source_diversity(history_positive)},
        {"row_set": "control_positive_rows", **source_diversity(control_positive)},
    ]
    checksum_after = model_parameter_checksum(model)
    summary = build_replay_summary(
        run_dir=run_dir,
        candidate_rows=candidate_records,
        replay_rows=replay_rows,
        rejected_rows=rejected_rows,
        actor_parameters_changed=str(checksum_after) != str(checksum_before),
        min_margin_gap=min_margin_gap,
        min_sequence_action_l2=min_sequence_action_l2,
    )
    summary["geometry_aware_selector"] = bool(geometry_aware_selector)
    summary["candidate_step_column"] = str(candidate_step_column)
    if geometry_aware_selector:
        geometry_summary = build_geometry_preflight_summary(
            preflight_rows=preflight_records,
            selected_rows=candidate_records,
            rejected_rows=geometry_rejected_rows,
        )
        summary["geometry_preflight"] = geometry_summary
        summary["geometry_preflight_rows_csv"] = run_dir / "geometry_preflight_rows.csv"
        summary["geometry_rejected_rows_csv"] = run_dir / "geometry_rejected_rows.csv"
        summary["geometry_summary_json"] = run_dir / "geometry_summary.json"
    write_csv_rows(run_dir / "selected_candidate_rows.csv", candidate_records)
    write_csv_rows(run_dir / "actual_replay_rows.csv", replay_rows)
    write_csv_rows(run_dir / "history_positive_rows.csv", history_positive)
    write_csv_rows(run_dir / "control_positive_rows.csv", control_positive)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "source_diversity_summary.csv", source_diversity_summary)
    write_csv_rows(run_dir / "relocation_summary.csv", relocation_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    if geometry_aware_selector:
        write_csv_rows(run_dir / "geometry_preflight_rows.csv", preflight_records)
        write_csv_rows(run_dir / "geometry_rejected_rows.csv", geometry_rejected_rows)
        write_json(run_dir / "geometry_summary.json", summary["geometry_preflight"])
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--candidate-rows", type=Path, required=True)
    parser.add_argument("--max-candidate-rows", type=int, default=128)
    parser.add_argument("--per-capability-pair-cap", type=int, default=12)
    parser.add_argument("--history-length", type=int, default=56)
    parser.add_argument("--recent-window-length", type=int, default=4)
    parser.add_argument("--max-continuation-steps", type=int, default=48)
    parser.add_argument("--min-margin-gap", type=float, default=DEFAULT_MIN_MARGIN_GAP)
    parser.add_argument("--min-sequence-action-l2", type=float, default=DEFAULT_MIN_SEQUENCE_ACTION_L2)
    parser.add_argument("--geometry-aware-selector", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--min-source-body-x", type=float, default=DEFAULT_MIN_SOURCE_BODY_X)
    parser.add_argument("--candidate-step-column", default=DEFAULT_CANDIDATE_STEP_COLUMN)
    parser.add_argument("--per-seed-cap", type=int, default=DEFAULT_PER_SEED_CAP)
    parser.add_argument("--per-reveal-bucket-cap", type=int, default=DEFAULT_PER_REVEAL_BUCKET_CAP)
    parser.add_argument("--per-variant-cap", type=int, default=DEFAULT_PER_VARIANT_CAP)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="bounded_relocation_replay_probe")
    if args.preflight_only:
        summary = run_geometry_preflight_only_probe(
            checkpoint_path=args.checkpoint,
            config_path=args.config,
            candidate_rows_path=args.candidate_rows,
            max_candidate_rows=args.max_candidate_rows,
            per_seed_cap=args.per_seed_cap,
            per_capability_pair_cap=args.per_capability_pair_cap,
            per_reveal_bucket_cap=args.per_reveal_bucket_cap,
            per_variant_cap=args.per_variant_cap,
            history_length=args.history_length,
            min_sequence_action_l2=args.min_sequence_action_l2,
            min_source_body_x=args.min_source_body_x,
            candidate_step_column=args.candidate_step_column,
            device=args.device,
            run_dir=run_dir,
        )
        print(f"summary_json={run_dir / 'summary.json'}")
        print(f"geometry_pass_rows={summary['geometry_pass_rows']}")
        print(f"selected_candidate_rows={summary['selected_candidate_rows']}")
        print("replay_started=false")
        return
    summary = run_bounded_relocation_replay_probe(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        candidate_rows_path=args.candidate_rows,
        max_candidate_rows=args.max_candidate_rows,
        per_capability_pair_cap=args.per_capability_pair_cap,
        history_length=args.history_length,
        recent_window_length=args.recent_window_length,
        max_continuation_steps=args.max_continuation_steps,
        min_margin_gap=args.min_margin_gap,
        min_sequence_action_l2=args.min_sequence_action_l2,
        geometry_aware_selector=args.geometry_aware_selector,
        min_source_body_x=args.min_source_body_x,
        candidate_step_column=args.candidate_step_column,
        per_seed_cap=args.per_seed_cap,
        per_reveal_bucket_cap=args.per_reveal_bucket_cap,
        per_variant_cap=args.per_variant_cap,
        device=args.device,
        run_dir=run_dir,
    )
    print(f"summary_json={run_dir / 'summary.json'}")
    print(f"selected_candidate_rows={summary['selected_candidate_rows']}")
    print(f"actual_replay_rows={summary['actual_replay_rows']}")
    print(f"history_positive_rows={summary['history_positive_rows']}")
    print(f"result_class={summary['result_class']}")


if __name__ == "__main__":
    main()
