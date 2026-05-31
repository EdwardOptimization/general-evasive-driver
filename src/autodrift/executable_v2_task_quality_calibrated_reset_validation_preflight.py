"""Reset-only validator for calibrated executable v2 task-quality specs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.executable_v2_task_quality_reset_validation_preflight import reset_task_quality_spec


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight")
DEFAULT_EVAL_SEED_BASE = 196000
TARGET_EXECUTABLE_SPEC_COUNT = 80
EXPECTED_OBSERVATION_DIM = 72
EXPECTED_SOURCE_KIND_COUNTS = {
    "anchor_neighborhood": 32,
    "mitigation_isolation_check": 16,
    "offtrack_boundary_relief": 8,
    "success_stabilizer": 24,
}
EXPECTED_ROLE_SURFACE_COUNTS = {
    "anchor_neighborhood|stable_aeb|post_friction_step": 16,
    "anchor_neighborhood|stable_aeb|steady_surface": 16,
    "mitigation_isolation_check|drift_required_recovery|steady_surface": 3,
    "mitigation_isolation_check|stable_aeb|post_friction_step": 4,
    "mitigation_isolation_check|unavoidable_mitigation|post_friction_step": 4,
    "mitigation_isolation_check|unavoidable_mitigation|steady_surface": 5,
    "offtrack_boundary_relief|stable_aes_only|relief_surface_unspecified": 8,
    "success_stabilizer|drift_required_recovery|post_friction_step": 4,
    "success_stabilizer|drift_required_recovery|steady_surface": 2,
    "success_stabilizer|stable_aeb|post_friction_step": 4,
    "success_stabilizer|stable_aeb|steady_surface": 4,
    "success_stabilizer|stable_aes_only|post_friction_step": 3,
    "success_stabilizer|stable_aes_only|steady_surface": 3,
    "success_stabilizer|unavoidable_mitigation|post_friction_step": 1,
    "success_stabilizer|unavoidable_mitigation|steady_surface": 3,
}
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
CONTRACT_FIELDNAMES = [
    "task_source_id",
    "candidate_source_id",
    "repair_candidate_id",
    "repair_source_kind",
    "selection_quota_name",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "parent_surface_variant",
    "normalized_surface_variant",
    "history_length_is_one",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "labels_enter_actor_input_false",
    "paper_holdout_candidate_false",
    "contract_violation_count",
]
QUOTA_METADATA_FIELDS = (
    "repair_source_kind",
    "source_role_semantics",
    "normalized_surface_variant",
)
QUOTA_METADATA_MISSING_FIELDNAMES = [
    "task_source_id",
    "candidate_source_id",
    "repair_candidate_id",
    "repair_source_kind",
    "source_role_semantics",
    "normalized_surface_variant",
    "missing_quota_fields",
]


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


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_counts(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts["|".join(str(row.get(key, "")) for key in keys)] += 1
    return dict(sorted(counts.items()))


def _aggregate_count_rows(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        counts[tuple(str(row.get(key, "")) for key in keys)] += 1
    out: list[dict[str, Any]] = []
    for values, count in sorted(counts.items()):
        item = {key: value for key, value in zip(keys, values)}
        item["reset_count"] = int(count)
        out.append(item)
    return out


def _quota_metadata_missing_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for spec in specs:
        missing_fields = [
            field for field in QUOTA_METADATA_FIELDS if str(spec.get(field, "")).strip() == ""
        ]
        if missing_fields:
            metadata = calibrated_metadata(spec)
            out.append(
                {
                    "task_source_id": metadata["task_source_id"],
                    "candidate_source_id": metadata["candidate_source_id"],
                    "repair_candidate_id": metadata["repair_candidate_id"],
                    "repair_source_kind": metadata["repair_source_kind"],
                    "source_role_semantics": metadata["source_role_semantics"],
                    "normalized_surface_variant": metadata["normalized_surface_variant"],
                    "missing_quota_fields": ";".join(missing_fields),
                }
            )
    return out


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def calibrated_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_source_id": str(spec.get("task_source_id", "")),
        "candidate_source_id": str(spec.get("candidate_source_id", "")),
        "repair_candidate_id": str(spec.get("repair_candidate_id", "")),
        "repair_source_kind": str(spec.get("repair_source_kind", "")),
        "selection_quota_name": str(spec.get("selection_quota_name", "")),
        "source_role_semantics": str(spec.get("source_role_semantics", "")),
        "parent_feasibility_tier_id": str(spec.get("parent_feasibility_tier_id", "")),
        "parent_surface_variant": str(spec.get("parent_surface_variant", "")),
        "normalized_surface_variant": str(spec.get("normalized_surface_variant", "")),
        "source_split": str(spec.get("source_split", "")),
        "base_geometry_source": str(spec.get("base_geometry_source", "")),
        "representative_cell_rule": str(spec.get("representative_cell_rule", "")),
        "source_v1_bounded_panel_spec_id": str(spec.get("source_v1_bounded_panel_spec_id", "")),
        "source_scenario_spec_id": str(spec.get("source_scenario_spec_id", "")),
        "preflight_sampled_obstacle_label": str(spec.get("sampled_obstacle_label", "")),
        "preflight_obstacle_distance": spec.get("obstacle_distance", ""),
        "preflight_obstacle_half_width": spec.get("obstacle_half_width", ""),
    }


def contract_row_for_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    checks = {
        "history_length_is_one": int(env_config.get("history_length", 0)) == 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool_value(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
        "labels_enter_actor_input_false": not _bool_value(spec.get("labels_enter_actor_input")),
        "paper_holdout_candidate_false": not _bool_value(spec.get("paper_holdout_candidate")),
    }
    return {
        **calibrated_metadata(spec),
        **checks,
        "contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def reset_calibrated_spec(
    *,
    spec: Mapping[str, Any],
    eval_seed: int,
    expected_observation_dim: int | None,
) -> dict[str, Any]:
    reset_row = reset_task_quality_spec(
        spec=spec,
        eval_seed=eval_seed,
        expected_observation_dim=expected_observation_dim,
    )
    contract = contract_row_for_spec(spec)
    metadata = calibrated_metadata(spec)
    reset_row.update(metadata)
    reset_row.update(
        {
            "contract_violation_count": int(contract["contract_violation_count"]),
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
        }
    )
    return reset_row


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "calibrated_reset_validation",
            "admissible": True,
            "reason": "M1960 may claim only reset-validity if all reset gates pass",
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
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "reset validation is not measured rollout evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "reset validation does not test history necessity or wrong-history interventions",
        },
    ]


def run_calibrated_reset_validation_preflight(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    next_blocker: str = "m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    reset_rows = [
        reset_calibrated_spec(
            spec=spec,
            eval_seed=int(eval_seed_base) + index,
            expected_observation_dim=expected_observation_dim,
        )
        for index, spec in enumerate(specs)
    ]
    contract_rows = [contract_row_for_spec(spec) for spec in specs]
    failure_rows = [dict(row) for row in reset_rows if not _bool_value(row.get("reset_success"))]
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    forbidden_key_hits = forbidden_key_violations(specs)
    target_count_matches = target_spec_count is None or len(specs) == int(target_spec_count)
    reset_success_count = sum(_bool_value(row.get("reset_success")) for row in reset_rows)
    observation_finite_count = sum(_bool_value(row.get("observation_finite")) for row in reset_rows)
    obstacle_initialized_count = sum(_bool_value(row.get("obstacle_initialized")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool_value(row.get("reset_success")) and not _bool_value(row.get("observation_dimension_matches"))
        for row in reset_rows
    )
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    label_actor_input_violation_count = sum(
        not _bool_value(row.get("labels_enter_actor_input_false"), default=True) for row in contract_rows
    )
    source_kind_counts = _count_by(reset_rows, "repair_source_kind")
    role_surface_counts = _group_counts(
        reset_rows,
        ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
    )
    expected_source_kind_counts = _count_by(specs, "repair_source_kind")
    expected_role_surface_counts = _group_counts(
        specs,
        ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
    )
    quota_metadata_missing_rows = _quota_metadata_missing_rows(specs)
    quota_metadata_missing_count = len(quota_metadata_missing_rows)
    source_kind_quota_pass = source_kind_counts == expected_source_kind_counts
    role_surface_quota_pass = role_surface_counts == expected_role_surface_counts
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
        and not forbidden_key_hits
        and quota_metadata_missing_count == 0
        and source_kind_quota_pass
        and role_surface_quota_pass
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_rows.csv", reset_rows)
    write_csv_rows(
        output / "reset_failure_rows.csv",
        failure_rows,
        fieldnames=list(reset_rows[0].keys()) if reset_rows else None,
    )
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(
        output / "reset_distribution_by_source_kind.csv",
        _aggregate_count_rows(reset_rows, ("repair_source_kind",)),
    )
    write_csv_rows(
        output / "reset_distribution_by_role_surface.csv",
        _aggregate_count_rows(
            reset_rows,
            ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
        ),
    )
    write_csv_rows(
        output / "quota_metadata_missing_rows.csv",
        quota_metadata_missing_rows,
        fieldnames=QUOTA_METADATA_MISSING_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "task_quality_calibrated_reset_validation_preflight_pass"
            if passes
            else "task_quality_calibrated_reset_validation_preflight_fail"
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
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "expected_quota_source": "executable_task_specs",
        "expected_source_kind_counts": expected_source_kind_counts,
        "expected_role_surface_counts": expected_role_surface_counts,
        "quota_metadata_missing_count": quota_metadata_missing_count,
        "source_kind_counts": source_kind_counts,
        "source_kind_quota_pass": source_kind_quota_pass,
        "role_surface_counts": role_surface_counts,
        "role_surface_quota_pass": role_surface_quota_pass,
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
            "reset_distribution_by_source_kind": str(output / "reset_distribution_by_source_kind.csv"),
            "reset_distribution_by_role_surface": str(output / "reset_distribution_by_role_surface.csv"),
            "quota_metadata_missing_rows": str(output / "quota_metadata_missing_rows.csv"),
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
    parser.add_argument("--next-blocker", default="m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit")
    args = parser.parse_args()
    summary = run_calibrated_reset_validation_preflight(
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
