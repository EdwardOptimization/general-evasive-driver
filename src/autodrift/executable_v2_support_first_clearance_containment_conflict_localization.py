"""No-rollout localization of M1895 clearance/containment conflicts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite


DEFAULT_EPISODE_ROWS = Path("runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv")
DEFAULT_SUMMARY = Path("runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization")
DEFAULT_NEXT_BLOCKER = "m1900-executable-v2-support-first-clearance-containment-conflict-localization-result-audit"
TARGET_EPISODE_COUNT = 960
PRIMARY_CONFLICT_CLASSES = (
    "joint_clearance_containment",
    "clearance_only_offtrack",
    "containment_collision",
    "collision_and_offtrack",
    "other_non_success",
)
NEAR_MISS_FLAGS = (
    "near_containment_after_clearance",
    "near_clearance_with_containment",
    "late_offtrack_after_clearance",
)
AGGREGATE_SPECS: dict[str, tuple[str, ...]] = {
    "role_panel_conflict_aggregate": ("role_panel_id",),
    "role_surface_conflict_aggregate": ("v2_role_surface_id",),
    "repair_variant_conflict_aggregate": ("repair_variant_id",),
    "repair_variant_kind_conflict_aggregate": ("repair_variant_kind",),
    "geometry_variant_conflict_aggregate": ("geometry_variant_id",),
    "success_semantics_variant_conflict_aggregate": ("success_semantics_variant_id",),
    "controller_profile_conflict_aggregate": ("controller_profile_name",),
    "hidden_dynamics_conflict_aggregate": ("hidden_dynamics_bucket",),
    "obstacle_timing_conflict_aggregate": ("obstacle_timing_bucket",),
    "obstacle_lateral_conflict_aggregate": ("obstacle_lateral_bucket",),
    "sampled_obstacle_label_conflict_aggregate": ("sampled_obstacle_label",),
    "role_surface_repair_variant_conflict_aggregate": ("v2_role_surface_id", "repair_variant_id"),
    "role_surface_profile_conflict_aggregate": ("v2_role_surface_id", "controller_profile_name"),
    "role_surface_lateral_conflict_aggregate": ("v2_role_surface_id", "obstacle_lateral_bucket"),
    "role_surface_timing_conflict_aggregate": ("v2_role_surface_id", "obstacle_timing_bucket"),
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


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _float_value(row: Mapping[str, Any], key: str) -> float:
    try:
        value = float(row.get(key, float("nan")))
    except (TypeError, ValueError):
        return float("nan")
    return value


def _finite_values(rows: Iterable[Mapping[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = _float_value(row, key)
        if math.isfinite(value):
            values.append(value)
    return values


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def _p10(values: list[float]) -> float:
    return float(np.percentile(values, 10.0)) if values else float("nan")


def classify_primary_conflict(row: Mapping[str, Any]) -> str:
    obstacle_clearance = _bool_value(row.get("obstacle_clearance_pass"))
    road_containment = _bool_value(row.get("road_containment_pass"))
    collision_failure = _bool_value(row.get("collision_failure"))
    if obstacle_clearance and road_containment:
        return "joint_clearance_containment"
    if obstacle_clearance and not road_containment and not collision_failure:
        return "clearance_only_offtrack"
    if not obstacle_clearance and road_containment and collision_failure:
        return "containment_collision"
    if not obstacle_clearance and not road_containment and collision_failure:
        return "collision_and_offtrack"
    return "other_non_success"


def near_miss_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    obstacle_clearance = _bool_value(row.get("obstacle_clearance_pass"))
    road_containment = _bool_value(row.get("road_containment_pass"))
    overshoot = _float_value(row, "max_off_track_overshoot")
    margin = _float_value(row, "min_clearance_margin")
    offtrack_time = _float_value(row, "time_to_first_off_track_s")
    return {
        "near_containment_after_clearance": bool(
            obstacle_clearance and not road_containment and math.isfinite(overshoot) and overshoot <= 0.15
        ),
        "near_clearance_with_containment": bool(
            road_containment and not obstacle_clearance and math.isfinite(margin) and margin >= -0.25
        ),
        "late_offtrack_after_clearance": bool(
            obstacle_clearance and not road_containment and math.isfinite(offtrack_time) and offtrack_time >= 2.0
        ),
    }


def conflict_class_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(episode_rows):
        flags = near_miss_flags(row)
        rows.append(
            {
                "row_index": index,
                "workload_id": row.get("workload_id", ""),
                "repaired_workload_id": row.get("repaired_workload_id", ""),
                "support_first_workload_id": row.get("support_first_workload_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "controller_profile_name": row.get("controller_profile_name", row.get("profile_name", "")),
                "role_panel_id": row.get("role_panel_id", ""),
                "v2_role_surface_id": row.get("v2_role_surface_id", ""),
                "repair_variant_id": row.get("repair_variant_id", ""),
                "repair_variant_kind": row.get("repair_variant_kind", ""),
                "geometry_variant_id": row.get("geometry_variant_id", ""),
                "success_semantics_variant_id": row.get("success_semantics_variant_id", ""),
                "hidden_dynamics_bucket": row.get("hidden_dynamics_bucket", ""),
                "obstacle_timing_bucket": row.get("obstacle_timing_bucket", ""),
                "obstacle_lateral_bucket": row.get("obstacle_lateral_bucket", ""),
                "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
                "primary_conflict_class": classify_primary_conflict(row),
                "obstacle_clearance_pass": _bool_value(row.get("obstacle_clearance_pass")),
                "road_containment_pass": _bool_value(row.get("road_containment_pass")),
                "collision_failure": _bool_value(row.get("collision_failure")),
                "obstacle_pass_before_offtrack": _bool_value(row.get("obstacle_pass_before_offtrack")),
                "offtrack_after_clearance": _bool_value(row.get("offtrack_after_clearance")),
                **flags,
                "any_near_miss": any(flags.values()),
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


def _rate(count: int, total: int) -> float:
    return float(count / total) if total else float("nan")


def _aggregate_conflict_rows(rows: list[dict[str, Any]], group_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in group_keys)].append(row)

    output_rows: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        total = len(group)
        class_counts = Counter(str(row["primary_conflict_class"]) for row in group)
        near_counts = {flag: sum(_bool_value(row.get(flag)) for row in group) for flag in NEAR_MISS_FLAGS}
        aggregate = {group_keys[index]: key[index] for index in range(len(group_keys))}
        aggregate["episode_count"] = total
        for conflict_class in PRIMARY_CONFLICT_CLASSES:
            count = int(class_counts.get(conflict_class, 0))
            aggregate[f"{conflict_class}_count"] = count
            aggregate[f"{conflict_class}_rate"] = _rate(count, total)
        for flag, count in near_counts.items():
            aggregate[f"{flag}_count"] = int(count)
            aggregate[f"{flag}_rate"] = _rate(int(count), total)
        margins = _finite_values(group, "min_clearance_margin")
        overshoots = _finite_values(group, "max_off_track_overshoot")
        impacts = _finite_values(group, "impact_severity_proxy")
        aggregate.update(
            {
                "clearance_margin_mean": _mean(margins),
                "clearance_margin_p10": _p10(margins),
                "max_off_track_overshoot_mean": _mean(overshoots),
                "impact_severity_proxy_mean": _mean(impacts),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        output_rows.append(aggregate)
    return output_rows


def _class_aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(rows)
    counts = Counter(str(row["primary_conflict_class"]) for row in rows)
    return [
        {
            "primary_conflict_class": conflict_class,
            "episode_count": int(counts.get(conflict_class, 0)),
            "episode_rate": _rate(int(counts.get(conflict_class, 0)), total),
            "diagnostic_only_no_ranking_claim": True,
        }
        for conflict_class in PRIMARY_CONFLICT_CLASSES
    ]


def _near_miss_aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(rows)
    return [
        {
            "near_miss_flag": flag,
            "episode_count": int(sum(_bool_value(row.get(flag)) for row in rows)),
            "episode_rate": _rate(int(sum(_bool_value(row.get(flag)) for row in rows)), total),
            "diagnostic_only_no_ranking_claim": True,
        }
        for flag in NEAR_MISS_FLAGS
    ]


def _recommended_next_route(class_counts: Mapping[str, int], near_miss_count: int) -> str:
    joint = int(class_counts.get("joint_clearance_containment", 0))
    clearance_only = int(class_counts.get("clearance_only_offtrack", 0))
    containment_collision = int(class_counts.get("containment_collision", 0))
    if joint > 0:
        return "route_to_controller_comparison_design_after_distribution_check"
    if clearance_only > 0 and containment_collision > 0 and near_miss_count > 0:
        return "route_to_task_quality_repair_axis_design"
    if clearance_only > 0 and containment_collision > 0:
        return "route_to_task_quality_repair_axis_design_or_branch_synthesis"
    return "route_to_branch_synthesis"


def localize_clearance_containment_conflicts(
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
    conflict_rows = conflict_class_rows(episode_rows)

    write_csv_rows(output / "conflict_class_rows.csv", conflict_rows)
    class_aggregate = _class_aggregate(conflict_rows)
    near_rows = [row for row in conflict_rows if _bool_value(row.get("any_near_miss"))]
    near_aggregate = _near_miss_aggregate(conflict_rows)
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
            "clearance_containment_conflict_localization_pass"
            if result_passes
            else "clearance_containment_conflict_localization_incomplete_or_fail"
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
    parser = argparse.ArgumentParser(description="Localize support-first clearance/containment conflicts.")
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = localize_clearance_containment_conflicts(
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
    print(f"recommended_next_route={summary['recommended_next_route']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
