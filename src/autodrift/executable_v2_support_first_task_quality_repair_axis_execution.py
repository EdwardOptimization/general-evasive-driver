"""Execution wrapper utilities for support-first task-quality repair-axis panels.

This module implements the infrastructure needed before a later milestone runs
the real M1902 workload. It does not execute the real panel by itself in M1905;
the focused tests exercise splitting, import/postprocess joins, and metadata
preservation on synthetic rows.
"""

from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_support_first_clearance_containment_conflict_localization import (
    classify_primary_conflict,
    near_miss_flags,
)


DEFAULT_TASK_QUALITY_REPAIR_AXIS_MATRIX = Path(
    "runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/"
    "task_quality_repair_axis_matrix.csv"
)
DEFAULT_SOURCE_EPISODE_ROWS = Path("runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1905_executable_v2_support_first_task_quality_repair_axis_execution_preflight")
DEFAULT_BASE_MEASURED_SPECS = Path(
    "runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/"
    "support_first_measured_executable_specs.json"
)
DEFAULT_NEXT_BLOCKER = "m1907-executable-v2-support-first-task-quality-repair-axis-wrapper-preflight-result-audit"
DEFAULT_MEASURED_NEXT_BLOCKER = (
    "m1910-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-command-design"
)

ROLLOUT_ROW_KIND = "rollout_geometry_variant"
IMPORT_ROW_KIND = "import_existing_episode"
POSTPROCESS_ROW_KIND = "postprocess_existing_episode"
IMPORT_POSTPROCESS_ROW_KINDS = (IMPORT_ROW_KIND, POSTPROCESS_ROW_KIND)
RolloutFunction = Callable[[Mapping[str, Any], int], Mapping[str, Any]]

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

REQUIRED_AXIS_METADATA_FIELDS = (
    "task_quality_repair_axis_row_id",
    "task_quality_axis_id",
    "repair_axis_variant_id",
    "axis_applicability",
    "target_conflict_class",
    "target_near_miss_class",
    "target_role_surface_id",
    "source_conflict_class",
    "source_episode_workload_id",
    "base_task_source_id",
    "base_support_first_workload_id",
    "axis_task_source_id",
    "axis_workload_id",
    "support_first_workload_id",
    "task_source_id",
    "support_first_v2_panel_spec_id",
    "source_scenario_spec_id",
    "controller_profile_name",
    "profile_name",
    "scenario_profile_name",
    "role_panel_id",
    "v2_role_surface_id",
    "surface_variant",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "sampled_obstacle_label",
    "geometry_delta_json",
    "semantics_delta_json",
    "execution_row_kind",
)

AXIS_METADATA_FIELDS_TO_OVERLAY = REQUIRED_AXIS_METADATA_FIELDS + (
    "source_near_miss_flags",
    "source_clearance_margin",
    "source_max_off_track_overshoot",
    "source_impact_severity_proxy",
    "diagnostic_only_no_ranking_claim",
)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _json_object(text: Any) -> dict[str, Any]:
    if isinstance(text, dict):
        return dict(text)
    if text in (None, ""):
        return {}
    value = json.loads(str(text))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unique_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows if str(row.get(key, "")).strip()})


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


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


def load_base_measured_specs(path: Path | str = DEFAULT_BASE_MEASURED_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("support_first_measured_executable_specs")
    if not isinstance(rows, list):
        raise ValueError("base measured specs must contain support_first_measured_executable_specs")
    return [dict(row) for row in rows]


def apply_axis_geometry_delta_to_env_config(
    env_config: Mapping[str, Any],
    geometry_delta: Mapping[str, Any],
) -> dict[str, Any]:
    data = copy.deepcopy(dict(env_config))
    max_steps_multiplier = _float_or_none(geometry_delta.get("max_steps_multiplier"))
    if max_steps_multiplier is not None:
        base_steps = int(data.get("max_steps", 800))
        data["max_steps"] = max(1, int(round(base_steps * max_steps_multiplier)))

    width_multipliers = [
        _float_or_none(geometry_delta.get("track_width_multiplier")),
        _float_or_none(geometry_delta.get("post_obstacle_track_width_multiplier")),
        _float_or_none(geometry_delta.get("pre_obstacle_track_width_multiplier")),
    ]
    width_multipliers = [value for value in width_multipliers if value is not None]
    if width_multipliers:
        base_width = float(data.get("track_width", 5.0))
        data["track_width"] = base_width * max(width_multipliers)

    obstacle = copy.deepcopy(dict(data.get("obstacle") or {}))
    if not _bool(geometry_delta.get("road_geometry_fixed"), default=False):
        clearance_delta = _float_or_none(geometry_delta.get("obstacle_clearance_gap_delta_m"))
        if clearance_delta is not None:
            obstacle["safety_margin"] = max(0.0, float(obstacle.get("safety_margin", 0.0)) + clearance_delta)
        reaction_delta = _float_or_none(geometry_delta.get("obstacle_reaction_distance_delta_m"))
        distance_range = obstacle.get("distance_range")
        if reaction_delta is not None and isinstance(distance_range, list) and len(distance_range) == 2:
            obstacle["distance_range"] = [
                float(distance_range[0]) + reaction_delta,
                float(distance_range[1]) + reaction_delta,
            ]
        if obstacle:
            data["obstacle"] = obstacle
    return data


def split_axis_matrix_rows(rows: list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rollout_rows: list[dict[str, Any]] = []
    import_postprocess_rows: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        kind = str(item.get("execution_row_kind", ""))
        if kind == ROLLOUT_ROW_KIND:
            rollout_rows.append(item)
        elif kind in IMPORT_POSTPROCESS_ROW_KINDS:
            import_postprocess_rows.append(item)
    return rollout_rows, import_postprocess_rows


def validation_failures(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    valid_kinds = {ROLLOUT_ROW_KIND, IMPORT_ROW_KIND, POSTPROCESS_ROW_KIND}
    for index, row in enumerate(rows):
        row_id = str(row.get("task_quality_repair_axis_row_id", index))
        kind = str(row.get("execution_row_kind", ""))
        if kind not in valid_kinds:
            failures.append(
                {
                    "task_quality_repair_axis_row_id": row_id,
                    "error_type": "unknown_execution_row_kind",
                    "error_message": kind,
                }
            )
        for field in REQUIRED_AXIS_METADATA_FIELDS:
            if not str(row.get(field, "")).strip():
                failures.append(
                    {
                        "task_quality_repair_axis_row_id": row_id,
                        "error_type": "missing_required_axis_metadata",
                        "error_message": field,
                    }
                )
        for key in FORBIDDEN_GUARDRAILS:
            if _bool(row.get(key), default=False):
                failures.append(
                    {
                        "task_quality_repair_axis_row_id": row_id,
                        "error_type": "guardrail_violation",
                        "error_message": key,
                    }
                )
    return failures


def planned_rollout_rows(
    rollout_matrix_rows: list[Mapping[str, Any]],
    *,
    eval_seed_base: int = 190500,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    planned_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(rollout_matrix_rows):
        row_id = str(row.get("task_quality_repair_axis_row_id", index))
        try:
            geometry_delta = _json_object(row.get("geometry_delta_json"))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            failures.append(
                {
                    "task_quality_repair_axis_row_id": row_id,
                    "error_type": "invalid_geometry_delta_json",
                    "error_message": str(exc),
                }
            )
            continue
        planned = dict(row)
        planned.update(
            {
                "workload_id": str(row.get("axis_workload_id", row_id)),
                "task_source_id": str(row.get("axis_task_source_id", row.get("task_source_id", ""))),
                "row_provenance": "planned_rollout_geometry_variant",
                "eval_seed": eval_seed_base + index,
                "geometry_delta_applied_json": json.dumps(geometry_delta, sort_keys=True, separators=(",", ":")),
                "environment_rollout_started": False,
                "measured_rollout_started": False,
                "policy_action_executed": False,
                **_claim_boundary_flags(),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        planned_rows.append(planned)
    return planned_rows, failures


def import_postprocess_episode_rows(
    import_postprocess_matrix_rows: list[Mapping[str, Any]],
    source_episode_rows: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_by_workload = {str(row.get("workload_id", "")): dict(row) for row in source_episode_rows}
    imported_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in import_postprocess_matrix_rows:
        row_id = str(row.get("task_quality_repair_axis_row_id", ""))
        source_workload_id = str(row.get("source_episode_workload_id", ""))
        source = source_by_workload.get(source_workload_id)
        if source is None:
            failures.append(
                {
                    "task_quality_repair_axis_row_id": row_id,
                    "source_episode_workload_id": source_workload_id,
                    "error_type": "missing_source_episode_row",
                    "error_message": "source_episode_workload_id not found in source episode rows",
                }
            )
            continue
        output = dict(source)
        for field in AXIS_METADATA_FIELDS_TO_OVERLAY:
            output[field] = row.get(field, "")
        output.update(
            {
                "workload_id": str(row.get("axis_workload_id", row_id)),
                "task_source_id": str(row.get("axis_task_source_id", row.get("task_source_id", ""))),
                "row_provenance": str(row.get("execution_row_kind", "")),
                "import_source_episode_workload_id": source_workload_id,
                "environment_rollout_started": False,
                "measured_rollout_started": False,
                "policy_action_executed": False,
                **_claim_boundary_flags(),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        output["postprocess_primary_conflict_class"] = classify_primary_conflict(output)
        flags = near_miss_flags(output)
        for key, value in flags.items():
            output[key] = value
        output["any_near_miss"] = any(flags.values())
        imported_rows.append(output)
    return imported_rows, failures


def measured_rollout_episode_rows(
    rollout_matrix_rows: list[Mapping[str, Any]],
    *,
    rollout_fn: RolloutFunction,
    eval_seed_base: int = 190900,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    planned_rows, planning_failures = planned_rollout_rows(rollout_matrix_rows, eval_seed_base=eval_seed_base)
    measured_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = list(planning_failures)
    for planned in planned_rows:
        row_id = str(planned.get("task_quality_repair_axis_row_id", ""))
        eval_seed = int(planned["eval_seed"])
        try:
            measured = dict(rollout_fn(planned, eval_seed))
        except Exception as exc:  # noqa: BLE001 - wrapper must persist row-level failures.
            failure = {field: planned.get(field, "") for field in REQUIRED_AXIS_METADATA_FIELDS}
            failure.update(
                {
                    "workload_id": str(planned.get("workload_id", row_id)),
                    "task_source_id": str(planned.get("task_source_id", "")),
                    "eval_seed": eval_seed,
                    "row_provenance": "measured_rollout_geometry_variant",
                    "environment_rollout_started": True,
                    "measured_rollout_started": True,
                    "policy_action_executed": False,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    **_claim_boundary_flags(),
                    "diagnostic_only_no_ranking_claim": True,
                }
            )
            failures.append(failure)
            continue

        output = dict(measured)
        for field in AXIS_METADATA_FIELDS_TO_OVERLAY:
            output[field] = planned.get(field, "")
        output.update(
            {
                "workload_id": str(planned.get("workload_id", row_id)),
                "task_source_id": str(planned.get("task_source_id", "")),
                "row_provenance": "measured_rollout_geometry_variant",
                "eval_seed": eval_seed,
                "environment_rollout_started": True,
                "measured_rollout_started": True,
                "policy_action_executed": True,
                **_claim_boundary_flags(),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        output["postprocess_primary_conflict_class"] = classify_primary_conflict(output)
        flags = near_miss_flags(output)
        for key, value in flags.items():
            output[key] = value
        output["any_near_miss"] = any(flags.values())
        measured_rows.append(output)
    return measured_rows, failures


def aggregate_count_rows(rows: list[Mapping[str, Any]], group_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = {}
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in group_keys)
        groups.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        aggregate = {group_keys[index]: key[index] for index in range(len(group_keys))}
        aggregate.update(
            {
                "row_count": len(group),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        output.append(aggregate)
    return output


def dry_run_prepare_execution(
    *,
    matrix_rows: list[Mapping[str, Any]],
    source_episode_rows: list[Mapping[str, Any]],
    eval_seed_base: int = 190500,
) -> dict[str, Any]:
    rows = [dict(row) for row in matrix_rows]
    rollout_rows, import_rows = split_axis_matrix_rows(rows)
    validation_rows = validation_failures(rows)
    planned_rows, rollout_failures = planned_rollout_rows(rollout_rows, eval_seed_base=eval_seed_base)
    imported_rows, import_failures = import_postprocess_episode_rows(import_rows, source_episode_rows)
    combined_rows = planned_rows + imported_rows
    failures = validation_rows + rollout_failures + import_failures
    summary = {
        "result_class": "task_quality_repair_axis_execution_wrapper_preflight_pass"
        if not failures
        else "task_quality_repair_axis_execution_wrapper_preflight_needs_repair",
        "generated_at_utc": utc_timestamp(),
        "matrix_row_count": len(rows),
        "planned_rollout_row_count": len(planned_rows),
        "import_postprocess_row_count": len(imported_rows),
        "combined_panel_row_count": len(combined_rows),
        "failure_count": len(failures),
        "controller_profile_count": _unique_count(rows, "controller_profile_name"),
        "source_spec_count": _unique_count(rows, "support_first_v2_panel_spec_id"),
        "role_surface_count": _unique_count(rows, "v2_role_surface_id"),
        "repair_axis_variant_count": _unique_count(rows, "repair_axis_variant_id"),
        "execution_row_kind_counts": _count_by(rows, "execution_row_kind"),
        "task_quality_axis_counts": _count_by(rows, "task_quality_axis_id"),
        "repair_axis_variant_counts": _count_by(rows, "repair_axis_variant_id"),
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
        "guardrail_flags": _claim_boundary_flags(),
        "guardrail_violation_count": 0,
        "ranking_blocked": True,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
    }
    return {
        "summary": summary,
        "planned_rollout_rows": planned_rows,
        "import_postprocess_rows": imported_rows,
        "combined_rows": combined_rows,
        "failure_rows": failures,
        "task_quality_axis_aggregate": aggregate_count_rows(combined_rows, ("task_quality_axis_id",)),
        "repair_axis_variant_aggregate": aggregate_count_rows(combined_rows, ("repair_axis_variant_id",)),
        "execution_row_kind_aggregate": aggregate_count_rows(combined_rows, ("execution_row_kind",)),
    }


def measured_prepare_execution(
    *,
    matrix_rows: list[Mapping[str, Any]],
    source_episode_rows: list[Mapping[str, Any]],
    rollout_fn: RolloutFunction,
    eval_seed_base: int = 190900,
    result_class_stem: str = "task_quality_repair_axis_measured_wrapper_mock",
) -> dict[str, Any]:
    rows = [dict(row) for row in matrix_rows]
    rollout_rows, import_rows = split_axis_matrix_rows(rows)
    validation_rows = validation_failures(rows)
    measured_rows, rollout_failures = measured_rollout_episode_rows(
        rollout_rows,
        rollout_fn=rollout_fn,
        eval_seed_base=eval_seed_base,
    )
    imported_rows, import_failures = import_postprocess_episode_rows(import_rows, source_episode_rows)
    combined_rows = measured_rows + imported_rows
    failures = validation_rows + rollout_failures + import_failures
    summary = {
        "result_class": f"{result_class_stem}_pass" if not failures else f"{result_class_stem}_needs_repair",
        "generated_at_utc": utc_timestamp(),
        "matrix_row_count": len(rows),
        "planned_rollout_row_count": len(rollout_rows),
        "measured_rollout_row_count": len(measured_rows),
        "import_postprocess_row_count": len(imported_rows),
        "combined_panel_row_count": len(combined_rows),
        "failure_count": len(failures),
        "controller_profile_count": _unique_count(rows, "controller_profile_name"),
        "source_spec_count": _unique_count(rows, "support_first_v2_panel_spec_id"),
        "role_surface_count": _unique_count(rows, "v2_role_surface_id"),
        "repair_axis_variant_count": _unique_count(rows, "repair_axis_variant_id"),
        "execution_row_kind_counts": _count_by(rows, "execution_row_kind"),
        "task_quality_axis_counts": _count_by(rows, "task_quality_axis_id"),
        "repair_axis_variant_counts": _count_by(rows, "repair_axis_variant_id"),
        "environment_reset_started": False,
        "environment_rollout_started": bool(rollout_rows),
        "measured_rollout_started": bool(rollout_rows),
        "policy_action_executed": bool(measured_rows),
        **_claim_boundary_flags(),
        "guardrail_flags": _claim_boundary_flags(),
        "guardrail_violation_count": 0,
        "ranking_blocked": True,
        "real_m1902_workload_executed": False,
        "next_blocker": DEFAULT_MEASURED_NEXT_BLOCKER,
    }
    return {
        "summary": summary,
        "rollout_episode_rows": measured_rows,
        "import_postprocess_rows": imported_rows,
        "combined_rows": combined_rows,
        "failure_rows": failures,
        "task_quality_axis_aggregate": aggregate_count_rows(combined_rows, ("task_quality_axis_id",)),
        "repair_axis_variant_aggregate": aggregate_count_rows(combined_rows, ("repair_axis_variant_id",)),
        "execution_row_kind_aggregate": aggregate_count_rows(combined_rows, ("execution_row_kind",)),
    }


def default_measured_rollout_fn(planned_row: Mapping[str, Any], eval_seed: int) -> Mapping[str, Any]:
    rollout_fn = build_measured_rollout_fn()
    return rollout_fn(planned_row, eval_seed)


def build_measured_rollout_fn(
    *,
    base_measured_specs_path: Path | str = DEFAULT_BASE_MEASURED_SPECS,
    device: str = "cpu",
) -> RolloutFunction:
    base_specs = load_base_measured_specs(base_measured_specs_path)
    base_by_task_source_id = {str(spec["task_source_id"]): dict(spec) for spec in base_specs}
    profile_cache: dict[str, tuple[dict[str, Any], Any, dict[str, str]]] = {}

    def rollout(planned_row: Mapping[str, Any], eval_seed: int) -> Mapping[str, Any]:
        base_task_source_id = str(planned_row.get("base_task_source_id") or planned_row.get("support_first_v2_panel_spec_id"))
        base_spec = base_by_task_source_id.get(base_task_source_id)
        if base_spec is None:
            raise KeyError(f"base measured executable spec not found: {base_task_source_id}")
        geometry_delta = _json_object(planned_row.get("geometry_delta_json"))
        executable_spec = copy.deepcopy(base_spec)
        executable_spec["task_source_id"] = str(planned_row.get("task_source_id", ""))
        executable_spec["support_first_v2_panel_spec_id"] = str(planned_row.get("support_first_v2_panel_spec_id", ""))
        executable_spec["support_first_materialized_v2_panel_spec_id"] = str(
            planned_row.get("support_first_materialized_v2_panel_spec_id", "")
        )
        executable_spec["source_scenario_spec_id"] = str(planned_row.get("source_scenario_spec_id", ""))
        executable_spec["env_config"] = apply_axis_geometry_delta_to_env_config(
            executable_spec["env_config"],
            geometry_delta,
        )

        profile_name = str(planned_row.get("profile_name", planned_row.get("controller_profile_name", "")))
        if profile_name not in profile_cache:
            from autodrift.checkpoints import load_actor_critic_checkpoint

            config_path = str(planned_row.get("profile_config_path", ""))
            checkpoint_path = str(planned_row.get("checkpoint_path", ""))
            profile_config = read_json(config_path)
            model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
            profile_cache[profile_name] = (
                profile_config,
                model,
                {
                    "profile_name": profile_name,
                    "config_path": config_path,
                    "checkpoint_path": checkpoint_path,
                },
            )
        profile_config, model, profile_row = profile_cache[profile_name]

        from autodrift.controller_family_full_rollout_execution import run_workload_cell

        return run_workload_cell(
            workload_row=planned_row,
            executable_spec=executable_spec,
            profile_config=profile_config,
            model=model,
            profile_row=profile_row,
            eval_seed=eval_seed,
        )

    return rollout


def write_dry_run_artifacts(result: Mapping[str, Any], output_dir: Path | str) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", result["summary"])
    write_csv_rows(output / "planned_rollout_rows.csv", list(result["planned_rollout_rows"]))
    write_csv_rows(output / "import_postprocess_episode_rows.csv", list(result["import_postprocess_rows"]))
    write_csv_rows(output / "episode_rows.csv", list(result["combined_rows"]))
    write_csv_rows(output / "failure_rows.csv", list(result["failure_rows"]))
    write_csv_rows(output / "task_quality_axis_aggregate.csv", list(result["task_quality_axis_aggregate"]))
    write_csv_rows(output / "repair_axis_variant_aggregate.csv", list(result["repair_axis_variant_aggregate"]))
    write_csv_rows(output / "execution_row_kind_aggregate.csv", list(result["execution_row_kind_aggregate"]))


def write_measured_artifacts(result: Mapping[str, Any], output_dir: Path | str) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", result["summary"])
    write_csv_rows(output / "rollout_episode_rows.csv", list(result["rollout_episode_rows"]))
    write_csv_rows(output / "import_postprocess_episode_rows.csv", list(result["import_postprocess_rows"]))
    write_csv_rows(output / "episode_rows.csv", list(result["combined_rows"]))
    write_csv_rows(output / "failure_rows.csv", list(result["failure_rows"]))
    write_csv_rows(output / "task_quality_axis_aggregate.csv", list(result["task_quality_axis_aggregate"]))
    write_csv_rows(output / "repair_axis_variant_aggregate.csv", list(result["repair_axis_variant_aggregate"]))
    write_csv_rows(output / "execution_row_kind_aggregate.csv", list(result["execution_row_kind_aggregate"]))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-quality-repair-axis-matrix", type=Path, default=DEFAULT_TASK_QUALITY_REPAIR_AXIS_MATRIX)
    parser.add_argument("--source-episode-rows", type=Path, default=DEFAULT_SOURCE_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=190500)
    parser.add_argument("--base-measured-specs", type=Path, default=DEFAULT_BASE_MEASURED_SPECS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dry-run-only", action="store_true")
    parser.add_argument("--measured-execution", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    matrix_rows = read_csv_rows(args.task_quality_repair_axis_matrix)
    source_rows = read_csv_rows(args.source_episode_rows)
    if args.measured_execution:
        rollout_fn = build_measured_rollout_fn(base_measured_specs_path=args.base_measured_specs, device=str(args.device))
        result = measured_prepare_execution(
            matrix_rows=matrix_rows,
            source_episode_rows=source_rows,
            rollout_fn=rollout_fn,
            eval_seed_base=args.eval_seed_base,
            result_class_stem="task_quality_repair_axis_measured_wrapper_execution",
        )
        write_measured_artifacts(result, args.output_dir)
    else:
        result = dry_run_prepare_execution(
            matrix_rows=matrix_rows,
            source_episode_rows=source_rows,
            eval_seed_base=args.eval_seed_base,
        )
        write_dry_run_artifacts(result, args.output_dir)
    print(json.dumps(result["summary"], sort_keys=True))
    return 0 if str(result["summary"]["result_class"]).endswith("_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
