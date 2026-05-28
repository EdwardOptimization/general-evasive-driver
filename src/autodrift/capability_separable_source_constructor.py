"""Construct matched-current hidden-dynamics sources with action separability."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    ExtremeSnapshot,
    _feature_distance,
    _snapshot_row,
    collect_fault_snapshots,
    find_cross_fault_match,
    find_nominal_match,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.terminal_margin_recovery_anchor import (
    _rollout_first_action_override,
    build_action_candidates,
    parse_float_list,
)
from autodrift.train_ppo import ActorCritic, resolve_device


def _as_outcome_snapshot(snapshot: ExtremeSnapshot) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=int(snapshot.seed),
        step=int(snapshot.step),
        observation=np.asarray(snapshot.observation, dtype=np.float32).copy(),
        hidden=snapshot.hidden.detach().clone(),
        env=snapshot.env,
        info=dict(snapshot.info),
    )


def _margin(row: dict[str, Any]) -> float:
    return _finite_float(row.get("min_clearance_margin"))


def _success(row: dict[str, Any]) -> bool:
    return bool(row.get("success", False)) and not bool(row.get("collision", False))


def _best_condition_row(rows: list[dict[str, Any]], condition: str) -> dict[str, Any] | None:
    condition_rows = [row for row in rows if str(row.get("condition")) == condition]
    finite_rows = [row for row in condition_rows if np.isfinite(_margin(row))]
    if not finite_rows:
        return condition_rows[0] if condition_rows else None
    return max(
        finite_rows,
        key=lambda row: (
            _success(row),
            _margin(row),
            -float(row.get("action_l2_from_shared_base", float("inf"))),
        ),
    )


def _row_for_candidate(rows: list[dict[str, Any]], condition: str, candidate_id: int) -> dict[str, Any] | None:
    for row in rows:
        if str(row.get("condition")) == condition and int(row.get("candidate_id", -1)) == int(candidate_id):
            return row
    return None


def _action_from_row(row: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [row.get("candidate_steer"), row.get("candidate_throttle"), row.get("candidate_brake")],
        dtype=np.float32,
    )


def evaluate_action_separability(
    *,
    pair_id: int,
    candidate_rows: list[dict[str, Any]],
    min_best_action_l2: float,
    min_cross_regret_margin: float,
    min_best_margin: float = 0.0,
) -> dict[str, Any]:
    """Evaluate whether one matched pair requires different first actions."""

    best_a = _best_condition_row(candidate_rows, "A")
    best_b = _best_condition_row(candidate_rows, "B")
    if best_a is None or best_b is None:
        return {
            "pair_id": int(pair_id),
            "accepted": False,
            "rejection_reason": "missing_condition_rollouts",
        }

    best_a_id = int(best_a["candidate_id"])
    best_b_id = int(best_b["candidate_id"])
    a_using_b = _row_for_candidate(candidate_rows, "A", best_b_id)
    b_using_a = _row_for_candidate(candidate_rows, "B", best_a_id)
    if a_using_b is None or b_using_a is None:
        return {
            "pair_id": int(pair_id),
            "accepted": False,
            "rejection_reason": "missing_cross_candidate_rollouts",
        }

    action_l2 = float(np.linalg.norm(_action_from_row(best_a) - _action_from_row(best_b)))
    margin_a_best_a = _margin(best_a)
    margin_a_best_b = _margin(a_using_b)
    margin_b_best_b = _margin(best_b)
    margin_b_best_a = _margin(b_using_a)
    cross_regret_a = (
        float(margin_a_best_a - margin_a_best_b)
        if np.isfinite(margin_a_best_a) and np.isfinite(margin_a_best_b)
        else float("nan")
    )
    cross_regret_b = (
        float(margin_b_best_b - margin_b_best_a)
        if np.isfinite(margin_b_best_b) and np.isfinite(margin_b_best_a)
        else float("nan")
    )
    best_a_viable = bool(_success(best_a) and np.isfinite(margin_a_best_a) and margin_a_best_a >= min_best_margin)
    best_b_viable = bool(_success(best_b) and np.isfinite(margin_b_best_b) and margin_b_best_b >= min_best_margin)
    symmetric_margin_accept = bool(
        best_a_viable
        and best_b_viable
        and action_l2 >= float(min_best_action_l2)
        and np.isfinite(cross_regret_a)
        and np.isfinite(cross_regret_b)
        and cross_regret_a >= float(min_cross_regret_margin)
        and cross_regret_b >= float(min_cross_regret_margin)
    )
    asymmetric_success_drop = bool(
        action_l2 >= float(min_best_action_l2)
        and (
            (best_a_viable and not _success(a_using_b) and np.isfinite(cross_regret_a))
            or (best_b_viable and not _success(b_using_a) and np.isfinite(cross_regret_b))
        )
    )
    accepted = bool(symmetric_margin_accept or asymmetric_success_drop)
    if action_l2 < float(min_best_action_l2):
        rejection_reason = "best_actions_too_close"
    elif not (best_a_viable and best_b_viable):
        rejection_reason = "best_candidate_not_viable"
    elif not (np.isfinite(cross_regret_a) and np.isfinite(cross_regret_b)):
        rejection_reason = "cross_regret_not_finite"
    elif not accepted:
        rejection_reason = "insufficient_cross_regret"
    else:
        rejection_reason = "accepted"
    return {
        "pair_id": int(pair_id),
        "accepted": accepted,
        "acceptance_reason": "capability_separable" if accepted else "",
        "rejection_reason": rejection_reason,
        "best_candidate_A": best_a_id,
        "best_candidate_B": best_b_id,
        "best_action_l2": action_l2,
        "best_A_steer": float(best_a["candidate_steer"]),
        "best_A_throttle": float(best_a["candidate_throttle"]),
        "best_A_brake": float(best_a["candidate_brake"]),
        "best_B_steer": float(best_b["candidate_steer"]),
        "best_B_throttle": float(best_b["candidate_throttle"]),
        "best_B_brake": float(best_b["candidate_brake"]),
        "margin_A_best_A": margin_a_best_a,
        "margin_A_best_B": margin_a_best_b,
        "margin_B_best_B": margin_b_best_b,
        "margin_B_best_A": margin_b_best_a,
        "cross_regret_A": cross_regret_a,
        "cross_regret_B": cross_regret_b,
        "best_A_success": _success(best_a),
        "best_B_success": _success(best_b),
        "A_using_B_success": _success(a_using_b),
        "B_using_A_success": _success(b_using_a),
        "symmetric_margin_accept": symmetric_margin_accept,
        "asymmetric_success_drop": asymmetric_success_drop,
    }


def classify_capability_separable_result(
    *,
    matched_pair_count: int,
    action_rollouts: int,
    accepted_separable_pairs: int,
    best_actions_diverged_pairs: int,
    low_regret_pairs: int,
) -> str:
    if int(matched_pair_count) == 0:
        return "matched_state_empty"
    if int(action_rollouts) == 0:
        return "action_rollout_empty"
    if int(accepted_separable_pairs) > 0:
        return "capability_separable_signal"
    if int(best_actions_diverged_pairs) > 0 and int(low_regret_pairs) > 0:
        return "action_divergent_low_regret"
    return "no_capability_separable_signal"


def _group_pair_summary(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in pair_rows:
        key = str(row.get("fault_family_pair", ""))
        groups.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key, rows in sorted(groups.items()):
        output.append(
            {
                "fault_family_pair": key,
                "rows": int(len(rows)),
                "accepted_separable_pairs": int(sum(1 for row in rows if bool(row.get("accepted", False)))),
                "unique_seeds": int(len({int(row.get("seed", -1)) for row in rows})),
                "best_action_l2_median": float(
                    np.nanmedian([_finite_float(row.get("best_action_l2")) for row in rows])
                ),
                "min_cross_regret_median": float(
                    np.nanmedian(
                        [
                            min(_finite_float(row.get("cross_regret_A")), _finite_float(row.get("cross_regret_B")))
                            for row in rows
                        ]
                    )
                ),
            }
        )
    return output


def _write_model_fidelity_limits(run_dir: Path, config: dict[str, Any]) -> Path:
    future_only_faults = [str(item) for item in config.get("future_only_faults", [])]
    output = run_dir / "model_fidelity_limits.md"
    lines = [
        "# M1242 Model Fidelity Limits",
        "",
        "M1242 is an offline source-construction smoke over the current single-track model.",
        "It may use current-model VehicleParams changes and proxy capability losses as source metadata.",
        "",
        "It does not make physical claims about true per-wheel or asymmetric failures.",
        "",
        "Future high-fidelity faults not represented as faithful current-model data:",
        "",
        *[f"- {item}" for item in future_only_faults],
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def _evaluate_pair_lattice(
    *,
    pair_id: int,
    condition_a: ExtremeSnapshot,
    condition_b: ExtremeSnapshot,
    model: ActorCritic,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base_a, _ = deterministic_action_from_hidden(model, condition_a.observation, condition_a.hidden, device)
    base_b, _ = deterministic_action_from_hidden(model, condition_b.observation, condition_b.hidden, device)
    shared_base = np.clip(0.5 * (np.asarray(base_a, dtype=np.float32) + np.asarray(base_b, dtype=np.float32)), -1.0, 1.0)
    candidates = build_action_candidates(
        shared_base,
        steer_deltas=steer_deltas,
        throttle_deltas=throttle_deltas,
        brake_deltas=brake_deltas,
    )
    lattice_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    outcome_a = _as_outcome_snapshot(condition_a)
    outcome_b = _as_outcome_snapshot(condition_b)
    for candidate in candidates:
        lattice_rows.append(
            {
                "pair_id": int(pair_id),
                "candidate_id": int(candidate.candidate_id),
                "shared_base_steer": float(shared_base[0]),
                "shared_base_throttle": float(shared_base[1]),
                "shared_base_brake": float(shared_base[2]),
                "base_A_steer": float(base_a[0]),
                "base_A_throttle": float(base_a[1]),
                "base_A_brake": float(base_a[2]),
                "base_B_steer": float(base_b[0]),
                "base_B_throttle": float(base_b[1]),
                "base_B_brake": float(base_b[2]),
                "steer_delta": float(candidate.steer_delta),
                "throttle_delta": float(candidate.throttle_delta),
                "brake_delta": float(candidate.brake_delta),
                "candidate_steer": float(candidate.action[0]),
                "candidate_throttle": float(candidate.action[1]),
                "candidate_brake": float(candidate.action[2]),
                "action_l2_from_shared_base": float(candidate.action_l2),
            }
        )
        for condition, snapshot in (("A", outcome_a), ("B", outcome_b)):
            result = _rollout_first_action_override(
                model=model,
                snapshot=snapshot,
                first_action=candidate.action,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            rollout_rows.append(
                {
                    "pair_id": int(pair_id),
                    "candidate_id": int(candidate.candidate_id),
                    "condition": condition,
                    "candidate_steer": float(candidate.action[0]),
                    "candidate_throttle": float(candidate.action[1]),
                    "candidate_brake": float(candidate.action[2]),
                    "action_l2_from_shared_base": float(candidate.action_l2),
                    "success": bool(result.get("success", False)),
                    "collision": bool(result.get("collision", False)),
                    "terminal_reason": str(result.get("terminal_reason", "")),
                    "min_clearance_margin": _finite_float(result.get("min_clearance_margin")),
                    "return": _finite_float(result.get("return")),
                    "steps": int(result.get("steps", 0)),
                    "obstacle_completed": bool(result.get("obstacle_completed", False)),
                    "beta_abs_peak": _finite_float(result.get("beta_abs_peak")),
                }
            )
    return lattice_rows, rollout_rows


def run_capability_separable_source_constructor(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    max_pairs: int,
    max_pairs_per_seed: int,
    max_pairs_per_family_pair: int,
    max_continuation_steps: int,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_best_action_l2: float,
    min_cross_regret_margin: float,
    pairing_mode: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    if pairing_mode not in {"nominal", "cross_fault"}:
        raise ValueError(f"unknown pairing_mode {pairing_mode!r}")
    pairing_rules = tuple(config.get("pairing_rules", ()))
    if pairing_mode == "cross_fault" and not pairing_rules:
        raise ValueError("cross_fault pairing mode requires config pairing_rules")

    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)

    faults = [NOMINAL_FAULT, *config["faults"]]
    min_step = int(config.get("min_step", 35))
    max_steps = int(config.get("max_steps", 260))
    snapshot_stride = int(config.get("snapshot_stride", 5))
    max_snapshots_per_scenario = int(config.get("max_snapshots_per_scenario", 4))
    obstacle_longitudinal_min = float(config.get("obstacle_longitudinal_min", -8.0))
    obstacle_longitudinal_max = float(config.get("obstacle_longitudinal_max", 90.0))

    snapshots: list[ExtremeSnapshot] = []
    scenario_rows: list[dict[str, Any]] = []
    for seed in range(int(seed_start), int(seed_start) + int(seed_count)):
        for fault in faults:
            scenario_snapshots, scenario_row = collect_fault_snapshots(
                model=model,
                env_config=env_config,
                fault=fault,
                seed=int(seed),
                start_snapshot_id=len(snapshots),
                min_step=min_step,
                max_steps=max_steps,
                snapshot_stride=snapshot_stride,
                max_snapshots_per_scenario=max_snapshots_per_scenario,
                obstacle_longitudinal_min=obstacle_longitudinal_min,
                obstacle_longitudinal_max=obstacle_longitudinal_max,
                device=resolved_device,
            )
            snapshots.extend(scenario_snapshots)
            scenario_rows.append(scenario_row)

    snapshots_by_seed: dict[int, list[ExtremeSnapshot]] = {}
    for snapshot in snapshots:
        snapshots_by_seed.setdefault(int(snapshot.seed), []).append(snapshot)

    candidate_pairs: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []
    for seed, seed_snapshots in sorted(snapshots_by_seed.items()):
        nominal_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name == "nominal"]
        fault_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name != "nominal"]
        for snapshot in fault_snapshots:
            if pairing_mode == "cross_fault":
                matched, match_distance, pairing_rule = find_cross_fault_match(snapshot, seed_snapshots, pairing_rules)
            else:
                matched, match_distance = find_nominal_match(snapshot, nominal_snapshots)
                pairing_rule = "fault->nominal"
            if matched is None:
                unmatched_rows.append(
                    {
                        "seed": int(seed),
                        "snapshot_id": int(snapshot.snapshot_id),
                        "fault_name": snapshot.fault.name,
                        "fault_family": snapshot.fault.family,
                        "fault_severity": snapshot.fault.severity,
                        "pairing_mode": pairing_mode,
                        "rejection_reason": "matched_state_empty",
                    }
                )
                continue
            family_pair = f"{snapshot.fault.family}->{matched.fault.family}"
            candidate_pairs.append(
                {
                    "condition_A": snapshot,
                    "condition_B": matched,
                    "seed": int(seed),
                    "match_distance": float(match_distance),
                    "pairing_rule": pairing_rule,
                    "fault_family_pair": family_pair,
                }
            )

    selected_pairs: list[dict[str, Any]] = []
    seed_counts: dict[int, int] = {}
    family_pair_counts: dict[str, int] = {}
    for candidate in candidate_pairs:
        if len(selected_pairs) >= int(max_pairs):
            break
        seed = int(candidate["seed"])
        family_pair = str(candidate["fault_family_pair"])
        if int(max_pairs_per_seed) > 0 and seed_counts.get(seed, 0) >= int(max_pairs_per_seed):
            continue
        if (
            int(max_pairs_per_family_pair) > 0
            and family_pair_counts.get(family_pair, 0) >= int(max_pairs_per_family_pair)
        ):
            continue
        selected_pairs.append(candidate)
        seed_counts[seed] = seed_counts.get(seed, 0) + 1
        family_pair_counts[family_pair] = family_pair_counts.get(family_pair, 0) + 1

    pair_rows: list[dict[str, Any]] = []
    lattice_rows: list[dict[str, Any]] = []
    action_rollout_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for pair_id, candidate in enumerate(selected_pairs):
        snapshot = candidate["condition_A"]
        matched = candidate["condition_B"]
        match_distance = float(candidate["match_distance"])
        pairing_rule = str(candidate["pairing_rule"])
        pair_lattice_rows, pair_rollout_rows = _evaluate_pair_lattice(
            pair_id=pair_id,
            condition_a=snapshot,
            condition_b=matched,
            model=model,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        decision = evaluate_action_separability(
            pair_id=pair_id,
            candidate_rows=pair_rollout_rows,
            min_best_action_l2=min_best_action_l2,
            min_cross_regret_margin=min_cross_regret_margin,
        )
        base_pair = {
            "pair_id": int(pair_id),
            "seed": int(candidate["seed"]),
            "condition_A_snapshot_id": int(snapshot.snapshot_id),
            "condition_B_snapshot_id": int(matched.snapshot_id),
            "condition_A_fault": snapshot.fault.name,
            "condition_A_fault_family": snapshot.fault.family,
            "condition_A_fault_severity": snapshot.fault.severity,
            "condition_B_fault": matched.fault.name,
            "condition_B_fault_family": matched.fault.family,
            "condition_B_fault_severity": matched.fault.severity,
            "fault_family_pair": f"{snapshot.fault.family}->{matched.fault.family}",
            "severity_pair": f"{snapshot.fault.severity}->{matched.fault.severity}",
            "step_A": int(snapshot.step),
            "step_B": int(matched.step),
            "feature_distance": float(_feature_distance(snapshot, matched)),
            "match_distance": float(match_distance),
            "pairing_mode": pairing_mode,
            "pairing_rule": pairing_rule,
            "assigned_split": "public_source_smoke",
        }
        pair_row = {**base_pair, **decision}
        pair_rows.append(pair_row)
        lattice_rows.extend(pair_lattice_rows)
        action_rollout_rows.extend(pair_rollout_rows)
        if bool(decision.get("accepted", False)):
            accepted_rows.append(pair_row)
        else:
            rejected_rows.append(pair_row)

    actor_parameters_changed = bool(checksum_before != model_parameter_checksum(model))
    best_actions_diverged_pairs = sum(
        1 for row in pair_rows if _finite_float(row.get("best_action_l2"), default=0.0) >= float(min_best_action_l2)
    )
    low_regret_pairs = sum(
        1
        for row in pair_rows
        if min(_finite_float(row.get("cross_regret_A")), _finite_float(row.get("cross_regret_B")))
        < float(min_cross_regret_margin)
    )
    unique_family_pairs = {str(row.get("fault_family_pair", "")) for row in pair_rows}
    matched_seeds = {int(row.get("seed", -1)) for row in pair_rows}
    result_class = classify_capability_separable_result(
        matched_pair_count=len(pair_rows),
        action_rollouts=len(action_rollout_rows),
        accepted_separable_pairs=len(accepted_rows),
        best_actions_diverged_pairs=best_actions_diverged_pairs,
        low_regret_pairs=low_regret_pairs,
    )
    fidelity_path = _write_model_fidelity_limits(run_dir, config)

    write_csv_rows(run_dir / "scenario_summary.csv", scenario_rows)
    write_csv_rows(run_dir / "snapshot_candidates.csv", [_snapshot_row(snapshot) for snapshot in snapshots])
    write_csv_rows(run_dir / "matched_capability_pairs.csv", pair_rows)
    write_csv_rows(run_dir / "action_lattice.csv", lattice_rows)
    write_csv_rows(run_dir / "action_rollouts.csv", action_rollout_rows)
    write_csv_rows(run_dir / "accepted_separable_pairs.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_pairs.csv", [*rejected_rows, *unmatched_rows])
    write_csv_rows(run_dir / "fault_family_pair_summary.csv", _group_pair_summary(pair_rows))

    summary = {
        "run_type": "capability_separable_source_constructor",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": config.get("env_config"),
        "pairing_mode": pairing_mode,
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "max_pairs": int(max_pairs),
        "max_pairs_per_seed": int(max_pairs_per_seed),
        "max_pairs_per_family_pair": int(max_pairs_per_family_pair),
        "max_continuation_steps": int(max_continuation_steps),
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "min_best_action_l2": float(min_best_action_l2),
        "min_cross_regret_margin": float(min_cross_regret_margin),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "candidate_pair_count": int(len(candidate_pairs)),
        "matched_pair_count": int(len(pair_rows)),
        "unmatched_rows": int(len(unmatched_rows)),
        "action_lattice_rows": int(len(lattice_rows)),
        "action_rollouts": int(len(action_rollout_rows)),
        "accepted_separable_pairs": int(len(accepted_rows)),
        "rejected_pairs": int(len(rejected_rows)),
        "best_actions_diverged_pairs": int(best_actions_diverged_pairs),
        "low_regret_pairs": int(low_regret_pairs),
        "unique_matched_fault_family_pairs": int(len(unique_family_pairs)),
        "unique_matched_seeds": int(len(matched_seeds)),
        "actor_parameters_changed": actor_parameters_changed,
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "result_class": result_class,
        "source_positive": bool(result_class == "capability_separable_signal"),
        "scenario_summary_csv": run_dir / "scenario_summary.csv",
        "snapshot_candidates_csv": run_dir / "snapshot_candidates.csv",
        "matched_capability_pairs_csv": run_dir / "matched_capability_pairs.csv",
        "action_lattice_csv": run_dir / "action_lattice.csv",
        "action_rollouts_csv": run_dir / "action_rollouts.csv",
        "accepted_separable_pairs_csv": run_dir / "accepted_separable_pairs.csv",
        "rejected_pairs_csv": run_dir / "rejected_pairs.csv",
        "fault_family_pair_summary_csv": run_dir / "fault_family_pair_summary.csv",
        "model_fidelity_limits_md": fidelity_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Construct capability-separable hidden-dynamics source rows.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--pairing-mode", choices=["nominal", "cross_fault"], default="cross_fault")
    parser.add_argument("--seed-start", type=int, default=124200)
    parser.add_argument("--seed-count", type=int, default=24)
    parser.add_argument("--max-pairs", type=int, default=160)
    parser.add_argument("--max-pairs-per-seed", type=int, default=8)
    parser.add_argument("--max-pairs-per-family-pair", type=int, default=24)
    parser.add_argument("--max-continuation-steps", type=int, default=18)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.30, -0.15, 0.0, 0.15, 0.30))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.20, 0.0, 0.20))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.30, -0.15, 0.0, 0.15, 0.30))
    parser.add_argument("--min-best-action-l2", type=float, default=0.12)
    parser.add_argument("--min-cross-regret-margin", type=float, default=0.02)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="capability_separable_source_constructor")
    summary = run_capability_separable_source_constructor(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        max_pairs=args.max_pairs,
        max_pairs_per_seed=args.max_pairs_per_seed,
        max_pairs_per_family_pair=args.max_pairs_per_family_pair,
        max_continuation_steps=args.max_continuation_steps,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        min_best_action_l2=args.min_best_action_l2,
        min_cross_regret_margin=args.min_cross_regret_margin,
        pairing_mode=args.pairing_mode,
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
