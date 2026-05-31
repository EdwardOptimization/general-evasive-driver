"""No-rerun multi-slice bounded diagnostic comparison."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.bounded_comparison_candidate_qualification import profile_group, read_csv_rows
from autodrift.bounded_diagnostic_comparison import (
    GROUP_FIELDNAMES,
    MATCH_FIELDS,
    aggregate_rows,
    candidate_key,
    filter_candidate_rows,
)
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_ADMITTED_CANDIDATES = Path(
    "runs/m2018_source_diverse_diagnostic_expansion_mining/admitted_expansion_candidates.csv"
)
DEFAULT_EPISODE_ROWS = Path(
    "runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/"
    "episode_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2020_multi_slice_bounded_diagnostic_comparison")
DEFAULT_NEXT_BLOCKER = "m2021-multi-slice-bounded-diagnostic-comparison-result-audit"

CANDIDATE_SUPPORT_FIELDNAMES = [
    "candidate_key",
    "repair_source_kind",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "matched_episode_count",
    "profile_group_count",
    "l2_episode_count",
    "l2_success_count",
    "non_l2_episode_count",
    "non_l2_success_count",
    "non_l2_success_rate",
]
AGGREGATE_GROUP_FIELDNAMES = [
    "profile_group",
    "candidate_count",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
]


def _outcome_count(rows: list[Mapping[str, Any]], bucket: str) -> int:
    return sum(1 for row in rows if row.get("outcome_bucket") == bucket)


def _candidate_support_row(candidate: Mapping[str, Any], rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    l2_rows = [row for row in rows if profile_group(str(row.get("profile_name", ""))) == "L2"]
    non_l2_rows = [row for row in rows if profile_group(str(row.get("profile_name", ""))) != "L2"]
    non_l2_success = _outcome_count(non_l2_rows, "success_obstacle_pass")
    support = {field: candidate.get(field, "") for field in MATCH_FIELDS}
    support.update(
        {
            "candidate_key": candidate_key(candidate),
            "matched_episode_count": len(rows),
            "profile_group_count": len({profile_group(str(row.get("profile_name", ""))) for row in rows}),
            "l2_episode_count": len(l2_rows),
            "l2_success_count": _outcome_count(l2_rows, "success_obstacle_pass"),
            "non_l2_episode_count": len(non_l2_rows),
            "non_l2_success_count": non_l2_success,
            "non_l2_success_rate": non_l2_success / len(non_l2_rows) if non_l2_rows else 0.0,
        }
    )
    return support


def aggregate_profile_groups_across_candidates(
    candidate_rows: list[dict[str, Any]],
    rows_by_candidate: dict[str, list[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for candidate in candidate_rows:
        key = candidate_key(candidate)
        for row in rows_by_candidate.get(key, []):
            grouped[profile_group(str(row.get("profile_name", "")))].append((key, row))

    output_rows: list[dict[str, Any]] = []
    for group in sorted(grouped):
        entries = grouped[group]
        rows = [row for _, row in entries]
        episode_count = len(rows)
        success_count = _outcome_count(rows, "success_obstacle_pass")
        collision_count = _outcome_count(rows, "collision_failure")
        offtrack_count = _outcome_count(rows, "off_track_noncollision_noncompletion")
        output_rows.append(
            {
                "profile_group": group,
                "candidate_count": len({key for key, _ in entries}),
                "episode_count": episode_count,
                "success_count": success_count,
                "collision_count": collision_count,
                "offtrack_outcome_count": offtrack_count,
                "success_rate": success_count / episode_count if episode_count else 0.0,
                "collision_rate": collision_count / episode_count if episode_count else 0.0,
                "offtrack_outcome_rate": offtrack_count / episode_count if episode_count else 0.0,
            }
        )
    return output_rows


def run_multi_slice_comparison(
    *,
    admitted_candidates_path: Path,
    episode_rows_path: Path,
    output_dir: Path,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_rows = read_csv_rows(admitted_candidates_path)
    episode_rows = read_csv_rows(episode_rows_path)

    rows_by_candidate: dict[str, list[Mapping[str, Any]]] = {}
    candidate_group_rows: list[dict[str, Any]] = []
    candidate_support_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        key = candidate_key(candidate)
        matched = filter_candidate_rows(episode_rows, candidate)
        rows_by_candidate[key] = matched
        candidate_group_rows.extend(aggregate_rows(rows=matched, candidate=candidate, group_key="profile_group"))
        candidate_support_rows.append(_candidate_support_row(candidate, matched))

    aggregate_group_rows = aggregate_profile_groups_across_candidates(candidate_rows, rows_by_candidate)
    claim_boundary_rows = [
        {
            "claim": "multi_slice_bounded_diagnostic_comparison_completed",
            "admissible": bool(candidate_rows and candidate_group_rows and aggregate_group_rows),
            "reason": "M2020 reads existing M2018/M2009 artifacts and writes diagnostic tables only",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "multi-slice public diagnostic table is not a ranking experiment",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2020 remains source-kind singleton and lacks controlled holdout comparison",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "public diagnostic table is not paper-level benchmark evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2020 does not test wrong-history or history necessity",
        },
    ]

    artifacts = {
        "summary": output_dir / "summary.json",
        "candidate_profile_group_comparison": output_dir / "candidate_profile_group_comparison.csv",
        "aggregate_profile_group_comparison": output_dir / "aggregate_profile_group_comparison.csv",
        "candidate_support": output_dir / "candidate_support.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
        "run_state": output_dir / "run_state.json",
    }
    write_csv_rows(artifacts["candidate_profile_group_comparison"], candidate_group_rows, GROUP_FIELDNAMES)
    write_csv_rows(artifacts["aggregate_profile_group_comparison"], aggregate_group_rows, AGGREGATE_GROUP_FIELDNAMES)
    write_csv_rows(artifacts["candidate_support"], candidate_support_rows, CANDIDATE_SUPPORT_FIELDNAMES)
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
    matched_episode_count = sum(len(rows) for rows in rows_by_candidate.values())
    result_passes = bool(candidate_rows and matched_episode_count and candidate_group_rows) and not any(
        guardrail_flags.values()
    )
    summary = {
        "result_class": (
            "multi_slice_bounded_diagnostic_comparison_pass"
            if result_passes
            else "multi_slice_bounded_diagnostic_comparison_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "admitted_candidates_path": str(admitted_candidates_path),
        "episode_rows_path": str(episode_rows_path),
        "output_dir": str(output_dir),
        "candidate_count": len(candidate_rows),
        "matched_episode_count": matched_episode_count,
        "candidate_profile_group_row_count": len(candidate_group_rows),
        "aggregate_profile_group_row_count": len(aggregate_group_rows),
        "candidate_keys": [candidate_key(row) for row in candidate_rows],
        "profile_groups": [row["profile_group"] for row in aggregate_group_rows],
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
            "target_episode_count": matched_episode_count,
            "completed_count": matched_episode_count,
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
    summary = run_multi_slice_comparison(
        admitted_candidates_path=args.admitted_candidates,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"matched_episode_count={summary['matched_episode_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
