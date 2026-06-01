"""No-rollout measured-readiness join for current-sim offtrack-support workload."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_PLANNED_WORKLOAD = Path("runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/planned_workload.csv")
DEFAULT_PROFILE_CHECKPOINTS = Path("runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness")
DEFAULT_NEXT_BLOCKER = "m2201-paper-route-current-sim-offtrack-support-measured-readiness-result-audit"
TARGET_WORKLOAD_COUNT = 2304
TARGET_PROFILE_COUNT = 8
EXPECTED_ROWS_PER_PROFILE = 288
CLAIM_FIELDS = (
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
SHORTCUT_FIELDS = (
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
)
MATERIALIZED_WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "repair_candidate_id",
    "repair_axis",
    "repair_split",
    "parent_task_source_id",
    "profile_name",
    "profile_level",
    "profile_config_path",
    "checkpoint_path",
    "checkpoint_exists",
    "checkpoint_required_for_measured_execution",
    "checkpoint_source_profile_name",
    "checkpoint_materialization_mode",
    "training_enabled_for_source_profile",
    "actor_encoder",
    "actor_history_length",
    "env_history_length",
    "observation_dim",
    "input_contract",
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
    "task_family",
    "history_representation",
    "history_window_steps",
    "reset_or_truncated_control",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "training_scheduled",
    "measured_execution_scheduled",
    "profile_specific_tuning",
    *CLAIM_FIELDS,
]
PROFILE_JOIN_FIELDNAMES = [
    "profile_name",
    "checkpoint_path",
    "checkpoint_exists",
    "checkpoint_source_profile_name",
    "checkpoint_materialization_mode",
    "training_enabled",
    "input_contract",
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
    "workload_row_count",
    "join_success",
    "failure_reason",
]
MISSING_FIELDNAMES = ["workload_id", "profile_name", "failure_type", "reason"]
AGGREGATE_FIELDNAMES = ["key", "count"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _aggregate_rows(rows: Iterable[Mapping[str, Any]], key: str) -> list[dict[str, int | str]]:
    return [{"key": name, "count": count} for name, count in _count_by(rows, key).items()]


def _claim_boundary_rows(*, readiness_admissible: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "checkpoint_complete_measured_readiness",
            "admissible": bool(readiness_admissible),
            "reason": "M2200 writes a checkpoint-complete workload without executing policies",
        },
        {"claim": "measured_execution", "admissible": False, "reason": "M2200 does not execute policies"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2200 does not compare outcomes"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2200 does not select a controller"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "M2200 is readiness only"},
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2200 has no measured outcomes"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2200 runs no history intervention"},
    ]


def _shortcut_count(profile_rows: Iterable[Mapping[str, Any]]) -> int:
    return sum(1 for row in profile_rows for field in SHORTCUT_FIELDS if _bool(row.get(field)))


def materialize_measured_readiness(
    *,
    planned_workload: Path | str = DEFAULT_PLANNED_WORKLOAD,
    profile_checkpoints: Path | str = DEFAULT_PROFILE_CHECKPOINTS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    target_workload_count: int = TARGET_WORKLOAD_COUNT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    workload_rows = read_csv_rows(planned_workload)
    profile_rows = read_csv_rows(profile_checkpoints)
    profile_by_name = {str(row.get("profile_name", "")): dict(row) for row in profile_rows}
    materialized_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    workload_counts = Counter(str(row.get("profile_name", "")) for row in workload_rows)

    for row in workload_rows:
        profile_name = str(row.get("profile_name", ""))
        profile = profile_by_name.get(profile_name)
        workload_id = str(row.get("workload_id", ""))
        if profile is None:
            missing_rows.append(
                {
                    "workload_id": workload_id,
                    "profile_name": profile_name,
                    "failure_type": "missing_profile_checkpoint_row",
                    "reason": f"profile checkpoint row not found for {profile_name}",
                }
            )
            continue
        checkpoint_path = str(profile.get("checkpoint_path", ""))
        checkpoint_exists = bool(checkpoint_path) and Path(checkpoint_path).exists()
        if not checkpoint_exists:
            missing_rows.append(
                {
                    "workload_id": workload_id,
                    "profile_name": profile_name,
                    "failure_type": "checkpoint_path_missing",
                    "reason": checkpoint_path,
                }
            )
        materialized_rows.append(
            {
                **row,
                "checkpoint_path": checkpoint_path,
                "checkpoint_exists": checkpoint_exists,
                "checkpoint_source_profile_name": str(profile.get("checkpoint_source_profile_name", profile_name)),
                "checkpoint_materialization_mode": str(profile.get("checkpoint_materialization_mode", "")),
                "training_enabled_for_source_profile": _bool(profile.get("training_enabled")),
                "actor_encoder": str(profile.get("actor_encoder", "")),
                "actor_history_length": str(profile.get("actor_history_length", "")),
                "env_history_length": str(profile.get("env_history_length", "")),
                "observation_dim": str(profile.get("observation_dim", "")),
                "input_contract": str(profile.get("input_contract", "")),
                "uses_hidden_oracle_actor_inputs": _bool(profile.get("uses_hidden_oracle_actor_inputs")),
                "uses_wheel_or_slip_inputs": _bool(profile.get("uses_wheel_or_slip_inputs")),
                "uses_reference_or_ttc_inputs": _bool(profile.get("uses_reference_or_ttc_inputs")),
                "measured_execution_scheduled": False,
                "profile_specific_tuning": _bool(row.get("profile_specific_tuning")),
                "controller_family_ranking_claim_made": False,
                "finite_window_vs_gru_conclusion_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )

    profile_join_rows: list[dict[str, Any]] = []
    for profile_name, profile in sorted(profile_by_name.items()):
        checkpoint_path = str(profile.get("checkpoint_path", ""))
        checkpoint_exists = bool(checkpoint_path) and Path(checkpoint_path).exists()
        shortcut_violation = any(_bool(profile.get(field)) for field in SHORTCUT_FIELDS)
        join_success = checkpoint_exists and not shortcut_violation and int(workload_counts.get(profile_name, 0)) > 0
        reason = ""
        if not checkpoint_exists:
            reason = "checkpoint_path_missing"
        elif shortcut_violation:
            reason = "profile_actor_input_shortcut"
        elif int(workload_counts.get(profile_name, 0)) <= 0:
            reason = "profile_has_no_workload_rows"
        profile_join_rows.append(
            {
                "profile_name": profile_name,
                "checkpoint_path": checkpoint_path,
                "checkpoint_exists": checkpoint_exists,
                "checkpoint_source_profile_name": str(profile.get("checkpoint_source_profile_name", profile_name)),
                "checkpoint_materialization_mode": str(profile.get("checkpoint_materialization_mode", "")),
                "training_enabled": _bool(profile.get("training_enabled")),
                "input_contract": str(profile.get("input_contract", "")),
                "uses_hidden_oracle_actor_inputs": _bool(profile.get("uses_hidden_oracle_actor_inputs")),
                "uses_wheel_or_slip_inputs": _bool(profile.get("uses_wheel_or_slip_inputs")),
                "uses_reference_or_ttc_inputs": _bool(profile.get("uses_reference_or_ttc_inputs")),
                "workload_row_count": int(workload_counts.get(profile_name, 0)),
                "join_success": join_success,
                "failure_reason": reason,
            }
        )

    checkpoint_path_present_count = sum(1 for row in materialized_rows if str(row.get("checkpoint_path", "")).strip())
    checkpoint_path_exists_count = sum(_bool(row.get("checkpoint_exists")) for row in materialized_rows)
    checkpoint_path_missing_count = len(materialized_rows) - checkpoint_path_exists_count
    profile_count = len(set(row.get("profile_name", "") for row in materialized_rows))
    profile_counts = _count_by(materialized_rows, "profile_name")
    rows_per_profile_pass = (
        int(target_workload_count) != TARGET_WORKLOAD_COUNT
        or all(count == EXPECTED_ROWS_PER_PROFILE for count in profile_counts.values())
    )
    l3_online_path = str(profile_by_name.get("L3_online_gru", {}).get("checkpoint_path", ""))
    reset_profile = profile_by_name.get("L3_reset_control", {})
    reset_control_alias_pass = (
        str(reset_profile.get("checkpoint_source_profile_name", "")) == "L3_online_gru"
        and str(reset_profile.get("checkpoint_path", "")) == l3_online_path
    )
    profile_shortcut_violation_count = _shortcut_count(profile_rows)
    profile_specific_tuning_count = sum(1 for row in materialized_rows if _bool(row.get("profile_specific_tuning")))
    claim_violation_count = sum(1 for row in materialized_rows for field in CLAIM_FIELDS if _bool(row.get(field)))
    guardrail_flags = {
        "environment_rollout_started_for_measured_execution": False,
        "policy_action_executed_for_measured_execution": False,
        "measured_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "profile_specific_tuning": bool(profile_specific_tuning_count),
        "profile_actor_input_shortcut": bool(profile_shortcut_violation_count),
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    production_target = int(target_workload_count) == TARGET_WORKLOAD_COUNT
    profile_count_pass = not production_target or profile_count == TARGET_PROFILE_COUNT
    result_pass = (
        len(materialized_rows) == int(target_workload_count)
        and checkpoint_path_exists_count == int(target_workload_count)
        and checkpoint_path_missing_count == 0
        and profile_count_pass
        and rows_per_profile_pass
        and reset_control_alias_pass
        and not missing_rows
        and profile_shortcut_violation_count == 0
        and profile_specific_tuning_count == 0
        and claim_violation_count == 0
        and guardrail_violation_count == 0
    )
    result_class = (
        "current_sim_offtrack_support_measured_readiness_pass"
        if result_pass
        else "current_sim_offtrack_support_measured_readiness_fail"
    )

    write_csv_rows(output / "materialized_workload.csv", materialized_rows, fieldnames=MATERIALIZED_WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "profile_checkpoint_join_rows.csv", profile_join_rows, fieldnames=PROFILE_JOIN_FIELDNAMES)
    write_csv_rows(output / "missing_checkpoint_rows.csv", missing_rows, fieldnames=MISSING_FIELDNAMES)
    write_csv_rows(output / "profile_counts.csv", _aggregate_rows(materialized_rows, "profile_name"), fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "task_family_counts.csv", _aggregate_rows(materialized_rows, "task_family"), fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "repair_split_counts.csv", _aggregate_rows(materialized_rows, "repair_split"), fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(readiness_admissible=result_pass), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "planned_workload": str(planned_workload),
        "profile_checkpoints": str(profile_checkpoints),
        "output_dir": str(output),
        "input_workload_count": len(workload_rows),
        "target_workload_count": int(target_workload_count),
        "materialized_workload_count": len(materialized_rows),
        "profile_checkpoint_row_count": len(profile_rows),
        "profile_count": profile_count,
        "profile_count_pass": profile_count_pass,
        "profile_counts": profile_counts,
        "rows_per_profile_pass": rows_per_profile_pass,
        "checkpoint_path_present_count": checkpoint_path_present_count,
        "checkpoint_path_exists_count": checkpoint_path_exists_count,
        "checkpoint_path_missing_count": checkpoint_path_missing_count,
        "missing_checkpoint_row_count": len(missing_rows),
        "reset_control_alias_pass": reset_control_alias_pass,
        "profile_shortcut_violation_count": profile_shortcut_violation_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "claim_violation_count": claim_violation_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started_for_measured_execution": False,
        "policy_action_executed_for_measured_execution": False,
        "measured_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "materialized_workload": str(output / "materialized_workload.csv"),
            "profile_checkpoint_join_rows": str(output / "profile_checkpoint_join_rows.csv"),
            "missing_checkpoint_rows": str(output / "missing_checkpoint_rows.csv"),
            "profile_counts": str(output / "profile_counts.csv"),
            "task_family_counts": str(output / "task_family_counts.csv"),
            "repair_split_counts": str(output / "repair_split_counts.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2200-paper-route-current-sim-offtrack-support-measured-readiness-implementation",
            "status": "completed" if result_pass else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--planned-workload", type=Path, default=DEFAULT_PLANNED_WORKLOAD)
    parser.add_argument("--profile-checkpoints", type=Path, default=DEFAULT_PROFILE_CHECKPOINTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_measured_readiness(
        planned_workload=args.planned_workload,
        profile_checkpoints=args.profile_checkpoints,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"materialized_workload_count={summary['materialized_workload_count']}")
    print(f"checkpoint_path_exists_count={summary['checkpoint_path_exists_count']}")
    print(f"checkpoint_path_missing_count={summary['checkpoint_path_missing_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
