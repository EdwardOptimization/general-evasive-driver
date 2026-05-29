"""No-training env-hook specs for decisive-history candidate generation."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.decisive_history_candidate_planner import (
    CandidateSourcePlan,
    default_source_plans,
    generate_candidates_from_plan,
    validate_source_plan,
)
from autodrift.decisive_history_tasks import DecisiveHistoryTaskCandidate
from autodrift.dynamics import RandomizationConfig
from autodrift.env import DriftEnvConfig, FrictionStepConfig, ObstacleTaskConfig, WarmupGateConfig


@dataclass(frozen=True)
class DecisiveHistoryEnvHookSpec:
    """Metadata-only hook spec for one future simulator candidate probe."""

    source_family: str
    task_family: str
    seed: int
    candidate_id: str
    capability_pair: str
    geometry_key: str
    reveal_step: int
    decision_step: int
    env_config: DriftEnvConfig
    warmup_mode: str
    capability_variant: str
    obstacle_variant: str
    labels_enter_actor_input: bool = False
    candidate_materialized: bool = False
    simulator_rollout_started: bool = False


@dataclass(frozen=True)
class DecisiveHistoryHookArtifacts:
    """Artifact paths and guardrails for a dry hook smoke."""

    hook_spec_rows: str
    hook_source_family_summary: str
    hook_guardrail_summary: str
    summary: str
    simulator_rollout_started: bool = False
    replay_started: bool = False
    training_started: bool = False
    ppo_used: bool = False
    promoted: bool = False
    private_holdout_used: bool = False
    actor_input_contract_changed: bool = False
    training_corpus_exported: bool = False
    labels_enter_actor_input: bool = False
    level3_self_id_claim_made: bool = False


def _range(center: float, width: float, floor: float = 0.01) -> tuple[float, float]:
    return (max(floor, center - width), max(floor, center + width))


def _randomization_for_family(source_family: str, capability_pair: str) -> RandomizationConfig:
    del capability_pair
    if source_family in {"t4_staged_warmup_capability", "t5_near_boundary_warmup"}:
        return RandomizationConfig(
            mu_range=(0.28, 1.05),
            brake_scale_range=(0.45, 1.35),
            drive_scale_range=(0.75, 1.15),
            tire_stiffness_scale_range=(0.70, 1.25),
            actuator_tau_scale_range=(0.90, 2.20),
        )
    if source_family == "t4_capability_step_temporal":
        return RandomizationConfig(
            mu_range=(0.32, 1.10),
            drive_scale_range=(0.55, 1.35),
            brake_scale_range=(0.55, 1.30),
            tire_stiffness_scale_range=(0.50, 1.45),
            actuator_tau_scale_range=(0.90, 2.00),
        )
    if source_family == "t4_actuator_delay_response":
        return RandomizationConfig(
            mu_range=(0.45, 1.05),
            brake_scale_range=(0.75, 1.20),
            drive_scale_range=(0.75, 1.20),
            tire_stiffness_scale_range=(0.75, 1.20),
            actuator_tau_scale_range=(0.75, 4.20),
        )
    if source_family == "t5_high_speed_close_obstacle":
        return RandomizationConfig(
            mu_range=(0.25, 0.95),
            brake_scale_range=(0.45, 1.20),
            drive_scale_range=(0.70, 1.25),
            tire_stiffness_scale_range=(0.55, 1.35),
            actuator_tau_scale_range=(0.90, 2.80),
        )
    if source_family == "t5_boundary_axis_retarget":
        return RandomizationConfig(
            mu_range=(0.30, 1.05),
            brake_scale_range=(0.55, 1.25),
            drive_scale_range=(0.70, 1.25),
            tire_stiffness_scale_range=(0.50, 1.50),
            actuator_tau_scale_range=(0.80, 3.20),
        )
    return RandomizationConfig()


def _obstacle_config_for_family(source_family: str, reveal_step: int) -> ObstacleTaskConfig:
    common = {
        "enabled": True,
        "finish_on_pass": True,
        "perception_reveal_step": int(reveal_step),
        "max_sample_attempts": 200,
        "clearance_margin_reward_scale": 0.0,
        "dense_clearance_margin_reward_scale": 0.0,
        "allowed_labels": ("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
    }
    if source_family == "t5_high_speed_close_obstacle":
        return ObstacleTaskConfig(
            **common,
            distance_range=(10.0, 22.0),
            half_width_range=(0.75, 1.35),
        )
    if source_family == "t5_boundary_axis_retarget":
        return ObstacleTaskConfig(
            **common,
            distance_range=(12.0, 34.0),
            half_width_range=(0.65, 1.45),
        )
    if source_family == "t5_near_boundary_warmup":
        return ObstacleTaskConfig(
            **common,
            distance_range=(12.0, 30.0),
            half_width_range=(0.65, 1.35),
        )
    return ObstacleTaskConfig(
        **common,
        distance_range=(14.0, 42.0),
        half_width_range=(0.55, 1.20),
    )


def _warmup_config_for_family(source_family: str, reveal_step: int) -> WarmupGateConfig:
    if source_family in {
        "t4_staged_warmup_capability",
        "t4_actuator_delay_response",
        "t5_near_boundary_warmup",
    }:
        return WarmupGateConfig(
            enabled=True,
            distance_range=(8.0, 24.0),
            lateral_offset_range=(-1.4, 1.4),
            half_width_range=(0.35, 0.95),
            reveal_step=max(0, int(reveal_step) - 20),
            max_active_steps=max(16, int(reveal_step) + 12),
            finish_pass_distance=2.0,
        )
    return WarmupGateConfig()


def _friction_step_for_family(source_family: str, reveal_step: int) -> FrictionStepConfig:
    if source_family in {"t4_capability_step_temporal", "t5_high_speed_close_obstacle"}:
        step = max(1, int(reveal_step) - 12)
        return FrictionStepConfig(
            enabled=True,
            step_range=(step, step + 6),
            mu_range=(0.25, 1.05),
            resample_speed_ref=False,
        )
    return FrictionStepConfig()


def env_config_for_hook_spec(
    *,
    source_family: str,
    capability_pair: str,
    reveal_step: int,
) -> DriftEnvConfig:
    """Build a P0-compatible env config for one hook spec."""

    if source_family == "t5_high_speed_close_obstacle":
        speed_range = (14.0, 20.0)
        friction_limited_speed = False
        max_steps = 360
    elif source_family.startswith("t5_"):
        speed_range = (9.0, 16.0)
        friction_limited_speed = True
        max_steps = 420
    else:
        speed_range = (7.0, 14.0)
        friction_limited_speed = True
        max_steps = 480
    return DriftEnvConfig(
        max_steps=max_steps,
        speed_range=speed_range,
        friction_limited_speed=friction_limited_speed,
        history_length=1,
        action_history_mode="full",
        include_privileged_params=False,
        obstacle_relative_velocity_mode="zero",
        wheel_observation_mode="none",
        friction_step=_friction_step_for_family(source_family, reveal_step),
        obstacle=_obstacle_config_for_family(source_family, reveal_step),
        warmup_gate=_warmup_config_for_family(source_family, reveal_step),
        randomization=_randomization_for_family(source_family, capability_pair),
    )


def _warmup_mode(source_family: str) -> str:
    if "warmup" in source_family:
        return "warmup_gate"
    if source_family == "t4_actuator_delay_response":
        return "actuator_response_probe"
    return "none"


def _obstacle_variant(source_family: str, geometry_key: str) -> str:
    if source_family == "t5_boundary_axis_retarget":
        return "boundary_axis_retarget"
    if source_family == "t5_high_speed_close_obstacle":
        return "high_speed_close"
    return str(geometry_key)


def source_plan_to_hook_specs(
    plan: CandidateSourcePlan,
    *,
    max_specs: int | None = None,
) -> list[DecisiveHistoryEnvHookSpec]:
    """Convert one no-training source plan into hook specs."""

    errors = validate_source_plan(plan)
    if errors:
        raise ValueError(f"invalid source plan {plan.source_family!r}: {', '.join(errors)}")
    candidates = generate_candidates_from_plan(plan)
    if max_specs is not None:
        candidates = candidates[: max(0, int(max_specs))]
    specs: list[DecisiveHistoryEnvHookSpec] = []
    for candidate in candidates:
        env_config = env_config_for_hook_spec(
            source_family=plan.source_family,
            capability_pair=candidate.capability_pair,
            reveal_step=candidate.reveal_step,
        )
        specs.append(
            DecisiveHistoryEnvHookSpec(
                source_family=plan.source_family,
                task_family=candidate.task_family,
                seed=int(candidate.seed),
                candidate_id=str(candidate.candidate_id),
                capability_pair=str(candidate.capability_pair),
                geometry_key=str(candidate.geometry_key),
                reveal_step=int(candidate.reveal_step),
                decision_step=int(candidate.decision_step),
                env_config=env_config,
                warmup_mode=_warmup_mode(plan.source_family),
                capability_variant=str(candidate.capability_pair).replace("|", "_vs_"),
                obstacle_variant=_obstacle_variant(plan.source_family, str(candidate.geometry_key)),
                labels_enter_actor_input=bool(candidate.labels_enter_actor_input),
                candidate_materialized=False,
                simulator_rollout_started=False,
            )
        )
    return specs


def default_hook_specs(seed_count: int = 2) -> list[DecisiveHistoryEnvHookSpec]:
    """Return deterministic hook specs for all default source families."""

    specs: list[DecisiveHistoryEnvHookSpec] = []
    for plan in default_source_plans(seed_count=seed_count):
        specs.extend(source_plan_to_hook_specs(plan))
    return specs


def hook_spec_to_candidate_stub(spec: DecisiveHistoryEnvHookSpec) -> DecisiveHistoryTaskCandidate:
    """Return a schema-only candidate stub; it is not simulator evidence."""

    return DecisiveHistoryTaskCandidate(
        task_family=spec.task_family,
        candidate_id=spec.candidate_id,
        seed=spec.seed,
        capability_pair=spec.capability_pair,
        reveal_step=spec.reveal_step,
        decision_step=spec.decision_step,
        geometry_key=spec.geometry_key,
        current_distance=0.0,
        recent_window_distance=0.0,
        older_history_distance=0.0,
        normal_margin=0.0,
        action_divergence=0.0,
        source_key=f"{spec.source_family}|{spec.seed}|{spec.capability_pair}|{spec.geometry_key}|{spec.reveal_step}",
        labels_enter_actor_input=spec.labels_enter_actor_input,
    )


def hook_spec_to_row(spec: DecisiveHistoryEnvHookSpec) -> dict[str, object]:
    """Flatten a hook spec for CSV artifacts."""

    cfg = spec.env_config
    return {
        "source_family": spec.source_family,
        "task_family": spec.task_family,
        "seed": spec.seed,
        "candidate_id": spec.candidate_id,
        "capability_pair": spec.capability_pair,
        "geometry_key": spec.geometry_key,
        "reveal_step": spec.reveal_step,
        "decision_step": spec.decision_step,
        "warmup_mode": spec.warmup_mode,
        "capability_variant": spec.capability_variant,
        "obstacle_variant": spec.obstacle_variant,
        "history_length": cfg.history_length,
        "action_history_mode": cfg.action_history_mode,
        "include_privileged_params": cfg.include_privileged_params,
        "obstacle_relative_velocity_mode": cfg.obstacle_relative_velocity_mode,
        "wheel_observation_mode": cfg.wheel_observation_mode,
        "speed_range": f"{cfg.speed_range[0]:.3f}|{cfg.speed_range[1]:.3f}",
        "friction_step_enabled": cfg.friction_step.enabled,
        "warmup_gate_enabled": cfg.warmup_gate.enabled,
        "obstacle_enabled": cfg.obstacle.enabled,
        "obstacle_distance_range": f"{cfg.obstacle.distance_range[0]:.3f}|{cfg.obstacle.distance_range[1]:.3f}",
        "obstacle_half_width_range": f"{cfg.obstacle.half_width_range[0]:.3f}|{cfg.obstacle.half_width_range[1]:.3f}",
        "obstacle_perception_reveal_step": cfg.obstacle.perception_reveal_step,
        "labels_enter_actor_input": spec.labels_enter_actor_input,
        "candidate_materialized": spec.candidate_materialized,
        "simulator_rollout_started": spec.simulator_rollout_started,
    }


def _source_family_summary(specs: Sequence[DecisiveHistoryEnvHookSpec]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_family: dict[str, list[DecisiveHistoryEnvHookSpec]] = {}
    for spec in specs:
        by_family.setdefault(spec.source_family, []).append(spec)
    for family, family_specs in sorted(by_family.items()):
        rows.append(
            {
                "source_family": family,
                "spec_rows": len(family_specs),
                "task_family": family_specs[0].task_family if family_specs else "",
                "unique_seeds": len({spec.seed for spec in family_specs}),
                "unique_capability_pairs": len({spec.capability_pair for spec in family_specs}),
                "unique_geometry_keys": len({spec.geometry_key for spec in family_specs}),
                "friction_step_enabled_rows": sum(1 for spec in family_specs if spec.env_config.friction_step.enabled),
                "warmup_gate_enabled_rows": sum(1 for spec in family_specs if spec.env_config.warmup_gate.enabled),
            }
        )
    return rows


def _guardrail_rows(specs: Sequence[DecisiveHistoryEnvHookSpec]) -> list[dict[str, object]]:
    guardrails = {
        "labels_enter_actor_input": any(spec.labels_enter_actor_input for spec in specs),
        "candidate_materialized": any(spec.candidate_materialized for spec in specs),
        "simulator_rollout_started": any(spec.simulator_rollout_started for spec in specs),
        "include_privileged_params": any(spec.env_config.include_privileged_params for spec in specs),
        "uses_wheel_observation": any(spec.env_config.wheel_observation_mode != "none" for spec in specs),
        "nonzero_obstacle_relative_velocity": any(
            spec.env_config.obstacle_relative_velocity_mode != "zero" for spec in specs
        ),
    }
    return [{"guardrail": key, "violated": bool(value)} for key, value in sorted(guardrails.items())]


def build_env_hook_summary(specs: Sequence[DecisiveHistoryEnvHookSpec]) -> dict[str, object]:
    """Build a no-training env-hook dry-smoke summary."""

    rows = list(specs)
    family_counts = Counter(spec.source_family for spec in rows)
    task_counts = Counter(spec.task_family for spec in rows)
    guardrails = _guardrail_rows(rows)
    return {
        "result_class": "decisive_history_env_hook_dry_smoke",
        "hook_spec_count": len(rows),
        "source_family_count": len(family_counts),
        "source_family_spec_counts": dict(sorted(family_counts.items())),
        "task_family_counts": dict(sorted(task_counts.items())),
        "unique_seeds": len({spec.seed for spec in rows}),
        "unique_capability_pairs": len({spec.capability_pair for spec in rows}),
        "unique_geometry_keys": len({spec.geometry_key for spec in rows}),
        "unique_reveal_steps": len({spec.reveal_step for spec in rows}),
        "guardrail_violation_count": sum(1 for row in guardrails if row["violated"]),
        "labels_enter_actor_input": any(spec.labels_enter_actor_input for spec in rows),
        "candidate_materialized": any(spec.candidate_materialized for spec in rows),
        "simulator_rollout_started": any(spec.simulator_rollout_started for spec in rows),
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "training_corpus_exported": False,
        "level3_self_id_claim_made": False,
    }


def run_env_hook_dry_smoke(run_dir: Path | str, *, seed_count: int = 2) -> dict[str, object]:
    """Write hook/spec artifacts without simulator rollout."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = default_hook_specs(seed_count=seed_count)
    spec_rows = [hook_spec_to_row(spec) for spec in specs]
    family_rows = _source_family_summary(specs)
    guardrail_rows = _guardrail_rows(specs)
    summary = build_env_hook_summary(specs)
    artifacts = DecisiveHistoryHookArtifacts(
        hook_spec_rows=str(output / "hook_spec_rows.csv"),
        hook_source_family_summary=str(output / "hook_source_family_summary.csv"),
        hook_guardrail_summary=str(output / "hook_guardrail_summary.csv"),
        summary=str(output / "summary.json"),
        labels_enter_actor_input=bool(summary["labels_enter_actor_input"]),
        simulator_rollout_started=bool(summary["simulator_rollout_started"]),
    )
    summary["artifacts"] = artifacts

    write_csv_rows(output / "hook_spec_rows.csv", spec_rows)
    write_csv_rows(output / "hook_source_family_summary.csv", family_rows)
    write_csv_rows(output / "hook_guardrail_summary.csv", guardrail_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training decisive-history env-hook dry smoke.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/m1505_decisive_history_env_hook_dry_smoke"))
    parser.add_argument("--seed-count", type=int, default=2)
    args = parser.parse_args()
    summary = run_env_hook_dry_smoke(args.run_dir, seed_count=int(args.seed_count))
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"hook_spec_count={summary['hook_spec_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
