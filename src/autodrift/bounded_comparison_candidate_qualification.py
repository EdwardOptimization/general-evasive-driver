"""No-rerun qualification for bounded comparison candidate slices."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SUMMARY = Path(
    "runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/summary.json"
)
DEFAULT_CANDIDATES = Path(
    "runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/"
    "comparison_support_candidates.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2014_bounded_comparison_candidate_qualification")
DEFAULT_NEXT_BLOCKER = "m2015-bounded-comparison-candidate-qualification-result-audit"

PROFILE_GROUPS = ("L0", "L1", "L2", "L3")
QUALIFICATION_FIELDNAMES = [
    "candidate_key",
    "repair_source_kind",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "source_support_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "nonzero_success_profile_count",
    "profiles_with_success",
    "success_profile_groups",
    "success_profile_group_count",
    "l2_success_present",
    "l2_total_success_count",
    "admitted_for_bounded_comparison",
    "admitted_scope",
    "rejection_reasons",
]


@dataclass(frozen=True)
class QualificationThresholds:
    min_episode_count: int = 48
    min_success_count: int = 10
    min_success_rate: float = 0.15
    max_collision_rate: float = 0.10
    max_offtrack_outcome_rate: float = 0.75
    min_nonzero_success_profile_count: int = 3
    min_success_profile_group_count: int = 2


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(str(value)))


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(str(value))


def profile_group(profile_name: str) -> str:
    for group in PROFILE_GROUPS:
        if profile_name.startswith(f"{group}_"):
            return group
    return "unknown"


def split_profiles(value: Any) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def candidate_key(row: Mapping[str, Any]) -> str:
    fields = [
        "repair_source_kind",
        "source_role_semantics",
        "parent_feasibility_tier_id",
        "normalized_surface_variant",
        "sampled_obstacle_label",
    ]
    return "|".join(str(row.get(field, "")) for field in fields)


def qualify_candidate(
    row: Mapping[str, Any],
    *,
    thresholds: QualificationThresholds,
    l2_total_success_count: int,
) -> dict[str, Any]:
    episode_count = _as_int(row.get("episode_count"))
    success_count = _as_int(row.get("success_count"))
    collision_count = _as_int(row.get("collision_count"))
    offtrack_outcome_count = _as_int(row.get("offtrack_outcome_count"))
    success_rate = _as_float(row.get("success_rate"))
    collision_rate = _as_float(row.get("collision_rate"))
    offtrack_outcome_rate = _as_float(row.get("offtrack_outcome_rate"))
    nonzero_success_profile_count = _as_int(row.get("nonzero_success_profile_count"))
    profiles = split_profiles(row.get("profiles_with_success"))
    groups = sorted({profile_group(profile) for profile in profiles if profile_group(profile) != "unknown"})
    l2_success_present = "L2" in groups

    reasons: list[str] = []
    if str(row.get("support_label", "")) != "comparison_ready_candidate":
        reasons.append("source_label_not_comparison_ready_candidate")
    if episode_count < thresholds.min_episode_count:
        reasons.append("episode_count_below_threshold")
    if success_count < thresholds.min_success_count:
        reasons.append("success_count_below_threshold")
    if success_rate < thresholds.min_success_rate:
        reasons.append("success_rate_below_threshold")
    if collision_rate > thresholds.max_collision_rate:
        reasons.append("collision_rate_above_threshold")
    if offtrack_outcome_rate > thresholds.max_offtrack_outcome_rate:
        reasons.append("offtrack_outcome_rate_above_threshold")
    if nonzero_success_profile_count < thresholds.min_nonzero_success_profile_count:
        reasons.append("nonzero_success_profile_count_below_threshold")
    if len(groups) < thresholds.min_success_profile_group_count:
        reasons.append("success_profile_group_count_below_threshold")

    admitted = not reasons
    if admitted and not l2_success_present:
        scope = "bounded_diagnostic_comparison_not_finite_window_vs_gru"
    elif admitted:
        scope = "bounded_diagnostic_comparison"
    else:
        scope = "not_admitted"

    return {
        "candidate_key": candidate_key(row),
        "repair_source_kind": row.get("repair_source_kind", ""),
        "source_role_semantics": row.get("source_role_semantics", ""),
        "parent_feasibility_tier_id": row.get("parent_feasibility_tier_id", ""),
        "normalized_surface_variant": row.get("normalized_surface_variant", ""),
        "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
        "source_support_label": row.get("support_label", ""),
        "episode_count": episode_count,
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_outcome_count": offtrack_outcome_count,
        "success_rate": success_rate,
        "collision_rate": collision_rate,
        "offtrack_outcome_rate": offtrack_outcome_rate,
        "nonzero_success_profile_count": nonzero_success_profile_count,
        "profiles_with_success": ";".join(profiles),
        "success_profile_groups": ";".join(groups),
        "success_profile_group_count": len(groups),
        "l2_success_present": bool(l2_success_present),
        "l2_total_success_count": int(l2_total_success_count),
        "admitted_for_bounded_comparison": bool(admitted),
        "admitted_scope": scope,
        "rejection_reasons": ";".join(reasons),
    }


def qualify_candidates(
    rows: Iterable[Mapping[str, Any]],
    *,
    thresholds: QualificationThresholds,
    l2_total_success_count: int,
) -> list[dict[str, Any]]:
    return [
        qualify_candidate(row, thresholds=thresholds, l2_total_success_count=l2_total_success_count)
        for row in rows
    ]


def run_qualification(
    *,
    summary_path: Path,
    candidates_path: Path,
    output_dir: Path,
    thresholds: QualificationThresholds = QualificationThresholds(),
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    source_rows = read_csv_rows(candidates_path)
    qualification_rows = qualify_candidates(
        source_rows,
        thresholds=thresholds,
        l2_total_success_count=_as_int(source_summary.get("l2_total_success_count")),
    )
    admitted_rows = [row for row in qualification_rows if row["admitted_for_bounded_comparison"]]
    rejected_rows = [row for row in qualification_rows if not row["admitted_for_bounded_comparison"]]

    artifacts = {
        "summary": output_dir / "summary.json",
        "candidate_qualification_rows": output_dir / "candidate_qualification_rows.csv",
        "admitted_candidates": output_dir / "admitted_candidates.csv",
        "rejected_candidates": output_dir / "rejected_candidates.csv",
        "run_state": output_dir / "run_state.json",
    }
    write_csv_rows(artifacts["candidate_qualification_rows"], qualification_rows, QUALIFICATION_FIELDNAMES)
    write_csv_rows(artifacts["admitted_candidates"], admitted_rows, QUALIFICATION_FIELDNAMES)
    write_csv_rows(artifacts["rejected_candidates"], rejected_rows, QUALIFICATION_FIELDNAMES)

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }
    result_passes = len(qualification_rows) == len(source_rows) and not any(guardrail_flags.values())
    summary = {
        "result_class": (
            "bounded_comparison_candidate_qualification_pass"
            if result_passes
            else "bounded_comparison_candidate_qualification_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "source_summary_path": str(summary_path),
        "source_candidates_path": str(candidates_path),
        "output_dir": str(output_dir),
        "source_candidate_count": len(source_rows),
        "qualification_row_count": len(qualification_rows),
        "admitted_candidate_count": len(admitted_rows),
        "rejected_candidate_count": len(rejected_rows),
        "admitted_candidate_keys": [row["candidate_key"] for row in admitted_rows],
        "rejected_candidate_keys": [row["candidate_key"] for row in rejected_rows],
        "thresholds": {
            "min_episode_count": thresholds.min_episode_count,
            "min_success_count": thresholds.min_success_count,
            "min_success_rate": thresholds.min_success_rate,
            "max_collision_rate": thresholds.max_collision_rate,
            "max_offtrack_outcome_rate": thresholds.max_offtrack_outcome_rate,
            "min_nonzero_success_profile_count": thresholds.min_nonzero_success_profile_count,
            "min_success_profile_group_count": thresholds.min_success_profile_group_count,
        },
        "source_l2_total_success_count": _as_int(source_summary.get("l2_total_success_count")),
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": sum(1 for value in guardrail_flags.values() if value),
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(artifacts["summary"], summary)
    write_run_state(
        artifacts["run_state"],
        {
            "target_episode_count": len(source_rows),
            "completed_count": len(qualification_rows),
            "failure_count": 0 if result_passes else 1,
            "complete": bool(result_passes),
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-episode-count", type=int, default=QualificationThresholds.min_episode_count)
    parser.add_argument("--min-success-count", type=int, default=QualificationThresholds.min_success_count)
    parser.add_argument("--min-success-rate", type=float, default=QualificationThresholds.min_success_rate)
    parser.add_argument("--max-collision-rate", type=float, default=QualificationThresholds.max_collision_rate)
    parser.add_argument("--max-offtrack-outcome-rate", type=float, default=QualificationThresholds.max_offtrack_outcome_rate)
    parser.add_argument(
        "--min-nonzero-success-profile-count",
        type=int,
        default=QualificationThresholds.min_nonzero_success_profile_count,
    )
    parser.add_argument(
        "--min-success-profile-group-count",
        type=int,
        default=QualificationThresholds.min_success_profile_group_count,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    thresholds = QualificationThresholds(
        min_episode_count=int(args.min_episode_count),
        min_success_count=int(args.min_success_count),
        min_success_rate=float(args.min_success_rate),
        max_collision_rate=float(args.max_collision_rate),
        max_offtrack_outcome_rate=float(args.max_offtrack_outcome_rate),
        min_nonzero_success_profile_count=int(args.min_nonzero_success_profile_count),
        min_success_profile_group_count=int(args.min_success_profile_group_count),
    )
    summary = run_qualification(
        summary_path=args.summary,
        candidates_path=args.candidates,
        output_dir=args.output_dir,
        thresholds=thresholds,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_candidate_count={summary['source_candidate_count']}")
    print(f"admitted_candidate_count={summary['admitted_candidate_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
