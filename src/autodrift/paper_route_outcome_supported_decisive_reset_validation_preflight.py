"""Focused reset-only validator for outcome-supported decisive task specs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.executable_v2_task_quality_reset_validation_preflight import reset_task_quality_spec
from autodrift.paper_route_outcome_supported_decisive_task_candidates import (
    DIFFICULTY_AXES,
    FAMILY_TARGETS,
    SPLIT_TARGETS,
)


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight")
DEFAULT_EVAL_SEED_BASE = 206600
TARGET_EXECUTABLE_SPEC_COUNT = sum(FAMILY_TARGETS.values())
EXPECTED_OBSERVATION_DIM = 72

METADATA_FIELDS = [
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
]
REQUIRED_METADATA_FIELDS = [
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
]
CONTRACT_FIELDNAMES = [
    *METADATA_FIELDS,
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "materialization_semantics_smoke_proxy",
    "paper_validity_claim_false",
    "generated_source_row_proxy_semantics",
    "profile_specific_tuning_false",
    "controller_family_ranking_claim_false",
    "finite_window_vs_gru_conclusion_claim_false",
    "paper_level_claim_false",
    "level3_self_id_claim_false",
    "contract_violation_count",
]
RESET_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "reset_success",
    "error_type",
    "error_message",
    "observation_length",
    "expected_observation_length",
    "observation_dimension_matches",
    "observation_finite",
    "obstacle_initialized",
    "reset_sampled_obstacle_label",
    "initial_mu",
    "speed_ref",
    "obstacle_distance",
    "obstacle_half_width",
    "contract_violation_count",
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
]
METADATA_MISSING_FIELDNAMES = [
    "task_source_id",
    "candidate_id",
    "panel_task_family",
    "source_kind",
    "missing_metadata_fields",
]
AGGREGATE_FIELDNAMES = ["key", "reset_count"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
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


def _string_bool(value: Any) -> str:
    return "true" if _bool(value) else "false"


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _count_by_key_func(rows: Iterable[Mapping[str, Any]], key_func: Callable[[Mapping[str, Any]], str]) -> dict[str, int]:
    return dict(sorted(Counter(str(key_func(row)) for row in rows).items()))


def _aggregate_rows(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    return [{"key": key, "reset_count": int(value)} for key, value in sorted(counts.items())]


def _axis_key(row: Mapping[str, Any]) -> str:
    return "|".join(str(row.get(axis, "")) for axis in DIFFICULTY_AXES)


def _difficulty_axis_coverage_registered(rows: Iterable[Mapping[str, Any]]) -> bool:
    all_rows = list(rows)
    for family in FAMILY_TARGETS:
        family_rows = [row for row in all_rows if str(row.get("panel_task_family", "")) == family]
        for axis, expected_values in DIFFICULTY_AXES.items():
            if {str(row.get(axis, "")) for row in family_rows} != set(expected_values):
                return False
    return True


def _registered_quota_matches(counts: Mapping[str, int], targets: Mapping[str, int]) -> bool:
    for key, target in targets.items():
        if int(counts.get(key, 0)) != int(target):
            return False
    return not any(key not in targets and int(value) != 0 for key, value in counts.items())


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def metadata_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    metadata = {field: spec.get(field, "") for field in METADATA_FIELDS}
    metadata["same_current_constraint"] = _string_bool(metadata["same_current_constraint"])
    metadata["history_intervention_candidate"] = _string_bool(metadata["history_intervention_candidate"])
    metadata["generated_source_row"] = _string_bool(metadata["generated_source_row"])
    metadata["paper_validity_claim"] = _string_bool(metadata["paper_validity_claim"])
    return metadata


def contract_row_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    generated = _bool(spec.get("generated_source_row"))
    materialization_semantics = str(spec.get("materialization_semantics", ""))
    checks = {
        "history_length_is_positive": int(env_config.get("history_length", 0)) >= 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
        "materialization_semantics_smoke_proxy": materialization_semantics == "smoke_proxy",
        "paper_validity_claim_false": not _bool(spec.get("paper_validity_claim")),
        "generated_source_row_proxy_semantics": (not generated) or materialization_semantics == "smoke_proxy",
        "profile_specific_tuning_false": not _bool(spec.get("profile_specific_tuning")),
        "controller_family_ranking_claim_false": not _bool(spec.get("controller_family_ranking_claim_made")),
        "finite_window_vs_gru_conclusion_claim_false": not _bool(spec.get("finite_window_vs_gru_conclusion_made")),
        "paper_level_claim_false": not _bool(spec.get("paper_level_claim_made")),
        "level3_self_id_claim_false": not _bool(spec.get("level3_self_id_claim_made")),
    }
    return {
        **metadata_for_spec(spec),
        **checks,
        "contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def metadata_missing_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        missing = [field for field in REQUIRED_METADATA_FIELDS if str(spec.get(field, "")).strip() == ""]
        if missing:
            metadata = metadata_for_spec(spec)
            rows.append(
                {
                    "task_source_id": metadata["task_source_id"],
                    "candidate_id": metadata["candidate_id"],
                    "panel_task_family": metadata["panel_task_family"],
                    "source_kind": metadata["source_kind"],
                    "missing_metadata_fields": ";".join(missing),
                }
            )
    return rows


def reset_focused_spec(
    *,
    spec: Mapping[str, Any],
    eval_seed: int,
    expected_observation_dim: int | None,
) -> dict[str, Any]:
    low_level = reset_task_quality_spec(
        spec=spec,
        eval_seed=int(eval_seed),
        expected_observation_dim=expected_observation_dim,
    )
    metadata = metadata_for_spec(spec)
    contract = contract_row_for_spec(spec)
    return {
        **metadata,
        "eval_seed": int(eval_seed),
        "reset_success": bool(low_level.get("reset_success")),
        "error_type": str(low_level.get("error_type", "")),
        "error_message": str(low_level.get("error_message", "")),
        "observation_length": low_level.get("observation_length", ""),
        "expected_observation_length": low_level.get("expected_observation_length", ""),
        "observation_dimension_matches": bool(low_level.get("observation_dimension_matches")),
        "observation_finite": bool(low_level.get("observation_finite")),
        "obstacle_initialized": bool(low_level.get("obstacle_initialized")),
        "reset_sampled_obstacle_label": str(low_level.get("sampled_obstacle_label", "")),
        "initial_mu": low_level.get("initial_mu", ""),
        "speed_ref": low_level.get("speed_ref", ""),
        "obstacle_distance": low_level.get("obstacle_distance", ""),
        "obstacle_half_width": low_level.get("obstacle_half_width", ""),
        "contract_violation_count": int(contract["contract_violation_count"]),
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
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "outcome_supported_decisive_reset_validity",
            "admissible": bool(passes),
            "reason": "reset validity is admissible only if all reset gates pass",
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
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated rows remain smoke proxies until later task-semantics validation",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "reset validation does not compare controller-family outcomes",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "reset validation does not test history necessity or wrong-history interventions",
        },
    ]


def run_outcome_supported_decisive_reset_validation_preflight(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    next_blocker: str = "m2067-paper-route-outcome-supported-decisive-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    reset_rows = [
        reset_focused_spec(
            spec=spec,
            eval_seed=int(eval_seed_base) + index,
            expected_observation_dim=expected_observation_dim,
        )
        for index, spec in enumerate(specs)
    ]
    contract_rows = [contract_row_for_spec(spec) for spec in specs]
    failure_rows = [dict(row) for row in reset_rows if not _bool(row.get("reset_success"))]
    missing_rows = metadata_missing_rows(specs)
    forbidden_key_hits = forbidden_key_violations(specs)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    target_count_matches = target_spec_count is None or len(specs) == int(target_spec_count)
    target_is_registered_full_panel = int(target_spec_count or 0) == TARGET_EXECUTABLE_SPEC_COUNT
    reset_success_count = sum(_bool(row.get("reset_success")) for row in reset_rows)
    observation_finite_count = sum(_bool(row.get("observation_finite")) for row in reset_rows)
    obstacle_initialized_count = sum(_bool(row.get("obstacle_initialized")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool(row.get("reset_success")) and not _bool(row.get("observation_dimension_matches"))
        for row in reset_rows
    )
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    expected_family_counts = _count_by(specs, "panel_task_family")
    family_counts = _count_by(reset_rows, "panel_task_family")
    expected_split_counts = _count_by(specs, "source_split")
    split_counts = _count_by(reset_rows, "source_split")
    expected_dynamics_counts = _count_by(specs, "dynamics_band")
    dynamics_counts = _count_by(reset_rows, "dynamics_band")
    expected_source_kind_counts = _count_by(specs, "source_kind")
    source_kind_counts = _count_by(reset_rows, "source_kind")
    expected_axis_counts = _count_by_key_func(specs, _axis_key)
    axis_counts = _count_by_key_func(reset_rows, _axis_key)
    family_quota_pass = family_counts == expected_family_counts
    split_quota_pass = split_counts == expected_split_counts
    dynamics_quota_pass = dynamics_counts == expected_dynamics_counts
    source_kind_quota_pass = source_kind_counts == expected_source_kind_counts
    difficulty_axis_coverage_pass = axis_counts == expected_axis_counts
    registered_family_quota_pass = (not target_is_registered_full_panel) or _registered_quota_matches(
        family_counts,
        FAMILY_TARGETS,
    )
    registered_split_quota_pass = (not target_is_registered_full_panel) or _registered_quota_matches(
        split_counts,
        SPLIT_TARGETS,
    )
    registered_difficulty_axis_coverage_pass = (not target_is_registered_full_panel) or _difficulty_axis_coverage_registered(reset_rows)

    passes = (
        target_count_matches
        and len(reset_rows) == len(specs)
        and reset_success_count == len(specs)
        and not failure_rows
        and observation_finite_count == len(specs)
        and observation_dimension_failure_count == 0
        and obstacle_initialized_count == len(specs)
        and contract_violation_count == 0
        and not missing_rows
        and not forbidden_key_hits
        and family_quota_pass
        and split_quota_pass
        and dynamics_quota_pass
        and source_kind_quota_pass
        and difficulty_axis_coverage_pass
        and registered_family_quota_pass
        and registered_split_quota_pass
        and registered_difficulty_axis_coverage_pass
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", failure_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output / "reset_distribution_by_family.csv", _aggregate_rows(family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "reset_distribution_by_split.csv", _aggregate_rows(split_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "reset_distribution_by_dynamics_band.csv", _aggregate_rows(dynamics_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "reset_distribution_by_source_kind.csv", _aggregate_rows(source_kind_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(passes), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "outcome_supported_decisive_reset_validation_preflight_pass"
            if passes
            else "outcome_supported_decisive_reset_validation_preflight_fail"
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
        "metadata_missing_count": len(missing_rows),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "expected_family_counts": expected_family_counts,
        "family_counts": family_counts,
        "family_quota_pass": family_quota_pass,
        "registered_family_quota_pass": registered_family_quota_pass,
        "expected_split_counts": expected_split_counts,
        "split_counts": split_counts,
        "split_quota_pass": split_quota_pass,
        "registered_split_quota_pass": registered_split_quota_pass,
        "expected_dynamics_counts": expected_dynamics_counts,
        "dynamics_counts": dynamics_counts,
        "dynamics_quota_pass": dynamics_quota_pass,
        "expected_source_kind_counts": expected_source_kind_counts,
        "source_kind_counts": source_kind_counts,
        "source_kind_quota_pass": source_kind_quota_pass,
        "expected_axis_counts": expected_axis_counts,
        "axis_counts": axis_counts,
        "difficulty_axis_coverage_pass": difficulty_axis_coverage_pass,
        "registered_difficulty_axis_coverage_pass": registered_difficulty_axis_coverage_pass,
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
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "reset_rows": str(output / "reset_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "contract_rows": str(output / "contract_rows.csv"),
            "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
            "reset_distribution_by_family": str(output / "reset_distribution_by_family.csv"),
            "reset_distribution_by_split": str(output / "reset_distribution_by_split.csv"),
            "reset_distribution_by_dynamics_band": str(output / "reset_distribution_by_dynamics_band.csv"),
            "reset_distribution_by_source_kind": str(output / "reset_distribution_by_source_kind.csv"),
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
    parser.add_argument("--next-blocker", default="m2067-paper-route-outcome-supported-decisive-reset-validation-result-audit")
    args = parser.parse_args()
    summary = run_outcome_supported_decisive_reset_validation_preflight(
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
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
