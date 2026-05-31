"""No-rollout metadata repair for public-gate core measured-runner compatibility."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.paper_route_controlled_routing_smoke_measured_runner import (
    VALIDATION_FAILURE_FIELDNAMES,
    load_executable_task_specs,
    load_workload_rows,
    validation_failure_rows,
)
from autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight import (
    CLAIM_FIELDNAMES,
    _guardrail_flags,
)
from autodrift.paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction import _stable_json


DEFAULT_PUBLIC_GATE_CORE_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/"
    "public_gate_core_executable_task_specs.json"
)
DEFAULT_PUBLIC_GATE_CORE_WORKLOAD = Path(
    "runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/"
    "public_gate_core_planned_sentinel_workload.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair"
)
DEFAULT_NEXT_BLOCKER = (
    "m2099-paper-route-outcome-supported-decisive-public-gate-core-measured-runner-compatibility-repair-result-audit"
)
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair_v0"

TARGET_SPEC_COUNT = 96
TARGET_WORKLOAD_COUNT = 480
TARGET_PROFILE_COUNT = 5

SPEC_FIELDNAMES = [
    "task_source_id",
    "panel_source_id",
    "candidate_id",
    "source_reference",
    "panel_task_family",
    "source_split",
    "source_kind",
    "source_edge",
    "window_tag",
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
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
    "source_kind",
    "source_edge",
    "window_tag",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
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
    "compatible_env_config_json",
]


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


def _string_bool(value: Any) -> str:
    return "true" if _bool(value) else "false"


def _claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "public_gate_core_measured_runner_metadata_compatibility",
            "admissible": bool(passes),
            "reason": "admissible only if repaired artifacts pass measured-runner validation without rollout",
        },
        {
            "claim": "measured_execution_readiness_before_audit",
            "admissible": False,
            "reason": "M2098 only repairs metadata; measured execution remains blocked until audit",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "no measured execution or ranking is run",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "metadata compatibility is not paper-level performance evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "no controller-family comparison is run",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "metadata compatibility does not test history necessity",
        },
    ]


def _repair_specs(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    for spec in specs:
        row = copy.deepcopy(dict(spec))
        row["panel_source_id"] = str(row.get("source_reference", "")).strip()
        repaired.append(row)
    return repaired


def _repair_workload(workload_rows: Iterable[Mapping[str, Any]], specs_by_id: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    for row_in in workload_rows:
        row = copy.deepcopy(dict(row_in))
        spec = specs_by_id.get(str(row.get("task_source_id", "")), {})
        row["panel_source_id"] = str(spec.get("panel_source_id", "")).strip()
        row["proxy_template_family"] = str(spec.get("proxy_template_family", "")).strip()
        row["generated_source_row"] = _string_bool(spec.get("generated_source_row"))
        repaired.append(row)
    return repaired


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
                "compatible_env_config_json": repaired_json,
            }
        )
    return rows


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(values)
    return int(sum(1 for value in counts.values() if value > 1))


def run_measured_runner_compatibility_repair(
    *,
    public_gate_core_executable_task_specs_path: Path | str = DEFAULT_PUBLIC_GATE_CORE_EXECUTABLE_TASK_SPECS,
    public_gate_core_workload_path: Path | str = DEFAULT_PUBLIC_GATE_CORE_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_workload_count: int = TARGET_WORKLOAD_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    original_specs = load_executable_task_specs(public_gate_core_executable_task_specs_path)
    original_workload = load_workload_rows(public_gate_core_workload_path)
    repaired_specs = _repair_specs(original_specs)
    repaired_by_id = {str(spec.get("task_source_id", "")): spec for spec in repaired_specs}
    repaired_workload = _repair_workload(original_workload, repaired_by_id)
    validation_failures = validation_failure_rows(executable_specs=repaired_specs, workload_rows=repaired_workload)
    integrity_rows = _env_config_integrity_rows(original_specs, repaired_specs)

    spec_panel_source_id_missing_count = sum(not str(spec.get("panel_source_id", "")).strip() for spec in repaired_specs)
    workload_proxy_template_family_missing_count = sum(
        not str(row.get("proxy_template_family", "")).strip() for row in repaired_workload
    )
    workload_generated_source_row_missing_count = sum(
        not str(row.get("generated_source_row", "")).strip() for row in repaired_workload
    )
    env_config_changed_count = sum(_bool(row.get("env_config_changed")) for row in integrity_rows)
    duplicate_workload_id_count = _duplicate_count(str(row.get("workload_id", "")) for row in repaired_workload)
    profile_count = len({str(row.get("profile_name", "")) for row in repaired_workload})
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    target_counts_pass = (
        len(repaired_specs) == int(target_spec_count)
        and len(repaired_workload) == int(target_workload_count)
        and profile_count == int(target_profile_count)
    )
    passes = (
        target_counts_pass
        and spec_panel_source_id_missing_count == 0
        and workload_proxy_template_family_missing_count == 0
        and workload_generated_source_row_missing_count == 0
        and len(validation_failures) == 0
        and env_config_changed_count == 0
        and duplicate_workload_id_count == 0
        and guardrail_violation_count == 0
    )

    write_json(
        output / "public_gate_core_measured_compatible_executable_task_specs.json",
        {
            "protocol": PROTOCOL_NAME,
            "source_executable_task_specs": str(public_gate_core_executable_task_specs_path),
            "source_workload": str(public_gate_core_workload_path),
            "executable_task_specs": repaired_specs,
        },
    )
    write_csv_rows(output / "public_gate_core_measured_compatible_executable_task_specs.csv", repaired_specs, SPEC_FIELDNAMES)
    write_csv_rows(output / "public_gate_core_measured_compatible_workload.csv", repaired_workload, WORKLOAD_FIELDNAMES)
    write_csv_rows(
        output / "compatibility_validation_failure_rows.csv",
        validation_failures,
        VALIDATION_FAILURE_FIELDNAMES,
    )
    write_csv_rows(output / "env_config_integrity_rows.csv", integrity_rows, ENV_CONFIG_INTEGRITY_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    artifacts = {
        "summary": str(output / "summary.json"),
        "public_gate_core_measured_compatible_executable_task_specs": str(
            output / "public_gate_core_measured_compatible_executable_task_specs.json"
        ),
        "public_gate_core_measured_compatible_executable_task_specs_csv": str(
            output / "public_gate_core_measured_compatible_executable_task_specs.csv"
        ),
        "public_gate_core_measured_compatible_workload": str(
            output / "public_gate_core_measured_compatible_workload.csv"
        ),
        "compatibility_validation_failure_rows": str(output / "compatibility_validation_failure_rows.csv"),
        "env_config_integrity_rows": str(output / "env_config_integrity_rows.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    summary = {
        "result_class": (
            "public_gate_core_measured_runner_compatibility_repair_pass"
            if passes
            else "public_gate_core_measured_runner_compatibility_repair_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "public_gate_core_executable_task_specs_path": str(public_gate_core_executable_task_specs_path),
        "public_gate_core_workload_path": str(public_gate_core_workload_path),
        "compatible_spec_count": len(repaired_specs),
        "compatible_workload_count": len(repaired_workload),
        "profile_count": profile_count,
        "target_spec_count": int(target_spec_count),
        "target_workload_count": int(target_workload_count),
        "target_profile_count": int(target_profile_count),
        "target_counts_pass": bool(target_counts_pass),
        "spec_panel_source_id_missing_count": int(spec_panel_source_id_missing_count),
        "workload_proxy_template_family_missing_count": int(workload_proxy_template_family_missing_count),
        "workload_generated_source_row_missing_count": int(workload_generated_source_row_missing_count),
        "measured_runner_validation_failure_count": len(validation_failures),
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
    parser.add_argument(
        "--public-gate-core-executable-task-specs",
        type=Path,
        default=DEFAULT_PUBLIC_GATE_CORE_EXECUTABLE_TASK_SPECS,
    )
    parser.add_argument("--public-gate-core-workload", type=Path, default=DEFAULT_PUBLIC_GATE_CORE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_SPEC_COUNT)
    parser.add_argument("--target-workload-count", type=int, default=TARGET_WORKLOAD_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_measured_runner_compatibility_repair(
        public_gate_core_executable_task_specs_path=args.public_gate_core_executable_task_specs,
        public_gate_core_workload_path=args.public_gate_core_workload,
        output_dir=args.output_dir,
        target_spec_count=int(args.target_spec_count),
        target_workload_count=int(args.target_workload_count),
        target_profile_count=int(args.target_profile_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"compatible_spec_count={summary['compatible_spec_count']}")
    print(f"compatible_workload_count={summary['compatible_workload_count']}")
    print(f"profile_count={summary['profile_count']}")
    print(f"measured_runner_validation_failure_count={summary['measured_runner_validation_failure_count']}")
    print(f"env_config_changed_count={summary['env_config_changed_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
