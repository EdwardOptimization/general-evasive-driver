"""No-training source-plan planner for decisive-history candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.decisive_history_tasks import (
    DecisiveHistoryTaskCandidate,
    DecisiveHistoryThresholds,
    build_harness_summary,
    candidate_to_row,
    classify_candidate,
)


@dataclass(frozen=True)
class CandidateSourcePlan:
    """Public no-training source plan for one T4/T5 candidate family."""

    source_family: str
    task_family: str
    seed_base: int
    seed_count: int
    capability_pairs: tuple[str, ...]
    geometry_keys: tuple[str, ...]
    reveal_steps: tuple[int, ...]
    decision_step_offset: int = 8
    current_distance: float = 0.02
    recent_window_distance: float = 0.03
    older_history_distance: float = 0.20
    normal_margin: float = 0.05
    action_divergence: float = 0.05
    labels_enter_actor_input: bool = False
    intervention_margins: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidatePlannerConfig:
    """Configuration for metadata-only candidate planning."""

    source_plans: tuple[CandidateSourcePlan, ...]
    thresholds: DecisiveHistoryThresholds = field(default_factory=DecisiveHistoryThresholds)
    private_holdout_used: bool = False
    actor_input_contract_changed: bool = False


def default_source_plans(seed_count: int = 2) -> tuple[CandidateSourcePlan, ...]:
    """Return the M1501 public source-family plan in deterministic smoke form."""

    return (
        CandidateSourcePlan(
            source_family="t4_staged_warmup_capability",
            task_family="T4",
            seed_base=150100,
            seed_count=seed_count,
            capability_pairs=("low_mu|high_mu", "brake_low|brake_high"),
            geometry_keys=("straight_close_left", "curve_close_right"),
            reveal_steps=(24, 32),
            older_history_distance=0.28,
            normal_margin=0.08,
            action_divergence=0.06,
            intervention_margins={"wrong_history": 0.01, "reset": 0.05, "current_tiled": 0.04},
        ),
        CandidateSourcePlan(
            source_family="t4_capability_step_temporal",
            task_family="T4",
            seed_base=150120,
            seed_count=seed_count,
            capability_pairs=("drive_low|drive_high", "tire_soft|tire_stiff"),
            geometry_keys=("late_reveal_left", "late_reveal_right"),
            reveal_steps=(28, 36),
            older_history_distance=0.22,
            normal_margin=0.06,
            action_divergence=0.05,
            intervention_margins={"wrong_history": 0.00, "delayed": 0.03},
        ),
        CandidateSourcePlan(
            source_family="t4_actuator_delay_response",
            task_family="T4",
            seed_base=150140,
            seed_count=seed_count,
            capability_pairs=("tau_fast|tau_slow", "steer_fast|steer_slow"),
            geometry_keys=("actuator_curve_left", "actuator_curve_right"),
            reveal_steps=(30, 38),
            older_history_distance=0.24,
            normal_margin=0.07,
            action_divergence=0.055,
            intervention_margins={"wrong_history": 0.015, "delayed": 0.02},
        ),
        CandidateSourcePlan(
            source_family="t5_near_boundary_warmup",
            task_family="T5",
            seed_base=150200,
            seed_count=seed_count,
            capability_pairs=("low_mu|high_mu", "brake_low|brake_high"),
            geometry_keys=("near_boundary_left", "near_boundary_right"),
            reveal_steps=(34, 42),
            older_history_distance=0.18,
            normal_margin=0.012,
            action_divergence=0.04,
            intervention_margins={"wrong_history": -0.014, "reset": 0.002, "current_tiled": 0.006},
        ),
        CandidateSourcePlan(
            source_family="t5_high_speed_close_obstacle",
            task_family="T5",
            seed_base=150220,
            seed_count=seed_count,
            capability_pairs=("speed_high_low_mu|speed_high_high_mu", "brake_low|brake_high"),
            geometry_keys=("high_speed_left", "high_speed_right"),
            reveal_steps=(18, 22),
            older_history_distance=0.16,
            normal_margin=0.018,
            action_divergence=0.045,
            intervention_margins={"wrong_history": -0.006, "delayed": -0.012},
        ),
        CandidateSourcePlan(
            source_family="t5_boundary_axis_retarget",
            task_family="T5",
            seed_base=150240,
            seed_count=seed_count,
            capability_pairs=("understeer|oversteer", "tau_fast|tau_slow"),
            geometry_keys=("boundary_axis_left", "boundary_axis_right"),
            reveal_steps=(40, 48),
            older_history_distance=0.19,
            normal_margin=0.010,
            action_divergence=0.035,
            intervention_margins={"wrong_history": -0.011, "reset": -0.004, "delayed": 0.001},
        ),
    )


def validate_source_plan(plan: CandidateSourcePlan) -> list[str]:
    """Validate source-plan schema without simulator execution."""

    errors: list[str] = []
    if not plan.source_family:
        errors.append("missing_source_family")
    if plan.task_family not in {"T4", "T5"}:
        errors.append("unknown_task_family")
    if int(plan.seed_base) < 0:
        errors.append("negative_seed_base")
    if int(plan.seed_count) <= 0:
        errors.append("nonpositive_seed_count")
    if not plan.capability_pairs:
        errors.append("missing_capability_pairs")
    if not plan.geometry_keys:
        errors.append("missing_geometry_keys")
    if not plan.reveal_steps:
        errors.append("missing_reveal_steps")
    if int(plan.decision_step_offset) <= 0:
        errors.append("nonpositive_decision_step_offset")
    if plan.labels_enter_actor_input:
        errors.append("labels_enter_actor_input")
    return errors


def source_plan_to_row(plan: CandidateSourcePlan) -> dict[str, object]:
    """Flatten one source plan for CSV artifacts."""

    return {
        "source_family": plan.source_family,
        "task_family": plan.task_family,
        "seed_base": plan.seed_base,
        "seed_count": plan.seed_count,
        "capability_pairs": "|".join(plan.capability_pairs),
        "geometry_keys": "|".join(plan.geometry_keys),
        "reveal_steps": "|".join(str(step) for step in plan.reveal_steps),
        "decision_step_offset": plan.decision_step_offset,
        "labels_enter_actor_input": plan.labels_enter_actor_input,
    }


def generate_candidates_from_plan(plan: CandidateSourcePlan) -> list[DecisiveHistoryTaskCandidate]:
    """Generate deterministic metadata candidates from a source plan."""

    errors = validate_source_plan(plan)
    if errors:
        raise ValueError(f"invalid source plan {plan.source_family!r}: {', '.join(errors)}")
    candidates: list[DecisiveHistoryTaskCandidate] = []
    for index in range(int(plan.seed_count)):
        seed = int(plan.seed_base) + index
        capability_pair = plan.capability_pairs[index % len(plan.capability_pairs)]
        geometry_key = plan.geometry_keys[index % len(plan.geometry_keys)]
        reveal_step = int(plan.reveal_steps[index % len(plan.reveal_steps)])
        candidate_id = f"{plan.source_family}-{index:03d}"
        source_key = f"{plan.source_family}|{seed}|{capability_pair}|{geometry_key}|{reveal_step}"
        candidates.append(
            DecisiveHistoryTaskCandidate(
                task_family=plan.task_family,
                candidate_id=candidate_id,
                seed=seed,
                capability_pair=capability_pair,
                reveal_step=reveal_step,
                decision_step=reveal_step + int(plan.decision_step_offset),
                geometry_key=geometry_key,
                current_distance=float(plan.current_distance),
                recent_window_distance=float(plan.recent_window_distance),
                older_history_distance=float(plan.older_history_distance),
                normal_margin=float(plan.normal_margin),
                action_divergence=float(plan.action_divergence),
                source_key=source_key,
                labels_enter_actor_input=bool(plan.labels_enter_actor_input),
                intervention_margins=dict(plan.intervention_margins),
            )
        )
    return candidates


def generate_candidates(config: CandidatePlannerConfig) -> list[DecisiveHistoryTaskCandidate]:
    """Generate deterministic metadata candidates for all source plans."""

    candidates: list[DecisiveHistoryTaskCandidate] = []
    for plan in config.source_plans:
        candidates.extend(generate_candidates_from_plan(plan))
    return candidates


def _source_family_summary(candidates: Sequence[DecisiveHistoryTaskCandidate]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_family: dict[str, list[DecisiveHistoryTaskCandidate]] = {}
    for candidate in candidates:
        family = str(candidate.source_key).split("|", maxsplit=1)[0]
        by_family.setdefault(family, []).append(candidate)
    for family, family_rows in sorted(by_family.items()):
        classifications = [classify_candidate(row) for row in family_rows]
        rows.append(
            {
                "source_family": family,
                "candidate_rows": len(family_rows),
                "accepted_rows": sum(1 for item in classifications if item.accepted),
                "task_family": family_rows[0].task_family if family_rows else "",
                "unique_seeds": len({row.seed for row in family_rows}),
                "unique_capability_pairs": len({row.capability_pair for row in family_rows}),
                "unique_geometry_keys": len({row.geometry_key for row in family_rows}),
            }
        )
    return rows


def build_planner_summary(
    config: CandidatePlannerConfig,
    candidates: Sequence[DecisiveHistoryTaskCandidate],
) -> dict[str, object]:
    """Build a no-training planner summary."""

    harness_summary = build_harness_summary(candidates, thresholds=config.thresholds)
    family_counts = Counter(str(row.source_key).split("|", maxsplit=1)[0] for row in candidates)
    summary: dict[str, object] = {
        "result_class": "decisive_history_candidate_planner_summary",
        "source_plan_count": len(config.source_plans),
        "source_families": [plan.source_family for plan in config.source_plans],
        "task_family_counts": dict(Counter(plan.task_family for plan in config.source_plans)),
        "source_family_candidate_counts": dict(sorted(family_counts.items())),
        "generated_candidate_rows": len(candidates),
        "harness": harness_summary,
        "private_holdout_used": bool(config.private_holdout_used),
        "actor_input_contract_changed": bool(config.actor_input_contract_changed),
        "labels_enter_actor_input": any(row.labels_enter_actor_input for row in candidates),
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "training_corpus_exported": False,
        "level3_self_id_claim_made": False,
    }
    return summary


def run_candidate_planner_smoke(
    run_dir: Path | str,
    *,
    seed_count: int = 2,
) -> dict[str, object]:
    """Run deterministic no-training candidate planner smoke."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    config = CandidatePlannerConfig(source_plans=default_source_plans(seed_count=seed_count))
    candidates = generate_candidates(config)
    classifications = [classify_candidate(candidate, thresholds=config.thresholds) for candidate in candidates]
    candidate_rows = [
        candidate_to_row(candidate, classification)
        for candidate, classification in zip(candidates, classifications)
    ]
    source_plan_rows = [source_plan_to_row(plan) for plan in config.source_plans]
    family_rows = _source_family_summary(candidates)
    summary = build_planner_summary(config, candidates)

    write_csv_rows(output / "source_plan_rows.csv", source_plan_rows)
    write_csv_rows(output / "candidate_rows.csv", candidate_rows)
    write_csv_rows(output / "source_family_summary.csv", family_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training decisive-history candidate planner smoke.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/m1502_decisive_history_candidate_planner_smoke"))
    parser.add_argument("--seed-count", type=int, default=2)
    args = parser.parse_args()
    summary = run_candidate_planner_smoke(args.run_dir, seed_count=int(args.seed_count))
    harness = summary["harness"]
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"generated_candidate_rows={summary['generated_candidate_rows']}")
    print(f"accepted_count={harness['accepted_count']}")


if __name__ == "__main__":
    main()
