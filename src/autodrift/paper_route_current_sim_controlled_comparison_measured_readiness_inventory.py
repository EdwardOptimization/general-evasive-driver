"""No-rollout readiness inventory for current-sim measured execution."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json"
)
DEFAULT_WORKLOAD = Path("runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory")
DEFAULT_NEXT_BLOCKER = "m2166-paper-route-current-sim-measured-readiness-inventory-result-audit"
TARGET_SPEC_COUNT = 40
TARGET_WORKLOAD_COUNT = 320
TARGET_PROFILE_COUNT = 8
OLD_CONTROLLED_ROUTING_REQUIRED_FIELDS = (
    "workload_id",
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
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
)
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
WORKLOAD_READINESS_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "profile_name",
    "checkpoint_required_for_measured_execution",
    "checkpoint_path",
    "checkpoint_path_present",
    "checkpoint_path_exists",
    "profile_config_path",
    "profile_config_exists",
    "workload_ready_for_measured_execution",
    "readiness_blockers",
]
PROFILE_READINESS_FIELDNAMES = [
    "profile_name",
    "profile_config_path",
    "profile_config_exists",
    "workload_count",
    "checkpoint_required_count",
    "checkpoint_path_missing_count",
    "checkpoint_path_exists_count",
    "profile_ready_for_measured_execution",
]
RUNNER_SCHEMA_GAP_FIELDNAMES = [
    "runner_name",
    "field",
    "present_in_executable_specs",
    "present_in_workload",
    "compatible_with_current_sim_panel",
    "gap_type",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_executable_task_specs(path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("current-sim measured readiness specs must contain executable_task_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("task_source_id", "")))


def load_workload_rows(path: Path | str = DEFAULT_WORKLOAD) -> list[dict[str, str]]:
    return sorted(read_csv_rows(path), key=lambda row: str(row.get("workload_id", "")))


def workload_readiness_rows(workload_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for workload_row in workload_rows:
        checkpoint_required = _bool_value(workload_row.get("checkpoint_required_for_measured_execution"))
        checkpoint_path = str(workload_row.get("checkpoint_path", "")).strip()
        profile_config_path = str(workload_row.get("profile_config_path", "")).strip()
        blockers: list[str] = []
        if checkpoint_required and not checkpoint_path:
            blockers.append("missing_required_checkpoint_path")
        if checkpoint_path and not Path(checkpoint_path).exists():
            blockers.append("checkpoint_path_not_found")
        if not profile_config_path:
            blockers.append("missing_profile_config_path")
        elif not Path(profile_config_path).exists():
            blockers.append("profile_config_path_not_found")
        rows.append(
            {
                "workload_id": str(workload_row.get("workload_id", "")),
                "task_source_id": str(workload_row.get("task_source_id", "")),
                "profile_name": str(workload_row.get("profile_name", "")),
                "checkpoint_required_for_measured_execution": checkpoint_required,
                "checkpoint_path": checkpoint_path,
                "checkpoint_path_present": bool(checkpoint_path),
                "checkpoint_path_exists": bool(checkpoint_path and Path(checkpoint_path).exists()),
                "profile_config_path": profile_config_path,
                "profile_config_exists": bool(profile_config_path and Path(profile_config_path).exists()),
                "workload_ready_for_measured_execution": not blockers,
                "readiness_blockers": ";".join(blockers),
            }
        )
    return rows


def profile_readiness_rows(workload_rows: Iterable[Mapping[str, Any]], workload_readiness: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows_by_profile: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    workload_by_id = {str(row.get("workload_id", "")): row for row in workload_readiness}
    for workload_row in workload_rows:
        rows_by_profile[str(workload_row.get("profile_name", ""))].append(workload_row)

    output: list[dict[str, Any]] = []
    for profile_name, rows in sorted(rows_by_profile.items()):
        readiness_rows = [workload_by_id.get(str(row.get("workload_id", "")), {}) for row in rows]
        checkpoint_required_count = sum(_bool_value(row.get("checkpoint_required_for_measured_execution")) for row in rows)
        checkpoint_path_missing_count = sum(not bool(str(row.get("checkpoint_path", "")).strip()) for row in rows)
        checkpoint_path_exists_count = sum(_bool_value(row.get("checkpoint_path_exists")) for row in readiness_rows)
        profile_config_path = str(rows[0].get("profile_config_path", "")) if rows else ""
        profile_config_exists = bool(profile_config_path and Path(profile_config_path).exists())
        output.append(
            {
                "profile_name": profile_name,
                "profile_config_path": profile_config_path,
                "profile_config_exists": profile_config_exists,
                "workload_count": len(rows),
                "checkpoint_required_count": int(checkpoint_required_count),
                "checkpoint_path_missing_count": int(checkpoint_path_missing_count),
                "checkpoint_path_exists_count": int(checkpoint_path_exists_count),
                "profile_ready_for_measured_execution": all(
                    _bool_value(row.get("workload_ready_for_measured_execution")) for row in readiness_rows
                ),
            }
        )
    return output


def runner_schema_gap_rows(
    *,
    executable_specs: Iterable[Mapping[str, Any]],
    workload_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    spec_fields: set[str] = set()
    workload_fields: set[str] = set()
    for spec in executable_specs:
        spec_fields.update(str(key) for key in spec.keys())
    for workload_row in workload_rows:
        workload_fields.update(str(key) for key in workload_row.keys())
    rows: list[dict[str, Any]] = []
    for field in OLD_CONTROLLED_ROUTING_REQUIRED_FIELDS:
        present_in_specs = field in spec_fields
        present_in_workload = field in workload_fields
        compatible = present_in_specs or present_in_workload
        rows.append(
            {
                "runner_name": "paper_route_controlled_routing_smoke_measured_runner",
                "field": field,
                "present_in_executable_specs": present_in_specs,
                "present_in_workload": present_in_workload,
                "compatible_with_current_sim_panel": compatible,
                "gap_type": "available" if compatible else "missing_required_runner_field",
            }
        )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "current_sim_measured_readiness_inventory_completed",
            "admissible": True,
            "reason": "no-rollout inventory can state static readiness blockers",
        },
        {
            "claim": "measured_execution_admissible",
            "admissible": False,
            "reason": "checkpoint and runner-schema readiness must be audited and repaired before rollout",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "no policy actions or measured rollout ran",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "readiness inventory is not measured benchmark evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "readiness inventory does not compare controller outcomes",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "readiness inventory does not test history necessity",
        },
    ]


def run_current_sim_measured_readiness_inventory(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_spec_count: int = TARGET_SPEC_COUNT,
    target_workload_count: int = TARGET_WORKLOAD_COUNT,
    target_profile_count: int = TARGET_PROFILE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_executable_task_specs(executable_task_specs_path)
    workload_rows = load_workload_rows(workload_path)
    workload_readiness = workload_readiness_rows(workload_rows)
    profile_readiness = profile_readiness_rows(workload_rows, workload_readiness)
    schema_gaps = runner_schema_gap_rows(executable_specs=specs, workload_rows=workload_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    profile_count = len({str(row.get("profile_name", "")) for row in workload_rows})
    checkpoint_required_count = sum(_bool_value(row.get("checkpoint_required_for_measured_execution")) for row in workload_rows)
    checkpoint_path_missing_count = sum(not bool(str(row.get("checkpoint_path", "")).strip()) for row in workload_rows)
    checkpoint_path_present_count = sum(bool(str(row.get("checkpoint_path", "")).strip()) for row in workload_rows)
    checkpoint_path_exists_count = sum(_bool_value(row.get("checkpoint_path_exists")) for row in workload_readiness)
    workload_ready_count = sum(_bool_value(row.get("workload_ready_for_measured_execution")) for row in workload_readiness)
    profile_ready_count = sum(_bool_value(row.get("profile_ready_for_measured_execution")) for row in profile_readiness)
    old_runner_missing_field_count = sum(
        not _bool_value(row.get("compatible_with_current_sim_panel")) for row in schema_gaps
    )
    count_pass = (
        len(specs) == int(target_spec_count)
        and len(workload_rows) == int(target_workload_count)
        and profile_count == int(target_profile_count)
    )
    result_class = (
        "current_sim_measured_readiness_inventory_complete"
        if count_pass and guardrail_violation_count == 0
        else "current_sim_measured_readiness_inventory_incomplete_or_fail"
    )

    write_csv_rows(output / "workload_readiness_rows.csv", workload_readiness, fieldnames=WORKLOAD_READINESS_FIELDNAMES)
    write_csv_rows(output / "profile_readiness_rows.csv", profile_readiness, fieldnames=PROFILE_READINESS_FIELDNAMES)
    write_csv_rows(output / "runner_schema_gap_rows.csv", schema_gaps, fieldnames=RUNNER_SCHEMA_GAP_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_task_specs_path": str(executable_task_specs_path),
        "workload_path": str(workload_path),
        "input_executable_spec_count": len(specs),
        "target_spec_count": int(target_spec_count),
        "input_workload_count": len(workload_rows),
        "target_workload_count": int(target_workload_count),
        "profile_count": int(profile_count),
        "target_profile_count": int(target_profile_count),
        "count_pass": count_pass,
        "checkpoint_required_workload_count": int(checkpoint_required_count),
        "checkpoint_path_missing_count": int(checkpoint_path_missing_count),
        "checkpoint_path_present_count": int(checkpoint_path_present_count),
        "checkpoint_path_exists_count": int(checkpoint_path_exists_count),
        "workload_ready_count": int(workload_ready_count),
        "profile_ready_count": int(profile_ready_count),
        "profile_counts": _count_by(workload_rows, "profile_name"),
        "task_family_counts": _count_by(workload_rows, "task_family"),
        "old_runner_name": "paper_route_controlled_routing_smoke_measured_runner",
        "old_runner_required_field_count": len(OLD_CONTROLLED_ROUTING_REQUIRED_FIELDS),
        "old_runner_missing_field_count": int(old_runner_missing_field_count),
        "old_runner_compatible_with_current_sim_panel": old_runner_missing_field_count == 0,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
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
            "workload_readiness_rows": str(output / "workload_readiness_rows.csv"),
            "profile_readiness_rows": str(output / "profile_readiness_rows.csv"),
            "runner_schema_gap_rows": str(output / "runner_schema_gap_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2165-paper-route-current-sim-controlled-comparison-measured-readiness-inventory-implementation",
            "status": "completed" if str(result_class).endswith("_complete") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_SPEC_COUNT)
    parser.add_argument("--target-workload-count", type=int, default=TARGET_WORKLOAD_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    summary = run_current_sim_measured_readiness_inventory(
        executable_task_specs_path=args.executable_task_specs,
        workload_path=args.workload,
        output_dir=args.output_dir,
        target_spec_count=int(args.target_spec_count),
        target_workload_count=int(args.target_workload_count),
        target_profile_count=int(args.target_profile_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_executable_spec_count={summary['input_executable_spec_count']}")
    print(f"input_workload_count={summary['input_workload_count']}")
    print(f"profile_count={summary['profile_count']}")
    print(f"checkpoint_path_missing_count={summary['checkpoint_path_missing_count']}")
    print(f"old_runner_missing_field_count={summary['old_runner_missing_field_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
