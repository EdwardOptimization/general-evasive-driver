"""No-reset repair preflight for outcome-supported decisive task specs."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
    profile_artifact_rows,
)
from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import reset_sampler_state_from_seed
from autodrift.paper_route_outcome_supported_decisive_materialization_preflight import (
    contract_checks,
)
from autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight import (
    METADATA_FIELDS,
    metadata_for_spec,
)
from autodrift.paper_route_outcome_supported_decisive_task_candidates import (
    DIFFICULTY_AXES,
    FAMILY_TARGETS,
    SENTINEL_PROFILES,
    SPLIT_TARGETS,
)
from autodrift.scenarios import ObstacleScenario, classify_obstacle_scenario


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.json"
)
DEFAULT_RESET_FAILURE_ROWS = Path(
    "runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_failure_rows.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight")
DEFAULT_NEXT_BLOCKER = "m2071-paper-route-outcome-supported-decisive-reset-materialization-repair-result-audit"
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_reset_materialization_repair_preflight_v0"

TARGET_EXECUTABLE_SPECS = sum(FAMILY_TARGETS.values())
TARGET_SENTINEL_PROFILE_COUNT = len(SENTINEL_PROFILES)
TARGET_SENTINEL_WORKLOAD = TARGET_EXECUTABLE_SPECS * TARGET_SENTINEL_PROFILE_COUNT

GLOBAL_DISTANCE_RANGE = (1.0, 80.0)
GLOBAL_HALF_WIDTH_RANGE = (0.20, 1.35)
GRID_DISTANCE_COUNT = 145
GRID_HALF_WIDTH_COUNT = 43

REPAIR_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "source_error_type",
    "source_error_message",
    "warmup_gate_repaired",
    "warmup_gate_repair_reason",
    "original_warmup_gate_enabled",
    "original_warmup_gate_max_active_steps",
    "repaired_warmup_gate_enabled",
    "repaired_warmup_gate_max_active_steps",
    "obstacle_filter_repaired",
    "obstacle_filter_repair_reason",
    "scenario_filter_feasible_before",
    "scenario_filter_feasible_after",
    "original_obstacle_distance_range",
    "original_obstacle_half_width_range",
    "original_obstacle_max_threshold_score",
    "repaired_obstacle_distance_range",
    "repaired_obstacle_half_width_range",
    "repaired_obstacle_max_threshold_score",
    "scenario_filter_candidate_label",
    "scenario_filter_candidate_score",
    "scenario_filter_candidate_distance",
    "scenario_filter_candidate_half_width",
]
SPEC_CSV_FIELDNAMES = [
    *METADATA_FIELDS,
    "warmup_gate_repaired",
    "obstacle_filter_repaired",
    "scenario_filter_feasible_after",
    "contract_violation_count",
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
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
AGGREGATE_FIELDNAMES = ["key", "count"]
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
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n", ""}:
            return False
    return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _range_to_string(value: Any) -> str:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"{float(value[0]):.6f}:{float(value[1]):.6f}"
    return ""


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _linspace(low: float, high: float, count: int) -> list[float]:
    if count <= 1:
        return [float(low)]
    step = (float(high) - float(low)) / float(count - 1)
    return [float(low) + step * index for index in range(count)]


def _threshold_score(scenario: ObstacleScenario) -> float:
    required = max(float(scenario.required_lateral_offset), 1e-6)
    aes_margin = float(scenario.conventional_lateral_capacity - scenario.required_lateral_offset) / required
    drift_margin = float(scenario.drift_lateral_capacity - scenario.required_lateral_offset) / required
    return float(min(abs(aes_margin), abs(drift_margin)))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _aggregate_rows(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    return [{"key": key, "count": int(value)} for key, value in sorted(counts.items())]


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def load_reset_failure_rows(path: Path | str = DEFAULT_RESET_FAILURE_ROWS) -> list[dict[str, str]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("task_source_id", "")))


def zero_step_warmup_gate_invalid(env_config: Mapping[str, Any]) -> bool:
    gate = dict(env_config.get("warmup_gate", {}))
    return int(gate.get("max_active_steps", 0) or 0) <= 0


def repair_warmup_gate(spec: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    env_config = copy.deepcopy(dict(spec.get("env_config", {})))
    gate = copy.deepcopy(dict(env_config.get("warmup_gate", {})))
    original_enabled = _bool(gate.get("enabled"))
    original_steps = int(gate.get("max_active_steps", 0) or 0)
    warmup_mode = str(spec.get("warmup_mode", "none"))
    dt = max(_float(env_config.get("dt", 0.02), 0.02), 1e-6)
    active = warmup_mode != "none"
    repair_reasons: list[str] = []

    if active:
        duration = max(_float(spec.get("warmup_duration_seconds", 0.0), 0.0), 0.5)
        target_steps = max(1, int(round(duration / dt)))
        if not original_enabled:
            repair_reasons.append("active_warmup_mode_enabled")
        if original_steps <= 0:
            repair_reasons.append("active_warmup_zero_step_floor")
        gate["enabled"] = True
        gate["max_active_steps"] = max(original_steps, target_steps, 1)
    else:
        if original_enabled:
            repair_reasons.append("warmup_mode_none_disables_gate")
        if original_steps <= 0:
            repair_reasons.append("disabled_warmup_positive_default")
        gate["enabled"] = False
        gate["max_active_steps"] = max(original_steps, 64)

    gate["reveal_step"] = max(0, int(gate.get("reveal_step", 0) or 0))
    gate.setdefault("distance_range", [12.0, 30.0])
    gate.setdefault("lateral_offset_range", [-1.2, 1.2])
    gate.setdefault("half_width_range", [0.35, 0.85])
    gate.setdefault("finish_pass_distance", 2.0)
    env_config["warmup_gate"] = gate
    return env_config, {
        "warmup_gate_repaired": bool(repair_reasons),
        "warmup_gate_repair_reason": ";".join(repair_reasons),
        "original_warmup_gate_enabled": original_enabled,
        "original_warmup_gate_max_active_steps": original_steps,
        "repaired_warmup_gate_enabled": bool(gate.get("enabled")),
        "repaired_warmup_gate_max_active_steps": int(gate.get("max_active_steps", 0) or 0),
    }


def _friction_step_range(config: Any) -> tuple[int, int] | None:
    low, high = config.friction_step.step_range
    low = max(1, int(low))
    high = min(int(high), int(config.max_steps) - 1)
    if high < low:
        return None
    return low, high


def _uses_obstacle_aligned_friction_step(config: Any) -> bool:
    return bool(config.friction_step.enabled and config.obstacle.enabled and config.obstacle.min_time_after_friction_step > 0.0)


def _obstacle_aligned_friction_step_range(*, config: Any, scenario: ObstacleScenario) -> tuple[int, int] | None:
    valid_range = _friction_step_range(config)
    if valid_range is None:
        return None
    low, high = valid_range
    latest_step = int((scenario.time_to_obstacle - config.obstacle.min_time_after_friction_step) / config.dt)
    high = min(high, latest_step)
    if high < low:
        return None
    return low, high


def _time_after_friction_step(*, config: Any, scenario: ObstacleScenario, friction_step_at: int | None) -> float:
    if friction_step_at is None:
        return float("inf")
    return float(scenario.time_to_obstacle - int(friction_step_at) * config.dt)


def _candidate_is_accepted(
    *,
    config: Any,
    scenario: ObstacleScenario,
    threshold_score: float,
    friction_step_at: int | None,
) -> bool:
    if scenario.label not in set(config.obstacle.allowed_labels):
        return False
    if config.obstacle.require_aeb_infeasible and scenario.label == "aeb_feasible":
        return False
    if config.obstacle.max_threshold_score is not None and threshold_score > config.obstacle.max_threshold_score:
        return False
    if _uses_obstacle_aligned_friction_step(config):
        return _obstacle_aligned_friction_step_range(config=config, scenario=scenario) is not None
    return _time_after_friction_step(config=config, scenario=scenario, friction_step_at=friction_step_at) >= float(
        config.obstacle.min_time_after_friction_step
    )


def _scan_for_accepted_obstacle(
    *,
    env_config: Mapping[str, Any],
    seed: int,
    distance_range: tuple[float, float],
    half_width_range: tuple[float, float],
    distance_count: int,
    half_width_count: int,
) -> dict[str, Any]:
    config = build_env_config(dict(env_config))
    state = reset_sampler_state_from_seed(env_config=env_config, seed=int(seed))
    scenario_config = config.obstacle.scenario_config(speed=float(state["speed_ref"]), mu=float(state["initial_mu"]))
    best: dict[str, Any] | None = None
    for distance in _linspace(distance_range[0], distance_range[1], distance_count):
        for half_width in _linspace(half_width_range[0], half_width_range[1], half_width_count):
            scenario = classify_obstacle_scenario(
                speed=float(state["speed_ref"]),
                mu=float(state["initial_mu"]),
                obstacle_distance=float(distance),
                obstacle_half_width=float(half_width),
                config=scenario_config,
            )
            score = _threshold_score(scenario)
            if not _candidate_is_accepted(
                config=config,
                scenario=scenario,
                threshold_score=score,
                friction_step_at=state["friction_step_at"],
            ):
                continue
            row = {
                "feasible": True,
                "label": scenario.label,
                "threshold_score": float(score),
                "distance": float(distance),
                "half_width": float(half_width),
            }
            if best is None or float(row["threshold_score"]) < float(best["threshold_score"]):
                best = row
    return best or {"feasible": False, "label": "", "threshold_score": "", "distance": "", "half_width": ""}


def repair_obstacle_filter(
    *,
    env_config: Mapping[str, Any],
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    repaired = copy.deepcopy(dict(env_config))
    obstacle = copy.deepcopy(dict(repaired.get("obstacle", {})))
    original_distance = list(obstacle.get("distance_range", [16.0, 55.0]))
    original_half_width = list(obstacle.get("half_width_range", [0.45, 1.15]))
    original_threshold = obstacle.get("max_threshold_score", "")
    before = _scan_for_accepted_obstacle(
        env_config=repaired,
        seed=int(seed),
        distance_range=(float(original_distance[0]), float(original_distance[1])),
        half_width_range=(float(original_half_width[0]), float(original_half_width[1])),
        distance_count=13,
        half_width_count=9,
    )
    if _bool(before.get("feasible")):
        return repaired, {
            "obstacle_filter_repaired": False,
            "obstacle_filter_repair_reason": "",
            "scenario_filter_feasible_before": True,
            "scenario_filter_feasible_after": True,
            "original_obstacle_distance_range": _range_to_string(original_distance),
            "original_obstacle_half_width_range": _range_to_string(original_half_width),
            "original_obstacle_max_threshold_score": original_threshold,
            "repaired_obstacle_distance_range": _range_to_string(original_distance),
            "repaired_obstacle_half_width_range": _range_to_string(original_half_width),
            "repaired_obstacle_max_threshold_score": obstacle.get("max_threshold_score", ""),
            "scenario_filter_candidate_label": before["label"],
            "scenario_filter_candidate_score": before["threshold_score"],
            "scenario_filter_candidate_distance": before["distance"],
            "scenario_filter_candidate_half_width": before["half_width"],
        }

    after = _scan_for_accepted_obstacle(
        env_config=repaired,
        seed=int(seed),
        distance_range=GLOBAL_DISTANCE_RANGE,
        half_width_range=GLOBAL_HALF_WIDTH_RANGE,
        distance_count=GRID_DISTANCE_COUNT,
        half_width_count=GRID_HALF_WIDTH_COUNT,
    )
    threshold_repaired = False
    if not _bool(after.get("feasible")):
        relaxed = copy.deepcopy(repaired)
        relaxed_obstacle = copy.deepcopy(dict(relaxed.get("obstacle", {})))
        current_threshold = relaxed_obstacle.get("max_threshold_score", None)
        relaxed_obstacle["max_threshold_score"] = max(_float(current_threshold, 0.25), 1.0)
        relaxed["obstacle"] = relaxed_obstacle
        relaxed_after = _scan_for_accepted_obstacle(
            env_config=relaxed,
            seed=int(seed),
            distance_range=GLOBAL_DISTANCE_RANGE,
            half_width_range=GLOBAL_HALF_WIDTH_RANGE,
            distance_count=GRID_DISTANCE_COUNT,
            half_width_count=GRID_HALF_WIDTH_COUNT,
        )
        if _bool(relaxed_after.get("feasible")):
            repaired = relaxed
            obstacle = relaxed_obstacle
            after = relaxed_after
            threshold_repaired = True
    if _bool(after.get("feasible")):
        obstacle["distance_range"] = [float(after["distance"]), float(after["distance"])]
        obstacle["half_width_range"] = [float(after["half_width"]), float(after["half_width"])]
        repaired["obstacle"] = obstacle
    repair_reason = ""
    if _bool(after.get("feasible")):
        repair_reason = "retarget_to_nearest_accepted_filter"
        if threshold_repaired:
            repair_reason += ";threshold_score_relaxed_to_1p0"
    return repaired, {
        "obstacle_filter_repaired": bool(after.get("feasible")),
        "obstacle_filter_repair_reason": repair_reason if repair_reason else "no_accepted_filter_found",
        "scenario_filter_feasible_before": False,
        "scenario_filter_feasible_after": bool(after.get("feasible")),
        "original_obstacle_distance_range": _range_to_string(original_distance),
        "original_obstacle_half_width_range": _range_to_string(original_half_width),
        "original_obstacle_max_threshold_score": original_threshold,
        "repaired_obstacle_distance_range": _range_to_string(obstacle.get("distance_range", original_distance)),
        "repaired_obstacle_half_width_range": _range_to_string(obstacle.get("half_width_range", original_half_width)),
        "repaired_obstacle_max_threshold_score": obstacle.get("max_threshold_score", ""),
        "scenario_filter_candidate_label": after["label"],
        "scenario_filter_candidate_score": after["threshold_score"],
        "scenario_filter_candidate_distance": after["distance"],
        "scenario_filter_candidate_half_width": after["half_width"],
    }


def repair_spec(spec: Mapping[str, Any], failure_row: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    failure_row = failure_row or {}
    seed = int(failure_row.get("eval_seed", 0) or 0)
    if seed <= 0:
        seed = 206600
    warmup_env, warmup_repair = repair_warmup_gate(spec)
    repaired_env, obstacle_repair = repair_obstacle_filter(env_config=warmup_env, seed=seed)
    build_env_config(repaired_env)
    checks = contract_checks(repaired_env)
    repaired_spec = dict(spec)
    repaired_spec["env_config"] = env_config_to_dict(build_env_config(repaired_env))
    repaired_spec["contract_checks"] = checks
    repaired_spec["contract_violation_count"] = int(sum(not bool(value) for value in checks.values()))
    repaired_spec["paper_validity_claim"] = False
    repaired_spec["profile_specific_tuning"] = False
    repaired_spec["controller_family_ranking_claim_made"] = False
    repaired_spec["finite_window_vs_gru_conclusion_made"] = False
    repaired_spec["paper_level_claim_made"] = False
    repaired_spec["level3_self_id_claim_made"] = False
    repair_row = {
        **metadata_for_spec(repaired_spec),
        "eval_seed": seed,
        "source_error_type": failure_row.get("error_type", ""),
        "source_error_message": failure_row.get("error_message", ""),
        **warmup_repair,
        **obstacle_repair,
    }
    repaired_spec["warmup_gate_repaired"] = bool(warmup_repair["warmup_gate_repaired"])
    repaired_spec["obstacle_filter_repaired"] = bool(obstacle_repair["obstacle_filter_repaired"])
    repaired_spec["scenario_filter_feasible_after"] = bool(obstacle_repair["scenario_filter_feasible_after"])
    return repaired_spec, repair_row


def _sentinel_profile_rows(profile_run_dir: Path | str) -> list[dict[str, Any]]:
    all_rows = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    by_name = {str(row["profile_name"]): row for row in all_rows}
    return [dict(by_name[name]) for name in SENTINEL_PROFILES if name in by_name]


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


def _axis_coverage_pass(specs: Iterable[Mapping[str, Any]]) -> bool:
    rows = list(specs)
    for family in FAMILY_TARGETS:
        family_rows = [row for row in rows if row["panel_task_family"] == family]
        for axis, expected_values in DIFFICULTY_AXES.items():
            if {str(row[axis]) for row in family_rows} != set(expected_values):
                return False
    return True


def _metadata_missing_count(specs: Iterable[Mapping[str, Any]]) -> int:
    required = {
        "task_source_id",
        "candidate_id",
        "candidate_set_id",
        "branch_id",
        "panel_task_family",
        "source_split",
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
        "materialization_semantics",
        "proxy_template_family",
    }
    return sum(1 for spec in specs if any(str(spec.get(field, "")).strip() == "" for field in required))


def claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "outcome_supported_decisive_repaired_materialization_preflight",
            "admissible": bool(passes),
            "reason": "repaired materialization is admissible only if no-reset repair gates pass",
        },
        {
            "claim": "reset_validity",
            "admissible": False,
            "reason": "reset validity requires a later reset-validation rerun",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and measured rollout remain blocked",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "repair preflight is task-quality infrastructure, not controller comparison",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated rows remain smoke proxies until later task-semantics validation",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "repair preflight does not test history necessity",
        },
    ]


def run_repair_preflight(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    reset_failure_rows_path: Path | str = DEFAULT_RESET_FAILURE_ROWS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    failure_rows = load_reset_failure_rows(reset_failure_rows_path)
    failure_by_id = {str(row.get("task_source_id", "")): dict(row) for row in failure_rows}

    repaired_specs: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    for spec in specs:
        repaired_spec, repair_row = repair_spec(spec, failure_by_id.get(str(spec.get("task_source_id", ""))))
        repaired_specs.append(repaired_spec)
        repair_rows.append(repair_row)

    workload_rows, profile_rows = planned_sentinel_workload_rows(repaired_specs, profile_run_dir=profile_run_dir)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    family_counts = {family: 0 for family in FAMILY_TARGETS}
    family_counts.update(_count_by(repaired_specs, "panel_task_family"))
    split_counts = {split: 0 for split in SPLIT_TARGETS}
    split_counts.update(_count_by(repaired_specs, "source_split"))
    zero_invalid_after = sum(zero_step_warmup_gate_invalid(spec["env_config"]) for spec in repaired_specs)
    feasible_after_count = sum(_bool(row.get("scenario_filter_feasible_after")) for row in repair_rows)
    infeasible_after_count = len(repair_rows) - feasible_after_count
    warmup_repaired_count = sum(_bool(row.get("warmup_gate_repaired")) for row in repair_rows)
    obstacle_repaired_count = sum(_bool(row.get("obstacle_filter_repaired")) for row in repair_rows)
    contract_violation_count = sum(int(spec.get("contract_violation_count", 0)) for spec in repaired_specs)
    metadata_missing_count = _metadata_missing_count(repaired_specs)
    forbidden_hits = forbidden_key_violations(repaired_specs)
    profile_missing_count = sum(1 for row in profile_rows if not (row["config_exists"] and row["checkpoint_exists"]))

    passes = (
        len(specs) == TARGET_EXECUTABLE_SPECS
        and len(repaired_specs) == TARGET_EXECUTABLE_SPECS
        and len(workload_rows) == TARGET_SENTINEL_WORKLOAD
        and len(profile_rows) == TARGET_SENTINEL_PROFILE_COUNT
        and zero_invalid_after == 0
        and feasible_after_count == len(repair_rows)
        and infeasible_after_count == 0
        and warmup_repaired_count >= 117
        and obstacle_repaired_count >= 123
        and family_counts == FAMILY_TARGETS
        and split_counts == SPLIT_TARGETS
        and _axis_coverage_pass(repaired_specs)
        and contract_violation_count == 0
        and metadata_missing_count == 0
        and not forbidden_hits
        and profile_missing_count == 0
        and guardrail_violation_count == 0
    )

    write_json(
        output / "repaired_executable_task_specs.json",
        {"protocol": PROTOCOL_NAME, "executable_task_specs": repaired_specs},
    )
    write_csv_rows(
        output / "repaired_executable_task_specs.csv",
        [
            {
                **metadata_for_spec(spec),
                "warmup_gate_repaired": spec.get("warmup_gate_repaired", False),
                "obstacle_filter_repaired": spec.get("obstacle_filter_repaired", False),
                "scenario_filter_feasible_after": spec.get("scenario_filter_feasible_after", False),
                "contract_violation_count": spec.get("contract_violation_count", 0),
            }
            for spec in repaired_specs
        ],
        SPEC_CSV_FIELDNAMES,
    )
    write_csv_rows(output / "repair_rows.csv", repair_rows, REPAIR_FIELDNAMES)
    write_csv_rows(output / "planned_sentinel_workload.csv", workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(output / "family_distribution.csv", _aggregate_rows(family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "split_distribution.csv", _aggregate_rows(split_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "outcome_supported_decisive_reset_materialization_repair_preflight_pass"
            if passes
            else "outcome_supported_decisive_reset_materialization_repair_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "executable_task_specs_path": str(executable_task_specs_path),
        "reset_failure_rows_path": str(reset_failure_rows_path),
        "profile_run_dir": str(profile_run_dir),
        "input_executable_spec_count": len(specs),
        "repaired_executable_spec_count": len(repaired_specs),
        "target_executable_spec_count": TARGET_EXECUTABLE_SPECS,
        "planned_sentinel_workload_count": len(workload_rows),
        "target_sentinel_workload_count": TARGET_SENTINEL_WORKLOAD,
        "sentinel_profile_count": len(profile_rows),
        "target_sentinel_profile_count": TARGET_SENTINEL_PROFILE_COUNT,
        "zero_step_warmup_gate_invalid_count_after": int(zero_invalid_after),
        "scenario_filter_feasible_after_count": int(feasible_after_count),
        "scenario_filter_infeasible_after_count": int(infeasible_after_count),
        "warmup_gate_repaired_count": int(warmup_repaired_count),
        "obstacle_filter_repaired_count": int(obstacle_repaired_count),
        "family_counts": family_counts,
        "expected_family_counts": FAMILY_TARGETS,
        "family_quota_pass": family_counts == FAMILY_TARGETS,
        "split_counts": split_counts,
        "expected_split_counts": SPLIT_TARGETS,
        "split_quota_pass": split_counts == SPLIT_TARGETS,
        "difficulty_axis_coverage_pass": _axis_coverage_pass(repaired_specs),
        "contract_violation_count": int(contract_violation_count),
        "metadata_missing_count": int(metadata_missing_count),
        "forbidden_key_violation_count": len(forbidden_hits),
        "profile_missing_count": int(profile_missing_count),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": int(guardrail_violation_count),
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
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repaired_executable_task_specs": str(output / "repaired_executable_task_specs.json"),
            "repair_rows": str(output / "repair_rows.csv"),
            "planned_sentinel_workload": str(output / "planned_sentinel_workload.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--reset-failure-rows", type=Path, default=DEFAULT_RESET_FAILURE_ROWS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_repair_preflight(
        executable_task_specs_path=args.executable_task_specs,
        reset_failure_rows_path=args.reset_failure_rows,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_executable_spec_count={summary['input_executable_spec_count']}")
    print(f"repaired_executable_spec_count={summary['repaired_executable_spec_count']}")
    print(f"zero_step_warmup_gate_invalid_count_after={summary['zero_step_warmup_gate_invalid_count_after']}")
    print(f"scenario_filter_feasible_after_count={summary['scenario_filter_feasible_after_count']}")
    print(f"scenario_filter_infeasible_after_count={summary['scenario_filter_infeasible_after_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
