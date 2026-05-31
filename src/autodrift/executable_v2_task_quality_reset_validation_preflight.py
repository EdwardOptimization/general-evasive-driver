"""Reset-only validator for task-quality executable v2 task specs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
)
from autodrift.env import AutoDriftEnv, DriftEnvConfig


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1933_executable_v2_task_quality_reset_validation_preflight")
DEFAULT_EVAL_SEED_BASE = 193300
TARGET_EXECUTABLE_SPEC_COUNT = 80
EXPECTED_OBSERVATION_DIM = 72
FORBIDDEN_GUARDRAILS = (
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
CONTRACT_ROW_FIELDNAMES = [
    "task_source_id",
    "candidate_source_id",
    "feasibility_tier_id",
    "source_role_semantics",
    "surface_variant",
    "history_length_is_one",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "labels_enter_actor_input_false",
    "paper_holdout_candidate_false",
    "contract_violation_count",
]


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


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _aggregate_count_rows(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, ...], int] = {}
    for row in rows:
        aggregate_key = tuple(str(row.get(key, "")) for key in keys)
        counts[aggregate_key] = counts.get(aggregate_key, 0) + 1
    output: list[dict[str, Any]] = []
    for aggregate_key, count in sorted(counts.items()):
        item = {keys[index]: aggregate_key[index] for index in range(len(keys))}
        item["reset_count"] = count
        output.append(item)
    return output


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def contract_row_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    checks = {
        "history_length_is_one": int(env_config.get("history_length", 0)) == 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
        "labels_enter_actor_input_false": not _bool(spec.get("labels_enter_actor_input")),
        "paper_holdout_candidate_false": not _bool(spec.get("paper_holdout_candidate")),
    }
    return {
        "task_source_id": str(spec.get("task_source_id", "")),
        "candidate_source_id": str(spec.get("candidate_source_id", "")),
        "feasibility_tier_id": str(spec.get("feasibility_tier_id", "")),
        "source_role_semantics": str(spec.get("source_role_semantics", "")),
        "surface_variant": str(spec.get("surface_variant", "")),
        **checks,
        "contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def _observation_length(env: AutoDriftEnv, obs: Any) -> int:
    array = np.asarray(obs, dtype=np.float64)
    if array.ndim == 0:
        return 0
    return int(array.size)


def _observation_space_dim(env: AutoDriftEnv) -> int | None:
    shape = getattr(getattr(env, "observation_space", None), "shape", None)
    if not shape:
        return None
    return int(np.prod(shape))


def _finite_observation(obs: Any) -> bool:
    try:
        array = np.asarray(obs, dtype=np.float64)
    except (TypeError, ValueError):
        return False
    return bool(array.size > 0 and np.all(np.isfinite(array)))


def _obstacle_initialized(info: Mapping[str, Any], env: AutoDriftEnv) -> bool:
    if "obstacle_label" in info:
        return bool(str(info.get("obstacle_label", "")))
    return bool(getattr(env, "obstacle_scenario", None) is not None)


def reset_task_quality_spec(
    *,
    spec: Mapping[str, Any],
    eval_seed: int,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
) -> dict[str, Any]:
    contract = contract_row_for_spec(spec)
    base = {
        "task_source_id": str(spec.get("task_source_id", "")),
        "candidate_source_id": str(spec.get("candidate_source_id", "")),
        "source_v1_bounded_panel_spec_id": str(spec.get("source_v1_bounded_panel_spec_id", "")),
        "source_scenario_spec_id": str(spec.get("source_scenario_spec_id", "")),
        "feasibility_tier_id": str(spec.get("feasibility_tier_id", "")),
        "source_role_semantics": str(spec.get("source_role_semantics", "")),
        "source_split": str(spec.get("source_split", "")),
        "surface_variant": str(spec.get("surface_variant", "")),
        "selected_accepted_cell_rule": str(spec.get("selected_accepted_cell_rule", "")),
        "label": str(spec.get("label", "")),
        "eval_seed": int(eval_seed),
        "environment_reset_started": True,
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
        "contract_violation_count": int(contract["contract_violation_count"]),
    }
    env: AutoDriftEnv | None = None
    try:
        config: DriftEnvConfig = build_env_config(dict(spec.get("env_config") or {}))
        env = AutoDriftEnv(config)
        obs, info = env.reset(seed=int(eval_seed))
        obs_len = _observation_length(env, obs)
        space_dim = _observation_space_dim(env)
        expected_dim = int(expected_observation_dim if expected_observation_dim is not None else space_dim or obs_len)
        observation_dimension_matches = obs_len == expected_dim
        base.update(
            {
                "reset_success": True,
                "error_type": "",
                "error_message": "",
                "observation_length": obs_len,
                "expected_observation_length": expected_dim,
                "observation_dimension_matches": bool(observation_dimension_matches),
                "observation_finite": _finite_observation(obs),
                "obstacle_initialized": _obstacle_initialized(info, env),
                "sampled_obstacle_label": str(info.get("obstacle_label", "")),
                "initial_mu": float(info.get("initial_mu", float("nan"))),
                "speed_ref": float(info.get("speed_ref", float("nan"))),
                "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
                "obstacle_half_width": float(info.get("active_obstacle_half_width", float("nan"))),
            }
        )
    except Exception as exc:  # noqa: BLE001 - reset validation must preserve failures.
        base.update(
            {
                "reset_success": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "observation_length": "",
                "expected_observation_length": expected_observation_dim if expected_observation_dim is not None else "",
                "observation_dimension_matches": False,
                "observation_finite": False,
                "obstacle_initialized": False,
                "sampled_obstacle_label": "",
                "initial_mu": "",
                "speed_ref": "",
                "obstacle_distance": "",
                "obstacle_half_width": "",
            }
        )
    finally:
        if env is not None:
            env.close()
    return base


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "task_quality_reset_validator_available",
            "admissible": True,
            "reason": "helper can consume executable_task_specs and run reset-only validation when executed",
        },
        {
            "claim": "reset_feasibility",
            "admissible": False,
            "reason": "M1931 implementation tests do not run the real M1928 reset workload",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and measured rollout remain blocked until reset validation passes",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "reset validation is a scenario admissibility gate, not a controller comparison",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "reset validation does not test history necessity or wrong-history interventions",
        },
    ]


def run_task_quality_reset_validation_preflight(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    next_blocker: str = "m1934-executable-v2-task-quality-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    reset_rows = [
        reset_task_quality_spec(
            spec=spec,
            eval_seed=int(eval_seed_base) + index,
            expected_observation_dim=expected_observation_dim,
        )
        for index, spec in enumerate(specs)
    ]
    contract_rows = [contract_row_for_spec(spec) for spec in specs]
    failure_rows = [dict(row) for row in reset_rows if not _bool(row.get("reset_success"))]
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    forbidden_key_hits = forbidden_key_violations(specs)
    target_count_matches = target_spec_count is None or len(specs) == int(target_spec_count)
    reset_success_count = sum(_bool(row.get("reset_success")) for row in reset_rows)
    observation_finite_count = sum(_bool(row.get("observation_finite")) for row in reset_rows)
    obstacle_initialized_count = sum(_bool(row.get("obstacle_initialized")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool(row.get("reset_success")) and not _bool(row.get("observation_dimension_matches"))
        for row in reset_rows
    )
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    label_actor_input_violation_count = sum(
        not _bool(row.get("labels_enter_actor_input_false"), default=True) for row in contract_rows
    )
    private_holdout_count = sum(
        not _bool(row.get("paper_holdout_candidate_false"), default=True) for row in contract_rows
    )
    passes = (
        target_count_matches
        and len(reset_rows) == len(specs)
        and reset_success_count == len(specs)
        and not failure_rows
        and observation_finite_count == len(specs)
        and observation_dimension_failure_count == 0
        and obstacle_initialized_count == len(specs)
        and contract_violation_count == 0
        and label_actor_input_violation_count == 0
        and private_holdout_count == 0
        and not forbidden_key_hits
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_rows.csv", reset_rows)
    write_csv_rows(
        output / "reset_failure_rows.csv",
        failure_rows,
        fieldnames=list(reset_rows[0].keys()) if reset_rows else None,
    )
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_ROW_FIELDNAMES)
    write_csv_rows(output / "reset_distribution_by_tier.csv", _aggregate_count_rows(reset_rows, ("feasibility_tier_id",)))
    write_csv_rows(
        output / "reset_distribution_by_role.csv",
        _aggregate_count_rows(reset_rows, ("source_role_semantics",)),
    )
    write_csv_rows(output / "reset_distribution_by_surface.csv", _aggregate_count_rows(reset_rows, ("surface_variant",)))
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "task_quality_reset_validation_preflight_pass"
            if passes
            else "task_quality_reset_validation_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_task_specs_path": str(executable_task_specs_path),
        "input_executable_spec_count": len(specs),
        "target_executable_spec_count": target_spec_count,
        "reset_attempt_count": len(reset_rows),
        "reset_success_count": int(reset_success_count),
        "reset_failure_count": len(failure_rows),
        "observation_finite_count": int(observation_finite_count),
        "observation_dimension_failure_count": int(observation_dimension_failure_count),
        "obstacle_initialized_count": int(obstacle_initialized_count),
        "contract_violation_count": int(contract_violation_count),
        "label_actor_input_violation_count": int(label_actor_input_violation_count),
        "private_holdout_count": int(private_holdout_count),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "tier_counts": _count_by(reset_rows, "feasibility_tier_id"),
        "role_counts": _count_by(reset_rows, "source_role_semantics"),
        "surface_counts": _count_by(reset_rows, "surface_variant"),
        "sampled_label_counts": _count_by(reset_rows, "sampled_obstacle_label"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": True,
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
        "passes_public_smoke_gates": bool(passes),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "reset_rows": str(output / "reset_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "contract_rows": str(output / "contract_rows.csv"),
            "reset_distribution_by_tier": str(output / "reset_distribution_by_tier.csv"),
            "reset_distribution_by_role": str(output / "reset_distribution_by_role.csv"),
            "reset_distribution_by_surface": str(output / "reset_distribution_by_surface.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_EXECUTABLE_SPEC_COUNT)
    parser.add_argument("--expected-observation-dim", type=int, default=EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--next-blocker", default="m1934-executable-v2-task-quality-reset-validation-result-audit")
    args = parser.parse_args()
    summary = run_task_quality_reset_validation_preflight(
        executable_task_specs_path=args.executable_task_specs,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_spec_count=int(args.target_spec_count),
        expected_observation_dim=int(args.expected_observation_dim),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"reset_attempt_count={summary['reset_attempt_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"reset_failure_count={summary['reset_failure_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
