"""Bounded fixed-policy source trace runner for decisive-history probes."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec, default_hook_specs
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS


DEFAULT_CHECKPOINT = Path("runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt")
DEFAULT_MAX_ROLLOUT_STEPS = 96
DEFAULT_RUN_DIR = Path("runs/m1511_decisive_history_bounded_runner_smoke")
SNAPSHOT_OFFSETS = (0, 8, 16)
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
class SourceTraceRow:
    """One bounded fixed-policy source trace step."""

    trace_id: str
    source_family: str
    task_family: str
    candidate_id: str
    seed: int
    capability_pair: str
    geometry_key: str
    reveal_step: int
    decision_step: int
    step: int
    phase: str
    terminated: bool
    truncated: bool
    reward: float
    action_steer: float
    action_throttle: float
    action_brake: float
    hidden_norm: float
    hidden_checksum: float
    observation_dim: int
    info_obstacle_label: str
    info_obstacle_distance: float
    info_obstacle_lateral_offset: float
    info_active_obstacle_body_x: float
    info_active_obstacle_body_y: float
    info_min_clearance_margin: float
    info_collision: bool
    info_obstacle_completed: bool
    info_warmup_gate_visible: bool
    info_warmup_gate_clearance_margin: float
    info_friction_step_at: int | None
    info_friction_step_applied: bool
    info_mu: float
    info_initial_mu: float
    info_brake_scale: float
    info_drive_scale: float
    info_steer_tau_scale: float


@dataclass(frozen=True)
class SourceSnapshotRow:
    """Compact source snapshot row for reveal/decision/terminal steps."""

    trace_id: str
    source_family: str
    task_family: str
    candidate_id: str
    seed: int
    snapshot_kind: str
    step: int
    phase: str
    action_steer: float
    action_throttle: float
    action_brake: float
    hidden_norm: float
    min_clearance_margin: float
    collision: bool
    obstacle_completed: bool
    terminal_reason: str


@dataclass(frozen=True)
class SourceAttemptSummary:
    """One source-family rollout attempt summary."""

    trace_id: str
    source_family: str
    task_family: str
    candidate_id: str
    seed: int
    rows: int
    reached_reveal: bool
    reached_decision: bool
    reached_post_decision: bool
    terminated: bool
    truncated: bool
    terminal_reason: str
    failure_type: str
    error_type: str = ""
    error_message: str = ""


def phase_for_step(step: int, reveal_step: int, decision_step: int, *, terminal: bool = False) -> str:
    """Classify one trace step relative to reveal and decision indices."""

    if terminal:
        return "terminal"
    if step < reveal_step:
        return "pre_reveal"
    if step == reveal_step:
        return "reveal"
    if step < decision_step:
        return "between_reveal_and_decision"
    if step == decision_step:
        return "decision"
    return "post_decision"


def hidden_stats(hidden: Any) -> tuple[float, float]:
    """Return deterministic scalar hidden diagnostics."""

    if hidden is None:
        return 0.0, 0.0
    array = hidden.detach().cpu().numpy().astype(np.float64, copy=False)
    if array.size == 0:
        return 0.0, 0.0
    return float(np.linalg.norm(array)), float(np.sum(np.round(array, 6)))


def assert_p0_env_contract(config: DriftEnvConfig) -> None:
    """Reject env configs that would violate the P0 human-view no-wheel contract."""

    if config.history_length != 1:
        raise ValueError("bounded runner requires history_length=1")
    if config.include_privileged_params:
        raise ValueError("bounded runner forbids privileged actor observation")
    if config.wheel_observation_mode != "none":
        raise ValueError("bounded runner forbids wheel observation mode")
    if config.action_history_mode != "full":
        raise ValueError("bounded runner requires full previous physical command history")
    if config.obstacle_relative_velocity_mode != "zero":
        raise ValueError("bounded runner requires zero obstacle relative velocity mode")


def assert_p0_model_contract(model: Any) -> None:
    """Reject checkpoints that are not the canonical P0 online-GRU actor."""

    if int(getattr(model, "obs_dim", -1)) != HUMAN_VIEW_OBS_DIM:
        raise ValueError(f"bounded runner requires {HUMAN_VIEW_OBS_DIM}-value actor frame")
    if str(getattr(model, "actor_encoder", "")) not in HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS:
        raise ValueError("bounded runner requires human-view online GRU actor")
    if not bool(getattr(model, "is_online_recurrent", False)):
        raise ValueError("bounded runner requires online recurrent actor")


def select_bounded_specs(
    *,
    seed_count: int = 1,
    source_family_cap: int = 1,
) -> list[DecisiveHistoryEnvHookSpec]:
    """Select a small source-diverse subset from deterministic hook specs."""

    if seed_count < 1:
        raise ValueError("seed_count must be positive")
    if source_family_cap < 1:
        raise ValueError("source_family_cap must be positive")
    selected: list[DecisiveHistoryEnvHookSpec] = []
    counts: Counter[str] = Counter()
    for spec in default_hook_specs(seed_count=seed_count):
        if counts[spec.source_family] >= source_family_cap:
            continue
        selected.append(spec)
        counts[spec.source_family] += 1
    return selected


def _to_float(info: dict[str, Any], key: str) -> float:
    value = info.get(key, float("nan"))
    return float(value) if value is not None else float("nan")


def _to_bool(info: dict[str, Any], key: str) -> bool:
    return bool(info.get(key, False))


def _terminal_reason(row: SourceTraceRow | None, *, exhausted_budget: bool) -> str:
    if row is None:
        return "no_rows"
    if bool(row.info_collision):
        return "collision"
    if bool(row.info_obstacle_completed):
        return "obstacle_completed"
    if row.truncated:
        return "truncated"
    if row.terminated:
        return "terminated"
    if exhausted_budget:
        return "max_rollout_steps"
    return "running"


def _failure_type(rows: Sequence[SourceTraceRow], terminal_reason: str, reveal_step: int, decision_step: int) -> str:
    if not rows:
        return "rollout_exception"
    if not any(row.step >= reveal_step for row in rows):
        return "did_not_reach_reveal_step"
    if not any(row.step >= decision_step for row in rows):
        return "did_not_reach_decision_step"
    if terminal_reason in {"collision", "obstacle_completed", "terminated", "truncated", "max_rollout_steps"}:
        return "none"
    return "rollout_exception"


def _trace_id(spec: DecisiveHistoryEnvHookSpec) -> str:
    return f"{spec.source_family}|{spec.seed}|{spec.candidate_id}"


def _make_trace_row(
    *,
    spec: DecisiveHistoryEnvHookSpec,
    step: int,
    observation_dim: int,
    action: np.ndarray,
    reward: float,
    hidden_norm: float,
    hidden_checksum: float,
    info: dict[str, Any],
    terminated: bool,
    truncated: bool,
) -> SourceTraceRow:
    terminal = bool(terminated or truncated)
    return SourceTraceRow(
        trace_id=_trace_id(spec),
        source_family=spec.source_family,
        task_family=spec.task_family,
        candidate_id=spec.candidate_id,
        seed=int(spec.seed),
        capability_pair=spec.capability_pair,
        geometry_key=spec.geometry_key,
        reveal_step=int(spec.reveal_step),
        decision_step=int(spec.decision_step),
        step=int(step),
        phase=phase_for_step(int(step), int(spec.reveal_step), int(spec.decision_step), terminal=terminal),
        terminated=bool(terminated),
        truncated=bool(truncated),
        reward=float(reward),
        action_steer=float(action[0]),
        action_throttle=float(action[1]),
        action_brake=float(action[2]),
        hidden_norm=float(hidden_norm),
        hidden_checksum=float(hidden_checksum),
        observation_dim=int(observation_dim),
        info_obstacle_label=str(info.get("obstacle_label", "")),
        info_obstacle_distance=_to_float(info, "obstacle_distance"),
        info_obstacle_lateral_offset=_to_float(info, "obstacle_lateral_offset"),
        info_active_obstacle_body_x=_to_float(info, "active_obstacle_body_x"),
        info_active_obstacle_body_y=_to_float(info, "active_obstacle_body_y"),
        info_min_clearance_margin=_to_float(info, "min_clearance_margin"),
        info_collision=_to_bool(info, "collision"),
        info_obstacle_completed=_to_bool(info, "obstacle_completed"),
        info_warmup_gate_visible=_to_bool(info, "warmup_gate_visible"),
        info_warmup_gate_clearance_margin=_to_float(info, "warmup_gate_clearance_margin"),
        info_friction_step_at=info.get("friction_step_at"),
        info_friction_step_applied=_to_bool(info, "friction_step_applied"),
        info_mu=_to_float(info, "mu"),
        info_initial_mu=_to_float(info, "initial_mu"),
        info_brake_scale=_to_float(info, "brake_scale"),
        info_drive_scale=_to_float(info, "drive_scale"),
        info_steer_tau_scale=_to_float(info, "steer_tau_scale"),
    )


def run_source_trace(
    spec: DecisiveHistoryEnvHookSpec,
    policy: ActorPolicy,
    *,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
) -> tuple[list[SourceTraceRow], SourceAttemptSummary]:
    """Run one bounded fixed-policy source trace."""

    if max_rollout_steps < 1:
        raise ValueError("max_rollout_steps must be positive")
    assert_p0_env_contract(spec.env_config)
    rows: list[SourceTraceRow] = []
    try:
        env = AutoDriftEnv(spec.env_config)
        observation, info = env.reset(seed=int(spec.seed))
        policy.env_config = spec.env_config
        policy.reset()
        terminated = False
        truncated = False
        for _ in range(int(max_rollout_steps)):
            if not np.all(np.isfinite(observation)):
                raise ValueError("nonfinite_observation")
            step = int(info.get("step", len(rows)))
            action = policy.act(observation, info)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            norm, checksum = hidden_stats(policy.hidden)
            next_observation, reward, terminated, truncated, next_info = env.step(action)
            row = _make_trace_row(
                spec=spec,
                step=step,
                observation_dim=int(np.asarray(observation).shape[0]),
                action=np.asarray(action, dtype=np.float64),
                reward=float(reward),
                hidden_norm=norm,
                hidden_checksum=checksum,
                info=next_info,
                terminated=bool(terminated),
                truncated=bool(truncated),
            )
            rows.append(row)
            observation = next_observation
            info = next_info
            if terminated or truncated:
                break
    except Exception as exc:
        failure = str(exc)
        if failure not in {"nonfinite_observation", "nonfinite_action"}:
            failure = "reset_failure" if not rows else "rollout_exception"
        return rows, SourceAttemptSummary(
            trace_id=_trace_id(spec),
            source_family=spec.source_family,
            task_family=spec.task_family,
            candidate_id=spec.candidate_id,
            seed=int(spec.seed),
            rows=len(rows),
            reached_reveal=any(row.step >= spec.reveal_step for row in rows),
            reached_decision=any(row.step >= spec.decision_step for row in rows),
            reached_post_decision=any(row.step > spec.decision_step for row in rows),
            terminated=bool(rows[-1].terminated) if rows else False,
            truncated=bool(rows[-1].truncated) if rows else False,
            terminal_reason=_terminal_reason(rows[-1] if rows else None, exhausted_budget=False),
            failure_type=failure,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    exhausted_budget = bool(rows) and not bool(rows[-1].terminated or rows[-1].truncated)
    terminal_reason = _terminal_reason(rows[-1] if rows else None, exhausted_budget=exhausted_budget)
    failure = _failure_type(rows, terminal_reason, int(spec.reveal_step), int(spec.decision_step))
    return rows, SourceAttemptSummary(
        trace_id=_trace_id(spec),
        source_family=spec.source_family,
        task_family=spec.task_family,
        candidate_id=spec.candidate_id,
        seed=int(spec.seed),
        rows=len(rows),
        reached_reveal=any(row.step >= spec.reveal_step for row in rows),
        reached_decision=any(row.step >= spec.decision_step for row in rows),
        reached_post_decision=any(row.step > spec.decision_step for row in rows),
        terminated=bool(rows[-1].terminated) if rows else False,
        truncated=bool(rows[-1].truncated) if rows else False,
        terminal_reason=terminal_reason,
        failure_type=failure,
    )


def build_snapshot_rows(rows: Sequence[SourceTraceRow], summary: SourceAttemptSummary) -> list[SourceSnapshotRow]:
    """Build reveal/decision/post-decision/terminal snapshots from trace rows."""

    by_step = {int(row.step): row for row in rows}
    desired: list[tuple[str, int]] = []
    if rows:
        reveal = int(rows[0].reveal_step)
        decision = int(rows[0].decision_step)
        desired.append(("reveal_step", reveal))
        desired.append(("decision_step", decision))
        for offset in SNAPSHOT_OFFSETS[1:]:
            desired.append((f"decision_plus_{offset}", decision + offset))
        desired.append(("terminal", int(rows[-1].step)))

    snapshots: list[SourceSnapshotRow] = []
    seen: set[tuple[str, int]] = set()
    for snapshot_kind, target_step in desired:
        eligible_steps = [step for step in by_step if step >= target_step]
        if not eligible_steps:
            continue
        row = by_step[min(eligible_steps)]
        key = (snapshot_kind, int(row.step))
        if key in seen:
            continue
        seen.add(key)
        snapshots.append(
            SourceSnapshotRow(
                trace_id=row.trace_id,
                source_family=row.source_family,
                task_family=row.task_family,
                candidate_id=row.candidate_id,
                seed=row.seed,
                snapshot_kind=snapshot_kind,
                step=row.step,
                phase=row.phase,
                action_steer=row.action_steer,
                action_throttle=row.action_throttle,
                action_brake=row.action_brake,
                hidden_norm=row.hidden_norm,
                min_clearance_margin=row.info_min_clearance_margin,
                collision=row.info_collision,
                obstacle_completed=row.info_obstacle_completed,
                terminal_reason=summary.terminal_reason,
            )
        )
    return snapshots


def _guardrail_rows() -> list[dict[str, object]]:
    return [{"guardrail": key, "violated": False} for key in GUARDRAIL_KEYS]


def build_runner_summary(
    *,
    checkpoint: Path | str,
    specs: Sequence[DecisiveHistoryEnvHookSpec],
    traces: Sequence[SourceTraceRow],
    snapshots: Sequence[SourceSnapshotRow],
    attempts: Sequence[SourceAttemptSummary],
    max_rollout_steps: int,
) -> dict[str, Any]:
    """Summarize bounded source-trace collection."""

    failure_counts = Counter(row.failure_type for row in attempts if row.failure_type != "none")
    guardrails = _guardrail_rows()
    return {
        "result_class": "decisive_history_bounded_runner_smoke",
        "checkpoint": str(checkpoint),
        "spec_count": len(specs),
        "source_family_count": len({spec.source_family for spec in specs}),
        "max_rollout_steps": int(max_rollout_steps),
        "trace_row_count": len(traces),
        "snapshot_row_count": len(snapshots),
        "rollout_success_count": sum(1 for row in attempts if row.failure_type == "none"),
        "rollout_failure_count": sum(1 for row in attempts if row.failure_type != "none"),
        "failure_type_counts": dict(sorted(failure_counts.items())),
        "source_families_attempted": sorted({row.source_family for row in attempts}),
        "source_families_completed": sorted({row.source_family for row in attempts if row.failure_type == "none"}),
        "source_families_reached_reveal": sorted({row.source_family for row in attempts if row.reached_reveal}),
        "source_families_reached_decision": sorted({row.source_family for row in attempts if row.reached_decision}),
        "source_families_reached_post_decision": sorted(
            {row.source_family for row in attempts if row.reached_post_decision}
        ),
        "guardrail_violation_count": sum(1 for row in guardrails if row["violated"]),
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


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [dict(row.__dict__) for row in rows]


def run_bounded_runner_smoke(
    run_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed_count: int = 1,
    source_family_cap: int = 1,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded fixed-policy source traces and write artifacts."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = select_bounded_specs(seed_count=seed_count, source_family_cap=source_family_cap)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, specs[0].env_config if specs else DriftEnvConfig())

    traces: list[SourceTraceRow] = []
    snapshots: list[SourceSnapshotRow] = []
    attempts: list[SourceAttemptSummary] = []
    for spec in specs:
        source_rows, attempt = run_source_trace(spec, policy, max_rollout_steps=max_rollout_steps)
        traces.extend(source_rows)
        attempts.append(attempt)
        snapshots.extend(build_snapshot_rows(source_rows, attempt))

    summary = build_runner_summary(
        checkpoint=checkpoint,
        specs=specs,
        traces=traces,
        snapshots=snapshots,
        attempts=attempts,
        max_rollout_steps=max_rollout_steps,
    )
    write_csv_rows(output / "source_trace_rows.csv", _asdict_rows(traces))
    write_csv_rows(output / "source_snapshot_rows.csv", _asdict_rows(snapshots))
    write_csv_rows(output / "source_family_summary.csv", _asdict_rows(attempts))
    write_csv_rows(output / "runner_guardrail_summary.csv", _guardrail_rows())
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded fixed-policy decisive-history source traces.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--source-family-cap", type=int, default=1)
    parser.add_argument("--max-rollout-steps", type=int, default=DEFAULT_MAX_ROLLOUT_STEPS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_bounded_runner_smoke(
        args.run_dir,
        checkpoint=args.checkpoint,
        seed_count=int(args.seed_count),
        source_family_cap=int(args.source_family_cap),
        max_rollout_steps=int(args.max_rollout_steps),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"trace_row_count={summary['trace_row_count']}")
    print(f"rollout_failure_count={summary['rollout_failure_count']}")


if __name__ == "__main__":
    main()
