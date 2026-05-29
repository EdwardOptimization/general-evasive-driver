"""Bounded measured source mining for fresh ambiguity probes.

The module runs fixed-policy public traces and writes measured pairing artifacts.
It still does not materialize candidates, export a training corpus, train, run
PPO, promote checkpoints, use private holdout, or change actor inputs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import (
    DEFAULT_CHECKPOINT,
    assert_p0_env_contract,
    assert_p0_model_contract,
    hidden_stats,
    phase_for_step,
)
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec, env_config_for_hook_spec
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy
from autodrift.fresh_ambiguity_source_mining import (
    FreshAmbiguitySourceRow,
    default_source_specs,
    expand_source_specs,
    row_id as source_row_id,
)


DEFAULT_RUN_DIR = Path("runs/m1531_fresh_ambiguity_measured_mining_smoke")
DEFAULT_MAX_ROLLOUT_STEPS = 128
SNAPSHOT_KINDS = ("reveal", "reveal_plus_4", "decision_minus_8", "decision", "post_decision_plus_8")
GUARDRAIL_KEYS = (
    "candidate_materialized",
    "training_started",
    "evaluation_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "training_corpus_exported",
    "labels_enter_actor_input",
    "level3_self_id_claim_made",
)


@dataclass(frozen=True)
class MeasuredTraceRow:
    """One measured fixed-policy trace step."""

    trace_id: str
    source_row_id: str
    source_family: str
    task_family: str
    seed: int
    hidden_capability_pair: str
    geometry_key: str
    simulator_scope: str
    proxy_fault_family: bool
    closed_t5_subset: bool
    reveal_step: int
    decision_step: int
    step: int
    phase: str
    observation_dim: int
    response_checksum: float
    context_checksum: float
    action_steer: float
    action_throttle: float
    action_brake: float
    hidden_norm: float
    hidden_checksum: float
    reward: float
    terminated: bool
    truncated: bool
    obstacle_label: str
    active_obstacle_body_x: float
    active_obstacle_body_y: float
    min_clearance_margin: float
    collision: bool
    obstacle_completed: bool
    terminal_reason: str


@dataclass(frozen=True)
class MeasuredSnapshotRow:
    """Compact measured snapshot used for pair mining."""

    trace_id: str
    source_row_id: str
    source_family: str
    task_family: str
    seed: int
    snapshot_kind: str
    step: int
    response_vector: tuple[float, ...]
    context_vector: tuple[float, ...]
    action_vector: tuple[float, float, float]
    hidden_norm: float
    hidden_checksum: float
    min_clearance_margin: float
    collision: bool
    obstacle_completed: bool
    terminal_reason: str


@dataclass(frozen=True)
class MeasuredPairCandidate:
    """Measured pair candidate before any DecisiveHistoryTaskCandidate export."""

    pair_id: str
    left_trace_id: str
    right_trace_id: str
    left_source_family: str
    right_source_family: str
    task_family: str
    scene_context_distance: float
    current_ego_distance: float
    recent_window_distance: float
    older_evidence_distance: float
    hidden_capability_distance: float
    first_action_l2: float
    prefix_action_l2: float
    terminal_margin_gap: float
    accepted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MeasuredInterventionRow:
    """Measured continuation placeholder row.

    M1531 records measured normal-continuation facts only. Wrong-history and
    donor-response interventions remain a later audit/implementation decision.
    """

    pair_id: str
    variant: str
    continuation_executed: bool
    terminal_margin_gap: float
    success_drop: bool
    note: str


@dataclass(frozen=True)
class SourceAttemptRow:
    """Summary for one measured source trace attempt."""

    trace_id: str
    source_family: str
    task_family: str
    seed: int
    rows: int
    reached_reveal: bool
    reached_decision: bool
    reached_post_decision: bool
    failure_type: str
    terminal_reason: str
    error_type: str = ""
    error_message: str = ""


def canonical_env_family(source_family: str) -> str:
    """Map fresh source families to existing P0-compatible env hook templates."""

    if source_family in {
        "t4_staged_warmup_capability",
        "t4_capability_step_temporal",
        "t4_actuator_delay_response",
        "t5_near_boundary_warmup",
        "t5_high_speed_close_obstacle",
        "t5_boundary_axis_retarget",
    }:
        return source_family
    if source_family in {"capability_step_down", "capability_step_up"}:
        return "t4_capability_step_temporal"
    if source_family == "actuator_delay_step":
        return "t4_actuator_delay_response"
    if source_family in {"brake_fade_or_loss_proxy", "grip_loss_proxy", "late_reveal_boundary"}:
        return "t5_high_speed_close_obstacle"
    if source_family in {"drive_loss_proxy", "curved_boundary_obstacle"}:
        return "t5_boundary_axis_retarget"
    return "t5_near_boundary_warmup" if source_family.startswith("t5") else "t4_capability_step_temporal"


def _proxy_adjusted_env_config(row: FreshAmbiguitySourceRow) -> DriftEnvConfig:
    canonical = canonical_env_family(row.source_family)
    config = env_config_for_hook_spec(
        source_family=canonical,
        capability_pair=row.hidden_capability_pair,
        reveal_step=int(row.reveal_step),
    )
    randomization = config.randomization
    if row.source_family in {"capability_step_down", "grip_loss_proxy"}:
        randomization = replace(
            randomization,
            mu_range=(0.22, min(0.70, float(randomization.mu_range[1]))),
            tire_stiffness_scale_range=(0.45, min(0.95, float(randomization.tire_stiffness_scale_range[1]))),
        )
    elif row.source_family == "brake_fade_or_loss_proxy":
        randomization = replace(
            randomization,
            brake_scale_range=(0.25, min(0.75, float(randomization.brake_scale_range[1]))),
        )
    elif row.source_family == "drive_loss_proxy":
        randomization = replace(
            randomization,
            drive_scale_range=(0.20, min(0.75, float(randomization.drive_scale_range[1]))),
        )
    elif row.source_family in {"actuator_delay_step", "t4_actuator_delay_response"}:
        randomization = replace(
            randomization,
            actuator_tau_scale_range=(max(1.5, float(randomization.actuator_tau_scale_range[0])), 4.5),
        )
    elif row.source_family == "capability_step_up":
        randomization = replace(
            randomization,
            mu_range=(0.35, max(1.05, float(randomization.mu_range[1]))),
            brake_scale_range=(0.55, max(1.25, float(randomization.brake_scale_range[1]))),
        )
    return replace(config, randomization=randomization)


def source_row_to_hook_spec(row: FreshAmbiguitySourceRow) -> DecisiveHistoryEnvHookSpec:
    """Convert one M1528 fresh source row to a runnable P0 env hook spec."""

    env_config = _proxy_adjusted_env_config(row)
    assert_p0_env_contract(env_config)
    return DecisiveHistoryEnvHookSpec(
        source_family=row.source_family,
        task_family=row.task_family,
        seed=int(row.seed),
        candidate_id=f"fresh-{row.source_family}-{row.source_index:03d}",
        capability_pair=row.hidden_capability_pair,
        geometry_key=row.geometry_key,
        reveal_step=int(row.reveal_step),
        decision_step=int(row.decision_step),
        env_config=env_config,
        warmup_mode="fresh_ambiguity_measured",
        capability_variant=row.hidden_capability_pair.replace("|", "_vs_"),
        obstacle_variant=row.geometry_key,
        labels_enter_actor_input=False,
        candidate_materialized=False,
        simulator_rollout_started=True,
    )


def _checksum(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.sum(np.round(values.astype(np.float64, copy=False), 6)))


def _terminal_reason(info: dict[str, Any], terminated: bool, truncated: bool, exhausted: bool) -> str:
    if bool(info.get("collision", False)):
        return "collision"
    if bool(info.get("obstacle_completed", False)):
        return "obstacle_completed"
    if truncated:
        return "truncated"
    if terminated:
        return "terminated"
    if exhausted:
        return "max_rollout_steps"
    return "running"


def _target_steps(reveal_step: int, decision_step: int) -> dict[str, int]:
    return {
        "reveal": int(reveal_step),
        "reveal_plus_4": int(reveal_step) + 4,
        "decision_minus_8": max(int(reveal_step), int(decision_step) - 8),
        "decision": int(decision_step),
        "post_decision_plus_8": int(decision_step) + 8,
    }


def run_measured_trace(
    row: FreshAmbiguitySourceRow,
    policy: ActorPolicy,
    *,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
) -> tuple[list[MeasuredTraceRow], list[MeasuredSnapshotRow], SourceAttemptRow]:
    """Run one fixed-policy measured trace from a fresh source row."""

    spec = source_row_to_hook_spec(row)
    trace_id = f"{spec.source_family}|{spec.seed}|{spec.candidate_id}"
    rows: list[MeasuredTraceRow] = []
    snapshot_rows: list[MeasuredSnapshotRow] = []
    pending_snapshots = _target_steps(int(spec.reveal_step), int(spec.decision_step))
    captured: set[str] = set()
    try:
        env = AutoDriftEnv(spec.env_config)
        observation, info = env.reset(seed=int(spec.seed))
        policy.env_config = spec.env_config
        policy.reset()
        terminated = False
        truncated = False
        for _ in range(int(max_rollout_steps)):
            obs_array = np.asarray(observation, dtype=np.float64)
            if not np.all(np.isfinite(obs_array)):
                raise ValueError("nonfinite_observation")
            step = int(info.get("step", len(rows)))
            action = np.asarray(policy.act(observation, info), dtype=np.float64)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            hidden_norm, hidden_checksum = hidden_stats(policy.hidden)
            response = obs_array[:12]
            context = obs_array[12:]
            next_observation, reward, terminated, truncated, next_info = env.step(action)
            terminal = _terminal_reason(next_info, bool(terminated), bool(truncated), exhausted=False)
            trace_row = MeasuredTraceRow(
                trace_id=trace_id,
                source_row_id=source_row_id(row),
                source_family=spec.source_family,
                task_family=spec.task_family,
                seed=int(spec.seed),
                hidden_capability_pair=spec.capability_pair,
                geometry_key=spec.geometry_key,
                simulator_scope=row.simulator_scope,
                proxy_fault_family=bool(row.proxy_fault_family),
                closed_t5_subset=bool(row.closed_t5_subset),
                reveal_step=int(spec.reveal_step),
                decision_step=int(spec.decision_step),
                step=step,
                phase=phase_for_step(step, int(spec.reveal_step), int(spec.decision_step), terminal=terminated or truncated),
                observation_dim=int(obs_array.shape[0]),
                response_checksum=_checksum(response),
                context_checksum=_checksum(context),
                action_steer=float(action[0]),
                action_throttle=float(action[1]),
                action_brake=float(action[2]),
                hidden_norm=float(hidden_norm),
                hidden_checksum=float(hidden_checksum),
                reward=float(reward),
                terminated=bool(terminated),
                truncated=bool(truncated),
                obstacle_label=str(next_info.get("obstacle_label", "")),
                active_obstacle_body_x=float(next_info.get("active_obstacle_body_x", float("nan"))),
                active_obstacle_body_y=float(next_info.get("active_obstacle_body_y", float("nan"))),
                min_clearance_margin=float(next_info.get("min_clearance_margin", float("nan"))),
                collision=bool(next_info.get("collision", False)),
                obstacle_completed=bool(next_info.get("obstacle_completed", False)),
                terminal_reason=terminal,
            )
            rows.append(trace_row)
            for kind, target_step in pending_snapshots.items():
                if kind in captured or step < target_step:
                    continue
                captured.add(kind)
                snapshot_rows.append(
                    MeasuredSnapshotRow(
                        trace_id=trace_id,
                        source_row_id=source_row_id(row),
                        source_family=spec.source_family,
                        task_family=spec.task_family,
                        seed=int(spec.seed),
                        snapshot_kind=kind,
                        step=step,
                        response_vector=tuple(float(value) for value in response),
                        context_vector=tuple(float(value) for value in context),
                        action_vector=(float(action[0]), float(action[1]), float(action[2])),
                        hidden_norm=float(hidden_norm),
                        hidden_checksum=float(hidden_checksum),
                        min_clearance_margin=float(trace_row.min_clearance_margin),
                        collision=bool(trace_row.collision),
                        obstacle_completed=bool(trace_row.obstacle_completed),
                        terminal_reason=terminal,
                    )
                )
            observation = next_observation
            info = next_info
            if terminated or truncated:
                break
    except Exception as exc:
        return rows, snapshot_rows, SourceAttemptRow(
            trace_id=trace_id,
            source_family=spec.source_family,
            task_family=spec.task_family,
            seed=int(spec.seed),
            rows=len(rows),
            reached_reveal=any(item.step >= spec.reveal_step for item in rows),
            reached_decision=any(item.step >= spec.decision_step for item in rows),
            reached_post_decision=any(item.step > spec.decision_step for item in rows),
            failure_type="rollout_exception" if rows else "reset_failure",
            terminal_reason=rows[-1].terminal_reason if rows else "exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    exhausted = bool(rows) and not bool(rows[-1].terminated or rows[-1].truncated)
    terminal_reason = _terminal_reason({}, False, False, exhausted) if exhausted else rows[-1].terminal_reason
    reached_reveal = any(item.step >= spec.reveal_step for item in rows)
    reached_decision = any(item.step >= spec.decision_step for item in rows)
    reached_post = any(item.step > spec.decision_step for item in rows)
    failure = "none"
    if not reached_reveal:
        failure = "did_not_reach_reveal_step"
    elif not reached_decision:
        failure = "did_not_reach_decision_step"
    return rows, snapshot_rows, SourceAttemptRow(
        trace_id=trace_id,
        source_family=spec.source_family,
        task_family=spec.task_family,
        seed=int(spec.seed),
        rows=len(rows),
        reached_reveal=reached_reveal,
        reached_decision=reached_decision,
        reached_post_decision=reached_post,
        failure_type=failure,
        terminal_reason=terminal_reason,
    )


def _vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    left_arr = np.asarray(left, dtype=np.float64)
    right_arr = np.asarray(right, dtype=np.float64)
    if left_arr.size == 0 or right_arr.size == 0 or left_arr.shape != right_arr.shape:
        return float("inf")
    return float(np.linalg.norm(left_arr - right_arr) / np.sqrt(float(left_arr.size)))


def _action_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))


def build_pair_candidates(snapshots: Sequence[MeasuredSnapshotRow], *, max_pairs: int = 64) -> list[MeasuredPairCandidate]:
    """Build measured same-anchor nearest-neighbor pair candidates."""

    decision_rows = [row for row in snapshots if row.snapshot_kind == "decision"]
    pairs: list[MeasuredPairCandidate] = []
    seen: set[tuple[str, str]] = set()
    for left in decision_rows:
        candidates = [
            right
            for right in decision_rows
            if right.trace_id != left.trace_id
            and right.task_family == left.task_family
            and right.source_family != left.source_family
        ]
        if not candidates:
            continue
        right = min(
            candidates,
            key=lambda item: _vector_distance(left.context_vector, item.context_vector)
            + _vector_distance(left.response_vector, item.response_vector),
        )
        key = tuple(sorted((left.trace_id, right.trace_id)))
        if key in seen:
            continue
        seen.add(key)
        scene_distance = _vector_distance(left.context_vector, right.context_vector)
        current_distance = _vector_distance(left.response_vector, right.response_vector)
        action_l2 = _action_distance(left.action_vector, right.action_vector)
        margin_gap = abs(float(left.min_clearance_margin) - float(right.min_clearance_margin))
        hidden_gap = abs(float(left.hidden_norm) - float(right.hidden_norm))
        reasons: list[str] = []
        if scene_distance > 0.10:
            reasons.append("scene_context_distance_too_large")
        if current_distance > 0.10:
            reasons.append("current_ego_distance_too_large")
        if action_l2 < 0.04:
            reasons.append("first_action_l2_too_small")
        if margin_gap < 0.02:
            reasons.append("terminal_margin_gap_too_small")
        pairs.append(
            MeasuredPairCandidate(
                pair_id=f"pair-{len(pairs):04d}",
                left_trace_id=left.trace_id,
                right_trace_id=right.trace_id,
                left_source_family=left.source_family,
                right_source_family=right.source_family,
                task_family=left.task_family,
                scene_context_distance=scene_distance,
                current_ego_distance=current_distance,
                recent_window_distance=current_distance,
                older_evidence_distance=hidden_gap,
                hidden_capability_distance=hidden_gap,
                first_action_l2=action_l2,
                prefix_action_l2=action_l2,
                terminal_margin_gap=margin_gap,
                accepted=not reasons,
                reasons=tuple(reasons),
            )
        )
        if len(pairs) >= int(max_pairs):
            break
    return pairs


def build_intervention_rows(pairs: Sequence[MeasuredPairCandidate]) -> list[MeasuredInterventionRow]:
    """Write measured normal rows only; history interventions require later audit."""

    return [
        MeasuredInterventionRow(
            pair_id=pair.pair_id,
            variant="normal_measured_pair",
            continuation_executed=True,
            terminal_margin_gap=float(pair.terminal_margin_gap),
            success_drop=False,
            note="normal measured pair only; wrong-history interventions not executed in M1531 smoke",
        )
        for pair in pairs
    ]


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [dict(row.__dict__) for row in rows]


def _csv_ready(rows: Sequence[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in _asdict_rows(rows):
        converted = dict(row)
        if "response_vector" in converted:
            converted["response_vector"] = "|".join(f"{float(value):.8g}" for value in converted["response_vector"])
        if "context_vector" in converted:
            converted["context_vector"] = "|".join(f"{float(value):.8g}" for value in converted["context_vector"])
        if "action_vector" in converted:
            converted["action_vector"] = "|".join(f"{float(value):.8g}" for value in converted["action_vector"])
        if "reasons" in converted:
            converted["reasons"] = "|".join(converted["reasons"])
        result.append(converted)
    return result


def _guardrail_summary() -> dict[str, bool]:
    return {
        "candidate_materialized": False,
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "training_corpus_exported": False,
        "labels_enter_actor_input": False,
        "level3_self_id_claim_made": False,
    }


def build_measured_summary(
    *,
    checkpoint: Path | str,
    source_rows: Sequence[FreshAmbiguitySourceRow],
    traces: Sequence[MeasuredTraceRow],
    snapshots: Sequence[MeasuredSnapshotRow],
    attempts: Sequence[SourceAttemptRow],
    pairs: Sequence[MeasuredPairCandidate],
    interventions: Sequence[MeasuredInterventionRow],
    max_rollout_steps: int,
) -> dict[str, Any]:
    """Summarize bounded measured mining smoke."""

    guardrails = _guardrail_summary()
    attempted_families = {row.source_family for row in attempts}
    reached_reveal = {row.source_family for row in attempts if row.reached_reveal}
    reached_decision = {row.source_family for row in attempts if row.reached_decision}
    family_counts = Counter(row.source_family for row in attempts)
    closed_t5 = sum(1 for row in source_rows if row.closed_t5_subset)
    proxy_fault_families = {row.source_family for row in source_rows if row.proxy_fault_family}
    total_sources = len(source_rows)
    max_family_share = (max(family_counts.values(), default=0) / len(attempts)) if attempts else 0.0
    accepted_pairs = [row for row in pairs if row.accepted]
    return {
        "result_class": "fresh_ambiguity_measured_mining_smoke",
        "checkpoint": str(checkpoint),
        "source_row_count": total_sources,
        "attempted_source_families": len(attempted_families),
        "reached_reveal_source_families": len(reached_reveal),
        "reached_decision_source_families": len(reached_decision),
        "trace_row_count": len(traces),
        "snapshot_row_count": len(snapshots),
        "measured_pair_candidate_count": len(pairs),
        "accepted_measured_pair_count": len(accepted_pairs),
        "intervention_row_count": len(interventions),
        "max_rollout_steps": int(max_rollout_steps),
        "max_single_source_family_share": float(max_family_share),
        "closed_t5_subset_rows": closed_t5,
        "max_closed_t5_subset_share": float(closed_t5 / total_sources) if total_sources else 0.0,
        "proxy_fault_family_count": len(proxy_fault_families),
        "proxy_fault_families": sorted(proxy_fault_families),
        "target_replay_failure_count": sum(1 for row in attempts if row.failure_type != "none"),
        "donor_replay_failure_count": 0,
        "failure_type_counts": dict(sorted(Counter(row.failure_type for row in attempts).items())),
        "source_families_attempted": sorted(attempted_families),
        "source_families_reached_decision": sorted(reached_decision),
        "history_interventions_executed": False,
        "guardrails": guardrails,
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        "passes_public_smoke_gates": (
            len(attempted_families) >= 8
            and len(reached_decision) >= 4
            and len(proxy_fault_families) >= 3
            and (float(closed_t5 / total_sources) if total_sources else 1.0) <= 0.20
            and sum(1 for value in guardrails.values() if bool(value)) == 0
        ),
        "passes_evidence_quality_targets": (
            len(pairs) >= 8
            and len(accepted_pairs) >= 2
            and any(row.accepted and row.left_source_family != "t5_high_speed_close_obstacle" for row in pairs)
            and False
        ),
        **guardrails,
    }


def run_measured_mining_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1531,
    seed_count: int = 1,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
    max_pair_candidates: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded measured source mining and write audit artifacts."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_rows = expand_source_specs(default_source_specs(seed=seed, seed_count=seed_count))
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, DriftEnvConfig())

    traces: list[MeasuredTraceRow] = []
    snapshots: list[MeasuredSnapshotRow] = []
    attempts: list[SourceAttemptRow] = []
    for source_row in source_rows:
        trace_rows, snapshot_rows, attempt = run_measured_trace(
            source_row,
            policy,
            max_rollout_steps=max_rollout_steps,
        )
        traces.extend(trace_rows)
        snapshots.extend(snapshot_rows)
        attempts.append(attempt)

    pairs = build_pair_candidates(snapshots, max_pairs=max_pair_candidates)
    interventions = build_intervention_rows(pairs)
    summary = build_measured_summary(
        checkpoint=checkpoint,
        source_rows=source_rows,
        traces=traces,
        snapshots=snapshots,
        attempts=attempts,
        pairs=pairs,
        interventions=interventions,
        max_rollout_steps=max_rollout_steps,
    )

    source_spec_rows = [
        {
            "source_row_id": source_row_id(row),
            "source_family": row.source_family,
            "task_family": row.task_family,
            "seed": row.seed,
            "hidden_capability_pair": row.hidden_capability_pair,
            "geometry_key": row.geometry_key,
            "simulator_scope": row.simulator_scope,
            "proxy_fault_family": row.proxy_fault_family,
            "closed_t5_subset": row.closed_t5_subset,
            "candidate_materialized": False,
            "labels_enter_actor_input": False,
        }
        for row in source_rows
    ]
    rejected_pairs = [pair for pair in pairs if not pair.accepted]
    family_summary = [
        {
            "source_family": family,
            "attempt_count": count,
            "reached_decision_count": sum(1 for row in attempts if row.source_family == family and row.reached_decision),
            "failure_count": sum(1 for row in attempts if row.source_family == family and row.failure_type != "none"),
        }
        for family, count in sorted(Counter(row.source_family for row in attempts).items())
    ]

    write_csv_rows(output / "measured_source_spec_rows.csv", source_spec_rows)
    write_csv_rows(output / "measured_trace_rows.csv", _csv_ready(traces))
    write_csv_rows(output / "measured_snapshot_rows.csv", _csv_ready(snapshots))
    write_csv_rows(output / "measured_pair_candidates.csv", _csv_ready(pairs))
    write_csv_rows(output / "measured_intervention_rows.csv", _csv_ready(interventions))
    write_csv_rows(output / "measured_rejected_pairs.csv", _csv_ready(rejected_pairs))
    write_csv_rows(output / "measured_source_family_summary.csv", family_summary)
    write_csv_rows(output / "measured_guardrail_summary.csv", [_guardrail_summary()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded measured fresh ambiguity source mining smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1531)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--max-rollout-steps", type=int, default=DEFAULT_MAX_ROLLOUT_STEPS)
    parser.add_argument("--max-pair-candidates", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_measured_mining_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_rollout_steps=int(args.max_rollout_steps),
        max_pair_candidates=int(args.max_pair_candidates),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"trace_row_count={summary['trace_row_count']}")
    print(f"measured_pair_candidate_count={summary['measured_pair_candidate_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
