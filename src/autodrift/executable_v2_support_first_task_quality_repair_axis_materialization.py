"""No-rollout support-first task-quality repair-axis materializer."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_support_first_clearance_containment_conflict_localization import (
    classify_primary_conflict,
    near_miss_flags,
)


DEFAULT_EPISODE_ROWS = Path("runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv")
DEFAULT_ROLE_SURFACE_AGGREGATE = Path(
    "runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/"
    "role_surface_conflict_aggregate.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization")
DEFAULT_NEXT_BLOCKER = "m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit"

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

PRESERVED_FIELDS = [
    "support_first_workload_id",
    "task_source_id",
    "support_first_v2_panel_spec_id",
    "support_first_materialized_v2_panel_spec_id",
    "source_scenario_spec_id",
    "controller_profile_name",
    "profile_name",
    "scenario_profile_name",
    "scenario_profile_group",
    "profile_config_path",
    "checkpoint_path",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "role_panel_id",
    "v2_role_surface_id",
    "surface_variant",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "sampled_obstacle_label",
    "allowed_labels_metadata_only",
    "strata",
]

REPAIR_AXIS_VARIANTS: list[dict[str, Any]] = [
    {
        "repair_axis_variant_id": "original_retained",
        "task_quality_axis_id": "baseline_and_semantics_retention",
        "repair_variant_kind": "baseline",
        "execution_row_kind": "import_existing_episode",
        "target_conflict_class": "baseline",
        "target_near_miss_class": "none",
        "geometry_delta": {},
        "semantics_delta": {"baseline_retained": True},
    },
    {
        "repair_axis_variant_id": "role_semantics_only",
        "task_quality_axis_id": "baseline_and_semantics_retention",
        "repair_variant_kind": "semantics",
        "execution_row_kind": "postprocess_existing_episode",
        "target_conflict_class": "all",
        "target_near_miss_class": "all",
        "geometry_delta": {},
        "semantics_delta": {"role_aware_diagnostic_fields": True},
    },
    {
        "repair_axis_variant_id": "post_clearance_recovery_window_plus",
        "task_quality_axis_id": "post_clearance_containment_recovery",
        "repair_variant_kind": "geometry",
        "execution_row_kind": "rollout_geometry_variant",
        "target_conflict_class": "clearance_only_offtrack",
        "target_near_miss_class": "late_offtrack_after_clearance",
        "geometry_delta": {"finish_rule": "post_obstacle_recovery_window_plus", "max_steps_multiplier": 1.5},
        "semantics_delta": {"role_aware_diagnostic_fields": True},
    },
    {
        "repair_axis_variant_id": "post_obstacle_containment_corridor_plus",
        "task_quality_axis_id": "post_clearance_containment_recovery",
        "repair_variant_kind": "geometry",
        "execution_row_kind": "rollout_geometry_variant",
        "target_conflict_class": "clearance_only_offtrack",
        "target_near_miss_class": "near_containment_after_clearance",
        "geometry_delta": {
            "road_corridor_rule": "post_obstacle_only",
            "post_obstacle_track_width_multiplier": 1.35,
            "pre_obstacle_track_width_multiplier": 1.0,
        },
        "semantics_delta": {"role_aware_diagnostic_fields": True},
    },
    {
        "repair_axis_variant_id": "post_clearance_recovery_corridor_combo",
        "task_quality_axis_id": "post_clearance_containment_recovery",
        "repair_variant_kind": "geometry",
        "execution_row_kind": "rollout_geometry_variant",
        "target_conflict_class": "clearance_only_offtrack",
        "target_near_miss_class": "near_containment_after_clearance",
        "geometry_delta": {
            "finish_rule": "post_obstacle_recovery_window_plus",
            "max_steps_multiplier": 1.5,
            "road_corridor_rule": "post_obstacle_only",
            "post_obstacle_track_width_multiplier": 1.35,
            "pre_obstacle_track_width_multiplier": 1.0,
        },
        "semantics_delta": {"role_aware_diagnostic_fields": True},
    },
    {
        "repair_axis_variant_id": "contained_clearance_gap_plus",
        "task_quality_axis_id": "contained_collision_clearance_feasibility",
        "repair_variant_kind": "geometry",
        "execution_row_kind": "rollout_geometry_variant",
        "target_conflict_class": "containment_collision",
        "target_near_miss_class": "near_clearance_with_containment",
        "geometry_delta": {"obstacle_clearance_gap_delta_m": 0.25, "road_geometry_fixed": True},
        "semantics_delta": {"role_aware_diagnostic_fields": True},
    },
    {
        "repair_axis_variant_id": "contained_reaction_distance_plus",
        "task_quality_axis_id": "contained_collision_clearance_feasibility",
        "repair_variant_kind": "geometry",
        "execution_row_kind": "rollout_geometry_variant",
        "target_conflict_class": "containment_collision",
        "target_near_miss_class": "near_clearance_with_containment",
        "geometry_delta": {"obstacle_reaction_distance_delta_m": 5.0, "road_geometry_fixed": True},
        "semantics_delta": {"role_aware_diagnostic_fields": True},
    },
    {
        "repair_axis_variant_id": "mitigation_scored_semantics",
        "task_quality_axis_id": "unavoidable_mitigation_semantics",
        "repair_variant_kind": "semantics",
        "execution_row_kind": "postprocess_existing_episode",
        "target_conflict_class": "unavoidable_mitigation",
        "target_near_miss_class": "impact_severity_proxy",
        "geometry_delta": {},
        "semantics_delta": {
            "mitigation_score_panel": True,
            "collision_free_pass_is_diagnostic_not_primary": True,
        },
    },
]

TASK_QUALITY_AXIS_SPEC: dict[str, Any] = {
    "axis_spec_id": "support_first_task_quality_repair_axis_v1",
    "diagnostic_only_no_ranking_claim": True,
    "axes": {
        "baseline_and_semantics_retention": {
            "purpose": "retain original evidence and add role-aware diagnostic semantics",
            "primary_conflict": "all",
        },
        "post_clearance_containment_recovery": {
            "purpose": "test recovery window and post-obstacle containment corridor after obstacle clearance",
            "primary_conflict": "clearance_only_offtrack",
        },
        "contained_collision_clearance_feasibility": {
            "purpose": "test whether contained collisions are just beyond clearance/timing feasibility",
            "primary_conflict": "containment_collision",
        },
        "unavoidable_mitigation_semantics": {
            "purpose": "score unavoidable mitigation with continuous impact and bounded-departure metrics",
            "primary_conflict": "unavoidable_mitigation",
        },
    },
    "forbidden_shortcuts": list(FORBIDDEN_GUARDRAILS)
    + [
        "controller_profile_tuning",
        "actor_input_changes",
        "controller_family_ranking",
        "paper_level_claim",
        "level3_self_id_claim",
    ],
}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _json_string(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _unique_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows})


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_violation_count(rows: Iterable[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows for key in FORBIDDEN_GUARDRAILS if _bool(row.get(key)))


def _original_rows(episode_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [row for row in episode_rows if str(row.get("repair_variant_id", "")) == "original"]
    return sorted(rows, key=lambda row: (str(row.get("support_first_workload_id", "")), str(row.get("workload_id", ""))))


def _surface_axis_targets(role_surface_rows: list[Mapping[str, Any]]) -> dict[str, set[str]]:
    targets: dict[str, set[str]] = defaultdict(lambda: {"baseline_and_semantics_retention"})
    for row in role_surface_rows:
        surface = str(row.get("v2_role_surface_id", ""))
        if _float(row.get("clearance_only_offtrack_rate")) > 0.0 or _float(
            row.get("near_containment_after_clearance_rate")
        ) > 0.0:
            targets[surface].add("post_clearance_containment_recovery")
        if _float(row.get("containment_collision_rate")) > 0.0 or _float(
            row.get("near_clearance_with_containment_rate")
        ) > 0.0:
            targets[surface].add("contained_collision_clearance_feasibility")
        if surface.startswith("unavoidable_mitigation::"):
            targets[surface].add("unavoidable_mitigation_semantics")
    return targets


def build_role_surface_axis_target_map(role_surface_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    targets = _surface_axis_targets(role_surface_rows)
    output_rows: list[dict[str, Any]] = []
    for row in sorted(role_surface_rows, key=lambda item: str(item.get("v2_role_surface_id", ""))):
        surface = str(row.get("v2_role_surface_id", ""))
        for axis in sorted(targets[surface]):
            output_rows.append(
                {
                    "v2_role_surface_id": surface,
                    "task_quality_axis_id": axis,
                    "axis_applicable": True,
                    "episode_count": row.get("episode_count", ""),
                    "clearance_only_offtrack_rate": row.get("clearance_only_offtrack_rate", ""),
                    "containment_collision_rate": row.get("containment_collision_rate", ""),
                    "near_containment_after_clearance_rate": row.get("near_containment_after_clearance_rate", ""),
                    "near_clearance_with_containment_rate": row.get("near_clearance_with_containment_rate", ""),
                    "diagnostic_only_no_ranking_claim": True,
                }
            )
    return output_rows


def _axis_applicability(row: Mapping[str, Any], variant: Mapping[str, Any], targets: Mapping[str, set[str]]) -> str:
    axis = str(variant["task_quality_axis_id"])
    if axis == "baseline_and_semantics_retention":
        return "all"
    surface = str(row.get("v2_role_surface_id", ""))
    if axis == "unavoidable_mitigation_semantics":
        return "targeted" if str(row.get("role_panel_id", "")).startswith("unavoidable_mitigation") else "diagnostic_control"
    return "targeted" if axis in targets.get(surface, set()) else "diagnostic_control"


def materialize_axis_matrix(
    *,
    original_rows: list[Mapping[str, Any]],
    role_surface_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    targets = _surface_axis_targets(role_surface_rows)
    matrix_rows: list[dict[str, Any]] = []
    for base_index, base in enumerate(original_rows):
        flags = near_miss_flags(base)
        source_conflict_class = classify_primary_conflict(base)
        source_near_miss_flags = [key for key, value in flags.items() if value]
        source_workload_id = str(base.get("workload_id", ""))
        source_key = str(base.get("support_first_workload_id") or source_workload_id or base_index)
        for variant_index, variant in enumerate(REPAIR_AXIS_VARIANTS):
            variant_id = str(variant["repair_axis_variant_id"])
            row: dict[str, Any] = {
                "task_quality_repair_axis_row_id": f"m1902-axis-{base_index:04d}-{variant_index:02d}",
                "task_quality_axis_id": variant["task_quality_axis_id"],
                "repair_axis_variant_id": variant_id,
                "axis_applicability": _axis_applicability(base, variant, targets),
                "target_conflict_class": variant["target_conflict_class"],
                "target_near_miss_class": variant["target_near_miss_class"],
                "target_role_surface_id": base.get("v2_role_surface_id", ""),
                "repair_variant_kind": variant["repair_variant_kind"],
                "execution_row_kind": variant["execution_row_kind"],
                "geometry_delta_json": _json_string(variant["geometry_delta"]),
                "semantics_delta_json": _json_string(variant["semantics_delta"]),
                "source_conflict_class": source_conflict_class,
                "source_near_miss_flags": ";".join(source_near_miss_flags),
                "source_clearance_margin": base.get("min_clearance_margin", ""),
                "source_max_off_track_overshoot": base.get("max_off_track_overshoot", ""),
                "source_impact_severity_proxy": base.get("impact_severity_proxy", ""),
                "source_episode_workload_id": source_workload_id,
                "base_task_source_id": base.get("task_source_id", ""),
                "base_support_first_workload_id": source_key,
                "axis_task_source_id": f"{base.get('task_source_id', '')}__m1902_{variant_id}",
                "axis_workload_id": f"{source_key}__m1902_{variant_id}",
                "actor_input_contract_changed": False,
                "profile_specific_tuning": False,
                "controller_family_ranking_claim_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
                "diagnostic_only_no_ranking_claim": True,
                "environment_reset_scheduled": False,
                "environment_rollout_scheduled": variant["execution_row_kind"] == "rollout_geometry_variant",
                "measured_rollout_scheduled": variant["execution_row_kind"] == "rollout_geometry_variant",
                "training_scheduled": False,
                "private_holdout_used": False,
            }
            for field in PRESERVED_FIELDS:
                row[field] = base.get(field, "")
            matrix_rows.append(row)
    return matrix_rows


def duplicate_axis_keys(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = "|".join(
            [
                str(row.get("base_support_first_workload_id", "")),
                str(row.get("repair_axis_variant_id", "")),
            ]
        )
        grouped[key].append(row)
    return [
        {
            "axis_key": key,
            "duplicate_count": len(group),
            "row_ids": ";".join(str(row.get("task_quality_repair_axis_row_id", "")) for row in group),
        }
        for key, group in sorted(grouped.items())
        if len(group) > 1
    ]


def build_summary(
    *,
    source_episode_rows: list[Mapping[str, Any]],
    original_rows: list[Mapping[str, Any]],
    matrix_rows: list[Mapping[str, Any]],
    target_map_rows: list[Mapping[str, Any]],
    duplicate_rows: list[Mapping[str, Any]],
    output_dir: Path,
    target_source_spec_count: int | None,
    target_controller_profile_count: int | None,
    target_repair_axis_variant_count: int | None,
    target_matrix_row_count: int | None,
    target_original_retained_row_count: int | None,
    next_blocker: str,
) -> dict[str, Any]:
    source_spec_count = _unique_count(original_rows, "support_first_v2_panel_spec_id")
    controller_profile_count = _unique_count(original_rows, "controller_profile_name")
    role_surface_count = _unique_count(original_rows, "v2_role_surface_id")
    variant_counts = _count_by(matrix_rows, "repair_axis_variant_id")
    axis_counts = _count_by(matrix_rows, "task_quality_axis_id")
    applicability_counts = _count_by(matrix_rows, "axis_applicability")
    original_retained_rows = [
        row for row in matrix_rows if str(row.get("repair_axis_variant_id", "")) == "original_retained"
    ]
    geometry_variant_rows = [
        row for row in matrix_rows if str(row.get("execution_row_kind", "")) == "rollout_geometry_variant"
    ]
    expected_matrix_rows = len(original_rows) * len(REPAIR_AXIS_VARIANTS)
    required_outputs = {
        "summary_json": str(output_dir / "summary.json"),
        "task_quality_repair_axis_matrix_csv": str(output_dir / "task_quality_repair_axis_matrix.csv"),
        "task_quality_repair_axis_spec_json": str(output_dir / "task_quality_repair_axis_spec.json"),
        "role_surface_axis_target_map_csv": str(output_dir / "role_surface_axis_target_map.csv"),
        "duplicate_axis_keys_csv": str(output_dir / "duplicate_axis_keys.csv"),
    }
    # Parent episode rows may legitimately contain historical rollout flags.
    # M1902 is a no-rollout materialization, so guardrails apply to the rows
    # produced by this helper, not to inherited source execution provenance.
    guardrail_violation_count = _guardrail_violation_count(matrix_rows)

    checks = {
        "target_source_spec_count_passed": target_source_spec_count is None
        or source_spec_count == target_source_spec_count,
        "target_controller_profile_count_passed": target_controller_profile_count is None
        or controller_profile_count == target_controller_profile_count,
        "target_repair_axis_variant_count_passed": target_repair_axis_variant_count is None
        or len(variant_counts) == target_repair_axis_variant_count,
        "target_matrix_row_count_passed": target_matrix_row_count is None
        or len(matrix_rows) == target_matrix_row_count,
        "target_original_retained_row_count_passed": target_original_retained_row_count is None
        or len(original_retained_rows) == target_original_retained_row_count,
        "expected_matrix_row_count_passed": len(matrix_rows) == expected_matrix_rows,
        "all_controller_profiles_represented": controller_profile_count == _unique_count(matrix_rows, "controller_profile_name"),
        "all_role_surfaces_represented": role_surface_count == _unique_count(matrix_rows, "v2_role_surface_id"),
        "all_variants_nonempty": all(count == len(original_rows) for count in variant_counts.values()),
        "original_baseline_retained": len(original_retained_rows) == len(original_rows),
        "duplicate_axis_key_count_zero": len(duplicate_rows) == 0,
        "guardrail_violation_count_zero": guardrail_violation_count == 0,
    }
    result_class = (
        "task_quality_repair_axis_materialization_pass"
        if all(checks.values())
        else "task_quality_repair_axis_materialization_needs_audit"
    )
    return {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_episode_row_count": len(source_episode_rows),
        "base_original_row_count": len(original_rows),
        "source_spec_count": source_spec_count,
        "controller_profile_count": controller_profile_count,
        "role_surface_count": role_surface_count,
        "repair_axis_variant_count": len(variant_counts),
        "repair_axis_variant_ids": sorted(variant_counts),
        "repair_axis_variant_counts": variant_counts,
        "task_quality_axis_counts": axis_counts,
        "axis_applicability_counts": applicability_counts,
        "repair_axis_matrix_row_count": len(matrix_rows),
        "expected_repair_axis_matrix_row_count": expected_matrix_rows,
        "original_retained_row_count": len(original_retained_rows),
        "geometry_rollout_variant_row_count": len(geometry_variant_rows),
        "role_surface_axis_target_map_row_count": len(target_map_rows),
        "duplicate_axis_key_count": len(duplicate_rows),
        "guardrail_violation_count": guardrail_violation_count,
        "target_source_spec_count": target_source_spec_count,
        "target_controller_profile_count": target_controller_profile_count,
        "target_repair_axis_variant_count": target_repair_axis_variant_count,
        "target_matrix_row_count": target_matrix_row_count,
        "target_original_retained_row_count": target_original_retained_row_count,
        "checks": checks,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "policy_action_executed": False,
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
        "ranking_blocked": True,
        "required_outputs": required_outputs,
        "next_blocker": next_blocker,
    }


def materialize(
    *,
    episode_rows_path: Path | str,
    role_surface_conflict_aggregate_path: Path | str,
    output_dir: Path | str,
    target_source_spec_count: int | None = None,
    target_controller_profile_count: int | None = None,
    target_repair_axis_variant_count: int | None = None,
    target_matrix_row_count: int | None = None,
    target_original_retained_row_count: int | None = None,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_episode_rows = _read_csv_rows(episode_rows_path)
    original = _original_rows(source_episode_rows)
    role_surface_rows = _read_csv_rows(role_surface_conflict_aggregate_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    target_map_rows = build_role_surface_axis_target_map(role_surface_rows)
    matrix_rows = materialize_axis_matrix(original_rows=original, role_surface_rows=role_surface_rows)
    duplicate_rows = duplicate_axis_keys(matrix_rows)
    summary = build_summary(
        source_episode_rows=source_episode_rows,
        original_rows=original,
        matrix_rows=matrix_rows,
        target_map_rows=target_map_rows,
        duplicate_rows=duplicate_rows,
        output_dir=output,
        target_source_spec_count=target_source_spec_count,
        target_controller_profile_count=target_controller_profile_count,
        target_repair_axis_variant_count=target_repair_axis_variant_count,
        target_matrix_row_count=target_matrix_row_count,
        target_original_retained_row_count=target_original_retained_row_count,
        next_blocker=next_blocker,
    )

    write_csv_rows(output / "task_quality_repair_axis_matrix.csv", matrix_rows)
    write_csv_rows(output / "role_surface_axis_target_map.csv", target_map_rows)
    write_csv_rows(output / "duplicate_axis_keys.csv", duplicate_rows)
    write_json(
        output / "task_quality_repair_axis_spec.json",
        {
            **TASK_QUALITY_AXIS_SPEC,
            "repair_axis_variants": REPAIR_AXIS_VARIANTS,
        },
    )
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--role-surface-conflict-aggregate", type=Path, default=DEFAULT_ROLE_SURFACE_AGGREGATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-source-spec-count", type=int, default=None)
    parser.add_argument("--target-controller-profile-count", type=int, default=None)
    parser.add_argument("--target-repair-axis-variant-count", type=int, default=None)
    parser.add_argument("--target-matrix-row-count", type=int, default=None)
    parser.add_argument("--target-original-retained-row-count", type=int, default=None)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize(
        episode_rows_path=args.episode_rows,
        role_surface_conflict_aggregate_path=args.role_surface_conflict_aggregate,
        output_dir=args.output_dir,
        target_source_spec_count=args.target_source_spec_count,
        target_controller_profile_count=args.target_controller_profile_count,
        target_repair_axis_variant_count=args.target_repair_axis_variant_count,
        target_matrix_row_count=args.target_matrix_row_count,
        target_original_retained_row_count=args.target_original_retained_row_count,
        next_blocker=args.next_blocker,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if str(summary["result_class"]).endswith("_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
