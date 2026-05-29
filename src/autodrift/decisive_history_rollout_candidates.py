"""Scaffolding for measured decisive-history rollout candidates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.decisive_history_tasks import (
    DecisiveHistoryTaskCandidate,
    DecisiveHistoryThresholds,
    build_harness_summary,
    candidate_to_row,
    classify_candidate,
)


INTERVENTION_VARIANTS = (
    "normal",
    "reset",
    "delayed",
    "wrong_history",
    "current_tiled",
    "zero_response",
    "zero_action_history",
)


@dataclass(frozen=True)
class RolloutCandidateMeasurement:
    """Measured quantities needed before materializing a T4/T5 candidate."""

    task_family: str
    candidate_id: str
    seed: int
    source_family: str
    capability_pair: str
    reveal_step: int
    decision_step: int
    geometry_key: str
    current_distance: float
    recent_window_distance: float
    older_history_distance: float
    normal_margin: float
    action_divergence: float
    intervention_margins: Mapping[str, float] = field(default_factory=dict)
    intervention_success: Mapping[str, bool] = field(default_factory=dict)
    measured_from_rollout: bool = True
    reset_only_source: bool = False
    labels_enter_actor_input: bool = False


@dataclass(frozen=True)
class CandidateMaterializationResult:
    """Materialization decision for one measured row."""

    accepted: bool
    candidate: DecisiveHistoryTaskCandidate | None
    rejection_reasons: tuple[str, ...]


def normalized_l2(left: Sequence[float], right: Sequence[float]) -> float:
    """Return scale-normalized L2 distance for finite equal-shaped arrays."""

    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.shape != right_array.shape:
        raise ValueError(f"distance shapes differ: {left_array.shape} vs {right_array.shape}")
    if left_array.size == 0:
        return 0.0
    if not np.all(np.isfinite(left_array)) or not np.all(np.isfinite(right_array)):
        raise ValueError("distance inputs must be finite")
    return float(np.linalg.norm(left_array - right_array) / np.sqrt(float(left_array.size)))


def current_frame_distance(left_observation: Sequence[float], right_observation: Sequence[float]) -> float:
    """Distance over deployable current-frame observation features."""

    return normalized_l2(left_observation, right_observation)


def history_window_distance(left_window: Sequence[Sequence[float]], right_window: Sequence[Sequence[float]]) -> float:
    """Distance over a recent or older command-response window."""

    return normalized_l2(np.asarray(left_window, dtype=np.float64), np.asarray(right_window, dtype=np.float64))


def action_sequence_divergence(left_actions: Sequence[Sequence[float]], right_actions: Sequence[Sequence[float]]) -> float:
    """Distance over rollout action prefixes."""

    return normalized_l2(np.asarray(left_actions, dtype=np.float64), np.asarray(right_actions, dtype=np.float64))


def _candidate_source_key(measurement: RolloutCandidateMeasurement) -> str:
    return (
        f"{measurement.source_family}|{measurement.seed}|{measurement.capability_pair}|"
        f"{measurement.geometry_key}|{measurement.reveal_step}"
    )


def _candidate_from_measurement(measurement: RolloutCandidateMeasurement) -> DecisiveHistoryTaskCandidate:
    return DecisiveHistoryTaskCandidate(
        task_family=measurement.task_family,
        candidate_id=measurement.candidate_id,
        seed=measurement.seed,
        capability_pair=measurement.capability_pair,
        reveal_step=measurement.reveal_step,
        decision_step=measurement.decision_step,
        geometry_key=measurement.geometry_key,
        current_distance=measurement.current_distance,
        recent_window_distance=measurement.recent_window_distance,
        older_history_distance=measurement.older_history_distance,
        normal_margin=measurement.normal_margin,
        action_divergence=measurement.action_divergence,
        source_key=_candidate_source_key(measurement),
        labels_enter_actor_input=measurement.labels_enter_actor_input,
        intervention_margins=dict(measurement.intervention_margins),
        intervention_success=dict(measurement.intervention_success),
    )


def materialize_candidate(
    measurement: RolloutCandidateMeasurement,
    *,
    thresholds: DecisiveHistoryThresholds | None = None,
) -> CandidateMaterializationResult:
    """Materialize only measured rollout evidence, never reset-only evidence."""

    reasons: list[str] = []
    if not measurement.measured_from_rollout:
        reasons.append("not_measured_from_rollout")
    if measurement.reset_only_source:
        reasons.append("reset_only_source")
    if measurement.labels_enter_actor_input:
        reasons.append("labels_enter_actor_input")
    candidate = _candidate_from_measurement(measurement)
    classification = classify_candidate(candidate, thresholds)
    reasons.extend(classification.reasons)
    accepted = not reasons
    return CandidateMaterializationResult(
        accepted=accepted,
        candidate=candidate if accepted else None,
        rejection_reasons=tuple(reasons),
    )


def measurement_to_row(
    measurement: RolloutCandidateMeasurement,
    result: CandidateMaterializationResult,
) -> dict[str, object]:
    """Flatten a measured row and materialization decision."""

    return {
        "candidate_id": measurement.candidate_id,
        "task_family": measurement.task_family,
        "seed": measurement.seed,
        "source_family": measurement.source_family,
        "capability_pair": measurement.capability_pair,
        "reveal_step": measurement.reveal_step,
        "decision_step": measurement.decision_step,
        "geometry_key": measurement.geometry_key,
        "current_distance": measurement.current_distance,
        "recent_window_distance": measurement.recent_window_distance,
        "older_history_distance": measurement.older_history_distance,
        "normal_margin": measurement.normal_margin,
        "action_divergence": measurement.action_divergence,
        "wrong_history_margin": measurement.intervention_margins.get("wrong_history", ""),
        "delayed_margin": measurement.intervention_margins.get("delayed", ""),
        "reset_margin": measurement.intervention_margins.get("reset", ""),
        "current_tiled_margin": measurement.intervention_margins.get("current_tiled", ""),
        "measured_from_rollout": measurement.measured_from_rollout,
        "reset_only_source": measurement.reset_only_source,
        "labels_enter_actor_input": measurement.labels_enter_actor_input,
        "materialized": result.accepted,
        "rejection_reasons": "|".join(result.rejection_reasons),
    }


def synthetic_rollout_measurements() -> list[RolloutCandidateMeasurement]:
    """Tiny deterministic measurements for scaffolding smoke and tests."""

    return [
        RolloutCandidateMeasurement(
            task_family="T4",
            candidate_id="synthetic-t4-measured",
            seed=150800,
            source_family="t4_staged_warmup_capability",
            capability_pair="low_mu|high_mu",
            reveal_step=24,
            decision_step=32,
            geometry_key="straight_close_left",
            current_distance=0.02,
            recent_window_distance=0.03,
            older_history_distance=0.26,
            normal_margin=0.08,
            action_divergence=0.06,
            intervention_margins={"wrong_history": 0.01, "reset": 0.04},
        ),
        RolloutCandidateMeasurement(
            task_family="T5",
            candidate_id="synthetic-t5-measured",
            seed=150801,
            source_family="t5_near_boundary_warmup",
            capability_pair="brake_low|brake_high",
            reveal_step=34,
            decision_step=42,
            geometry_key="near_boundary_left",
            current_distance=0.04,
            recent_window_distance=0.04,
            older_history_distance=0.18,
            normal_margin=0.012,
            action_divergence=0.04,
            intervention_margins={"wrong_history": -0.014, "delayed": -0.010},
        ),
        RolloutCandidateMeasurement(
            task_family="T4",
            candidate_id="synthetic-reset-only-rejected",
            seed=150802,
            source_family="t4_capability_step_temporal",
            capability_pair="drive_low|drive_high",
            reveal_step=28,
            decision_step=36,
            geometry_key="late_reveal_left",
            current_distance=0.02,
            recent_window_distance=0.03,
            older_history_distance=0.22,
            normal_margin=0.06,
            action_divergence=0.05,
            intervention_margins={"wrong_history": 0.00},
            measured_from_rollout=False,
            reset_only_source=True,
        ),
    ]


def materialize_measurements(
    measurements: Sequence[RolloutCandidateMeasurement],
    *,
    thresholds: DecisiveHistoryThresholds | None = None,
) -> tuple[list[DecisiveHistoryTaskCandidate], list[dict[str, object]]]:
    """Return accepted candidates and flattened audit rows."""

    candidates: list[DecisiveHistoryTaskCandidate] = []
    rows: list[dict[str, object]] = []
    for measurement in measurements:
        result = materialize_candidate(measurement, thresholds=thresholds)
        if result.candidate is not None:
            candidates.append(result.candidate)
        rows.append(measurement_to_row(measurement, result))
    return candidates, rows


def build_rollout_candidate_summary(
    measurements: Sequence[RolloutCandidateMeasurement],
    candidates: Sequence[DecisiveHistoryTaskCandidate],
    audit_rows: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Build a no-training scaffolding summary."""

    rejection_reasons: dict[str, int] = {}
    for row in audit_rows:
        reasons = str(row.get("rejection_reasons", ""))
        for reason in [item for item in reasons.split("|") if item]:
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
    return {
        "result_class": "decisive_history_rollout_candidate_scaffold_smoke",
        "measurement_count": len(measurements),
        "materialized_candidate_count": len(candidates),
        "rejected_count": len(audit_rows) - len(candidates),
        "rejection_reasons": rejection_reasons,
        "accepted_t4_count": sum(1 for candidate in candidates if candidate.task_family == "T4"),
        "accepted_t5_count": sum(1 for candidate in candidates if candidate.task_family == "T5"),
        "candidate_materialized_from_reset_only": any(
            bool(row["materialized"]) and bool(row["reset_only_source"]) for row in audit_rows
        ),
        "labels_enter_actor_input": any(bool(row["labels_enter_actor_input"]) for row in audit_rows),
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


def run_rollout_candidate_scaffold_smoke(run_dir: Path | str) -> dict[str, object]:
    """Write synthetic no-training scaffolding artifacts."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    measurements = synthetic_rollout_measurements()
    candidates, audit_rows = materialize_measurements(measurements)
    classifications = [classify_candidate(candidate) for candidate in candidates]
    candidate_rows = [
        candidate_to_row(candidate, classification)
        for candidate, classification in zip(candidates, classifications)
    ]
    summary = build_rollout_candidate_summary(measurements, candidates, audit_rows)
    summary["harness"] = build_harness_summary(candidates)
    write_csv_rows(output / "measurement_rows.csv", audit_rows)
    write_csv_rows(output / "materialized_candidate_rows.csv", candidate_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic decisive-history rollout candidate scaffold smoke.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/m1508_decisive_history_rollout_candidate_scaffold_smoke"))
    args = parser.parse_args()
    summary = run_rollout_candidate_scaffold_smoke(args.run_dir)
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"materialized_candidate_count={summary['materialized_candidate_count']}")
    print(f"rejected_count={summary['rejected_count']}")


if __name__ == "__main__":
    main()
