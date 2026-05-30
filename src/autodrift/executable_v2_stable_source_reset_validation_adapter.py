"""No-reset adapter from stable source materialization to executable v2 reset specs."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_STABLE_MATERIALIZATION_SPECS = Path(
    "runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_specs.json"
)
DEFAULT_STABLE_MATERIALIZATION_MATRIX = Path(
    "runs/m1811_executable_v2_stable_source_materialization/stable_source_materialization_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1814_executable_v2_stable_source_reset_validation_adapter")
STABLE_SURFACE = "stable_avoidance_aes"
PRIMARY_METRIC = "admissible_obstacle_pass_rate"
PRIMARY_METRIC_DIRECTION = "higher_is_better"
ADMISSIBILITY_GATE = "collision_rate_low_and_off_track_rate_low"
TARGET_EXECUTABLE_SPEC_COUNT = 36
TARGET_PROFILE_COUNT = 12
TARGET_MATERIALIZATION_SPEC_COUNT = 3
TARGET_ROLE_SURFACE_COUNT = 1
FORBIDDEN_GUARDRAILS = (
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
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def _read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_stable_materialization_specs(path: Path | str = DEFAULT_STABLE_MATERIALIZATION_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted(
        [dict(row) for row in payload["stable_source_materialization_specs"]],
        key=lambda row: str(row.get("materialized_bounded_panel_spec_id", row.get("bounded_panel_spec_id", ""))),
    )


def load_stable_materialization_matrix(path: Path | str = DEFAULT_STABLE_MATERIALIZATION_MATRIX) -> list[dict[str, Any]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("stable_materialization_workload_id", "")))


def _spec_key(row: Mapping[str, Any]) -> str:
    return str(row.get("materialized_bounded_panel_spec_id", row.get("bounded_panel_spec_id", "")))


def _matrix_spec_key(row: Mapping[str, Any]) -> str:
    return str(row.get("bounded_panel_spec_id", row.get("scenario_spec_id", "")))


def _workload_id(row: Mapping[str, Any]) -> str:
    value = str(row.get("stable_materialization_workload_id", ""))
    if value:
        return value
    return f"{_matrix_spec_key(row)}::{row.get('profile_name', '')}"


def _source_spec_map(specs: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    mapped: dict[str, Mapping[str, Any]] = {}
    for spec in specs:
        key = _spec_key(spec)
        if key:
            mapped[key] = spec
    return mapped


def _executable_row(*, materialized_spec: Mapping[str, Any], matrix_row: Mapping[str, Any]) -> dict[str, Any]:
    label = str(materialized_spec.get("target_v2_task_label", materialized_spec.get("allowed_labels_metadata_only", "")))
    surface = str(materialized_spec.get("v2_role_surface_id", matrix_row.get("v2_role_surface_id", STABLE_SURFACE)))
    profile_name = str(matrix_row.get("profile_name", ""))
    return {
        "v2_panel_spec_id": _workload_id(matrix_row),
        "source_v1_bounded_panel_spec_id": str(
            materialized_spec.get(
                "target_bounded_panel_spec_id",
                materialized_spec.get("source_basis_bounded_panel_spec_id", ""),
            )
        ),
        "source_v1_role_panel_id": str(materialized_spec.get("role_panel_id", surface)),
        "source_scenario_spec_id": str(
            materialized_spec.get(
                "materialized_source_scenario_spec_id",
                matrix_row.get("source_scenario_spec_id", ""),
            )
        ),
        "v2_role_surface_id": surface,
        "role_panel_id": str(materialized_spec.get("role_panel_id", surface)),
        "profile_name": profile_name,
        "profile_config_path": str(matrix_row.get("profile_config_path", "")),
        "checkpoint_path": str(matrix_row.get("checkpoint_path", "")),
        "config_exists": _bool(matrix_row.get("config_exists"), default=False),
        "checkpoint_exists": _bool(matrix_row.get("checkpoint_exists"), default=False),
        "v2_task_label": label,
        "allowed_labels_metadata_only": str(materialized_spec.get("allowed_labels_metadata_only", label)),
        "labels_enter_actor_input": False,
        "hidden_dynamics_bucket": str(materialized_spec.get("hidden_dynamics_bucket", matrix_row.get("hidden_dynamics_bucket", ""))),
        "road_boundary_bucket": str(materialized_spec.get("road_boundary_bucket", matrix_row.get("road_boundary_bucket", ""))),
        "obstacle_timing_bucket": str(materialized_spec.get("obstacle_timing_bucket", matrix_row.get("obstacle_timing_bucket", ""))),
        "obstacle_lateral_bucket": str(
            materialized_spec.get("obstacle_lateral_bucket", matrix_row.get("obstacle_lateral_bucket", ""))
        ),
        "v2_primary_metric": PRIMARY_METRIC,
        "v2_primary_metric_direction": PRIMARY_METRIC_DIRECTION,
        "v2_admissibility_gate": ADMISSIBILITY_GATE,
        "reset_ready_spec": True,
        "diagnostic_only_no_ranking_claim": True,
        "v2_ranking_admissible_by_default": False,
        "reset_validation_required": True,
        "materialized_source_scenario_spec_id": str(materialized_spec.get("materialized_source_scenario_spec_id", "")),
        "materialized_bounded_panel_spec_id": str(materialized_spec.get("materialized_bounded_panel_spec_id", "")),
        "target_bounded_panel_spec_id": str(materialized_spec.get("target_bounded_panel_spec_id", "")),
        "target_source_scenario_spec_id": str(materialized_spec.get("target_source_scenario_spec_id", "")),
        "stable_materialization_spec_id": str(materialized_spec.get("stable_materialization_spec_id", "")),
        "stable_materialization_key": str(materialized_spec.get("stable_materialization_key", "")),
        "stable_materialization_workload_id": _workload_id(matrix_row),
        "materialization_strategy": str(materialized_spec.get("materialization_strategy", "")),
        "sampler_repair_variant_id": str(materialized_spec.get("sampler_repair_variant_id", "")),
        "source_basis_support_status": str(materialized_spec.get("source_basis_support_status", "")),
        "near_candidate_ids": str(materialized_spec.get("near_candidate_ids", "")),
        "profile_controls_preserved": _bool(materialized_spec.get("profile_controls_preserved"), default=True),
        "evaluation_role": str(matrix_row.get("evaluation_role", "")),
        "primary_metric_family": str(matrix_row.get("primary_metric_family", "")),
        "env_config": dict(materialized_spec.get("env_config", {})),
        "measured_execution_admissible": False,
        "controller_family_ranking_admissible": False,
        "environment_reset_scheduled": False,
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
    }


def executable_v2_rows_from_stable_materialization(
    *,
    materialization_specs: list[Mapping[str, Any]],
    materialization_matrix: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    specs_by_key = _source_spec_map(materialization_specs)
    rows: list[dict[str, Any]] = []
    missing_join_rows: list[dict[str, Any]] = []
    workload_counts: Counter[str] = Counter()
    for matrix_row in materialization_matrix:
        workload_counts[_workload_id(matrix_row)] += 1
        source_key = _matrix_spec_key(matrix_row)
        materialized_spec = specs_by_key.get(source_key)
        if materialized_spec is None:
            missing_join_rows.append(
                {
                    "stable_materialization_workload_id": _workload_id(matrix_row),
                    "bounded_panel_spec_id": source_key,
                    "profile_name": str(matrix_row.get("profile_name", "")),
                    "reason": "missing materialized stable source spec for matrix row",
                }
            )
            continue
        rows.append(_executable_row(materialized_spec=materialized_spec, matrix_row=matrix_row))

    duplicate_rows = [
        {"stable_materialization_workload_id": workload_id, "duplicate_count": count}
        for workload_id, count in sorted(workload_counts.items())
        if count > 1
    ]
    return sorted(rows, key=lambda row: str(row["v2_panel_spec_id"])), missing_join_rows, duplicate_rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "targeted_reset_validation_payload_ready",
            "admissible": True,
            "reason": "adapter emits executable_v2_panel_specs-shaped artifacts for later reset-only validation",
        },
        {
            "claim": "reset_feasibility_repaired",
            "admissible": False,
            "reason": "reset has not been run over the converted payload",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "measured execution remains blocked until reset support is observed",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "conversion is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_executable_v2_stable_source_reset_validation_adapter(
    *,
    stable_materialization_specs_path: Path | str = DEFAULT_STABLE_MATERIALIZATION_SPECS,
    stable_materialization_matrix_path: Path | str = DEFAULT_STABLE_MATERIALIZATION_MATRIX,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_executable_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    target_profile_count: int | None = TARGET_PROFILE_COUNT,
    target_materialization_spec_count: int | None = TARGET_MATERIALIZATION_SPEC_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    next_blocker: str = "m1815-executable-v2-stable-source-reset-validation-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    materialization_specs = load_stable_materialization_specs(stable_materialization_specs_path)
    materialization_matrix = load_stable_materialization_matrix(stable_materialization_matrix_path)
    executable_rows, missing_join_rows, duplicate_workload_rows = executable_v2_rows_from_stable_materialization(
        materialization_specs=materialization_specs,
        materialization_matrix=materialization_matrix,
    )

    profile_count = len({str(row.get("profile_name", "")) for row in executable_rows})
    role_surface_count = len({str(row.get("v2_role_surface_id", "")) for row in executable_rows})
    reset_ready_spec_count = sum(_bool(row.get("reset_ready_spec")) for row in executable_rows)
    reset_validation_required_count = sum(_bool(row.get("reset_validation_required")) for row in executable_rows)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in executable_rows)
    ranking_admissible_by_default_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in executable_rows)
    env_config_missing_count = sum(not bool(row.get("env_config")) for row in executable_rows)
    materialization_count_matches = (
        target_materialization_spec_count is None
        or len(materialization_specs) == int(target_materialization_spec_count)
    )
    spec_count_matches = target_executable_spec_count is None or len(executable_rows) == int(target_executable_spec_count)
    profile_count_matches = target_profile_count is None or profile_count == int(target_profile_count)
    role_surface_count_matches = target_role_surface_count is None or role_surface_count == int(target_role_surface_count)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    result_passes = (
        materialization_count_matches
        and spec_count_matches
        and profile_count_matches
        and role_surface_count_matches
        and not missing_join_rows
        and not duplicate_workload_rows
        and reset_ready_spec_count == len(executable_rows)
        and reset_validation_required_count == len(executable_rows)
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and env_config_missing_count == 0
        and guardrail_violation_count == 0
    )

    write_json(
        output / "targeted_reset_executable_v2_panel_specs.json",
        {
            "generated_at_utc": utc_timestamp(),
            "source_stable_materialization_specs_path": str(stable_materialization_specs_path),
            "source_stable_materialization_matrix_path": str(stable_materialization_matrix_path),
            "executable_v2_panel_specs": executable_rows,
        },
    )
    write_csv_rows(output / "targeted_reset_executable_v2_panel_specs.csv", executable_rows)
    write_csv_rows(output / "targeted_reset_validation_matrix.csv", executable_rows)
    write_csv_rows(output / "targeted_reset_missing_join_rows.csv", missing_join_rows)
    write_csv_rows(output / "targeted_reset_duplicate_workload_rows.csv", duplicate_workload_rows)
    write_csv_rows(output / "targeted_reset_validation_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "executable_v2_stable_source_reset_validation_adapter_pass"
            if result_passes
            else "executable_v2_stable_source_reset_validation_adapter_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "stable_materialization_specs_path": str(stable_materialization_specs_path),
        "stable_materialization_matrix_path": str(stable_materialization_matrix_path),
        "input_materialization_spec_count": len(materialization_specs),
        "target_materialization_spec_count": target_materialization_spec_count,
        "input_materialization_matrix_row_count": len(materialization_matrix),
        "targeted_reset_executable_spec_count": len(executable_rows),
        "target_executable_spec_count": target_executable_spec_count,
        "profile_control_count": profile_count,
        "target_profile_count": target_profile_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "reset_ready_spec_count": reset_ready_spec_count,
        "reset_validation_required_count": reset_validation_required_count,
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "ranking_admissible_by_default_count": ranking_admissible_by_default_count,
        "env_config_missing_count": env_config_missing_count,
        "missing_join_count": len(missing_join_rows),
        "duplicate_workload_count": len(duplicate_workload_rows),
        "role_surface_counts": _count_by_key(executable_rows, "v2_role_surface_id"),
        "task_label_counts": _count_by_key(executable_rows, "v2_task_label"),
        "profile_counts": _count_by_key(executable_rows, "profile_name"),
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
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "targeted_reset_executable_v2_panel_specs_json": str(
                output / "targeted_reset_executable_v2_panel_specs.json"
            ),
            "targeted_reset_executable_v2_panel_specs_csv": str(
                output / "targeted_reset_executable_v2_panel_specs.csv"
            ),
            "targeted_reset_validation_matrix": str(output / "targeted_reset_validation_matrix.csv"),
            "targeted_reset_missing_join_rows": str(output / "targeted_reset_missing_join_rows.csv"),
            "targeted_reset_duplicate_workload_rows": str(output / "targeted_reset_duplicate_workload_rows.csv"),
            "targeted_reset_validation_claim_boundary": str(output / "targeted_reset_validation_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert stable source materialization artifacts into executable v2 reset specs without reset."
    )
    parser.add_argument("--stable-materialization-specs", type=Path, default=DEFAULT_STABLE_MATERIALIZATION_SPECS)
    parser.add_argument("--stable-materialization-matrix", type=Path, default=DEFAULT_STABLE_MATERIALIZATION_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-executable-spec-count", type=int, default=TARGET_EXECUTABLE_SPEC_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--target-materialization-spec-count", type=int, default=TARGET_MATERIALIZATION_SPEC_COUNT)
    parser.add_argument("--target-role-surface-count", type=int, default=TARGET_ROLE_SURFACE_COUNT)
    parser.add_argument("--next-blocker", default="m1815-executable-v2-stable-source-reset-validation-execution-design")
    args = parser.parse_args()

    summary = run_executable_v2_stable_source_reset_validation_adapter(
        stable_materialization_specs_path=args.stable_materialization_specs,
        stable_materialization_matrix_path=args.stable_materialization_matrix,
        output_dir=args.output_dir,
        target_executable_spec_count=args.target_executable_spec_count,
        target_profile_count=args.target_profile_count,
        target_materialization_spec_count=args.target_materialization_spec_count,
        target_role_surface_count=args.target_role_surface_count,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"targeted_reset_executable_spec_count={summary['targeted_reset_executable_spec_count']}")
    print(f"profile_control_count={summary['profile_control_count']}")
    print(f"missing_join_count={summary['missing_join_count']}")
    print(f"duplicate_workload_count={summary['duplicate_workload_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
