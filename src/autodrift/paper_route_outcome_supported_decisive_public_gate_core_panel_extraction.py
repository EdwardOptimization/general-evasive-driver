"""No-reset public-gate core panel selector for outcome-supported decisive tasks."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
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
from autodrift.paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction import (
    _bool,
    _count_by,
    _count_by_axis,
    _load_executable_task_specs,
    _read_csv_rows,
    _stable_json,
)
from autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight import (
    METADATA_FIELDS,
    contract_row_for_spec,
    metadata_for_spec,
    metadata_missing_rows,
)


DEFAULT_RESET_VALID_CORE_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2088_paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction/"
    "reset_valid_core_executable_task_specs.json"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight/"
    "reset_rows.csv"
)
DEFAULT_RESET_FAILURE_ROWS = Path(
    "runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight/"
    "reset_failure_rows.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction")
DEFAULT_NEXT_BLOCKER = "m2095-paper-route-outcome-supported-decisive-public-gate-core-panel-extraction-result-audit"
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_public_gate_core_panel_extraction_v0"

TARGET_INPUT_SPEC_COUNT = 238
TARGET_PUBLIC_GATE_CORE_SPEC_COUNT = 96
TARGET_EXCLUDED_SPEC_COUNT = 142
TARGET_DYNAMICS_COUNTS = {
    "actuator_delay": 24,
    "low_mu": 24,
    "mixed_mu": 24,
    "nominal_mu": 24,
}
TARGET_AXIS_COUNT_MIN = 8
TARGET_AXIS_COUNT_MAX = 8

PUBLIC_GATE_CORE_SPEC_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "m2091_reset_success",
    "inclusion_rule",
    "contract_violation_count",
]
EXCLUDED_SPEC_FIELDNAMES = [
    *METADATA_FIELDS,
    "eval_seed",
    "m2091_reset_success",
    "exclusion_reason",
    "contract_violation_count",
]


def _claim_boundary_rows(passes: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "public_gate_core_panel_materialization",
            "admissible": bool(passes),
            "reason": "admissible only if the no-reset selector includes exactly public-gate reset-success rows",
        },
        {
            "claim": "fresh_reset_validity",
            "admissible": False,
            "reason": "M2094 reuses M2091 reset evidence and does not rerun environment reset",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and measured rollouts remain blocked",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "panel extraction is task-quality infrastructure, not controller comparison",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated rows remain smoke proxies until later task-semantics validation",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2094 does not execute controller families or compare architectures",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2094 does not test history necessity",
        },
    ]


def _row_for_spec(
    spec: Mapping[str, Any],
    *,
    reset_by_id: Mapping[str, Mapping[str, Any]],
    reason_key: str,
    reason_value: str,
) -> dict[str, Any]:
    task_id = str(spec.get("task_source_id", ""))
    reset_row = reset_by_id.get(task_id, {})
    contract = contract_row_for_spec(spec)
    return {
        **metadata_for_spec(spec),
        "eval_seed": reset_row.get("eval_seed", ""),
        "m2091_reset_success": bool(_bool(reset_row.get("reset_success"))),
        reason_key: reason_value,
        "contract_violation_count": int(contract.get("contract_violation_count", 0)),
    }


def _public_gate_core_spec_csv_rows(
    specs: Iterable[Mapping[str, Any]],
    reset_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _row_for_spec(
            spec,
            reset_by_id=reset_by_id,
            reason_key="inclusion_rule",
            reason_value="source_split_public_gate_and_m2091_reset_success",
        )
        for spec in specs
    ]


def _excluded_spec_csv_rows(
    specs: Iterable[Mapping[str, Any]],
    reset_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        source_split = str(spec.get("source_split", ""))
        task_id = str(spec.get("task_source_id", ""))
        reset_success = _bool(reset_by_id.get(task_id, {}).get("reset_success"))
        if source_split != "public_gate":
            reason = "source_split_not_public_gate"
        elif not reset_success:
            reason = "m2091_reset_failed"
        else:
            reason = "not_selected"
        rows.append(
            _row_for_spec(
                spec,
                reset_by_id=reset_by_id,
                reason_key="exclusion_reason",
                reason_value=reason,
            )
        )
    return rows


def _min_count(counts: Mapping[str, int]) -> int:
    return int(min(counts.values())) if counts else 0


def _max_count(counts: Mapping[str, int]) -> int:
    return int(max(counts.values())) if counts else 0


def run_public_gate_core_panel_extraction(
    *,
    reset_valid_core_executable_task_specs_path: Path | str = DEFAULT_RESET_VALID_CORE_EXECUTABLE_TASK_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    reset_failure_rows_path: Path | str = DEFAULT_RESET_FAILURE_ROWS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_input_spec_count: int = TARGET_INPUT_SPEC_COUNT,
    target_public_gate_core_spec_count: int = TARGET_PUBLIC_GATE_CORE_SPEC_COUNT,
    target_excluded_spec_count: int = TARGET_EXCLUDED_SPEC_COUNT,
    target_dynamics_counts: Mapping[str, int] | None = None,
    target_axis_count_min: int = TARGET_AXIS_COUNT_MIN,
    target_axis_count_max: int = TARGET_AXIS_COUNT_MAX,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    specs = _load_executable_task_specs(reset_valid_core_executable_task_specs_path)
    reset_rows = sorted(_read_csv_rows(reset_rows_path), key=lambda row: str(row.get("task_source_id", "")))
    reset_failure_rows = sorted(_read_csv_rows(reset_failure_rows_path), key=lambda row: str(row.get("task_source_id", "")))
    specs_by_id = {str(spec.get("task_source_id", "")): spec for spec in specs}
    reset_by_id = {str(row.get("task_source_id", "")): row for row in reset_rows}

    reset_success_ids = {task_id for task_id, row in reset_by_id.items() if _bool(row.get("reset_success"))}
    reset_failure_ids = {str(row.get("task_source_id", "")) for row in reset_failure_rows}
    missing_reset_rows = sorted(set(specs_by_id) - set(reset_by_id))
    unexpected_reset_rows = sorted(set(reset_by_id) - set(specs_by_id))

    public_gate_core_specs = [
        copy.deepcopy(spec)
        for spec in specs
        if str(spec.get("source_split", "")) == "public_gate" and str(spec.get("task_source_id", "")) in reset_success_ids
    ]
    core_by_id = {str(spec.get("task_source_id", "")): spec for spec in public_gate_core_specs}
    excluded_specs = [copy.deepcopy(spec) for spec in specs if str(spec.get("task_source_id", "")) not in core_by_id]

    env_config_changed_count = sum(
        _stable_json(specs_by_id[task_id].get("env_config", {})) != _stable_json(core_by_id[task_id].get("env_config", {}))
        for task_id in core_by_id
    )

    contract_rows = [contract_row_for_spec(spec) for spec in public_gate_core_specs]
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    missing_rows = metadata_missing_rows(public_gate_core_specs)
    forbidden_key_hits = forbidden_key_violations(public_gate_core_specs)
    workload_rows, profile_rows = planned_sentinel_workload_rows(public_gate_core_specs, profile_run_dir=profile_run_dir)
    profile_missing_count = sum(
        (not _bool(row.get("config_exists"))) or (not _bool(row.get("checkpoint_exists")))
        for row in profile_rows
    )

    input_split_counts = _count_by(specs, "source_split")
    core_family_counts = _count_by(public_gate_core_specs, "panel_task_family")
    core_split_counts = _count_by(public_gate_core_specs, "source_split")
    core_axis_counts = _count_by_axis(public_gate_core_specs)
    core_dynamics_counts = _count_by(public_gate_core_specs, "dynamics_band")
    core_source_kind_counts = _count_by(public_gate_core_specs, "source_kind")

    public_gate_total_count = int(input_split_counts.get("public_gate", 0))
    public_gate_included_count = int(core_split_counts.get("public_gate", 0))
    public_gate_excluded_count = sum(1 for spec in excluded_specs if str(spec.get("source_split", "")) == "public_gate")
    public_debug_included_count = int(core_split_counts.get("public_debug", 0))
    public_debug_excluded_count = sum(1 for spec in excluded_specs if str(spec.get("source_split", "")) == "public_debug")
    reset_failure_excluded_count = sum(
        1 for spec in excluded_specs if str(spec.get("task_source_id", "")) in reset_failure_ids
    )

    axis_count_min = _min_count(core_axis_counts)
    axis_count_max = _max_count(core_axis_counts)
    expected_dynamics_counts = dict(TARGET_DYNAMICS_COUNTS if target_dynamics_counts is None else target_dynamics_counts)
    dynamics_counts_match = core_dynamics_counts == expected_dynamics_counts

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_counts_pass = (
        len(specs) == int(target_input_spec_count)
        and len(reset_rows) == int(target_input_spec_count)
        and len(public_gate_core_specs) == int(target_public_gate_core_spec_count)
        and len(excluded_specs) == int(target_excluded_spec_count)
        and public_gate_included_count == int(target_public_gate_core_spec_count)
        and public_gate_total_count == int(target_public_gate_core_spec_count)
    )
    passes = (
        target_counts_pass
        and not missing_reset_rows
        and not unexpected_reset_rows
        and public_gate_excluded_count == 0
        and public_debug_included_count == 0
        and env_config_changed_count == 0
        and contract_violation_count == 0
        and not missing_rows
        and not forbidden_key_hits
        and guardrail_violation_count == 0
        and len(workload_rows) == len(public_gate_core_specs) * TARGET_SENTINEL_PROFILE_COUNT
        and dynamics_counts_match
        and axis_count_min == int(target_axis_count_min)
        and axis_count_max == int(target_axis_count_max)
    )

    artifacts = {
        "summary": str(output / "summary.json"),
        "public_gate_core_executable_task_specs": str(output / "public_gate_core_executable_task_specs.json"),
        "public_gate_core_executable_task_specs_csv": str(output / "public_gate_core_executable_task_specs.csv"),
        "public_gate_core_excluded_rows": str(output / "public_gate_core_excluded_rows.csv"),
        "public_gate_core_planned_sentinel_workload": str(output / "public_gate_core_planned_sentinel_workload.csv"),
        "public_gate_core_distribution_by_family": str(output / "public_gate_core_distribution_by_family.csv"),
        "public_gate_core_distribution_by_split": str(output / "public_gate_core_distribution_by_split.csv"),
        "public_gate_core_distribution_by_axis": str(output / "public_gate_core_distribution_by_axis.csv"),
        "public_gate_core_distribution_by_dynamics_band": str(output / "public_gate_core_distribution_by_dynamics_band.csv"),
        "public_gate_core_distribution_by_source_kind": str(output / "public_gate_core_distribution_by_source_kind.csv"),
        "contract_rows": str(output / "contract_rows.csv"),
        "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
        "profile_artifacts": str(output / "profile_artifacts.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }

    write_json(
        output / "public_gate_core_executable_task_specs.json",
        {
            "protocol": PROTOCOL_NAME,
            "source_executable_task_specs": str(reset_valid_core_executable_task_specs_path),
            "source_reset_rows": str(reset_rows_path),
            "source_reset_failure_rows": str(reset_failure_rows_path),
            "executable_task_specs": public_gate_core_specs,
        },
    )
    write_csv_rows(
        output / "public_gate_core_executable_task_specs.csv",
        _public_gate_core_spec_csv_rows(public_gate_core_specs, reset_by_id),
        PUBLIC_GATE_CORE_SPEC_FIELDNAMES,
    )
    write_csv_rows(
        output / "public_gate_core_excluded_rows.csv",
        _excluded_spec_csv_rows(excluded_specs, reset_by_id),
        EXCLUDED_SPEC_FIELDNAMES,
    )
    write_csv_rows(output / "public_gate_core_planned_sentinel_workload.csv", workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "public_gate_core_distribution_by_family.csv", _aggregate_rows(core_family_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "public_gate_core_distribution_by_split.csv", _aggregate_rows(core_split_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "public_gate_core_distribution_by_axis.csv", _aggregate_rows(core_axis_counts), AGGREGATE_FIELDNAMES)
    write_csv_rows(
        output / "public_gate_core_distribution_by_dynamics_band.csv",
        _aggregate_rows(core_dynamics_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        output / "public_gate_core_distribution_by_source_kind.csv",
        _aggregate_rows(core_source_kind_counts),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(output / "contract_rows.csv", contract_rows)
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(passes), CLAIM_FIELDNAMES)

    summary = {
        "result_class": (
            "outcome_supported_decisive_public_gate_core_panel_extraction_pass"
            if passes
            else "outcome_supported_decisive_public_gate_core_panel_extraction_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "output_dir": str(output),
        "reset_valid_core_executable_task_specs_path": str(reset_valid_core_executable_task_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "reset_failure_rows_path": str(reset_failure_rows_path),
        "input_executable_spec_count": len(specs),
        "input_reset_row_count": len(reset_rows),
        "input_reset_failure_row_count": len(reset_failure_rows),
        "reset_success_row_count": len(reset_success_ids),
        "reset_failure_row_count": len(reset_failure_ids),
        "public_gate_core_executable_spec_count": len(public_gate_core_specs),
        "excluded_spec_count": len(excluded_specs),
        "target_input_spec_count": int(target_input_spec_count),
        "target_public_gate_core_spec_count": int(target_public_gate_core_spec_count),
        "target_excluded_spec_count": int(target_excluded_spec_count),
        "missing_reset_row_count": len(missing_reset_rows),
        "unexpected_reset_row_count": len(unexpected_reset_rows),
        "missing_reset_rows": missing_reset_rows,
        "unexpected_reset_rows": unexpected_reset_rows,
        "public_gate_total_count": public_gate_total_count,
        "public_gate_included_count": public_gate_included_count,
        "public_gate_excluded_count": public_gate_excluded_count,
        "public_debug_included_count": public_debug_included_count,
        "public_debug_excluded_count": public_debug_excluded_count,
        "reset_failure_excluded_count": reset_failure_excluded_count,
        "env_config_changed_count": int(env_config_changed_count),
        "contract_violation_count": int(contract_violation_count),
        "metadata_missing_count": len(missing_rows),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "profile_missing_count": int(profile_missing_count),
        "target_sentinel_profile_count": TARGET_SENTINEL_PROFILE_COUNT,
        "planned_sentinel_workload_count": len(workload_rows),
        "core_family_counts": core_family_counts,
        "core_split_counts": core_split_counts,
        "core_axis_counts": core_axis_counts,
        "axis_count_min": axis_count_min,
        "axis_count_max": axis_count_max,
        "target_axis_count_min": int(target_axis_count_min),
        "target_axis_count_max": int(target_axis_count_max),
        "core_dynamics_counts": core_dynamics_counts,
        "target_dynamics_counts": expected_dynamics_counts,
        "dynamics_counts_match": bool(dynamics_counts_match),
        "core_source_kind_counts": core_source_kind_counts,
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
    parser.add_argument(
        "--reset-valid-core-executable-task-specs",
        type=Path,
        default=DEFAULT_RESET_VALID_CORE_EXECUTABLE_TASK_SPECS,
    )
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--reset-failure-rows", type=Path, default=DEFAULT_RESET_FAILURE_ROWS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-input-spec-count", type=int, default=TARGET_INPUT_SPEC_COUNT)
    parser.add_argument("--target-public-gate-core-spec-count", type=int, default=TARGET_PUBLIC_GATE_CORE_SPEC_COUNT)
    parser.add_argument("--target-excluded-spec-count", type=int, default=TARGET_EXCLUDED_SPEC_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_public_gate_core_panel_extraction(
        reset_valid_core_executable_task_specs_path=args.reset_valid_core_executable_task_specs,
        reset_rows_path=args.reset_rows,
        reset_failure_rows_path=args.reset_failure_rows,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        target_input_spec_count=int(args.target_input_spec_count),
        target_public_gate_core_spec_count=int(args.target_public_gate_core_spec_count),
        target_excluded_spec_count=int(args.target_excluded_spec_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_executable_spec_count={summary['input_executable_spec_count']}")
    print(f"public_gate_core_executable_spec_count={summary['public_gate_core_executable_spec_count']}")
    print(f"excluded_spec_count={summary['excluded_spec_count']}")
    print(f"public_gate_included_count={summary['public_gate_included_count']}")
    print(f"public_debug_included_count={summary['public_debug_included_count']}")
    print(f"env_config_changed_count={summary['env_config_changed_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
