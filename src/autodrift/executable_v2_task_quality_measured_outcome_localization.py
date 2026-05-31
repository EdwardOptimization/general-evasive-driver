"""No-rerun outcome localization for the executable-v2 task-quality panel."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SUMMARY = Path("runs/m1938_executable_v2_task_quality_measured_execution/summary.json")
DEFAULT_EPISODE_ROWS = Path("runs/m1938_executable_v2_task_quality_measured_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1942_executable_v2_task_quality_measured_outcome_localization")
DEFAULT_NEXT_BLOCKER = "m1943-executable-v2-task-quality-measured-outcome-localization-result-audit"
TARGET_EPISODE_COUNT = 960
TARGET_PROFILE_COUNT = 12
TARGET_TIER_COUNT = 5
TARGET_ROLE_COUNT = 4
TARGET_SURFACE_COUNT = 2
SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
FORBIDDEN_LOCAL_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
OUTCOME_VALUES = (
    "success_obstacle_pass",
    "collision_failure",
    "off_track_noncollision_noncompletion",
)
AGGREGATE_SPECS: dict[str, tuple[str, ...]] = {
    "outcome_by_profile": ("profile_name",),
    "outcome_by_tier": ("feasibility_tier_id",),
    "outcome_by_role": ("source_role_semantics",),
    "outcome_by_surface": ("surface_variant",),
    "outcome_by_sampled_label": ("sampled_obstacle_label",),
    "outcome_by_profile_tier": ("profile_name", "feasibility_tier_id"),
    "outcome_by_profile_role": ("profile_name", "source_role_semantics"),
    "outcome_by_profile_surface": ("profile_name", "surface_variant"),
    "outcome_by_profile_sampled_label": ("profile_name", "sampled_obstacle_label"),
    "outcome_by_tier_role_surface": ("feasibility_tier_id", "source_role_semantics", "surface_variant"),
    "outcome_by_candidate_source_profile": ("candidate_source_id", "profile_name"),
}
AGGREGATE_FIELDNAMES = [
    "slice_kind",
    "support_label",
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
    "all_selected_metrics_finite",
    "success_obstacle_pass",
    "collision_failure",
    "off_track_noncollision_noncompletion",
    "termination_off_track",
    "termination_obstacle_collision",
    "termination_empty",
]
SUCCESS_SOURCE_FIELDNAMES = [
    "workload_id",
    "candidate_source_id",
    "task_source_id",
    "profile_name",
    "feasibility_tier_id",
    "source_role_semantics",
    "surface_variant",
    "sampled_obstacle_label",
    "target_boundary_mode",
    "target_support_mode",
    "selected_accepted_cell_rule",
    "outcome_bucket",
    "termination_reason",
    "min_clearance_margin",
    "return",
    "steps",
]
DOMINANCE_FIELDNAMES = [
    "slice_kind",
    "dominance_type",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "collision_rate",
    "offtrack_outcome_rate",
    "support_label",
    "profile_name",
    "feasibility_tier_id",
    "source_role_semantics",
    "surface_variant",
    "sampled_obstacle_label",
]
L2_DIAGNOSTIC_FIELDNAMES = [
    "profile_name",
    "feasibility_tier_id",
    "source_role_semantics",
    "surface_variant",
    "sampled_obstacle_label",
    "l2_episode_count",
    "l2_success_count",
    "l2_collision_count",
    "l2_offtrack_outcome_count",
    "l2_zero_success",
    "non_l2_same_slice_success_count",
    "non_l2_same_slice_success_profile_count",
    "non_l2_same_slice_success_profiles",
    "same_slice_non_l2_success_l2_zero_pattern",
]
COMPARISON_CANDIDATE_FIELDNAMES = [
    "feasibility_tier_id",
    "source_role_semantics",
    "surface_variant",
    "sampled_obstacle_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "nonzero_success_profile_count",
    "profiles_with_success",
    "support_label",
]
CLAIM_BOUNDARY_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def _float_or_nan(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if math.isfinite(result) else float("nan")


def _finite(value: Any) -> bool:
    return math.isfinite(_float_or_nan(value))


def _metric(row: Mapping[str, Any], metric: str) -> float:
    if metric == "success":
        return 1.0 if _bool(row.get("success")) else 0.0
    if metric == "collision":
        return 1.0 if _bool(row.get("collision")) else 0.0
    return _float_or_nan(row.get(metric, "nan"))


def selected_metrics_are_finite(rows: Iterable[Mapping[str, Any]]) -> bool:
    return all(math.isfinite(_metric(row, metric)) for row in rows for metric in SELECTED_METRICS)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_rows(rows: Iterable[Mapping[str, Any]], keys: Sequence[str]) -> dict[tuple[str, ...], list[Mapping[str, Any]]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)
    return dict(sorted(groups.items()))


def support_label(*, episode_count: int, success_count: int, offtrack_rate: float, collision_rate: float) -> str:
    if success_count == 0:
        return "no_support"
    if success_count < 5:
        return "weak_support"
    if episode_count >= 20 and offtrack_rate < 0.70 and collision_rate < 0.30:
        return "comparison_ready_candidate_without_profile_diversity_check"
    if offtrack_rate < 0.80:
        return "candidate_support"
    return "weak_support"


def _mean_metric(rows: list[Mapping[str, Any]], metric: str) -> float | None:
    values = [_metric(row, metric) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return None
    return float(sum(finite) / len(finite))


def aggregate_outcomes(rows: list[Mapping[str, Any]], keys: Sequence[str], *, slice_kind: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for group_values, group_rows in _group_rows(rows, keys).items():
        outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in group_rows)
        termination_counts = Counter(str(row.get("termination_reason", "")) for row in group_rows)
        episode_count = len(group_rows)
        success_count = int(outcome_counts.get("success_obstacle_pass", 0))
        collision_count = int(outcome_counts.get("collision_failure", 0))
        offtrack_outcome_count = int(outcome_counts.get("off_track_noncollision_noncompletion", 0))
        offtrack_termination_count = int(termination_counts.get("off_track", 0))
        collision_rate = collision_count / episode_count if episode_count else 0.0
        offtrack_rate = offtrack_outcome_count / episode_count if episode_count else 0.0
        row = {
            "slice_kind": slice_kind,
            "support_label": support_label(
                episode_count=episode_count,
                success_count=success_count,
                offtrack_rate=offtrack_rate,
                collision_rate=collision_rate,
            ),
            "episode_count": episode_count,
            "success_count": success_count,
            "collision_count": collision_count,
            "offtrack_outcome_count": offtrack_outcome_count,
            "offtrack_termination_count": offtrack_termination_count,
            "success_rate": success_count / episode_count if episode_count else 0.0,
            "collision_rate": collision_rate,
            "offtrack_outcome_rate": offtrack_rate,
            "offtrack_termination_rate": offtrack_termination_count / episode_count if episode_count else 0.0,
            "clearance_margin_mean": _mean_metric(group_rows, "min_clearance_margin"),
            "return_mean": _mean_metric(group_rows, "return"),
            "steps_mean": _mean_metric(group_rows, "steps"),
            "all_selected_metrics_finite": selected_metrics_are_finite(group_rows),
            "success_obstacle_pass": success_count,
            "collision_failure": collision_count,
            "off_track_noncollision_noncompletion": offtrack_outcome_count,
            "termination_off_track": offtrack_termination_count,
            "termination_obstacle_collision": int(termination_counts.get("obstacle_collision", 0)),
            "termination_empty": int(termination_counts.get("", 0)),
        }
        row.update({key: value for key, value in zip(keys, group_values)})
        output.append(row)
    return output


def success_source_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("outcome_bucket", "")) != "success_obstacle_pass":
            continue
        output.append({field: row.get(field, "") for field in SUCCESS_SOURCE_FIELDNAMES})
    return output


def dominance_rows(rows: list[dict[str, Any]], *, dominance_type: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        episode_count = int(row.get("episode_count", 0))
        if episode_count < 5:
            continue
        offtrack_rate = float(row.get("offtrack_outcome_rate", 0.0))
        collision_rate = float(row.get("collision_rate", 0.0))
        if dominance_type == "offtrack" and offtrack_rate < 0.80:
            continue
        if dominance_type == "collision" and collision_rate < 0.30:
            continue
        output.append({field: row.get(field, "") for field in DOMINANCE_FIELDNAMES} | {"dominance_type": dominance_type})
    return output


def l2_zero_success_diagnostic(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scenario_keys = ("feasibility_tier_id", "source_role_semantics", "surface_variant", "sampled_obstacle_label")
    by_l2_profile_slice = _group_rows(
        [row for row in rows if str(row.get("profile_name", "")).startswith("L2_")],
        ("profile_name", *scenario_keys),
    )
    by_scenario = _group_rows(rows, scenario_keys)
    output: list[dict[str, Any]] = []
    for group_values, group_rows in by_l2_profile_slice.items():
        profile = group_values[0]
        scenario_values = group_values[1:]
        scenario_rows = by_scenario.get(tuple(scenario_values), [])
        non_l2_success_profiles = sorted(
            {
                str(row.get("profile_name", ""))
                for row in scenario_rows
                if not str(row.get("profile_name", "")).startswith("L2_")
                and str(row.get("outcome_bucket", "")) == "success_obstacle_pass"
            }
        )
        outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in group_rows)
        success_count = int(outcome_counts.get("success_obstacle_pass", 0))
        output.append(
            {
                "profile_name": profile,
                "feasibility_tier_id": scenario_values[0],
                "source_role_semantics": scenario_values[1],
                "surface_variant": scenario_values[2],
                "sampled_obstacle_label": scenario_values[3],
                "l2_episode_count": len(group_rows),
                "l2_success_count": success_count,
                "l2_collision_count": int(outcome_counts.get("collision_failure", 0)),
                "l2_offtrack_outcome_count": int(outcome_counts.get("off_track_noncollision_noncompletion", 0)),
                "l2_zero_success": success_count == 0,
                "non_l2_same_slice_success_count": sum(
                    1
                    for row in scenario_rows
                    if not str(row.get("profile_name", "")).startswith("L2_")
                    and str(row.get("outcome_bucket", "")) == "success_obstacle_pass"
                ),
                "non_l2_same_slice_success_profile_count": len(non_l2_success_profiles),
                "non_l2_same_slice_success_profiles": ";".join(non_l2_success_profiles),
                "same_slice_non_l2_success_l2_zero_pattern": success_count == 0 and bool(non_l2_success_profiles),
            }
        )
    return output


def comparison_support_candidates(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scenario_keys = ("feasibility_tier_id", "source_role_semantics", "surface_variant", "sampled_obstacle_label")
    output: list[dict[str, Any]] = []
    for group_values, group_rows in _group_rows(rows, scenario_keys).items():
        outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in group_rows)
        episode_count = len(group_rows)
        success_count = int(outcome_counts.get("success_obstacle_pass", 0))
        collision_count = int(outcome_counts.get("collision_failure", 0))
        offtrack_count = int(outcome_counts.get("off_track_noncollision_noncompletion", 0))
        profiles_with_success = sorted(
            {
                str(row.get("profile_name", ""))
                for row in group_rows
                if str(row.get("outcome_bucket", "")) == "success_obstacle_pass"
            }
        )
        collision_rate = collision_count / episode_count if episode_count else 0.0
        offtrack_rate = offtrack_count / episode_count if episode_count else 0.0
        support = (
            "comparison_ready_candidate"
            if success_count >= 5
            and episode_count >= 20
            and offtrack_rate < 0.70
            and collision_rate < 0.30
            and len(profiles_with_success) >= 2
            else support_label(
                episode_count=episode_count,
                success_count=success_count,
                offtrack_rate=offtrack_rate,
                collision_rate=collision_rate,
            )
        )
        if support not in {"candidate_support", "comparison_ready_candidate"}:
            continue
        output.append(
            {
                "feasibility_tier_id": group_values[0],
                "source_role_semantics": group_values[1],
                "surface_variant": group_values[2],
                "sampled_obstacle_label": group_values[3],
                "episode_count": episode_count,
                "success_count": success_count,
                "collision_count": collision_count,
                "offtrack_outcome_count": offtrack_count,
                "success_rate": success_count / episode_count if episode_count else 0.0,
                "collision_rate": collision_rate,
                "offtrack_outcome_rate": offtrack_rate,
                "nonzero_success_profile_count": len(profiles_with_success),
                "profiles_with_success": ";".join(profiles_with_success),
                "support_label": support,
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "no_rerun_outcome_localization_completed",
            "admissible": True,
            "reason": "M1942 reads existing M1938 artifacts and writes diagnostic aggregates only",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "low-support public diagnostic localization is not a ranking experiment",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "L2 zero-success localization is diagnostic and requires a later controlled comparison",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "single public diagnostic panel is not paper-level evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "outcome localization does not test wrong-history or history necessity",
        },
    ]


def _required_artifacts(output: Path) -> dict[str, str]:
    artifacts = {
        "summary": output / "summary.json",
        "claim_boundary": output / "claim_boundary.csv",
        "success_source_rows": output / "success_source_rows.csv",
        "offtrack_dominance_rows": output / "offtrack_dominance_rows.csv",
        "collision_dominance_rows": output / "collision_dominance_rows.csv",
        "l2_zero_success_diagnostic": output / "l2_zero_success_diagnostic.csv",
        "comparison_support_candidates": output / "comparison_support_candidates.csv",
        "run_state": output / "run_state.json",
    }
    for name in AGGREGATE_SPECS:
        artifacts[name] = output / f"{name}.csv"
    return {key: str(value) for key, value in artifacts.items()}


def localize_measured_outcomes(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    target_tier_count: int = TARGET_TIER_COUNT,
    target_role_count: int = TARGET_ROLE_COUNT,
    target_surface_count: int = TARGET_SURFACE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    episode_rows = [dict(row) for row in read_csv_rows(episode_rows_path)]

    aggregate_rows: dict[str, list[dict[str, Any]]] = {}
    all_aggregate_rows: list[dict[str, Any]] = []
    for name, keys in AGGREGATE_SPECS.items():
        rows = aggregate_outcomes(episode_rows, keys, slice_kind=name)
        aggregate_rows[name] = rows
        all_aggregate_rows.extend(rows)
        fieldnames = [*keys, *AGGREGATE_FIELDNAMES]
        write_csv_rows(output / f"{name}.csv", rows, fieldnames=fieldnames)

    success_rows = success_source_rows(episode_rows)
    offtrack_rows = dominance_rows(all_aggregate_rows, dominance_type="offtrack")
    collision_rows = dominance_rows(all_aggregate_rows, dominance_type="collision")
    l2_rows = l2_zero_success_diagnostic(episode_rows)
    comparison_rows = comparison_support_candidates(episode_rows)
    claim_rows = claim_boundary_rows()

    write_csv_rows(output / "success_source_rows.csv", success_rows, fieldnames=SUCCESS_SOURCE_FIELDNAMES)
    write_csv_rows(output / "offtrack_dominance_rows.csv", offtrack_rows, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(output / "collision_dominance_rows.csv", collision_rows, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(output / "l2_zero_success_diagnostic.csv", l2_rows, fieldnames=L2_DIAGNOSTIC_FIELDNAMES)
    write_csv_rows(
        output / "comparison_support_candidates.csv",
        comparison_rows,
        fieldnames=COMPARISON_CANDIDATE_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)

    outcome_counts = _count_by(episode_rows, "outcome_bucket")
    source_outcome_counts = {str(key): int(value) for key, value in source_summary.get("outcome_counts", {}).items()}
    outcome_counts_match_source_summary = outcome_counts == source_outcome_counts
    profile_count = len({str(row.get("profile_name", "")) for row in episode_rows})
    tier_count = len({str(row.get("feasibility_tier_id", "")) for row in episode_rows})
    role_count = len({str(row.get("source_role_semantics", "")) for row in episode_rows})
    surface_count = len({str(row.get("surface_variant", "")) for row in episode_rows})
    local_guardrail_flags = {key: False for key in FORBIDDEN_LOCAL_GUARDRAILS}
    guardrail_violation_count = sum(1 for value in local_guardrail_flags.values() if value)
    artifacts = _required_artifacts(output)
    required_aggregate_files_written = all(Path(path).exists() for path in artifacts.values() if path.endswith(".csv"))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows)
    l2_total_success_count = sum(int(row["l2_success_count"]) for row in l2_rows)
    l2_same_slice_non_l2_success_count = sum(
        1 for row in l2_rows if _bool(row.get("same_slice_non_l2_success_l2_zero_pattern"))
    )
    comparison_ready_candidate_count = sum(
        1 for row in comparison_rows if str(row.get("support_label", "")) == "comparison_ready_candidate"
    )
    result_passes = (
        source_summary.get("result_class") == "task_quality_measured_execution_pass"
        and len(episode_rows) == int(target_episode_count)
        and profile_count == int(target_profile_count)
        and tier_count == int(target_tier_count)
        and role_count == int(target_role_count)
        and surface_count == int(target_surface_count)
        and outcome_counts_match_source_summary
        and all_selected_metrics_finite
        and required_aggregate_files_written
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "task_quality_measured_outcome_localization_pass"
            if result_passes
            else "task_quality_measured_outcome_localization_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary_path": str(summary_path),
        "episode_rows_path": str(episode_rows_path),
        "source_result_class": source_summary.get("result_class", ""),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "profile_count": profile_count,
        "target_profile_count": int(target_profile_count),
        "tier_count": tier_count,
        "target_tier_count": int(target_tier_count),
        "role_count": role_count,
        "target_role_count": int(target_role_count),
        "surface_count": surface_count,
        "target_surface_count": int(target_surface_count),
        "outcome_counts": outcome_counts,
        "source_outcome_counts": source_outcome_counts,
        "outcome_counts_match_source_summary": outcome_counts_match_source_summary,
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
        "profile_counts": _count_by(episode_rows, "profile_name"),
        "tier_counts": _count_by(episode_rows, "feasibility_tier_id"),
        "role_counts": _count_by(episode_rows, "source_role_semantics"),
        "surface_counts": _count_by(episode_rows, "surface_variant"),
        "sampled_label_counts": _count_by(episode_rows, "sampled_obstacle_label"),
        "all_selected_metrics_finite": all_selected_metrics_finite,
        "required_aggregate_files_written": required_aggregate_files_written,
        "aggregate_row_counts": {name: len(rows) for name, rows in aggregate_rows.items()},
        "success_source_row_count": len(success_rows),
        "offtrack_dominance_row_count": len(offtrack_rows),
        "collision_dominance_row_count": len(collision_rows),
        "l2_zero_success_diagnostic_row_count": len(l2_rows),
        "l2_total_success_count": l2_total_success_count,
        "l2_same_slice_non_l2_success_pattern_count": l2_same_slice_non_l2_success_count,
        "comparison_support_candidate_count": len(comparison_rows),
        "comparison_ready_candidate_count": comparison_ready_candidate_count,
        "guardrail_flags": local_guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
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
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "target_episode_count": int(target_episode_count),
            "completed_count": len(episode_rows),
            "failure_count": 0 if result_passes else 1,
            "complete": bool(result_passes),
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--target-tier-count", type=int, default=TARGET_TIER_COUNT)
    parser.add_argument("--target-role-count", type=int, default=TARGET_ROLE_COUNT)
    parser.add_argument("--target-surface-count", type=int, default=TARGET_SURFACE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = localize_measured_outcomes(
        summary_path=args.summary,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        target_profile_count=int(args.target_profile_count),
        target_tier_count=int(args.target_tier_count),
        target_role_count=int(args.target_role_count),
        target_surface_count=int(args.target_surface_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"outcome_counts_match_source_summary={summary['outcome_counts_match_source_summary']}")
    print(f"comparison_ready_candidate_count={summary['comparison_ready_candidate_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
