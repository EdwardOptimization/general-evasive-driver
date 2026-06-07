"""Materialize M3022 broad-failure objective-contract rows.

M3022 consumes the accepted M3018/M3019/M3020/M3021 Route A new-source
localization artifacts. It performs no reset, step, rollout, replay,
validation, training, target fitting, ranking, promotion, checkpoint mutation,
or profile tuning. It writes machine-checkable objective-family, row
assignment, guard, claim-boundary, gate, summary, doc, and M3023 audit
artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3022-engineering-controller-route-a-post-residual-stop-new-source-"
    "broad-failure-objective-contract-materialization-preflight"
)
NEXT_ID = (
    "m3023-engineering-controller-route-a-post-residual-stop-new-source-"
    "broad-failure-objective-contract-materialization-result-audit"
)
M3018_ID = (
    "m3018-engineering-controller-route-a-post-residual-stop-new-source-"
    "failure-localization-materialization-preflight"
)
M3019_ID = (
    "m3019-engineering-controller-route-a-post-residual-stop-new-source-"
    "failure-localization-materialization-result-audit"
)
M3020_ID = (
    "m3020-engineering-controller-route-a-post-residual-stop-new-source-"
    "failure-localization-result-synthesis"
)
M3021_ID = (
    "m3021-engineering-controller-route-a-post-residual-stop-new-source-"
    "broad-failure-objective-admission-design"
)

DEFAULT_M3018_DIR = Path(
    "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_"
    "failure_localization_materialization_preflight"
)
DEFAULT_M3019_AUDIT = Path(f"docs/{M3019_ID}.md")
DEFAULT_M3020_SYNTHESIS = Path(f"docs/{M3020_ID}.md")
DEFAULT_M3021_DESIGN = Path(f"docs/{M3021_ID}.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_"
    "broad_failure_objective_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_LOCALIZATION_ROWS = 32
EXPECTED_PROFILE_SOURCE_AGGREGATE_ROWS = 32
EXPECTED_TASK_SOURCE_COUNT = 16
EXPECTED_PROFILE_BINDING_COUNT = 2
EXPECTED_OBJECTIVE_FAMILY_COUNTS = {
    "offtrack_recovery_broad_failure_contract": 22,
    "collision_clearance_guard_contract": 5,
    "speed_floor_guard_contract": 2,
    "success_identity_context_guard": 3,
}
EXPECTED_FAILURE_FAMILY_COUNTS = {
    "collision_clearance_failure": 5,
    "offtrack_high_severity_recovery_failure": 5,
    "offtrack_recovery_failure": 17,
    "speed_floor_context": 2,
    "success_context": 3,
}

CLAIM_SCOPE = (
    "M3022 Route A post-residual-stop new-source broad-failure objective-"
    "contract materialization only; existing M3018 localization rows may be "
    "grouped into objective-family, component, row-assignment, profile/source "
    "guard, actor guard, claim-boundary, and gate artifacts. No reset, step, "
    "rollout, replay, validation, target materialization, fitting, training, "
    "PPO, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, profile tuning, repair target selection, validation result, "
    "repair success, driver performance, paper, current-sim verdict, "
    "high-fidelity validation, finite-window-vs-GRU, full ideal driver, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target materialization, residual fitting, repair execution, validation "
    "result, repair success, driver performance, current-sim verdict, paper "
    "evidence, high-fidelity validation readiness or result, finite-window-vs-"
    "GRU conclusion, full ideal driver completion, level3 self-identification, "
    "controller/profile ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, profile tuning, training, replay, or PPO"
)

PATH_KEYS = [
    "summary",
    "objective_family_rows",
    "objective_component_rows",
    "row_assignment_rows",
    "profile_source_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

OBJECTIVE_FAMILY_FIELDNAMES = [
    "objective_family",
    "source_failure_family",
    "source_row_count",
    "source_task_source_count",
    "source_profile_binding_count",
    "admitted_for_contract_materialization",
    "future_target_materialization_manifest_required",
    "future_fitting_manifest_required",
    "future_execution_manifest_required",
    "training_scheduled",
    "execution_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "validation_denominator_allowed",
    "performance_claim_allowed",
    "paper_claim_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_input_change_required",
    "actor_visible_labels_required",
    "claim_boundary",
]

OBJECTIVE_COMPONENT_FIELDNAMES = [
    "component_id",
    "objective_family",
    "component_role",
    "source_failure_family",
    "source_row_count",
    "source_task_source_count",
    "source_profile_binding_count",
    "guard_context",
    "admitted_for_contract_materialization",
    "future_target_materialization_manifest_required",
    "training_scheduled",
    "execution_scheduled",
    "claim_boundary",
]

ROW_ASSIGNMENT_FIELDNAMES = [
    "row_assignment_id",
    "source_localization_row_id",
    "source_episode_row_index",
    "task_source_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "executable_source_family",
    "env_template_family",
    "outcome_family",
    "failure_family",
    "primary_failure_mode",
    "objective_family",
    "component_role",
    "guard_status",
    "diagnostic_success",
    "diagnostic_non_success",
    "preserve_row",
    "actor_visible_label_allowed",
    "future_target_materialization_allowed",
    "training_scheduled",
    "execution_scheduled",
    "validation_denominator_allowed",
    "performance_claim_allowed",
    "paper_claim_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]

PROFILE_SOURCE_GUARD_FIELDNAMES = [
    "profile_source_guard_id",
    "source_aggregate_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "task_source_id",
    "task_family",
    "source_edge",
    "window_tag",
    "scheduled_count",
    "episode_count",
    "accounted_count",
    "success_count",
    "collision_count",
    "obstacle_collision_termination_count",
    "offtrack_count",
    "speed_too_low_count",
    "blank_termination_count",
    "non_success_count",
    "dominant_failure_family",
    "objective_family",
    "guard_status",
    "preserve_as_guard_context",
    "ranking_allowed",
    "validation_denominator_allowed",
    "performance_claim_allowed",
    "claim_boundary",
]

ACTOR_CONTRACT_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "status_pass",
    "observed",
    "expected",
    "actor_input_change_required",
    "actor_visible_label_allowed",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3022",
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

OBJECTIVE_DEFS = {
    "offtrack_recovery_broad_failure_contract": {
        "failure_families": [
            "offtrack_recovery_failure",
            "offtrack_high_severity_recovery_failure",
        ],
        "component_role": "primary_recovery",
        "guard_status": "failure_pressure",
        "source_failure_family": "offtrack_recovery_failure|offtrack_high_severity_recovery_failure",
        "guard_context": False,
    },
    "collision_clearance_guard_contract": {
        "failure_families": ["collision_clearance_failure"],
        "component_role": "secondary_safety",
        "guard_status": "safety_guard",
        "source_failure_family": "collision_clearance_failure",
        "guard_context": True,
    },
    "speed_floor_guard_contract": {
        "failure_families": ["speed_floor_context"],
        "component_role": "speed_floor_guard",
        "guard_status": "speed_guard",
        "source_failure_family": "speed_floor_context",
        "guard_context": True,
    },
    "success_identity_context_guard": {
        "failure_families": ["success_context"],
        "component_role": "success_identity_guard",
        "guard_status": "success_identity_guard",
        "source_failure_family": "success_context",
        "guard_context": True,
    },
}


def run_new_source_broad_failure_objective_contract_materialization_preflight(
    *,
    m3018_dir: Path | str = DEFAULT_M3018_DIR,
    m3019_audit: Path | str = DEFAULT_M3019_AUDIT,
    m3020_synthesis: Path | str = DEFAULT_M3020_SYNTHESIS,
    m3021_design: Path | str = DEFAULT_M3021_DESIGN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3018_dir=Path(m3018_dir),
        m3019_audit=Path(m3019_audit),
        m3020_synthesis=Path(m3020_synthesis),
        m3021_design=Path(m3021_design),
        follow_up_manifest=Path(follow_up_manifest),
    )

    localization_rows = source["failure_localization_rows"]
    aggregate_rows = source["profile_source_aggregate_rows"]
    objective_family_rows = build_objective_family_rows(localization_rows)
    objective_component_rows = build_objective_component_rows(localization_rows)
    row_assignment_rows = build_row_assignment_rows(localization_rows)
    profile_source_guard_rows = build_profile_source_guard_rows(aggregate_rows)
    actor_guard_rows = build_actor_contract_guard_rows(source=source, row_assignment_rows=row_assignment_rows)

    write_csv_rows(paths["objective_family_rows"], objective_family_rows, fieldnames=OBJECTIVE_FAMILY_FIELDNAMES)
    write_csv_rows(
        paths["objective_component_rows"],
        objective_component_rows,
        fieldnames=OBJECTIVE_COMPONENT_FIELDNAMES,
    )
    write_csv_rows(paths["row_assignment_rows"], row_assignment_rows, fieldnames=ROW_ASSIGNMENT_FIELDNAMES)
    write_csv_rows(
        paths["profile_source_guard_rows"],
        profile_source_guard_rows,
        fieldnames=PROFILE_SOURCE_GUARD_FIELDNAMES,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_CONTRACT_GUARD_FIELDNAMES)
    write_json(
        paths["follow_up_manifest"],
        build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]),
    )
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()
    write_run_state(
        paths["run_state"],
        {
            "localization_row_count": len(localization_rows),
            "profile_source_aggregate_row_count": len(aggregate_rows),
            "objective_family_row_count": len(objective_family_rows),
            "row_assignment_row_count": len(row_assignment_rows),
            "execution_performed_by_m3022": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    required_core_artifacts_present = all(
        paths[key].exists()
        for key in PATH_KEYS
        if key not in {"summary", "doc", "claim_boundary_rows", "gate_matrix"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_core_artifacts_present,
        objective_rows_present=bool(objective_family_rows),
        row_assignments_present=bool(row_assignment_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        profile_source_guard_rows=profile_source_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_core_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        profile_source_guard_rows=profile_source_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        objective_rows_present=bool(objective_family_rows),
        row_assignments_present=bool(row_assignment_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        profile_source_guard_rows=profile_source_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        profile_source_guard_rows=profile_source_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "localization_row_count": len(localization_rows),
            "profile_source_aggregate_row_count": len(aggregate_rows),
            "objective_family_row_count": len(objective_family_rows),
            "row_assignment_row_count": len(row_assignment_rows),
            "execution_performed_by_m3022": False,
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "objective_family_rows": output_dir / "objective_family_rows.csv",
        "objective_component_rows": output_dir / "objective_component_rows.csv",
        "row_assignment_rows": output_dir / "row_assignment_rows.csv",
        "profile_source_guard_rows": output_dir / "profile_source_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3018_dir: Path,
    m3019_audit: Path,
    m3020_synthesis: Path,
    m3021_design: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3019_audit": m3019_audit,
        "m3020_synthesis": m3020_synthesis,
        "m3021_design": m3021_design,
        "m3018_summary": m3018_dir / "summary.json",
        "failure_localization_rows": m3018_dir / "failure_localization_rows.csv",
        "profile_source_aggregate_rows": m3018_dir / "profile_source_aggregate_rows.csv",
        "m3018_claim_boundary_rows": m3018_dir / "claim_boundary_rows.csv",
        "m3018_gate_matrix": m3018_dir / "gate_matrix.csv",
        "m3018_run_state": m3018_dir / "run_state.json",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3019_audit_text": paths["m3019_audit"].read_text(encoding="utf-8")
        if source_exists["m3019_audit"]
        else "",
        "m3020_synthesis_text": paths["m3020_synthesis"].read_text(encoding="utf-8")
        if source_exists["m3020_synthesis"]
        else "",
        "m3021_design_text": paths["m3021_design"].read_text(encoding="utf-8")
        if source_exists["m3021_design"]
        else "",
        "m3018_summary": read_json(paths["m3018_summary"]) if source_exists["m3018_summary"] else {},
        "failure_localization_rows": read_csv_rows(paths["failure_localization_rows"])
        if source_exists["failure_localization_rows"]
        else [],
        "profile_source_aggregate_rows": read_csv_rows(paths["profile_source_aggregate_rows"])
        if source_exists["profile_source_aggregate_rows"]
        else [],
        "m3018_claim_boundary_rows": read_csv_rows(paths["m3018_claim_boundary_rows"])
        if source_exists["m3018_claim_boundary_rows"]
        else [],
        "m3018_gate_matrix": read_csv_rows(paths["m3018_gate_matrix"])
        if source_exists["m3018_gate_matrix"]
        else [],
        "m3018_run_state": read_json(paths["m3018_run_state"]) if source_exists["m3018_run_state"] else {},
    }


def build_objective_family_rows(localization_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for objective_family in OBJECTIVE_DEFS:
        family_rows = rows_for_objective(localization_rows, objective_family)
        rows.append(
            {
                "objective_family": objective_family,
                "source_failure_family": OBJECTIVE_DEFS[objective_family]["source_failure_family"],
                "source_row_count": len(family_rows),
                "source_task_source_count": len({row.get("task_source_id", "") for row in family_rows}),
                "source_profile_binding_count": len({row.get("profile_name", "") for row in family_rows}),
                "admitted_for_contract_materialization": True,
                "future_target_materialization_manifest_required": True,
                "future_fitting_manifest_required": True,
                "future_execution_manifest_required": True,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "validation_denominator_allowed": False,
                "performance_claim_allowed": False,
                "paper_claim_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_input_change_required": False,
                "actor_visible_labels_required": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_objective_component_rows(localization_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, objective_family in enumerate(OBJECTIVE_DEFS, start=1):
        definition = OBJECTIVE_DEFS[objective_family]
        family_rows = rows_for_objective(localization_rows, objective_family)
        rows.append(
            {
                "component_id": f"m3022-objective-component-{index:04d}",
                "objective_family": objective_family,
                "component_role": definition["component_role"],
                "source_failure_family": definition["source_failure_family"],
                "source_row_count": len(family_rows),
                "source_task_source_count": len({row.get("task_source_id", "") for row in family_rows}),
                "source_profile_binding_count": len({row.get("profile_name", "") for row in family_rows}),
                "guard_context": bool(definition["guard_context"]),
                "admitted_for_contract_materialization": True,
                "future_target_materialization_manifest_required": True,
                "training_scheduled": False,
                "execution_scheduled": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_row_assignment_rows(localization_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(localization_rows, start=1):
        objective_family = objective_for_failure_family(str(row.get("failure_family", "")))
        definition = OBJECTIVE_DEFS.get(objective_family, {})
        is_success_guard = objective_family == "success_identity_context_guard"
        rows.append(
            {
                "row_assignment_id": f"m3022-row-assignment-{index:04d}",
                "source_localization_row_id": row.get("localization_row_id", ""),
                "source_episode_row_index": row.get("source_episode_row_index", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "profile_binding_name": row.get("profile_binding_name", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "strata": row.get("strata", ""),
                "executable_source_family": row.get("executable_source_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "outcome_family": row.get("outcome_family", ""),
                "failure_family": row.get("failure_family", ""),
                "primary_failure_mode": row.get("primary_failure_mode", ""),
                "objective_family": objective_family,
                "component_role": definition.get("component_role", "unmapped"),
                "guard_status": definition.get("guard_status", "unmapped_failure_family"),
                "diagnostic_success": _bool(row.get("diagnostic_success", False)),
                "diagnostic_non_success": _bool(row.get("diagnostic_non_success", False)),
                "preserve_row": True,
                "actor_visible_label_allowed": False,
                "future_target_materialization_allowed": not is_success_guard,
                "training_scheduled": False,
                "execution_scheduled": False,
                "validation_denominator_allowed": False,
                "performance_claim_allowed": False,
                "paper_claim_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_profile_source_guard_rows(aggregate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(aggregate_rows, start=1):
        objective_family = objective_for_failure_family(str(row.get("dominant_failure_family", "")))
        definition = OBJECTIVE_DEFS.get(objective_family, {})
        rows.append(
            {
                "profile_source_guard_id": f"m3022-profile-source-guard-{index:04d}",
                "source_aggregate_id": row.get("aggregate_id", ""),
                "profile_name": row.get("profile_name", ""),
                "profile_binding_name": row.get("profile_binding_name", ""),
                "binding_role": row.get("binding_role", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "scheduled_count": row.get("scheduled_count", ""),
                "episode_count": row.get("episode_count", ""),
                "accounted_count": row.get("accounted_count", ""),
                "success_count": row.get("success_count", ""),
                "collision_count": row.get("collision_count", ""),
                "obstacle_collision_termination_count": row.get("obstacle_collision_termination_count", ""),
                "offtrack_count": row.get("offtrack_count", ""),
                "speed_too_low_count": row.get("speed_too_low_count", ""),
                "blank_termination_count": row.get("blank_termination_count", ""),
                "non_success_count": row.get("non_success_count", ""),
                "dominant_failure_family": row.get("dominant_failure_family", ""),
                "objective_family": objective_family,
                "guard_status": definition.get("guard_status", "unmapped_failure_family"),
                "preserve_as_guard_context": True,
                "ranking_allowed": False,
                "validation_denominator_allowed": False,
                "performance_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: dict[str, Any],
    row_assignment_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = source["m3018_summary"]
    checks = [
        (
            "actor_observation_shape",
            "contract_shape",
            int(summary.get("observation_shape", -1)) == P0_OBSERVATION_DIM,
            summary.get("observation_shape"),
            P0_OBSERVATION_DIM,
        ),
        (
            "actor_action_shape",
            "contract_shape",
            int(summary.get("action_shape", -1)) == ACTION_DIM,
            summary.get("action_shape"),
            ACTION_DIM,
        ),
        (
            "actor_input_contract_unchanged",
            "actor_input",
            not _bool(summary.get("actor_input_contract_changed", False)),
            summary.get("actor_input_contract_changed"),
            False,
        ),
        (
            "hidden_oracle_actor_input_absent",
            "actor_input",
            not _bool(summary.get("hidden_oracle_actor_input_detected", False)),
            summary.get("hidden_oracle_actor_input_detected"),
            False,
        ),
        (
            "future_target_actor_input_absent",
            "actor_input",
            not _bool(summary.get("future_target_actor_input_required", False)),
            summary.get("future_target_actor_input_required"),
            False,
        ),
        (
            "source_route_outcome_labels_actor_invisible",
            "actor_input",
            not any_label_visible(summary),
            actor_label_visibility(summary),
            "all false",
        ),
        (
            "ttc_actor_input_absent",
            "actor_input",
            not _bool(summary.get("ttc_actor_input_required", False)),
            summary.get("ttc_actor_input_required"),
            False,
        ),
        (
            "objective_labels_actor_invisible",
            "actor_input",
            not any(_bool(row.get("actor_visible_label_allowed", False)) for row in row_assignment_rows),
            "all row_assignment actor_visible_label_allowed false",
            False,
        ),
    ]
    return [
        {
            "guard_id": f"m3022_{guard_id}",
            "guard_family": guard_family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "actor_input_change_required": False,
            "actor_visible_label_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, guard_family, status_pass, observed, expected in checks
    ]


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    objective_rows_present: bool,
    row_assignments_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("objective_family_rows_materialized", "artifact", objective_rows_present, "objective_family_rows.csv"),
        ("objective_component_rows_materialized", "artifact", objective_rows_present, "objective_component_rows.csv"),
        ("row_assignment_rows_materialized", "artifact", row_assignments_present, "row_assignment_rows.csv"),
        ("profile_source_guard_rows_materialized", "artifact", artifacts_present, "profile_source_guard_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_materialized", "artifact", artifacts_present, "summary.json"),
        ("doc_materialized", "artifact", artifacts_present, f"docs/{MILESTONE_ID}.md"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3023 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_replay_execution", "execution", "future audited execution manifest"),
        ("target_materialization", "objective", "future audited target materialization manifest"),
        ("residual_fitting_or_training", "training", "future audited fitting or training manifest"),
        ("ppo_or_replay", "training", "future audited training manifest"),
        ("profile_specific_tuning", "execution", "future audited tuning route"),
        ("repair_target_selection", "repair", "future result audit before any repair target"),
        ("checkpoint_mutation_or_promotion", "promotion", "future promotion gate"),
        ("controller_or_profile_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcut inputs"),
    ]
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3022_{claim_id}",
        "claim_family": family,
        "allowed_in_m3022": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    objective_family_rows: list[dict[str, Any]],
    objective_component_rows: list[dict[str, Any]],
    row_assignment_rows: list[dict[str, Any]],
    profile_source_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    summary = source["m3018_summary"]
    localization_rows = source["failure_localization_rows"]
    aggregate_rows = source["profile_source_aggregate_rows"]
    objective_counts = Counter(str(row.get("objective_family", "")) for row in row_assignment_rows)
    failure_counts = Counter(str(row.get("failure_family", "")) for row in localization_rows)
    task_source_ids = {str(row.get("task_source_id", "")) for row in localization_rows if row.get("task_source_id")}
    profile_names = {str(row.get("profile_name", "")) for row in localization_rows if row.get("profile_name")}
    success_target_rows = [
        row
        for row in row_assignment_rows
        if row.get("objective_family") == "success_identity_context_guard"
        and _bool(row.get("future_target_materialization_allowed", True))
    ]
    forbidden_flags = forbidden_m3022_summary_flags(summary)
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M3018/M3019/M3020/M3021/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m3019_accepts_m3018",
            "lineage",
            "accepts M3018" in source["m3019_audit_text"],
            "accepts M3018" in source["m3019_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3020_admits_m3021",
            "lineage",
            M3021_ID in source["m3020_synthesis_text"],
            M3021_ID in source["m3020_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3021_admits_m3022",
            "lineage",
            MILESTONE_ID in source["m3021_design_text"],
            MILESTONE_ID in source["m3021_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3018_status_pass",
            "lineage",
            _bool(summary.get("status_pass", False))
            and _bool(summary.get("gate_matrix_pass", False))
            and _bool(summary.get("required_artifacts_present", False)),
            {
                "status_pass": summary.get("status_pass"),
                "gate_matrix_pass": summary.get("gate_matrix_pass"),
                "required_artifacts_present": summary.get("required_artifacts_present"),
            },
            "all true",
            "lineage_invalid",
        ),
        (
            "localization_rows_accounted",
            "denominator",
            len(localization_rows) == EXPECTED_LOCALIZATION_ROWS
            and len(row_assignment_rows) == len(localization_rows),
            {"localization_rows": len(localization_rows), "row_assignments": len(row_assignment_rows)},
            EXPECTED_LOCALIZATION_ROWS,
            "metric_artifact",
        ),
        (
            "profile_source_aggregate_rows_accounted",
            "denominator",
            len(aggregate_rows) == EXPECTED_PROFILE_SOURCE_AGGREGATE_ROWS
            and len(profile_source_guard_rows) == len(aggregate_rows),
            {"aggregate_rows": len(aggregate_rows), "profile_source_guards": len(profile_source_guard_rows)},
            EXPECTED_PROFILE_SOURCE_AGGREGATE_ROWS,
            "metric_artifact",
        ),
        (
            "task_source_denominator_preserved",
            "denominator",
            len(task_source_ids) == EXPECTED_TASK_SOURCE_COUNT,
            len(task_source_ids),
            EXPECTED_TASK_SOURCE_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "profile_binding_count_preserved",
            "denominator",
            len(profile_names) == EXPECTED_PROFILE_BINDING_COUNT,
            sorted(profile_names),
            EXPECTED_PROFILE_BINDING_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "objective_family_counts_match_expected",
            "objective_contract",
            dict(sorted(objective_counts.items())) == EXPECTED_OBJECTIVE_FAMILY_COUNTS,
            dict(sorted(objective_counts.items())),
            EXPECTED_OBJECTIVE_FAMILY_COUNTS,
            "metric_artifact",
        ),
        (
            "failure_family_counts_match_expected",
            "objective_contract",
            dict(sorted(failure_counts.items())) == EXPECTED_FAILURE_FAMILY_COUNTS,
            dict(sorted(failure_counts.items())),
            EXPECTED_FAILURE_FAMILY_COUNTS,
            "metric_artifact",
        ),
        (
            "objective_family_rows_complete",
            "objective_contract",
            len(objective_family_rows) == len(EXPECTED_OBJECTIVE_FAMILY_COUNTS),
            len(objective_family_rows),
            len(EXPECTED_OBJECTIVE_FAMILY_COUNTS),
            "metric_artifact",
        ),
        (
            "objective_component_rows_complete",
            "objective_contract",
            len(objective_component_rows) == len(EXPECTED_OBJECTIVE_FAMILY_COUNTS),
            len(objective_component_rows),
            len(EXPECTED_OBJECTIVE_FAMILY_COUNTS),
            "metric_artifact",
        ),
        (
            "success_context_guard_not_target",
            "objective_contract",
            not success_target_rows,
            f"success_target_rows={len(success_target_rows)}",
            "success rows are guard context only",
            "objective_overfit",
        ),
        (
            "actor_contract_preserved",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in actor_guard_rows),
            f"rows={len(actor_guard_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_guard_rows)}",
            "all actor guard rows pass",
            "contract_violation",
        ),
        (
            "no_m3022_execution_training_ranking_or_mutation",
            "contract",
            not forbidden_flags,
            forbidden_flags,
            "all false",
            "contract_violation",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row.get("status_pass", False)) for row in claim_rows),
            f"rows={len(claim_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in claim_rows)}",
            "all claim rows pass",
            "proof_washout",
        ),
        (
            "follow_up_manifest_registered",
            "lineage",
            source["source_exists"]["follow_up_manifest"],
            source["source_exists"]["follow_up_manifest"],
            True,
            "lineage_invalid",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m3022_{gate_id}",
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
    objective_family_rows: list[dict[str, Any]],
    objective_component_rows: list[dict[str, Any]],
    row_assignment_rows: list[dict[str, Any]],
    profile_source_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    localization_rows = source["failure_localization_rows"]
    aggregate_rows = source["profile_source_aggregate_rows"]
    objective_counts = Counter(str(row.get("objective_family", "")) for row in row_assignment_rows)
    failure_counts = Counter(str(row.get("failure_family", "")) for row in localization_rows)
    profile_counts = Counter(str(row.get("profile_name", "")) for row in localization_rows)
    task_family_counts = Counter(str(row.get("task_family", "")) for row in localization_rows)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    claim_boundary_rows_pass = all(_bool(row.get("status_pass", False)) for row in claim_rows)
    actor_contract_guard_rows_pass = all(_bool(row.get("status_pass", False)) for row in actor_guard_rows)
    status_pass = bool(
        gate_matrix_pass
        and claim_boundary_rows_pass
        and actor_contract_guard_rows_pass
        and required_artifacts_present
    )
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "new_source_broad_failure_objective_contract_materialization_preflight_complete"
            if status_pass
            else "new_source_broad_failure_objective_contract_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3018_status_pass": _bool(source["m3018_summary"].get("status_pass", False)),
        "m3018_gate_matrix_pass": _bool(source["m3018_summary"].get("gate_matrix_pass", False)),
        "m3018_required_artifacts_present": _bool(
            source["m3018_summary"].get("required_artifacts_present", False)
        ),
        "source_spec_count": int(source["m3018_summary"].get("source_spec_count", 0)),
        "unique_task_source_count": len({row.get("task_source_id", "") for row in localization_rows}),
        "target_task_source_count": EXPECTED_TASK_SOURCE_COUNT,
        "profile_binding_count": len({row.get("profile_name", "") for row in localization_rows}),
        "target_profile_binding_count": EXPECTED_PROFILE_BINDING_COUNT,
        "failure_localization_row_count": len(localization_rows),
        "target_failure_localization_row_count": EXPECTED_LOCALIZATION_ROWS,
        "profile_source_aggregate_row_count": len(aggregate_rows),
        "target_profile_source_aggregate_row_count": EXPECTED_PROFILE_SOURCE_AGGREGATE_ROWS,
        "objective_family_row_count": len(objective_family_rows),
        "objective_component_row_count": len(objective_component_rows),
        "row_assignment_row_count": len(row_assignment_rows),
        "profile_source_guard_row_count": len(profile_source_guard_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "objective_family_counts": dict(sorted(objective_counts.items())),
        "target_objective_family_counts": EXPECTED_OBJECTIVE_FAMILY_COUNTS,
        "failure_family_counts": dict(sorted(failure_counts.items())),
        "target_failure_family_counts": EXPECTED_FAILURE_FAMILY_COUNTS,
        "profile_counts": dict(sorted(profile_counts.items())),
        "task_family_counts": dict(sorted(task_family_counts.items())),
        "success_context_guard_row_count": int(objective_counts.get("success_identity_context_guard", 0)),
        "success_context_future_target_materialization_allowed_count": sum(
            1
            for row in row_assignment_rows
            if row.get("objective_family") == "success_identity_context_guard"
            and _bool(row.get("future_target_materialization_allowed", True))
        ),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_boundary_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "actor_contract_guard_rows_pass": actor_contract_guard_rows_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "target_materialization_run": False,
        "fitting_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "ranking_run": False,
        "winner_selected": False,
        "repair_target_selected": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "objective_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "success_rate_metric_recorded": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
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
            "# M3022 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Objective Contract Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- localization rows: {summary['failure_localization_row_count']}/{summary['target_failure_localization_row_count']}",
            f"- profile/source aggregate rows: {summary['profile_source_aggregate_row_count']}/{summary['target_profile_source_aggregate_row_count']}",
            f"- task_source ids: {summary['unique_task_source_count']}/{summary['target_task_source_count']}",
            f"- profile bindings: {summary['profile_binding_count']}/{summary['target_profile_binding_count']}",
            f"- objective family rows: {summary['objective_family_row_count']}",
            f"- objective component rows: {summary['objective_component_row_count']}",
            f"- row assignments: {summary['row_assignment_row_count']}",
            f"- profile/source guard rows: {summary['profile_source_guard_row_count']}",
            f"- objective family counts: {summary['objective_family_counts']}",
            f"- failure family counts: {summary['failure_family_counts']}",
            f"- success-context guard rows: {summary['success_context_guard_row_count']}",
            f"- success-context future target rows: {summary['success_context_future_target_materialization_allowed_count']}",
            f"- actor contract guard pass: {summary['actor_contract_guard_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- required artifacts present: {summary['required_artifacts_present']}",
            "",
            "## Boundary",
            "",
            "M3022 materializes objective-contract metadata from existing M3018 rows only. It does not rerun environments, materialize numeric targets, fit, train, rank, promote, mutate checkpoints, tune profiles, validate, select a repair target, or claim performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Interpretation",
            "",
            "The output contract preserves the 32-row M3018 localization denominator and maps the broad negative surface into four objective families: offtrack recovery pressure, collision clearance guard, speed-floor guard, and success identity context guard. These rows are trainer/evaluator-side metadata only. They are not numeric targets, validation evidence, ranking evidence, repair-success evidence, current-sim verdict evidence, paper evidence, high-fidelity evidence, finite-window-vs-GRU evidence, full-driver evidence, or self-ID evidence.",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3022 broad-failure objective-contract materialization artifacts before any target materialization fitting execution ranking validation performance paper high-fidelity full-driver finite-window-vs-GRU or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "objective_family_rows.csv"),
                str(output_dir / "objective_component_rows.csv"),
                str(output_dir / "row_assignment_rows.csv"),
                str(output_dir / "profile_source_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m3021-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-admission-design.md",
                "docs/m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis.md",
                "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/summary.json",
                "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/failure_localization_rows.csv",
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3021_ID}.json",
                f"experiments/manifests/{M3020_ID}.json",
                f"experiments/manifests/{M3019_ID}.json",
                f"experiments/manifests/{M3018_ID}.json",
            ],
            "parent_objective": [
                "audit M3022 broad-failure objective-contract materialization before any target materialization fitting execution ranking validation or claim"
            ],
            "derived_from": [MILESTONE_ID, M3021_ID, M3020_ID, M3019_ID, M3018_ID],
            "blocked_by": [
                "M3022 materialization requires result audit before interpretation or continuation",
                "M3021 admits only a no-execution objective-contract materialization route",
                "M3018/M3019/M3020 evidence is broad negative diagnostic evidence and cannot justify direct repair success or validation claims",
            ],
            "supersedes": [
                "direct target materialization fitting execution ranking validation or promotion from M3022 rows without audit"
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3023 must audit M3022 summary gate matrix row counts actor guards claim boundaries and follow-up registration",
            "M3023 must preserve all 32 M3018 localization rows and all objective guard families",
            "M3023 must not claim validation repair-success performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M3023 must select exactly one next route or stop/synthesis state after audit",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote select a winner mutate checkpoints or tune profiles",
            "do not materialize numeric targets or fit an objective in M3023",
            "do not change actor input or action contract",
            "do not convert M3022 objective-contract rows into performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_broad_failure_objective_contract_materialization_result_audit",
            "evidence_increment": "audits M3022 objective-contract materialization artifacts",
            "claim_scope": "Result audit only; no target materialization fitting execution validation ranking promotion repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3022 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if M3022 dropped any M3018 localization row or guard family",
                "stop if the objective contract is insufficient to justify a bounded next route",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if objective-contract rows are complete but next route remains ambiguous",
                "route to a bounded design only after M3023 accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3022 completes objective-contract materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3022 broad-failure objective-contract materialization artifacts",
            "admission_evidence": [
                "M3022 summary and gate matrix",
                "M3022 objective family component row assignment profile/source guard actor guard claim and run-state artifacts",
            ],
            "blocked_shortcuts": [
                "no target materialization fitting execution validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO checkpoint mutation profile tuning or promotion",
                "no hidden/oracle/future-target/source/route/outcome/progress/verdict/TTC actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3023 status queue scoreboard and review",
                "one follow-up manifest only if M3023 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3023 audit accepts or rejects M3022 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3023 audits Route A objective-contract infrastructure and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3023; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3015/M3018 new-source diagnostic localization plus M3021/M3022 objective-contract design/materialization only.",
            "negative_result_policy": "Preserve negative diagnostics and audit objective-contract materialization before any engineering continuation.",
            "allowed_claims": [
                "M3022 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized M3022 objective-contract artifacts",
            "paper_verdict_delta": "no paper verdict; audit may inform bounded Route A engineering continuation only",
            "must_synthesize_if": [
                "M3023 cannot accept M3022 as complete and claim-safe",
                "M3023 would claim validation readiness driver performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID",
                "M3023 cannot choose exactly one bounded next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3023 audits M3022 artifacts row counts gates actor and claim boundaries",
            "M3023 selects exactly one next route or stop state",
            "no target materialization fitting execution validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3023 hides M3022 missing artifacts or gate failures",
            "M3023 treats M3022 objective-contract rows as validation readiness or performance verdict",
            "M3023 changes actor input or action contract",
            "M3023 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3023 audits M3022 artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "objective_family_rows.csv"),
            str(output_dir / "row_assignment_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def rows_for_objective(rows: list[dict[str, str]], objective_family: str) -> list[dict[str, str]]:
    families = set(OBJECTIVE_DEFS[objective_family]["failure_families"])
    return [row for row in rows if str(row.get("failure_family", "")) in families]


def objective_for_failure_family(failure_family: str) -> str:
    for objective_family, definition in OBJECTIVE_DEFS.items():
        if failure_family in set(definition["failure_families"]):
            return objective_family
    return "unmapped_failure_family"


def any_label_visible(summary: Mapping[str, Any]) -> bool:
    return any(_bool(summary.get(key, False)) for key in LABEL_VISIBILITY_KEYS)


def actor_label_visibility(summary: Mapping[str, Any]) -> dict[str, bool]:
    return {key: _bool(summary.get(key, False)) for key in LABEL_VISIBILITY_KEYS}


LABEL_VISIBILITY_KEYS = (
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
)


def forbidden_m3022_summary_flags(summary: Mapping[str, Any]) -> dict[str, bool]:
    keys = (
        "environment_reset_run",
        "environment_step_run",
        "policy_action_run",
        "policy_rollout_run",
        "validation_run",
        "training_run",
        "replay_run",
        "ppo_run",
        "source_build_run",
        "ranking_run",
        "winner_selected",
        "checkpoint_mutated",
        "checkpoint_promoted",
        "profile_specific_tuning",
        "repair_target_selected",
        "success_rate_verdict_claim_made",
        "driver_performance_claim_made",
        "repair_success_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "finite_window_vs_gru_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "full_ideal_driver_completion_claim_made",
        "level3_self_id_claim_made",
    )
    return {key: _bool(summary.get(key, False)) for key in keys if _bool(summary.get(key, False))}


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3018-dir", type=Path, default=DEFAULT_M3018_DIR)
    parser.add_argument("--m3019-audit", type=Path, default=DEFAULT_M3019_AUDIT)
    parser.add_argument("--m3020-synthesis", type=Path, default=DEFAULT_M3020_SYNTHESIS)
    parser.add_argument("--m3021-design", type=Path, default=DEFAULT_M3021_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_new_source_broad_failure_objective_contract_materialization_preflight(
        m3018_dir=args.m3018_dir,
        m3019_audit=args.m3019_audit,
        m3020_synthesis=args.m3020_synthesis,
        m3021_design=args.m3021_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"objective_family_rows={summary['objective_family_row_count']}")
    print(f"row_assignment_rows={summary['row_assignment_row_count']}")
    print(f"profile_source_guard_rows={summary['profile_source_guard_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
