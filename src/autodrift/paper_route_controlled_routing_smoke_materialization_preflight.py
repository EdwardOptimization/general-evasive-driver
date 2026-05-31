"""No-reset materialization preflight for the controlled routing-smoke panel."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
    profile_artifact_rows,
)
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.bounded_comparison_candidate_qualification import read_csv_rows
from autodrift.paper_route_controlled_comparison_panel_preflight import SOURCE_FIELDNAMES, TASK_FAMILIES


DEFAULT_PANEL_SOURCES = Path("runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv")
DEFAULT_GENERATED_SOURCE_SPECS = Path(
    "runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_source_specs.csv"
)
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight")
DEFAULT_NEXT_BLOCKER = "m2034-paper-route-controlled-routing-smoke-materialization-preflight-result-audit"
TARGET_SELECTED_SOURCE_COUNT = 36
TARGET_PROFILE_COUNT = 12
TARGET_WORKLOAD_COUNT = TARGET_SELECTED_SOURCE_COUNT * TARGET_PROFILE_COUNT
PROTOCOL_NAME = "paper_route_controlled_routing_smoke_materialization_preflight_v0"

SELECTED_SOURCE_FIELDNAMES = [
    *SOURCE_FIELDNAMES,
    "selected_source_rank",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
]
EXECUTABLE_SPEC_CSV_FIELDNAMES = [
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
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
MATERIALIZATION_FAILURE_FIELDNAMES = [
    "panel_source_id",
    "panel_task_family",
    "source_kind",
    "failure_type",
    "reason",
]
AGGREGATE_FIELDNAMES = ["key", "count"]
FAMILY_KIND_AGGREGATE_FIELDNAMES = ["panel_task_family", "source_kind", "count"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool_string(value: bool) -> str:
    return "true" if bool(value) else "false"


def _generated_source_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {str(row["source_spec_id"]) for row in read_csv_rows(path)}


def select_smoke_sources(
    source_rows: list[Mapping[str, Any]],
    *,
    generated_source_ids: set[str],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    sorted_rows = sorted(
        source_rows,
        key=lambda row: (
            TASK_FAMILIES.index(str(row["panel_task_family"])),
            str(row["source_kind"]),
            str(row["panel_source_id"]),
        ),
    )
    for row in sorted_rows:
        key = (str(row["panel_task_family"]), str(row["source_kind"]))
        if key in seen:
            continue
        seen.add(key)
        generated = str(row["panel_source_id"]) in generated_source_ids
        proxy_template = proxy_template_for_source(row)
        selected.append(
            {
                **{field: row.get(field, "") for field in SOURCE_FIELDNAMES},
                "selected_source_rank": len(selected),
                "materialization_semantics": "smoke_proxy",
                "proxy_template_family": proxy_template,
                "generated_source_row": _bool_string(generated),
                "paper_validity_claim": "false",
            }
        )
    return selected


def proxy_template_for_source(row: Mapping[str, Any]) -> str:
    family = str(row.get("panel_task_family", ""))
    kind = str(row.get("source_kind", "")).lower()
    surface = str(row.get("normalized_surface_variant", "")).lower()
    text = f"{kind}|{surface}"
    if "brake_authority" in text or "drive_brake" in text:
        return "t4_staged_warmup_capability"
    if "yaw_authority" in text or "steer_lag" in text or "rear_lateral" in text:
        return "t4_actuator_delay_response"
    if "terminal_boundary" in text or "boundary" in text:
        return "t5_boundary_axis_retarget"
    if "actuator_delay" in text:
        return "t4_actuator_delay_response"
    if "capability_step" in text or "warmup" in text:
        return "t4_staged_warmup_capability"
    if "mixed" in text:
        return "t5_near_boundary_warmup"
    if family == "T4_variable_diagnostic_delay":
        if "actuator_delay" in text:
            return "t4_actuator_delay_response"
        return "t4_staged_warmup_capability"
    if family == "T5_source_rich_extreme_dynamics":
        if "boundary" in text:
            return "t5_boundary_axis_retarget"
        return "t5_near_boundary_warmup"
    return "t5_near_boundary_warmup"


def contract_checks(env_config: Any) -> dict[str, bool]:
    return {
        "history_length_is_positive": int(env_config.history_length) >= 1,
        "action_history_mode_full": env_config.action_history_mode == "full",
        "include_privileged_params_false": not bool(env_config.include_privileged_params),
        "wheel_observation_mode_none": env_config.wheel_observation_mode == "none",
        "obstacle_relative_velocity_mode_zero": env_config.obstacle_relative_velocity_mode == "zero",
    }


def materialize_executable_specs(selected_sources: list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, source in enumerate(selected_sources):
        template = str(source["proxy_template_family"])
        try:
            env_config = env_config_for_hook_spec(
                source_family=template,
                capability_pair="routing_smoke_proxy",
                reveal_step=60 + (index % 5) * 8,
            )
            assert_human_view_env_contract(env_config)
            checks = contract_checks(env_config)
            contract_violation_count = sum(1 for value in checks.values() if not bool(value))
            if str(source.get("paper_validity_claim", "")).lower() != "false":
                raise ValueError("smoke proxy row cannot make paper validity claim")
            specs.append(
                {
                    **{field: source.get(field, "") for field in SOURCE_FIELDNAMES},
                    "task_source_id": f"m2033-smoke-{index:04d}-{source['panel_source_id']}",
                    "materialization_semantics": source["materialization_semantics"],
                    "proxy_template_family": template,
                    "generated_source_row": source["generated_source_row"],
                    "paper_validity_claim": source["paper_validity_claim"],
                    "contract_checks": checks,
                    "contract_violation_count": contract_violation_count,
                    "env_config": env_config_to_dict(env_config),
                }
            )
        except Exception as exc:  # pragma: no cover - exercised through fail-closed artifacts in real runs.
            failures.append(
                {
                    "panel_source_id": str(source.get("panel_source_id", "")),
                    "panel_task_family": str(source.get("panel_task_family", "")),
                    "source_kind": str(source.get("source_kind", "")),
                    "failure_type": type(exc).__name__,
                    "reason": str(exc),
                }
            )
    return specs, failures


def executable_spec_csv_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        checks = dict(spec.get("contract_checks", {}))
        rows.append(
            {
                "task_source_id": spec["task_source_id"],
                "panel_source_id": spec["panel_source_id"],
                "panel_task_family": spec["panel_task_family"],
                "source_origin": spec["source_origin"],
                "source_kind": spec["source_kind"],
                "source_edge": spec["source_edge"],
                "window_tag": spec["window_tag"],
                "source_role_semantics": spec["source_role_semantics"],
                "parent_feasibility_tier_id": spec["parent_feasibility_tier_id"],
                "normalized_surface_variant": spec["normalized_surface_variant"],
                "sampled_obstacle_label": spec["sampled_obstacle_label"],
                "source_reference": spec["source_reference"],
                "materialization_semantics": spec["materialization_semantics"],
                "proxy_template_family": spec["proxy_template_family"],
                "generated_source_row": spec["generated_source_row"],
                "paper_validity_claim": spec["paper_validity_claim"],
                "contract_violation_count": spec["contract_violation_count"],
                **checks,
            }
        )
    return rows


def planned_workload_rows(
    executable_specs: list[Mapping[str, Any]],
    *,
    profile_run_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles = profile_artifact_rows(m1674_run_dir=profile_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in executable_specs:
        for profile in profiles:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "panel_source_id": spec["panel_source_id"],
                    "panel_task_family": spec["panel_task_family"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
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
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows, profiles


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    return [{"key": key_value, "count": count} for key_value, count in sorted(Counter(str(row[key]) for row in rows).items())]


def _family_kind_counts(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((str(row["panel_task_family"]), str(row["source_kind"])) for row in rows)
    return [
        {"panel_task_family": family, "source_kind": source_kind, "count": count}
        for (family, source_kind), count in sorted(counts.items())
    ]


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(str(value) for value in values)
    return sum(1 for value, count in counts.items() if count > 1)


def run_materialization_preflight(
    *,
    panel_sources_path: Path = DEFAULT_PANEL_SOURCES,
    generated_source_specs_path: Path = DEFAULT_GENERATED_SOURCE_SPECS,
    profile_run_dir: Path = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = read_csv_rows(panel_sources_path)
    generated_ids = _generated_source_ids(generated_source_specs_path)
    selected_sources = select_smoke_sources(source_rows, generated_source_ids=generated_ids)
    executable_specs, materialization_failures = materialize_executable_specs(selected_sources)
    workload_rows, profile_rows = planned_workload_rows(executable_specs, profile_run_dir=profile_run_dir)

    profile_missing_count = sum(1 for row in profile_rows if not (row["config_exists"] and row["checkpoint_exists"]))
    duplicate_task_source_id_count = _duplicate_count(str(row["task_source_id"]) for row in executable_specs)
    duplicate_workload_id_count = _duplicate_count(str(row["workload_id"]) for row in workload_rows)
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in executable_specs)
    forbidden_key_violation_rows = forbidden_key_violations(executable_specs)
    smoke_proxy_paper_claim_count = sum(1 for row in executable_specs if str(row.get("paper_validity_claim", "")).lower() != "false")
    generated_non_proxy_count = sum(
        1
        for row in executable_specs
        if str(row.get("generated_source_row", "")).lower() == "true"
        and str(row.get("materialization_semantics", "")) != "smoke_proxy"
    )

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
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "source_provenance_dropped": False,
        "smoke_proxy_paper_validity_claim_made": smoke_proxy_paper_claim_count > 0,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)

    pass_conditions = (
        len(selected_sources) == TARGET_SELECTED_SOURCE_COUNT
        and len(executable_specs) == TARGET_SELECTED_SOURCE_COUNT
        and len(workload_rows) == TARGET_WORKLOAD_COUNT
        and len(materialization_failures) == 0
        and profile_missing_count == 0
        and duplicate_task_source_id_count == 0
        and duplicate_workload_id_count == 0
        and contract_violation_count == 0
        and not forbidden_key_violation_rows
        and generated_non_proxy_count == 0
        and guardrail_violation_count == 0
    )
    if pass_conditions:
        result_class = "controlled_routing_smoke_materialization_preflight_pass"
    elif selected_sources or executable_specs or workload_rows:
        result_class = "controlled_routing_smoke_materialization_preflight_partial"
    else:
        result_class = "controlled_routing_smoke_materialization_preflight_fail_closed"

    claim_rows = [
        {
            "claim": "controlled_routing_smoke_materialization_preflight_completed",
            "admissible": True,
            "reason": "M2033 writes no-reset materialization artifacts for a bounded smoke workload",
        },
        {
            "claim": "routing_smoke_execution_ready",
            "admissible": pass_conditions,
            "reason": "requires selected sources executable specs workload profile artifacts and guardrails to pass",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2033 does not execute or compare controller outcomes",
        },
        {
            "claim": "paper_valid_generated_task_semantics",
            "admissible": False,
            "reason": "generated T2/T3 rows are smoke proxies until validated by later task semantics work",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2033 is materialization preflight only",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2033 does not run history intervention outcome tests",
        },
    ]

    artifacts = {
        "summary": output_dir / "summary.json",
        "selected_smoke_sources": output_dir / "selected_smoke_sources.csv",
        "executable_task_specs_json": output_dir / "executable_task_specs.json",
        "executable_task_specs_csv": output_dir / "executable_task_specs.csv",
        "planned_workload": output_dir / "planned_workload.csv",
        "profile_artifacts": output_dir / "profile_artifacts.csv",
        "materialization_failures": output_dir / "materialization_failures.csv",
        "source_kind_aggregate": output_dir / "source_kind_aggregate.csv",
        "family_source_kind_aggregate": output_dir / "family_source_kind_aggregate.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
    }
    write_csv_rows(artifacts["selected_smoke_sources"], selected_sources, SELECTED_SOURCE_FIELDNAMES)
    write_json(
        artifacts["executable_task_specs_json"],
        {
            "protocol": PROTOCOL_NAME,
            "executable_task_specs": executable_specs,
        },
    )
    write_csv_rows(artifacts["executable_task_specs_csv"], executable_spec_csv_rows(executable_specs), EXECUTABLE_SPEC_CSV_FIELDNAMES)
    write_csv_rows(artifacts["planned_workload"], workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(artifacts["profile_artifacts"], profile_rows, ["profile_name", "config_path", "checkpoint_path", "config_exists", "checkpoint_exists"])
    write_csv_rows(artifacts["materialization_failures"], materialization_failures, MATERIALIZATION_FAILURE_FIELDNAMES)
    write_csv_rows(artifacts["source_kind_aggregate"], _count_by(selected_sources, "source_kind"), AGGREGATE_FIELDNAMES)
    write_csv_rows(artifacts["family_source_kind_aggregate"], _family_kind_counts(selected_sources), FAMILY_KIND_AGGREGATE_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_rows, CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "panel_sources_path": str(panel_sources_path),
        "generated_source_specs_path": str(generated_source_specs_path),
        "profile_run_dir": str(profile_run_dir),
        "input_source_count": len(source_rows),
        "selected_source_count": len(selected_sources),
        "target_selected_source_count": TARGET_SELECTED_SOURCE_COUNT,
        "executable_task_spec_count": len(executable_specs),
        "planned_workload_count": len(workload_rows),
        "target_workload_count": TARGET_WORKLOAD_COUNT,
        "profile_count": len(profile_rows),
        "target_profile_count": TARGET_PROFILE_COUNT,
        "profile_missing_count": profile_missing_count,
        "materialization_failure_count": len(materialization_failures),
        "duplicate_task_source_id_count": duplicate_task_source_id_count,
        "duplicate_workload_id_count": duplicate_workload_id_count,
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": len(forbidden_key_violation_rows),
        "generated_non_proxy_count": generated_non_proxy_count,
        "smoke_proxy_paper_claim_count": smoke_proxy_paper_claim_count,
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
    parser.add_argument("--panel-sources", type=Path, default=DEFAULT_PANEL_SOURCES)
    parser.add_argument("--generated-source-specs", type=Path, default=DEFAULT_GENERATED_SOURCE_SPECS)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_materialization_preflight(
        panel_sources_path=args.panel_sources,
        generated_source_specs_path=args.generated_source_specs,
        profile_run_dir=args.profile_run_dir,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_source_count={summary['selected_source_count']}")
    print(f"executable_task_spec_count={summary['executable_task_spec_count']}")
    print(f"planned_workload_count={summary['planned_workload_count']}")
    print(f"profile_missing_count={summary['profile_missing_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
