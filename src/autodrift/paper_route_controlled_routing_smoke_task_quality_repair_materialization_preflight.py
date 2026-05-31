"""No-reset materialization preflight for routing-smoke task-quality repair templates."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations


DEFAULT_TEMPLATES = Path("configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json")
DEFAULT_PARENT_SPECS = Path("runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json")
DEFAULT_PARENT_WORKLOAD = Path("runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv")
DEFAULT_SOURCE_PROFILE_LOCALIZATION = Path(
    "runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/outcome_by_source_profile.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight")
DEFAULT_NEXT_BLOCKER = "m2049-paper-route-controlled-routing-smoke-task-quality-repair-materialization-preflight-result-audit"

PROTOCOL_NAME = "paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight_v0"
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
AGGREGATE_FIELDNAMES = ["key", "count"]
FAILURE_FIELDNAMES = ["repair_candidate_id", "repair_axis", "failure_type", "reason"]

SPEC_CSV_FIELDNAMES = [
    "task_source_id",
    "parent_task_source_id",
    "repair_candidate_id",
    "repair_axis",
    "source_split",
    "parent_resolution_method",
    "parent_resolution_key",
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
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
    "contract_violation_count",
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "parent_task_source_id",
    "repair_candidate_id",
    "repair_axis",
    "source_split",
    "panel_source_id",
    "panel_task_family",
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
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
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return float(default)


def _field(row: Mapping[str, Any], name: str, default: str = "") -> str:
    value = str(row.get(name, "")).strip()
    return value if value else default


def _load_parent_specs(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    if isinstance(payload, Mapping):
        specs = payload.get("executable_task_specs", [])
    else:
        specs = payload
    return [dict(row) for row in specs]


def _profile_rows(parent_workload_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for row in parent_workload_rows:
        name = _field(row, "profile_name")
        if name and name not in profiles:
            profiles[name] = {
                "profile_name": name,
                "profile_config_path": row.get("profile_config_path", ""),
                "checkpoint_path": row.get("checkpoint_path", ""),
            }
    return [profiles[name] for name in sorted(profiles)]


def _index_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key, "")): dict(row) for row in rows if str(row.get(key, ""))}


def _group_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(dict(row))
    return dict(groups)


def _choose(rows: Sequence[Mapping[str, Any]], index: int) -> Mapping[str, Any] | None:
    if not rows:
        return None
    return rows[index % len(rows)]


def _spec_matches(spec: Mapping[str, Any], **criteria: Any) -> bool:
    for key, value in criteria.items():
        if str(value) and str(spec.get(key, "")) != str(value):
            return False
    return True


def _resolve_parent(
    candidate: Mapping[str, Any],
    *,
    specs_by_id: Mapping[str, Mapping[str, Any]],
    parent_specs: Sequence[Mapping[str, Any]],
    source_profile_rows: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, str, str]:
    exact_key = _field(candidate, "parent_task_source_id")
    if exact_key in specs_by_id:
        return specs_by_id[exact_key], "exact_task_source_id", exact_key

    repair_axis = _field(candidate, "repair_axis")
    local_index = int(candidate.get("repair_sequence_index", 0))
    if repair_axis == "l2_offtrack_relief":
        profile = _field(candidate, "parent_profile_name")
        rows = [
            row
            for row in source_profile_rows
            if _field(row, "profile_name") == profile and _float(row.get("offtrack_outcome_count", 0.0)) > 0.0
        ]
        source_row = _choose(rows, local_index)
        if source_row is not None:
            source_id = _field(source_row, "task_source_id")
            if source_id in specs_by_id:
                return specs_by_id[source_id], "source_profile_offtrack_slice", f"{profile}:{source_id}"

    if repair_axis == "family_offtrack_relief":
        family = _field(candidate, "parent_panel_task_family")
        rows = [spec for spec in parent_specs if _spec_matches(spec, panel_task_family=family)]
        spec = _choose(rows, local_index)
        if spec is not None:
            return spec, "family_slice", family

    if repair_axis == "zero_success_source_kind_relief":
        source_kind = _field(candidate, "parent_source_kind")
        rows = [spec for spec in parent_specs if _spec_matches(spec, source_kind=source_kind)]
        spec = _choose(rows, local_index)
        if spec is not None:
            return spec, "source_kind_slice", source_kind

    if repair_axis == "generated_proxy_support_check":
        rows = [
            spec
            for spec in parent_specs
            if _bool(spec.get("generated_source_row", False)) and str(spec.get("materialization_semantics", "")) == "smoke_proxy"
        ]
        spec = _choose(rows, local_index)
        if spec is not None:
            return spec, "generated_proxy_slice", "generated_source_row=true"

    return None, "unresolved", exact_key or repair_axis


def _shift_range(values: Any, delta: float, *, lower_bound: float) -> list[float]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) != 2:
        values = [lower_bound, lower_bound]
    low = max(lower_bound, _float(values[0], lower_bound) + delta)
    high = max(low, _float(values[1], low) + delta)
    return [float(low), float(high)]


def _apply_template_delta(env_config: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    repaired = copy.deepcopy(dict(env_config))
    obstacle = copy.deepcopy(dict(repaired.get("obstacle", {})))
    warmup = copy.deepcopy(dict(repaired.get("warmup_gate", {})))
    obstacle["distance_range"] = _shift_range(
        obstacle.get("distance_range", [8.0, 8.0]),
        _float(candidate.get("obstacle_distance_delta_m", 0.0)),
        lower_bound=8.0,
    )
    obstacle["half_width_range"] = _shift_range(
        obstacle.get("half_width_range", [0.25, 0.25]),
        _float(candidate.get("obstacle_half_width_delta_m", 0.0)),
        lower_bound=0.25,
    )
    repaired["track_width"] = max(4.0, _float(repaired.get("track_width", 5.0), 5.0) + _float(candidate.get("track_width_delta_m", 0.0)))
    warmup["reveal_step"] = max(0, int(_float(warmup.get("reveal_step", 0), 0.0) + _float(candidate.get("warmup_reveal_step_delta", 0.0))))
    repaired["max_steps"] = max(
        int(_float(repaired.get("max_steps", 0), 0.0)),
        int(_float(repaired.get("max_steps", 0), 0.0) + _float(candidate.get("max_steps_delta", 0.0))),
    )
    repaired["obstacle"] = obstacle
    repaired["warmup_gate"] = warmup
    return repaired


def contract_checks(env_config: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "history_length_is_positive": int(env_config.get("history_length", 0)) >= 1,
        "action_history_mode_full": env_config.get("action_history_mode") == "full",
        "include_privileged_params_false": not _bool(env_config.get("include_privileged_params", False)),
        "wheel_observation_mode_none": env_config.get("wheel_observation_mode") == "none",
        "obstacle_relative_velocity_mode_zero": env_config.get("obstacle_relative_velocity_mode") == "zero",
    }


def _materialize_spec(
    candidate: Mapping[str, Any],
    parent_spec: Mapping[str, Any],
    *,
    parent_resolution_method: str,
    parent_resolution_key: str,
) -> dict[str, Any]:
    env_config = _apply_template_delta(parent_spec.get("env_config", {}), candidate)
    checks = contract_checks(env_config)
    contract_violation_count = sum(1 for value in checks.values() if not value)
    task_source_id = f"m2048-repair-{candidate['repair_candidate_id']}"
    generated_source_row = bool(candidate.get("target_generated_source_row", parent_spec.get("generated_source_row", False)))
    spec = {
        **{key: value for key, value in parent_spec.items() if key not in {"env_config", "contract_checks", "contract_violation_count"}},
        "task_source_id": task_source_id,
        "parent_task_source_id": parent_spec.get("task_source_id", ""),
        "repair_candidate_id": candidate["repair_candidate_id"],
        "repair_branch_id": candidate["repair_branch_id"],
        "repair_axis": candidate["repair_axis"],
        "repair_source_family": candidate.get("repair_source_family", ""),
        "source_split": candidate.get("source_split", ""),
        "parent_resolution_method": parent_resolution_method,
        "parent_resolution_key": parent_resolution_key,
        "materialization_semantics": "smoke_proxy",
        "generated_source_row": generated_source_row,
        "paper_validity_claim": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "template_delta": {
            "obstacle_distance_delta_m": candidate.get("obstacle_distance_delta_m", 0.0),
            "obstacle_half_width_delta_m": candidate.get("obstacle_half_width_delta_m", 0.0),
            "track_width_delta_m": candidate.get("track_width_delta_m", 0.0),
            "warmup_reveal_step_delta": candidate.get("warmup_reveal_step_delta", 0),
            "max_steps_delta": candidate.get("max_steps_delta", 0),
        },
        "contract_checks": checks,
        "contract_violation_count": contract_violation_count,
        "env_config": env_config,
    }
    return spec


def materialize_repair_specs(
    candidates: Sequence[Mapping[str, Any]],
    *,
    parent_specs: Sequence[Mapping[str, Any]],
    source_profile_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs_by_id = _index_by(parent_specs, "task_source_id")
    repaired_specs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for candidate in candidates:
        parent, method, key = _resolve_parent(
            candidate,
            specs_by_id=specs_by_id,
            parent_specs=parent_specs,
            source_profile_rows=source_profile_rows,
        )
        if parent is None:
            failures.append(
                {
                    "repair_candidate_id": candidate.get("repair_candidate_id", ""),
                    "repair_axis": candidate.get("repair_axis", ""),
                    "failure_type": "unresolved_parent",
                    "reason": str(key),
                }
            )
            continue
        repaired_specs.append(
            _materialize_spec(
                candidate,
                parent,
                parent_resolution_method=method,
                parent_resolution_key=key,
            )
        )
    return repaired_specs, failures


def _spec_csv_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        checks = dict(spec.get("contract_checks", {}))
        rows.append({field: spec.get(field, "") for field in SPEC_CSV_FIELDNAMES if field not in checks} | checks)
    return rows


def planned_workload_rows(specs: Sequence[Mapping[str, Any]], profiles: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        for profile in profiles:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "parent_task_source_id": spec["parent_task_source_id"],
                    "repair_candidate_id": spec["repair_candidate_id"],
                    "repair_axis": spec["repair_axis"],
                    "source_split": spec["source_split"],
                    "panel_source_id": spec["panel_source_id"],
                    "panel_task_family": spec["panel_task_family"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["profile_config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "source_origin": spec["source_origin"],
                    "source_kind": spec["source_kind"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "source_role_semantics": spec["source_role_semantics"],
                    "parent_feasibility_tier_id": spec["parent_feasibility_tier_id"],
                    "normalized_surface_variant": spec["normalized_surface_variant"],
                    "sampled_obstacle_label": spec["sampled_obstacle_label"],
                    "materialization_semantics": spec["materialization_semantics"],
                    "proxy_template_family": spec["proxy_template_family"],
                    "generated_source_row": spec["generated_source_row"],
                    "paper_validity_claim": spec["paper_validity_claim"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(str(value) for value in values)
    return sum(1 for _, count in counts.items() if count > 1)


def _claim_rows(pass_conditions: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "controlled_routing_smoke_task_quality_repair_materialization_preflight_completed",
            "admissible": True,
            "reason": "M2048 writes repaired no-reset materialization artifacts only",
        },
        {
            "claim": "reset_validation_ready",
            "admissible": pass_conditions,
            "reason": "requires repaired specs, workload, parent resolution, contract, and claim guards to pass",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2048 does not execute or compare controller outcomes",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated repair rows remain smoke proxies until separately validated",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2048 is materialization preflight only",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2048 does not run history intervention outcome tests",
        },
    ]


def run_repair_materialization_preflight(
    *,
    templates_path: Path = DEFAULT_TEMPLATES,
    parent_specs_path: Path = DEFAULT_PARENT_SPECS,
    parent_workload_path: Path = DEFAULT_PARENT_WORKLOAD,
    source_profile_localization_path: Path = DEFAULT_SOURCE_PROFILE_LOCALIZATION,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    target_profile_count: int | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    template_payload = read_json(templates_path)
    candidates = [dict(row) for row in template_payload.get("candidates", [])]
    expected_candidate_count = int(template_payload.get("expected_candidate_source_count", len(candidates)))
    expected_axis_counts = {str(k): int(v) for k, v in template_payload.get("expected_repair_axis_counts", {}).items()}
    expected_split_counts = {str(k): int(v) for k, v in template_payload.get("expected_source_split_counts", {}).items()}
    parent_specs = _load_parent_specs(parent_specs_path)
    parent_workload_rows = read_csv_rows(parent_workload_path)
    source_profile_rows = read_csv_rows(source_profile_localization_path)
    profiles = _profile_rows(parent_workload_rows)
    if target_profile_count is None:
        target_profile_count = len(profiles)

    repaired_specs, materialization_failures = materialize_repair_specs(
        candidates,
        parent_specs=parent_specs,
        source_profile_rows=source_profile_rows,
    )
    workload_rows = planned_workload_rows(repaired_specs, profiles)
    axis_counts = _count_by(repaired_specs, "repair_axis")
    split_counts = _count_by(repaired_specs, "source_split")
    duplicate_task_source_id_count = _duplicate_count(str(row.get("task_source_id", "")) for row in repaired_specs)
    duplicate_workload_id_count = _duplicate_count(str(row.get("workload_id", "")) for row in workload_rows)
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in repaired_specs)
    forbidden_key_violation_rows = forbidden_key_violations(repaired_specs)
    generated_proxy_paper_claim_count = sum(
        1 for row in repaired_specs if _bool(row.get("generated_source_row", False)) and _bool(row.get("paper_validity_claim", False))
    )
    profile_specific_tuning_count = sum(1 for row in repaired_specs if _bool(row.get("profile_specific_tuning", False)))
    forbidden_claim_count = sum(
        1
        for row in repaired_specs
        if _bool(row.get("controller_family_ranking_claim_made", False))
        or _bool(row.get("finite_window_vs_gru_conclusion_made", False))
        or _bool(row.get("paper_level_claim_made", False))
        or _bool(row.get("level3_self_id_claim_made", False))
    )

    expected_workload_count = expected_candidate_count * int(target_profile_count)
    guardrail_flags = {
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
        "profile_specific_tuning": profile_specific_tuning_count > 0,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "generated_proxy_paper_validity_claim_made": generated_proxy_paper_claim_count > 0,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    pass_conditions = (
        template_payload.get("result_class") == "controlled_routing_smoke_task_quality_repair_templates_pass"
        and len(candidates) == expected_candidate_count
        and len(repaired_specs) == expected_candidate_count
        and len(workload_rows) == expected_workload_count
        and len(materialization_failures) == 0
        and len(profiles) == int(target_profile_count)
        and axis_counts == expected_axis_counts
        and split_counts == expected_split_counts
        and duplicate_task_source_id_count == 0
        and duplicate_workload_id_count == 0
        and contract_violation_count == 0
        and not forbidden_key_violation_rows
        and generated_proxy_paper_claim_count == 0
        and profile_specific_tuning_count == 0
        and forbidden_claim_count == 0
        and guardrail_violation_count == 0
    )
    result_class = (
        "controlled_routing_smoke_task_quality_repair_materialization_preflight_pass"
        if pass_conditions
        else "controlled_routing_smoke_task_quality_repair_materialization_preflight_incomplete_or_fail"
    )

    artifacts = {
        "summary": output_dir / "summary.json",
        "executable_task_specs_json": output_dir / "executable_task_specs.json",
        "executable_task_specs_csv": output_dir / "executable_task_specs.csv",
        "planned_workload": output_dir / "planned_workload.csv",
        "profile_artifacts": output_dir / "profile_artifacts.csv",
        "materialization_failures": output_dir / "materialization_failures.csv",
        "repair_axis_aggregate": output_dir / "repair_axis_aggregate.csv",
        "source_split_aggregate": output_dir / "source_split_aggregate.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
    }
    write_json(artifacts["executable_task_specs_json"], {"protocol": PROTOCOL_NAME, "executable_task_specs": repaired_specs})
    write_csv_rows(artifacts["executable_task_specs_csv"], _spec_csv_rows(repaired_specs), SPEC_CSV_FIELDNAMES)
    write_csv_rows(artifacts["planned_workload"], workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(artifacts["profile_artifacts"], profiles, ["profile_name", "profile_config_path", "checkpoint_path"])
    write_csv_rows(artifacts["materialization_failures"], materialization_failures, FAILURE_FIELDNAMES)
    write_csv_rows(artifacts["repair_axis_aggregate"], [{"key": k, "count": v} for k, v in sorted(axis_counts.items())], AGGREGATE_FIELDNAMES)
    write_csv_rows(artifacts["source_split_aggregate"], [{"key": k, "count": v} for k, v in sorted(split_counts.items())], AGGREGATE_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], _claim_rows(pass_conditions), CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "templates_path": str(templates_path),
        "parent_specs_path": str(parent_specs_path),
        "parent_workload_path": str(parent_workload_path),
        "source_profile_localization_path": str(source_profile_localization_path),
        "input_candidate_count": len(candidates),
        "expected_candidate_count": expected_candidate_count,
        "repaired_spec_count": len(repaired_specs),
        "planned_workload_count": len(workload_rows),
        "expected_workload_count": expected_workload_count,
        "profile_count": len(profiles),
        "target_profile_count": int(target_profile_count),
        "repair_axis_counts": axis_counts,
        "expected_repair_axis_counts": expected_axis_counts,
        "source_split_counts": split_counts,
        "expected_source_split_counts": expected_split_counts,
        "unresolved_parent_count": len(materialization_failures),
        "materialization_failure_count": len(materialization_failures),
        "duplicate_task_source_id_count": duplicate_task_source_id_count,
        "duplicate_workload_id_count": duplicate_workload_id_count,
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": len(forbidden_key_violation_rows),
        "generated_proxy_paper_claim_count": generated_proxy_paper_claim_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "forbidden_claim_count": forbidden_claim_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": next_blocker,
    }
    write_json(artifacts["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--parent-specs", type=Path, default=DEFAULT_PARENT_SPECS)
    parser.add_argument("--parent-workload", type=Path, default=DEFAULT_PARENT_WORKLOAD)
    parser.add_argument("--source-profile-localization", type=Path, default=DEFAULT_SOURCE_PROFILE_LOCALIZATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_repair_materialization_preflight(
        templates_path=args.templates,
        parent_specs_path=args.parent_specs,
        parent_workload_path=args.parent_workload,
        source_profile_localization_path=args.source_profile_localization,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"repaired_spec_count={summary['repaired_spec_count']}")
    print(f"planned_workload_count={summary['planned_workload_count']}")
    print(f"unresolved_parent_count={summary['unresolved_parent_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
