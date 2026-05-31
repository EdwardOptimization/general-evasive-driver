"""No-reset calibrated materialization preflight for M1956 selected sources."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.executable_v2_task_quality_scenario_redesign_materialization_preflight import (
    env_config_for_materialized_source,
)


DEFAULT_SUBSET_CONFIG = Path("configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json")
DEFAULT_REPAIR_ACCEPTED_CELLS = Path(
    "runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight")
DEFAULT_NEXT_BLOCKER = "m1959-executable-v2-task-quality-calibrated-reset-validation-command-design"
PROTOCOL_NAME = "task_quality_calibrated_materialization_preflight_v0"

ROLE_STABLE_AEB = "stable_aeb"
ROLE_STABLE_AES_ONLY = "stable_aes_only"
ROLE_DRIFT_REQUIRED = "drift_required_recovery"
ROLE_UNAVOIDABLE = "unavoidable_mitigation"
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


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _source_id(row: Mapping[str, Any]) -> str:
    return str(row.get("candidate_source_id", ""))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_counts(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts["|".join(str(row.get(key, "")) for key in keys)] += 1
    return dict(sorted(counts.items()))


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(str(value) for value in values)
    return sum(1 for value, count in counts.items() if value and count > 1)


def _accepted_cells_by_source(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not _bool_value(row.get("accepted")):
            continue
        grouped[str(row.get("candidate_source_id", ""))].append(dict(row))
    return grouped


def representative_cell_sort_key(role: str, row: Mapping[str, Any]) -> tuple[float, float, float, str]:
    threshold = _float_value(row.get("threshold_score"))
    distance = _float_value(row.get("obstacle_distance"))
    half_width = _float_value(row.get("obstacle_half_width"))
    source_id = str(row.get("candidate_source_id", ""))
    if role == ROLE_STABLE_AEB:
        return (-threshold, -distance, half_width, source_id)
    if role in {ROLE_STABLE_AES_ONLY, ROLE_DRIFT_REQUIRED}:
        return (threshold, distance, -half_width, source_id)
    if role == ROLE_UNAVOIDABLE:
        return (distance, -half_width, threshold, source_id)
    return (threshold, distance, -half_width, source_id)


def representative_cell_for_source(
    source: Mapping[str, Any],
    accepted_cells: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str]:
    source_id = _source_id(source)
    cells = list(accepted_cells.get(source_id, []))
    if not cells:
        return None, "missing_accepted_cell"
    role = str(source.get("source_role_semantics", ""))
    selected = sorted(cells, key=lambda row: representative_cell_sort_key(role, row))[0]
    if role == ROLE_STABLE_AEB:
        rule = "stable_aeb_max_threshold_then_farther_distance"
    elif role in {ROLE_STABLE_AES_ONLY, ROLE_DRIFT_REQUIRED}:
        rule = "boundary_min_threshold_then_closer_wider"
    elif role == ROLE_UNAVOIDABLE:
        rule = "mitigation_closer_wider_then_threshold"
    else:
        rule = "default_min_threshold"
    return dict(selected), rule


def _contract_checks(env_config: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "history_length_is_one": int(env_config.get("history_length", 0)) == 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool_value(env_config.get("include_privileged_params")),
        "wheel_observation_mode_none": str(env_config.get("wheel_observation_mode", "")) == "none",
        "obstacle_relative_velocity_mode_zero": str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero",
    }


def materialize_executable_spec(
    *,
    source: Mapping[str, Any],
    cell: Mapping[str, Any],
    representative_cell_rule: str,
    index: int,
) -> dict[str, Any]:
    env_config = env_config_for_materialized_source(template=source, cell=cell)
    checks = _contract_checks(env_config)
    source_id = _source_id(source)
    task_source_id = f"tqcm_exec_v0_{index:04d}_{source_id}"
    return {
        "task_source_id": task_source_id,
        "candidate_source_id": source_id,
        "repair_candidate_id": str(source.get("repair_candidate_id", "")),
        "repair_source_kind": str(source.get("repair_source_kind", "")),
        "selection_quota_name": str(source.get("selection_quota_name", "")),
        "source_role_semantics": str(source.get("source_role_semantics", "")),
        "parent_feasibility_tier_id": str(source.get("parent_feasibility_tier_id", "")),
        "parent_surface_variant": str(source.get("parent_surface_variant", "")),
        "normalized_surface_variant": str(source.get("normalized_surface_variant", "")),
        "source_split": str(source.get("source_split", "")),
        "source_v1_bounded_panel_spec_id": str(source.get("source_v1_bounded_panel_spec_id", "")),
        "source_scenario_spec_id": str(source.get("source_scenario_spec_id", "")),
        "speed_ref": _float_value(source.get("speed_ref")),
        "mu": _float_value(source.get("mu")),
        "friction_step_enabled": _bool_value(source.get("friction_step_enabled")),
        "friction_step_at": _int_value(source.get("friction_step_at")),
        "obstacle_distance": _float_value(cell.get("obstacle_distance")),
        "obstacle_half_width": _float_value(cell.get("obstacle_half_width")),
        "sampled_obstacle_label": str(cell.get("label", "")),
        "threshold_score": _float_value(cell.get("threshold_score")),
        "time_to_obstacle": _float_value(cell.get("time_to_obstacle")),
        "time_after_friction_step": _float_value(cell.get("time_after_friction_step")),
        "base_geometry_source": str(source.get("base_geometry_source", "")),
        "post_obstacle_track_width": _float_value(source.get("post_obstacle_track_width")),
        "representative_cell_rule": representative_cell_rule,
        "contract_checks": checks,
        "contract_violation_count": int(sum(1 for value in checks.values() if not bool(value))),
        "diagnostic_only_no_ranking_claim": True,
        "env_config": env_config,
    }


def executable_spec_csv_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    checks = dict(spec.get("contract_checks", {}))
    return {
        "task_source_id": spec.get("task_source_id", ""),
        "candidate_source_id": spec.get("candidate_source_id", ""),
        "repair_candidate_id": spec.get("repair_candidate_id", ""),
        "repair_source_kind": spec.get("repair_source_kind", ""),
        "selection_quota_name": spec.get("selection_quota_name", ""),
        "source_role_semantics": spec.get("source_role_semantics", ""),
        "parent_feasibility_tier_id": spec.get("parent_feasibility_tier_id", ""),
        "parent_surface_variant": spec.get("parent_surface_variant", ""),
        "normalized_surface_variant": spec.get("normalized_surface_variant", ""),
        "source_split": spec.get("source_split", ""),
        "speed_ref": spec.get("speed_ref", 0.0),
        "mu": spec.get("mu", 0.0),
        "friction_step_enabled": spec.get("friction_step_enabled", False),
        "friction_step_at": spec.get("friction_step_at", 0),
        "obstacle_distance": spec.get("obstacle_distance", 0.0),
        "obstacle_half_width": spec.get("obstacle_half_width", 0.0),
        "sampled_obstacle_label": spec.get("sampled_obstacle_label", ""),
        "threshold_score": spec.get("threshold_score", 0.0),
        "representative_cell_rule": spec.get("representative_cell_rule", ""),
        "contract_violation_count": spec.get("contract_violation_count", 0),
        **checks,
    }


def planned_workload_rows(
    executable_specs: list[Mapping[str, Any]],
    *,
    profile_run_dir: Path | str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profile_rows = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in executable_specs:
        for profile in profile_rows:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "candidate_source_id": spec["candidate_source_id"],
                    "repair_source_kind": spec["repair_source_kind"],
                    "selection_quota_name": spec["selection_quota_name"],
                    "source_role_semantics": spec["source_role_semantics"],
                    "parent_feasibility_tier_id": spec["parent_feasibility_tier_id"],
                    "normalized_surface_variant": spec["normalized_surface_variant"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "config_exists": profile["config_exists"],
                    "checkpoint_exists": profile["checkpoint_exists"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                }
            )
    return rows, profile_rows


def _aggregate_rows(
    executable_specs: list[Mapping[str, Any]],
    keys: tuple[str, ...],
    *,
    count_name: str,
) -> list[dict[str, Any]]:
    counts = Counter(tuple(str(row.get(key, "")) for key in keys) for row in executable_specs)
    rows: list[dict[str, Any]] = []
    for values, count in sorted(counts.items()):
        row = {key: value for key, value in zip(keys, values)}
        row[count_name] = int(count)
        rows.append(row)
    return rows


def _claim_boundary_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim": "calibrated_materialization_preflight_artifact",
            "supported": summary.get("result_class") == "task_quality_calibrated_materialization_preflight_pass",
            "reason": "M1958 creates no-reset executable specs and planned workload artifacts",
        },
        {
            "claim": "reset_validity",
            "supported": False,
            "reason": "M1958 does not run environment reset",
        },
        {
            "claim": "measured_execution_success",
            "supported": False,
            "reason": "M1958 does not run rollout or measured execution",
        },
        {
            "claim": "controller_family_ranking",
            "supported": False,
            "reason": "M1958 writes a planned workload only",
        },
        {
            "claim": "paper_level_evidence",
            "supported": False,
            "reason": "M1958 is a no-reset preflight milestone",
        },
        {
            "claim": "level3_self_identification",
            "supported": False,
            "reason": "M1958 does not test history necessity",
        },
    ]


def run_calibrated_materialization_preflight(
    *,
    subset_config_path: Path | str = DEFAULT_SUBSET_CONFIG,
    repair_accepted_cells_path: Path | str = DEFAULT_REPAIR_ACCEPTED_CELLS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    subset_payload = read_json(subset_config_path)
    selected_sources = [dict(row) for row in subset_payload.get("selected_sources", [])]
    accepted_rows = [dict(row) for row in read_csv_rows(repair_accepted_cells_path)]
    accepted_by_source = _accepted_cells_by_source(accepted_rows)

    executable_specs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, source in enumerate(selected_sources):
        try:
            cell, rule = representative_cell_for_source(source, accepted_by_source)
            if cell is None:
                failures.append(
                    {
                        "candidate_source_id": _source_id(source),
                        "failure_reason": rule,
                    }
                )
                continue
            executable_specs.append(
                materialize_executable_spec(
                    source=source,
                    cell=cell,
                    representative_cell_rule=rule,
                    index=index,
                )
            )
        except Exception as exc:  # noqa: BLE001 - preflight must record blockers without partial execution.
            failures.append(
                {
                    "candidate_source_id": _source_id(source),
                    "failure_reason": "materialization_exception",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )

    workload_rows, profile_rows = planned_workload_rows(executable_specs, profile_run_dir=profile_run_dir)
    forbidden_key_hits = forbidden_key_violations(executable_specs)
    contract_violation_count = sum(_int_value(spec.get("contract_violation_count")) for spec in executable_specs)
    missing_profile_artifact_count = sum(
        1 for row in profile_rows if not bool(row["config_exists"]) or not bool(row["checkpoint_exists"])
    )
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    source_kind_counts = Counter(str(spec.get("repair_source_kind", "")) for spec in executable_specs)
    role_surface_counts = _group_counts(
        executable_specs,
        ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
    )
    source_kind_quota_pass = dict(sorted(source_kind_counts.items())) == EXPECTED_SOURCE_KIND_COUNTS
    role_surface_quota_pass = role_surface_counts == EXPECTED_ROLE_SURFACE_COUNTS
    duplicate_task_source_id_count = _duplicate_count(str(spec.get("task_source_id", "")) for spec in executable_specs)
    duplicate_workload_key_count = _duplicate_count(str(row.get("workload_id", "")) for row in workload_rows)
    selected_count = len(selected_sources)
    profile_count = len({row["profile_name"] for row in workload_rows})
    missing_accepted_cell_count = sum(1 for row in failures if row.get("failure_reason") == "missing_accepted_cell")

    passes = (
        selected_count == 80
        and len(executable_specs) == 80
        and profile_count == len(EXPECTED_PROFILE_NAMES)
        and len(workload_rows) == 80 * len(EXPECTED_PROFILE_NAMES)
        and not failures
        and missing_accepted_cell_count == 0
        and duplicate_task_source_id_count == 0
        and duplicate_workload_key_count == 0
        and len(forbidden_key_hits) == 0
        and contract_violation_count == 0
        and missing_profile_artifact_count == 0
        and source_kind_quota_pass
        and role_surface_quota_pass
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "task_quality_calibrated_materialization_preflight_pass"
            if passes
            else "task_quality_calibrated_materialization_preflight_fail"
        ),
        "protocol_name": PROTOCOL_NAME,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "subset_config_path": str(subset_config_path),
        "repair_accepted_cells_path": str(repair_accepted_cells_path),
        "profile_run_dir": str(profile_run_dir),
        "selected_source_count": selected_count,
        "executable_task_spec_count": len(executable_specs),
        "expected_executable_task_spec_count": 80,
        "controller_profile_count": profile_count,
        "expected_controller_profile_count": len(EXPECTED_PROFILE_NAMES),
        "planned_workload_cell_count": len(workload_rows),
        "expected_planned_workload_cell_count": 80 * len(EXPECTED_PROFILE_NAMES),
        "input_accepted_cell_row_count": len(accepted_rows),
        "selected_accepted_cell_row_count": sum(len(accepted_by_source.get(_source_id(source), [])) for source in selected_sources),
        "missing_accepted_cell_count": missing_accepted_cell_count,
        "materialization_failure_count": len(failures),
        "duplicate_task_source_id_count": duplicate_task_source_id_count,
        "duplicate_workload_key_count": duplicate_workload_key_count,
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "contract_violation_count": contract_violation_count,
        "missing_profile_artifact_count": missing_profile_artifact_count,
        "source_kind_counts": dict(sorted(source_kind_counts.items())),
        "source_kind_quota_pass": source_kind_quota_pass,
        "role_surface_counts": role_surface_counts,
        "role_surface_quota_pass": role_surface_quota_pass,
        "calibrated_anchor_selected_count": int(source_kind_counts.get("anchor_neighborhood", 0)),
        "calibrated_anchor_post_friction_step_selected_count": sum(
            1
            for spec in executable_specs
            if spec.get("repair_source_kind") == "anchor_neighborhood"
            and spec.get("normalized_surface_variant") == "post_friction_step"
        ),
        "calibrated_anchor_steady_surface_selected_count": sum(
            1
            for spec in executable_specs
            if spec.get("repair_source_kind") == "anchor_neighborhood"
            and spec.get("normalized_surface_variant") == "steady_surface"
        ),
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
        "passes_public_gates": passes,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "executable_task_specs": str(output / "executable_task_specs.json"),
            "executable_task_specs_csv": str(output / "executable_task_specs.csv"),
            "planned_workload": str(output / "planned_workload.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "materialization_failures": str(output / "materialization_failures.csv"),
            "source_kind_aggregate": str(output / "source_kind_aggregate.csv"),
            "role_surface_aggregate": str(output / "role_surface_aggregate.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }

    executable_payload = {
        "protocol_name": PROTOCOL_NAME,
        "generated_at_utc": summary["generated_at_utc"],
        "claim_scope": "no-reset calibrated executable materialization only",
        "subset_config": str(subset_config_path),
        "accepted_cells": str(repair_accepted_cells_path),
        "executable_task_specs": executable_specs,
    }
    write_json(output / "executable_task_specs.json", executable_payload)
    write_csv_rows(output / "executable_task_specs.csv", [executable_spec_csv_row(spec) for spec in executable_specs])
    write_csv_rows(output / "planned_workload.csv", workload_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows)
    write_csv_rows(output / "materialization_failures.csv", failures)
    write_csv_rows(
        output / "source_kind_aggregate.csv",
        _aggregate_rows(executable_specs, ("repair_source_kind",), count_name="executable_task_spec_count"),
    )
    write_csv_rows(
        output / "role_surface_aggregate.csv",
        _aggregate_rows(
            executable_specs,
            ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
            count_name="executable_task_spec_count",
        ),
    )
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset-config", type=Path, default=DEFAULT_SUBSET_CONFIG)
    parser.add_argument("--repair-accepted-cells", type=Path, default=DEFAULT_REPAIR_ACCEPTED_CELLS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_calibrated_materialization_preflight(
        subset_config_path=args.subset_config,
        repair_accepted_cells_path=args.repair_accepted_cells,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"executable_task_spec_count={summary['executable_task_spec_count']}")
    print(f"planned_workload_cell_count={summary['planned_workload_cell_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"forbidden_key_violation_count={summary['forbidden_key_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
