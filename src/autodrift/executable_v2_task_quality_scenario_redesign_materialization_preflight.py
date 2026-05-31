"""No-rollout executable materialization for the task-quality scenario redesign panel."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.executable_v2_support_first_source_mining import required_label_for_role
from autodrift.executable_v2_task_quality_scenario_redesign_source_mining_audit import (
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
    TIER_E,
)


DEFAULT_SUBSET_CONFIG = Path("configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json")
DEFAULT_TEMPLATE = Path("configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json")
DEFAULT_ACCEPTED_CELLS = Path(
    "runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution/support_first_accepted_cells.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight")
DEFAULT_NEXT_BLOCKER = "m1929-executable-v2-task-quality-scenario-redesign-materialization-result-audit"
PROTOCOL_NAME = "task_quality_scenario_redesign_materialization_preflight_v0"
POSITIVE_TIERS = {TIER_A, TIER_B}
BOUNDARY_TIERS = {TIER_C, TIER_D}
MITIGATION_TIERS = {TIER_E}
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


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_value(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int_value(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _maybe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _source_id(row: Mapping[str, Any]) -> str:
    return str(row.get("candidate_source_id", row.get("source_v1_bounded_panel_spec_id", "")))


def load_subset_sources(path: Path | str = DEFAULT_SUBSET_CONFIG) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [dict(row) for row in payload.get("selected_sources", [])]


def load_template_rows(path: Path | str = DEFAULT_TEMPLATE) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [dict(row) for row in payload.get("candidate_sources", [])]


def _accepted_cells_by_source(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not _bool_value(row.get("accepted")):
            continue
        grouped[_source_id(row)].append(dict(row))
    return grouped


def accepted_cell_sort_key(tier: str, row: Mapping[str, Any]) -> tuple[float, float, float, str]:
    threshold = _float_value(row.get("threshold_score"))
    distance = _float_value(row.get("obstacle_distance"))
    half_width = _float_value(row.get("obstacle_half_width"))
    source = _source_id(row)
    if tier in POSITIVE_TIERS:
        return (-threshold, -distance, half_width, source)
    if tier in BOUNDARY_TIERS:
        return (threshold, distance, -half_width, source)
    return (distance, -half_width, threshold, source)


def representative_cell_for_source(
    *,
    source: Mapping[str, Any],
    accepted_cells: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str]:
    source_id = _source_id(source)
    cells = list(accepted_cells.get(source_id, []))
    if not cells:
        return None, "missing_accepted_cell"
    tier = str(source.get("feasibility_tier_id", ""))
    selected = sorted(cells, key=lambda row: accepted_cell_sort_key(tier, row))[0]
    if tier in POSITIVE_TIERS:
        rule = "positive_support_max_threshold"
    elif tier in BOUNDARY_TIERS:
        rule = "boundary_min_threshold"
    elif tier in MITIGATION_TIERS:
        rule = "mitigation_closest_largest_obstacle"
    else:
        rule = "default_first_accepted"
    return dict(selected), rule


def _require_aeb_infeasible(role: str) -> bool:
    return role != "stable_aeb"


def env_config_for_materialized_source(
    *,
    template: Mapping[str, Any],
    cell: Mapping[str, Any],
) -> dict[str, Any]:
    speed = _float_value(template.get("speed_ref", cell.get("speed_ref")))
    mu = _float_value(template.get("mu", cell.get("mu")))
    label = str(cell.get("label", required_label_for_role(str(template.get("source_role_semantics", "")))))
    friction_enabled = _bool_value(template.get("friction_step_enabled"))
    friction_step_at = _int_value(cell.get("friction_step_at", template.get("friction_step_at")), default=20)
    max_threshold = _maybe_float(template.get("max_threshold_score"))
    obstacle_data: dict[str, Any] = {
        "enabled": True,
        "allowed_labels": [label],
        "require_aeb_infeasible": _require_aeb_infeasible(str(template.get("source_role_semantics", ""))),
        "distance_range": [
            _float_value(cell.get("obstacle_distance")),
            _float_value(cell.get("obstacle_distance")),
        ],
        "half_width_range": [
            _float_value(cell.get("obstacle_half_width")),
            _float_value(cell.get("obstacle_half_width")),
        ],
        "ego_half_width": _float_value(template.get("ego_half_width"), default=0.90),
        "safety_margin": _float_value(template.get("safety_margin"), default=0.30),
        "brake_mu_fraction": _float_value(template.get("brake_mu_fraction"), default=0.90),
        "conventional_lateral_mu_fraction": _float_value(
            template.get("conventional_lateral_mu_fraction"), default=0.42
        ),
        "drift_lateral_mu_fraction": _float_value(template.get("drift_lateral_mu_fraction"), default=0.85),
        "min_time_after_friction_step": _float_value(template.get("min_time_after_friction_step")),
        "max_sample_attempts": 1,
        "finish_on_pass": True,
        "pass_reward": 10.0,
    }
    if max_threshold is not None:
        obstacle_data["max_threshold_score"] = max_threshold
    env_data = {
        "dt": _float_value(template.get("dt"), default=0.05),
        "max_steps": 800,
        "track_kind": "circle",
        "track_radius": 18.0,
        "track_width": _float_value(template.get("pre_obstacle_track_width"), default=5.0),
        "speed_range": [speed, speed],
        "friction_limited_speed": False,
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "zero",
        "wheel_observation_mode": "none",
        "randomization": {
            "mu_range": [mu, mu],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "friction_step": {
            "enabled": friction_enabled,
            "step_range": [friction_step_at, friction_step_at],
            "mu_range": [mu, mu],
            "resample_speed_ref": False,
        },
        "obstacle": obstacle_data,
    }
    env_config = build_env_config(env_data)
    assert_human_view_env_contract(env_config)
    return env_config_to_dict(env_config)


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
    template: Mapping[str, Any],
    cell: Mapping[str, Any],
    cell_rule: str,
    index: int,
) -> dict[str, Any]:
    env_config = env_config_for_materialized_source(template=template, cell=cell)
    checks = _contract_checks(env_config)
    source_id = _source_id(source)
    spec_id = f"tqsr_exec_v0_{index:04d}_{source_id}"
    return {
        "task_source_id": spec_id,
        "candidate_source_id": source_id,
        "source_v1_bounded_panel_spec_id": source.get("source_v1_bounded_panel_spec_id", source_id),
        "source_scenario_spec_id": source.get("source_scenario_spec_id", ""),
        "feasibility_tier_id": source.get("feasibility_tier_id", ""),
        "source_role_semantics": source.get("source_role_semantics", ""),
        "source_split": source.get("source_split", ""),
        "surface_variant": source.get("surface_variant", ""),
        "speed_ref": _float_value(source.get("speed_ref")),
        "mu": _float_value(source.get("mu")),
        "obstacle_distance": _float_value(cell.get("obstacle_distance")),
        "obstacle_half_width": _float_value(cell.get("obstacle_half_width")),
        "label": cell.get("label", ""),
        "threshold_score": _float_value(cell.get("threshold_score")),
        "time_to_obstacle": _float_value(cell.get("time_to_obstacle")),
        "time_after_friction_step": _float_value(cell.get("time_after_friction_step")),
        "target_support_mode": source.get("target_support_mode", template.get("target_support_mode", "")),
        "target_boundary_mode": source.get("target_boundary_mode", template.get("target_boundary_mode", "")),
        "selected_accepted_cell_rule": cell_rule,
        "diagnostic_only_no_ranking_claim": True,
        "paper_holdout_candidate": False,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "contract_checks": checks,
        "contract_violation_count": sum(1 for value in checks.values() if not bool(value)),
        "env_config": env_config,
    }


def executable_spec_csv_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    checks = dict(spec.get("contract_checks", {}))
    return {
        "task_source_id": spec.get("task_source_id", ""),
        "candidate_source_id": spec.get("candidate_source_id", ""),
        "feasibility_tier_id": spec.get("feasibility_tier_id", ""),
        "source_role_semantics": spec.get("source_role_semantics", ""),
        "source_split": spec.get("source_split", ""),
        "surface_variant": spec.get("surface_variant", ""),
        "speed_ref": spec.get("speed_ref", ""),
        "mu": spec.get("mu", ""),
        "obstacle_distance": spec.get("obstacle_distance", ""),
        "obstacle_half_width": spec.get("obstacle_half_width", ""),
        "label": spec.get("label", ""),
        "threshold_score": spec.get("threshold_score", ""),
        "target_support_mode": spec.get("target_support_mode", ""),
        "target_boundary_mode": spec.get("target_boundary_mode", ""),
        "selected_accepted_cell_rule": spec.get("selected_accepted_cell_rule", ""),
        "contract_violation_count": spec.get("contract_violation_count", ""),
        "diagnostic_only_no_ranking_claim": spec.get("diagnostic_only_no_ranking_claim", True),
        **checks,
    }


def workload_rows(
    executable_specs: list[Mapping[str, Any]],
    *,
    profile_run_dir: Path | str,
) -> list[dict[str, Any]]:
    profiles = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in executable_specs:
        strata = ";".join(
            [
                str(spec.get("feasibility_tier_id", "")),
                str(spec.get("source_role_semantics", "")),
                str(spec.get("surface_variant", "")),
                str(spec.get("source_split", "")),
            ]
        )
        for profile in profiles:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "candidate_source_id": spec["candidate_source_id"],
                    "profile_name": profile["profile_name"],
                    "feasibility_tier_id": spec["feasibility_tier_id"],
                    "source_role_semantics": spec["source_role_semantics"],
                    "source_split": spec["source_split"],
                    "surface_variant": spec["surface_variant"],
                    "target_boundary_mode": spec["target_boundary_mode"],
                    "selected_accepted_cell_rule": spec["selected_accepted_cell_rule"],
                    "strata": strata,
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "config_exists": profile["config_exists"],
                    "checkpoint_exists": profile["checkpoint_exists"],
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def run_materialization_preflight(
    *,
    subset_config_path: Path | str = DEFAULT_SUBSET_CONFIG,
    template_path: Path | str = DEFAULT_TEMPLATE,
    accepted_cells_path: Path | str = DEFAULT_ACCEPTED_CELLS,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_executable_spec_count: int = 80,
    expected_profile_count: int = len(EXPECTED_PROFILE_NAMES),
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_sources = load_subset_sources(subset_config_path)
    template_by_source = {_source_id(row): dict(row) for row in load_template_rows(template_path)}
    accepted_by_source = _accepted_cells_by_source(read_csv_rows(accepted_cells_path))

    executable_specs: list[dict[str, Any]] = []
    selected_cells: list[dict[str, Any]] = []
    unmappable: list[dict[str, Any]] = []
    for source in selected_sources:
        source_id = _source_id(source)
        template = template_by_source.get(source_id)
        if template is None:
            unmappable.append({"candidate_source_id": source_id, "error_type": "missing_template_row"})
            continue
        cell, rule = representative_cell_for_source(source=source, accepted_cells=accepted_by_source)
        if cell is None:
            unmappable.append({"candidate_source_id": source_id, "error_type": rule})
            continue
        try:
            spec = materialize_executable_spec(
                source=source,
                template=template,
                cell=cell,
                cell_rule=rule,
                index=len(executable_specs),
            )
        except Exception as exc:  # noqa: BLE001 - preflight must preserve materialization blockers.
            unmappable.append(
                {
                    "candidate_source_id": source_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            continue
        executable_specs.append(spec)
        selected_cells.append(
            {
                **cell,
                "selected_accepted_cell_rule": rule,
                "task_source_id": spec["task_source_id"],
                "feasibility_tier_id": source.get("feasibility_tier_id", ""),
                "source_role_semantics": source.get("source_role_semantics", ""),
            }
        )

    profiles = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    workloads = workload_rows(executable_specs, profile_run_dir=profile_run_dir)
    missing_profile_artifact_count = sum(
        1 for row in profiles if not _bool_value(row.get("config_exists")) or not _bool_value(row.get("checkpoint_exists"))
    )
    contract_violation_count = sum(_int_value(spec.get("contract_violation_count")) for spec in executable_specs)
    forbidden_key_hits = forbidden_key_violations(executable_specs)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_workload_cell_count = int(target_executable_spec_count) * int(expected_profile_count)
    passes = (
        len(selected_sources) == int(target_executable_spec_count)
        and len(executable_specs) == int(target_executable_spec_count)
        and len(selected_cells) == int(target_executable_spec_count)
        and len(workloads) == target_workload_cell_count
        and len({row["profile_name"] for row in workloads}) == int(expected_profile_count)
        and not unmappable
        and missing_profile_artifact_count == 0
        and contract_violation_count == 0
        and not forbidden_key_hits
        and guardrail_violation_count == 0
    )

    executable_payload = {
        "protocol_name": PROTOCOL_NAME,
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "no-rollout executable materialization only",
        "subset_config_path": str(subset_config_path),
        "template_path": str(template_path),
        "accepted_cells_path": str(accepted_cells_path),
        "profile_run_dir": str(profile_run_dir),
        "executable_task_specs": executable_specs,
    }
    summary = {
        "result_class": (
            "task_quality_scenario_materialization_preflight_pass"
            if passes
            else "task_quality_scenario_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "subset_config_path": str(subset_config_path),
        "template_path": str(template_path),
        "accepted_cells_path": str(accepted_cells_path),
        "profile_run_dir": str(profile_run_dir),
        "selected_source_count": len(selected_sources),
        "target_executable_spec_count": int(target_executable_spec_count),
        "executable_spec_count": len(executable_specs),
        "selected_accepted_cell_count": len(selected_cells),
        "workload_cell_count": len(workloads),
        "target_workload_cell_count": target_workload_cell_count,
        "profile_count": len({row["profile_name"] for row in workloads}),
        "expected_profile_count": int(expected_profile_count),
        "tier_counts": _count_by(executable_specs, "feasibility_tier_id"),
        "role_counts": _count_by(executable_specs, "source_role_semantics"),
        "surface_counts": _count_by(executable_specs, "surface_variant"),
        "split_counts": _count_by(executable_specs, "source_split"),
        "accepted_cell_rule_counts": _count_by(executable_specs, "selected_accepted_cell_rule"),
        "unmappable_source_count": len(unmappable),
        "contract_violation_count": int(contract_violation_count),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "missing_profile_artifact_count": int(missing_profile_artifact_count),
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
        "passes_public_smoke_gates": bool(passes),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "executable_task_specs": str(output / "executable_task_specs.json"),
            "executable_task_specs_csv": str(output / "executable_task_specs.csv"),
            "executable_workload_matrix": str(output / "executable_workload_matrix.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "selected_accepted_cells": str(output / "selected_accepted_cells.csv"),
            "unmappable_sources": str(output / "unmappable_sources.csv"),
        },
        "next_blocker": next_blocker,
    }

    write_json(output / "executable_task_specs.json", executable_payload)
    write_csv_rows(output / "executable_task_specs.csv", [executable_spec_csv_row(spec) for spec in executable_specs])
    write_csv_rows(output / "executable_workload_matrix.csv", workloads)
    write_csv_rows(output / "profile_artifacts.csv", profiles)
    write_csv_rows(output / "selected_accepted_cells.csv", selected_cells)
    write_csv_rows(output / "unmappable_sources.csv", unmappable)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset-config", type=Path, default=DEFAULT_SUBSET_CONFIG)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--accepted-cells", type=Path, default=DEFAULT_ACCEPTED_CELLS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_materialization_preflight(
        subset_config_path=args.subset_config,
        template_path=args.template,
        accepted_cells_path=args.accepted_cells,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"executable_spec_count={summary['executable_spec_count']}")
    print(f"selected_accepted_cell_count={summary['selected_accepted_cell_count']}")
    print(f"workload_cell_count={summary['workload_cell_count']}")
    print(f"profile_count={summary['profile_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
