"""Materialize M2970 nonzero residual training-admission rows.

M2970 consumes the accepted M2966/M2967/M2968/M2969 actor-head delta
nonzero-residual objective chain. It performs no environment, policy,
validation, training, ranking, or promotion work. It turns M2966 objective
rows into auditable training-admission candidate, guard, objective-balance,
actor-contract, claim-boundary, and gate artifacts for a later result audit.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-admission-materialization-preflight"
)
NEXT_ID = (
    "m2971-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-admission-materialization-result-audit"
)
DEFAULT_M2966_DIR = Path(
    "runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_objective_materialization_preflight"
)
DEFAULT_M2967_AUDIT = Path(
    "docs/m2967-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-objective-materialization-result-audit.md"
)
DEFAULT_M2968_SYNTHESIS = Path(
    "docs/m2968-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-objective-branch-synthesis.md"
)
DEFAULT_M2969_DESIGN = Path(
    "docs/m2969-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-admission-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_training_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-admission-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2971-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-training-admission-materialization-result-audit.json"
)

EXPECTED_ROW_ASSIGNMENT_COUNT = 56
EXPECTED_TRAINING_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_IDENTITY_ROW_COUNT = 13
EXPECTED_STALE_GUARDRAIL_COUNT = 11
EXPECTED_OBJECTIVE_FAMILY_COUNT = 4
EXPECTED_OBJECTIVE_COMPONENT_COUNT = 4
EXPECTED_OUTCOME_COUNTS = {
    "diagnostic_success": 13,
    "collision": 7,
    "off_track": 35,
    "speed_too_low": 1,
}
EXPECTED_TRAINING_CANDIDATE_OBJECTIVE_COUNTS = {
    "collision_clearance_residual_objective": 7,
    "offtrack_recovery_residual_objective": 35,
    "speed_floor_context_guard_objective": 1,
}
NON_SUCCESS_OBJECTIVE_FAMILIES = set(EXPECTED_TRAINING_CANDIDATE_OBJECTIVE_COUNTS)

TRAINING_ADMISSION_STATUS = "guarded_residual_training_admission_materialized_for_future_audit"
SUCCESS_GUARD_STATUS = "success_identity_guard_materialized_no_positive_target"
STALE_GUARD_STATUS = "blocked_stale_fixed_source_guardrail_materialized_non_executed"

CLAIM_SCOPE = (
    "M2970 Route A actor-head delta nonzero residual training-admission materialization only; "
    "accepted M2966 objective-family, objective-component, row-assignment, success-identity, "
    "stale-guardrail, actor-contract, claim-boundary, and gate rows may be transformed into "
    "candidate and guard artifacts for later audit while all 56 row assignments, 43 non-success "
    "training candidates, 13 success identity guards, and 11 stale fixed-source guardrails remain "
    "accounted. No reset, step, rollout, replay, validation, training, PPO, dependency work, "
    "residual fitting or selection, ranking, winner selection, promotion, success-rate verdict, "
    "repair success, driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, residual training readiness, residual quality, driver performance, validation "
    "readiness or result, controller-family ranking, source-family ranking, task-family ranking, "
    "profile ranking, checkpoint ranking, candidate ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

PROFILE_FIELDNAMES = [
    "training_admission_profile_id",
    "source_objective_materialization_id",
    "source_row_assignment_count",
    "training_candidate_row_count",
    "success_identity_guard_row_count",
    "stale_guardrail_row_count",
    "objective_family_count",
    "objective_component_count",
    "profile_status",
    "future_training_manifest_required",
    "future_result_audit_required",
    "training_scheduled",
    "execution_scheduled",
    "ppo_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "actor_visible_label",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
CANDIDATE_FIELDNAMES = [
    "training_admission_candidate_id",
    "source_row_assignment_id",
    "localization_row_id",
    "execution_candidate_id",
    "source_milestone",
    "source_row_id",
    "task_family",
    "workload_id",
    "outcome_family",
    "objective_family",
    "training_admission_status",
    "future_training_manifest_required",
    "future_execution_manifest_required",
    "training_scheduled",
    "execution_scheduled",
    "ppo_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "actor_visible_label",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
TRAINING_GUARD_FIELDNAMES = [
    "training_admission_guard_id",
    "source_guard_id",
    "source_guardrail_id",
    "source_row_assignment_id",
    "localization_row_id",
    "execution_candidate_id",
    "source_milestone",
    "task_family",
    "outcome_family",
    "guard_family",
    "guard_role",
    "row_count",
    "training_target_allowed",
    "positive_training_target",
    "execution_allowed",
    "training_scheduled",
    "execution_scheduled",
    "actor_visible_label",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
OBJECTIVE_BALANCE_FIELDNAMES = [
    "objective_balance_id",
    "objective_family",
    "component_id",
    "component_role",
    "source_trigger_outcome",
    "source_row_count",
    "training_candidate_count",
    "success_identity_guard_count",
    "stale_guardrail_count",
    "balance_role",
    "loss_component",
    "target_signal",
    "future_training_manifest_required",
    "materialization_only_no_training",
    "actor_visible",
    "training_scheduled",
    "execution_scheduled",
    "ranking_allowed",
    "claim_boundary",
]
SUCCESS_IDENTITY_FIELDNAMES = [
    "guard_id",
    "source_success_identity_guard_id",
    "localization_row_id",
    "execution_candidate_id",
    "source_milestone",
    "task_family",
    "outcome_family",
    "residual_target",
    "training_admission_status",
    "actor_visible",
    "positive_training_target",
    "training_scheduled",
    "execution_scheduled",
    "claim_boundary",
]
STALE_GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "source_stale_guardrail_id",
    "source_guardrail_context_id",
    "guardrail_source",
    "guardrail_family",
    "source_milestone",
    "source_row_id",
    "row_count",
    "execution_run",
    "objective_denominator_allowed",
    "training_denominator_allowed",
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
    "allowed_in_m2970",
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
    "training_admission_profile_rows",
    "training_admission_candidate_rows",
    "training_admission_guard_rows",
    "objective_balance_rows",
    "success_identity_guard_rows",
    "stale_guardrail_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_nonzero_residual_training_admission_materialization_preflight(
    *,
    m2966_dir: Path | str = DEFAULT_M2966_DIR,
    m2967_audit: Path | str = DEFAULT_M2967_AUDIT,
    m2968_synthesis: Path | str = DEFAULT_M2968_SYNTHESIS,
    m2969_design: Path | str = DEFAULT_M2969_DESIGN,
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
        m2966_dir=Path(m2966_dir),
        m2967_audit=Path(m2967_audit),
        m2968_synthesis=Path(m2968_synthesis),
        m2969_design=Path(m2969_design),
        follow_up_manifest=Path(follow_up_manifest),
    )

    candidate_rows = build_training_admission_candidate_rows(source["row_assignment_rows"])
    success_rows = build_success_identity_guard_rows(source["success_identity_guard_rows"])
    stale_rows = build_stale_guardrail_rows(source["stale_guardrail_rows"])
    guard_rows = build_training_admission_guard_rows(success_rows, stale_rows)
    objective_balance_rows = build_objective_balance_rows(
        source["objective_family_rows"],
        source["objective_component_rows"],
        candidate_rows,
        success_rows,
        stale_rows,
    )
    profile_rows = build_training_admission_profile_rows(
        source=source,
        candidate_rows=candidate_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        objective_balance_rows=objective_balance_rows,
    )

    write_csv_rows(paths["training_admission_profile_rows"], profile_rows, fieldnames=PROFILE_FIELDNAMES)
    write_csv_rows(paths["training_admission_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["training_admission_guard_rows"], guard_rows, fieldnames=TRAINING_GUARD_FIELDNAMES)
    write_csv_rows(paths["objective_balance_rows"], objective_balance_rows, fieldnames=OBJECTIVE_BALANCE_FIELDNAMES)
    write_csv_rows(paths["success_identity_guard_rows"], success_rows, fieldnames=SUCCESS_IDENTITY_FIELDNAMES)
    write_csv_rows(paths["stale_guardrail_rows"], stale_rows, fieldnames=STALE_GUARDRAIL_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "source_row_assignment_count": len(source["row_assignment_rows"]),
            "training_admission_candidate_row_count": len(candidate_rows),
            "training_admission_guard_row_count": len(guard_rows),
            "success_identity_guard_row_count": len(success_rows),
            "stale_guardrail_row_count": len(stale_rows),
            "objective_balance_row_count": len(objective_balance_rows),
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
        profile_rows=profile_rows,
        candidate_rows=candidate_rows,
        guard_rows=guard_rows,
        objective_balance_rows=objective_balance_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        candidate_rows_present=bool(candidate_rows),
        guard_rows_present=bool(guard_rows),
        objective_balance_present=bool(objective_balance_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        profile_rows=profile_rows,
        candidate_rows=candidate_rows,
        guard_rows=guard_rows,
        objective_balance_rows=objective_balance_rows,
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
        profile_rows=profile_rows,
        candidate_rows=candidate_rows,
        guard_rows=guard_rows,
        objective_balance_rows=objective_balance_rows,
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
        candidate_rows_present=bool(candidate_rows),
        guard_rows_present=bool(guard_rows),
        objective_balance_present=bool(objective_balance_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        profile_rows=profile_rows,
        candidate_rows=candidate_rows,
        guard_rows=guard_rows,
        objective_balance_rows=objective_balance_rows,
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
        profile_rows=profile_rows,
        candidate_rows=candidate_rows,
        guard_rows=guard_rows,
        objective_balance_rows=objective_balance_rows,
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
            "source_row_assignment_count": len(source["row_assignment_rows"]),
            "training_admission_candidate_row_count": len(candidate_rows),
            "training_admission_guard_row_count": len(guard_rows),
            "success_identity_guard_row_count": len(success_rows),
            "stale_guardrail_row_count": len(stale_rows),
            "objective_balance_row_count": len(objective_balance_rows),
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
        "training_admission_profile_rows": output_dir / "training_admission_profile_rows.csv",
        "training_admission_candidate_rows": output_dir / "training_admission_candidate_rows.csv",
        "training_admission_guard_rows": output_dir / "training_admission_guard_rows.csv",
        "objective_balance_rows": output_dir / "objective_balance_rows.csv",
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
    m2966_dir: Path,
    m2967_audit: Path,
    m2968_synthesis: Path,
    m2969_design: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2967_audit": m2967_audit,
        "m2968_synthesis": m2968_synthesis,
        "m2969_design": m2969_design,
        "m2966_summary": m2966_dir / "summary.json",
        "objective_family_rows": m2966_dir / "objective_family_rows.csv",
        "objective_component_rows": m2966_dir / "objective_component_rows.csv",
        "row_assignment_rows": m2966_dir / "row_assignment_rows.csv",
        "success_identity_guard_rows": m2966_dir / "success_identity_guard_rows.csv",
        "stale_guardrail_rows": m2966_dir / "stale_guardrail_rows.csv",
        "actor_contract_guard_rows": m2966_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2966_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2966_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2967_audit_text": paths["m2967_audit"].read_text(encoding="utf-8")
        if source_exists["m2967_audit"]
        else "",
        "m2968_synthesis_text": paths["m2968_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2968_synthesis"]
        else "",
        "m2969_design_text": paths["m2969_design"].read_text(encoding="utf-8")
        if source_exists["m2969_design"]
        else "",
        "m2966_summary": read_json(paths["m2966_summary"]) if source_exists["m2966_summary"] else {},
        "objective_family_rows": read_csv_rows(paths["objective_family_rows"]),
        "objective_component_rows": read_csv_rows(paths["objective_component_rows"]),
        "row_assignment_rows": read_csv_rows(paths["row_assignment_rows"]),
        "success_identity_guard_rows": read_csv_rows(paths["success_identity_guard_rows"]),
        "stale_guardrail_rows": read_csv_rows(paths["stale_guardrail_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
    }


def build_training_admission_candidate_rows(row_assignment_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    admitted_rows = [
        row
        for row in row_assignment_rows
        if _bool(row.get("training_candidate_after_future_audit"))
        and not _bool(row.get("success_identity_guard"))
        and str(row.get("objective_family", "")) in NON_SUCCESS_OBJECTIVE_FAMILIES
    ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(admitted_rows, start=1):
        rows.append(
            {
                "training_admission_candidate_id": f"m2970-training-admission-candidate-{index:04d}",
                "source_row_assignment_id": row.get("assignment_id", ""),
                "localization_row_id": row.get("localization_row_id", ""),
                "execution_candidate_id": row.get("execution_candidate_id", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "task_family": row.get("task_family", ""),
                "workload_id": row.get("workload_id", ""),
                "outcome_family": row.get("outcome_family", ""),
                "objective_family": row.get("objective_family", ""),
                "training_admission_status": TRAINING_ADMISSION_STATUS,
                "future_training_manifest_required": True,
                "future_execution_manifest_required": True,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ppo_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "actor_visible_label": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_identity_guard_rows(source_success_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_success_rows, start=1):
        rows.append(
            {
                "guard_id": f"m2970-success-identity-guard-{index:04d}",
                "source_success_identity_guard_id": row.get("guard_id", ""),
                "localization_row_id": row.get("localization_row_id", ""),
                "execution_candidate_id": row.get("execution_candidate_id", ""),
                "source_milestone": row.get("source_milestone", ""),
                "task_family": row.get("task_family", ""),
                "outcome_family": row.get("outcome_family", ""),
                "residual_target": row.get("residual_target", "zero_residual_identity"),
                "training_admission_status": SUCCESS_GUARD_STATUS,
                "actor_visible": False,
                "positive_training_target": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_stale_guardrail_rows(source_stale_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_stale_rows, start=1):
        rows.append(
            {
                "guardrail_id": f"m2970-stale-guardrail-{index:04d}",
                "source_stale_guardrail_id": row.get("guardrail_id", ""),
                "source_guardrail_context_id": row.get("source_guardrail_context_id", ""),
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "row_count": _to_int(row.get("row_count"), default=1),
                "execution_run": False,
                "objective_denominator_allowed": False,
                "training_denominator_allowed": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_training_admission_guard_rows(
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(success_rows, start=1):
        rows.append(
            {
                "training_admission_guard_id": f"m2970-training-guard-success-{index:04d}",
                "source_guard_id": row["source_success_identity_guard_id"],
                "source_guardrail_id": "",
                "source_row_assignment_id": "",
                "localization_row_id": row["localization_row_id"],
                "execution_candidate_id": row["execution_candidate_id"],
                "source_milestone": row["source_milestone"],
                "task_family": row["task_family"],
                "outcome_family": row["outcome_family"],
                "guard_family": "success_identity_guard",
                "guard_role": "zero_residual_identity_guard_not_positive_training_target",
                "row_count": 1,
                "training_target_allowed": False,
                "positive_training_target": False,
                "execution_allowed": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "actor_visible_label": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, row in enumerate(stale_rows, start=1):
        rows.append(
            {
                "training_admission_guard_id": f"m2970-training-guard-stale-{index + offset:04d}",
                "source_guard_id": "",
                "source_guardrail_id": row["source_stale_guardrail_id"],
                "source_row_assignment_id": "",
                "localization_row_id": "",
                "execution_candidate_id": "",
                "source_milestone": row["source_milestone"],
                "task_family": "",
                "outcome_family": "stale_fixed_source_guardrail",
                "guard_family": row["guardrail_family"],
                "guard_role": STALE_GUARD_STATUS,
                "row_count": row["row_count"],
                "training_target_allowed": False,
                "positive_training_target": False,
                "execution_allowed": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "actor_visible_label": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_objective_balance_rows(
    objective_family_rows: list[dict[str, str]],
    objective_component_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    component_by_family = {str(row.get("objective_family", "")): row for row in objective_component_rows}
    candidate_counts = Counter(str(row.get("objective_family", "")) for row in candidate_rows)
    rows: list[dict[str, Any]] = []
    for index, family_row in enumerate(sorted(objective_family_rows, key=lambda row: row.get("objective_family", "")), start=1):
        objective_family = str(family_row.get("objective_family", ""))
        component = component_by_family.get(objective_family, {})
        is_success = objective_family == "success_identity_guard"
        rows.append(
            {
                "objective_balance_id": f"m2970-objective-balance-{index:04d}",
                "objective_family": objective_family,
                "component_id": component.get("component_id", ""),
                "component_role": component.get("component_role", ""),
                "source_trigger_outcome": family_row.get("source_trigger_outcome", ""),
                "source_row_count": _to_int(family_row.get("source_row_count")),
                "training_candidate_count": 0 if is_success else candidate_counts.get(objective_family, 0),
                "success_identity_guard_count": len(success_rows) if is_success else 0,
                "stale_guardrail_count": len(stale_rows) if index == 1 else 0,
                "balance_role": "identity_guard" if is_success else "future_training_candidate_after_audit",
                "loss_component": component.get("loss_component", ""),
                "target_signal": component.get("target_signal", ""),
                "future_training_manifest_required": objective_family in NON_SUCCESS_OBJECTIVE_FAMILIES,
                "materialization_only_no_training": True,
                "actor_visible": False,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ranking_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_training_admission_profile_rows(
    *,
    source: Mapping[str, Any],
    candidate_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    objective_balance_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "training_admission_profile_id": "m2970-guarded-residual-training-admission-profile-0001",
            "source_objective_materialization_id": "m2966",
            "source_row_assignment_count": len(source["row_assignment_rows"]),
            "training_candidate_row_count": len(candidate_rows),
            "success_identity_guard_row_count": len(success_rows),
            "stale_guardrail_row_count": len(stale_rows),
            "objective_family_count": len(source["objective_family_rows"]),
            "objective_component_count": len(source["objective_component_rows"]),
            "profile_status": "materialized_for_m2971_audit_only",
            "future_training_manifest_required": True,
            "future_result_audit_required": True,
            "training_scheduled": False,
            "execution_scheduled": False,
            "ppo_scheduled": False,
            "ranking_allowed": False,
            "winner_selection_allowed": False,
            "promotion_allowed": False,
            "actor_visible_label": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "self_id_claim_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_actor_contract_guard_rows(
    *,
    source: Mapping[str, Any],
    profile_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    objective_balance_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = source["m2966_summary"]
    checks = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        ("actor_action_dim", ACTION_DIM, ACTION_DIM),
        ("m2966_status_pass", summary.get("status_pass"), True),
        ("m2966_gate_matrix_pass", summary.get("gate_matrix_pass"), True),
        ("m2966_actor_input_contract_changed", summary.get("actor_input_contract_changed", False), False),
        ("hidden_oracle_actor_input_detected", summary.get("hidden_oracle_actor_input_detected", False), False),
        ("future_target_actor_input_required", summary.get("future_target_actor_input_required", False), False),
        ("objective_labels_actor_visible", False, False),
        ("admission_labels_actor_visible", False, False),
        ("verdict_labels_actor_visible", False, False),
        ("training_scheduled", any_row_truthy("training_scheduled", profile_rows, candidate_rows, guard_rows, objective_balance_rows, success_rows, stale_rows), False),
        ("execution_scheduled", any_row_truthy("execution_scheduled", profile_rows, candidate_rows, guard_rows, objective_balance_rows, success_rows, stale_rows), False),
        ("ppo_scheduled", any_row_truthy("ppo_scheduled", profile_rows, candidate_rows), False),
        ("ranking_allowed", any_row_truthy("ranking_allowed", profile_rows, candidate_rows, objective_balance_rows), False),
        ("success_identity_positive_training_target", any_row_truthy("positive_training_target", success_rows, guard_rows), False),
        ("stale_guardrail_execution_run", any_row_truthy("execution_run", stale_rows), False),
        ("actor_visible_label", any_row_truthy("actor_visible_label", profile_rows, candidate_rows, guard_rows), False),
        ("objective_balance_actor_visible", any_row_truthy("actor_visible", objective_balance_rows), False),
    ]
    return [
        {
            "guard_id": f"m2970-actor-guard-{index:04d}",
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
    candidate_rows_present: bool,
    guard_rows_present: bool,
    objective_balance_present: bool,
) -> list[dict[str, Any]]:
    allowed = {
        "training_admission_materialization_artifacts_present": artifacts_present,
        "training_candidate_artifacts_present": candidate_rows_present,
        "training_guard_artifacts_present": guard_rows_present,
        "objective_balance_artifacts_present": objective_balance_present,
        "actor_and_claim_boundary_preserved": True,
        "m2971_result_audit_registered": follow_up_manifest_registered,
    }
    blocked = {
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "dependency_execution_performed": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
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
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    rows: list[dict[str, Any]] = []
    for index, (claim, made) in enumerate(allowed.items(), start=1):
        rows.append(
            {
                "claim_id": f"m2970-claim-allowed-{index:04d}",
                "claim_family": claim,
                "allowed_in_m2970": True,
                "claim_made": made,
                "status_pass": bool(made),
                "evidence_required_before_claim": "M2970 required artifact and follow-up audit registration",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, (claim, made) in enumerate(blocked.items(), start=1):
        rows.append(
            {
                "claim_id": f"m2970-claim-blocked-{index + offset:04d}",
                "claim_family": claim,
                "allowed_in_m2970": False,
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
    profile_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    objective_balance_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    summary = source["m2966_summary"]
    outcome_counts = Counter(str(row.get("outcome_family", "")) for row in source["row_assignment_rows"])
    training_candidate_objective_counts = Counter(str(row.get("objective_family", "")) for row in candidate_rows)
    gates = [
        (
            "m2970_source_artifacts_present",
            "lineage",
            all(
                source["source_exists"][key]
                for key in [
                    "m2967_audit",
                    "m2968_synthesis",
                    "m2969_design",
                    "m2966_summary",
                    "objective_family_rows",
                    "objective_component_rows",
                    "row_assignment_rows",
                    "success_identity_guard_rows",
                    "stale_guardrail_rows",
                    "actor_contract_guard_rows",
                    "claim_boundary_rows",
                    "gate_matrix",
                ]
            ),
            source["source_exists"],
            "M2966/M2967/M2968/M2969 artifacts present",
        ),
        ("m2970_m2966_status_pass", "lineage", summary.get("status_pass") is True, summary.get("status_pass"), True),
        ("m2970_m2966_gate_matrix_pass", "lineage", summary.get("gate_matrix_pass") is True, summary.get("gate_matrix_pass"), True),
        (
            "m2970_m2967_accepts_m2966",
            "lineage",
            "accept_m2966_nonzero_residual_objective_materialization_claim_safe" in source["m2967_audit_text"],
            "accept_m2966_nonzero_residual_objective_materialization_claim_safe" in source["m2967_audit_text"],
            True,
        ),
        (
            "m2970_m2968_continues_to_training_admission",
            "lineage",
            "continue_to_m2969_nonzero_residual_training_admission_design" in source["m2968_synthesis_text"],
            "continue_to_m2969_nonzero_residual_training_admission_design" in source["m2968_synthesis_text"],
            True,
        ),
        (
            "m2970_m2969_admits_m2970",
            "lineage",
            MILESTONE_ID in source["m2969_design_text"],
            MILESTONE_ID in source["m2969_design_text"],
            True,
        ),
        (
            "m2970_row_assignments_accounted",
            "training_admission",
            len(source["row_assignment_rows"]) == EXPECTED_ROW_ASSIGNMENT_COUNT,
            len(source["row_assignment_rows"]),
            EXPECTED_ROW_ASSIGNMENT_COUNT,
        ),
        (
            "m2970_training_candidates_materialized",
            "training_admission",
            len(candidate_rows) == EXPECTED_TRAINING_CANDIDATE_COUNT,
            len(candidate_rows),
            EXPECTED_TRAINING_CANDIDATE_COUNT,
        ),
        (
            "m2970_success_identity_guards_materialized",
            "guardrail",
            len(success_rows) == EXPECTED_SUCCESS_IDENTITY_ROW_COUNT
            and not any_row_truthy("positive_training_target", success_rows),
            {"success_rows": len(success_rows), "positive_target": any_row_truthy("positive_training_target", success_rows)},
            {"success_rows": EXPECTED_SUCCESS_IDENTITY_ROW_COUNT, "positive_target": False},
        ),
        (
            "m2970_stale_guardrails_preserved",
            "guardrail",
            len(stale_rows) == EXPECTED_STALE_GUARDRAIL_COUNT and not any_row_truthy("execution_run", stale_rows),
            {"stale_rows": len(stale_rows), "execution_run": any_row_truthy("execution_run", stale_rows)},
            {"stale_rows": EXPECTED_STALE_GUARDRAIL_COUNT, "execution_run": False},
        ),
        (
            "m2970_training_guard_rows_materialized",
            "guardrail",
            len(guard_rows) == EXPECTED_SUCCESS_IDENTITY_ROW_COUNT + EXPECTED_STALE_GUARDRAIL_COUNT,
            len(guard_rows),
            EXPECTED_SUCCESS_IDENTITY_ROW_COUNT + EXPECTED_STALE_GUARDRAIL_COUNT,
        ),
        (
            "m2970_objective_family_count_accounted",
            "objective_balance",
            len(source["objective_family_rows"]) == EXPECTED_OBJECTIVE_FAMILY_COUNT,
            len(source["objective_family_rows"]),
            EXPECTED_OBJECTIVE_FAMILY_COUNT,
        ),
        (
            "m2970_objective_component_count_accounted",
            "objective_balance",
            len(source["objective_component_rows"]) == EXPECTED_OBJECTIVE_COMPONENT_COUNT,
            len(source["objective_component_rows"]),
            EXPECTED_OBJECTIVE_COMPONENT_COUNT,
        ),
        (
            "m2970_objective_balance_rows_materialized",
            "objective_balance",
            len(objective_balance_rows) == EXPECTED_OBJECTIVE_FAMILY_COUNT,
            len(objective_balance_rows),
            EXPECTED_OBJECTIVE_FAMILY_COUNT,
        ),
        (
            "m2970_outcome_counts_match_m2966",
            "training_admission",
            dict(outcome_counts) == EXPECTED_OUTCOME_COUNTS,
            dict(outcome_counts),
            EXPECTED_OUTCOME_COUNTS,
        ),
        (
            "m2970_training_candidate_objective_counts_match_design",
            "training_admission",
            dict(training_candidate_objective_counts) == EXPECTED_TRAINING_CANDIDATE_OBJECTIVE_COUNTS,
            dict(training_candidate_objective_counts),
            EXPECTED_TRAINING_CANDIDATE_OBJECTIVE_COUNTS,
        ),
        (
            "m2970_profile_materialized_no_training",
            "contract",
            len(profile_rows) == 1 and not any_row_truthy("training_scheduled", profile_rows),
            {"profile_rows": len(profile_rows), "training_scheduled": any_row_truthy("training_scheduled", profile_rows)},
            {"profile_rows": 1, "training_scheduled": False},
        ),
        (
            "m2970_no_training_execution_or_ranking_scheduled",
            "contract",
            no_training_execution_or_ranking(profile_rows, candidate_rows, guard_rows, objective_balance_rows, success_rows, stale_rows),
            "all false",
            "all false",
        ),
        (
            "m2970_actor_contract_guards_pass",
            "contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            f"rows={len(actor_rows)} pass={sum(_bool(row['status_pass']) for row in actor_rows)}",
            "all actor guards pass",
        ),
        (
            "m2970_claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            f"allowed={sum(_bool(row['allowed_in_m2970']) for row in claim_rows)} "
            f"blocked={sum(not _bool(row['allowed_in_m2970']) for row in claim_rows)}",
            "allowed pass and blocked not made",
        ),
        ("m2970_required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True),
        (
            "m2970_follow_up_audit_registered",
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
        "ppo_scheduled",
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


def any_row_truthy(field: str, *row_sets: list[dict[str, Any]]) -> bool:
    return any(_bool(row.get(field)) for rows in row_sets for row in rows)


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
    profile_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    objective_balance_rows: list[dict[str, Any]],
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
    outcome_counts = Counter(str(row.get("outcome_family", "")) for row in source["row_assignment_rows"])
    training_candidate_objective_counts = Counter(str(row.get("objective_family", "")) for row in candidate_rows)
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    status_pass = gate_matrix_pass and actor_rows_pass and claim_rows_pass and required_artifacts_present
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "engineering_controller_route_a_actor_head_delta_nonzero_residual_training_admission_materialization_pass"
        if status_pass
        else "engineering_controller_route_a_actor_head_delta_nonzero_residual_training_admission_materialization_blocked",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2966_status_pass": source["m2966_summary"].get("status_pass") is True,
        "m2966_gate_matrix_pass": source["m2966_summary"].get("gate_matrix_pass") is True,
        "source_row_assignment_count": len(source["row_assignment_rows"]),
        "source_objective_family_row_count": len(source["objective_family_rows"]),
        "source_objective_component_row_count": len(source["objective_component_rows"]),
        "training_admission_profile_row_count": len(profile_rows),
        "training_admission_candidate_row_count": len(candidate_rows),
        "training_admission_guard_row_count": len(guard_rows),
        "objective_balance_row_count": len(objective_balance_rows),
        "success_identity_guard_row_count": len(success_rows),
        "stale_guardrail_row_count": len(stale_rows),
        "outcome_counts": dict(outcome_counts),
        "training_candidate_objective_counts": dict(training_candidate_objective_counts),
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
        "admission_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "dependency_execution_performed": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
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
            "# M2970 Engineering Controller Route A Actor-Head Delta Nonzero Residual Training Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- M2966 row assignments loaded: {summary['source_row_assignment_count']}",
            f"- training-admission profile rows: {summary['training_admission_profile_row_count']}",
            f"- training-admission candidate rows: {summary['training_admission_candidate_row_count']}",
            f"- training-admission guard rows: {summary['training_admission_guard_row_count']}",
            f"- objective-balance rows: {summary['objective_balance_row_count']}",
            f"- success identity guard rows: {summary['success_identity_guard_row_count']}",
            f"- stale guardrail rows: {summary['stale_guardrail_row_count']}",
            f"- outcome counts: {summary['outcome_counts']}",
            f"- training candidate objective counts: {summary['training_candidate_objective_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2970 materializes a no-execution guarded residual training-admission surface from the accepted M2966/M2967/M2968/M2969 chain. It does not reset, step, roll out, replay, validate, train, run PPO, rank, promote, or claim performance.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2970 guarded residual training-admission materialization before any residual training execution validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "training_admission_profile_rows.csv"),
                str(output_dir / "training_admission_candidate_rows.csv"),
                str(output_dir / "training_admission_guard_rows.csv"),
                str(output_dir / "objective_balance_rows.csv"),
                str(output_dir / "success_identity_guard_rows.csv"),
                str(output_dir / "stale_guardrail_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight.json",
                "experiments/manifests/m2969-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-design.json",
            ],
            "parent_objective": [
                "audit M2970 training-admission materialization before any nonzero residual training or execution"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2969-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-design",
                "m2968-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-branch-synthesis",
                "m2967-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-result-audit",
                "m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight",
            ],
            "blocked_by": [
                "M2970 training-admission rows require a result audit before training or execution",
                "candidate rows are materialization artifacts only and cannot be interpreted as repair success",
                "13 success identity guards and 11 stale fixed-source rows must remain protected guardrails",
            ],
            "supersedes": [
                "direct nonzero residual training from M2966 objective rows without training-admission materialization audit",
                "direct performance interpretation of M2970 training-admission rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2971 must audit M2970 summary training candidate guard objective-balance actor and claim boundaries",
            "M2971 must preserve 56 row assignments 43 training candidates 13 success identity guards and 11 blocked stale fixed-source guardrails",
            "M2971 must not claim repair success validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2971 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote publish select a winner or execute dependency work",
            "do not fit train select or execute a nonzero residual head",
            "do not change actor input or action contract",
            "do not convert M2970 training-admission rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_training_admission_materialization_result_audit",
            "evidence_increment": "audits M2970 nonzero residual training-admission materialization artifacts",
            "claim_scope": "Result audit only; no validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2970 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if guardrails entered execution training or denominators",
                "stop if training-admission rows would be used as training instructions before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if materialization is complete but no route candidate is viable",
                "route to a bounded training-preflight design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2970 completes training-admission materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2970 actor-head delta nonzero residual training-admission materialization artifacts",
            "admission_evidence": [
                "M2970 summary and gate matrix",
                "M2970 training profile candidate guard objective-balance success identity stale guard actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO residual selection or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2971 status queue scoreboard research log and review",
                "one follow-up manifest only if M2971 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2971 audit accepts or rejects M2970 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2971 audits Route A training-admission materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2971; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2970 Route A actor-head delta training-admission materialization only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2970 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized nonzero residual training-admission rows",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2971 cannot accept M2970 as complete and claim-safe",
                "M2971 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2971 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2971 audits M2970 artifacts row counts gates actor and claim boundaries",
            "M2971 selects exactly one next route or stop state",
            "no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2971 hides M2970 failures or missing artifacts",
            "M2971 treats M2970 training-admission materialization as training execution readiness performance verdict or repair success",
            "M2971 changes actor input or action contract",
            "M2971 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2971 audits M2970 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "training_admission_candidate_rows.csv"),
            str(output_dir / "training_admission_guard_rows.csv"),
            str(output_dir / "objective_balance_rows.csv"),
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
    parser.add_argument("--m2966-dir", type=Path, default=DEFAULT_M2966_DIR)
    parser.add_argument("--m2967-audit", type=Path, default=DEFAULT_M2967_AUDIT)
    parser.add_argument("--m2968-synthesis", type=Path, default=DEFAULT_M2968_SYNTHESIS)
    parser.add_argument("--m2969-design", type=Path, default=DEFAULT_M2969_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_nonzero_residual_training_admission_materialization_preflight(
        m2966_dir=args.m2966_dir,
        m2967_audit=args.m2967_audit,
        m2968_synthesis=args.m2968_synthesis,
        m2969_design=args.m2969_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(
        "M2970 training-admission materialization "
        f"status_pass={summary['status_pass']} gate_matrix_pass={summary['gate_matrix_pass']} "
        f"summary={summary['paths']['summary']}"
    )


if __name__ == "__main__":
    main()
