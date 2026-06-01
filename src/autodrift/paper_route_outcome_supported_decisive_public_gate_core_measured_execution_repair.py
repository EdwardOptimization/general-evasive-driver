"""No-rollout repair for public-gate core measured execution artifacts."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.paper_route_controlled_routing_smoke_measured_runner import (
    METADATA_MISSING_FIELDNAMES,
    VALIDATION_FAILURE_FIELDNAMES,
    load_executable_task_specs,
    load_workload_rows,
    metadata_missing_rows,
    validation_failure_rows,
)
from autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight import (
    CLAIM_FIELDNAMES,
    _guardrail_flags,
)
from autodrift.paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction import _stable_json


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair/"
    "public_gate_core_measured_compatible_executable_task_specs.json"
)
DEFAULT_WORKLOAD = Path(
    "runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair/"
    "public_gate_core_measured_compatible_workload.csv"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight/reset_rows.csv"
)
DEFAULT_FAILURE_ROWS = Path(
    "runs/m2101_paper_route_outcome_supported_decisive_public_gate_core_measured_execution/failure_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2104_paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair")
DEFAULT_NEXT_BLOCKER = "m2105-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-repair-result-audit"
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair_v0"

TARGET_SPEC_COUNT = 96
TARGET_WORKLOAD_COUNT = 480
TARGET_PROFILE_COUNT = 5
TARGET_EVAL_SEED_OVERRIDE_COUNT = 2

FULL_METADATA_SENTINELS = {
    "parent_feasibility_tier_id": "tier_not_applicable_outcome_supported_decisive",
    "normalized_surface_variant": "outcome_supported_decisive_public_gate_core",
}
SPEC_FIELDNAMES = [
    "task_source_id",
    "panel_source_id",
    "candidate_id",
    "source_reference",
    "panel_task_family",
    "source_split",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "panel_source_id",
    "candidate_id",
    "panel_task_family",
    "source_split",
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
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
    "eval_seed_override",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
ENV_CONFIG_INTEGRITY_FIELDNAMES = [
    "task_source_id",
    "env_config_changed",
    "original_env_config_json",
    "repaired_env_config_json",
]
EVAL_SEED_OVERRIDE_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "profile_name",
    "eval_seed_override",
    "source",
]


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def _claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "public_gate_core_measured_execution_repair",
            "admissible": bool(passes),
            "reason": "admissible only if repaired artifacts are metadata-complete without rollout",
        },
        {
            "claim": "measured_execution_rerun_readiness_before_audit",
            "admissible": False,
            "reason": "M2104 repairs artifacts only; rerun remains blocked until audit",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "no measured rerun or ranking is performed",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "metadata and seed repair is not paper-level performance evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "no controller-family comparison is interpreted",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "artifact repair does not test history necessity",
        },
    ]


def _reset_by_id(reset_rows: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("task_source_id", "")): row for row in reset_rows}


def _failure_workload_ids(failure_rows: Iterable[Mapping[str, Any]]) -> set[str]:
    return {str(row.get("workload_id", "")) for row in failure_rows if str(row.get("workload_id", "")).strip()}


def _repair_spec(spec: Mapping[str, Any], reset_row: Mapping[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(dict(spec))
    row["source_role_semantics"] = str(row.get("task_role_semantics", "")).strip()
    row["parent_feasibility_tier_id"] = FULL_METADATA_SENTINELS["parent_feasibility_tier_id"]
    row["normalized_surface_variant"] = FULL_METADATA_SENTINELS["normalized_surface_variant"]
    row["sampled_obstacle_label"] = str(reset_row.get("reset_sampled_obstacle_label", "")).strip()
    return row


def _repair_workload(
    workload_row: Mapping[str, Any],
    *,
    spec: Mapping[str, Any],
    reset_row: Mapping[str, Any],
    failed_workload_ids: set[str],
) -> dict[str, Any]:
    row = copy.deepcopy(dict(workload_row))
    for field in (
        "source_origin",
        "source_role_semantics",
        "parent_feasibility_tier_id",
        "normalized_surface_variant",
        "sampled_obstacle_label",
        "source_reference",
    ):
        row[field] = str(spec.get(field, "")).strip()
    if str(row.get("workload_id", "")) in failed_workload_ids:
        row["eval_seed_override"] = str(reset_row.get("eval_seed", "")).strip()
    else:
        row["eval_seed_override"] = ""
    return row


def _env_config_integrity_rows(
    original_specs: Iterable[Mapping[str, Any]],
    repaired_specs: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    repaired_by_id = {str(spec.get("task_source_id", "")): spec for spec in repaired_specs}
    rows: list[dict[str, Any]] = []
    for spec in original_specs:
        task_id = str(spec.get("task_source_id", ""))
        original_json = _stable_json(spec.get("env_config", {}))
        repaired_json = _stable_json(repaired_by_id.get(task_id, {}).get("env_config", {}))
        rows.append(
            {
                "task_source_id": task_id,
                "env_config_changed": original_json != repaired_json,
                "original_env_config_json": original_json,
                "repaired_env_config_json": repaired_json,
            }
        )
    return rows


def _eval_seed_override_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        override = str(row.get("eval_seed_override", "")).strip()
        if override:
            output.append(
                {
                    "workload_id": row.get("workload_id", ""),
                    "task_source_id": row.get("task_source_id", ""),
                    "profile_name": row.get("profile_name", ""),
                    "eval_seed_override": override,
                    "source": "m2091_reset_success_seed",
                }
            )
    return output


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(values)
    return int(sum(1 for value in counts.values() if value > 1))


def run_measured_execution_repair(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    failure_rows_path: Path | str = DEFAULT_FAILURE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_workload_count: int = TARGET_WORKLOAD_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    target_eval_seed_override_count: int = TARGET_EVAL_SEED_OVERRIDE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    original_specs = load_executable_task_specs(executable_task_specs_path)
    original_workload = load_workload_rows(workload_path)
    reset_lookup = _reset_by_id(_read_csv_rows(reset_rows_path))
    failed_workload_ids = _failure_workload_ids(_read_csv_rows(failure_rows_path))

    repaired_specs = [
        _repair_spec(spec, reset_lookup.get(str(spec.get("task_source_id", "")), {}))
        for spec in original_specs
    ]
    repaired_by_id = {str(spec.get("task_source_id", "")): spec for spec in repaired_specs}
    repaired_workload = [
        _repair_workload(
            row,
            spec=repaired_by_id.get(str(row.get("task_source_id", "")), {}),
            reset_row=reset_lookup.get(str(row.get("task_source_id", "")), {}),
            failed_workload_ids=failed_workload_ids,
        )
        for row in original_workload
    ]

    missing_rows = metadata_missing_rows(executable_specs=repaired_specs, workload_rows=repaired_workload)
    validation_failures = validation_failure_rows(executable_specs=repaired_specs, workload_rows=repaired_workload)
    integrity_rows = _env_config_integrity_rows(original_specs, repaired_specs)
    override_rows = _eval_seed_override_rows(repaired_workload)

    env_config_changed_count = sum(_bool(row.get("env_config_changed")) for row in integrity_rows)
    duplicate_workload_id_count = _duplicate_count(str(row.get("workload_id", "")) for row in repaired_workload)
    profile_count = len({str(row.get("profile_name", "")) for row in repaired_workload})
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_counts_pass = (
        len(repaired_specs) == int(target_spec_count)
        and len(repaired_workload) == int(target_workload_count)
        and profile_count == int(target_profile_count)
        and len(override_rows) == int(target_eval_seed_override_count)
    )
    passes = (
        target_counts_pass
        and not missing_rows
        and not validation_failures
        and env_config_changed_count == 0
        and duplicate_workload_id_count == 0
        and guardrail_violation_count == 0
    )

    write_json(
        output / "public_gate_core_measured_repaired_executable_task_specs.json",
        {
            "protocol": PROTOCOL_NAME,
            "source_executable_task_specs": str(executable_task_specs_path),
            "source_workload": str(workload_path),
            "source_reset_rows": str(reset_rows_path),
            "source_failure_rows": str(failure_rows_path),
            "executable_task_specs": repaired_specs,
        },
    )
    write_csv_rows(output / "public_gate_core_measured_repaired_executable_task_specs.csv", repaired_specs, SPEC_FIELDNAMES)
    write_csv_rows(output / "public_gate_core_measured_repaired_workload.csv", repaired_workload, WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows, METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output / "validation_failure_rows.csv", validation_failures, VALIDATION_FAILURE_FIELDNAMES)
    write_csv_rows(output / "env_config_integrity_rows.csv", integrity_rows, ENV_CONFIG_INTEGRITY_FIELDNAMES)
    write_csv_rows(output / "eval_seed_override_rows.csv", override_rows, EVAL_SEED_OVERRIDE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    artifacts = {
        "summary": str(output / "summary.json"),
        "public_gate_core_measured_repaired_executable_task_specs": str(
            output / "public_gate_core_measured_repaired_executable_task_specs.json"
        ),
        "public_gate_core_measured_repaired_executable_task_specs_csv": str(
            output / "public_gate_core_measured_repaired_executable_task_specs.csv"
        ),
        "public_gate_core_measured_repaired_workload": str(output / "public_gate_core_measured_repaired_workload.csv"),
        "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
        "validation_failure_rows": str(output / "validation_failure_rows.csv"),
        "env_config_integrity_rows": str(output / "env_config_integrity_rows.csv"),
        "eval_seed_override_rows": str(output / "eval_seed_override_rows.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    summary = {
        "result_class": (
            "public_gate_core_measured_execution_repair_pass"
            if passes
            else "public_gate_core_measured_execution_repair_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "executable_task_specs_path": str(executable_task_specs_path),
        "workload_path": str(workload_path),
        "reset_rows_path": str(reset_rows_path),
        "failure_rows_path": str(failure_rows_path),
        "compatible_spec_count": len(repaired_specs),
        "compatible_workload_count": len(repaired_workload),
        "profile_count": profile_count,
        "target_spec_count": int(target_spec_count),
        "target_workload_count": int(target_workload_count),
        "target_profile_count": int(target_profile_count),
        "target_counts_pass": bool(target_counts_pass),
        "metadata_missing_count": len(missing_rows),
        "validation_failure_count": len(validation_failures),
        "eval_seed_override_count": len(override_rows),
        "target_eval_seed_override_count": int(target_eval_seed_override_count),
        "eval_seed_override_workload_ids": [str(row["workload_id"]) for row in override_rows],
        "env_config_changed_count": int(env_config_changed_count),
        "duplicate_workload_id_count": int(duplicate_workload_id_count),
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
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--failure-rows", type=Path, default=DEFAULT_FAILURE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_SPEC_COUNT)
    parser.add_argument("--target-workload-count", type=int, default=TARGET_WORKLOAD_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--target-eval-seed-override-count", type=int, default=TARGET_EVAL_SEED_OVERRIDE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_measured_execution_repair(
        executable_task_specs_path=args.executable_task_specs,
        workload_path=args.workload,
        reset_rows_path=args.reset_rows,
        failure_rows_path=args.failure_rows,
        output_dir=args.output_dir,
        target_spec_count=int(args.target_spec_count),
        target_workload_count=int(args.target_workload_count),
        target_profile_count=int(args.target_profile_count),
        target_eval_seed_override_count=int(args.target_eval_seed_override_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"compatible_spec_count={summary['compatible_spec_count']}")
    print(f"compatible_workload_count={summary['compatible_workload_count']}")
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"validation_failure_count={summary['validation_failure_count']}")
    print(f"eval_seed_override_count={summary['eval_seed_override_count']}")
    print(f"env_config_changed_count={summary['env_config_changed_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
