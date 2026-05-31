"""No-reset reduced-panel selector for outcome-supported decisive reset-valid rows."""

from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight import (
    AGGREGATE_FIELDNAMES,
    CLAIM_FIELDNAMES,
    PROFILE_FIELDNAMES,
    TARGET_SENTINEL_PROFILE_COUNT,
    WORKLOAD_FIELDNAMES,
    _aggregate_rows,
    _guardrail_flags,
    planned_sentinel_workload_rows,
)
from autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight import (
    METADATA_FIELDS,
    RESET_FIELDNAMES,
    contract_row_for_spec,
    metadata_for_spec,
    metadata_missing_rows,
)
from autodrift.paper_route_outcome_supported_decisive_task_candidates import DIFFICULTY_AXES


DEFAULT_DENSITY_AWARE_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2082_paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight/"
    "density_aware_repaired_executable_task_specs.json"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/"
    "reset_rows.csv"
)
DEFAULT_RESET_FAILURE_ROWS = Path(
    "runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight/"
    "reset_failure_rows.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2088_paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction")
DEFAULT_NEXT_BLOCKER = "m2089-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-result-audit"
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction_v0"

TARGET_INPUT_SPEC_COUNT = 240
TARGET_REDUCED_SPEC_COUNT = 238
TARGET_EXCLUDED_SPEC_COUNT = 2
TARGET_PUBLIC_GATE_PRESERVED_COUNT = 96

REDUCED_SPEC_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "m2085_reset_success",
    "contract_violation_count",
]


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _axis_key(row: Mapping[str, Any]) -> str:
    return "|".join(str(row.get(axis, "")) for axis in DIFFICULTY_AXES)


def _count_by_axis(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(_axis_key(row) for row in rows).items()))


def _coverage_loss_count(original_counts: Mapping[str, int], reduced_counts: Mapping[str, int]) -> int:
    keys = set(original_counts) | set(reduced_counts)
    return int(sum(max(0, int(original_counts.get(key, 0)) - int(reduced_counts.get(key, 0))) for key in keys))


def _load_executable_task_specs(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task spec payload must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def _claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "reset_valid_core_panel_materialization",
            "admissible": bool(passes),
            "reason": "admissible only if the no-reset reduction preserves public-gate rows and claim guards",
        },
        {
            "claim": "fresh_reset_validity",
            "admissible": False,
            "reason": "the reduced panel reuses M2085 reset evidence and does not rerun reset",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and measured rollout remain blocked",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "panel reduction is task-quality infrastructure, not controller comparison",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated rows remain smoke proxies until later task-semantics validation",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "panel reduction does not test history necessity",
        },
    ]


def _reduced_spec_csv_rows(specs: Iterable[Mapping[str, Any]], reset_by_id: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        task_id = str(spec.get("task_source_id", ""))
        reset_row = reset_by_id.get(task_id, {})
        contract = contract_row_for_spec(spec)
        rows.append(
            {
                **metadata_for_spec(spec),
                "eval_seed": reset_row.get("eval_seed", ""),
                "m2085_reset_success": bool(_bool(reset_row.get("reset_success"))),
                "contract_violation_count": int(contract.get("contract_violation_count", 0)),
            }
        )
    return rows


def run_reset_valid_core_panel_reduction(
    *,
    density_aware_executable_task_specs_path: Path | str = DEFAULT_DENSITY_AWARE_EXECUTABLE_TASK_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    reset_failure_rows_path: Path | str = DEFAULT_RESET_FAILURE_ROWS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_input_spec_count: int = TARGET_INPUT_SPEC_COUNT,
    target_reduced_spec_count: int = TARGET_REDUCED_SPEC_COUNT,
    target_excluded_spec_count: int = TARGET_EXCLUDED_SPEC_COUNT,
    target_public_gate_preserved_count: int = TARGET_PUBLIC_GATE_PRESERVED_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    specs = _load_executable_task_specs(density_aware_executable_task_specs_path)
    reset_rows = sorted(_read_csv_rows(reset_rows_path), key=lambda row: str(row.get("task_source_id", "")))
    reset_failure_rows = sorted(_read_csv_rows(reset_failure_rows_path), key=lambda row: str(row.get("task_source_id", "")))
    specs_by_id = {str(spec.get("task_source_id", "")): spec for spec in specs}
    reset_by_id = {str(row.get("task_source_id", "")): row for row in reset_rows}

    reset_success_ids = {task_id for task_id, row in reset_by_id.items() if _bool(row.get("reset_success"))}
    reset_failure_ids = {str(row.get("task_source_id", "")) for row in reset_failure_rows}
    missing_reset_rows = sorted(set(specs_by_id) - set(reset_by_id))
    unexpected_reset_rows = sorted(set(reset_by_id) - set(specs_by_id))

    reduced_specs = [copy.deepcopy(spec) for spec in specs if str(spec.get("task_source_id", "")) in reset_success_ids]
    excluded_specs = [copy.deepcopy(specs_by_id[task_id]) for task_id in sorted(reset_failure_ids) if task_id in specs_by_id]
    reduced_by_id = {str(spec.get("task_source_id", "")): spec for spec in reduced_specs}
    env_config_changed_count = sum(
        _stable_json(specs_by_id[task_id].get("env_config", {})) != _stable_json(reduced_by_id[task_id].get("env_config", {}))
        for task_id in reduced_by_id
    )

    contract_rows = [contract_row_for_spec(spec) for spec in reduced_specs]
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    missing_rows = metadata_missing_rows(reduced_specs)
    forbidden_key_hits = forbidden_key_violations(reduced_specs)
    workload_rows, profile_rows = planned_sentinel_workload_rows(reduced_specs, profile_run_dir=profile_run_dir)
    profile_missing_count = sum(
        (not _bool(row.get("config_exists"))) or (not _bool(row.get("checkpoint_exists")))
        for row in profile_rows
    )

    original_family_counts = _count_by(specs, "panel_task_family")
    reduced_family_counts = _count_by(reduced_specs, "panel_task_family")
    original_split_counts = _count_by(specs, "source_split")
    reduced_split_counts = _count_by(reduced_specs, "source_split")
    original_dynamics_counts = _count_by(specs, "dynamics_band")
    reduced_dynamics_counts = _count_by(reduced_specs, "dynamics_band")
    original_source_kind_counts = _count_by(specs, "source_kind")
    reduced_source_kind_counts = _count_by(reduced_specs, "source_kind")
    original_axis_counts = _count_by_axis(specs)
    reduced_axis_counts = _count_by_axis(reduced_specs)

    public_gate_total_count = int(original_split_counts.get("public_gate", 0))
    public_gate_preserved_count = int(reduced_split_counts.get("public_gate", 0))
    public_gate_excluded_count = public_gate_total_count - public_gate_preserved_count
    public_debug_excluded_count = int(original_split_counts.get("public_debug", 0)) - int(reduced_split_counts.get("public_debug", 0))
    family_coverage_loss_count = _coverage_loss_count(original_family_counts, reduced_family_counts)
    axis_coverage_loss_count = _coverage_loss_count(original_axis_counts, reduced_axis_counts)
    dynamics_coverage_loss_count = _coverage_loss_count(original_dynamics_counts, reduced_dynamics_counts)
    source_kind_coverage_loss_count = _coverage_loss_count(original_source_kind_counts, reduced_source_kind_counts)

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_counts_pass = (
        len(specs) == int(target_input_spec_count)
        and len(reset_rows) == int(target_input_spec_count)
        and len(reduced_specs) == int(target_reduced_spec_count)
        and len(excluded_specs) == int(target_excluded_spec_count)
        and public_gate_preserved_count == int(target_public_gate_preserved_count)
    )
    passes = (
        target_counts_pass
        and not missing_reset_rows
        and not unexpected_reset_rows
        and len(reset_failure_ids) == int(target_excluded_spec_count)
        and public_gate_excluded_count == 0
        and env_config_changed_count == 0
        and contract_violation_count == 0
        and not missing_rows
        and not forbidden_key_hits
        and guardrail_violation_count == 0
    )

    artifacts = {
        "summary": str(output / "summary.json"),
        "reset_valid_core_executable_task_specs": str(output / "reset_valid_core_executable_task_specs.json"),
        "reset_valid_core_executable_task_specs_csv": str(output / "reset_valid_core_executable_task_specs.csv"),
        "reset_valid_core_excluded_rows": str(output / "reset_valid_core_excluded_rows.csv"),
        "reset_valid_core_planned_sentinel_workload": str(output / "reset_valid_core_planned_sentinel_workload.csv"),
        "reset_valid_core_distribution_by_family": str(output / "reset_valid_core_distribution_by_family.csv"),
        "reset_valid_core_distribution_by_split": str(output / "reset_valid_core_distribution_by_split.csv"),
        "reset_valid_core_distribution_by_dynamics_band": str(output / "reset_valid_core_distribution_by_dynamics_band.csv"),
        "reset_valid_core_distribution_by_source_kind": str(output / "reset_valid_core_distribution_by_source_kind.csv"),
        "reset_valid_core_distribution_by_axis": str(output / "reset_valid_core_distribution_by_axis.csv"),
        "contract_rows": str(output / "contract_rows.csv"),
        "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
        "profile_artifacts": str(output / "profile_artifacts.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }

    write_json(
        output / "reset_valid_core_executable_task_specs.json",
        {
            "protocol": PROTOCOL_NAME,
            "source_executable_task_specs": str(density_aware_executable_task_specs_path),
            "source_reset_rows": str(reset_rows_path),
            "source_reset_failure_rows": str(reset_failure_rows_path),
            "executable_task_specs": reduced_specs,
        },
    )
    write_csv_rows(
        output / "reset_valid_core_executable_task_specs.csv",
        _reduced_spec_csv_rows(reduced_specs, reset_by_id),
        REDUCED_SPEC_FIELDNAMES,
    )
    write_csv_rows(output / "reset_valid_core_excluded_rows.csv", reset_failure_rows, RESET_FIELDNAMES)
    write_csv_rows(output / "reset_valid_core_planned_sentinel_workload.csv", workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "reset_valid_core_distribution_by_family.csv", _aggregate_rows(reduced_family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "reset_valid_core_distribution_by_split.csv", _aggregate_rows(reduced_split_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(
        output / "reset_valid_core_distribution_by_dynamics_band.csv",
        _aggregate_rows(reduced_dynamics_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        output / "reset_valid_core_distribution_by_source_kind.csv",
        _aggregate_rows(reduced_source_kind_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(output / "reset_valid_core_distribution_by_axis.csv", _aggregate_rows(reduced_axis_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "contract_rows.csv", contract_rows)
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "outcome_supported_decisive_reset_valid_core_panel_reduction_pass"
            if passes
            else "outcome_supported_decisive_reset_valid_core_panel_reduction_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "density_aware_executable_task_specs_path": str(density_aware_executable_task_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "reset_failure_rows_path": str(reset_failure_rows_path),
        "input_executable_spec_count": len(specs),
        "input_reset_row_count": len(reset_rows),
        "reset_success_row_count": len(reset_success_ids),
        "reset_failure_row_count": len(reset_failure_ids),
        "reduced_executable_spec_count": len(reduced_specs),
        "excluded_spec_count": len(excluded_specs),
        "target_input_spec_count": int(target_input_spec_count),
        "target_reduced_spec_count": int(target_reduced_spec_count),
        "target_excluded_spec_count": int(target_excluded_spec_count),
        "missing_reset_row_count": len(missing_reset_rows),
        "unexpected_reset_row_count": len(unexpected_reset_rows),
        "missing_reset_rows": missing_reset_rows,
        "unexpected_reset_rows": unexpected_reset_rows,
        "public_gate_total_count": public_gate_total_count,
        "public_gate_preserved_count": public_gate_preserved_count,
        "target_public_gate_preserved_count": int(target_public_gate_preserved_count),
        "public_gate_excluded_count": public_gate_excluded_count,
        "public_debug_excluded_count": public_debug_excluded_count,
        "env_config_changed_count": int(env_config_changed_count),
        "contract_violation_count": int(contract_violation_count),
        "metadata_missing_count": len(missing_rows),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "profile_missing_count": int(profile_missing_count),
        "target_sentinel_profile_count": TARGET_SENTINEL_PROFILE_COUNT,
        "planned_sentinel_workload_count": len(workload_rows),
        "original_family_counts": original_family_counts,
        "reduced_family_counts": reduced_family_counts,
        "family_coverage_loss_count": family_coverage_loss_count,
        "original_split_counts": original_split_counts,
        "reduced_split_counts": reduced_split_counts,
        "original_dynamics_counts": original_dynamics_counts,
        "reduced_dynamics_counts": reduced_dynamics_counts,
        "dynamics_coverage_loss_count": dynamics_coverage_loss_count,
        "original_source_kind_counts": original_source_kind_counts,
        "reduced_source_kind_counts": reduced_source_kind_counts,
        "source_kind_coverage_loss_count": source_kind_coverage_loss_count,
        "original_axis_counts": original_axis_counts,
        "reduced_axis_counts": reduced_axis_counts,
        "axis_coverage_loss_count": axis_coverage_loss_count,
        "target_counts_pass": bool(target_counts_pass),
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
    parser.add_argument("--density-aware-executable-task-specs", type=Path, default=DEFAULT_DENSITY_AWARE_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--reset-failure-rows", type=Path, default=DEFAULT_RESET_FAILURE_ROWS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-input-spec-count", type=int, default=TARGET_INPUT_SPEC_COUNT)
    parser.add_argument("--target-reduced-spec-count", type=int, default=TARGET_REDUCED_SPEC_COUNT)
    parser.add_argument("--target-excluded-spec-count", type=int, default=TARGET_EXCLUDED_SPEC_COUNT)
    parser.add_argument("--target-public-gate-preserved-count", type=int, default=TARGET_PUBLIC_GATE_PRESERVED_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_reset_valid_core_panel_reduction(
        density_aware_executable_task_specs_path=args.density_aware_executable_task_specs,
        reset_rows_path=args.reset_rows,
        reset_failure_rows_path=args.reset_failure_rows,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        target_input_spec_count=int(args.target_input_spec_count),
        target_reduced_spec_count=int(args.target_reduced_spec_count),
        target_excluded_spec_count=int(args.target_excluded_spec_count),
        target_public_gate_preserved_count=int(args.target_public_gate_preserved_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_executable_spec_count={summary['input_executable_spec_count']}")
    print(f"reduced_executable_spec_count={summary['reduced_executable_spec_count']}")
    print(f"excluded_spec_count={summary['excluded_spec_count']}")
    print(f"public_gate_preserved_count={summary['public_gate_preserved_count']}")
    print(f"env_config_changed_count={summary['env_config_changed_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
