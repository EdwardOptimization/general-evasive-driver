"""No-rerun mining for source-diverse diagnostic expansion candidates."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.bounded_comparison_candidate_qualification import profile_group, read_csv_rows
from autodrift.bounded_diagnostic_comparison import MATCH_FIELDS, candidate_key
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_L2_DIAGNOSTIC = Path(
    "runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/"
    "l2_zero_success_diagnostic.csv"
)
DEFAULT_EPISODE_ROWS = Path(
    "runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/"
    "episode_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2018_source_diverse_diagnostic_expansion_mining")
DEFAULT_NEXT_BLOCKER = "m2019-source-diverse-diagnostic-expansion-mining-result-audit"
M2016_SINGLETON_KEY = (
    "success_stabilizer|stable_aes_only|tier_b_feasible_emergency|post_friction_step|aes_feasible"
)

CANDIDATE_FIELDNAMES = [
    "candidate_key",
    "repair_source_kind",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "episode_count",
    "l2_episode_count",
    "l2_success_count",
    "l2_collision_count",
    "l2_offtrack_outcome_count",
    "non_l2_episode_count",
    "non_l2_success_count",
    "non_l2_collision_count",
    "non_l2_offtrack_outcome_count",
    "non_l2_success_rate",
    "l2_zero_success",
    "non_l2_success_profile_count",
    "non_l2_success_profiles",
    "non_l2_success_profile_groups",
    "non_l2_success_profile_group_count",
    "candidate_source_count",
    "task_source_count",
    "base_geometry_source_count",
    "repair_candidate_count",
    "base_geometry_sources",
    "diagnostic_l2_row_count",
    "diagnostic_pattern_row_count",
    "beyond_m2016_singleton",
    "source_diverse_candidate",
    "admitted_for_expansion",
    "rejection_reasons",
]
SUMMARY_FIELDNAMES = [
    "metric",
    "value",
]


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(str(value)))


def _outcome_count(rows: list[Mapping[str, Any]], bucket: str) -> int:
    return sum(1 for row in rows if row.get("outcome_bucket") == bucket)


def _sorted_join(values: Iterable[Any]) -> str:
    return ";".join(sorted({str(value) for value in values if str(value)}))


def _group_episode_rows(episode_rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        grouped[candidate_key(row)].append(row)
    return grouped


def _group_diagnostic_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[candidate_key(row)].append(row)
    return grouped


def _candidate_from_rows(
    *,
    key: str,
    episode_rows: list[Mapping[str, Any]],
    diagnostic_rows: list[Mapping[str, Any]],
    min_non_l2_success_count: int,
    min_non_l2_success_profile_group_count: int,
    min_candidate_source_count: int,
) -> dict[str, Any] | None:
    if not episode_rows:
        return None
    representative = episode_rows[0]
    l2_rows = [row for row in episode_rows if profile_group(str(row.get("profile_name", ""))) == "L2"]
    non_l2_rows = [row for row in episode_rows if profile_group(str(row.get("profile_name", ""))) != "L2"]
    l2_success_count = _outcome_count(l2_rows, "success_obstacle_pass")
    non_l2_success_rows = [row for row in non_l2_rows if row.get("outcome_bucket") == "success_obstacle_pass"]
    non_l2_success_count = len(non_l2_success_rows)
    if not l2_rows or l2_success_count != 0 or non_l2_success_count <= 0:
        return None

    non_l2_success_profiles = sorted({str(row.get("profile_name", "")) for row in non_l2_success_rows})
    non_l2_success_groups = sorted({profile_group(profile) for profile in non_l2_success_profiles})
    candidate_source_count = len({str(row.get("candidate_source_id", "")) for row in episode_rows})
    task_source_count = len({str(row.get("task_source_id", "")) for row in episode_rows})
    base_geometry_sources = sorted({str(row.get("base_geometry_source", "")) for row in episode_rows})
    repair_candidate_count = len({str(row.get("repair_candidate_id", "")) for row in episode_rows})
    diagnostic_pattern_count = sum(
        1 for row in diagnostic_rows if _as_bool(row.get("same_slice_non_l2_success_l2_zero_pattern"))
    )

    reasons: list[str] = []
    if non_l2_success_count < min_non_l2_success_count:
        reasons.append("non_l2_success_count_below_threshold")
    if len(non_l2_success_groups) < min_non_l2_success_profile_group_count:
        reasons.append("non_l2_success_profile_group_count_below_threshold")
    if candidate_source_count < min_candidate_source_count:
        reasons.append("candidate_source_count_below_threshold")

    source_diverse_candidate = candidate_source_count >= min_candidate_source_count and task_source_count >= 1
    beyond_m2016_singleton = key != M2016_SINGLETON_KEY
    return {
        "candidate_key": key,
        "repair_source_kind": representative.get("repair_source_kind", ""),
        "source_role_semantics": representative.get("source_role_semantics", ""),
        "parent_feasibility_tier_id": representative.get("parent_feasibility_tier_id", ""),
        "normalized_surface_variant": representative.get("normalized_surface_variant", ""),
        "sampled_obstacle_label": representative.get("sampled_obstacle_label", ""),
        "episode_count": len(episode_rows),
        "l2_episode_count": len(l2_rows),
        "l2_success_count": l2_success_count,
        "l2_collision_count": _outcome_count(l2_rows, "collision_failure"),
        "l2_offtrack_outcome_count": _outcome_count(l2_rows, "off_track_noncollision_noncompletion"),
        "non_l2_episode_count": len(non_l2_rows),
        "non_l2_success_count": non_l2_success_count,
        "non_l2_collision_count": _outcome_count(non_l2_rows, "collision_failure"),
        "non_l2_offtrack_outcome_count": _outcome_count(non_l2_rows, "off_track_noncollision_noncompletion"),
        "non_l2_success_rate": non_l2_success_count / len(non_l2_rows) if non_l2_rows else 0.0,
        "l2_zero_success": True,
        "non_l2_success_profile_count": len(non_l2_success_profiles),
        "non_l2_success_profiles": ";".join(non_l2_success_profiles),
        "non_l2_success_profile_groups": ";".join(non_l2_success_groups),
        "non_l2_success_profile_group_count": len(non_l2_success_groups),
        "candidate_source_count": candidate_source_count,
        "task_source_count": task_source_count,
        "base_geometry_source_count": len(base_geometry_sources),
        "repair_candidate_count": repair_candidate_count,
        "base_geometry_sources": ";".join(base_geometry_sources),
        "diagnostic_l2_row_count": len(diagnostic_rows),
        "diagnostic_pattern_row_count": diagnostic_pattern_count,
        "beyond_m2016_singleton": beyond_m2016_singleton,
        "source_diverse_candidate": source_diverse_candidate,
        "admitted_for_expansion": not reasons,
        "rejection_reasons": ";".join(reasons),
    }


def mine_expansion_candidates(
    *,
    diagnostic_rows: list[Mapping[str, Any]],
    episode_rows: list[Mapping[str, Any]],
    min_non_l2_success_count: int = 2,
    min_non_l2_success_profile_group_count: int = 2,
    min_candidate_source_count: int = 2,
) -> list[dict[str, Any]]:
    episode_by_key = _group_episode_rows(episode_rows)
    diagnostic_by_key = _group_diagnostic_rows(diagnostic_rows)
    candidates: list[dict[str, Any]] = []
    for key in sorted(episode_by_key):
        candidate = _candidate_from_rows(
            key=key,
            episode_rows=episode_by_key[key],
            diagnostic_rows=diagnostic_by_key.get(key, []),
            min_non_l2_success_count=min_non_l2_success_count,
            min_non_l2_success_profile_group_count=min_non_l2_success_profile_group_count,
            min_candidate_source_count=min_candidate_source_count,
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def source_diversity_summary_rows(candidates: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    admitted = [row for row in candidates if _as_bool(row.get("admitted_for_expansion"))]
    beyond = [row for row in admitted if _as_bool(row.get("beyond_m2016_singleton"))]
    rows = {
        "candidate_count": len(candidates),
        "admitted_candidate_count": len(admitted),
        "beyond_m2016_admitted_candidate_count": len(beyond),
        "repair_source_kind_count": len({row.get("repair_source_kind", "") for row in admitted}),
        "role_count": len({row.get("source_role_semantics", "") for row in admitted}),
        "tier_count": len({row.get("parent_feasibility_tier_id", "") for row in admitted}),
        "surface_count": len({row.get("normalized_surface_variant", "") for row in admitted}),
        "label_count": len({row.get("sampled_obstacle_label", "") for row in admitted}),
        "max_candidate_source_count": max((_as_int(row.get("candidate_source_count")) for row in admitted), default=0),
        "m2016_singleton_included": any(row.get("candidate_key") == M2016_SINGLETON_KEY for row in admitted),
    }
    return [{"metric": key, "value": value} for key, value in rows.items()]


def run_mining(
    *,
    l2_diagnostic_path: Path,
    episode_rows_path: Path,
    output_dir: Path,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_rows = read_csv_rows(l2_diagnostic_path)
    episode_rows = read_csv_rows(episode_rows_path)
    candidates = mine_expansion_candidates(diagnostic_rows=diagnostic_rows, episode_rows=episode_rows)
    admitted = [row for row in candidates if _as_bool(row.get("admitted_for_expansion"))]
    beyond = [row for row in admitted if _as_bool(row.get("beyond_m2016_singleton"))]
    diversity_rows = source_diversity_summary_rows(candidates)
    claim_boundary_rows = [
        {
            "claim": "source_diverse_diagnostic_expansion_mining_completed",
            "admissible": True,
            "reason": "M2018 reads existing M2012/M2009 artifacts and writes mining tables only",
        },
        {
            "claim": "source_diverse_expansion_exists",
            "admissible": bool(beyond),
            "reason": "requires at least one admitted L2-zero/non-L2-success candidate beyond the M2016 singleton",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "mining candidates are diagnostics, not a ranking experiment",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "mining does not provide fair source-diverse controlled comparison or holdout",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "mining does not test wrong-history or history necessity",
        },
    ]

    artifacts = {
        "summary": output_dir / "summary.json",
        "diagnostic_expansion_candidates": output_dir / "diagnostic_expansion_candidates.csv",
        "admitted_expansion_candidates": output_dir / "admitted_expansion_candidates.csv",
        "source_diversity_summary": output_dir / "source_diversity_summary.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
        "run_state": output_dir / "run_state.json",
    }
    write_csv_rows(artifacts["diagnostic_expansion_candidates"], candidates, CANDIDATE_FIELDNAMES)
    write_csv_rows(artifacts["admitted_expansion_candidates"], admitted, CANDIDATE_FIELDNAMES)
    write_csv_rows(artifacts["source_diversity_summary"], diversity_rows, SUMMARY_FIELDNAMES)
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
    result_passes = bool(candidates) and not any(guardrail_flags.values())
    summary = {
        "result_class": (
            "source_diverse_diagnostic_expansion_mining_pass"
            if result_passes
            else "source_diverse_diagnostic_expansion_mining_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "l2_diagnostic_path": str(l2_diagnostic_path),
        "episode_rows_path": str(episode_rows_path),
        "output_dir": str(output_dir),
        "diagnostic_row_count": len(diagnostic_rows),
        "episode_row_count": len(episode_rows),
        "candidate_count": len(candidates),
        "admitted_candidate_count": len(admitted),
        "beyond_m2016_admitted_candidate_count": len(beyond),
        "admitted_candidate_keys": [str(row["candidate_key"]) for row in admitted],
        "beyond_m2016_admitted_candidate_keys": [str(row["candidate_key"]) for row in beyond],
        "repair_source_kind_count": len({row.get("repair_source_kind", "") for row in admitted}),
        "role_count": len({row.get("source_role_semantics", "") for row in admitted}),
        "tier_count": len({row.get("parent_feasibility_tier_id", "") for row in admitted}),
        "surface_count": len({row.get("normalized_surface_variant", "") for row in admitted}),
        "label_count": len({row.get("sampled_obstacle_label", "") for row in admitted}),
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
            "target_episode_count": len(episode_rows),
            "completed_count": len(episode_rows),
            "failure_count": 0 if result_passes else 1,
            "complete": bool(result_passes),
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--l2-diagnostic", type=Path, default=DEFAULT_L2_DIAGNOSTIC)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_mining(
        l2_diagnostic_path=args.l2_diagnostic,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"admitted_candidate_count={summary['admitted_candidate_count']}")
    print(f"beyond_m2016_admitted_candidate_count={summary['beyond_m2016_admitted_candidate_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
