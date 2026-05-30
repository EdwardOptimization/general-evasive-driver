"""Measured execution adapter for the metric-specific bounded panel."""

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
from autodrift.metric_specific_bounded_panel_materialization_preflight import DEFAULT_OUTPUT_DIR as DEFAULT_M1771_OUTPUT_DIR
from autodrift.outcome_metric_instrumentation import profile_hidden_dynamics_worst_rows


DEFAULT_BOUNDED_PANEL_SPECS = DEFAULT_M1771_OUTPUT_DIR / "bounded_panel_specs.json"
DEFAULT_BOUNDED_PANEL_MATRIX = DEFAULT_M1771_OUTPUT_DIR / "bounded_panel_matrix.csv"
DEFAULT_RUN_DIR = Path("runs/m1777_metric_specific_bounded_panel_measured_execution")
DEFAULT_EVAL_SEED_BASE = 177700
TARGET_EPISODE_COUNT = 288
TARGET_PROFILE_COUNT = 12
TARGET_BOUNDED_PANEL_SPEC_COUNT = 24
TARGET_ROLE_PANEL_COUNT = 4
PANEL_STRING_SEMANTICS_FIELDS = (
    "evaluation_role",
    "primary_metric_family",
    "panel_evaluation_role",
    "panel_primary_metric_family",
    "panel_metric_contract",
)
PANEL_BOOLEAN_SEMANTICS_FIELDS = (
    "ranking_eligible_after_audit",
    "diagnostic_only_no_ranking_claim",
    "benchmark_row",
    "metric_required_avoidance_success",
    "metric_required_benchmark_success",
    "metric_required_collision_mitigation_score",
    "metric_required_controlled_drift_recovery_success",
    "metric_required_diagnostic_only_no_ranking_claim",
    "metric_required_hidden_dynamics_robustness",
    "metric_required_impact_severity_proxy",
    "metric_required_off_track_severity_proxy",
    "metric_required_off_track_violation",
    "metric_required_recovery_success",
    "metric_required_recovery_time_proxy",
    "metric_required_drift_used",
    "metric_required_impact_beta_abs",
    "metric_required_impact_speed_proxy",
    "metric_required_impact_yaw_rate_abs",
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
BOUNDED_PANEL_FAILURE_FIELDNAMES = [
    "workload_id",
    "bounded_panel_workload_id",
    "scenario_workload_id",
    "scenario_spec_id",
    "bounded_panel_spec_id",
    "source_scenario_spec_id",
    "m1728_scenario_spec_id",
    "role_panel_id",
    "scenario_family_id",
    "scenario_family",
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


def load_bounded_panel_specs(path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted([dict(row) for row in payload["bounded_panel_specs"]], key=lambda row: str(row["bounded_panel_spec_id"]))


def bounded_panel_workload_rows(path: Path | str = DEFAULT_BOUNDED_PANEL_MATRIX) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item.update(
            {
                "workload_id": str(row["bounded_panel_workload_id"]),
                "task_source_id": str(row["bounded_panel_spec_id"]),
                "task_family": str(row["scenario_family_id"]),
                "source_edge": str(row["scenario_family"]),
                "window_tag": str(row["hidden_dynamics_bucket"]),
                "executable_source_family": str(row["scenario_family"]),
                "env_template_family": str(row["scenario_family"]),
                "labels_enter_actor_input": _as_bool(row.get("labels_enter_actor_input", False)),
                "ranking_eligible_after_audit": _as_bool(row.get("ranking_eligible_after_audit", False)),
                "diagnostic_only_no_ranking_claim": _as_bool(row.get("diagnostic_only_no_ranking_claim", True)),
                "sampling_repair_applied": _as_bool(row.get("sampling_repair_applied", False)),
            }
        )
        item["strata"] = ";".join(
            [
                "metric_specific_bounded_panel",
                f"role_panel_{row['role_panel_id']}",
                f"scenario_family_{row['scenario_family']}",
                f"hidden_dynamics_{row['hidden_dynamics_bucket']}",
                f"road_boundary_{row['road_boundary_bucket']}",
                f"obstacle_timing_{row['obstacle_timing_bucket']}",
                f"obstacle_lateral_{row['obstacle_lateral_bucket']}",
            ]
        )
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


def _panel_semantics_passthrough_values(workload_row: Mapping[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in PANEL_STRING_SEMANTICS_FIELDS:
        values[field] = str(workload_row.get(field, ""))
    for field in PANEL_BOOLEAN_SEMANTICS_FIELDS:
        values[field] = _as_bool(workload_row.get(field, False))
    return values


def _run_bounded_panel_workload_cell(
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
            "bounded_panel_workload_id": str(workload_row["bounded_panel_workload_id"]),
            "scenario_workload_id": str(workload_row["scenario_workload_id"]),
            "scenario_spec_id": str(workload_row["scenario_spec_id"]),
            "bounded_panel_spec_id": str(workload_row["bounded_panel_spec_id"]),
            "source_scenario_spec_id": str(workload_row["source_scenario_spec_id"]),
            "m1728_scenario_spec_id": str(workload_row["m1728_scenario_spec_id"]),
            "role_panel_id": str(workload_row["role_panel_id"]),
            "role_panel_label": str(workload_row["role_panel_label"]),
            "scenario_family_id": str(workload_row["scenario_family_id"]),
            "scenario_family": str(workload_row["scenario_family"]),
            "scenario_role": str(workload_row["scenario_role"]),
            "obstacle_timing_bucket": str(workload_row["obstacle_timing_bucket"]),
            "obstacle_lateral_bucket": str(workload_row["obstacle_lateral_bucket"]),
            "road_boundary_bucket": str(workload_row["road_boundary_bucket"]),
            "hidden_dynamics_bucket": str(workload_row["hidden_dynamics_bucket"]),
            "allowed_labels_metadata_only": str(workload_row["allowed_labels_metadata_only"]),
            "labels_enter_actor_input": _as_bool(workload_row.get("labels_enter_actor_input", False)),
            "sampling_repair_source": str(workload_row["sampling_repair_source"]),
            "sampling_repair_variant_id": str(workload_row["sampling_repair_variant_id"]),
            "sampling_repair_applied": _as_bool(workload_row.get("sampling_repair_applied", False)),
            **_panel_semantics_passthrough_values(workload_row),
            "sampled_obstacle_label": str(row.get("obstacle_label", row.get("sampled_obstacle_label", ""))),
            "metric_specific_bounded_panel_execution": True,
            "full_rollout_execution": False,
            "controller_family_ranking_claim_made": False,
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
                "bounded_panel_workload_id": str(row.get("bounded_panel_workload_id", "")),
                "bounded_panel_spec_id": str(row.get("bounded_panel_spec_id", "")),
                "profile_name": str(row.get("profile_name", "")),
                "field": field,
                "rule": rule,
                "value": row.get(field, ""),
                "reason": reason,
            }
        )

    for row in episode_rows:
        for field in PANEL_STRING_SEMANTICS_FIELDS:
            record(
                row,
                field=field,
                rule="panel_semantics_required",
                applicable=True,
                valid=bool(str(row.get(field, "")).strip()),
                reason="expected_nonempty_panel_semantics_field",
            )
        for field in PANEL_BOOLEAN_SEMANTICS_FIELDS:
            record(
                row,
                field=field,
                rule="panel_semantics_required",
                applicable=True,
                valid=_is_bool_like(row.get(field)),
                reason="expected_bool_like_panel_semantics_field",
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
        "role_panel_aggregate": aggregate_outcome_rows(episode_rows, ("role_panel_id",)),
        "scenario_family_aggregate": aggregate_outcome_rows(episode_rows, ("scenario_family",)),
        "scenario_role_aggregate": aggregate_outcome_rows(episode_rows, ("scenario_role",)),
        "evaluation_role_aggregate": aggregate_outcome_rows(episode_rows, ("evaluation_role",)),
        "primary_metric_family_aggregate": aggregate_outcome_rows(episode_rows, ("primary_metric_family",)),
        "hidden_dynamics_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("hidden_dynamics_bucket",)),
        "road_boundary_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("road_boundary_bucket",)),
        "obstacle_timing_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("obstacle_timing_bucket",)),
        "obstacle_lateral_bucket_aggregate": aggregate_outcome_rows(episode_rows, ("obstacle_lateral_bucket",)),
        "sampled_obstacle_label_aggregate": aggregate_outcome_rows(episode_rows, ("sampled_obstacle_label",)),
        "outcome_aggregate": aggregate_outcome_rows(episode_rows, ("outcome_bucket",)),
        "termination_reason_aggregate": aggregate_outcome_rows(episode_rows, ("termination_reason",)),
        "profile_outcome_aggregate": aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket")),
        "role_panel_outcome_aggregate": aggregate_outcome_rows(episode_rows, ("role_panel_id", "outcome_bucket")),
        "primary_metric_family_outcome_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("primary_metric_family", "outcome_bucket"),
        ),
        "role_panel_sampled_label_aggregate": aggregate_outcome_rows(
            episode_rows,
            ("role_panel_id", "sampled_obstacle_label"),
        ),
        "profile_hidden_dynamics_worst_bucket": profile_hidden_dynamics_worst_rows(episode_rows),
    }
    for name, rows in aggregates.items():
        write_csv_rows(output_dir / f"{name}.csv", rows)
    return {f"{name}_rows": len(rows) for name, rows in aggregates.items()}


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def finalize_bounded_panel_outputs(
    *,
    output_dir: Path,
    target_workload_count: int,
    next_blocker: str = "m1778-paper-route-metric-specific-bounded-panel-measured-execution-result-audit",
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=BOUNDED_PANEL_FAILURE_FIELDNAMES)
    aggregate_counts = _write_aggregates(output_dir, episode_rows)
    metric_completeness_summary, metric_completeness_failures = metric_completeness_rows(episode_rows)
    write_csv_rows(output_dir / "metric_completeness_summary.csv", metric_completeness_summary)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_completeness_failures)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    profile_count = len({row["profile_name"] for row in episode_rows}) if episode_rows else 0
    bounded_panel_spec_count = len({row["bounded_panel_spec_id"] for row in episode_rows}) if episode_rows else 0
    role_panel_count = len({row["role_panel_id"] for row in episode_rows}) if episode_rows else 0
    result_passes = (
        len(episode_rows) == target_workload_count
        and not failure_rows
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and profile_count == TARGET_PROFILE_COUNT
        and bounded_panel_spec_count == TARGET_BOUNDED_PANEL_SPEC_COUNT
        and role_panel_count == TARGET_ROLE_PANEL_COUNT
        and aggregate_counts["role_panel_aggregate_rows"] == TARGET_ROLE_PANEL_COUNT
        and aggregate_counts["profile_aggregate_rows"] == TARGET_PROFILE_COUNT
        and aggregate_counts["outcome_aggregate_rows"] > 0
        and aggregate_counts["termination_reason_aggregate_rows"] > 0
        and aggregate_counts["primary_metric_family_aggregate_rows"] > 0
        and aggregate_counts["role_panel_sampled_label_aggregate_rows"] > 0
        and bool(metric_completeness_summary)
        and not metric_completeness_failures
    )
    summary = {
        "result_class": (
            "metric_specific_bounded_panel_measured_execution_pass"
            if result_passes
            else "metric_specific_bounded_panel_measured_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": target_workload_count,
        "profile_count": profile_count,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "bounded_panel_spec_count": bounded_panel_spec_count,
        "target_bounded_panel_spec_count": TARGET_BOUNDED_PANEL_SPEC_COUNT,
        "role_panel_count": role_panel_count,
        "target_role_panel_count": TARGET_ROLE_PANEL_COUNT,
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        **aggregate_counts,
        "metric_completeness_summary_rows": len(metric_completeness_summary),
        "metric_completeness_failure_count": len(metric_completeness_failures),
        "metric_completeness_passed": bool(metric_completeness_summary and not metric_completeness_failures),
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
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "episode_rows": str(output_dir / "episode_rows.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
            "profile_aggregate": str(output_dir / "profile_aggregate.csv"),
            "role_panel_aggregate": str(output_dir / "role_panel_aggregate.csv"),
            "scenario_family_aggregate": str(output_dir / "scenario_family_aggregate.csv"),
            "scenario_role_aggregate": str(output_dir / "scenario_role_aggregate.csv"),
            "evaluation_role_aggregate": str(output_dir / "evaluation_role_aggregate.csv"),
            "primary_metric_family_aggregate": str(output_dir / "primary_metric_family_aggregate.csv"),
            "hidden_dynamics_bucket_aggregate": str(output_dir / "hidden_dynamics_bucket_aggregate.csv"),
            "road_boundary_bucket_aggregate": str(output_dir / "road_boundary_bucket_aggregate.csv"),
            "obstacle_timing_bucket_aggregate": str(output_dir / "obstacle_timing_bucket_aggregate.csv"),
            "obstacle_lateral_bucket_aggregate": str(output_dir / "obstacle_lateral_bucket_aggregate.csv"),
            "sampled_obstacle_label_aggregate": str(output_dir / "sampled_obstacle_label_aggregate.csv"),
            "outcome_aggregate": str(output_dir / "outcome_aggregate.csv"),
            "termination_reason_aggregate": str(output_dir / "termination_reason_aggregate.csv"),
            "profile_outcome_aggregate": str(output_dir / "profile_outcome_aggregate.csv"),
            "role_panel_outcome_aggregate": str(output_dir / "role_panel_outcome_aggregate.csv"),
            "primary_metric_family_outcome_aggregate": str(output_dir / "primary_metric_family_outcome_aggregate.csv"),
            "role_panel_sampled_label_aggregate": str(output_dir / "role_panel_sampled_label_aggregate.csv"),
            "profile_hidden_dynamics_worst_bucket": str(output_dir / "profile_hidden_dynamics_worst_bucket.csv"),
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


def run_metric_specific_bounded_panel_measured_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    bounded_panel_specs_path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS,
    bounded_panel_matrix_path: Path | str = DEFAULT_BOUNDED_PANEL_MATRIX,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = "m1778-paper-route-metric-specific-bounded-panel-measured-execution-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_bounded_panel_specs(bounded_panel_specs_path)
    spec_by_id = {str(spec["bounded_panel_spec_id"]): spec for spec in executable_specs}
    workload_rows = bounded_panel_workload_rows(bounded_panel_matrix_path)
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
            output / "role_panel_aggregate.csv",
            output / "scenario_family_aggregate.csv",
            output / "scenario_role_aggregate.csv",
            output / "evaluation_role_aggregate.csv",
            output / "primary_metric_family_aggregate.csv",
            output / "hidden_dynamics_bucket_aggregate.csv",
            output / "road_boundary_bucket_aggregate.csv",
            output / "obstacle_timing_bucket_aggregate.csv",
            output / "obstacle_lateral_bucket_aggregate.csv",
            output / "sampled_obstacle_label_aggregate.csv",
            output / "outcome_aggregate.csv",
            output / "termination_reason_aggregate.csv",
            output / "profile_outcome_aggregate.csv",
            output / "role_panel_outcome_aggregate.csv",
            output / "primary_metric_family_outcome_aggregate.csv",
            output / "role_panel_sampled_label_aggregate.csv",
            output / "profile_hidden_dynamics_worst_bucket.csv",
            output / "metric_completeness_summary.csv",
            output / "metric_completeness_failures.csv",
        ):
            if path.exists():
                path.unlink()
        completed = set()

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=BOUNDED_PANEL_FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = _run_bounded_panel_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["bounded_panel_spec_id"])],
                profile_config=profile_config,
                model=model,
                profile_row=profile_by_name[profile_name],
                eval_seed=eval_seed,
            )
            append_csv_row(output / "episode_rows.csv", row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - measured execution must preserve failures as rows.
            failure_row = {
                "workload_id": workload_id,
                "bounded_panel_workload_id": str(workload_row.get("bounded_panel_workload_id", "")),
                "scenario_workload_id": str(workload_row.get("scenario_workload_id", "")),
                "scenario_spec_id": str(workload_row.get("scenario_spec_id", "")),
                "bounded_panel_spec_id": str(workload_row.get("bounded_panel_spec_id", "")),
                "source_scenario_spec_id": str(workload_row.get("source_scenario_spec_id", "")),
                "m1728_scenario_spec_id": str(workload_row.get("m1728_scenario_spec_id", "")),
                "role_panel_id": str(workload_row.get("role_panel_id", "")),
                "scenario_family_id": str(workload_row.get("scenario_family_id", "")),
                "scenario_family": str(workload_row.get("scenario_family", "")),
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

    return finalize_bounded_panel_outputs(
        output_dir=output,
        target_workload_count=len(workload_rows),
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run measured execution for the metric-specific bounded panel.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--bounded-panel-specs", type=Path, default=DEFAULT_BOUNDED_PANEL_SPECS)
    parser.add_argument("--bounded-panel-matrix", type=Path, default=DEFAULT_BOUNDED_PANEL_MATRIX)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--next-blocker",
        default="m1778-paper-route-metric-specific-bounded-panel-measured-execution-result-audit",
    )
    args = parser.parse_args()

    summary = run_metric_specific_bounded_panel_measured_execution(
        output_dir=args.output_dir,
        bounded_panel_specs_path=args.bounded_panel_specs,
        bounded_panel_matrix_path=args.bounded_panel_matrix,
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
