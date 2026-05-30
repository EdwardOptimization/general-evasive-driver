"""No-reset source-level sampler repair planner for targeted reset failures."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.scenarios import ObstacleScenarioConfig, classify_obstacle_scenario


DEFAULT_TARGETED_RESET_SPECS = Path(
    "runs/m1816_executable_v2_stable_source_reset_validation_adapter/targeted_reset_executable_v2_panel_specs.json"
)
DEFAULT_RESET_ROWS = Path("runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/reset_stress_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1823_executable_v2_stable_source_targeted_reset_sampler_repair")
SYSTEMATIC_ATTEMPTS = 10000
SPARSE_ATTEMPTS = 5000
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


def _read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_targeted_reset_specs(path: Path | str = DEFAULT_TARGETED_RESET_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted([dict(row) for row in payload["executable_v2_panel_specs"]], key=lambda row: str(row["v2_panel_spec_id"]))


def load_reset_rows(path: Path | str = DEFAULT_RESET_ROWS) -> list[dict[str, Any]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("v2_panel_spec_id", "")))


def _source_key(row: Mapping[str, Any]) -> str:
    return str(
        row.get(
            "materialized_bounded_panel_spec_id",
            row.get("source_scenario_spec_id", row.get("source_v1_bounded_panel_spec_id", "")),
        )
    )


def _range(value: Any, default: tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (float(value[0]), float(value[1]))
    return default


def _speed_range(env_config: Mapping[str, Any]) -> tuple[float, float]:
    return _range(env_config.get("speed_range"), (8.0, 16.0))


def _mu_range(env_config: Mapping[str, Any]) -> tuple[float, float]:
    randomization = dict(env_config.get("randomization", {}))
    friction_step = dict(env_config.get("friction_step", {}))
    if _bool(friction_step.get("enabled"), default=False):
        return _range(friction_step.get("mu_range"), _range(randomization.get("mu_range"), (0.25, 1.15)))
    return _range(randomization.get("mu_range"), (0.25, 1.15))


def _linspace_range(bounds: tuple[float, float], count: int) -> list[float]:
    low, high = bounds
    if count <= 1 or abs(high - low) < 1e-9:
        return [float((low + high) / 2.0)]
    return [float(item) for item in np.linspace(low, high, count)]


def label_density(
    *,
    env_config: Mapping[str, Any],
    obstacle: Mapping[str, Any],
    target_label: str,
    speed_count: int = 5,
    mu_count: int = 5,
    distance_count: int = 9,
    half_width_count: int = 5,
) -> float:
    speeds = _linspace_range(_speed_range(env_config), speed_count)
    mus = _linspace_range(_mu_range(env_config), mu_count)
    distance_range = _range(obstacle.get("distance_range"), (16.0, 55.0))
    half_width_range = _range(obstacle.get("half_width_range"), (0.45, 1.15))
    distances = _linspace_range(distance_range, distance_count)
    half_widths = _linspace_range(half_width_range, half_width_count)
    scenario_config = ObstacleScenarioConfig(
        obstacle_distance_range=distance_range,
        obstacle_half_width_range=half_width_range,
        ego_half_width=float(obstacle.get("ego_half_width", 0.90)),
        safety_margin=float(obstacle.get("safety_margin", 0.30)),
        brake_mu_fraction=float(obstacle.get("brake_mu_fraction", 0.90)),
        conventional_lateral_mu_fraction=float(obstacle.get("conventional_lateral_mu_fraction", 0.42)),
        drift_lateral_mu_fraction=float(obstacle.get("drift_lateral_mu_fraction", 0.85)),
    )
    total = 0
    hits = 0
    for speed in speeds:
        for mu in mus:
            for distance in distances:
                for half_width in half_widths:
                    scenario = classify_obstacle_scenario(
                        speed=speed,
                        mu=mu,
                        obstacle_distance=distance,
                        obstacle_half_width=half_width,
                        config=scenario_config,
                    )
                    total += 1
                    hits += int(scenario.label == target_label)
    return float(hits / max(total, 1))


def _candidate_obstacles(env_config: Mapping[str, Any], target_label: str, repair_class: str) -> list[dict[str, Any]]:
    base = deepcopy(dict(env_config.get("obstacle", {})))
    original_distance = _range(base.get("distance_range"), (16.0, 55.0))
    original_half = _range(base.get("half_width_range"), (0.45, 1.15))
    candidates: list[dict[str, Any]] = []

    def add(name: str, distance: tuple[float, float], half_width: tuple[float, float], attempts: int) -> None:
        candidate = deepcopy(base)
        candidate["repair_candidate_name"] = name
        candidate["allowed_labels"] = [target_label]
        candidate["max_sample_attempts"] = max(int(candidate.get("max_sample_attempts", 0) or 0), attempts)
        candidate["distance_range"] = [float(distance[0]), float(distance[1])]
        candidate["half_width_range"] = [float(half_width[0]), float(half_width[1])]
        if target_label == "aes_feasible":
            candidate["require_aeb_infeasible"] = True
        elif target_label == "aeb_feasible":
            candidate["require_aeb_infeasible"] = False
        candidates.append(candidate)

    attempts = SYSTEMATIC_ATTEMPTS if repair_class == "systematic" else SPARSE_ATTEMPTS
    add("original_attempts", original_distance, original_half, attempts)
    if target_label == "aes_feasible":
        add("aes_medium_band", (10.0, 55.0), (0.35, 1.15), attempts)
        add("aes_close_medium_band", (8.0, 45.0), (0.35, 1.05), attempts)
        add("aes_wide_search_band", (6.0, 70.0), (0.30, 1.25), attempts)
    elif target_label == "aeb_feasible":
        add("aeb_far_narrow_band", (max(18.0, original_distance[0]), max(55.0, original_distance[1])), (0.30, 0.90), attempts)
        add("aeb_wide_search_band", (16.0, 75.0), (0.30, 1.00), attempts)
    return candidates


def _select_repaired_obstacle(
    *,
    env_config: Mapping[str, Any],
    target_label: str,
    repair_class: str,
) -> tuple[dict[str, Any], float]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for obstacle in _candidate_obstacles(env_config, target_label, repair_class):
        density = label_density(env_config=env_config, obstacle=obstacle, target_label=target_label)
        scored.append((density, obstacle))
    scored.sort(key=lambda item: (item[0], str(item[1].get("repair_candidate_name", ""))), reverse=True)
    return scored[0][1], float(scored[0][0])


def repair_targets(
    *,
    targeted_specs: list[Mapping[str, Any]],
    reset_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reset_by_id = {str(row["v2_panel_spec_id"]): row for row in reset_rows}
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for spec in targeted_specs:
        grouped[_source_key(spec)].append(spec)

    targets: list[dict[str, Any]] = []
    for source_key in sorted(grouped):
        specs = grouped[source_key]
        failures = [spec for spec in specs if not _bool(reset_by_id.get(str(spec["v2_panel_spec_id"]), {}).get("reset_success"))]
        if not failures:
            continue
        successes = len(specs) - len(failures)
        first = specs[0]
        repair_class = "systematic" if successes == 0 else "sparse"
        target_label = str(first.get("v2_task_label", ""))
        targets.append(
            {
                "repair_target_id": f"repair-{len(targets):03d}",
                "source_key": source_key,
                "target_label": target_label,
                "repair_class": repair_class,
                "attempted_profile_count": len(specs),
                "reset_success_count": successes,
                "sampling_failure_count": len(failures),
                "hidden_dynamics_bucket": str(first.get("hidden_dynamics_bucket", "")),
                "road_boundary_bucket": str(first.get("road_boundary_bucket", "")),
                "obstacle_timing_bucket": str(first.get("obstacle_timing_bucket", "")),
                "obstacle_lateral_bucket": str(first.get("obstacle_lateral_bucket", "")),
                "profile_names": ";".join(sorted(str(spec.get("profile_name", "")) for spec in specs)),
            }
        )
    return targets


def repaired_specs(
    *,
    targeted_specs: list[Mapping[str, Any]],
    reset_rows: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    targets = repair_targets(targeted_specs=targeted_specs, reset_rows=reset_rows)
    target_by_source = {str(row["source_key"]): row for row in targets}
    repaired: list[dict[str, Any]] = []
    for spec in targeted_specs:
        row = deepcopy(dict(spec))
        target = target_by_source.get(_source_key(spec))
        if target is None:
            row["source_sampler_repair_applied"] = False
            row["source_sampler_repair_class"] = ""
            row["source_sampler_repair_density"] = ""
            repaired.append(row)
            continue
        env_config = deepcopy(dict(row["env_config"]))
        obstacle, density = _select_repaired_obstacle(
            env_config=env_config,
            target_label=str(target["target_label"]),
            repair_class=str(target["repair_class"]),
        )
        env_config["obstacle"] = {key: value for key, value in obstacle.items() if key != "repair_candidate_name"}
        row["env_config"] = env_config
        row["source_sampler_repair_applied"] = True
        row["source_sampler_repair_class"] = str(target["repair_class"])
        row["source_sampler_repair_candidate"] = str(obstacle.get("repair_candidate_name", ""))
        row["source_sampler_repair_density"] = density
        row["source_sampler_repair_target_id"] = str(target["repair_target_id"])
        row["reset_ready_spec"] = True
        row["reset_validation_required"] = True
        row["labels_enter_actor_input"] = False
        row["v2_ranking_admissible_by_default"] = False
        repaired.append(row)
    return sorted(repaired, key=lambda row: str(row["v2_panel_spec_id"])), targets


def _target_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "repair_target_id": row.get("repair_target_id", ""),
        "source_key": row.get("source_key", ""),
        "target_label": row.get("target_label", ""),
        "repair_class": row.get("repair_class", ""),
        "attempted_profile_count": row.get("attempted_profile_count", ""),
        "reset_success_count": row.get("reset_success_count", ""),
        "sampling_failure_count": row.get("sampling_failure_count", ""),
        "hidden_dynamics_bucket": row.get("hidden_dynamics_bucket", ""),
        "road_boundary_bucket": row.get("road_boundary_bucket", ""),
        "obstacle_timing_bucket": row.get("obstacle_timing_bucket", ""),
        "obstacle_lateral_bucket": row.get("obstacle_lateral_bucket", ""),
        "profile_names": row.get("profile_names", ""),
    }


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "source_level_sampler_repair_plan",
            "admissible": True,
            "reason": "no-reset repaired payload can guide later reset preflight",
        },
        {
            "claim": "reset_feasibility_repaired",
            "admissible": False,
            "reason": "repaired payload still requires reset-only validation",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "measured execution remains blocked until reset support is observed",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "sampler repair is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_targeted_reset_sampler_repair_planner(
    *,
    targeted_reset_specs_path: Path | str = DEFAULT_TARGETED_RESET_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_repair_source_count: int | None = 3,
    target_profile_count: int | None = 12,
    target_repaired_spec_count: int | None = 36,
    next_blocker: str = "m1824-executable-v2-stable-source-targeted-reset-sampler-repair-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    targeted_specs = load_targeted_reset_specs(targeted_reset_specs_path)
    reset_rows = load_reset_rows(reset_rows_path)
    repaired, targets = repaired_specs(targeted_specs=targeted_specs, reset_rows=reset_rows)

    profile_count = len({str(row.get("profile_name", "")) for row in repaired})
    repair_source_count = len(targets)
    systematic_source_count = sum(str(row["repair_class"]) == "systematic" for row in targets)
    sparse_source_count = sum(str(row["repair_class"]) == "sparse" for row in targets)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in repaired)
    ranking_admissible_by_default_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in repaired)
    reset_ready_spec_count = sum(_bool(row.get("reset_ready_spec")) for row in repaired)
    repaired_spec_matches = target_repaired_spec_count is None or len(repaired) == int(target_repaired_spec_count)
    repair_source_matches = target_repair_source_count is None or repair_source_count == int(target_repair_source_count)
    profile_matches = target_profile_count is None or profile_count == int(target_profile_count)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    result_passes = (
        repaired_spec_matches
        and repair_source_matches
        and profile_matches
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and reset_ready_spec_count == len(repaired)
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "source_sampler_repair_targets.csv", [_target_row(row) for row in targets])
    write_json(output / "source_sampler_repair_specs.json", {"source_sampler_repair_specs": repaired})
    write_csv_rows(output / "source_sampler_repair_specs.csv", repaired)
    write_csv_rows(output / "source_sampler_repair_matrix.csv", repaired)
    write_json(
        output / "repaired_targeted_reset_executable_v2_panel_specs.json",
        {"generated_at_utc": utc_timestamp(), "executable_v2_panel_specs": repaired},
    )
    write_csv_rows(output / "source_sampler_repair_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "targeted_reset_sampler_repair_planner_pass"
            if result_passes
            else "targeted_reset_sampler_repair_planner_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "targeted_reset_specs_path": str(targeted_reset_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "input_spec_count": len(targeted_specs),
        "input_reset_row_count": len(reset_rows),
        "repair_target_source_count": repair_source_count,
        "target_repair_source_count": target_repair_source_count,
        "systematic_source_count": systematic_source_count,
        "sparse_source_count": sparse_source_count,
        "profile_control_count": profile_count,
        "target_profile_count": target_profile_count,
        "repaired_executable_spec_count": len(repaired),
        "target_repaired_spec_count": target_repaired_spec_count,
        "reset_ready_spec_count": reset_ready_spec_count,
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "ranking_admissible_by_default_count": ranking_admissible_by_default_count,
        "repair_class_counts": _count_by_key(targets, "repair_class"),
        "repair_label_counts": _count_by_key(targets, "target_label"),
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
            "source_sampler_repair_targets": str(output / "source_sampler_repair_targets.csv"),
            "source_sampler_repair_specs": str(output / "source_sampler_repair_specs.json"),
            "repaired_targeted_reset_executable_v2_panel_specs": str(
                output / "repaired_targeted_reset_executable_v2_panel_specs.json"
            ),
            "source_sampler_repair_claim_boundary": str(output / "source_sampler_repair_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan no-reset targeted reset sampler repair artifacts.")
    parser.add_argument("--targeted-reset-specs", type=Path, default=DEFAULT_TARGETED_RESET_SPECS)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-repair-source-count", type=int, default=3)
    parser.add_argument("--target-profile-count", type=int, default=12)
    parser.add_argument("--target-repaired-spec-count", type=int, default=36)
    parser.add_argument("--next-blocker", default="m1824-executable-v2-stable-source-targeted-reset-sampler-repair-execution-design")
    args = parser.parse_args()

    summary = run_targeted_reset_sampler_repair_planner(
        targeted_reset_specs_path=args.targeted_reset_specs,
        reset_rows_path=args.reset_rows,
        output_dir=args.output_dir,
        target_repair_source_count=args.target_repair_source_count,
        target_profile_count=args.target_profile_count,
        target_repaired_spec_count=args.target_repaired_spec_count,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"repair_target_source_count={summary['repair_target_source_count']}")
    print(f"repaired_executable_spec_count={summary['repaired_executable_spec_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
