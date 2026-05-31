"""No-reset density-aware repair for the residual outcome-supported decisive reset failures."""

from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.paper_route_outcome_supported_decisive_materialization_preflight import contract_checks
from autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight import (
    AGGREGATE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    PROFILE_FIELDNAMES,
    SPEC_CSV_FIELDNAMES,
    TARGET_SENTINEL_PROFILE_COUNT,
    WORKLOAD_FIELDNAMES,
    _aggregate_rows,
    _axis_coverage_pass,
    _bool,
    _count_by,
    _float,
    _guardrail_flags,
    _metadata_missing_count,
    _range_to_string,
    load_executable_task_specs,
    planned_sentinel_workload_rows,
    zero_step_warmup_gate_invalid,
)
from autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight import (
    METADATA_FIELDS,
    metadata_for_spec,
)
from autodrift.paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight import (
    DEFAULT_DISTANCE_GRID_COUNT,
    DEFAULT_HALF_WIDTH_GRID_COUNT,
    DEFAULT_MAX_DISTANCE_WINDOW_WIDTH,
    DEFAULT_MAX_HALF_WIDTH_WINDOW_WIDTH,
    DEFAULT_MAX_THRESHOLD_SCORE_CEILING,
    DEFAULT_REQUIRED_SEED_SUPPORT,
    DEFAULT_SUPPORT_SEED_COUNT,
    GLOBAL_DISTANCE_RANGE,
    GLOBAL_HALF_WIDTH_RANGE,
    _accepted_points,
    _points_in_window,
    _threshold_candidates,
    support_seeds_for_eval_seed,
)
from autodrift.paper_route_outcome_supported_decisive_task_candidates import (
    FAMILY_TARGETS,
    SENTINEL_PROFILES,
    SPLIT_TARGETS,
)


DEFAULT_SEED_ROBUST_REPAIRED_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/"
    "seed_robust_repaired_executable_task_specs.json"
)
DEFAULT_RESET_FAILURE_ROWS = Path(
    "runs/m2079_paper_route_outcome_supported_decisive_seed_robust_repaired_reset_validation_preflight/"
    "reset_failure_rows.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2082_paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight")
DEFAULT_NEXT_BLOCKER = "m2083-paper-route-outcome-supported-decisive-density-aware-obstacle-filter-repair-result-audit"
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight_v0"

TARGET_EXECUTABLE_SPECS = sum(FAMILY_TARGETS.values())
TARGET_SENTINEL_WORKLOAD = TARGET_EXECUTABLE_SPECS * len(SENTINEL_PROFILES)
DEFAULT_MINIMUM_ACCEPTED_GRID_CELL_COUNT = 80
DEFAULT_TARGETED_REPAIR_COUNT = 6

DENSITY_SUPPORT_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "support_seed",
    "support_seed_offset",
    "threshold_score_used",
    "seed_supported",
    "accepted_grid_cell_count",
    "accepted_grid_cell_fraction",
    "minimum_accepted_grid_cell_count_required",
    "density_pass",
    "candidate_label",
    "candidate_threshold_score",
    "candidate_distance",
    "candidate_half_width",
    "repaired_distance_range",
    "repaired_half_width_range",
]
DENSITY_REPAIR_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "targeted_repair",
    "support_seed_count",
    "required_seed_support",
    "minimum_accepted_grid_cell_count_required",
    "seed_support_count",
    "density_min_accepted_grid_cell_count",
    "density_support_pass",
    "original_obstacle_distance_range",
    "original_obstacle_half_width_range",
    "original_obstacle_max_threshold_score",
    "repaired_obstacle_distance_range",
    "repaired_obstacle_half_width_range",
    "repaired_obstacle_max_threshold_score",
    "distance_window_width",
    "half_width_window_width",
    "threshold_score_escalated",
    "repair_reason",
]


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_reset_failure_rows(path: Path | str = DEFAULT_RESET_FAILURE_ROWS) -> list[dict[str, str]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("task_source_id", "")))


def _stable_env_json(env_config: Mapping[str, Any]) -> str:
    return json.dumps(env_config, sort_keys=True, separators=(",", ":"))


def _cover_density_window(
    point_sets: list[list[dict[str, Any]]],
    *,
    max_distance_window_width: float,
    max_half_width_window_width: float,
    minimum_accepted_grid_cell_count: int,
) -> dict[str, Any] | None:
    distance_lows: set[float] = set()
    half_width_lows: set[float] = set()
    for points in point_sets:
        for point in points:
            distance = float(point["distance"])
            half_width = float(point["half_width"])
            distance_lows.add(distance)
            distance_lows.add(distance - max_distance_window_width)
            half_width_lows.add(half_width)
            half_width_lows.add(half_width - max_half_width_window_width)

    best_score: tuple[int, int, float, float, float, float] | None = None
    best: dict[str, Any] | None = None
    for distance_low_raw in distance_lows:
        distance_low = max(float(GLOBAL_DISTANCE_RANGE[0]), float(distance_low_raw))
        distance_high = min(float(GLOBAL_DISTANCE_RANGE[1]), distance_low_raw + max_distance_window_width)
        if distance_high < distance_low:
            continue
        distance_filtered: list[list[dict[str, Any]]] = []
        for points in point_sets:
            filtered = [
                dict(point)
                for point in points
                if distance_low <= float(point["distance"]) <= distance_high
            ]
            if not filtered:
                break
            distance_filtered.append(filtered)
        if len(distance_filtered) != len(point_sets):
            continue
        for half_width_low_raw in half_width_lows:
            half_width_low = max(float(GLOBAL_HALF_WIDTH_RANGE[0]), float(half_width_low_raw))
            half_width_high = min(float(GLOBAL_HALF_WIDTH_RANGE[1]), half_width_low_raw + max_half_width_window_width)
            if half_width_high < half_width_low:
                continue
            per_seed: list[dict[str, Any]] = []
            counts: list[int] = []
            mean_score = 0.0
            for points in distance_filtered:
                inside = _points_in_window(
                    points,
                    distance_low=distance_low,
                    distance_high=distance_high,
                    half_width_low=half_width_low,
                    half_width_high=half_width_high,
                )
                if len(inside) < int(minimum_accepted_grid_cell_count):
                    per_seed = []
                    break
                counts.append(len(inside))
                best_point = min(inside, key=lambda point: float(point["threshold_score"]))
                mean_score += float(best_point["threshold_score"])
                per_seed.append(best_point)
            if not per_seed:
                continue
            score = (
                min(counts),
                sum(counts),
                -mean_score,
                -(float(distance_high) - float(distance_low)),
                -(float(half_width_high) - float(half_width_low)),
                -float(distance_low),
            )
            if best_score is None or score > best_score:
                best_score = score
                best = {
                    "distance_low": float(distance_low),
                    "distance_high": float(distance_high),
                    "half_width_low": float(half_width_low),
                    "half_width_high": float(half_width_high),
                    "per_seed_points": per_seed,
                    "per_seed_inside_counts": counts,
                    "total_inside_count": int(sum(counts)),
                    "min_inside_count": int(min(counts)),
                }
    return best


def _claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "density_aware_obstacle_filter_repair_preflight",
            "admissible": bool(passes),
            "reason": "admissible only if no-reset density support gates pass",
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


def repair_spec_density_aware(
    spec: Mapping[str, Any],
    *,
    failure_row: Mapping[str, Any],
    support_seed_count: int,
    required_seed_support: int,
    minimum_accepted_grid_cell_count: int,
    max_distance_window_width: float,
    max_half_width_window_width: float,
    max_threshold_score_ceiling: float,
    distance_grid_count: int,
    half_width_grid_count: int,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    env_config = copy.deepcopy(dict(spec.get("env_config", {})))
    original_obstacle = copy.deepcopy(dict(env_config.get("obstacle", {})))
    eval_seed = int(failure_row.get("eval_seed", 0) or 0)
    if eval_seed <= 0:
        raise ValueError(f"missing positive eval_seed for {spec.get('task_source_id', '')}")
    support_seeds = support_seeds_for_eval_seed(
        eval_seed,
        support_seed_count=support_seed_count,
        stride=TARGET_EXECUTABLE_SPECS,
    )
    distance_values = [
        float(GLOBAL_DISTANCE_RANGE[0])
        + (float(GLOBAL_DISTANCE_RANGE[1]) - float(GLOBAL_DISTANCE_RANGE[0])) * index / (distance_grid_count - 1)
        for index in range(int(distance_grid_count))
    ]
    half_width_values = [
        float(GLOBAL_HALF_WIDTH_RANGE[0])
        + (float(GLOBAL_HALF_WIDTH_RANGE[1]) - float(GLOBAL_HALF_WIDTH_RANGE[0])) * index / (half_width_grid_count - 1)
        for index in range(int(half_width_grid_count))
    ]
    original_threshold = original_obstacle.get("max_threshold_score", 0.25)
    chosen: dict[str, Any] | None = None
    threshold_used = _float(original_threshold, 0.25)
    point_sets: list[list[dict[str, Any]]] = []
    for threshold in _threshold_candidates(original_threshold, max_threshold_score_ceiling):
        candidate_env = copy.deepcopy(env_config)
        candidate_obstacle = copy.deepcopy(dict(candidate_env.get("obstacle", {})))
        candidate_obstacle["max_threshold_score"] = float(threshold)
        candidate_env["obstacle"] = candidate_obstacle
        candidate_sets: list[list[dict[str, Any]]] = []
        for seed in support_seeds:
            points = _accepted_points(
                env_config=candidate_env,
                seed=seed,
                distance_values=distance_values,
                half_width_values=half_width_values,
            )
            if not points:
                break
            candidate_sets.append(points)
        if len(candidate_sets) != len(support_seeds):
            continue
        cover = _cover_density_window(
            candidate_sets,
            max_distance_window_width=max_distance_window_width,
            max_half_width_window_width=max_half_width_window_width,
            minimum_accepted_grid_cell_count=minimum_accepted_grid_cell_count,
        )
        if cover is None:
            continue
        chosen = cover
        threshold_used = float(threshold)
        point_sets = candidate_sets
        break

    support_rows: list[dict[str, Any]] = []
    repaired_env = copy.deepcopy(env_config)
    seed_support_count = 0
    min_count = 0
    if chosen is not None:
        obstacle = copy.deepcopy(dict(repaired_env.get("obstacle", {})))
        obstacle["distance_range"] = [float(chosen["distance_low"]), float(chosen["distance_high"])]
        obstacle["half_width_range"] = [float(chosen["half_width_low"]), float(chosen["half_width_high"])]
        obstacle["max_threshold_score"] = float(threshold_used)
        repaired_env["obstacle"] = obstacle
        total_grid_count = max(int(distance_grid_count) * int(half_width_grid_count), 1)
        min_count = int(chosen["min_inside_count"])
        for seed, points, best_point in zip(support_seeds, point_sets, chosen["per_seed_points"], strict=True):
            inside = _points_in_window(
                points,
                distance_low=float(chosen["distance_low"]),
                distance_high=float(chosen["distance_high"]),
                half_width_low=float(chosen["half_width_low"]),
                half_width_high=float(chosen["half_width_high"]),
            )
            supported = len(inside) >= int(minimum_accepted_grid_cell_count)
            seed_support_count += int(supported)
            support_rows.append(
                {
                    **metadata_for_spec(spec),
                    "eval_seed": eval_seed,
                    "support_seed": int(seed),
                    "support_seed_offset": int(seed) - eval_seed,
                    "threshold_score_used": float(threshold_used),
                    "seed_supported": bool(inside),
                    "accepted_grid_cell_count": len(inside),
                    "accepted_grid_cell_fraction": len(inside) / total_grid_count,
                    "minimum_accepted_grid_cell_count_required": int(minimum_accepted_grid_cell_count),
                    "density_pass": supported,
                    "candidate_label": best_point["label"],
                    "candidate_threshold_score": best_point["threshold_score"],
                    "candidate_distance": best_point["distance"],
                    "candidate_half_width": best_point["half_width"],
                    "repaired_distance_range": _range_to_string(obstacle["distance_range"]),
                    "repaired_half_width_range": _range_to_string(obstacle["half_width_range"]),
                }
            )
    else:
        for seed in support_seeds:
            support_rows.append(
                {
                    **metadata_for_spec(spec),
                    "eval_seed": eval_seed,
                    "support_seed": int(seed),
                    "support_seed_offset": int(seed) - eval_seed,
                    "threshold_score_used": "",
                    "seed_supported": False,
                    "accepted_grid_cell_count": 0,
                    "accepted_grid_cell_fraction": 0.0,
                    "minimum_accepted_grid_cell_count_required": int(minimum_accepted_grid_cell_count),
                    "density_pass": False,
                    "candidate_label": "",
                    "candidate_threshold_score": "",
                    "candidate_distance": "",
                    "candidate_half_width": "",
                    "repaired_distance_range": _range_to_string(original_obstacle.get("distance_range", "")),
                    "repaired_half_width_range": _range_to_string(original_obstacle.get("half_width_range", "")),
                }
            )

    built = build_env_config(repaired_env)
    checks = contract_checks(repaired_env)
    repaired_spec = dict(spec)
    repaired_spec["env_config"] = env_config_to_dict(built)
    repaired_spec["contract_checks"] = checks
    repaired_spec["contract_violation_count"] = int(sum(not bool(value) for value in checks.values()))
    repaired_spec["paper_validity_claim"] = False
    repaired_spec["profile_specific_tuning"] = False
    repaired_spec["controller_family_ranking_claim_made"] = False
    repaired_spec["finite_window_vs_gru_conclusion_made"] = False
    repaired_spec["paper_level_claim_made"] = False
    repaired_spec["level3_self_id_claim_made"] = False
    density_support_pass = int(seed_support_count) >= int(required_seed_support) and min_count >= int(
        minimum_accepted_grid_cell_count
    )

    obstacle_after = dict(repaired_spec["env_config"].get("obstacle", {}))
    distance_range = obstacle_after.get("distance_range", [0.0, 0.0])
    half_width_range = obstacle_after.get("half_width_range", [0.0, 0.0])
    repair_row = {
        **metadata_for_spec(repaired_spec),
        "eval_seed": eval_seed,
        "targeted_repair": True,
        "support_seed_count": int(support_seed_count),
        "required_seed_support": int(required_seed_support),
        "minimum_accepted_grid_cell_count_required": int(minimum_accepted_grid_cell_count),
        "seed_support_count": int(seed_support_count),
        "density_min_accepted_grid_cell_count": int(min_count),
        "density_support_pass": bool(density_support_pass),
        "original_obstacle_distance_range": _range_to_string(original_obstacle.get("distance_range", "")),
        "original_obstacle_half_width_range": _range_to_string(original_obstacle.get("half_width_range", "")),
        "original_obstacle_max_threshold_score": original_threshold,
        "repaired_obstacle_distance_range": _range_to_string(distance_range),
        "repaired_obstacle_half_width_range": _range_to_string(half_width_range),
        "repaired_obstacle_max_threshold_score": obstacle_after.get("max_threshold_score", ""),
        "distance_window_width": float(distance_range[1]) - float(distance_range[0]),
        "half_width_window_width": float(half_width_range[1]) - float(half_width_range[0]),
        "threshold_score_escalated": float(threshold_used) > _float(original_threshold, 0.25),
        "repair_reason": (
            "density_aware_window_found"
            if density_support_pass
            else "density_aware_window_not_found_within_bounds"
        ),
    }
    return repaired_spec, repair_row, support_rows


def _unchanged_repair_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    obstacle = dict(dict(spec.get("env_config", {})).get("obstacle", {}))
    distance_range = obstacle.get("distance_range", [0.0, 0.0])
    half_width_range = obstacle.get("half_width_range", [0.0, 0.0])
    return {
        **metadata_for_spec(spec),
        "eval_seed": "",
        "targeted_repair": False,
        "support_seed_count": "",
        "required_seed_support": "",
        "minimum_accepted_grid_cell_count_required": "",
        "seed_support_count": "",
        "density_min_accepted_grid_cell_count": "",
        "density_support_pass": True,
        "original_obstacle_distance_range": _range_to_string(distance_range),
        "original_obstacle_half_width_range": _range_to_string(half_width_range),
        "original_obstacle_max_threshold_score": obstacle.get("max_threshold_score", ""),
        "repaired_obstacle_distance_range": _range_to_string(distance_range),
        "repaired_obstacle_half_width_range": _range_to_string(half_width_range),
        "repaired_obstacle_max_threshold_score": obstacle.get("max_threshold_score", ""),
        "distance_window_width": float(distance_range[1]) - float(distance_range[0]),
        "half_width_window_width": float(half_width_range[1]) - float(half_width_range[0]),
        "threshold_score_escalated": False,
        "repair_reason": "non_target_spec_unchanged",
    }


def run_density_aware_repair_preflight(
    *,
    seed_robust_repaired_executable_task_specs_path: Path | str = DEFAULT_SEED_ROBUST_REPAIRED_EXECUTABLE_TASK_SPECS,
    reset_failure_rows_path: Path | str = DEFAULT_RESET_FAILURE_ROWS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    support_seed_count: int = DEFAULT_SUPPORT_SEED_COUNT,
    required_seed_support: int = DEFAULT_REQUIRED_SEED_SUPPORT,
    minimum_accepted_grid_cell_count: int = DEFAULT_MINIMUM_ACCEPTED_GRID_CELL_COUNT,
    target_spec_count: int = TARGET_EXECUTABLE_SPECS,
    targeted_repair_count: int = DEFAULT_TARGETED_REPAIR_COUNT,
    max_distance_window_width: float = DEFAULT_MAX_DISTANCE_WINDOW_WIDTH,
    max_half_width_window_width: float = DEFAULT_MAX_HALF_WIDTH_WINDOW_WIDTH,
    max_threshold_score_ceiling: float = DEFAULT_MAX_THRESHOLD_SCORE_CEILING,
    distance_grid_count: int = DEFAULT_DISTANCE_GRID_COUNT,
    half_width_grid_count: int = DEFAULT_HALF_WIDTH_GRID_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(seed_robust_repaired_executable_task_specs_path)
    original_env_by_id = {str(spec["task_source_id"]): _stable_env_json(spec["env_config"]) for spec in specs}
    failure_rows = load_reset_failure_rows(reset_failure_rows_path)
    failure_by_id = {str(row.get("task_source_id", "")): dict(row) for row in failure_rows}

    repaired_specs: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    for spec in specs:
        task_id = str(spec.get("task_source_id", ""))
        if task_id in failure_by_id:
            repaired_spec, repair_row, rows = repair_spec_density_aware(
                spec,
                failure_row=failure_by_id[task_id],
                support_seed_count=support_seed_count,
                required_seed_support=required_seed_support,
                minimum_accepted_grid_cell_count=minimum_accepted_grid_cell_count,
                max_distance_window_width=max_distance_window_width,
                max_half_width_window_width=max_half_width_window_width,
                max_threshold_score_ceiling=max_threshold_score_ceiling,
                distance_grid_count=distance_grid_count,
                half_width_grid_count=half_width_grid_count,
            )
            support_rows.extend(rows)
        else:
            repaired_spec = dict(spec)
            repair_row = _unchanged_repair_row(spec)
        repaired_specs.append(repaired_spec)
        repair_rows.append(repair_row)

    workload_rows, profile_rows = planned_sentinel_workload_rows(repaired_specs, profile_run_dir=profile_run_dir)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    family_counts = {family: 0 for family in FAMILY_TARGETS}
    family_counts.update(_count_by(repaired_specs, "panel_task_family"))
    split_counts = {split: 0 for split in SPLIT_TARGETS}
    split_counts.update(_count_by(repaired_specs, "source_split"))
    targeted_rows = [row for row in repair_rows if _bool(row.get("targeted_repair"))]
    density_pass_count = sum(_bool(row.get("density_support_pass")) for row in targeted_rows)
    density_fail_count = len(targeted_rows) - density_pass_count
    density_min_count = min((int(row.get("density_min_accepted_grid_cell_count", 0) or 0) for row in targeted_rows), default=0)
    targeted_ids = {str(row["task_source_id"]) for row in targeted_rows}
    non_target_changed_count = sum(
        1
        for spec in repaired_specs
        if str(spec["task_source_id"]) not in targeted_ids
        and _stable_env_json(spec["env_config"]) != original_env_by_id[str(spec["task_source_id"])]
    )
    zero_invalid_after = sum(zero_step_warmup_gate_invalid(spec["env_config"]) for spec in repaired_specs)
    contract_violation_count = sum(int(spec.get("contract_violation_count", 0)) for spec in repaired_specs)
    metadata_missing_count = _metadata_missing_count(repaired_specs)
    forbidden_hits = forbidden_key_violations(repaired_specs)
    profile_missing_count = sum(1 for row in profile_rows if not (row["config_exists"] and row["checkpoint_exists"]))
    distance_window_width_max = max((float(row["distance_window_width"]) for row in targeted_rows), default=0.0)
    half_width_window_width_max = max((float(row["half_width_window_width"]) for row in targeted_rows), default=0.0)
    threshold_score_ceiling_used = max(
        (_float(row.get("repaired_obstacle_max_threshold_score"), 0.0) for row in targeted_rows),
        default=0.0,
    )
    family_quota_pass = family_counts == FAMILY_TARGETS
    split_quota_pass = split_counts == SPLIT_TARGETS
    difficulty_axis_coverage_pass = _axis_coverage_pass(repaired_specs)
    passes = (
        len(specs) == int(target_spec_count)
        and len(repaired_specs) == int(target_spec_count)
        and len(targeted_rows) == int(targeted_repair_count)
        and non_target_changed_count == 0
        and len(workload_rows) == int(target_spec_count) * TARGET_SENTINEL_PROFILE_COUNT
        and len(profile_rows) == TARGET_SENTINEL_PROFILE_COUNT
        and int(support_seed_count) == DEFAULT_SUPPORT_SEED_COUNT
        and int(required_seed_support) == DEFAULT_REQUIRED_SEED_SUPPORT
        and int(minimum_accepted_grid_cell_count) == DEFAULT_MINIMUM_ACCEPTED_GRID_CELL_COUNT
        and density_pass_count == int(targeted_repair_count)
        and density_fail_count == 0
        and density_min_count >= int(minimum_accepted_grid_cell_count)
        and distance_window_width_max <= float(max_distance_window_width) + 1e-9
        and half_width_window_width_max <= float(max_half_width_window_width) + 1e-9
        and threshold_score_ceiling_used <= float(max_threshold_score_ceiling) + 1e-9
        and zero_invalid_after == 0
        and family_quota_pass
        and split_quota_pass
        and difficulty_axis_coverage_pass
        and contract_violation_count == 0
        and metadata_missing_count == 0
        and not forbidden_hits
        and profile_missing_count == 0
        and guardrail_violation_count == 0
    )

    write_json(
        output / "density_aware_repaired_executable_task_specs.json",
        {"protocol": PROTOCOL_NAME, "executable_task_specs": repaired_specs},
    )
    write_csv_rows(
        output / "density_aware_repaired_executable_task_specs.csv",
        [
            {
                **metadata_for_spec(spec),
                "warmup_gate_repaired": spec.get("warmup_gate_repaired", False),
                "obstacle_filter_repaired": spec.get("obstacle_filter_repaired", False),
                "scenario_filter_feasible_after": bool(
                    str(spec["task_source_id"]) not in targeted_ids
                    or next(
                        row for row in targeted_rows if row["task_source_id"] == spec["task_source_id"]
                    )["density_support_pass"]
                ),
                "contract_violation_count": spec.get("contract_violation_count", 0),
            }
            for spec in repaired_specs
        ],
        SPEC_CSV_FIELDNAMES,
    )
    write_csv_rows(output / "density_aware_repair_rows.csv", repair_rows, DENSITY_REPAIR_FIELDNAMES)
    write_csv_rows(output / "density_support_rows.csv", support_rows, DENSITY_SUPPORT_FIELDNAMES)
    write_csv_rows(output / "planned_sentinel_workload.csv", workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(output / "family_distribution.csv", _aggregate_rows(family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "split_distribution.csv", _aggregate_rows(split_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(
        output / "density_support_distribution.csv",
        _aggregate_rows(Counter(str(row["density_min_accepted_grid_cell_count"]) for row in targeted_rows)),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight_pass"
            if passes
            else "outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "seed_robust_repaired_executable_task_specs_path": str(seed_robust_repaired_executable_task_specs_path),
        "reset_failure_rows_path": str(reset_failure_rows_path),
        "profile_run_dir": str(profile_run_dir),
        "input_executable_spec_count": len(specs),
        "repaired_executable_spec_count": len(repaired_specs),
        "target_executable_spec_count": int(target_spec_count),
        "targeted_repair_count": len(targeted_rows),
        "expected_targeted_repair_count": int(targeted_repair_count),
        "non_target_spec_changed_count": int(non_target_changed_count),
        "planned_sentinel_workload_count": len(workload_rows),
        "target_sentinel_workload_count": int(target_spec_count) * TARGET_SENTINEL_PROFILE_COUNT,
        "sentinel_profile_count": len(profile_rows),
        "target_sentinel_profile_count": TARGET_SENTINEL_PROFILE_COUNT,
        "target_support_seed_count": int(support_seed_count),
        "required_seed_support": int(required_seed_support),
        "minimum_accepted_grid_cell_count_required": int(minimum_accepted_grid_cell_count),
        "density_support_pass_count": int(density_pass_count),
        "density_support_fail_count": int(density_fail_count),
        "density_support_min_accepted_grid_cell_count": int(density_min_count),
        "zero_step_warmup_gate_invalid_count_after": int(zero_invalid_after),
        "distance_window_width_max": float(distance_window_width_max),
        "half_width_window_width_max": float(half_width_window_width_max),
        "threshold_score_ceiling_used": float(threshold_score_ceiling_used),
        "family_counts": family_counts,
        "expected_family_counts": FAMILY_TARGETS,
        "family_quota_pass": family_quota_pass,
        "split_counts": split_counts,
        "expected_split_counts": SPLIT_TARGETS,
        "split_quota_pass": split_quota_pass,
        "difficulty_axis_coverage_pass": difficulty_axis_coverage_pass,
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
            "density_aware_repaired_executable_task_specs": str(
                output / "density_aware_repaired_executable_task_specs.json"
            ),
            "density_aware_repair_rows": str(output / "density_aware_repair_rows.csv"),
            "density_support_rows": str(output / "density_support_rows.csv"),
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
    parser.add_argument(
        "--seed-robust-repaired-executable-task-specs",
        type=Path,
        default=DEFAULT_SEED_ROBUST_REPAIRED_EXECUTABLE_TASK_SPECS,
    )
    parser.add_argument("--reset-failure-rows", type=Path, default=DEFAULT_RESET_FAILURE_ROWS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--support-seed-count", type=int, default=DEFAULT_SUPPORT_SEED_COUNT)
    parser.add_argument("--required-seed-support", type=int, default=DEFAULT_REQUIRED_SEED_SUPPORT)
    parser.add_argument("--minimum-accepted-grid-cell-count", type=int, default=DEFAULT_MINIMUM_ACCEPTED_GRID_CELL_COUNT)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_EXECUTABLE_SPECS)
    parser.add_argument("--targeted-repair-count", type=int, default=DEFAULT_TARGETED_REPAIR_COUNT)
    parser.add_argument("--max-distance-window-width", type=float, default=DEFAULT_MAX_DISTANCE_WINDOW_WIDTH)
    parser.add_argument("--max-half-width-window-width", type=float, default=DEFAULT_MAX_HALF_WIDTH_WINDOW_WIDTH)
    parser.add_argument("--max-threshold-score-ceiling", type=float, default=DEFAULT_MAX_THRESHOLD_SCORE_CEILING)
    parser.add_argument("--distance-grid-count", type=int, default=DEFAULT_DISTANCE_GRID_COUNT)
    parser.add_argument("--half-width-grid-count", type=int, default=DEFAULT_HALF_WIDTH_GRID_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_density_aware_repair_preflight(
        seed_robust_repaired_executable_task_specs_path=args.seed_robust_repaired_executable_task_specs,
        reset_failure_rows_path=args.reset_failure_rows,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        support_seed_count=args.support_seed_count,
        required_seed_support=args.required_seed_support,
        minimum_accepted_grid_cell_count=args.minimum_accepted_grid_cell_count,
        target_spec_count=args.target_spec_count,
        targeted_repair_count=args.targeted_repair_count,
        max_distance_window_width=args.max_distance_window_width,
        max_half_width_window_width=args.max_half_width_window_width,
        max_threshold_score_ceiling=args.max_threshold_score_ceiling,
        distance_grid_count=args.distance_grid_count,
        half_width_grid_count=args.half_width_grid_count,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_executable_spec_count={summary['input_executable_spec_count']}")
    print(f"repaired_executable_spec_count={summary['repaired_executable_spec_count']}")
    print(f"targeted_repair_count={summary['targeted_repair_count']}")
    print(f"non_target_spec_changed_count={summary['non_target_spec_changed_count']}")
    print(f"density_support_pass_count={summary['density_support_pass_count']}")
    print(f"density_support_fail_count={summary['density_support_fail_count']}")
    print(f"density_support_min_accepted_grid_cell_count={summary['density_support_min_accepted_grid_cell_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
