"""Measured execution runner for support-first executable-v2 workloads."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
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
from autodrift.executable_v2_support_first_measured_runner_adapter import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1875_OUTPUT_DIR,
)
from autodrift.outcome_metric_instrumentation import profile_hidden_dynamics_worst_rows


DEFAULT_SUPPORT_FIRST_MEASURED_SPECS = DEFAULT_M1875_OUTPUT_DIR / "support_first_measured_executable_specs.json"
DEFAULT_SUPPORT_FIRST_WORKLOAD = DEFAULT_M1875_OUTPUT_DIR / "support_first_measured_workload_matrix.csv"
DEFAULT_RUN_DIR = Path("runs/m1879_executable_v2_support_first_measured_runner_execution")
DEFAULT_EVAL_SEED_BASE = 187900
TARGET_EPISODE_COUNT = 2160
TARGET_CONTROLLER_PROFILE_COUNT = 12
TARGET_SUPPORT_FIRST_SPEC_COUNT = 180
TARGET_ROLE_PANEL_COUNT = 4
TARGET_ROLE_SURFACE_COUNT = 8
SUPPORT_FIRST_PASSTHROUGH_FIELDS = (
    "support_first_workload_id",
    "support_first_v2_panel_spec_id",
    "support_first_materialized_v2_panel_spec_id",
    "source_scenario_spec_id",
    "controller_profile_name",
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
)
REQUIRED_EPISODE_STRING_FIELDS = (
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
    "profile_config_path",
    "checkpoint_path",
)
ALWAYS_FINITE_METRIC_FIELDS = (
    "dt",
    "track_width",
    "max_abs_beta",
    "max_abs_yaw_rate",
    "max_off_track_overshoot",
    "off_track_severity_proxy",
    "collision_mitigation_score",
)
ALWAYS_BOOLEAN_METRIC_FIELDS = (
    "recovery_success",
    "drift_used",
    "controlled_drift_recovery_success",
    "collision",
    "obstacle_passed_raw",
)
OBSTACLE_PASS_FINITE_FIELDS = (
    "first_obstacle_pass_step",
    "first_obstacle_pass_time_s",
)
RECOVERY_SUCCESS_FINITE_FIELDS = (
    "first_recovery_step",
    "first_recovery_time_s",
    "recovery_time_proxy",
)
COLLISION_FINITE_FIELDS = (
    "impact_speed_proxy",
    "impact_beta_abs",
    "impact_yaw_rate_abs",
    "impact_severity_proxy",
)
SUPPORT_FIRST_FAILURE_FIELDNAMES = [
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
    "role_panel_id",
    "v2_role_surface_id",
    "surface_variant",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "sampled_obstacle_label",
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
    "outcome_aggregate.csv",
    "termination_reason_aggregate.csv",
    "controller_profile_role_panel_aggregate.csv",
    "controller_profile_role_surface_aggregate.csv",
    "profile_outcome_aggregate.csv",
    "role_panel_outcome_aggregate.csv",
    "role_surface_outcome_aggregate.csv",
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
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def _is_finite_value(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(numeric))


def _is_bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return value in {0, 1, 0.0, 1.0}
    if isinstance(value, str):
        return value.strip().lower() in {"true", "false", "1", "0", "yes", "no", "y", "n"}
    return False


def _target_matches(actual: int, target: int | None) -> bool:
    return target is None or int(actual) == int(target)


def load_support_first_measured_specs(
    path: Path | str = DEFAULT_SUPPORT_FIRST_MEASURED_SPECS,
) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("support_first_measured_executable_specs")
    if not isinstance(rows, list):
        raise ValueError("support-first measured runner input must contain support_first_measured_executable_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def support_first_workload_rows(path: Path | str = DEFAULT_SUPPORT_FIRST_WORKLOAD) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["workload_id"] = str(row["workload_id"])
        item["support_first_workload_id"] = str(row.get("support_first_workload_id", row["workload_id"]))
        item["controller_profile_name"] = str(row.get("controller_profile_name", row.get("profile_name", "")))
        item["profile_name"] = str(row.get("profile_name", item["controller_profile_name"]))
        item["task_source_id"] = str(row["task_source_id"])
        item["strata"] = str(row.get("strata", ""))
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


def _support_first_passthrough_values(workload_row: Mapping[str, Any]) -> dict[str, Any]:
    values = {field: str(workload_row.get(field, "")) for field in SUPPORT_FIRST_PASSTHROUGH_FIELDS}
    values["profile_name"] = str(workload_row.get("profile_name", workload_row.get("controller_profile_name", "")))
    values["controller_profile_name"] = str(workload_row.get("controller_profile_name", values["profile_name"]))
    values["sampled_obstacle_label"] = str(workload_row.get("sampled_obstacle_label", ""))
    return values


def _run_support_first_workload_cell(
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
            **_support_first_passthrough_values(workload_row),
            "sampled_obstacle_label": actual_label or planned_label,
            "allowed_labels_metadata_only": str(workload_row.get("allowed_labels_metadata_only", "")),
            "profile_config_path": str(profile_row["config_path"]),
            "checkpoint_path": str(profile_row["checkpoint_path"]),
            "eval_seed": int(eval_seed),
            "support_first_measured_runner_execution": True,
            "full_rollout_execution": False,
            "environment_rollout_started": True,
            "measured_rollout_started": True,
            "policy_action_executed": True,
            "private_holdout_used": False,
            "promoted": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    row["success"] = bool(row.get("obstacle_completed", False)) and not bool(row.get("collision", False))
    return row


def metric_completeness_rows(
    episode_rows: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    counters: dict[tuple[str, str], dict[str, int]] = {}
    failures: list[dict[str, Any]] = []

    def record(row: Mapping[str, Any], *, field: str, rule: str, applicable: bool, valid: bool, reason: str) -> None:
        key = (field, rule)
        counters.setdefault(key, {"row_count": 0, "applicable_count": 0, "valid_count": 0, "invalid_count": 0})
        counters[key]["row_count"] += 1
        if not applicable:
            return
        counters[key]["applicable_count"] += 1
        if valid:
            counters[key]["valid_count"] += 1
            return
        counters[key]["invalid_count"] += 1
        failures.append(
            {
                "workload_id": str(row.get("workload_id", "")),
                "support_first_workload_id": str(row.get("support_first_workload_id", "")),
                "task_source_id": str(row.get("task_source_id", "")),
                "controller_profile_name": str(row.get("controller_profile_name", "")),
                "field": field,
                "rule": rule,
                "value": row.get(field, ""),
                "reason": reason,
            }
        )

    for row in episode_rows:
        for field in REQUIRED_EPISODE_STRING_FIELDS:
            record(
                row,
                field=field,
                rule="support_first_required",
                applicable=True,
                valid=bool(str(row.get(field, "")).strip()),
                reason="expected_nonempty_support_first_field",
            )
        record(
            row,
            field="eval_seed",
            rule="support_first_required",
            applicable=True,
            valid=_is_finite_value(row.get("eval_seed")),
            reason="expected_finite_eval_seed",
        )
        for field in ALWAYS_FINITE_METRIC_FIELDS:
            record(
                row,
                field=field,
                rule="always_finite",
                applicable=True,
                valid=_is_finite_value(row.get(field)),
                reason="expected_finite_value",
            )
        for field in ALWAYS_BOOLEAN_METRIC_FIELDS:
            record(
                row,
                field=field,
                rule="always_boolean",
                applicable=True,
                valid=_is_bool_like(row.get(field)),
                reason="expected_bool_like_value",
            )
        obstacle_passed = _as_bool(row.get("obstacle_passed_raw"), default=False)
        for field in OBSTACLE_PASS_FINITE_FIELDS:
            record(
                row,
                field=field,
                rule="finite_when_obstacle_passed",
                applicable=obstacle_passed,
                valid=_is_finite_value(row.get(field)),
                reason="expected_finite_value_when_obstacle_passed",
            )
        recovery_success = _as_bool(row.get("recovery_success"), default=False)
        for field in RECOVERY_SUCCESS_FINITE_FIELDS:
            record(
                row,
                field=field,
                rule="finite_when_recovered",
                applicable=recovery_success,
                valid=_is_finite_value(row.get(field)),
                reason="expected_finite_value_when_recovered",
            )
        collision = _as_bool(row.get("collision"), default=False)
        for field in COLLISION_FINITE_FIELDS:
            record(
                row,
                field=field,
                rule="finite_when_collision",
                applicable=collision,
                valid=_is_finite_value(row.get(field)),
                reason="expected_finite_value_when_collision",
            )

    summary_rows: list[dict[str, Any]] = []
    for field, rule in sorted(counters):
        counts = counters[(field, rule)]
        summary_rows.append(
            {
                "field": field,
                "rule": rule,
                **counts,
                "completeness_rate": (
                    counts["valid_count"] / counts["applicable_count"]
                    if counts["applicable_count"]
                    else 1.0
                ),
            }
        )
    return summary_rows, failures


def _write_aggregates(output_dir: Path, episode_rows: list[dict[str, Any]]) -> dict[str, int]:
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
        "outcome_aggregate": aggregate_outcome_rows(episode_rows, ("outcome_bucket",)),
        "termination_reason_aggregate": aggregate_outcome_rows(episode_rows, ("termination_reason",)),
        "controller_profile_role_panel_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("controller_profile_name", "role_panel_id"),
        ),
        "controller_profile_role_surface_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("controller_profile_name", "v2_role_surface_id"),
        ),
        "profile_outcome_aggregate": aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket")),
        "role_panel_outcome_aggregate": aggregate_outcome_rows(episode_rows, ("role_panel_id", "outcome_bucket")),
        "role_surface_outcome_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("v2_role_surface_id", "outcome_bucket"),
        ),
        "profile_hidden_dynamics_worst_bucket": profile_hidden_dynamics_worst_rows(episode_rows),
    }
    for name, rows in aggregates.items():
        write_csv_rows(output_dir / f"{name}.csv", rows)
    return {f"{name}_rows": len(rows) for name, rows in aggregates.items()}


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _unique_count(rows: Iterable[Mapping[str, Any]], field: str) -> int:
    return len({str(row.get(field, "")) for row in rows if str(row.get(field, "")).strip()})


def finalize_support_first_measured_outputs(
    *,
    output_dir: Path,
    target_workload_count: int,
    target_controller_profile_count: int | None = TARGET_CONTROLLER_PROFILE_COUNT,
    target_support_first_spec_count: int | None = TARGET_SUPPORT_FIRST_SPEC_COUNT,
    target_role_panel_count: int | None = TARGET_ROLE_PANEL_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    next_blocker: str = "m1880-executable-v2-support-first-measured-runner-result-audit",
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=SUPPORT_FIRST_FAILURE_FIELDNAMES)
    aggregate_counts = _write_aggregates(output_dir, episode_rows)
    metric_completeness_summary, metric_completeness_failures = metric_completeness_rows(episode_rows)
    write_csv_rows(output_dir / "metric_completeness_summary.csv", metric_completeness_summary)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_completeness_failures)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    profile_count = _unique_count(episode_rows, "profile_name")
    controller_profile_count = _unique_count(episode_rows, "controller_profile_name")
    support_first_spec_count = _unique_count(episode_rows, "support_first_v2_panel_spec_id")
    role_panel_count = _unique_count(episode_rows, "role_panel_id")
    role_surface_count = _unique_count(episode_rows, "v2_role_surface_id")
    profile_alias_mismatch_count = sum(
        1
        for row in episode_rows
        if str(row.get("profile_name", "")) != str(row.get("controller_profile_name", ""))
    )
    result_passes = (
        len(episode_rows) == int(target_workload_count)
        and not failure_rows
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and _target_matches(controller_profile_count, target_controller_profile_count)
        and _target_matches(support_first_spec_count, target_support_first_spec_count)
        and _target_matches(role_panel_count, target_role_panel_count)
        and _target_matches(role_surface_count, target_role_surface_count)
        and profile_alias_mismatch_count == 0
        and aggregate_counts["profile_aggregate_rows"] == profile_count
        and aggregate_counts["controller_profile_aggregate_rows"] == controller_profile_count
        and aggregate_counts["role_panel_aggregate_rows"] == role_panel_count
        and aggregate_counts["role_surface_aggregate_rows"] == role_surface_count
        and aggregate_counts["outcome_aggregate_rows"] > 0
        and aggregate_counts["termination_reason_aggregate_rows"] > 0
        and bool(metric_completeness_summary)
        and not metric_completeness_failures
    )
    summary = {
        "result_class": (
            "executable_v2_support_first_measured_runner_execution_pass"
            if result_passes
            else "executable_v2_support_first_measured_runner_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_workload_count),
        "profile_count": profile_count,
        "controller_profile_count": controller_profile_count,
        "target_controller_profile_count": target_controller_profile_count,
        "support_first_spec_count": support_first_spec_count,
        "target_support_first_spec_count": target_support_first_spec_count,
        "role_panel_count": role_panel_count,
        "target_role_panel_count": target_role_panel_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "profile_alias_mismatch_count": profile_alias_mismatch_count,
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        **aggregate_counts,
        "metric_completeness_summary_rows": len(metric_completeness_summary),
        "metric_completeness_failure_count": len(metric_completeness_failures),
        "metric_completeness_passed": bool(metric_completeness_summary and not metric_completeness_failures),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(episode_rows or failure_rows),
        "measured_rollout_started": bool(episode_rows or failure_rows),
        "policy_action_executed": bool(episode_rows),
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
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "episode_rows": str(output_dir / "episode_rows.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
            **{name.removesuffix(".csv"): str(output_dir / name) for name in AGGREGATE_FILENAMES},
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_workload_count": int(target_workload_count),
            "completed_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "complete": len(episode_rows) == int(target_workload_count) and not failure_rows,
        },
    )
    return summary


def _clear_outputs(output: Path) -> None:
    for filename in (
        "episode_rows.csv",
        "failure_rows.csv",
        "summary.json",
        "run_state.json",
        *AGGREGATE_FILENAMES,
    ):
        path = output / filename
        if path.exists():
            path.unlink()


def run_support_first_measured_runner_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    support_first_measured_specs_path: Path | str = DEFAULT_SUPPORT_FIRST_MEASURED_SPECS,
    support_first_workload_path: Path | str = DEFAULT_SUPPORT_FIRST_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    target_controller_profile_count: int | None = TARGET_CONTROLLER_PROFILE_COUNT,
    target_support_first_spec_count: int | None = TARGET_SUPPORT_FIRST_SPEC_COUNT,
    target_role_panel_count: int | None = TARGET_ROLE_PANEL_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    next_blocker: str = "m1880-executable-v2-support-first-measured-runner-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_support_first_measured_specs(support_first_measured_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    workload_rows = support_first_workload_rows(support_first_workload_path)
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_cache = _load_profile_cache(profile_rows, device=device)
    completed = completed_workload_ids(output / "episode_rows.csv") if resume else set()
    if not resume:
        _clear_outputs(output)
        completed = set()

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=SUPPORT_FIRST_FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = _run_support_first_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["task_source_id"])],
                profile_config=profile_config,
                model=model,
                profile_row=profile_by_name[profile_name],
                eval_seed=eval_seed,
            )
            append_csv_row(output / "episode_rows.csv", row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - execution must persist row-level failures.
            failure_row = {
                "workload_id": workload_id,
                "support_first_workload_id": str(workload_row.get("support_first_workload_id", "")),
                "task_source_id": str(workload_row.get("task_source_id", "")),
                "support_first_v2_panel_spec_id": str(workload_row.get("support_first_v2_panel_spec_id", "")),
                "support_first_materialized_v2_panel_spec_id": str(
                    workload_row.get("support_first_materialized_v2_panel_spec_id", "")
                ),
                "source_scenario_spec_id": str(workload_row.get("source_scenario_spec_id", "")),
                "controller_profile_name": str(workload_row.get("controller_profile_name", "")),
                "profile_name": profile_name,
                "scenario_profile_name": str(workload_row.get("scenario_profile_name", "")),
                "scenario_profile_group": str(workload_row.get("scenario_profile_group", "")),
                "role_panel_id": str(workload_row.get("role_panel_id", "")),
                "v2_role_surface_id": str(workload_row.get("v2_role_surface_id", "")),
                "surface_variant": str(workload_row.get("surface_variant", "")),
                "hidden_dynamics_bucket": str(workload_row.get("hidden_dynamics_bucket", "")),
                "road_boundary_bucket": str(workload_row.get("road_boundary_bucket", "")),
                "obstacle_timing_bucket": str(workload_row.get("obstacle_timing_bucket", "")),
                "obstacle_lateral_bucket": str(workload_row.get("obstacle_lateral_bucket", "")),
                "sampled_obstacle_label": str(workload_row.get("sampled_obstacle_label", "")),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
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
            append_csv_row(output / "failure_rows.csv", failure_row)
        write_run_state(
            output / "run_state.json",
            {
                "target_workload_count": len(workload_rows),
                "completed_count": len(completed_workload_ids(output / "episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_support_first_measured_outputs(
        output_dir=output,
        target_workload_count=len(workload_rows),
        target_controller_profile_count=target_controller_profile_count,
        target_support_first_spec_count=target_support_first_spec_count,
        target_role_panel_count=target_role_panel_count,
        target_role_surface_count=target_role_surface_count,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run support-first measured controller rollout execution.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--support-first-measured-specs", type=Path, default=DEFAULT_SUPPORT_FIRST_MEASURED_SPECS)
    parser.add_argument("--support-first-workload", type=Path, default=DEFAULT_SUPPORT_FIRST_WORKLOAD)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default="m1880-executable-v2-support-first-measured-runner-result-audit")
    args = parser.parse_args()

    summary = run_support_first_measured_runner_execution(
        output_dir=args.output_dir,
        support_first_measured_specs_path=args.support_first_measured_specs,
        support_first_workload_path=args.support_first_workload,
        m1674_run_dir=args.m1674_run_dir,
        eval_seed_base=int(args.eval_seed_base),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"controller_profile_count={summary['controller_profile_count']}")
    print(f"support_first_spec_count={summary['support_first_spec_count']}")
    print(f"role_surface_count={summary['role_surface_count']}")
    print(f"metric_completeness_passed={summary['metric_completeness_passed']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
