"""Measured runner adapter for calibrated task-quality executable v2 workloads."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import append_csv_row, completed_workload_ids, write_run_state
from autodrift.executable_v2_task_quality_measured_runner import (
    _bool,
    _episode_success,
    _load_profile_cache,
    _metric_value,
    _real_rollout_metrics,
    read_csv_rows,
    selected_metrics_are_finite,
)


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json"
)
DEFAULT_WORKLOAD = Path("runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1965_executable_v2_task_quality_calibrated_measured_execution")
DEFAULT_EVAL_SEED_BASE = 196500
TARGET_EPISODE_COUNT = 960
TARGET_SPEC_COUNT = 80
TARGET_PROFILE_COUNT = 12
EXPECTED_SOURCE_KIND_COUNTS = {
    "anchor_neighborhood": 384,
    "mitigation_isolation_check": 192,
    "offtrack_boundary_relief": 96,
    "success_stabilizer": 288,
}
EXPECTED_ROLE_SURFACE_COUNTS = {
    "anchor_neighborhood|stable_aeb|post_friction_step": 192,
    "anchor_neighborhood|stable_aeb|steady_surface": 192,
    "mitigation_isolation_check|drift_required_recovery|steady_surface": 36,
    "mitigation_isolation_check|stable_aeb|post_friction_step": 48,
    "mitigation_isolation_check|unavoidable_mitigation|post_friction_step": 48,
    "mitigation_isolation_check|unavoidable_mitigation|steady_surface": 60,
    "offtrack_boundary_relief|stable_aes_only|relief_surface_unspecified": 96,
    "success_stabilizer|drift_required_recovery|post_friction_step": 48,
    "success_stabilizer|drift_required_recovery|steady_surface": 24,
    "success_stabilizer|stable_aeb|post_friction_step": 48,
    "success_stabilizer|stable_aeb|steady_surface": 48,
    "success_stabilizer|stable_aes_only|post_friction_step": 36,
    "success_stabilizer|stable_aes_only|steady_surface": 36,
    "success_stabilizer|unavoidable_mitigation|post_friction_step": 12,
    "success_stabilizer|unavoidable_mitigation|steady_surface": 36,
}
QUOTA_METADATA_FIELDS = (
    "repair_source_kind",
    "source_role_semantics",
    "normalized_surface_variant",
)
QUOTA_METADATA_MISSING_FIELDNAMES = [
    "row_index",
    "workload_id",
    "task_source_id",
    "profile_name",
    "missing_quota_fields",
    *QUOTA_METADATA_FIELDS,
]
SUMMARY_SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
CALIBRATED_PASSTHROUGH_FIELDS = (
    "workload_id",
    "task_source_id",
    "candidate_source_id",
    "repair_candidate_id",
    "repair_source_kind",
    "selection_quota_name",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "parent_surface_variant",
    "normalized_surface_variant",
    "source_split",
    "base_geometry_source",
    "representative_cell_rule",
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
)
FAILURE_FIELDNAMES = [
    *CALIBRATED_PASSTHROUGH_FIELDS,
    "eval_seed",
    "error_type",
    "error_message",
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
RolloutFunction = Callable[[Mapping[str, Any], Mapping[str, Any], int], Mapping[str, Any]]


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("calibrated measured runner specs must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def load_workload_rows(path: Path | str = DEFAULT_WORKLOAD) -> list[dict[str, Any]]:
    return sorted([dict(row) for row in read_csv_rows(path)], key=lambda row: str(row.get("workload_id", "")))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_counts(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts["|".join(str(row.get(key, "")) for key in keys)] += 1
    return dict(sorted(counts.items()))


def quota_metadata_missing_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    missing_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        missing_fields = [field for field in QUOTA_METADATA_FIELDS if not str(row.get(field, "")).strip()]
        if not missing_fields:
            continue
        missing_rows.append(
            {
                "row_index": int(index),
                "workload_id": str(row.get("workload_id", "")),
                "task_source_id": str(row.get("task_source_id", "")),
                "profile_name": str(row.get("profile_name", "")),
                "missing_quota_fields": ",".join(missing_fields),
                **{field: str(row.get(field, "")) for field in QUOTA_METADATA_FIELDS},
            }
        )
    return missing_rows


def expected_quota_counts_from_workload(
    workload_rows: list[Mapping[str, Any]],
) -> tuple[dict[str, int], dict[str, int], list[dict[str, Any]]]:
    return (
        _count_by(workload_rows, "repair_source_kind"),
        _group_counts(workload_rows, QUOTA_METADATA_FIELDS),
        quota_metadata_missing_rows(workload_rows),
    )


def _spec_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_v1_bounded_panel_spec_id": str(spec.get("source_v1_bounded_panel_spec_id", "")),
        "source_scenario_spec_id": str(spec.get("source_scenario_spec_id", "")),
        "speed_ref": spec.get("speed_ref", ""),
        "mu": spec.get("mu", ""),
        "friction_step_enabled": spec.get("friction_step_enabled", ""),
        "friction_step_at": spec.get("friction_step_at", ""),
        "obstacle_distance": spec.get("obstacle_distance", ""),
        "obstacle_half_width": spec.get("obstacle_half_width", ""),
        "threshold_score": spec.get("threshold_score", ""),
        "time_to_obstacle": spec.get("time_to_obstacle", ""),
        "time_after_friction_step": spec.get("time_after_friction_step", ""),
        "preflight_sampled_obstacle_label": str(spec.get("sampled_obstacle_label", "")),
    }


def calibrated_metadata_row(workload_row: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    row = {field: str(workload_row.get(field, spec.get(field, ""))) for field in CALIBRATED_PASSTHROUGH_FIELDS}
    row.update(_spec_metadata(spec))
    return row


def measured_episode_row(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = dict(rollout_metrics)
    row.update(calibrated_metadata_row(workload_row, executable_spec))
    row.update(
        {
            "eval_seed": int(eval_seed),
            "success": _episode_success(row),
            "task_quality_calibrated_measured_execution": True,
            "environment_rollout_started": True,
            "policy_action_executed": True,
            "measured_rollout_started": True,
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
    )
    row["sampled_obstacle_label"] = str(
        row.get(
            "sampled_obstacle_label",
            row.get("obstacle_label", executable_spec.get("sampled_obstacle_label", "")),
        )
    )
    return row


def measured_failure_row(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    eval_seed: int,
    error: BaseException,
) -> dict[str, Any]:
    return {
        **calibrated_metadata_row(workload_row, executable_spec),
        "eval_seed": int(eval_seed),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "environment_rollout_started": True,
        "policy_action_executed": False,
        "measured_rollout_started": True,
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


def validation_failure_rows(
    *,
    executable_specs: list[Mapping[str, Any]],
    workload_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    spec_ids = {str(spec.get("task_source_id", "")) for spec in executable_specs}
    workload_ids: Counter[str] = Counter(str(row.get("workload_id", "")) for row in workload_rows)
    required_workload_fields = (
        "workload_id",
        "task_source_id",
        "profile_name",
        "profile_config_path",
        "checkpoint_path",
        "repair_source_kind",
        "selection_quota_name",
        "source_role_semantics",
        "normalized_surface_variant",
    )
    required_spec_fields = (
        "task_source_id",
        "candidate_source_id",
        "repair_candidate_id",
        "repair_source_kind",
        "selection_quota_name",
        "source_role_semantics",
        "parent_feasibility_tier_id",
        "normalized_surface_variant",
        "base_geometry_source",
        "representative_cell_rule",
        "env_config",
    )
    for workload_id, count in sorted(workload_ids.items()):
        if workload_id and count > 1:
            failures.append({"workload_id": workload_id, "error_type": "duplicate_workload_id", "error_message": str(count)})
    for spec in executable_specs:
        task_source_id = str(spec.get("task_source_id", ""))
        for field in required_spec_fields:
            if field == "env_config":
                if not isinstance(spec.get(field), Mapping):
                    failures.append(
                        {"workload_id": task_source_id, "error_type": "missing_spec_field", "error_message": field}
                    )
                continue
            if not str(spec.get(field, "")).strip():
                failures.append({"workload_id": task_source_id, "error_type": "missing_spec_field", "error_message": field})
    for index, row in enumerate(workload_rows):
        workload_id = str(row.get("workload_id", f"row_{index}"))
        for field in required_workload_fields:
            if not str(row.get(field, "")).strip():
                failures.append({"workload_id": workload_id, "error_type": "missing_workload_field", "error_message": field})
        if str(row.get("task_source_id", "")) not in spec_ids:
            failures.append(
                {
                    "workload_id": workload_id,
                    "error_type": "missing_executable_spec",
                    "error_message": str(row.get("task_source_id", "")),
                }
            )
        for flag in (
            "environment_rollout_scheduled",
            "training_scheduled",
            "profile_specific_tuning",
            "controller_family_ranking_claim_made",
            "paper_level_claim_made",
            "level3_self_id_claim_made",
        ):
            if _bool(row.get(flag), default=False):
                failures.append({"workload_id": workload_id, "error_type": "guardrail_violation", "error_message": flag})
    return failures


def aggregate_rows(rows: list[Mapping[str, Any]], group_key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key, ""))].append(row)
    output: list[dict[str, Any]] = []
    for group, group_rows in sorted(groups.items()):
        margins = [_metric_value(row, "min_clearance_margin") for row in group_rows]
        output.append(
            {
                group_key: group,
                "episode_count": len(group_rows),
                "success_rate": float(np.mean([_metric_value(row, "success") for row in group_rows])),
                "collision_rate": float(np.mean([_metric_value(row, "collision") for row in group_rows])),
                "clearance_margin_mean": float(np.mean(margins)) if margins else float("nan"),
                "return_mean": float(np.mean([_metric_value(row, "return") for row in group_rows])),
                "steps_mean": float(np.mean([_metric_value(row, "steps") for row in group_rows])),
                "all_selected_metrics_finite": selected_metrics_are_finite(group_rows),
            }
        )
    return output


def aggregate_role_surface_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("repair_source_kind", "")),
            str(row.get("source_role_semantics", "")),
            str(row.get("normalized_surface_variant", "")),
        )
        groups[key].append(row)
    output: list[dict[str, Any]] = []
    for (kind, role, surface), group_rows in sorted(groups.items()):
        margins = [_metric_value(row, "min_clearance_margin") for row in group_rows]
        output.append(
            {
                "repair_source_kind": kind,
                "source_role_semantics": role,
                "normalized_surface_variant": surface,
                "episode_count": len(group_rows),
                "success_rate": float(np.mean([_metric_value(row, "success") for row in group_rows])),
                "collision_rate": float(np.mean([_metric_value(row, "collision") for row in group_rows])),
                "clearance_margin_mean": float(np.mean(margins)) if margins else float("nan"),
                "return_mean": float(np.mean([_metric_value(row, "return") for row in group_rows])),
                "all_selected_metrics_finite": selected_metrics_are_finite(group_rows),
            }
        )
    return output


def metric_completeness_failure_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in rows:
        for metric in SUMMARY_SELECTED_METRICS:
            if not np.isfinite(_metric_value(row, metric)):
                failures.append(
                    {
                        "workload_id": str(row.get("workload_id", "")),
                        "metric": metric,
                        "value": row.get(metric, ""),
                    }
                )
    return failures


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "calibrated_task_quality_measured_execution_completed",
            "admissible": True,
            "reason": "episode rows are measured rollout artifacts when the runner is executed",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "measured execution must be audited before ranking or comparison claims",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "single public diagnostic execution is not paper-level evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "measured rollout does not test wrong-history or history necessity by itself",
        },
    ]


def _matches_expected_counts(actual: dict[str, int], expected: Mapping[str, int] | None) -> bool:
    if expected is None:
        return False
    return actual == dict(sorted((str(key), int(value)) for key, value in expected.items()))


def finalize_outputs(
    *,
    output_dir: Path,
    target_episode_count: int,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    expected_source_kind_counts: Mapping[str, int] | None = None,
    expected_role_surface_counts: Mapping[str, int] | None = None,
    expected_quota_source: str = "unspecified",
    quota_metadata_missing_rows_: Iterable[Mapping[str, Any]] | None = None,
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    metric_failures = metric_completeness_failure_rows(episode_rows)
    aggregate_paths = {
        "profile_aggregate": ("profile_aggregate.csv", "profile_name"),
        "source_kind_aggregate": ("source_kind_aggregate.csv", "repair_source_kind"),
        "role_aggregate": ("role_aggregate.csv", "source_role_semantics"),
        "normalized_surface_aggregate": ("normalized_surface_aggregate.csv", "normalized_surface_variant"),
        "sampled_label_aggregate": ("sampled_label_aggregate.csv", "sampled_obstacle_label"),
        "outcome_aggregate": ("outcome_aggregate.csv", "outcome_bucket"),
        "termination_reason_aggregate": ("termination_reason_aggregate.csv", "termination_reason"),
    }
    artifacts: dict[str, str] = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "validation_failure_rows": str(output_dir / "validation_failure_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        "quota_metadata_missing_rows": str(output_dir / "quota_metadata_missing_rows.csv"),
        "claim_boundary": str(output_dir / "claim_boundary.csv"),
        "run_state": str(output_dir / "run_state.json"),
    }
    for artifact_key, (filename, group_key) in aggregate_paths.items():
        path = output_dir / filename
        if episode_rows and group_key in episode_rows[0]:
            write_csv_rows(path, aggregate_rows(episode_rows, group_key))
        else:
            write_csv_rows(path, [])
        artifacts[artifact_key] = str(path)
    role_surface_path = output_dir / "role_surface_aggregate.csv"
    write_csv_rows(role_surface_path, aggregate_role_surface_rows(episode_rows))
    artifacts["role_surface_aggregate"] = str(role_surface_path)
    quota_missing_rows = [dict(row) for row in (quota_metadata_missing_rows_ or [])]
    write_csv_rows(
        output_dir / "quota_metadata_missing_rows.csv",
        quota_missing_rows,
        fieldnames=QUOTA_METADATA_MISSING_FIELDNAMES,
    )
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_failures)
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows())

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    spec_count = len({str(row.get("task_source_id", "")) for row in episode_rows})
    profile_count = len({str(row.get("profile_name", "")) for row in episode_rows})
    source_kind_counts = _count_by(episode_rows, "repair_source_kind")
    role_surface_counts = _group_counts(
        episode_rows,
        ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
    )
    source_kind_quota_pass = _matches_expected_counts(source_kind_counts, expected_source_kind_counts)
    role_surface_quota_pass = _matches_expected_counts(role_surface_counts, expected_role_surface_counts)
    quota_metadata_missing_count = len(quota_missing_rows)
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and spec_count == int(target_spec_count)
        and profile_count == int(target_profile_count)
        and quota_metadata_missing_count == 0
        and source_kind_quota_pass
        and role_surface_quota_pass
        and not metric_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "task_quality_calibrated_measured_execution_pass"
            if passes
            else "task_quality_calibrated_measured_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "failure_count": len(failure_rows),
        "spec_count": spec_count,
        "target_spec_count": int(target_spec_count),
        "profile_count": profile_count,
        "target_profile_count": int(target_profile_count),
        "expected_quota_source": str(expected_quota_source),
        "expected_source_kind_counts": dict(
            sorted((str(key), int(value)) for key, value in (expected_source_kind_counts or {}).items())
        ),
        "expected_role_surface_counts": dict(
            sorted((str(key), int(value)) for key, value in (expected_role_surface_counts or {}).items())
        ),
        "quota_metadata_missing_count": quota_metadata_missing_count,
        "source_kind_counts": source_kind_counts,
        "source_kind_quota_pass": source_kind_quota_pass,
        "role_surface_counts": role_surface_counts,
        "role_surface_quota_pass": role_surface_quota_pass,
        "sampled_label_counts": _count_by(episode_rows, "sampled_obstacle_label"),
        "outcome_counts": _count_by(episode_rows, "outcome_bucket"),
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(episode_rows or failure_rows),
        "policy_action_executed": bool(episode_rows),
        "measured_rollout_started": bool(episode_rows or failure_rows),
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
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_episode_count": int(target_episode_count),
            "completed_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "complete": bool(passes),
        },
    )
    return summary


def run_calibrated_task_quality_measured_execution(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    target_episode_count: int | None = TARGET_EPISODE_COUNT,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    expected_source_kind_counts: Mapping[str, int] | None = None,
    expected_role_surface_counts: Mapping[str, int] | None = None,
    next_blocker: str = "m1966-executable-v2-task-quality-calibrated-measured-execution-result-audit",
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_task_specs(executable_task_specs_path)
    workload_rows = load_workload_rows(workload_path)
    computed_source_counts, computed_role_counts, quota_missing_rows = expected_quota_counts_from_workload(workload_rows)
    expected_quota_source = "explicit"
    if expected_source_kind_counts is None or expected_role_surface_counts is None:
        if expected_source_kind_counts is None:
            expected_source_kind_counts = computed_source_counts
        if expected_role_surface_counts is None:
            expected_role_surface_counts = computed_role_counts
        expected_quota_source = "workload"
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    validation_failures = validation_failure_rows(executable_specs=executable_specs, workload_rows=workload_rows)
    if validation_failures:
        write_csv_rows(output / "validation_failure_rows.csv", validation_failures)
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
        return finalize_outputs(
            output_dir=output,
            target_episode_count=int(target_episode_count or len(workload_rows)),
            target_spec_count=int(target_spec_count),
            target_profile_count=int(target_profile_count),
            expected_source_kind_counts=expected_source_kind_counts,
            expected_role_surface_counts=expected_role_surface_counts,
            expected_quota_source=expected_quota_source,
            quota_metadata_missing_rows_=quota_missing_rows,
            next_blocker=next_blocker,
        )
    write_csv_rows(output / "validation_failure_rows.csv", [])

    completed = completed_workload_ids(output / "episode_rows.csv") if resume else set()
    if not resume:
        for path in output.glob("*.csv"):
            path.unlink()
        for path in (output / "summary.json", output / "run_state.json"):
            if path.exists():
                path.unlink()
        completed = set()
    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    profile_cache = None if rollout_fn is not None else _load_profile_cache(workload_rows, device=device)
    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        eval_seed = int(eval_seed_base) + int(cell_index)
        executable_spec = spec_by_id[str(workload_row["task_source_id"])]
        try:
            if rollout_fn is None:
                profile_config, model, _profile_row = profile_cache[str(workload_row["profile_name"])]  # type: ignore[index]
                rollout_metrics = _real_rollout_metrics(
                    workload_row=workload_row,
                    executable_spec=executable_spec,
                    profile_config=profile_config,
                    model=model,
                    eval_seed=eval_seed,
                )
            else:
                rollout_metrics = dict(rollout_fn(workload_row, executable_spec, eval_seed))
            row = measured_episode_row(
                workload_row=workload_row,
                executable_spec=executable_spec,
                rollout_metrics=rollout_metrics,
                eval_seed=eval_seed,
            )
            append_csv_row(output / "episode_rows.csv", row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - measured execution must preserve row failures.
            append_csv_row(
                output / "failure_rows.csv",
                measured_failure_row(
                    workload_row=workload_row,
                    executable_spec=executable_spec,
                    eval_seed=eval_seed,
                    error=exc,
                ),
            )
        write_run_state(
            output / "run_state.json",
            {
                "target_episode_count": int(target_episode_count or len(workload_rows)),
                "completed_count": len(completed_workload_ids(output / "episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_outputs(
        output_dir=output,
        target_episode_count=int(target_episode_count or len(workload_rows)),
        target_spec_count=int(target_spec_count),
        target_profile_count=int(target_profile_count),
        expected_source_kind_counts=expected_source_kind_counts,
        expected_role_surface_counts=expected_role_surface_counts,
        expected_quota_source=expected_quota_source,
        quota_metadata_missing_rows_=quota_missing_rows,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_SPEC_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--next-blocker", default="m1966-executable-v2-task-quality-calibrated-measured-execution-result-audit")
    args = parser.parse_args()
    summary = run_calibrated_task_quality_measured_execution(
        output_dir=args.output_dir,
        executable_task_specs_path=args.executable_task_specs,
        workload_path=args.workload,
        eval_seed_base=int(args.eval_seed_base),
        device=str(args.device),
        resume=not bool(args.no_resume),
        target_episode_count=int(args.target_episode_count),
        target_spec_count=int(args.target_spec_count),
        target_profile_count=int(args.target_profile_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"metric_completeness_failure_count={summary['metric_completeness_failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
