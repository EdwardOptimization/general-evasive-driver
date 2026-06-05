"""Materialize scenario-role metric panel artifacts from M2740 taxonomy.

M2743 is a no-rollout materialization step. It converts the accepted M2740
taxonomy and M2742 design into actor-invisible role, metric, target, guardrail,
actor-contract, claim-boundary, and gate artifacts before any execution or
performance interpretation.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-"
    "scenario-role-metric-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-"
    "scenario-role-metric-panel-materialization-result-audit"
)
DEFAULT_M2740_DIR = Path(
    "runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy"
)
DEFAULT_M2742_DESIGN = Path(
    "docs/m2742-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-design.md"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit.json"
)

EXPECTED_SCENARIO_ROLE_COUNT = 6
EXPECTED_EXECUTION_TAXONOMY_ROW_COUNT = 18
EXPECTED_TAXONOMY_ROW_COUNT = 61
EXPECTED_OFFTRACK_TARGET_COUNT = 14
EXPECTED_COLLISION_CAUTION_COUNT = 1
EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_COUNT = 3
EXPECTED_NEGATIVE_CONTEXT_GUARD_COUNT = 31
EXPECTED_BLOCKED_SAME_SURFACE_GUARD_COUNT = 1
EXPECTED_PROTECTED_HF3_EXCLUSION_COUNT = 11

CLAIM_SCOPE = (
    "M2743 Route A source-diverse failure taxonomy scenario-role metric panel "
    "materialization only; no reset, step, policy action, rollout, replay, "
    "validation, training, PPO, source build, adapter probe, external "
    "simulation, private holdout, profile-specific tuning, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, source-family ranking, task-family ranking, "
    "profile ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim "
    "verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

ROLE_BY_TAXONOMY = {
    "off_track": "offtrack_containment_target",
    "collision_failure": "collision_caution_guard",
    "diagnostic_success_context": "diagnostic_success_context",
    "negative_context_guard": "negative_context_guardrail",
    "blocked_guard": "blocked_same_surface_guard",
    "protected_or_hf3_blocker": "protected_hf3_exclusion_guard",
}
ROLE_PRIORITY = {
    "offtrack_containment_target": 1,
    "collision_caution_guard": 2,
    "diagnostic_success_context": 3,
    "negative_context_guardrail": 4,
    "blocked_same_surface_guard": 5,
    "protected_hf3_exclusion_guard": 6,
}
METRIC_FAMILY_BY_ROLE = {
    "offtrack_containment_target": "road_containment",
    "collision_caution_guard": "collision_caution",
    "diagnostic_success_context": "diagnostic_regression_context",
    "negative_context_guardrail": "negative_context_exclusion",
    "blocked_same_surface_guard": "same_surface_blocker",
    "protected_hf3_exclusion_guard": "protected_hf3_exclusion",
}
METRIC_NAMES_BY_ROLE = {
    "offtrack_containment_target": "taxonomy_family;termination_reason;offtrack;task_family;source_family",
    "collision_caution_guard": "collision;outcome_bucket;task_family;source_family",
    "diagnostic_success_context": "success;outcome_bucket;task_family;source_family",
    "negative_context_guardrail": "execution_run;execution_admitted;actor_visible",
    "blocked_same_surface_guard": "execution_run;execution_admitted;blocked_guard",
    "protected_hf3_exclusion_guard": "protected_denominator;execution_run;actor_visible",
}

SOURCE_FIELDNAMES = [
    "source_id",
    "source_family",
    "path",
    "present",
    "row_count",
    "status_pass",
    "claim_boundary",
]
SCENARIO_ROLE_FIELDNAMES = [
    "scenario_role_id",
    "scenario_role",
    "source_taxonomy_family",
    "source_row_type",
    "source_row_count",
    "execution_taxonomy_row_count",
    "guardrail_taxonomy_row_count",
    "target_panel_admitted_count",
    "collision_caution_count",
    "diagnostic_success_context_count",
    "negative_context_guard_count",
    "blocked_same_surface_guard_count",
    "protected_hf3_exclusion_count",
    "execution_scheduled",
    "guardrail_only",
    "actor_visible_allowed",
    "scenario_role_labels_actor_visible",
    "ranking_allowed",
    "ordinary_success_denominator_allowed",
    "claim_scope",
]
METRIC_CONTRACT_FIELDNAMES = [
    "metric_contract_id",
    "scenario_role_id",
    "scenario_role",
    "source_taxonomy_family",
    "source_row_count",
    "metric_family",
    "metric_names",
    "metric_source",
    "row_level_binding_required",
    "target_panel_admission_policy",
    "guardrail_only",
    "actor_visible_allowed",
    "metric_labels_actor_visible",
    "ranking_allowed",
    "success_rate_verdict_allowed",
    "ordinary_success_denominator_allowed",
    "claim_scope",
]
TARGET_PANEL_FIELDNAMES = [
    "target_panel_id",
    "source_taxonomy_id",
    "scenario_role_id",
    "scenario_role",
    "source_row_type",
    "source_milestone",
    "source_family",
    "source_key",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "taxonomy_family",
    "primary_failure_family",
    "repair_signal",
    "target_panel_admitted",
    "execution_scheduled",
    "guardrail_only",
    "actor_visible_allowed",
    "target_labels_actor_visible",
    "ranking_allowed",
    "ordinary_success_denominator_allowed",
    "claim_scope",
]
GUARDRAIL_CONTEXT_FIELDNAMES = [
    "guardrail_context_id",
    "scenario_role_id",
    "scenario_role",
    "source_taxonomy_family",
    "source_row_type",
    "row_count",
    "execution_run_count",
    "execution_admitted_count",
    "protected_denominator_count",
    "actor_visible_count",
    "guardrail_only",
    "ordinary_success_denominator_allowed",
    "claim_scope",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2743",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "source_accounting_rows",
    "scenario_role_rows",
    "metric_contract_rows",
    "target_panel_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_source_diverse_failure_taxonomy_scenario_role_metric_panel(
    *,
    m2740_dir: Path | str = DEFAULT_M2740_DIR,
    m2742_design: Path | str = DEFAULT_M2742_DESIGN,
    route_plan: Path | str = DEFAULT_ROUTE_PLAN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2740_dir=Path(m2740_dir),
        m2742_design=Path(m2742_design),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )
    taxonomy_rows = source["taxonomy_rows"]
    scenario_role_rows = build_scenario_role_rows(taxonomy_rows)
    metric_contract_rows = build_metric_contract_rows(scenario_role_rows)
    target_panel_rows = build_target_panel_rows(taxonomy_rows, scenario_role_rows=scenario_role_rows)
    guardrail_context_rows = build_guardrail_context_rows(taxonomy_rows, scenario_role_rows=scenario_role_rows)
    actor_rows = build_actor_contract_guard_rows(
        source=source,
        scenario_role_rows=scenario_role_rows,
        metric_contract_rows=metric_contract_rows,
        target_panel_rows=target_panel_rows,
        guardrail_context_rows=guardrail_context_rows,
    )
    source_rows = build_source_accounting_rows(source=source)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        panel_rows_present=bool(scenario_role_rows),
        required_artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        scenario_role_rows=scenario_role_rows,
        metric_contract_rows=metric_contract_rows,
        target_panel_rows=target_panel_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["source_accounting_rows"], source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(paths["scenario_role_rows"], scenario_role_rows, fieldnames=SCENARIO_ROLE_FIELDNAMES)
    write_csv_rows(paths["metric_contract_rows"], metric_contract_rows, fieldnames=METRIC_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["target_panel_rows"], target_panel_rows, fieldnames=TARGET_PANEL_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_context_rows, fieldnames=GUARDRAIL_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        panel_rows_present=bool(scenario_role_rows),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        scenario_role_rows=scenario_role_rows,
        metric_contract_rows=metric_contract_rows,
        target_panel_rows=target_panel_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        taxonomy_rows=taxonomy_rows,
        scenario_role_rows=scenario_role_rows,
        metric_contract_rows=metric_contract_rows,
        target_panel_rows=target_panel_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        scenario_role_rows=scenario_role_rows,
        metric_contract_rows=metric_contract_rows,
        target_panel_rows=target_panel_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        taxonomy_rows=taxonomy_rows,
        scenario_role_rows=scenario_role_rows,
        metric_contract_rows=metric_contract_rows,
        target_panel_rows=target_panel_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_accounting_rows": output_dir / "source_accounting_rows.csv",
        "scenario_role_rows": output_dir / "scenario_role_rows.csv",
        "metric_contract_rows": output_dir / "metric_contract_rows.csv",
        "target_panel_rows": output_dir / "target_panel_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2740_dir: Path,
    m2742_design: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2742_design_doc": m2742_design,
        "route_plan": route_plan,
        "m2740_summary": m2740_dir / "summary.json",
        "m2740_taxonomy_rows": m2740_dir / "taxonomy_rows.csv",
        "m2740_taxonomy_aggregate_rows": m2740_dir / "taxonomy_aggregate_rows.csv",
        "m2740_source_family_context_rows": m2740_dir / "source_family_context_rows.csv",
        "m2740_task_family_context_rows": m2740_dir / "task_family_context_rows.csv",
        "m2740_guardrail_context_rows": m2740_dir / "guardrail_context_rows.csv",
        "m2740_actor_contract_join_rows": m2740_dir / "actor_contract_join_rows.csv",
        "m2740_claim_boundary_rows": m2740_dir / "claim_boundary_rows.csv",
        "m2740_gate_matrix": m2740_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2742_design_text": paths["m2742_design_doc"].read_text(encoding="utf-8")
        if source_exists["m2742_design_doc"]
        else "",
        "route_plan_text": paths["route_plan"].read_text(encoding="utf-8") if source_exists["route_plan"] else "",
        "m2740_summary": read_json(paths["m2740_summary"]) if source_exists["m2740_summary"] else {},
        "taxonomy_rows": read_csv_rows(paths["m2740_taxonomy_rows"]),
        "taxonomy_aggregate_rows": read_csv_rows(paths["m2740_taxonomy_aggregate_rows"]),
        "source_family_context_rows": read_csv_rows(paths["m2740_source_family_context_rows"]),
        "task_family_context_rows": read_csv_rows(paths["m2740_task_family_context_rows"]),
        "guardrail_context_rows": read_csv_rows(paths["m2740_guardrail_context_rows"]),
        "actor_contract_join_rows": read_csv_rows(paths["m2740_actor_contract_join_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2740_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2740_gate_matrix"]),
    }


def build_source_accounting_rows(*, source: dict[str, Any]) -> list[dict[str, Any]]:
    row_counts = {
        "m2740_taxonomy_rows": len(source["taxonomy_rows"]),
        "m2740_taxonomy_aggregate_rows": len(source["taxonomy_aggregate_rows"]),
        "m2740_source_family_context_rows": len(source["source_family_context_rows"]),
        "m2740_task_family_context_rows": len(source["task_family_context_rows"]),
        "m2740_guardrail_context_rows": len(source["guardrail_context_rows"]),
        "m2740_actor_contract_join_rows": len(source["actor_contract_join_rows"]),
        "m2740_claim_boundary_rows": len(source["claim_boundary_rows"]),
        "m2740_gate_matrix": len(source["gate_matrix"]),
    }
    return [
        {
            "source_id": f"m2743-source-{index:04d}",
            "source_family": key,
            "path": str(path),
            "present": bool(source["source_exists"].get(key, False)),
            "row_count": row_counts.get(key, ""),
            "status_pass": bool(source["source_exists"].get(key, False)),
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (key, path) in enumerate(source["paths"].items(), start=1)
    ]


def build_scenario_role_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for taxonomy_family, role in sorted(ROLE_BY_TAXONOMY.items(), key=lambda item: ROLE_PRIORITY[item[1]]):
        group_rows = [row for row in taxonomy_rows if row.get("taxonomy_family") == taxonomy_family]
        execution_rows = [row for row in group_rows if row.get("source_row_type") == "candidate_execution"]
        guardrail_rows = [row for row in group_rows if row.get("source_row_type") != "candidate_execution"]
        is_target = role == "offtrack_containment_target"
        rows.append(
            {
                "scenario_role_id": f"m2743-role-{ROLE_PRIORITY[role]:04d}",
                "scenario_role": role,
                "source_taxonomy_family": taxonomy_family,
                "source_row_type": dominant_source_type(group_rows),
                "source_row_count": len(group_rows),
                "execution_taxonomy_row_count": len(execution_rows),
                "guardrail_taxonomy_row_count": len(guardrail_rows),
                "target_panel_admitted_count": len(group_rows) if is_target else 0,
                "collision_caution_count": len(group_rows) if role == "collision_caution_guard" else 0,
                "diagnostic_success_context_count": len(group_rows) if role == "diagnostic_success_context" else 0,
                "negative_context_guard_count": len(group_rows) if role == "negative_context_guardrail" else 0,
                "blocked_same_surface_guard_count": len(group_rows) if role == "blocked_same_surface_guard" else 0,
                "protected_hf3_exclusion_count": len(group_rows) if role == "protected_hf3_exclusion_guard" else 0,
                "execution_scheduled": False,
                "guardrail_only": role != "offtrack_containment_target",
                "actor_visible_allowed": False,
                "scenario_role_labels_actor_visible": False,
                "ranking_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_metric_contract_rows(scenario_role_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, role_row in enumerate(scenario_role_rows, start=1):
        role = str(role_row["scenario_role"])
        rows.append(
            {
                "metric_contract_id": f"m2743-metric-contract-{index:04d}",
                "scenario_role_id": role_row["scenario_role_id"],
                "scenario_role": role,
                "source_taxonomy_family": role_row["source_taxonomy_family"],
                "source_row_count": role_row["source_row_count"],
                "metric_family": METRIC_FAMILY_BY_ROLE[role],
                "metric_names": METRIC_NAMES_BY_ROLE[role],
                "metric_source": "M2740 taxonomy rows only; unavailable telemetry must remain unavailable",
                "row_level_binding_required": role in {
                    "offtrack_containment_target",
                    "collision_caution_guard",
                    "diagnostic_success_context",
                },
                "target_panel_admission_policy": "admit_offtrack_only" if role == "offtrack_containment_target" else "guardrail_or_context_only",
                "guardrail_only": role != "offtrack_containment_target",
                "actor_visible_allowed": False,
                "metric_labels_actor_visible": False,
                "ranking_allowed": False,
                "success_rate_verdict_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_panel_rows(
    taxonomy_rows: list[dict[str, Any]], *, scenario_role_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    role_id_by_role = {row["scenario_role"]: row["scenario_role_id"] for row in scenario_role_rows}
    rows: list[dict[str, Any]] = []
    execution_rows = [row for row in taxonomy_rows if row.get("source_row_type") == "candidate_execution"]
    for index, row in enumerate(execution_rows, start=1):
        taxonomy_family = str(row.get("taxonomy_family", ""))
        role = ROLE_BY_TAXONOMY.get(taxonomy_family, "other_diagnostic_context")
        admitted = role == "offtrack_containment_target"
        rows.append(
            {
                "target_panel_id": f"m2743-target-panel-{index:04d}",
                "source_taxonomy_id": row.get("taxonomy_id", ""),
                "scenario_role_id": role_id_by_role.get(role, ""),
                "scenario_role": role,
                "source_row_type": row.get("source_row_type", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_family": row.get("source_family", ""),
                "source_key": row.get("source_key", ""),
                "workload_id": row.get("workload_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": row.get("task_family", ""),
                "taxonomy_family": taxonomy_family,
                "primary_failure_family": row.get("primary_failure_family", ""),
                "repair_signal": row.get("repair_signal", ""),
                "target_panel_admitted": admitted,
                "execution_scheduled": False,
                "guardrail_only": not admitted,
                "actor_visible_allowed": False,
                "target_labels_actor_visible": False,
                "ranking_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(
    taxonomy_rows: list[dict[str, Any]], *, scenario_role_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    role_id_by_role = {row["scenario_role"]: row["scenario_role_id"] for row in scenario_role_rows}
    guard_roles = {
        "collision_caution_guard",
        "diagnostic_success_context",
        "negative_context_guardrail",
        "blocked_same_surface_guard",
        "protected_hf3_exclusion_guard",
    }
    rows = []
    for index, role in enumerate(sorted(guard_roles, key=lambda item: ROLE_PRIORITY[item]), start=1):
        taxonomy_family = next(key for key, value in ROLE_BY_TAXONOMY.items() if value == role)
        group_rows = [row for row in taxonomy_rows if row.get("taxonomy_family") == taxonomy_family]
        rows.append(
            {
                "guardrail_context_id": f"m2743-guardrail-context-{index:04d}",
                "scenario_role_id": role_id_by_role.get(role, ""),
                "scenario_role": role,
                "source_taxonomy_family": taxonomy_family,
                "source_row_type": dominant_source_type(group_rows),
                "row_count": len(group_rows),
                "execution_run_count": sum(bool_value(row.get("execution_run", False)) for row in group_rows if row.get("source_row_type") != "candidate_execution"),
                "execution_admitted_count": sum(bool_value(row.get("execution_admitted", False)) for row in group_rows if row.get("source_row_type") != "candidate_execution"),
                "protected_denominator_count": sum(bool_value(row.get("protected_rows_in_success_denominator", False)) for row in group_rows),
                "actor_visible_count": sum(bool_value(row.get("actor_visible_allowed", False)) for row in group_rows),
                "guardrail_only": True,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: dict[str, Any],
    scenario_role_rows: list[dict[str, Any]],
    metric_contract_rows: list[dict[str, Any]],
    target_panel_rows: list[dict[str, Any]],
    guardrail_context_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("observation_shape", P0_OBSERVATION_DIM, 72, False),
        actor_guard("action_shape", ACTION_DIM, 3, False),
        actor_guard("hidden_oracle_actor_input_detected", hidden_oracle_detected(source), False, False),
        actor_guard("scenario_role_labels_actor_visible", any_bool(scenario_role_rows, "scenario_role_labels_actor_visible"), False, False),
        actor_guard("metric_labels_actor_visible", any_bool(metric_contract_rows, "metric_labels_actor_visible"), False, False),
        actor_guard("target_labels_actor_visible", any_bool(target_panel_rows, "target_labels_actor_visible"), False, False),
        actor_guard("protected_labels_actor_visible", False, False, False),
        actor_guard("blocker_labels_actor_visible", False, False, False),
        actor_guard("route_decision_labels_actor_visible", False, False, False),
        actor_guard("success_progress_verdict_labels_actor_visible", False, False, False),
        actor_guard("source_family_ranking_allowed", False, False, False),
        actor_guard("task_family_ranking_allowed", False, False, False),
        actor_guard("profile_ranking_allowed", False, False, False),
        actor_guard("execution_scheduled", any_bool(target_panel_rows, "execution_scheduled"), False, False),
        actor_guard(
            "protected_rows_in_success_denominator",
            any_bool(guardrail_context_rows, "ordinary_success_denominator_allowed"),
            False,
            False,
        ),
        actor_guard(
            "m2740_actor_join_rows_pass",
            all(bool_value(row.get("status_pass")) for row in source["actor_contract_join_rows"]),
            True,
            False,
        ),
    ]


def actor_guard(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "guard_id": f"m2743-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    panel_rows_present: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("scenario_role_panel_materialized", "artifact", panel_rows_present, "scenario_role_rows.csv"),
        ("metric_contracts_materialized", "artifact", required_artifacts_present, "metric_contract_rows.csv"),
        ("target_panel_materialized", "artifact", required_artifacts_present, "target_panel_rows.csv"),
        ("guardrail_context_materialized", "contract", required_artifacts_present, "guardrail_context_rows.csv"),
        ("actor_contract_guards_materialized", "contract", required_artifacts_present, "actor_contract_guard_rows.csv"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2744 result-audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future execution manifest"),
        ("policy_action_execution", "execution", "future execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("source_build_or_adapter_probe", "execution", "future source route"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2743"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("source_family_ranking", "ranking", "future audited comparison interpretation"),
        ("task_family_ranking", "ranking", "future audited comparison interpretation"),
        ("profile_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2743_{claim_id}",
        "claim_family": family,
        "allowed_in_m2743": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    taxonomy_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    metric_contract_rows: list[dict[str, Any]],
    target_panel_rows: list[dict[str, Any]],
    guardrail_context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2743"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2743"])]
    execution_taxonomy_rows = [row for row in taxonomy_rows if row.get("source_row_type") == "candidate_execution"]
    offtrack_targets = [row for row in target_panel_rows if row["scenario_role"] == "offtrack_containment_target"]
    collision_context = [row for row in target_panel_rows if row["scenario_role"] == "collision_caution_guard"]
    success_context = [row for row in target_panel_rows if row["scenario_role"] == "diagnostic_success_context"]
    role_counts = {row["scenario_role"]: int(row["source_row_count"]) for row in scenario_role_rows}
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2740/M2742/route/follow-up artifacts present", "lineage_invalid"),
        ("m2742_admits_materialization", "lineage", "admit_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization" in source["m2742_design_text"], "decision present", "decision present", "lineage_invalid"),
        ("route_plan_scenario_role_artifact", "lineage", "scenario-role metric report" in source["route_plan_text"], "scenario-role metric report", "scenario-role metric report", "lineage_invalid"),
        ("m2740_status_pass", "lineage", bool_value(source["m2740_summary"].get("status_pass", False)), source["m2740_summary"].get("status_pass"), True, "lineage_invalid"),
        ("taxonomy_row_count", "artifact", len(taxonomy_rows) == EXPECTED_TAXONOMY_ROW_COUNT, len(taxonomy_rows), EXPECTED_TAXONOMY_ROW_COUNT, "metric_artifact"),
        ("execution_taxonomy_row_count", "artifact", len(execution_taxonomy_rows) == EXPECTED_EXECUTION_TAXONOMY_ROW_COUNT, len(execution_taxonomy_rows), EXPECTED_EXECUTION_TAXONOMY_ROW_COUNT, "metric_artifact"),
        ("scenario_role_count", "artifact", len(scenario_role_rows) == EXPECTED_SCENARIO_ROLE_COUNT, len(scenario_role_rows), EXPECTED_SCENARIO_ROLE_COUNT, "metric_artifact"),
        ("metric_contract_count", "artifact", len(metric_contract_rows) == len(scenario_role_rows), len(metric_contract_rows), len(scenario_role_rows), "metric_artifact"),
        ("offtrack_target_count", "artifact", len(offtrack_targets) == EXPECTED_OFFTRACK_TARGET_COUNT and role_counts.get("offtrack_containment_target") == EXPECTED_OFFTRACK_TARGET_COUNT, f"target_rows={len(offtrack_targets)} role_rows={role_counts.get('offtrack_containment_target')}", EXPECTED_OFFTRACK_TARGET_COUNT, "metric_artifact"),
        ("collision_caution_count", "artifact", len(collision_context) == EXPECTED_COLLISION_CAUTION_COUNT and role_counts.get("collision_caution_guard") == EXPECTED_COLLISION_CAUTION_COUNT, f"target_rows={len(collision_context)} role_rows={role_counts.get('collision_caution_guard')}", EXPECTED_COLLISION_CAUTION_COUNT, "metric_artifact"),
        ("diagnostic_success_context_count", "artifact", len(success_context) == EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_COUNT and role_counts.get("diagnostic_success_context") == EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_COUNT, f"target_rows={len(success_context)} role_rows={role_counts.get('diagnostic_success_context')}", EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_COUNT, "metric_artifact"),
        ("negative_context_guard_count", "artifact", role_counts.get("negative_context_guardrail") == EXPECTED_NEGATIVE_CONTEXT_GUARD_COUNT, role_counts.get("negative_context_guardrail"), EXPECTED_NEGATIVE_CONTEXT_GUARD_COUNT, "metric_artifact"),
        ("blocked_same_surface_guard_count", "artifact", role_counts.get("blocked_same_surface_guard") == EXPECTED_BLOCKED_SAME_SURFACE_GUARD_COUNT, role_counts.get("blocked_same_surface_guard"), EXPECTED_BLOCKED_SAME_SURFACE_GUARD_COUNT, "metric_artifact"),
        ("protected_hf3_exclusion_count", "artifact", role_counts.get("protected_hf3_exclusion_guard") == EXPECTED_PROTECTED_HF3_EXCLUSION_COUNT, role_counts.get("protected_hf3_exclusion_guard"), EXPECTED_PROTECTED_HF3_EXCLUSION_COUNT, "metric_artifact"),
        ("offtrack_rows_admitted_only", "contract", all(bool_value(row["target_panel_admitted"]) for row in offtrack_targets) and not any(bool_value(row["target_panel_admitted"]) for row in collision_context + success_context), "only offtrack target rows admitted", "all collision/success false", "contract_violation"),
        ("no_execution_scheduled", "execution_guardrail", not any_bool(target_panel_rows + scenario_role_rows, "execution_scheduled"), "no execution scheduled", "all false", "objective_overfit"),
        ("guardrail_context_preserved", "contract", guardrail_context_preserved(guardrail_context_rows), f"rows={len(guardrail_context_rows)}", "all guardrails actor-invisible outside denominators", "contract_violation"),
        ("labels_actor_invisible", "contract", labels_actor_invisible(scenario_role_rows, metric_contract_rows, target_panel_rows), "role metric target labels actor-invisible", "all false", "contract_violation"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_rows)}", "all actor guards pass", "contract_violation"),
        ("source_task_profile_nonranking", "claim_boundary", not any_bool(scenario_role_rows + metric_contract_rows + target_panel_rows, "ranking_allowed"), "no ranking allowed", "all false", "proof_washout"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status, observed, expected, failure_type) for gate_id, family, status, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2743_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    taxonomy_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    metric_contract_rows: list[dict[str, Any]],
    target_panel_rows: list[dict[str, Any]],
    guardrail_context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    role_counts = {row["scenario_role"]: int(row["source_row_count"]) for row in scenario_role_rows}
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2740_status_pass": bool_value(source["m2740_summary"].get("status_pass", False)),
        "taxonomy_row_count": len(taxonomy_rows),
        "execution_taxonomy_row_count": len([row for row in taxonomy_rows if row.get("source_row_type") == "candidate_execution"]),
        "scenario_role_row_count": len(scenario_role_rows),
        "metric_contract_row_count": len(metric_contract_rows),
        "target_panel_row_count": len(target_panel_rows),
        "offtrack_target_row_count": role_counts.get("offtrack_containment_target", 0),
        "collision_caution_row_count": role_counts.get("collision_caution_guard", 0),
        "diagnostic_success_context_row_count": role_counts.get("diagnostic_success_context", 0),
        "negative_context_guardrail_row_count": role_counts.get("negative_context_guardrail", 0),
        "blocked_same_surface_guard_row_count": role_counts.get("blocked_same_surface_guard", 0),
        "protected_hf3_exclusion_guard_row_count": role_counts.get("protected_hf3_exclusion_guard", 0),
        "guardrail_context_row_count": len(guardrail_context_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(bool_value(row["status_pass"]) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": hidden_oracle_detected(source),
        "scenario_role_labels_actor_visible": any_bool(scenario_role_rows, "scenario_role_labels_actor_visible"),
        "metric_labels_actor_visible": any_bool(metric_contract_rows, "metric_labels_actor_visible"),
        "target_labels_actor_visible": any_bool(target_panel_rows, "target_labels_actor_visible"),
        "ranking_allowed": any_bool(scenario_role_rows + metric_contract_rows + target_panel_rows, "ranking_allowed"),
        "execution_scheduled": any_bool(target_panel_rows + scenario_role_rows, "execution_scheduled"),
        "protected_rows_in_success_denominator": any_bool(guardrail_context_rows, "ordinary_success_denominator_allowed"),
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2743 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scenario role rows: {summary['scenario_role_row_count']}",
            f"- metric contract rows: {summary['metric_contract_row_count']}",
            f"- target panel rows: {summary['target_panel_row_count']}",
            f"- offtrack target rows: {summary['offtrack_target_row_count']}",
            f"- collision caution rows: {summary['collision_caution_row_count']}",
            f"- diagnostic success context rows: {summary['diagnostic_success_context_row_count']}",
            f"- negative-context guard rows: {summary['negative_context_guardrail_row_count']}",
            f"- same-surface blocked guard rows: {summary['blocked_same_surface_guard_row_count']}",
            f"- protected/HF3 exclusion guard rows: {summary['protected_hf3_exclusion_guard_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2743 materializes actor-invisible scenario-role metric panel artifacts from existing M2740 taxonomy rows only. It does not execute environments, train, validate, rank, or claim driver performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Artifacts",
            "",
            *[f"- {key}: `{value}`" for key, value in summary["paths"].items()],
            "",
            "## Next",
            "",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
        ]
    )


def dominant_source_type(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    counts = Counter(str(row.get("source_row_type", "")) for row in rows)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def labels_actor_invisible(
    scenario_role_rows: list[dict[str, Any]],
    metric_contract_rows: list[dict[str, Any]],
    target_panel_rows: list[dict[str, Any]],
) -> bool:
    return not any_bool(scenario_role_rows, "scenario_role_labels_actor_visible") and not any_bool(
        metric_contract_rows, "metric_labels_actor_visible"
    ) and not any_bool(target_panel_rows, "target_labels_actor_visible")


def guardrail_context_preserved(guardrail_context_rows: list[dict[str, Any]]) -> bool:
    return bool(guardrail_context_rows) and all(
        int(row["protected_denominator_count"]) == 0
        and int(row["actor_visible_count"]) == 0
        and not bool_value(row["ordinary_success_denominator_allowed"])
        for row in guardrail_context_rows
    )


def hidden_oracle_detected(source: dict[str, Any]) -> bool:
    summary = source["m2740_summary"]
    if bool_value(summary.get("hidden_oracle_actor_input_detected", False)):
        return True
    actor_rows = source["actor_contract_join_rows"]
    for row in actor_rows:
        if row.get("contract_field") == "hidden_oracle_actor_input_detected":
            return bool_value(row.get("observed_value", False))
    return False


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def any_bool(rows: list[dict[str, Any]], key: str) -> bool:
    return any(bool_value(row.get(key, False)) for row in rows)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2740-dir", type=Path, default=DEFAULT_M2740_DIR)
    parser.add_argument("--m2742-design", type=Path, default=DEFAULT_M2742_DESIGN)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)

    summary = materialize_source_diverse_failure_taxonomy_scenario_role_metric_panel(
        m2740_dir=args.m2740_dir,
        m2742_design=args.m2742_design,
        route_plan=args.route_plan,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"scenario_role_row_count={summary['scenario_role_row_count']}")
    print(f"offtrack_target_row_count={summary['offtrack_target_row_count']}")
    print(f"protected_hf3_exclusion_guard_row_count={summary['protected_hf3_exclusion_guard_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
