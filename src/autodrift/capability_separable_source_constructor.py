"""Construct matched-current hidden-dynamics sources with action separability."""

from __future__ import annotations

import argparse
import copy
import math
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
from autodrift.wrong_history_boundary_relocation_surface import obstacle_body_geometry, relocate_outcome_snapshot


def _as_outcome_snapshot(snapshot: ExtremeSnapshot) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=int(snapshot.seed),
        step=int(snapshot.step),
        observation=np.asarray(snapshot.observation, dtype=np.float32).copy(),
        hidden=snapshot.hidden.detach().clone(),
        env=snapshot.env,
        info=dict(snapshot.info),
    )


def _ensure_outcome_snapshot(snapshot: ExtremeSnapshot | OutcomeSnapshot) -> OutcomeSnapshot:
    if isinstance(snapshot, OutcomeSnapshot):
        return snapshot
    return _as_outcome_snapshot(snapshot)


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
    if "candidate_vector" in row:
        return np.asarray(row["candidate_vector"], dtype=np.float32)
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

    sequence_length = max(1, int(best_a.get("sequence_length", 1)))
    action_l2 = float(np.linalg.norm(_action_from_row(best_a) - _action_from_row(best_b)) / math.sqrt(sequence_length))
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


def build_short_sequence_candidates(
    shared_base_action: np.ndarray,
    *,
    sequence_length: int,
    template_set: str,
) -> list[dict[str, Any]]:
    """Build compact shared steer/brake pulse candidates around one base action."""

    if str(template_set) != "steer_brake_pulses":
        raise ValueError(f"unsupported sequence_template_set {template_set!r}")
    base = np.asarray(shared_base_action, dtype=np.float32)
    if base.shape != (3,):
        raise ValueError(f"shared_base_action must have shape (3,), got {base.shape}")
    length = int(sequence_length)
    if length < 1:
        raise ValueError("sequence_length must be positive")

    steer_deltas = (-0.30, -0.15, 0.0, 0.15, 0.30)
    brake_deltas = (-0.30, 0.0, 0.30)
    templates = ("hold", "release", "ramp")
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()
    candidate_id = 0
    for template in templates:
        if template == "hold":
            scales = np.ones(length, dtype=np.float32)
        elif template == "release":
            scales = np.linspace(1.0, 0.0, num=length, dtype=np.float32)
        else:
            scales = np.linspace(0.0, 1.0, num=length, dtype=np.float32)
        for steer_delta in steer_deltas:
            for brake_delta in brake_deltas:
                sequence = []
                for scale in scales:
                    delta = np.asarray([float(steer_delta) * float(scale), 0.0, float(brake_delta) * float(scale)])
                    sequence.append(np.clip(base + delta, -1.0, 1.0).astype(np.float32))
                sequence_array = np.asarray(sequence, dtype=np.float32)
                flat = sequence_array.reshape(-1)
                key = tuple(round(float(value), 6) for value in flat.tolist())
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "template": template,
                        "steer_delta": float(steer_delta),
                        "throttle_delta": 0.0,
                        "brake_delta": float(brake_delta),
                        "sequence": sequence_array,
                        "candidate_vector": flat.astype(np.float32),
                        "action_l2_from_shared_base": float(
                            np.linalg.norm(flat - np.tile(base, length)) / math.sqrt(length)
                        ),
                    }
                )
                candidate_id += 1
    return candidates


def _pair_min_best_margin(decision: dict[str, Any]) -> float:
    return min(
        _finite_float(decision.get("margin_A_best_A")),
        _finite_float(decision.get("margin_B_best_B")),
    )


def _band_distance(value: float, *, target_min: float, target_max: float) -> float:
    if not np.isfinite(value):
        return float("inf")
    if float(target_min) <= float(value) <= float(target_max):
        return 0.0
    return min(abs(float(value) - float(target_min)), abs(float(value) - float(target_max)))


def _dedupe_geometry(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    output: list[dict[str, float]] = []
    seen: set[tuple[float, float, float]] = set()
    for row in rows:
        key = (
            round(float(row["body_x"]), 6),
            round(float(row["body_y"]), 6),
            round(float(row["half_width"]), 6),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def viability_band_geometry_candidates(
    snapshot: OutcomeSnapshot,
    *,
    pair_min_best_margin: float,
    target_min_best_margin: float,
    target_max_best_margin: float,
    max_half_width: float = 6.0,
) -> list[dict[str, float]]:
    body_x, body_y, half_width = obstacle_body_geometry(snapshot)
    target_mid = 0.5 * (float(target_min_best_margin) + float(target_max_best_margin))
    half_widths = [float(half_width)]
    if np.isfinite(pair_min_best_margin):
        for target in (target_min_best_margin, target_mid, target_max_best_margin):
            half_widths.append(float(half_width) + float(pair_min_best_margin) - float(target))
    half_widths.extend([float(half_width) - 0.5, float(half_width) + 0.5, float(half_width) + 1.0])
    half_widths = [float(np.clip(value, 0.2, max_half_width)) for value in half_widths if np.isfinite(value)]

    body_xs = [float(body_x)]
    body_ys = [
        float(body_y),
        0.0,
    ]
    candidates = [
        {"body_x": body_x_value, "body_y": body_y_value, "half_width": half_width_value}
        for body_x_value in body_xs
        for body_y_value in body_ys
        for half_width_value in half_widths
    ]
    return _dedupe_geometry(candidates)


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


def _rollout_action_sequence_override(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    action_sequence: np.ndarray,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
    actions = np.asarray(action_sequence, dtype=np.float32)
    if actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"action_sequence must have shape (K, 3), got {actions.shape}")

    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)

    for action in actions:
        if terminated or truncated:
            break
        _, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        obs, reward, terminated, truncated, info = env.step(np.clip(action, -1.0, 1.0).astype(np.float32))
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        hidden = next_hidden

    for _ in range(max(0, int(max_continuation_steps))):
        if terminated or truncated:
            break
        policy_action, next_hidden = deterministic_action_from_hidden(
            model,
            np.asarray(obs, dtype=np.float32),
            hidden,
            device,
        )
        obs, reward, terminated, truncated, info = env.step(policy_action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        hidden = next_hidden

    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    if bool(info.get("collision", False)):
        reason = "collision"
    elif bool(info.get("obstacle_completed", False)):
        reason = "obstacle_completed"
    elif bool(terminated):
        reason = "terminated"
    elif bool(truncated):
        reason = "truncated"
    else:
        reason = "running"
    return {
        "steps": int(len(rewards)),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(actions[0, 0]),
        "first_throttle": float(actions[0, 1]),
        "first_brake": float(actions[0, 2]),
    }


def _evaluate_pair_lattice(
    *,
    pair_id: int,
    condition_a: ExtremeSnapshot | OutcomeSnapshot,
    condition_b: ExtremeSnapshot | OutcomeSnapshot,
    model: ActorCritic,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    candidate_mode: str,
    sequence_length: int,
    sequence_template_set: str,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    outcome_a = _ensure_outcome_snapshot(condition_a)
    outcome_b = _ensure_outcome_snapshot(condition_b)
    base_a, _ = deterministic_action_from_hidden(model, outcome_a.observation, outcome_a.hidden, device)
    base_b, _ = deterministic_action_from_hidden(model, outcome_b.observation, outcome_b.hidden, device)
    shared_base = np.clip(0.5 * (np.asarray(base_a, dtype=np.float32) + np.asarray(base_b, dtype=np.float32)), -1.0, 1.0)
    if candidate_mode == "first_action":
        candidates = [
            {
                "candidate_id": candidate.candidate_id,
                "template": "first_action",
                "steer_delta": candidate.steer_delta,
                "throttle_delta": candidate.throttle_delta,
                "brake_delta": candidate.brake_delta,
                "sequence": candidate.action.reshape(1, 3),
                "candidate_vector": candidate.action.reshape(-1),
                "action_l2_from_shared_base": candidate.action_l2,
            }
            for candidate in build_action_candidates(
                shared_base,
                steer_deltas=steer_deltas,
                throttle_deltas=throttle_deltas,
                brake_deltas=brake_deltas,
            )
        ]
    elif candidate_mode == "short_sequence":
        candidates = build_short_sequence_candidates(
            shared_base,
            sequence_length=sequence_length,
            template_set=sequence_template_set,
        )
    else:
        raise ValueError(f"unknown candidate_mode {candidate_mode!r}")
    lattice_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        sequence = np.asarray(candidate["sequence"], dtype=np.float32)
        first_action = sequence[0]
        last_action = sequence[-1]
        lattice_rows.append(
            {
                "pair_id": int(pair_id),
                "candidate_id": int(candidate["candidate_id"]),
                "candidate_mode": candidate_mode,
                "sequence_length": int(sequence.shape[0]),
                "template": str(candidate["template"]),
                "shared_base_steer": float(shared_base[0]),
                "shared_base_throttle": float(shared_base[1]),
                "shared_base_brake": float(shared_base[2]),
                "base_A_steer": float(base_a[0]),
                "base_A_throttle": float(base_a[1]),
                "base_A_brake": float(base_a[2]),
                "base_B_steer": float(base_b[0]),
                "base_B_throttle": float(base_b[1]),
                "base_B_brake": float(base_b[2]),
                "steer_delta": float(candidate["steer_delta"]),
                "throttle_delta": float(candidate["throttle_delta"]),
                "brake_delta": float(candidate["brake_delta"]),
                "candidate_steer": float(first_action[0]),
                "candidate_throttle": float(first_action[1]),
                "candidate_brake": float(first_action[2]),
                "last_steer": float(last_action[0]),
                "last_throttle": float(last_action[1]),
                "last_brake": float(last_action[2]),
                "candidate_vector": candidate["candidate_vector"].tolist(),
                "action_l2_from_shared_base": float(candidate["action_l2_from_shared_base"]),
            }
        )
        for condition, snapshot in (("A", outcome_a), ("B", outcome_b)):
            if candidate_mode == "first_action":
                result = _rollout_first_action_override(
                    model=model,
                    snapshot=snapshot,
                    first_action=first_action,
                    max_continuation_steps=max_continuation_steps,
                    device=device,
                )
            else:
                result = _rollout_action_sequence_override(
                    model=model,
                    snapshot=snapshot,
                    action_sequence=sequence,
                    max_continuation_steps=max_continuation_steps,
                    device=device,
                )
            rollout_rows.append(
                {
                    "pair_id": int(pair_id),
                    "candidate_id": int(candidate["candidate_id"]),
                    "candidate_mode": candidate_mode,
                    "sequence_length": int(sequence.shape[0]),
                    "template": str(candidate["template"]),
                    "condition": condition,
                    "candidate_steer": float(first_action[0]),
                    "candidate_throttle": float(first_action[1]),
                    "candidate_brake": float(first_action[2]),
                    "last_steer": float(last_action[0]),
                    "last_throttle": float(last_action[1]),
                    "last_brake": float(last_action[2]),
                    "candidate_vector": candidate["candidate_vector"].tolist(),
                    "action_l2_from_shared_base": float(candidate["action_l2_from_shared_base"]),
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


def _evaluate_pair_with_relocation_candidates(
    *,
    pair_id: int,
    condition_a: ExtremeSnapshot,
    condition_b: ExtremeSnapshot,
    model: ActorCritic,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    candidate_mode: str,
    sequence_length: int,
    sequence_template_set: str,
    max_continuation_steps: int,
    min_best_action_l2: float,
    min_cross_regret_margin: float,
    source_window_mode: str,
    target_min_best_margin: float,
    target_max_best_margin: float,
    max_relocation_candidates: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    original_a = _as_outcome_snapshot(condition_a)
    original_b = _as_outcome_snapshot(condition_b)
    original_lattice, original_rollouts = _evaluate_pair_lattice(
        pair_id=pair_id,
        condition_a=original_a,
        condition_b=original_b,
        model=model,
        steer_deltas=steer_deltas,
        throttle_deltas=throttle_deltas,
        brake_deltas=brake_deltas,
        candidate_mode=candidate_mode,
        sequence_length=sequence_length,
        sequence_template_set=sequence_template_set,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    original_decision = evaluate_action_separability(
        pair_id=pair_id,
        candidate_rows=original_rollouts,
        min_best_action_l2=min_best_action_l2,
        min_cross_regret_margin=min_cross_regret_margin,
    )
    if source_window_mode == "matched_current":
        return original_lattice, original_rollouts, {**original_decision, "relocation_id": 0}, []
    if source_window_mode != "viability_band_relocation":
        raise ValueError(f"unknown source_window_mode {source_window_mode!r}")

    pair_min_best_margin = _pair_min_best_margin(original_decision)
    geometry_candidates = viability_band_geometry_candidates(
        original_a,
        pair_min_best_margin=pair_min_best_margin,
        target_min_best_margin=target_min_best_margin,
        target_max_best_margin=target_max_best_margin,
    )
    if int(max_relocation_candidates) > 0:
        geometry_candidates = geometry_candidates[: int(max_relocation_candidates)]
    relocation_rows: list[dict[str, Any]] = []
    evaluated: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]] = []
    for relocation_id, geometry in enumerate(geometry_candidates):
        relocated_a = relocate_outcome_snapshot(
            original_a,
            body_longitudinal=float(geometry["body_x"]),
            body_lateral=float(geometry["body_y"]),
            half_width=float(geometry["half_width"]),
        )
        relocated_b = relocate_outcome_snapshot(
            original_b,
            body_longitudinal=float(geometry["body_x"]),
            body_lateral=float(geometry["body_y"]),
            half_width=float(geometry["half_width"]),
        )
        lattice_rows, rollout_rows = _evaluate_pair_lattice(
            pair_id=pair_id,
            condition_a=relocated_a,
            condition_b=relocated_b,
            model=model,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            candidate_mode=candidate_mode,
            sequence_length=sequence_length,
            sequence_template_set=sequence_template_set,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        decision = evaluate_action_separability(
            pair_id=pair_id,
            candidate_rows=rollout_rows,
            min_best_action_l2=min_best_action_l2,
            min_cross_regret_margin=min_cross_regret_margin,
        )
        relocated_min_margin = _pair_min_best_margin(decision)
        near_boundary = bool(
            np.isfinite(relocated_min_margin)
            and float(target_min_best_margin) <= relocated_min_margin <= float(target_max_best_margin)
            and bool(decision.get("best_A_success", False))
            and bool(decision.get("best_B_success", False))
        )
        band_distance = _band_distance(
            relocated_min_margin,
            target_min=target_min_best_margin,
            target_max=target_max_best_margin,
        )
        relocation_decision = {
            **decision,
            "relocation_id": int(relocation_id),
            "relocated_obstacle_body_x": float(geometry["body_x"]),
            "relocated_obstacle_body_y": float(geometry["body_y"]),
            "relocated_obstacle_half_width": float(geometry["half_width"]),
            "pair_min_best_margin": relocated_min_margin,
            "near_boundary_viability": near_boundary,
            "band_distance": band_distance,
            "source_pair_min_best_margin": pair_min_best_margin,
        }
        relocation_rows.append(relocation_decision)
        evaluated.append((relocation_decision, lattice_rows, rollout_rows, relocation_decision))
        if bool(relocation_decision.get("accepted", False)):
            break

    if not evaluated:
        return original_lattice, original_rollouts, {**original_decision, "relocation_id": 0}, relocation_rows
    best_decision, best_lattice, best_rollouts, _ = min(
        evaluated,
        key=lambda item: (
            not bool(item[0].get("near_boundary_viability", False)),
            not bool(item[0].get("accepted", False)),
            float(item[0].get("band_distance", float("inf"))),
            -float(item[0].get("best_action_l2", 0.0)),
        ),
    )
    return best_lattice, best_rollouts, best_decision, relocation_rows


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
    candidate_mode: str = "first_action",
    sequence_length: int = 1,
    sequence_template_set: str = "steer_brake_pulses",
    source_window_mode: str = "matched_current",
    target_min_best_margin: float = 0.02,
    target_max_best_margin: float = 0.5,
    max_relocation_candidates: int = 8,
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
    relocation_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for pair_id, candidate in enumerate(selected_pairs):
        snapshot = candidate["condition_A"]
        matched = candidate["condition_B"]
        match_distance = float(candidate["match_distance"])
        pairing_rule = str(candidate["pairing_rule"])
        pair_lattice_rows, pair_rollout_rows, decision, pair_relocation_rows = _evaluate_pair_with_relocation_candidates(
            pair_id=pair_id,
            condition_a=snapshot,
            condition_b=matched,
            model=model,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            candidate_mode=candidate_mode,
            sequence_length=sequence_length,
            sequence_template_set=sequence_template_set,
            max_continuation_steps=max_continuation_steps,
            min_best_action_l2=min_best_action_l2,
            min_cross_regret_margin=min_cross_regret_margin,
            source_window_mode=source_window_mode,
            target_min_best_margin=target_min_best_margin,
            target_max_best_margin=target_max_best_margin,
            max_relocation_candidates=max_relocation_candidates,
            device=resolved_device,
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
        relocation_rows.extend({**base_pair, **row} for row in pair_relocation_rows)
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
    near_boundary_viability_pairs = sum(1 for row in pair_rows if bool(row.get("near_boundary_viability", False)))
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
    if candidate_mode == "short_sequence":
        write_csv_rows(run_dir / "sequence_lattice.csv", lattice_rows)
        write_csv_rows(run_dir / "sequence_rollouts.csv", action_rollout_rows)
    write_csv_rows(run_dir / "relocation_candidates.csv", relocation_rows)
    write_csv_rows(
        run_dir / "relocated_source_pairs.csv",
        pair_rows if source_window_mode == "viability_band_relocation" else [],
    )
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
        "candidate_mode": candidate_mode,
        "sequence_length": int(sequence_length),
        "sequence_template_set": sequence_template_set,
        "source_window_mode": source_window_mode,
        "target_min_best_margin": float(target_min_best_margin),
        "target_max_best_margin": float(target_max_best_margin),
        "max_relocation_candidates": int(max_relocation_candidates),
        "min_best_action_l2": float(min_best_action_l2),
        "min_cross_regret_margin": float(min_cross_regret_margin),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "candidate_pair_count": int(len(candidate_pairs)),
        "matched_pair_count": int(len(pair_rows)),
        "unmatched_rows": int(len(unmatched_rows)),
        "action_lattice_rows": int(len(lattice_rows)),
        "action_rollouts": int(len(action_rollout_rows)),
        "sequence_lattice_rows": int(len(lattice_rows)) if candidate_mode == "short_sequence" else 0,
        "sequence_rollouts": int(len(action_rollout_rows)) if candidate_mode == "short_sequence" else 0,
        "accepted_separable_pairs": int(len(accepted_rows)),
        "rejected_pairs": int(len(rejected_rows)),
        "relocation_candidates": int(len(relocation_rows)),
        "relocated_matched_pairs": int(len(pair_rows)) if source_window_mode == "viability_band_relocation" else 0,
        "near_boundary_viability_pairs": int(near_boundary_viability_pairs),
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
        "relocation_candidates_csv": run_dir / "relocation_candidates.csv",
        "relocated_source_pairs_csv": run_dir / "relocated_source_pairs.csv",
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
    parser.add_argument("--candidate-mode", choices=["first_action", "short_sequence"], default="first_action")
    parser.add_argument("--sequence-length", type=int, default=1)
    parser.add_argument("--sequence-template-set", choices=["steer_brake_pulses"], default="steer_brake_pulses")
    parser.add_argument(
        "--source-window-mode",
        choices=["matched_current", "viability_band_relocation"],
        default="matched_current",
    )
    parser.add_argument("--target-min-best-margin", type=float, default=0.02)
    parser.add_argument("--target-max-best-margin", type=float, default=0.5)
    parser.add_argument("--max-relocation-candidates", type=int, default=8)
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
        candidate_mode=args.candidate_mode,
        sequence_length=args.sequence_length,
        sequence_template_set=args.sequence_template_set,
        source_window_mode=args.source_window_mode,
        target_min_best_margin=args.target_min_best_margin,
        target_max_best_margin=args.target_max_best_margin,
        max_relocation_candidates=args.max_relocation_candidates,
        pairing_mode=args.pairing_mode,
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
