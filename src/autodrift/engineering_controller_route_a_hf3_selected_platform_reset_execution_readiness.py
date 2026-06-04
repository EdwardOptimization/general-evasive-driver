"""Route A HF3 selected-platform reset-execution readiness materialization.

This module only materializes static reset-execution readiness artifacts. It
does not install, import, build, probe, reset, step, roll out, replay,
validate, train, rank, or promote any backend.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-"
    "readiness-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2624-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-"
    "readiness-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-"
    "readiness-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness"
)
DEFAULT_M2619_SUMMARY = Path(
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/"
    "summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"
DEPLOYED_ACTION_MAPPING = "[steer, throttle, brake]"

SOURCE_ARTIFACTS = (
    "docs/m2622-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-design.md",
    "docs/m2621-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-result-synthesis.md",
    "docs/m2620-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-result-audit.md",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/summary.json",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_request_schema_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_initial_state_admission_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_actor_view_parity_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_seed_lineage_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_outcome_taxonomy_guard_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_execution_precondition_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_feasibility_actor_action_guard_rows.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_feasibility_claim_boundary_checks.csv",
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/selected_platform_reset_feasibility_readiness_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
    "docs/self-id-go-no-go-paper-route-plan.md",
    "docs/paper-route-finite-window-vs-gru-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform reset-execution readiness design materialization only; "
    "static source-build/adapter-probe evidence admission backend availability fixture reset "
    "invocation dry-run reset request binding actor-view after-reset extraction reset outcome "
    "audit schema actor/action guard and gate panels may be materialized for the selected "
    "open/auditable platform family; not dependency execution readiness, source build execution, "
    "adapter probe execution, reset execution, reset success, rollout feasibility, replay execution, "
    "validation protocol readiness, validation admission, external validation execution, "
    "high-fidelity validation readiness/result, ranking, driver performance, paper, FW-vs-GRU, "
    "current-sim verdict, high-fidelity validation, or self-ID"
)

SOURCE_BUILD_ADAPTER_PROBE_EVIDENCE_ADMISSION_FIELDNAMES = [
    "evidence_admission_id",
    "evidence_family",
    "selected_platform_family",
    "required_before_reset_execution",
    "materialized_in_m2623",
    "satisfied_by_m2623",
    "execution_allowed_in_m2623",
    "source_build_execution_required_later",
    "adapter_probe_execution_required_later",
    "dependency_mutation_allowed_in_m2623",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

BACKEND_AVAILABILITY_FIXTURE_FIELDNAMES = [
    "backend_fixture_id",
    "route_role_id",
    "selected_platform_family",
    "backend_family",
    "fixture_family",
    "backend_availability_required_before_reset",
    "fixture_schema_materialized_in_m2623",
    "backend_started_in_m2623",
    "backend_reset_called_in_m2623",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

RESET_INVOCATION_DRY_RUN_CONTRACT_FIELDNAMES = [
    "dry_run_contract_id",
    "route_role_id",
    "selected_platform_family",
    "reset_api_family",
    "initial_state_binding_required",
    "deterministic_seed_required",
    "actor_view_required_after_reset",
    "source_build_required_before_execution",
    "adapter_probe_required_before_execution",
    "backend_availability_required_before_execution",
    "reset_invocation_contract_materialized_in_m2623",
    "reset_executed_in_m2623",
    "status_pass",
    "claim_boundary",
]

RESET_REQUEST_BINDING_FIELDNAMES = [
    "reset_request_binding_id",
    "route_role_id",
    "selected_platform_family",
    "reset_request_schema_id",
    "initial_state_admission_id",
    "seed_lineage_id",
    "binding_materialized_in_m2623",
    "reset_executed_in_m2623",
    "replay_executed_in_m2623",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

ACTOR_VIEW_AFTER_RESET_EXTRACTION_FIELDNAMES = [
    "after_reset_actor_view_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "action_shape",
    "deployed_action_mapping",
    "ego_kinematics_included",
    "actuator_state_included",
    "previous_command_included",
    "road_geometry_included",
    "obstacle_geometry_included",
    "after_reset_extractor_contract_materialized_in_m2623",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "selected_platform_actor_visible",
    "protocol_status_actor_visible",
    "status_pass",
    "claim_boundary",
]

RESET_OUTCOME_AUDIT_SCHEMA_FIELDNAMES = [
    "outcome_audit_schema_id",
    "outcome_field",
    "field_family",
    "required_for_future_reset_execution_audit",
    "allowed_to_support_reset_success_after_execution",
    "allowed_to_support_rollout_feasibility_after_execution",
    "allowed_to_support_validation_after_execution",
    "actor_visible_allowed",
    "materialized_in_m2623",
    "status_pass",
    "claim_boundary",
]

ACTOR_ACTION_GUARD_FIELDNAMES = [
    "actor_action_guard_id",
    "route_role_id",
    "actor_observation_shape",
    "action_shape",
    "deployed_action_mapping",
    "actor_input_mutation_detected",
    "action_contract_mutation_detected",
    "hidden_oracle_actor_input_detected",
    "metadata_actor_visible",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2623",
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

VALIDATION_ROLES = (
    "stable_avoidable_aeb_feasible",
    "stable_aes_aeb_infeasible",
)

EVIDENCE_ADMISSIONS = (
    (
        "source_build_log_admission",
        "source_build_evidence",
        False,
        True,
        False,
    ),
    (
        "adapter_probe_trace_admission",
        "adapter_probe_evidence",
        False,
        False,
        True,
    ),
    (
        "dependency_mutation_guard_admission",
        "dependency_mutation_guard",
        True,
        False,
        False,
    ),
    (
        "source_equivalence_trace_admission",
        "source_equivalence_trace",
        True,
        True,
        True,
    ),
)

OUTCOME_FIELDS = (
    ("backend_available", "backend_status"),
    ("source_build_artifact", "source_build_evidence"),
    ("adapter_probe_trace", "adapter_probe_evidence"),
    ("reset_request_valid", "request_status"),
    ("reset_attempted", "execution_status"),
    ("reset_status", "execution_status"),
    ("actor_view_available", "actor_view_status"),
    ("diagnostics_available", "audit_metadata"),
    ("failure_reason", "audit_metadata"),
    ("execution_timestamp", "audit_metadata"),
)

ALLOWED_CLAIMS = frozenset({"selected_platform_reset_execution_readiness_design_materialized"})

CLAIM_CHECKS = (
    (
        "selected_platform_reset_execution_readiness_design_materialized",
        True,
        "M2623 source-build/adapter-probe admission backend fixture dry-run reset binding "
        "after-reset actor-view outcome schema actor/action guard claim-boundary and gate rows",
    ),
    ("dependency_ready_for_execution", False, "future dependency execution readiness audit"),
    ("source_build_executed", False, "future explicit source build execution"),
    ("adapter_probe_executed", False, "future explicit adapter probe execution"),
    ("reset_executed", False, "future explicit reset execution"),
    ("reset_success", False, "future audited reset-success artifact"),
    ("policy_action_executed", False, "future explicit policy-action execution"),
    ("environment_step_executed", False, "future explicit environment-step execution"),
    ("rollout_executed", False, "future explicit rollout execution"),
    ("rollout_feasibility", False, "future rollout-feasibility audit"),
    ("replay_executed", False, "future explicit replay execution"),
    ("validation_protocol_readiness", False, "future validation protocol-readiness audit"),
    ("validation_admission", False, "future validation-admission audit"),
    ("external_validation_execution", False, "future explicit external-validation execution"),
    ("validation_readiness", False, "future validation readiness audit"),
    ("validation_result", False, "future validation-result audit"),
    ("high_fidelity_validation_readiness", False, "future high-fidelity readiness audit"),
    ("high_fidelity_validation_result", False, "future high-fidelity validation result audit"),
    ("driver_performance", False, "measured validation with claim-boundary audit"),
    ("controller_family_ranking", False, "controller-family comparison milestone"),
    ("winner_selection", False, "controller-family comparison milestone"),
    ("success_rate", False, "separate verdict milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("current_sim_verdict", False, "separate current-sim verdict synthesis"),
    ("paper_level_evidence", False, "separate paper-route evidence matrix"),
    ("finite_window_vs_gru", False, "separate finite-window-vs-GRU matrix"),
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
    "source_build_run": False,
    "adapter_probe_run": False,
    "reset_execution_run": False,
    "policy_action_run": False,
    "environment_step_run": False,
    "rollout_execution_run": False,
    "replay_run": False,
    "validation_execution_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "dependency_execution_readiness_claim_made": False,
    "source_build_execution_claim_made": False,
    "adapter_probe_execution_claim_made": False,
    "reset_execution_claim_made": False,
    "reset_success_claim_made": False,
    "rollout_feasibility_claim_made": False,
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


def materialize_route_a_hf3_selected_platform_reset_execution_readiness(
    output_dir: Path,
    *,
    m2619_summary_path: Path = DEFAULT_M2619_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2619_summary = read_json(m2619_summary_path)

    evidence_rows = build_source_build_adapter_probe_evidence_admission_rows(m2619_summary)
    backend_rows = build_backend_availability_fixture_rows(evidence_rows)
    dry_run_rows = build_reset_invocation_dry_run_contract_rows(backend_rows)
    binding_rows = build_reset_request_binding_rows(dry_run_rows)
    actor_view_rows = build_actor_view_after_reset_extraction_rows(binding_rows)
    outcome_rows = build_reset_outcome_audit_schema_rows()
    actor_action_guard_rows = build_actor_action_guard_rows(actor_view_rows)
    claim_rows = build_claim_boundary_checks(
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2619_summary=m2619_summary,
        evidence_rows=evidence_rows,
        backend_rows=backend_rows,
        dry_run_rows=dry_run_rows,
        binding_rows=binding_rows,
        actor_view_rows=actor_view_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )

    evidence_path = (
        output_dir / "hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows.csv"
    )
    backend_path = output_dir / "hf3_selected_platform_backend_availability_fixture_rows.csv"
    dry_run_path = output_dir / "hf3_selected_platform_reset_invocation_dry_run_contract_rows.csv"
    binding_path = output_dir / "hf3_selected_platform_reset_request_binding_rows.csv"
    actor_view_path = (
        output_dir / "hf3_selected_platform_actor_view_after_reset_extraction_rows.csv"
    )
    outcome_path = output_dir / "hf3_selected_platform_reset_outcome_audit_schema_rows.csv"
    actor_action_guard_path = (
        output_dir / "hf3_selected_platform_reset_execution_actor_action_guard_rows.csv"
    )
    claim_path = (
        output_dir / "hf3_selected_platform_reset_execution_readiness_claim_boundary_checks.csv"
    )
    gate_path = output_dir / "selected_platform_reset_execution_readiness_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(
        evidence_path,
        evidence_rows,
        fieldnames=SOURCE_BUILD_ADAPTER_PROBE_EVIDENCE_ADMISSION_FIELDNAMES,
    )
    write_csv_rows(
        backend_path,
        backend_rows,
        fieldnames=BACKEND_AVAILABILITY_FIXTURE_FIELDNAMES,
    )
    write_csv_rows(
        dry_run_path,
        dry_run_rows,
        fieldnames=RESET_INVOCATION_DRY_RUN_CONTRACT_FIELDNAMES,
    )
    write_csv_rows(binding_path, binding_rows, fieldnames=RESET_REQUEST_BINDING_FIELDNAMES)
    write_csv_rows(
        actor_view_path,
        actor_view_rows,
        fieldnames=ACTOR_VIEW_AFTER_RESET_EXTRACTION_FIELDNAMES,
    )
    write_csv_rows(outcome_path, outcome_rows, fieldnames=RESET_OUTCOME_AUDIT_SCHEMA_FIELDNAMES)
    write_csv_rows(
        actor_action_guard_path,
        actor_action_guard_rows,
        fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES,
    )
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2619_summary=m2619_summary,
        evidence_rows=evidence_rows,
        backend_rows=backend_rows,
        dry_run_rows=dry_run_rows,
        binding_rows=binding_rows,
        actor_view_rows=actor_view_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        evidence_path=evidence_path,
        backend_path=backend_path,
        dry_run_path=dry_run_path,
        binding_path=binding_path,
        actor_view_path=actor_view_path,
        outcome_path=outcome_path,
        actor_action_guard_path=actor_action_guard_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_source_build_adapter_probe_evidence_admission_rows(
    m2619_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2619_reset_feasibility_evidence_accepted(m2619_summary or {})
    return [
        {
            "evidence_admission_id": evidence_id,
            "evidence_family": evidence_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "required_before_reset_execution": True,
            "materialized_in_m2623": True,
            "satisfied_by_m2623": satisfied_by_m2623,
            "execution_allowed_in_m2623": False,
            "source_build_execution_required_later": source_build_required_later,
            "adapter_probe_execution_required_later": adapter_probe_required_later,
            "dependency_mutation_allowed_in_m2623": False,
            "actor_visible_allowed": False,
            "status_pass": bool(parent_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for (
            evidence_id,
            evidence_family,
            satisfied_by_m2623,
            source_build_required_later,
            adapter_probe_required_later,
        ) in EVIDENCE_ADMISSIONS
    ]


def build_backend_availability_fixture_rows(
    evidence_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    evidence_materialized = _source_build_adapter_probe_evidence_admission_materialized(
        evidence_rows or []
    )
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "backend_fixture_id": f"{route_role_id}_backend_availability_fixture",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "backend_family": SELECTED_PLATFORM_FAMILY,
                "fixture_family": "future_backend_availability_pre_reset_fixture",
                "backend_availability_required_before_reset": True,
                "fixture_schema_materialized_in_m2623": True,
                "backend_started_in_m2623": False,
                "backend_reset_called_in_m2623": False,
                "actor_visible_allowed": False,
                "status_pass": bool(evidence_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_invocation_dry_run_contract_rows(
    backend_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    backend_materialized = _backend_availability_fixture_materialized(backend_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "dry_run_contract_id": f"{route_role_id}_reset_invocation_dry_run_contract",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "reset_api_family": "selected_platform_backend_reset_request_to_actor_view",
                "initial_state_binding_required": True,
                "deterministic_seed_required": True,
                "actor_view_required_after_reset": True,
                "source_build_required_before_execution": True,
                "adapter_probe_required_before_execution": True,
                "backend_availability_required_before_execution": True,
                "reset_invocation_contract_materialized_in_m2623": True,
                "reset_executed_in_m2623": False,
                "status_pass": bool(backend_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_request_binding_rows(
    dry_run_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    dry_run_materialized = _reset_invocation_dry_run_contract_materialized(
        dry_run_rows or []
    )
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "reset_request_binding_id": f"{route_role_id}_reset_request_binding",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "reset_request_schema_id": f"{route_role_id}_reset_request_schema",
                "initial_state_admission_id": f"{route_role_id}_initial_state_admission",
                "seed_lineage_id": f"{route_role_id}_reset_seed_lineage",
                "binding_materialized_in_m2623": True,
                "reset_executed_in_m2623": False,
                "replay_executed_in_m2623": False,
                "actor_visible_allowed": False,
                "status_pass": bool(dry_run_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_view_after_reset_extraction_rows(
    binding_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    bindings_materialized = _reset_request_binding_materialized(binding_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "after_reset_actor_view_id": f"{route_role_id}_actor_view_after_reset_extraction",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
                "ego_kinematics_included": True,
                "actuator_state_included": True,
                "previous_command_included": True,
                "road_geometry_included": True,
                "obstacle_geometry_included": True,
                "after_reset_extractor_contract_materialized_in_m2623": True,
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "validation_outcome_actor_visible": False,
                "selected_platform_actor_visible": False,
                "protocol_status_actor_visible": False,
                "status_pass": bool(
                    bindings_materialized and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_outcome_audit_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "outcome_audit_schema_id": f"{outcome_field}_reset_outcome_audit_schema",
            "outcome_field": outcome_field,
            "field_family": field_family,
            "required_for_future_reset_execution_audit": True,
            "allowed_to_support_reset_success_after_execution": True,
            "allowed_to_support_rollout_feasibility_after_execution": True,
            "allowed_to_support_validation_after_execution": True,
            "actor_visible_allowed": False,
            "materialized_in_m2623": True,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for outcome_field, field_family in OUTCOME_FIELDS
    ]


def build_actor_action_guard_rows(
    actor_view_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for actor_view in actor_view_rows:
        rows.append(
            {
                "actor_action_guard_id": (
                    f"{actor_view['route_role_id']}_reset_execution_actor_action_guard"
                ),
                "route_role_id": actor_view["route_role_id"],
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
                "actor_input_mutation_detected": False,
                "action_contract_mutation_detected": False,
                "hidden_oracle_actor_input_detected": False,
                "metadata_actor_visible": False,
                "status_pass": bool(
                    _boolish(actor_view["status_pass"])
                    and P0_OBSERVATION_DIM == 72
                    and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    evidence_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    dry_run_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = _reset_execution_readiness_materialized(
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2623": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2619_summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    dry_run_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2623"])
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
            "m2619_m2620_m2621_reset_feasibility_readiness_evidence_accepted",
            "lineage",
            _m2619_reset_feasibility_evidence_accepted(m2619_summary),
            (
                f"m2619_status={m2619_summary.get('status_pass')};"
                f"selected={m2619_summary.get('selected_platform_family_in_m2619')};"
                f"reset_executed={m2619_summary.get('reset_executed_in_m2619')};"
                f"validation_ready={m2619_summary.get('validation_protocol_ready_in_m2619')}"
            ),
            f"m2619_status=True;selected={SELECTED_PLATFORM_FAMILY};"
            "reset_executed=False;validation_ready=False",
            "lineage_invalid",
        ),
        (
            "source_build_adapter_probe_evidence_admission_rows_pass",
            "contract",
            _source_build_adapter_probe_evidence_admission_materialized(evidence_rows),
            f"rows={len(evidence_rows)};selected={_selected_platform_family(evidence_rows)}",
            f"rows=4;selected={SELECTED_PLATFORM_FAMILY};execution=false;actor_visible=false",
            "contract_violation",
        ),
        (
            "backend_availability_fixture_rows_pass",
            "contract",
            _backend_availability_fixture_materialized(backend_rows),
            f"rows={len(backend_rows)}",
            "rows=2;fixture materialized;backend start/reset=false",
            "contract_violation",
        ),
        (
            "reset_invocation_dry_run_contract_rows_pass",
            "contract",
            _reset_invocation_dry_run_contract_materialized(dry_run_rows),
            f"rows={len(dry_run_rows)}",
            "rows=2;source/probe/backend prerequisites true;reset=false",
            "contract_violation",
        ),
        (
            "reset_request_binding_rows_pass",
            "lineage",
            _reset_request_binding_materialized(binding_rows),
            f"rows={len(binding_rows)}",
            "rows=2;M2619 schema/initial-state/seed references;reset/replay=false",
            "lineage_invalid",
        ),
        (
            "actor_view_after_reset_extraction_rows_pass",
            "contract",
            _actor_view_after_reset_extraction_materialized(actor_view_rows),
            f"rows={len(actor_view_rows)}",
            "rows=2;obs=72;action=3;deployable actor fields=true;metadata=false",
            "contract_violation",
        ),
        (
            "reset_outcome_audit_schema_rows_pass",
            "claim_boundary",
            _reset_outcome_audit_schema_materialized(outcome_rows),
            f"rows={len(outcome_rows)}",
            "rows=10;schema only;actor-visible=false",
            "objective_overfit",
        ),
        (
            "actor_action_guard_rows_pass",
            "contract",
            _actor_action_guard_preserved(actor_action_guard_rows),
            f"rows={len(actor_action_guard_rows)}",
            "rows=2;obs=72;action=3;mapping preserved;metadata=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and len(forbidden_claims_allowed) == 0,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;materialization_claim_only=true",
            "objective_overfit",
        ),
        (
            "no_build_probe_reset_step_action_rollout_replay_or_validation_execution",
            "claim_boundary",
            not _any_forbidden_execution(
                evidence_rows,
                backend_rows,
                dry_run_rows,
                binding_rows,
            ),
            "build/probe/reset/step/action/rollout/replay/validation=false",
            "build/probe/reset/step/action/rollout/replay/validation=false",
            "objective_overfit",
        ),
        (
            "reset_success_rollout_validation_and_performance_forbidden",
            "claim_boundary",
            not _any_reset_validation_or_performance_claim(claim_rows),
            "reset success/rollout/validation/readiness/result/performance=false",
            "reset success/rollout/validation/readiness/result/performance=false",
            "objective_overfit",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            _actor_action_guard_preserved(actor_action_guard_rows)
            and _actor_view_after_reset_extraction_materialized(actor_view_rows),
            "P0 72/3 preserved;metadata actor-visible=false",
            "P0 72/3 preserved;metadata actor-visible=false",
            "contract_violation",
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
    m2619_summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    dry_run_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    evidence_path: Path,
    backend_path: Path,
    dry_run_path: Path,
    binding_path: Path,
    actor_view_path: Path,
    outcome_path: Path,
    actor_action_guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2623"])
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS
    )
    materialized = _reset_execution_readiness_materialized(
        evidence_rows,
        backend_rows,
        dry_run_rows,
        binding_rows,
        actor_view_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_hf3_selected_platform_reset_execution_"
            "readiness_materialization_preflight_pass"
        ),
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows": str(
            evidence_path
        ),
        "hf3_selected_platform_backend_availability_fixture_rows": str(backend_path),
        "hf3_selected_platform_reset_invocation_dry_run_contract_rows": str(dry_run_path),
        "hf3_selected_platform_reset_request_binding_rows": str(binding_path),
        "hf3_selected_platform_actor_view_after_reset_extraction_rows": str(
            actor_view_path
        ),
        "hf3_selected_platform_reset_outcome_audit_schema_rows": str(outcome_path),
        "hf3_selected_platform_reset_execution_actor_action_guard_rows": str(
            actor_action_guard_path
        ),
        "hf3_selected_platform_reset_execution_readiness_claim_boundary_checks": str(
            claim_path
        ),
        "selected_platform_reset_execution_readiness_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2619_status_pass": bool(m2619_summary.get("status_pass")),
        "m2619_materialization_gates_all_pass": bool(
            m2619_summary.get("materialization_gates_all_pass")
        ),
        "m2619_selected_platform_family": m2619_summary.get("selected_platform_family_in_m2619"),
        "m2619_reset_feasibility_readiness_design_materialized": bool(
            m2619_summary.get(
                "selected_platform_reset_feasibility_readiness_design_materialized_in_m2619"
            )
        ),
        "m2619_reset_request_schema_materialized": bool(
            m2619_summary.get("reset_request_schema_materialized_in_m2619")
        ),
        "m2619_actor_view_parity_materialized": bool(
            m2619_summary.get("actor_view_parity_materialized_in_m2619")
        ),
        "m2619_reset_executed": bool(m2619_summary.get("reset_executed_in_m2619")),
        "m2619_validation_protocol_ready": bool(
            m2619_summary.get("validation_protocol_ready_in_m2619")
        ),
        "m2619_validation_admission_granted": bool(
            m2619_summary.get("validation_admission_granted_in_m2619")
        ),
        "m2619_validation_result_claim_allowed": bool(
            m2619_summary.get("validation_result_claim_allowed")
        ),
        "m2619_reset_success_claim_allowed": bool(
            m2619_summary.get("reset_success_claim_allowed_in_m2619")
        ),
        "m2619_rollout_feasibility_claim_allowed": bool(
            m2619_summary.get("rollout_feasibility_claim_allowed_in_m2619")
        ),
        "m2619_driver_performance_claim_allowed": bool(
            m2619_summary.get("driver_performance_claim_allowed_in_m2619")
        ),
        "source_build_adapter_probe_evidence_admission_row_count": len(evidence_rows),
        "backend_availability_fixture_row_count": len(backend_rows),
        "reset_invocation_dry_run_contract_row_count": len(dry_run_rows),
        "reset_request_binding_row_count": len(binding_rows),
        "actor_view_after_reset_extraction_row_count": len(actor_view_rows),
        "reset_outcome_audit_schema_row_count": len(outcome_rows),
        "actor_action_guard_row_count": len(actor_action_guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "source_build_adapter_probe_evidence_admission_rows_all_pass": _all_status_pass(
            evidence_rows
        ),
        "backend_availability_fixture_rows_all_pass": _all_status_pass(backend_rows),
        "reset_invocation_dry_run_contract_rows_all_pass": _all_status_pass(dry_run_rows),
        "reset_request_binding_rows_all_pass": _all_status_pass(binding_rows),
        "actor_view_after_reset_extraction_rows_all_pass": _all_status_pass(actor_view_rows),
        "reset_outcome_audit_schema_rows_all_pass": _all_status_pass(outcome_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(actor_action_guard_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "selected_platform_reset_execution_readiness_design_materialized_in_m2623": (
            materialized
        ),
        "selected_platform_family_in_m2623": SELECTED_PLATFORM_FAMILY,
        "selected_platform_family_is_open_auditable": True,
        "source_build_adapter_probe_evidence_admission_materialized_in_m2623": (
            _source_build_adapter_probe_evidence_admission_materialized(evidence_rows)
        ),
        "backend_availability_fixture_materialized_in_m2623": (
            _backend_availability_fixture_materialized(backend_rows)
        ),
        "reset_invocation_dry_run_contract_materialized_in_m2623": (
            _reset_invocation_dry_run_contract_materialized(dry_run_rows)
        ),
        "reset_request_binding_materialized_in_m2623": _reset_request_binding_materialized(
            binding_rows
        ),
        "actor_view_after_reset_extraction_materialized_in_m2623": (
            _actor_view_after_reset_extraction_materialized(actor_view_rows)
        ),
        "reset_outcome_audit_schema_materialized_in_m2623": (
            _reset_outcome_audit_schema_materialized(outcome_rows)
        ),
        "selected_platform_reset_execution_readiness_design_materialized_claim_allowed": (
            _claim_allowed(
                claim_rows,
                "selected_platform_reset_execution_readiness_design_materialized",
            )
        ),
        "forbidden_claim_allowed_in_m2623": forbidden_claim_allowed,
        "external_install_allowed_in_m2623": False,
        "external_import_allowed_in_m2623": False,
        "runtime_execution_allowed_in_m2623": False,
        "dependency_mutation_allowed_in_m2623": False,
        "source_build_executed_in_m2623": any(
            _boolish(row["execution_allowed_in_m2623"])
            and row["evidence_family"] == "source_build_evidence"
            for row in evidence_rows
        ),
        "adapter_probe_executed_in_m2623": any(
            _boolish(row["execution_allowed_in_m2623"])
            and row["evidence_family"] == "adapter_probe_evidence"
            for row in evidence_rows
        ),
        "reset_executed_in_m2623": any(
            _boolish(row["reset_executed_in_m2623"]) for row in dry_run_rows + binding_rows
        ),
        "environment_step_executed_in_m2623": False,
        "policy_action_executed_in_m2623": False,
        "rollout_executed_in_m2623": False,
        "replay_executed_in_m2623": any(
            _boolish(row["replay_executed_in_m2623"]) for row in binding_rows
        ),
        "external_validation_execution_allowed_in_m2623": False,
        "validation_protocol_ready_in_m2623": _claim_allowed(
            claim_rows,
            "validation_protocol_readiness",
        ),
        "validation_admission_granted_in_m2623": _claim_allowed(
            claim_rows,
            "validation_admission",
        ),
        "validation_result_claim_allowed": _claim_allowed(claim_rows, "validation_result"),
        "reset_success_claim_allowed_in_m2623": _claim_allowed(claim_rows, "reset_success"),
        "rollout_feasibility_claim_allowed_in_m2623": _claim_allowed(
            claim_rows,
            "rollout_feasibility",
        ),
        "driver_performance_claim_allowed_in_m2623": _claim_allowed(
            claim_rows,
            "driver_performance",
        ),
        "source_build_required_before_reset_execution": True,
        "adapter_probe_required_before_reset_execution": True,
        "backend_availability_required_before_reset_execution": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"])
            for row in actor_view_rows + actor_action_guard_rows
        ),
        "diagnostics_actor_visible": any(
            _boolish(row["diagnostics_actor_visible"]) for row in actor_view_rows
        ),
        "taxonomy_label_actor_visible": any(
            _boolish(row["taxonomy_label_actor_visible"]) for row in actor_view_rows
        ),
        "backend_status_actor_visible": any(
            _boolish(row["backend_status_actor_visible"]) for row in actor_view_rows
        ),
        "reset_outcome_actor_visible": any(
            _boolish(row["reset_outcome_actor_visible"]) for row in actor_view_rows
        ),
        "validation_outcome_actor_visible": any(
            _boolish(row["validation_outcome_actor_visible"]) for row in actor_view_rows
        ),
        "selected_platform_actor_visible": any(
            _boolish(row["selected_platform_actor_visible"]) for row in actor_view_rows
        ),
        "protocol_status_actor_visible": any(
            _boolish(row["protocol_status_actor_visible"]) for row in actor_view_rows
        ),
        "metadata_actor_visible": any(
            _boolish(row["metadata_actor_visible"]) for row in actor_action_guard_rows
        ),
        "actor_input_mutation_detected": any(
            _boolish(row["actor_input_mutation_detected"]) for row in actor_action_guard_rows
        ),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"]) for row in actor_action_guard_rows
        ),
        "repo_local_boundary_only": True,
        "repo_local_static_selected_platform_reset_execution_readiness_materialization": True,
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2623 Engineering Controller Route A Baseline HF3 Selected-Platform "
                "Reset-Execution Readiness Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                f"- milestone: `{summary['milestone']}`",
                f"- summary: `{summary['summary']}`",
                f"- next: `{summary['next_blocker']}`",
                "",
                "## Materialized Evidence",
                "",
                "```text",
                f"status_pass: {summary['status_pass']}",
                "source_build_adapter_probe_evidence_admission_rows: "
                f"{summary['source_build_adapter_probe_evidence_admission_row_count']}",
                "backend_availability_fixture_rows: "
                f"{summary['backend_availability_fixture_row_count']}",
                "reset_invocation_dry_run_contract_rows: "
                f"{summary['reset_invocation_dry_run_contract_row_count']}",
                f"reset_request_binding_rows: {summary['reset_request_binding_row_count']}",
                "actor_view_after_reset_extraction_rows: "
                f"{summary['actor_view_after_reset_extraction_row_count']}",
                f"reset_outcome_audit_schema_rows: {summary['reset_outcome_audit_schema_row_count']}",
                f"actor_action_guard_rows: {summary['actor_action_guard_row_count']}",
                f"claim_boundary_rows: {summary['claim_boundary_check_count']}",
                f"materialization_gates: {summary['materialization_gate_count']}",
                "selected_platform_reset_execution_readiness_design_materialized_in_m2623: "
                f"{summary['selected_platform_reset_execution_readiness_design_materialized_in_m2623']}",
                f"selected_platform_family_in_m2623: {summary['selected_platform_family_in_m2623']}",
                f"external_install_allowed_in_m2623: {summary['external_install_allowed_in_m2623']}",
                f"external_import_allowed_in_m2623: {summary['external_import_allowed_in_m2623']}",
                f"runtime_execution_allowed_in_m2623: {summary['runtime_execution_allowed_in_m2623']}",
                f"dependency_mutation_allowed_in_m2623: {summary['dependency_mutation_allowed_in_m2623']}",
                f"source_build_executed_in_m2623: {summary['source_build_executed_in_m2623']}",
                f"adapter_probe_executed_in_m2623: {summary['adapter_probe_executed_in_m2623']}",
                f"reset_executed_in_m2623: {summary['reset_executed_in_m2623']}",
                f"environment_step_executed_in_m2623: {summary['environment_step_executed_in_m2623']}",
                f"policy_action_executed_in_m2623: {summary['policy_action_executed_in_m2623']}",
                f"rollout_executed_in_m2623: {summary['rollout_executed_in_m2623']}",
                f"replay_executed_in_m2623: {summary['replay_executed_in_m2623']}",
                "external_validation_execution_allowed_in_m2623: "
                f"{summary['external_validation_execution_allowed_in_m2623']}",
                f"validation_protocol_ready_in_m2623: {summary['validation_protocol_ready_in_m2623']}",
                f"validation_admission_granted_in_m2623: {summary['validation_admission_granted_in_m2623']}",
                f"validation_result_claim_allowed: {summary['validation_result_claim_allowed']}",
                f"reset_success_claim_allowed_in_m2623: {summary['reset_success_claim_allowed_in_m2623']}",
                "rollout_feasibility_claim_allowed_in_m2623: "
                f"{summary['rollout_feasibility_claim_allowed_in_m2623']}",
                "driver_performance_claim_allowed_in_m2623: "
                f"{summary['driver_performance_claim_allowed_in_m2623']}",
                f"actor contract: P0 observation {summary['observation_shape']} / action {summary['action_shape']}",
                "```",
                "",
                "## Artifact Paths",
                "",
                "- source-build/adapter-probe evidence admission rows: "
                f"`{summary['hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows']}`",
                "- backend availability fixture rows: "
                f"`{summary['hf3_selected_platform_backend_availability_fixture_rows']}`",
                "- reset invocation dry-run contract rows: "
                f"`{summary['hf3_selected_platform_reset_invocation_dry_run_contract_rows']}`",
                "- reset request binding rows: "
                f"`{summary['hf3_selected_platform_reset_request_binding_rows']}`",
                "- actor-view after-reset extraction rows: "
                f"`{summary['hf3_selected_platform_actor_view_after_reset_extraction_rows']}`",
                "- reset outcome audit schema rows: "
                f"`{summary['hf3_selected_platform_reset_outcome_audit_schema_rows']}`",
                "- actor/action guard rows: "
                f"`{summary['hf3_selected_platform_reset_execution_actor_action_guard_rows']}`",
                "- claim-boundary rows: "
                f"`{summary['hf3_selected_platform_reset_execution_readiness_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['selected_platform_reset_execution_readiness_gate_matrix']}`",
                "",
                "## Supported Claims",
                "",
                "Supported:",
                "",
                "- selected-platform reset-execution readiness design artifacts are materialized",
                "- source-build/adapter-probe evidence admission, backend availability fixture, "
                "reset invocation dry-run, reset request binding, actor-view after-reset extraction, "
                "outcome audit schema, actor/action, claim-boundary, and gate rows are materialized",
                f"- selected platform family remains `{SELECTED_PLATFORM_FAMILY}`",
                "- P0 `72/3` actor/action contract is preserved",
                "",
                "## Rejected Claims",
                "",
                "Rejected:",
                "",
                "- dependency ready for execution",
                "- source build or adapter probe executed",
                "- reset executed or reset success",
                "- policy action, environment step, rollout, replay, or validation executed",
                "- rollout feasibility",
                "- validation protocol readiness",
                "- validation admission",
                "- validation readiness or result",
                "- external validation execution",
                "- high-fidelity validation readiness or result",
                "- controller ranking, success-rate verdict, winner selection, or checkpoint promotion",
                "- driver-performance claim",
                "- current-sim verdict",
                "- paper-level evidence",
                "- finite-window-vs-GRU result",
                "- level3 self-identification evidence",
                "",
                "## Boundary",
                "",
                "M2623 is a static reset-execution readiness materialization preflight. It "
                "does not execute source build, adapter probe, reset, policy action, environment "
                "step, rollout, replay, validation, training, ranking, promotion, or any high-fidelity "
                "simulator. Reset outcome audit schema rows are future execution audit schema and "
                "are not actor-visible.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _m2619_reset_feasibility_evidence_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("selected_platform_family_in_m2619") == SELECTED_PLATFORM_FAMILY
        and summary.get(
            "selected_platform_reset_feasibility_readiness_design_materialized_in_m2619"
        )
        and summary.get("reset_request_schema_materialized_in_m2619")
        and summary.get("actor_view_parity_materialized_in_m2619")
        and not summary.get("source_build_executed_in_m2619")
        and not summary.get("adapter_probe_executed_in_m2619")
        and not summary.get("reset_executed_in_m2619")
        and not summary.get("environment_step_executed_in_m2619")
        and not summary.get("policy_action_executed_in_m2619")
        and not summary.get("rollout_executed_in_m2619")
        and not summary.get("replay_executed_in_m2619")
        and not summary.get("validation_protocol_ready_in_m2619")
        and not summary.get("validation_admission_granted_in_m2619")
        and not summary.get("validation_result_claim_allowed")
        and not summary.get("reset_success_claim_allowed_in_m2619")
        and not summary.get("rollout_feasibility_claim_allowed_in_m2619")
        and not summary.get("driver_performance_claim_allowed_in_m2619")
    )


def _source_build_adapter_probe_evidence_admission_materialized(
    rows: list[dict[str, Any]],
) -> bool:
    return bool(
        len(rows) == len(EVIDENCE_ADMISSIONS)
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["evidence_admission_id"] for row in rows}
        == {item[0] for item in EVIDENCE_ADMISSIONS}
        and all(_boolish(row["required_before_reset_execution"]) for row in rows)
        and all(_boolish(row["materialized_in_m2623"]) for row in rows)
        and not any(_boolish(row["execution_allowed_in_m2623"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2623"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _backend_availability_fixture_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(_boolish(row["backend_availability_required_before_reset"]) for row in rows)
        and all(_boolish(row["fixture_schema_materialized_in_m2623"]) for row in rows)
        and not any(_boolish(row["backend_started_in_m2623"]) for row in rows)
        and not any(_boolish(row["backend_reset_called_in_m2623"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _reset_invocation_dry_run_contract_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(_boolish(row["initial_state_binding_required"]) for row in rows)
        and all(_boolish(row["deterministic_seed_required"]) for row in rows)
        and all(_boolish(row["actor_view_required_after_reset"]) for row in rows)
        and all(_boolish(row["source_build_required_before_execution"]) for row in rows)
        and all(_boolish(row["adapter_probe_required_before_execution"]) for row in rows)
        and all(_boolish(row["backend_availability_required_before_execution"]) for row in rows)
        and all(
            _boolish(row["reset_invocation_contract_materialized_in_m2623"])
            for row in rows
        )
        and not any(_boolish(row["reset_executed_in_m2623"]) for row in rows)
    )


def _reset_request_binding_materialized(rows: list[dict[str, Any]]) -> bool:
    expected_request_ids = {f"{role}_reset_request_schema" for role in VALIDATION_ROLES}
    expected_initial_state_ids = {f"{role}_initial_state_admission" for role in VALIDATION_ROLES}
    expected_seed_ids = {f"{role}_reset_seed_lineage" for role in VALIDATION_ROLES}
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and {row["reset_request_schema_id"] for row in rows} == expected_request_ids
        and {row["initial_state_admission_id"] for row in rows} == expected_initial_state_ids
        and {row["seed_lineage_id"] for row in rows} == expected_seed_ids
        and all(_boolish(row["binding_materialized_in_m2623"]) for row in rows)
        and not any(_boolish(row["reset_executed_in_m2623"]) for row in rows)
        and not any(_boolish(row["replay_executed_in_m2623"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _actor_view_after_reset_extraction_materialized(rows: list[dict[str, Any]]) -> bool:
    metadata_columns = [
        "hidden_oracle_actor_input_detected",
        "diagnostics_actor_visible",
        "taxonomy_label_actor_visible",
        "backend_status_actor_visible",
        "reset_outcome_actor_visible",
        "validation_outcome_actor_visible",
        "selected_platform_actor_visible",
        "protocol_status_actor_visible",
    ]
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(row["actor_observation_shape"] == P0_OBSERVATION_DIM for row in rows)
        and all(row["action_shape"] == ACTION_DIM for row in rows)
        and all(row["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING for row in rows)
        and all(_boolish(row["ego_kinematics_included"]) for row in rows)
        and all(_boolish(row["actuator_state_included"]) for row in rows)
        and all(_boolish(row["previous_command_included"]) for row in rows)
        and all(_boolish(row["road_geometry_included"]) for row in rows)
        and all(_boolish(row["obstacle_geometry_included"]) for row in rows)
        and all(
            _boolish(row["after_reset_extractor_contract_materialized_in_m2623"])
            for row in rows
        )
        and not any(_boolish(row[column]) for row in rows for column in metadata_columns)
    )


def _reset_outcome_audit_schema_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(OUTCOME_FIELDS)
        and _all_status_pass(rows)
        and {row["outcome_field"] for row in rows} == {item[0] for item in OUTCOME_FIELDS}
        and all(_boolish(row["required_for_future_reset_execution_audit"]) for row in rows)
        and all(_boolish(row["materialized_in_m2623"]) for row in rows)
        and all(_boolish(row["allowed_to_support_reset_success_after_execution"]) for row in rows)
        and all(
            _boolish(row["allowed_to_support_rollout_feasibility_after_execution"])
            for row in rows
        )
        and all(_boolish(row["allowed_to_support_validation_after_execution"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _actor_action_guard_preserved(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(row["actor_observation_shape"] == P0_OBSERVATION_DIM for row in rows)
        and all(row["action_shape"] == ACTION_DIM for row in rows)
        and all(row["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING for row in rows)
        and not any(_boolish(row["actor_input_mutation_detected"]) for row in rows)
        and not any(_boolish(row["action_contract_mutation_detected"]) for row in rows)
        and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in rows)
        and not any(_boolish(row["metadata_actor_visible"]) for row in rows)
    )


def _reset_execution_readiness_materialized(
    evidence_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    dry_run_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _source_build_adapter_probe_evidence_admission_materialized(evidence_rows)
        and _backend_availability_fixture_materialized(backend_rows)
        and _reset_invocation_dry_run_contract_materialized(dry_run_rows)
        and _reset_request_binding_materialized(binding_rows)
        and _actor_view_after_reset_extraction_materialized(actor_view_rows)
        and _reset_outcome_audit_schema_materialized(outcome_rows)
        and _actor_action_guard_preserved(actor_action_guard_rows)
    )


def _any_forbidden_execution(
    evidence_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    dry_run_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        any(_boolish(row["execution_allowed_in_m2623"]) for row in evidence_rows)
        or any(_boolish(row["dependency_mutation_allowed_in_m2623"]) for row in evidence_rows)
        or any(_boolish(row["backend_started_in_m2623"]) for row in backend_rows)
        or any(_boolish(row["backend_reset_called_in_m2623"]) for row in backend_rows)
        or any(_boolish(row["reset_executed_in_m2623"]) for row in dry_run_rows)
        or any(_boolish(row["reset_executed_in_m2623"]) for row in binding_rows)
        or any(_boolish(row["replay_executed_in_m2623"]) for row in binding_rows)
    )


def _any_reset_validation_or_performance_claim(claim_rows: list[dict[str, Any]]) -> bool:
    forbidden_claims = {
        "reset_success",
        "rollout_feasibility",
        "validation_protocol_readiness",
        "validation_admission",
        "validation_readiness",
        "validation_result",
        "external_validation_execution",
        "high_fidelity_validation_readiness",
        "high_fidelity_validation_result",
        "driver_performance",
        "paper_level_evidence",
        "finite_window_vs_gru",
        "current_sim_verdict",
        "level3_self_identification",
    }
    return any(
        row["claim_family"] in forbidden_claims and _boolish(row["claim_allowed_in_m2623"])
        for row in claim_rows
    )


def _claim_allowed(rows: list[dict[str, Any]], claim_family: str) -> bool:
    return any(
        row["claim_family"] == claim_family and _boolish(row["claim_allowed_in_m2623"])
        for row in rows
    )


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _selected_platform_family(rows: list[dict[str, Any]]) -> str | None:
    families = {row.get("selected_platform_family") for row in rows}
    return families.pop() if len(families) == 1 else None


def _boolish(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Route A HF3 selected-platform reset-execution readiness artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2619-summary", type=Path, default=DEFAULT_M2619_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_selected_platform_reset_execution_readiness(
        args.output_dir,
        m2619_summary_path=args.m2619_summary,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "m2623_selected_platform_reset_execution_readiness_materialization "
        f"status_pass={summary['status_pass']} "
        f"summary={summary['summary']}"
    )
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
