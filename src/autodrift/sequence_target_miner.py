"""Mine diagnostic short-horizon action-sequence targets."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_conditioned_grounded_target_miner import _diversity, _empty_float_stat, load_boundary_source_rows
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import (
    SurfaceConfig,
    _finite_float,
    _hidden_array,
    parse_surface_config,
    request_steps_for_target_rows,
    risk_score,
    source_diversity_weights,
    variant_hidden_for_row,
)
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, _snapshot, collect_requested_outcome_snapshots
from autodrift.terminal_margin_recovery_anchor import parse_float_list
from autodrift.train_ppo import ActorCritic, resolve_device


SOURCE_METADATA_FIELDNAMES = [
    "source_tier",
    "expansion_reason",
    "original_m609_boundary",
    "m613_accepted_sequence",
]

SEQUENCE_CANDIDATE_FIELDNAMES = [
    "source_index",
    "coupling_row_index",
    "candidate_id",
    "family",
    "sequence_length",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "capability_z_distance",
    "action_distance",
    "coupling_gap",
    "baseline_success",
    "baseline_collision",
    "baseline_terminal_reason",
    "baseline_margin",
    "baseline_risk_score",
    "candidate_success",
    "candidate_collision",
    "candidate_off_road",
    "candidate_spin_out",
    "candidate_terminal_reason",
    "candidate_margin",
    "candidate_risk_score",
    "margin_improvement",
    "risk_improvement",
    "steer_delta",
    "throttle_delta",
    "brake_delta",
    "sequence_mean_l2",
    "sequence_max_l2",
    "max_delta_delta_l2",
    "accepted",
    "rejection_reason",
] + SOURCE_METADATA_FIELDNAMES

ACCEPTED_SEQUENCE_FIELDNAMES = [
    "source_index",
    "coupling_row_index",
    "candidate_id",
    "family",
    "sequence_length",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "capability_z_distance",
    "action_distance",
    "coupling_gap",
    "baseline_margin",
    "target_margin",
    "margin_improvement",
    "baseline_risk_score",
    "target_risk_score",
    "risk_improvement",
    "sequence_mean_l2",
    "sequence_max_l2",
    "max_delta_delta_l2",
    "acceptance_reason",
    "weight",
] + SOURCE_METADATA_FIELDNAMES

UNACCEPTED_SEQUENCE_FIELDNAMES = [
    "source_index",
    "coupling_row_index",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "capability_z_distance",
    "action_distance",
    "coupling_gap",
    "baseline_margin",
    "baseline_risk_score",
    "best_candidate_id",
    "best_family",
    "best_sequence_length",
    "best_margin",
    "best_margin_improvement",
    "best_risk_improvement",
    "best_sequence_mean_l2",
    "best_sequence_max_l2",
    "best_max_delta_delta_l2",
    "best_rejection_reason",
] + SOURCE_METADATA_FIELDNAMES


@dataclass(frozen=True)
class SequenceCandidate:
    candidate_id: int
    family: str
    sequence_length: int
    steer_delta: float
    throttle_delta: float
    brake_delta: float
    action_sequence: np.ndarray
    delta_sequence: np.ndarray
    sequence_mean_l2: float
    sequence_max_l2: float
    max_delta_delta_l2: float
    trust_region_ok: bool


def parse_int_list(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("int list must contain at least one value")
    return values


def source_metadata(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for column in SOURCE_METADATA_FIELDNAMES:
        value = row.get(column, "")
        if pd.isna(value):
            value = ""
        output[column] = value
    return output


def accepted_candidate_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in candidate_rows if bool(row.get("accepted", False))]


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].value_counts().to_dict().items()}


def sequence_scales(length: int, family: str) -> np.ndarray:
    if length <= 0:
        raise ValueError("sequence length must be positive")
    if family == "constant_delta":
        return np.ones(int(length), dtype=np.float32)
    if family == "decay_pulse":
        if int(length) == 3:
            return np.asarray([1.0, 0.5, 0.25], dtype=np.float32)
        if int(length) == 5:
            return np.asarray([1.0, 0.7, 0.45, 0.25, 0.0], dtype=np.float32)
        return np.linspace(1.0, 0.0, int(length), dtype=np.float32)
    raise ValueError(f"unknown scaled sequence family: {family}")


def sequence_trust_metrics(
    *,
    action_sequence: np.ndarray,
    base_action_sequence: np.ndarray,
) -> tuple[float, float, float]:
    actions = np.asarray(action_sequence, dtype=np.float32)
    base = np.asarray(base_action_sequence, dtype=np.float32)
    if actions.shape != base.shape or actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"expected matching (K, 3) sequences, got {actions.shape} and {base.shape}")
    deltas = actions.astype(np.float64) - base.astype(np.float64)
    step_l2 = np.linalg.norm(deltas, axis=1)
    delta_delta = np.diff(deltas, axis=0)
    delta_delta_l2 = np.linalg.norm(delta_delta, axis=1) if len(delta_delta) else np.asarray([0.0])
    return float(step_l2.mean()), float(step_l2.max()), float(delta_delta_l2.max())


def _make_candidate(
    *,
    candidate_id: int,
    family: str,
    base_action_sequence: np.ndarray,
    delta_sequence: np.ndarray,
    steer_delta: float,
    throttle_delta: float,
    brake_delta: float,
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
) -> SequenceCandidate:
    actions = np.clip(np.asarray(base_action_sequence, dtype=np.float32) + np.asarray(delta_sequence, dtype=np.float32), -1.0, 1.0)
    sequence_mean_l2, sequence_max_l2, max_delta_delta_l2 = sequence_trust_metrics(
        action_sequence=actions,
        base_action_sequence=base_action_sequence,
    )
    trust_region_ok = (
        sequence_max_l2 <= float(per_step_action_l2) + 1e-8
        and sequence_mean_l2 <= float(sequence_mean_l2_limit) + 1e-8
        and sequence_max_l2 <= float(sequence_max_l2_limit) + 1e-8
        and max_delta_delta_l2 <= float(max_delta_delta_l2_limit) + 1e-8
    )
    return SequenceCandidate(
        candidate_id=int(candidate_id),
        family=str(family),
        sequence_length=int(actions.shape[0]),
        steer_delta=float(steer_delta),
        throttle_delta=float(throttle_delta),
        brake_delta=float(brake_delta),
        action_sequence=actions.astype(np.float32),
        delta_sequence=np.asarray(delta_sequence, dtype=np.float32),
        sequence_mean_l2=sequence_mean_l2,
        sequence_max_l2=sequence_max_l2,
        max_delta_delta_l2=max_delta_delta_l2,
        trust_region_ok=bool(trust_region_ok),
    )


def build_sequence_candidates(
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
) -> list[SequenceCandidate]:
    base = np.asarray(base_action_sequence, dtype=np.float32)
    if base.ndim != 2 or base.shape[1] != 3:
        raise ValueError(f"base action sequence must have shape (K, 3), got {base.shape}")
    candidates: list[SequenceCandidate] = []
    candidate_id = 0
    for family in families:
        if family in {"constant_delta", "decay_pulse"}:
            scales = sequence_scales(base.shape[0], family)
            for steer_delta in steer_deltas:
                for brake_delta in brake_deltas:
                    for throttle_delta in throttle_deltas:
                        delta = np.asarray([steer_delta, throttle_delta, brake_delta], dtype=np.float32)
                        delta_sequence = scales[:, None] * delta[None, :]
                        candidates.append(
                            _make_candidate(
                                candidate_id=candidate_id,
                                family=family,
                                base_action_sequence=base,
                                delta_sequence=delta_sequence,
                                steer_delta=steer_delta,
                                throttle_delta=throttle_delta,
                                brake_delta=brake_delta,
                                per_step_action_l2=per_step_action_l2,
                                sequence_mean_l2_limit=sequence_mean_l2_limit,
                                sequence_max_l2_limit=sequence_max_l2_limit,
                                max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                            )
                        )
                        candidate_id += 1
        elif family == "brake_release_then_steer":
            for steer_delta in steer_deltas:
                if abs(float(steer_delta)) < 1e-12:
                    continue
                for brake_delta in brake_deltas:
                    if float(brake_delta) >= 0.0:
                        continue
                    delta_sequence = np.zeros_like(base, dtype=np.float32)
                    delta_sequence[: min(2, len(delta_sequence)), 2] = float(brake_delta)
                    delta_sequence[1:, 0] = float(steer_delta)
                    candidates.append(
                        _make_candidate(
                            candidate_id=candidate_id,
                            family=family,
                            base_action_sequence=base,
                            delta_sequence=delta_sequence,
                            steer_delta=steer_delta,
                            throttle_delta=0.0,
                            brake_delta=brake_delta,
                            per_step_action_l2=per_step_action_l2,
                            sequence_mean_l2_limit=sequence_mean_l2_limit,
                            sequence_max_l2_limit=sequence_max_l2_limit,
                            max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                        )
                    )
                    candidate_id += 1
        elif family == "steer_then_brake":
            for steer_delta in steer_deltas:
                if abs(float(steer_delta)) < 1e-12:
                    continue
                for brake_delta in brake_deltas:
                    if abs(float(brake_delta)) < 1e-12:
                        continue
                    delta_sequence = np.zeros_like(base, dtype=np.float32)
                    delta_sequence[: min(2, len(delta_sequence)), 0] = float(steer_delta)
                    delta_sequence[1:, 2] = float(brake_delta)
                    candidates.append(
                        _make_candidate(
                            candidate_id=candidate_id,
                            family=family,
                            base_action_sequence=base,
                            delta_sequence=delta_sequence,
                            steer_delta=steer_delta,
                            throttle_delta=0.0,
                            brake_delta=brake_delta,
                            per_step_action_l2=per_step_action_l2,
                            sequence_mean_l2_limit=sequence_mean_l2_limit,
                            sequence_max_l2_limit=sequence_max_l2_limit,
                            max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                        )
                    )
                    candidate_id += 1
        else:
            raise ValueError(f"unknown sequence candidate family: {family}")
    return candidates


def collect_base_action_sequence(
    *,
    model: ActorCritic,
    snapshot: OutcomeSnapshot,
    sequence_length: int,
    device: torch.device,
) -> np.ndarray:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
    actions: list[np.ndarray] = []
    terminated = False
    truncated = False
    for _ in range(int(sequence_length)):
        if terminated or truncated:
            if not actions:
                raise ValueError("snapshot terminated before any base action could be collected")
            actions.append(actions[-1].copy())
            continue
        action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        actions.append(np.asarray(action, dtype=np.float32).copy())
        obs, _, terminated, truncated, _ = env.step(action)
        hidden = next_hidden
    return np.asarray(actions, dtype=np.float32)


def rollout_sequence_override(
    *,
    model: ActorCritic,
    snapshot: OutcomeSnapshot,
    action_sequence: np.ndarray,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
    actions = np.clip(np.asarray(action_sequence, dtype=np.float32), -1.0, 1.0)
    if actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"action sequence must have shape (K, 3), got {actions.shape}")
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env.config.max_steps - int(snapshot.step))

    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    executed_prefix_steps = 0

    for action in actions:
        if terminated or truncated or len(rewards) >= max_steps:
            break
        _, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        hidden = next_hidden
        executed_prefix_steps += 1

    while not (terminated or truncated) and len(rewards) < max_steps:
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
    reason = terminal_reason(info, terminated, truncated, env.config)
    first_action = actions[0] if len(actions) else np.zeros(3, dtype=np.float32)
    return {
        "steps": int(len(rewards)),
        "prefix_steps": int(executed_prefix_steps),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
    }


def sequence_acceptance(
    *,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    trust_region_ok: bool,
    min_margin_improvement: float,
    min_risk_improvement: float,
) -> tuple[bool, str]:
    if not bool(trust_region_ok):
        return False, "outside_sequence_trust_region"
    if bool(candidate.get("collision", False)):
        return False, "candidate_collision"
    if bool(candidate.get("off_road", False)):
        return False, "candidate_off_road"
    if bool(candidate.get("spin_out", False)):
        return False, "candidate_spin_out"
    baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
    candidate_margin = _finite_float(candidate.get("min_clearance_margin"))
    margin_improvement = (
        candidate_margin - baseline_margin
        if np.isfinite(candidate_margin) and np.isfinite(baseline_margin)
        else float("nan")
    )
    risk_improvement = risk_score(baseline) - risk_score(candidate)
    if bool(baseline.get("collision", False)) and not bool(candidate.get("collision", False)):
        return True, "baseline_collision_avoided"
    if np.isfinite(margin_improvement) and margin_improvement >= float(min_margin_improvement):
        return True, "margin_improved"
    if np.isfinite(risk_improvement) and risk_improvement >= float(min_risk_improvement):
        return True, "risk_improved"
    return False, "insufficient_margin_or_risk_improvement"


def select_best_sequence(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in candidate_rows if bool(row.get("accepted", False))]
    if not accepted:
        return None
    return max(
        accepted,
        key=lambda row: (
            bool(row.get("baseline_collision", False)) and not bool(row.get("candidate_collision", False)),
            _finite_float(row.get("margin_improvement"), float("-inf")),
            _finite_float(row.get("risk_improvement"), float("-inf")),
            -_finite_float(row.get("sequence_mean_l2"), float("inf")),
        ),
    )


def _best_any_sequence(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidate_rows:
        raise ValueError("cannot choose from an empty candidate list")
    return max(
        candidate_rows,
        key=lambda row: (
            _finite_float(row.get("margin_improvement"), float("-inf")),
            _finite_float(row.get("risk_improvement"), float("-inf")),
            -_finite_float(row.get("sequence_mean_l2"), float("inf")),
        ),
    )


def write_sequence_target_corpus(
    *,
    output_npz: Path,
    observations: list[np.ndarray],
    normal_hidden: list[np.ndarray],
    variant_hidden: list[np.ndarray],
    target_action_sequences: list[np.ndarray],
    normal_base_action_sequences: list[np.ndarray],
    variant_base_actions: list[np.ndarray],
    weights: list[float],
    row_ids: list[int],
    source_indices: list[int],
    sequence_lengths: list[int],
) -> None:
    if not observations:
        raise ValueError("cannot write empty sequence target corpus")
    max_len = max(int(length) for length in sequence_lengths)

    def _pad_sequence(sequence: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        seq = np.asarray(sequence, dtype=np.float32)
        if seq.ndim != 2 or seq.shape[1] != 3:
            raise ValueError(f"expected (K, 3) sequence, got {seq.shape}")
        padded = np.zeros((max_len, 3), dtype=np.float32)
        mask = np.zeros(max_len, dtype=np.float32)
        padded[: seq.shape[0]] = seq
        mask[: seq.shape[0]] = 1.0
        return padded, mask

    padded_targets: list[np.ndarray] = []
    padded_bases: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    for target, base in zip(target_action_sequences, normal_base_action_sequences, strict=True):
        padded_target, mask = _pad_sequence(target)
        padded_base, _ = _pad_sequence(base)
        padded_targets.append(padded_target)
        padded_bases.append(padded_base)
        masks.append(mask)

    np.savez_compressed(
        output_npz,
        observation=np.asarray(observations, dtype=np.float32),
        normal_hidden=np.asarray(normal_hidden, dtype=np.float32),
        variant_hidden=np.asarray(variant_hidden, dtype=np.float32),
        target_action_sequence=np.asarray(padded_targets, dtype=np.float32),
        normal_base_action_sequence=np.asarray(padded_bases, dtype=np.float32),
        sequence_mask=np.asarray(masks, dtype=np.float32),
        variant_base_action=np.asarray(variant_base_actions, dtype=np.float32),
        weight=np.asarray(weights, dtype=np.float32),
        row_id=np.asarray(row_ids, dtype=np.int64),
        source_index=np.asarray(source_indices, dtype=np.int64),
        sequence_length=np.asarray(sequence_lengths, dtype=np.int64),
    )


def mine_sequences_for_surface(
    *,
    model: ActorCritic,
    env_config_path: Path,
    rows: pd.DataFrame,
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
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, list[np.ndarray]]]:
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=request_steps_for_target_rows(rows, delay_steps=delay_steps),
        device=device,
    )
    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    unaccepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observations": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "target_action_sequences": [],
        "normal_base_action_sequences": [],
        "variant_base_actions": [],
    }
    accepted_sequences: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    for _, row in rows.reset_index(drop=True).iterrows():
        source_index = int(row["source_index"])
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        normal_hidden = left.hidden.detach().clone()
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
        row_candidate_rows: list[dict[str, Any]] = []
        candidate_id_offset = 0
        candidate_by_id: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        for sequence_length in sequence_lengths:
            base_sequence = baseline_sequence[: int(sequence_length)]
            for candidate in build_sequence_candidates(
                base_sequence,
                steer_deltas=steer_deltas,
                throttle_deltas=throttle_deltas,
                brake_deltas=brake_deltas,
                families=families,
                per_step_action_l2=per_step_action_l2,
                sequence_mean_l2_limit=sequence_mean_l2_limit,
                sequence_max_l2_limit=sequence_max_l2_limit,
                max_delta_delta_l2_limit=max_delta_delta_l2_limit,
            ):
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
                candidate_row = {
                    "source_index": source_index,
                    "coupling_row_index": int(row["coupling_row_index"]),
                    "candidate_id": candidate_id,
                    "family": candidate.family,
                    "sequence_length": int(candidate.sequence_length),
                    "surface": str(row["surface"]),
                    "target": str(row["target"]),
                    "variant": str(row["variant"]),
                    "left_seed": int(row["left_seed"]),
                    "right_seed": int(row["right_seed"]),
                    "left_step": int(row["left_step"]),
                    "right_step": int(row["right_step"]),
                    "capability_z_distance": float(row["capability_z_distance"]),
                    "action_distance": float(row["action_distance"]),
                    "coupling_gap": float(row["coupling_gap"]),
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
                    "sequence_mean_l2": float(candidate.sequence_mean_l2),
                    "sequence_max_l2": float(candidate.sequence_max_l2),
                    "max_delta_delta_l2": float(candidate.max_delta_delta_l2),
                    "accepted": bool(accepted),
                    "rejection_reason": rejection_reason,
                    **source_metadata(row),
                }
                candidate_rows.append(candidate_row)
                row_candidate_rows.append(candidate_row)
                candidate_by_id[candidate_id] = (candidate.action_sequence.copy(), base_sequence.copy())
            candidate_id_offset += len(
                build_sequence_candidates(
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
            )

        best = select_best_sequence(row_candidate_rows)
        if best is None:
            best_any = _best_any_sequence(row_candidate_rows)
            unaccepted_rows.append(
                {
                    "source_index": source_index,
                    "coupling_row_index": int(row["coupling_row_index"]),
                    "surface": str(row["surface"]),
                    "target": str(row["target"]),
                    "variant": str(row["variant"]),
                    "left_seed": int(row["left_seed"]),
                    "right_seed": int(row["right_seed"]),
                    "left_step": int(row["left_step"]),
                    "right_step": int(row["right_step"]),
                    "capability_z_distance": float(row["capability_z_distance"]),
                    "action_distance": float(row["action_distance"]),
                    "coupling_gap": float(row["coupling_gap"]),
                    "baseline_margin": float(best_any["baseline_margin"]),
                    "baseline_risk_score": float(best_any["baseline_risk_score"]),
                    "best_candidate_id": int(best_any["candidate_id"]),
                    "best_family": str(best_any["family"]),
                    "best_sequence_length": int(best_any["sequence_length"]),
                    "best_margin": float(best_any["candidate_margin"]),
                    "best_margin_improvement": float(best_any["margin_improvement"]),
                    "best_risk_improvement": float(best_any["risk_improvement"]),
                    "best_sequence_mean_l2": float(best_any["sequence_mean_l2"]),
                    "best_sequence_max_l2": float(best_any["sequence_max_l2"]),
                    "best_max_delta_delta_l2": float(best_any["max_delta_delta_l2"]),
                    "best_rejection_reason": str(best_any["rejection_reason"]),
                    **source_metadata(row),
                }
            )
            continue

        accepted_rows.append(
            {
                "source_index": source_index,
                "coupling_row_index": int(row["coupling_row_index"]),
                "candidate_id": int(best["candidate_id"]),
                "family": str(best["family"]),
                "sequence_length": int(best["sequence_length"]),
                "surface": str(row["surface"]),
                "target": str(row["target"]),
                "variant": str(row["variant"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "capability_z_distance": float(row["capability_z_distance"]),
                "action_distance": float(row["action_distance"]),
                "coupling_gap": float(row["coupling_gap"]),
                "baseline_margin": float(best["baseline_margin"]),
                "target_margin": float(best["candidate_margin"]),
                "margin_improvement": float(best["margin_improvement"]),
                "baseline_risk_score": float(best["baseline_risk_score"]),
                "target_risk_score": float(best["candidate_risk_score"]),
                "risk_improvement": float(best["risk_improvement"]),
                "sequence_mean_l2": float(best["sequence_mean_l2"]),
                "sequence_max_l2": float(best["sequence_max_l2"]),
                "max_delta_delta_l2": float(best["max_delta_delta_l2"]),
                "acceptance_reason": str(best["rejection_reason"]),
                **source_metadata(row),
            }
        )
        accepted_sequences[source_index] = candidate_by_id[int(best["candidate_id"])]
        target_sequence, base_sequence = accepted_sequences[source_index]
        corpus["observations"].append(np.asarray(left.observation, dtype=np.float32).copy())
        corpus["normal_hidden"].append(_hidden_array(normal_hidden))
        corpus["variant_hidden"].append(_hidden_array(variant_hidden))
        corpus["target_action_sequences"].append(target_sequence)
        corpus["normal_base_action_sequences"].append(base_sequence)
        corpus["variant_base_actions"].append(np.asarray(variant_base_action, dtype=np.float32).copy())

    weights = source_diversity_weights(accepted_rows)
    for accepted_row in accepted_rows:
        accepted_row["weight"] = float(
            weights.get(int(accepted_row["source_index"]), 1.0)
            * min(4.0, max(1.0, _finite_float(accepted_row["margin_improvement"], 0.0) / max(min_margin_improvement, 1e-9)))
        )
    return candidate_rows, accepted_rows, unaccepted_rows, corpus


def run_sequence_target_miner(
    *,
    checkpoint_path: Path,
    boundary_source_rows_csv: Path,
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
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    source_rows = load_boundary_source_rows(boundary_source_rows_csv)
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(source_rows["surface"].astype(str)).difference(surface_config_by_name)) if not source_rows.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    unaccepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observations": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "target_action_sequences": [],
        "normal_base_action_sequences": [],
        "variant_base_actions": [],
    }
    for surface, surface_rows in source_rows.groupby("surface", observed=True):
        surface_candidate_rows, surface_accepted_rows, surface_unaccepted_rows, surface_corpus = mine_sequences_for_surface(
            model=model,
            env_config_path=surface_config_by_name[str(surface)],
            rows=surface_rows.reset_index(drop=True),
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
        candidate_rows.extend(surface_candidate_rows)
        accepted_rows.extend(surface_accepted_rows)
        unaccepted_rows.extend(surface_unaccepted_rows)
        for key, values in surface_corpus.items():
            corpus[key].extend(values)

    target_corpus_path: Path | None = None
    if accepted_rows:
        target_corpus_path = run_dir / "sequence_target_corpus.npz"
        write_sequence_target_corpus(
            output_npz=target_corpus_path,
            observations=corpus["observations"],
            normal_hidden=corpus["normal_hidden"],
            variant_hidden=corpus["variant_hidden"],
            target_action_sequences=corpus["target_action_sequences"],
            normal_base_action_sequences=corpus["normal_base_action_sequences"],
            variant_base_actions=corpus["variant_base_actions"],
            weights=[float(row["weight"]) for row in accepted_rows],
            row_ids=list(range(len(accepted_rows))),
            source_indices=[int(row["source_index"]) for row in accepted_rows],
            sequence_lengths=[int(row["sequence_length"]) for row in accepted_rows],
        )

    write_csv_rows(run_dir / "selected_boundary_source_rows.csv", source_rows.to_dict(orient="records"))
    accepted_candidate_output_rows = accepted_candidate_rows(candidate_rows)
    write_csv_rows(run_dir / "sequence_candidates.csv", candidate_rows, fieldnames=SEQUENCE_CANDIDATE_FIELDNAMES)
    write_csv_rows(
        run_dir / "accepted_candidate_sequences.csv",
        accepted_candidate_output_rows,
        fieldnames=SEQUENCE_CANDIDATE_FIELDNAMES,
    )
    write_csv_rows(run_dir / "accepted_sequences.csv", accepted_rows, fieldnames=ACCEPTED_SEQUENCE_FIELDNAMES)
    write_csv_rows(run_dir / "unaccepted_rows.csv", unaccepted_rows, fieldnames=UNACCEPTED_SEQUENCE_FIELDNAMES)

    candidate_frame = pd.DataFrame(candidate_rows)
    accepted_candidate_frame = pd.DataFrame(accepted_candidate_output_rows)
    accepted_frame = pd.DataFrame(accepted_rows)
    unaccepted_frame = pd.DataFrame(unaccepted_rows)
    summary = {
        "run_type": "sequence_target_miner",
        "checkpoint": checkpoint_path,
        "boundary_source_rows_csv": boundary_source_rows_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "source_row_diversity": _diversity(source_rows),
        "accepted_sequence_diversity": _diversity(accepted_frame),
        "sequence_lengths": sequence_lengths,
        "families": families,
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "delay_steps": int(delay_steps),
        "per_step_action_l2": float(per_step_action_l2),
        "sequence_mean_l2_limit": float(sequence_mean_l2_limit),
        "sequence_max_l2_limit": float(sequence_max_l2_limit),
        "max_delta_delta_l2_limit": float(max_delta_delta_l2_limit),
        "min_margin_improvement": float(min_margin_improvement),
        "min_risk_improvement": float(min_risk_improvement),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolved_device),
        "source_rows": int(len(source_rows)),
        "candidate_rollouts": int(len(candidate_rows)),
        "accepted_candidate_sequences": int(len(accepted_candidate_output_rows)),
        "accepted_sequences": int(len(accepted_rows)),
        "unaccepted_rows": int(len(unaccepted_rows)),
        "candidate_margin_improvement_max": _empty_float_stat(candidate_frame, "margin_improvement", "max"),
        "candidate_margin_improvement_mean": _empty_float_stat(candidate_frame, "margin_improvement", "mean"),
        "candidate_risk_improvement_max": _empty_float_stat(candidate_frame, "risk_improvement", "max"),
        "candidate_risk_improvement_mean": _empty_float_stat(candidate_frame, "risk_improvement", "mean"),
        "accepted_margin_improvement_mean": _empty_float_stat(accepted_frame, "margin_improvement", "mean"),
        "accepted_margin_improvement_min": _empty_float_stat(accepted_frame, "margin_improvement", "min"),
        "accepted_margin_improvement_max": _empty_float_stat(accepted_frame, "margin_improvement", "max"),
        "best_unaccepted_margin_improvement": _empty_float_stat(unaccepted_frame, "best_margin_improvement", "max"),
        "best_unaccepted_risk_improvement": _empty_float_stat(unaccepted_frame, "best_risk_improvement", "max"),
        "candidate_rejection_counts": (
            candidate_frame[~candidate_frame["accepted"].astype(bool)]["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "candidate_acceptance_reason_counts": (
            candidate_frame[candidate_frame["accepted"].astype(bool)]["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "accepted_candidate_diversity": _diversity(accepted_candidate_frame),
        "accepted_candidate_counts_by_family": _value_counts(accepted_candidate_frame, "family"),
        "accepted_candidate_counts_by_tier": _value_counts(accepted_candidate_frame, "source_tier"),
        "accepted_candidate_counts_by_sequence_length": _value_counts(accepted_candidate_frame, "sequence_length"),
        "accepted_sequence_counts_by_family": (
            accepted_frame["family"].value_counts().to_dict()
            if not accepted_frame.empty
            else {}
        ),
        "accepted_sequence_counts_by_tier": _value_counts(accepted_frame, "source_tier"),
        "diagnostic_only": True,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "sequence_target_corpus_npz": target_corpus_path,
        "sequence_candidates_csv": run_dir / "sequence_candidates.csv",
        "accepted_candidate_sequences_csv": run_dir / "accepted_candidate_sequences.csv",
        "accepted_sequences_csv": run_dir / "accepted_sequences.csv",
        "unaccepted_rows_csv": run_dir / "unaccepted_rows.csv",
        "selected_boundary_source_rows_csv": run_dir / "selected_boundary_source_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine diagnostic action-sequence targets.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--boundary-source-rows", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(3, 5))
    parser.add_argument("--family", type=str, action="append", default=None)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.08, -0.04, 0.0, 0.04, 0.08))
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
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    families = tuple(args.family or ("constant_delta", "decay_pulse", "brake_release_then_steer", "steer_then_brake"))
    run_dir = args.run_dir or make_run_dir(prefix="sequence_target_miner")
    summary = run_sequence_target_miner(
        checkpoint_path=args.checkpoint_policy.path,
        boundary_source_rows_csv=args.boundary_source_rows,
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
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
