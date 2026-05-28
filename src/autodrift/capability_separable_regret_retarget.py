"""Retarget low-regret capability-separable pairs near obstacle geometry boundaries."""

from __future__ import annotations

import argparse
import ast
import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.capability_separable_source_constructor import (
    _as_outcome_snapshot,
    _rollout_action_sequence_override,
    _write_model_fidelity_limits,
    classify_capability_separable_result,
    evaluate_action_separability,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    ExtremeSnapshot,
    collect_fault_snapshots,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_BODY_X_DELTAS = (-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0)
DEFAULT_BODY_Y_DELTAS = (-0.30, -0.15, -0.075, 0.0, 0.075, 0.15, 0.30)
DEFAULT_HALF_WIDTH_DELTAS = (-0.08, -0.04, -0.02, -0.01, 0.0, 0.01, 0.02, 0.04, 0.08)


def parse_float_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("float list must contain at least one value")
    return values


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int_value(value: Any, default: int = 0) -> int:
    if value in ("", None):
        return int(default)
    return int(value)


def _float_value(value: Any, default: float = float("nan")) -> float:
    if value in ("", None):
        return float(default)
    return float(value)


def parse_candidate_sequence(row: dict[str, Any]) -> np.ndarray:
    raw = row.get("candidate_vector")
    if raw in ("", None):
        raise ValueError(f"candidate row {row.get('candidate_id')} has no candidate_vector")
    values = ast.literal_eval(str(raw)) if isinstance(raw, str) else raw
    vector = np.asarray(values, dtype=np.float32)
    length = _int_value(row.get("sequence_length"), default=0)
    if length <= 0:
        if vector.size % 3 != 0:
            raise ValueError(f"candidate_vector length is not divisible by 3: {vector.size}")
        length = vector.size // 3
    if vector.size != length * 3:
        raise ValueError(f"candidate_vector length {vector.size} does not match sequence_length {length}")
    return vector.reshape(length, 3).astype(np.float32)


def retarget_geometry_candidates(
    *,
    base_body_x: float,
    base_body_y: float,
    base_half_width: float,
    body_x_deltas: tuple[float, ...] = DEFAULT_BODY_X_DELTAS,
    body_y_deltas: tuple[float, ...] = DEFAULT_BODY_Y_DELTAS,
    half_width_deltas: tuple[float, ...] = DEFAULT_HALF_WIDTH_DELTAS,
    min_body_x: float = 0.5,
    min_half_width: float = 0.1,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[float, float, float]] = set()
    for body_x_delta in body_x_deltas:
        body_x = float(base_body_x) + float(body_x_delta)
        if body_x <= float(min_body_x):
            continue
        for body_y_delta in body_y_deltas:
            body_y = float(base_body_y) + float(body_y_delta)
            for half_width_delta in half_width_deltas:
                half_width = float(base_half_width) + float(half_width_delta)
                if half_width < float(min_half_width):
                    continue
                key = (round(body_x, 6), round(body_y, 6), round(half_width, 6))
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    {
                        "retarget_id": len(candidates),
                        "body_x_delta": float(body_x_delta),
                        "body_y_delta": float(body_y_delta),
                        "half_width_delta": float(half_width_delta),
                        "relocated_obstacle_body_x": body_x,
                        "relocated_obstacle_body_y": body_y,
                        "relocated_obstacle_half_width": half_width,
                    }
                )
    return candidates


def is_regret_boundary_target(
    row: dict[str, Any],
    *,
    min_best_action_l2: float,
    min_cross_regret_margin: float,
) -> bool:
    if _bool_value(row.get("accepted")):
        return False
    if not (_bool_value(row.get("best_A_success")) and _bool_value(row.get("best_B_success"))):
        return False
    if str(row.get("rejection_reason", "")).strip() != "insufficient_cross_regret":
        return False
    if _float_value(row.get("best_action_l2"), default=0.0) < float(min_best_action_l2):
        return False
    min_regret = min(_float_value(row.get("cross_regret_A")), _float_value(row.get("cross_regret_B")))
    return bool(np.isfinite(min_regret) and 0.0 < min_regret < float(min_cross_regret_margin))


def select_target_pairs(
    rows: list[dict[str, Any]],
    *,
    target_pair_id: int | None,
    max_target_pairs: int,
    min_best_action_l2: float,
    min_cross_regret_margin: float,
) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in rows
        if is_regret_boundary_target(
            row,
            min_best_action_l2=min_best_action_l2,
            min_cross_regret_margin=min_cross_regret_margin,
        )
    ]
    if target_pair_id is not None:
        candidates = [row for row in candidates if _int_value(row.get("pair_id"), default=-1) == int(target_pair_id)]
        if not candidates:
            raise ValueError(f"target_pair_id {target_pair_id} is not a regret-boundary target")
    candidates.sort(
        key=lambda row: (
            min(_float_value(row.get("cross_regret_A")), _float_value(row.get("cross_regret_B"))),
            -_float_value(row.get("best_action_l2"), default=0.0),
            _int_value(row.get("pair_id"), default=0),
        )
    )
    if int(max_target_pairs) > 0:
        candidates = candidates[: int(max_target_pairs)]
    if not candidates:
        raise ValueError("no regret-boundary target pairs selected")
    return candidates


def _candidate_rows_by_pair(path: Path, selected_pair_ids: set[int]) -> dict[tuple[int, int], dict[str, Any]]:
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    for row in _read_csv_rows(path):
        pair_id = _int_value(row.get("pair_id"), default=-1)
        if pair_id not in selected_pair_ids:
            continue
        candidate_id = _int_value(row.get("candidate_id"), default=-1)
        rows[(pair_id, candidate_id)] = dict(row)
    return rows


def _reconstruct_snapshots(
    *,
    model: ActorCritic,
    env_config_path: Path,
    scenario_config: dict[str, Any],
    source_summary: dict[str, Any],
    device: torch.device,
) -> dict[int, ExtremeSnapshot]:
    env_config = load_env_config(env_config_path)
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    snapshots: list[ExtremeSnapshot] = []
    seed_start = int(source_summary["seed_start"])
    seed_count = int(source_summary["seed_count"])
    for seed in range(seed_start, seed_start + seed_count):
        for fault in faults:
            scenario_snapshots, _ = collect_fault_snapshots(
                model=model,
                env_config=env_config,
                fault=fault,
                seed=int(seed),
                start_snapshot_id=len(snapshots),
                min_step=int(source_summary.get("effective_min_step", scenario_config.get("min_step", 35))),
                max_steps=int(source_summary.get("effective_max_steps", scenario_config.get("max_steps", 260))),
                snapshot_stride=int(
                    source_summary.get("effective_snapshot_stride", scenario_config.get("snapshot_stride", 5))
                ),
                max_snapshots_per_scenario=int(
                    source_summary.get(
                        "effective_max_snapshots_per_scenario",
                        scenario_config.get("max_snapshots_per_scenario", 4),
                    )
                ),
                obstacle_longitudinal_min=float(
                    source_summary.get(
                        "effective_obstacle_longitudinal_min",
                        scenario_config.get("obstacle_longitudinal_min", -8.0),
                    )
                ),
                obstacle_longitudinal_max=float(
                    source_summary.get(
                        "effective_obstacle_longitudinal_max",
                        scenario_config.get("obstacle_longitudinal_max", 90.0),
                    )
                ),
                device=device,
            )
            snapshots.extend(scenario_snapshots)
    return {int(snapshot.snapshot_id): snapshot for snapshot in snapshots}


def _validated_snapshot(
    snapshots: dict[int, ExtremeSnapshot],
    *,
    row: dict[str, Any],
    condition: str,
) -> ExtremeSnapshot:
    prefix = f"condition_{condition}"
    snapshot_id = _int_value(row.get(f"{prefix}_snapshot_id"), default=-1)
    if snapshot_id not in snapshots:
        raise ValueError(f"missing reconstructed snapshot_id={snapshot_id} for pair {row.get('pair_id')}")
    snapshot = snapshots[snapshot_id]
    expected_seed = _int_value(row.get("seed"), default=-1)
    expected_fault = str(row.get(f"{prefix}_fault", ""))
    expected_step = _int_value(row.get(f"step_{condition}"), default=-1)
    if int(snapshot.seed) != expected_seed or snapshot.fault.name != expected_fault or int(snapshot.step) != expected_step:
        raise ValueError(
            "reconstructed snapshot mismatch: "
            f"snapshot_id={snapshot_id} got seed={snapshot.seed} fault={snapshot.fault.name} step={snapshot.step}; "
            f"expected seed={expected_seed} fault={expected_fault} step={expected_step}"
        )
    return snapshot


def _rollout_fixed_sequence(
    *,
    pair_id: int,
    retarget_id: int,
    condition: str,
    candidate_row: dict[str, Any],
    snapshot: OutcomeSnapshot,
    model: ActorCritic,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    sequence = parse_candidate_sequence(candidate_row)
    result = _rollout_action_sequence_override(
        model=model,
        snapshot=snapshot,
        action_sequence=sequence,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    first = sequence[0]
    last = sequence[-1]
    return {
        "pair_id": int(pair_id),
        "retarget_id": int(retarget_id),
        "candidate_id": _int_value(candidate_row.get("candidate_id"), default=-1),
        "candidate_mode": str(candidate_row.get("candidate_mode", "")),
        "candidate_origin": str(candidate_row.get("candidate_origin", "")),
        "proposal_seed": _int_value(candidate_row.get("proposal_seed"), default=-1),
        "proposal_local_index": _int_value(candidate_row.get("proposal_local_index"), default=-1),
        "sequence_length": int(sequence.shape[0]),
        "template": str(candidate_row.get("template", "")),
        "condition": condition,
        "candidate_steer": float(first[0]),
        "candidate_throttle": float(first[1]),
        "candidate_brake": float(first[2]),
        "last_steer": float(last[0]),
        "last_throttle": float(last[1]),
        "last_brake": float(last[2]),
        "candidate_vector": sequence.reshape(-1).tolist(),
        "action_l2_from_shared_base": _float_value(candidate_row.get("action_l2_from_shared_base"), default=0.0),
        "success": bool(result.get("success", False)),
        "collision": bool(result.get("collision", False)),
        "terminal_reason": str(result.get("terminal_reason", "")),
        "min_clearance_margin": _finite_float(result.get("min_clearance_margin")),
        "return": _finite_float(result.get("return")),
        "steps": int(result.get("steps", 0)),
        "obstacle_completed": bool(result.get("obstacle_completed", False)),
        "beta_abs_peak": _finite_float(result.get("beta_abs_peak")),
    }


def retarget_diagnostics(
    *,
    rollout_rows: list[dict[str, Any]],
    decision: dict[str, Any],
    min_cross_regret_margin: float,
) -> dict[str, Any]:
    all_collided = bool(rollout_rows and all(bool(row.get("collision", False)) for row in rollout_rows))
    own_viability_fail = not (
        bool(decision.get("best_A_success", False)) and bool(decision.get("best_B_success", False))
    )
    wrong_branch_collision = not (
        bool(decision.get("A_using_B_success", False)) and bool(decision.get("B_using_A_success", False))
    )
    min_cross_regret = min(
        _finite_float(decision.get("cross_regret_A")),
        _finite_float(decision.get("cross_regret_B")),
    )
    low_regret = bool(np.isfinite(min_cross_regret) and min_cross_regret < float(min_cross_regret_margin))
    return {
        "all_four_rollouts_collision": all_collided,
        "own_branch_viability_fail": bool(own_viability_fail),
        "wrong_branch_collision": bool(wrong_branch_collision),
        "low_regret": low_regret,
        "min_cross_regret": min_cross_regret,
    }


def _evaluate_retarget_geometry(
    *,
    pair_row: dict[str, Any],
    geometry: dict[str, Any],
    snapshot_a: ExtremeSnapshot,
    snapshot_b: ExtremeSnapshot,
    candidate_a: dict[str, Any],
    candidate_b: dict[str, Any],
    model: ActorCritic,
    max_continuation_steps: int,
    min_best_action_l2: float,
    min_cross_regret_margin: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pair_id = _int_value(pair_row.get("pair_id"), default=-1)
    retarget_id = _int_value(geometry.get("retarget_id"), default=-1)
    relocated_a = relocate_outcome_snapshot(
        _as_outcome_snapshot(snapshot_a),
        body_longitudinal=float(geometry["relocated_obstacle_body_x"]),
        body_lateral=float(geometry["relocated_obstacle_body_y"]),
        half_width=float(geometry["relocated_obstacle_half_width"]),
    )
    relocated_b = relocate_outcome_snapshot(
        _as_outcome_snapshot(snapshot_b),
        body_longitudinal=float(geometry["relocated_obstacle_body_x"]),
        body_lateral=float(geometry["relocated_obstacle_body_y"]),
        half_width=float(geometry["relocated_obstacle_half_width"]),
    )
    rollout_rows = [
        _rollout_fixed_sequence(
            pair_id=pair_id,
            retarget_id=retarget_id,
            condition=condition,
            candidate_row=candidate,
            snapshot=snapshot,
            model=model,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        for candidate in (candidate_a, candidate_b)
        for condition, snapshot in (("A", relocated_a), ("B", relocated_b))
    ]
    decision = evaluate_action_separability(
        pair_id=pair_id,
        candidate_rows=rollout_rows,
        min_best_action_l2=min_best_action_l2,
        min_cross_regret_margin=min_cross_regret_margin,
    )
    diagnostics = retarget_diagnostics(
        rollout_rows=rollout_rows,
        decision=decision,
        min_cross_regret_margin=min_cross_regret_margin,
    )
    row = {
        "source_pair_id": pair_id,
        "retarget_id": retarget_id,
        "seed": _int_value(pair_row.get("seed"), default=-1),
        "condition_A_fault": str(pair_row.get("condition_A_fault", "")),
        "condition_B_fault": str(pair_row.get("condition_B_fault", "")),
        "fault_family_pair": str(pair_row.get("fault_family_pair", "")),
        "source_relocated_obstacle_body_x": _float_value(pair_row.get("relocated_obstacle_body_x")),
        "source_relocated_obstacle_body_y": _float_value(pair_row.get("relocated_obstacle_body_y")),
        "source_relocated_obstacle_half_width": _float_value(pair_row.get("relocated_obstacle_half_width")),
        **geometry,
        **decision,
        **diagnostics,
    }
    return row, rollout_rows


def run_regret_boundary_retarget(
    *,
    source_run_dir: Path,
    checkpoint_path: Path,
    config_path: Path,
    target_pair_id: int | None,
    max_target_pairs: int,
    max_continuation_steps: int,
    min_best_action_l2: float,
    min_cross_regret_margin: float,
    body_x_deltas: tuple[float, ...],
    body_y_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    min_body_x: float,
    min_half_width: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(source_run_dir / "summary.json")
    scenario_config = load_scenario_config(config_path)
    env_config_path = Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json"))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)

    pair_rows = _read_csv_rows(source_run_dir / "matched_capability_pairs.csv")
    selected_pairs = select_target_pairs(
        pair_rows,
        target_pair_id=target_pair_id,
        max_target_pairs=max_target_pairs,
        min_best_action_l2=min_best_action_l2,
        min_cross_regret_margin=min_cross_regret_margin,
    )
    selected_pair_ids = {_int_value(row.get("pair_id"), default=-1) for row in selected_pairs}
    candidate_rows = _candidate_rows_by_pair(source_run_dir / "trajectory_proposals.csv", selected_pair_ids)

    snapshots = _reconstruct_snapshots(
        model=model,
        env_config_path=env_config_path,
        scenario_config=scenario_config,
        source_summary=source_summary,
        device=resolved_device,
    )

    retarget_candidates: list[dict[str, Any]] = []
    retarget_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    source_reconstruction_rows: list[dict[str, Any]] = []

    for pair_row in selected_pairs:
        pair_id = _int_value(pair_row.get("pair_id"), default=-1)
        snapshot_a = _validated_snapshot(snapshots, row=pair_row, condition="A")
        snapshot_b = _validated_snapshot(snapshots, row=pair_row, condition="B")
        source_reconstruction_rows.extend(
            [
                {
                    "pair_id": pair_id,
                    "condition": "A",
                    "snapshot_id": int(snapshot_a.snapshot_id),
                    "seed": int(snapshot_a.seed),
                    "fault": snapshot_a.fault.name,
                    "step": int(snapshot_a.step),
                    "status": "matched",
                },
                {
                    "pair_id": pair_id,
                    "condition": "B",
                    "snapshot_id": int(snapshot_b.snapshot_id),
                    "seed": int(snapshot_b.seed),
                    "fault": snapshot_b.fault.name,
                    "step": int(snapshot_b.step),
                    "status": "matched",
                },
            ]
        )
        best_a_id = _int_value(pair_row.get("best_candidate_A"), default=-1)
        best_b_id = _int_value(pair_row.get("best_candidate_B"), default=-1)
        key_a = (pair_id, best_a_id)
        key_b = (pair_id, best_b_id)
        if key_a not in candidate_rows or key_b not in candidate_rows:
            raise ValueError(f"missing best candidate rows for pair {pair_id}: {best_a_id}, {best_b_id}")
        geometries = retarget_geometry_candidates(
            base_body_x=_float_value(pair_row.get("relocated_obstacle_body_x")),
            base_body_y=_float_value(pair_row.get("relocated_obstacle_body_y")),
            base_half_width=_float_value(pair_row.get("relocated_obstacle_half_width")),
            body_x_deltas=body_x_deltas,
            body_y_deltas=body_y_deltas,
            half_width_deltas=half_width_deltas,
            min_body_x=min_body_x,
            min_half_width=min_half_width,
        )
        for geometry in geometries:
            geometry_row = {"source_pair_id": pair_id, **geometry}
            retarget_candidates.append(geometry_row)
            retarget_row, rows = _evaluate_retarget_geometry(
                pair_row=pair_row,
                geometry=geometry,
                snapshot_a=snapshot_a,
                snapshot_b=snapshot_b,
                candidate_a=candidate_rows[key_a],
                candidate_b=candidate_rows[key_b],
                model=model,
                max_continuation_steps=max_continuation_steps,
                min_best_action_l2=min_best_action_l2,
                min_cross_regret_margin=min_cross_regret_margin,
                device=resolved_device,
            )
            retarget_rows.append(retarget_row)
            rollout_rows.extend(rows)
            if bool(retarget_row.get("accepted", False)):
                accepted_rows.append(retarget_row)
            else:
                rejected_rows.append(retarget_row)

    actor_parameters_changed = bool(checksum_before != model_parameter_checksum(model))
    best_actions_diverged_pairs = sum(
        1 for row in retarget_rows if _finite_float(row.get("best_action_l2"), default=0.0) >= float(min_best_action_l2)
    )
    low_regret_pairs = sum(1 for row in retarget_rows if bool(row.get("low_regret", False)))
    result_class = classify_capability_separable_result(
        matched_pair_count=len(retarget_rows),
        action_rollouts=len(rollout_rows),
        accepted_separable_pairs=len(accepted_rows),
        best_actions_diverged_pairs=best_actions_diverged_pairs,
        low_regret_pairs=low_regret_pairs,
    )
    fidelity_path = _write_model_fidelity_limits(run_dir, scenario_config)

    write_csv_rows(run_dir / "target_pairs.csv", selected_pairs)
    write_csv_rows(run_dir / "source_reconstruction.csv", source_reconstruction_rows)
    write_csv_rows(run_dir / "retarget_candidates.csv", retarget_candidates)
    write_csv_rows(run_dir / "retarget_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "accepted_regret_retarget_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_regret_retarget_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "retarget_decisions.csv", retarget_rows)

    summary = {
        "run_type": "capability_separable_regret_boundary_retarget",
        "source_run_dir": source_run_dir,
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": env_config_path,
        "target_pair_id": target_pair_id,
        "max_target_pairs": int(max_target_pairs),
        "selected_target_pairs": int(len(selected_pairs)),
        "selected_pair_ids": sorted(selected_pair_ids),
        "max_continuation_steps": int(max_continuation_steps),
        "min_best_action_l2": float(min_best_action_l2),
        "min_cross_regret_margin": float(min_cross_regret_margin),
        "body_x_deltas": body_x_deltas,
        "body_y_deltas": body_y_deltas,
        "half_width_deltas": half_width_deltas,
        "min_body_x": float(min_body_x),
        "min_half_width": float(min_half_width),
        "source_seed_start": int(source_summary.get("seed_start", -1)),
        "source_seed_count": int(source_summary.get("seed_count", -1)),
        "source_reconstructed_snapshot_count": int(len(snapshots)),
        "retarget_candidate_count": int(len(retarget_candidates)),
        "retarget_rollouts": int(len(rollout_rows)),
        "strict_accepted_count": int(len(accepted_rows)),
        "accepted_separable_pairs": int(len(accepted_rows)),
        "rejected_retarget_rows": int(len(rejected_rows)),
        "all_four_rollouts_collision_count": int(
            sum(1 for row in retarget_rows if bool(row.get("all_four_rollouts_collision", False)))
        ),
        "own_branch_viability_fail_count": int(
            sum(1 for row in retarget_rows if bool(row.get("own_branch_viability_fail", False)))
        ),
        "wrong_branch_collision_count": int(
            sum(1 for row in retarget_rows if bool(row.get("wrong_branch_collision", False)))
        ),
        "low_regret_count": int(low_regret_pairs),
        "best_actions_diverged_pairs": int(best_actions_diverged_pairs),
        "actor_parameters_changed": actor_parameters_changed,
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "source_reconstruction_reliable": True,
        "result_class": result_class,
        "source_positive": bool(result_class == "capability_separable_signal"),
        "target_pairs_csv": run_dir / "target_pairs.csv",
        "source_reconstruction_csv": run_dir / "source_reconstruction.csv",
        "retarget_candidates_csv": run_dir / "retarget_candidates.csv",
        "retarget_rollouts_csv": run_dir / "retarget_rollouts.csv",
        "retarget_decisions_csv": run_dir / "retarget_decisions.csv",
        "accepted_regret_retarget_rows_csv": run_dir / "accepted_regret_retarget_rows.csv",
        "rejected_regret_retarget_rows_csv": run_dir / "rejected_regret_retarget_rows.csv",
        "model_fidelity_limits_md": fidelity_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Retarget low-regret capability-separable source pairs.")
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--target-pair-id", type=int, default=None)
    parser.add_argument("--max-target-pairs", type=int, default=1)
    parser.add_argument("--max-continuation-steps", type=int, default=18)
    parser.add_argument("--min-best-action-l2", type=float, default=0.12)
    parser.add_argument("--min-cross-regret-margin", type=float, default=0.02)
    parser.add_argument("--body-x-deltas", type=parse_float_list, default=DEFAULT_BODY_X_DELTAS)
    parser.add_argument("--body-y-deltas", type=parse_float_list, default=DEFAULT_BODY_Y_DELTAS)
    parser.add_argument("--half-width-deltas", type=parse_float_list, default=DEFAULT_HALF_WIDTH_DELTAS)
    parser.add_argument("--min-body-x", type=float, default=0.5)
    parser.add_argument("--min-half-width", type=float, default=0.1)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="capability_separable_regret_retarget")
    summary = run_regret_boundary_retarget(
        source_run_dir=args.source_run_dir,
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        target_pair_id=args.target_pair_id,
        max_target_pairs=args.max_target_pairs,
        max_continuation_steps=args.max_continuation_steps,
        min_best_action_l2=args.min_best_action_l2,
        min_cross_regret_margin=args.min_cross_regret_margin,
        body_x_deltas=args.body_x_deltas,
        body_y_deltas=args.body_y_deltas,
        half_width_deltas=args.half_width_deltas,
        min_body_x=args.min_body_x,
        min_half_width=args.min_half_width,
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
