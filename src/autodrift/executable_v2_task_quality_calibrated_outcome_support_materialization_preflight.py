"""No-reset materialization preflight for calibrated outcome-support repair sources."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.executable_v2_support_first_source_mining import required_label_for_role
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


DEFAULT_SOURCE_ROWS = Path(
    "runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv"
)
DEFAULT_ACCEPTED_CELLS = Path(
    "runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight")
DEFAULT_NEXT_BLOCKER = "m1987-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-result-audit"
PROTOCOL_NAME = "task_quality_calibrated_outcome_support_materialization_preflight_v0"
AXIS_SELECTED_QUOTAS = {
    "offtrack_anchor_relief": 24,
    "offtrack_boundary_relief_extension": 16,
    "success_support_expansion": 20,
    "collision_mitigation_relief": 12,
    "mitigation_metric_isolation": 8,
}
DIAGNOSTIC_AXIS = "mitigation_metric_isolation"
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
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
)
SPEC_CSV_FIELDS = [
    "task_source_id",
    "candidate_source_id",
    "repair_candidate_id",
    "repair_axis",
    "repair_source_kind",
    "source_role_semantics",
    "feasibility_tier_id",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "source_split",
    "sampled_obstacle_label",
    "speed_ref",
    "mu",
    "friction_step_enabled",
    "friction_step_at",
    "obstacle_distance",
    "obstacle_half_width",
    "post_obstacle_track_width",
    "base_geometry_source",
    "representative_cell_rule",
    "diagnostic_only_no_ranking_claim",
    "contract_violation_count",
    "history_length_is_one",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
]
WORKLOAD_FIELDS = [
    "workload_id",
    "task_source_id",
    "candidate_source_id",
    "repair_candidate_id",
    "repair_axis",
    "repair_source_kind",
    "source_role_semantics",
    "feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "diagnostic_only_no_ranking_claim",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
]
FAILURE_FIELDS = ["candidate_source_id", "repair_axis", "failure_reason", "error_type", "error_message"]
AGGREGATE_FIELDS = ["aggregate_key", "selected_source_count", "diagnostic_only_no_ranking_claim_count"]
ROLE_SURFACE_FIELDS = [
    "repair_axis",
    "source_role_semantics",
    "feasibility_tier_id",
    "normalized_surface_variant",
    "selected_source_count",
]
CLAIM_BOUNDARY_FIELDS = ["claim", "supported", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _source_id(row: Mapping[str, Any]) -> str:
    return str(row.get("candidate_source_id", ""))


def _source_supported(row: Mapping[str, Any]) -> bool:
    return str(row.get("source_support_status", "")) == "supported"


def eligible_source(row: Mapping[str, Any]) -> bool:
    return (
        _source_supported(row)
        and not _bool(row.get("labels_enter_actor_input"))
        and not _bool(row.get("v2_ranking_admissible_by_default"))
        and not _bool(row.get("profile_specific_tuning"))
    )


def source_sort_key(row: Mapping[str, Any]) -> tuple[int, str, str, str, str]:
    split_rank = 0 if str(row.get("source_split", "")) == "public_gate" else 1
    return (
        split_rank,
        str(row.get("source_role_semantics", "")),
        str(row.get("normalized_surface_variant", "")),
        str(row.get("sampled_obstacle_label", "")),
        _source_id(row),
    )


def select_sources(rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible = [dict(row) for row in rows if eligible_source(row)]
    selected: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for axis, quota in AXIS_SELECTED_QUOTAS.items():
        axis_rows = sorted((row for row in eligible if str(row.get("repair_axis", "")) == axis), key=source_sort_key)
        if len(axis_rows) < quota:
            failures.append(
                {
                    "candidate_source_id": "",
                    "repair_axis": axis,
                    "failure_reason": "insufficient_supported_sources_for_axis_quota",
                    "error_type": "",
                    "error_message": f"required {quota}, found {len(axis_rows)}",
                }
            )
            selected.extend(axis_rows)
            continue
        selected.extend(axis_rows[:quota])
    return selected, failures


def _accepted_cells_by_source(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not _bool(row.get("accepted")):
            continue
        grouped[_source_id(row)].append(dict(row))
    return grouped


def representative_cell_sort_key(role: str, row: Mapping[str, Any]) -> tuple[float, float, float, str]:
    threshold = _float(row.get("threshold_score"))
    distance = _float(row.get("obstacle_distance"))
    half_width = _float(row.get("obstacle_half_width"))
    source = _source_id(row)
    if role == ROLE_STABLE_AEB:
        return (-threshold, -distance, half_width, source)
    if role in {ROLE_STABLE_AES, ROLE_DRIFT_REQUIRED}:
        return (threshold, distance, -half_width, source)
    if role == ROLE_UNAVOIDABLE:
        return (distance, -half_width, threshold, source)
    return (threshold, distance, -half_width, source)


def representative_cell_for_source(
    source: Mapping[str, Any],
    accepted_cells: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str]:
    source_id = _source_id(source)
    cells = list(accepted_cells.get(source_id, []))
    if not cells:
        return None, "missing_accepted_cell"
    role = str(source.get("source_role_semantics", ""))
    selected = sorted(cells, key=lambda row: representative_cell_sort_key(role, row))[0]
    if role == ROLE_STABLE_AEB:
        rule = "stable_aeb_max_threshold_then_farther_distance"
    elif role == ROLE_STABLE_AES:
        rule = "stable_aes_boundary_min_threshold_then_closer_wider"
    elif role == ROLE_DRIFT_REQUIRED:
        rule = "drift_required_boundary_min_threshold_then_closer_wider"
    elif role == ROLE_UNAVOIDABLE:
        rule = "unavoidable_mitigation_closer_wider_then_threshold"
    else:
        rule = "default_min_threshold"
    return dict(selected), rule


def env_config_for_materialized_source(
    *,
    source: Mapping[str, Any],
    cell: Mapping[str, Any],
) -> dict[str, Any]:
    role = str(source.get("source_role_semantics", ""))
    speed = _float(source.get("speed_ref", cell.get("speed_ref")), 18.0)
    mu = _float(source.get("mu", cell.get("mu")), 0.40)
    label = str(cell.get("label", required_label_for_role(role)))
    friction_enabled = _bool(source.get("friction_step_enabled"))
    friction_step_at = _int(cell.get("friction_step_at", source.get("friction_step_at")), 20)
    track_width = _float(source.get("post_obstacle_track_width"), 6.0)
    env_data = {
        "dt": 0.05,
        "max_steps": 800,
        "track_kind": "circle",
        "track_radius": 18.0,
        "track_width": track_width,
        "speed_range": [speed, speed],
        "friction_limited_speed": False,
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "zero",
        "wheel_observation_mode": "none",
        "randomization": {
            "mu_range": [mu, mu],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "friction_step": {
            "enabled": friction_enabled,
            "step_range": [friction_step_at, friction_step_at],
            "mu_range": [mu, mu],
            "resample_speed_ref": False,
        },
        "obstacle": {
            "enabled": True,
            "allowed_labels": [label],
            "require_aeb_infeasible": role != ROLE_STABLE_AEB,
            "distance_range": [_float(cell.get("obstacle_distance")), _float(cell.get("obstacle_distance"))],
            "half_width_range": [_float(cell.get("obstacle_half_width")), _float(cell.get("obstacle_half_width"))],
            "ego_half_width": 0.90,
            "safety_margin": 0.30,
            "brake_mu_fraction": 0.90,
            "conventional_lateral_mu_fraction": 0.42,
            "drift_lateral_mu_fraction": 0.85,
            "min_time_after_friction_step": 0.30 if friction_enabled else 0.0,
            "max_sample_attempts": 1,
            "finish_on_pass": True,
            "pass_reward": 10.0,
        },
    }
    env_config = build_env_config(env_data)
    assert_human_view_env_contract(env_config)
    return env_config_to_dict(env_config)


def _contract_checks(env_config: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "history_length_is_one": int(env_config.get("history_length", 0)) == 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
    }


def materialize_executable_spec(
    *,
    source: Mapping[str, Any],
    cell: Mapping[str, Any],
    representative_cell_rule: str,
    index: int,
) -> dict[str, Any]:
    env_config = env_config_for_materialized_source(source=source, cell=cell)
    checks = _contract_checks(env_config)
    source_id = _source_id(source)
    repair_axis = str(source.get("repair_axis", ""))
    diagnostic_only = repair_axis == DIAGNOSTIC_AXIS
    return {
        "task_source_id": f"tqcos_exec_v0_{index:04d}_{source_id}",
        "candidate_source_id": source_id,
        "repair_candidate_id": str(source.get("repair_candidate_id", "")),
        "repair_axis": repair_axis,
        "repair_source_kind": str(source.get("repair_source_kind", "")),
        "repair_source_family": str(source.get("repair_source_family", "")),
        "source_role_semantics": str(source.get("source_role_semantics", "")),
        "feasibility_tier_id": str(source.get("feasibility_tier_id", "")),
        "parent_feasibility_tier_id": str(source.get("parent_feasibility_tier_id", "")),
        "normalized_surface_variant": str(source.get("normalized_surface_variant", "")),
        "source_split": str(source.get("source_split", "")),
        "sampled_obstacle_label": str(cell.get("label", source.get("sampled_obstacle_label", ""))),
        "speed_ref": _float(source.get("speed_ref")),
        "mu": _float(source.get("mu")),
        "friction_step_enabled": _bool(source.get("friction_step_enabled")),
        "friction_step_at": _int(cell.get("friction_step_at", source.get("friction_step_at")), 0),
        "obstacle_distance": _float(cell.get("obstacle_distance")),
        "obstacle_half_width": _float(cell.get("obstacle_half_width")),
        "threshold_score": _float(cell.get("threshold_score")),
        "time_to_obstacle": _float(cell.get("time_to_obstacle")),
        "time_after_friction_step": _float(cell.get("time_after_friction_step")),
        "post_obstacle_track_width": _float(source.get("post_obstacle_track_width")),
        "base_geometry_source": str(source.get("base_geometry_source", "")),
        "representative_cell_rule": representative_cell_rule,
        "diagnostic_only_no_ranking_claim": diagnostic_only,
        "source_support_status": str(source.get("source_support_status", "")),
        "contract_checks": checks,
        "contract_violation_count": int(sum(1 for value in checks.values() if not bool(value))),
        "diagnostic_only_source_handling": "not_ranking_row" if diagnostic_only else "",
        "env_config": env_config,
    }


def executable_spec_csv_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    checks = dict(spec.get("contract_checks", {}))
    return {field: spec.get(field, checks.get(field, "")) for field in SPEC_CSV_FIELDS}


def planned_workload_rows(
    executable_specs: list[Mapping[str, Any]],
    *,
    profile_run_dir: Path | str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profile_rows = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in executable_specs:
        for profile in profile_rows:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "candidate_source_id": spec["candidate_source_id"],
                    "repair_candidate_id": spec["repair_candidate_id"],
                    "repair_axis": spec["repair_axis"],
                    "repair_source_kind": spec["repair_source_kind"],
                    "source_role_semantics": spec["source_role_semantics"],
                    "feasibility_tier_id": spec["feasibility_tier_id"],
                    "normalized_surface_variant": spec["normalized_surface_variant"],
                    "sampled_obstacle_label": spec["sampled_obstacle_label"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "config_exists": profile["config_exists"],
                    "checkpoint_exists": profile["checkpoint_exists"],
                    "diagnostic_only_no_ranking_claim": spec["diagnostic_only_no_ranking_claim"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                }
            )
    return rows, profile_rows


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(str(value) for value in values)
    return sum(1 for value, count in counts.items() if value and count > 1)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _aggregate_axis_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("repair_axis", ""))].append(row)
    return [
        {
            "aggregate_key": key,
            "selected_source_count": len(items),
            "diagnostic_only_no_ranking_claim_count": sum(_bool(row.get("diagnostic_only_no_ranking_claim")) for row in items),
        }
        for key, items in sorted(grouped.items())
    ]


def _role_surface_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row.get("repair_axis", "")),
                str(row.get("source_role_semantics", "")),
                str(row.get("feasibility_tier_id", "")),
                str(row.get("normalized_surface_variant", "")),
            )
        ].append(row)
    return [
        {
            "repair_axis": axis,
            "source_role_semantics": role,
            "feasibility_tier_id": tier,
            "normalized_surface_variant": surface,
            "selected_source_count": len(items),
        }
        for (axis, role, tier, surface), items in sorted(grouped.items())
    ]


def _claim_boundary_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    passed = summary.get("result_class") == "task_quality_calibrated_outcome_support_materialization_preflight_pass"
    return [
        {
            "claim": "outcome_support_materialization_preflight_artifact",
            "supported": passed,
            "reason": "M1986 creates no-reset executable specs and planned workload artifacts",
        },
        {
            "claim": "reset_validity",
            "supported": False,
            "reason": "M1986 does not run environment reset",
        },
        {
            "claim": "measured_execution_success",
            "supported": False,
            "reason": "M1986 does not run rollout or measured execution",
        },
        {
            "claim": "controller_family_ranking",
            "supported": False,
            "reason": "M1986 writes a planned workload only",
        },
        {
            "claim": "paper_level_evidence",
            "supported": False,
            "reason": "M1986 is a no-reset preflight milestone",
        },
        {
            "claim": "level3_self_identification",
            "supported": False,
            "reason": "M1986 does not test history necessity",
        },
    ]


def run_outcome_support_materialization_preflight(
    *,
    source_rows_path: Path | str = DEFAULT_SOURCE_ROWS,
    accepted_cells_path: Path | str = DEFAULT_ACCEPTED_CELLS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_rows = [dict(row) for row in read_csv_rows(source_rows_path)]
    accepted_rows = [dict(row) for row in read_csv_rows(accepted_cells_path)]
    accepted_by_source = _accepted_cells_by_source(accepted_rows)
    selected_sources, selection_failures = select_sources(source_rows)

    executable_specs: list[dict[str, Any]] = []
    failures = list(selection_failures)
    selected_cells: list[dict[str, Any]] = []
    for index, source in enumerate(selected_sources):
        try:
            cell, rule = representative_cell_for_source(source, accepted_by_source)
            if cell is None:
                failures.append(
                    {
                        "candidate_source_id": _source_id(source),
                        "repair_axis": str(source.get("repair_axis", "")),
                        "failure_reason": rule,
                        "error_type": "",
                        "error_message": "",
                    }
                )
                continue
            selected_cells.append({**cell, "representative_cell_rule": rule, "repair_axis": source.get("repair_axis", "")})
            executable_specs.append(
                materialize_executable_spec(source=source, cell=cell, representative_cell_rule=rule, index=index)
            )
        except Exception as exc:  # noqa: BLE001 - preflight must record row-level blockers.
            failures.append(
                {
                    "candidate_source_id": _source_id(source),
                    "repair_axis": str(source.get("repair_axis", "")),
                    "failure_reason": "materialization_exception",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )

    workload_rows, profile_rows = planned_workload_rows(executable_specs, profile_run_dir=profile_run_dir)
    forbidden_key_hits = forbidden_key_violations(executable_specs)
    contract_violation_count = sum(_int(spec.get("contract_violation_count")) for spec in executable_specs)
    missing_profile_artifact_count = sum(
        1 for row in profile_rows if not bool(row["config_exists"]) or not bool(row["checkpoint_exists"])
    )
    duplicate_task_source_id_count = _duplicate_count(str(spec.get("task_source_id", "")) for spec in executable_specs)
    duplicate_workload_key_count = _duplicate_count(str(row.get("workload_id", "")) for row in workload_rows)
    selected_unsupported_source_count = sum(1 for row in selected_sources if not _source_supported(row))
    selected_axis_counts = _count_by(executable_specs, "repair_axis")
    selected_quota_pass = selected_axis_counts == AXIS_SELECTED_QUOTAS
    diagnostic_only_count = sum(_bool(spec.get("diagnostic_only_no_ranking_claim")) for spec in executable_specs)
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    profile_count = len({row["profile_name"] for row in workload_rows})
    passes = (
        len(selected_sources) == 80
        and len(executable_specs) == 80
        and len(workload_rows) == 80 * len(EXPECTED_PROFILE_NAMES)
        and profile_count == len(EXPECTED_PROFILE_NAMES)
        and selected_unsupported_source_count == 0
        and len(failures) == 0
        and duplicate_task_source_id_count == 0
        and duplicate_workload_key_count == 0
        and len(forbidden_key_hits) == 0
        and contract_violation_count == 0
        and missing_profile_artifact_count == 0
        and selected_quota_pass
        and diagnostic_only_count == AXIS_SELECTED_QUOTAS[DIAGNOSTIC_AXIS]
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "task_quality_calibrated_outcome_support_materialization_preflight_pass"
            if passes
            else "task_quality_calibrated_outcome_support_materialization_preflight_fail"
        ),
        "protocol_name": PROTOCOL_NAME,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_rows_path": str(source_rows_path),
        "accepted_cells_path": str(accepted_cells_path),
        "profile_run_dir": str(profile_run_dir),
        "input_source_row_count": len(source_rows),
        "input_accepted_cell_row_count": len(accepted_rows),
        "eligible_source_count": sum(eligible_source(row) for row in source_rows),
        "selected_source_count": len(selected_sources),
        "expected_selected_source_count": 80,
        "executable_task_spec_count": len(executable_specs),
        "expected_executable_task_spec_count": 80,
        "profile_count": profile_count,
        "expected_profile_count": len(EXPECTED_PROFILE_NAMES),
        "planned_workload_rows": len(workload_rows),
        "expected_planned_workload_rows": 80 * len(EXPECTED_PROFILE_NAMES),
        "selected_unsupported_source_count": selected_unsupported_source_count,
        "materialization_failure_count": len(failures),
        "duplicate_task_source_id_count": duplicate_task_source_id_count,
        "duplicate_workload_key_count": duplicate_workload_key_count,
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "contract_violation_count": contract_violation_count,
        "missing_profile_artifact_count": missing_profile_artifact_count,
        "repair_axis_selected_counts": selected_axis_counts,
        "target_repair_axis_selected_counts": AXIS_SELECTED_QUOTAS,
        "repair_axis_selected_quota_pass": selected_quota_pass,
        "diagnostic_only_no_ranking_claim_count": diagnostic_only_count,
        "labels_enter_actor_input_count": 0,
        "v2_ranking_admissible_by_default_count": 0,
        "profile_specific_tuning_count": 0,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "passes_public_gates": passes,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "selected_source_rows": str(output / "selected_source_rows.csv"),
            "selected_accepted_cells": str(output / "selected_accepted_cells.csv"),
            "executable_task_specs": str(output / "executable_task_specs.json"),
            "executable_task_specs_csv": str(output / "executable_task_specs.csv"),
            "planned_workload": str(output / "planned_workload.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "materialization_failures": str(output / "materialization_failures.csv"),
            "repair_axis_aggregate": str(output / "repair_axis_aggregate.csv"),
            "role_surface_aggregate": str(output / "role_surface_aggregate.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    executable_payload = {
        "protocol_name": PROTOCOL_NAME,
        "generated_at_utc": summary["generated_at_utc"],
        "claim_scope": "no-reset calibrated outcome-support executable materialization only",
        "source_rows_path": str(source_rows_path),
        "accepted_cells_path": str(accepted_cells_path),
        "executable_task_specs": executable_specs,
    }
    write_json(output / "executable_task_specs.json", executable_payload)
    write_csv_rows(output / "selected_source_rows.csv", selected_sources)
    write_csv_rows(output / "selected_accepted_cells.csv", selected_cells)
    write_csv_rows(output / "executable_task_specs.csv", [executable_spec_csv_row(spec) for spec in executable_specs], fieldnames=SPEC_CSV_FIELDS)
    write_csv_rows(output / "planned_workload.csv", workload_rows, fieldnames=WORKLOAD_FIELDS)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows)
    write_csv_rows(output / "materialization_failures.csv", failures, fieldnames=FAILURE_FIELDS)
    write_csv_rows(output / "repair_axis_aggregate.csv", _aggregate_axis_rows(executable_specs), fieldnames=AGGREGATE_FIELDS)
    write_csv_rows(output / "role_surface_aggregate.csv", _role_surface_rows(executable_specs), fieldnames=ROLE_SURFACE_FIELDS)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(summary), fieldnames=CLAIM_BOUNDARY_FIELDS)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-rows", type=Path, default=DEFAULT_SOURCE_ROWS)
    parser.add_argument("--accepted-cells", type=Path, default=DEFAULT_ACCEPTED_CELLS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_outcome_support_materialization_preflight(
        source_rows_path=args.source_rows,
        accepted_cells_path=args.accepted_cells,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_source_count={summary['selected_source_count']}")
    print(f"executable_task_spec_count={summary['executable_task_spec_count']}")
    print(f"planned_workload_rows={summary['planned_workload_rows']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
