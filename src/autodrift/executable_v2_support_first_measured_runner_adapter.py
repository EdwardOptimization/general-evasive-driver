"""No-rollout adapter for support-first measured controller workloads."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)


DEFAULT_EXECUTABLE_V2_PANEL_SPECS = Path(
    "runs/m1866_executable_v2_support_first_reset_validation_adapter/"
    "support_first_reset_executable_v2_panel_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1874_executable_v2_support_first_measured_runner_adapter_preflight")
TARGET_SUPPORT_FIRST_SPEC_COUNT = 180
TARGET_CONTROLLER_PROFILE_COUNT = 12
TARGET_WORKLOAD_CELL_COUNT = TARGET_SUPPORT_FIRST_SPEC_COUNT * TARGET_CONTROLLER_PROFILE_COUNT
TARGET_ROLE_COUNT = 4
TARGET_ROLE_SURFACE_COUNT = 8
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
REQUIRED_SPEC_FIELDS = (
    "task_source_id",
    "support_first_v2_panel_spec_id",
    "role_panel_id",
    "v2_role_surface_id",
    "surface_variant",
    "scenario_profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "sampled_obstacle_label",
    "diagnostic_only_no_ranking_claim",
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "env_config",
)
REQUIRED_WORKLOAD_FIELDS = (
    "workload_id",
    "support_first_workload_id",
    "task_source_id",
    "support_first_v2_panel_spec_id",
    "controller_profile_name",
    "profile_name",
    "scenario_profile_name",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "task_family",
    "source_edge",
    "window_tag",
    "role_panel_id",
    "v2_role_surface_id",
    "surface_variant",
    "hidden_dynamics_bucket",
    "sampled_obstacle_label",
    "strata",
)
MISSING_FIELDNAMES = ["row_kind", "row_id", "missing_field"]
DUPLICATE_FIELDNAMES = ["row_kind", "row_id", "duplicate_count"]
COUNT_FIELDNAMES = ["group", "count"]


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


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _counter_rows(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    return [{"group": key, "count": int(value)} for key, value in sorted(counts.items())]


def _env_config(row: Mapping[str, Any]) -> dict[str, Any]:
    env_config = deepcopy(dict(row.get("env_config") or {}))
    env_config.setdefault("history_length", 1)
    env_config.setdefault("action_history_mode", "full")
    env_config.setdefault("include_privileged_params", False)
    env_config.setdefault("obstacle_relative_velocity_mode", "zero")
    env_config.setdefault("wheel_observation_mode", "none")
    return env_config


def load_support_first_executable_v2_specs(
    path: Path | str = DEFAULT_EXECUTABLE_V2_PANEL_SPECS,
) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_v2_panel_specs")
    if not isinstance(rows, list):
        raise ValueError("support-first measured adapter input must contain executable_v2_panel_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("v2_panel_spec_id", "")))


def normalize_support_first_spec(row: Mapping[str, Any]) -> dict[str, Any]:
    spec_id = str(row.get("v2_panel_spec_id", row.get("support_first_materialized_v2_panel_spec_id", "")))
    role = str(row.get("role_panel_id", row.get("source_role_semantics", "")))
    surface = str(row.get("surface_variant", row.get("source_family_id", "")))
    hidden = str(row.get("hidden_dynamics_bucket", ""))
    source_family = str(row.get("source_family_id", surface))
    label = str(row.get("v2_task_label", row.get("allowed_labels_metadata_only", "")))
    scenario_profile_name = str(row.get("profile_name", ""))
    scenario_profile_group = str(row.get("profile_group", row.get("source_role_semantics", role)))
    return {
        "task_source_id": spec_id,
        "support_first_v2_panel_spec_id": spec_id,
        "support_first_materialized_v2_panel_spec_id": str(
            row.get("support_first_materialized_v2_panel_spec_id", spec_id)
        ),
        "source_scenario_spec_id": str(row.get("source_scenario_spec_id", "")),
        "role_panel_id": role,
        "v2_role_surface_id": str(row.get("v2_role_surface_id", f"{role}::{surface}")),
        "surface_variant": surface,
        "scenario_profile_name": scenario_profile_name,
        "scenario_profile_group": scenario_profile_group,
        "task_family": role,
        "source_edge": surface,
        "window_tag": hidden,
        "executable_source_family": source_family,
        "env_template_family": source_family,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": str(row.get("road_boundary_bucket", "")),
        "obstacle_timing_bucket": str(row.get("obstacle_timing_bucket", "")),
        "obstacle_lateral_bucket": str(row.get("obstacle_lateral_bucket", "")),
        "sampled_obstacle_label": label,
        "allowed_labels_metadata_only": str(row.get("allowed_labels_metadata_only", label)),
        "diagnostic_only_no_ranking_claim": _bool(row.get("diagnostic_only_no_ranking_claim"), default=True),
        "labels_enter_actor_input": _bool(row.get("labels_enter_actor_input")),
        "v2_ranking_admissible_by_default": _bool(row.get("v2_ranking_admissible_by_default")),
        "env_config": _env_config(row),
    }


def normalize_support_first_specs(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted([normalize_support_first_spec(row) for row in rows], key=lambda row: str(row["task_source_id"]))


def workload_strata(spec: Mapping[str, Any], controller_profile_name: str) -> str:
    items = [
        "support_first_executable_v2",
        f"role_panel_{spec.get('role_panel_id', '')}",
        f"role_surface_{spec.get('v2_role_surface_id', '')}",
        f"surface_variant_{spec.get('surface_variant', '')}",
        f"scenario_profile_{spec.get('scenario_profile_name', '')}",
        f"hidden_dynamics_{spec.get('hidden_dynamics_bucket', '')}",
        f"road_boundary_{spec.get('road_boundary_bucket', '')}",
        f"obstacle_timing_{spec.get('obstacle_timing_bucket', '')}",
        f"obstacle_lateral_{spec.get('obstacle_lateral_bucket', '')}",
        f"controller_profile_{controller_profile_name}",
    ]
    return ";".join(items)


def measured_workload_rows(
    normalized_specs: Iterable[Mapping[str, Any]],
    profile_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in normalized_specs:
        task_source_id = str(spec["task_source_id"])
        for profile in profile_rows:
            controller_profile_name = str(profile["profile_name"])
            workload_id = f"{task_source_id}::{controller_profile_name}"
            rows.append(
                {
                    "workload_id": workload_id,
                    "support_first_workload_id": workload_id,
                    "task_source_id": task_source_id,
                    "support_first_v2_panel_spec_id": str(spec["support_first_v2_panel_spec_id"]),
                    "support_first_materialized_v2_panel_spec_id": str(
                        spec.get("support_first_materialized_v2_panel_spec_id", "")
                    ),
                    "source_scenario_spec_id": str(spec.get("source_scenario_spec_id", "")),
                    "controller_profile_name": controller_profile_name,
                    "profile_name": controller_profile_name,
                    "scenario_profile_name": str(spec["scenario_profile_name"]),
                    "scenario_profile_group": str(spec.get("scenario_profile_group", "")),
                    "profile_config_path": str(profile["config_path"]),
                    "checkpoint_path": str(profile["checkpoint_path"]),
                    "config_exists": _bool(profile.get("config_exists")),
                    "checkpoint_exists": _bool(profile.get("checkpoint_exists")),
                    "task_family": str(spec["task_family"]),
                    "source_edge": str(spec["source_edge"]),
                    "window_tag": str(spec["window_tag"]),
                    "executable_source_family": str(spec["executable_source_family"]),
                    "env_template_family": str(spec["env_template_family"]),
                    "role_panel_id": str(spec["role_panel_id"]),
                    "v2_role_surface_id": str(spec["v2_role_surface_id"]),
                    "surface_variant": str(spec["surface_variant"]),
                    "hidden_dynamics_bucket": str(spec["hidden_dynamics_bucket"]),
                    "road_boundary_bucket": str(spec["road_boundary_bucket"]),
                    "obstacle_timing_bucket": str(spec["obstacle_timing_bucket"]),
                    "obstacle_lateral_bucket": str(spec["obstacle_lateral_bucket"]),
                    "sampled_obstacle_label": str(spec["sampled_obstacle_label"]),
                    "allowed_labels_metadata_only": str(spec["allowed_labels_metadata_only"]),
                    "strata": workload_strata(spec, controller_profile_name),
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return sorted(rows, key=lambda row: str(row["workload_id"]))


def missing_required_field_rows(
    spec_rows: Iterable[Mapping[str, Any]],
    workload_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in spec_rows:
        row_id = str(row.get("task_source_id", ""))
        for field in REQUIRED_SPEC_FIELDS:
            value = row.get(field)
            if value is None or value == "" or (field == "env_config" and not value):
                output.append({"row_kind": "spec", "row_id": row_id, "missing_field": field})
    for row in workload_rows:
        row_id = str(row.get("workload_id", ""))
        for field in REQUIRED_WORKLOAD_FIELDS:
            value = row.get(field)
            if value is None or value == "":
                output.append({"row_kind": "workload", "row_id": row_id, "missing_field": field})
    return output


def duplicate_key_rows(
    spec_rows: Iterable[Mapping[str, Any]],
    workload_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    spec_counts = Counter(str(row.get("task_source_id", "")) for row in spec_rows)
    workload_counts = Counter(str(row.get("workload_id", "")) for row in workload_rows)
    for row_kind, counts in (("spec", spec_counts), ("workload", workload_counts)):
        for row_id, count in sorted(counts.items()):
            if row_id and count > 1:
                output.append({"row_kind": row_kind, "row_id": row_id, "duplicate_count": count})
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "support_first_measured_runner_adapter_ready",
            "admissible": True,
            "reason": "adapter can emit normalized no-rollout measured specs and workload rows",
        },
        {
            "claim": "support_first_measured_workload_materialized",
            "admissible": False,
            "reason": "project materialization is a later execution milestone",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "policy action execution remains blocked until measured runner execution is registered",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "adapter artifacts preserve diagnostics only and do not rank profiles",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "adapter artifacts do not test history necessity",
        },
    ]


def run_support_first_measured_runner_adapter(
    *,
    executable_v2_panel_specs_path: Path | str = DEFAULT_EXECUTABLE_V2_PANEL_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    profile_seed: int = 167400,
    target_support_first_spec_count: int | None = TARGET_SUPPORT_FIRST_SPEC_COUNT,
    target_controller_profile_count: int | None = TARGET_CONTROLLER_PROFILE_COUNT,
    target_workload_cell_count: int | None = TARGET_WORKLOAD_CELL_COUNT,
    target_role_count: int | None = TARGET_ROLE_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    next_blocker: str = "m1874-executable-v2-support-first-measured-runner-adapter-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_specs = load_support_first_executable_v2_specs(executable_v2_panel_specs_path)
    normalized_specs = normalize_support_first_specs(source_specs)
    controller_profiles = profile_artifact_rows(m1674_run_dir=m1674_run_dir, profile_seed=profile_seed)
    workload_rows = measured_workload_rows(normalized_specs, controller_profiles)
    missing_rows = missing_required_field_rows(normalized_specs, workload_rows)
    duplicate_rows = duplicate_key_rows(normalized_specs, workload_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    support_first_spec_count = len(normalized_specs)
    controller_profile_count = len({str(row.get("profile_name", "")) for row in controller_profiles})
    workload_cell_count = len(workload_rows)
    role_count = len({str(row.get("role_panel_id", "")) for row in normalized_specs})
    role_surface_count = len({str(row.get("v2_role_surface_id", "")) for row in normalized_specs})
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in normalized_specs)
    ranking_admissible_by_default_count = sum(
        _bool(row.get("v2_ranking_admissible_by_default")) for row in normalized_specs
    )
    missing_profile_artifact_count = sum(
        1
        for row in controller_profiles
        if not _bool(row.get("config_exists")) or not _bool(row.get("checkpoint_exists"))
    )
    profile_alias_mismatch_count = sum(
        1 for row in workload_rows if str(row.get("profile_name", "")) != str(row.get("controller_profile_name", ""))
    )
    scenario_as_controller_profile_count = sum(
        1
        for row in workload_rows
        if str(row.get("scenario_profile_name", "")) == str(row.get("controller_profile_name", ""))
    )

    result_passes = (
        (target_support_first_spec_count is None or support_first_spec_count == int(target_support_first_spec_count))
        and (
            target_controller_profile_count is None
            or controller_profile_count == int(target_controller_profile_count)
        )
        and (target_workload_cell_count is None or workload_cell_count == int(target_workload_cell_count))
        and (target_role_count is None or role_count == int(target_role_count))
        and (target_role_surface_count is None or role_surface_count == int(target_role_surface_count))
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and missing_profile_artifact_count == 0
        and profile_alias_mismatch_count == 0
        and scenario_as_controller_profile_count == 0
        and not missing_rows
        and not duplicate_rows
        and guardrail_violation_count == 0
    )

    role_surface_counts = _count_by_key(normalized_specs, "v2_role_surface_id")
    controller_profile_counts = _count_by_key(workload_rows, "controller_profile_name")
    scenario_profile_counts = _count_by_key(normalized_specs, "scenario_profile_name")

    write_json(
        output / "support_first_measured_executable_specs.json",
        {
            "generated_at_utc": utc_timestamp(),
            "source_executable_v2_panel_specs_path": str(executable_v2_panel_specs_path),
            "m1674_run_dir": str(m1674_run_dir),
            "profile_seed": int(profile_seed),
            "support_first_measured_executable_specs": normalized_specs,
        },
    )
    write_csv_rows(output / "support_first_measured_executable_specs.csv", normalized_specs)
    write_csv_rows(output / "support_first_measured_workload_matrix.csv", workload_rows)
    write_csv_rows(output / "support_first_role_surface_counts.csv", _counter_rows(role_surface_counts), COUNT_FIELDNAMES)
    write_csv_rows(
        output / "controller_profile_artifact_rows.csv",
        [dict(row) for row in controller_profiles],
    )
    write_csv_rows(
        output / "support_first_measured_missing_field_rows.csv",
        missing_rows,
        MISSING_FIELDNAMES,
    )
    write_csv_rows(
        output / "support_first_measured_duplicate_key_rows.csv",
        duplicate_rows,
        DUPLICATE_FIELDNAMES,
    )
    write_csv_rows(output / "support_first_measured_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "executable_v2_support_first_measured_runner_adapter_pass"
            if result_passes
            else "executable_v2_support_first_measured_runner_adapter_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_v2_panel_specs_path": str(executable_v2_panel_specs_path),
        "m1674_run_dir": str(m1674_run_dir),
        "profile_seed": int(profile_seed),
        "support_first_spec_count": support_first_spec_count,
        "target_support_first_spec_count": target_support_first_spec_count,
        "controller_profile_count": controller_profile_count,
        "target_controller_profile_count": target_controller_profile_count,
        "workload_cell_count": workload_cell_count,
        "target_workload_cell_count": target_workload_cell_count,
        "role_count": role_count,
        "target_role_count": target_role_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "ranking_admissible_by_default_count": ranking_admissible_by_default_count,
        "missing_profile_artifact_count": missing_profile_artifact_count,
        "profile_alias_mismatch_count": profile_alias_mismatch_count,
        "scenario_as_controller_profile_count": scenario_as_controller_profile_count,
        "missing_required_field_count": len(missing_rows),
        "duplicate_key_count": len(duplicate_rows),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "role_counts": _count_by_key(normalized_specs, "role_panel_id"),
        "role_surface_counts": role_surface_counts,
        "controller_profile_counts": controller_profile_counts,
        "scenario_profile_counts": scenario_profile_counts,
        "task_label_counts": _count_by_key(normalized_specs, "sampled_obstacle_label"),
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
            "support_first_measured_executable_specs_json": str(
                output / "support_first_measured_executable_specs.json"
            ),
            "support_first_measured_executable_specs_csv": str(
                output / "support_first_measured_executable_specs.csv"
            ),
            "support_first_measured_workload_matrix": str(output / "support_first_measured_workload_matrix.csv"),
            "support_first_role_surface_counts": str(output / "support_first_role_surface_counts.csv"),
            "controller_profile_artifact_rows": str(output / "controller_profile_artifact_rows.csv"),
            "support_first_measured_missing_field_rows": str(
                output / "support_first_measured_missing_field_rows.csv"
            ),
            "support_first_measured_duplicate_key_rows": str(
                output / "support_first_measured_duplicate_key_rows.csv"
            ),
            "support_first_measured_claim_boundary": str(output / "support_first_measured_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert support-first executable v2 specs into measured controller workload rows without rollout."
    )
    parser.add_argument("--executable-v2-panel-specs", type=Path, default=DEFAULT_EXECUTABLE_V2_PANEL_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--profile-seed", type=int, default=167400)
    parser.add_argument("--target-support-first-spec-count", type=int, default=TARGET_SUPPORT_FIRST_SPEC_COUNT)
    parser.add_argument("--target-controller-profile-count", type=int, default=TARGET_CONTROLLER_PROFILE_COUNT)
    parser.add_argument("--target-workload-cell-count", type=int, default=TARGET_WORKLOAD_CELL_COUNT)
    parser.add_argument("--target-role-count", type=int, default=TARGET_ROLE_COUNT)
    parser.add_argument("--target-role-surface-count", type=int, default=TARGET_ROLE_SURFACE_COUNT)
    parser.add_argument(
        "--next-blocker",
        default="m1874-executable-v2-support-first-measured-runner-adapter-execution-design",
    )
    args = parser.parse_args()

    summary = run_support_first_measured_runner_adapter(
        executable_v2_panel_specs_path=args.executable_v2_panel_specs,
        output_dir=args.output_dir,
        m1674_run_dir=args.m1674_run_dir,
        profile_seed=int(args.profile_seed),
        target_support_first_spec_count=int(args.target_support_first_spec_count),
        target_controller_profile_count=int(args.target_controller_profile_count),
        target_workload_cell_count=int(args.target_workload_cell_count),
        target_role_count=int(args.target_role_count),
        target_role_surface_count=int(args.target_role_surface_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"support_first_spec_count={summary['support_first_spec_count']}")
    print(f"controller_profile_count={summary['controller_profile_count']}")
    print(f"workload_cell_count={summary['workload_cell_count']}")
    print(f"role_surface_count={summary['role_surface_count']}")
    print(f"scenario_as_controller_profile_count={summary['scenario_as_controller_profile_count']}")
    print(f"missing_required_field_count={summary['missing_required_field_count']}")
    print(f"duplicate_key_count={summary['duplicate_key_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
