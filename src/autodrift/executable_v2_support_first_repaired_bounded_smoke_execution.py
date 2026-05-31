"""Measured execution wrapper for support-first repaired bounded-smoke panels."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import aggregate_outcome_rows
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import (
    _load_profile_cache,
    append_csv_row,
    completed_workload_ids,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.executable_v2_support_first_measured_runner_execution import metric_completeness_rows
from autodrift.executable_v2_support_first_repaired_runner_adapter import DEFAULT_OUTPUT_DIR as DEFAULT_M1889_OUTPUT_DIR
from autodrift.executable_v2_support_first_success_semantics_task_quality_repair_materialization import (
    diagnostic_flags,
)
from autodrift.outcome_metric_instrumentation import profile_hidden_dynamics_worst_rows


DEFAULT_SUPPORT_FIRST_REPAIRED_MEASURED_SPECS = DEFAULT_M1889_OUTPUT_DIR / "repaired_measured_executable_specs.json"
DEFAULT_SUPPORT_FIRST_REPAIRED_WORKLOAD = DEFAULT_M1889_OUTPUT_DIR / "repaired_measured_workload_matrix.csv"
DEFAULT_SUPPORT_FIRST_REPAIRED_IMPORT_ROWS = DEFAULT_M1889_OUTPUT_DIR / "repaired_measured_import_rows.csv"
DEFAULT_SOURCE_EPISODE_ROWS = Path("runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv")
DEFAULT_RUN_DIR = Path("runs/m1893_executable_v2_support_first_repaired_bounded_smoke_execution")
DEFAULT_EVAL_SEED_BASE = 189300
TARGET_ROLLOUT_EPISODE_COUNT = 576
TARGET_IMPORT_EPISODE_COUNT = 384
TARGET_TOTAL_PANEL_ROW_COUNT = 960
TARGET_CONTROLLER_PROFILE_COUNT = 12
TARGET_SELECTED_SOURCE_SPEC_COUNT = 16
TARGET_REPAIRED_EXECUTABLE_SPEC_COUNT = 48
TARGET_ROLE_PANEL_COUNT = 4
TARGET_ROLE_SURFACE_COUNT = 8
TARGET_REPAIR_VARIANT_COUNT = 5
TARGET_ROLLOUT_VARIANT_COUNT = 3
TARGET_IMPORT_VARIANT_COUNT = 2
ROLLOUT_ROW_KIND = "rollout_geometry_variant"
IMPORT_ROW_KIND = "import_existing_episode"
REQUIRED_REPAIRED_METADATA_FIELDS = (
    "repair_row_id",
    "repair_source_key",
    "repair_variant_id",
    "repair_variant_kind",
    "geometry_variant_id",
    "success_semantics_variant_id",
    "role_semantics_id",
    "config_delta_json",
    "execution_row_kind",
    "semantic_recompute_required",
    "support_first_workload_id",
    "base_workload_id",
    "base_support_first_workload_id",
    "base_task_source_id",
    "base_support_first_v2_panel_spec_id",
    "source_scenario_spec_id",
    "controller_profile_name",
    "profile_name",
    "scenario_profile_name",
    "scenario_profile_group",
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
)
REPAIRED_FAILURE_FIELDNAMES = [
    "workload_id",
    "repaired_workload_id",
    "repair_row_id",
    "repair_variant_id",
    "task_source_id",
    "base_task_source_id",
    "base_workload_id",
    "controller_profile_name",
    "profile_name",
    "role_panel_id",
    "v2_role_surface_id",
    "execution_row_kind",
    "error_type",
    "error_message",
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
]
IMPORT_FAILURE_FIELDNAMES = [
    "repaired_import_row_id",
    "repair_row_id",
    "repair_variant_id",
    "base_workload_id",
    "import_source_episode_workload_id",
    "controller_profile_name",
    "profile_name",
    "role_panel_id",
    "v2_role_surface_id",
    "execution_row_kind",
    "error_type",
    "error_message",
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
]
FORBIDDEN_GUARDRAILS = (
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
AGGREGATE_FILENAMES = (
    "profile_aggregate.csv",
    "controller_profile_aggregate.csv",
    "role_panel_aggregate.csv",
    "role_surface_aggregate.csv",
    "surface_variant_aggregate.csv",
    "scenario_profile_aggregate.csv",
    "hidden_dynamics_bucket_aggregate.csv",
    "road_boundary_bucket_aggregate.csv",
    "obstacle_timing_bucket_aggregate.csv",
    "obstacle_lateral_bucket_aggregate.csv",
    "sampled_obstacle_label_aggregate.csv",
    "repair_variant_aggregate.csv",
    "repair_variant_kind_aggregate.csv",
    "geometry_variant_aggregate.csv",
    "success_semantics_variant_aggregate.csv",
    "execution_row_kind_aggregate.csv",
    "controller_profile_repair_variant_aggregate.csv",
    "controller_profile_role_surface_repair_variant_aggregate.csv",
    "role_surface_repair_variant_aggregate.csv",
    "repair_variant_outcome_aggregate.csv",
    "outcome_aggregate.csv",
    "termination_reason_aggregate.csv",
    "import_rollout_alignment.csv",
    "profile_hidden_dynamics_worst_bucket.csv",
    "metric_completeness_summary.csv",
    "metric_completeness_failures.csv",
)


def _as_bool(value: Any, *, default: bool = False) -> bool:
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


def _target_matches(actual: int, target: int | None) -> bool:
    return target is None or int(actual) == int(target)


def _unique_count(rows: Iterable[Mapping[str, Any]], field: str) -> int:
    return len({str(row.get(field, "")) for row in rows if str(row.get(field, "")).strip()})


def _duplicate_count(rows: Iterable[Mapping[str, Any]], field: str) -> int:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        value = str(row.get(field, ""))
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return len(duplicates)


def load_support_first_repaired_measured_specs(
    path: Path | str = DEFAULT_SUPPORT_FIRST_REPAIRED_MEASURED_SPECS,
) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("support_first_repaired_measured_executable_specs")
    if not isinstance(rows, list):
        raise ValueError(
            "support-first repaired bounded-smoke runner input must contain "
            "support_first_repaired_measured_executable_specs"
        )
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def repaired_rollout_workload_rows(
    path: Path | str = DEFAULT_SUPPORT_FIRST_REPAIRED_WORKLOAD,
) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["workload_id"] = str(row["workload_id"])
        item["repaired_workload_id"] = str(row.get("repaired_workload_id", row["workload_id"]))
        item["task_source_id"] = str(row["task_source_id"])
        item["controller_profile_name"] = str(row.get("controller_profile_name", row.get("profile_name", "")))
        item["profile_name"] = str(row.get("profile_name", item["controller_profile_name"]))
        item["execution_row_kind"] = str(row.get("execution_row_kind", ROLLOUT_ROW_KIND))
        item["semantic_recompute_required"] = str(row.get("semantic_recompute_required", "False"))
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


def repaired_import_metadata_rows(
    path: Path | str = DEFAULT_SUPPORT_FIRST_REPAIRED_IMPORT_ROWS,
) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["repaired_import_row_id"] = str(row.get("repaired_import_row_id", row.get("repair_row_id", "")))
        item["workload_id"] = str(item["repaired_import_row_id"])
        item["import_source_episode_workload_id"] = str(
            row.get("import_source_episode_workload_id", row.get("base_workload_id", ""))
        )
        item["controller_profile_name"] = str(row.get("controller_profile_name", row.get("profile_name", "")))
        item["profile_name"] = str(row.get("profile_name", item["controller_profile_name"]))
        item["execution_row_kind"] = str(row.get("execution_row_kind", IMPORT_ROW_KIND))
        item["semantic_recompute_required"] = str(row.get("semantic_recompute_required", "False"))
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


def _repaired_passthrough_values(row: Mapping[str, Any]) -> dict[str, Any]:
    values = {field: str(row.get(field, "")) for field in REQUIRED_REPAIRED_METADATA_FIELDS}
    values["controller_profile_name"] = str(row.get("controller_profile_name", row.get("profile_name", "")))
    values["profile_name"] = str(row.get("profile_name", values["controller_profile_name"]))
    values["sampled_obstacle_label"] = str(row.get("sampled_obstacle_label", ""))
    values["allowed_labels_metadata_only"] = str(row.get("allowed_labels_metadata_only", ""))
    return values


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _claim_boundary_flags() -> dict[str, bool]:
    return {
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
    }


def _run_repaired_workload_cell(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: dict[str, Any],
    model: Any,
    profile_row: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = run_workload_cell(
        workload_row=workload_row,
        executable_spec=executable_spec,
        profile_config=profile_config,
        model=model,
        profile_row=profile_row,
        eval_seed=eval_seed,
    )
    planned_label = str(workload_row.get("sampled_obstacle_label", ""))
    actual_label = str(row.get("obstacle_label", row.get("sampled_obstacle_label", planned_label)))
    row.update(
        {
            **_repaired_passthrough_values(workload_row),
            "workload_id": str(workload_row["workload_id"]),
            "repaired_workload_id": str(workload_row.get("repaired_workload_id", workload_row["workload_id"])),
            "task_source_id": str(workload_row["task_source_id"]),
            "support_first_v2_panel_spec_id": str(workload_row.get("support_first_v2_panel_spec_id", "")),
            "support_first_materialized_v2_panel_spec_id": str(
                workload_row.get("support_first_materialized_v2_panel_spec_id", "")
            ),
            "sampled_obstacle_label": actual_label or planned_label,
            "profile_config_path": str(profile_row["config_path"]),
            "checkpoint_path": str(profile_row["checkpoint_path"]),
            "eval_seed": int(eval_seed),
            "support_first_repaired_bounded_smoke_execution": True,
            "support_first_measured_runner_execution": False,
            "full_rollout_execution": False,
            "imported_episode_row": False,
            "environment_rollout_started": True,
            "measured_rollout_started": True,
            "policy_action_executed": True,
            **_claim_boundary_flags(),
        }
    )
    row.update(diagnostic_flags(row))
    row["success"] = bool(row.get("obstacle_completed", False)) and not bool(row.get("collision", False))
    return row


def import_episode_rows_from_source(
    *,
    import_rows: Iterable[Mapping[str, Any]],
    source_episode_rows: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_by_workload = {str(row.get("workload_id", "")): dict(row) for row in source_episode_rows}
    imported: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    alignment: list[dict[str, Any]] = []
    for import_row in import_rows:
        source_workload_id = str(import_row.get("import_source_episode_workload_id", ""))
        source = source_by_workload.get(source_workload_id)
        output_workload_id = str(import_row.get("repaired_import_row_id", import_row.get("workload_id", "")))
        alignment_row = {
            "repaired_import_row_id": output_workload_id,
            "output_workload_id": output_workload_id,
            "repair_variant_id": str(import_row.get("repair_variant_id", "")),
            "semantic_recompute_required": str(import_row.get("semantic_recompute_required", "")),
            "import_source_episode_workload_id": source_workload_id,
            "source_found": source is not None,
        }
        alignment.append(alignment_row)
        if source is None:
            failures.append(
                {
                    "repaired_import_row_id": output_workload_id,
                    "repair_row_id": str(import_row.get("repair_row_id", "")),
                    "repair_variant_id": str(import_row.get("repair_variant_id", "")),
                    "base_workload_id": str(import_row.get("base_workload_id", "")),
                    "import_source_episode_workload_id": source_workload_id,
                    "controller_profile_name": str(import_row.get("controller_profile_name", "")),
                    "profile_name": str(import_row.get("profile_name", "")),
                    "role_panel_id": str(import_row.get("role_panel_id", "")),
                    "v2_role_surface_id": str(import_row.get("v2_role_surface_id", "")),
                    "execution_row_kind": IMPORT_ROW_KIND,
                    "error_type": "MissingImportSourceEpisode",
                    "error_message": source_workload_id,
                    **_claim_boundary_flags(),
                }
            )
            continue
        imported_row = dict(source)
        imported_row.update(
            {
                **_repaired_passthrough_values(import_row),
                "workload_id": output_workload_id,
                "repaired_import_row_id": output_workload_id,
                "task_source_id": str(import_row.get("task_source_id", source.get("task_source_id", ""))),
                "support_first_v2_panel_spec_id": str(import_row.get("support_first_v2_panel_spec_id", "")),
                "support_first_materialized_v2_panel_spec_id": str(
                    import_row.get("support_first_materialized_v2_panel_spec_id", "")
                ),
                "import_source_episode_workload_id": source_workload_id,
                "source_environment_rollout_started": source.get("environment_rollout_started", ""),
                "source_measured_rollout_started": source.get("measured_rollout_started", ""),
                "source_policy_action_executed": source.get("policy_action_executed", ""),
                "support_first_repaired_bounded_smoke_execution": True,
                "support_first_measured_runner_execution": False,
                "full_rollout_execution": False,
                "imported_episode_row": True,
                "environment_rollout_started": False,
                "measured_rollout_started": False,
                "policy_action_executed": False,
                **_claim_boundary_flags(),
            }
        )
        imported_row.update(diagnostic_flags(imported_row))
        imported.append(imported_row)
    return imported, failures, alignment


def _write_repaired_aggregates(output_dir: Path, episode_rows: list[dict[str, Any]]) -> dict[str, int]:
    aggregates = {
        "profile_aggregate": aggregate_outcome_rows(episode_rows, ("profile_name",)),
        "controller_profile_aggregate": aggregate_outcome_rows(episode_rows, ("controller_profile_name",)),
        "role_panel_aggregate": aggregate_outcome_rows(episode_rows, ("role_panel_id",)),
        "role_surface_aggregate": aggregate_outcome_rows(episode_rows, ("v2_role_surface_id",)),
        "surface_variant_aggregate": aggregate_outcome_rows(episode_rows, ("surface_variant",)),
        "scenario_profile_aggregate": aggregate_outcome_rows(episode_rows, ("scenario_profile_name",)),
        "hidden_dynamics_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("hidden_dynamics_bucket",)),
        "road_boundary_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("road_boundary_bucket",)),
        "obstacle_timing_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("obstacle_timing_bucket",)),
        "obstacle_lateral_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("obstacle_lateral_bucket",)),
        "sampled_obstacle_label_aggregate": aggregate_outcome_rows(episode_rows, ("sampled_obstacle_label",)),
        "repair_variant_aggregate": aggregate_outcome_rows(episode_rows, ("repair_variant_id",)),
        "repair_variant_kind_aggregate": aggregate_outcome_rows(episode_rows, ("repair_variant_kind",)),
        "geometry_variant_aggregate": aggregate_outcome_rows(episode_rows, ("geometry_variant_id",)),
        "success_semantics_variant_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("success_semantics_variant_id",),
        ),
        "execution_row_kind_aggregate": aggregate_outcome_rows(episode_rows, ("execution_row_kind",)),
        "controller_profile_repair_variant_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("controller_profile_name", "repair_variant_id"),
        ),
        "controller_profile_role_surface_repair_variant_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("controller_profile_name", "v2_role_surface_id", "repair_variant_id"),
        ),
        "role_surface_repair_variant_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("v2_role_surface_id", "repair_variant_id"),
        ),
        "repair_variant_outcome_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("repair_variant_id", "outcome_bucket"),
        ),
        "outcome_aggregate": aggregate_outcome_rows(episode_rows, ("outcome_bucket",)),
        "termination_reason_aggregate": aggregate_outcome_rows(episode_rows, ("termination_reason",)),
        "profile_hidden_dynamics_worst_bucket": profile_hidden_dynamics_worst_rows(episode_rows),
    }
    for name, rows in aggregates.items():
        write_csv_rows(output_dir / f"{name}.csv", rows)
    return {f"{name}_rows": len(rows) for name, rows in aggregates.items()}


def finalize_repaired_bounded_smoke_outputs(
    *,
    output_dir: Path,
    source_episode_rows_path: Path | str,
    support_first_repaired_import_rows_path: Path | str,
    target_rollout_episode_count: int | None = TARGET_ROLLOUT_EPISODE_COUNT,
    target_import_episode_count: int | None = TARGET_IMPORT_EPISODE_COUNT,
    target_total_panel_row_count: int | None = TARGET_TOTAL_PANEL_ROW_COUNT,
    target_controller_profile_count: int | None = TARGET_CONTROLLER_PROFILE_COUNT,
    target_selected_source_spec_count: int | None = TARGET_SELECTED_SOURCE_SPEC_COUNT,
    target_repaired_executable_spec_count: int | None = TARGET_REPAIRED_EXECUTABLE_SPEC_COUNT,
    target_role_panel_count: int | None = TARGET_ROLE_PANEL_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    target_repair_variant_count: int | None = TARGET_REPAIR_VARIANT_COUNT,
    target_rollout_variant_count: int | None = TARGET_ROLLOUT_VARIANT_COUNT,
    target_import_variant_count: int | None = TARGET_IMPORT_VARIANT_COUNT,
    next_blocker: str = "m1894-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit",
) -> dict[str, Any]:
    rollout_rows = [dict(row) for row in read_csv_rows(output_dir / "rollout_episode_rows.csv")]
    rollout_failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    import_metadata_rows = repaired_import_metadata_rows(support_first_repaired_import_rows_path)
    imported_rows, import_failure_rows, alignment_rows = import_episode_rows_from_source(
        import_rows=import_metadata_rows,
        source_episode_rows=read_csv_rows(source_episode_rows_path),
    )
    episode_rows = sorted(
        [*rollout_rows, *imported_rows],
        key=lambda row: (
            str(row.get("base_support_first_v2_panel_spec_id", row.get("support_first_v2_panel_spec_id", ""))),
            str(row.get("controller_profile_name", "")),
            str(row.get("repair_variant_id", "")),
            str(row.get("workload_id", "")),
        ),
    )
    write_csv_rows(output_dir / "import_episode_rows.csv", imported_rows)
    write_csv_rows(output_dir / "import_failure_rows.csv", import_failure_rows, fieldnames=IMPORT_FAILURE_FIELDNAMES)
    write_csv_rows(output_dir / "import_rollout_alignment.csv", alignment_rows)
    write_csv_rows(output_dir / "episode_rows.csv", episode_rows)
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", rollout_failure_rows, fieldnames=REPAIRED_FAILURE_FIELDNAMES)

    aggregate_counts = _write_repaired_aggregates(output_dir, episode_rows)
    metric_completeness_summary, metric_completeness_failures = metric_completeness_rows(episode_rows)
    write_csv_rows(output_dir / "metric_completeness_summary.csv", metric_completeness_summary)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_completeness_failures)

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    controller_profile_count = _unique_count(episode_rows, "controller_profile_name")
    selected_source_spec_count = _unique_count(episode_rows, "base_support_first_v2_panel_spec_id")
    repaired_executable_spec_count = _unique_count(rollout_rows, "task_source_id")
    role_panel_count = _unique_count(episode_rows, "role_panel_id")
    role_surface_count = _unique_count(episode_rows, "v2_role_surface_id")
    repair_variant_count = _unique_count(episode_rows, "repair_variant_id")
    rollout_variant_count = _unique_count(rollout_rows, "repair_variant_id")
    import_variant_count = _unique_count(imported_rows, "repair_variant_id")
    profile_alias_mismatch_count = sum(
        1
        for row in episode_rows
        if str(row.get("profile_name", "")) != str(row.get("controller_profile_name", ""))
    )
    duplicate_panel_row_count = _duplicate_count(episode_rows, "workload_id")
    result_passes = (
        _target_matches(len(rollout_rows), target_rollout_episode_count)
        and _target_matches(len(imported_rows), target_import_episode_count)
        and _target_matches(len(episode_rows), target_total_panel_row_count)
        and not rollout_failure_rows
        and not import_failure_rows
        and _target_matches(controller_profile_count, target_controller_profile_count)
        and _target_matches(selected_source_spec_count, target_selected_source_spec_count)
        and _target_matches(repaired_executable_spec_count, target_repaired_executable_spec_count)
        and _target_matches(role_panel_count, target_role_panel_count)
        and _target_matches(role_surface_count, target_role_surface_count)
        and _target_matches(repair_variant_count, target_repair_variant_count)
        and _target_matches(rollout_variant_count, target_rollout_variant_count)
        and _target_matches(import_variant_count, target_import_variant_count)
        and profile_alias_mismatch_count == 0
        and duplicate_panel_row_count == 0
        and all_selected_metrics_finite
        and bool(metric_completeness_summary)
        and not metric_completeness_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "executable_v2_support_first_repaired_bounded_smoke_execution_pass"
            if result_passes
            else "executable_v2_support_first_repaired_bounded_smoke_execution_incomplete_or_fail"
        ),
        "output_dir": str(output_dir),
        "rollout_episode_count": len(rollout_rows),
        "target_rollout_episode_count": target_rollout_episode_count,
        "import_episode_count": len(imported_rows),
        "target_import_episode_count": target_import_episode_count,
        "total_panel_row_count": len(episode_rows),
        "target_total_panel_row_count": target_total_panel_row_count,
        "failure_count": len(rollout_failure_rows),
        "import_failure_count": len(import_failure_rows),
        "source_episode_join_missing_count": len(import_failure_rows),
        "controller_profile_count": controller_profile_count,
        "target_controller_profile_count": target_controller_profile_count,
        "selected_source_spec_count": selected_source_spec_count,
        "target_selected_source_spec_count": target_selected_source_spec_count,
        "repaired_executable_spec_count": repaired_executable_spec_count,
        "target_repaired_executable_spec_count": target_repaired_executable_spec_count,
        "role_panel_count": role_panel_count,
        "target_role_panel_count": target_role_panel_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "repair_variant_count": repair_variant_count,
        "target_repair_variant_count": target_repair_variant_count,
        "rollout_variant_count": rollout_variant_count,
        "target_rollout_variant_count": target_rollout_variant_count,
        "import_variant_count": import_variant_count,
        "target_import_variant_count": target_import_variant_count,
        "profile_alias_mismatch_count": profile_alias_mismatch_count,
        "duplicate_panel_row_count": duplicate_panel_row_count,
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        **aggregate_counts,
        "metric_completeness_summary_rows": len(metric_completeness_summary),
        "metric_completeness_failure_count": len(metric_completeness_failures),
        "metric_completeness_passed": bool(metric_completeness_summary and not metric_completeness_failures),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(rollout_rows or rollout_failure_rows),
        "measured_rollout_started": bool(rollout_rows or rollout_failure_rows),
        "policy_action_executed": bool(rollout_rows),
        **_claim_boundary_flags(),
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "episode_rows": str(output_dir / "episode_rows.csv"),
            "rollout_episode_rows": str(output_dir / "rollout_episode_rows.csv"),
            "import_episode_rows": str(output_dir / "import_episode_rows.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "import_failure_rows": str(output_dir / "import_failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
            **{name.removesuffix(".csv"): str(output_dir / name) for name in AGGREGATE_FILENAMES},
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_rollout_episode_count": target_rollout_episode_count,
            "completed_rollout_count": len(rollout_rows),
            "failure_count": len(rollout_failure_rows),
            "import_episode_count": len(imported_rows),
            "import_failure_count": len(import_failure_rows),
            "total_panel_row_count": len(episode_rows),
            "complete": result_passes,
        },
    )
    return summary


def _clear_outputs(output: Path) -> None:
    for filename in (
        "episode_rows.csv",
        "rollout_episode_rows.csv",
        "import_episode_rows.csv",
        "failure_rows.csv",
        "import_failure_rows.csv",
        "summary.json",
        "run_state.json",
        *AGGREGATE_FILENAMES,
    ):
        path = output / filename
        if path.exists():
            path.unlink()


def run_repaired_bounded_smoke_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    support_first_repaired_measured_specs_path: Path | str = DEFAULT_SUPPORT_FIRST_REPAIRED_MEASURED_SPECS,
    support_first_repaired_workload_path: Path | str = DEFAULT_SUPPORT_FIRST_REPAIRED_WORKLOAD,
    support_first_repaired_import_rows_path: Path | str = DEFAULT_SUPPORT_FIRST_REPAIRED_IMPORT_ROWS,
    source_episode_rows_path: Path | str = DEFAULT_SOURCE_EPISODE_ROWS,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    target_rollout_episode_count: int | None = TARGET_ROLLOUT_EPISODE_COUNT,
    target_import_episode_count: int | None = TARGET_IMPORT_EPISODE_COUNT,
    target_total_panel_row_count: int | None = TARGET_TOTAL_PANEL_ROW_COUNT,
    target_controller_profile_count: int | None = TARGET_CONTROLLER_PROFILE_COUNT,
    target_selected_source_spec_count: int | None = TARGET_SELECTED_SOURCE_SPEC_COUNT,
    target_repaired_executable_spec_count: int | None = TARGET_REPAIRED_EXECUTABLE_SPEC_COUNT,
    target_role_panel_count: int | None = TARGET_ROLE_PANEL_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    target_repair_variant_count: int | None = TARGET_REPAIR_VARIANT_COUNT,
    target_rollout_variant_count: int | None = TARGET_ROLLOUT_VARIANT_COUNT,
    target_import_variant_count: int | None = TARGET_IMPORT_VARIANT_COUNT,
    next_blocker: str = "m1894-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not resume:
        _clear_outputs(output)

    executable_specs = load_support_first_repaired_measured_specs(support_first_repaired_measured_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    workload_rows = repaired_rollout_workload_rows(support_first_repaired_workload_path)
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_cache = _load_profile_cache(profile_rows, device=device)
    completed = completed_workload_ids(output / "rollout_episode_rows.csv") if resume else set()

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=REPAIRED_FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = _run_repaired_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["task_source_id"])],
                profile_config=profile_config,
                model=model,
                profile_row=profile_by_name[profile_name],
                eval_seed=eval_seed,
            )
            append_csv_row(output / "rollout_episode_rows.csv", row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - execution must persist row-level failures.
            failure_row = {
                "workload_id": workload_id,
                "repaired_workload_id": str(workload_row.get("repaired_workload_id", workload_id)),
                "repair_row_id": str(workload_row.get("repair_row_id", "")),
                "repair_variant_id": str(workload_row.get("repair_variant_id", "")),
                "task_source_id": str(workload_row.get("task_source_id", "")),
                "base_task_source_id": str(workload_row.get("base_task_source_id", "")),
                "base_workload_id": str(workload_row.get("base_workload_id", "")),
                "controller_profile_name": str(workload_row.get("controller_profile_name", "")),
                "profile_name": profile_name,
                "role_panel_id": str(workload_row.get("role_panel_id", "")),
                "v2_role_surface_id": str(workload_row.get("v2_role_surface_id", "")),
                "execution_row_kind": str(workload_row.get("execution_row_kind", ROLLOUT_ROW_KIND)),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                **_claim_boundary_flags(),
            }
            append_csv_row(output / "failure_rows.csv", failure_row)
        write_run_state(
            output / "run_state.json",
            {
                "target_rollout_episode_count": target_rollout_episode_count,
                "completed_rollout_count": len(completed_workload_ids(output / "rollout_episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_repaired_bounded_smoke_outputs(
        output_dir=output,
        source_episode_rows_path=source_episode_rows_path,
        support_first_repaired_import_rows_path=support_first_repaired_import_rows_path,
        target_rollout_episode_count=target_rollout_episode_count,
        target_import_episode_count=target_import_episode_count,
        target_total_panel_row_count=target_total_panel_row_count,
        target_controller_profile_count=target_controller_profile_count,
        target_selected_source_spec_count=target_selected_source_spec_count,
        target_repaired_executable_spec_count=target_repaired_executable_spec_count,
        target_role_panel_count=target_role_panel_count,
        target_role_surface_count=target_role_surface_count,
        target_repair_variant_count=target_repair_variant_count,
        target_rollout_variant_count=target_rollout_variant_count,
        target_import_variant_count=target_import_variant_count,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run support-first repaired bounded-smoke rollout execution.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument(
        "--support-first-repaired-measured-specs",
        type=Path,
        default=DEFAULT_SUPPORT_FIRST_REPAIRED_MEASURED_SPECS,
    )
    parser.add_argument(
        "--support-first-repaired-workload",
        type=Path,
        default=DEFAULT_SUPPORT_FIRST_REPAIRED_WORKLOAD,
    )
    parser.add_argument(
        "--support-first-repaired-import-rows",
        type=Path,
        default=DEFAULT_SUPPORT_FIRST_REPAIRED_IMPORT_ROWS,
    )
    parser.add_argument("--source-episode-rows", type=Path, default=DEFAULT_SOURCE_EPISODE_ROWS)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default="m1894-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit")
    args = parser.parse_args()

    summary = run_repaired_bounded_smoke_execution(
        output_dir=args.output_dir,
        support_first_repaired_measured_specs_path=args.support_first_repaired_measured_specs,
        support_first_repaired_workload_path=args.support_first_repaired_workload,
        support_first_repaired_import_rows_path=args.support_first_repaired_import_rows,
        source_episode_rows_path=args.source_episode_rows,
        m1674_run_dir=args.m1674_run_dir,
        eval_seed_base=int(args.eval_seed_base),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"rollout_episode_count={summary['rollout_episode_count']}")
    print(f"import_episode_count={summary['import_episode_count']}")
    print(f"total_panel_row_count={summary['total_panel_row_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"import_failure_count={summary['import_failure_count']}")
    print(f"metric_completeness_passed={summary['metric_completeness_passed']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
