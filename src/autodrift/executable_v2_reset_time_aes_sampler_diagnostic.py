"""Reset-time sampler diagnostics for executable v2 AES reset failures."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import asdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.dynamics import sample_vehicle_params
from autodrift.scenarios import ObstacleScenario, classify_obstacle_scenario
from autodrift.tasks import make_track


DEFAULT_REPAIRED_SPECS = Path(
    "runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/"
    "repaired_targeted_reset_executable_v2_panel_specs.json"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic")
TARGET_LABEL = "aes_feasible"
ACCEPTED = "accepted"
REJECT_AEB_FEASIBLE = "aeb_feasible_rejected"
REJECT_LABEL = "label_not_allowed"
REJECT_THRESHOLD = "threshold_filter"
REJECT_FRICTION_TIMING = "friction_timing_filter"
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


def _range(value: Any, default: tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (float(value[0]), float(value[1]))
    return default


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _threshold_score(scenario: ObstacleScenario) -> float:
    required = max(float(scenario.required_lateral_offset), 1e-6)
    aes_margin = float(scenario.conventional_lateral_capacity - scenario.required_lateral_offset) / required
    drift_margin = float(scenario.drift_lateral_capacity - scenario.required_lateral_offset) / required
    return float(min(abs(aes_margin), abs(drift_margin)))


def _friction_step_range(env_config: Mapping[str, Any]) -> tuple[int, int] | None:
    config = build_env_config(dict(env_config))
    low, high = config.friction_step.step_range
    low = max(1, int(low))
    high = min(int(high), config.max_steps - 1)
    if high < low:
        return None
    return low, high


def _uses_obstacle_aligned_friction_step(env_config: Mapping[str, Any]) -> bool:
    config = build_env_config(dict(env_config))
    return bool(
        config.friction_step.enabled
        and config.obstacle.enabled
        and config.obstacle.min_time_after_friction_step > 0.0
    )


def _obstacle_time_after_friction_step(
    *,
    env_config: Mapping[str, Any],
    scenario: ObstacleScenario,
    friction_step_at: int | None,
) -> float:
    config = build_env_config(dict(env_config))
    if friction_step_at is None:
        return float("inf")
    return float(scenario.time_to_obstacle - int(friction_step_at) * config.dt)


def _obstacle_aligned_friction_step_range(
    *,
    env_config: Mapping[str, Any],
    scenario: ObstacleScenario,
) -> tuple[int, int] | None:
    config = build_env_config(dict(env_config))
    valid_range = _friction_step_range(env_config)
    if valid_range is None:
        return None
    low, high = valid_range
    latest_step = int(math.floor((scenario.time_to_obstacle - config.obstacle.min_time_after_friction_step) / config.dt))
    high = min(high, latest_step)
    if high < low:
        return None
    return low, high


def _sample_friction_step_at(*, env_config: Mapping[str, Any], rng: np.random.Generator) -> int | None:
    config = build_env_config(dict(env_config))
    if not config.friction_step.enabled:
        return None
    valid_range = _friction_step_range(env_config)
    if valid_range is None:
        return None
    low, high = valid_range
    if high <= low:
        return int(low)
    return int(rng.integers(low, high + 1))


def _sample_speed_ref(*, env_config: Mapping[str, Any], rng: np.random.Generator, mu: float) -> float:
    config = build_env_config(dict(env_config))
    low, high = config.speed_range
    if config.friction_limited_speed:
        track = make_track(config.track_kind, config.track_radius)
        friction_speed = math.sqrt(max(float(mu) * 9.81 * track.reference_radius, 1e-6))
        high = min(high, friction_speed * config.friction_speed_margin)
    if high <= low:
        return float(max(high, 1.0))
    return float(rng.uniform(low, high))


def _advance_rng_to_obstacle_sampler(
    *,
    env_config: Mapping[str, Any],
    rng: np.random.Generator,
    speed_ref: float,
) -> None:
    config = build_env_config(dict(env_config))
    rng.uniform(*config.beta_target_range)
    initial_beta = float(rng.normal(0.0, 0.04))
    track = make_track(config.track_kind, config.track_radius)
    track.reset_pose(rng, float(speed_ref), beta=initial_beta)
    if config.warmup_gate.enabled:
        rng.uniform(*config.warmup_gate.distance_range)
        rng.uniform(*config.warmup_gate.lateral_offset_range)
        rng.uniform(*config.warmup_gate.half_width_range)


def reset_sampler_state_from_seed(*, env_config: Mapping[str, Any], seed: int) -> dict[str, Any]:
    """Reproduce reset RNG state up to obstacle sampling without calling env.reset."""

    config = build_env_config(dict(env_config))
    rng = np.random.default_rng(int(seed))
    params = sample_vehicle_params(rng, config=config.randomization)
    friction_step_at = (
        None
        if _uses_obstacle_aligned_friction_step(env_config)
        else _sample_friction_step_at(env_config=env_config, rng=rng)
    )
    speed_ref = _sample_speed_ref(env_config=env_config, rng=rng, mu=float(params.mu))
    _advance_rng_to_obstacle_sampler(env_config=env_config, rng=rng, speed_ref=speed_ref)
    return {
        "rng": rng,
        "speed_ref": float(speed_ref),
        "initial_mu": float(params.mu),
        "friction_step_at": friction_step_at,
    }


def evaluate_obstacle_candidate(
    *,
    env_config: Mapping[str, Any],
    speed_ref: float,
    mu: float,
    obstacle_distance: float,
    obstacle_half_width: float,
    friction_step_at: int | None = None,
) -> dict[str, Any]:
    config = build_env_config(dict(env_config))
    scenario = classify_obstacle_scenario(
        speed=float(speed_ref),
        mu=float(mu),
        obstacle_distance=float(obstacle_distance),
        obstacle_half_width=float(obstacle_half_width),
        config=config.obstacle.scenario_config(speed=float(speed_ref), mu=float(mu)),
    )
    threshold_score = _threshold_score(scenario)
    allowed_labels = set(config.obstacle.allowed_labels)
    is_allowed = scenario.label in allowed_labels
    is_aeb_valid = not config.obstacle.require_aeb_infeasible or scenario.label != "aeb_feasible"
    is_near_threshold = config.obstacle.max_threshold_score is None or threshold_score <= config.obstacle.max_threshold_score
    aligned_step_range = (
        _obstacle_aligned_friction_step_range(env_config=env_config, scenario=scenario)
        if _uses_obstacle_aligned_friction_step(env_config)
        else None
    )
    time_after_step = _obstacle_time_after_friction_step(
        env_config=env_config,
        scenario=scenario,
        friction_step_at=friction_step_at,
    )
    has_time_after_step = (
        aligned_step_range is not None
        if _uses_obstacle_aligned_friction_step(env_config)
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
        "threshold_score": threshold_score,
        "time_to_obstacle": float(scenario.time_to_obstacle),
        "time_after_friction_step": float(time_after_step),
        "friction_step_at": "" if friction_step_at is None else int(friction_step_at),
        "aligned_friction_step_low": "" if aligned_step_range is None else int(aligned_step_range[0]),
        "aligned_friction_step_high": "" if aligned_step_range is None else int(aligned_step_range[1]),
        "accepted": reject_reason == ACCEPTED,
        "reject_reason": reject_reason,
    }


def replay_reset_time_obstacle_attempts(
    *,
    env_config: Mapping[str, Any],
    seed: int,
    max_attempts: int | None = None,
) -> list[dict[str, Any]]:
    """Replay obstacle sampler attempts up to first accepted candidate."""

    config = build_env_config(dict(env_config))
    state = reset_sampler_state_from_seed(env_config=env_config, seed=int(seed))
    rng = state["rng"]
    attempts = int(max_attempts or config.obstacle.max_sample_attempts)
    rows: list[dict[str, Any]] = []
    for attempt_index in range(max(1, attempts)):
        obstacle_distance = float(rng.uniform(*config.obstacle.distance_range))
        obstacle_half_width = float(rng.uniform(*config.obstacle.half_width_range))
        row = evaluate_obstacle_candidate(
            env_config=env_config,
            speed_ref=float(state["speed_ref"]),
            mu=float(state["initial_mu"]),
            obstacle_distance=obstacle_distance,
            obstacle_half_width=obstacle_half_width,
            friction_step_at=state["friction_step_at"],
        )
        row["attempt_index"] = int(attempt_index)
        rows.append(row)
        if bool(row["accepted"]):
            break
    return rows


def summarize_attempts(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    label_counts = _count_by_key(rows, "label")
    reject_counts = _count_by_key(rows, "reject_reason")
    accepted_count = int(sum(_bool(row.get("accepted")) for row in rows))
    dominant_reject_reason = ""
    nonaccepted = {key: value for key, value in reject_counts.items() if key != ACCEPTED}
    if nonaccepted:
        dominant_reject_reason = sorted(nonaccepted.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return {
        "attempt_count": len(rows),
        "accepted_count": accepted_count,
        "label_counts": label_counts,
        "reject_reason_counts": reject_counts,
        "dominant_reject_reason": dominant_reject_reason,
    }


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "reset_time_sampler_diagnostic_plan",
            "admissible": True,
            "reason": "diagnostic rows can guide source-level sampler repair",
        },
        {
            "claim": "reset_feasibility_repaired",
            "admissible": False,
            "reason": "diagnostic does not repair or validate reset feasibility",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "measured execution remains blocked until reset support is observed",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "sampler diagnostic is task-quality infrastructure, not ranking evidence",
        },
    ]


def load_repaired_specs(path: Path | str = DEFAULT_REPAIRED_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted([dict(row) for row in payload["executable_v2_panel_specs"]], key=lambda row: str(row["v2_panel_spec_id"]))


def load_reset_rows(path: Path | str = DEFAULT_RESET_ROWS) -> list[dict[str, Any]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("v2_panel_spec_id", "")))


def failed_aes_target_ids(reset_rows: Iterable[Mapping[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for row in reset_rows:
        if str(row.get("v2_task_label", "")) != TARGET_LABEL:
            continue
        if _bool(row.get("reset_success"), default=False):
            continue
        ids.add(str(row.get("v2_panel_spec_id", "")))
    return ids


def run_reset_time_aes_sampler_diagnostic(
    *,
    repaired_specs_path: Path | str = DEFAULT_REPAIRED_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    max_example_rows_per_spec: int = 8,
    next_blocker: str = "m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    repaired_specs = load_repaired_specs(repaired_specs_path)
    reset_rows = load_reset_rows(reset_rows_path)
    failed_ids = failed_aes_target_ids(reset_rows)
    specs_by_id = {str(row["v2_panel_spec_id"]): row for row in repaired_specs}

    target_rows: list[dict[str, Any]] = []
    attempt_summary_rows: list[dict[str, Any]] = []
    reject_reason_rows: list[dict[str, Any]] = []
    label_count_rows: list[dict[str, Any]] = []
    example_rows: list[dict[str, Any]] = []
    offline_density_rows: list[dict[str, Any]] = []

    for reset_row in reset_rows:
        spec_id = str(reset_row.get("v2_panel_spec_id", ""))
        if spec_id not in failed_ids:
            continue
        spec = specs_by_id[spec_id]
        env_config = dict(spec["env_config"])
        eval_seed = int(reset_row["eval_seed"])
        attempts = replay_reset_time_obstacle_attempts(env_config=env_config, seed=eval_seed)
        summary = summarize_attempts(attempts)
        source_id = str(spec.get("source_v1_bounded_panel_spec_id", ""))
        target_rows.append(
            {
                "v2_panel_spec_id": spec_id,
                "profile_name": spec.get("profile_name", ""),
                "source_v1_bounded_panel_spec_id": source_id,
                "source_scenario_spec_id": spec.get("source_scenario_spec_id", ""),
                "hidden_dynamics_bucket": spec.get("hidden_dynamics_bucket", ""),
                "repair_candidate": spec.get("source_sampler_repair_candidate", ""),
                "attempt_budget": build_env_config(env_config).obstacle.max_sample_attempts,
                "offline_density": spec.get("source_sampler_repair_density", ""),
                "reset_time_density": float(summary["accepted_count"]) / max(int(summary["attempt_count"]), 1),
                "dominant_reject_reason": summary["dominant_reject_reason"],
            }
        )
        attempt_summary_rows.append(
            {
                "v2_panel_spec_id": spec_id,
                "profile_name": spec.get("profile_name", ""),
                "source_v1_bounded_panel_spec_id": source_id,
                "attempt_count": summary["attempt_count"],
                "accepted_count": summary["accepted_count"],
                "dominant_reject_reason": summary["dominant_reject_reason"],
            }
        )
        offline_density_rows.append(
            {
                "v2_panel_spec_id": spec_id,
                "profile_name": spec.get("profile_name", ""),
                "source_v1_bounded_panel_spec_id": source_id,
                "repair_candidate": spec.get("source_sampler_repair_candidate", ""),
                "offline_density": spec.get("source_sampler_repair_density", ""),
                "env_config_obstacle": asdict(build_env_config(env_config).obstacle),
            }
        )
        for reason, count in summary["reject_reason_counts"].items():
            reject_reason_rows.append(
                {
                    "v2_panel_spec_id": spec_id,
                    "profile_name": spec.get("profile_name", ""),
                    "source_v1_bounded_panel_spec_id": source_id,
                    "reject_reason": reason,
                    "count": count,
                }
            )
        for label, count in summary["label_counts"].items():
            label_count_rows.append(
                {
                    "v2_panel_spec_id": spec_id,
                    "profile_name": spec.get("profile_name", ""),
                    "source_v1_bounded_panel_spec_id": source_id,
                    "label": label,
                    "count": count,
                }
            )
        for row in attempts[: max(0, int(max_example_rows_per_spec))]:
            example = dict(row)
            example["v2_panel_spec_id"] = spec_id
            example["profile_name"] = spec.get("profile_name", "")
            example["source_v1_bounded_panel_spec_id"] = source_id
            example_rows.append(example)

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    write_csv_rows(output / "aes_source_diagnostic_targets.csv", target_rows)
    write_csv_rows(output / "offline_density_rows.csv", offline_density_rows)
    write_csv_rows(output / "reset_time_attempt_summary.csv", attempt_summary_rows)
    write_csv_rows(output / "reset_time_reject_reason_counts.csv", reject_reason_rows)
    write_csv_rows(output / "reset_time_label_counts.csv", label_count_rows)
    write_csv_rows(output / "reset_time_candidate_examples.csv", example_rows)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())
    summary = {
        "result_class": "reset_time_aes_sampler_diagnostic_pass",
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repaired_specs_path": str(repaired_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "target_failed_aes_row_count": len(failed_ids),
        "diagnostic_target_row_count": len(target_rows),
        "source_count": len({str(row.get("source_v1_bounded_panel_spec_id", "")) for row in target_rows}),
        "reject_reason_counts": _count_by_key(reject_reason_rows, "reject_reason"),
        "label_counts": _count_by_key(label_count_rows, "label"),
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
            "aes_source_diagnostic_targets": str(output / "aes_source_diagnostic_targets.csv"),
            "offline_density_rows": str(output / "offline_density_rows.csv"),
            "reset_time_attempt_summary": str(output / "reset_time_attempt_summary.csv"),
            "reset_time_reject_reason_counts": str(output / "reset_time_reject_reason_counts.csv"),
            "reset_time_label_counts": str(output / "reset_time_label_counts.csv"),
            "reset_time_candidate_examples": str(output / "reset_time_candidate_examples.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repaired-specs", default=str(DEFAULT_REPAIRED_SPECS))
    parser.add_argument("--reset-rows", default=str(DEFAULT_RESET_ROWS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-example-rows-per-spec", type=int, default=8)
    parser.add_argument(
        "--next-blocker",
        default="m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit",
    )
    args = parser.parse_args()
    summary = run_reset_time_aes_sampler_diagnostic(
        repaired_specs_path=args.repaired_specs,
        reset_rows_path=args.reset_rows,
        output_dir=args.output_dir,
        max_example_rows_per_spec=args.max_example_rows_per_spec,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"target_failed_aes_row_count={summary['target_failed_aes_row_count']}")
    print(f"source_count={summary['source_count']}")


if __name__ == "__main__":
    main()
