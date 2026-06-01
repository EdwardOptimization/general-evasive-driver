"""Reset-only validator for the current-sim scenario task-family config pack."""

from __future__ import annotations

import argparse
from collections import Counter
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig


DEFAULT_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation")
DEFAULT_EVAL_SEED_BASE = 228300
TARGET_SCENARIO_SPEC_COUNT = 72
EXPECTED_OBSERVATION_DIM = 72
LATERAL_OFFSET_TOLERANCE_M = 0.05
LATERAL_BUCKET_THRESHOLD_M = 0.5
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
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
)
CONTRACT_ROW_FIELDNAMES = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "history_length_is_one",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "labels_enter_actor_input_false",
    "ranking_admissible_false",
    "paper_level_claim_made_false",
    "level3_self_id_claim_made_false",
    "actor_contract_violation_count",
]
LABEL_ROW_FIELDNAMES = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "allowed_labels_metadata_only",
    "expected_sampled_obstacle_label",
    "actual_obstacle_label",
    "allowed_label_count",
    "label_allowed",
    "single_label_exact_match",
    "labels_enter_actor_input",
]
LATERAL_ROW_FIELDNAMES = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "obstacle_lateral_offset_bucket",
    "expected_obstacle_lateral_offset_m",
    "actual_obstacle_lateral_offset_m",
    "numeric_offset_matches",
    "bucket_matches_signed_convention",
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


def _float_or_nan(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite(value: float) -> bool:
    return math.isfinite(float(value))


def _split_allowed_labels(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = [item.strip() for item in value.split(";")]
    elif isinstance(value, (list, tuple)):
        parts = [str(item).strip() for item in value]
    else:
        parts = []
    return [item for item in parts if item]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _aggregate_count_rows(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        counts[tuple(str(row.get(key, "")) for key in keys)] += 1
    output: list[dict[str, Any]] = []
    for values, count in sorted(counts.items()):
        item = {key: value for key, value in zip(keys, values)}
        item["reset_count"] = int(count)
        output.append(item)
    return output


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def load_scenario_specs(config_path: Path | str = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    payload = read_json(config_path)
    rows = payload.get("scenario_specs")
    if not isinstance(rows, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("scenario_spec_id", "")))


def contract_row_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    checks = {
        "history_length_is_one": int(env_config.get("history_length", 0)) == 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
        "labels_enter_actor_input_false": not _bool(spec.get("labels_enter_actor_input")),
        "ranking_admissible_false": not _bool(spec.get("ranking_admissible")),
        "paper_level_claim_made_false": not _bool(spec.get("paper_level_claim_made")),
        "level3_self_id_claim_made_false": not _bool(spec.get("level3_self_id_claim_made")),
    }
    return {
        "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
        "scenario_family_id": str(spec.get("scenario_family_id", "")),
        "role_family": str(spec.get("role_family", "")),
        **checks,
        "actor_contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def _observation_length(obs: Any) -> int:
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


def label_consistency_row(spec: Mapping[str, Any], actual_label: str) -> dict[str, Any]:
    allowed_labels = _split_allowed_labels(spec.get("allowed_labels_metadata_only"))
    expected = str(spec.get("sampled_obstacle_label", ""))
    label_allowed = bool(actual_label and actual_label in allowed_labels)
    single_label_exact_match = bool(len(allowed_labels) != 1 or actual_label == expected)
    return {
        "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
        "scenario_family_id": str(spec.get("scenario_family_id", "")),
        "role_family": str(spec.get("role_family", "")),
        "allowed_labels_metadata_only": ";".join(allowed_labels),
        "expected_sampled_obstacle_label": expected,
        "actual_obstacle_label": actual_label,
        "allowed_label_count": int(len(allowed_labels)),
        "label_allowed": label_allowed,
        "single_label_exact_match": single_label_exact_match,
        "labels_enter_actor_input": bool(spec.get("labels_enter_actor_input", False)),
    }


def _bucket_matches_signed_convention(bucket: str, actual_offset: float) -> bool:
    if not _finite(actual_offset):
        return False
    if bucket == "centerline":
        return abs(actual_offset) <= LATERAL_OFFSET_TOLERANCE_M
    if bucket == "left_offset":
        return actual_offset >= LATERAL_BUCKET_THRESHOLD_M
    if bucket == "right_offset":
        return actual_offset <= -LATERAL_BUCKET_THRESHOLD_M
    return False


def lateral_consistency_row(spec: Mapping[str, Any], actual_offset: float) -> dict[str, Any]:
    expected = _float_or_nan(spec.get("obstacle_lateral_offset_m"))
    bucket = str(spec.get("obstacle_lateral_offset_bucket", ""))
    numeric_matches = bool(
        _finite(expected)
        and _finite(actual_offset)
        and abs(float(actual_offset) - float(expected)) <= LATERAL_OFFSET_TOLERANCE_M
    )
    return {
        "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
        "scenario_family_id": str(spec.get("scenario_family_id", "")),
        "role_family": str(spec.get("role_family", "")),
        "obstacle_lateral_offset_bucket": bucket,
        "expected_obstacle_lateral_offset_m": expected,
        "actual_obstacle_lateral_offset_m": actual_offset,
        "numeric_offset_matches": numeric_matches,
        "bucket_matches_signed_convention": _bucket_matches_signed_convention(bucket, actual_offset),
    }


def reset_scenario_spec(
    *,
    spec: Mapping[str, Any],
    eval_seed: int,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = contract_row_for_spec(spec)
    base = {
        "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
        "scenario_family_id": str(spec.get("scenario_family_id", "")),
        "role_family": str(spec.get("role_family", "")),
        "role_semantics": str(spec.get("role_semantics", "")),
        "same_scene_group_id": str(spec.get("same_scene_group_id", "")),
        "sampled_obstacle_label": str(spec.get("sampled_obstacle_label", "")),
        "allowed_labels_metadata_only": str(spec.get("allowed_labels_metadata_only", "")),
        "hidden_dynamics_bucket": str(spec.get("hidden_dynamics_bucket", "")),
        "obstacle_longitudinal_timing_bucket": str(spec.get("obstacle_longitudinal_timing_bucket", "")),
        "obstacle_lateral_offset_m": _float_or_nan(spec.get("obstacle_lateral_offset_m")),
        "obstacle_lateral_offset_bucket": str(spec.get("obstacle_lateral_offset_bucket", "")),
        "initial_speed_mps": _float_or_nan(spec.get("initial_speed_mps")),
        "track_kind": str(spec.get("track_kind", "")),
        "track_radius_m": _float_or_nan(spec.get("track_radius_m")),
        "track_width_m": _float_or_nan(spec.get("track_width_m")),
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
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "actor_contract_violation_count": int(contract["actor_contract_violation_count"]),
    }
    env: AutoDriftEnv | None = None
    actual_label = ""
    actual_offset = float("nan")
    try:
        config: DriftEnvConfig = build_env_config(dict(spec.get("env_config") or {}))
        env = AutoDriftEnv(config)
        obs, info = env.reset(seed=int(eval_seed))
        obs_len = _observation_length(obs)
        space_dim = _observation_space_dim(env)
        expected_dim = int(expected_observation_dim if expected_observation_dim is not None else space_dim or obs_len)
        actual_label = str(info.get("obstacle_label", ""))
        actual_offset = _float_or_nan(info.get("obstacle_lateral_offset"))
        base.update(
            {
                "reset_success": True,
                "error_type": "",
                "error_message": "",
                "observation_length": obs_len,
                "expected_observation_length": expected_dim,
                "observation_dimension_matches": bool(obs_len == expected_dim),
                "observation_finite": _finite_observation(obs),
                "obstacle_initialized": _obstacle_initialized(info, env),
                "actual_obstacle_label": actual_label,
                "actual_obstacle_distance": _float_or_nan(info.get("obstacle_distance")),
                "actual_obstacle_half_width": _float_or_nan(info.get("active_obstacle_half_width")),
                "actual_obstacle_lateral_offset": actual_offset,
                "initial_mu": _float_or_nan(info.get("initial_mu")),
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
                "actual_obstacle_label": "",
                "actual_obstacle_distance": "",
                "actual_obstacle_half_width": "",
                "actual_obstacle_lateral_offset": "",
                "initial_mu": "",
            }
        )
    finally:
        if env is not None:
            env.close()
    label_row = label_consistency_row(spec, actual_label)
    lateral_row = lateral_consistency_row(spec, actual_offset)
    return base, contract, label_row, lateral_row


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "scenario_task_family_reset_validation",
            "admissible": True,
            "reason": "M2284 may claim only reset-validity if all reset gates pass",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and measured rollout remain blocked until reset validation is audited",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "reset validation is a scenario admissibility gate, not a controller comparison",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "no controller-family comparison is run",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "reset validation does not test history necessity or wrong-history interventions",
        },
    ]


def run_scenario_task_family_reset_validation(
    *,
    config_path: Path | str = DEFAULT_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_SCENARIO_SPEC_COUNT,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    next_blocker: str = "m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_scenario_specs(config_path)
    reset_rows: list[dict[str, Any]] = []
    contract_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    lateral_rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        reset_row, contract_row, label_row, lateral_row = reset_scenario_spec(
            spec=spec,
            eval_seed=int(eval_seed_base) + index,
            expected_observation_dim=expected_observation_dim,
        )
        reset_rows.append(reset_row)
        contract_rows.append(contract_row)
        label_rows.append(label_row)
        lateral_rows.append(lateral_row)

    failure_rows = [dict(row) for row in reset_rows if not _bool(row.get("reset_success"))]
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_count_matches = target_spec_count is None or len(specs) == int(target_spec_count)
    reset_success_count = sum(_bool(row.get("reset_success")) for row in reset_rows)
    observation_finite_count = sum(_bool(row.get("observation_finite")) for row in reset_rows)
    obstacle_initialized_count = sum(_bool(row.get("obstacle_initialized")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool(row.get("reset_success")) and not _bool(row.get("observation_dimension_matches"))
        for row in reset_rows
    )
    actor_contract_violation_count = sum(int(row.get("actor_contract_violation_count", 0)) for row in contract_rows)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in label_rows)
    ranking_admissible_count = sum(_bool(spec.get("ranking_admissible")) for spec in specs)
    label_not_allowed_count = sum(not _bool(row.get("label_allowed")) for row in label_rows)
    single_label_exact_mismatch_count = sum(
        not _bool(row.get("single_label_exact_match")) for row in label_rows
    )
    lateral_offset_numeric_mismatch_count = sum(
        not _bool(row.get("numeric_offset_matches")) for row in lateral_rows
    )
    lateral_bucket_mismatch_count = sum(
        not _bool(row.get("bucket_matches_signed_convention")) for row in lateral_rows
    )
    passes = (
        target_count_matches
        and len(reset_rows) == len(specs)
        and reset_success_count == len(specs)
        and not failure_rows
        and observation_finite_count == len(specs)
        and observation_dimension_failure_count == 0
        and obstacle_initialized_count == len(specs)
        and actor_contract_violation_count == 0
        and labels_enter_actor_input_count == 0
        and ranking_admissible_count == 0
        and label_not_allowed_count == 0
        and single_label_exact_mismatch_count == 0
        and lateral_offset_numeric_mismatch_count == 0
        and lateral_bucket_mismatch_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_validation_rows.csv", reset_rows)
    write_csv_rows(
        output / "reset_failures.csv",
        failure_rows,
        fieldnames=list(reset_rows[0].keys()) if reset_rows else None,
    )
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_ROW_FIELDNAMES)
    write_csv_rows(output / "label_consistency_rows.csv", label_rows, fieldnames=LABEL_ROW_FIELDNAMES)
    write_csv_rows(output / "lateral_offset_consistency_rows.csv", lateral_rows, fieldnames=LATERAL_ROW_FIELDNAMES)
    write_csv_rows(output / "role_family_reset_aggregate.csv", _aggregate_count_rows(reset_rows, ("role_family",)))
    write_csv_rows(
        output / "scenario_family_reset_aggregate.csv",
        _aggregate_count_rows(reset_rows, ("scenario_family_id",)),
    )
    write_csv_rows(
        output / "obstacle_lateral_offset_bucket_reset_aggregate.csv",
        _aggregate_count_rows(reset_rows, ("obstacle_lateral_offset_bucket",)),
    )
    write_csv_rows(
        output / "hidden_dynamics_bucket_reset_aggregate.csv",
        _aggregate_count_rows(reset_rows, ("hidden_dynamics_bucket",)),
    )
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "current_sim_scenario_task_family_reset_validation_pass"
            if passes
            else "current_sim_scenario_task_family_reset_validation_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "config_path": str(config_path),
        "input_scenario_spec_count": len(specs),
        "target_scenario_spec_count": target_spec_count,
        "target_count_matches": bool(target_count_matches),
        "reset_attempt_count": len(reset_rows),
        "reset_success_count": int(reset_success_count),
        "reset_failure_count": len(failure_rows),
        "observation_finite_count": int(observation_finite_count),
        "observation_dimension_failure_count": int(observation_dimension_failure_count),
        "obstacle_initialized_count": int(obstacle_initialized_count),
        "actor_contract_violation_count": int(actor_contract_violation_count),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_count": int(ranking_admissible_count),
        "label_not_allowed_count": int(label_not_allowed_count),
        "single_label_exact_mismatch_count": int(single_label_exact_mismatch_count),
        "lateral_offset_numeric_mismatch_count": int(lateral_offset_numeric_mismatch_count),
        "lateral_bucket_mismatch_count": int(lateral_bucket_mismatch_count),
        "role_family_counts": _count_by(reset_rows, "role_family"),
        "scenario_family_counts": _count_by(reset_rows, "scenario_family_id"),
        "obstacle_lateral_offset_bucket_counts": _count_by(reset_rows, "obstacle_lateral_offset_bucket"),
        "hidden_dynamics_bucket_counts": _count_by(reset_rows, "hidden_dynamics_bucket"),
        "actual_obstacle_label_counts": _count_by(reset_rows, "actual_obstacle_label"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": bool(reset_rows),
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
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "passes_public_reset_validation_gates": bool(passes),
        "primary_route": (
            "scenario_task_family_reset_validation_route_to_result_audit"
            if passes
            else "scenario_task_family_reset_validation_failure_route_to_result_audit"
        ),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "reset_validation_rows": str(output / "reset_validation_rows.csv"),
            "reset_failures": str(output / "reset_failures.csv"),
            "contract_rows": str(output / "contract_rows.csv"),
            "label_consistency_rows": str(output / "label_consistency_rows.csv"),
            "lateral_offset_consistency_rows": str(output / "lateral_offset_consistency_rows.csv"),
            "role_family_reset_aggregate": str(output / "role_family_reset_aggregate.csv"),
            "scenario_family_reset_aggregate": str(output / "scenario_family_reset_aggregate.csv"),
            "obstacle_lateral_offset_bucket_reset_aggregate": str(
                output / "obstacle_lateral_offset_bucket_reset_aggregate.csv"
            ),
            "hidden_dynamics_bucket_reset_aggregate": str(output / "hidden_dynamics_bucket_reset_aggregate.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_SCENARIO_SPEC_COUNT)
    parser.add_argument("--expected-observation-dim", type=int, default=EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--next-blocker", default="m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit")
    args = parser.parse_args()
    summary = run_scenario_task_family_reset_validation(
        config_path=args.config,
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
    print(f"actor_contract_violation_count={summary['actor_contract_violation_count']}")
    print(f"lateral_bucket_mismatch_count={summary['lateral_bucket_mismatch_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
