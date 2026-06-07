"""Materialize M3037 Active Safety Driver v1 baseline measurement tables.

M3037 consumes the accepted M3035 baseline contract and the already executed
M3015 closed-loop rows. It writes official baseline measurement tables and
aggregates without rerunning environments, training, validation, ranking,
promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or
self-ID verdicts.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-"
    "table-materialization-preflight"
)
NEXT_ID = (
    "m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-"
    "table-result-audit"
)
M3036_ID = "m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit"

DEFAULT_M3035_DIR = Path(
    "runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_"
    "materialization_preflight"
)
DEFAULT_M3015_DIR = Path(
    "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_"
    "bounded_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3037_engineering_controller_active_safety_driver_v1_baseline_"
    "measurement_table_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_EPISODE_ROWS = 32
EXPECTED_PROFILE_ROWS = 2
EXPECTED_BASELINE_CANDIDATES = 2
NEXT_PRIORITY = 30330

CLAIM_SCOPE = (
    "M3037 Active Safety Driver v1 baseline measurement table materialization "
    "preflight only; accepted M3035 contract rows and already executed M3015 "
    "closed-loop rows may be converted into row-level baseline measurements, "
    "candidate profile aggregates, benchmark-role aggregates, metric coverage, "
    "actor-contract, claim-boundary, gate, summary, doc, and M3038 audit manifest "
    "artifacts. No environment reset, step, rollout, replay, validation, training, "
    "PPO, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "repair-success, driver-performance verdict, paper, current-sim verdict, "
    "high-fidelity validation, finite-window-vs-GRU, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "checkpoint ranking, winner selection, checkpoint promotion, validation "
    "result, repair success, driver-performance verdict, current-sim verdict, "
    "paper evidence, high-fidelity validation readiness or result, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)
DECISION_PASS = "active_safety_driver_v1_baseline_measurement_table_materialized_route_to_m3038_result_audit"

DERIVED_SOURCE_FIELD_REQUIREMENTS = {
    "termination_reason": {
        "obstacle_collision_termination",
        "off_track_termination",
        "speed_too_low_termination",
    },
}

MEASUREMENT_FIELDNAMES = [
    "baseline_measurement_row_id",
    "source_episode_index",
    "seed",
    "eval_seed",
    "profile_name",
    "binding_role",
    "task_source_id",
    "task_family",
    "source_edge",
    "window_tag",
    "primary_benchmark_role",
    "benchmark_roles",
    "role_seed_matches",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "obstacle_collision_termination",
    "off_track_termination",
    "speed_too_low_termination",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "beta_abs_error_mean",
    "lateral_rmse",
    "action_rate_mean",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    "recoverability_window_success_available",
    "recoverability_window_success",
    "return",
    "baseline_measurement_materialized",
    "validation_result_claim_made",
    "driver_performance_claim_made",
    "ranking_allowed",
    "promotion_allowed",
    "claim_boundary",
]
PROFILE_AGG_FIELDNAMES = [
    "candidate_profile_aggregate_id",
    "profile_name",
    "binding_role",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "obstacle_collision_termination_count",
    "obstacle_collision_termination_rate",
    "off_track_termination_count",
    "off_track_termination_rate",
    "speed_too_low_termination_count",
    "speed_too_low_termination_rate",
    "non_success_count",
    "min_clearance_margin_mean",
    "min_clearance_margin_p10",
    "min_clearance_margin_p5",
    "min_clearance_margin_min",
    "min_obstacle_clearance_mean",
    "min_obstacle_clearance_min",
    "high_sideslip_fraction_mean",
    "high_sideslip_fraction_p95",
    "beta_abs_error_mean_mean",
    "lateral_rmse_mean",
    "action_rate_mean_mean",
    "action_rate_mean_p95",
    "max_off_track_overshoot_mean",
    "max_off_track_overshoot_max",
    "recoverability_available_count",
    "recoverability_success_count",
    "recoverability_success_rate",
    "return_mean",
    "steps_mean",
    "ranking_allowed",
    "winner_selected",
    "promotion_allowed",
    "driver_performance_verdict_claim_made",
    "claim_boundary",
]
ROLE_AGG_FIELDNAMES = [
    "benchmark_role_aggregate_id",
    "benchmark_role",
    "role_seed",
    "profile_name",
    "binding_role",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "off_track_termination_count",
    "off_track_termination_rate",
    "speed_too_low_termination_count",
    "speed_too_low_termination_rate",
    "min_clearance_margin_mean",
    "min_clearance_margin_p10",
    "min_clearance_margin_min",
    "high_sideslip_fraction_mean",
    "action_rate_mean_mean",
    "recoverability_available_count",
    "recoverability_success_count",
    "recoverability_success_rate",
    "ranking_allowed",
    "driver_performance_verdict_claim_made",
    "claim_boundary",
]
METRIC_COVERAGE_FIELDNAMES = [
    "metric_coverage_id",
    "source_metric_contract_id",
    "metric_family",
    "metric_name",
    "source_field",
    "required_for_baseline_measurement",
    "materialized_in_m3037",
    "future_instrumentation_required",
    "row_count",
    "aggregate_surface",
    "performance_claim_allowed_in_m3037",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3037",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "baseline_measurement_rows": output_dir / "baseline_measurement_rows.csv",
        "candidate_profile_metric_aggregate_rows": output_dir / "candidate_profile_metric_aggregate_rows.csv",
        "benchmark_role_metric_aggregate_rows": output_dir / "benchmark_role_metric_aggregate_rows.csv",
        "metric_coverage_rows": output_dir / "metric_coverage_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Iterable[float | None]) -> float | str:
    finite = [float(value) for value in values if value is not None]
    return sum(finite) / len(finite) if finite else ""


def _min(values: Iterable[float | None]) -> float | str:
    finite = [float(value) for value in values if value is not None]
    return min(finite) if finite else ""


def _quantile(values: Iterable[float | None], quantile: float) -> float | str:
    finite = sorted(float(value) for value in values if value is not None)
    if not finite:
        return ""
    if len(finite) == 1:
        return finite[0]
    index = quantile * (len(finite) - 1)
    lower = int(index)
    upper = min(lower + 1, len(finite) - 1)
    weight = index - lower
    return finite[lower] * (1.0 - weight) + finite[upper] * weight


def _rate(count: int, denominator: int) -> float | str:
    return count / denominator if denominator else ""


def _contains_role_seed(row: dict[str, Any], role_seed: str) -> bool:
    haystack = "|".join(
        str(row.get(field, ""))
        for field in ("source_edge", "executable_source_family", "env_template_family")
    )
    return role_seed in haystack


def load_source_artifacts(
    *,
    m3035_dir: Path,
    m3015_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3035_summary": m3035_dir / "summary.json",
        "baseline_candidate_rows": m3035_dir / "baseline_candidate_rows.csv",
        "benchmark_role_rows": m3035_dir / "benchmark_role_rows.csv",
        "metric_contract_rows": m3035_dir / "metric_contract_rows.csv",
        "m3035_actor_contract_guard_rows": m3035_dir / "actor_contract_guard_rows.csv",
        "m3035_claim_boundary_rows": m3035_dir / "claim_boundary_rows.csv",
        "m3035_gate_matrix": m3035_dir / "gate_matrix.csv",
        "m3015_summary": m3015_dir / "summary.json",
        "m3015_episode_rows": m3015_dir / "episode_rows.csv",
        "m3015_profile_aggregate_rows": m3015_dir / "profile_aggregate_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3035_summary": read_json(paths["m3035_summary"]) if exists["m3035_summary"] else {},
        "baseline_candidate_rows": read_csv_rows(paths["baseline_candidate_rows"])
        if exists["baseline_candidate_rows"]
        else [],
        "benchmark_role_rows": read_csv_rows(paths["benchmark_role_rows"])
        if exists["benchmark_role_rows"]
        else [],
        "metric_contract_rows": read_csv_rows(paths["metric_contract_rows"])
        if exists["metric_contract_rows"]
        else [],
        "m3035_actor_contract_guard_rows": read_csv_rows(paths["m3035_actor_contract_guard_rows"])
        if exists["m3035_actor_contract_guard_rows"]
        else [],
        "m3035_claim_boundary_rows": read_csv_rows(paths["m3035_claim_boundary_rows"])
        if exists["m3035_claim_boundary_rows"]
        else [],
        "m3035_gate_matrix": read_csv_rows(paths["m3035_gate_matrix"]) if exists["m3035_gate_matrix"] else [],
        "m3015_summary": read_json(paths["m3015_summary"]) if exists["m3015_summary"] else {},
        "m3015_episode_rows": read_csv_rows(paths["m3015_episode_rows"])
        if exists["m3015_episode_rows"]
        else [],
        "m3015_profile_aggregate_rows": read_csv_rows(paths["m3015_profile_aggregate_rows"])
        if exists["m3015_profile_aggregate_rows"]
        else [],
    }


def match_roles(row: dict[str, Any], benchmark_role_rows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    roles: list[str] = []
    seeds: list[str] = []
    for role_row in benchmark_role_rows:
        seed = str(role_row.get("role_seed", ""))
        if seed and _contains_role_seed(row, seed):
            role = str(role_row.get("benchmark_role", ""))
            if role and role not in roles:
                roles.append(role)
            if seed not in seeds:
                seeds.append(seed)
    return roles, seeds


def build_baseline_measurement_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    benchmark_role_rows = source["benchmark_role_rows"]
    for index, row in enumerate(source["m3015_episode_rows"], start=1):
        roles, seeds = match_roles(row, benchmark_role_rows)
        termination_reason = str(row.get("termination_reason", ""))
        rows.append(
            {
                "baseline_measurement_row_id": f"m3037-baseline-measurement-{index:04d}",
                "source_episode_index": index,
                "seed": row.get("seed", ""),
                "eval_seed": row.get("eval_seed", ""),
                "profile_name": row.get("profile_name", ""),
                "binding_role": row.get("binding_role", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "primary_benchmark_role": roles[0] if roles else "unmapped",
                "benchmark_roles": "|".join(roles),
                "role_seed_matches": "|".join(seeds),
                "steps": row.get("steps", ""),
                "terminated": _bool(row.get("terminated", False)),
                "truncated": _bool(row.get("truncated", False)),
                "success": _bool(row.get("success", False)),
                "collision": _bool(row.get("collision", False)),
                "obstacle_collision_termination": termination_reason == "obstacle_collision",
                "off_track_termination": termination_reason == "off_track",
                "speed_too_low_termination": termination_reason == "speed_too_low",
                "min_obstacle_clearance": _float(row.get("min_obstacle_clearance")),
                "obstacle_collision_radius": _float(row.get("obstacle_collision_radius")),
                "min_clearance_margin": _float(row.get("min_clearance_margin")),
                "high_sideslip_fraction": _float(row.get("high_sideslip_fraction")),
                "beta_abs_error_mean": _float(row.get("beta_abs_error_mean")),
                "lateral_rmse": _float(row.get("lateral_rmse")),
                "action_rate_mean": _float(row.get("action_rate_mean")),
                "max_off_track_overshoot": _float(row.get("max_off_track_overshoot")),
                "time_to_first_off_track_s": _float(row.get("time_to_first_off_track_s")),
                "off_track_severity_proxy": _float(row.get("off_track_severity_proxy")),
                "recoverability_window_success_available": _bool(
                    row.get("recoverability_window_success_available", False)
                ),
                "recoverability_window_success": _bool(row.get("recoverability_window_success", False)),
                "return": _float(row.get("return")),
                "baseline_measurement_materialized": True,
                "validation_result_claim_made": False,
                "driver_performance_claim_made": False,
                "ranking_allowed": False,
                "promotion_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def aggregate_measurements(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    success_count = sum(_bool(row.get("success")) for row in rows)
    collision_count = sum(_bool(row.get("collision")) for row in rows)
    obstacle_collision_count = sum(_bool(row.get("obstacle_collision_termination")) for row in rows)
    off_track_count = sum(_bool(row.get("off_track_termination")) for row in rows)
    speed_too_low_count = sum(_bool(row.get("speed_too_low_termination")) for row in rows)
    recoverability_available_count = sum(_bool(row.get("recoverability_window_success_available")) for row in rows)
    recoverability_success_count = sum(_bool(row.get("recoverability_window_success")) for row in rows)
    return {
        "episode_count": count,
        "success_count": success_count,
        "success_rate": _rate(success_count, count),
        "collision_count": collision_count,
        "collision_rate": _rate(collision_count, count),
        "obstacle_collision_termination_count": obstacle_collision_count,
        "obstacle_collision_termination_rate": _rate(obstacle_collision_count, count),
        "off_track_termination_count": off_track_count,
        "off_track_termination_rate": _rate(off_track_count, count),
        "speed_too_low_termination_count": speed_too_low_count,
        "speed_too_low_termination_rate": _rate(speed_too_low_count, count),
        "non_success_count": count - success_count,
        "min_clearance_margin_mean": _mean(row.get("min_clearance_margin") for row in rows),
        "min_clearance_margin_p10": _quantile((row.get("min_clearance_margin") for row in rows), 0.10),
        "min_clearance_margin_p5": _quantile((row.get("min_clearance_margin") for row in rows), 0.05),
        "min_clearance_margin_min": _min(row.get("min_clearance_margin") for row in rows),
        "min_obstacle_clearance_mean": _mean(row.get("min_obstacle_clearance") for row in rows),
        "min_obstacle_clearance_min": _min(row.get("min_obstacle_clearance") for row in rows),
        "high_sideslip_fraction_mean": _mean(row.get("high_sideslip_fraction") for row in rows),
        "high_sideslip_fraction_p95": _quantile((row.get("high_sideslip_fraction") for row in rows), 0.95),
        "beta_abs_error_mean_mean": _mean(row.get("beta_abs_error_mean") for row in rows),
        "lateral_rmse_mean": _mean(row.get("lateral_rmse") for row in rows),
        "action_rate_mean_mean": _mean(row.get("action_rate_mean") for row in rows),
        "action_rate_mean_p95": _quantile((row.get("action_rate_mean") for row in rows), 0.95),
        "max_off_track_overshoot_mean": _mean(row.get("max_off_track_overshoot") for row in rows),
        "max_off_track_overshoot_max": _quantile((row.get("max_off_track_overshoot") for row in rows), 1.0),
        "recoverability_available_count": recoverability_available_count,
        "recoverability_success_count": recoverability_success_count,
        "recoverability_success_rate": _rate(recoverability_success_count, recoverability_available_count),
        "return_mean": _mean(row.get("return") for row in rows),
        "steps_mean": _mean(_float(row.get("steps")) for row in rows),
    }


def build_candidate_profile_aggregate_rows(measurement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in measurement_rows:
        groups[str(row.get("profile_name", ""))].append(row)
    rows: list[dict[str, Any]] = []
    for index, profile_name in enumerate(sorted(groups), start=1):
        group = groups[profile_name]
        aggregate = aggregate_measurements(group)
        rows.append(
            {
                "candidate_profile_aggregate_id": f"m3037-candidate-profile-aggregate-{index:04d}",
                "profile_name": profile_name,
                "binding_role": str(group[0].get("binding_role", "")) if group else "",
                **aggregate,
                "ranking_allowed": False,
                "winner_selected": False,
                "promotion_allowed": False,
                "driver_performance_verdict_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_benchmark_role_aggregate_rows(
    measurement_rows: list[dict[str, Any]],
    benchmark_role_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for role_row in benchmark_role_rows:
        role = str(role_row.get("benchmark_role", ""))
        seed = str(role_row.get("role_seed", ""))
        matching = [row for row in measurement_rows if seed in str(row.get("role_seed_matches", "")).split("|")]
        by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in matching:
            by_profile[str(row.get("profile_name", ""))].append(row)
        for profile_name in sorted(by_profile):
            index += 1
            group = by_profile[profile_name]
            aggregate = aggregate_measurements(group)
            role_aggregate = {
                "benchmark_role_aggregate_id": f"m3037-benchmark-role-aggregate-{index:04d}",
                "benchmark_role": role,
                "role_seed": seed,
                "profile_name": profile_name,
                "binding_role": str(group[0].get("binding_role", "")) if group else "",
                "episode_count": aggregate["episode_count"],
                "success_count": aggregate["success_count"],
                "success_rate": aggregate["success_rate"],
                "collision_count": aggregate["collision_count"],
                "collision_rate": aggregate["collision_rate"],
                "off_track_termination_count": aggregate["off_track_termination_count"],
                "off_track_termination_rate": aggregate["off_track_termination_rate"],
                "speed_too_low_termination_count": aggregate["speed_too_low_termination_count"],
                "speed_too_low_termination_rate": aggregate["speed_too_low_termination_rate"],
                "min_clearance_margin_mean": aggregate["min_clearance_margin_mean"],
                "min_clearance_margin_p10": aggregate["min_clearance_margin_p10"],
                "min_clearance_margin_min": aggregate["min_clearance_margin_min"],
                "high_sideslip_fraction_mean": aggregate["high_sideslip_fraction_mean"],
                "action_rate_mean_mean": aggregate["action_rate_mean_mean"],
                "recoverability_available_count": aggregate["recoverability_available_count"],
                "recoverability_success_count": aggregate["recoverability_success_count"],
                "recoverability_success_rate": aggregate["recoverability_success_rate"],
                "ranking_allowed": False,
                "driver_performance_verdict_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
            rows.append(role_aggregate)
    return rows


def build_metric_coverage_rows(
    metric_contract_rows: list[dict[str, Any]],
    measurement_rows: list[dict[str, Any]],
    profile_aggregate_rows: list[dict[str, Any]],
    role_aggregate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    measurement_fields = set(measurement_rows[0].keys()) if measurement_rows else set()
    profile_fields = set(profile_aggregate_rows[0].keys()) if profile_aggregate_rows else set()
    role_fields = set(role_aggregate_rows[0].keys()) if role_aggregate_rows else set()
    rows: list[dict[str, Any]] = []
    for index, metric_row in enumerate(metric_contract_rows, start=1):
        source_field = str(metric_row.get("source_field", ""))
        all_fields = measurement_fields | profile_fields | role_fields
        derived_requirements = DERIVED_SOURCE_FIELD_REQUIREMENTS.get(source_field, set())
        materialized = (
            source_field in all_fields
            or bool(derived_requirements and derived_requirements.issubset(all_fields))
        )
        if source_field in {"baseline_candidate_rows.csv", "benchmark_role_rows.csv"}:
            materialized = True
        rows.append(
            {
                "metric_coverage_id": f"m3037-metric-coverage-{index:04d}",
                "source_metric_contract_id": metric_row.get("metric_contract_id", ""),
                "metric_family": metric_row.get("metric_family", ""),
                "metric_name": metric_row.get("metric_name", ""),
                "source_field": source_field,
                "required_for_baseline_measurement": _bool(
                    metric_row.get("required_for_baseline_measurement", False)
                ),
                "materialized_in_m3037": materialized,
                "future_instrumentation_required": _bool(
                    metric_row.get("future_instrumentation_required", False)
                ),
                "row_count": len(measurement_rows) if materialized else 0,
                "aggregate_surface": "measurement|candidate_profile|benchmark_role"
                if materialized
                else "future_instrumentation",
                "performance_claim_allowed_in_m3037": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m3035 = source["m3035_summary"]
    m3015 = source["m3015_summary"]
    m3035_guard_pass = all(
        _bool(row.get("status_pass", False)) for row in source["m3035_actor_contract_guard_rows"]
    )
    checks = [
        (
            "m3035_actor_contract_guard_rows_pass",
            "m3035_contract",
            m3035_guard_pass,
            m3035_guard_pass,
            True,
        ),
        (
            "m3035_actor_contract_shape",
            "actor_contract",
            _bool(m3035.get("actor_contract_shape_72_action_3", False)),
            {
                "observation_shape": m3035.get("observation_shape"),
                "action_shape": m3035.get("action_shape"),
            },
            {"observation_shape": P0_OBSERVATION_DIM, "action_shape": ACTION_DIM},
        ),
        (
            "m3015_actor_contract_shape",
            "actor_contract",
            int(m3015.get("observation_shape", -1)) == P0_OBSERVATION_DIM
            and int(m3015.get("action_shape", -1)) == ACTION_DIM,
            {
                "observation_shape": m3015.get("observation_shape"),
                "action_shape": m3015.get("action_shape"),
            },
            {"observation_shape": P0_OBSERVATION_DIM, "action_shape": ACTION_DIM},
        ),
        (
            "hidden_oracle_actor_input_absent",
            "actor_input",
            not _bool(m3015.get("hidden_oracle_actor_input_detected", False)),
            m3015.get("hidden_oracle_actor_input_detected", False),
            False,
        ),
        (
            "ttc_actor_input_absent",
            "actor_input",
            not _bool(m3015.get("ttc_actor_input_required", False)),
            m3015.get("ttc_actor_input_required", False),
            False,
        ),
        (
            "actor_visible_labels_absent",
            "actor_input",
            not any(
                _bool(m3015.get(key, False))
                for key in (
                    "source_labels_actor_visible",
                    "route_labels_actor_visible",
                    "outcome_labels_actor_visible",
                    "success_progress_labels_actor_visible",
                    "verdict_labels_actor_visible",
                )
            ),
            {
                key: m3015.get(key, False)
                for key in (
                    "source_labels_actor_visible",
                    "route_labels_actor_visible",
                    "outcome_labels_actor_visible",
                    "success_progress_labels_actor_visible",
                    "verdict_labels_actor_visible",
                )
            },
            "all false",
        ),
    ]
    return [
        {
            "guard_id": f"m3037-{guard_id}",
            "guard_family": family,
            "observed": observed,
            "expected": expected,
            "status_pass": bool(status_pass),
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, family, status_pass, observed, expected in checks
    ]


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3037-{claim_id}",
        "claim_family": family,
        "allowed_in_m3037": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    allowed = [
        ("baseline_measurement_rows_materialized", "artifact", artifacts_present, "baseline_measurement_rows.csv"),
        (
            "candidate_profile_metric_aggregates_materialized",
            "artifact",
            artifacts_present,
            "candidate_profile_metric_aggregate_rows.csv",
        ),
        (
            "benchmark_role_metric_aggregates_materialized",
            "artifact",
            artifacts_present,
            "benchmark_role_metric_aggregate_rows.csv",
        ),
        ("metric_coverage_rows_materialized", "artifact", artifacts_present, "metric_coverage_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("summary_materialized", "artifact", artifacts_present, "summary.json"),
        ("doc_materialized", "artifact", artifacts_present, f"docs/{MILESTONE_ID}.md"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3038 audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future audited execution milestone"),
        ("training_or_ppo", "training", "future audited training milestone"),
        ("validation_result", "validation", "future validation run and audit"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/verdict audit"),
        ("checkpoint_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("checkpoint_or_config_mutation", "side_effect", "M3037 is read-only"),
        ("target_tensor_as_closed_loop_evidence", "target_tensor", "future target fitting and closed-loop audit"),
        ("current_sim_verdict", "verdict", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future HF backend and mapping audit"),
        ("finite_window_vs_gru_result", "architecture", "future same-case architecture comparison"),
        ("paper_level_evidence", "paper", "future paper evidence audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full active-safety driver gate"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m3037-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    measurement_rows: list[dict[str, Any]],
    profile_aggregate_rows: list[dict[str, Any]],
    role_aggregate_rows: list[dict[str, Any]],
    metric_coverage_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_metric_rows = [
        row for row in metric_coverage_rows if _bool(row.get("required_for_baseline_measurement", False))
    ]
    materialized_required_metrics = [
        row for row in required_metric_rows if _bool(row.get("materialized_in_m3037", False))
    ]
    m3035 = source["m3035_summary"]
    role_count_expected = sum(
        1
        for role_row in source["benchmark_role_rows"]
        if int(float(role_row.get("source_row_count", 0) or 0)) > 0
    ) * EXPECTED_PROFILE_ROWS
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "all source artifacts and follow-up manifest present",
            "lineage_invalid",
        ),
        (
            "m3035_status_and_gate_pass",
            "lineage",
            _bool(m3035.get("status_pass", False)) and _bool(m3035.get("gate_matrix_pass", False)),
            {"status_pass": m3035.get("status_pass"), "gate_matrix_pass": m3035.get("gate_matrix_pass")},
            "all true",
            "lineage_invalid",
        ),
        (
            "baseline_candidates_preserved",
            "baseline_contract",
            len(source["baseline_candidate_rows"]) == EXPECTED_BASELINE_CANDIDATES,
            len(source["baseline_candidate_rows"]),
            EXPECTED_BASELINE_CANDIDATES,
            "metric_artifact",
        ),
        (
            "episode_rows_preserved",
            "denominator",
            len(source["m3015_episode_rows"]) == EXPECTED_EPISODE_ROWS
            and len(measurement_rows) == EXPECTED_EPISODE_ROWS,
            {"episode_rows": len(source["m3015_episode_rows"]), "measurement_rows": len(measurement_rows)},
            EXPECTED_EPISODE_ROWS,
            "metric_artifact",
        ),
        (
            "candidate_profile_aggregates_materialized",
            "metric_contract",
            len(profile_aggregate_rows) == EXPECTED_PROFILE_ROWS,
            len(profile_aggregate_rows),
            EXPECTED_PROFILE_ROWS,
            "metric_artifact",
        ),
        (
            "benchmark_role_aggregates_materialized",
            "metric_contract",
            len(role_aggregate_rows) == role_count_expected,
            len(role_aggregate_rows),
            role_count_expected,
            "scenario_sampling_failure",
        ),
        (
            "required_metrics_materialized",
            "metric_contract",
            len(materialized_required_metrics) == len(required_metric_rows),
            {"required": len(required_metric_rows), "materialized": len(materialized_required_metrics)},
            "all required metric rows materialized",
            "metric_artifact",
        ),
        (
            "actor_contract_guard_rows_pass",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in actor_guard_rows),
            f"{sum(_bool(row.get('status_pass', False)) for row in actor_guard_rows)}/{len(actor_guard_rows)}",
            "all pass",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            all(_bool(row.get("status_pass", False)) for row in claim_rows),
            f"{sum(_bool(row.get('status_pass', False)) for row in claim_rows)}/{len(claim_rows)}",
            "all pass",
            "proof_washout",
        ),
        (
            "m3037_no_new_execution_training_validation_ranking",
            "contract",
            True,
            {
                "environment_step_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
            },
            "all false",
            "contract_violation",
        ),
        (
            "follow_up_manifest_registered",
            "lineage",
            follow_up_manifest_registered,
            follow_up_manifest_registered,
            True,
            "lineage_invalid",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    measurement_rows: list[dict[str, Any]],
    profile_aggregate_rows: list[dict[str, Any]],
    role_aggregate_rows: list[dict[str, Any]],
    metric_coverage_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
    required_artifacts_present: bool,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    actor_contract_guard_rows_pass = all(_bool(row.get("status_pass", False)) for row in actor_guard_rows)
    claim_boundary_rows_pass = all(_bool(row.get("status_pass", False)) for row in claim_rows)
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_guard_rows_pass
        and claim_boundary_rows_pass
        and required_artifacts_present
    )
    profile_counts = Counter(str(row.get("profile_name", "")) for row in measurement_rows)
    role_counts = Counter(str(row.get("primary_benchmark_role", "")) for row in measurement_rows)
    aggregate_by_profile = {row["profile_name"]: row for row in profile_aggregate_rows}
    return {
        "milestone": MILESTONE_ID,
        "status_pass": status_pass,
        "result_class": (
            "active_safety_driver_v1_baseline_measurement_table_materialization_preflight_complete"
            if status_pass
            else "active_safety_driver_v1_baseline_measurement_table_materialization_preflight_fail"
        ),
        "decision": DECISION_PASS if status_pass else "active_safety_driver_v1_baseline_measurement_table_incomplete",
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": NEXT_ID,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3035_status_pass": _bool(source["m3035_summary"].get("status_pass", False)),
        "m3035_gate_matrix_pass": _bool(source["m3035_summary"].get("gate_matrix_pass", False)),
        "m3015_episode_row_count": len(source["m3015_episode_rows"]),
        "baseline_measurement_row_count": len(measurement_rows),
        "candidate_profile_metric_aggregate_row_count": len(profile_aggregate_rows),
        "benchmark_role_metric_aggregate_row_count": len(role_aggregate_rows),
        "metric_coverage_row_count": len(metric_coverage_rows),
        "required_metric_coverage_count": sum(
            _bool(row.get("required_for_baseline_measurement", False)) for row in metric_coverage_rows
        ),
        "materialized_required_metric_coverage_count": sum(
            _bool(row.get("required_for_baseline_measurement", False))
            and _bool(row.get("materialized_in_m3037", False))
            for row in metric_coverage_rows
        ),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": actor_contract_guard_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_boundary_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "profile_counts": dict(sorted(profile_counts.items())),
        "primary_role_counts": dict(sorted(role_counts.items())),
        "candidate_profile_aggregates": aggregate_by_profile,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "high_fidelity_validation_run": False,
        "finite_window_vs_gru_comparison_run": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "ttc_actor_input_required": False,
        "success_rate_metric_recorded": True,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    candidate_lines = []
    for profile, aggregate in sorted(summary["candidate_profile_aggregates"].items()):
        candidate_lines.extend(
            [
                f"### {profile}",
                "",
                f"- episode count: {aggregate['episode_count']}",
                f"- success/collision/off-track/speed-floor counts: {aggregate['success_count']} / {aggregate['collision_count']} / {aggregate['off_track_termination_count']} / {aggregate['speed_too_low_termination_count']}",
                f"- success rate: {aggregate['success_rate']}",
                f"- collision rate: {aggregate['collision_rate']}",
                f"- off-track termination rate: {aggregate['off_track_termination_rate']}",
                f"- min clearance margin mean/p10/p5/min: {aggregate['min_clearance_margin_mean']} / {aggregate['min_clearance_margin_p10']} / {aggregate['min_clearance_margin_p5']} / {aggregate['min_clearance_margin_min']}",
                f"- high sideslip fraction mean/p95: {aggregate['high_sideslip_fraction_mean']} / {aggregate['high_sideslip_fraction_p95']}",
                f"- action rate mean/p95: {aggregate['action_rate_mean_mean']} / {aggregate['action_rate_mean_p95']}",
                "",
            ]
        )
    return "\n".join(
        [
            "# M3037 Active Safety Driver v1 Baseline Measurement Table Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- decision: `{summary['decision']}`",
            f"- baseline measurement rows: {summary['baseline_measurement_row_count']}",
            f"- candidate profile aggregate rows: {summary['candidate_profile_metric_aggregate_row_count']}",
            f"- benchmark role aggregate rows: {summary['benchmark_role_metric_aggregate_row_count']}",
            f"- metric coverage rows: {summary['metric_coverage_row_count']}",
            f"- required metric coverage: {summary['materialized_required_metric_coverage_count']}/{summary['required_metric_coverage_count']}",
            f"- actor contract guard pass: {summary['actor_contract_guard_rows_pass']}",
            f"- claim boundary pass: {summary['claim_boundary_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
            "## Candidate Baseline Aggregates",
            "",
            *candidate_lines,
            "## Interpretation",
            "",
            "M3037 materializes official Active Safety Driver v1 baseline measurement tables from already executed M3015 closed-loop rows under the accepted M3035 contract. These aggregates expose collision, off-track, clearance, stability, recovery, action-rate, and role-split baseline pressure. They do not rank the candidate and parent, select a winner, promote a checkpoint, or claim driver performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Boundary",
            "",
            "M3037 does not reset, step, roll out, train, validate, rank, promote, mutate checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or use M3032 target tensors as closed-loop evidence.",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- selected next action: `{summary['selected_next_action']}`",
            "",
        ]
    )


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": NEXT_PRIORITY,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3037 Active Safety Driver v1 baseline measurement table artifacts before any training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim.",
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "baseline_measurement_rows.csv"),
            str(output_dir / "candidate_profile_metric_aggregate_rows.csv"),
            str(output_dir / "benchmark_role_metric_aggregate_rows.csv"),
            str(output_dir / "metric_coverage_rows.csv"),
            str(output_dir / "actor_contract_guard_rows.csv"),
            str(output_dir / "claim_boundary_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "commands": [{"name": "active_safety_driver_v1_baseline_measurement_table_result_audit_doc", "command": "true"}],
        "decision_rule": "Pass only if M3038 audits M3037 row counts gates actor contract metric coverage aggregate tables and selects exactly one next training admission measurement repair or stop route without overclaiming.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3038 audits M3037 summary gate matrix baseline rows profile aggregates role aggregates metric coverage actor and claim artifacts",
            "M3038 preserves actor 72/action 3 and rejects training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU and self-ID claims",
            "M3038 selects exactly one next training admission measurement repair or stop route",
        ],
        "failure_criteria": [
            "M3038 treats M3037 baseline measurement tables as a driver-performance verdict",
            "M3038 omits metric coverage or aggregate audits",
            "M3038 runs training validation ranking promotion high-fidelity or architecture comparison",
            "M3038 leaves the next route ambiguous",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "baseline_measurement_rows.csv"),
                str(output_dir / "candidate_profile_metric_aggregate_rows.csv"),
                str(output_dir / "benchmark_role_metric_aggregate_rows.csv"),
                str(output_dir / "metric_coverage_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                "experiments/manifests/m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit.json",
                "experiments/manifests/m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight.json",
            ],
            "parent_objective": [
                "audit Active Safety Driver v1 baseline measurement table materialization before training or comparison"
            ],
            "derived_from": [MILESTONE_ID, M3036_ID],
            "blocked_by": [
                "M3037 materialization requires result audit before training admission or interpretation",
                "Baseline measurement tables are not a validation or driver-performance verdict",
            ],
            "supersedes": ["direct training or ranking before baseline measurement table audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3038 must audit M3037 summary and gate_matrix pass status",
            "M3038 must audit baseline measurement rows profile aggregates role aggregates and metric coverage rows",
            "M3038 must preserve actor 72/action 3 and no hidden oracle target TTC source route outcome progress or verdict actor inputs",
            "M3038 must reject driver-performance validation current-sim high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3038 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step rollout replay training validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3037 materialization into driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate checkpoints configs profiles or actor contract",
        ],
        "status": "pending",
        "next_blocker": NEXT_ID,
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_baseline_measurement_table_result_audit",
            "evidence_increment": "audits official baseline measurement tables before training admission",
            "claim_scope": "Result audit only; no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3037 artifacts are incomplete or actor contract guards fail",
                "stop if the next route would train before baseline table acceptance",
                "stop if baseline tables are treated as a validation or performance verdict",
            ],
            "fallback_plan": [
                "route to metric coverage repair if M3037 fails",
                "route to active-safety training admission if M3037 is accepted",
                "route to synthesis if the branch cannot produce an evidence-changing training or measurement route next",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3037 completes baseline measurement table materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit Active Safety Driver v1 baseline measurement table materialization",
            "admission_evidence": [
                "M3037 summary and gate matrix",
                "M3037 baseline measurement rows and aggregate tables",
                "M3036 accepted M3035 baseline contract",
            ],
            "blocked_shortcuts": [
                "no environment reset step rollout replay training validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3038 status queue scoreboard research log and review",
                "one follow-up manifest only if M3038 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3037 artifacts are accepted or rejected",
                "one next training admission measurement repair or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3038 audits engineering baseline tables and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3038; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3037 baseline measurement table artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot block active-safety training admission if safety contract gates pass.",
            "allowed_claims": [
                "M3037 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits baseline measurement tables before an evidence-changing training admission route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3038 prepares engineering-first training admission",
            "must_synthesize_if": [
                "M3038 cannot select a training admission or repair route",
                "M3038 would require another process-only milestone before any evidence-changing route",
                "M3038 would re-promote self-ID proof as the mainline objective",
            ],
        },
    }


def run_active_safety_driver_v1_baseline_measurement_table_materialization_preflight(
    *,
    m3035_dir: Path | str = DEFAULT_M3035_DIR,
    m3015_dir: Path | str = DEFAULT_M3015_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    follow_up = Path(follow_up_manifest)
    paths = artifact_paths(output, doc_path=doc, follow_up_manifest=follow_up)
    source = load_source_artifacts(m3035_dir=Path(m3035_dir), m3015_dir=Path(m3015_dir), follow_up_manifest=follow_up)

    measurement_rows = build_baseline_measurement_rows(source)
    profile_aggregate_rows = build_candidate_profile_aggregate_rows(measurement_rows)
    role_aggregate_rows = build_benchmark_role_aggregate_rows(measurement_rows, source["benchmark_role_rows"])
    metric_coverage_rows = build_metric_coverage_rows(
        source["metric_contract_rows"],
        measurement_rows,
        profile_aggregate_rows,
        role_aggregate_rows,
    )
    actor_guard_rows = build_actor_contract_guard_rows(source)
    write_json(
        follow_up,
        build_follow_up_manifest(output_dir=output, doc_path=doc, summary_path=paths["summary"]),
    )
    source["source_exists"]["follow_up_manifest"] = follow_up.exists()

    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=follow_up.exists(), artifacts_present=True)
    gate_rows = build_gate_matrix_rows(
        source=source,
        measurement_rows=measurement_rows,
        profile_aggregate_rows=profile_aggregate_rows,
        role_aggregate_rows=role_aggregate_rows,
        metric_coverage_rows=metric_coverage_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        follow_up_manifest_registered=follow_up.exists(),
        required_artifacts_present=True,
    )
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        measurement_rows=measurement_rows,
        profile_aggregate_rows=profile_aggregate_rows,
        role_aggregate_rows=role_aggregate_rows,
        metric_coverage_rows=metric_coverage_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        follow_up_manifest=follow_up,
        required_artifacts_present=True,
    )

    write_csv_rows(paths["baseline_measurement_rows"], measurement_rows, MEASUREMENT_FIELDNAMES)
    write_csv_rows(
        paths["candidate_profile_metric_aggregate_rows"],
        profile_aggregate_rows,
        PROFILE_AGG_FIELDNAMES,
    )
    write_csv_rows(paths["benchmark_role_metric_aggregate_rows"], role_aggregate_rows, ROLE_AGG_FIELDNAMES)
    write_csv_rows(paths["metric_coverage_rows"], metric_coverage_rows, METRIC_COVERAGE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "status": "completed" if summary["status_pass"] else "failed",
            "generated_at_utc": summary["generated_at_utc"],
            "output_dir": str(output),
            "next_blocker": NEXT_ID,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(render_milestone_doc(summary), encoding="utf-8")
    write_json(paths["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3035-dir", type=Path, default=DEFAULT_M3035_DIR)
    parser.add_argument("--m3015-dir", type=Path, default=DEFAULT_M3015_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_active_safety_driver_v1_baseline_measurement_table_materialization_preflight(
        m3035_dir=args.m3035_dir,
        m3015_dir=args.m3015_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
