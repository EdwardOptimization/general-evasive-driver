"""Focused measured runner adapter for current-sim controlled-comparison panels."""

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
    selected_metrics_are_finite,
)


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json"
)
DEFAULT_WORKLOAD = Path("runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2169_paper_route_current_sim_controlled_comparison_measured_execution")
DEFAULT_EVAL_SEED_BASE = 216900
TARGET_EPISODE_COUNT = 320
TARGET_SPEC_COUNT = 40
TARGET_PROFILE_COUNT = 8
SUMMARY_SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
SPEC_METADATA_FIELDS = (
    "task_source_id",
    "benchmark_spec_id",
    "task_family",
    "claim_level_target",
    "scenario_source",
    "source_kind",
    "source_reference",
    "source_index",
    "source_seed",
    "eval_seed_override",
    "materialization_semantics",
    "paper_validity_status",
    "generated_proxy_source",
    "actor_input_contract",
    "metric_gap_policy",
    "source_family_template",
    "capability_pair",
    "reveal_step",
)
WORKLOAD_METADATA_FIELDS = (
    "workload_id",
    "profile_name",
    "profile_level",
    "profile_config_path",
    "checkpoint_path",
    "checkpoint_required_for_measured_execution",
    "history_representation",
    "history_window_steps",
    "reset_or_truncated_control",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
METADATA_FIELDS = (*SPEC_METADATA_FIELDS, *WORKLOAD_METADATA_FIELDS)
FAILURE_FIELDNAMES = [
    *METADATA_FIELDS,
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
    "winner_selected",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
METADATA_MISSING_FIELDNAMES = [
    "row_index",
    "workload_id",
    "task_source_id",
    "profile_name",
    "missing_metadata_fields",
]
VALIDATION_FAILURE_FIELDNAMES = ["workload_id", "error_type", "error_message"]
AGGREGATE_FIELDNAMES = [
    "key",
    "episode_count",
    "success_rate",
    "collision_rate",
    "clearance_margin_mean",
    "return_mean",
    "steps_mean",
    "all_selected_metrics_finite",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
FORBIDDEN_GUARDRAILS = (
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "winner_selected",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
RolloutFunction = Callable[[Mapping[str, Any], Mapping[str, Any], int], Mapping[str, Any]]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _float_metric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _metric_or_nan(row: Mapping[str, Any], metric: str) -> float:
    if metric in {"success", "collision"}:
        return _metric_value(row, metric)
    return _float_metric(row.get(metric, float("nan")))


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("current-sim measured runner specs must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def load_workload_rows(path: Path | str = DEFAULT_WORKLOAD) -> list[dict[str, str]]:
    return sorted(read_csv_rows(path), key=lambda row: str(row.get("workload_id", "")))


def eval_seed_for_workload(*, workload_row: Mapping[str, Any], executable_spec: Mapping[str, Any], eval_seed_base: int, cell_index: int) -> int:
    workload_override = str(workload_row.get("eval_seed_override", "")).strip()
    if workload_override:
        return int(workload_override)
    spec_override = str(executable_spec.get("eval_seed_override", "")).strip()
    if spec_override:
        return int(spec_override)
    return int(eval_seed_base) + int(cell_index)


def current_sim_metadata_row(workload_row: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    row = {field: str(spec.get(field, "")) for field in SPEC_METADATA_FIELDS}
    row.update({field: str(workload_row.get(field, "")) for field in WORKLOAD_METADATA_FIELDS})
    for field in (
        "generated_proxy_source",
        "reset_or_truncated_control",
        "environment_reset_scheduled",
        "environment_rollout_scheduled",
        "training_scheduled",
        "profile_specific_tuning",
        "controller_family_ranking_claim_made",
        "finite_window_vs_gru_conclusion_made",
        "paper_level_claim_made",
        "level3_self_id_claim_made",
    ):
        if field in row:
            row[field] = "true" if _bool(row.get(field)) else "false"
    return row


def metadata_missing_rows(
    *,
    executable_specs: list[Mapping[str, Any]],
    workload_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    spec_by_id = {str(spec.get("task_source_id", "")): spec for spec in executable_specs}
    rows: list[dict[str, Any]] = []
    for index, workload_row in enumerate(workload_rows):
        task_source_id = str(workload_row.get("task_source_id", ""))
        spec = spec_by_id.get(task_source_id, {})
        metadata = current_sim_metadata_row(workload_row, spec)
        missing = [field for field in METADATA_FIELDS if not str(metadata.get(field, "")).strip()]
        if missing:
            rows.append(
                {
                    "row_index": int(index),
                    "workload_id": str(workload_row.get("workload_id", "")),
                    "task_source_id": task_source_id,
                    "profile_name": str(workload_row.get("profile_name", "")),
                    "missing_metadata_fields": ";".join(missing),
                }
            )
    return rows


def validation_failure_rows(
    *,
    executable_specs: list[Mapping[str, Any]],
    workload_rows: list[Mapping[str, Any]],
    require_checkpoint_paths: bool,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    spec_ids = {str(spec.get("task_source_id", "")) for spec in executable_specs}
    workload_ids: Counter[str] = Counter(str(row.get("workload_id", "")) for row in workload_rows)
    required_spec_fields = (*SPEC_METADATA_FIELDS, "env_config")
    required_workload_fields = (
        "workload_id",
        "task_source_id",
        "profile_name",
        "profile_config_path",
        "checkpoint_required_for_measured_execution",
        "task_family",
        "history_representation",
        "history_window_steps",
        "profile_level",
    )
    for workload_id, count in sorted(workload_ids.items()):
        if workload_id and count > 1:
            failures.append({"workload_id": workload_id, "error_type": "duplicate_workload_id", "error_message": str(count)})
    for spec in executable_specs:
        task_source_id = str(spec.get("task_source_id", ""))
        for field in required_spec_fields:
            if field == "env_config":
                if not isinstance(spec.get(field), Mapping):
                    failures.append({"workload_id": task_source_id, "error_type": "missing_spec_field", "error_message": field})
                continue
            if not str(spec.get(field, "")).strip():
                failures.append({"workload_id": task_source_id, "error_type": "missing_spec_field", "error_message": field})
    for index, row in enumerate(workload_rows):
        workload_id = str(row.get("workload_id", f"row_{index}"))
        for field in required_workload_fields:
            if not str(row.get(field, "")).strip():
                failures.append({"workload_id": workload_id, "error_type": "missing_workload_field", "error_message": field})
        if str(row.get("task_source_id", "")) not in spec_ids:
            failures.append({"workload_id": workload_id, "error_type": "missing_executable_spec", "error_message": str(row.get("task_source_id", ""))})
        profile_config_path = str(row.get("profile_config_path", "")).strip()
        if profile_config_path and not Path(profile_config_path).exists():
            failures.append({"workload_id": workload_id, "error_type": "profile_config_path_not_found", "error_message": profile_config_path})
        checkpoint_required = _bool(row.get("checkpoint_required_for_measured_execution"))
        checkpoint_path = str(row.get("checkpoint_path", "")).strip()
        if require_checkpoint_paths and checkpoint_required:
            if not checkpoint_path:
                failures.append({"workload_id": workload_id, "error_type": "missing_checkpoint_path", "error_message": "checkpoint_required_for_measured_execution"})
            elif not Path(checkpoint_path).exists():
                failures.append({"workload_id": workload_id, "error_type": "checkpoint_path_not_found", "error_message": checkpoint_path})
        for flag in (
            "training_scheduled",
            "profile_specific_tuning",
            "controller_family_ranking_claim_made",
            "finite_window_vs_gru_conclusion_made",
            "paper_level_claim_made",
            "level3_self_id_claim_made",
        ):
            if _bool(row.get(flag), default=False):
                failures.append({"workload_id": workload_id, "error_type": "guardrail_violation", "error_message": flag})
    return failures


def measured_episode_row(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = dict(rollout_metrics)
    row.update(current_sim_metadata_row(workload_row, executable_spec))
    row.update(
        {
            "eval_seed": int(eval_seed),
            "success": _episode_success(row),
            "current_sim_controlled_comparison_measured_execution": True,
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
            "winner_selected": False,
            "finite_window_vs_gru_conclusion_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    row["reset_sampled_obstacle_label"] = str(row.get("obstacle_label", row.get("sampled_obstacle_label", "")))
    return row


def measured_failure_row(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    eval_seed: int,
    error: BaseException,
) -> dict[str, Any]:
    return {
        **current_sim_metadata_row(workload_row, executable_spec),
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
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def aggregate_rows(rows: list[Mapping[str, Any]], group_key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key, ""))].append(row)
    output: list[dict[str, Any]] = []
    for group, group_rows in sorted(groups.items()):
        margins = [_metric_or_nan(row, "min_clearance_margin") for row in group_rows]
        output.append(
            {
                "key": group,
                "episode_count": len(group_rows),
                "success_rate": float(np.mean([_metric_or_nan(row, "success") for row in group_rows])),
                "collision_rate": float(np.mean([_metric_or_nan(row, "collision") for row in group_rows])),
                "clearance_margin_mean": float(np.mean(margins)) if margins else float("nan"),
                "return_mean": float(np.mean([_metric_or_nan(row, "return") for row in group_rows])),
                "steps_mean": float(np.mean([_metric_or_nan(row, "steps") for row in group_rows])),
                "all_selected_metrics_finite": selected_metrics_are_finite(group_rows),
            }
        )
    return output


def metric_completeness_failure_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in rows:
        for metric in SUMMARY_SELECTED_METRICS:
            if not np.isfinite(_metric_or_nan(row, metric)):
                failures.append({"workload_id": str(row.get("workload_id", "")), "metric": metric, "value": row.get(metric, "")})
    return failures


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "current_sim_measured_runner_adapter",
            "admissible": True,
            "reason": "adapter output is valid only as infrastructure until real measured execution is audited",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "measured execution must be audited before ranking or comparison claims",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "adapter execution does not select a winner",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "adapter tests and single public measured execution are not paper-level evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "measured execution must be audited and compared under denominator-backed protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "measured execution does not test wrong-history or history necessity by itself",
        },
    ]


def finalize_outputs(
    *,
    output_dir: Path,
    executable_specs: list[Mapping[str, Any]],
    workload_rows: list[Mapping[str, Any]],
    target_episode_count: int,
    target_spec_count: int,
    target_profile_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    metric_failures = metric_completeness_failure_rows(episode_rows)
    missing_rows = metadata_missing_rows(executable_specs=executable_specs, workload_rows=workload_rows)
    write_csv_rows(output_dir / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_failures)
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    aggregate_paths = {
        "profile_aggregate": ("profile_aggregate.csv", "profile_name"),
        "profile_level_aggregate": ("profile_level_aggregate.csv", "profile_level"),
        "history_representation_aggregate": ("history_representation_aggregate.csv", "history_representation"),
        "task_family_aggregate": ("task_family_aggregate.csv", "task_family"),
        "source_family_template_aggregate": ("source_family_template_aggregate.csv", "source_family_template"),
        "capability_pair_aggregate": ("capability_pair_aggregate.csv", "capability_pair"),
        "outcome_aggregate": ("outcome_aggregate.csv", "outcome_bucket"),
        "termination_reason_aggregate": ("termination_reason_aggregate.csv", "termination_reason"),
    }
    artifacts: dict[str, str] = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "validation_failure_rows": str(output_dir / "validation_failure_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        "metadata_missing_rows": str(output_dir / "metadata_missing_rows.csv"),
        "claim_boundary": str(output_dir / "claim_boundary.csv"),
        "run_state": str(output_dir / "run_state.json"),
    }
    for artifact_key, (filename, group_key) in aggregate_paths.items():
        path = output_dir / filename
        if episode_rows and group_key in episode_rows[0]:
            write_csv_rows(path, aggregate_rows(episode_rows, group_key), fieldnames=AGGREGATE_FIELDNAMES)
        else:
            write_csv_rows(path, [], fieldnames=AGGREGATE_FIELDNAMES)
        artifacts[artifact_key] = str(path)

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    spec_count = len({str(row.get("task_source_id", "")) for row in episode_rows})
    profile_count = len({str(row.get("profile_name", "")) for row in episode_rows})
    task_family_counts = _count_by(episode_rows, "task_family")
    expected_task_family_counts = _count_by(workload_rows, "task_family")
    profile_counts = _count_by(episode_rows, "profile_name")
    expected_profile_counts = _count_by(workload_rows, "profile_name")
    history_representation_counts = _count_by(episode_rows, "history_representation")
    expected_history_representation_counts = _count_by(workload_rows, "history_representation")
    task_family_quota_pass = task_family_counts == expected_task_family_counts
    profile_quota_pass = profile_counts == expected_profile_counts
    history_representation_quota_pass = history_representation_counts == expected_history_representation_counts
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and spec_count == int(target_spec_count)
        and profile_count == int(target_profile_count)
        and not missing_rows
        and task_family_quota_pass
        and profile_quota_pass
        and history_representation_quota_pass
        and not metric_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_controlled_comparison_measured_execution_pass"
            if passes
            else "current_sim_controlled_comparison_measured_execution_incomplete_or_fail"
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
        "metadata_missing_count": len(missing_rows),
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "expected_task_family_counts": expected_task_family_counts,
        "task_family_counts": task_family_counts,
        "task_family_quota_pass": task_family_quota_pass,
        "expected_profile_counts": expected_profile_counts,
        "profile_counts": profile_counts,
        "profile_quota_pass": profile_quota_pass,
        "expected_history_representation_counts": expected_history_representation_counts,
        "history_representation_counts": history_representation_counts,
        "history_representation_quota_pass": history_representation_quota_pass,
        "outcome_counts": _count_by(episode_rows, "outcome_bucket"),
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
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
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
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


def run_current_sim_measured_execution(
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
    next_blocker: str = "m2170-paper-route-current-sim-controlled-comparison-measured-execution-result-audit",
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_task_specs(executable_task_specs_path)
    workload_rows = load_workload_rows(workload_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    validation_failures = validation_failure_rows(
        executable_specs=executable_specs,
        workload_rows=workload_rows,
        require_checkpoint_paths=rollout_fn is None,
    )
    if validation_failures:
        write_csv_rows(output / "validation_failure_rows.csv", validation_failures, fieldnames=VALIDATION_FAILURE_FIELDNAMES)
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
        return finalize_outputs(
            output_dir=output,
            executable_specs=executable_specs,
            workload_rows=workload_rows,
            target_episode_count=int(target_episode_count or len(workload_rows)),
            target_spec_count=int(target_spec_count),
            target_profile_count=int(target_profile_count),
            next_blocker=next_blocker,
        )
    write_csv_rows(output / "validation_failure_rows.csv", [], fieldnames=VALIDATION_FAILURE_FIELDNAMES)

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
        executable_spec = spec_by_id[str(workload_row["task_source_id"])]
        eval_seed = eval_seed_for_workload(
            workload_row=workload_row,
            executable_spec=executable_spec,
            eval_seed_base=int(eval_seed_base),
            cell_index=int(cell_index),
        )
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
        executable_specs=executable_specs,
        workload_rows=workload_rows,
        target_episode_count=int(target_episode_count or len(workload_rows)),
        target_spec_count=int(target_spec_count),
        target_profile_count=int(target_profile_count),
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
    parser.add_argument("--next-blocker", default="m2170-paper-route-current-sim-controlled-comparison-measured-execution-result-audit")
    args = parser.parse_args()
    summary = run_current_sim_measured_execution(
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
