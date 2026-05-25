"""Retarget v4 low-margin boundary windows with closed-loop replay."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import (
    _base_half_width,
    _collect_seed_snapshots,
    _find_snapshot,
    relocate_temporal_snapshot,
)
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _load_residual_head,
    replay_residual_sequence_variant,
)


DEFAULT_TARGET_MARGINS = (5e-6, 2.5e-5, 4.5e-5)
DEFAULT_DISTANCE_DELTAS = (0.02, 0.05, 0.10, 0.20, 0.25)

ANCHOR_FIELDS = [
    "anchor_id",
    "anchor_pool",
    "contrast_group_id",
    "seed",
    "source_index",
    "step",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fault_severity",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fault_severity",
    "fault_family_pair",
    "variant",
    "horizon",
    "alpha",
    "source_margin",
    "source_success",
    "source_collision",
    "source_terminal_reason",
]

PLAN_FIELDS = [
    *ANCHOR_FIELDS,
    "candidate_id",
    "retarget_axis",
    "target_margin_m",
    "obstacle_distance_delta_m",
    "half_width_delta_m",
    "target_obstacle_distance_m",
    "target_obstacle_half_width_m",
    "plan_reason",
]

REPLAY_FIELDS = [
    *PLAN_FIELDS,
    "reconstructed",
    "rejection_reason",
    "steps",
    "return",
    "terminated",
    "truncated",
    "success",
    "collision",
    "off_road",
    "spin_out",
    "terminal_reason",
    "obstacle_completed",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "first_steer",
    "first_throttle",
    "first_brake",
    "first_residual_steer",
    "first_residual_throttle",
    "first_residual_brake",
    "intervention_success",
    "intervention_collision",
    "intervention_margin",
    "intervention_prefix_l2_mean",
]

AXIS_SUMMARY_FIELDS = [
    "retarget_axis",
    "candidate_rows",
    "replay_rows",
    "accepted_rows",
    "unique_seed_count",
    "unique_source_index_count",
    "unique_fault_pair_count",
    "max_seed_dominance",
    "max_source_index_dominance",
    "max_fault_pair_dominance",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def parse_float_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one float is required")
    return values


def _normal_alpha_rows(rows: list[dict[str, str]], *, alpha: float) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if str(row.get("branch", "")) == "normal"
        and abs(_finite_float(row.get("alpha")) - float(alpha)) <= 1e-12
    ]


def _source_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("contrast_group_id", "")),
        str(row.get("seed", "")),
        str(row.get("source_index", "")),
        str(row.get("step", "")),
        str(row.get("preferred_fault", "")),
        str(row.get("wrong_fault", "")),
        str(row.get("variant", "")),
        str(row.get("horizon", "")),
    )


def _source_variant(row: dict[str, Any]) -> str:
    variant = str(row.get("variant", ""))
    if variant and variant != "normal":
        return variant
    parts = str(row.get("contrast_group_id", "")).split("|")
    if len(parts) >= 3 and parts[2]:
        return parts[2]
    return variant


def _anchor_meta(row: dict[str, Any], *, anchor_id: int, anchor_pool: str) -> dict[str, Any]:
    return {
        "anchor_id": int(anchor_id),
        "anchor_pool": str(anchor_pool),
        "contrast_group_id": str(row.get("contrast_group_id", "")),
        "seed": int(float(row.get("seed", -1))),
        "source_index": int(float(row.get("source_index", -1))),
        "step": int(float(row.get("step", -1))),
        "preferred_fault": str(row.get("preferred_fault", "")),
        "preferred_fault_family": str(row.get("preferred_fault_family", "")),
        "preferred_fault_severity": str(row.get("preferred_fault_severity", "")),
        "wrong_fault": str(row.get("wrong_fault", "")),
        "wrong_fault_family": str(row.get("wrong_fault_family", "")),
        "wrong_fault_severity": str(row.get("wrong_fault_severity", "")),
        "fault_family_pair": str(row.get("fault_family_pair", "")),
        "variant": _source_variant(row),
        "horizon": int(float(row.get("horizon", 0))),
        "alpha": _finite_float(row.get("alpha")),
        "source_margin": _finite_float(row.get("min_clearance_margin")),
        "source_success": parse_bool(row.get("success", False)),
        "source_collision": parse_bool(row.get("collision", False)),
        "source_terminal_reason": str(row.get("terminal_reason", "")),
    }


def select_boundary_anchor_rows(
    rows: list[dict[str, str]],
    *,
    alpha: float,
    collision_margin_floor: float,
    safe_margin_ceiling: float,
    diagnostic_safe_margin_ceiling: float,
    max_anchors: int | None = None,
) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    normal_rows = _normal_alpha_rows(rows, alpha=alpha)
    ordered_rows = sorted(
        normal_rows,
        key=lambda row: (
            0 if parse_bool(row.get("collision", False)) else 1,
            abs(_finite_float(row.get("min_clearance_margin"), default=1e9)),
            str(row.get("seed", "")),
            str(row.get("source_index", "")),
        ),
    )
    for row in ordered_rows:
        if _source_variant(row) not in SUPPORTED_VARIANTS:
            continue
        margin = _finite_float(row.get("min_clearance_margin"))
        if not np.isfinite(margin):
            continue
        pool = ""
        if parse_bool(row.get("collision", False)) and float(collision_margin_floor) <= margin < 0.0:
            pool = "collision_edge"
        elif parse_bool(row.get("success", False)) and not parse_bool(row.get("collision", False)) and 0.0 < margin <= float(safe_margin_ceiling):
            pool = "safe_edge"
        elif (
            parse_bool(row.get("success", False))
            and not parse_bool(row.get("collision", False))
            and float(safe_margin_ceiling) < margin <= float(diagnostic_safe_margin_ceiling)
        ):
            pool = "diagnostic_safe"
        if not pool:
            continue
        key = _source_key(row)
        if key in seen:
            continue
        seen.add(key)
        anchors.append(_anchor_meta(row, anchor_id=len(anchors), anchor_pool=pool))
        if max_anchors is not None and len(anchors) >= int(max_anchors):
            break
    return anchors


def _candidate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("anchor_id", "")),
        str(row.get("retarget_axis", "")),
        f"{_finite_float(row.get('target_margin_m')):.8f}",
        f"{_finite_float(row.get('obstacle_distance_delta_m')):.8f}",
        f"{_finite_float(row.get('half_width_delta_m')):.8f}",
    )


def plan_retarget_candidates(
    anchors: list[dict[str, Any]],
    *,
    target_margins: tuple[float, ...],
    distance_deltas: tuple[float, ...],
    max_half_width_delta: float,
    max_distance_delta: float,
    max_candidates_per_anchor: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for anchor in anchors:
        margin = _finite_float(anchor.get("source_margin"))
        if not np.isfinite(margin):
            continue
        local_rows: list[dict[str, Any]] = []
        if str(anchor.get("anchor_pool")) in {"collision_edge", "safe_edge"}:
            for target_margin in target_margins:
                half_delta = float(margin) - float(target_margin)
                if abs(half_delta) <= float(max_half_width_delta):
                    local_rows.append(
                        {
                            **anchor,
                            "retarget_axis": "obstacle_half_width",
                            "target_margin_m": float(target_margin),
                            "obstacle_distance_delta_m": 0.0,
                            "half_width_delta_m": float(half_delta),
                            "plan_reason": f"{anchor['anchor_pool']}_half_width_to_target_margin",
                        }
                    )
        direction = 1.0 if str(anchor.get("anchor_pool")) == "collision_edge" else -1.0
        if str(anchor.get("anchor_pool")) in {"collision_edge", "safe_edge"}:
            for delta in distance_deltas:
                signed_delta = direction * float(delta)
                if abs(signed_delta) <= float(max_distance_delta):
                    local_rows.append(
                        {
                            **anchor,
                            "retarget_axis": "obstacle_distance",
                            "target_margin_m": float("nan"),
                            "obstacle_distance_delta_m": float(signed_delta),
                            "half_width_delta_m": 0.0,
                            "plan_reason": f"{anchor['anchor_pool']}_distance_bracket",
                        }
                    )
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, ...]] = set()
        for row in local_rows:
            key = _candidate_key(row)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        deduped.sort(
            key=lambda row: (
                0 if str(row.get("retarget_axis")) == "obstacle_half_width" else 1,
                abs(_finite_float(row.get("half_width_delta_m"), default=0.0)),
                abs(_finite_float(row.get("obstacle_distance_delta_m"), default=0.0)),
            )
        )
        for row in deduped[: max(1, int(max_candidates_per_anchor))]:
            next_row = dict(row)
            next_row["candidate_id"] = len(candidates)
            next_row["target_obstacle_distance_m"] = float("nan")
            next_row["target_obstacle_half_width_m"] = float("nan")
            candidates.append(next_row)
    return candidates


def _accepted_rows(
    rows: list[dict[str, Any]],
    *,
    primary_margin_threshold: float,
) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for row in rows:
        margin = _finite_float(row.get("min_clearance_margin"))
        if (
            bool(row.get("reconstructed", False))
            and parse_bool(row.get("success", False))
            and not parse_bool(row.get("collision", False))
            and np.isfinite(margin)
            and 0.0 <= margin <= float(primary_margin_threshold)
        ):
            accepted.append(row)
    return accepted


def _axis_summary_rows(plan_rows: list[dict[str, Any]], replay_rows: list[dict[str, Any]], accepted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = sorted({str(row.get("retarget_axis", "")) for row in [*plan_rows, *replay_rows, *accepted_rows]})
    output: list[dict[str, Any]] = []
    for axis in axes:
        planned = [row for row in plan_rows if str(row.get("retarget_axis", "")) == axis]
        replayed = [row for row in replay_rows if str(row.get("retarget_axis", "")) == axis]
        accepted = [row for row in accepted_rows if str(row.get("retarget_axis", "")) == axis]
        output.append(
            {
                "retarget_axis": axis,
                "candidate_rows": int(len(planned)),
                "replay_rows": int(len(replayed)),
                "accepted_rows": int(len(accepted)),
                "unique_seed_count": unique_count(accepted, "seed"),
                "unique_source_index_count": unique_count(accepted, "source_index"),
                "unique_fault_pair_count": unique_count(accepted, "fault_family_pair"),
                "max_seed_dominance": max_share(accepted, "seed"),
                "max_source_index_dominance": max_share(accepted, "source_index"),
                "max_fault_pair_dominance": max_share(accepted, "fault_family_pair"),
            }
        )
    return output


def classify_boundary_window_result(
    *,
    actor_changed: bool,
    residual_changed: bool,
    reconstruction_failures: int,
    accepted_rows: list[dict[str, Any]],
    min_rows: int,
    min_seeds: int,
    min_source_indices: int,
    min_fault_pairs: int,
    max_seed_dominance: float,
    max_source_index_dominance: float,
    max_fault_pair_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_low_margin_boundary_window_contract_violation"
    if int(reconstruction_failures) > 0 and not accepted_rows:
        return "v4_low_margin_boundary_window_replay_error"
    if not accepted_rows or len(accepted_rows) < int(min_rows):
        return "v4_low_margin_boundary_window_sparse"
    axes = [str(row.get("retarget_axis", "")) for row in accepted_rows]
    if len(set(axes)) <= 1:
        return "v4_low_margin_boundary_window_geometry_only_diagnostic"
    if (
        unique_count(accepted_rows, "seed") < int(min_seeds)
        or unique_count(accepted_rows, "source_index") < int(min_source_indices)
        or unique_count(accepted_rows, "fault_family_pair") < int(min_fault_pairs)
        or max_share(accepted_rows, "seed") > float(max_seed_dominance)
        or max_share(accepted_rows, "source_index") > float(max_source_index_dominance)
        or max_share(accepted_rows, "fault_family_pair") > float(max_fault_pair_dominance)
    ):
        return "v4_low_margin_boundary_window_source_concentrated"
    return "v4_low_margin_boundary_window_pass"


def _append_progress(progress_path: Path, row: dict[str, Any]) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")


def _snapshot_obstacle_body(snapshot: Any) -> tuple[float, float]:
    obstacle_position = getattr(snapshot.env, "obstacle_position", None)
    if obstacle_position is None:
        return float(snapshot.obstacle_distance), float(snapshot.obstacle_lateral_offset)
    body = snapshot.env._body_point(obstacle_position)
    return float(body[0]), float(body[1])


def run_boundary_window_retarget(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    reference_replay_rows_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    primary_margin_threshold: float,
    collision_margin_floor: float,
    safe_margin_ceiling: float,
    diagnostic_safe_margin_ceiling: float,
    target_margins: tuple[float, ...],
    distance_deltas: tuple[float, ...],
    max_half_width_delta: float,
    max_distance_delta: float,
    max_anchors: int | None,
    max_candidates_per_anchor: int,
    min_rows: int,
    min_seeds: int,
    min_source_indices: int,
    min_fault_pairs: int,
    max_seed_dominance: float,
    max_source_index_dominance: float,
    max_fault_pair_dominance: float,
) -> dict[str, Any]:
    del positive_rows_path, contrast_rows_path
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    reference_rows = read_csv_rows(reference_replay_rows_path)
    anchor_rows = select_boundary_anchor_rows(
        reference_rows,
        alpha=float(alpha),
        collision_margin_floor=float(collision_margin_floor),
        safe_margin_ceiling=float(safe_margin_ceiling),
        diagnostic_safe_margin_ceiling=float(diagnostic_safe_margin_ceiling),
        max_anchors=max_anchors,
    )
    plan_rows = plan_retarget_candidates(
        anchor_rows,
        target_margins=target_margins,
        distance_deltas=distance_deltas,
        max_half_width_delta=float(max_half_width_delta),
        max_distance_delta=float(max_distance_delta),
        max_candidates_per_anchor=int(max_candidates_per_anchor),
    )

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("boundary-window retarget requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_checksum_before = model_parameter_checksum(residual_head)
    response_dim = response_feature_dim_for_model(model)
    max_continuation_steps = int(scenario_config.get("max_continuation_steps", 50))
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]

    snapshots_by_seed: dict[int, list[Any]] = {}
    for seed in sorted({int(row["seed"]) for row in anchor_rows}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(seed),
            config=scenario_config,
            device=resolved_device,
        )

    replay_rows: list[dict[str, Any]] = []
    reconstruction_failures = 0
    for plan in plan_rows:
        candidate_start = time.time()
        meta = {key: plan.get(key, "") for key in PLAN_FIELDS}
        seed = int(plan.get("seed", -1))
        step = int(plan.get("step", -1))
        horizon = int(plan.get("horizon", 0))
        snapshot = _find_snapshot(
            snapshots_by_seed.get(seed, []),
            fault_name=str(plan.get("preferred_fault", "")),
            step=step,
        )
        if snapshot is None:
            reconstruction_failures += 1
            replay = {**meta, "reconstructed": False, "rejection_reason": "missing_source_snapshot"}
            replay_rows.append(replay)
            _append_progress(
                progress_path,
                {
                    "candidate_id": int(plan.get("candidate_id", -1)),
                    "anchor_id": int(plan.get("anchor_id", -1)),
                    "retarget_axis": str(plan.get("retarget_axis", "")),
                    "status": "missing_source_snapshot",
                    "elapsed_seconds": time.time() - candidate_start,
                },
            )
            continue
        base_distance, base_lateral = _snapshot_obstacle_body(snapshot)
        base_half_width = _base_half_width(snapshot)
        target_distance = max(1.0, base_distance + _finite_float(plan.get("obstacle_distance_delta_m"), default=0.0))
        target_half_width = max(0.05, base_half_width + _finite_float(plan.get("half_width_delta_m"), default=0.0))
        plan["target_obstacle_distance_m"] = float(target_distance)
        plan["target_obstacle_half_width_m"] = float(target_half_width)
        meta["target_obstacle_distance_m"] = float(target_distance)
        meta["target_obstacle_half_width_m"] = float(target_half_width)
        relocated = relocate_temporal_snapshot(
            snapshot,
            body_longitudinal=float(target_distance),
            body_lateral=float(base_lateral),
            half_width=float(target_half_width),
        )
        normal, normal_actions = replay_residual_sequence_variant(
            model=model,
            residual_head=residual_head,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            horizon=horizon,
            response_dim=response_dim,
            reference_actions=None,
            base_reference_actions=None,
            max_continuation_steps=max_continuation_steps,
            alpha=float(alpha),
            device=resolved_device,
        )
        replay = {
            **meta,
            "reconstructed": True,
            "rejection_reason": "",
            **normal,
            "intervention_success": "",
            "intervention_collision": "",
            "intervention_margin": "",
            "intervention_prefix_l2_mean": "",
        }
        replay["variant"] = str(plan.get("variant", ""))
        margin = _finite_float(normal.get("min_clearance_margin"))
        if (
            parse_bool(normal.get("success", False))
            and not parse_bool(normal.get("collision", False))
            and np.isfinite(margin)
            and 0.0 <= margin <= float(primary_margin_threshold)
            and str(plan.get("variant", "")) in SUPPORTED_VARIANTS
        ):
            intervention, _ = replay_residual_sequence_variant(
                model=model,
                residual_head=residual_head,
                snapshot=relocated,
                env_config=env_config,
                variant=str(plan.get("variant")),
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=normal_actions,
                base_reference_actions=normal_actions,
                max_continuation_steps=max_continuation_steps,
                alpha=float(alpha),
                device=resolved_device,
            )
            replay["intervention_success"] = bool(intervention.get("success", False))
            replay["intervention_collision"] = bool(intervention.get("collision", False))
            replay["intervention_margin"] = _finite_float(intervention.get("min_clearance_margin"))
            replay["intervention_prefix_l2_mean"] = _finite_float(intervention.get("prefix_l2_mean"))
        replay_rows.append(replay)
        _append_progress(
            progress_path,
            {
                "candidate_id": int(plan.get("candidate_id", -1)),
                "anchor_id": int(plan.get("anchor_id", -1)),
                "retarget_axis": str(plan.get("retarget_axis", "")),
                "status": "replayed",
                "margin": margin if np.isfinite(margin) else None,
                "success": bool(normal.get("success", False)),
                "collision": bool(normal.get("collision", False)),
                "elapsed_seconds": time.time() - candidate_start,
            },
        )

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    accepted = _accepted_rows(replay_rows, primary_margin_threshold=primary_margin_threshold)
    axis_rows = _axis_summary_rows(plan_rows, replay_rows, accepted)
    result_class = classify_boundary_window_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        reconstruction_failures=int(reconstruction_failures),
        accepted_rows=accepted,
        min_rows=int(min_rows),
        min_seeds=int(min_seeds),
        min_source_indices=int(min_source_indices),
        min_fault_pairs=int(min_fault_pairs),
        max_seed_dominance=float(max_seed_dominance),
        max_source_index_dominance=float(max_source_index_dominance),
        max_fault_pair_dominance=float(max_fault_pair_dominance),
    )
    write_csv_rows(run_dir / "boundary_anchor_rows.csv", anchor_rows, fieldnames=ANCHOR_FIELDS)
    write_csv_rows(run_dir / "retarget_plan_rows.csv", plan_rows, fieldnames=PLAN_FIELDS)
    write_csv_rows(run_dir / "retarget_replay_rows.csv", replay_rows, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_low_margin_window_rows.csv", accepted, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "diagnostic_axis_summary.csv", axis_rows, fieldnames=AXIS_SUMMARY_FIELDS)
    summary = {
        "run_type": "v4_low_margin_boundary_window_retarget",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "reference_replay_rows": reference_replay_rows_path,
        "scenario_config": scenario_config_path,
        "alpha": float(alpha),
        "primary_margin_threshold": float(primary_margin_threshold),
        "anchor_rows": int(len(anchor_rows)),
        "collision_edge_anchor_rows": int(sum(1 for row in anchor_rows if row["anchor_pool"] == "collision_edge")),
        "safe_edge_anchor_rows": int(sum(1 for row in anchor_rows if row["anchor_pool"] == "safe_edge")),
        "diagnostic_safe_anchor_rows": int(sum(1 for row in anchor_rows if row["anchor_pool"] == "diagnostic_safe")),
        "retarget_plan_rows": int(len(plan_rows)),
        "retarget_replay_rows": int(len(replay_rows)),
        "reconstruction_failures": int(reconstruction_failures),
        "accepted_low_margin_window_rows": int(len(accepted)),
        "unique_accepted_seeds": unique_count(accepted, "seed"),
        "unique_accepted_source_indices": unique_count(accepted, "source_index"),
        "unique_accepted_fault_family_pairs": unique_count(accepted, "fault_family_pair"),
        "max_accepted_seed_dominance": max_share(accepted, "seed"),
        "max_accepted_source_index_dominance": max_share(accepted, "source_index"),
        "max_accepted_fault_pair_dominance": max_share(accepted, "fault_family_pair"),
        "unique_accepted_retarget_axes": unique_count(accepted, "retarget_axis"),
        "max_accepted_retarget_axis_dominance": max_share(accepted, "retarget_axis"),
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
        "boundary_anchor_rows_csv": run_dir / "boundary_anchor_rows.csv",
        "retarget_plan_rows_csv": run_dir / "retarget_plan_rows.csv",
        "retarget_replay_rows_csv": run_dir / "retarget_replay_rows.csv",
        "accepted_low_margin_window_rows_csv": run_dir / "accepted_low_margin_window_rows.csv",
        "diagnostic_axis_summary_csv": run_dir / "diagnostic_axis_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 low-margin boundary-window retargeting.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--reference-replay-rows", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--primary-margin-threshold", type=float, default=5e-5)
    parser.add_argument("--collision-margin-floor", type=float, default=-1e-3)
    parser.add_argument("--safe-margin-ceiling", type=float, default=1e-2)
    parser.add_argument("--diagnostic-safe-margin-ceiling", type=float, default=2e-1)
    parser.add_argument("--target-margins", type=parse_float_list, default=DEFAULT_TARGET_MARGINS)
    parser.add_argument("--distance-deltas", type=parse_float_list, default=DEFAULT_DISTANCE_DELTAS)
    parser.add_argument("--max-half-width-delta", type=float, default=1e-2)
    parser.add_argument("--max-distance-delta", type=float, default=2.5e-1)
    parser.add_argument("--max-anchors", type=int, default=None)
    parser.add_argument("--max-candidates-per-anchor", type=int, default=8)
    parser.add_argument("--min-rows", type=int, default=80)
    parser.add_argument("--min-seeds", type=int, default=8)
    parser.add_argument("--min-source-indices", type=int, default=8)
    parser.add_argument("--min-fault-pairs", type=int, default=4)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-source-index-dominance", type=float, default=0.15)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.40)
    args = parser.parse_args()
    summary = run_boundary_window_retarget(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        reference_replay_rows_path=args.reference_replay_rows,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        primary_margin_threshold=float(args.primary_margin_threshold),
        collision_margin_floor=float(args.collision_margin_floor),
        safe_margin_ceiling=float(args.safe_margin_ceiling),
        diagnostic_safe_margin_ceiling=float(args.diagnostic_safe_margin_ceiling),
        target_margins=tuple(args.target_margins),
        distance_deltas=tuple(args.distance_deltas),
        max_half_width_delta=float(args.max_half_width_delta),
        max_distance_delta=float(args.max_distance_delta),
        max_anchors=args.max_anchors,
        max_candidates_per_anchor=int(args.max_candidates_per_anchor),
        min_rows=int(args.min_rows),
        min_seeds=int(args.min_seeds),
        min_source_indices=int(args.min_source_indices),
        min_fault_pairs=int(args.min_fault_pairs),
        max_seed_dominance=float(args.max_seed_dominance),
        max_source_index_dominance=float(args.max_source_index_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
