"""Route A HF3 after-closure platform-selection decision materialization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2604-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2605-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-"
    "materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2604-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-"
    "decision-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision"
)
DEFAULT_M2600_SUMMARY = Path(
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/summary.json"
)

SOURCE_ARTIFACTS = (
    "docs/m2603-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-design.md",
    "docs/m2602-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-result-synthesis.md",
    "docs/m2601-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-result-audit.md",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/summary.json",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_criteria_rows.csv",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_auditability_rows.csv",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_dependency_import_risk_rows.csv",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_validation_role_compatibility_rows.csv",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_actor_action_guard_rows.csv",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_claim_boundary_checks.csv",
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/after_closure_platform_selection_criteria_gate_matrix.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 after-closure platform-selection decision-design materialization preflight only; "
    "decision-design artifacts may be materialized; not actual platform selection, selection "
    "decision, selected platform family, validation protocol readiness, validation admission, "
    "external validation execution, high-fidelity validation readiness/result, HF4 discrepancy "
    "result, rollout success, ranking, driver performance, paper, FW-vs-GRU, current-sim verdict, "
    "high-fidelity validation, or self-ID"
)

DECISION_REQUEST_FIELDNAMES = [
    "decision_request_id",
    "decision_scope",
    "criteria_materialization_accepted_before_request",
    "actual_selection_allowed_in_m2604",
    "selection_decision_made_in_m2604",
    "selected_platform_family_in_m2604",
    "future_selection_requires_result_audit",
    "future_protocol_readiness_required_after_selection",
    "status_pass",
    "claim_boundary",
]

EVIDENCE_ADMISSION_FIELDNAMES = [
    "evidence_admission_id",
    "source_artifact",
    "evidence_role",
    "admitted_for_decision_design_in_m2604",
    "admitted_for_actual_selection_in_m2604",
    "admitted_for_validation_readiness_in_m2604",
    "status_pass",
    "claim_boundary",
]

CANDIDATE_COMPARISON_FIELDNAMES = [
    "candidate_comparison_id",
    "platform_family",
    "comparison_role",
    "open_auditable_backend_preferred",
    "source_or_equivalent_trace_required",
    "black_box_demonstration_only",
    "repo_local_diagnostic_only",
    "eligible_for_future_selection_after_audit",
    "selected_in_m2604",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_GUARD_FIELDNAMES = [
    "dependency_guard_id",
    "platform_family",
    "external_install_allowed_in_m2604",
    "external_import_allowed_in_m2604",
    "runtime_execution_allowed_in_m2604",
    "dependency_mutation_allowed_in_m2604",
    "license_or_api_review_required_before_install",
    "source_build_or_adapter_probe_required_before_selection",
    "sandbox_plan_required_before_execution",
    "status_pass",
    "claim_boundary",
]

VALIDATION_ROLE_FIELDNAMES = [
    "compatibility_id",
    "route_role_id",
    "candidate_role_label",
    "actor_observation_shape",
    "action_shape",
    "decision_design_materialized_in_m2604",
    "reset_feasibility_evidence_required_later",
    "rollout_feasibility_evidence_required_later",
    "holdout_or_generalization_policy_required_later",
    "external_validation_execution_allowed_in_m2604",
    "validation_protocol_ready_in_m2604",
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
    "protocol_status_actor_visible",
    "action_contract_mutation_detected",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2604",
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
        "chrono_vehicle_or_equivalent_open_backend",
        "preferred future validation backend candidate after decision materialization audit",
        True,
        True,
        False,
        False,
        True,
    ),
    (
        "black_box_industry_demonstration_backend",
        "optional demonstration backend only, not validation authority",
        False,
        False,
        True,
        False,
        False,
    ),
    (
        "repo_local_current_sim_backend",
        "repo-local diagnostic and adapter contract source only, not validation authority",
        False,
        True,
        False,
        True,
        False,
    ),
)

VALIDATION_ROLES = (
    (
        "stable_avoidable_aeb_feasible",
        "stable avoidable / AEB-feasible low-cost pilot decision compatibility",
    ),
    (
        "stable_aes_aeb_infeasible",
        "stable AES / AEB-infeasible low-cost pilot decision compatibility",
    ),
)

EVIDENCE_SOURCES = (
    (
        "criteria_materialization_summary",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/summary.json",
    ),
    (
        "criteria_rows",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_criteria_rows.csv",
    ),
    (
        "auditability_rows",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_auditability_rows.csv",
    ),
    (
        "dependency_import_risk_rows",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_dependency_import_risk_rows.csv",
    ),
    (
        "validation_role_compatibility_rows",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_validation_role_compatibility_rows.csv",
    ),
    (
        "actor_action_guard_rows",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_actor_action_guard_rows.csv",
    ),
    (
        "claim_boundary_rows",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_claim_boundary_checks.csv",
    ),
    (
        "criteria_gate_matrix",
        "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/after_closure_platform_selection_criteria_gate_matrix.csv",
    ),
)

CLAIM_CHECKS = (
    (
        "after_closure_platform_selection_decision_design_materialized",
        True,
        "M2604 decision request evidence-admission candidate-comparison dependency guard "
        "validation-role compatibility actor/action guard claim-boundary and gate rows",
    ),
    ("platform_selected_for_validation", False, "later explicit platform-selection result audit"),
    ("selection_decision_made", False, "later platform-selection decision result milestone"),
    ("selected_platform_family", False, "later platform-selection decision result milestone"),
    ("validation_protocol_ready", False, "later protocol-readiness audit with executable protocol"),
    ("validation_admission_granted", False, "later validation-admission result audit"),
    ("external_validation_execution", False, "later explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "later readiness decision after platform/protocol audit"),
    ("high_fidelity_validation_result", False, "later external validation execution result audit"),
    ("hf4_discrepancy_result", False, "later HF4 external validation and discrepancy result audit"),
    ("rollout_success", False, "later audited rollout-success criteria"),
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
    "platform_selection_claim_made": False,
    "selection_decision_claim_made": False,
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


def materialize_route_a_hf3_after_closure_platform_selection_decision(
    output_dir: Path,
    *,
    m2600_summary_path: Path = DEFAULT_M2600_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2600_summary = read_json(m2600_summary_path)

    decision_rows = build_decision_request_rows(m2600_summary)
    evidence_rows = build_evidence_admission_rows(source_exists, m2600_summary)
    candidate_rows = build_candidate_comparison_rows(decision_rows, evidence_rows)
    dependency_rows = build_dependency_guard_rows()
    compatibility_rows = build_validation_role_compatibility_rows(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
    )
    guard_rows = build_actor_action_guard_rows(compatibility_rows)
    claim_rows = build_claim_boundary_checks(
        decision_rows,
        evidence_rows,
        candidate_rows,
        dependency_rows,
        compatibility_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2600_summary=m2600_summary,
        decision_rows=decision_rows,
        evidence_rows=evidence_rows,
        candidate_rows=candidate_rows,
        dependency_rows=dependency_rows,
        compatibility_rows=compatibility_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    decision_path = output_dir / "hf3_after_closure_platform_selection_decision_request_rows.csv"
    evidence_path = output_dir / "hf3_after_closure_platform_selection_evidence_admission_rows.csv"
    candidate_path = output_dir / "hf3_after_closure_platform_selection_candidate_comparison_rows.csv"
    dependency_path = output_dir / "hf3_after_closure_platform_selection_dependency_guard_rows.csv"
    compatibility_path = (
        output_dir / "hf3_after_closure_platform_selection_validation_role_compatibility_rows.csv"
    )
    guard_path = output_dir / "hf3_after_closure_platform_selection_decision_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_after_closure_platform_selection_decision_claim_boundary_checks.csv"
    gate_path = output_dir / "after_closure_platform_selection_decision_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(decision_path, decision_rows, fieldnames=DECISION_REQUEST_FIELDNAMES)
    write_csv_rows(evidence_path, evidence_rows, fieldnames=EVIDENCE_ADMISSION_FIELDNAMES)
    write_csv_rows(candidate_path, candidate_rows, fieldnames=CANDIDATE_COMPARISON_FIELDNAMES)
    write_csv_rows(dependency_path, dependency_rows, fieldnames=DEPENDENCY_GUARD_FIELDNAMES)
    write_csv_rows(compatibility_path, compatibility_rows, fieldnames=VALIDATION_ROLE_FIELDNAMES)
    write_csv_rows(guard_path, guard_rows, fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2600_summary=m2600_summary,
        decision_rows=decision_rows,
        evidence_rows=evidence_rows,
        candidate_rows=candidate_rows,
        dependency_rows=dependency_rows,
        compatibility_rows=compatibility_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        decision_path=decision_path,
        evidence_path=evidence_path,
        candidate_path=candidate_path,
        dependency_path=dependency_path,
        compatibility_path=compatibility_path,
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


def build_decision_request_rows(m2600_summary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    criteria_accepted = _criteria_evidence_accepted(m2600_summary or {})
    scopes = (
        (
            "preferred_open_auditable_backend_decision_request",
            "prepare future selection request for an open/auditable backend or equivalent after audit",
        ),
        (
            "demonstration_and_diagnostic_exclusion_request",
            "represent black-box demonstration-only and repo-local diagnostic-only exclusions",
        ),
    )
    return [
        {
            "decision_request_id": decision_request_id,
            "decision_scope": decision_scope,
            "criteria_materialization_accepted_before_request": criteria_accepted,
            "actual_selection_allowed_in_m2604": False,
            "selection_decision_made_in_m2604": False,
            "selected_platform_family_in_m2604": "none",
            "future_selection_requires_result_audit": True,
            "future_protocol_readiness_required_after_selection": True,
            "status_pass": bool(criteria_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for decision_request_id, decision_scope in scopes
    ]


def build_evidence_admission_rows(
    source_exists: dict[str, bool] | None = None,
    m2600_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    criteria_accepted = _criteria_evidence_accepted(m2600_summary or {})
    source_exists = source_exists or {path: Path(path).exists() for _, path in EVIDENCE_SOURCES}
    rows = []
    for evidence_role, source_artifact in EVIDENCE_SOURCES:
        source_present = bool(source_exists.get(source_artifact, Path(source_artifact).exists()))
        rows.append(
            {
                "evidence_admission_id": f"{evidence_role}_decision_design_admission",
                "source_artifact": source_artifact,
                "evidence_role": evidence_role,
                "admitted_for_decision_design_in_m2604": bool(criteria_accepted and source_present),
                "admitted_for_actual_selection_in_m2604": False,
                "admitted_for_validation_readiness_in_m2604": False,
                "status_pass": bool(criteria_accepted and source_present),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_candidate_comparison_rows(
    decision_rows: list[dict[str, Any]] | None = None,
    evidence_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    design_ready = bool(
        decision_rows
        and evidence_rows
        and _all_status_pass(decision_rows)
        and _all_status_pass(evidence_rows)
        and not any(_boolish(row["actual_selection_allowed_in_m2604"]) for row in decision_rows)
        and not any(_boolish(row["selection_decision_made_in_m2604"]) for row in decision_rows)
    )
    rows = []
    for (
        platform_family,
        role,
        open_preferred,
        source_trace_required,
        black_box_only,
        repo_local_only,
        eligible_later,
    ) in PLATFORM_FAMILIES:
        rows.append(
            {
                "candidate_comparison_id": f"{platform_family}_decision_candidate_comparison",
                "platform_family": platform_family,
                "comparison_role": role,
                "open_auditable_backend_preferred": bool(open_preferred),
                "source_or_equivalent_trace_required": bool(source_trace_required),
                "black_box_demonstration_only": bool(black_box_only),
                "repo_local_diagnostic_only": bool(repo_local_only),
                "eligible_for_future_selection_after_audit": bool(eligible_later and design_ready),
                "selected_in_m2604": False,
                "status_pass": bool(design_ready),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_dependency_guard_rows() -> list[dict[str, Any]]:
    rows = []
    for platform_family, *_ in PLATFORM_FAMILIES:
        rows.append(
            {
                "dependency_guard_id": f"{platform_family}_decision_dependency_guard",
                "platform_family": platform_family,
                "external_install_allowed_in_m2604": False,
                "external_import_allowed_in_m2604": False,
                "runtime_execution_allowed_in_m2604": False,
                "dependency_mutation_allowed_in_m2604": False,
                "license_or_api_review_required_before_install": True,
                "source_build_or_adapter_probe_required_before_selection": True,
                "sandbox_plan_required_before_execution": True,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_validation_role_compatibility_rows(
    decision_rows: list[dict[str, Any]] | None = None,
    evidence_rows: list[dict[str, Any]] | None = None,
    candidate_rows: list[dict[str, Any]] | None = None,
    dependency_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    design_materialized = _decision_design_materialized(
        decision_rows or [],
        evidence_rows or [],
        candidate_rows or [],
        dependency_rows or [],
    )
    rows = []
    for route_role_id, label in VALIDATION_ROLES:
        rows.append(
            {
                "compatibility_id": f"{route_role_id}_platform_selection_decision_compatibility",
                "route_role_id": route_role_id,
                "candidate_role_label": label,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "decision_design_materialized_in_m2604": design_materialized,
                "reset_feasibility_evidence_required_later": True,
                "rollout_feasibility_evidence_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "external_validation_execution_allowed_in_m2604": False,
                "validation_protocol_ready_in_m2604": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(design_materialized and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(compatibility_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for compatibility in compatibility_rows:
        rows.append(
            {
                "actor_action_guard_id": f"{compatibility['route_role_id']}_decision_actor_action_guard",
                "route_role_id": compatibility["route_role_id"],
                "actor_observation_shape": _int_value(compatibility["actor_observation_shape"], default=-1),
                "action_shape": _int_value(compatibility["action_shape"], default=-1),
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
                "protocol_status_actor_visible": False,
                "action_contract_mutation_detected": False,
                "status_pass": bool(
                    _boolish(compatibility["status_pass"])
                    and _int_value(compatibility["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM
                    and _int_value(compatibility["action_shape"], default=-1) == ACTION_DIM
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
    compatibility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    design_materialized = bool(
        _decision_design_materialized(decision_rows, evidence_rows, candidate_rows, dependency_rows)
        and len(compatibility_rows) == len(VALIDATION_ROLES)
        and _all_status_pass(compatibility_rows)
        and len(guard_rows) == len(compatibility_rows)
        and _all_status_pass(guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and design_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2604": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "after_closure_platform_selection_decision_design_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2600_summary: dict[str, Any],
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    compatibility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] != "after_closure_platform_selection_decision_design_materialized"
        and _boolish(row["claim_allowed_in_m2604"])
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
            "m2600_m2601_m2602_criteria_evidence_accepted",
            "lineage",
            _criteria_evidence_accepted(m2600_summary),
            (
                f"m2600_status={m2600_summary.get('status_pass')};"
                f"criteria={m2600_summary.get('platform_selection_criteria_materialized_in_m2600')};"
                f"selected={m2600_summary.get('platform_selected_in_m2600')};"
                f"decision={m2600_summary.get('selection_decision_allowed_in_m2600')};"
                f"protocol_ready={m2600_summary.get('validation_protocol_ready_in_m2600')}"
            ),
            "m2600_status=True;criteria=True;selected=False;decision=False;protocol_ready=False",
            "lineage_invalid",
        ),
        (
            "decision_request_rows_complete",
            "contract",
            len(decision_rows) == 2
            and _all_status_pass(decision_rows)
            and not any(_boolish(row["actual_selection_allowed_in_m2604"]) for row in decision_rows)
            and not any(_boolish(row["selection_decision_made_in_m2604"]) for row in decision_rows)
            and {row["selected_platform_family_in_m2604"] for row in decision_rows} == {"none"}
            and all(_boolish(row["future_selection_requires_result_audit"]) for row in decision_rows)
            and all(_boolish(row["future_protocol_readiness_required_after_selection"]) for row in decision_rows),
            f"rows={len(decision_rows)}",
            "rows=2;selection/decision=false;selected_family=none;future_audit/readiness=true",
            "contract_violation",
        ),
        (
            "evidence_admission_rows_pass",
            "lineage",
            len(evidence_rows) == len(EVIDENCE_SOURCES)
            and _all_status_pass(evidence_rows)
            and all(_boolish(row["admitted_for_decision_design_in_m2604"]) for row in evidence_rows)
            and not any(_boolish(row["admitted_for_actual_selection_in_m2604"]) for row in evidence_rows)
            and not any(_boolish(row["admitted_for_validation_readiness_in_m2604"]) for row in evidence_rows),
            f"rows={len(evidence_rows)}",
            "rows=8;decision_design=true;actual_selection/readiness=false",
            "lineage_invalid",
        ),
        (
            "candidate_comparison_rows_pass",
            "contract",
            len(candidate_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(candidate_rows)
            and {row["platform_family"] for row in candidate_rows}
            == {
                "chrono_vehicle_or_equivalent_open_backend",
                "black_box_industry_demonstration_backend",
                "repo_local_current_sim_backend",
            }
            and any(
                row["platform_family"] == "chrono_vehicle_or_equivalent_open_backend"
                and _boolish(row["open_auditable_backend_preferred"])
                and _boolish(row["eligible_for_future_selection_after_audit"])
                for row in candidate_rows
            )
            and any(
                row["platform_family"] == "black_box_industry_demonstration_backend"
                and _boolish(row["black_box_demonstration_only"])
                for row in candidate_rows
            )
            and any(
                row["platform_family"] == "repo_local_current_sim_backend"
                and _boolish(row["repo_local_diagnostic_only"])
                for row in candidate_rows
            )
            and not any(_boolish(row["selected_in_m2604"]) for row in candidate_rows),
            f"rows={len(candidate_rows)}",
            "rows=3;open_future_eligible=true;black_box_demo=true;repo_local_diagnostic=true;selected=false",
            "contract_violation",
        ),
        (
            "dependency_guard_rows_pass",
            "contract",
            len(dependency_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(dependency_rows)
            and not any(_boolish(row["external_install_allowed_in_m2604"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2604"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2604"]) for row in dependency_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2604"]) for row in dependency_rows)
            and all(_boolish(row["license_or_api_review_required_before_install"]) for row in dependency_rows)
            and all(_boolish(row["source_build_or_adapter_probe_required_before_selection"]) for row in dependency_rows)
            and all(_boolish(row["sandbox_plan_required_before_execution"]) for row in dependency_rows),
            f"rows={len(dependency_rows)}",
            "rows=3;install/import/run/mutation=false;future_reviews=true",
            "contract_violation",
        ),
        (
            "validation_role_compatibility_rows_pass",
            "scenario",
            len(compatibility_rows) == len(VALIDATION_ROLES)
            and _all_status_pass(compatibility_rows)
            and {row["route_role_id"] for row in compatibility_rows}
            == {"stable_avoidable_aeb_feasible", "stable_aes_aeb_infeasible"}
            and all(_boolish(row["decision_design_materialized_in_m2604"]) for row in compatibility_rows)
            and all(_boolish(row["reset_feasibility_evidence_required_later"]) for row in compatibility_rows)
            and all(_boolish(row["rollout_feasibility_evidence_required_later"]) for row in compatibility_rows)
            and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in compatibility_rows)
            and not any(_boolish(row["external_validation_execution_allowed_in_m2604"]) for row in compatibility_rows)
            and not any(_boolish(row["validation_protocol_ready_in_m2604"]) for row in compatibility_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in compatibility_rows),
            f"rows={len(compatibility_rows)}",
            "rows=2;design=true;future reset/rollout/holdout=true;execution/readiness/result=false",
            "scenario_sampling_failure",
        ),
        (
            "actor_action_guard_rows_pass",
            "contract",
            len(guard_rows) == len(compatibility_rows)
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
            and not any(_boolish(row["protocol_status_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in guard_rows),
            f"rows={len(guard_rows)}",
            "rows=compatibility_rows;obs=72;action=3;hidden/status/criteria/decision/outcomes=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and len(forbidden_claims_allowed) == 0,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            "rows=19;forbidden_claims=0;decision_design_materialized=true",
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
            "no_platform_selected_or_external_execution",
            "claim_boundary",
            not any(_boolish(row["actual_selection_allowed_in_m2604"]) for row in decision_rows)
            and not any(_boolish(row["selection_decision_made_in_m2604"]) for row in decision_rows)
            and not any(_boolish(row["selected_in_m2604"]) for row in candidate_rows)
            and not any(_boolish(row["external_install_allowed_in_m2604"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2604"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2604"]) for row in dependency_rows),
            "selection/decision/selected/install/import/run/reset/action/step/rollout/validation=false",
            "selection/decision/selected/install/import/run/reset/action/step/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "validation_readiness_and_result_forbidden",
            "claim_boundary",
            not any(_boolish(row["validation_protocol_ready_in_m2604"]) for row in compatibility_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in compatibility_rows)
            and not any(
                _boolish(row["claim_allowed_in_m2604"])
                for row in claim_rows
                if row["claim_family"]
                in {
                    "validation_protocol_ready",
                    "validation_admission_granted",
                    "high_fidelity_validation_readiness",
                    "high_fidelity_validation_result",
                    "driver_performance",
                }
            ),
            "readiness/result/performance=false",
            "readiness/result/performance=false",
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
    m2600_summary: dict[str, Any],
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    compatibility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    decision_path: Path,
    evidence_path: Path,
    candidate_path: Path,
    dependency_path: Path,
    compatibility_path: Path,
    guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2604"])
        for row in claim_rows
        if row["claim_family"] != "after_closure_platform_selection_decision_design_materialized"
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": "engineering_controller_route_a_hf3_after_closure_platform_selection_decision_materialization_preflight_pass",
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_after_closure_platform_selection_decision_request_rows": str(decision_path),
        "hf3_after_closure_platform_selection_evidence_admission_rows": str(evidence_path),
        "hf3_after_closure_platform_selection_candidate_comparison_rows": str(candidate_path),
        "hf3_after_closure_platform_selection_dependency_guard_rows": str(dependency_path),
        "hf3_after_closure_platform_selection_validation_role_compatibility_rows": str(compatibility_path),
        "hf3_after_closure_platform_selection_decision_actor_action_guard_rows": str(guard_path),
        "hf3_after_closure_platform_selection_decision_claim_boundary_checks": str(claim_path),
        "after_closure_platform_selection_decision_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2600_status_pass": bool(m2600_summary.get("status_pass")),
        "m2600_platform_selection_criteria_materialized": bool(
            m2600_summary.get("platform_selection_criteria_materialized_in_m2600")
        ),
        "m2600_platform_selected": bool(m2600_summary.get("platform_selected_in_m2600")),
        "m2600_selection_decision_allowed": bool(m2600_summary.get("selection_decision_allowed_in_m2600")),
        "m2600_validation_protocol_ready": bool(m2600_summary.get("validation_protocol_ready_in_m2600")),
        "m2600_external_validation_execution_allowed": bool(
            m2600_summary.get("external_validation_execution_allowed_in_m2600")
        ),
        "m2600_driver_performance_claim_allowed": bool(
            m2600_summary.get("driver_performance_claim_allowed_in_m2600")
        ),
        "decision_request_row_count": len(decision_rows),
        "evidence_admission_row_count": len(evidence_rows),
        "candidate_comparison_row_count": len(candidate_rows),
        "dependency_guard_row_count": len(dependency_rows),
        "validation_role_compatibility_row_count": len(compatibility_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "platform_selection_decision_design_materialized_in_m2604": bool(
            _all_status_pass(decision_rows)
            and _all_status_pass(evidence_rows)
            and _all_status_pass(candidate_rows)
            and _all_status_pass(dependency_rows)
            and _all_status_pass(compatibility_rows)
            and _all_status_pass(guard_rows)
        ),
        "after_closure_platform_selection_decision_design_materialized_claim_allowed": any(
            row["claim_family"] == "after_closure_platform_selection_decision_design_materialized"
            and _boolish(row["claim_allowed_in_m2604"])
            for row in claim_rows
        ),
        "forbidden_claim_allowed_in_m2604": forbidden_claim_allowed,
        "platform_selected_in_m2604": any(_boolish(row["selected_in_m2604"]) for row in candidate_rows),
        "selection_decision_made_in_m2604": any(
            _boolish(row["selection_decision_made_in_m2604"]) for row in decision_rows
        ),
        "selected_platform_family_in_m2604": "none",
        "external_install_allowed_in_m2604": any(
            _boolish(row["external_install_allowed_in_m2604"]) for row in dependency_rows
        ),
        "external_import_allowed_in_m2604": any(
            _boolish(row["external_import_allowed_in_m2604"]) for row in dependency_rows
        ),
        "runtime_execution_allowed_in_m2604": any(
            _boolish(row["runtime_execution_allowed_in_m2604"]) for row in dependency_rows
        ),
        "dependency_mutation_allowed_in_m2604": any(
            _boolish(row["dependency_mutation_allowed_in_m2604"]) for row in dependency_rows
        ),
        "validation_protocol_ready_in_m2604": any(
            _boolish(row["validation_protocol_ready_in_m2604"]) for row in compatibility_rows
        ),
        "validation_admission_granted_in_m2604": False,
        "external_validation_execution_allowed_in_m2604": any(
            _boolish(row["external_validation_execution_allowed_in_m2604"])
            for row in compatibility_rows
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"]) for row in compatibility_rows
        ),
        "driver_performance_claim_allowed_in_m2604": any(
            row["claim_family"] == "driver_performance" and _boolish(row["claim_allowed_in_m2604"])
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
    content = f"""# M2604 Engineering Controller Route A Baseline HF3 After-Closure Platform Selection Decision Materialization Preflight

- status: completed
- result_class: `{summary["result_class"]}`
- milestone: `{summary["milestone"]}`
- summary: `{summary["summary"]}`
- next: `{summary["next_blocker"]}`

## Materialized Evidence

```text
status_pass: {summary["status_pass"]}
decision_request_rows: {summary["decision_request_row_count"]}
evidence_admission_rows: {summary["evidence_admission_row_count"]}
candidate_comparison_rows: {summary["candidate_comparison_row_count"]}
dependency_guard_rows: {summary["dependency_guard_row_count"]}
validation_role_compatibility_rows: {summary["validation_role_compatibility_row_count"]}
actor_action_guard_rows: {summary["actor_action_guard_row_count"]}
claim_boundary_rows: {summary["claim_boundary_check_count"]}
materialization_gates: {summary["materialization_gate_count"]}
platform_selection_decision_design_materialized_in_m2604: {summary["platform_selection_decision_design_materialized_in_m2604"]}
platform_selected_in_m2604: {summary["platform_selected_in_m2604"]}
selection_decision_made_in_m2604: {summary["selection_decision_made_in_m2604"]}
selected_platform_family_in_m2604: {summary["selected_platform_family_in_m2604"]}
validation_protocol_ready_in_m2604: {summary["validation_protocol_ready_in_m2604"]}
external_validation_execution_allowed_in_m2604: {summary["external_validation_execution_allowed_in_m2604"]}
driver_performance_claim_allowed_in_m2604: {summary["driver_performance_claim_allowed_in_m2604"]}
actor contract: P0 observation {summary["observation_shape"]} / action {summary["action_shape"]}
```

## Artifact Paths

- decision request rows: `{summary["hf3_after_closure_platform_selection_decision_request_rows"]}`
- evidence admission rows: `{summary["hf3_after_closure_platform_selection_evidence_admission_rows"]}`
- candidate comparison rows: `{summary["hf3_after_closure_platform_selection_candidate_comparison_rows"]}`
- dependency guard rows: `{summary["hf3_after_closure_platform_selection_dependency_guard_rows"]}`
- validation-role compatibility rows: `{summary["hf3_after_closure_platform_selection_validation_role_compatibility_rows"]}`
- actor/action guard rows: `{summary["hf3_after_closure_platform_selection_decision_actor_action_guard_rows"]}`
- claim-boundary rows: `{summary["hf3_after_closure_platform_selection_decision_claim_boundary_checks"]}`
- gate matrix: `{summary["after_closure_platform_selection_decision_gate_matrix"]}`

## Supported Claims

Supported:

- after-closure HF3 platform-selection decision-design artifacts are materialized
- accepted M2600/M2601/M2602 criteria evidence is admitted for decision design only
- open/auditable backend preference is represented for a future selection decision only
- black-box backends remain demonstration-only
- repo-local current-sim remains diagnostic-only
- exactly two HF3 low-cost pilot roles are represented
- P0 `72/3` actor/action contract is preserved

## Rejected Claims

Rejected:

- actual platform selection
- selection decision
- selected platform family
- external simulator install/import/runtime execution
- validation protocol readiness
- validation admission
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


def _criteria_evidence_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("platform_selection_criteria_materialized_in_m2600")
        and summary.get("after_closure_platform_selection_criteria_materialized_claim_allowed")
        and summary.get("platform_selection_criteria_row_count") == 3
        and summary.get("platform_auditability_row_count") == 3
        and summary.get("dependency_import_risk_row_count") == 3
        and summary.get("validation_role_compatibility_row_count") == 2
        and summary.get("actor_action_guard_row_count") == 2
        and summary.get("claim_boundary_check_count") == 18
        and summary.get("materialization_gate_count") == 11
        and not summary.get("platform_selected_in_m2600")
        and not summary.get("selection_decision_allowed_in_m2600")
        and not summary.get("validation_protocol_ready_in_m2600")
        and not summary.get("external_validation_execution_allowed_in_m2600")
        and not summary.get("driver_performance_claim_allowed_in_m2600")
    )


def _decision_design_materialized(
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        len(decision_rows) == 2
        and _all_status_pass(decision_rows)
        and len(evidence_rows) == len(EVIDENCE_SOURCES)
        and _all_status_pass(evidence_rows)
        and len(candidate_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(candidate_rows)
        and len(dependency_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(dependency_rows)
        and not any(_boolish(row["actual_selection_allowed_in_m2604"]) for row in decision_rows)
        and not any(_boolish(row["selection_decision_made_in_m2604"]) for row in decision_rows)
        and not any(_boolish(row["selected_in_m2604"]) for row in candidate_rows)
        and not any(_boolish(row["external_install_allowed_in_m2604"]) for row in dependency_rows)
        and not any(_boolish(row["external_import_allowed_in_m2604"]) for row in dependency_rows)
        and not any(_boolish(row["runtime_execution_allowed_in_m2604"]) for row in dependency_rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2604"]) for row in dependency_rows)
    )


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
    parser.add_argument("--m2600-summary-path", type=Path, default=DEFAULT_M2600_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_after_closure_platform_selection_decision(
        args.output_dir,
        m2600_summary_path=args.m2600_summary_path,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(summary["summary"])
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
