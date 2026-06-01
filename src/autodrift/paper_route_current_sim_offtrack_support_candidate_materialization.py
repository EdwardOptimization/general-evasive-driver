"""No-rollout materialization for current-sim offtrack-support repair candidates."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract


DEFAULT_CANDIDATE_CONFIG = Path("configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json")
DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization")
DEFAULT_NEXT_BLOCKER = "m2195-paper-route-current-sim-offtrack-support-candidate-materialization-result-audit"
PROTOCOL = "paper_route_current_sim_offtrack_support_candidate_materialization_v0"
EXPECTED_CANDIDATE_COUNT = 288
EXPECTED_SPLITS = {"public_debug": 176, "public_gate": 112}
EXPECTED_AXIS_COUNTS = {
    "diagnostic_warmup_support_ladder": 32,
    "offtrack_saturation_relief": 96,
    "older_history_ambiguity_support_ladder": 64,
    "positive_support_preservation": 32,
    "terminal_boundary_support_ladder": 64,
}
PROFILE_ROWS = [
    {
        "profile_name": "L0_current_masked",
        "profile_level": "L0",
        "history_representation": "current_response",
        "history_window_steps": 0,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l0_current_masked_smoke.json",
    },
    {
        "profile_name": "L1_one_step",
        "profile_level": "L1",
        "history_representation": "one_step_command_response",
        "history_window_steps": 1,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l1_one_step_smoke.json",
    },
    {
        "profile_name": "L2_window_13",
        "profile_level": "L2",
        "history_representation": "explicit_finite_window",
        "history_window_steps": 13,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l2_window_13_smoke.json",
    },
    {
        "profile_name": "L2_window_25",
        "profile_level": "L2",
        "history_representation": "explicit_finite_window",
        "history_window_steps": 25,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l2_window_25_smoke.json",
    },
    {
        "profile_name": "L2_window_50",
        "profile_level": "L2",
        "history_representation": "explicit_finite_window",
        "history_window_steps": 50,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l2_window_50_smoke.json",
    },
    {
        "profile_name": "L2_window_100",
        "profile_level": "L2",
        "history_representation": "explicit_finite_window",
        "history_window_steps": 100,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l2_window_100_smoke.json",
    },
    {
        "profile_name": "L3_online_gru",
        "profile_level": "L3",
        "history_representation": "online_recurrent_hidden",
        "history_window_steps": 0,
        "reset_or_truncated_control": False,
        "profile_config_path": "configs/paper_route_profiles/m1190_l3_online_gru_smoke.json",
    },
    {
        "profile_name": "L3_reset_control",
        "profile_level": "L3",
        "history_representation": "online_recurrent_hidden",
        "history_window_steps": 0,
        "reset_or_truncated_control": True,
        "profile_config_path": "configs/paper_route_profiles/m1190_l3_reset_control_smoke.json",
    },
]
GUARDRAIL_FIELDS = (
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "environment_reset_started",
    "environment_rollout_started",
    "training_started",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
CLAIM_FIELDS = (
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
SPEC_FIELDNAMES = [
    "task_source_id",
    "parent_task_source_id",
    "repair_branch_id",
    "repair_candidate_id",
    "repair_axis",
    "repair_variant_id",
    "repair_split",
    "task_family",
    "parent_task_family",
    "source_family_template",
    "capability_pair",
    "claim_level_target",
    "materialization_semantics",
    "paper_validity_status",
    "actor_input_contract",
    "profile_specific_tuning",
    *CLAIM_FIELDS,
    "reveal_step",
    "contract_violation_count",
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "obstacle_enabled",
    "obstacle_max_sample_attempts_at_least_200",
]
MATERIALIZATION_FIELDNAMES = [
    "repair_candidate_id",
    "parent_task_source_id",
    "task_source_id",
    "repair_axis",
    "repair_variant_id",
    "repair_split",
    "parent_task_family",
    "original_track_width",
    "repaired_track_width",
    "original_track_radius",
    "repaired_track_radius",
    "original_obstacle_distance_range",
    "repaired_obstacle_distance_range",
    "original_obstacle_half_width_range",
    "repaired_obstacle_half_width_range",
    "original_reveal_step",
    "repaired_reveal_step",
    "original_speed_range",
    "repaired_speed_range",
    "materialization_failure",
    "failure_reason",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "repair_candidate_id",
    "repair_axis",
    "repair_split",
    "parent_task_source_id",
    "profile_name",
    "profile_level",
    "profile_config_path",
    "checkpoint_path",
    "checkpoint_required_for_measured_execution",
    "task_family",
    "history_representation",
    "history_window_steps",
    "reset_or_truncated_control",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    *CLAIM_FIELDS,
]
FAILURE_FIELDNAMES = ["item_id", "item_type", "failure_type", "reason"]
AGGREGATE_FIELDNAMES = ["key", "count"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _range2(value: Any, *, default: tuple[float, float]) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return default
    return float(value[0]), float(value[1])


def _range_text(value: tuple[float, float] | list[float]) -> str:
    return f"{float(value[0]):.6g}:{float(value[1]):.6g}"


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _candidate_guardrail_violations(candidate: Mapping[str, Any]) -> list[str]:
    return [field for field in GUARDRAIL_FIELDS if _bool(candidate.get(field))]


def load_candidates(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("candidates")
    if not isinstance(rows, list):
        raise ValueError("candidate config must contain candidates")
    return [dict(row) for row in rows]


def load_executable_specs(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return [dict(row) for row in rows]


def _contract_checks(env_config: Any) -> dict[str, bool]:
    obstacle = env_config.obstacle
    return {
        "history_length_is_positive": int(env_config.history_length) >= 1,
        "action_history_mode_full": env_config.action_history_mode == "full",
        "include_privileged_params_false": not bool(env_config.include_privileged_params),
        "wheel_observation_mode_none": env_config.wheel_observation_mode == "none",
        "obstacle_relative_velocity_mode_zero": env_config.obstacle_relative_velocity_mode == "zero",
        "obstacle_enabled": bool(obstacle.enabled),
        "obstacle_max_sample_attempts_at_least_200": int(obstacle.max_sample_attempts) >= 200,
    }


def _apply_deltas(env_config: Mapping[str, Any], candidate: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    env = copy.deepcopy(dict(env_config))
    obstacle = copy.deepcopy(dict(env.get("obstacle", {})))
    original_track_width = _float(env.get("track_width"), 8.0)
    original_track_radius = _float(env.get("track_radius"), 60.0)
    original_distance = _range2(obstacle.get("distance_range"), default=(12.0, 34.0))
    original_half_width = _range2(obstacle.get("half_width_range"), default=(0.65, 1.45))
    original_speed = _range2(env.get("speed_range"), default=(9.0, 16.0))
    original_reveal = int(obstacle.get("perception_reveal_step", env.get("reveal_step", 0)) or 0)

    repaired_track_width = min(14.0, max(4.0, original_track_width + _float(candidate.get("delta_track_width"))))
    repaired_track_radius = max(8.0, original_track_radius + _float(candidate.get("delta_track_radius")))
    repaired_distance = (
        original_distance[0] + _float(candidate.get("delta_obstacle_distance_min")),
        original_distance[1] + _float(candidate.get("delta_obstacle_distance_max")),
    )
    repaired_half_width = (
        original_half_width[0] + _float(candidate.get("delta_obstacle_half_width_min")),
        original_half_width[1] + _float(candidate.get("delta_obstacle_half_width_max")),
    )
    repaired_reveal = max(0, original_reveal + int(candidate.get("delta_reveal_step", 0) or 0))
    repaired_speed = (
        original_speed[0] + _float(candidate.get("delta_speed_min")),
        original_speed[1] + _float(candidate.get("delta_speed_max")),
    )

    if repaired_distance[0] < 4.0 or repaired_distance[1] < repaired_distance[0]:
        raise ValueError(f"invalid repaired obstacle distance range: {repaired_distance}")
    if repaired_distance[1] > max(120.0, original_distance[1] + 16.0):
        raise ValueError(f"repaired obstacle distance range too large: {repaired_distance}")
    if repaired_half_width[0] < 0.25 or repaired_half_width[1] < repaired_half_width[0] or repaired_half_width[1] > 2.5:
        raise ValueError(f"invalid repaired obstacle half-width range: {repaired_half_width}")
    if repaired_speed[0] < 4.0 or repaired_speed[1] < repaired_speed[0] or repaired_speed[1] > 35.0:
        raise ValueError(f"invalid repaired speed range: {repaired_speed}")

    env["track_width"] = repaired_track_width
    env["track_radius"] = repaired_track_radius
    env["speed_range"] = [repaired_speed[0], repaired_speed[1]]
    obstacle["distance_range"] = [repaired_distance[0], repaired_distance[1]]
    obstacle["half_width_range"] = [repaired_half_width[0], repaired_half_width[1]]
    obstacle["perception_reveal_step"] = repaired_reveal
    env["obstacle"] = obstacle
    metadata = {
        "original_track_width": original_track_width,
        "repaired_track_width": repaired_track_width,
        "original_track_radius": original_track_radius,
        "repaired_track_radius": repaired_track_radius,
        "original_obstacle_distance_range": _range_text(original_distance),
        "repaired_obstacle_distance_range": _range_text(repaired_distance),
        "original_obstacle_half_width_range": _range_text(original_half_width),
        "repaired_obstacle_half_width_range": _range_text(repaired_half_width),
        "original_reveal_step": original_reveal,
        "repaired_reveal_step": repaired_reveal,
        "original_speed_range": _range_text(original_speed),
        "repaired_speed_range": _range_text(repaired_speed),
    }
    return env, metadata


def _materialize_candidate(
    candidate: Mapping[str, Any],
    *,
    parent_specs: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    candidate_id = str(candidate.get("repair_candidate_id", ""))
    parent_id = str(candidate.get("parent_task_source_id", ""))
    row_base = {
        "repair_candidate_id": candidate_id,
        "parent_task_source_id": parent_id,
        "task_source_id": candidate_id,
        "repair_axis": str(candidate.get("repair_axis", "")),
        "repair_variant_id": str(candidate.get("repair_variant_id", "")),
        "repair_split": str(candidate.get("repair_split", "")),
        "parent_task_family": str(candidate.get("parent_task_family", "")),
    }
    guardrail_violations = _candidate_guardrail_violations(candidate)
    if guardrail_violations:
        raise ValueError(f"candidate guardrail violations: {','.join(guardrail_violations)}")
    if parent_id not in parent_specs:
        raise ValueError(f"missing parent executable spec: {parent_id}")
    parent = parent_specs[parent_id]
    repaired_env_data, delta_metadata = _apply_deltas(parent.get("env_config", {}), candidate)
    env_config = build_env_config(repaired_env_data)
    assert_human_view_env_contract(env_config)
    checks = _contract_checks(env_config)
    contract_violation_count = sum(1 for value in checks.values() if not bool(value))
    spec = copy.deepcopy(dict(parent))
    spec.update(
        {
            "task_source_id": candidate_id,
            "parent_task_source_id": parent_id,
            "repair_branch_id": str(candidate.get("repair_branch_id", "")),
            "repair_candidate_id": candidate_id,
            "repair_axis": str(candidate.get("repair_axis", "")),
            "repair_variant_id": str(candidate.get("repair_variant_id", "")),
            "repair_split": str(candidate.get("repair_split", "")),
            "parent_task_family": str(candidate.get("parent_task_family", "")),
            "parent_source_family_template": str(candidate.get("parent_source_family_template", "")),
            "parent_capability_pair": str(candidate.get("parent_capability_pair", "")),
            "parent_claim_level_target": str(candidate.get("parent_claim_level_target", "")),
            "parent_support_class": str(candidate.get("parent_support_class", "")),
            "scenario_source": "current_sim_offtrack_support_repair_candidate_v0",
            "source_reference": f"{parent_id}::{candidate_id}",
            "materialization_semantics": "current_sim_offtrack_support_repair_materialization_v0",
            "paper_validity_status": "current_sim_offtrack_support_candidate_not_reset_validated",
            "generated_proxy_source": False,
            "profile_specific_tuning": False,
            "actor_input_contract": "P0_human_view_no_wheel_no_oracle",
            "controller_family_ranking_claim_made": False,
            "finite_window_vs_gru_conclusion_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
            "reveal_step": int(delta_metadata["repaired_reveal_step"]),
            "env_config": env_config_to_dict(env_config),
            "contract_checks": checks,
            "contract_violation_count": contract_violation_count,
            **checks,
        }
    )
    return spec, {**row_base, **delta_metadata, "materialization_failure": False, "failure_reason": ""}, None


def _workload_rows(spec_rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        for profile in profile_rows:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "repair_candidate_id": spec["repair_candidate_id"],
                    "repair_axis": spec["repair_axis"],
                    "repair_split": spec["repair_split"],
                    "parent_task_source_id": spec["parent_task_source_id"],
                    "profile_name": profile["profile_name"],
                    "profile_level": profile["profile_level"],
                    "profile_config_path": profile["profile_config_path"],
                    "checkpoint_path": "",
                    "checkpoint_required_for_measured_execution": True,
                    "task_family": spec["task_family"],
                    "history_representation": profile["history_representation"],
                    "history_window_steps": profile["history_window_steps"],
                    "reset_or_truncated_control": profile["reset_or_truncated_control"],
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "current_sim_offtrack_support_candidate_materialized",
            "admissible": True,
            "reason": "M2194 writes no-rollout repaired executable specs and planned workload rows only",
        },
        {"claim": "reset_validity", "admissible": False, "reason": "M2194 does not reset environments"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2194 does not execute or compare controllers"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2194 does not choose a winning profile"},
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2194 materializes comparison inputs but does not execute comparison",
        },
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2194 is not measured evidence"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2194 does not run history interventions"},
    ]


def _aggregate_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [{"key": name, "count": count} for name, count in sorted(Counter(str(row.get(key, "")) for row in rows).items())]


def materialize_candidates(
    *,
    candidate_config: Path | str = DEFAULT_CANDIDATE_CONFIG,
    executable_task_specs: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    expected_candidate_count: int = EXPECTED_CANDIDATE_COUNT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates = load_candidates(candidate_config)
    parent_specs = {str(spec.get("task_source_id", "")): spec for spec in load_executable_specs(executable_task_specs)}
    candidate_ids = [str(row.get("repair_candidate_id", "")) for row in candidates]
    duplicate_candidate_id_count = len(candidate_ids) - len(set(candidate_ids))
    candidate_axis_counts = _count_by(candidates, "repair_axis")
    candidate_split_counts = _count_by(candidates, "repair_split")
    candidate_guardrail_violation_count = sum(len(_candidate_guardrail_violations(row)) for row in candidates)

    spec_rows: list[dict[str, Any]] = []
    materialization_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("repair_candidate_id", ""))
        try:
            spec, row, failure = _materialize_candidate(candidate, parent_specs=parent_specs)
            spec_rows.append(spec)
            materialization_rows.append(row)
            if failure is not None:
                failure_rows.append(failure)
        except Exception as exc:  # pragma: no cover - exercised through failure count tests
            failure_rows.append(
                {
                    "item_id": candidate_id,
                    "item_type": "repair_candidate",
                    "failure_type": type(exc).__name__,
                    "reason": str(exc),
                }
            )
            materialization_rows.append(
                {
                    "repair_candidate_id": candidate_id,
                    "parent_task_source_id": str(candidate.get("parent_task_source_id", "")),
                    "task_source_id": candidate_id,
                    "repair_axis": str(candidate.get("repair_axis", "")),
                    "repair_variant_id": str(candidate.get("repair_variant_id", "")),
                    "repair_split": str(candidate.get("repair_split", "")),
                    "parent_task_family": str(candidate.get("parent_task_family", "")),
                    "original_track_width": "",
                    "repaired_track_width": "",
                    "original_track_radius": "",
                    "repaired_track_radius": "",
                    "original_obstacle_distance_range": "",
                    "repaired_obstacle_distance_range": "",
                    "original_obstacle_half_width_range": "",
                    "repaired_obstacle_half_width_range": "",
                    "original_reveal_step": "",
                    "repaired_reveal_step": "",
                    "original_speed_range": "",
                    "repaired_speed_range": "",
                    "materialization_failure": True,
                    "failure_reason": str(exc),
                }
            )

    profile_rows = [dict(row, profile_config_exists=Path(row["profile_config_path"]).exists()) for row in PROFILE_ROWS]
    workload_rows = _workload_rows(spec_rows, profile_rows)
    claim_rows = _claim_boundary_rows()
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in spec_rows)
    forbidden_key_violation_count = sum(
        1
        for row in spec_rows
        if any(
            _bool(row.get(key))
            for key in (
                "generated_proxy_source",
                "profile_specific_tuning",
                "controller_family_ranking_claim_made",
                "finite_window_vs_gru_conclusion_made",
                "paper_level_claim_made",
                "level3_self_id_claim_made",
            )
        )
    )
    profile_specific_tuning_count = sum(1 for row in spec_rows + workload_rows if _bool(row.get("profile_specific_tuning")))
    actor_input_contract_change_count = sum(1 for row in spec_rows if int(row.get("contract_violation_count", 0)) > 0)
    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_execution_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "profile_specific_tuning": bool(profile_specific_tuning_count),
        "actor_input_contract_changed": bool(actor_input_contract_change_count),
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    expected_workload_count = int(expected_candidate_count) * len(profile_rows)
    result_pass = (
        len(candidates) == int(expected_candidate_count)
        and len(spec_rows) == int(expected_candidate_count)
        and len(workload_rows) == expected_workload_count
        and duplicate_candidate_id_count == 0
        and candidate_guardrail_violation_count == 0
        and len(failure_rows) == 0
        and contract_violation_count == 0
        and forbidden_key_violation_count == 0
        and profile_specific_tuning_count == 0
        and guardrail_violation_count == 0
    )
    result_class = (
        "current_sim_offtrack_support_candidate_materialization_pass"
        if result_pass
        else "current_sim_offtrack_support_candidate_materialization_fail"
    )

    write_json(
        output / "repaired_executable_task_specs.json",
        {
            "protocol": PROTOCOL,
            "generated_at_utc": utc_timestamp(),
            "candidate_config": str(candidate_config),
            "executable_task_specs_path": str(executable_task_specs),
            "claim_scope": "no_rollout_offtrack_support_candidate_materialization_only",
            "executable_task_specs": spec_rows,
        },
    )
    write_csv_rows(output / "repaired_executable_task_specs.csv", spec_rows, fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(output / "planned_workload.csv", workload_rows, fieldnames=WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "materialization_rows.csv", materialization_rows, fieldnames=MATERIALIZATION_FIELDNAMES)
    write_csv_rows(output / "materialization_failures.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "candidate_axis_counts.csv", _aggregate_rows(candidates, "repair_axis"), fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "candidate_split_counts.csv", _aggregate_rows(candidates, "repair_split"), fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "task_family_counts.csv", _aggregate_rows(spec_rows, "task_family"), fieldnames=AGGREGATE_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "candidate_config": str(candidate_config),
        "executable_task_specs_path": str(executable_task_specs),
        "candidate_count": len(candidates),
        "expected_candidate_count": int(expected_candidate_count),
        "repaired_executable_spec_count": len(spec_rows),
        "expected_repaired_executable_spec_count": int(expected_candidate_count),
        "planned_workload_row_count": len(workload_rows),
        "expected_planned_workload_row_count": expected_workload_count,
        "profile_count": len(profile_rows),
        "duplicate_candidate_id_count": duplicate_candidate_id_count,
        "candidate_guardrail_violation_count": candidate_guardrail_violation_count,
        "materialization_failure_count": len(failure_rows),
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": forbidden_key_violation_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "actor_input_contract_change_count": actor_input_contract_change_count,
        "candidate_axis_counts": candidate_axis_counts,
        "expected_candidate_axis_counts": EXPECTED_AXIS_COUNTS if int(expected_candidate_count) == EXPECTED_CANDIDATE_COUNT else {},
        "candidate_split_counts": candidate_split_counts,
        "expected_candidate_split_counts": EXPECTED_SPLITS if int(expected_candidate_count) == EXPECTED_CANDIDATE_COUNT else {},
        "task_family_counts": _count_by(spec_rows, "task_family"),
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_execution_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repaired_executable_task_specs": str(output / "repaired_executable_task_specs.json"),
            "repaired_executable_task_specs_csv": str(output / "repaired_executable_task_specs.csv"),
            "planned_workload": str(output / "planned_workload.csv"),
            "materialization_rows": str(output / "materialization_rows.csv"),
            "materialization_failures": str(output / "materialization_failures.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "candidate_axis_counts": str(output / "candidate_axis_counts.csv"),
            "candidate_split_counts": str(output / "candidate_split_counts.csv"),
            "task_family_counts": str(output / "task_family_counts.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2194-paper-route-current-sim-offtrack-support-candidate-materialization-implementation-and-run",
            "status": "completed" if result_pass else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_CANDIDATE_CONFIG)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_candidates(
        candidate_config=args.candidate_config,
        executable_task_specs=args.executable_task_specs,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"repaired_executable_spec_count={summary['repaired_executable_spec_count']}")
    print(f"planned_workload_row_count={summary['planned_workload_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
