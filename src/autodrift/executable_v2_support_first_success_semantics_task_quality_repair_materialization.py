"""No-rollout support-first success-semantics/task-quality repair materializer."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json


DEFAULT_WORKLOAD_MATRIX = Path(
    "runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/"
    "support_first_measured_workload_matrix.csv"
)
DEFAULT_EPISODE_ROWS = Path("runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv")
DEFAULT_LOCALIZATION_SUMMARY = Path("runs/m1882_executable_v2_support_first_outcome_localization/summary.json")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization"
)

FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "measured_rollout_started",
    "policy_action_executed",
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
    "workload_id",
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

REPAIR_VARIANTS: list[dict[str, Any]] = [
    {
        "repair_variant_id": "original",
        "repair_variant_kind": "baseline",
        "geometry_variant_id": "original_geometry",
        "success_semantics_variant_id": "original_binary_success",
        "config_delta": {},
        "diagnostic_only": True,
        "execution_design_required": False,
    },
    {
        "repair_variant_id": "semantics_only",
        "repair_variant_kind": "semantics",
        "geometry_variant_id": "original_geometry",
        "success_semantics_variant_id": "role_aware_success_v1",
        "config_delta": {"success_semantics": "role_aware_success_v1"},
        "diagnostic_only": True,
        "execution_design_required": False,
    },
    {
        "repair_variant_id": "finish_extended",
        "repair_variant_kind": "geometry",
        "geometry_variant_id": "finish_extended_v1",
        "success_semantics_variant_id": "role_aware_success_v1",
        "config_delta": {
            "success_semantics": "role_aware_success_v1",
            "finish_rule": "post_obstacle_recovery_window_v1",
            "max_steps_multiplier": 1.5,
        },
        "diagnostic_only": True,
        "execution_design_required": True,
    },
    {
        "repair_variant_id": "road_relaxed",
        "repair_variant_kind": "geometry",
        "geometry_variant_id": "road_relaxed_v1",
        "success_semantics_variant_id": "role_aware_success_v1",
        "config_delta": {
            "success_semantics": "role_aware_success_v1",
            "track_width_multiplier": 1.5,
            "offtrack_overshoot_tolerance_m": 0.5,
        },
        "diagnostic_only": True,
        "execution_design_required": True,
    },
    {
        "repair_variant_id": "road_relaxed_finish_extended",
        "repair_variant_kind": "geometry",
        "geometry_variant_id": "road_relaxed_finish_extended_v1",
        "success_semantics_variant_id": "role_aware_success_v1",
        "config_delta": {
            "success_semantics": "role_aware_success_v1",
            "track_width_multiplier": 1.5,
            "offtrack_overshoot_tolerance_m": 0.5,
            "finish_rule": "post_obstacle_recovery_window_v1",
            "max_steps_multiplier": 1.5,
        },
        "diagnostic_only": True,
        "execution_design_required": True,
    },
]


ROLE_SEMANTICS_SPEC: dict[str, Any] = {
    "semantics_id": "role_aware_success_v1",
    "diagnostic_fields": {
        "obstacle_clearance_pass": "collision == false and min_clearance_margin > 0",
        "road_containment_pass": "termination_reason != off_track",
        "obstacle_pass_before_offtrack": "first_obstacle_pass_step finite and pass time <= first offtrack time when offtrack exists",
        "offtrack_after_clearance": "obstacle_clearance_pass and termination_reason == off_track",
        "controlled_recovery_pass": "recovery_success or controlled_drift_recovery_success",
        "mitigation_quality": "collision_mitigation_score / impact_severity_proxy / impact_speed_proxy as continuous diagnostics",
    },
    "role_panels": {
        "stable_aeb": {
            "primary": ["no_collision", "road_containment", "obstacle_pass_if_present"],
            "diagnostic": ["obstacle_clearance_without_road_containment"],
        },
        "stable_aes_only": {
            "primary": ["no_collision", "obstacle_pass", "road_containment_or_bounded_recovery"],
            "diagnostic": ["offtrack_after_clearance"],
        },
        "drift_required_recovery": {
            "primary": ["no_collision", "obstacle_clearance", "controlled_recovery"],
            "diagnostic": ["drift_used_unrecovered", "offtrack_after_clearance"],
        },
        "unavoidable_mitigation": {
            "primary": ["lower_impact_severity", "bounded_road_departure"],
            "diagnostic": ["collision_free_pass_allowed_but_not_required"],
        },
    },
    "ranking_policy": "diagnostic_only_until_repaired_execution_audit",
    "actor_input_policy": "semantic labels and outcomes are metric outputs only and must not enter actor observation",
}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "nan", "none"}:
        return False
    return default


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _json_string(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _unique_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows})


def diagnostic_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    collision = _bool(row.get("collision"))
    margin = _float_or_none(row.get("min_clearance_margin"))
    obstacle_clearance_pass = (not collision) and margin is not None and margin > 0.0
    termination_reason = str(row.get("termination_reason", ""))
    first_pass_time = _float_or_none(row.get("first_obstacle_pass_time_s"))
    first_offtrack_time = _float_or_none(row.get("time_to_first_off_track_s"))
    obstacle_pass_before_offtrack = first_pass_time is not None and (
        first_offtrack_time is None or first_pass_time <= first_offtrack_time
    )
    controlled_recovery_pass = _bool(row.get("recovery_success")) or _bool(row.get("controlled_drift_recovery_success"))
    return {
        "obstacle_clearance_pass": obstacle_clearance_pass,
        "road_containment_pass": termination_reason != "off_track",
        "obstacle_pass_before_offtrack": obstacle_pass_before_offtrack,
        "offtrack_after_clearance": obstacle_clearance_pass and termination_reason == "off_track",
        "controlled_recovery_pass": controlled_recovery_pass,
        "collision_failure": collision,
    }


def role_diagnostic_summary(episode_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        grouped[str(row.get("role_panel_id", row.get("task_family", "")))].append(row)

    summaries: list[dict[str, Any]] = []
    for role, rows in sorted(grouped.items()):
        counters = Counter()
        for row in rows:
            for key, value in diagnostic_flags(row).items():
                if value:
                    counters[key] += 1
        row_count = len(rows)
        summary = {
            "role_panel_id": role,
            "row_count": row_count,
            "obstacle_clearance_pass_count": counters["obstacle_clearance_pass"],
            "road_containment_pass_count": counters["road_containment_pass"],
            "obstacle_pass_before_offtrack_count": counters["obstacle_pass_before_offtrack"],
            "offtrack_after_clearance_count": counters["offtrack_after_clearance"],
            "controlled_recovery_pass_count": counters["controlled_recovery_pass"],
            "collision_failure_count": counters["collision_failure"],
        }
        if row_count:
            for key in [
                "obstacle_clearance_pass",
                "road_containment_pass",
                "obstacle_pass_before_offtrack",
                "offtrack_after_clearance",
                "controlled_recovery_pass",
                "collision_failure",
            ]:
                summary[f"{key}_rate"] = counters[key] / row_count
        summaries.append(summary)
    return summaries


def materialize_repair_matrix(workload_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for workload_index, workload_row in enumerate(workload_rows):
        source_key = str(workload_row.get("support_first_workload_id") or workload_row.get("workload_id") or workload_index)
        for variant_index, variant in enumerate(REPAIR_VARIANTS):
            row: dict[str, Any] = {
                "repair_row_id": f"m1884-repair-{workload_index:04d}-{variant_index:02d}",
                "repair_source_key": source_key,
                "repair_variant_id": variant["repair_variant_id"],
                "repair_variant_kind": variant["repair_variant_kind"],
                "geometry_variant_id": variant["geometry_variant_id"],
                "success_semantics_variant_id": variant["success_semantics_variant_id"],
                "role_semantics_id": f"{workload_row.get('role_panel_id', '')}::role_aware_success_v1",
                "config_delta_json": _json_string(variant["config_delta"]),
                "diagnostic_only_no_ranking_claim": "True",
                "execution_design_required": str(bool(variant["execution_design_required"])),
                "environment_reset_scheduled": "False",
                "environment_rollout_scheduled": "False",
                "training_scheduled": "False",
                "profile_specific_tuning": "False",
                "actor_input_contract_changed": "False",
                "controller_family_ranking_claim_made": "False",
                "paper_level_claim_made": "False",
                "level3_self_id_claim_made": "False",
            }
            for field in PRESERVED_FIELDS:
                row[field] = str(workload_row.get(field, ""))
            rows.append(row)
    return rows


def duplicate_repair_keys(matrix_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in matrix_rows:
        key = "|".join([str(row.get("repair_source_key", "")), str(row.get("repair_variant_id", ""))])
        by_key[key].append(row)
    duplicates: list[dict[str, Any]] = []
    for key, rows in sorted(by_key.items()):
        if len(rows) > 1:
            duplicates.append(
                {
                    "repair_key": key,
                    "duplicate_count": len(rows),
                    "repair_row_ids": ";".join(str(row.get("repair_row_id", "")) for row in rows),
                }
            )
    return duplicates


def _guardrail_violation_count(workload_rows: list[Mapping[str, Any]]) -> int:
    violations = 0
    for row in workload_rows:
        for key in FORBIDDEN_GUARDRAILS:
            if _bool(row.get(key), default=False):
                violations += 1
    return violations


def build_summary(
    *,
    workload_rows: list[Mapping[str, Any]],
    episode_rows: list[Mapping[str, Any]],
    matrix_rows: list[Mapping[str, Any]],
    duplicate_rows: list[Mapping[str, Any]],
    localization_summary: Mapping[str, Any],
    output_dir: Path,
    target_workload_row_count: int | None,
    target_repair_variant_count: int | None,
    next_blocker: str,
) -> dict[str, Any]:
    variant_counts = _count_by(matrix_rows, "repair_variant_id")
    controller_profile_count = _unique_count(workload_rows, "controller_profile_name")
    role_panel_count = _unique_count(workload_rows, "role_panel_id")
    role_surface_count = _unique_count(workload_rows, "v2_role_surface_id")
    source_spec_count = _unique_count(workload_rows, "support_first_v2_panel_spec_id")
    source_profile_count = _unique_count(workload_rows, "support_first_workload_id")
    original_rows = [row for row in matrix_rows if str(row.get("repair_variant_id")) == "original"]
    guardrail_violation_count = _guardrail_violation_count(workload_rows)
    profile_alias_mismatch_count = sum(
        1
        for row in workload_rows
        if str(row.get("controller_profile_name", "")) != str(row.get("profile_name", row.get("controller_profile_name", "")))
    )
    semantic_role_set = set(ROLE_SEMANTICS_SPEC["role_panels"])
    observed_role_set = {str(row.get("role_panel_id", "")) for row in workload_rows}
    role_semantics_missing = sorted(role for role in observed_role_set if role not in semantic_role_set)

    matrix_variant_count = len(variant_counts)
    expected_matrix_row_count = len(workload_rows) * len(REPAIR_VARIANTS)
    matrix_complete = len(matrix_rows) == expected_matrix_row_count
    original_baseline_retained = len(original_rows) == len(workload_rows)
    all_profiles_preserved = controller_profile_count == _unique_count(matrix_rows, "controller_profile_name")
    target_workload_passed = target_workload_row_count is None or len(workload_rows) == target_workload_row_count
    target_variant_passed = target_repair_variant_count is None or matrix_variant_count == target_repair_variant_count
    guardrail_passed = guardrail_violation_count == 0
    role_semantics_complete = not role_semantics_missing

    result_class = (
        "support_first_success_semantics_task_quality_repair_materialization_pass"
        if all(
            [
                matrix_complete,
                original_baseline_retained,
                all_profiles_preserved,
                not duplicate_rows,
                target_workload_passed,
                target_variant_passed,
                guardrail_passed,
                role_semantics_complete,
                profile_alias_mismatch_count == 0,
            ]
        )
        else "support_first_success_semantics_task_quality_repair_materialization_needs_audit"
    )

    return {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "workload_row_count": len(workload_rows),
        "episode_row_count": len(episode_rows),
        "repair_variant_count": matrix_variant_count,
        "repair_variant_ids": sorted(variant_counts),
        "repair_variant_counts": variant_counts,
        "repair_matrix_row_count": len(matrix_rows),
        "expected_repair_matrix_row_count": expected_matrix_row_count,
        "matrix_complete": matrix_complete,
        "original_baseline_row_count": len(original_rows),
        "original_baseline_retained": original_baseline_retained,
        "controller_profile_count": controller_profile_count,
        "role_panel_count": role_panel_count,
        "role_surface_count": role_surface_count,
        "support_first_spec_count": source_spec_count,
        "source_profile_count": source_profile_count,
        "all_controller_profiles_preserved": all_profiles_preserved,
        "profile_alias_mismatch_count": profile_alias_mismatch_count,
        "duplicate_repair_key_count": len(duplicate_rows),
        "role_semantics_complete": role_semantics_complete,
        "role_semantics_missing": role_semantics_missing,
        "target_workload_row_count": target_workload_row_count,
        "target_workload_row_count_passed": target_workload_passed,
        "target_repair_variant_count": target_repair_variant_count,
        "target_repair_variant_count_passed": target_variant_passed,
        "role_diagnostic_summary": role_diagnostic_summary(episode_rows),
        "localization_result_class": localization_summary.get("result_class"),
        "localization_outcome_dominance_class": localization_summary.get("outcome_dominance_class"),
        "localization_dominant_slice_count": localization_summary.get("dominant_slice_count"),
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
        "semantic_labels_enter_actor_input": False,
        "guardrail_violation_count": guardrail_violation_count,
        "ranking_blocked": True,
        "next_blocker": next_blocker,
    }


def materialize(
    *,
    workload_matrix: Path,
    episode_rows_path: Path,
    localization_summary_path: Path,
    output_dir: Path,
    target_workload_row_count: int | None,
    target_repair_variant_count: int | None,
    next_blocker: str,
) -> dict[str, Any]:
    workload_rows = _read_csv_rows(workload_matrix)
    episode_rows = _read_csv_rows(episode_rows_path)
    localization_summary = _read_json(localization_summary_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_rows = materialize_repair_matrix(workload_rows)
    duplicate_rows = duplicate_repair_keys(matrix_rows)
    summary = build_summary(
        workload_rows=workload_rows,
        episode_rows=episode_rows,
        matrix_rows=matrix_rows,
        duplicate_rows=duplicate_rows,
        localization_summary=localization_summary,
        output_dir=output_dir,
        target_workload_row_count=target_workload_row_count,
        target_repair_variant_count=target_repair_variant_count,
        next_blocker=next_blocker,
    )

    write_csv_rows(output_dir / "repair_variant_matrix.csv", matrix_rows)
    write_csv_rows(output_dir / "duplicate_repair_keys.csv", duplicate_rows)
    write_csv_rows(output_dir / "role_diagnostic_summary.csv", summary["role_diagnostic_summary"])
    write_json(output_dir / "role_semantics_spec.json", ROLE_SEMANTICS_SPEC)
    write_json(output_dir / "repair_variant_spec.json", {"repair_variants": REPAIR_VARIANTS})
    write_json(output_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload-matrix", type=Path, default=DEFAULT_WORKLOAD_MATRIX)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--localization-summary", type=Path, default=DEFAULT_LOCALIZATION_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-workload-row-count", type=int, default=None)
    parser.add_argument("--target-repair-variant-count", type=int, default=None)
    parser.add_argument(
        "--next-blocker",
        default="m1885-executable-v2-support-first-success-semantics-task-quality-repair-materialization-result-audit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize(
        workload_matrix=args.workload_matrix,
        episode_rows_path=args.episode_rows,
        localization_summary_path=args.localization_summary,
        output_dir=args.output_dir,
        target_workload_row_count=args.target_workload_row_count,
        target_repair_variant_count=args.target_repair_variant_count,
        next_blocker=args.next_blocker,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if str(summary["result_class"]).endswith("_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
