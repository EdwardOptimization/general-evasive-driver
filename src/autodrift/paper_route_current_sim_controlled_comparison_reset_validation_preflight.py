"""Reset-only validation for current-sim controlled-comparison executable specs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.executable_v2_task_quality_reset_validation_preflight import reset_task_quality_spec


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight")
DEFAULT_EVAL_SEED_BASE = 215300
DEFAULT_NEXT_BLOCKER = "m2155-paper-route-current-sim-controlled-comparison-reset-validation-result-audit"
TARGET_EXECUTABLE_SPEC_COUNT = 40
EXPECTED_OBSERVATION_DIM = 72
EXPECTED_MATERIALIZATION_SEMANTICS = "current_sim_executable_spec_v0"
EXPECTED_PAPER_VALIDITY_STATUS = "current_sim_executable_candidate_not_reset_validated"
EXPECTED_ACTOR_INPUT_CONTRACT = "P0_human_view_no_wheel_no_oracle"
SEED_SOURCE_MODE_BASE_PLUS_INDEX = "eval_seed_base_plus_index"
SEED_SOURCE_MODE_PREFER_SPEC_OVERRIDE = "prefer_spec_eval_seed_override"
SEED_SOURCE_MODES = (SEED_SOURCE_MODE_BASE_PLUS_INDEX, SEED_SOURCE_MODE_PREFER_SPEC_OVERRIDE)

METADATA_FIELDS = [
    "task_source_id",
    "benchmark_spec_id",
    "task_family",
    "claim_level_target",
    "scenario_source",
    "source_kind",
    "source_reference",
    "source_index",
    "source_seed",
    "eval_seed_override",
    "materialization_semantics",
    "paper_validity_status",
    "generated_proxy_source",
    "profile_specific_tuning",
    "actor_input_contract",
    "source_family_template",
    "capability_pair",
    "reveal_step",
    "metric_gap_policy",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
CONTRACT_FIELDNAMES = [
    *METADATA_FIELDS,
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "obstacle_enabled",
    "obstacle_max_sample_attempts_at_least_200",
    "materialization_semantics_current_sim_executable_spec_v0",
    "paper_validity_status_not_reset_validated",
    "generated_proxy_source_false",
    "profile_specific_tuning_false",
    "actor_input_contract_p0_human_view",
    "ranking_claim_false",
    "finite_window_vs_gru_conclusion_false",
    "paper_level_claim_false",
    "level3_self_id_claim_false",
    "contract_violation_count",
]
RESET_FIELDNAMES = [
    *METADATA_FIELDS,
    "row_index",
    "eval_seed_base",
    "eval_seed",
    "actual_eval_seed",
    "seed_source",
    "seed_source_parse_error",
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
    "benchmark_spec_id",
    "task_family",
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


def _bool_value(value: Any, *, default: bool = False) -> bool:
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
    return "true" if _bool_value(value) else "false"


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _aggregate_rows(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    return [{"key": key, "reset_count": int(value)} for key, value in sorted(counts.items())]


def _parse_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _eval_seed_for_spec(
    *,
    spec: Mapping[str, Any],
    row_index: int,
    eval_seed_base: int,
    seed_source_mode: str,
) -> tuple[int, str, str]:
    if seed_source_mode not in SEED_SOURCE_MODES:
        raise ValueError(f"unsupported seed_source_mode: {seed_source_mode}")
    if seed_source_mode == SEED_SOURCE_MODE_PREFER_SPEC_OVERRIDE:
        raw_override = spec.get("eval_seed_override")
        parsed_override = _parse_int(raw_override)
        if parsed_override is not None:
            return parsed_override, "eval_seed_override", ""
        if str(raw_override or "").strip():
            parse_error = f"invalid_eval_seed_override:{raw_override}"
        else:
            parse_error = "missing_eval_seed_override"
        return int(eval_seed_base) + int(row_index), "eval_seed_base_plus_index", parse_error
    return int(eval_seed_base) + int(row_index), "eval_seed_base_plus_index", ""


def _expected_seed_source_counts(*, seed_source_mode: str, spec_count: int) -> dict[str, int]:
    if seed_source_mode == SEED_SOURCE_MODE_PREFER_SPEC_OVERRIDE:
        return {"eval_seed_override": int(spec_count)}
    if seed_source_mode == SEED_SOURCE_MODE_BASE_PLUS_INDEX:
        return {"eval_seed_base_plus_index": int(spec_count)}
    raise ValueError(f"unsupported seed_source_mode: {seed_source_mode}")


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def current_sim_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    metadata = {field: str(spec.get(field, "")) for field in METADATA_FIELDS}
    for field in (
        "generated_proxy_source",
        "profile_specific_tuning",
        "controller_family_ranking_claim_made",
        "finite_window_vs_gru_conclusion_made",
        "paper_level_claim_made",
        "level3_self_id_claim_made",
    ):
        metadata[field] = _string_bool(spec.get(field))
    return metadata


def contract_row_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    obstacle = dict(env_config.get("obstacle") or {})
    materialization_semantics = str(spec.get("materialization_semantics", ""))
    paper_validity_status = str(spec.get("paper_validity_status", ""))
    actor_input_contract = str(spec.get("actor_input_contract", ""))
    checks = {
        "history_length_is_positive": int(env_config.get("history_length", 0)) >= 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool_value(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
        "obstacle_enabled": _bool_value(obstacle.get("enabled")),
        "obstacle_max_sample_attempts_at_least_200": int(obstacle.get("max_sample_attempts", 0)) >= 200,
        "materialization_semantics_current_sim_executable_spec_v0": (
            materialization_semantics == EXPECTED_MATERIALIZATION_SEMANTICS
        ),
        "paper_validity_status_not_reset_validated": paper_validity_status == EXPECTED_PAPER_VALIDITY_STATUS,
        "generated_proxy_source_false": not _bool_value(spec.get("generated_proxy_source")),
        "profile_specific_tuning_false": not _bool_value(spec.get("profile_specific_tuning")),
        "actor_input_contract_p0_human_view": actor_input_contract == EXPECTED_ACTOR_INPUT_CONTRACT,
        "ranking_claim_false": not _bool_value(spec.get("controller_family_ranking_claim_made")),
        "finite_window_vs_gru_conclusion_false": not _bool_value(spec.get("finite_window_vs_gru_conclusion_made")),
        "paper_level_claim_false": not _bool_value(spec.get("paper_level_claim_made")),
        "level3_self_id_claim_false": not _bool_value(spec.get("level3_self_id_claim_made")),
    }
    return {
        **current_sim_metadata(spec),
        **checks,
        "contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def metadata_missing_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        missing = [field for field in METADATA_FIELDS if str(spec.get(field, "")).strip() == ""]
        if missing:
            metadata = current_sim_metadata(spec)
            rows.append(
                {
                    "task_source_id": metadata["task_source_id"],
                    "benchmark_spec_id": metadata["benchmark_spec_id"],
                    "task_family": metadata["task_family"],
                    "missing_metadata_fields": ";".join(missing),
                }
            )
    return rows


def reset_current_sim_spec(
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
    metadata = current_sim_metadata(spec)
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


def claim_boundary_rows(*, reset_validity_admissible: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "current_sim_controlled_comparison_reset_validity",
            "admissible": reset_validity_admissible,
            "reason": "reset validity is admissible only if all reset gates pass and after M2155 audit",
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
            "claim": "winner_selection",
            "admissible": False,
            "reason": "reset validation does not compare controller-family outcomes",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "paper evidence requires measured execution and audited comparison support",
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


def run_current_sim_reset_validation_preflight(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    seed_source_mode: str = SEED_SOURCE_MODE_BASE_PLUS_INDEX,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    reset_rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        actual_eval_seed, seed_source, seed_source_parse_error = _eval_seed_for_spec(
            spec=spec,
            row_index=index,
            eval_seed_base=int(eval_seed_base),
            seed_source_mode=seed_source_mode,
        )
        row = reset_current_sim_spec(
            spec=spec,
            eval_seed=actual_eval_seed,
            expected_observation_dim=expected_observation_dim,
        )
        row.update(
            {
                "row_index": int(index),
                "eval_seed_base": int(eval_seed_base),
                "eval_seed": int(actual_eval_seed),
                "actual_eval_seed": int(actual_eval_seed),
                "seed_source": seed_source,
                "seed_source_parse_error": seed_source_parse_error,
            }
        )
        reset_rows.append(row)
    contract_rows = [contract_row_for_spec(spec) for spec in specs]
    failure_rows = [dict(row) for row in reset_rows if not _bool_value(row.get("reset_success"))]
    missing_rows = metadata_missing_rows(specs)
    forbidden_key_hits = forbidden_key_violations(specs)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    target_count_matches = target_spec_count is None or len(specs) == int(target_spec_count)
    reset_success_count = sum(_bool_value(row.get("reset_success")) for row in reset_rows)
    observation_finite_count = sum(_bool_value(row.get("observation_finite")) for row in reset_rows)
    obstacle_initialized_count = sum(_bool_value(row.get("obstacle_initialized")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool_value(row.get("reset_success")) and not _bool_value(row.get("observation_dimension_matches"))
        for row in reset_rows
    )
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    task_family_counts = _count_by(reset_rows, "task_family")
    expected_task_family_counts = _count_by(specs, "task_family")
    source_family_template_counts = _count_by(reset_rows, "source_family_template")
    expected_source_family_template_counts = _count_by(specs, "source_family_template")
    seed_source_counts = _count_by(reset_rows, "seed_source")
    expected_seed_source_counts = _expected_seed_source_counts(
        seed_source_mode=seed_source_mode,
        spec_count=len(specs),
    )
    seed_source_parse_failure_count = sum(
        1 for row in reset_rows if str(row.get("seed_source_parse_error", "")).strip()
    )
    task_family_quota_pass = task_family_counts == expected_task_family_counts
    source_family_template_quota_pass = source_family_template_counts == expected_source_family_template_counts
    seed_source_quota_pass = seed_source_counts == expected_seed_source_counts and seed_source_parse_failure_count == 0
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
        and task_family_quota_pass
        and source_family_template_quota_pass
        and seed_source_quota_pass
        and guardrail_violation_count == 0
    )
    result_class = (
        "current_sim_controlled_comparison_reset_validation_preflight_pass"
        if passes
        else "current_sim_controlled_comparison_reset_validation_preflight_fail"
    )

    write_csv_rows(output / "reset_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", failure_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(
        output / "reset_distribution_by_task_family.csv",
        _aggregate_rows(task_family_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        output / "reset_distribution_by_source_family_template.csv",
        _aggregate_rows(source_family_template_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        output / "reset_distribution_by_seed_source.csv",
        _aggregate_rows(seed_source_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(
        output / "claim_boundary.csv",
        claim_boundary_rows(reset_validity_admissible=bool(passes)),
        fieldnames=CLAIM_FIELDNAMES,
    )

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_task_specs_path": str(executable_task_specs_path),
        "input_executable_spec_count": len(specs),
        "target_executable_spec_count": target_spec_count,
        "seed_source_mode": seed_source_mode,
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
        "expected_task_family_counts": expected_task_family_counts,
        "task_family_counts": task_family_counts,
        "task_family_quota_pass": task_family_quota_pass,
        "expected_source_family_template_counts": expected_source_family_template_counts,
        "source_family_template_counts": source_family_template_counts,
        "source_family_template_quota_pass": source_family_template_quota_pass,
        "expected_seed_source_counts": expected_seed_source_counts,
        "seed_source_counts": seed_source_counts,
        "seed_source_quota_pass": seed_source_quota_pass,
        "seed_source_parse_failure_count": int(seed_source_parse_failure_count),
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
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "reset_rows": str(output / "reset_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "contract_rows": str(output / "contract_rows.csv"),
            "reset_distribution_by_task_family": str(output / "reset_distribution_by_task_family.csv"),
            "reset_distribution_by_source_family_template": str(
                output / "reset_distribution_by_source_family_template.csv"
            ),
            "reset_distribution_by_seed_source": str(output / "reset_distribution_by_seed_source.csv"),
            "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2154-paper-route-current-sim-controlled-comparison-reset-validation-implementation-and-run",
            "status": "completed" if passes else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_EXECUTABLE_SPEC_COUNT)
    parser.add_argument("--expected-observation-dim", type=int, default=EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--seed-source-mode", choices=SEED_SOURCE_MODES, default=SEED_SOURCE_MODE_BASE_PLUS_INDEX)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    summary = run_current_sim_reset_validation_preflight(
        executable_task_specs_path=args.executable_task_specs,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_spec_count=int(args.target_spec_count),
        expected_observation_dim=args.expected_observation_dim,
        seed_source_mode=str(args.seed_source_mode),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"reset_attempt_count={summary['reset_attempt_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"reset_failure_count={summary['reset_failure_count']}")
    print(f"seed_source_mode={summary['seed_source_mode']}")
    print(f"seed_source_counts={summary['seed_source_counts']}")
    print(f"seed_source_quota_pass={summary['seed_source_quota_pass']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
