"""Route A HF3 after-closure platform-selection criteria materialization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2600-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2601-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-"
    "materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2600-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-"
    "criteria-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria"
)
DEFAULT_M2596_SUMMARY = Path(
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/summary.json"
)

SOURCE_ARTIFACTS = (
    "docs/m2599-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-design.md",
    "docs/m2598-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-result-synthesis.md",
    "docs/m2597-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-result-audit.md",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/summary.json",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_platform_candidate_rows.csv",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_dependency_import_policy_rows.csv",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_validation_protocol_skeleton_rows.csv",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_source_only_evidence_rows.csv",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_actor_action_guard_rows.csv",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_claim_boundary_checks.csv",
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/after_closure_platform_protocol_readiness_gate_matrix.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 after-closure platform-selection criteria materialization preflight only; "
    "criteria artifacts may be materialized; not actual platform selection, selection decision, "
    "validation protocol readiness, validation admission, external validation execution, "
    "high-fidelity validation readiness/result, HF4 discrepancy result, rollout success, ranking, "
    "driver performance, paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

CRITERIA_FIELDNAMES = [
    "criteria_id",
    "platform_family",
    "selection_role",
    "open_auditable_backend_required",
    "source_or_equivalent_trace_required",
    "deterministic_reset_step_api_required",
    "time_step_contract_required",
    "actuator_latency_contract_required",
    "state_extraction_boundary_required",
    "failure_status_taxonomy_required",
    "scenario_role_support_required",
    "black_box_demonstration_only",
    "repo_local_diagnostic_only",
    "selected_for_validation_in_m2600",
    "selection_decision_allowed_in_m2600",
    "status_pass",
    "claim_boundary",
]

AUDITABILITY_FIELDNAMES = [
    "auditability_id",
    "platform_family",
    "source_or_model_auditable",
    "adapter_contract_traceable",
    "reset_step_determinism_auditable",
    "state_extraction_boundary_auditable",
    "failure_status_mapping_auditable",
    "validation_authority_allowed_after_future_selection",
    "demonstration_only",
    "diagnostic_only",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_RISK_FIELDNAMES = [
    "dependency_risk_id",
    "platform_family",
    "external_install_allowed_in_m2600",
    "external_import_allowed_in_m2600",
    "runtime_execution_allowed_in_m2600",
    "dependency_mutation_allowed_in_m2600",
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
    "platform_selection_criteria_materialized_in_m2600",
    "reset_feasibility_evidence_required_later",
    "rollout_feasibility_evidence_required_later",
    "holdout_or_generalization_policy_required_later",
    "external_validation_execution_allowed_in_m2600",
    "validation_protocol_ready_in_m2600",
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
    "protocol_status_actor_visible",
    "action_contract_mutation_detected",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2600",
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
        "preferred future validation backend candidate after criteria materialization and audit",
        True,
        True,
        False,
        False,
    ),
    (
        "black_box_industry_demonstration_backend",
        "optional demonstration backend only, not validation authority",
        False,
        False,
        True,
        False,
    ),
    (
        "repo_local_current_sim_backend",
        "repo-local diagnostic and adapter contract source only, not validation authority",
        False,
        True,
        False,
        True,
    ),
)

VALIDATION_ROLES = (
    (
        "stable_avoidable_aeb_feasible",
        "stable avoidable / AEB-feasible low-cost pilot compatibility",
    ),
    (
        "stable_aes_aeb_infeasible",
        "stable AES / AEB-infeasible low-cost pilot compatibility",
    ),
)

CLAIM_CHECKS = (
    (
        "after_closure_platform_selection_criteria_materialized",
        True,
        "M2600 criteria auditability dependency/import risk validation-role compatibility actor/action "
        "guard claim-boundary and gate rows",
    ),
    ("platform_selected_for_validation", False, "later explicit platform-selection result audit"),
    ("selection_decision_made", False, "later platform-selection decision milestone"),
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


def materialize_route_a_hf3_after_closure_platform_selection_criteria(
    output_dir: Path,
    *,
    m2596_summary_path: Path = DEFAULT_M2596_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2596_summary = read_json(m2596_summary_path)

    criteria_rows = build_platform_selection_criteria_rows(m2596_summary)
    auditability_rows = build_platform_auditability_rows()
    dependency_rows = build_dependency_import_risk_rows()
    compatibility_rows = build_validation_role_compatibility_rows(criteria_rows)
    guard_rows = build_actor_action_guard_rows(compatibility_rows)
    claim_rows = build_claim_boundary_checks(
        criteria_rows,
        auditability_rows,
        dependency_rows,
        compatibility_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2596_summary=m2596_summary,
        criteria_rows=criteria_rows,
        auditability_rows=auditability_rows,
        dependency_rows=dependency_rows,
        compatibility_rows=compatibility_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    criteria_path = output_dir / "hf3_after_closure_platform_selection_criteria_rows.csv"
    auditability_path = output_dir / "hf3_after_closure_platform_auditability_rows.csv"
    dependency_path = output_dir / "hf3_after_closure_dependency_import_risk_rows.csv"
    compatibility_path = output_dir / "hf3_after_closure_validation_role_compatibility_rows.csv"
    guard_path = output_dir / "hf3_after_closure_platform_selection_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_after_closure_platform_selection_claim_boundary_checks.csv"
    gate_path = output_dir / "after_closure_platform_selection_criteria_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(criteria_path, criteria_rows, fieldnames=CRITERIA_FIELDNAMES)
    write_csv_rows(auditability_path, auditability_rows, fieldnames=AUDITABILITY_FIELDNAMES)
    write_csv_rows(dependency_path, dependency_rows, fieldnames=DEPENDENCY_RISK_FIELDNAMES)
    write_csv_rows(compatibility_path, compatibility_rows, fieldnames=VALIDATION_ROLE_FIELDNAMES)
    write_csv_rows(guard_path, guard_rows, fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2596_summary=m2596_summary,
        criteria_rows=criteria_rows,
        auditability_rows=auditability_rows,
        dependency_rows=dependency_rows,
        compatibility_rows=compatibility_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        criteria_path=criteria_path,
        auditability_path=auditability_path,
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


def build_platform_selection_criteria_rows(
    m2596_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    after_closure_ready = _after_closure_readiness_accepted(m2596_summary or {})
    rows = []
    for (
        platform_family,
        role,
        open_required,
        source_trace_required,
        black_box_only,
        repo_local_only,
    ) in PLATFORM_FAMILIES:
        status_pass = bool(after_closure_ready)
        rows.append(
            {
                "criteria_id": f"{platform_family}_after_closure_platform_selection_criteria",
                "platform_family": platform_family,
                "selection_role": role,
                "open_auditable_backend_required": bool(open_required),
                "source_or_equivalent_trace_required": bool(source_trace_required),
                "deterministic_reset_step_api_required": not bool(black_box_only),
                "time_step_contract_required": True,
                "actuator_latency_contract_required": True,
                "state_extraction_boundary_required": True,
                "failure_status_taxonomy_required": True,
                "scenario_role_support_required": True,
                "black_box_demonstration_only": bool(black_box_only),
                "repo_local_diagnostic_only": bool(repo_local_only),
                "selected_for_validation_in_m2600": False,
                "selection_decision_allowed_in_m2600": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_platform_auditability_rows() -> list[dict[str, Any]]:
    rows = []
    for platform_family, _, open_required, source_trace_required, black_box_only, repo_local_only in PLATFORM_FAMILIES:
        rows.append(
            {
                "auditability_id": f"{platform_family}_after_closure_auditability",
                "platform_family": platform_family,
                "source_or_model_auditable": bool(source_trace_required),
                "adapter_contract_traceable": True,
                "reset_step_determinism_auditable": not bool(black_box_only),
                "state_extraction_boundary_auditable": True,
                "failure_status_mapping_auditable": True,
                "validation_authority_allowed_after_future_selection": bool(open_required),
                "demonstration_only": bool(black_box_only),
                "diagnostic_only": bool(repo_local_only),
                "status_pass": bool(
                    (open_required and source_trace_required and not black_box_only and not repo_local_only)
                    or (black_box_only and not open_required)
                    or (repo_local_only and source_trace_required and not open_required)
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_dependency_import_risk_rows() -> list[dict[str, Any]]:
    rows = []
    for platform_family, *_ in PLATFORM_FAMILIES:
        rows.append(
            {
                "dependency_risk_id": f"{platform_family}_after_closure_dependency_import_risk",
                "platform_family": platform_family,
                "external_install_allowed_in_m2600": False,
                "external_import_allowed_in_m2600": False,
                "runtime_execution_allowed_in_m2600": False,
                "dependency_mutation_allowed_in_m2600": False,
                "license_or_api_review_required_before_install": True,
                "source_build_or_adapter_probe_required_before_selection": True,
                "sandbox_plan_required_before_execution": True,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_validation_role_compatibility_rows(
    criteria_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    criteria_materialized = bool(
        criteria_rows
        and len(criteria_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(criteria_rows)
        and not any(_boolish(row["selected_for_validation_in_m2600"]) for row in criteria_rows)
        and not any(_boolish(row["selection_decision_allowed_in_m2600"]) for row in criteria_rows)
    )
    rows = []
    for route_role_id, label in VALIDATION_ROLES:
        rows.append(
            {
                "compatibility_id": f"{route_role_id}_platform_selection_compatibility",
                "route_role_id": route_role_id,
                "candidate_role_label": label,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "platform_selection_criteria_materialized_in_m2600": criteria_materialized,
                "reset_feasibility_evidence_required_later": True,
                "rollout_feasibility_evidence_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "external_validation_execution_allowed_in_m2600": False,
                "validation_protocol_ready_in_m2600": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(criteria_materialized and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(compatibility_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for compatibility in compatibility_rows:
        rows.append(
            {
                "actor_action_guard_id": f"{compatibility['route_role_id']}_platform_selection_actor_action_guard",
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
    criteria_rows: list[dict[str, Any]],
    auditability_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    compatibility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    criteria_materialized = bool(
        len(criteria_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(criteria_rows)
        and len(auditability_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(auditability_rows)
        and len(dependency_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(dependency_rows)
        and len(compatibility_rows) == len(VALIDATION_ROLES)
        and _all_status_pass(compatibility_rows)
        and len(guard_rows) == len(compatibility_rows)
        and _all_status_pass(guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and criteria_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2600": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "after_closure_platform_selection_criteria_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2596_summary: dict[str, Any],
    criteria_rows: list[dict[str, Any]],
    auditability_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    compatibility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] != "after_closure_platform_selection_criteria_materialized"
        and _boolish(row["claim_allowed_in_m2600"])
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
            "m2596_after_closure_readiness_accepted",
            "lineage",
            _after_closure_readiness_accepted(m2596_summary),
            (
                f"m2596_status={m2596_summary.get('status_pass')};"
                f"source_closure={m2596_summary.get('source_only_closure_accepted_in_m2596')};"
                f"selected={m2596_summary.get('platform_selected_in_m2596')};"
                f"protocol_ready={m2596_summary.get('validation_protocol_ready_in_m2596')}"
            ),
            "m2596_status=True;source_closure=True;selected=False;protocol_ready=False",
            "lineage_invalid",
        ),
        (
            "platform_selection_criteria_rows_complete",
            "contract",
            len(criteria_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(criteria_rows)
            and not any(_boolish(row["selected_for_validation_in_m2600"]) for row in criteria_rows)
            and not any(_boolish(row["selection_decision_allowed_in_m2600"]) for row in criteria_rows)
            and any(
                row["platform_family"] == "chrono_vehicle_or_equivalent_open_backend"
                and _boolish(row["open_auditable_backend_required"])
                for row in criteria_rows
            )
            and any(
                row["platform_family"] == "black_box_industry_demonstration_backend"
                and _boolish(row["black_box_demonstration_only"])
                for row in criteria_rows
            )
            and any(
                row["platform_family"] == "repo_local_current_sim_backend"
                and _boolish(row["repo_local_diagnostic_only"])
                for row in criteria_rows
            ),
            f"rows={len(criteria_rows)}",
            "rows=3;open=true;black_box_demo=true;repo_local_diagnostic=true;selected/decision=false",
            "contract_violation",
        ),
        (
            "auditability_rows_pass",
            "contract",
            len(auditability_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(auditability_rows)
            and any(
                row["platform_family"] == "chrono_vehicle_or_equivalent_open_backend"
                and _boolish(row["validation_authority_allowed_after_future_selection"])
                for row in auditability_rows
            )
            and any(
                row["platform_family"] == "black_box_industry_demonstration_backend"
                and _boolish(row["demonstration_only"])
                for row in auditability_rows
            )
            and any(
                row["platform_family"] == "repo_local_current_sim_backend"
                and _boolish(row["diagnostic_only"])
                for row in auditability_rows
            ),
            f"rows={len(auditability_rows)}",
            "rows=3;open_future_authority=true;black_box_demo=true;repo_local_diagnostic=true",
            "contract_violation",
        ),
        (
            "dependency_import_risk_rows_pass",
            "contract",
            len(dependency_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(dependency_rows)
            and not any(_boolish(row["external_install_allowed_in_m2600"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2600"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2600"]) for row in dependency_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2600"]) for row in dependency_rows),
            f"rows={len(dependency_rows)}",
            "rows=3;install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "validation_role_compatibility_rows_pass",
            "scenario",
            len(compatibility_rows) == len(VALIDATION_ROLES)
            and _all_status_pass(compatibility_rows)
            and {row["route_role_id"] for row in compatibility_rows}
            == {"stable_avoidable_aeb_feasible", "stable_aes_aeb_infeasible"}
            and all(_boolish(row["platform_selection_criteria_materialized_in_m2600"]) for row in compatibility_rows)
            and all(_boolish(row["reset_feasibility_evidence_required_later"]) for row in compatibility_rows)
            and all(_boolish(row["rollout_feasibility_evidence_required_later"]) for row in compatibility_rows)
            and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in compatibility_rows)
            and not any(_boolish(row["external_validation_execution_allowed_in_m2600"]) for row in compatibility_rows)
            and not any(_boolish(row["validation_protocol_ready_in_m2600"]) for row in compatibility_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in compatibility_rows),
            f"rows={len(compatibility_rows)}",
            "rows=2;criteria=true;future reset/rollout/holdout=true;execution/readiness/result=false",
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
            and not any(_boolish(row["protocol_status_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in guard_rows),
            f"rows={len(guard_rows)}",
            "rows=compatibility_rows;obs=72;action=3;hidden/status/criteria/outcomes=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and len(forbidden_claims_allowed) == 0,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            "rows=18;forbidden_claims=0;criteria_materialized=true",
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
            not any(_boolish(row["selected_for_validation_in_m2600"]) for row in criteria_rows)
            and not any(_boolish(row["selection_decision_allowed_in_m2600"]) for row in criteria_rows)
            and not any(_boolish(row["external_install_allowed_in_m2600"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2600"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2600"]) for row in dependency_rows),
            "selected/decision/install/import/run/reset/action/step/rollout/validation=false",
            "selected/decision/install/import/run/reset/action/step/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "validation_readiness_and_result_forbidden",
            "claim_boundary",
            not any(_boolish(row["validation_protocol_ready_in_m2600"]) for row in compatibility_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in compatibility_rows)
            and not any(
                _boolish(row["claim_allowed_in_m2600"])
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
    m2596_summary: dict[str, Any],
    criteria_rows: list[dict[str, Any]],
    auditability_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    compatibility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    criteria_path: Path,
    auditability_path: Path,
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
        _boolish(row["claim_allowed_in_m2600"])
        for row in claim_rows
        if row["claim_family"] != "after_closure_platform_selection_criteria_materialized"
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": "engineering_controller_route_a_hf3_after_closure_platform_selection_criteria_materialization_preflight_pass",
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_after_closure_platform_selection_criteria_rows": str(criteria_path),
        "hf3_after_closure_platform_auditability_rows": str(auditability_path),
        "hf3_after_closure_dependency_import_risk_rows": str(dependency_path),
        "hf3_after_closure_validation_role_compatibility_rows": str(compatibility_path),
        "hf3_after_closure_platform_selection_actor_action_guard_rows": str(guard_path),
        "hf3_after_closure_platform_selection_claim_boundary_checks": str(claim_path),
        "after_closure_platform_selection_criteria_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2596_status_pass": bool(m2596_summary.get("status_pass")),
        "m2596_source_only_closure_accepted": bool(
            m2596_summary.get("source_only_closure_accepted_in_m2596")
        ),
        "m2596_platform_selected": bool(m2596_summary.get("platform_selected_in_m2596")),
        "m2596_validation_protocol_ready": bool(
            m2596_summary.get("validation_protocol_ready_in_m2596")
        ),
        "m2596_external_validation_execution_allowed": bool(
            m2596_summary.get("external_validation_execution_allowed_in_m2596")
        ),
        "platform_selection_criteria_row_count": len(criteria_rows),
        "platform_auditability_row_count": len(auditability_rows),
        "dependency_import_risk_row_count": len(dependency_rows),
        "validation_role_compatibility_row_count": len(compatibility_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "platform_selection_criteria_materialized_in_m2600": _all_status_pass(criteria_rows),
        "after_closure_platform_selection_criteria_materialized_claim_allowed": any(
            row["claim_family"] == "after_closure_platform_selection_criteria_materialized"
            and _boolish(row["claim_allowed_in_m2600"])
            for row in claim_rows
        ),
        "forbidden_claim_allowed_in_m2600": forbidden_claim_allowed,
        "platform_selected_in_m2600": any(
            _boolish(row["selected_for_validation_in_m2600"]) for row in criteria_rows
        ),
        "selection_decision_allowed_in_m2600": any(
            _boolish(row["selection_decision_allowed_in_m2600"]) for row in criteria_rows
        ),
        "external_install_allowed_in_m2600": any(
            _boolish(row["external_install_allowed_in_m2600"]) for row in dependency_rows
        ),
        "external_import_allowed_in_m2600": any(
            _boolish(row["external_import_allowed_in_m2600"]) for row in dependency_rows
        ),
        "runtime_execution_allowed_in_m2600": any(
            _boolish(row["runtime_execution_allowed_in_m2600"]) for row in dependency_rows
        ),
        "dependency_mutation_allowed_in_m2600": any(
            _boolish(row["dependency_mutation_allowed_in_m2600"]) for row in dependency_rows
        ),
        "validation_protocol_ready_in_m2600": any(
            _boolish(row["validation_protocol_ready_in_m2600"]) for row in compatibility_rows
        ),
        "validation_admission_granted_in_m2600": False,
        "external_validation_execution_allowed_in_m2600": any(
            _boolish(row["external_validation_execution_allowed_in_m2600"])
            for row in compatibility_rows
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"]) for row in compatibility_rows
        ),
        "driver_performance_claim_allowed_in_m2600": any(
            row["claim_family"] == "driver_performance" and _boolish(row["claim_allowed_in_m2600"])
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
    content = f"""# M2600 Engineering Controller Route A Baseline HF3 After-Closure Platform Selection Criteria Materialization Preflight

- status: completed
- result_class: `{summary["result_class"]}`
- milestone: `{summary["milestone"]}`
- summary: `{summary["summary"]}`
- next: `{summary["next_blocker"]}`

## Materialized Evidence

```text
status_pass: {summary["status_pass"]}
platform_selection_criteria_rows: {summary["platform_selection_criteria_row_count"]}
platform_auditability_rows: {summary["platform_auditability_row_count"]}
dependency_import_risk_rows: {summary["dependency_import_risk_row_count"]}
validation_role_compatibility_rows: {summary["validation_role_compatibility_row_count"]}
actor_action_guard_rows: {summary["actor_action_guard_row_count"]}
claim_boundary_rows: {summary["claim_boundary_check_count"]}
materialization_gates: {summary["materialization_gate_count"]}
platform_selection_criteria_materialized_in_m2600: {summary["platform_selection_criteria_materialized_in_m2600"]}
platform_selected_in_m2600: {summary["platform_selected_in_m2600"]}
selection_decision_allowed_in_m2600: {summary["selection_decision_allowed_in_m2600"]}
validation_protocol_ready_in_m2600: {summary["validation_protocol_ready_in_m2600"]}
external_validation_execution_allowed_in_m2600: {summary["external_validation_execution_allowed_in_m2600"]}
driver_performance_claim_allowed_in_m2600: {summary["driver_performance_claim_allowed_in_m2600"]}
actor contract: P0 observation {summary["observation_shape"]} / action {summary["action_shape"]}
```

## Artifact Paths

- criteria rows: `{summary["hf3_after_closure_platform_selection_criteria_rows"]}`
- auditability rows: `{summary["hf3_after_closure_platform_auditability_rows"]}`
- dependency/import risk rows: `{summary["hf3_after_closure_dependency_import_risk_rows"]}`
- validation-role compatibility rows: `{summary["hf3_after_closure_validation_role_compatibility_rows"]}`
- actor/action guard rows: `{summary["hf3_after_closure_platform_selection_actor_action_guard_rows"]}`
- claim-boundary rows: `{summary["hf3_after_closure_platform_selection_claim_boundary_checks"]}`
- gate matrix: `{summary["after_closure_platform_selection_criteria_gate_matrix"]}`

## Supported Claims

Supported:

- after-closure HF3 platform-selection criteria artifacts are materialized
- exactly three platform families are represented
- the preferred future validation backend direction remains open/auditable
- black-box backends remain demonstration-only
- repo-local current-sim remains diagnostic-only
- exactly two HF3 low-cost pilot roles are represented
- P0 `72/3` actor/action contract is preserved

## Rejected Claims

Rejected:

- actual platform selection
- selection decision
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


def _after_closure_readiness_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("source_only_closure_accepted_in_m2596")
        and not summary.get("source_only_closure_missing_after_m2596")
        and not summary.get("platform_selected_in_m2596")
        and not summary.get("validation_protocol_ready_in_m2596")
        and not summary.get("external_validation_execution_allowed_in_m2596")
        and not summary.get("driver_performance_claim_allowed_in_m2596")
    )


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _boolish(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Route A HF3 after-closure platform-selection criteria artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2596-summary", type=Path, default=DEFAULT_M2596_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_after_closure_platform_selection_criteria(
        args.output_dir,
        m2596_summary_path=args.m2596_summary,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(summary["result_class"])
    print(f"status_pass={summary['status_pass']}")
    print(f"summary={summary['summary']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
