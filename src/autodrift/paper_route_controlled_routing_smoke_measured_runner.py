"""Focused measured runner for the controlled routing-smoke workload."""

from __future__ import annotations

import argparse
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
    "runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json"
)
DEFAULT_WORKLOAD = Path("runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2039_paper_route_controlled_routing_smoke_measured_execution")
DEFAULT_EVAL_SEED_BASE = 203900
TARGET_EPISODE_COUNT = 432
TARGET_SPEC_COUNT = 36
TARGET_PROFILE_COUNT = 12
SUMMARY_SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
METADATA_FIELDS = (
    "workload_id",
    "task_source_id",
    "panel_source_id",
    "panel_task_family",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "source_reference",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
)
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
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
RolloutFunction = Callable[[Mapping[str, Any], Mapping[str, Any], int], Mapping[str, Any]]


def _string_bool(value: Any) -> str:
    return "true" if _bool(value) else "false"


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _count_by_key_func(rows: Iterable[Mapping[str, Any]], key_func: Any) -> dict[str, int]:
    return dict(sorted(Counter(str(key_func(row)) for row in rows).items()))


def _generated_proxy_key(row: Mapping[str, Any]) -> str:
    return (
        f"generated={_string_bool(row.get('generated_source_row'))}|"
        f"semantics={row.get('materialization_semantics', '')}|"
        f"paper_claim={str(row.get('paper_validity_claim', '')).lower()}"
    )


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("controlled routing-smoke measured runner specs must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def load_workload_rows(path: Path | str = DEFAULT_WORKLOAD) -> list[dict[str, Any]]:
    return sorted([dict(row) for row in read_csv_rows(path)], key=lambda row: str(row.get("workload_id", "")))


def controlled_metadata_row(workload_row: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    row = {field: str(workload_row.get(field, spec.get(field, ""))) for field in METADATA_FIELDS}
    row["generated_source_row"] = _string_bool(row.get("generated_source_row"))
    row["paper_validity_claim"] = str(row.get("paper_validity_claim", "")).lower()
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
        metadata = controlled_metadata_row(workload_row, spec)
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
        "panel_task_family",
        "source_kind",
        "proxy_template_family",
        "generated_source_row",
        "paper_validity_claim",
    )
    required_spec_fields = (
        "task_source_id",
        "panel_source_id",
        "panel_task_family",
        "source_kind",
        "source_reference",
        "materialization_semantics",
        "proxy_template_family",
        "generated_source_row",
        "paper_validity_claim",
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
        for flag in (
            "training_scheduled",
            "profile_specific_tuning",
            "controller_family_ranking_claim_made",
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
    row.update(controlled_metadata_row(workload_row, executable_spec))
    row.update(
        {
            "eval_seed": int(eval_seed),
            "success": _episode_success(row),
            "controlled_routing_smoke_measured_execution": True,
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
        **controlled_metadata_row(workload_row, executable_spec),
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
        margins = [_metric_value(row, "min_clearance_margin") for row in group_rows]
        output.append(
            {
                "key": group,
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


def metric_completeness_failure_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in rows:
        for metric in SUMMARY_SELECTED_METRICS:
            if not np.isfinite(_metric_value(row, metric)):
                failures.append({"workload_id": str(row.get("workload_id", "")), "metric": metric, "value": row.get(metric, "")})
    return failures


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "controlled_routing_smoke_measured_execution_completed",
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
            "reason": "single public routing-smoke execution is not paper-level evidence",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated T2/T3 rows remain smoke proxies until later task-semantics validation",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "measured execution must be audited before comparison claims",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "measured rollout does not test wrong-history or history necessity by itself",
        },
    ]


def finalize_outputs(
    *,
    output_dir: Path,
    executable_specs: list[Mapping[str, Any]],
    workload_rows: list[Mapping[str, Any]],
    target_episode_count: int,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
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
        "family_aggregate": ("family_aggregate.csv", "panel_task_family"),
        "source_kind_aggregate": ("source_kind_aggregate.csv", "source_kind"),
        "proxy_template_aggregate": ("proxy_template_aggregate.csv", "proxy_template_family"),
        "generated_proxy_aggregate": ("generated_proxy_aggregate.csv", "generated_source_row"),
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
    family_counts = _count_by(episode_rows, "panel_task_family")
    expected_family_counts = _count_by(workload_rows, "panel_task_family")
    source_kind_counts = _count_by(episode_rows, "source_kind")
    expected_source_kind_counts = _count_by(workload_rows, "source_kind")
    proxy_template_counts = _count_by(episode_rows, "proxy_template_family")
    expected_proxy_template_counts = _count_by(workload_rows, "proxy_template_family")
    generated_proxy_counts = _count_by_key_func(episode_rows, _generated_proxy_key)
    expected_generated_proxy_counts = _count_by_key_func(workload_rows, _generated_proxy_key)
    family_quota_pass = family_counts == expected_family_counts
    source_kind_quota_pass = source_kind_counts == expected_source_kind_counts
    proxy_template_quota_pass = proxy_template_counts == expected_proxy_template_counts
    generated_proxy_quota_pass = generated_proxy_counts == expected_generated_proxy_counts
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and spec_count == int(target_spec_count)
        and profile_count == int(target_profile_count)
        and not missing_rows
        and family_quota_pass
        and source_kind_quota_pass
        and proxy_template_quota_pass
        and generated_proxy_quota_pass
        and not metric_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "controlled_routing_smoke_measured_execution_pass"
            if passes
            else "controlled_routing_smoke_measured_execution_incomplete_or_fail"
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
        "expected_family_counts": expected_family_counts,
        "family_counts": family_counts,
        "family_quota_pass": family_quota_pass,
        "expected_source_kind_counts": expected_source_kind_counts,
        "source_kind_counts": source_kind_counts,
        "source_kind_quota_pass": source_kind_quota_pass,
        "expected_proxy_template_counts": expected_proxy_template_counts,
        "proxy_template_counts": proxy_template_counts,
        "proxy_template_quota_pass": proxy_template_quota_pass,
        "expected_generated_proxy_counts": expected_generated_proxy_counts,
        "generated_proxy_counts": generated_proxy_counts,
        "generated_proxy_quota_pass": generated_proxy_quota_pass,
        "profile_counts": _count_by(episode_rows, "profile_name"),
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


def run_controlled_routing_smoke_measured_execution(
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
    next_blocker: str = "m2040-paper-route-controlled-routing-smoke-measured-execution-result-audit",
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_task_specs(executable_task_specs_path)
    workload_rows = load_workload_rows(workload_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    validation_failures = validation_failure_rows(executable_specs=executable_specs, workload_rows=workload_rows)
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
    parser.add_argument("--next-blocker", default="m2040-paper-route-controlled-routing-smoke-measured-execution-result-audit")
    args = parser.parse_args()
    summary = run_controlled_routing_smoke_measured_execution(
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
