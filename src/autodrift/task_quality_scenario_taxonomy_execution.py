"""Measured execution for the task-quality scenario taxonomy."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import (
    FORBIDDEN_GUARDRAILS,
    aggregate_outcome_rows,
)
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
from autodrift.outcome_metric_instrumentation import profile_hidden_dynamics_worst_rows
from autodrift.task_quality_scenario_taxonomy_preflight import DEFAULT_OUTPUT_DIR as DEFAULT_M1728_OUTPUT_DIR


DEFAULT_SCENARIO_SPECS = DEFAULT_M1728_OUTPUT_DIR / "scenario_specs.json"
DEFAULT_SCENARIO_MATRIX = DEFAULT_M1728_OUTPUT_DIR / "scenario_matrix.csv"
DEFAULT_UNSUPPORTED_FEATURES = DEFAULT_M1728_OUTPUT_DIR / "unsupported_scenario_features.csv"
DEFAULT_RUN_DIR = Path("runs/m1731_task_quality_scenario_taxonomy_execution")
DEFAULT_EVAL_SEED_BASE = 173100
TARGET_EPISODE_COUNT = 864
TARGET_PROFILE_COUNT = 12
TARGET_SCENARIO_SPEC_COUNT = 72
TARGET_SCENARIO_FAMILY_COUNT = 6
TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT = 5
TARGET_UNSUPPORTED_FEATURE_COUNT = TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT
SEMANTICS_PAYLOAD_KEYS = (
    "scenario_specs",
    "repaired_scenario_specs",
    "semantics_scenario_specs",
)
SCENARIO_SEMANTICS_FIELDS = (
    "evaluation_role",
    "primary_metric_family",
    "ranking_eligible_after_audit",
    "diagnostic_only_no_ranking_claim",
    "benchmark_row",
    "metric_required_benchmark_success",
    "metric_required_avoidance_success",
    "metric_required_controlled_drift_recovery_success",
    "metric_required_collision_mitigation_score",
    "metric_required_impact_severity_proxy",
    "metric_required_off_track_violation",
    "metric_required_off_track_severity_proxy",
    "metric_required_recovery_success",
    "metric_required_recovery_time_proxy",
    "metric_required_hidden_dynamics_robustness",
    "metric_required_diagnostic_only_no_ranking_claim",
)
SCENARIO_BOOLEAN_SEMANTICS_FIELDS = frozenset(
    field
    for field in SCENARIO_SEMANTICS_FIELDS
    if field
    not in {
        "evaluation_role",
        "primary_metric_family",
    }
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
    "diagnostic_only_no_ranking_claim",
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
SCENARIO_FAILURE_FIELDNAMES = [
    "workload_id",
    "scenario_workload_id",
    "scenario_spec_id",
    "scenario_family_id",
    "scenario_family",
    "m1728_scenario_spec_id",
    "sampling_repair_source",
    "sampling_repair_variant_id",
    "sampling_repair_applied",
    *SCENARIO_SEMANTICS_FIELDS,
    "profile_name",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "road_boundary_bucket",
    "hidden_dynamics_bucket",
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
    "unsupported_faults_treated_as_covered",
]


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


def _first_present(*values: Any, default: Any = "") -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return default


def _is_finite_value(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return numeric == numeric and numeric not in {float("inf"), float("-inf")}


def _is_bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return value in {0, 1, 0.0, 1.0}
    if isinstance(value, str):
        return value.strip().lower() in {"true", "false", "1", "0", "yes", "no", "y", "n"}
    return False


def load_scenario_specs(path: Path | str = DEFAULT_SCENARIO_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    for key in SEMANTICS_PAYLOAD_KEYS:
        if key in payload:
            return list(payload[key])
    raise KeyError(f"{path} must contain one of {SEMANTICS_PAYLOAD_KEYS}")


def scenario_taxonomy_workload_rows(
    *,
    scenario_specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
    workload_path: Path | str = DEFAULT_SCENARIO_MATRIX,
) -> list[dict[str, Any]]:
    specs = load_scenario_specs(scenario_specs_path)
    spec_by_id = {str(spec["scenario_spec_id"]): spec for spec in specs}
    rows = read_csv_rows(workload_path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        spec = spec_by_id[str(row["scenario_spec_id"])]
        template_source_family = str(
            _first_present(
                spec.get("template_source_family"),
                row.get("template_source_family"),
                default="not_available",
            )
        )
        item = dict(row)
        item.update(
            {
                "workload_id": str(row["scenario_workload_id"]),
                "task_source_id": str(row["scenario_spec_id"]),
                "task_family": str(spec["scenario_family_id"]),
                "source_edge": str(spec["scenario_family"]),
                "window_tag": str(spec["hidden_dynamics_bucket"]),
                "executable_source_family": template_source_family,
                "env_template_family": template_source_family,
                "scenario_family_id": str(spec["scenario_family_id"]),
                "scenario_family": str(spec["scenario_family"]),
                "scenario_role": str(spec["scenario_role"]),
                "obstacle_timing_bucket": str(spec["obstacle_timing_bucket"]),
                "obstacle_lateral_bucket": str(spec["obstacle_lateral_bucket"]),
                "road_boundary_bucket": str(spec["road_boundary_bucket"]),
                "hidden_dynamics_bucket": str(spec["hidden_dynamics_bucket"]),
                "template_source_family": template_source_family,
                "allowed_labels_metadata_only": str(spec["allowed_labels_metadata_only"]),
                "labels_enter_actor_input": _as_bool(
                    _first_present(
                        spec.get("labels_enter_actor_input"),
                        row.get("labels_enter_actor_input"),
                        default=False,
                    )
                ),
                "m1728_scenario_spec_id": str(spec.get("m1728_scenario_spec_id", spec["scenario_spec_id"])),
                "sampling_repair_source": str(
                    _first_present(
                        spec.get("sampling_repair_source"),
                        row.get("sampling_repair_source"),
                        default="not_applicable",
                    )
                ),
                "sampling_repair_variant_id": str(
                    _first_present(
                        spec.get("sampling_repair_variant_id"),
                        row.get("sampling_repair_variant_id"),
                        default="not_applicable",
                    )
                ),
                "sampling_repair_applied": _as_bool(
                    _first_present(
                        spec.get("sampling_repair_applied"),
                        row.get("sampling_repair_applied"),
                        default=False,
                    )
                ),
            }
        )
        for field in SCENARIO_SEMANTICS_FIELDS:
            value = _first_present(spec.get(field), row.get(field), default="")
            item[field] = _as_bool(value) if field in SCENARIO_BOOLEAN_SEMANTICS_FIELDS else str(value)
        item["strata"] = ";".join(
            [
                "scenario_taxonomy",
                f"scenario_family_{spec['scenario_family']}",
                f"hidden_dynamics_{spec['hidden_dynamics_bucket']}",
                f"road_boundary_{spec['road_boundary_bucket']}",
                f"obstacle_timing_{spec['obstacle_timing_bucket']}",
            ]
        )
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


def _semantics_passthrough_values(workload_row: Mapping[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in SCENARIO_SEMANTICS_FIELDS:
        value = workload_row.get(field, "")
        values[field] = _as_bool(value) if field in SCENARIO_BOOLEAN_SEMANTICS_FIELDS else str(value)
    return values


def _run_scenario_workload_cell(
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
    row.update(
        {
            "scenario_workload_id": str(workload_row["scenario_workload_id"]),
            "scenario_spec_id": str(workload_row["scenario_spec_id"]),
            "scenario_family_id": str(workload_row["scenario_family_id"]),
            "scenario_family": str(workload_row["scenario_family"]),
            "scenario_role": str(workload_row["scenario_role"]),
            "obstacle_timing_bucket": str(workload_row["obstacle_timing_bucket"]),
            "obstacle_lateral_bucket": str(workload_row["obstacle_lateral_bucket"]),
            "road_boundary_bucket": str(workload_row["road_boundary_bucket"]),
            "hidden_dynamics_bucket": str(workload_row["hidden_dynamics_bucket"]),
            "template_source_family": str(workload_row["template_source_family"]),
            "allowed_labels_metadata_only": str(workload_row["allowed_labels_metadata_only"]),
            "labels_enter_actor_input": bool(workload_row["labels_enter_actor_input"]),
            "m1728_scenario_spec_id": str(workload_row["m1728_scenario_spec_id"]),
            "sampling_repair_source": str(workload_row["sampling_repair_source"]),
            "sampling_repair_variant_id": str(workload_row["sampling_repair_variant_id"]),
            "sampling_repair_applied": bool(workload_row["sampling_repair_applied"]),
            **_semantics_passthrough_values(workload_row),
            "sampled_obstacle_label": str(row.get("obstacle_label", "")),
            "scenario_taxonomy_execution": True,
            "full_rollout_execution": False,
            "controller_family_ranking_claim_made": False,
            "unsupported_faults_treated_as_covered": False,
        }
    )
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
                "scenario_workload_id": str(row.get("scenario_workload_id", "")),
                "scenario_spec_id": str(row.get("scenario_spec_id", "")),
                "profile_name": str(row.get("profile_name", "")),
                "field": field,
                "rule": rule,
                "value": row.get(field, ""),
                "reason": reason,
            }
        )

    for row in episode_rows:
        for field in SCENARIO_SEMANTICS_FIELDS:
            value = row.get(field, "")
            if field in SCENARIO_BOOLEAN_SEMANTICS_FIELDS:
                valid = _is_bool_like(value)
                reason = "expected_bool_like_semantics_field"
            else:
                valid = bool(str(value).strip())
                reason = "expected_nonempty_semantics_field"
            record(row, field=field, rule="semantics_required", applicable=True, valid=valid, reason=reason)

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


def _write_scenario_aggregates(output_dir: Path, episode_rows: list[dict[str, Any]]) -> dict[str, int]:
    aggregates = {
        "profile_aggregate": aggregate_outcome_rows(episode_rows, ("profile_name",)),
        "scenario_family_aggregate": aggregate_outcome_rows(episode_rows, ("scenario_family",)),
        "scenario_role_aggregate": aggregate_outcome_rows(episode_rows, ("scenario_role",)),
        "evaluation_role_aggregate": aggregate_outcome_rows(episode_rows, ("evaluation_role",)),
        "primary_metric_family_aggregate": aggregate_outcome_rows(episode_rows, ("primary_metric_family",)),
        "sampling_repair_variant_aggregate": aggregate_outcome_rows(episode_rows, ("sampling_repair_variant_id",)),
        "hidden_dynamics_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("hidden_dynamics_bucket",)),
        "road_boundary_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("road_boundary_bucket",)),
        "obstacle_timing_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("obstacle_timing_bucket",)),
        "obstacle_lateral_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("obstacle_lateral_bucket",)),
        "sampled_obstacle_label_aggregate": aggregate_outcome_rows(episode_rows, ("sampled_obstacle_label",)),
        "outcome_aggregate": aggregate_outcome_rows(episode_rows, ("outcome_bucket",)),
        "termination_reason_aggregate": aggregate_outcome_rows(episode_rows, ("termination_reason",)),
        "profile_outcome_aggregate": aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket")),
        "scenario_family_outcome_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("scenario_family", "outcome_bucket"),
        ),
        "evaluation_role_outcome_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("evaluation_role", "outcome_bucket"),
        ),
        "primary_metric_family_outcome_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("primary_metric_family", "outcome_bucket"),
        ),
        "scenario_family_sampled_label_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("scenario_family", "sampled_obstacle_label"),
        ),
        "profile_hidden_dynamics_worst_bucket": profile_hidden_dynamics_worst_rows(episode_rows),
    }
    for name, rows in aggregates.items():
        write_csv_rows(output_dir / f"{name}.csv", rows)
    return {f"{name}_rows": len(rows) for name, rows in aggregates.items()}


def _guardrail_flags() -> dict[str, bool]:
    flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    flags["unsupported_faults_treated_as_covered"] = False
    return flags


def load_unsupported_feature_rows(path: Path | str = DEFAULT_UNSUPPORTED_FEATURES) -> list[dict[str, str]]:
    return read_csv_rows(path)


def finalize_scenario_taxonomy_outputs(
    *,
    output_dir: Path,
    target_workload_count: int,
    unsupported_features_path: Path | str = DEFAULT_UNSUPPORTED_FEATURES,
    next_blocker: str = "m1732-paper-route-task-quality-scenario-taxonomy-result-audit",
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=SCENARIO_FAILURE_FIELDNAMES)
    unsupported_rows = load_unsupported_feature_rows(unsupported_features_path)
    write_csv_rows(output_dir / "unsupported_scenario_features.csv", unsupported_rows)
    aggregate_counts = _write_scenario_aggregates(output_dir, episode_rows)
    metric_completeness_summary, metric_completeness_failures = metric_completeness_rows(episode_rows)
    write_csv_rows(output_dir / "metric_completeness_summary.csv", metric_completeness_summary)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_completeness_failures)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    silent_unsupported_approximation_count = sum(
        str(row.get("silently_approximated", "")).strip().lower() in {"true", "1", "yes"}
        for row in unsupported_rows
    )
    profile_count = len({row["profile_name"] for row in episode_rows}) if episode_rows else 0
    scenario_spec_count = len({row["scenario_spec_id"] for row in episode_rows}) if episode_rows else 0
    scenario_family_count = len({row["scenario_family"] for row in episode_rows}) if episode_rows else 0
    result_passes = (
        len(episode_rows) == target_workload_count
        and not failure_rows
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and profile_count == TARGET_PROFILE_COUNT
        and scenario_spec_count == TARGET_SCENARIO_SPEC_COUNT
        and scenario_family_count == TARGET_SCENARIO_FAMILY_COUNT
        and aggregate_counts["scenario_family_aggregate_rows"] == TARGET_SCENARIO_FAMILY_COUNT
        and aggregate_counts["evaluation_role_aggregate_rows"] > 0
        and aggregate_counts["primary_metric_family_aggregate_rows"] > 0
        and aggregate_counts["sampling_repair_variant_aggregate_rows"] > 0
        and aggregate_counts["hidden_dynamics_bucket_aggregate_rows"] > 0
        and aggregate_counts["road_boundary_bucket_aggregate_rows"] > 0
        and aggregate_counts["obstacle_timing_bucket_aggregate_rows"] > 0
        and aggregate_counts["sampled_obstacle_label_aggregate_rows"] > 0
        and aggregate_counts["outcome_aggregate_rows"] > 0
        and aggregate_counts["termination_reason_aggregate_rows"] > 0
        and aggregate_counts["scenario_family_outcome_aggregate_rows"] > 0
        and aggregate_counts["evaluation_role_outcome_aggregate_rows"] > 0
        and aggregate_counts["primary_metric_family_outcome_aggregate_rows"] > 0
        and aggregate_counts["scenario_family_sampled_label_aggregate_rows"] > 0
        and metric_completeness_summary
        and not metric_completeness_failures
        and len(unsupported_rows) == TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT
        and silent_unsupported_approximation_count == 0
        and not guardrail_flags["unsupported_faults_treated_as_covered"]
    )
    summary = {
        "result_class": (
            "task_quality_scenario_taxonomy_execution_pass"
            if result_passes
            else "task_quality_scenario_taxonomy_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": target_workload_count,
        "profile_count": profile_count,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "scenario_spec_count": scenario_spec_count,
        "target_scenario_spec_count": TARGET_SCENARIO_SPEC_COUNT,
        "scenario_family_count": scenario_family_count,
        "target_scenario_family_count": TARGET_SCENARIO_FAMILY_COUNT,
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        **aggregate_counts,
        "metric_completeness_summary_rows": len(metric_completeness_summary),
        "metric_completeness_failure_count": len(metric_completeness_failures),
        "metric_completeness_passed": bool(metric_completeness_summary and not metric_completeness_failures),
        "unsupported_scenario_feature_count": len(unsupported_rows),
        "target_unsupported_scenario_feature_count": TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT,
        "silent_unsupported_approximation_count": silent_unsupported_approximation_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(episode_rows or failure_rows),
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
        "unsupported_faults_treated_as_covered": False,
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "episode_rows": str(output_dir / "episode_rows.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
            "profile_aggregate": str(output_dir / "profile_aggregate.csv"),
            "scenario_family_aggregate": str(output_dir / "scenario_family_aggregate.csv"),
            "scenario_role_aggregate": str(output_dir / "scenario_role_aggregate.csv"),
            "evaluation_role_aggregate": str(output_dir / "evaluation_role_aggregate.csv"),
            "primary_metric_family_aggregate": str(output_dir / "primary_metric_family_aggregate.csv"),
            "sampling_repair_variant_aggregate": str(output_dir / "sampling_repair_variant_aggregate.csv"),
            "hidden_dynamics_bucket_aggregate": str(output_dir / "hidden_dynamics_bucket_aggregate.csv"),
            "road_boundary_bucket_aggregate": str(output_dir / "road_boundary_bucket_aggregate.csv"),
            "obstacle_timing_bucket_aggregate": str(output_dir / "obstacle_timing_bucket_aggregate.csv"),
            "obstacle_lateral_bucket_aggregate": str(output_dir / "obstacle_lateral_bucket_aggregate.csv"),
            "sampled_obstacle_label_aggregate": str(output_dir / "sampled_obstacle_label_aggregate.csv"),
            "outcome_aggregate": str(output_dir / "outcome_aggregate.csv"),
            "termination_reason_aggregate": str(output_dir / "termination_reason_aggregate.csv"),
            "profile_outcome_aggregate": str(output_dir / "profile_outcome_aggregate.csv"),
            "scenario_family_outcome_aggregate": str(output_dir / "scenario_family_outcome_aggregate.csv"),
            "evaluation_role_outcome_aggregate": str(output_dir / "evaluation_role_outcome_aggregate.csv"),
            "primary_metric_family_outcome_aggregate": str(output_dir / "primary_metric_family_outcome_aggregate.csv"),
            "scenario_family_sampled_label_aggregate": str(
                output_dir / "scenario_family_sampled_label_aggregate.csv"
            ),
            "profile_hidden_dynamics_worst_bucket": str(
                output_dir / "profile_hidden_dynamics_worst_bucket.csv"
            ),
            "unsupported_scenario_features": str(output_dir / "unsupported_scenario_features.csv"),
            "metric_completeness_summary": str(output_dir / "metric_completeness_summary.csv"),
            "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_workload_count": target_workload_count,
            "completed_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "complete": len(episode_rows) == target_workload_count and not failure_rows,
        },
    )
    return summary


def run_scenario_taxonomy_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    scenario_specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
    executable_scenario_specs_path: Path | str | None = None,
    workload_path: Path | str = DEFAULT_SCENARIO_MATRIX,
    unsupported_features_path: Path | str = DEFAULT_UNSUPPORTED_FEATURES,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = "m1732-paper-route-task-quality-scenario-taxonomy-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_scenario_specs(executable_scenario_specs_path or scenario_specs_path)
    spec_by_id = {str(spec["scenario_spec_id"]): spec for spec in executable_specs}
    workload_rows = scenario_taxonomy_workload_rows(
        scenario_specs_path=scenario_specs_path,
        workload_path=workload_path,
    )
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_cache = _load_profile_cache(profile_rows, device=device)
    completed = completed_workload_ids(output / "episode_rows.csv") if resume else set()
    if not resume:
        for path in (
            output / "episode_rows.csv",
            output / "failure_rows.csv",
            output / "summary.json",
            output / "run_state.json",
            output / "profile_aggregate.csv",
            output / "scenario_family_aggregate.csv",
            output / "scenario_role_aggregate.csv",
            output / "evaluation_role_aggregate.csv",
            output / "primary_metric_family_aggregate.csv",
            output / "sampling_repair_variant_aggregate.csv",
            output / "hidden_dynamics_bucket_aggregate.csv",
            output / "road_boundary_bucket_aggregate.csv",
            output / "obstacle_timing_bucket_aggregate.csv",
            output / "obstacle_lateral_bucket_aggregate.csv",
            output / "sampled_obstacle_label_aggregate.csv",
            output / "outcome_aggregate.csv",
            output / "termination_reason_aggregate.csv",
            output / "profile_outcome_aggregate.csv",
            output / "scenario_family_outcome_aggregate.csv",
            output / "evaluation_role_outcome_aggregate.csv",
            output / "primary_metric_family_outcome_aggregate.csv",
            output / "scenario_family_sampled_label_aggregate.csv",
            output / "profile_hidden_dynamics_worst_bucket.csv",
            output / "unsupported_scenario_features.csv",
            output / "metric_completeness_summary.csv",
            output / "metric_completeness_failures.csv",
        ):
            if path.exists():
                path.unlink()
        completed = set()

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=SCENARIO_FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = _run_scenario_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["scenario_spec_id"])],
                profile_config=profile_config,
                model=model,
                profile_row=profile_by_name[profile_name],
                eval_seed=eval_seed,
            )
            append_csv_row(output / "episode_rows.csv", row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - rollout must preserve failures as rows.
            failure_row = {
                "workload_id": workload_id,
                "scenario_workload_id": str(workload_row.get("scenario_workload_id", "")),
                "scenario_spec_id": str(workload_row.get("scenario_spec_id", "")),
                "scenario_family_id": str(workload_row.get("scenario_family_id", "")),
                "scenario_family": str(workload_row.get("scenario_family", "")),
                "m1728_scenario_spec_id": str(workload_row.get("m1728_scenario_spec_id", "")),
                "sampling_repair_source": str(workload_row.get("sampling_repair_source", "")),
                "sampling_repair_variant_id": str(workload_row.get("sampling_repair_variant_id", "")),
                "sampling_repair_applied": bool(workload_row.get("sampling_repair_applied", False)),
                **_semantics_passthrough_values(workload_row),
                "profile_name": profile_name,
                "obstacle_timing_bucket": str(workload_row.get("obstacle_timing_bucket", "")),
                "obstacle_lateral_bucket": str(workload_row.get("obstacle_lateral_bucket", "")),
                "road_boundary_bucket": str(workload_row.get("road_boundary_bucket", "")),
                "hidden_dynamics_bucket": str(workload_row.get("hidden_dynamics_bucket", "")),
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
                "unsupported_faults_treated_as_covered": False,
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

    return finalize_scenario_taxonomy_outputs(
        output_dir=output,
        target_workload_count=len(workload_rows),
        unsupported_features_path=unsupported_features_path,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run measured task-quality scenario taxonomy execution.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--scenario-specs", type=Path, default=DEFAULT_SCENARIO_SPECS)
    parser.add_argument("--executable-scenario-specs", type=Path, default=None)
    parser.add_argument("--workload", type=Path, default=DEFAULT_SCENARIO_MATRIX)
    parser.add_argument("--unsupported-features", type=Path, default=DEFAULT_UNSUPPORTED_FEATURES)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default="m1732-paper-route-task-quality-scenario-taxonomy-result-audit")
    args = parser.parse_args()

    summary = run_scenario_taxonomy_execution(
        output_dir=args.output_dir,
        scenario_specs_path=args.scenario_specs,
        executable_scenario_specs_path=args.executable_scenario_specs,
        workload_path=args.workload,
        unsupported_features_path=args.unsupported_features,
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
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
