"""No-training boundary miner for temporal action-sensitive rows."""

from __future__ import annotations

import argparse
import copy
import csv
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    FaultSpec,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import DecisionSnapshot, clone_hidden
from autodrift.outcome_sensitive_corpus import relocate_obstacle_snapshot
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_response_mismatch import (
    TemporalSnapshot,
    _group_summary,
    _row_for_variant,
    build_temporal_variant_hiddens,
    collect_temporal_snapshots,
    replay_temporal_variant,
)
from autodrift.train_ppo import ActorCritic, resolve_device


TEMPORAL_BOUNDARY_VARIANTS = (
    "normal",
    "reset_hidden",
    "mismatch_zero_command_history",
    "delayed_hidden_20",
    "pre_fault_stale_hidden",
)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _parse_float_list(raw: str) -> tuple[float, ...]:
    values = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated float")
    return tuple(float(value) for value in values)


def _dominance_fraction(values: list[str]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return float(max(counts.values()) / max(len(values), 1))


def _source_row_identity(raw: dict[str, Any]) -> tuple[str, ...]:
    for key in ("pair_id", "proposal_id", "selected_index"):
        value = str(raw.get(key, "")).strip()
        if value:
            return (
                key,
                value,
                str(raw.get("variant", "")),
                str(raw.get("seed", "")),
                str(raw.get("step", "")),
            )
    return (
        "fallback",
        str(raw.get("seed", "")),
        str(raw.get("step", "")),
        str(raw.get("variant", "")),
        str(raw.get("preferred_fault", "")),
        str(raw.get("wrong_fault", "")),
        str(raw.get("fault_family_pair", "")),
    )


def _bucket_float(value: Any, *, width: float, missing: str = "missing") -> str:
    number = _finite_float(value)
    if not np.isfinite(number):
        return missing
    return str(int(np.floor(float(number) / float(width))))


def _source_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    seeds = [str(row.get("seed", "")) for row in rows]
    preferred_families = [str(row.get("preferred_fault_family", "")) for row in rows]
    fault_pairs = [
        str(row.get("fault_family_pair", ""))
        or f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}"
        for row in rows
    ]
    sentinel_rows = [row for row in rows if str(row.get("source_role", "")) == "sentinel"]
    return {
        "source_unique_seeds": int(len(set(seeds))),
        "source_unique_preferred_fault_families": int(len(set(preferred_families))),
        "source_unique_fault_family_pairs": int(len(set(fault_pairs))),
        "source_max_seed_dominance": float(_dominance_fraction(seeds)),
        "source_max_preferred_family_dominance": float(_dominance_fraction(preferred_families)),
        "source_sentinel_fraction": float(len(sentinel_rows) / max(len(rows), 1)),
    }


def classify_boundary_miner_result(
    *,
    candidate_variant_count: int,
    accepted_rows: int,
    temporal_action_critical_rows: int,
    temporal_outcome_critical_rows: int,
    unique_fault_families: int,
    unique_seeds: int,
    max_fault_family_dominance: float,
    normal_history_retention_pass: bool,
    sentinel_false_positive_rate: float,
    normal_failed_rejected: int,
    min_accepted_rows: int = 30,
    min_temporal_outcome_rows: int = 20,
    min_unique_fault_families: int = 4,
    min_unique_seeds: int = 10,
    max_family_dominance: float = 0.40,
    max_sentinel_false_positive_rate: float = 0.05,
) -> str:
    if int(candidate_variant_count) <= 0:
        return "boundary_miner_empty"
    if float(sentinel_false_positive_rate) > float(max_sentinel_false_positive_rate):
        return "boundary_miner_artifact"
    if int(normal_failed_rejected) > int(candidate_variant_count) // 2:
        return "normal_failed_too_severe"
    if (
        bool(normal_history_retention_pass)
        and int(accepted_rows) >= int(min_accepted_rows)
        and int(temporal_outcome_critical_rows) >= int(min_temporal_outcome_rows)
        and int(unique_fault_families) >= int(min_unique_fault_families)
        and int(unique_seeds) >= int(min_unique_seeds)
        and float(max_fault_family_dominance) <= float(max_family_dominance)
    ):
        return "temporal_outcome_boundary_positive"
    if int(temporal_action_critical_rows) > 0:
        return "temporal_action_only_boundary_sparse"
    return "boundary_miner_empty"


def _source_role(row: dict[str, Any], min_action_l2_gap: float) -> str | None:
    variant = str(row.get("variant", ""))
    normal_success = _parse_bool(row.get("normal_success", False))
    normal_margin = _finite_float(row.get("normal_margin"))
    first_action_distance = _finite_float(row.get("first_action_distance_from_normal"))
    normal_ok = bool(normal_success or (np.isfinite(normal_margin) and normal_margin >= 0.0))
    if not normal_ok:
        return None
    if (
        variant == "mismatch_zero_command_history"
        and _parse_bool(row.get("temporal_action_critical", False))
        and np.isfinite(first_action_distance)
        and first_action_distance >= float(min_action_l2_gap)
    ):
        return "primary"
    if (
        variant in {"reset_hidden", "delayed_hidden_20", "pre_fault_stale_hidden"}
        and (_parse_bool(row.get("action_critical", False)) or _parse_bool(row.get("temporal_action_critical", False)))
    ):
        return "secondary"
    if (
        variant != "normal"
        and np.isfinite(first_action_distance)
        and first_action_distance < 0.005
        and np.isfinite(normal_margin)
        and normal_margin > 0.5
    ):
        return "sentinel"
    return None


def load_source_rows(
    temporal_rows_path: Path,
    *,
    seed_start: int,
    seed_count: int,
    max_source_rows: int,
    min_action_l2_gap: float,
    sentinel_fraction: float = 0.10,
) -> list[dict[str, Any]]:
    seed_min = int(seed_start)
    seed_max = int(seed_start) + int(seed_count)
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    seen_keys: set[tuple[str, ...]] = set()

    def ingest(path: Path, *, sentinel_only: bool) -> None:
        if not path.exists():
            return
        with path.open(newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                seed = int(raw.get("seed", -1))
                if seed < seed_min or seed >= seed_max:
                    continue
                role = _source_role(raw, min_action_l2_gap)
                if role is None or (sentinel_only and role != "sentinel"):
                    continue
                dedup_key = _source_row_identity(raw)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                row = dict(raw)
                row["source_role"] = role
                score = _finite_float(row.get("first_action_distance_from_normal"), default=0.0)
                normal_margin = _finite_float(row.get("normal_margin"), default=0.0)
                row["_selection_score"] = float(score - 0.001 * max(normal_margin, 0.0))
                step_bucket = str(row.get("step_bucket", "")).strip() or str(int(int(row.get("step", 0)) // 20))
                margin_bucket = _bucket_float(normal_margin, width=0.05)
                action_bucket = _bucket_float(score, width=0.005)
                key = (
                    role,
                    str(row.get("seed", "")),
                    str(row.get("preferred_fault_family", "")),
                    str(row.get("wrong_fault_family", "")),
                    str(row.get("fault_family_pair", "")),
                    str(row.get("preferred_fault_severity", "")),
                    str(row.get("source_pool", "")),
                    step_bucket,
                    margin_bucket,
                    action_bucket,
                    str(row.get("assigned_split", "")),
                )
                grouped.setdefault(key, []).append(row)

    ingest(temporal_rows_path, sentinel_only=False)
    sibling_rollouts = temporal_rows_path.parent / "intervention_rollouts.csv"
    if sibling_rollouts != temporal_rows_path:
        ingest(sibling_rollouts, sentinel_only=True)

    primary_groups = {
        key: sorted(rows, key=lambda item: float(item["_selection_score"]), reverse=True)
        for key, rows in grouped.items()
        if key[0] != "sentinel"
    }
    sentinel_groups = {
        key: sorted(rows, key=lambda item: float(item["_selection_score"]), reverse=True)
        for key, rows in grouped.items()
        if key[0] == "sentinel"
    }

    sentinel_target = max(1, int(round(float(max_source_rows) * float(sentinel_fraction)))) if sentinel_groups else 0
    primary_target = max(0, int(max_source_rows) - sentinel_target)
    selected = _round_robin_take(primary_groups, primary_target)
    selected.extend(_round_robin_take(sentinel_groups, sentinel_target))
    for index, row in enumerate(selected):
        row["source_index"] = int(index)
        row.pop("_selection_score", None)
    return selected


def _round_robin_take(groups: dict[tuple[str, ...], list[dict[str, Any]]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    keys = _balanced_group_order(list(groups))
    cursor = {key: 0 for key in keys}
    while len(selected) < int(limit):
        progressed = False
        for key in keys:
            offset = cursor[key]
            rows = groups[key]
            if offset >= len(rows):
                continue
            selected.append(rows[offset])
            cursor[key] = offset + 1
            progressed = True
            if len(selected) >= int(limit):
                break
        if not progressed:
            break
    return selected


def _balanced_group_order(keys: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    dimensions = (0, 2, 3, 4, 1, 7, 8, 9, 10, 5, 6)

    def order(items: list[tuple[str, ...]], dims: tuple[int, ...]) -> list[tuple[str, ...]]:
        if len(items) <= 1 or not dims:
            return sorted(items)
        dim = dims[0]
        grouped: dict[str, list[tuple[str, ...]]] = {}
        for item in items:
            value = item[dim] if dim < len(item) else ""
            grouped.setdefault(str(value), []).append(item)
        ordered_groups = [order(grouped[value], dims[1:]) for value in sorted(grouped)]
        result: list[tuple[str, ...]] = []
        while ordered_groups:
            next_groups: list[list[tuple[str, ...]]] = []
            for group in ordered_groups:
                if not group:
                    continue
                result.append(group[0])
                if len(group) > 1:
                    next_groups.append(group[1:])
            ordered_groups = next_groups
        return result

    return order(keys, dimensions)


def _snapshot_to_decision(snapshot: TemporalSnapshot) -> DecisionSnapshot:
    return DecisionSnapshot(
        condition=snapshot.fault.name,
        seed=int(snapshot.seed),
        step=int(snapshot.step),
        observation=np.asarray(snapshot.observation, dtype=np.float32).copy(),
        hidden=clone_hidden(snapshot.hidden),
        env=copy.deepcopy(snapshot.env),
        info=dict(snapshot.info),
        obstacle_distance=float(snapshot.obstacle_distance),
        snapshot_score=0.0,
    )


def relocate_temporal_snapshot(
    snapshot: TemporalSnapshot,
    *,
    body_longitudinal: float,
    body_lateral: float,
    half_width: float | None,
) -> TemporalSnapshot:
    relocated = relocate_obstacle_snapshot(
        _snapshot_to_decision(snapshot),
        body_longitudinal=float(body_longitudinal),
        body_lateral=float(body_lateral),
        half_width=half_width,
    )
    return replace(
        snapshot,
        observation=np.asarray(relocated.observation, dtype=np.float32).copy(),
        env=relocated.env,
        info=dict(relocated.info),
        obstacle_distance=float(body_longitudinal),
        obstacle_lateral_offset=float(body_lateral),
    )


def _base_half_width(snapshot: TemporalSnapshot) -> float:
    scenario = getattr(snapshot.env, "obstacle_scenario", None)
    if scenario is not None and np.isfinite(float(scenario.obstacle_half_width)):
        return float(scenario.obstacle_half_width)
    return float(snapshot.env.config.obstacle.half_width_range[0])


def _candidate_grid(
    snapshot: TemporalSnapshot,
    *,
    obstacle_x_shifts: tuple[float, ...],
    obstacle_y_shifts: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    max_candidates_per_source: int,
) -> list[dict[str, Any]]:
    base_distance = _finite_float(snapshot.obstacle_distance)
    base_lateral = _finite_float(snapshot.obstacle_lateral_offset, default=0.0)
    base_half_width = _base_half_width(snapshot)
    rows: list[dict[str, Any]] = []
    for x_shift in obstacle_x_shifts:
        body_longitudinal = max(1.0, float(base_distance) + float(x_shift))
        for y_shift in obstacle_y_shifts:
            body_lateral = float(base_lateral) + float(y_shift)
            for width_delta in half_width_deltas:
                half_width = max(0.05, float(base_half_width) + float(width_delta))
                score = abs(float(x_shift)) + 0.5 * abs(float(y_shift)) + 2.0 * abs(float(width_delta))
                rows.append(
                    {
                        "obstacle_x_shift_m": float(x_shift),
                        "obstacle_y_shift_m": float(y_shift),
                        "half_width_delta_m": float(width_delta),
                        "step_offset": 0,
                        "boundary_slack_delta_m": 0.0,
                        "fault_activation_step_delta": 0,
                        "target_obstacle_distance": float(body_longitudinal),
                        "relocated_obstacle_body_y": float(body_lateral),
                        "relocated_obstacle_half_width": float(half_width),
                        "_boundary_score": float(score),
                    }
                )
    rows.sort(key=lambda row: (float(row["_boundary_score"]), float(row["target_obstacle_distance"])))
    for index, row in enumerate(rows[: max(1, int(max_candidates_per_source))]):
        row["boundary_candidate_id"] = int(index)
        row.pop("_boundary_score", None)
    return rows[: max(1, int(max_candidates_per_source))]


def _collect_seed_snapshots(
    *,
    model: ActorCritic,
    env_config: Any,
    faults: list[FaultSpec],
    seed: int,
    config: dict[str, Any],
    device: torch.device,
) -> list[TemporalSnapshot]:
    snapshots: list[TemporalSnapshot] = []
    for fault in faults:
        scenario_snapshots, _ = collect_temporal_snapshots(
            model=model,
            env_config=env_config,
            fault=fault,
            seed=int(seed),
            start_snapshot_id=len(snapshots),
            min_step=int(config.get("min_step", 30)),
            max_steps=int(config.get("max_steps", 280)),
            snapshot_stride=int(config.get("snapshot_stride", 4)),
            max_snapshots_per_scenario=int(config.get("max_snapshots_per_scenario", 5)),
            obstacle_longitudinal_min=float(config.get("obstacle_longitudinal_min", -10.0)),
            obstacle_longitudinal_max=float(config.get("obstacle_longitudinal_max", 95.0)),
            history_window_steps=int(config.get("temporal_history_window_steps", 30)),
            device=device,
        )
        snapshots.extend(scenario_snapshots)
    return snapshots


def _find_snapshot(
    snapshots: list[TemporalSnapshot],
    *,
    fault_name: str,
    step: int,
) -> TemporalSnapshot | None:
    candidates = [snapshot for snapshot in snapshots if snapshot.fault.name == fault_name]
    if not candidates:
        return None
    return min(candidates, key=lambda snapshot: abs(int(snapshot.step) - int(step)))


def _candidate_meta(source: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_index": int(source.get("source_index", -1)),
        "source_pair_id": int(source.get("pair_id", -1)),
        "source_role": str(source.get("source_role", "")),
        "seed": int(source.get("seed", -1)),
        "step": int(source.get("step", -1)),
        "preferred_snapshot_id": int(source.get("preferred_snapshot_id", -1)),
        "wrong_snapshot_id": int(source.get("wrong_snapshot_id", -1)),
        "preferred_fault": str(source.get("preferred_fault", "")),
        "preferred_fault_family": str(source.get("preferred_fault_family", "")),
        "preferred_fault_severity": str(source.get("preferred_fault_severity", "")),
        "wrong_fault": str(source.get("wrong_fault", "")),
        "wrong_fault_family": str(source.get("wrong_fault_family", "")),
        "wrong_fault_severity": str(source.get("wrong_fault_severity", "")),
        "fault_family_pair": str(source.get("fault_family_pair", "")),
        "severity_pair": str(source.get("severity_pair", "")),
        "pairing_rule": str(source.get("pairing_rule", "")),
        "source_pool": str(source.get("source_pool", "")),
        "assigned_split": str(source.get("assigned_split", "")),
        "boundary_candidate_id": int(candidate.get("boundary_candidate_id", -1)),
        "step_offset": int(candidate.get("step_offset", 0)),
        "obstacle_x_shift_m": float(candidate.get("obstacle_x_shift_m", 0.0)),
        "obstacle_y_shift_m": float(candidate.get("obstacle_y_shift_m", 0.0)),
        "half_width_delta_m": float(candidate.get("half_width_delta_m", 0.0)),
        "boundary_slack_delta_m": float(candidate.get("boundary_slack_delta_m", 0.0)),
        "fault_activation_step_delta": int(candidate.get("fault_activation_step_delta", 0)),
        "target_obstacle_distance": float(candidate.get("target_obstacle_distance", float("nan"))),
        "relocated_obstacle_body_y": float(candidate.get("relocated_obstacle_body_y", float("nan"))),
        "relocated_obstacle_half_width": float(candidate.get("relocated_obstacle_half_width", float("nan"))),
    }


def _accepted_boundary_row(row: dict[str, Any]) -> bool:
    return bool(
        row.get("source_role") != "sentinel"
        and row.get("variant") != "reset_hidden"
        and row.get("variant") != "normal"
        and row.get("temporal_action_critical", False)
        and row.get("temporal_outcome_critical", False)
    )


def run_temporal_action_boundary_outcome_miner(
    *,
    checkpoint_path: Path,
    config_path: Path,
    temporal_rows_path: Path,
    seed_start: int,
    seed_count: int,
    device: str,
    run_dir: Path,
    max_source_rows: int = 128,
    max_candidates_per_source: int = 12,
    obstacle_x_shifts: tuple[float, ...] = (-12.0, -8.0, -4.0, 0.0, 4.0),
    obstacle_y_shifts: tuple[float, ...] = (-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75),
    half_width_deltas: tuple[float, ...] = (0.0, 0.10, 0.20),
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("boundary miner requires an online recurrent checkpoint")
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    max_continuation_steps = int(config.get("max_continuation_steps", 50))

    source_rows = load_source_rows(
        temporal_rows_path,
        seed_start=seed_start,
        seed_count=seed_count,
        max_source_rows=max_source_rows,
        min_action_l2_gap=min_action_l2_gap,
    )
    source_balance_summary = _source_summary(source_rows)
    faults = [NOMINAL_FAULT, *config["faults"]]
    snapshots_by_seed: dict[int, list[TemporalSnapshot]] = {}
    for seed in sorted({int(row["seed"]) for row in source_rows}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=seed,
            config=config,
            device=resolved_device,
        )

    source_output_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for source in source_rows:
        seed = int(source["seed"])
        seed_snapshots = snapshots_by_seed.get(seed, [])
        snapshot = _find_snapshot(
            seed_snapshots,
            fault_name=str(source["preferred_fault"]),
            step=int(source["step"]),
        )
        wrong_snapshot = _find_snapshot(
            seed_snapshots,
            fault_name=str(source["wrong_fault"]),
            step=int(source["step"]),
        )
        source_record = dict(source)
        source_record.pop("_selection_score", None)
        source_output_rows.append(source_record)
        if snapshot is None or wrong_snapshot is None:
            rejected_rows.append(
                {
                    **source_record,
                    "rejection_reason": "source_snapshot_missing",
                }
            )
            continue
        for candidate in _candidate_grid(
            snapshot,
            obstacle_x_shifts=obstacle_x_shifts,
            obstacle_y_shifts=obstacle_y_shifts,
            half_width_deltas=half_width_deltas,
            max_candidates_per_source=max_candidates_per_source,
        ):
            meta = _candidate_meta(source_record, candidate)
            candidate_rows.append(meta)
            try:
                relocated = relocate_temporal_snapshot(
                    snapshot,
                    body_longitudinal=float(candidate["target_obstacle_distance"]),
                    body_lateral=float(candidate["relocated_obstacle_body_y"]),
                    half_width=float(candidate["relocated_obstacle_half_width"]),
                )
            except (ValueError, AttributeError) as exc:
                rejected_rows.append({**meta, "rejection_reason": f"relocation_failed:{exc}"})
                continue
            variant_hiddens = build_temporal_variant_hiddens(
                model=model,
                snapshot=relocated,
                wrong_snapshot=wrong_snapshot,
                response_dim=response_dim,
                device=resolved_device,
            )
            normal, normal_actions = replay_temporal_variant(
                model=model,
                snapshot=relocated,
                env_config=env_config,
                variant="normal",
                variant_hidden=variant_hiddens["normal"],
                normal_first_action=None,
                normal_actions=None,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            normal_first_action = np.asarray(
                [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
                dtype=np.float32,
            )
            normal_margin = _finite_float(normal.get("min_clearance_margin"))
            normal_ok = bool(normal.get("success", False) or (np.isfinite(normal_margin) and normal_margin >= 0.0))
            for variant in TEMPORAL_BOUNDARY_VARIANTS:
                variant_hidden = variant_hiddens.get(variant)
                if variant_hidden is None:
                    continue
                if variant == "normal":
                    result = normal
                else:
                    result, _ = replay_temporal_variant(
                        model=model,
                        snapshot=relocated,
                        env_config=env_config,
                        variant=variant,
                        variant_hidden=variant_hidden,
                        normal_first_action=normal_first_action,
                        normal_actions=normal_actions,
                        max_continuation_steps=max_continuation_steps,
                        device=resolved_device,
                    )
                row = _row_for_variant(
                    pair_meta=meta,
                    source_pool=str(source_record.get("source_pool", "")),
                    variant=variant,
                    result=result,
                    normal=normal,
                    action_threshold=min_action_l2_gap,
                    margin_threshold=min_history_margin_gap,
                )
                row["accepted_temporal_boundary"] = _accepted_boundary_row(row)
                rollout_rows.append(row)
                if row["accepted_temporal_boundary"]:
                    accepted_rows.append(row)
            if not normal_ok:
                rejected_rows.append({**meta, "rejection_reason": "normal_history_failed"})

    temporal_action_rows = [row for row in rollout_rows if bool(row.get("temporal_action_critical", False))]
    temporal_outcome_rows = [row for row in rollout_rows if bool(row.get("temporal_outcome_critical", False))]
    normal_failed_rejected = [row for row in rejected_rows if str(row.get("rejection_reason", "")) == "normal_history_failed"]
    sentinel_rows = [row for row in rollout_rows if str(row.get("source_role", "")) == "sentinel"]
    sentinel_false_positive_rows = [
        row
        for row in sentinel_rows
        if bool(row.get("temporal_action_critical", False)) and bool(row.get("temporal_outcome_critical", False))
    ]
    non_sentinel_rollout_rows = [row for row in rollout_rows if str(row.get("source_role", "")) != "sentinel"]
    unique_fault_families = len({str(row.get("preferred_fault_family", "")) for row in accepted_rows})
    unique_seeds = len({int(row.get("seed", -1)) for row in accepted_rows})
    max_fault_family_dominance = _dominance_fraction([str(row.get("preferred_fault_family", "")) for row in accepted_rows])
    normal_rows = [row for row in rollout_rows if row.get("variant") == "normal"]
    normal_history_retention_pass = bool(
        normal_rows
        and not any(str(row.get("terminal_reason", "")) == "artifact" for row in normal_rows)
        and len(normal_failed_rejected) <= max(1, len(candidate_rows) // 2)
    )
    sentinel_false_positive_rate = float(len(sentinel_false_positive_rows) / max(len(sentinel_rows), 1))
    result_class = classify_boundary_miner_result(
        candidate_variant_count=len(non_sentinel_rollout_rows),
        accepted_rows=len(accepted_rows),
        temporal_action_critical_rows=len(temporal_action_rows),
        temporal_outcome_critical_rows=len(temporal_outcome_rows),
        unique_fault_families=unique_fault_families,
        unique_seeds=unique_seeds,
        max_fault_family_dominance=max_fault_family_dominance,
        normal_history_retention_pass=normal_history_retention_pass,
        sentinel_false_positive_rate=sentinel_false_positive_rate,
        normal_failed_rejected=len(normal_failed_rejected),
    )

    write_csv_rows(run_dir / "source_rows.csv", source_output_rows)
    write_csv_rows(run_dir / "candidate_variants.csv", candidate_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "accepted_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "variant_summary.csv", _group_summary(rollout_rows, ("variant",)))
    write_csv_rows(run_dir / "fault_family_summary.csv", _group_summary(rollout_rows, ("fault_family_pair", "variant")))

    checksum_after = model_parameter_checksum(model)
    summary = {
        "run_type": "temporal_action_boundary_outcome_miner",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "temporal_rows": temporal_rows_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "fault_count": int(len(faults) - 1),
        "source_candidate_rows": int(len(source_rows)),
        "candidate_variant_count": int(len(rollout_rows)),
        "accepted_rows": int(len(accepted_rows)),
        "temporal_action_critical_rows": int(len(temporal_action_rows)),
        "temporal_outcome_critical_rows": int(len(temporal_outcome_rows)),
        "normal_failed_rejected": int(len(normal_failed_rejected)),
        "history_insensitive_rejected": int(
            len([row for row in rollout_rows if not bool(row.get("temporal_action_critical", False))])
        ),
        "sentinel_rows": int(len(sentinel_rows)),
        "sentinel_false_positive_rows": int(len(sentinel_false_positive_rows)),
        "sentinel_false_positive_rate": sentinel_false_positive_rate,
        "unique_fault_families": int(unique_fault_families),
        "unique_seeds": int(unique_seeds),
        "max_fault_family_dominance": float(max_fault_family_dominance),
        "normal_history_retention_pass": bool(normal_history_retention_pass),
        "source_role_counts": {
            role: int(sum(1 for row in source_output_rows if str(row.get("source_role", "")) == role))
            for role in sorted({str(row.get("source_role", "")) for row in source_output_rows})
        },
        **source_balance_summary,
        "thresholds": {
            "min_action_l2_gap": min_action_l2_gap,
            "min_history_margin_gap": min_history_margin_gap,
            "max_source_rows": int(max_source_rows),
            "max_candidates_per_source": int(max_candidates_per_source),
            "obstacle_x_shifts": list(obstacle_x_shifts),
            "obstacle_y_shifts": list(obstacle_y_shifts),
            "half_width_deltas": list(half_width_deltas),
        },
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "temporal_outcome_boundary_positive": bool(result_class == "temporal_outcome_boundary_positive"),
        "summary_json": run_dir / "summary.json",
        "source_rows_csv": run_dir / "source_rows.csv",
        "candidate_variants_csv": run_dir / "candidate_variants.csv",
        "intervention_rollouts_csv": run_dir / "intervention_rollouts.csv",
        "accepted_rows_csv": run_dir / "accepted_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "fault_family_summary_csv": run_dir / "fault_family_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training temporal action-boundary outcome miner.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--temporal-rows", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=72000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--max-source-rows", type=int, default=128)
    parser.add_argument("--max-candidates-per-source", type=int, default=12)
    parser.add_argument("--obstacle-x-shifts", type=_parse_float_list, default=(-12.0, -8.0, -4.0, 0.0, 4.0))
    parser.add_argument("--obstacle-y-shifts", type=_parse_float_list, default=(-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75))
    parser.add_argument("--half-width-deltas", type=_parse_float_list, default=(0.0, 0.10, 0.20))
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="temporal_action_boundary_outcome_miner")
    summary = run_temporal_action_boundary_outcome_miner(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        temporal_rows_path=args.temporal_rows,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        device=args.device,
        run_dir=run_dir,
        max_source_rows=args.max_source_rows,
        max_candidates_per_source=args.max_candidates_per_source,
        obstacle_x_shifts=tuple(args.obstacle_x_shifts),
        obstacle_y_shifts=tuple(args.obstacle_y_shifts),
        half_width_deltas=tuple(args.half_width_deltas),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
