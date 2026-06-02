"""Support-policy feasibility calibration for the scenario task-family pack."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import run_episode_with_policy
from autodrift.outcome_metric_instrumentation import OUTCOME_METRIC_FIELDS
from autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics import (
    annotate_role_success,
    bool_value as role_bool_value,
    is_collision as role_is_collision,
    is_offtrack as role_is_offtrack,
    role_success,
)
from autodrift.policies import make_policy


DEFAULT_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration")
DEFAULT_EVAL_SEED_BASE = 231300
DEFAULT_SUPPORT_POLICIES = ("aeb", "aes", "envelope_aes")
DEFAULT_SEED_REPEATS = 5
TARGET_SCENARIO_SPEC_COUNT = 72
TARGET_SUPPORT_POLICY_COUNT = 3
TARGET_EPISODE_COUNT = TARGET_SCENARIO_SPEC_COUNT * TARGET_SUPPORT_POLICY_COUNT * DEFAULT_SEED_REPEATS
DEFAULT_NEXT_BLOCKER = "m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit"

SCENARIO_METADATA_FIELDS = [
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
    "actor_contract_id",
]
SUPPORT_POLICY_METADATA = {
    "aeb": {
        "support_policy_kind": "full_braking_support_bound",
        "support_policy_uses_privileged_info": False,
        "support_policy_deployable_candidate": False,
    },
    "aes": {
        "support_policy_kind": "heuristic_steer_brake_support_bound",
        "support_policy_uses_privileged_info": True,
        "support_policy_deployable_candidate": False,
    },
    "envelope_aes": {
        "support_policy_kind": "privileged_friction_envelope_support_bound",
        "support_policy_uses_privileged_info": True,
        "support_policy_deployable_candidate": False,
    },
}
FORBIDDEN_GUARDRAILS = [
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


def _extend_unique(fields: Sequence[str], extras: Sequence[str]) -> list[str]:
    output = list(fields)
    for field in extras:
        if field not in output:
            output.append(field)
    return output


EPISODE_FIELDNAMES = _extend_unique([
    "workload_id",
    "scenario_index",
    "support_policy_index",
    "seed_repeat_index",
    "eval_seed",
    *SCENARIO_METADATA_FIELDS,
    "reset_sampled_obstacle_label",
    "sampled_label_matches_spec",
    "support_policy_name",
    "support_policy_kind",
    "support_policy_uses_privileged_info",
    "support_policy_deployable_candidate",
    "diagnostic_only",
    "ranking_admissible",
    "policy",
    "seed",
    "steps",
    "terminated",
    "truncated",
    "raw_success",
    "role_success",
    "role_success_reason",
    "role_success_outcome_bucket",
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
], OUTCOME_METRIC_FIELDS)
FAILURE_FIELDNAMES = [
    "workload_id",
    "scenario_index",
    "support_policy_index",
    "seed_repeat_index",
    "eval_seed",
    *SCENARIO_METADATA_FIELDS,
    "support_policy_name",
    "support_policy_kind",
    "support_policy_uses_privileged_info",
    "support_policy_deployable_candidate",
    "diagnostic_only",
    "ranking_admissible",
    "error_type",
    "error_message",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    *FORBIDDEN_GUARDRAILS,
]
VALIDATION_FAILURE_FIELDNAMES = ["workload_id", "error_type", "error_message"]
METADATA_MISSING_FIELDNAMES = ["workload_id", "missing_metadata_fields"]
METRIC_COMPLETENESS_FIELDNAMES = ["workload_id", "metric", "value"]
SUPPORT_AGGREGATE_FIELDNAMES = [
    "group_axis",
    "group_value",
    "support_policy_name",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "offtrack_count",
    "offtrack_rate",
    "obstacle_completed_count",
    "obstacle_completed_rate",
    "mean_return",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_max_off_track_overshoot",
    "dominant_failure_mode",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
SCENARIO_SUPPORT_FIELDNAMES = [
    *SCENARIO_METADATA_FIELDS,
    "episode_count",
    "support_label",
    "support_label_reason",
    "support_clear_policy_count",
    "support_mixed_policy_count",
    "support_blocked_policy_count",
    "metric_conflict_policy_count",
    "best_support_success_count",
    "best_support_policy_name",
    "aeb_success_count",
    "aeb_collision_count",
    "aeb_offtrack_count",
    "aes_success_count",
    "aes_collision_count",
    "aes_offtrack_count",
    "envelope_aes_success_count",
    "envelope_aes_collision_count",
    "envelope_aes_offtrack_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
ROLE_SUPPORT_FIELDNAMES = [
    "role_family",
    "scenario_count",
    "support_clear_count",
    "support_mixed_count",
    "support_blocked_count",
    "metric_conflict_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]

RolloutFunction = Callable[[Mapping[str, Any], Mapping[str, Any], str, int], Mapping[str, Any]]


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


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _mean(values: Iterable[Any]) -> float | None:
    finite = [_float_metric(value) for value in values if _finite(value)]
    if not finite:
        return None
    return float(np.mean(finite))


def _min(values: Iterable[Any]) -> float | None:
    finite = [_float_metric(value) for value in values if _finite(value)]
    if not finite:
        return None
    return float(np.min(finite))


def _episode_success(row: Mapping[str, Any]) -> bool:
    return role_success(row)


def _failure_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        bucket = str(row.get("outcome_bucket", ""))
        termination_reason = str(row.get("termination_reason", ""))
        if bucket == "success_obstacle_pass" or _episode_success(row):
            counts["success"] += 1
        elif bucket == "collision_failure" or role_is_collision(row):
            counts["collision"] += 1
        elif bucket == "off_track_noncollision_noncompletion" or role_is_offtrack(row):
            counts["offtrack"] += 1
        elif bucket == "max_steps_noncompletion" or _bool(row.get("truncated")):
            counts["max_step_noncompletion"] += 1
        else:
            counts["other_failure"] += 1
        if _bool(row.get("obstacle_completed")):
            counts["obstacle_completed"] += 1
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


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_scenario_specs(path: Path | str = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    payload = read_json(path)
    specs = payload.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return [dict(spec) for spec in specs]


def support_policy_metadata(policy_name: str) -> dict[str, Any]:
    if policy_name not in SUPPORT_POLICY_METADATA:
        raise ValueError(f"unsupported support policy: {policy_name}")
    return {
        "support_policy_name": policy_name,
        **SUPPORT_POLICY_METADATA[policy_name],
        "diagnostic_only": True,
        "ranking_admissible": False,
    }


def eval_seed_for_cell(*, eval_seed_base: int, scenario_index: int, support_policy_index: int, seed_repeat_index: int) -> int:
    return int(eval_seed_base) + int(scenario_index) * 1000 + int(support_policy_index) * 100 + int(seed_repeat_index)


def workload_rows(
    *,
    scenario_specs: Sequence[Mapping[str, Any]],
    support_policies: Sequence[str],
    seed_repeats: int,
    eval_seed_base: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_index, scenario in enumerate(scenario_specs):
        scenario_id = str(scenario.get("scenario_spec_id", f"scenario_{scenario_index:03d}"))
        for support_policy_index, policy_name in enumerate(support_policies):
            for seed_repeat_index in range(int(seed_repeats)):
                eval_seed = eval_seed_for_cell(
                    eval_seed_base=int(eval_seed_base),
                    scenario_index=int(scenario_index),
                    support_policy_index=int(support_policy_index),
                    seed_repeat_index=int(seed_repeat_index),
                )
                rows.append(
                    {
                        "workload_id": f"{scenario_id}::{policy_name}::repeat_{seed_repeat_index}",
                        "scenario_index": int(scenario_index),
                        "support_policy_index": int(support_policy_index),
                        "seed_repeat_index": int(seed_repeat_index),
                        "eval_seed": int(eval_seed),
                        "support_policy_name": policy_name,
                    }
                )
    return rows


def _scenario_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: spec.get(field, "") for field in SCENARIO_METADATA_FIELDS}


def _workload_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "workload_id": row.get("workload_id", ""),
        "scenario_index": row.get("scenario_index", ""),
        "support_policy_index": row.get("support_policy_index", ""),
        "seed_repeat_index": row.get("seed_repeat_index", ""),
        "eval_seed": row.get("eval_seed", ""),
    }


def validation_failure_rows(
    *,
    scenario_specs: Sequence[Mapping[str, Any]],
    support_policies: Sequence[str],
    workload: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    workload_ids = Counter(str(row.get("workload_id", "")) for row in workload)
    for workload_id, count in sorted(workload_ids.items()):
        if workload_id and count > 1:
            failures.append({"workload_id": workload_id, "error_type": "duplicate_workload_id", "error_message": str(count)})
    for policy_name in support_policies:
        if policy_name not in SUPPORT_POLICY_METADATA:
            failures.append({"workload_id": policy_name, "error_type": "unsupported_support_policy", "error_message": policy_name})
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
    return failures


def metadata_missing_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        missing = [
            field
            for field in (
                "workload_id",
                "support_policy_name",
                *SCENARIO_METADATA_FIELDS,
            )
            if not str(row.get(field, "")).strip()
        ]
        if missing:
            output.append({"workload_id": str(row.get("workload_id", "")), "missing_metadata_fields": ";".join(missing)})
    return output


def metric_completeness_failure_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in rows:
        for metric in (
            "success",
            "collision",
            "min_clearance_margin",
            "return",
            "steps",
            "action_rate_mean",
            "high_sideslip_fraction",
        ):
            if metric in {"success", "collision"}:
                continue
            if not _finite(row.get(metric)):
                failures.append({"workload_id": str(row.get("workload_id", "")), "metric": metric, "value": row.get(metric, "")})
    return failures


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "scenario_task_family_support_policy_feasibility_calibration_completed",
            "admissible": True,
            "reason": "episode rows are diagnostic support-policy rollout artifacts when the runner completes",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "support policies are not deployable candidates and must not be ranked",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2313 does not select a support policy or controller family",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2313 is public diagnostic support calibration, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2313 does not execute finite-window or GRU checkpoint comparison",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2313 runs no wrong-history, reset-hidden, or zero-history interventions",
        },
    ]


def support_episode_row(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    support_policy_name: str,
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = dict(rollout_metrics)
    reset_label = str(row.get("obstacle_label", row.get("sampled_obstacle_label", "")))
    spec_label = str(scenario_spec.get("sampled_obstacle_label", ""))
    row.update(_workload_metadata(workload_row))
    row.update(_scenario_metadata(scenario_spec))
    row.update(support_policy_metadata(support_policy_name))
    success_annotation = annotate_role_success(row)
    row.update(
        {
            "eval_seed": int(eval_seed),
            "raw_success": success_annotation["raw_success"],
            "role_success": success_annotation["role_success"],
            "role_success_reason": success_annotation["role_success_reason"],
            "role_success_outcome_bucket": success_annotation["role_success_outcome_bucket"],
            "success": success_annotation["success"],
            "reset_sampled_obstacle_label": reset_label,
            "sampled_label_matches_spec": reset_label == spec_label,
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


def support_failure_row(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    support_policy_name: str,
    eval_seed: int,
    error: BaseException,
) -> dict[str, Any]:
    return {
        **_workload_metadata(workload_row),
        **_scenario_metadata(scenario_spec),
        **support_policy_metadata(support_policy_name),
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
    scenario_spec: Mapping[str, Any],
    support_policy_name: str,
    eval_seed: int,
) -> dict[str, Any]:
    env_config = build_env_config(dict(scenario_spec["env_config"]))
    env = AutoDriftEnv(env_config)
    policy = make_policy(support_policy_name, env, seed=int(eval_seed))
    try:
        return dict(run_episode_with_policy(env, policy, support_policy_name, int(eval_seed)))
    finally:
        env.close()


def aggregate_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_axis: str,
    group_value: str,
    support_policy_name: str,
) -> dict[str, Any]:
    counts = _failure_counts(rows)
    total = len(rows)
    return {
        "group_axis": group_axis,
        "group_value": group_value,
        "support_policy_name": support_policy_name,
        "episode_count": total,
        "success_count": counts.get("success", 0),
        "success_rate": _rate(counts.get("success", 0), total),
        "collision_count": counts.get("collision", 0),
        "collision_rate": _rate(counts.get("collision", 0), total),
        "offtrack_count": counts.get("offtrack", 0),
        "offtrack_rate": _rate(counts.get("offtrack", 0), total),
        "obstacle_completed_count": counts.get("obstacle_completed", 0),
        "obstacle_completed_rate": _rate(counts.get("obstacle_completed", 0), total),
        "mean_return": _mean([row.get("return") for row in rows]),
        "mean_min_clearance_margin": _mean([row.get("min_clearance_margin") for row in rows]),
        "min_min_clearance_margin": _min([row.get("min_clearance_margin") for row in rows]),
        "mean_max_off_track_overshoot": _mean([row.get("max_off_track_overshoot") for row in rows]),
        "dominant_failure_mode": _dominant_failure_mode(rows),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def support_aggregate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        for axis in (
            "global",
            "scenario_spec_id",
            "role_family",
            "sampled_obstacle_label",
            "obstacle_longitudinal_timing_bucket",
            "obstacle_lateral_offset_bucket",
            "hidden_dynamics_bucket",
        ):
            value = "all" if axis == "global" else str(row.get(axis, ""))
            grouped[(axis, value, str(row.get("support_policy_name", "")))].append(row)
    for (axis, value, policy_name), group in sorted(grouped.items()):
        output.append(aggregate_row(group, group_axis=axis, group_value=value, support_policy_name=policy_name))
    return output


def _policy_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    by_policy: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_policy[str(row.get("support_policy_name", ""))].append(row)
    for policy_name, group in by_policy.items():
        counts = _failure_counts(group)
        result[policy_name] = {
            "success": counts.get("success", 0),
            "collision": counts.get("collision", 0),
            "offtrack": counts.get("offtrack", 0),
            "obstacle_completed": counts.get("obstacle_completed", 0),
            "max_step_noncompletion": counts.get("max_step_noncompletion", 0),
            "other_failure": counts.get("other_failure", 0),
        }
    return result


def _policy_support_label(counts: Mapping[str, int], *, seed_repeats: int) -> str:
    success = int(counts.get("success", 0))
    collision = int(counts.get("collision", 0))
    offtrack = int(counts.get("offtrack", 0))
    obstacle_completed = int(counts.get("obstacle_completed", 0))
    max_step_or_other = int(counts.get("max_step_noncompletion", 0)) + int(counts.get("other_failure", 0))
    if success >= max(1, int(np.ceil(0.6 * seed_repeats))) and collision <= max(0, seed_repeats // 2):
        return "support_clear"
    if obstacle_completed >= max(1, int(np.ceil(0.6 * seed_repeats))) and success < max(1, int(np.ceil(0.6 * seed_repeats))):
        return "metric_conflict"
    if success == 0 and collision == 0 and offtrack == 0 and max_step_or_other > 0:
        return "metric_conflict"
    if success > 0 or (collision > 0 and offtrack > 0):
        return "support_mixed"
    return "support_blocked"


def scenario_support_label_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    scenario_specs: Sequence[Mapping[str, Any]],
    seed_repeats: int,
) -> list[dict[str, Any]]:
    rows_by_scenario: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_scenario[str(row.get("scenario_spec_id", ""))].append(row)
    specs_by_id = {str(spec.get("scenario_spec_id", "")): spec for spec in scenario_specs}
    output: list[dict[str, Any]] = []
    for scenario_id in sorted(specs_by_id):
        group = rows_by_scenario.get(scenario_id, [])
        counts_by_policy = _policy_counts(group)
        labels = {
            policy_name: _policy_support_label(counts_by_policy.get(policy_name, {}), seed_repeats=int(seed_repeats))
            for policy_name in DEFAULT_SUPPORT_POLICIES
        }
        label_counts = Counter(labels.values())
        if label_counts.get("support_clear", 0):
            support_label = "support_clear"
            reason = "at least one support policy reaches the clear threshold"
        elif label_counts.get("metric_conflict", 0):
            support_label = "metric_conflict"
            reason = "support policy obstacle completion conflicts with terminal metric"
        elif label_counts.get("support_mixed", 0):
            support_label = "support_mixed"
            reason = "support policies have partial success or mixed collision/offtrack failures"
        else:
            support_label = "support_blocked"
            reason = "no support policy produces successful obstacle passage"
        best_policy = ""
        best_success = -1
        for policy_name, counts in sorted(counts_by_policy.items()):
            success = int(counts.get("success", 0))
            if success > best_success:
                best_success = success
                best_policy = policy_name
        row = {
            **_scenario_metadata(specs_by_id[scenario_id]),
            "episode_count": len(group),
            "support_label": support_label,
            "support_label_reason": reason,
            "support_clear_policy_count": label_counts.get("support_clear", 0),
            "support_mixed_policy_count": label_counts.get("support_mixed", 0),
            "support_blocked_policy_count": label_counts.get("support_blocked", 0),
            "metric_conflict_policy_count": label_counts.get("metric_conflict", 0),
            "best_support_success_count": max(best_success, 0),
            "best_support_policy_name": best_policy,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
        for policy_name in DEFAULT_SUPPORT_POLICIES:
            counts = counts_by_policy.get(policy_name, {})
            row[f"{policy_name}_success_count"] = int(counts.get("success", 0))
            row[f"{policy_name}_collision_count"] = int(counts.get("collision", 0))
            row[f"{policy_name}_offtrack_count"] = int(counts.get("offtrack", 0))
        output.append(row)
    return output


def role_support_summary_rows(scenario_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in scenario_rows:
        grouped[str(row.get("role_family", ""))].append(row)
    output: list[dict[str, Any]] = []
    for role, group in sorted(grouped.items()):
        counts = Counter(str(row.get("support_label", "")) for row in group)
        output.append(
            {
                "role_family": role,
                "scenario_count": len(group),
                "support_clear_count": counts.get("support_clear", 0),
                "support_mixed_count": counts.get("support_mixed", 0),
                "support_blocked_count": counts.get("support_blocked", 0),
                "metric_conflict_count": counts.get("metric_conflict", 0),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def finalize_outputs(
    *,
    output_dir: Path,
    scenario_specs: Sequence[Mapping[str, Any]],
    support_policies: Sequence[str],
    seed_repeats: int,
    target_scenario_spec_count: int,
    target_support_policy_count: int,
    target_episode_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    validation_failures = [dict(row) for row in read_csv_rows(output_dir / "validation_failure_rows.csv")]
    missing_rows = metadata_missing_rows(episode_rows)
    metric_failures = metric_completeness_failure_rows(episode_rows)
    aggregates = support_aggregate_rows(episode_rows)
    scenario_labels = scenario_support_label_rows(
        episode_rows,
        scenario_specs=scenario_specs,
        seed_repeats=int(seed_repeats),
    )
    role_summary = role_support_summary_rows(scenario_labels)
    write_csv_rows(output_dir / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_failures, fieldnames=METRIC_COMPLETENESS_FIELDNAMES)
    write_csv_rows(output_dir / "support_aggregate_rows.csv", aggregates, fieldnames=SUPPORT_AGGREGATE_FIELDNAMES)
    write_csv_rows(output_dir / "scenario_support_labels.csv", scenario_labels, fieldnames=SCENARIO_SUPPORT_FIELDNAMES)
    write_csv_rows(output_dir / "role_support_summary.csv", role_summary, fieldnames=ROLE_SUPPORT_FIELDNAMES)
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    scenario_spec_count = len({str(row.get("scenario_spec_id", "")) for row in episode_rows})
    support_policy_count = len({str(row.get("support_policy_name", "")) for row in episode_rows})
    seed_repeat_count = len({str(row.get("seed_repeat_index", "")) for row in episode_rows})
    ranking_admissible_count = sum(role_bool_value(row.get("ranking_admissible"), default=False) for row in episode_rows)
    winner_selected_count = sum(role_bool_value(row.get("winner_selected"), default=False) for row in episode_rows)
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and len(validation_failures) == 0
        and scenario_spec_count == int(target_scenario_spec_count)
        and support_policy_count == int(target_support_policy_count)
        and seed_repeat_count == int(seed_repeats)
        and not missing_rows
        and not metric_failures
        and guardrail_violation_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
    )
    global_counts = _failure_counts(episode_rows)
    support_label_counts = _count_by(scenario_labels, "support_label")
    artifacts = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "validation_failure_rows": str(output_dir / "validation_failure_rows.csv"),
        "metadata_missing_rows": str(output_dir / "metadata_missing_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        "support_aggregate_rows": str(output_dir / "support_aggregate_rows.csv"),
        "scenario_support_labels": str(output_dir / "scenario_support_labels.csv"),
        "role_support_summary": str(output_dir / "role_support_summary.csv"),
        "claim_boundary": str(output_dir / "claim_boundary.csv"),
        "run_state": str(output_dir / "run_state.json"),
    }
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_feasibility_calibration_pass"
            if passes
            else "current_sim_scenario_task_family_feasibility_calibration_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "failure_count": len(failure_rows),
        "validation_failure_count": len(validation_failures),
        "scenario_spec_count": scenario_spec_count,
        "target_scenario_spec_count": int(target_scenario_spec_count),
        "support_policy_count": support_policy_count,
        "target_support_policy_count": int(target_support_policy_count),
        "seed_repeat_count": seed_repeat_count,
        "target_seed_repeat_count": int(seed_repeats),
        "metadata_missing_count": len(missing_rows),
        "metric_completeness_failure_count": len(metric_failures),
        "ranking_admissible_count": int(ranking_admissible_count),
        "winner_selected_count": int(winner_selected_count),
        "role_family_counts": _count_by(episode_rows, "role_family"),
        "support_policy_counts": _count_by(episode_rows, "support_policy_name"),
        "support_label_counts": support_label_counts,
        "outcome_counts": _count_by(episode_rows, "outcome_bucket"),
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
        "global_success_count": global_counts.get("success", 0),
        "global_collision_count": global_counts.get("collision", 0),
        "global_offtrack_count": global_counts.get("offtrack", 0),
        "global_obstacle_completed_count": global_counts.get("obstacle_completed", 0),
        "global_success_rate": _rate(global_counts.get("success", 0), len(episode_rows)),
        "global_collision_rate": _rate(global_counts.get("collision", 0), len(episode_rows)),
        "global_offtrack_rate": _rate(global_counts.get("offtrack", 0), len(episode_rows)),
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
        "diagnostic_only": True,
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


def run_feasibility_calibration(
    *,
    config_path: Path | str = DEFAULT_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    support_policies: Sequence[str] = DEFAULT_SUPPORT_POLICIES,
    seed_repeats: int = DEFAULT_SEED_REPEATS,
    target_scenario_spec_count: int = TARGET_SCENARIO_SPEC_COUNT,
    target_support_policy_count: int = TARGET_SUPPORT_POLICY_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scenario_specs = load_scenario_specs(config_path)
    support_policy_names = tuple(str(policy) for policy in support_policies)
    workload = workload_rows(
        scenario_specs=scenario_specs,
        support_policies=support_policy_names,
        seed_repeats=int(seed_repeats),
        eval_seed_base=int(eval_seed_base),
    )
    validation_failures = validation_failure_rows(
        scenario_specs=scenario_specs,
        support_policies=support_policy_names,
        workload=workload,
    )
    if validation_failures:
        write_csv_rows(output / "validation_failure_rows.csv", validation_failures, fieldnames=VALIDATION_FAILURE_FIELDNAMES)
        write_csv_rows(output / "episode_rows.csv", [], fieldnames=EPISODE_FIELDNAMES)
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
        return finalize_outputs(
            output_dir=output,
            scenario_specs=scenario_specs,
            support_policies=support_policy_names,
            seed_repeats=int(seed_repeats),
            target_scenario_spec_count=int(target_scenario_spec_count),
            target_support_policy_count=int(target_support_policy_count),
            target_episode_count=int(target_episode_count),
            next_blocker=str(next_blocker),
        )

    episode_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for row in workload:
        scenario = scenario_specs[int(row["scenario_index"])]
        policy_name = str(row["support_policy_name"])
        eval_seed = int(row["eval_seed"])
        try:
            if rollout_fn is None:
                rollout_metrics = _real_rollout_metrics(
                    scenario_spec=scenario,
                    support_policy_name=policy_name,
                    eval_seed=int(eval_seed),
                )
            else:
                rollout_metrics = dict(rollout_fn(row, scenario, policy_name, int(eval_seed)))
            episode_rows.append(
                support_episode_row(
                    workload_row=row,
                    scenario_spec=scenario,
                    support_policy_name=policy_name,
                    rollout_metrics=rollout_metrics,
                    eval_seed=int(eval_seed),
                )
            )
        except Exception as exc:  # noqa: BLE001 - row failures must be preserved.
            failure_rows.append(
                support_failure_row(
                    workload_row=row,
                    scenario_spec=scenario,
                    support_policy_name=policy_name,
                    eval_seed=int(eval_seed),
                    error=exc,
                )
            )

    write_csv_rows(output / "validation_failure_rows.csv", [], fieldnames=VALIDATION_FAILURE_FIELDNAMES)
    write_csv_rows(output / "episode_rows.csv", episode_rows, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(output / "failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    return finalize_outputs(
        output_dir=output,
        scenario_specs=scenario_specs,
        support_policies=support_policy_names,
        seed_repeats=int(seed_repeats),
        target_scenario_spec_count=int(target_scenario_spec_count),
        target_support_policy_count=int(target_support_policy_count),
        target_episode_count=int(target_episode_count),
        next_blocker=str(next_blocker),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--support-policies", nargs="+", default=list(DEFAULT_SUPPORT_POLICIES))
    parser.add_argument("--seed-repeats", type=int, default=DEFAULT_SEED_REPEATS)
    parser.add_argument("--target-scenario-spec-count", type=int, default=TARGET_SCENARIO_SPEC_COUNT)
    parser.add_argument("--target-support-policy-count", type=int, default=TARGET_SUPPORT_POLICY_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_feasibility_calibration(
        config_path=args.config,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        support_policies=tuple(str(policy) for policy in args.support_policies),
        seed_repeats=int(args.seed_repeats),
        target_scenario_spec_count=int(args.target_scenario_spec_count),
        target_support_policy_count=int(args.target_support_policy_count),
        target_episode_count=int(args.target_episode_count),
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
