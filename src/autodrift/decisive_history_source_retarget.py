"""Bounded public source retargeting for decisive-history trace probes."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import (
    DEFAULT_CHECKPOINT,
    SourceAttemptSummary,
    SourceSnapshotRow,
    SourceTraceRow,
    assert_p0_env_contract,
    assert_p0_model_contract,
    build_snapshot_rows,
    run_source_trace,
)
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec, default_hook_specs
from autodrift.evaluate import ActorPolicy


DEFAULT_BASELINE_TRACE_ROWS = Path("runs/m1511_decisive_history_bounded_runner_smoke/source_trace_rows.csv")
DEFAULT_RUN_DIR = Path("runs/m1514_decisive_history_source_retarget_smoke")
DEFAULT_MAX_ROLLOUT_STEPS = 128
RETARGET_MODES = (
    "close_wide",
    "low_mu_close",
    "late_reveal_high_speed",
    "drift_required_focus",
    "wide_low_brake",
)
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
class RetargetedHookSpec:
    """One deterministic retargeted hook spec."""

    base_spec: DecisiveHistoryEnvHookSpec
    hook_spec: DecisiveHistoryEnvHookSpec
    retarget_mode: str


def _scale_range(values: tuple[float, float], scale: float, *, floor: float = 0.01) -> tuple[float, float]:
    return (max(floor, float(values[0]) * scale), max(floor, float(values[1]) * scale))


def _shift_range(values: tuple[float, float], shift: float, *, floor: float = 0.01) -> tuple[float, float]:
    return (max(floor, float(values[0]) + shift), max(floor, float(values[1]) + shift))


def _clip_range(values: tuple[float, float], *, low: float, high: float) -> tuple[float, float]:
    clipped = (min(max(float(values[0]), low), high), min(max(float(values[1]), low), high))
    return (min(clipped), max(clipped))


def _format_range(values: tuple[float, float]) -> str:
    return f"{values[0]:.6g}|{values[1]:.6g}"


def retarget_hook_spec(spec: DecisiveHistoryEnvHookSpec, mode: str) -> RetargetedHookSpec:
    """Return a P0-compatible retargeted hook spec for one deterministic mode."""

    if mode not in RETARGET_MODES:
        raise ValueError(f"unknown retarget mode: {mode}")
    cfg = spec.env_config
    obstacle = cfg.obstacle
    randomization = cfg.randomization
    speed_range = cfg.speed_range
    reveal_step = int(spec.reveal_step)
    decision_step = int(spec.decision_step)

    if mode == "close_wide":
        obstacle = replace(
            obstacle,
            distance_range=_scale_range(obstacle.distance_range, 0.68, floor=5.0),
            half_width_range=_shift_range(obstacle.half_width_range, 0.55, floor=0.10),
            max_sample_attempts=max(obstacle.max_sample_attempts, 400),
        )
    elif mode == "low_mu_close":
        obstacle = replace(
            obstacle,
            distance_range=_scale_range(obstacle.distance_range, 0.76, floor=5.0),
            half_width_range=_shift_range(obstacle.half_width_range, 0.30, floor=0.10),
            max_sample_attempts=max(obstacle.max_sample_attempts, 400),
        )
        randomization = replace(
            randomization,
            mu_range=(0.22, min(0.65, float(randomization.mu_range[1]))),
            brake_scale_range=(0.35, min(0.90, float(randomization.brake_scale_range[1]))),
            tire_stiffness_scale_range=(0.45, min(1.00, float(randomization.tire_stiffness_scale_range[1]))),
        )
    elif mode == "late_reveal_high_speed":
        reveal_step = int(spec.reveal_step) + 6
        decision_step = int(spec.decision_step) + 6
        obstacle = replace(
            obstacle,
            distance_range=_scale_range(obstacle.distance_range, 0.72, floor=5.0),
            half_width_range=_shift_range(obstacle.half_width_range, 0.35, floor=0.10),
            perception_reveal_step=reveal_step,
            max_sample_attempts=max(obstacle.max_sample_attempts, 400),
        )
        speed_range = _clip_range(_shift_range(speed_range, 3.0, floor=1.0), low=1.0, high=24.0)
    elif mode == "drift_required_focus":
        obstacle = replace(
            obstacle,
            distance_range=_scale_range(obstacle.distance_range, 0.70, floor=5.0),
            half_width_range=_shift_range(obstacle.half_width_range, 0.60, floor=0.10),
            allowed_labels=("aes_feasible", "drift_required", "unavoidable"),
            require_aeb_infeasible=True,
            max_sample_attempts=max(obstacle.max_sample_attempts, 800),
        )
        randomization = replace(
            randomization,
            mu_range=(0.22, min(0.75, float(randomization.mu_range[1]))),
            brake_scale_range=(0.35, min(0.95, float(randomization.brake_scale_range[1]))),
        )
    elif mode == "wide_low_brake":
        obstacle = replace(
            obstacle,
            distance_range=_scale_range(obstacle.distance_range, 0.82, floor=5.0),
            half_width_range=_shift_range(obstacle.half_width_range, 0.75, floor=0.10),
            max_sample_attempts=max(obstacle.max_sample_attempts, 400),
        )
        randomization = replace(
            randomization,
            brake_scale_range=(0.30, min(0.85, float(randomization.brake_scale_range[1]))),
            actuator_tau_scale_range=(max(1.10, float(randomization.actuator_tau_scale_range[0])), 4.0),
        )

    env_config = replace(
        cfg,
        speed_range=speed_range,
        obstacle=obstacle,
        randomization=randomization,
    )
    retargeted = replace(
        spec,
        candidate_id=f"{spec.candidate_id}-{mode}",
        reveal_step=reveal_step,
        decision_step=decision_step,
        env_config=env_config,
        capability_variant=f"{spec.capability_variant}|{mode}",
        obstacle_variant=f"{spec.obstacle_variant}|{mode}",
        labels_enter_actor_input=False,
        candidate_materialized=False,
        simulator_rollout_started=True,
    )
    assert_p0_env_contract(retargeted.env_config)
    return RetargetedHookSpec(base_spec=spec, hook_spec=retargeted, retarget_mode=mode)


def build_retarget_specs(
    *,
    seed_count: int = 1,
    source_family_cap: int = 4,
) -> list[RetargetedHookSpec]:
    """Build bounded source-diverse retarget specs."""

    if seed_count < 1:
        raise ValueError("seed_count must be positive")
    if source_family_cap < 1:
        raise ValueError("source_family_cap must be positive")
    retargeted: list[RetargetedHookSpec] = []
    for spec in default_hook_specs(seed_count=seed_count):
        for mode in RETARGET_MODES[:source_family_cap]:
            retargeted.append(retarget_hook_spec(spec, mode))
    return retargeted


def retarget_spec_to_row(retargeted: RetargetedHookSpec) -> dict[str, Any]:
    """Flatten one retargeted spec for audit artifacts."""

    base = retargeted.base_spec
    spec = retargeted.hook_spec
    base_cfg = base.env_config
    cfg = spec.env_config
    return {
        "source_family": spec.source_family,
        "retarget_mode": retargeted.retarget_mode,
        "base_candidate_id": base.candidate_id,
        "retarget_candidate_id": spec.candidate_id,
        "seed": spec.seed,
        "task_family": spec.task_family,
        "base_distance_range": _format_range(base_cfg.obstacle.distance_range),
        "retarget_distance_range": _format_range(cfg.obstacle.distance_range),
        "base_half_width_range": _format_range(base_cfg.obstacle.half_width_range),
        "retarget_half_width_range": _format_range(cfg.obstacle.half_width_range),
        "base_speed_range": _format_range(base_cfg.speed_range),
        "retarget_speed_range": _format_range(cfg.speed_range),
        "base_mu_range": _format_range(base_cfg.randomization.mu_range),
        "retarget_mu_range": _format_range(cfg.randomization.mu_range),
        "base_brake_scale_range": _format_range(base_cfg.randomization.brake_scale_range),
        "retarget_brake_scale_range": _format_range(cfg.randomization.brake_scale_range),
        "base_reveal_step": base.reveal_step,
        "retarget_reveal_step": spec.reveal_step,
        "base_decision_step": base.decision_step,
        "retarget_decision_step": spec.decision_step,
        "allowed_labels": "|".join(cfg.obstacle.allowed_labels),
        "labels_enter_actor_input": spec.labels_enter_actor_input,
        "candidate_materialized": spec.candidate_materialized,
    }


def load_baseline_min_margins(path: Path | str = DEFAULT_BASELINE_TRACE_ROWS) -> dict[str, float]:
    """Load M1511 per-source-family minimum trace margins."""

    margins: dict[str, float] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            family = str(row["source_family"])
            try:
                margin = float(row["info_min_clearance_margin"])
            except (KeyError, TypeError, ValueError):
                continue
            if not np.isfinite(margin):
                continue
            margins[family] = min(margins.get(family, margin), margin)
    return margins


def _min_margins_from_traces(traces: Sequence[SourceTraceRow]) -> dict[str, float]:
    margins: dict[str, float] = {}
    for row in traces:
        margin = float(row.info_min_clearance_margin)
        if not np.isfinite(margin):
            continue
        margins[row.source_family] = min(margins.get(row.source_family, margin), margin)
    return margins


def _non_aeb_label_families(traces: Sequence[SourceTraceRow]) -> list[str]:
    labels: defaultdict[str, set[str]] = defaultdict(set)
    for row in traces:
        if row.info_obstacle_label:
            labels[row.source_family].add(row.info_obstacle_label)
    return sorted(
        family
        for family, family_labels in labels.items()
        if any(label != "aeb_feasible" for label in family_labels)
    )


def _near_boundary_proxy_count(traces: Sequence[SourceTraceRow], threshold: float = 1.0) -> int:
    return sum(1 for row in traces if np.isfinite(row.info_min_clearance_margin) and row.info_min_clearance_margin < threshold)


def _guardrail_rows(retargets: Sequence[RetargetedHookSpec]) -> list[dict[str, object]]:
    checks = {
        "candidate_materialized": any(item.hook_spec.candidate_materialized for item in retargets),
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "training_corpus_exported": False,
        "labels_enter_actor_input": any(item.hook_spec.labels_enter_actor_input for item in retargets),
        "level3_self_id_claim_made": False,
    }
    return [{"guardrail": key, "violated": bool(checks[key])} for key in GUARDRAIL_KEYS]


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [dict(row.__dict__) for row in rows]


def _attempt_rows(
    attempts: Sequence[SourceAttemptSummary],
    retargets: Sequence[RetargetedHookSpec],
) -> list[dict[str, Any]]:
    by_trace = {retarget.hook_spec.candidate_id: retarget for retarget in retargets}
    rows: list[dict[str, Any]] = []
    for attempt in attempts:
        retarget = by_trace.get(attempt.candidate_id)
        row = dict(attempt.__dict__)
        if retarget is not None:
            row["retarget_mode"] = retarget.retarget_mode
            row["base_candidate_id"] = retarget.base_spec.candidate_id
        rows.append(row)
    return rows


def build_retarget_summary(
    *,
    checkpoint: Path | str,
    retargets: Sequence[RetargetedHookSpec],
    traces: Sequence[SourceTraceRow],
    snapshots: Sequence[SourceSnapshotRow],
    attempts: Sequence[SourceAttemptSummary],
    baseline_min_margins: Mapping[str, float],
    max_rollout_steps: int,
) -> dict[str, Any]:
    """Build a public no-training retarget smoke summary."""

    retarget_min = _min_margins_from_traces(traces)
    reductions = {
        family: float(baseline_min_margins[family]) - float(retarget_min[family])
        for family in sorted(retarget_min)
        if family in baseline_min_margins
    }
    reduction_fraction = {
        family: reductions[family] / max(abs(float(baseline_min_margins[family])), 1e-6)
        for family in reductions
    }
    failure_counts = Counter(row.failure_type for row in attempts if row.failure_type != "none")
    guardrails = _guardrail_rows(retargets)
    non_aeb_families = _non_aeb_label_families(traces)
    finite_margins = [row.info_min_clearance_margin for row in traces if np.isfinite(row.info_min_clearance_margin)]
    return {
        "result_class": "decisive_history_source_retarget_smoke",
        "checkpoint": str(checkpoint),
        "spec_count": len(retargets),
        "source_family_count": len({item.hook_spec.source_family for item in retargets}),
        "retarget_mode_count": len({item.retarget_mode for item in retargets}),
        "max_rollout_steps": int(max_rollout_steps),
        "trace_row_count": len(traces),
        "snapshot_row_count": len(snapshots),
        "rollout_success_count": sum(1 for row in attempts if row.failure_type == "none"),
        "rollout_failure_count": sum(1 for row in attempts if row.failure_type != "none"),
        "failure_type_counts": dict(sorted(failure_counts.items())),
        "baseline_min_margin_by_source_family": dict(sorted(baseline_min_margins.items())),
        "retarget_min_margin_by_source_family": dict(sorted(retarget_min.items())),
        "margin_reduction_by_source_family": dict(sorted(reductions.items())),
        "margin_reduction_fraction_by_source_family": dict(sorted(reduction_fraction.items())),
        "global_min_margin": float(min(finite_margins)) if finite_margins else None,
        "near_boundary_proxy_count": _near_boundary_proxy_count(traces),
        "non_aeb_label_source_families": non_aeb_families,
        "non_aeb_label_source_family_count": len(non_aeb_families),
        "source_families_attempted": sorted({row.source_family for row in attempts}),
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
        "labels_enter_actor_input": any(item.hook_spec.labels_enter_actor_input for item in retargets),
        "level3_self_id_claim_made": False,
    }


def run_retarget_smoke(
    run_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    baseline_trace_rows: Path | str = DEFAULT_BASELINE_TRACE_ROWS,
    seed_count: int = 1,
    source_family_cap: int = 4,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run a bounded public source retarget smoke."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    baseline_min_margins = load_baseline_min_margins(baseline_trace_rows)
    retargets = build_retarget_specs(seed_count=seed_count, source_family_cap=source_family_cap)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, retargets[0].hook_spec.env_config)

    traces: list[SourceTraceRow] = []
    snapshots: list[SourceSnapshotRow] = []
    attempts: list[SourceAttemptSummary] = []
    for retargeted in retargets:
        source_rows, attempt = run_source_trace(retargeted.hook_spec, policy, max_rollout_steps=max_rollout_steps)
        traces.extend(source_rows)
        attempts.append(attempt)
        snapshots.extend(build_snapshot_rows(source_rows, attempt))

    summary = build_retarget_summary(
        checkpoint=checkpoint,
        retargets=retargets,
        traces=traces,
        snapshots=snapshots,
        attempts=attempts,
        baseline_min_margins=baseline_min_margins,
        max_rollout_steps=max_rollout_steps,
    )
    write_csv_rows(output / "retarget_spec_rows.csv", [retarget_spec_to_row(item) for item in retargets])
    write_csv_rows(output / "retarget_trace_rows.csv", _asdict_rows(traces))
    write_csv_rows(output / "retarget_snapshot_rows.csv", _asdict_rows(snapshots))
    write_csv_rows(output / "retarget_source_family_summary.csv", _attempt_rows(attempts, retargets))
    write_csv_rows(output / "retarget_guardrail_summary.csv", _guardrail_rows(retargets))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded decisive-history source retarget smoke.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--baseline-trace-rows", type=Path, default=DEFAULT_BASELINE_TRACE_ROWS)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--source-family-cap", type=int, default=4)
    parser.add_argument("--max-rollout-steps", type=int, default=DEFAULT_MAX_ROLLOUT_STEPS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_retarget_smoke(
        args.run_dir,
        checkpoint=args.checkpoint,
        baseline_trace_rows=args.baseline_trace_rows,
        seed_count=int(args.seed_count),
        source_family_cap=int(args.source_family_cap),
        max_rollout_steps=int(args.max_rollout_steps),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"trace_row_count={summary['trace_row_count']}")
    print(f"global_min_margin={summary['global_min_margin']}")
    print(f"rollout_failure_count={summary['rollout_failure_count']}")


if __name__ == "__main__":
    main()
