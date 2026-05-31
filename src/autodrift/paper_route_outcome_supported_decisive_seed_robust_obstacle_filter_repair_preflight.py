"""No-reset seed-robust obstacle-filter repair for outcome-supported decisive specs."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import reset_sampler_state_from_seed
from autodrift.paper_route_outcome_supported_decisive_materialization_preflight import contract_checks
from autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight import (
    AGGREGATE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    FORBIDDEN_GUARDRAILS,
    GLOBAL_DISTANCE_RANGE,
    GLOBAL_HALF_WIDTH_RANGE,
    PROFILE_FIELDNAMES,
    SPEC_CSV_FIELDNAMES,
    TARGET_SENTINEL_PROFILE_COUNT,
    WORKLOAD_FIELDNAMES,
    _aggregate_rows,
    _axis_coverage_pass,
    _bool,
    _candidate_is_accepted,
    _count_by,
    _float,
    _guardrail_flags,
    _linspace,
    _metadata_missing_count,
    _range_to_string,
    _threshold_score,
    load_executable_task_specs,
    planned_sentinel_workload_rows,
    zero_step_warmup_gate_invalid,
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
from autodrift.scenarios import classify_obstacle_scenario


DEFAULT_REPAIRED_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/"
    "repaired_executable_task_specs.json"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m2073_paper_route_outcome_supported_decisive_repaired_reset_validation_preflight/reset_rows.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2077-paper-route-outcome-supported-decisive-seed-robust-obstacle-filter-repair-result-audit"
)
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight_v0"

TARGET_EXECUTABLE_SPECS = sum(FAMILY_TARGETS.values())
TARGET_SENTINEL_WORKLOAD = TARGET_EXECUTABLE_SPECS * len(SENTINEL_PROFILES)
DEFAULT_SUPPORT_SEED_COUNT = 5
DEFAULT_REQUIRED_SEED_SUPPORT = 5
DEFAULT_MAX_DISTANCE_WINDOW_WIDTH = 12.0
DEFAULT_MAX_HALF_WIDTH_WINDOW_WIDTH = 0.8
DEFAULT_MAX_THRESHOLD_SCORE_CEILING = 1.0
DEFAULT_DISTANCE_GRID_COUNT = 145
DEFAULT_HALF_WIDTH_GRID_COUNT = 43

SEED_SUPPORT_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "support_seed",
    "support_seed_offset",
    "threshold_score_used",
    "seed_supported",
    "accepted_grid_cell_count",
    "accepted_grid_cell_fraction",
    "candidate_label",
    "candidate_threshold_score",
    "candidate_distance",
    "candidate_half_width",
    "repaired_distance_range",
    "repaired_half_width_range",
]
SEED_ROBUST_REPAIR_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "support_seed_count",
    "required_seed_support",
    "seed_support_count",
    "seed_support_pass",
    "original_obstacle_distance_range",
    "original_obstacle_half_width_range",
    "original_obstacle_max_threshold_score",
    "repaired_obstacle_distance_range",
    "repaired_obstacle_half_width_range",
    "repaired_obstacle_max_threshold_score",
    "distance_window_width",
    "half_width_window_width",
    "threshold_score_escalated",
    "scenario_filter_seed_robust_after",
    "repair_reason",
]


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_reset_rows(path: Path | str = DEFAULT_RESET_ROWS) -> list[dict[str, str]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("task_source_id", "")))


def _threshold_candidates(original: Any, ceiling: float) -> list[float]:
    values = [_float(original, 0.25), 0.5, 1.0]
    out: list[float] = []
    for value in values:
        value = min(float(value), float(ceiling))
        if value not in out:
            out.append(value)
    return out


def support_seeds_for_eval_seed(eval_seed: int, *, support_seed_count: int, stride: int) -> list[int]:
    return [int(eval_seed) + int(stride) * index for index in range(int(support_seed_count))]


def _accepted_points(
    *,
    env_config: Mapping[str, Any],
    seed: int,
    distance_values: list[float],
    half_width_values: list[float],
) -> list[dict[str, Any]]:
    config = build_env_config(dict(env_config))
    state = reset_sampler_state_from_seed(env_config=env_config, seed=int(seed))
    scenario_config = config.obstacle.scenario_config(speed=float(state["speed_ref"]), mu=float(state["initial_mu"]))
    points: list[dict[str, Any]] = []
    for distance in distance_values:
        for half_width in half_width_values:
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
            points.append(
                {
                    "distance": float(distance),
                    "half_width": float(half_width),
                    "threshold_score": float(score),
                    "label": str(scenario.label),
                }
            )
    return points


def _points_in_window(
    points: Iterable[Mapping[str, Any]],
    *,
    distance_low: float,
    distance_high: float,
    half_width_low: float,
    half_width_high: float,
) -> list[dict[str, Any]]:
    return [
        dict(point)
        for point in points
        if distance_low <= float(point["distance"]) <= distance_high
        and half_width_low <= float(point["half_width"]) <= half_width_high
    ]


def _cover_seed_point_sets(
    point_sets: list[list[dict[str, Any]]],
    *,
    max_distance_window_width: float,
    max_half_width_window_width: float,
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

    best_score: tuple[float, int, float, float, float, float] | None = None
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
            total_inside = 0
            for points in distance_filtered:
                inside = _points_in_window(
                    points,
                    distance_low=distance_low,
                    distance_high=distance_high,
                    half_width_low=half_width_low,
                    half_width_high=half_width_high,
                )
                if not inside:
                    per_seed = []
                    break
                total_inside += len(inside)
                per_seed.append(min(inside, key=lambda point: float(point["threshold_score"])))
            if not per_seed:
                continue
            mean_score = sum(float(point["threshold_score"]) for point in per_seed) / len(per_seed)
            score = (
                mean_score,
                -int(total_inside),
                float(distance_high - distance_low),
                float(half_width_high - half_width_low),
                float(distance_low),
                float(half_width_low),
            )
            if best_score is None or score < best_score:
                best_score = score
                best = {
                    "distance_low": float(distance_low),
                    "distance_high": float(distance_high),
                    "half_width_low": float(half_width_low),
                    "half_width_high": float(half_width_high),
                    "per_seed_points": per_seed,
                    "per_seed_inside_counts": [
                        len(
                            _points_in_window(
                                points,
                                distance_low=distance_low,
                                distance_high=distance_high,
                                half_width_low=half_width_low,
                                half_width_high=half_width_high,
                            )
                        )
                        for points in point_sets
                    ],
                    "total_inside_count": int(total_inside),
                }
    return best


def _claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "seed_robust_obstacle_filter_repair_preflight",
            "admissible": bool(passes),
            "reason": "admissible only if no-reset multi-seed support gates pass",
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


def repair_spec_seed_robust(
    spec: Mapping[str, Any],
    *,
    reset_row: Mapping[str, Any],
    support_seed_count: int,
    required_seed_support: int,
    max_distance_window_width: float,
    max_half_width_window_width: float,
    max_threshold_score_ceiling: float,
    distance_grid_count: int,
    half_width_grid_count: int,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    env_config = copy.deepcopy(dict(spec.get("env_config", {})))
    original_obstacle = copy.deepcopy(dict(env_config.get("obstacle", {})))
    eval_seed = int(reset_row.get("eval_seed", 0) or 0)
    if eval_seed <= 0:
        raise ValueError(f"missing positive eval_seed for {spec.get('task_source_id', '')}")
    support_seeds = support_seeds_for_eval_seed(
        eval_seed,
        support_seed_count=support_seed_count,
        stride=TARGET_EXECUTABLE_SPECS,
    )
    distance_values = _linspace(GLOBAL_DISTANCE_RANGE[0], GLOBAL_DISTANCE_RANGE[1], int(distance_grid_count))
    half_width_values = _linspace(GLOBAL_HALF_WIDTH_RANGE[0], GLOBAL_HALF_WIDTH_RANGE[1], int(half_width_grid_count))
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
        cover = _cover_seed_point_sets(
            candidate_sets,
            max_distance_window_width=max_distance_window_width,
            max_half_width_window_width=max_half_width_window_width,
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
    if chosen is not None:
        obstacle = copy.deepcopy(dict(repaired_env.get("obstacle", {})))
        obstacle["distance_range"] = [float(chosen["distance_low"]), float(chosen["distance_high"])]
        obstacle["half_width_range"] = [float(chosen["half_width_low"]), float(chosen["half_width_high"])]
        obstacle["max_threshold_score"] = float(threshold_used)
        repaired_env["obstacle"] = obstacle
        total_grid_count = max(int(distance_grid_count) * int(half_width_grid_count), 1)
        for seed, points, best_point in zip(support_seeds, point_sets, chosen["per_seed_points"], strict=True):
            inside = _points_in_window(
                points,
                distance_low=float(chosen["distance_low"]),
                distance_high=float(chosen["distance_high"]),
                half_width_low=float(chosen["half_width_low"]),
                half_width_high=float(chosen["half_width_high"]),
            )
            supported = bool(inside)
            seed_support_count += int(supported)
            support_rows.append(
                {
                    **metadata_for_spec(spec),
                    "eval_seed": eval_seed,
                    "support_seed": int(seed),
                    "support_seed_offset": int(seed) - eval_seed,
                    "threshold_score_used": float(threshold_used),
                    "seed_supported": supported,
                    "accepted_grid_cell_count": len(inside),
                    "accepted_grid_cell_fraction": len(inside) / total_grid_count,
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
    seed_support_pass = int(seed_support_count) >= int(required_seed_support)
    repaired_spec["seed_robust_support_pass"] = bool(seed_support_pass)
    repaired_spec["seed_support_count"] = int(seed_support_count)
    repaired_spec["required_seed_support"] = int(required_seed_support)
    repaired_spec["scenario_filter_seed_robust_after"] = bool(seed_support_pass)

    obstacle_after = dict(repaired_spec["env_config"].get("obstacle", {}))
    distance_range = obstacle_after.get("distance_range", [0.0, 0.0])
    half_width_range = obstacle_after.get("half_width_range", [0.0, 0.0])
    repair_row = {
        **metadata_for_spec(repaired_spec),
        "eval_seed": eval_seed,
        "support_seed_count": int(support_seed_count),
        "required_seed_support": int(required_seed_support),
        "seed_support_count": int(seed_support_count),
        "seed_support_pass": bool(seed_support_pass),
        "original_obstacle_distance_range": _range_to_string(original_obstacle.get("distance_range", "")),
        "original_obstacle_half_width_range": _range_to_string(original_obstacle.get("half_width_range", "")),
        "original_obstacle_max_threshold_score": original_threshold,
        "repaired_obstacle_distance_range": _range_to_string(distance_range),
        "repaired_obstacle_half_width_range": _range_to_string(half_width_range),
        "repaired_obstacle_max_threshold_score": obstacle_after.get("max_threshold_score", ""),
        "distance_window_width": float(distance_range[1]) - float(distance_range[0]),
        "half_width_window_width": float(half_width_range[1]) - float(half_width_range[0]),
        "threshold_score_escalated": float(threshold_used) > _float(original_threshold, 0.25),
        "scenario_filter_seed_robust_after": bool(seed_support_pass),
        "repair_reason": (
            "seed_robust_window_found"
            if seed_support_pass
            else "seed_robust_window_not_found_within_bounds"
        ),
    }
    return repaired_spec, repair_row, support_rows


def run_seed_robust_repair_preflight(
    *,
    repaired_executable_task_specs_path: Path | str = DEFAULT_REPAIRED_EXECUTABLE_TASK_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    support_seed_count: int = DEFAULT_SUPPORT_SEED_COUNT,
    required_seed_support: int = DEFAULT_REQUIRED_SEED_SUPPORT,
    target_spec_count: int = TARGET_EXECUTABLE_SPECS,
    max_distance_window_width: float = DEFAULT_MAX_DISTANCE_WINDOW_WIDTH,
    max_half_width_window_width: float = DEFAULT_MAX_HALF_WIDTH_WINDOW_WIDTH,
    max_threshold_score_ceiling: float = DEFAULT_MAX_THRESHOLD_SCORE_CEILING,
    distance_grid_count: int = DEFAULT_DISTANCE_GRID_COUNT,
    half_width_grid_count: int = DEFAULT_HALF_WIDTH_GRID_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(repaired_executable_task_specs_path)
    reset_rows = load_reset_rows(reset_rows_path)
    reset_by_id = {str(row.get("task_source_id", "")): dict(row) for row in reset_rows}

    repaired_specs: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    seed_support_rows: list[dict[str, Any]] = []
    for spec in specs:
        reset_row = reset_by_id.get(str(spec.get("task_source_id", "")))
        if reset_row is None:
            raise ValueError(f"missing reset row for {spec.get('task_source_id', '')}")
        repaired_spec, repair_row, support_rows = repair_spec_seed_robust(
            spec,
            reset_row=reset_row,
            support_seed_count=support_seed_count,
            required_seed_support=required_seed_support,
            max_distance_window_width=max_distance_window_width,
            max_half_width_window_width=max_half_width_window_width,
            max_threshold_score_ceiling=max_threshold_score_ceiling,
            distance_grid_count=distance_grid_count,
            half_width_grid_count=half_width_grid_count,
        )
        repaired_specs.append(repaired_spec)
        repair_rows.append(repair_row)
        seed_support_rows.extend(support_rows)

    workload_rows, profile_rows = planned_sentinel_workload_rows(repaired_specs, profile_run_dir=profile_run_dir)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    family_counts = {family: 0 for family in FAMILY_TARGETS}
    family_counts.update(_count_by(repaired_specs, "panel_task_family"))
    split_counts = {split: 0 for split in SPLIT_TARGETS}
    split_counts.update(_count_by(repaired_specs, "source_split"))
    zero_invalid_after = sum(zero_step_warmup_gate_invalid(spec["env_config"]) for spec in repaired_specs)
    seed_support_pass_count = sum(_bool(row.get("seed_support_pass")) for row in repair_rows)
    seed_support_fail_count = len(repair_rows) - seed_support_pass_count
    contract_violation_count = sum(int(spec.get("contract_violation_count", 0)) for spec in repaired_specs)
    metadata_missing_count = _metadata_missing_count(repaired_specs)
    forbidden_hits = forbidden_key_violations(repaired_specs)
    profile_missing_count = sum(1 for row in profile_rows if not (row["config_exists"] and row["checkpoint_exists"]))
    distance_window_width_max = max((float(row["distance_window_width"]) for row in repair_rows), default=0.0)
    half_width_window_width_max = max((float(row["half_width_window_width"]) for row in repair_rows), default=0.0)
    threshold_score_ceiling_used = max(
        (_float(row.get("repaired_obstacle_max_threshold_score"), 0.0) for row in repair_rows),
        default=0.0,
    )
    family_quota_pass = family_counts == FAMILY_TARGETS
    split_quota_pass = split_counts == SPLIT_TARGETS
    difficulty_axis_coverage_pass = _axis_coverage_pass(repaired_specs)
    passes = (
        len(specs) == int(target_spec_count)
        and len(repaired_specs) == int(target_spec_count)
        and len(workload_rows) == int(target_spec_count) * TARGET_SENTINEL_PROFILE_COUNT
        and len(profile_rows) == TARGET_SENTINEL_PROFILE_COUNT
        and int(support_seed_count) == DEFAULT_SUPPORT_SEED_COUNT
        and int(required_seed_support) == DEFAULT_REQUIRED_SEED_SUPPORT
        and seed_support_pass_count == int(target_spec_count)
        and seed_support_fail_count == 0
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
        output / "seed_robust_repaired_executable_task_specs.json",
        {"protocol": PROTOCOL_NAME, "executable_task_specs": repaired_specs},
    )
    write_csv_rows(
        output / "seed_robust_repaired_executable_task_specs.csv",
        [
            {
                **metadata_for_spec(spec),
                "warmup_gate_repaired": spec.get("warmup_gate_repaired", False),
                "obstacle_filter_repaired": spec.get("obstacle_filter_repaired", False),
                "scenario_filter_feasible_after": spec.get("scenario_filter_seed_robust_after", False),
                "contract_violation_count": spec.get("contract_violation_count", 0),
            }
            for spec in repaired_specs
        ],
        SPEC_CSV_FIELDNAMES,
    )
    write_csv_rows(output / "seed_robust_repair_rows.csv", repair_rows, SEED_ROBUST_REPAIR_FIELDNAMES)
    write_csv_rows(output / "seed_support_rows.csv", seed_support_rows, SEED_SUPPORT_FIELDNAMES)
    write_csv_rows(output / "planned_sentinel_workload.csv", workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(output / "family_distribution.csv", _aggregate_rows(family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "split_distribution.csv", _aggregate_rows(split_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(
        output / "seed_support_distribution.csv",
        _aggregate_rows(Counter(str(row["seed_support_count"]) for row in repair_rows)),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight_pass"
            if passes
            else "outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "repaired_executable_task_specs_path": str(repaired_executable_task_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "profile_run_dir": str(profile_run_dir),
        "input_executable_spec_count": len(specs),
        "repaired_executable_spec_count": len(repaired_specs),
        "target_executable_spec_count": int(target_spec_count),
        "planned_sentinel_workload_count": len(workload_rows),
        "target_sentinel_workload_count": int(target_spec_count) * TARGET_SENTINEL_PROFILE_COUNT,
        "sentinel_profile_count": len(profile_rows),
        "target_sentinel_profile_count": TARGET_SENTINEL_PROFILE_COUNT,
        "target_support_seed_count": int(support_seed_count),
        "required_seed_support": int(required_seed_support),
        "seed_robust_support_pass_count": int(seed_support_pass_count),
        "seed_robust_support_fail_count": int(seed_support_fail_count),
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
            "seed_robust_repaired_executable_task_specs": str(
                output / "seed_robust_repaired_executable_task_specs.json"
            ),
            "seed_robust_repair_rows": str(output / "seed_robust_repair_rows.csv"),
            "seed_support_rows": str(output / "seed_support_rows.csv"),
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
    parser.add_argument("--repaired-executable-task-specs", type=Path, default=DEFAULT_REPAIRED_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--support-seed-count", type=int, default=DEFAULT_SUPPORT_SEED_COUNT)
    parser.add_argument("--required-seed-support", type=int, default=DEFAULT_REQUIRED_SEED_SUPPORT)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_EXECUTABLE_SPECS)
    parser.add_argument("--max-distance-window-width", type=float, default=DEFAULT_MAX_DISTANCE_WINDOW_WIDTH)
    parser.add_argument("--max-half-width-window-width", type=float, default=DEFAULT_MAX_HALF_WIDTH_WINDOW_WIDTH)
    parser.add_argument("--max-threshold-score-ceiling", type=float, default=DEFAULT_MAX_THRESHOLD_SCORE_CEILING)
    parser.add_argument("--distance-grid-count", type=int, default=DEFAULT_DISTANCE_GRID_COUNT)
    parser.add_argument("--half-width-grid-count", type=int, default=DEFAULT_HALF_WIDTH_GRID_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_seed_robust_repair_preflight(
        repaired_executable_task_specs_path=args.repaired_executable_task_specs,
        reset_rows_path=args.reset_rows,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        support_seed_count=args.support_seed_count,
        required_seed_support=args.required_seed_support,
        target_spec_count=args.target_spec_count,
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
    print(f"seed_robust_support_pass_count={summary['seed_robust_support_pass_count']}")
    print(f"seed_robust_support_fail_count={summary['seed_robust_support_fail_count']}")
    print(f"distance_window_width_max={summary['distance_window_width_max']:.6f}")
    print(f"half_width_window_width_max={summary['half_width_window_width_max']:.6f}")
    print(f"threshold_score_ceiling_used={summary['threshold_score_ceiling_used']:.6f}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
