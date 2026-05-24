"""Mine projected sequence candidates for trust-primary near misses."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_conditioned_grounded_target_miner import _diversity, _empty_float_stat, load_boundary_source_rows
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import (
    SurfaceConfig,
    _finite_float,
    parse_surface_config,
    request_steps_for_target_rows,
    risk_score,
    variant_hidden_for_row,
)
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import _snapshot, collect_requested_outcome_snapshots
from autodrift.sequence_target_miner import (
    SequenceCandidate,
    _make_candidate,
    _value_counts,
    collect_base_action_sequence,
    parse_int_list,
    rollout_sequence_override,
    sequence_acceptance,
    sequence_scales,
    sequence_trust_metrics,
    source_metadata,
)
from autodrift.terminal_margin_recovery_anchor import parse_float_list
from autodrift.train_ppo import resolve_device


PROJECTED_FAMILIES = (
    "projected_constant_delta",
    "projected_decay_pulse",
    "projected_brake_release_then_steer",
    "projected_steer_then_brake",
    "projected_linear_ramp",
    "projected_half_sine_pulse",
    "projected_s_curve_pulse",
)


@dataclass(frozen=True)
class ProjectedSequenceCandidate:
    candidate: SequenceCandidate
    raw_family: str
    projection_scale: float
    raw_sequence_mean_l2: float
    raw_sequence_max_l2: float
    raw_max_delta_delta_l2: float


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if pd.isna(value):
        return False
    return bool(value)


def projected_sequence_scales(length: int, family: str) -> np.ndarray:
    if length <= 0:
        raise ValueError("sequence length must be positive")
    if not family.startswith("projected_"):
        raise ValueError(f"projected family must start with projected_: {family}")
    raw_family = family.removeprefix("projected_")
    if raw_family in {"constant_delta", "decay_pulse"}:
        return sequence_scales(length, raw_family)
    if raw_family in {"brake_release_then_steer", "steer_then_brake"}:
        return np.ones(int(length), dtype=np.float32)
    if raw_family == "linear_ramp":
        return np.linspace(0.25, 1.0, int(length), dtype=np.float32)
    if raw_family == "half_sine_pulse":
        scales = np.sin(np.linspace(0.0, np.pi, int(length), dtype=np.float64)).astype(np.float32)
        scales[np.abs(scales) < 1e-7] = 0.0
        return scales
    if raw_family == "s_curve_pulse":
        t = np.linspace(0.0, 1.0, int(length), dtype=np.float32)
        return (t * t * (3.0 - 2.0 * t)).astype(np.float32)
    raise ValueError(f"unknown projected sequence family: {family}")


def projection_scale_for_metrics(
    *,
    sequence_mean_l2: float,
    sequence_max_l2: float,
    max_delta_delta_l2: float,
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
) -> float:
    eps = 1e-12
    scale = min(
        1.0,
        float(per_step_action_l2) / max(float(sequence_max_l2), eps),
        float(sequence_max_l2_limit) / max(float(sequence_max_l2), eps),
        float(sequence_mean_l2_limit) / max(float(sequence_mean_l2), eps),
        float(max_delta_delta_l2_limit) / max(float(max_delta_delta_l2), eps),
    )
    return float(max(0.0, min(1.0, scale)))


def project_delta_sequence(
    *,
    base_action_sequence: np.ndarray,
    delta_sequence: np.ndarray,
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
) -> tuple[np.ndarray, float, tuple[float, float, float]]:
    base = np.asarray(base_action_sequence, dtype=np.float32)
    raw_delta = np.asarray(delta_sequence, dtype=np.float32)
    raw_actions = np.clip(base + raw_delta, -1.0, 1.0)
    raw_metrics = sequence_trust_metrics(action_sequence=raw_actions, base_action_sequence=base)
    scale = projection_scale_for_metrics(
        sequence_mean_l2=raw_metrics[0],
        sequence_max_l2=raw_metrics[1],
        max_delta_delta_l2=raw_metrics[2],
        per_step_action_l2=per_step_action_l2,
        sequence_mean_l2_limit=sequence_mean_l2_limit,
        sequence_max_l2_limit=sequence_max_l2_limit,
        max_delta_delta_l2_limit=max_delta_delta_l2_limit,
    )
    if scale < 1.0:
        scale *= 1.0 - 1e-6
    return (scale * raw_delta).astype(np.float32), scale, raw_metrics


def _raw_family(family: str) -> str:
    return family.removeprefix("projected_")


def _structured_delta_sequence(
    *,
    family: str,
    base: np.ndarray,
    steer_delta: float,
    throttle_delta: float,
    brake_delta: float,
) -> np.ndarray | None:
    raw_family = _raw_family(family)
    if raw_family in {"constant_delta", "decay_pulse", "linear_ramp", "half_sine_pulse", "s_curve_pulse"}:
        scales = projected_sequence_scales(base.shape[0], family)
        delta = np.asarray([steer_delta, throttle_delta, brake_delta], dtype=np.float32)
        return scales[:, None] * delta[None, :]
    if raw_family == "brake_release_then_steer":
        if abs(float(steer_delta)) < 1e-12 or float(brake_delta) >= 0.0:
            return None
        delta_sequence = np.zeros_like(base, dtype=np.float32)
        delta_sequence[: min(2, len(delta_sequence)), 2] = float(brake_delta)
        delta_sequence[1:, 0] = float(steer_delta)
        return delta_sequence
    if raw_family == "steer_then_brake":
        if abs(float(steer_delta)) < 1e-12 or abs(float(brake_delta)) < 1e-12:
            return None
        delta_sequence = np.zeros_like(base, dtype=np.float32)
        delta_sequence[: min(2, len(delta_sequence)), 0] = float(steer_delta)
        delta_sequence[1:, 2] = float(brake_delta)
        return delta_sequence
    raise ValueError(f"unknown projected sequence family: {family}")


def build_projected_sequence_candidates(
    base_action_sequence: np.ndarray,
    *,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    families: tuple[str, ...],
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
) -> list[ProjectedSequenceCandidate]:
    base = np.asarray(base_action_sequence, dtype=np.float32)
    if base.ndim != 2 or base.shape[1] != 3:
        raise ValueError(f"base action sequence must have shape (K, 3), got {base.shape}")
    output: list[ProjectedSequenceCandidate] = []
    candidate_id = 0
    for family in families:
        for steer_delta in steer_deltas:
            for brake_delta in brake_deltas:
                for throttle_delta in throttle_deltas:
                    raw_delta = _structured_delta_sequence(
                        family=family,
                        base=base,
                        steer_delta=float(steer_delta),
                        throttle_delta=float(throttle_delta),
                        brake_delta=float(brake_delta),
                    )
                    if raw_delta is None:
                        continue
                    projected_delta, scale, raw_metrics = project_delta_sequence(
                        base_action_sequence=base,
                        delta_sequence=raw_delta,
                        per_step_action_l2=per_step_action_l2,
                        sequence_mean_l2_limit=sequence_mean_l2_limit,
                        sequence_max_l2_limit=sequence_max_l2_limit,
                        max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                    )
                    candidate = _make_candidate(
                        candidate_id=candidate_id,
                        family=family,
                        base_action_sequence=base,
                        delta_sequence=projected_delta,
                        steer_delta=float(steer_delta),
                        throttle_delta=float(throttle_delta),
                        brake_delta=float(brake_delta),
                        per_step_action_l2=per_step_action_l2,
                        sequence_mean_l2_limit=sequence_mean_l2_limit,
                        sequence_max_l2_limit=sequence_max_l2_limit,
                        max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                    )
                    output.append(
                        ProjectedSequenceCandidate(
                            candidate=candidate,
                            raw_family=_raw_family(family),
                            projection_scale=scale,
                            raw_sequence_mean_l2=raw_metrics[0],
                            raw_sequence_max_l2=raw_metrics[1],
                            raw_max_delta_delta_l2=raw_metrics[2],
                        )
                    )
                    candidate_id += 1
    return output


def select_focused_source_rows(
    near_miss_sources: pd.DataFrame,
    source_rows: pd.DataFrame,
    *,
    max_accepted_candidates: int,
    include_collision_sources: bool = False,
) -> pd.DataFrame:
    required = {"source_index", "accepted_candidate_count", "best_primary_failure", "has_collision_near_miss"}
    missing = sorted(required.difference(near_miss_sources.columns))
    if missing:
        raise ValueError("near-miss sources missing columns: " + ", ".join(missing))
    mask = (
        (near_miss_sources["accepted_candidate_count"].astype(int) <= int(max_accepted_candidates))
        & near_miss_sources["best_primary_failure"].isin(["mean_l2_excess", "max_l2_excess"])
    )
    if not include_collision_sources:
        mask &= ~near_miss_sources["has_collision_near_miss"].map(_bool)
    selected_ids = set(near_miss_sources.loc[mask, "source_index"].astype(int).tolist())
    selected = source_rows[source_rows["source_index"].astype(int).isin(selected_ids)].copy()
    selected["trust_projected_focus"] = True
    return selected.sort_values("source_index").reset_index(drop=True)


def _near_source_lookup(near_miss_sources: pd.DataFrame) -> dict[int, dict[str, Any]]:
    return {
        int(row["source_index"]): dict(row)
        for _, row in near_miss_sources.reset_index(drop=True).iterrows()
    }


def _best_any(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidate_rows:
        return None
    return max(
        candidate_rows,
        key=lambda row: (
            _finite_float(row.get("margin_improvement"), float("-inf")),
            _finite_float(row.get("risk_improvement"), float("-inf")),
            -_finite_float(row.get("sequence_mean_l2"), float("inf")),
        ),
    )


def _best_accepted(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in candidate_rows if _bool(row.get("accepted", False))]
    if not accepted:
        return None
    return max(
        accepted,
        key=lambda row: (
            _finite_float(row.get("margin_improvement"), float("-inf")),
            _finite_float(row.get("risk_improvement"), float("-inf")),
            -_finite_float(row.get("sequence_mean_l2"), float("inf")),
        ),
    )


def source_recovery_summary(
    candidate_rows: list[dict[str, Any]],
    near_miss_sources: pd.DataFrame,
) -> list[dict[str, Any]]:
    near_lookup = _near_source_lookup(near_miss_sources)
    output: list[dict[str, Any]] = []
    frame = pd.DataFrame(candidate_rows)
    if frame.empty:
        return output
    for source_index, group in frame.groupby("source_index", observed=True):
        rows = group.to_dict(orient="records")
        best_any = _best_any(rows)
        best_accepted = _best_accepted(rows)
        near = near_lookup.get(int(source_index), {})
        accepted_before = int(near.get("accepted_candidate_count", 0) or 0)
        accepted_after = int(group["accepted"].map(_bool).sum())
        best_row = best_accepted or best_any or {}
        output.append(
            {
                "source_index": int(source_index),
                "source_tier": str(near.get("source_tier", best_row.get("source_tier", ""))),
                "surface": str(near.get("surface", best_row.get("surface", ""))),
                "target": str(near.get("target", best_row.get("target", ""))),
                "variant": str(near.get("variant", best_row.get("variant", ""))),
                "accepted_before_m624": accepted_before,
                "accepted_after_projection": accepted_after,
                "projected_candidate_count": int(len(group)),
                "best_projected_margin_improvement": _finite_float(best_row.get("margin_improvement")),
                "best_projected_risk_improvement": _finite_float(best_row.get("risk_improvement")),
                "best_projected_family": str(best_row.get("family", "")),
                "best_raw_family": str(best_row.get("raw_family", "")),
                "best_sequence_length": int(best_row.get("sequence_length", -1)),
                "best_projection_scale": _finite_float(best_row.get("projection_scale")),
                "best_rejection_reason": str(best_row.get("rejection_reason", "")),
                "trust_primary": str(near.get("best_primary_failure", "")) in {"mean_l2_excess", "max_l2_excess"},
                "collision_primary": str(near.get("best_primary_failure", "")) == "candidate_collision",
                "recovered_by_projection": bool(accepted_before == 0 and accepted_after > 0),
                "improved_by_projection": bool(accepted_after > accepted_before),
            }
        )
    return sorted(output, key=lambda row: (not row["recovered_by_projection"], -row["best_projected_margin_improvement"]))


def mine_projected_sequences_for_surface(
    *,
    model: Any,
    env_config_path: Path,
    rows: pd.DataFrame,
    near_miss_sources: pd.DataFrame,
    sequence_lengths: tuple[int, ...],
    families: tuple[str, ...],
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    delay_steps: int,
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_continuation_steps: int,
    device: Any,
) -> list[dict[str, Any]]:
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=request_steps_for_target_rows(rows, delay_steps=delay_steps),
        device=device,
    )
    near_lookup = _near_source_lookup(near_miss_sources)
    candidate_rows: list[dict[str, Any]] = []
    for _, row in rows.reset_index(drop=True).iterrows():
        source_index = int(row["source_index"])
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        variant_hidden = variant_hidden_for_row(row=row, snapshots=snapshots, delay_steps=delay_steps).detach().clone()
        variant_base_action, _ = deterministic_action_from_hidden(model, left.observation, variant_hidden, device)
        baseline_sequence = collect_base_action_sequence(
            model=model,
            snapshot=left,
            sequence_length=max(sequence_lengths),
            device=device,
        )
        baseline = rollout_sequence_override(
            model=model,
            snapshot=left,
            action_sequence=baseline_sequence[: max(sequence_lengths)],
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        baseline_risk = risk_score(baseline)
        candidate_id_offset = 0
        near = near_lookup.get(source_index, {})
        for sequence_length in sequence_lengths:
            base_sequence = baseline_sequence[: int(sequence_length)]
            projected_candidates = build_projected_sequence_candidates(
                base_sequence,
                steer_deltas=steer_deltas,
                throttle_deltas=throttle_deltas,
                brake_deltas=brake_deltas,
                families=families,
                per_step_action_l2=per_step_action_l2,
                sequence_mean_l2_limit=sequence_mean_l2_limit,
                sequence_max_l2_limit=sequence_max_l2_limit,
                max_delta_delta_l2_limit=max_delta_delta_l2_limit,
            )
            for projected in projected_candidates:
                candidate = projected.candidate
                candidate_id = int(candidate_id_offset + candidate.candidate_id)
                result = rollout_sequence_override(
                    model=model,
                    snapshot=left,
                    action_sequence=candidate.action_sequence,
                    max_continuation_steps=max_continuation_steps,
                    device=device,
                )
                candidate_risk = risk_score(result)
                baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
                candidate_margin = _finite_float(result.get("min_clearance_margin"))
                margin_improvement = (
                    candidate_margin - baseline_margin
                    if np.isfinite(candidate_margin) and np.isfinite(baseline_margin)
                    else float("nan")
                )
                accepted, rejection_reason = sequence_acceptance(
                    candidate=result,
                    baseline=baseline,
                    trust_region_ok=candidate.trust_region_ok,
                    min_margin_improvement=min_margin_improvement,
                    min_risk_improvement=min_risk_improvement,
                )
                candidate_rows.append(
                    {
                        "source_index": source_index,
                        "coupling_row_index": int(row["coupling_row_index"]),
                        "candidate_id": candidate_id,
                        "family": candidate.family,
                        "raw_family": projected.raw_family,
                        "sequence_length": int(candidate.sequence_length),
                        "surface": str(row["surface"]),
                        "target": str(row["target"]),
                        "variant": str(row["variant"]),
                        "left_seed": int(row["left_seed"]),
                        "right_seed": int(row["right_seed"]),
                        "left_step": int(row["left_step"]),
                        "right_step": int(row["right_step"]),
                        "baseline_success": bool(baseline.get("success", False)),
                        "baseline_collision": bool(baseline.get("collision", False)),
                        "baseline_terminal_reason": str(baseline.get("terminal_reason", "")),
                        "baseline_margin": baseline_margin,
                        "baseline_risk_score": baseline_risk,
                        "candidate_success": bool(result.get("success", False)),
                        "candidate_collision": bool(result.get("collision", False)),
                        "candidate_off_road": bool(result.get("off_road", False)),
                        "candidate_spin_out": bool(result.get("spin_out", False)),
                        "candidate_terminal_reason": str(result.get("terminal_reason", "")),
                        "candidate_margin": candidate_margin,
                        "candidate_risk_score": candidate_risk,
                        "margin_improvement": margin_improvement,
                        "risk_improvement": baseline_risk - candidate_risk,
                        "steer_delta": float(candidate.steer_delta),
                        "throttle_delta": float(candidate.throttle_delta),
                        "brake_delta": float(candidate.brake_delta),
                        "projection_scale": float(projected.projection_scale),
                        "raw_sequence_mean_l2": float(projected.raw_sequence_mean_l2),
                        "raw_sequence_max_l2": float(projected.raw_sequence_max_l2),
                        "raw_max_delta_delta_l2": float(projected.raw_max_delta_delta_l2),
                        "sequence_mean_l2": float(candidate.sequence_mean_l2),
                        "sequence_max_l2": float(candidate.sequence_max_l2),
                        "max_delta_delta_l2": float(candidate.max_delta_delta_l2),
                        "accepted": bool(accepted),
                        "rejection_reason": rejection_reason,
                        "near_miss_best_primary_failure": str(near.get("best_primary_failure", "")),
                        "near_miss_accepted_candidate_count": int(near.get("accepted_candidate_count", 0) or 0),
                        "variant_base_steer": float(np.asarray(variant_base_action, dtype=np.float32)[0]),
                        "variant_base_throttle": float(np.asarray(variant_base_action, dtype=np.float32)[1]),
                        "variant_base_brake": float(np.asarray(variant_base_action, dtype=np.float32)[2]),
                        **source_metadata(row),
                    }
                )
            candidate_id_offset += len(projected_candidates)
    return candidate_rows


def run_trust_projected_sequence_shape(
    *,
    checkpoint_path: Path,
    near_miss_sources_csv: Path,
    source_table_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    sequence_lengths: tuple[int, ...],
    families: tuple[str, ...],
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    delay_steps: int,
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_continuation_steps: int,
    max_accepted_candidates: int,
    include_collision_sources: bool,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    near_miss_sources = pd.read_csv(near_miss_sources_csv)
    source_rows = load_boundary_source_rows(source_table_csv)
    focused_rows = select_focused_source_rows(
        near_miss_sources,
        source_rows,
        max_accepted_candidates=max_accepted_candidates,
        include_collision_sources=include_collision_sources,
    )
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(focused_rows["surface"].astype(str)).difference(surface_config_by_name)) if not focused_rows.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    candidate_rows: list[dict[str, Any]] = []
    for surface, surface_rows in focused_rows.groupby("surface", observed=True):
        candidate_rows.extend(
            mine_projected_sequences_for_surface(
                model=model,
                env_config_path=surface_config_by_name[str(surface)],
                rows=surface_rows.reset_index(drop=True),
                near_miss_sources=near_miss_sources,
                sequence_lengths=sequence_lengths,
                families=families,
                steer_deltas=steer_deltas,
                throttle_deltas=throttle_deltas,
                brake_deltas=brake_deltas,
                delay_steps=delay_steps,
                per_step_action_l2=per_step_action_l2,
                sequence_mean_l2_limit=sequence_mean_l2_limit,
                sequence_max_l2_limit=sequence_max_l2_limit,
                max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                min_margin_improvement=min_margin_improvement,
                min_risk_improvement=min_risk_improvement,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
        )

    accepted_rows = [row for row in candidate_rows if _bool(row.get("accepted", False))]
    source_summary = source_recovery_summary(candidate_rows, near_miss_sources)
    candidate_frame = pd.DataFrame(candidate_rows)
    accepted_frame = pd.DataFrame(accepted_rows)
    source_summary_frame = pd.DataFrame(source_summary)
    write_csv_rows(run_dir / "selected_projected_source_rows.csv", focused_rows.to_dict(orient="records"))
    write_csv_rows(run_dir / "projected_sequence_candidates.csv", candidate_rows)
    write_csv_rows(run_dir / "accepted_projected_sequences.csv", accepted_rows)
    write_csv_rows(run_dir / "source_recovery_summary.csv", source_summary)
    unaccepted_sources = [
        row for row in source_summary if int(row.get("accepted_after_projection", 0)) == 0
    ]
    write_csv_rows(run_dir / "unaccepted_projected_rows.csv", unaccepted_sources)

    trust_ok = True
    if not candidate_frame.empty:
        trust_ok = bool(
            (candidate_frame["sequence_mean_l2"] <= float(sequence_mean_l2_limit) + 1e-8).all()
            and (candidate_frame["sequence_max_l2"] <= float(sequence_max_l2_limit) + 1e-8).all()
            and (candidate_frame["max_delta_delta_l2"] <= float(max_delta_delta_l2_limit) + 1e-8).all()
        )
    recovered_sources = (
        source_summary_frame[source_summary_frame["recovered_by_projection"].map(_bool)]
        if not source_summary_frame.empty
        else pd.DataFrame()
    )
    summary = {
        "run_type": "trust_projected_sequence_shape",
        "checkpoint": checkpoint_path,
        "near_miss_sources_csv": near_miss_sources_csv,
        "source_table_csv": source_table_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "source_row_diversity": _diversity(focused_rows),
        "accepted_projected_diversity": _diversity(accepted_frame),
        "sequence_lengths": sequence_lengths,
        "families": families,
        "focused_source_rows": int(len(focused_rows)),
        "focused_source_ids": focused_rows["source_index"].astype(int).tolist() if not focused_rows.empty else [],
        "candidate_rollouts": int(len(candidate_rows)),
        "accepted_projected_candidates": int(len(accepted_rows)),
        "sources_recovered_by_projection": int(len(recovered_sources)),
        "recovered_source_ids": recovered_sources["source_index"].astype(int).tolist() if not recovered_sources.empty else [],
        "trust_limits_preserved": trust_ok,
        "candidate_margin_improvement_max": _empty_float_stat(candidate_frame, "margin_improvement", "max"),
        "candidate_margin_improvement_mean": _empty_float_stat(candidate_frame, "margin_improvement", "mean"),
        "accepted_margin_improvement_mean": _empty_float_stat(accepted_frame, "margin_improvement", "mean"),
        "accepted_margin_improvement_min": _empty_float_stat(accepted_frame, "margin_improvement", "min"),
        "accepted_margin_improvement_max": _empty_float_stat(accepted_frame, "margin_improvement", "max"),
        "candidate_rejection_counts": (
            candidate_frame[~candidate_frame["accepted"].map(_bool)]["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "candidate_acceptance_reason_counts": (
            candidate_frame[candidate_frame["accepted"].map(_bool)]["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "accepted_counts_by_family": _value_counts(accepted_frame, "family"),
        "accepted_counts_by_source": _value_counts(accepted_frame, "source_index"),
        "diagnostic_only": True,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "target_acceptance_thresholds_changed": False,
        "trust_regions_changed": False,
        "projected_sequence_candidates_csv": run_dir / "projected_sequence_candidates.csv",
        "accepted_projected_sequences_csv": run_dir / "accepted_projected_sequences.csv",
        "source_recovery_summary_csv": run_dir / "source_recovery_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine no-training projected sequence candidates.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--near-miss-sources", type=Path, required=True)
    parser.add_argument("--near-miss-candidates", type=Path, required=False)
    parser.add_argument("--source-table", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(3, 5, 7))
    parser.add_argument("--family", type=str, action="append", default=None)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.08, -0.06, -0.04, 0.0, 0.04, 0.06, 0.08))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.06, 0.0, 0.03))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.08, -0.04, 0.0, 0.04, 0.08))
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--per-step-action-l2", type=float, default=0.10)
    parser.add_argument("--sequence-mean-l2-limit", type=float, default=0.08)
    parser.add_argument("--sequence-max-l2-limit", type=float, default=0.10)
    parser.add_argument("--max-delta-delta-l2-limit", type=float, default=0.08)
    parser.add_argument("--min-margin-improvement", type=float, default=0.02)
    parser.add_argument("--min-risk-improvement", type=float, default=0.05)
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--max-accepted-candidates", type=int, default=3)
    parser.add_argument("--include-collision-sources", action="store_true")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    families = tuple(args.family or PROJECTED_FAMILIES)
    run_dir = args.run_dir or make_run_dir(prefix="trust_projected_sequence_shape")
    summary = run_trust_projected_sequence_shape(
        checkpoint_path=args.checkpoint_policy.path,
        near_miss_sources_csv=args.near_miss_sources,
        source_table_csv=args.source_table,
        surface_configs=tuple(args.surface_config),
        sequence_lengths=tuple(args.sequence_lengths),
        families=families,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        delay_steps=args.delay_steps,
        per_step_action_l2=args.per_step_action_l2,
        sequence_mean_l2_limit=args.sequence_mean_l2_limit,
        sequence_max_l2_limit=args.sequence_max_l2_limit,
        max_delta_delta_l2_limit=args.max_delta_delta_l2_limit,
        min_margin_improvement=args.min_margin_improvement,
        min_risk_improvement=args.min_risk_improvement,
        max_continuation_steps=args.max_continuation_steps,
        max_accepted_candidates=args.max_accepted_candidates,
        include_collision_sources=args.include_collision_sources,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
