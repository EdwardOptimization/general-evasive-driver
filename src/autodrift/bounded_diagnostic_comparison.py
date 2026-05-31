"""No-rerun bounded diagnostic comparison for one admitted candidate slice."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.bounded_comparison_candidate_qualification import profile_group, read_csv_rows
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_ADMITTED_CANDIDATES = Path("runs/m2014_bounded_comparison_candidate_qualification/admitted_candidates.csv")
DEFAULT_EPISODE_ROWS = Path(
    "runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/"
    "episode_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2016_bounded_diagnostic_comparison")
DEFAULT_NEXT_BLOCKER = "m2017-bounded-diagnostic-comparison-result-audit"

MATCH_FIELDS = (
    "repair_source_kind",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
)
PROFILE_FIELDNAMES = [
    "candidate_key",
    "profile_name",
    "profile_group",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "offtrack_termination_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "offtrack_termination_rate",
    "clearance_margin_mean",
    "return_mean",
    "steps_mean",
    "action_rate_mean",
    "high_sideslip_fraction_mean",
]
GROUP_FIELDNAMES = [
    "candidate_key",
    "profile_group",
    "profile_count",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "offtrack_termination_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "offtrack_termination_rate",
    "clearance_margin_mean",
    "return_mean",
    "steps_mean",
    "action_rate_mean",
    "high_sideslip_fraction_mean",
]


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(str(value))
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float | None:
    values = [_as_float(row.get(key)) for row in rows]
    finite = [value for value in values if value is not None]
    if not finite:
        return None
    return sum(finite) / len(finite)


def _outcome_count(rows: list[Mapping[str, Any]], bucket: str) -> int:
    return sum(1 for row in rows if row.get("outcome_bucket") == bucket)


def candidate_key(row: Mapping[str, Any]) -> str:
    return "|".join(str(row.get(field, "")) for field in MATCH_FIELDS)


def filter_candidate_rows(
    episode_rows: Iterable[Mapping[str, Any]],
    admitted_candidate: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    return [
        row
        for row in episode_rows
        if all(str(row.get(field, "")) == str(admitted_candidate.get(field, "")) for field in MATCH_FIELDS)
    ]


def aggregate_rows(
    *,
    rows: list[Mapping[str, Any]],
    candidate: Mapping[str, Any],
    group_key: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if group_key == "profile_group":
            key = profile_group(str(row.get("profile_name", "")))
        else:
            key = str(row.get(group_key, ""))
        grouped[key].append(row)

    output_rows: list[dict[str, Any]] = []
    for key in sorted(grouped):
        slice_rows = grouped[key]
        episode_count = len(slice_rows)
        success_count = _outcome_count(slice_rows, "success_obstacle_pass")
        collision_count = _outcome_count(slice_rows, "collision_failure")
        offtrack_outcome_count = _outcome_count(slice_rows, "off_track_noncollision_noncompletion")
        offtrack_termination_count = sum(1 for row in slice_rows if row.get("termination_reason") == "off_track")
        base = {
            "candidate_key": candidate_key(candidate),
            "episode_count": episode_count,
            "success_count": success_count,
            "collision_count": collision_count,
            "offtrack_outcome_count": offtrack_outcome_count,
            "offtrack_termination_count": offtrack_termination_count,
            "success_rate": success_count / episode_count if episode_count else 0.0,
            "collision_rate": collision_count / episode_count if episode_count else 0.0,
            "offtrack_outcome_rate": offtrack_outcome_count / episode_count if episode_count else 0.0,
            "offtrack_termination_rate": offtrack_termination_count / episode_count if episode_count else 0.0,
            "clearance_margin_mean": _mean(slice_rows, "min_clearance_margin"),
            "return_mean": _mean(slice_rows, "return"),
            "steps_mean": _mean(slice_rows, "steps"),
            "action_rate_mean": _mean(slice_rows, "action_rate_mean"),
            "high_sideslip_fraction_mean": _mean(slice_rows, "high_sideslip_fraction"),
        }
        if group_key == "profile_group":
            base["profile_group"] = key
            base["profile_count"] = len({str(row.get("profile_name", "")) for row in slice_rows})
        else:
            base["profile_name"] = key
            base["profile_group"] = profile_group(key)
        output_rows.append(base)
    return output_rows


def run_bounded_diagnostic_comparison(
    *,
    admitted_candidates_path: Path,
    episode_rows_path: Path,
    output_dir: Path,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    admitted_candidates = read_csv_rows(admitted_candidates_path)
    episode_rows = read_csv_rows(episode_rows_path)
    if not admitted_candidates:
        matched_rows: list[Mapping[str, Any]] = []
        admitted_candidate: Mapping[str, Any] = {}
    else:
        admitted_candidate = admitted_candidates[0]
        matched_rows = filter_candidate_rows(episode_rows, admitted_candidate)

    profile_rows = aggregate_rows(rows=matched_rows, candidate=admitted_candidate, group_key="profile_name")
    group_rows = aggregate_rows(rows=matched_rows, candidate=admitted_candidate, group_key="profile_group")
    claim_boundary_rows = [
        {
            "claim": "bounded_diagnostic_comparison_completed",
            "admissible": bool(matched_rows and profile_rows and group_rows),
            "reason": "M2016 reads existing M2009/M2014 artifacts and writes diagnostic tables only",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "single admitted public slice is diagnostic, not a ranking experiment",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2014 admitted scope has l2_success_present=false and l2_total_success_count=0",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "single-slice diagnostic table is not paper-level evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "bounded diagnostic comparison does not test wrong-history or history necessity",
        },
    ]

    artifacts = {
        "summary": output_dir / "summary.json",
        "profile_comparison": output_dir / "profile_comparison.csv",
        "profile_group_comparison": output_dir / "profile_group_comparison.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
        "run_state": output_dir / "run_state.json",
    }
    write_csv_rows(artifacts["profile_comparison"], profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(artifacts["profile_group_comparison"], group_rows, GROUP_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_boundary_rows)

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
    result_passes = bool(matched_rows and profile_rows and group_rows) and not any(guardrail_flags.values())
    summary = {
        "result_class": "bounded_diagnostic_comparison_pass" if result_passes else "bounded_diagnostic_comparison_fail",
        "generated_at_utc": utc_timestamp(),
        "admitted_candidates_path": str(admitted_candidates_path),
        "episode_rows_path": str(episode_rows_path),
        "output_dir": str(output_dir),
        "admitted_candidate_count": len(admitted_candidates),
        "selected_candidate_key": candidate_key(admitted_candidate) if admitted_candidate else "",
        "matched_episode_count": len(matched_rows),
        "profile_row_count": len(profile_rows),
        "profile_group_row_count": len(group_rows),
        "profile_names": [row["profile_name"] for row in profile_rows],
        "profile_groups": [row["profile_group"] for row in group_rows],
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
            "target_episode_count": len(matched_rows),
            "completed_count": len(matched_rows),
            "failure_count": 0 if result_passes else 1,
            "complete": bool(result_passes),
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admitted-candidates", type=Path, default=DEFAULT_ADMITTED_CANDIDATES)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_bounded_diagnostic_comparison(
        admitted_candidates_path=args.admitted_candidates,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"matched_episode_count={summary['matched_episode_count']}")
    print(f"profile_row_count={summary['profile_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
