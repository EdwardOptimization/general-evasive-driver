"""Bounded terminal-boundary task-sampling calibration smoke."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import (
    DEFAULT_CHECKPOINT,
    DEFAULT_MAX_ROLLOUT_STEPS,
    SourceAttemptSummary,
    SourceSnapshotRow,
    SourceTraceRow,
    assert_p0_env_contract,
    assert_p0_model_contract,
    build_snapshot_rows,
    run_source_trace,
)
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import ActorPolicy
from autodrift.fresh_ambiguity_measured_mining import source_row_to_hook_spec
from autodrift.fresh_ambiguity_source_mining import FreshAmbiguitySourceRow, row_id as source_row_id
from autodrift.terminal_boundary_source_repair import TERMINAL_TARGET_FAMILIES, terminal_repair_source_rows


DEFAULT_RUN_DIR = Path("runs/m1544_terminal_boundary_task_sampling_calibration_smoke")
DECISION_MARGIN_WINDOW = (-0.03, 0.12)
PREFERRED_DECISION_MARGIN_WINDOW = (-0.01, 0.06)
POST_DECISION_MARGIN_WINDOW = (-0.05, 0.10)
TERMINAL_MARGIN_WINDOW = (-0.05, 0.12)
GUARDRAILS = {
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


@dataclass(frozen=True)
class CalibrationMode:
    """One bounded task retarget mode for terminal-boundary calibration."""

    name: str
    distance_scale: float
    half_width_shift: float
    speed_shift: float
    reveal_delta: int
    require_aeb_infeasible: bool = False
    low_authority_band: bool = False


@dataclass(frozen=True)
class CalibrationSpecRow:
    """Flattened calibration spec row for public audit artifacts."""

    calibration_id: str
    source_row_id: str
    source_family: str
    task_family: str
    seed: int
    capability_pair: str
    geometry_key: str
    mode_name: str
    distance_scale: float
    half_width_shift: float
    speed_shift: float
    reveal_delta: int
    require_aeb_infeasible: bool
    low_authority_band: bool
    base_distance_min: float
    base_distance_max: float
    retarget_distance_min: float
    retarget_distance_max: float
    base_half_width_min: float
    base_half_width_max: float
    retarget_half_width_min: float
    retarget_half_width_max: float
    base_speed_min: float
    base_speed_max: float
    retarget_speed_min: float
    retarget_speed_max: float
    reveal_step: int
    decision_step: int
    candidate_materialized: bool = False
    training_corpus_exported: bool = False
    actor_input_contract_changed: bool = False
    labels_enter_actor_input: bool = False


@dataclass(frozen=True)
class CalibrationSpec:
    """Runnable calibration hook plus flattened artifact row."""

    source_row: FreshAmbiguitySourceRow
    hook_spec: DecisiveHistoryEnvHookSpec
    artifact_row: CalibrationSpecRow


@dataclass(frozen=True)
class AcceptedCalibratedRow:
    """One calibrated terminal target row that entered a margin window."""

    calibration_id: str
    trace_id: str
    source_row_id: str
    source_family: str
    seed: int
    mode_name: str
    window_kind: str
    decision_margin: float
    post_decision_margin: float
    terminal_margin: float
    decision_window_hit: bool
    preferred_decision_window_hit: bool
    post_decision_window_hit: bool
    terminal_window_hit: bool
    terminal_reason: str
    collision: bool
    obstacle_completed: bool
    candidate_materialized: bool = False
    training_corpus_exported: bool = False


def calibration_modes() -> tuple[CalibrationMode, ...]:
    """Return a bounded curated calibration grid."""

    return (
        CalibrationMode("close_wide", 0.70, 0.40, 0.0, 0),
        CalibrationMode("very_close_wide", 0.60, 0.60, 0.0, 0),
        CalibrationMode("close_high_speed", 0.70, 0.40, 3.0, 0),
        CalibrationMode("very_close_high_speed", 0.60, 0.60, 3.0, 0),
        CalibrationMode("late_close_high_speed", 0.70, 0.40, 3.0, 8),
        CalibrationMode("late_very_close", 0.62, 0.60, 1.5, 8),
        CalibrationMode("low_authority_close", 0.70, 0.40, 1.5, 0, low_authority_band=True),
        CalibrationMode("low_authority_very_close", 0.62, 0.60, 1.5, 4, low_authority_band=True),
        CalibrationMode("aeb_infeasible_close", 0.68, 0.50, 1.5, 4, require_aeb_infeasible=True),
        CalibrationMode(
            "aeb_infeasible_low_authority",
            0.62,
            0.65,
            3.0,
            8,
            require_aeb_infeasible=True,
            low_authority_band=True,
        ),
    )


def _scale_range(values: tuple[float, float], scale: float, *, floor: float = 0.01) -> tuple[float, float]:
    return (max(floor, float(values[0]) * scale), max(floor, float(values[1]) * scale))


def _shift_range(values: tuple[float, float], shift: float, *, floor: float = 0.01) -> tuple[float, float]:
    return (max(floor, float(values[0]) + shift), max(floor, float(values[1]) + shift))


def _clip_range(values: tuple[float, float], *, low: float, high: float) -> tuple[float, float]:
    clipped = (min(max(float(values[0]), low), high), min(max(float(values[1]), low), high))
    return (min(clipped), max(clipped))


def terminal_calibration_source_rows(
    *,
    seed: int = 1843,
    seed_count: int = 2,
    max_base_rows: int = 20,
) -> list[FreshAmbiguitySourceRow]:
    """Return bounded terminal target rows for calibration."""

    rows = [
        row
        for row in terminal_repair_source_rows(seed=seed, seed_count=seed_count, max_repair_source_specs=max_base_rows)
        if row.source_family in set(TERMINAL_TARGET_FAMILIES)
    ]
    return rows[: max(0, int(max_base_rows))]


def _retarget_hook_spec(
    row: FreshAmbiguitySourceRow,
    mode: CalibrationMode,
    *,
    calibration_index: int,
) -> CalibrationSpec:
    base = source_row_to_hook_spec(row)
    cfg = base.env_config
    obstacle = cfg.obstacle
    randomization = cfg.randomization
    base_distance = obstacle.distance_range
    base_width = obstacle.half_width_range
    base_speed = cfg.speed_range
    reveal_step = max(1, int(row.reveal_step) + int(mode.reveal_delta))
    decision_offset = max(4, int(row.decision_step) - int(row.reveal_step))
    decision_step = reveal_step + decision_offset
    obstacle = replace(
        obstacle,
        distance_range=_scale_range(obstacle.distance_range, float(mode.distance_scale), floor=5.0),
        half_width_range=_shift_range(obstacle.half_width_range, float(mode.half_width_shift), floor=0.10),
        perception_reveal_step=reveal_step,
        require_aeb_infeasible=bool(mode.require_aeb_infeasible),
        max_sample_attempts=max(int(obstacle.max_sample_attempts), 800),
    )
    if mode.low_authority_band:
        randomization = replace(
            randomization,
            mu_range=(0.22, min(0.70, float(randomization.mu_range[1]))),
            brake_scale_range=(0.30, min(0.85, float(randomization.brake_scale_range[1]))),
            tire_stiffness_scale_range=(0.45, min(1.00, float(randomization.tire_stiffness_scale_range[1]))),
        )
    speed_range = _clip_range(_shift_range(cfg.speed_range, float(mode.speed_shift), floor=1.0), low=1.0, high=24.0)
    env_config = replace(cfg, obstacle=obstacle, randomization=randomization, speed_range=speed_range)
    assert_p0_env_contract(env_config)
    calibration_id = f"calib-{calibration_index:04d}-{row.source_family}-{mode.name}"
    hook = replace(
        base,
        candidate_id=calibration_id,
        reveal_step=reveal_step,
        decision_step=decision_step,
        env_config=env_config,
        obstacle_variant=f"{base.obstacle_variant}|{mode.name}",
        capability_variant=f"{base.capability_variant}|{mode.name}",
        labels_enter_actor_input=False,
        candidate_materialized=False,
        simulator_rollout_started=True,
    )
    artifact = CalibrationSpecRow(
        calibration_id=calibration_id,
        source_row_id=source_row_id(row),
        source_family=row.source_family,
        task_family=row.task_family,
        seed=int(row.seed),
        capability_pair=row.hidden_capability_pair,
        geometry_key=row.geometry_key,
        mode_name=mode.name,
        distance_scale=float(mode.distance_scale),
        half_width_shift=float(mode.half_width_shift),
        speed_shift=float(mode.speed_shift),
        reveal_delta=int(mode.reveal_delta),
        require_aeb_infeasible=bool(mode.require_aeb_infeasible),
        low_authority_band=bool(mode.low_authority_band),
        base_distance_min=float(base_distance[0]),
        base_distance_max=float(base_distance[1]),
        retarget_distance_min=float(obstacle.distance_range[0]),
        retarget_distance_max=float(obstacle.distance_range[1]),
        base_half_width_min=float(base_width[0]),
        base_half_width_max=float(base_width[1]),
        retarget_half_width_min=float(obstacle.half_width_range[0]),
        retarget_half_width_max=float(obstacle.half_width_range[1]),
        base_speed_min=float(base_speed[0]),
        base_speed_max=float(base_speed[1]),
        retarget_speed_min=float(speed_range[0]),
        retarget_speed_max=float(speed_range[1]),
        reveal_step=reveal_step,
        decision_step=decision_step,
    )
    return CalibrationSpec(source_row=row, hook_spec=hook, artifact_row=artifact)


def build_calibration_specs(
    source_rows: Sequence[FreshAmbiguitySourceRow],
    *,
    max_calibration_specs: int = 160,
) -> list[CalibrationSpec]:
    """Build bounded retargeted calibration specs."""

    specs: list[CalibrationSpec] = []
    for row in source_rows:
        for mode in calibration_modes():
            if len(specs) >= int(max_calibration_specs):
                return specs
            specs.append(_retarget_hook_spec(row, mode, calibration_index=len(specs)))
    return specs


def _snapshot_margin(snapshots: Sequence[SourceSnapshotRow], kind: str) -> float:
    values = [float(row.min_clearance_margin) for row in snapshots if row.snapshot_kind == kind]
    finite = [value for value in values if np.isfinite(value)]
    return float(finite[0]) if finite else float("nan")


def _window_hit(value: float, window: tuple[float, float]) -> bool:
    return bool(np.isfinite(value) and float(window[0]) <= float(value) <= float(window[1]))


def accepted_calibrated_row(
    spec: CalibrationSpec,
    snapshots: Sequence[SourceSnapshotRow],
    attempt: SourceAttemptSummary,
) -> AcceptedCalibratedRow | None:
    """Return accepted calibrated row if a decision or post-decision window fired."""

    decision_margin = _snapshot_margin(snapshots, "decision_step")
    post_margin = min(
        (
            float(row.min_clearance_margin)
            for row in snapshots
            if row.snapshot_kind in {"decision_plus_8", "decision_plus_16"}
            and np.isfinite(float(row.min_clearance_margin))
        ),
        default=float("nan"),
    )
    terminal_margin = _snapshot_margin(snapshots, "terminal")
    decision_hit = _window_hit(decision_margin, DECISION_MARGIN_WINDOW)
    preferred_decision_hit = _window_hit(decision_margin, PREFERRED_DECISION_MARGIN_WINDOW)
    post_hit = _window_hit(post_margin, POST_DECISION_MARGIN_WINDOW)
    terminal_hit = _window_hit(terminal_margin, TERMINAL_MARGIN_WINDOW)
    if not (decision_hit or post_hit):
        return None
    terminal_snapshot = next((row for row in snapshots if row.snapshot_kind == "terminal"), None)
    window_kind = "decision" if decision_hit else "post_decision"
    return AcceptedCalibratedRow(
        calibration_id=spec.artifact_row.calibration_id,
        trace_id=attempt.trace_id,
        source_row_id=spec.artifact_row.source_row_id,
        source_family=spec.source_row.source_family,
        seed=int(spec.source_row.seed),
        mode_name=spec.artifact_row.mode_name,
        window_kind=window_kind,
        decision_margin=decision_margin,
        post_decision_margin=post_margin,
        terminal_margin=terminal_margin,
        decision_window_hit=decision_hit,
        preferred_decision_window_hit=preferred_decision_hit,
        post_decision_window_hit=post_hit,
        terminal_window_hit=terminal_hit,
        terminal_reason=attempt.terminal_reason,
        collision=bool(terminal_snapshot.collision) if terminal_snapshot is not None else False,
        obstacle_completed=bool(terminal_snapshot.obstacle_completed) if terminal_snapshot is not None else False,
    )


def _guardrail_summary() -> list[dict[str, Any]]:
    return [{"guardrail": key, "violated": bool(value)} for key, value in GUARDRAILS.items()]


def build_family_summary(accepted: Sequence[AcceptedCalibratedRow]) -> list[dict[str, Any]]:
    """Summarize accepted calibrated rows by terminal source family."""

    grouped: dict[str, list[AcceptedCalibratedRow]] = {}
    for row in accepted:
        grouped.setdefault(row.source_family, []).append(row)
    summaries: list[dict[str, Any]] = []
    for family, rows in sorted(grouped.items()):
        summaries.append(
            {
                "source_family": family,
                "accepted_count": len(rows),
                "decision_window_hit_count": sum(1 for row in rows if row.decision_window_hit),
                "post_decision_window_hit_count": sum(1 for row in rows if row.post_decision_window_hit),
                "preferred_decision_window_hit_count": sum(1 for row in rows if row.preferred_decision_window_hit),
                "terminal_window_hit_count": sum(1 for row in rows if row.terminal_window_hit),
                "min_decision_margin": min((row.decision_margin for row in rows), default=float("nan")),
                "max_decision_margin": max((row.decision_margin for row in rows), default=float("nan")),
            }
        )
    return summaries


def build_summary(
    *,
    source_rows: Sequence[FreshAmbiguitySourceRow],
    specs: Sequence[CalibrationSpec],
    traces: Sequence[SourceTraceRow],
    snapshots: Sequence[SourceSnapshotRow],
    attempts: Sequence[SourceAttemptSummary],
    accepted: Sequence[AcceptedCalibratedRow],
    max_rollout_steps: int,
) -> dict[str, Any]:
    """Build calibration smoke summary."""

    family_counts = Counter(row.source_family for row in accepted)
    max_family_share = max((count / max(1, len(accepted)) for count in family_counts.values()), default=0.0)
    finite_snapshot_count = sum(1 for row in snapshots if np.isfinite(float(row.min_clearance_margin)))
    guardrails = dict(GUARDRAILS)
    decision_hits = sum(1 for row in accepted if row.decision_window_hit)
    post_hits = sum(1 for row in accepted if row.post_decision_window_hit)
    summary = {
        "result_class": "terminal_boundary_task_sampling_calibration_smoke",
        "terminal_base_source_rows": len(source_rows),
        "calibration_spec_count": len(specs),
        "max_rollout_steps": int(max_rollout_steps),
        "trace_row_count": len(traces),
        "snapshot_row_count": len(snapshots),
        "finite_margin_row_count": finite_snapshot_count,
        "terminal_target_trace_count": sum(1 for row in attempts if row.reached_decision),
        "terminal_family_count": len({row.source_family for row in source_rows}),
        "accepted_calibrated_row_count": len(accepted),
        "accepted_terminal_family_count": len(family_counts),
        "decision_window_hit_count": decision_hits,
        "preferred_decision_window_hit_count": sum(1 for row in accepted if row.preferred_decision_window_hit),
        "post_decision_window_hit_count": post_hits,
        "terminal_window_hit_count": sum(1 for row in accepted if row.terminal_window_hit),
        "max_single_terminal_family_share": max_family_share,
        "rollout_failure_count": sum(1 for row in attempts if row.failure_type != "none"),
        "failure_type_counts": dict(sorted(Counter(row.failure_type for row in attempts).items())),
        "accepted_source_family_counts": dict(sorted(family_counts.items())),
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_calibration_source_gates"] = (
        int(summary["terminal_base_source_rows"]) >= 10
        and int(summary["calibration_spec_count"]) >= 40
        and int(summary["terminal_target_trace_count"]) >= 20
        and int(summary["terminal_family_count"]) >= 4
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_near_boundary_gates"] = (
        int(summary["accepted_calibrated_row_count"]) >= 8
        and int(summary["accepted_terminal_family_count"]) >= 3
        and int(summary["decision_window_hit_count"]) >= 4
        and int(summary["post_decision_window_hit_count"]) >= 4
        and float(summary["max_single_terminal_family_share"]) <= 0.50
    )
    summary["passes_quality_gates"] = (
        int(summary["finite_margin_row_count"]) == int(summary["snapshot_row_count"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_public_smoke_gates"] = (
        bool(summary["passes_calibration_source_gates"])
        and bool(summary["passes_near_boundary_gates"])
        and bool(summary["passes_quality_gates"])
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_near_boundary_gates"])
    return summary


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row) for row in rows]


def run_terminal_boundary_task_sampling_calibration_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 2,
    max_base_rows: int = 20,
    max_calibration_specs: int = 160,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded calibration smoke over retargeted terminal source specs."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_rows = terminal_calibration_source_rows(seed=seed, seed_count=seed_count, max_base_rows=max_base_rows)
    specs = build_calibration_specs(source_rows, max_calibration_specs=max_calibration_specs)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, DriftEnvConfig())
    traces: list[SourceTraceRow] = []
    snapshots: list[SourceSnapshotRow] = []
    attempts: list[SourceAttemptSummary] = []
    accepted: list[AcceptedCalibratedRow] = []
    for spec in specs:
        trace_rows, attempt = run_source_trace(spec.hook_spec, policy, max_rollout_steps=max_rollout_steps)
        snapshot_rows = build_snapshot_rows(trace_rows, attempt)
        traces.extend(trace_rows)
        snapshots.extend(snapshot_rows)
        attempts.append(attempt)
        accepted_row = accepted_calibrated_row(spec, snapshot_rows, attempt)
        if accepted_row is not None:
            accepted.append(accepted_row)

    family_summary = build_family_summary(accepted)
    summary = build_summary(
        source_rows=source_rows,
        specs=specs,
        traces=traces,
        snapshots=snapshots,
        attempts=attempts,
        accepted=accepted,
        max_rollout_steps=max_rollout_steps,
    )
    write_csv_rows(output / "source_rows.csv", _asdict_rows(source_rows))
    write_csv_rows(output / "calibration_specs.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "trace_rows.csv", _asdict_rows(traces))
    write_csv_rows(output / "snapshot_rows.csv", _asdict_rows(snapshots))
    write_csv_rows(output / "accepted_calibrated_rows.csv", _asdict_rows(accepted))
    write_csv_rows(output / "family_summary.csv", family_summary)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_summary())
    write_csv_rows(output / "source_attempt_rows.csv", _asdict_rows(attempts))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run terminal-boundary task sampling calibration smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=2)
    parser.add_argument("--max-base-rows", type=int, default=20)
    parser.add_argument("--max-calibration-specs", type=int, default=160)
    parser.add_argument("--max-rollout-steps", type=int, default=DEFAULT_MAX_ROLLOUT_STEPS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_terminal_boundary_task_sampling_calibration_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_base_rows=int(args.max_base_rows),
        max_calibration_specs=int(args.max_calibration_specs),
        max_rollout_steps=int(args.max_rollout_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"accepted_calibrated_row_count={summary['accepted_calibrated_row_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
