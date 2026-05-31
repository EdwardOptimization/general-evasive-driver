"""No-rerun outcome localization for the M1915 task-quality repair-axis panel."""

from __future__ import annotations

import argparse
from collections import Counter
import math
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite
from autodrift.executable_v2_support_first_clearance_containment_conflict_localization import (
    NEAR_MISS_FLAGS,
    PRIMARY_CONFLICT_CLASSES,
    _aggregate_conflict_rows,
    _class_aggregate,
    _near_miss_aggregate,
    classify_primary_conflict,
    near_miss_flags,
)


DEFAULT_EPISODE_ROWS = Path(
    "runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/"
    "episode_rows.csv"
)
DEFAULT_SUMMARY = Path(
    "runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization"
)
DEFAULT_NEXT_BLOCKER = "m1918-executable-v2-support-first-task-quality-repair-axis-measured-branch-synthesis"
TARGET_EPISODE_COUNT = 1536
AGGREGATE_SPECS: dict[str, tuple[str, ...]] = {
    "execution_kind_conflict_aggregate": ("execution_row_kind",),
    "task_quality_axis_conflict_aggregate": ("task_quality_axis_id",),
    "repair_axis_variant_conflict_aggregate": ("repair_axis_variant_id",),
    "role_panel_conflict_aggregate": ("role_panel_id",),
    "role_surface_conflict_aggregate": ("v2_role_surface_id",),
    "controller_profile_conflict_aggregate": ("controller_profile_name",),
    "variant_profile_conflict_aggregate": ("repair_axis_variant_id", "controller_profile_name"),
    "variant_role_surface_conflict_aggregate": ("repair_axis_variant_id", "v2_role_surface_id"),
    "task_axis_variant_conflict_aggregate": ("task_quality_axis_id", "repair_axis_variant_id"),
    "classification_source_conflict_aggregate": ("classification_source",),
}
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
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
FLAG_FIELDS = (
    "obstacle_clearance_pass",
    "road_containment_pass",
    "collision_failure",
    "obstacle_pass_before_offtrack",
    "offtrack_after_clearance",
    "controlled_recovery_pass",
)


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _has_value(value: Any) -> bool:
    return str(value).strip() not in {"", "nan", "None"}


def _float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _explicit_task_quality_fields_available(row: Mapping[str, Any]) -> bool:
    return all(_has_value(row.get(field, "")) for field in FLAG_FIELDS)


def infer_task_quality_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    """Infer task-quality flags when measured rollout rows lack postprocess fields."""

    if _explicit_task_quality_fields_available(row):
        return {field: _bool_value(row.get(field)) for field in FLAG_FIELDS}

    collision = _bool_value(row.get("collision"))
    margin = _float_or_none(row.get("min_clearance_margin"))
    termination_reason = str(row.get("termination_reason", ""))
    first_pass_time = _float_or_none(row.get("first_obstacle_pass_time_s"))
    first_offtrack_time = _float_or_none(row.get("time_to_first_off_track_s"))
    obstacle_clearance_pass = (not collision) and margin is not None and margin > 0.0
    road_containment_pass = termination_reason != "off_track"
    obstacle_pass_before_offtrack = first_pass_time is not None and (
        first_offtrack_time is None or first_pass_time <= first_offtrack_time
    )
    controlled_recovery_pass = _bool_value(row.get("recovery_success")) or _bool_value(
        row.get("controlled_drift_recovery_success")
    )
    return {
        "obstacle_clearance_pass": obstacle_clearance_pass,
        "road_containment_pass": road_containment_pass,
        "collision_failure": collision,
        "obstacle_pass_before_offtrack": obstacle_pass_before_offtrack,
        "offtrack_after_clearance": obstacle_clearance_pass and termination_reason == "off_track",
        "controlled_recovery_pass": controlled_recovery_pass,
    }


def localized_conflict_rows(episode_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(episode_rows):
        explicit_fields = _explicit_task_quality_fields_available(row)
        inferred_flags = infer_task_quality_flags(row)
        enriched = {**row, **inferred_flags}
        flags = near_miss_flags(enriched)
        rows.append(
            {
                "row_index": index,
                "workload_id": row.get("workload_id", ""),
                "task_quality_repair_axis_row_id": row.get("task_quality_repair_axis_row_id", ""),
                "task_quality_axis_id": row.get("task_quality_axis_id", ""),
                "repair_axis_variant_id": row.get("repair_axis_variant_id", ""),
                "axis_applicability": row.get("axis_applicability", ""),
                "target_conflict_class": row.get("target_conflict_class", ""),
                "target_near_miss_class": row.get("target_near_miss_class", ""),
                "execution_row_kind": row.get("execution_row_kind", ""),
                "row_provenance": row.get("row_provenance", ""),
                "classification_source": (
                    "explicit_task_quality_fields" if explicit_fields else "raw_metric_inference"
                ),
                "controller_profile_name": row.get("controller_profile_name", row.get("profile_name", "")),
                "role_panel_id": row.get("role_panel_id", ""),
                "v2_role_surface_id": row.get("v2_role_surface_id", ""),
                "hidden_dynamics_bucket": row.get("hidden_dynamics_bucket", ""),
                "road_boundary_bucket": row.get("road_boundary_bucket", ""),
                "obstacle_timing_bucket": row.get("obstacle_timing_bucket", ""),
                "obstacle_lateral_bucket": row.get("obstacle_lateral_bucket", ""),
                "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
                "primary_conflict_class": classify_primary_conflict(enriched),
                **inferred_flags,
                **flags,
                "any_near_miss": any(flags.values()),
                "success": _bool_value(row.get("success")),
                "collision": _bool_value(row.get("collision")),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "max_off_track_overshoot": row.get("max_off_track_overshoot", ""),
                "impact_severity_proxy": row.get("impact_severity_proxy", ""),
                "time_to_first_off_track_s": row.get("time_to_first_off_track_s", ""),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
    return rows


def _counter(rows: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _recommended_next_route(class_counts: Mapping[str, int], near_miss_row_count: int) -> str:
    joint = int(class_counts.get("joint_clearance_containment", 0))
    if joint > 0:
        return "route_to_task_quality_aggregate_audit_before_any_ranking"
    if near_miss_row_count > 0:
        return "route_to_branch_synthesis_with_task_quality_findings"
    return "route_to_branch_synthesis_outcome_dominated"


def localize_task_quality_repair_axis_outcomes(
    *,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    summary_path: Path | str = DEFAULT_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episode_rows = [dict(row) for row in read_csv_rows(episode_rows_path)]
    source_summary = read_json(summary_path) if Path(summary_path).exists() else {}
    conflict_rows = localized_conflict_rows(episode_rows)

    write_csv_rows(output / "conflict_class_rows.csv", conflict_rows)
    class_aggregate = _class_aggregate(conflict_rows)
    near_aggregate = _near_miss_aggregate(conflict_rows)
    near_rows = [row for row in conflict_rows if _bool_value(row.get("any_near_miss"))]
    write_csv_rows(output / "conflict_class_aggregate.csv", class_aggregate)
    write_csv_rows(output / "near_miss_rows.csv", near_rows)
    write_csv_rows(output / "near_miss_aggregate.csv", near_aggregate)

    aggregate_row_counts: dict[str, int] = {
        "conflict_class_rows": len(conflict_rows),
        "conflict_class_aggregate_rows": len(class_aggregate),
        "near_miss_rows": len(near_rows),
        "near_miss_aggregate_rows": len(near_aggregate),
    }
    artifact_paths: dict[str, str] = {
        "summary": str(output / "summary.json"),
        "conflict_class_rows": str(output / "conflict_class_rows.csv"),
        "conflict_class_aggregate": str(output / "conflict_class_aggregate.csv"),
        "near_miss_rows": str(output / "near_miss_rows.csv"),
        "near_miss_aggregate": str(output / "near_miss_aggregate.csv"),
    }
    for name, keys in AGGREGATE_SPECS.items():
        rows = _aggregate_conflict_rows(conflict_rows, keys)
        write_csv_rows(output / f"{name}.csv", rows)
        aggregate_row_counts[f"{name}_rows"] = len(rows)
        artifact_paths[name] = str(output / f"{name}.csv")

    class_counts = {row["primary_conflict_class"]: int(row["episode_count"]) for row in class_aggregate}
    near_counts = {row["near_miss_flag"]: int(row["episode_count"]) for row in near_aggregate}
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    all_rows_classified_once = len(conflict_rows) == len(episode_rows) and all(
        str(row.get("primary_conflict_class", "")) in PRIMARY_CONFLICT_CLASSES for row in conflict_rows
    )
    required_aggregate_files_written = all((output / f"{name}.csv").exists() for name in AGGREGATE_SPECS)
    classification_source_counts = _counter(conflict_rows, "classification_source")
    result_passes = (
        len(episode_rows) == int(target_episode_count)
        and bool(all_selected_metrics_finite)
        and guardrail_violation_count == 0
        and all_rows_classified_once
        and required_aggregate_files_written
        and set(PRIMARY_CONFLICT_CLASSES).issubset(set(class_counts))
        and set(NEAR_MISS_FLAGS).issubset(set(near_counts))
    )
    recommended_next_route = _recommended_next_route(class_counts, len(near_rows))

    summary = {
        "result_class": (
            "task_quality_repair_axis_measured_panel_outcome_localization_pass"
            if result_passes
            else "task_quality_repair_axis_measured_panel_outcome_localization_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "episode_rows_path": str(episode_rows_path),
        "source_summary_path": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        "all_rows_classified_once": bool(all_rows_classified_once),
        "primary_conflict_classes": list(PRIMARY_CONFLICT_CLASSES),
        "primary_conflict_class_counts": class_counts,
        "near_miss_flags": list(NEAR_MISS_FLAGS),
        "near_miss_counts": near_counts,
        "near_miss_row_count": len(near_rows),
        "classification_source_counts": classification_source_counts,
        "execution_row_kind_counts": _counter(conflict_rows, "execution_row_kind"),
        "repair_axis_variant_counts": _counter(conflict_rows, "repair_axis_variant_id"),
        "task_quality_axis_counts": _counter(conflict_rows, "task_quality_axis_id"),
        "required_aggregate_files_written": bool(required_aggregate_files_written),
        "recommended_next_route": recommended_next_route,
        "ranking_blocked": True,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
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
        **aggregate_row_counts,
        "artifacts": artifact_paths,
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Localize task-quality repair-axis measured panel outcomes.")
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = localize_task_quality_repair_axis_outcomes(
        episode_rows_path=args.episode_rows,
        summary_path=args.summary,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"primary_conflict_class_counts={summary['primary_conflict_class_counts']}")
    print(f"near_miss_row_count={summary['near_miss_row_count']}")
    print(f"classification_source_counts={summary['classification_source_counts']}")
    print(f"recommended_next_route={summary['recommended_next_route']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
