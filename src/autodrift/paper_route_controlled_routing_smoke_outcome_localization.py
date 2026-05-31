"""No-rerun outcome localization for the controlled routing-smoke panel."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SUMMARY = Path("runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json")
DEFAULT_EPISODE_ROWS = Path("runs/m2039_paper_route_controlled_routing_smoke_measured_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2042_paper_route_controlled_routing_smoke_outcome_localization")
DEFAULT_NEXT_BLOCKER = "m2043-paper-route-controlled-routing-smoke-outcome-localization-result-audit"

TARGET_EPISODE_COUNT = 432
TARGET_PROFILE_COUNT = 12
TARGET_SPEC_COUNT = 36
TARGET_FAMILY_COUNT = 5

OUTCOME_VALUES = (
    "success_obstacle_pass",
    "collision_failure",
    "off_track_noncollision_noncompletion",
)
SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
REQUIRED_SCHEMA_FIELDS = (
    "workload_id",
    "task_source_id",
    "panel_source_id",
    "panel_task_family",
    "source_origin",
    "source_kind",
    "source_edge",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "source_reference",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
    "profile_name",
    "outcome_bucket",
    "termination_reason",
)
AGGREGATE_SPECS: dict[str, tuple[str, ...]] = {
    "outcome_by_profile": ("profile_name",),
    "outcome_by_family": ("panel_task_family",),
    "outcome_by_source_kind": ("source_kind",),
    "outcome_by_proxy_template": ("proxy_template_family",),
    "outcome_by_generated_proxy": ("generated_source_row", "materialization_semantics", "paper_validity_claim"),
    "outcome_by_sampled_label": ("sampled_obstacle_label",),
    "outcome_by_profile_family": ("profile_name", "panel_task_family"),
    "outcome_by_profile_source_kind": ("profile_name", "source_kind"),
    "outcome_by_profile_generated_proxy": (
        "profile_name",
        "generated_source_row",
        "materialization_semantics",
        "paper_validity_claim",
    ),
    "outcome_by_source_profile": ("task_source_id", "profile_name"),
    "outcome_by_source_family_kind": ("task_source_id", "panel_task_family", "source_kind"),
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
    "success_profile_count",
    "profiles_with_success",
    "success_source_count",
    "sources_with_success",
    "all_selected_metrics_finite",
    "success_obstacle_pass",
    "collision_failure",
    "off_track_noncollision_noncompletion",
    "termination_off_track",
    "termination_obstacle_collision",
    "termination_empty",
]
SUCCESS_ROW_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "panel_source_id",
    "panel_task_family",
    "source_kind",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
    "profile_name",
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
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "support_label",
    "profile_name",
    "panel_task_family",
    "source_kind",
    "proxy_template_family",
    "generated_source_row",
    "materialization_semantics",
    "paper_validity_claim",
]
COMPARISON_CANDIDATE_FIELDNAMES = [
    "slice_kind",
    "support_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "success_profile_count",
    "profiles_with_success",
    "success_source_count",
    "sources_with_success",
    "profile_name",
    "panel_task_family",
    "source_kind",
    "proxy_template_family",
    "generated_source_row",
    "materialization_semantics",
    "paper_validity_claim",
]
CLAIM_BOUNDARY_FIELDNAMES = ["claim", "admissible", "reason"]
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
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_nan(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if math.isfinite(result) else float("nan")


def _metric(row: Mapping[str, Any], metric: str) -> float:
    if metric == "success":
        return 1.0 if _bool(row.get("success")) else 0.0
    if metric == "collision":
        return 1.0 if _bool(row.get("collision")) else 0.0
    return _float_or_nan(row.get(metric, "nan"))


def selected_metrics_are_finite(rows: Iterable[Mapping[str, Any]]) -> bool:
    return all(math.isfinite(_metric(row, metric)) for row in rows for metric in SELECTED_METRICS)


def _mean_metric(rows: list[Mapping[str, Any]], metric: str) -> float | None:
    values = [_metric(row, metric) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return None
    return float(sum(finite) / len(finite))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_rows(rows: Iterable[Mapping[str, Any]], keys: Sequence[str]) -> dict[tuple[str, ...], list[Mapping[str, Any]]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)
    return dict(sorted(groups.items()))


def schema_missing_fields(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    if not rows:
        return list(REQUIRED_SCHEMA_FIELDS)
    available = set(rows[0])
    return [field for field in REQUIRED_SCHEMA_FIELDS if field not in available]


def support_label(
    *,
    episode_count: int,
    success_count: int,
    collision_rate: float,
    offtrack_rate: float,
    success_profile_count: int,
    success_source_count: int,
) -> str:
    if success_count == 0:
        return "no_support"
    if (
        episode_count >= 24
        and success_count >= 6
        and success_profile_count >= 3
        and success_source_count >= 3
        and collision_rate < 0.30
        and offtrack_rate < 0.70
    ):
        return "comparison_ready_candidate"
    if (
        episode_count >= 12
        and success_count >= 3
        and success_profile_count >= 2
        and collision_rate < 0.40
        and offtrack_rate < 0.85
    ):
        return "candidate_support"
    return "weak_support"


def aggregate_outcomes(rows: list[Mapping[str, Any]], keys: Sequence[str], *, slice_kind: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for group_values, group_rows in _group_rows(rows, keys).items():
        outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in group_rows)
        termination_counts = Counter(str(row.get("termination_reason", "")) for row in group_rows)
        episode_count = len(group_rows)
        success_count = int(outcome_counts.get("success_obstacle_pass", 0))
        collision_count = int(outcome_counts.get("collision_failure", 0))
        offtrack_count = int(outcome_counts.get("off_track_noncollision_noncompletion", 0))
        offtrack_termination_count = int(termination_counts.get("off_track", 0))
        profiles_with_success = sorted(
            {
                str(row.get("profile_name", ""))
                for row in group_rows
                if str(row.get("outcome_bucket", "")) == "success_obstacle_pass"
            }
        )
        sources_with_success = sorted(
            {
                str(row.get("task_source_id", ""))
                for row in group_rows
                if str(row.get("outcome_bucket", "")) == "success_obstacle_pass"
            }
        )
        collision_rate = collision_count / episode_count if episode_count else 0.0
        offtrack_rate = offtrack_count / episode_count if episode_count else 0.0
        row = {
            "slice_kind": slice_kind,
            "support_label": support_label(
                episode_count=episode_count,
                success_count=success_count,
                collision_rate=collision_rate,
                offtrack_rate=offtrack_rate,
                success_profile_count=len(profiles_with_success),
                success_source_count=len(sources_with_success),
            ),
            "episode_count": episode_count,
            "success_count": success_count,
            "collision_count": collision_count,
            "offtrack_outcome_count": offtrack_count,
            "offtrack_termination_count": offtrack_termination_count,
            "success_rate": success_count / episode_count if episode_count else 0.0,
            "collision_rate": collision_rate,
            "offtrack_outcome_rate": offtrack_rate,
            "offtrack_termination_rate": offtrack_termination_count / episode_count if episode_count else 0.0,
            "clearance_margin_mean": _mean_metric(group_rows, "min_clearance_margin"),
            "return_mean": _mean_metric(group_rows, "return"),
            "steps_mean": _mean_metric(group_rows, "steps"),
            "success_profile_count": len(profiles_with_success),
            "profiles_with_success": ";".join(profiles_with_success),
            "success_source_count": len(sources_with_success),
            "sources_with_success": ";".join(sources_with_success),
            "all_selected_metrics_finite": selected_metrics_are_finite(group_rows),
            "success_obstacle_pass": success_count,
            "collision_failure": collision_count,
            "off_track_noncollision_noncompletion": offtrack_count,
            "termination_off_track": offtrack_termination_count,
            "termination_obstacle_collision": int(termination_counts.get("obstacle_collision", 0)),
            "termination_empty": int(termination_counts.get("", 0)),
        }
        row.update({key: value for key, value in zip(keys, group_values)})
        output.append(row)
    return output


def success_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {field: row.get(field, "") for field in SUCCESS_ROW_FIELDNAMES}
        for row in rows
        if str(row.get("outcome_bucket", "")) == "success_obstacle_pass"
    ]


def dominance_rows(rows: list[dict[str, Any]], *, dominance_type: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        episode_count = int(row.get("episode_count", 0))
        if episode_count < 6:
            continue
        offtrack_rate = float(row.get("offtrack_outcome_rate", 0.0))
        collision_rate = float(row.get("collision_rate", 0.0))
        if dominance_type == "offtrack" and offtrack_rate < 0.80:
            continue
        if dominance_type == "collision" and collision_rate < 0.30:
            continue
        output.append({field: row.get(field, "") for field in DOMINANCE_FIELDNAMES} | {"dominance_type": dominance_type})
    return output


def comparison_support_candidates(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {field: row.get(field, "") for field in COMPARISON_CANDIDATE_FIELDNAMES}
        for row in aggregate_rows
        if str(row.get("support_label", "")) in {"candidate_support", "comparison_ready_candidate"}
    ]
    return sorted(
        candidates,
        key=lambda row: (
            0 if row["support_label"] == "comparison_ready_candidate" else 1,
            -float(row.get("success_count", 0)),
            -float(row.get("episode_count", 0)),
            str(row.get("slice_kind", "")),
        ),
    )


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "no_rerun_controlled_routing_smoke_outcome_localization_completed",
            "admissible": True,
            "reason": "M2042 reads existing M2039 artifacts and writes diagnostic aggregates only",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "localization identifies support slices but does not run a ranking experiment",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "routing smoke is low-support and generated proxy rows are not paper-valid benchmark tasks",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "routing smoke is not a paper-level benchmark and generated rows remain smoke proxies",
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
        "success_rows": output / "success_rows.csv",
        "offtrack_dominance_slices": output / "offtrack_dominance_slices.csv",
        "collision_dominance_slices": output / "collision_dominance_slices.csv",
        "comparison_support_candidates": output / "comparison_support_candidates.csv",
        "run_state": output / "run_state.json",
    }
    for name in AGGREGATE_SPECS:
        artifacts[name] = output / f"{name}.csv"
    return {key: str(value) for key, value in artifacts.items()}


def localize_controlled_routing_smoke_outcomes(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_family_count: int = TARGET_FAMILY_COUNT,
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
        write_csv_rows(output / f"{name}.csv", rows, fieldnames=[*keys, *AGGREGATE_FIELDNAMES])

    successes = success_rows(episode_rows)
    offtrack_slices = dominance_rows(all_aggregate_rows, dominance_type="offtrack")
    collision_slices = dominance_rows(all_aggregate_rows, dominance_type="collision")
    support_candidates = comparison_support_candidates(all_aggregate_rows)
    claim_rows = claim_boundary_rows()

    write_csv_rows(output / "success_rows.csv", successes, fieldnames=SUCCESS_ROW_FIELDNAMES)
    write_csv_rows(output / "offtrack_dominance_slices.csv", offtrack_slices, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(output / "collision_dominance_slices.csv", collision_slices, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(
        output / "comparison_support_candidates.csv",
        support_candidates,
        fieldnames=COMPARISON_CANDIDATE_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)

    missing_schema_fields = schema_missing_fields(episode_rows)
    outcome_counts = _count_by(episode_rows, "outcome_bucket")
    source_outcome_counts = {str(key): int(value) for key, value in source_summary.get("outcome_counts", {}).items()}
    profile_count = len({str(row.get("profile_name", "")) for row in episode_rows})
    spec_count = len({str(row.get("task_source_id", "")) for row in episode_rows})
    family_count = len({str(row.get("panel_task_family", "")) for row in episode_rows})
    generated_proxy_counts = _count_by(episode_rows, "generated_source_row")
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows)
    local_guardrail_flags = {key: False for key in FORBIDDEN_LOCAL_GUARDRAILS}
    guardrail_violation_count = sum(1 for value in local_guardrail_flags.values() if value)
    artifacts = _required_artifacts(output)
    required_files_written = all(Path(path).exists() for path in artifacts.values() if path.endswith(".csv"))
    outcome_counts_match_source_summary = outcome_counts == source_outcome_counts
    comparison_ready_candidate_count = sum(
        1 for row in support_candidates if str(row.get("support_label", "")) == "comparison_ready_candidate"
    )
    candidate_support_count = sum(
        1 for row in support_candidates if str(row.get("support_label", "")) == "candidate_support"
    )
    result_passes = (
        source_summary.get("result_class") == "controlled_routing_smoke_measured_execution_pass"
        and len(episode_rows) == int(target_episode_count)
        and profile_count == int(target_profile_count)
        and spec_count == int(target_spec_count)
        and family_count == int(target_family_count)
        and not missing_schema_fields
        and outcome_counts_match_source_summary
        and all_selected_metrics_finite
        and required_files_written
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "controlled_routing_smoke_outcome_localization_pass"
            if result_passes
            else "controlled_routing_smoke_outcome_localization_incomplete_or_fail"
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
        "spec_count": spec_count,
        "target_spec_count": int(target_spec_count),
        "family_count": family_count,
        "target_family_count": int(target_family_count),
        "missing_schema_fields": missing_schema_fields,
        "outcome_counts": outcome_counts,
        "source_outcome_counts": source_outcome_counts,
        "outcome_counts_match_source_summary": outcome_counts_match_source_summary,
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
        "profile_counts": _count_by(episode_rows, "profile_name"),
        "family_counts": _count_by(episode_rows, "panel_task_family"),
        "source_kind_counts": _count_by(episode_rows, "source_kind"),
        "proxy_template_counts": _count_by(episode_rows, "proxy_template_family"),
        "generated_proxy_counts": generated_proxy_counts,
        "sampled_label_counts": _count_by(episode_rows, "sampled_obstacle_label"),
        "aggregate_row_counts": {name: len(rows) for name, rows in aggregate_rows.items()},
        "success_row_count": len(successes),
        "offtrack_dominance_slice_count": len(offtrack_slices),
        "collision_dominance_slice_count": len(collision_slices),
        "comparison_support_candidate_count": candidate_support_count,
        "comparison_ready_candidate_count": comparison_ready_candidate_count,
        "all_selected_metrics_finite": all_selected_metrics_finite,
        "required_files_written": required_files_written,
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
        "finite_window_vs_gru_conclusion_made": False,
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
    parser.add_argument("--target-spec-count", type=int, default=TARGET_SPEC_COUNT)
    parser.add_argument("--target-family-count", type=int, default=TARGET_FAMILY_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = localize_controlled_routing_smoke_outcomes(
        summary_path=args.summary,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        target_profile_count=int(args.target_profile_count),
        target_spec_count=int(args.target_spec_count),
        target_family_count=int(args.target_family_count),
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
