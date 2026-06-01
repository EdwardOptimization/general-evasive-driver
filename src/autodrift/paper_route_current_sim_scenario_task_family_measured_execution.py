"""Focused measured execution for the current-sim scenario task-family pack."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

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


DEFAULT_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_SELECTED_ROWS = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv"
)
DEFAULT_CONFIG_ROOT = Path("runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs")
DEFAULT_OUTPUT_DIR = Path("runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution")
DEFAULT_EVAL_SEED_BASE = 229300
TARGET_SCENARIO_SPEC_COUNT = 72
TARGET_SELECTED_CHECKPOINT_COUNT = 15
TARGET_EPISODE_COUNT = TARGET_SCENARIO_SPEC_COUNT * TARGET_SELECTED_CHECKPOINT_COUNT
DEFAULT_NEXT_BLOCKER = "m2294-paper-route-current-sim-scenario-task-family-measured-execution-result-audit"

SUMMARY_SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
SCENARIO_METADATA_FIELDS = (
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "sampled_obstacle_label",
    "allowed_labels_metadata_only",
    "same_scene_group_id",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "initial_speed_mps",
    "track_radius_m",
    "track_width_m",
)
SELECTED_METADATA_FIELDS = (
    "matrix_id",
    "profile_name",
    "seed_id",
    "selected_checkpoint_path",
    "selected_checkpoint_step",
    "selected_checkpoint_kind",
    "selected_readiness_floor_pass",
)
WORKLOAD_METADATA_FIELDS = (
    "workload_id",
    "scenario_index",
    "selected_checkpoint_index",
    "eval_seed",
    "profile_seed",
    "profile_config_path",
)
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
EPISODE_FIELDNAMES = [
    *WORKLOAD_METADATA_FIELDS,
    *SCENARIO_METADATA_FIELDS,
    *SELECTED_METADATA_FIELDS,
    "reset_sampled_obstacle_label",
    "sampled_label_matches_spec",
    "policy",
    "seed",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "outcome_bucket",
    "return",
    "min_clearance_margin",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "high_sideslip_fraction",
    "action_rate_mean",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    *FORBIDDEN_GUARDRAILS,
]
FAILURE_FIELDNAMES = [
    *WORKLOAD_METADATA_FIELDS,
    *SCENARIO_METADATA_FIELDS,
    *SELECTED_METADATA_FIELDS,
    "error_type",
    "error_message",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    *FORBIDDEN_GUARDRAILS,
]
VALIDATION_FAILURE_FIELDNAMES = ["workload_id", "error_type", "error_message"]
METADATA_MISSING_FIELDNAMES = [
    "workload_id",
    "missing_metadata_fields",
]
METRIC_COMPLETENESS_FIELDNAMES = [
    "workload_id",
    "metric",
    "value",
]
AGGREGATE_FIELDNAMES = [
    "group_axis",
    "group_key",
    "group_value",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "offtrack_count",
    "offtrack_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_failure_count",
    "other_failure_rate",
    "mean_return",
    "mean_steps",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_max_off_track_overshoot",
    "mean_time_to_first_off_track_s",
    "mean_high_sideslip_fraction",
    "mean_action_rate",
    "dominant_failure_mode",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]

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
    if text in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _float_metric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite(value: Any) -> bool:
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


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _mean(values: Sequence[Any]) -> float | None:
    finite = [_float_metric(value) for value in values if _finite(value)]
    if not finite:
        return None
    return float(np.mean(finite))


def _min(values: Sequence[Any]) -> float | None:
    finite = [_float_metric(value) for value in values if _finite(value)]
    if not finite:
        return None
    return float(np.min(finite))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_scenario_specs(path: Path | str = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    payload = read_json(path)
    specs = payload.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return [dict(spec) for spec in specs]


def load_selected_rows(path: Path | str = DEFAULT_SELECTED_ROWS) -> list[dict[str, str]]:
    return read_csv_rows(path)


def _selected_key(row: Mapping[str, Any]) -> str:
    matrix_id = str(row.get("matrix_id", "")).strip()
    if matrix_id:
        return matrix_id
    return f"{row.get('profile_name', '')}::seed_{row.get('seed_id', '')}"


def _profile_seed(row: Mapping[str, Any]) -> str:
    return f"{row.get('profile_name', '')}|{row.get('seed_id', '')}"


def _config_path(config_root: Path, selected_row: Mapping[str, Any]) -> Path:
    profile_name = str(selected_row.get("profile_name", ""))
    seed_id = int(float(str(selected_row.get("seed_id", "-1"))))
    return config_root / profile_name / f"seed_{seed_id}" / "config.json"


def eval_seed_for_cell(*, eval_seed_base: int, selected_index: int, scenario_index: int) -> int:
    return int(eval_seed_base) + int(selected_index) * 1000 + int(scenario_index)


def workload_rows(
    *,
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    config_root: Path | str,
    eval_seed_base: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = Path(config_root)
    for selected_index, selected in enumerate(selected_rows):
        selected_key = _selected_key(selected)
        for scenario_index, scenario in enumerate(scenario_specs):
            scenario_id = str(scenario.get("scenario_spec_id", f"scenario_{scenario_index:03d}"))
            eval_seed = eval_seed_for_cell(
                eval_seed_base=int(eval_seed_base),
                selected_index=int(selected_index),
                scenario_index=int(scenario_index),
            )
            rows.append(
                {
                    "workload_id": f"{selected_key}::{scenario_id}",
                    "scenario_index": int(scenario_index),
                    "selected_checkpoint_index": int(selected_index),
                    "eval_seed": int(eval_seed),
                    "profile_seed": _profile_seed(selected),
                    "profile_config_path": str(_config_path(root, selected)),
                    "scenario_spec_id": scenario_id,
                    "selected_key": selected_key,
                }
            )
    return rows


def _scenario_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: spec.get(field, "") for field in SCENARIO_METADATA_FIELDS}


def _selected_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in SELECTED_METADATA_FIELDS}


def _workload_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in WORKLOAD_METADATA_FIELDS}


def merged_metadata(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **_workload_metadata(workload_row),
        **_scenario_metadata(scenario_spec),
        **_selected_metadata(selected_row),
    }


def metadata_missing_rows(
    *,
    workload: Sequence[Mapping[str, Any]],
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for workload_row in workload:
        scenario = scenario_specs[int(workload_row["scenario_index"])]
        selected = selected_rows[int(workload_row["selected_checkpoint_index"])]
        metadata = merged_metadata(workload_row=workload_row, scenario_spec=scenario, selected_row=selected)
        missing = [field for field in (*WORKLOAD_METADATA_FIELDS, *SCENARIO_METADATA_FIELDS, *SELECTED_METADATA_FIELDS) if not str(metadata.get(field, "")).strip()]
        if missing:
            rows.append(
                {
                    "workload_id": str(workload_row.get("workload_id", "")),
                    "missing_metadata_fields": ";".join(missing),
                }
            )
    return rows


def validation_failure_rows(
    *,
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    config_root: Path | str,
    require_checkpoint_paths: bool,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    workload_ids = Counter(str(row.get("workload_id", "")) for row in workload)
    for workload_id, count in sorted(workload_ids.items()):
        if workload_id and count > 1:
            failures.append({"workload_id": workload_id, "error_type": "duplicate_workload_id", "error_message": str(count)})
    for index, scenario in enumerate(scenario_specs):
        scenario_id = str(scenario.get("scenario_spec_id", f"scenario_{index:03d}"))
        if not isinstance(scenario.get("env_config"), Mapping):
            failures.append({"workload_id": scenario_id, "error_type": "missing_scenario_field", "error_message": "env_config"})
        for field in SCENARIO_METADATA_FIELDS:
            if not str(scenario.get(field, "")).strip():
                failures.append({"workload_id": scenario_id, "error_type": "missing_scenario_field", "error_message": field})
        if str(scenario.get("actor_contract_id", "")) != "P0_human_view_no_wheel_no_oracle":
            failures.append({"workload_id": scenario_id, "error_type": "actor_contract_violation", "error_message": "actor_contract_id"})
        if int(scenario.get("contract_violation_count", 0)) != 0:
            failures.append({"workload_id": scenario_id, "error_type": "actor_contract_violation", "error_message": "contract_violation_count"})
        for flag in (
            "labels_enter_actor_input",
            "ranking_admissible",
            "paper_level_claim_made",
            "level3_self_id_claim_made",
            "execution_blocked_by_unsupported_capability",
        ):
            if _bool(scenario.get(flag), default=False):
                failures.append({"workload_id": scenario_id, "error_type": "guardrail_violation", "error_message": flag})
    root = Path(config_root)
    for index, selected in enumerate(selected_rows):
        selected_key = _selected_key(selected) or f"selected_{index:03d}"
        for field in SELECTED_METADATA_FIELDS:
            if not str(selected.get(field, "")).strip():
                failures.append({"workload_id": selected_key, "error_type": "missing_selected_field", "error_message": field})
        config_path = _config_path(root, selected)
        if not config_path.exists():
            failures.append({"workload_id": selected_key, "error_type": "profile_config_path_not_found", "error_message": str(config_path)})
        checkpoint_path = str(selected.get("selected_checkpoint_path", "")).strip()
        if require_checkpoint_paths:
            if not checkpoint_path:
                failures.append({"workload_id": selected_key, "error_type": "missing_checkpoint_path", "error_message": "selected_checkpoint_path"})
            elif not Path(checkpoint_path).exists():
                failures.append({"workload_id": selected_key, "error_type": "checkpoint_path_not_found", "error_message": checkpoint_path})
        if _bool(selected.get("ranking_admissible"), default=False) or _bool(selected.get("winner_selected"), default=False):
            failures.append({"workload_id": selected_key, "error_type": "guardrail_violation", "error_message": "selected_row_ranking"})
    return failures


def selected_metrics_are_finite(rows: Iterable[Mapping[str, Any]]) -> bool:
    for row in rows:
        for metric in SUMMARY_SELECTED_METRICS:
            if not np.isfinite(_metric_value(row, metric)):
                return False
    return True


def metric_completeness_failure_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
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


def _failure_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        bucket = str(row.get("outcome_bucket", ""))
        termination_reason = str(row.get("termination_reason", ""))
        if bucket == "success_obstacle_pass" or _episode_success(row):
            counts["success"] += 1
        elif bucket == "collision_failure" or _bool(row.get("collision")):
            counts["collision"] += 1
        elif bucket == "off_track_noncollision_noncompletion" or termination_reason == "off_track":
            counts["offtrack"] += 1
        elif bucket == "max_steps_noncompletion" or _bool(row.get("truncated")):
            counts["max_step_noncompletion"] += 1
        else:
            counts["other_failure"] += 1
    return dict(counts)


def _dominant_failure_mode(rows: Sequence[Mapping[str, Any]]) -> str:
    total = len(rows)
    if not total:
        return "low_support_or_incomplete"
    counts = _failure_counts(rows)
    success = counts.get("success", 0)
    if _rate(success, total) >= 2.0 / 3.0:
        return "success_supported"
    failures = max(1, total - success)
    buckets = (
        ("offtrack_dominated_failure", counts.get("offtrack", 0)),
        ("collision_dominated_failure", counts.get("collision", 0)),
        ("max_step_noncompletion_dominated_failure", counts.get("max_step_noncompletion", 0)),
    )
    for label, count in buckets:
        if count / failures >= 0.5:
            return label
    return "mixed_failure"


def aggregate_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_axis: str,
    group_key: str,
    group_value: str,
) -> dict[str, Any]:
    counts = _failure_counts(rows)
    total = len(rows)
    return {
        "group_axis": group_axis,
        "group_key": group_key,
        "group_value": group_value,
        "episode_count": total,
        "success_count": counts.get("success", 0),
        "success_rate": _rate(counts.get("success", 0), total),
        "collision_count": counts.get("collision", 0),
        "collision_rate": _rate(counts.get("collision", 0), total),
        "offtrack_count": counts.get("offtrack", 0),
        "offtrack_rate": _rate(counts.get("offtrack", 0), total),
        "max_step_noncompletion_count": counts.get("max_step_noncompletion", 0),
        "max_step_noncompletion_rate": _rate(counts.get("max_step_noncompletion", 0), total),
        "other_failure_count": counts.get("other_failure", 0),
        "other_failure_rate": _rate(counts.get("other_failure", 0), total),
        "mean_return": _mean([row.get("return") for row in rows]),
        "mean_steps": _mean([row.get("steps") for row in rows]),
        "mean_min_clearance_margin": _mean([row.get("min_clearance_margin") for row in rows]),
        "min_min_clearance_margin": _min([row.get("min_clearance_margin") for row in rows]),
        "mean_max_off_track_overshoot": _mean([row.get("max_off_track_overshoot") for row in rows]),
        "mean_time_to_first_off_track_s": _mean([row.get("time_to_first_off_track_s") for row in rows]),
        "mean_high_sideslip_fraction": _mean([row.get("high_sideslip_fraction") for row in rows]),
        "mean_action_rate": _mean([row.get("action_rate_mean") for row in rows]),
        "dominant_failure_mode": _dominant_failure_mode(rows),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def aggregate_rows(rows: Sequence[Mapping[str, Any]], *, group_axis: str, group_key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key, ""))].append(row)
    return [
        aggregate_row(group, group_axis=group_axis, group_key=group_key, group_value=value)
        for value, group in sorted(groups.items())
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "scenario_task_family_measured_execution_completed",
            "admissible": True,
            "reason": "episode rows are measured rollout artifacts when the runner completes",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2293 output is diagnostic and must be audited before any comparison claim",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2293 does not select or promote a controller family",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2293 is a public measured-execution panel, not a paper-level statistical result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2293 does not execute the denominator-backed comparison protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2293 does not run wrong-history, reset-hidden, or zero-history interventions",
        },
    ]


def measured_episode_row(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = dict(rollout_metrics)
    metadata = merged_metadata(workload_row=workload_row, scenario_spec=scenario_spec, selected_row=selected_row)
    reset_label = str(row.get("obstacle_label", row.get("sampled_obstacle_label", "")))
    spec_label = str(scenario_spec.get("sampled_obstacle_label", ""))
    row.update(metadata)
    row.update(
        {
            "eval_seed": int(eval_seed),
            "success": _episode_success(row),
            "reset_sampled_obstacle_label": reset_label,
            "sampled_label_matches_spec": reset_label == spec_label,
            "scenario_task_family_measured_execution": True,
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
    return row


def measured_failure_row(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    eval_seed: int,
    error: BaseException,
) -> dict[str, Any]:
    return {
        **merged_metadata(workload_row=workload_row, scenario_spec=scenario_spec, selected_row=selected_row),
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


def _real_rollout_metrics(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    profile_config: dict[str, Any],
    model_cache: dict[tuple[str, int], Any],
    device: str,
    eval_seed: int,
) -> dict[str, Any]:
    env_config = env_config_for_executable_profile(executable_spec=scenario_spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    target_obs_dim = int(env.observation_space.shape[0])
    cache_key = (str(workload_row["selected_key"]), target_obs_dim)
    model = model_cache.get(cache_key)
    if model is None:
        model, _ = load_actor_critic_checkpoint(
            str(selected_row["selected_checkpoint_path"]),
            device=device,
            obs_dim=target_obs_dim,
        )
        model_cache[cache_key] = model
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    try:
        return dict(run_episode_with_policy(env, policy, "checkpoint", int(eval_seed)))
    finally:
        env.close()


def finalize_outputs(
    *,
    output_dir: Path,
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    target_episode_count: int,
    target_scenario_spec_count: int,
    target_selected_checkpoint_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    validation_failures = read_csv_rows(output_dir / "validation_failure_rows.csv")
    missing_rows = metadata_missing_rows(workload=workload, scenario_specs=scenario_specs, selected_rows=selected_rows)
    metric_failures = metric_completeness_failure_rows(episode_rows)
    write_csv_rows(output_dir / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_failures, fieldnames=METRIC_COMPLETENESS_FIELDNAMES)
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    aggregate_paths = {
        "aggregate_by_role_family": ("aggregate_by_role_family.csv", "role_family"),
        "aggregate_by_scenario_family": ("aggregate_by_scenario_family.csv", "scenario_family_id"),
        "aggregate_by_profile_seed": ("aggregate_by_profile_seed.csv", "profile_seed"),
        "aggregate_by_profile": ("aggregate_by_profile.csv", "profile_name"),
        "aggregate_by_obstacle_label": ("aggregate_by_obstacle_label.csv", "sampled_obstacle_label"),
        "aggregate_by_timing_bucket": ("aggregate_by_timing_bucket.csv", "obstacle_longitudinal_timing_bucket"),
        "aggregate_by_lateral_bucket": ("aggregate_by_lateral_bucket.csv", "obstacle_lateral_offset_bucket"),
        "aggregate_by_hidden_dynamics_bucket": ("aggregate_by_hidden_dynamics_bucket.csv", "hidden_dynamics_bucket"),
    }
    artifacts: dict[str, str] = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "validation_failure_rows": str(output_dir / "validation_failure_rows.csv"),
        "metadata_missing_rows": str(output_dir / "metadata_missing_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        "claim_boundary": str(output_dir / "claim_boundary.csv"),
        "run_state": str(output_dir / "run_state.json"),
    }
    for artifact_key, (filename, group_key) in aggregate_paths.items():
        path = output_dir / filename
        write_csv_rows(path, aggregate_rows(episode_rows, group_axis=group_key, group_key=group_key), fieldnames=AGGREGATE_FIELDNAMES)
        artifacts[artifact_key] = str(path)

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    scenario_spec_count = len({str(row.get("scenario_spec_id", "")) for row in episode_rows})
    selected_checkpoint_count = len({str(row.get("selected_key", "")) for row in workload})
    selected_checkpoint_count_from_rows = len({str(row.get("matrix_id", "")) for row in episode_rows})
    label_mismatch_count = int(sum(not _bool(row.get("sampled_label_matches_spec"), default=False) for row in episode_rows))
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and len(validation_failures) == 0
        and scenario_spec_count == int(target_scenario_spec_count)
        and selected_checkpoint_count_from_rows == int(target_selected_checkpoint_count)
        and not missing_rows
        and not metric_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_measured_execution_pass"
            if passes
            else "current_sim_scenario_task_family_measured_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "failure_count": len(failure_rows),
        "validation_failure_count": len(validation_failures),
        "scenario_spec_count": scenario_spec_count,
        "target_scenario_spec_count": int(target_scenario_spec_count),
        "selected_checkpoint_count": selected_checkpoint_count_from_rows,
        "planned_selected_checkpoint_count": selected_checkpoint_count,
        "target_selected_checkpoint_count": int(target_selected_checkpoint_count),
        "metadata_missing_count": len(missing_rows),
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "label_mismatch_count": label_mismatch_count,
        "role_family_counts": _count_by(episode_rows, "role_family"),
        "scenario_family_counts": _count_by(episode_rows, "scenario_family_id"),
        "profile_counts": _count_by(episode_rows, "profile_name"),
        "profile_seed_counts": _count_by(episode_rows, "profile_seed"),
        "obstacle_label_counts": _count_by(episode_rows, "sampled_obstacle_label"),
        "timing_bucket_counts": _count_by(episode_rows, "obstacle_longitudinal_timing_bucket"),
        "lateral_bucket_counts": _count_by(episode_rows, "obstacle_lateral_offset_bucket"),
        "hidden_dynamics_bucket_counts": _count_by(episode_rows, "hidden_dynamics_bucket"),
        "outcome_counts": _count_by(episode_rows, "outcome_bucket"),
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
        "global_outcome": aggregate_row(episode_rows, group_axis="global", group_key="global", group_value="all"),
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
        "ranking_admissible_count": 0,
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
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def run_scenario_task_family_measured_execution(
    *,
    config_path: Path | str = DEFAULT_CONFIG,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_scenario_spec_count: int = TARGET_SCENARIO_SPEC_COUNT,
    target_selected_checkpoint_count: int = TARGET_SELECTED_CHECKPOINT_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scenario_specs = load_scenario_specs(config_path)
    selected_rows = load_selected_rows(selected_rows_path)
    workload = workload_rows(
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
        config_root=config_root,
        eval_seed_base=int(eval_seed_base),
    )

    if not resume:
        for path in output.glob("*.csv"):
            path.unlink()
        for path in (output / "summary.json", output / "run_state.json"):
            if path.exists():
                path.unlink()

    validation_failures = validation_failure_rows(
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
        workload=workload,
        config_root=config_root,
        require_checkpoint_paths=rollout_fn is None,
    )
    if validation_failures:
        write_csv_rows(output / "validation_failure_rows.csv", validation_failures, fieldnames=VALIDATION_FAILURE_FIELDNAMES)
        write_csv_rows(output / "episode_rows.csv", [], fieldnames=EPISODE_FIELDNAMES)
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
        return finalize_outputs(
            output_dir=output,
            scenario_specs=scenario_specs,
            selected_rows=selected_rows,
            workload=workload,
            target_episode_count=int(target_episode_count),
            target_scenario_spec_count=int(target_scenario_spec_count),
            target_selected_checkpoint_count=int(target_selected_checkpoint_count),
            next_blocker=str(next_blocker),
        )

    write_csv_rows(output / "validation_failure_rows.csv", [], fieldnames=VALIDATION_FAILURE_FIELDNAMES)
    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
    if not (output / "episode_rows.csv").exists():
        write_csv_rows(output / "episode_rows.csv", [], fieldnames=EPISODE_FIELDNAMES)

    completed = completed_workload_ids(output / "episode_rows.csv") if resume else set()
    profile_config_cache: dict[str, dict[str, Any]] = {}
    model_cache: dict[tuple[str, int], Any] = {}
    for row in workload:
        workload_id = str(row["workload_id"])
        if workload_id in completed:
            continue
        scenario = scenario_specs[int(row["scenario_index"])]
        selected = selected_rows[int(row["selected_checkpoint_index"])]
        eval_seed = int(row["eval_seed"])
        try:
            if rollout_fn is None:
                config_key = str(row["profile_config_path"])
                profile_config = profile_config_cache.get(config_key)
                if profile_config is None:
                    profile_config = read_json(config_key)
                    profile_config_cache[config_key] = profile_config
                rollout_metrics = _real_rollout_metrics(
                    workload_row=row,
                    scenario_spec=scenario,
                    selected_row=selected,
                    profile_config=profile_config,
                    model_cache=model_cache,
                    device=str(device),
                    eval_seed=int(eval_seed),
                )
            else:
                rollout_metrics = dict(rollout_fn(row, scenario, int(eval_seed)))
            episode_row = measured_episode_row(
                workload_row=row,
                scenario_spec=scenario,
                selected_row=selected,
                rollout_metrics=rollout_metrics,
                eval_seed=int(eval_seed),
            )
            append_csv_row(output / "episode_rows.csv", episode_row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - row failures must be preserved.
            append_csv_row(
                output / "failure_rows.csv",
                measured_failure_row(
                    workload_row=row,
                    scenario_spec=scenario,
                    selected_row=selected,
                    eval_seed=int(eval_seed),
                    error=exc,
                ),
            )
        write_run_state(
            output / "run_state.json",
            {
                "target_episode_count": int(target_episode_count),
                "completed_count": len(completed_workload_ids(output / "episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_outputs(
        output_dir=output,
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
        workload=workload,
        target_episode_count=int(target_episode_count),
        target_scenario_spec_count=int(target_scenario_spec_count),
        target_selected_checkpoint_count=int(target_selected_checkpoint_count),
        next_blocker=str(next_blocker),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-scenario-spec-count", type=int, default=TARGET_SCENARIO_SPEC_COUNT)
    parser.add_argument("--target-selected-checkpoint-count", type=int, default=TARGET_SELECTED_CHECKPOINT_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_scenario_task_family_measured_execution(
        config_path=args.config,
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_scenario_spec_count=int(args.target_scenario_spec_count),
        target_selected_checkpoint_count=int(args.target_selected_checkpoint_count),
        target_episode_count=int(args.target_episode_count),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"metric_completeness_failure_count={summary['metric_completeness_failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
