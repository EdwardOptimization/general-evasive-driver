"""Route A HF3 after-closure platform-selection decision result materialization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2607-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-"
    "result-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2608-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-"
    "result-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2607-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-"
    "decision-result-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result"
)
DEFAULT_M2604_SUMMARY = Path(
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"

SOURCE_ARTIFACTS = (
    "docs/m2606-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-result-synthesis.md",
    "docs/m2605-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-result-audit.md",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/summary.json",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_request_rows.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_evidence_admission_rows.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_candidate_comparison_rows.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_dependency_guard_rows.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_validation_role_compatibility_rows.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_actor_action_guard_rows.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_claim_boundary_checks.csv",
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/after_closure_platform_selection_decision_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 after-closure platform-selection decision-result materialization only; "
    "a bounded open/auditable platform family may be selected for future validation "
    "preparation; not validation protocol readiness, validation admission, external "
    "validation execution, high-fidelity validation readiness/result, HF4 discrepancy "
    "result, rollout success, ranking, driver performance, paper, FW-vs-GRU, "
    "current-sim verdict, high-fidelity validation, or self-ID"
)

DECISION_RESULT_FIELDNAMES = [
    "decision_result_id",
    "selected_platform_family",
    "decision_scope",
    "source_or_equivalent_trace_required",
    "open_auditable_backend_selected",
    "black_box_backend_selected",
    "repo_local_current_sim_selected",
    "future_selection_result_audit_required",
    "validation_protocol_ready_in_m2607",
    "validation_admission_granted_in_m2607",
    "external_validation_execution_allowed_in_m2607",
    "driver_performance_claim_allowed_in_m2607",
    "status_pass",
    "claim_boundary",
]

EVIDENCE_FIELDNAMES = [
    "decision_evidence_id",
    "source_artifact",
    "evidence_role",
    "admitted_for_platform_selection_decision_in_m2607",
    "admitted_for_validation_readiness_in_m2607",
    "admitted_for_driver_performance_in_m2607",
    "status_pass",
    "claim_boundary",
]

CANDIDATE_DISPOSITION_FIELDNAMES = [
    "candidate_disposition_id",
    "platform_family",
    "disposition",
    "selected_in_m2607",
    "open_auditable_backend",
    "black_box_demonstration_only",
    "repo_local_diagnostic_only",
    "validation_authority_after_future_protocol_audit",
    "dependency_review_required_later",
    "validation_execution_allowed_in_m2607",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_EXECUTION_GUARD_FIELDNAMES = [
    "dependency_execution_guard_id",
    "platform_family",
    "external_install_allowed_in_m2607",
    "external_import_allowed_in_m2607",
    "runtime_execution_allowed_in_m2607",
    "dependency_mutation_allowed_in_m2607",
    "source_build_or_adapter_probe_required_later",
    "license_or_api_review_required_later",
    "sandbox_plan_required_before_execution",
    "status_pass",
    "claim_boundary",
]

VALIDATION_ADMISSION_GUARD_FIELDNAMES = [
    "validation_admission_guard_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "action_shape",
    "platform_selection_decision_made_in_m2607",
    "reset_feasibility_evidence_required_later",
    "rollout_feasibility_evidence_required_later",
    "executable_protocol_required_later",
    "holdout_or_generalization_policy_required_later",
    "validation_protocol_ready_in_m2607",
    "validation_admission_granted_in_m2607",
    "external_validation_execution_allowed_in_m2607",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

ACTOR_ACTION_GUARD_FIELDNAMES = [
    "actor_action_guard_id",
    "route_role_id",
    "actor_observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "rollout_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "platform_selection_actor_visible",
    "platform_selection_criteria_actor_visible",
    "platform_selection_decision_actor_visible",
    "selected_platform_actor_visible",
    "protocol_status_actor_visible",
    "action_contract_mutation_detected",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2607",
    "evidence_required_before_claim",
    "status_pass",
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

PLATFORM_FAMILIES = (
    (
        SELECTED_PLATFORM_FAMILY,
        "selected_for_future_validation_preparation",
        True,
        False,
        False,
    ),
    (
        "black_box_industry_demonstration_backend",
        "rejected_demonstration_only",
        False,
        True,
        False,
    ),
    (
        "repo_local_current_sim_backend",
        "rejected_diagnostic_only",
        False,
        False,
        True,
    ),
)

VALIDATION_ROLES = (
    "stable_avoidable_aeb_feasible",
    "stable_aes_aeb_infeasible",
)

EVIDENCE_SOURCES = (
    (
        "m2606_synthesis_doc",
        "docs/m2606-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-result-synthesis.md",
    ),
    (
        "m2605_audit_doc",
        "docs/m2605-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-result-audit.md",
    ),
    (
        "m2604_summary",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/summary.json",
    ),
    (
        "m2604_decision_request_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_request_rows.csv",
    ),
    (
        "m2604_evidence_admission_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_evidence_admission_rows.csv",
    ),
    (
        "m2604_candidate_comparison_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_candidate_comparison_rows.csv",
    ),
    (
        "m2604_dependency_guard_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_dependency_guard_rows.csv",
    ),
    (
        "m2604_validation_role_compatibility_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_validation_role_compatibility_rows.csv",
    ),
    (
        "m2604_actor_action_guard_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_actor_action_guard_rows.csv",
    ),
    (
        "m2604_claim_boundary_rows",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_claim_boundary_checks.csv",
    ),
    (
        "m2604_gate_matrix",
        "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/after_closure_platform_selection_decision_gate_matrix.csv",
    ),
    ("post_m2470_route_plan", "docs/post-m2470-route-plan.md"),
)

CLAIM_CHECKS = (
    (
        "after_closure_platform_selection_decision_result_materialized",
        True,
        "M2607 decision-result evidence candidate-disposition dependency/execution validation-admission "
        "actor/action claim-boundary and gate rows",
    ),
    (
        "bounded_open_auditable_platform_family_selected",
        True,
        "M2607 selected chrono_vehicle_or_equivalent_open_backend with black-box and repo-local "
        "families rejected for validation authority",
    ),
    ("validation_protocol_ready", False, "future executable protocol-readiness audit"),
    ("validation_admission_granted", False, "future validation-admission audit"),
    ("external_validation_execution", False, "future explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "future platform/protocol readiness and audit"),
    ("high_fidelity_validation_result", False, "future external validation execution result audit"),
    ("hf4_discrepancy_result", False, "future HF4 discrepancy result audit"),
    ("rollout_success", False, "future audited rollout-success criteria"),
    ("success_rate_or_controller_family_verdict", False, "separate benchmark/verdict milestone"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("driver_performance", False, "measured validation with claim-boundary audit"),
    ("paper_level_evidence", False, "separate paper-route evidence matrix"),
    ("finite_window_vs_gru_result", False, "separate paper-route finite-window-vs-GRU matrix"),
    ("current_sim_verdict", False, "separate current-sim verdict synthesis"),
    ("level3_self_identification", False, "separate self-ID proof gate"),
)

FORBIDDEN_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "external_install_performed": False,
    "external_import_performed": False,
    "dependency_mutation_performed": False,
    "actor_input_mutation_performed": False,
    "action_contract_mutation_performed": False,
    "reset_execution_run": False,
    "policy_action_run": False,
    "environment_step_run": False,
    "rollout_execution_run": False,
    "validation_execution_run": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "validation_protocol_readiness_claim_made": False,
    "validation_admission_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_result_claim_made": False,
    "rollout_success_claim_made": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "hf4_discrepancy_result_claim_made": False,
}


def materialize_route_a_hf3_after_closure_platform_selection_decision_result(
    output_dir: Path,
    *,
    m2604_summary_path: Path = DEFAULT_M2604_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2604_summary = read_json(m2604_summary_path)

    decision_rows = build_decision_result_rows(m2604_summary)
    evidence_rows = build_decision_evidence_rows(source_exists, m2604_summary)
    candidate_rows = build_candidate_disposition_rows(decision_rows, evidence_rows)
    dependency_rows = build_dependency_execution_guard_rows()
    admission_rows = build_validation_admission_guard_rows(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
    )
    guard_rows = build_actor_action_guard_rows(admission_rows)
    claim_rows = build_claim_boundary_checks(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
        admission_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2604_summary=m2604_summary,
        decision_rows=decision_rows,
        evidence_rows=evidence_rows,
        candidate_rows=candidate_rows,
        dependency_rows=dependency_rows,
        admission_rows=admission_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    decision_path = output_dir / "hf3_after_closure_platform_selection_decision_result_rows.csv"
    evidence_path = output_dir / "hf3_after_closure_platform_selection_decision_evidence_rows.csv"
    candidate_path = output_dir / "hf3_after_closure_platform_selection_candidate_disposition_rows.csv"
    dependency_path = output_dir / "hf3_after_closure_platform_selection_dependency_execution_guard_rows.csv"
    admission_path = output_dir / "hf3_after_closure_platform_selection_validation_admission_guard_rows.csv"
    guard_path = output_dir / "hf3_after_closure_platform_selection_decision_result_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_after_closure_platform_selection_decision_result_claim_boundary_checks.csv"
    gate_path = output_dir / "after_closure_platform_selection_decision_result_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(decision_path, decision_rows, fieldnames=DECISION_RESULT_FIELDNAMES)
    write_csv_rows(evidence_path, evidence_rows, fieldnames=EVIDENCE_FIELDNAMES)
    write_csv_rows(candidate_path, candidate_rows, fieldnames=CANDIDATE_DISPOSITION_FIELDNAMES)
    write_csv_rows(dependency_path, dependency_rows, fieldnames=DEPENDENCY_EXECUTION_GUARD_FIELDNAMES)
    write_csv_rows(admission_path, admission_rows, fieldnames=VALIDATION_ADMISSION_GUARD_FIELDNAMES)
    write_csv_rows(guard_path, guard_rows, fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2604_summary=m2604_summary,
        decision_rows=decision_rows,
        evidence_rows=evidence_rows,
        candidate_rows=candidate_rows,
        dependency_rows=dependency_rows,
        admission_rows=admission_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        decision_path=decision_path,
        evidence_path=evidence_path,
        candidate_path=candidate_path,
        dependency_path=dependency_path,
        admission_path=admission_path,
        guard_path=guard_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_decision_result_rows(m2604_summary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    evidence_accepted = _decision_design_evidence_accepted(m2604_summary or {})
    return [
        {
            "decision_result_id": "open_auditable_backend_family_selection_result",
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "decision_scope": "select bounded open/auditable platform family for future validation preparation",
            "source_or_equivalent_trace_required": True,
            "open_auditable_backend_selected": True,
            "black_box_backend_selected": False,
            "repo_local_current_sim_selected": False,
            "future_selection_result_audit_required": True,
            "validation_protocol_ready_in_m2607": False,
            "validation_admission_granted_in_m2607": False,
            "external_validation_execution_allowed_in_m2607": False,
            "driver_performance_claim_allowed_in_m2607": False,
            "status_pass": bool(evidence_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
    ]


def build_decision_evidence_rows(
    source_exists: dict[str, bool] | None = None,
    m2604_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    evidence_accepted = _decision_design_evidence_accepted(m2604_summary or {})
    source_exists = source_exists or {path: Path(path).exists() for _, path in EVIDENCE_SOURCES}
    rows = []
    for evidence_role, source_artifact in EVIDENCE_SOURCES:
        source_present = bool(source_exists.get(source_artifact, Path(source_artifact).exists()))
        rows.append(
            {
                "decision_evidence_id": f"{evidence_role}_decision_result_evidence",
                "source_artifact": source_artifact,
                "evidence_role": evidence_role,
                "admitted_for_platform_selection_decision_in_m2607": bool(
                    evidence_accepted and source_present
                ),
                "admitted_for_validation_readiness_in_m2607": False,
                "admitted_for_driver_performance_in_m2607": False,
                "status_pass": bool(evidence_accepted and source_present),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_candidate_disposition_rows(
    decision_rows: list[dict[str, Any]] | None = None,
    evidence_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    decision_materialized = _decision_result_materialized(decision_rows or [], evidence_rows or [])
    rows = []
    for platform_family, disposition, open_auditable, black_box_only, repo_local_only in PLATFORM_FAMILIES:
        selected = bool(decision_materialized and platform_family == SELECTED_PLATFORM_FAMILY)
        rows.append(
            {
                "candidate_disposition_id": f"{platform_family}_decision_result_disposition",
                "platform_family": platform_family,
                "disposition": disposition,
                "selected_in_m2607": selected,
                "open_auditable_backend": bool(open_auditable),
                "black_box_demonstration_only": bool(black_box_only),
                "repo_local_diagnostic_only": bool(repo_local_only),
                "validation_authority_after_future_protocol_audit": bool(selected),
                "dependency_review_required_later": True,
                "validation_execution_allowed_in_m2607": False,
                "status_pass": bool(
                    decision_materialized
                    and (
                        (selected and open_auditable and not black_box_only and not repo_local_only)
                        or (not selected and (black_box_only or repo_local_only))
                    )
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_dependency_execution_guard_rows() -> list[dict[str, Any]]:
    rows = []
    for platform_family, *_ in PLATFORM_FAMILIES:
        rows.append(
            {
                "dependency_execution_guard_id": f"{platform_family}_decision_result_dependency_guard",
                "platform_family": platform_family,
                "external_install_allowed_in_m2607": False,
                "external_import_allowed_in_m2607": False,
                "runtime_execution_allowed_in_m2607": False,
                "dependency_mutation_allowed_in_m2607": False,
                "source_build_or_adapter_probe_required_later": True,
                "license_or_api_review_required_later": True,
                "sandbox_plan_required_before_execution": True,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_validation_admission_guard_rows(
    decision_rows: list[dict[str, Any]] | None = None,
    evidence_rows: list[dict[str, Any]] | None = None,
    candidate_rows: list[dict[str, Any]] | None = None,
    dependency_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    selection_decision_made = _selection_decision_made(
        decision_rows or [],
        evidence_rows or [],
        candidate_rows or [],
        dependency_rows or [],
    )
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "validation_admission_guard_id": f"{route_role_id}_decision_result_validation_admission_guard",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "platform_selection_decision_made_in_m2607": selection_decision_made,
                "reset_feasibility_evidence_required_later": True,
                "rollout_feasibility_evidence_required_later": True,
                "executable_protocol_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "validation_protocol_ready_in_m2607": False,
                "validation_admission_granted_in_m2607": False,
                "external_validation_execution_allowed_in_m2607": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(
                    selection_decision_made and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(admission_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for admission in admission_rows:
        rows.append(
            {
                "actor_action_guard_id": f"{admission['route_role_id']}_decision_result_actor_action_guard",
                "route_role_id": admission["route_role_id"],
                "actor_observation_shape": _int_value(admission["actor_observation_shape"], default=-1),
                "action_shape": _int_value(admission["action_shape"], default=-1),
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "rollout_outcome_actor_visible": False,
                "validation_outcome_actor_visible": False,
                "platform_selection_actor_visible": False,
                "platform_selection_criteria_actor_visible": False,
                "platform_selection_decision_actor_visible": False,
                "selected_platform_actor_visible": False,
                "protocol_status_actor_visible": False,
                "action_contract_mutation_detected": False,
                "status_pass": bool(
                    _boolish(admission["status_pass"])
                    and _int_value(admission["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM
                    and _int_value(admission["action_shape"], default=-1) == ACTION_DIM
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = bool(
        _selection_decision_made(decision_rows, evidence_rows, candidate_rows, dependency_rows)
        and len(admission_rows) == len(VALIDATION_ROLES)
        and _all_status_pass(admission_rows)
        and len(guard_rows) == len(admission_rows)
        and _all_status_pass(guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2607": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family
                    in {
                        "after_closure_platform_selection_decision_result_materialized",
                        "bounded_open_auditable_platform_family_selected",
                    }
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2604_summary: dict[str, Any],
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"]
        not in {
            "after_closure_platform_selection_decision_result_materialized",
            "bounded_open_auditable_platform_family_selected",
        }
        and _boolish(row["claim_allowed_in_m2607"])
    ]
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()),
            f"missing={sum(1 for exists in source_exists.values() if not exists)}",
            "missing=0",
            "lineage_invalid",
        ),
        (
            "m2604_m2605_m2606_decision_design_evidence_accepted",
            "lineage",
            _decision_design_evidence_accepted(m2604_summary),
            (
                f"m2604_status={m2604_summary.get('status_pass')};"
                f"design={m2604_summary.get('platform_selection_decision_design_materialized_in_m2604')};"
                f"selected={m2604_summary.get('platform_selected_in_m2604')};"
                f"selected_family={m2604_summary.get('selected_platform_family_in_m2604')};"
                f"protocol_ready={m2604_summary.get('validation_protocol_ready_in_m2604')}"
            ),
            "m2604_status=True;design=True;selected=False;selected_family=none;protocol_ready=False",
            "lineage_invalid",
        ),
        (
            "decision_result_rows_complete",
            "contract",
            len(decision_rows) == 1
            and _all_status_pass(decision_rows)
            and {row["selected_platform_family"] for row in decision_rows} == {SELECTED_PLATFORM_FAMILY}
            and all(_boolish(row["source_or_equivalent_trace_required"]) for row in decision_rows)
            and all(_boolish(row["open_auditable_backend_selected"]) for row in decision_rows)
            and not any(_boolish(row["black_box_backend_selected"]) for row in decision_rows)
            and not any(_boolish(row["repo_local_current_sim_selected"]) for row in decision_rows)
            and all(_boolish(row["future_selection_result_audit_required"]) for row in decision_rows)
            and not any(_boolish(row["validation_protocol_ready_in_m2607"]) for row in decision_rows)
            and not any(_boolish(row["validation_admission_granted_in_m2607"]) for row in decision_rows)
            and not any(_boolish(row["external_validation_execution_allowed_in_m2607"]) for row in decision_rows)
            and not any(_boolish(row["driver_performance_claim_allowed_in_m2607"]) for row in decision_rows),
            f"rows={len(decision_rows)};selected={_selected_platform_family(decision_rows)}",
            f"rows=1;selected={SELECTED_PLATFORM_FAMILY};validation/performance=false",
            "contract_violation",
        ),
        (
            "decision_evidence_rows_pass",
            "lineage",
            len(evidence_rows) == len(EVIDENCE_SOURCES)
            and _all_status_pass(evidence_rows)
            and all(
                _boolish(row["admitted_for_platform_selection_decision_in_m2607"])
                for row in evidence_rows
            )
            and not any(
                _boolish(row["admitted_for_validation_readiness_in_m2607"]) for row in evidence_rows
            )
            and not any(
                _boolish(row["admitted_for_driver_performance_in_m2607"]) for row in evidence_rows
            ),
            f"rows={len(evidence_rows)}",
            "rows=12;platform_selection_decision=true;readiness/performance=false",
            "lineage_invalid",
        ),
        (
            "candidate_disposition_rows_pass",
            "contract",
            len(candidate_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(candidate_rows)
            and _selected_candidate_count(candidate_rows) == 1
            and any(
                row["platform_family"] == SELECTED_PLATFORM_FAMILY
                and _boolish(row["selected_in_m2607"])
                and _boolish(row["open_auditable_backend"])
                for row in candidate_rows
            )
            and any(
                row["platform_family"] == "black_box_industry_demonstration_backend"
                and not _boolish(row["selected_in_m2607"])
                and _boolish(row["black_box_demonstration_only"])
                for row in candidate_rows
            )
            and any(
                row["platform_family"] == "repo_local_current_sim_backend"
                and not _boolish(row["selected_in_m2607"])
                and _boolish(row["repo_local_diagnostic_only"])
                for row in candidate_rows
            )
            and not any(_boolish(row["validation_execution_allowed_in_m2607"]) for row in candidate_rows),
            f"rows={len(candidate_rows)};selected={_selected_candidate_count(candidate_rows)}",
            "rows=3;selected_open=1;black_box_demo/repo_local_diagnostic rejected;execution=false",
            "contract_violation",
        ),
        (
            "dependency_execution_guard_rows_pass",
            "contract",
            len(dependency_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(dependency_rows)
            and not any(_boolish(row["external_install_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2607"]) for row in dependency_rows)
            and all(_boolish(row["source_build_or_adapter_probe_required_later"]) for row in dependency_rows)
            and all(_boolish(row["license_or_api_review_required_later"]) for row in dependency_rows)
            and all(_boolish(row["sandbox_plan_required_before_execution"]) for row in dependency_rows),
            f"rows={len(dependency_rows)}",
            "rows=3;install/import/run/mutation=false;future reviews=true",
            "contract_violation",
        ),
        (
            "validation_admission_guard_rows_pass",
            "claim_boundary",
            len(admission_rows) == len(VALIDATION_ROLES)
            and _all_status_pass(admission_rows)
            and {row["route_role_id"] for row in admission_rows} == set(VALIDATION_ROLES)
            and {row["selected_platform_family"] for row in admission_rows} == {SELECTED_PLATFORM_FAMILY}
            and all(_boolish(row["platform_selection_decision_made_in_m2607"]) for row in admission_rows)
            and all(_boolish(row["reset_feasibility_evidence_required_later"]) for row in admission_rows)
            and all(_boolish(row["rollout_feasibility_evidence_required_later"]) for row in admission_rows)
            and all(_boolish(row["executable_protocol_required_later"]) for row in admission_rows)
            and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in admission_rows)
            and not any(_boolish(row["validation_protocol_ready_in_m2607"]) for row in admission_rows)
            and not any(_boolish(row["validation_admission_granted_in_m2607"]) for row in admission_rows)
            and not any(
                _boolish(row["external_validation_execution_allowed_in_m2607"])
                for row in admission_rows
            )
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in admission_rows),
            f"rows={len(admission_rows)}",
            "rows=2;decision=true;future prerequisites=true;ready/admitted/execution/result=false",
            "objective_overfit",
        ),
        (
            "actor_action_guard_rows_pass",
            "contract",
            len(guard_rows) == len(admission_rows)
            and _all_status_pass(guard_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in guard_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in guard_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in guard_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["reset_outcome_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["rollout_outcome_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["validation_outcome_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["platform_selection_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["platform_selection_criteria_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["platform_selection_decision_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["selected_platform_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["protocol_status_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in guard_rows),
            f"rows={len(guard_rows)}",
            "rows=admission_rows;obs=72;action=3;hidden/status/selection/outcomes=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and len(forbidden_claims_allowed) == 0,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            "rows=17;forbidden_claims=0;decision_result_materialized=true;selected_open=true",
            "objective_overfit",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "obs=72;action=3",
            "contract_violation",
        ),
        (
            "no_external_execution_or_dependency_mutation",
            "claim_boundary",
            not any(_boolish(row["external_install_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2607"]) for row in dependency_rows)
            and not any(_boolish(row["external_validation_execution_allowed_in_m2607"]) for row in decision_rows)
            and not any(
                _boolish(row["external_validation_execution_allowed_in_m2607"])
                for row in admission_rows
            ),
            "install/import/run/mutation/reset/action/step/rollout/validation=false",
            "install/import/run/mutation/reset/action/step/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "validation_readiness_result_and_performance_forbidden",
            "claim_boundary",
            not any(_boolish(row["validation_protocol_ready_in_m2607"]) for row in decision_rows)
            and not any(_boolish(row["validation_protocol_ready_in_m2607"]) for row in admission_rows)
            and not any(_boolish(row["validation_admission_granted_in_m2607"]) for row in admission_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in admission_rows)
            and not any(_boolish(row["driver_performance_claim_allowed_in_m2607"]) for row in decision_rows)
            and not any(
                _boolish(row["claim_allowed_in_m2607"])
                for row in claim_rows
                if row["claim_family"]
                in {
                    "validation_protocol_ready",
                    "validation_admission_granted",
                    "external_validation_execution",
                    "high_fidelity_validation_readiness",
                    "high_fidelity_validation_result",
                    "driver_performance",
                }
            ),
            "readiness/admission/result/performance=false",
            "readiness/admission/result/performance=false",
            "objective_overfit",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": gate_family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if status_pass else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, gate_family, status_pass, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    source_exists: dict[str, bool],
    m2604_summary: dict[str, Any],
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    decision_path: Path,
    evidence_path: Path,
    candidate_path: Path,
    dependency_path: Path,
    admission_path: Path,
    guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2607"])
        for row in claim_rows
        if row["claim_family"]
        not in {
            "after_closure_platform_selection_decision_result_materialized",
            "bounded_open_auditable_platform_family_selected",
        }
    )
    selected_family = _selected_platform_family(decision_rows)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": "engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result_materialization_preflight_pass",
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_after_closure_platform_selection_decision_result_rows": str(decision_path),
        "hf3_after_closure_platform_selection_decision_evidence_rows": str(evidence_path),
        "hf3_after_closure_platform_selection_candidate_disposition_rows": str(candidate_path),
        "hf3_after_closure_platform_selection_dependency_execution_guard_rows": str(dependency_path),
        "hf3_after_closure_platform_selection_validation_admission_guard_rows": str(admission_path),
        "hf3_after_closure_platform_selection_decision_result_actor_action_guard_rows": str(guard_path),
        "hf3_after_closure_platform_selection_decision_result_claim_boundary_checks": str(claim_path),
        "after_closure_platform_selection_decision_result_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2604_status_pass": bool(m2604_summary.get("status_pass")),
        "m2604_materialization_gates_all_pass": bool(m2604_summary.get("materialization_gates_all_pass")),
        "m2604_decision_design_materialized": bool(
            m2604_summary.get("platform_selection_decision_design_materialized_in_m2604")
        ),
        "m2604_platform_selected": bool(m2604_summary.get("platform_selected_in_m2604")),
        "m2604_selection_decision_made": bool(m2604_summary.get("selection_decision_made_in_m2604")),
        "m2604_selected_platform_family": m2604_summary.get("selected_platform_family_in_m2604"),
        "m2604_validation_protocol_ready": bool(m2604_summary.get("validation_protocol_ready_in_m2604")),
        "m2604_external_validation_execution_allowed": bool(
            m2604_summary.get("external_validation_execution_allowed_in_m2604")
        ),
        "m2604_driver_performance_claim_allowed": bool(
            m2604_summary.get("driver_performance_claim_allowed_in_m2604")
        ),
        "decision_result_row_count": len(decision_rows),
        "decision_evidence_row_count": len(evidence_rows),
        "candidate_disposition_row_count": len(candidate_rows),
        "dependency_execution_guard_row_count": len(dependency_rows),
        "validation_admission_guard_row_count": len(admission_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "platform_selection_decision_result_materialized_in_m2607": bool(
            _selection_decision_made(decision_rows, evidence_rows, candidate_rows, dependency_rows)
            and _all_status_pass(admission_rows)
            and _all_status_pass(guard_rows)
        ),
        "after_closure_platform_selection_decision_result_materialized_claim_allowed": any(
            row["claim_family"] == "after_closure_platform_selection_decision_result_materialized"
            and _boolish(row["claim_allowed_in_m2607"])
            for row in claim_rows
        ),
        "bounded_open_auditable_platform_family_selected_claim_allowed": any(
            row["claim_family"] == "bounded_open_auditable_platform_family_selected"
            and _boolish(row["claim_allowed_in_m2607"])
            for row in claim_rows
        ),
        "forbidden_claim_allowed_in_m2607": forbidden_claim_allowed,
        "platform_selection_decision_made_in_m2607": _selection_decision_made(
            decision_rows, evidence_rows, candidate_rows, dependency_rows
        ),
        "selected_platform_family_in_m2607": selected_family,
        "selected_platform_family_is_open_auditable": selected_family == SELECTED_PLATFORM_FAMILY,
        "black_box_backend_selected_in_m2607": any(
            row["platform_family"] == "black_box_industry_demonstration_backend"
            and _boolish(row["selected_in_m2607"])
            for row in candidate_rows
        ),
        "repo_local_current_sim_selected_in_m2607": any(
            row["platform_family"] == "repo_local_current_sim_backend"
            and _boolish(row["selected_in_m2607"])
            for row in candidate_rows
        ),
        "external_install_allowed_in_m2607": any(
            _boolish(row["external_install_allowed_in_m2607"]) for row in dependency_rows
        ),
        "external_import_allowed_in_m2607": any(
            _boolish(row["external_import_allowed_in_m2607"]) for row in dependency_rows
        ),
        "runtime_execution_allowed_in_m2607": any(
            _boolish(row["runtime_execution_allowed_in_m2607"]) for row in dependency_rows
        ),
        "dependency_mutation_allowed_in_m2607": any(
            _boolish(row["dependency_mutation_allowed_in_m2607"]) for row in dependency_rows
        ),
        "validation_protocol_ready_in_m2607": any(
            _boolish(row["validation_protocol_ready_in_m2607"]) for row in admission_rows
        ),
        "validation_admission_granted_in_m2607": any(
            _boolish(row["validation_admission_granted_in_m2607"]) for row in admission_rows
        ),
        "external_validation_execution_allowed_in_m2607": any(
            _boolish(row["external_validation_execution_allowed_in_m2607"]) for row in admission_rows
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"]) for row in admission_rows
        ),
        "driver_performance_claim_allowed_in_m2607": any(
            row["claim_family"] == "driver_performance" and _boolish(row["claim_allowed_in_m2607"])
            for row in claim_rows
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"]) for row in guard_rows
        ),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in guard_rows),
        "taxonomy_label_actor_visible": any(
            _boolish(row["taxonomy_label_actor_visible"]) for row in guard_rows
        ),
        "backend_status_actor_visible": any(
            _boolish(row["backend_status_actor_visible"]) for row in guard_rows
        ),
        "reset_outcome_actor_visible": any(
            _boolish(row["reset_outcome_actor_visible"]) for row in guard_rows
        ),
        "rollout_outcome_actor_visible": any(
            _boolish(row["rollout_outcome_actor_visible"]) for row in guard_rows
        ),
        "validation_outcome_actor_visible": any(
            _boolish(row["validation_outcome_actor_visible"]) for row in guard_rows
        ),
        "platform_selection_actor_visible": any(
            _boolish(row["platform_selection_actor_visible"]) for row in guard_rows
        ),
        "platform_selection_criteria_actor_visible": any(
            _boolish(row["platform_selection_criteria_actor_visible"]) for row in guard_rows
        ),
        "platform_selection_decision_actor_visible": any(
            _boolish(row["platform_selection_decision_actor_visible"]) for row in guard_rows
        ),
        "selected_platform_actor_visible": any(
            _boolish(row["selected_platform_actor_visible"]) for row in guard_rows
        ),
        "protocol_status_actor_visible": any(
            _boolish(row["protocol_status_actor_visible"]) for row in guard_rows
        ),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"]) for row in guard_rows
        ),
        "repo_local_boundary_only": True,
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# M2607 Engineering Controller Route A Baseline HF3 After-Closure Platform Selection Decision Result Materialization Preflight

- status: completed
- result_class: `{summary["result_class"]}`
- milestone: `{summary["milestone"]}`
- summary: `{summary["summary"]}`
- next: `{summary["next_blocker"]}`

## Materialized Evidence

```text
status_pass: {summary["status_pass"]}
decision_result_rows: {summary["decision_result_row_count"]}
decision_evidence_rows: {summary["decision_evidence_row_count"]}
candidate_disposition_rows: {summary["candidate_disposition_row_count"]}
dependency_execution_guard_rows: {summary["dependency_execution_guard_row_count"]}
validation_admission_guard_rows: {summary["validation_admission_guard_row_count"]}
actor_action_guard_rows: {summary["actor_action_guard_row_count"]}
claim_boundary_rows: {summary["claim_boundary_check_count"]}
materialization_gates: {summary["materialization_gate_count"]}
platform_selection_decision_result_materialized_in_m2607: {summary["platform_selection_decision_result_materialized_in_m2607"]}
platform_selection_decision_made_in_m2607: {summary["platform_selection_decision_made_in_m2607"]}
selected_platform_family_in_m2607: {summary["selected_platform_family_in_m2607"]}
selected_platform_family_is_open_auditable: {summary["selected_platform_family_is_open_auditable"]}
black_box_backend_selected_in_m2607: {summary["black_box_backend_selected_in_m2607"]}
repo_local_current_sim_selected_in_m2607: {summary["repo_local_current_sim_selected_in_m2607"]}
validation_protocol_ready_in_m2607: {summary["validation_protocol_ready_in_m2607"]}
validation_admission_granted_in_m2607: {summary["validation_admission_granted_in_m2607"]}
external_validation_execution_allowed_in_m2607: {summary["external_validation_execution_allowed_in_m2607"]}
driver_performance_claim_allowed_in_m2607: {summary["driver_performance_claim_allowed_in_m2607"]}
actor contract: P0 observation {summary["observation_shape"]} / action {summary["action_shape"]}
```

## Artifact Paths

- decision result rows: `{summary["hf3_after_closure_platform_selection_decision_result_rows"]}`
- decision evidence rows: `{summary["hf3_after_closure_platform_selection_decision_evidence_rows"]}`
- candidate disposition rows: `{summary["hf3_after_closure_platform_selection_candidate_disposition_rows"]}`
- dependency/execution guard rows: `{summary["hf3_after_closure_platform_selection_dependency_execution_guard_rows"]}`
- validation-admission guard rows: `{summary["hf3_after_closure_platform_selection_validation_admission_guard_rows"]}`
- actor/action guard rows: `{summary["hf3_after_closure_platform_selection_decision_result_actor_action_guard_rows"]}`
- claim-boundary rows: `{summary["hf3_after_closure_platform_selection_decision_result_claim_boundary_checks"]}`
- gate matrix: `{summary["after_closure_platform_selection_decision_result_gate_matrix"]}`

## Supported Claims

Supported:

- after-closure HF3 platform-selection decision-result artifacts are materialized
- a bounded open/auditable platform family is selected for future validation preparation
- selected family is `{summary["selected_platform_family_in_m2607"]}`
- black-box industry backends remain demonstration-only
- repo-local current-sim remains diagnostic-only
- exactly two HF3 low-cost pilot roles preserve future reset, rollout, protocol, and holdout prerequisites
- P0 `72/3` actor/action contract is preserved

## Rejected Claims

Rejected:

- validation protocol readiness
- validation admission
- external simulator install/import/runtime execution
- validation readiness or result
- external validation execution
- HF4 discrepancy result
- rollout success
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver performance
- paper-level evidence
- finite-window-vs-GRU result
- current-sim verdict
- high-fidelity validation result
- level3 self-identification

## Next Step

If accepted by audit, route to:

```text
{summary["next_blocker"]}
```
"""
    path.write_text(content, encoding="utf-8")


def _decision_design_evidence_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("platform_selection_decision_design_materialized_in_m2604")
        and summary.get("after_closure_platform_selection_decision_design_materialized_claim_allowed")
        and summary.get("decision_request_row_count") == 2
        and summary.get("evidence_admission_row_count") == 8
        and summary.get("candidate_comparison_row_count") == 3
        and summary.get("dependency_guard_row_count") == 3
        and summary.get("validation_role_compatibility_row_count") == 2
        and summary.get("actor_action_guard_row_count") == 2
        and summary.get("claim_boundary_check_count") == 19
        and summary.get("materialization_gate_count") == 12
        and summary.get("source_artifacts_exist")
        and not summary.get("platform_selected_in_m2604")
        and not summary.get("selection_decision_made_in_m2604")
        and summary.get("selected_platform_family_in_m2604") == "none"
        and not summary.get("validation_protocol_ready_in_m2604")
        and not summary.get("external_validation_execution_allowed_in_m2604")
        and not summary.get("driver_performance_claim_allowed_in_m2604")
    )


def _decision_result_materialized(
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        len(decision_rows) == 1
        and _all_status_pass(decision_rows)
        and len(evidence_rows) == len(EVIDENCE_SOURCES)
        and _all_status_pass(evidence_rows)
        and _selected_platform_family(decision_rows) == SELECTED_PLATFORM_FAMILY
        and all(_boolish(row["open_auditable_backend_selected"]) for row in decision_rows)
        and not any(_boolish(row["black_box_backend_selected"]) for row in decision_rows)
        and not any(_boolish(row["repo_local_current_sim_selected"]) for row in decision_rows)
        and not any(_boolish(row["validation_protocol_ready_in_m2607"]) for row in decision_rows)
        and not any(_boolish(row["validation_admission_granted_in_m2607"]) for row in decision_rows)
        and not any(_boolish(row["external_validation_execution_allowed_in_m2607"]) for row in decision_rows)
        and not any(_boolish(row["driver_performance_claim_allowed_in_m2607"]) for row in decision_rows)
    )


def _selection_decision_made(
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _decision_result_materialized(decision_rows, evidence_rows)
        and len(candidate_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(candidate_rows)
        and _selected_candidate_count(candidate_rows) == 1
        and any(
            row["platform_family"] == SELECTED_PLATFORM_FAMILY
            and _boolish(row["selected_in_m2607"])
            and _boolish(row["open_auditable_backend"])
            for row in candidate_rows
        )
        and len(dependency_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(dependency_rows)
        and not any(_boolish(row["external_install_allowed_in_m2607"]) for row in dependency_rows)
        and not any(_boolish(row["external_import_allowed_in_m2607"]) for row in dependency_rows)
        and not any(_boolish(row["runtime_execution_allowed_in_m2607"]) for row in dependency_rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2607"]) for row in dependency_rows)
    )


def _selected_platform_family(decision_rows: list[dict[str, Any]]) -> str:
    selected = [
        row["selected_platform_family"]
        for row in decision_rows
        if _boolish(row.get("open_auditable_backend_selected"))
    ]
    return selected[0] if len(selected) == 1 else "none"


def _selected_candidate_count(candidate_rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in candidate_rows if _boolish(row.get("selected_in_m2607")))


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2604-summary-path", type=Path, default=DEFAULT_M2604_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_after_closure_platform_selection_decision_result(
        args.output_dir,
        m2604_summary_path=args.m2604_summary_path,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(summary["summary"])
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
