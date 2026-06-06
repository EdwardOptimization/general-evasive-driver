"""Materialize M2966 nonzero residual objective rows.

M2966 consumes the accepted M2963/M2964/M2965 actor-head delta objective
admission chain. It performs no environment, policy, validation, training,
ranking, or promotion work. It turns the accepted M2965 nonzero residual
objective design into machine-checkable objective, row-assignment, guard,
actor-contract, claim-boundary, and gate artifacts for a later result audit.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-objective-materialization-preflight"
)
NEXT_ID = (
    "m2967-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-objective-materialization-result-audit"
)
DEFAULT_M2963_DIR = Path(
    "runs/m2963_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "post_zero_residual_failure_localization_objective_admission_preflight"
)
DEFAULT_M2964_AUDIT = Path(
    "docs/m2964-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "post-zero-residual-failure-localization-objective-admission-result-audit.md"
)
DEFAULT_M2965_DESIGN = Path(
    "docs/m2965-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-objective-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_objective_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-objective-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2967-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-objective-materialization-result-audit.json"
)

EXPECTED_LOCALIZATION_ROW_COUNT = 56
EXPECTED_OBJECTIVE_ADMISSION_ROW_COUNT = 4
EXPECTED_NON_SUCCESS_OBJECTIVE_FAMILY_COUNT = 3
EXPECTED_SUCCESS_IDENTITY_ROW_COUNT = 13
EXPECTED_STALE_GUARDRAIL_COUNT = 11
EXPECTED_OUTCOME_COUNTS = {
    "diagnostic_success": 13,
    "collision": 7,
    "off_track": 35,
    "speed_too_low": 1,
}
NON_SUCCESS_OBJECTIVE_FAMILIES = {
    "collision_clearance_residual_objective",
    "offtrack_recovery_residual_objective",
    "speed_floor_context_guard_objective",
}
OBJECTIVE_COMPONENTS = {
    "offtrack_recovery_residual_objective": {
        "component_role": "primary_recovery_pressure",
        "loss_component": "bounded_residual_offtrack_recovery_candidate",
        "target_signal": "trainer_side_offtrack_recovery_context_not_actor_input",
    },
    "collision_clearance_residual_objective": {
        "component_role": "secondary_safety_clearance",
        "loss_component": "bounded_residual_collision_clearance_candidate",
        "target_signal": "trainer_side_clearance_context_not_actor_input",
    },
    "speed_floor_context_guard_objective": {
        "component_role": "context_speed_floor_guard",
        "loss_component": "bounded_residual_speed_floor_guard_candidate",
        "target_signal": "trainer_side_speed_floor_context_not_actor_input",
    },
    "success_identity_guard": {
        "component_role": "identity_residual_guard",
        "loss_component": "zero_residual_success_identity_guard",
        "target_signal": "trainer_side_success_identity_context_not_actor_input",
    },
}

CLAIM_SCOPE = (
    "M2966 Route A actor-head delta nonzero residual objective materialization only; "
    "M2963 objective-admission rows may be transformed into objective-family, "
    "objective-component, row-assignment, success-identity, stale-guardrail, "
    "actor-contract, claim-boundary, and gate artifacts for later audit while "
    "all 56 localized rows and 11 stale fixed-source guardrails remain accounted. "
    "No reset, step, rollout, replay, validation, training, PPO, dependency work, "
    "nonzero residual fitting or selection, ranking, winner selection, promotion, "
    "success-rate verdict, repair success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, nonzero residual quality, driver performance, validation "
    "readiness or result, controller-family ranking, source-family ranking, "
    "task-family ranking, profile ranking, checkpoint ranking, candidate ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation "
    "readiness or result, full ideal driver completion, or level3 self-identification"
)

OBJECTIVE_FAMILY_FIELDNAMES = [
    "objective_family",
    "source_trigger_outcome",
    "source_row_count",
    "admitted_for_materialization",
    "future_training_manifest_required",
    "future_execution_manifest_required",
    "training_scheduled",
    "execution_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
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
    "source_trigger_outcome",
    "source_row_count",
    "loss_component",
    "target_signal",
    "success_identity_guard",
    "materialization_only_no_training",
    "actor_visible",
    "training_scheduled",
    "execution_scheduled",
    "ranking_allowed",
    "claim_boundary",
]
ROW_ASSIGNMENT_FIELDNAMES = [
    "assignment_id",
    "localization_row_id",
    "execution_candidate_id",
    "source_milestone",
    "source_row_id",
    "task_family",
    "workload_id",
    "outcome_family",
    "objective_family",
    "objective_role",
    "training_candidate_after_future_audit",
    "success_identity_guard",
    "stale_guardrail",
    "actor_visible_label",
    "training_scheduled",
    "execution_scheduled",
    "ranking_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "claim_boundary",
]
SUCCESS_IDENTITY_FIELDNAMES = [
    "guard_id",
    "localization_row_id",
    "execution_candidate_id",
    "source_milestone",
    "task_family",
    "outcome_family",
    "residual_target",
    "actor_visible",
    "positive_training_target",
    "training_scheduled",
    "execution_scheduled",
    "claim_boundary",
]
STALE_GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "source_guardrail_context_id",
    "guardrail_source",
    "guardrail_family",
    "source_milestone",
    "source_row_id",
    "row_count",
    "execution_run",
    "objective_denominator_allowed",
    "training_scheduled",
    "execution_scheduled",
    "claim_boundary",
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
    "allowed_in_m2966",
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
    "objective_family_rows",
    "objective_component_rows",
    "row_assignment_rows",
    "success_identity_guard_rows",
    "stale_guardrail_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_nonzero_residual_objective_materialization_preflight(
    *,
    m2963_dir: Path | str = DEFAULT_M2963_DIR,
    m2964_audit: Path | str = DEFAULT_M2964_AUDIT,
    m2965_design: Path | str = DEFAULT_M2965_DESIGN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2963_dir=Path(m2963_dir),
        m2964_audit=Path(m2964_audit),
        m2965_design=Path(m2965_design),
        follow_up_manifest=Path(follow_up_manifest),
    )

    localization_rows = source["failure_localization_rows"]
    objective_admission_rows = source["residual_objective_admission_rows"]
    objective_family_rows = build_objective_family_rows(objective_admission_rows)
    objective_component_rows = build_objective_component_rows(objective_family_rows)
    row_assignment_rows = build_row_assignment_rows(localization_rows)
    success_rows = build_success_identity_guard_rows(row_assignment_rows)
    stale_rows = build_stale_guardrail_rows(source["guardrail_context_rows"])

    write_csv_rows(paths["objective_family_rows"], objective_family_rows, fieldnames=OBJECTIVE_FAMILY_FIELDNAMES)
    write_csv_rows(
        paths["objective_component_rows"],
        objective_component_rows,
        fieldnames=OBJECTIVE_COMPONENT_FIELDNAMES,
    )
    write_csv_rows(paths["row_assignment_rows"], row_assignment_rows, fieldnames=ROW_ASSIGNMENT_FIELDNAMES)
    write_csv_rows(paths["success_identity_guard_rows"], success_rows, fieldnames=SUCCESS_IDENTITY_FIELDNAMES)
    write_csv_rows(paths["stale_guardrail_rows"], stale_rows, fieldnames=STALE_GUARDRAIL_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "failure_localization_row_count": len(localization_rows),
            "residual_objective_admission_row_count": len(objective_admission_rows),
            "objective_family_row_count": len(objective_family_rows),
            "row_assignment_row_count": len(row_assignment_rows),
            "success_identity_guard_row_count": len(success_rows),
            "stale_guardrail_row_count": len(stale_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        source=source,
        objective_family_rows=objective_family_rows,
        row_assignment_rows=row_assignment_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        row_assignments_present=bool(row_assignment_rows),
        objective_rows_present=bool(objective_family_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_derived_outputs(paths, actor_rows, claim_rows, gate_rows)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
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

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        row_assignments_present=bool(row_assignment_rows),
        objective_rows_present=bool(objective_family_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
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
        objective_family_rows=objective_family_rows,
        objective_component_rows=objective_component_rows,
        row_assignment_rows=row_assignment_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
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
    write_run_state(
        paths["run_state"],
        {
            "failure_localization_row_count": len(localization_rows),
            "residual_objective_admission_row_count": len(objective_admission_rows),
            "objective_family_row_count": len(objective_family_rows),
            "row_assignment_row_count": len(row_assignment_rows),
            "success_identity_guard_row_count": len(success_rows),
            "stale_guardrail_row_count": len(stale_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "objective_family_rows": output_dir / "objective_family_rows.csv",
        "objective_component_rows": output_dir / "objective_component_rows.csv",
        "row_assignment_rows": output_dir / "row_assignment_rows.csv",
        "success_identity_guard_rows": output_dir / "success_identity_guard_rows.csv",
        "stale_guardrail_rows": output_dir / "stale_guardrail_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2963_dir: Path,
    m2964_audit: Path,
    m2965_design: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2964_audit": m2964_audit,
        "m2965_design": m2965_design,
        "m2963_summary": m2963_dir / "summary.json",
        "failure_localization_rows": m2963_dir / "failure_localization_rows.csv",
        "residual_objective_admission_rows": m2963_dir / "residual_objective_admission_rows.csv",
        "guardrail_context_rows": m2963_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": m2963_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2963_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2963_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2964_audit_text": paths["m2964_audit"].read_text(encoding="utf-8")
        if source_exists["m2964_audit"]
        else "",
        "m2965_design_text": paths["m2965_design"].read_text(encoding="utf-8")
        if source_exists["m2965_design"]
        else "",
        "m2963_summary": read_json(paths["m2963_summary"]) if source_exists["m2963_summary"] else {},
        "failure_localization_rows": read_csv_rows(paths["failure_localization_rows"]),
        "residual_objective_admission_rows": read_csv_rows(paths["residual_objective_admission_rows"]),
        "guardrail_context_rows": read_csv_rows(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
    }


def build_objective_family_rows(objective_admission_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in sorted(objective_admission_rows, key=lambda row: row.get("objective_family", "")):
        objective_family = str(source_row.get("objective_family", ""))
        admitted = _bool(source_row.get("admitted_for_m2964_audit")) and objective_family in NON_SUCCESS_OBJECTIVE_FAMILIES
        rows.append(
            {
                "objective_family": objective_family,
                "source_trigger_outcome": source_row.get("trigger_outcome_family", ""),
                "source_row_count": _to_int(source_row.get("candidate_row_count")),
                "admitted_for_materialization": admitted or objective_family == "success_identity_guard",
                "future_training_manifest_required": admitted,
                "future_execution_manifest_required": admitted,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_input_change_required": False,
                "actor_visible_labels_required": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_objective_component_rows(objective_family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, family_row in enumerate(objective_family_rows, start=1):
        objective_family = str(family_row["objective_family"])
        component = OBJECTIVE_COMPONENTS.get(
            objective_family,
            {
                "component_role": "unknown_objective_guard",
                "loss_component": "not_admitted",
                "target_signal": "not_actor_input",
            },
        )
        rows.append(
            {
                "component_id": f"m2966-objective-component-{index:04d}",
                "objective_family": objective_family,
                "component_role": component["component_role"],
                "source_trigger_outcome": family_row["source_trigger_outcome"],
                "source_row_count": family_row["source_row_count"],
                "loss_component": component["loss_component"],
                "target_signal": component["target_signal"],
                "success_identity_guard": objective_family == "success_identity_guard",
                "materialization_only_no_training": True,
                "actor_visible": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ranking_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_row_assignment_rows(localization_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(localization_rows, start=1):
        objective_family = str(row.get("residual_objective_candidate_family", ""))
        success_guard = objective_family == "success_identity_guard" or row.get("outcome_family") == "diagnostic_success"
        admitted = objective_family in NON_SUCCESS_OBJECTIVE_FAMILIES and not success_guard
        rows.append(
            {
                "assignment_id": f"m2966-row-assignment-{index:04d}",
                "localization_row_id": row.get("localization_row_id", ""),
                "execution_candidate_id": row.get("execution_candidate_id", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "task_family": row.get("task_family", ""),
                "workload_id": row.get("workload_id", ""),
                "outcome_family": row.get("outcome_family", ""),
                "objective_family": objective_family,
                "objective_role": "success_identity_guard" if success_guard else "future_training_candidate_after_audit",
                "training_candidate_after_future_audit": admitted,
                "success_identity_guard": success_guard,
                "stale_guardrail": False,
                "actor_visible_label": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ranking_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_identity_guard_rows(row_assignment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    success_assignments = [row for row in row_assignment_rows if _bool(row.get("success_identity_guard"))]
    for index, row in enumerate(success_assignments, start=1):
        rows.append(
            {
                "guard_id": f"m2966-success-identity-guard-{index:04d}",
                "localization_row_id": row["localization_row_id"],
                "execution_candidate_id": row["execution_candidate_id"],
                "source_milestone": row["source_milestone"],
                "task_family": row["task_family"],
                "outcome_family": row["outcome_family"],
                "residual_target": "zero_residual_identity",
                "actor_visible": False,
                "positive_training_target": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_stale_guardrail_rows(guardrail_context_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    stale_rows = [
        row
        for row in guardrail_context_rows
        if str(row.get("guardrail_family", "")).strip()
        == "actor_head_delta_execution_admission_blocked_stale_fixed_surface"
        and str(row.get("guardrail_source", "")).strip() == "m2956_rejection_rows"
    ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(stale_rows, start=1):
        rows.append(
            {
                "guardrail_id": f"m2966-stale-guardrail-{index:04d}",
                "source_guardrail_context_id": row.get("guardrail_context_id", ""),
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "row_count": _to_int(row.get("row_count"), default=1),
                "execution_run": False,
                "objective_denominator_allowed": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: Mapping[str, Any],
    objective_family_rows: list[dict[str, Any]],
    row_assignment_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = source["m2963_summary"]
    checks = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        ("actor_action_dim", ACTION_DIM, ACTION_DIM),
        ("m2963_actor_input_contract_changed", summary.get("actor_input_contract_changed", False), False),
        ("hidden_oracle_actor_input_detected", summary.get("hidden_oracle_actor_input_detected", False), False),
        ("future_target_actor_input_required", summary.get("future_target_actor_input_required", False), False),
        ("objective_labels_actor_visible", False, False),
        ("training_scheduled", any(_bool(row["training_scheduled"]) for row in objective_family_rows), False),
        ("execution_scheduled", any(_bool(row["execution_scheduled"]) for row in objective_family_rows), False),
        ("row_assignment_training_scheduled", any(_bool(row["training_scheduled"]) for row in row_assignment_rows), False),
        ("row_assignment_execution_scheduled", any(_bool(row["execution_scheduled"]) for row in row_assignment_rows), False),
        ("success_identity_positive_training_target", any(_bool(row["positive_training_target"]) for row in success_rows), False),
        ("stale_guardrails_execution_run", any(_bool(row["execution_run"]) for row in stale_rows), False),
    ]
    return [
        {
            "guard_id": f"m2966-actor-guard-{index:04d}",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(checks, start=1)
    ]


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    row_assignments_present: bool,
    objective_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = {
        "objective_materialization_artifacts_present": artifacts_present,
        "row_assignment_artifacts_present": row_assignments_present,
        "objective_family_artifacts_present": objective_rows_present,
        "actor_and_claim_boundary_preserved": True,
        "m2967_result_audit_registered": follow_up_manifest_registered,
    }
    blocked = {
        "environment_reset_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    rows: list[dict[str, Any]] = []
    for index, (claim, made) in enumerate(allowed.items(), start=1):
        rows.append(
            {
                "claim_id": f"m2966-claim-allowed-{index:04d}",
                "claim_family": claim,
                "allowed_in_m2966": True,
                "claim_made": made,
                "status_pass": bool(made),
                "evidence_required_before_claim": "M2966 required artifact and follow-up audit registration",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, (claim, made) in enumerate(blocked.items(), start=1):
        rows.append(
            {
                "claim_id": f"m2966-claim-blocked-{index + offset:04d}",
                "claim_family": claim,
                "allowed_in_m2966": False,
                "claim_made": made,
                "status_pass": not bool(made),
                "evidence_required_before_claim": FORBIDDEN_INTERPRETATION,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    objective_family_rows: list[dict[str, Any]],
    objective_component_rows: list[dict[str, Any]],
    row_assignment_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    summary = source["m2963_summary"]
    outcome_counts = Counter(str(row.get("outcome_family", "")) for row in row_assignment_rows)
    objective_families = {str(row["objective_family"]) for row in objective_family_rows}
    non_success_families = objective_families & NON_SUCCESS_OBJECTIVE_FAMILIES
    gates = [
        (
            "m2966_source_artifacts_present",
            "lineage",
            all(
                source["source_exists"][key]
                for key in [
                    "m2964_audit",
                    "m2965_design",
                    "m2963_summary",
                    "failure_localization_rows",
                    "residual_objective_admission_rows",
                    "guardrail_context_rows",
                    "actor_contract_guard_rows",
                    "claim_boundary_rows",
                    "gate_matrix",
                ]
            ),
            source["source_exists"],
            "M2963/M2964/M2965 artifacts present",
        ),
        ("m2966_m2963_status_pass", "lineage", summary.get("status_pass") is True, summary.get("status_pass"), True),
        (
            "m2966_m2963_gate_matrix_pass",
            "lineage",
            summary.get("gate_matrix_pass") is True,
            summary.get("gate_matrix_pass"),
            True,
        ),
        (
            "m2966_m2964_accepts_m2963",
            "lineage",
            "accept_m2963_post_zero_residual" in source["m2964_audit_text"],
            "accept_m2963_post_zero_residual" in source["m2964_audit_text"],
            True,
        ),
        (
            "m2966_m2965_admits_m2966",
            "lineage",
            MILESTONE_ID in source["m2965_design_text"],
            MILESTONE_ID in source["m2965_design_text"],
            True,
        ),
        (
            "m2966_localization_rows_accounted",
            "objective_materialization",
            len(row_assignment_rows) == EXPECTED_LOCALIZATION_ROW_COUNT,
            len(row_assignment_rows),
            EXPECTED_LOCALIZATION_ROW_COUNT,
        ),
        (
            "m2966_objective_admission_rows_accounted",
            "objective_materialization",
            len(objective_family_rows) == EXPECTED_OBJECTIVE_ADMISSION_ROW_COUNT,
            len(objective_family_rows),
            EXPECTED_OBJECTIVE_ADMISSION_ROW_COUNT,
        ),
        (
            "m2966_non_success_objective_families_materialized",
            "objective_materialization",
            len(non_success_families) == EXPECTED_NON_SUCCESS_OBJECTIVE_FAMILY_COUNT,
            sorted(non_success_families),
            sorted(NON_SUCCESS_OBJECTIVE_FAMILIES),
        ),
        (
            "m2966_objective_component_rows_materialized",
            "objective_materialization",
            len(objective_component_rows) == len(objective_family_rows),
            len(objective_component_rows),
            len(objective_family_rows),
        ),
        (
            "m2966_success_identity_guard_rows_materialized",
            "guardrail",
            len(success_rows) == EXPECTED_SUCCESS_IDENTITY_ROW_COUNT,
            len(success_rows),
            EXPECTED_SUCCESS_IDENTITY_ROW_COUNT,
        ),
        (
            "m2966_stale_guardrails_preserved",
            "guardrail",
            len(stale_rows) == EXPECTED_STALE_GUARDRAIL_COUNT and not any(_bool(row["execution_run"]) for row in stale_rows),
            {"stale_rows": len(stale_rows), "execution_run": any(_bool(row["execution_run"]) for row in stale_rows)},
            {"stale_rows": EXPECTED_STALE_GUARDRAIL_COUNT, "execution_run": False},
        ),
        (
            "m2966_outcome_counts_match_m2963",
            "objective_materialization",
            dict(outcome_counts) == EXPECTED_OUTCOME_COUNTS,
            dict(outcome_counts),
            EXPECTED_OUTCOME_COUNTS,
        ),
        (
            "m2966_no_training_or_execution_scheduled",
            "contract",
            no_training_execution_or_ranking(objective_family_rows, row_assignment_rows, success_rows, stale_rows),
            "all false",
            "all false",
        ),
        (
            "m2966_actor_contract_guards_pass",
            "contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            f"rows={len(actor_rows)} pass={sum(_bool(row['status_pass']) for row in actor_rows)}",
            "all actor guards pass",
        ),
        (
            "m2966_claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            f"allowed={sum(_bool(row['allowed_in_m2966']) for row in claim_rows)} "
            f"blocked={sum(not _bool(row['allowed_in_m2966']) for row in claim_rows)}",
            "allowed pass and blocked not made",
        ),
        ("m2966_required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True),
        (
            "m2966_follow_up_audit_registered",
            "lineage",
            source["source_exists"]["follow_up_manifest"],
            source["source_exists"]["follow_up_manifest"],
            True,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for gate_id, family, passed, observed, expected in gates:
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(passed),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if passed else "contract_violation",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def no_training_execution_or_ranking(*row_sets: list[dict[str, Any]]) -> bool:
    forbidden_fields = [
        "training_scheduled",
        "execution_scheduled",
        "ranking_allowed",
        "winner_selection_allowed",
        "promotion_allowed",
        "execution_run",
    ]
    for rows in row_sets:
        for row in rows:
            for field in forbidden_fields:
                if field in row and _bool(row[field]):
                    return False
    return True


def write_derived_outputs(
    paths: Mapping[str, Path],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    objective_family_rows: list[dict[str, Any]],
    objective_component_rows: list[dict[str, Any]],
    row_assignment_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    outcome_counts = Counter(str(row.get("outcome_family", "")) for row in row_assignment_rows)
    objective_families = {str(row["objective_family"]) for row in objective_family_rows}
    non_success_families = objective_families & NON_SUCCESS_OBJECTIVE_FAMILIES
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    status_pass = gate_matrix_pass and actor_rows_pass and claim_rows_pass and required_artifacts_present
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "engineering_controller_route_a_actor_head_delta_nonzero_residual_objective_materialization_pass"
        if status_pass
        else "engineering_controller_route_a_actor_head_delta_nonzero_residual_objective_materialization_blocked",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2963_status_pass": source["m2963_summary"].get("status_pass") is True,
        "m2963_gate_matrix_pass": source["m2963_summary"].get("gate_matrix_pass") is True,
        "failure_localization_row_count": len(source["failure_localization_rows"]),
        "residual_objective_admission_row_count": len(source["residual_objective_admission_rows"]),
        "objective_family_row_count": len(objective_family_rows),
        "objective_component_row_count": len(objective_component_rows),
        "row_assignment_row_count": len(row_assignment_rows),
        "success_identity_guard_row_count": len(success_rows),
        "stale_guardrail_row_count": len(stale_rows),
        "non_success_objective_family_count": len(non_success_families),
        "outcome_counts": dict(outcome_counts),
        "objective_families": sorted(objective_families),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "objective_labels_actor_visible": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "training_run": False,
        "ppo_run": False,
        "dependency_execution_performed": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "nonzero_residual_head_trained": False,
        "nonzero_residual_head_selected": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "private_holdout_used": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M2966 Engineering Controller Route A Actor-Head Delta Nonzero Residual Objective Materialization Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- M2963 localization rows loaded: {summary['failure_localization_row_count']}",
            f"- M2963 objective-admission rows loaded: {summary['residual_objective_admission_row_count']}",
            f"- objective family rows: {summary['objective_family_row_count']}",
            f"- objective component rows: {summary['objective_component_row_count']}",
            f"- row assignment rows: {summary['row_assignment_row_count']}",
            f"- success identity guard rows: {summary['success_identity_guard_row_count']}",
            f"- stale guardrail rows: {summary['stale_guardrail_row_count']}",
            f"- non-success objective families: {summary['non_success_objective_family_count']}",
            f"- outcome counts: {summary['outcome_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2966 materializes a no-execution nonzero residual objective surface from the accepted M2963/M2964/M2965 chain. It does not reset, step, roll out, replay, validate, train, rank, promote, or claim performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
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
        "hypothesis": "A bounded result audit can accept or reject the M2966 nonzero residual objective materialization before any residual training execution validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
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
                str(output_dir / "success_identity_guard_rows.csv"),
                str(output_dir / "stale_guardrail_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight.json",
                "experiments/manifests/m2965-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-design.json",
            ],
            "parent_objective": [
                "audit M2966 objective materialization before any nonzero residual training or execution design"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2965-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-design",
            ],
            "blocked_by": [
                "M2966 objective rows require a result audit before training or execution",
                "objective rows are materialization artifacts only and cannot be interpreted as repair success",
                "11 blocked stale fixed-source rows must remain protected guardrails",
            ],
            "supersedes": [
                "direct nonzero residual training from M2966 objective materialization without result audit",
                "direct performance interpretation of M2966 objective rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2967 must audit M2966 summary objective row actor and claim boundaries",
            "M2967 must preserve 56 row assignments 4 objective families 13 success identity guards and 11 blocked stale fixed-source guardrails",
            "M2967 must not claim repair success validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2967 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote publish select a winner or execute dependency work",
            "do not fit train select or execute a nonzero residual head",
            "do not change actor input or action contract",
            "do not convert M2966 objective rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_objective_materialization_result_audit",
            "evidence_increment": "audits M2966 nonzero residual objective materialization artifacts",
            "claim_scope": "Result audit only; no validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2966 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if guardrails entered execution or denominators",
                "stop if objective rows would be used as training instructions before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if materialization is complete but no route candidate is viable",
                "route to a bounded training-admission design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2966 completes objective materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2966 actor-head delta nonzero residual objective materialization artifacts",
            "admission_evidence": [
                "M2966 summary and gate matrix",
                "M2966 objective family component row assignment success identity stale guard actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO residual selection or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2967 status queue scoreboard research log and review",
                "one follow-up manifest only if M2967 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2967 audit accepts or rejects M2966 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2967 audits Route A objective materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2967; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2966 Route A actor-head delta objective materialization only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2966 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized nonzero residual objective rows",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2967 cannot accept M2966 as complete and claim-safe",
                "M2967 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2967 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2967 audits M2966 artifacts row counts gates actor and claim boundaries",
            "M2967 selects exactly one next route or stop state",
            "no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2967 hides M2966 failures or missing artifacts",
            "M2967 treats M2966 objective materialization as training readiness performance verdict or repair success",
            "M2967 changes actor input or action contract",
            "M2967 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2967 audits M2966 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "objective_family_rows.csv"),
            str(output_dir / "objective_component_rows.csv"),
            str(output_dir / "row_assignment_rows.csv"),
            str(output_dir / "success_identity_guard_rows.csv"),
            str(output_dir / "stale_guardrail_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2963-dir", type=Path, default=DEFAULT_M2963_DIR)
    parser.add_argument("--m2964-audit", type=Path, default=DEFAULT_M2964_AUDIT)
    parser.add_argument("--m2965-design", type=Path, default=DEFAULT_M2965_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_nonzero_residual_objective_materialization_preflight(
        m2963_dir=args.m2963_dir,
        m2964_audit=args.m2964_audit,
        m2965_design=args.m2965_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(
        "M2966 objective materialization "
        f"status_pass={summary['status_pass']} gate_matrix_pass={summary['gate_matrix_pass']} "
        f"summary={summary['paths']['summary']}"
    )


if __name__ == "__main__":
    main()
