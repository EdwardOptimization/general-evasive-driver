"""No-training scaffolding for decisive history-necessity tasks.

The module is intentionally small and metadata-only. It defines the public
T4/T5 task contract, diagnostics, and acceptance predicates without touching
the simulator, actor inputs, replay, PPO, or checkpoint state.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import math
from pathlib import Path
from typing import Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json


TASK_FAMILIES = ("T4", "T5")
INTERVENTIONS = (
    "normal",
    "current_tiled",
    "reset",
    "delayed",
    "wrong_history",
    "zero_response",
    "zero_action_history",
)
HISTORY_INTERVENTIONS = (
    "current_tiled",
    "reset",
    "delayed",
    "wrong_history",
)


@dataclass(frozen=True)
class DecisiveHistoryThresholds:
    """Public development thresholds for T4/T5 candidate acceptance."""

    max_current_distance: float = 0.05
    max_recent_window_distance: float = 0.05
    min_older_history_distance: float = 0.10
    min_action_divergence: float = 0.03
    min_margin_gap: float = 0.02
    near_pass_margin_min: float = 0.0005
    near_pass_margin_max: float = 0.03


@dataclass(frozen=True)
class DecisiveHistoryTaskCandidate:
    """Metadata for a public decisive-history task candidate."""

    task_family: str
    candidate_id: str
    seed: int
    capability_pair: str
    reveal_step: int
    decision_step: int
    geometry_key: str
    current_distance: float
    recent_window_distance: float
    older_history_distance: float
    normal_margin: float
    action_divergence: float = 0.0
    source_key: str = ""
    labels_enter_actor_input: bool = False
    intervention_margins: Mapping[str, float] = field(default_factory=dict)
    intervention_success: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateClassification:
    """Acceptance result for one candidate."""

    candidate_id: str
    task_family: str
    accepted: bool
    reasons: tuple[str, ...]
    max_margin_gap: float
    success_drop_variants: tuple[str, ...]


def _finite(value: float) -> bool:
    return math.isfinite(float(value))


def candidate_source_key(candidate: DecisiveHistoryTaskCandidate) -> str:
    """Return a stable source key for diversity summaries."""

    if candidate.source_key:
        return str(candidate.source_key)
    return (
        f"{candidate.seed}|{candidate.capability_pair}|"
        f"{candidate.reveal_step}|{candidate.geometry_key}"
    )


def validate_candidate(candidate: DecisiveHistoryTaskCandidate) -> list[str]:
    """Validate metadata without interpreting task success."""

    errors: list[str] = []
    if candidate.task_family not in TASK_FAMILIES:
        errors.append("unknown_task_family")
    if not candidate.candidate_id:
        errors.append("missing_candidate_id")
    if not candidate.capability_pair:
        errors.append("missing_capability_pair")
    if not candidate.geometry_key:
        errors.append("missing_geometry_key")
    if int(candidate.seed) < 0:
        errors.append("negative_seed")
    if int(candidate.reveal_step) < 0:
        errors.append("negative_reveal_step")
    if int(candidate.decision_step) < 0:
        errors.append("negative_decision_step")
    if int(candidate.decision_step) < int(candidate.reveal_step):
        errors.append("decision_before_reveal")
    for field_name in (
        "current_distance",
        "recent_window_distance",
        "older_history_distance",
        "normal_margin",
        "action_divergence",
    ):
        if not _finite(float(getattr(candidate, field_name))):
            errors.append(f"non_finite_{field_name}")
    for variant, margin in candidate.intervention_margins.items():
        if variant not in INTERVENTIONS:
            errors.append(f"unknown_intervention_{variant}")
        if not _finite(float(margin)):
            errors.append(f"non_finite_margin_{variant}")
    for variant in candidate.intervention_success:
        if variant not in INTERVENTIONS:
            errors.append(f"unknown_success_intervention_{variant}")
    if candidate.labels_enter_actor_input:
        errors.append("labels_enter_actor_input")
    return errors


def margin_gap(candidate: DecisiveHistoryTaskCandidate, variant: str) -> float:
    """Return positive gap when normal history has higher terminal margin."""

    margin = candidate.intervention_margins.get(variant)
    if margin is None:
        return 0.0
    return float(candidate.normal_margin) - float(margin)


def success_drop_variants(candidate: DecisiveHistoryTaskCandidate) -> tuple[str, ...]:
    """Return interventions that turn a normal success into failure."""

    normal_success = bool(
        candidate.intervention_success.get("normal", float(candidate.normal_margin) > 0.0)
    )
    if not normal_success:
        return ()
    drops: list[str] = []
    for variant in INTERVENTIONS:
        if variant == "normal":
            continue
        variant_success = candidate.intervention_success.get(variant)
        if variant_success is None:
            variant_success = candidate.intervention_margins.get(variant, 1.0) > 0.0
        if not bool(variant_success):
            drops.append(variant)
    return tuple(drops)


def _max_history_margin_gap(candidate: DecisiveHistoryTaskCandidate) -> float:
    return max((margin_gap(candidate, variant) for variant in HISTORY_INTERVENTIONS), default=0.0)


def classify_candidate(
    candidate: DecisiveHistoryTaskCandidate,
    thresholds: DecisiveHistoryThresholds | None = None,
) -> CandidateClassification:
    """Classify a T4 or T5 candidate under public development thresholds."""

    thresholds = thresholds or DecisiveHistoryThresholds()
    reasons = validate_candidate(candidate)
    drops = success_drop_variants(candidate)
    max_gap = _max_history_margin_gap(candidate)

    if candidate.task_family == "T4":
        if float(candidate.current_distance) > thresholds.max_current_distance:
            reasons.append("current_distance_too_large")
        if float(candidate.recent_window_distance) > thresholds.max_recent_window_distance:
            reasons.append("recent_window_distance_too_large")
        if float(candidate.older_history_distance) < thresholds.min_older_history_distance:
            reasons.append("older_history_distance_too_small")
        if float(candidate.action_divergence) < thresholds.min_action_divergence:
            reasons.append("action_divergence_too_small")
        wrong_gap = margin_gap(candidate, "wrong_history")
        if wrong_gap < thresholds.min_margin_gap and "wrong_history" not in drops:
            reasons.append("wrong_history_not_outcome_relevant")
    elif candidate.task_family == "T5":
        normal_margin = float(candidate.normal_margin)
        if normal_margin < thresholds.near_pass_margin_min:
            reasons.append("normal_margin_below_near_pass_band")
        if normal_margin > thresholds.near_pass_margin_max:
            reasons.append("normal_margin_above_near_pass_band")
        if max_gap < thresholds.min_margin_gap and not drops:
            reasons.append("history_interventions_not_outcome_relevant")

    return CandidateClassification(
        candidate_id=candidate.candidate_id,
        task_family=candidate.task_family,
        accepted=not reasons,
        reasons=tuple(reasons),
        max_margin_gap=max_gap,
        success_drop_variants=drops,
    )


def source_diversity_summary(candidates: Sequence[DecisiveHistoryTaskCandidate]) -> dict[str, float | int]:
    """Summarize candidate source diversity for public-gate diagnostics."""

    rows = list(candidates)
    source_counts = Counter(candidate_source_key(row) for row in rows)
    max_source_rows = max(source_counts.values(), default=0)
    total = len(rows)
    return {
        "total_candidates": total,
        "unique_seeds": len({row.seed for row in rows}),
        "unique_capability_pairs": len({row.capability_pair for row in rows}),
        "unique_reveal_steps": len({row.reveal_step for row in rows}),
        "unique_geometry_keys": len({row.geometry_key for row in rows}),
        "unique_source_keys": len(source_counts),
        "max_source_rows": max_source_rows,
        "max_source_share": (float(max_source_rows) / float(total)) if total else 0.0,
    }


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def matching_diagnostics_summary(candidates: Sequence[DecisiveHistoryTaskCandidate]) -> dict[str, float | int]:
    """Summarize current/recent/older-history matching diagnostics."""

    rows = list(candidates)
    current = [float(row.current_distance) for row in rows]
    recent = [float(row.recent_window_distance) for row in rows]
    older = [float(row.older_history_distance) for row in rows]
    return {
        "total_candidates": len(rows),
        "current_distance_mean": _mean(current),
        "current_distance_max": max(current, default=0.0),
        "recent_window_distance_mean": _mean(recent),
        "recent_window_distance_max": max(recent, default=0.0),
        "older_history_distance_mean": _mean(older),
        "older_history_distance_min": min(older, default=0.0),
        "older_history_distance_max": max(older, default=0.0),
    }


def candidate_to_row(
    candidate: DecisiveHistoryTaskCandidate,
    classification: CandidateClassification | None = None,
) -> dict[str, object]:
    """Flatten a candidate for CSV artifacts."""

    classification = classification or classify_candidate(candidate)
    return {
        "candidate_id": candidate.candidate_id,
        "task_family": candidate.task_family,
        "seed": candidate.seed,
        "capability_pair": candidate.capability_pair,
        "reveal_step": candidate.reveal_step,
        "decision_step": candidate.decision_step,
        "geometry_key": candidate.geometry_key,
        "source_key": candidate_source_key(candidate),
        "current_distance": candidate.current_distance,
        "recent_window_distance": candidate.recent_window_distance,
        "older_history_distance": candidate.older_history_distance,
        "normal_margin": candidate.normal_margin,
        "action_divergence": candidate.action_divergence,
        "accepted": classification.accepted,
        "reasons": "|".join(classification.reasons),
        "max_margin_gap": classification.max_margin_gap,
        "success_drop_variants": "|".join(classification.success_drop_variants),
        "wrong_history_margin": candidate.intervention_margins.get("wrong_history", ""),
        "delayed_margin": candidate.intervention_margins.get("delayed", ""),
        "reset_margin": candidate.intervention_margins.get("reset", ""),
        "current_tiled_margin": candidate.intervention_margins.get("current_tiled", ""),
    }


def build_harness_summary(
    candidates: Sequence[DecisiveHistoryTaskCandidate],
    thresholds: DecisiveHistoryThresholds | None = None,
) -> dict[str, object]:
    """Build the no-training decisive-history harness summary."""

    thresholds = thresholds or DecisiveHistoryThresholds()
    rows = list(candidates)
    classifications = [classify_candidate(candidate, thresholds) for candidate in rows]
    accepted = [item for item in classifications if item.accepted]
    validation_errors = [reason for item in classifications for reason in item.reasons]
    return {
        "result_class": "decisive_history_task_harness_summary",
        "task_families": list(TASK_FAMILIES),
        "interventions": list(INTERVENTIONS),
        "candidate_count": len(rows),
        "accepted_count": len(accepted),
        "accepted_t4_count": sum(1 for item in accepted if item.task_family == "T4"),
        "accepted_t5_count": sum(1 for item in accepted if item.task_family == "T5"),
        "validation_error_count": len(validation_errors),
        "validation_reasons": dict(Counter(validation_errors)),
        "matching": matching_diagnostics_summary(rows),
        "source_diversity": source_diversity_summary(rows),
        "thresholds": thresholds,
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "training_corpus_exported": False,
        "labels_enter_actor_input": any(row.labels_enter_actor_input for row in rows),
        "level3_self_id_claim_made": False,
    }


def sample_harness_candidates() -> list[DecisiveHistoryTaskCandidate]:
    """Return deterministic tiny examples for runtime smoke and tests."""

    return [
        DecisiveHistoryTaskCandidate(
            task_family="T4",
            candidate_id="t4-good",
            seed=1500,
            capability_pair="low_mu|high_mu",
            reveal_step=24,
            decision_step=32,
            geometry_key="straight_close_left",
            current_distance=0.02,
            recent_window_distance=0.03,
            older_history_distance=0.28,
            normal_margin=0.08,
            action_divergence=0.06,
            intervention_margins={
                "wrong_history": 0.01,
                "reset": 0.05,
                "current_tiled": 0.04,
            },
        ),
        DecisiveHistoryTaskCandidate(
            task_family="T5",
            candidate_id="t5-good",
            seed=1501,
            capability_pair="brake_low|brake_high",
            reveal_step=28,
            decision_step=36,
            geometry_key="curve_terminal_boundary",
            current_distance=0.04,
            recent_window_distance=0.04,
            older_history_distance=0.14,
            normal_margin=0.012,
            action_divergence=0.04,
            intervention_margins={
                "wrong_history": -0.018,
                "delayed": -0.006,
                "reset": 0.004,
            },
        ),
        DecisiveHistoryTaskCandidate(
            task_family="T4",
            candidate_id="t4-reject-current",
            seed=1502,
            capability_pair="tau_fast|tau_slow",
            reveal_step=20,
            decision_step=24,
            geometry_key="straight_close_right",
            current_distance=0.20,
            recent_window_distance=0.02,
            older_history_distance=0.20,
            normal_margin=0.05,
            action_divergence=0.06,
            intervention_margins={"wrong_history": 0.00},
        ),
    ]


def run_harness_smoke(run_dir: Path | str) -> dict[str, object]:
    """Write a deterministic no-training smoke artifact."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates = sample_harness_candidates()
    classifications = [classify_candidate(candidate) for candidate in candidates]
    rows = [
        candidate_to_row(candidate, classification)
        for candidate, classification in zip(candidates, classifications)
    ]
    summary = build_harness_summary(candidates)
    write_csv_rows(output / "candidate_rows.csv", rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a no-training decisive-history task harness smoke.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/m1500_decisive_history_task_harness_smoke"))
    args = parser.parse_args()
    summary = run_harness_smoke(args.run_dir)
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"accepted_count={summary['accepted_count']}")


if __name__ == "__main__":
    main()
