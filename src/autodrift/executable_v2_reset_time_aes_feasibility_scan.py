"""No-reset reset-time AES feasibility grid scan."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import (
    ACCEPTED,
    REJECT_AEB_FEASIBLE,
    REJECT_FRICTION_TIMING,
    REJECT_LABEL,
    REJECT_THRESHOLD,
    TARGET_LABEL,
    reset_sampler_state_from_seed,
)
from autodrift.scenarios import ObstacleScenario, ObstacleScenarioConfig, classify_obstacle_scenario


DEFAULT_REPAIRED_SPECS = Path(
    "runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/"
    "repaired_targeted_reset_executable_v2_panel_specs.json"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1843_executable_v2_reset_time_aes_feasibility_scan")
DEFAULT_DISTANCE_RANGE = (1.0, 60.0)
DEFAULT_DISTANCE_COUNT = 120
DEFAULT_HALF_WIDTH_RANGE = (0.20, 1.40)
DEFAULT_HALF_WIDTH_COUNT = 61
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


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _source_key(row: Mapping[str, Any]) -> str:
    return str(
        row.get(
            "source_v1_bounded_panel_spec_id",
            row.get(
                "materialized_bounded_panel_spec_id",
                row.get("source_scenario_spec_id", ""),
            ),
        )
    )


def _friction_value(value: Any) -> int | str:
    return "" if value is None else int(value)


def _linspace(low: float, high: float, count: int) -> list[float]:
    count = int(count)
    if count <= 0:
        raise ValueError("grid count must be positive")
    low = float(low)
    high = float(high)
    if count == 1:
        return [low]
    if high < low:
        raise ValueError("grid range must be ordered")
    step = (high - low) / float(count - 1)
    return [low + step * index for index in range(count)]


def _threshold_score(scenario: ObstacleScenario) -> float:
    required = max(float(scenario.required_lateral_offset), 1e-6)
    aes_margin = float(scenario.conventional_lateral_capacity - scenario.required_lateral_offset) / required
    drift_margin = float(scenario.drift_lateral_capacity - scenario.required_lateral_offset) / required
    return float(min(abs(aes_margin), abs(drift_margin)))


def _friction_step_range_from_config(config: Any) -> tuple[int, int] | None:
    low, high = config.friction_step.step_range
    low = max(1, int(low))
    high = min(int(high), config.max_steps - 1)
    if high < low:
        return None
    return low, high


def _uses_obstacle_aligned_friction_step_config(config: Any) -> bool:
    return bool(
        config.friction_step.enabled
        and config.obstacle.enabled
        and config.obstacle.min_time_after_friction_step > 0.0
    )


def _obstacle_aligned_friction_step_range_from_config(
    *,
    config: Any,
    scenario: ObstacleScenario,
) -> tuple[int, int] | None:
    valid_range = _friction_step_range_from_config(config)
    if valid_range is None:
        return None
    low, high = valid_range
    latest_step = int(math.floor((scenario.time_to_obstacle - config.obstacle.min_time_after_friction_step) / config.dt))
    high = min(high, latest_step)
    if high < low:
        return None
    return low, high


def _obstacle_time_after_friction_step_from_config(
    *,
    config: Any,
    scenario: ObstacleScenario,
    friction_step_at: int | None,
) -> float:
    if friction_step_at is None:
        return float("inf")
    return float(scenario.time_to_obstacle - int(friction_step_at) * config.dt)


def _dominant(counts: Mapping[str, int], *, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    filtered = {key: value for key, value in counts.items() if key not in exclude}
    if not filtered:
        return ""
    return sorted(filtered.items(), key=lambda item: (-int(item[1]), str(item[0])))[0][0]


def load_repaired_specs(path: Path | str = DEFAULT_REPAIRED_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted([dict(row) for row in payload["executable_v2_panel_specs"]], key=lambda row: str(row["v2_panel_spec_id"]))


def load_reset_rows(path: Path | str = DEFAULT_RESET_ROWS) -> list[dict[str, Any]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("v2_panel_spec_id", "")))


def failed_aes_target_rows(
    *,
    repaired_specs: Iterable[Mapping[str, Any]],
    reset_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    specs_by_id = {str(row["v2_panel_spec_id"]): dict(row) for row in repaired_specs}
    targets: list[dict[str, Any]] = []
    for reset_row in reset_rows:
        spec_id = str(reset_row.get("v2_panel_spec_id", ""))
        if spec_id not in specs_by_id:
            continue
        if str(reset_row.get("v2_task_label", "")) != TARGET_LABEL:
            continue
        if _bool(reset_row.get("reset_success"), default=False):
            continue
        spec = dict(specs_by_id[spec_id])
        targets.append(
            {
                "v2_panel_spec_id": spec_id,
                "profile_name": spec.get("profile_name", ""),
                "source_v1_bounded_panel_spec_id": _source_key(spec),
                "source_scenario_spec_id": spec.get("source_scenario_spec_id", ""),
                "eval_seed": int(reset_row.get("eval_seed", 0) or 0),
                "v2_task_label": reset_row.get("v2_task_label", ""),
                "env_config": spec["env_config"],
            }
        )
    return sorted(targets, key=lambda row: str(row["v2_panel_spec_id"]))


def evaluate_grid_cell(
    *,
    config: Any,
    scenario_config: ObstacleScenarioConfig,
    speed_ref: float,
    mu: float,
    obstacle_distance: float,
    obstacle_half_width: float,
    friction_step_at: int | None,
) -> dict[str, Any]:
    scenario = classify_obstacle_scenario(
        speed=float(speed_ref),
        mu=float(mu),
        obstacle_distance=float(obstacle_distance),
        obstacle_half_width=float(obstacle_half_width),
        config=scenario_config,
    )
    threshold_score = _threshold_score(scenario)
    is_allowed = scenario.label in set(config.obstacle.allowed_labels)
    is_aeb_valid = not config.obstacle.require_aeb_infeasible or scenario.label != "aeb_feasible"
    is_near_threshold = config.obstacle.max_threshold_score is None or threshold_score <= config.obstacle.max_threshold_score
    aligned_step_range = (
        _obstacle_aligned_friction_step_range_from_config(config=config, scenario=scenario)
        if _uses_obstacle_aligned_friction_step_config(config)
        else None
    )
    time_after_step = _obstacle_time_after_friction_step_from_config(
        config=config,
        scenario=scenario,
        friction_step_at=friction_step_at,
    )
    has_time_after_step = (
        aligned_step_range is not None
        if _uses_obstacle_aligned_friction_step_config(config)
        else time_after_step >= config.obstacle.min_time_after_friction_step
    )

    if not is_aeb_valid:
        reject_reason = REJECT_AEB_FEASIBLE
    elif not is_allowed:
        reject_reason = REJECT_LABEL
    elif not is_near_threshold:
        reject_reason = REJECT_THRESHOLD
    elif not has_time_after_step:
        reject_reason = REJECT_FRICTION_TIMING
    else:
        reject_reason = ACCEPTED

    return {
        "speed_ref": float(speed_ref),
        "initial_mu": float(mu),
        "obstacle_distance": float(obstacle_distance),
        "obstacle_half_width": float(obstacle_half_width),
        "label": scenario.label,
        "threshold_score": float(threshold_score),
        "time_to_obstacle": float(scenario.time_to_obstacle),
        "time_after_friction_step": float(time_after_step),
        "friction_step_at": _friction_value(friction_step_at),
        "aligned_friction_step_low": "" if aligned_step_range is None else int(aligned_step_range[0]),
        "aligned_friction_step_high": "" if aligned_step_range is None else int(aligned_step_range[1]),
        "accepted": reject_reason == ACCEPTED,
        "reject_reason": reject_reason,
    }


def scan_profile_grid(
    *,
    target: Mapping[str, Any],
    distance_values: Iterable[float],
    half_width_values: Iterable[float],
    max_boundary_examples: int = 8,
) -> dict[str, Any]:
    env_config = dict(target["env_config"])
    config = build_env_config(env_config)
    reset_state = reset_sampler_state_from_seed(env_config=env_config, seed=int(target["eval_seed"]))
    speed_ref = float(reset_state["speed_ref"])
    initial_mu = float(reset_state["initial_mu"])
    friction_step_at = reset_state["friction_step_at"]
    scenario_config = config.obstacle.scenario_config(speed=speed_ref, mu=initial_mu)
    label_counts: Counter[str] = Counter()
    reject_counts: Counter[str] = Counter()
    accepted_cells: list[dict[str, Any]] = []
    boundary_examples: list[dict[str, Any]] = []
    grid_cell_count = 0

    metadata = {
        "v2_panel_spec_id": target["v2_panel_spec_id"],
        "profile_name": target.get("profile_name", ""),
        "source_v1_bounded_panel_spec_id": target.get("source_v1_bounded_panel_spec_id", ""),
        "source_scenario_spec_id": target.get("source_scenario_spec_id", ""),
        "eval_seed": int(target.get("eval_seed", 0) or 0),
    }

    for distance in distance_values:
        for half_width in half_width_values:
            grid_cell_count += 1
            cell = evaluate_grid_cell(
                config=config,
                scenario_config=scenario_config,
                speed_ref=speed_ref,
                mu=initial_mu,
                obstacle_distance=float(distance),
                obstacle_half_width=float(half_width),
                friction_step_at=friction_step_at,
            )
            label_counts[str(cell["label"])] += 1
            reject_counts[str(cell["reject_reason"])] += 1
            row = {**metadata, **cell}
            if bool(cell["accepted"]) and str(cell["label"]) == TARGET_LABEL:
                accepted_cells.append(row)
            elif len(boundary_examples) < max(0, int(max_boundary_examples)):
                boundary_examples.append(row)

    accepted_distance = [float(row["obstacle_distance"]) for row in accepted_cells]
    accepted_half_width = [float(row["obstacle_half_width"]) for row in accepted_cells]
    profile_summary = {
        **metadata,
        "speed_ref": speed_ref,
        "initial_mu": initial_mu,
        "friction_step_at": _friction_value(friction_step_at),
        "grid_cell_count": int(grid_cell_count),
        "accepted_cell_count": len(accepted_cells),
        "accepted_distance_min": min(accepted_distance) if accepted_distance else "",
        "accepted_distance_max": max(accepted_distance) if accepted_distance else "",
        "accepted_half_width_min": min(accepted_half_width) if accepted_half_width else "",
        "accepted_half_width_max": max(accepted_half_width) if accepted_half_width else "",
        "dominant_label": _dominant(label_counts),
        "dominant_reject_reason": _dominant(reject_counts, exclude={ACCEPTED}),
        "feasible": len(accepted_cells) > 0,
    }
    label_count_rows = [
        {**metadata, "label": label, "count": int(count)} for label, count in sorted(label_counts.items())
    ]
    reject_reason_rows = [
        {**metadata, "reject_reason": reason, "count": int(count)} for reason, count in sorted(reject_counts.items())
    ]
    return {
        "profile_summary": profile_summary,
        "accepted_cells": accepted_cells,
        "label_count_rows": label_count_rows,
        "reject_reason_rows": reject_reason_rows,
        "boundary_examples": boundary_examples,
    }


def source_summary_rows(profile_summaries: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in profile_summaries:
        grouped[str(row.get("source_v1_bounded_panel_spec_id", ""))].append(row)

    output: list[dict[str, Any]] = []
    for source, rows in sorted(grouped.items()):
        feasible_rows = [row for row in rows if _bool(row.get("feasible"))]
        accepted_cell_count_total = sum(int(row.get("accepted_cell_count", 0) or 0) for row in rows)
        distance_mins = [float(row["accepted_distance_min"]) for row in feasible_rows if row.get("accepted_distance_min") != ""]
        distance_maxs = [float(row["accepted_distance_max"]) for row in feasible_rows if row.get("accepted_distance_max") != ""]
        half_mins = [float(row["accepted_half_width_min"]) for row in feasible_rows if row.get("accepted_half_width_min") != ""]
        half_maxs = [float(row["accepted_half_width_max"]) for row in feasible_rows if row.get("accepted_half_width_max") != ""]
        output.append(
            {
                "source_v1_bounded_panel_spec_id": source,
                "source_scenario_spec_id": rows[0].get("source_scenario_spec_id", "") if rows else "",
                "profile_count": len(rows),
                "feasible_profile_count": len(feasible_rows),
                "accepted_cell_count_total": int(accepted_cell_count_total),
                "distance_min_suggestion": min(distance_mins) if distance_mins else "",
                "distance_max_suggestion": max(distance_maxs) if distance_maxs else "",
                "half_width_min_suggestion": min(half_mins) if half_mins else "",
                "half_width_max_suggestion": max(half_maxs) if half_maxs else "",
                "source_feasible": len(rows) > 0 and len(feasible_rows) == len(rows),
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "reset_time_aes_feasibility_scan_helper",
            "admissible": True,
            "reason": "no-reset helper can scan conditional AES-only grid support",
        },
        {
            "claim": "project_artifact_scan_result",
            "admissible": False,
            "reason": "M1841 implements helper and tests only; project artifacts require later execution design",
        },
        {
            "claim": "source_repair_payload_generated",
            "admissible": False,
            "reason": "scan evidence must precede source repair v3 payload generation",
        },
        {
            "claim": "reset_feasibility_repaired",
            "admissible": False,
            "reason": "feasibility scan does not repair or validate reset feasibility",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "feasibility scan is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_reset_time_aes_feasibility_scan(
    *,
    repaired_specs_path: Path | str = DEFAULT_REPAIRED_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    distance_range: tuple[float, float] = DEFAULT_DISTANCE_RANGE,
    distance_count: int = DEFAULT_DISTANCE_COUNT,
    half_width_range: tuple[float, float] = DEFAULT_HALF_WIDTH_RANGE,
    half_width_count: int = DEFAULT_HALF_WIDTH_COUNT,
    max_boundary_examples_per_profile: int = 8,
    expected_target_source_count: int | None = 2,
    expected_target_profile_count_total: int | None = 24,
    next_blocker: str = "m1844-executable-v2-reset-time-aes-feasibility-scan-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    repaired_specs = load_repaired_specs(repaired_specs_path)
    reset_rows = load_reset_rows(reset_rows_path)
    targets = failed_aes_target_rows(repaired_specs=repaired_specs, reset_rows=reset_rows)
    distance_values = _linspace(float(distance_range[0]), float(distance_range[1]), int(distance_count))
    half_width_values = _linspace(float(half_width_range[0]), float(half_width_range[1]), int(half_width_count))

    profile_summary: list[dict[str, Any]] = []
    accepted_cells: list[dict[str, Any]] = []
    label_count_rows: list[dict[str, Any]] = []
    reject_reason_rows: list[dict[str, Any]] = []
    boundary_examples: list[dict[str, Any]] = []
    for target in targets:
        scan = scan_profile_grid(
            target=target,
            distance_values=distance_values,
            half_width_values=half_width_values,
            max_boundary_examples=max_boundary_examples_per_profile,
        )
        profile_summary.append(scan["profile_summary"])
        accepted_cells.extend(scan["accepted_cells"])
        label_count_rows.extend(scan["label_count_rows"])
        reject_reason_rows.extend(scan["reject_reason_rows"])
        boundary_examples.extend(scan["boundary_examples"])

    source_summary = source_summary_rows(profile_summary)
    target_source_count = len({str(row.get("source_v1_bounded_panel_spec_id", "")) for row in targets})
    feasible_profile_count_total = sum(_bool(row.get("feasible")) for row in profile_summary)
    feasible_source_count = sum(_bool(row.get("source_feasible")) for row in source_summary)
    grid_cell_count_total = sum(int(row.get("grid_cell_count", 0) or 0) for row in profile_summary)
    accepted_cell_count_total = len(accepted_cells)
    all_profiles_supported = len(profile_summary) > 0 and feasible_profile_count_total == len(profile_summary)
    no_profiles_supported = feasible_profile_count_total == 0
    if all_profiles_supported:
        result_class = "reset_time_aes_feasibility_scan_full_support"
    elif no_profiles_supported:
        result_class = "reset_time_aes_feasibility_scan_no_support"
    else:
        result_class = "reset_time_aes_feasibility_scan_partial_support"

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    expected_source_match = expected_target_source_count is None or target_source_count == int(expected_target_source_count)
    expected_profile_match = (
        expected_target_profile_count_total is None
        or len(profile_summary) == int(expected_target_profile_count_total)
    )

    write_csv_rows(output / "reset_time_aes_feasibility_profile_summary.csv", profile_summary)
    write_csv_rows(output / "reset_time_aes_feasibility_source_summary.csv", source_summary)
    write_csv_rows(output / "reset_time_aes_feasibility_accepted_cells.csv", accepted_cells)
    write_csv_rows(output / "reset_time_aes_feasibility_label_counts.csv", label_count_rows)
    write_csv_rows(output / "reset_time_aes_feasibility_reject_reason_counts.csv", reject_reason_rows)
    write_csv_rows(output / "reset_time_aes_feasibility_boundary_examples.csv", boundary_examples)
    write_csv_rows(output / "reset_time_aes_feasibility_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repaired_specs_path": str(repaired_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "target_source_count": int(target_source_count),
        "expected_target_source_count": expected_target_source_count,
        "target_profile_count_total": len(profile_summary),
        "expected_target_profile_count_total": expected_target_profile_count_total,
        "feasible_profile_count_total": int(feasible_profile_count_total),
        "feasible_source_count": int(feasible_source_count),
        "grid_cell_count_total": int(grid_cell_count_total),
        "accepted_cell_count_total": int(accepted_cell_count_total),
        "label_count_total": sum(int(row.get("count", 0) or 0) for row in label_count_rows),
        "reject_reason_count_total": sum(int(row.get("count", 0) or 0) for row in reject_reason_rows),
        "distance_range": [float(distance_range[0]), float(distance_range[1])],
        "distance_count": int(distance_count),
        "half_width_range": [float(half_width_range[0]), float(half_width_range[1])],
        "half_width_count": int(half_width_count),
        "expected_source_match": bool(expected_source_match),
        "expected_profile_match": bool(expected_profile_match),
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
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "profile_summary": str(output / "reset_time_aes_feasibility_profile_summary.csv"),
            "source_summary": str(output / "reset_time_aes_feasibility_source_summary.csv"),
            "accepted_cells": str(output / "reset_time_aes_feasibility_accepted_cells.csv"),
            "label_counts": str(output / "reset_time_aes_feasibility_label_counts.csv"),
            "reject_reason_counts": str(output / "reset_time_aes_feasibility_reject_reason_counts.csv"),
            "boundary_examples": str(output / "reset_time_aes_feasibility_boundary_examples.csv"),
            "claim_boundary": str(output / "reset_time_aes_feasibility_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repaired-specs", type=Path, default=DEFAULT_REPAIRED_SPECS)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--distance-min", type=float, default=DEFAULT_DISTANCE_RANGE[0])
    parser.add_argument("--distance-max", type=float, default=DEFAULT_DISTANCE_RANGE[1])
    parser.add_argument("--distance-count", type=int, default=DEFAULT_DISTANCE_COUNT)
    parser.add_argument("--half-width-min", type=float, default=DEFAULT_HALF_WIDTH_RANGE[0])
    parser.add_argument("--half-width-max", type=float, default=DEFAULT_HALF_WIDTH_RANGE[1])
    parser.add_argument("--half-width-count", type=int, default=DEFAULT_HALF_WIDTH_COUNT)
    parser.add_argument("--max-boundary-examples-per-profile", type=int, default=8)
    parser.add_argument("--expected-target-source-count", type=int, default=2)
    parser.add_argument("--expected-target-profile-count-total", type=int, default=24)
    parser.add_argument(
        "--next-blocker",
        default="m1844-executable-v2-reset-time-aes-feasibility-scan-result-audit",
    )
    args = parser.parse_args()
    summary = run_reset_time_aes_feasibility_scan(
        repaired_specs_path=args.repaired_specs,
        reset_rows_path=args.reset_rows,
        output_dir=args.output_dir,
        distance_range=(args.distance_min, args.distance_max),
        distance_count=args.distance_count,
        half_width_range=(args.half_width_min, args.half_width_max),
        half_width_count=args.half_width_count,
        max_boundary_examples_per_profile=args.max_boundary_examples_per_profile,
        expected_target_source_count=args.expected_target_source_count,
        expected_target_profile_count_total=args.expected_target_profile_count_total,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"target_profile_count_total={summary['target_profile_count_total']}")
    print(f"feasible_profile_count_total={summary['feasible_profile_count_total']}")
    print(f"accepted_cell_count_total={summary['accepted_cell_count_total']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
