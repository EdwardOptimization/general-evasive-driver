"""Measured runner adapter for task-quality executable v2 workloads."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    append_csv_row,
    completed_workload_ids,
    env_config_for_executable_profile,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, run_episode_with_policy


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json"
)
DEFAULT_WORKLOAD = Path(
    "runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1938_executable_v2_task_quality_measured_execution")
DEFAULT_EVAL_SEED_BASE = 193800
TARGET_EPISODE_COUNT = 960
TARGET_SPEC_COUNT = 80
TARGET_PROFILE_COUNT = 12
TARGET_TIER_COUNT = 5
TARGET_ROLE_COUNT = 4
TARGET_SURFACE_COUNT = 2
SUMMARY_SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
PASSTHROUGH_FIELDS = (
    "workload_id",
    "task_source_id",
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "profile_name",
    "feasibility_tier_id",
    "source_role_semantics",
    "source_split",
    "surface_variant",
    "target_boundary_mode",
    "selected_accepted_cell_rule",
    "strata",
    "profile_config_path",
    "checkpoint_path",
)
FAILURE_FIELDNAMES = [
    *PASSTHROUGH_FIELDS,
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


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "nan", "none"}:
        return False
    return default


def _float_metric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite_metric(value: Any) -> bool:
    return bool(np.isfinite(_float_metric(value)))


def _episode_success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success"))
    return _bool(row.get("obstacle_completed")) and not _bool(row.get("collision"))


def _metric_value(row: Mapping[str, Any], metric: str) -> float:
    if metric == "success":
        return float(_episode_success(row))
    if metric == "collision":
        return float(_bool(row.get("collision")))
    return _float_metric(row.get(metric, float("nan")))


def selected_metrics_are_finite(rows: Iterable[Mapping[str, Any]]) -> bool:
    for row in rows:
        for metric in SUMMARY_SELECTED_METRICS:
            if not np.isfinite(_metric_value(row, metric)):
                return False
    return True


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("task-quality measured runner specs must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def load_workload_rows(path: Path | str = DEFAULT_WORKLOAD) -> list[dict[str, Any]]:
    return sorted([dict(row) for row in read_csv_rows(path)], key=lambda row: str(row.get("workload_id", "")))


def _spec_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_v1_bounded_panel_spec_id": str(spec.get("source_v1_bounded_panel_spec_id", "")),
        "source_scenario_spec_id": str(spec.get("source_scenario_spec_id", "")),
        "label": str(spec.get("label", "")),
        "speed_ref": spec.get("speed_ref", ""),
        "mu": spec.get("mu", ""),
        "obstacle_distance": spec.get("obstacle_distance", ""),
        "obstacle_half_width": spec.get("obstacle_half_width", ""),
        "threshold_score": spec.get("threshold_score", ""),
        "target_support_mode": str(spec.get("target_support_mode", "")),
        "time_after_friction_step": spec.get("time_after_friction_step", ""),
    }


def workload_metadata_row(workload_row: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    row = {field: str(workload_row.get(field, spec.get(field, ""))) for field in PASSTHROUGH_FIELDS}
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
    row.update(workload_metadata_row(workload_row, executable_spec))
    row.update(
        {
            "eval_seed": int(eval_seed),
            "success": _episode_success(row),
            "task_quality_measured_execution": True,
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
        row.get("sampled_obstacle_label", row.get("obstacle_label", executable_spec.get("label", "")))
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
        **workload_metadata_row(workload_row, executable_spec),
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
    required_workload_fields = ("workload_id", "task_source_id", "profile_name", "profile_config_path", "checkpoint_path")
    for workload_id, count in sorted(workload_ids.items()):
        if workload_id and count > 1:
            failures.append({"workload_id": workload_id, "error_type": "duplicate_workload_id", "error_message": str(count)})
    for index, row in enumerate(workload_rows):
        workload_id = str(row.get("workload_id", f"row_{index}"))
        for field in required_workload_fields:
            if not str(row.get(field, "")).strip():
                failures.append({"workload_id": workload_id, "error_type": "missing_workload_field", "error_message": field})
        if str(row.get("task_source_id", "")) not in spec_ids:
            failures.append({"workload_id": workload_id, "error_type": "missing_executable_spec", "error_message": str(row.get("task_source_id", ""))})
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


def _load_profile_cache(
    workload_rows: Iterable[Mapping[str, Any]],
    *,
    device: str,
) -> dict[str, tuple[dict[str, Any], Any, dict[str, Any]]]:
    cache: dict[str, tuple[dict[str, Any], Any, dict[str, Any]]] = {}
    for row in workload_rows:
        profile_name = str(row.get("profile_name", ""))
        if profile_name in cache:
            continue
        profile_config = read_json(row["profile_config_path"])
        model, _ = load_actor_critic_checkpoint(row["checkpoint_path"], device=device)
        cache[profile_name] = (
            profile_config,
            model,
            {
                "profile_name": profile_name,
                "config_path": str(row["profile_config_path"]),
                "checkpoint_path": str(row["checkpoint_path"]),
            },
        )
    return cache


def _real_rollout_metrics(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: dict[str, Any],
    model: Any,
    eval_seed: int,
) -> dict[str, Any]:
    env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    target_obs_dim = int(env.observation_space.shape[0])
    model_obs_dim = int(getattr(model, "obs_dim", -1))
    if model_obs_dim != target_obs_dim:
        env.close()
        raise ValueError(
            f"profile {workload_row['profile_name']} checkpoint obs_dim {model_obs_dim} "
            f"does not match task env obs_dim {target_obs_dim}"
        )
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    try:
        return dict(run_episode_with_policy(env, policy, "checkpoint", int(eval_seed)))
    finally:
        env.close()


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
            "claim": "task_quality_measured_execution_completed",
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


def finalize_outputs(
    *,
    output_dir: Path,
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
    aggregate_paths = {
        "profile_aggregate": ("profile_aggregate.csv", "profile_name"),
        "tier_aggregate": ("tier_aggregate.csv", "feasibility_tier_id"),
        "role_aggregate": ("role_aggregate.csv", "source_role_semantics"),
        "surface_aggregate": ("surface_aggregate.csv", "surface_variant"),
        "sampled_label_aggregate": ("sampled_label_aggregate.csv", "sampled_obstacle_label"),
        "outcome_aggregate": ("outcome_aggregate.csv", "outcome_bucket"),
        "termination_reason_aggregate": ("termination_reason_aggregate.csv", "termination_reason"),
    }
    artifacts: dict[str, str] = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
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
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_failures)
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows())

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    spec_count = len({str(row.get("task_source_id", "")) for row in episode_rows})
    profile_count = len({str(row.get("profile_name", "")) for row in episode_rows})
    tier_count = len({str(row.get("feasibility_tier_id", "")) for row in episode_rows})
    role_count = len({str(row.get("source_role_semantics", "")) for row in episode_rows})
    surface_count = len({str(row.get("surface_variant", "")) for row in episode_rows})
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and spec_count == int(target_spec_count)
        and profile_count == int(target_profile_count)
        and not metric_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "task_quality_measured_execution_pass"
            if passes
            else "task_quality_measured_execution_incomplete_or_fail"
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
        "tier_count": tier_count,
        "target_tier_count": TARGET_TIER_COUNT,
        "role_count": role_count,
        "target_role_count": TARGET_ROLE_COUNT,
        "surface_count": surface_count,
        "target_surface_count": TARGET_SURFACE_COUNT,
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "profile_counts": _count_by(episode_rows, "profile_name"),
        "tier_counts": _count_by(episode_rows, "feasibility_tier_id"),
        "role_counts": _count_by(episode_rows, "source_role_semantics"),
        "surface_counts": _count_by(episode_rows, "surface_variant"),
        "sampled_label_counts": _count_by(episode_rows, "sampled_obstacle_label"),
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


def run_task_quality_measured_execution(
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
    next_blocker: str = "m1939-executable-v2-task-quality-measured-execution-result-audit",
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_task_specs(executable_task_specs_path)
    workload_rows = load_workload_rows(workload_path)
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
            next_blocker=next_blocker,
        )

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
    parser.add_argument("--next-blocker", default="m1939-executable-v2-task-quality-measured-execution-result-audit")
    args = parser.parse_args()
    summary = run_task_quality_measured_execution(
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
