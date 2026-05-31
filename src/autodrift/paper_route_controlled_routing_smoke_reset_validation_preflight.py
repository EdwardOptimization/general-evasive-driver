"""Reset-only validator for the controlled routing-smoke executable specs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
)
from autodrift.executable_v2_task_quality_reset_validation_preflight import reset_task_quality_spec


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight")
DEFAULT_EVAL_SEED_BASE = 203600
TARGET_EXECUTABLE_SPEC_COUNT = 36
EXPECTED_OBSERVATION_DIM = 72
METADATA_FIELDS = [
    "task_source_id",
    "panel_source_id",
    "panel_task_family",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "source_reference",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
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
    "panel_source_id",
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


def _count_by_key_func(rows: Iterable[Mapping[str, Any]], key_func: Any) -> dict[str, int]:
    return dict(sorted(Counter(str(key_func(row)) for row in rows).items()))


def _aggregate_rows(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    return [{"key": key, "reset_count": int(value)} for key, value in sorted(counts.items())]


def _generated_proxy_key(row: Mapping[str, Any]) -> str:
    paper_claim = str(row.get("paper_validity_claim", "")).strip().lower()
    return (
        f"generated={_string_bool(row.get('generated_source_row'))}|"
        f"semantics={row.get('materialization_semantics', '')}|"
        f"paper_claim={paper_claim}"
    )


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def controlled_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    metadata = {field: str(spec.get(field, "")) for field in METADATA_FIELDS}
    metadata["generated_source_row"] = _string_bool(spec.get("generated_source_row"))
    metadata["paper_validity_claim"] = str(spec.get("paper_validity_claim", "")).lower()
    return metadata


def contract_row_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    generated = _bool_value(spec.get("generated_source_row"))
    materialization_semantics = str(spec.get("materialization_semantics", ""))
    paper_validity_claim = str(spec.get("paper_validity_claim", "")).lower()
    checks = {
        "history_length_is_positive": int(env_config.get("history_length", 0)) >= 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool_value(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
        "materialization_semantics_smoke_proxy": materialization_semantics == "smoke_proxy",
        "paper_validity_claim_false": paper_validity_claim == "false",
        "generated_source_row_proxy_semantics": (not generated) or materialization_semantics == "smoke_proxy",
    }
    return {
        **controlled_metadata(spec),
        **checks,
        "contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def metadata_missing_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        missing = [field for field in METADATA_FIELDS if str(spec.get(field, "")).strip() == ""]
        if missing:
            metadata = controlled_metadata(spec)
            rows.append(
                {
                    "task_source_id": metadata["task_source_id"],
                    "panel_source_id": metadata["panel_source_id"],
                    "panel_task_family": metadata["panel_task_family"],
                    "source_kind": metadata["source_kind"],
                    "missing_metadata_fields": ";".join(missing),
                }
            )
    return rows


def reset_controlled_spec(
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
    metadata = controlled_metadata(spec)
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


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "controlled_routing_smoke_reset_validity",
            "admissible": True,
            "reason": "M2036 may claim reset-validity only if all reset gates pass",
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
            "reason": "generated T2/T3 rows remain smoke proxies until later task-semantics validation",
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


def run_controlled_routing_smoke_reset_validation_preflight(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    next_blocker: str = "m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    reset_rows = [
        reset_controlled_spec(
            spec=spec,
            eval_seed=int(eval_seed_base) + index,
            expected_observation_dim=expected_observation_dim,
        )
        for index, spec in enumerate(specs)
    ]
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
    family_counts = _count_by(reset_rows, "panel_task_family")
    expected_family_counts = _count_by(specs, "panel_task_family")
    source_kind_counts = _count_by(reset_rows, "source_kind")
    expected_source_kind_counts = _count_by(specs, "source_kind")
    proxy_template_counts = _count_by(reset_rows, "proxy_template_family")
    expected_proxy_template_counts = _count_by(specs, "proxy_template_family")
    generated_proxy_counts = _count_by_key_func(reset_rows, _generated_proxy_key)
    expected_generated_proxy_counts = _count_by_key_func(specs, _generated_proxy_key)
    family_quota_pass = family_counts == expected_family_counts
    source_kind_quota_pass = source_kind_counts == expected_source_kind_counts
    proxy_template_quota_pass = proxy_template_counts == expected_proxy_template_counts
    generated_proxy_quota_pass = generated_proxy_counts == expected_generated_proxy_counts
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
        and source_kind_quota_pass
        and proxy_template_quota_pass
        and generated_proxy_quota_pass
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(
        output / "reset_failure_rows.csv",
        failure_rows,
        fieldnames=RESET_FIELDNAMES,
    )
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(output / "reset_distribution_by_family.csv", _aggregate_rows(family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(
        output / "reset_distribution_by_source_kind.csv",
        _aggregate_rows(source_kind_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        output / "reset_distribution_by_proxy_template.csv",
        _aggregate_rows(proxy_template_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        output / "reset_distribution_by_generated_proxy.csv",
        _aggregate_rows(generated_proxy_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "controlled_routing_smoke_reset_validation_preflight_pass"
            if passes
            else "controlled_routing_smoke_reset_validation_preflight_fail"
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
        "expected_source_kind_counts": expected_source_kind_counts,
        "source_kind_counts": source_kind_counts,
        "source_kind_quota_pass": source_kind_quota_pass,
        "expected_proxy_template_counts": expected_proxy_template_counts,
        "proxy_template_counts": proxy_template_counts,
        "proxy_template_quota_pass": proxy_template_quota_pass,
        "expected_generated_proxy_counts": expected_generated_proxy_counts,
        "generated_proxy_counts": generated_proxy_counts,
        "generated_proxy_quota_pass": generated_proxy_quota_pass,
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
            "reset_distribution_by_family": str(output / "reset_distribution_by_family.csv"),
            "reset_distribution_by_source_kind": str(output / "reset_distribution_by_source_kind.csv"),
            "reset_distribution_by_proxy_template": str(output / "reset_distribution_by_proxy_template.csv"),
            "reset_distribution_by_generated_proxy": str(output / "reset_distribution_by_generated_proxy.csv"),
            "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
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
    parser.add_argument("--next-blocker", default="m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit")
    args = parser.parse_args()
    summary = run_controlled_routing_smoke_reset_validation_preflight(
        executable_task_specs_path=args.executable_task_specs,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_spec_count=int(args.target_spec_count),
        expected_observation_dim=args.expected_observation_dim,
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
