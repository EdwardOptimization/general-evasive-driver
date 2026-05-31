"""No-reset materialization preflight for outcome-supported decisive tasks."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
    profile_artifact_rows,
)
from autodrift.paper_route_outcome_supported_decisive_task_candidates import (
    DIFFICULTY_AXES,
    FAMILY_TARGETS,
    SENTINEL_PROFILES,
    SPLIT_TARGETS,
)


DEFAULT_CANDIDATES = Path("configs/paper_route_outcome_supported_decisive_task_candidates_v0.json")
DEFAULT_BASE_PROFILE_CONFIG = Path("configs/paper_route_corrected_profiles/m1207_l0_current_masked.json")
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight")
DEFAULT_NEXT_BLOCKER = "m2064-paper-route-outcome-supported-decisive-materialization-preflight-result-audit"
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_materialization_preflight_v0"

TARGET_EXECUTABLE_SPECS = sum(FAMILY_TARGETS.values())
TARGET_SENTINEL_PROFILE_COUNT = len(SENTINEL_PROFILES)
TARGET_SENTINEL_WORKLOAD = TARGET_EXECUTABLE_SPECS * TARGET_SENTINEL_PROFILE_COUNT

DISTANCE_RANGES = {
    "early": [52.0, 70.0],
    "medium": [34.0, 52.0],
    "late": [18.0, 36.0],
}
ROAD_WIDTHS = {"generous": 7.0, "nominal": 5.5, "tight": 4.4}
TRACK_RADII = {"straight_or_low": 60.0, "moderate": 32.0, "high": 18.0}
SPEED_RANGES = {"low": [7.0, 11.0], "nominal": [10.0, 15.0], "high": [14.0, 20.0]}
MU_RANGES = {
    "nominal_mu": [0.75, 1.05],
    "low_mu": [0.35, 0.55],
    "mixed_mu": [0.28, 1.05],
    "actuator_delay": [0.45, 0.85],
}
ACTUATOR_TAU_RANGES = {
    "nominal_mu": [0.65, 1.35],
    "low_mu": [0.75, 1.65],
    "mixed_mu": [0.65, 2.20],
    "actuator_delay": [1.80, 2.80],
}

SPEC_CSV_FIELDNAMES = [
    "task_source_id",
    "candidate_id",
    "candidate_set_id",
    "branch_id",
    "panel_task_family",
    "source_split",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_reference",
    "task_role_semantics",
    "obstacle_distance_band",
    "road_width_band",
    "curvature_band",
    "dynamics_band",
    "initial_speed_band",
    "same_current_constraint",
    "history_intervention_candidate",
    "warmup_mode",
    "warmup_duration_seconds",
    "obstacle_reveal_delay_seconds",
    "recent_window_seconds",
    "older_history_offset_seconds",
    "diagnostic_delay_seconds",
    "terminal_margin_bucket",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "contract_violation_count",
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "obstacle_enabled",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "candidate_id",
    "panel_task_family",
    "source_split",
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
    "source_kind",
    "source_edge",
    "window_tag",
    "materialization_semantics",
    "paper_validity_claim",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
PROFILE_FIELDNAMES = ["profile_name", "config_path", "checkpoint_path", "config_exists", "checkpoint_exists"]
FAILURE_FIELDNAMES = ["candidate_id", "panel_task_family", "failure_type", "reason"]
FAMILY_AXIS_FIELDNAMES = ["panel_task_family", "axis", "value", "count"]
SOURCE_KIND_FIELDNAMES = ["panel_task_family", "source_kind", "count"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return float(default)


def _load_candidates(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    candidates = list(payload.get("candidates", []))
    return [dict(row) for row in candidates]


def _sentinel_profile_rows(profile_run_dir: Path | str) -> list[dict[str, Any]]:
    all_rows = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    by_name = {str(row["profile_name"]): row for row in all_rows}
    return [dict(by_name[name]) for name in SENTINEL_PROFILES if name in by_name]


def _proxy_template_for_candidate(candidate: Mapping[str, Any]) -> str:
    family = str(candidate.get("panel_task_family", ""))
    source_kind = str(candidate.get("source_kind", "")).lower()
    if family == "T1_reactive_active_safety":
        return "t5_near_boundary_warmup"
    if family == "T2_same_current_different_older_history":
        if "brake" in source_kind:
            return "t4_staged_warmup_capability"
        if "steer" in source_kind or "yaw" in source_kind:
            return "t4_actuator_delay_response"
        return "t5_near_boundary_warmup"
    if family == "T3_active_diagnostic_warmup":
        return "t4_staged_warmup_capability"
    if family == "T4_variable_diagnostic_delay":
        return "t4_actuator_delay_response"
    if family == "T5_terminal_boundary_near_constraint":
        return "t5_boundary_axis_retarget"
    return "t5_near_boundary_warmup"


def _warmup_gate(base: Mapping[str, Any], candidate: Mapping[str, Any], *, dt: float) -> dict[str, Any]:
    gate = copy.deepcopy(dict(base.get("warmup_gate", {})))
    warmup_mode = str(candidate.get("warmup_mode", "none"))
    family = str(candidate.get("panel_task_family", ""))
    active = warmup_mode != "none" or family in {
        "T2_same_current_different_older_history",
        "T3_active_diagnostic_warmup",
        "T4_variable_diagnostic_delay",
        "T5_terminal_boundary_near_constraint",
    }
    reveal_delay = _float(candidate.get("obstacle_reveal_delay_seconds", 0.0), 0.0)
    diagnostic_delay = _float(candidate.get("diagnostic_delay_seconds", 0.0), 0.0)
    duration = _float(candidate.get("warmup_duration_seconds", 0.0), 0.0)
    gate["enabled"] = bool(active)
    gate["reveal_step"] = max(0, int(round((reveal_delay + diagnostic_delay) / max(dt, 1e-6))))
    gate["max_active_steps"] = max(0, int(round(duration / max(dt, 1e-6))))
    return gate


def _env_config_for_candidate(candidate: Mapping[str, Any], *, base_env: Mapping[str, Any]) -> dict[str, Any]:
    env = copy.deepcopy(dict(base_env))
    dt = _float(env.get("dt", 0.02), 0.02)
    obstacle = copy.deepcopy(dict(env.get("obstacle", {})))
    randomization = copy.deepcopy(dict(env.get("randomization", {})))

    obstacle["enabled"] = True
    obstacle["distance_range"] = DISTANCE_RANGES[str(candidate["obstacle_distance_band"])]
    obstacle["perception_reveal_step"] = max(0, int(round(_float(candidate.get("obstacle_reveal_delay_seconds", 0.0)) / dt)))
    if str(candidate.get("panel_task_family")) == "T5_terminal_boundary_near_constraint":
        obstacle["half_width_range"] = [0.65, 1.25]
    else:
        obstacle["half_width_range"] = [0.45, 1.05]

    dynamics_band = str(candidate["dynamics_band"])
    randomization["mu_range"] = MU_RANGES[dynamics_band]
    randomization["actuator_tau_scale_range"] = ACTUATOR_TAU_RANGES[dynamics_band]

    env["action_history_mode"] = "full"
    env["include_privileged_params"] = False
    env["wheel_observation_mode"] = "none"
    env["obstacle_relative_velocity_mode"] = "zero"
    env["history_length"] = max(1, int(env.get("history_length", 1)))
    env["obstacle"] = obstacle
    env["randomization"] = randomization
    env["friction_limited_speed"] = True
    env["speed_range"] = SPEED_RANGES[str(candidate["initial_speed_band"])]
    env["track_kind"] = "circle"
    env["track_radius"] = TRACK_RADII[str(candidate["curvature_band"])]
    env["track_width"] = ROAD_WIDTHS[str(candidate["road_width_band"])]
    env["warmup_gate"] = _warmup_gate(env, candidate, dt=dt)
    return env


def contract_checks(env_config: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "history_length_is_positive": int(env_config.get("history_length", 0)) >= 1,
        "action_history_mode_full": env_config.get("action_history_mode") == "full",
        "include_privileged_params_false": not _bool(env_config.get("include_privileged_params", False)),
        "wheel_observation_mode_none": env_config.get("wheel_observation_mode") == "none",
        "obstacle_relative_velocity_mode_zero": env_config.get("obstacle_relative_velocity_mode") == "zero",
        "obstacle_enabled": bool(dict(env_config.get("obstacle", {})).get("enabled", False)),
    }


def materialize_executable_specs(
    *,
    candidates: list[Mapping[str, Any]],
    base_env: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    required_fields = {
        "candidate_id",
        "candidate_set_id",
        "branch_id",
        "panel_task_family",
        "source_split",
        "source_origin",
        "source_kind",
        "source_edge",
        "window_tag",
        "source_reference",
        *DIFFICULTY_AXES.keys(),
    }
    for candidate in candidates:
        try:
            missing = sorted(field for field in required_fields if field not in candidate)
            if missing:
                raise ValueError(f"missing required candidate fields: {','.join(missing)}")
            env_config = _env_config_for_candidate(candidate, base_env=base_env)
            checks = contract_checks(env_config)
            contract_violation_count = sum(1 for value in checks.values() if not bool(value))
            if _bool(candidate.get("paper_validity_claim", False)):
                raise ValueError("candidate paper_validity_claim must be false")
            task_source_id = f"m2063-osd-{candidate['candidate_id']}"
            specs.append(
                {
                    "task_source_id": task_source_id,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_set_id": candidate["candidate_set_id"],
                    "branch_id": candidate["branch_id"],
                    "panel_task_family": candidate["panel_task_family"],
                    "source_split": candidate["source_split"],
                    "source_origin": candidate["source_origin"],
                    "source_kind": candidate["source_kind"],
                    "source_edge": candidate["source_edge"],
                    "window_tag": candidate["window_tag"],
                    "source_reference": candidate["source_reference"],
                    "task_role_semantics": candidate.get("task_role_semantics", ""),
                    "obstacle_distance_band": candidate["obstacle_distance_band"],
                    "road_width_band": candidate["road_width_band"],
                    "curvature_band": candidate["curvature_band"],
                    "dynamics_band": candidate["dynamics_band"],
                    "initial_speed_band": candidate["initial_speed_band"],
                    "same_current_constraint": bool(candidate.get("same_current_constraint", False)),
                    "history_intervention_candidate": bool(candidate.get("history_intervention_candidate", False)),
                    "warmup_mode": candidate.get("warmup_mode", "none"),
                    "warmup_duration_seconds": _float(candidate.get("warmup_duration_seconds", 0.0)),
                    "obstacle_reveal_delay_seconds": _float(candidate.get("obstacle_reveal_delay_seconds", 0.0)),
                    "recent_window_seconds": _float(candidate.get("recent_window_seconds", 0.0)),
                    "older_history_offset_seconds": _float(candidate.get("older_history_offset_seconds", 0.0)),
                    "diagnostic_delay_seconds": _float(candidate.get("diagnostic_delay_seconds", 0.0)),
                    "terminal_margin_bucket": candidate.get("terminal_margin_bucket", ""),
                    "materialization_semantics": "smoke_proxy",
                    "proxy_template_family": _proxy_template_for_candidate(candidate),
                    "generated_source_row": True,
                    "paper_validity_claim": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "contract_checks": checks,
                    "contract_violation_count": contract_violation_count,
                    "env_config": env_config,
                }
            )
        except Exception as exc:  # noqa: BLE001 - preflight should record every invalid row.
            failures.append(
                {
                    "candidate_id": str(candidate.get("candidate_id", "")),
                    "panel_task_family": str(candidate.get("panel_task_family", "")),
                    "failure_type": type(exc).__name__,
                    "reason": str(exc),
                }
            )
    return specs, failures


def _spec_csv_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        checks = dict(spec.get("contract_checks", {}))
        rows.append({key: spec.get(key, "") for key in SPEC_CSV_FIELDNAMES if key not in checks} | checks)
    return rows


def planned_sentinel_workload_rows(
    specs: list[Mapping[str, Any]],
    *,
    profile_run_dir: Path | str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles = _sentinel_profile_rows(profile_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in specs:
        for profile in profiles:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "candidate_id": spec["candidate_id"],
                    "panel_task_family": spec["panel_task_family"],
                    "source_split": spec["source_split"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "source_kind": spec["source_kind"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "materialization_semantics": spec["materialization_semantics"],
                    "paper_validity_claim": spec["paper_validity_claim"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows, profiles


def _counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _duplicate_count(values: Iterable[Any]) -> int:
    return sum(1 for _value, count in Counter(str(value) for value in values).items() if count > 1)


def _axis_aggregate(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for spec in specs:
        family = str(spec["panel_task_family"])
        for axis in DIFFICULTY_AXES:
            counts[(family, axis, str(spec[axis]))] += 1
    return [
        {"panel_task_family": family, "axis": axis, "value": value, "count": count}
        for (family, axis, value), count in sorted(counts.items())
    ]


def _source_kind_aggregate(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((str(spec["panel_task_family"]), str(spec["source_kind"])) for spec in specs)
    return [
        {"panel_task_family": family, "source_kind": source_kind, "count": count}
        for (family, source_kind), count in sorted(counts.items())
    ]


def _axis_coverage_pass(specs: Iterable[Mapping[str, Any]]) -> bool:
    rows = list(specs)
    for family in FAMILY_TARGETS:
        family_rows = [row for row in rows if row["panel_task_family"] == family]
        for axis, expected_values in DIFFICULTY_AXES.items():
            if {str(row[axis]) for row in family_rows} != set(expected_values):
                return False
    return True


def _claim_rows(pass_conditions: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "outcome_supported_decisive_materialization_preflight_completed",
            "admissible": True,
            "reason": "M2063 writes no-reset materialization artifacts for the M2060 candidate panel",
        },
        {
            "claim": "reset_validation_ready",
            "admissible": pass_conditions,
            "reason": "requires executable specs workload profile artifacts contract checks and claim guards to pass",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2063 does not execute or compare controller outcomes",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "M2063 materializes smoke proxies only",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2063 is materialization preflight only",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2063 does not run history intervention outcome tests",
        },
    ]


def run_materialization_preflight(
    *,
    candidates_path: Path | str = DEFAULT_CANDIDATES,
    base_profile_config_path: Path | str = DEFAULT_BASE_PROFILE_CONFIG,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates = _load_candidates(candidates_path)
    base_profile = read_json(base_profile_config_path)
    base_env = dict(base_profile.get("env", {}))
    executable_specs, materialization_failures = materialize_executable_specs(
        candidates=candidates,
        base_env=base_env,
    )
    workload_rows, profile_rows = planned_sentinel_workload_rows(executable_specs, profile_run_dir=profile_run_dir)

    family_counts = {family: 0 for family in FAMILY_TARGETS}
    family_counts.update(_counter_dict(spec["panel_task_family"] for spec in executable_specs))
    split_counts = {split: 0 for split in SPLIT_TARGETS}
    split_counts.update(_counter_dict(spec["source_split"] for spec in executable_specs))
    profile_missing_count = sum(1 for row in profile_rows if not (row["config_exists"] and row["checkpoint_exists"]))
    duplicate_task_source_id_count = _duplicate_count(spec["task_source_id"] for spec in executable_specs)
    duplicate_workload_id_count = _duplicate_count(row["workload_id"] for row in workload_rows)
    contract_violation_count = sum(int(spec.get("contract_violation_count", 0)) for spec in executable_specs)
    forbidden_key_hits = forbidden_key_violations(executable_specs)
    smoke_proxy_paper_claim_count = sum(1 for spec in executable_specs if _bool(spec.get("paper_validity_claim", False)))
    profile_specific_tuning_count = sum(1 for row in workload_rows if _bool(row.get("profile_specific_tuning", False)))
    scheduled_rollout_count = sum(1 for row in workload_rows if _bool(row.get("environment_rollout_scheduled", False)))
    training_scheduled_count = sum(1 for row in workload_rows if _bool(row.get("training_scheduled", False)))

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": scheduled_rollout_count > 0,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": training_scheduled_count > 0,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": profile_specific_tuning_count > 0,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "smoke_proxy_paper_validity_claim_made": smoke_proxy_paper_claim_count > 0,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)

    pass_conditions = (
        len(executable_specs) == TARGET_EXECUTABLE_SPECS
        and len(workload_rows) == TARGET_SENTINEL_WORKLOAD
        and len(profile_rows) == TARGET_SENTINEL_PROFILE_COUNT
        and family_counts == FAMILY_TARGETS
        and split_counts == SPLIT_TARGETS
        and _axis_coverage_pass(executable_specs)
        and len(materialization_failures) == 0
        and profile_missing_count == 0
        and duplicate_task_source_id_count == 0
        and duplicate_workload_id_count == 0
        and contract_violation_count == 0
        and not forbidden_key_hits
        and guardrail_violation_count == 0
    )
    if pass_conditions:
        result_class = "outcome_supported_decisive_materialization_preflight_pass"
    elif executable_specs or workload_rows:
        result_class = "outcome_supported_decisive_materialization_preflight_partial"
    else:
        result_class = "outcome_supported_decisive_materialization_preflight_fail_closed"

    artifacts = {
        "summary": output / "summary.json",
        "executable_task_specs_json": output / "executable_task_specs.json",
        "executable_task_specs_csv": output / "executable_task_specs.csv",
        "planned_sentinel_workload": output / "planned_sentinel_workload.csv",
        "profile_artifacts": output / "profile_artifacts.csv",
        "family_axis_aggregate": output / "family_axis_aggregate.csv",
        "source_kind_aggregate": output / "source_kind_aggregate.csv",
        "materialization_failures": output / "materialization_failures.csv",
        "claim_boundary": output / "claim_boundary.csv",
    }
    write_json(
        artifacts["executable_task_specs_json"],
        {"protocol": PROTOCOL_NAME, "executable_task_specs": executable_specs},
    )
    write_csv_rows(artifacts["executable_task_specs_csv"], _spec_csv_rows(executable_specs), SPEC_CSV_FIELDNAMES)
    write_csv_rows(artifacts["planned_sentinel_workload"], workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(artifacts["profile_artifacts"], profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(artifacts["family_axis_aggregate"], _axis_aggregate(executable_specs), FAMILY_AXIS_FIELDNAMES)
    write_csv_rows(artifacts["source_kind_aggregate"], _source_kind_aggregate(executable_specs), SOURCE_KIND_FIELDNAMES)
    write_csv_rows(artifacts["materialization_failures"], materialization_failures, FAILURE_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], _claim_rows(pass_conditions), CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "candidates_path": str(candidates_path),
        "base_profile_config_path": str(base_profile_config_path),
        "profile_run_dir": str(profile_run_dir),
        "candidate_count": len(candidates),
        "executable_spec_count": len(executable_specs),
        "target_executable_spec_count": TARGET_EXECUTABLE_SPECS,
        "planned_sentinel_workload_count": len(workload_rows),
        "target_sentinel_workload_count": TARGET_SENTINEL_WORKLOAD,
        "sentinel_profile_count": len(profile_rows),
        "target_sentinel_profile_count": TARGET_SENTINEL_PROFILE_COUNT,
        "sentinel_profiles": list(SENTINEL_PROFILES),
        "family_counts": family_counts,
        "expected_family_counts": FAMILY_TARGETS,
        "source_split_counts": split_counts,
        "expected_source_split_counts": SPLIT_TARGETS,
        "difficulty_axis_coverage_pass": _axis_coverage_pass(executable_specs),
        "materialization_failure_count": len(materialization_failures),
        "profile_missing_count": profile_missing_count,
        "duplicate_task_source_id_count": duplicate_task_source_id_count,
        "duplicate_workload_id_count": duplicate_workload_id_count,
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "smoke_proxy_paper_claim_count": smoke_proxy_paper_claim_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "scheduled_rollout_count": scheduled_rollout_count,
        "training_scheduled_count": training_scheduled_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": next_blocker,
    }
    write_json(artifacts["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--base-profile-config", type=Path, default=DEFAULT_BASE_PROFILE_CONFIG)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_materialization_preflight(
        candidates_path=args.candidates,
        base_profile_config_path=args.base_profile_config,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"executable_spec_count={summary['executable_spec_count']}")
    print(f"planned_sentinel_workload_count={summary['planned_sentinel_workload_count']}")
    print(f"sentinel_profile_count={summary['sentinel_profile_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
