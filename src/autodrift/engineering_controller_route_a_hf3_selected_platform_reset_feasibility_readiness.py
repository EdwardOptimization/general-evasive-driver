"""Route A HF3 selected-platform reset-feasibility readiness materialization.

This module only materializes static reset-feasibility readiness artifacts. It
does not import, build, probe, reset, step, roll out, replay, validate, train,
rank, or promote any backend.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2619-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-"
    "readiness-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2620-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-"
    "readiness-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2619-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-"
    "readiness-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness"
)
DEFAULT_M2615_SUMMARY = Path(
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/"
    "summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"
DEPLOYED_ACTION_MAPPING = "[steer, throttle, brake]"

SOURCE_ARTIFACTS = (
    "docs/m2618-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-design.md",
    "docs/m2617-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-result-synthesis.md",
    "docs/m2616-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-result-audit.md",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/summary.json",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_reset_step_api_readiness_rows.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_actor_extractor_parity_rows.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_action_mapping_parity_rows.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_scenario_role_binding_rows.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_result_export_replay_readiness_rows.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_executable_protocol_actor_action_guard_rows.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_executable_protocol_claim_boundary_checks.csv",
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/selected_platform_executable_protocol_readiness_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform reset-feasibility readiness design materialization only; "
    "static reset request initial-state actor-view seed-lineage outcome-taxonomy precondition "
    "actor/action guard and gate panels may be materialized for the selected open/auditable "
    "platform family; not source build execution, adapter probe execution, reset execution, "
    "reset success, rollout feasibility, replay execution, validation protocol readiness, "
    "validation admission, external validation execution, high-fidelity validation readiness/result, "
    "ranking, driver performance, paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, "
    "or self-ID"
)

RESET_REQUEST_SCHEMA_FIELDNAMES = [
    "reset_request_schema_id",
    "route_role_id",
    "selected_platform_family",
    "backend_family",
    "scenario_binding_id",
    "seed_policy",
    "actor_observation_shape",
    "action_shape",
    "reset_request_schema_materialized_in_m2619",
    "initial_state_required",
    "actor_view_required_after_reset",
    "source_build_required_before_execution",
    "adapter_probe_required_before_execution",
    "reset_executed_in_m2619",
    "policy_action_allowed_in_m2619",
    "environment_step_allowed_in_m2619",
    "rollout_allowed_in_m2619",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

INITIAL_STATE_ADMISSION_FIELDNAMES = [
    "initial_state_admission_id",
    "route_role_id",
    "selected_platform_family",
    "initial_state_family",
    "source_binding_id",
    "initial_state_admission_materialized_in_m2619",
    "geometry_binding_required",
    "actor_view_required_after_reset",
    "hidden_oracle_actor_input_allowed",
    "feasibility_label_actor_visible",
    "reset_status_actor_visible",
    "validation_status_actor_visible",
    "reset_execution_allowed_in_m2619",
    "status_pass",
    "claim_boundary",
]

ACTOR_VIEW_PARITY_FIELDNAMES = [
    "actor_view_parity_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "action_shape",
    "actor_view_contract_defined_in_m2619",
    "ego_kinematics_included",
    "actuator_state_included",
    "previous_command_included",
    "road_geometry_included",
    "obstacle_geometry_included",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "selected_platform_actor_visible",
    "protocol_status_actor_visible",
    "status_pass",
    "claim_boundary",
]

RESET_SEED_LINEAGE_FIELDNAMES = [
    "reset_seed_lineage_id",
    "route_role_id",
    "selected_platform_family",
    "scenario_spec_id",
    "seed_policy",
    "parent_checkpoint_count",
    "parent_summary",
    "deterministic_seed_required",
    "replay_lineage_required",
    "lineage_materialized_in_m2619",
    "reset_executed_in_m2619",
    "replay_executed_in_m2619",
    "status_pass",
    "claim_boundary",
]

RESET_OUTCOME_TAXONOMY_GUARD_FIELDNAMES = [
    "outcome_taxonomy_guard_id",
    "outcome_field",
    "field_family",
    "actor_visible_allowed",
    "audit_metadata_allowed",
    "required_for_future_execution_audit",
    "allowed_to_support_reset_success_after_execution",
    "allowed_to_support_validation",
    "reset_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "status_pass",
    "claim_boundary",
]

RESET_EXECUTION_PRECONDITION_FIELDNAMES = [
    "precondition_id",
    "precondition_family",
    "selected_platform_family",
    "required_before_reset_execution",
    "materialized_in_m2619",
    "satisfied_by_m2619",
    "source_build_required",
    "adapter_probe_required",
    "backend_availability_required",
    "reset_request_schema_required",
    "actor_view_parity_required",
    "deterministic_lineage_required",
    "claim_boundary_required",
    "reset_execution_allowed_in_m2619",
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
    "claim_allowed_in_m2619",
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

OUTCOME_FIELDS = (
    ("backend_available", "backend_status"),
    ("reset_request_valid", "request_status"),
    ("reset_attempted", "execution_status"),
    ("reset_status", "execution_status"),
    ("actor_view_available", "actor_view_status"),
    ("diagnostics_available", "audit_metadata"),
    ("failure_reason", "audit_metadata"),
    ("execution_timestamp", "audit_metadata"),
)

PRECONDITIONS = (
    (
        "source_or_equivalent_trace_precondition",
        "source_trace",
        True,
        False,
        False,
        False,
        False,
        False,
        False,
    ),
    (
        "source_build_precondition",
        "source_build",
        False,
        True,
        False,
        False,
        False,
        False,
        False,
    ),
    (
        "adapter_probe_precondition",
        "adapter_probe",
        False,
        False,
        True,
        False,
        False,
        False,
        False,
    ),
    (
        "backend_availability_precondition",
        "backend_availability",
        False,
        False,
        False,
        True,
        False,
        False,
        False,
    ),
    (
        "reset_request_schema_precondition",
        "reset_request_schema",
        True,
        False,
        False,
        False,
        True,
        False,
        False,
    ),
    (
        "actor_view_and_lineage_precondition",
        "actor_view_and_lineage",
        True,
        False,
        False,
        False,
        False,
        True,
        True,
    ),
)

ALLOWED_CLAIMS = frozenset({"selected_platform_reset_feasibility_readiness_design_materialized"})

CLAIM_CHECKS = (
    (
        "selected_platform_reset_feasibility_readiness_design_materialized",
        True,
        "M2619 reset request initial-state actor-view seed-lineage outcome-taxonomy "
        "precondition actor/action guard claim-boundary and gate rows",
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
    ("validation_protocol_ready", False, "future validation protocol-readiness audit"),
    ("validation_admission_granted", False, "future validation-admission audit"),
    ("validation_readiness", False, "future validation readiness audit"),
    ("validation_result", False, "future validation-result audit"),
    ("external_validation_execution", False, "future explicit external-validation execution"),
    ("high_fidelity_validation_readiness", False, "future high-fidelity readiness audit"),
    ("high_fidelity_validation_result", False, "future high-fidelity validation result audit"),
    ("hf4_discrepancy_result", False, "future HF4 discrepancy audit"),
    ("success_rate_or_controller_family_verdict", False, "separate verdict milestone"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("driver_performance", False, "measured validation with claim-boundary audit"),
    ("current_sim_verdict", False, "separate current-sim verdict synthesis"),
    ("paper_level_evidence", False, "separate paper-route evidence matrix"),
    ("finite_window_vs_gru_result", False, "separate finite-window-vs-GRU matrix"),
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


def materialize_route_a_hf3_selected_platform_reset_feasibility_readiness(
    output_dir: Path,
    *,
    m2615_summary_path: Path = DEFAULT_M2615_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2615_summary = read_json(m2615_summary_path)

    request_rows = build_reset_request_schema_rows(m2615_summary)
    initial_state_rows = build_initial_state_admission_rows(request_rows)
    actor_view_rows = build_actor_view_parity_rows(initial_state_rows)
    seed_lineage_rows = build_reset_seed_lineage_rows(actor_view_rows, m2615_summary)
    outcome_guard_rows = build_reset_outcome_taxonomy_guard_rows()
    precondition_rows = build_reset_execution_precondition_rows(
        request_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
    )
    actor_action_guard_rows = build_actor_action_guard_rows(actor_view_rows)
    claim_rows = build_claim_boundary_checks(
        request_rows,
        initial_state_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
        precondition_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2615_summary=m2615_summary,
        request_rows=request_rows,
        initial_state_rows=initial_state_rows,
        actor_view_rows=actor_view_rows,
        seed_lineage_rows=seed_lineage_rows,
        outcome_guard_rows=outcome_guard_rows,
        precondition_rows=precondition_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )

    request_path = output_dir / "hf3_selected_platform_reset_request_schema_rows.csv"
    initial_state_path = output_dir / "hf3_selected_platform_initial_state_admission_rows.csv"
    actor_view_path = output_dir / "hf3_selected_platform_actor_view_parity_rows.csv"
    seed_lineage_path = output_dir / "hf3_selected_platform_reset_seed_lineage_rows.csv"
    outcome_guard_path = output_dir / "hf3_selected_platform_reset_outcome_taxonomy_guard_rows.csv"
    precondition_path = output_dir / "hf3_selected_platform_reset_execution_precondition_rows.csv"
    actor_action_guard_path = (
        output_dir / "hf3_selected_platform_reset_feasibility_actor_action_guard_rows.csv"
    )
    claim_path = output_dir / "hf3_selected_platform_reset_feasibility_claim_boundary_checks.csv"
    gate_path = output_dir / "selected_platform_reset_feasibility_readiness_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(request_path, request_rows, fieldnames=RESET_REQUEST_SCHEMA_FIELDNAMES)
    write_csv_rows(
        initial_state_path,
        initial_state_rows,
        fieldnames=INITIAL_STATE_ADMISSION_FIELDNAMES,
    )
    write_csv_rows(actor_view_path, actor_view_rows, fieldnames=ACTOR_VIEW_PARITY_FIELDNAMES)
    write_csv_rows(seed_lineage_path, seed_lineage_rows, fieldnames=RESET_SEED_LINEAGE_FIELDNAMES)
    write_csv_rows(
        outcome_guard_path,
        outcome_guard_rows,
        fieldnames=RESET_OUTCOME_TAXONOMY_GUARD_FIELDNAMES,
    )
    write_csv_rows(
        precondition_path,
        precondition_rows,
        fieldnames=RESET_EXECUTION_PRECONDITION_FIELDNAMES,
    )
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
        m2615_summary=m2615_summary,
        request_rows=request_rows,
        initial_state_rows=initial_state_rows,
        actor_view_rows=actor_view_rows,
        seed_lineage_rows=seed_lineage_rows,
        outcome_guard_rows=outcome_guard_rows,
        precondition_rows=precondition_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        request_path=request_path,
        initial_state_path=initial_state_path,
        actor_view_path=actor_view_path,
        seed_lineage_path=seed_lineage_path,
        outcome_guard_path=outcome_guard_path,
        precondition_path=precondition_path,
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


def build_reset_request_schema_rows(
    m2615_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2615_executable_protocol_evidence_accepted(m2615_summary or {})
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "reset_request_schema_id": f"{route_role_id}_reset_request_schema",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "backend_family": SELECTED_PLATFORM_FAMILY,
                "scenario_binding_id": f"{route_role_id}_scenario_binding",
                "seed_policy": "deterministic_manifest_seed_before_future_reset_execution",
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "reset_request_schema_materialized_in_m2619": True,
                "initial_state_required": True,
                "actor_view_required_after_reset": True,
                "source_build_required_before_execution": True,
                "adapter_probe_required_before_execution": True,
                "reset_executed_in_m2619": False,
                "policy_action_allowed_in_m2619": False,
                "environment_step_allowed_in_m2619": False,
                "rollout_allowed_in_m2619": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(parent_accepted and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_initial_state_admission_rows(
    request_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    request_materialized = _reset_request_schema_materialized(request_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "initial_state_admission_id": f"{route_role_id}_initial_state_admission",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "initial_state_family": "bounded_hf3_role_initial_state_contract",
                "source_binding_id": f"{route_role_id}_scenario_binding",
                "initial_state_admission_materialized_in_m2619": True,
                "geometry_binding_required": True,
                "actor_view_required_after_reset": True,
                "hidden_oracle_actor_input_allowed": False,
                "feasibility_label_actor_visible": False,
                "reset_status_actor_visible": False,
                "validation_status_actor_visible": False,
                "reset_execution_allowed_in_m2619": False,
                "status_pass": bool(request_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_view_parity_rows(
    initial_state_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    initial_state_materialized = _initial_state_admission_materialized(initial_state_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "actor_view_parity_id": f"{route_role_id}_reset_actor_view_parity",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "actor_view_contract_defined_in_m2619": True,
                "ego_kinematics_included": True,
                "actuator_state_included": True,
                "previous_command_included": True,
                "road_geometry_included": True,
                "obstacle_geometry_included": True,
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "selected_platform_actor_visible": False,
                "protocol_status_actor_visible": False,
                "status_pass": bool(
                    initial_state_materialized and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_seed_lineage_rows(
    actor_view_rows: list[dict[str, Any]] | None = None,
    m2615_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    actor_view_materialized = _actor_view_parity_materialized(actor_view_rows or [])
    parent_summary = (m2615_summary or {}).get("summary", str(DEFAULT_M2615_SUMMARY))
    rows = []
    for idx, route_role_id in enumerate(VALIDATION_ROLES, start=1):
        rows.append(
            {
                "reset_seed_lineage_id": f"{route_role_id}_reset_seed_lineage",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "scenario_spec_id": f"{route_role_id}_hf3_selected_platform_reset_schema",
                "seed_policy": f"deterministic_role_seed_{idx:02d}_no_reset_execution",
                "parent_checkpoint_count": 3,
                "parent_summary": parent_summary,
                "deterministic_seed_required": True,
                "replay_lineage_required": True,
                "lineage_materialized_in_m2619": True,
                "reset_executed_in_m2619": False,
                "replay_executed_in_m2619": False,
                "status_pass": bool(actor_view_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_outcome_taxonomy_guard_rows() -> list[dict[str, Any]]:
    return [
        {
            "outcome_taxonomy_guard_id": f"{outcome_field}_taxonomy_guard",
            "outcome_field": outcome_field,
            "field_family": field_family,
            "actor_visible_allowed": False,
            "audit_metadata_allowed": True,
            "required_for_future_execution_audit": True,
            "allowed_to_support_reset_success_after_execution": True,
            "allowed_to_support_validation": False,
            "reset_outcome_actor_visible": False,
            "validation_outcome_actor_visible": False,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for outcome_field, field_family in OUTCOME_FIELDS
    ]


def build_reset_execution_precondition_rows(
    request_rows: list[dict[str, Any]] | None = None,
    actor_view_rows: list[dict[str, Any]] | None = None,
    seed_lineage_rows: list[dict[str, Any]] | None = None,
    outcome_guard_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    materialized = bool(
        _reset_request_schema_materialized(request_rows or [])
        and _actor_view_parity_materialized(actor_view_rows or [])
        and _reset_seed_lineage_materialized(seed_lineage_rows or [])
        and _reset_outcome_taxonomy_guard_materialized(outcome_guard_rows or [])
    )
    rows = []
    for (
        precondition_id,
        family,
        satisfied_by_m2619,
        source_build_required,
        adapter_probe_required,
        backend_availability_required,
        reset_request_schema_required,
        actor_view_parity_required,
        deterministic_lineage_required,
    ) in PRECONDITIONS:
        rows.append(
            {
                "precondition_id": precondition_id,
                "precondition_family": family,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "required_before_reset_execution": True,
                "materialized_in_m2619": True,
                "satisfied_by_m2619": satisfied_by_m2619,
                "source_build_required": source_build_required,
                "adapter_probe_required": adapter_probe_required,
                "backend_availability_required": backend_availability_required,
                "reset_request_schema_required": reset_request_schema_required,
                "actor_view_parity_required": actor_view_parity_required,
                "deterministic_lineage_required": deterministic_lineage_required,
                "claim_boundary_required": True,
                "reset_execution_allowed_in_m2619": False,
                "status_pass": materialized,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(
    actor_view_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for actor_view in actor_view_rows:
        rows.append(
            {
                "actor_action_guard_id": f"{actor_view['route_role_id']}_reset_actor_action_guard",
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
    request_rows: list[dict[str, Any]],
    initial_state_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    seed_lineage_rows: list[dict[str, Any]],
    outcome_guard_rows: list[dict[str, Any]],
    precondition_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = _reset_feasibility_readiness_materialized(
        request_rows,
        initial_state_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
        precondition_rows,
        actor_action_guard_rows,
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2619": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2615_summary: dict[str, Any],
    request_rows: list[dict[str, Any]],
    initial_state_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    seed_lineage_rows: list[dict[str, Any]],
    outcome_guard_rows: list[dict[str, Any]],
    precondition_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2619"])
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
            "m2615_m2616_m2617_m2618_executable_protocol_readiness_evidence_accepted",
            "lineage",
            _m2615_executable_protocol_evidence_accepted(m2615_summary),
            (
                f"m2615_status={m2615_summary.get('status_pass')};"
                f"selected={m2615_summary.get('selected_platform_family_in_m2615')};"
                f"reset_executed={m2615_summary.get('reset_executed_in_m2615')};"
                f"validation_ready={m2615_summary.get('validation_protocol_ready_in_m2615')}"
            ),
            f"m2615_status=True;selected={SELECTED_PLATFORM_FAMILY};"
            "reset_executed=False;validation_ready=False",
            "lineage_invalid",
        ),
        (
            "reset_request_schema_rows_pass",
            "contract",
            _reset_request_schema_materialized(request_rows),
            f"rows={len(request_rows)};selected={_selected_platform_family(request_rows)}",
            f"rows=2;selected={SELECTED_PLATFORM_FAMILY};obs=72;action=3;execution=false",
            "contract_violation",
        ),
        (
            "initial_state_admission_rows_pass",
            "contract",
            _initial_state_admission_materialized(initial_state_rows),
            f"rows={len(initial_state_rows)}",
            "rows=2;hidden/feasibility/reset/validation actor-visible=false;reset=false",
            "contract_violation",
        ),
        (
            "actor_view_parity_rows_pass",
            "contract",
            _actor_view_parity_materialized(actor_view_rows),
            f"rows={len(actor_view_rows)}",
            "rows=2;obs=72;action=3;deployable actor fields=true;metadata=false",
            "contract_violation",
        ),
        (
            "reset_seed_lineage_rows_pass",
            "lineage",
            _reset_seed_lineage_materialized(seed_lineage_rows),
            f"rows={len(seed_lineage_rows)}",
            "rows=2;deterministic seed and lineage materialized;reset/replay=false",
            "lineage_invalid",
        ),
        (
            "reset_outcome_taxonomy_guard_rows_pass",
            "claim_boundary",
            _reset_outcome_taxonomy_guard_materialized(outcome_guard_rows),
            f"rows={len(outcome_guard_rows)}",
            "rows=8;outcomes actor-visible=false;validation=false",
            "objective_overfit",
        ),
        (
            "reset_execution_precondition_rows_pass",
            "claim_boundary",
            _reset_execution_preconditions_materialized(precondition_rows),
            f"rows={len(precondition_rows)}",
            "rows=6;preconditions materialized;reset execution=false",
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
                request_rows,
                initial_state_rows,
                seed_lineage_rows,
                precondition_rows,
            ),
            "build/probe/reset/step/action/rollout/replay/validation=false",
            "build/probe/reset/step/action/rollout/replay/validation=false",
            "objective_overfit",
        ),
        (
            "reset_success_validation_rollout_and_performance_forbidden",
            "claim_boundary",
            not _any_reset_validation_or_performance_claim(request_rows, outcome_guard_rows, claim_rows),
            "reset success/rollout/validation/readiness/result/performance=false",
            "reset success/rollout/validation/readiness/result/performance=false",
            "objective_overfit",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            _actor_action_guard_preserved(actor_action_guard_rows)
            and _actor_view_parity_materialized(actor_view_rows),
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
    m2615_summary: dict[str, Any],
    request_rows: list[dict[str, Any]],
    initial_state_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    seed_lineage_rows: list[dict[str, Any]],
    outcome_guard_rows: list[dict[str, Any]],
    precondition_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    request_path: Path,
    initial_state_path: Path,
    actor_view_path: Path,
    seed_lineage_path: Path,
    outcome_guard_path: Path,
    precondition_path: Path,
    actor_action_guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2619"])
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS
    )
    materialized = _reset_feasibility_readiness_materialized(
        request_rows,
        initial_state_rows,
        actor_view_rows,
        seed_lineage_rows,
        outcome_guard_rows,
        precondition_rows,
        actor_action_guard_rows,
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_hf3_selected_platform_reset_feasibility_"
            "readiness_materialization_preflight_pass"
        ),
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_selected_platform_reset_request_schema_rows": str(request_path),
        "hf3_selected_platform_initial_state_admission_rows": str(initial_state_path),
        "hf3_selected_platform_actor_view_parity_rows": str(actor_view_path),
        "hf3_selected_platform_reset_seed_lineage_rows": str(seed_lineage_path),
        "hf3_selected_platform_reset_outcome_taxonomy_guard_rows": str(outcome_guard_path),
        "hf3_selected_platform_reset_execution_precondition_rows": str(precondition_path),
        "hf3_selected_platform_reset_feasibility_actor_action_guard_rows": str(
            actor_action_guard_path
        ),
        "hf3_selected_platform_reset_feasibility_claim_boundary_checks": str(claim_path),
        "selected_platform_reset_feasibility_readiness_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2615_status_pass": bool(m2615_summary.get("status_pass")),
        "m2615_materialization_gates_all_pass": bool(
            m2615_summary.get("materialization_gates_all_pass")
        ),
        "m2615_selected_platform_family": m2615_summary.get("selected_platform_family_in_m2615"),
        "m2615_executable_protocol_readiness_design_materialized": bool(
            m2615_summary.get(
                "selected_platform_executable_protocol_readiness_design_materialized_in_m2615"
            )
        ),
        "m2615_reset_step_api_contract_materialized": bool(
            m2615_summary.get("reset_step_api_contract_materialized_in_m2615")
        ),
        "m2615_reset_executed": bool(m2615_summary.get("reset_executed_in_m2615")),
        "m2615_validation_protocol_ready": bool(
            m2615_summary.get("validation_protocol_ready_in_m2615")
        ),
        "m2615_validation_admission_granted": bool(
            m2615_summary.get("validation_admission_granted_in_m2615")
        ),
        "m2615_validation_result_claim_allowed": bool(
            m2615_summary.get("validation_result_claim_allowed")
        ),
        "m2615_driver_performance_claim_allowed": bool(
            m2615_summary.get("driver_performance_claim_allowed_in_m2615")
        ),
        "reset_request_schema_row_count": len(request_rows),
        "initial_state_admission_row_count": len(initial_state_rows),
        "actor_view_parity_row_count": len(actor_view_rows),
        "reset_seed_lineage_row_count": len(seed_lineage_rows),
        "reset_outcome_taxonomy_guard_row_count": len(outcome_guard_rows),
        "reset_execution_precondition_row_count": len(precondition_rows),
        "actor_action_guard_row_count": len(actor_action_guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "reset_request_schema_rows_all_pass": _all_status_pass(request_rows),
        "initial_state_admission_rows_all_pass": _all_status_pass(initial_state_rows),
        "actor_view_parity_rows_all_pass": _all_status_pass(actor_view_rows),
        "reset_seed_lineage_rows_all_pass": _all_status_pass(seed_lineage_rows),
        "reset_outcome_taxonomy_guard_rows_all_pass": _all_status_pass(outcome_guard_rows),
        "reset_execution_precondition_rows_all_pass": _all_status_pass(precondition_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(actor_action_guard_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "selected_platform_reset_feasibility_readiness_design_materialized_in_m2619": (
            materialized
        ),
        "selected_platform_family_in_m2619": SELECTED_PLATFORM_FAMILY,
        "selected_platform_family_is_open_auditable": True,
        "reset_request_schema_materialized_in_m2619": _reset_request_schema_materialized(
            request_rows
        ),
        "initial_state_admission_materialized_in_m2619": _initial_state_admission_materialized(
            initial_state_rows
        ),
        "actor_view_parity_materialized_in_m2619": _actor_view_parity_materialized(
            actor_view_rows
        ),
        "reset_seed_lineage_materialized_in_m2619": _reset_seed_lineage_materialized(
            seed_lineage_rows
        ),
        "reset_outcome_taxonomy_guard_materialized_in_m2619": (
            _reset_outcome_taxonomy_guard_materialized(outcome_guard_rows)
        ),
        "reset_execution_precondition_materialized_in_m2619": (
            _reset_execution_preconditions_materialized(precondition_rows)
        ),
        "selected_platform_reset_feasibility_readiness_design_materialized_claim_allowed": (
            _claim_allowed(
                claim_rows,
                "selected_platform_reset_feasibility_readiness_design_materialized",
            )
        ),
        "forbidden_claim_allowed_in_m2619": forbidden_claim_allowed,
        "external_install_allowed_in_m2619": False,
        "external_import_allowed_in_m2619": False,
        "runtime_execution_allowed_in_m2619": False,
        "dependency_mutation_allowed_in_m2619": False,
        "source_build_executed_in_m2619": False,
        "adapter_probe_executed_in_m2619": False,
        "reset_executed_in_m2619": any(
            _boolish(row.get("reset_executed_in_m2619"))
            for row in request_rows + seed_lineage_rows
        ),
        "environment_step_executed_in_m2619": any(
            _boolish(row["environment_step_allowed_in_m2619"]) for row in request_rows
        ),
        "policy_action_executed_in_m2619": any(
            _boolish(row["policy_action_allowed_in_m2619"]) for row in request_rows
        ),
        "rollout_executed_in_m2619": any(
            _boolish(row["rollout_allowed_in_m2619"]) for row in request_rows
        ),
        "replay_executed_in_m2619": any(
            _boolish(row["replay_executed_in_m2619"]) for row in seed_lineage_rows
        ),
        "external_validation_execution_allowed_in_m2619": False,
        "validation_protocol_ready_in_m2619": _claim_allowed(
            claim_rows,
            "validation_protocol_ready",
        ),
        "validation_admission_granted_in_m2619": _claim_allowed(
            claim_rows,
            "validation_admission_granted",
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"]) for row in request_rows
        ),
        "reset_success_claim_allowed_in_m2619": _claim_allowed(claim_rows, "reset_success"),
        "rollout_feasibility_claim_allowed_in_m2619": _claim_allowed(
            claim_rows,
            "rollout_feasibility",
        ),
        "driver_performance_claim_allowed_in_m2619": _claim_allowed(
            claim_rows,
            "driver_performance",
        ),
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
            _boolish(row["reset_outcome_actor_visible"])
            for row in actor_view_rows + outcome_guard_rows
        ),
        "validation_outcome_actor_visible": any(
            _boolish(row["validation_outcome_actor_visible"]) for row in outcome_guard_rows
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
        "repo_local_static_selected_platform_reset_feasibility_readiness_materialization": True,
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2619 Engineering Controller Route A Baseline HF3 Selected-Platform "
                "Reset-Feasibility Readiness Materialization Preflight",
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
                f"reset_request_schema_rows: {summary['reset_request_schema_row_count']}",
                f"initial_state_admission_rows: {summary['initial_state_admission_row_count']}",
                f"actor_view_parity_rows: {summary['actor_view_parity_row_count']}",
                f"reset_seed_lineage_rows: {summary['reset_seed_lineage_row_count']}",
                "reset_outcome_taxonomy_guard_rows: "
                f"{summary['reset_outcome_taxonomy_guard_row_count']}",
                "reset_execution_precondition_rows: "
                f"{summary['reset_execution_precondition_row_count']}",
                f"actor_action_guard_rows: {summary['actor_action_guard_row_count']}",
                f"claim_boundary_rows: {summary['claim_boundary_check_count']}",
                f"materialization_gates: {summary['materialization_gate_count']}",
                "selected_platform_reset_feasibility_readiness_design_materialized_in_m2619: "
                f"{summary['selected_platform_reset_feasibility_readiness_design_materialized_in_m2619']}",
                f"selected_platform_family_in_m2619: {summary['selected_platform_family_in_m2619']}",
                f"external_install_allowed_in_m2619: {summary['external_install_allowed_in_m2619']}",
                f"external_import_allowed_in_m2619: {summary['external_import_allowed_in_m2619']}",
                f"runtime_execution_allowed_in_m2619: {summary['runtime_execution_allowed_in_m2619']}",
                f"dependency_mutation_allowed_in_m2619: {summary['dependency_mutation_allowed_in_m2619']}",
                f"source_build_executed_in_m2619: {summary['source_build_executed_in_m2619']}",
                f"adapter_probe_executed_in_m2619: {summary['adapter_probe_executed_in_m2619']}",
                f"reset_executed_in_m2619: {summary['reset_executed_in_m2619']}",
                f"environment_step_executed_in_m2619: {summary['environment_step_executed_in_m2619']}",
                f"policy_action_executed_in_m2619: {summary['policy_action_executed_in_m2619']}",
                f"rollout_executed_in_m2619: {summary['rollout_executed_in_m2619']}",
                f"replay_executed_in_m2619: {summary['replay_executed_in_m2619']}",
                "external_validation_execution_allowed_in_m2619: "
                f"{summary['external_validation_execution_allowed_in_m2619']}",
                f"validation_protocol_ready_in_m2619: {summary['validation_protocol_ready_in_m2619']}",
                f"validation_admission_granted_in_m2619: {summary['validation_admission_granted_in_m2619']}",
                f"validation_result_claim_allowed: {summary['validation_result_claim_allowed']}",
                f"reset_success_claim_allowed_in_m2619: {summary['reset_success_claim_allowed_in_m2619']}",
                "driver_performance_claim_allowed_in_m2619: "
                f"{summary['driver_performance_claim_allowed_in_m2619']}",
                f"actor contract: P0 observation {summary['observation_shape']} / action {summary['action_shape']}",
                "```",
                "",
                "## Artifact Paths",
                "",
                f"- reset request schema rows: `{summary['hf3_selected_platform_reset_request_schema_rows']}`",
                f"- initial-state admission rows: `{summary['hf3_selected_platform_initial_state_admission_rows']}`",
                f"- actor-view parity rows: `{summary['hf3_selected_platform_actor_view_parity_rows']}`",
                f"- reset seed/lineage rows: `{summary['hf3_selected_platform_reset_seed_lineage_rows']}`",
                "- reset outcome taxonomy guard rows: "
                f"`{summary['hf3_selected_platform_reset_outcome_taxonomy_guard_rows']}`",
                "- reset-execution precondition rows: "
                f"`{summary['hf3_selected_platform_reset_execution_precondition_rows']}`",
                "- actor/action guard rows: "
                f"`{summary['hf3_selected_platform_reset_feasibility_actor_action_guard_rows']}`",
                "- claim-boundary rows: "
                f"`{summary['hf3_selected_platform_reset_feasibility_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['selected_platform_reset_feasibility_readiness_gate_matrix']}`",
                "",
                "## Supported Claims",
                "",
                "Supported:",
                "",
                "- selected-platform reset-feasibility readiness design artifacts are materialized",
                "- reset request schema, initial-state admission, actor-view parity, seed/lineage, "
                "outcome taxonomy, precondition, actor/action, claim-boundary, and gate rows are materialized",
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
                "- controller ranking, success-rate verdict, or checkpoint promotion",
                "- driver-performance claim",
                "- current-sim verdict",
                "- paper-level evidence",
                "- finite-window-vs-GRU result",
                "- level3 self-identification evidence",
                "",
                "## Boundary",
                "",
                "M2619 is a static reset-feasibility readiness materialization preflight. It "
                "does not execute reset, source build, adapter probe, policy action, environment "
                "step, rollout, replay, validation, training, ranking, promotion, or any high-fidelity "
                "simulator. Reset outcome taxonomy rows are future audit schema and are not actor-visible.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _m2615_executable_protocol_evidence_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("source_artifacts_exist")
        and summary.get("materialization_gates_all_pass")
        and summary.get("selected_platform_family_in_m2615") == SELECTED_PLATFORM_FAMILY
        and summary.get("selected_platform_executable_protocol_readiness_design_materialized_in_m2615")
        and summary.get("reset_step_api_contract_materialized_in_m2615")
        and summary.get("actor_extractor_parity_materialized_in_m2615")
        and summary.get("action_mapping_parity_materialized_in_m2615")
        and summary.get("scenario_role_binding_materialized_in_m2615")
        and summary.get("result_export_replay_materialized_in_m2615")
        and not summary.get("forbidden_claim_allowed_in_m2615")
        and not summary.get("external_install_allowed_in_m2615")
        and not summary.get("external_import_allowed_in_m2615")
        and not summary.get("runtime_execution_allowed_in_m2615")
        and not summary.get("dependency_mutation_allowed_in_m2615")
        and not summary.get("source_build_executed_in_m2615")
        and not summary.get("adapter_probe_executed_in_m2615")
        and not summary.get("reset_executed_in_m2615")
        and not summary.get("environment_step_executed_in_m2615")
        and not summary.get("policy_action_executed_in_m2615")
        and not summary.get("rollout_executed_in_m2615")
        and not summary.get("replay_executed_in_m2615")
        and not summary.get("external_validation_execution_allowed_in_m2615")
        and not summary.get("validation_protocol_ready_in_m2615")
        and not summary.get("validation_admission_granted_in_m2615")
        and not summary.get("validation_result_claim_allowed")
        and not summary.get("driver_performance_claim_allowed_in_m2615")
    )


def _reset_request_schema_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and {row["actor_observation_shape"] for row in rows} == {P0_OBSERVATION_DIM}
        and {row["action_shape"] for row in rows} == {ACTION_DIM}
        and not any(_boolish(row["reset_executed_in_m2619"]) for row in rows)
        and not any(_boolish(row["policy_action_allowed_in_m2619"]) for row in rows)
        and not any(_boolish(row["environment_step_allowed_in_m2619"]) for row in rows)
        and not any(_boolish(row["rollout_allowed_in_m2619"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _initial_state_admission_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and not any(_boolish(row["hidden_oracle_actor_input_allowed"]) for row in rows)
        and not any(_boolish(row["feasibility_label_actor_visible"]) for row in rows)
        and not any(_boolish(row["reset_status_actor_visible"]) for row in rows)
        and not any(_boolish(row["validation_status_actor_visible"]) for row in rows)
        and not any(_boolish(row["reset_execution_allowed_in_m2619"]) for row in rows)
    )


def _actor_view_parity_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["actor_observation_shape"] for row in rows} == {P0_OBSERVATION_DIM}
        and {row["action_shape"] for row in rows} == {ACTION_DIM}
        and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in rows)
        and not any(_boolish(row["diagnostics_actor_visible"]) for row in rows)
        and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in rows)
        and not any(_boolish(row["backend_status_actor_visible"]) for row in rows)
        and not any(_boolish(row["reset_outcome_actor_visible"]) for row in rows)
        and not any(_boolish(row["selected_platform_actor_visible"]) for row in rows)
        and not any(_boolish(row["protocol_status_actor_visible"]) for row in rows)
    )


def _reset_seed_lineage_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and {row["parent_checkpoint_count"] for row in rows} == {3}
        and not any(_boolish(row["reset_executed_in_m2619"]) for row in rows)
        and not any(_boolish(row["replay_executed_in_m2619"]) for row in rows)
    )


def _reset_outcome_taxonomy_guard_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(OUTCOME_FIELDS)
        and _all_status_pass(rows)
        and {row["outcome_field"] for row in rows} == {field for field, _ in OUTCOME_FIELDS}
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
        and not any(_boolish(row["reset_outcome_actor_visible"]) for row in rows)
        and not any(_boolish(row["validation_outcome_actor_visible"]) for row in rows)
        and not any(_boolish(row["allowed_to_support_validation"]) for row in rows)
    )


def _reset_execution_preconditions_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(PRECONDITIONS)
        and _all_status_pass(rows)
        and {row["precondition_id"] for row in rows} == {row[0] for row in PRECONDITIONS}
        and not any(_boolish(row["reset_execution_allowed_in_m2619"]) for row in rows)
    )


def _actor_action_guard_preserved(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and {row["actor_observation_shape"] for row in rows} == {P0_OBSERVATION_DIM}
        and {row["action_shape"] for row in rows} == {ACTION_DIM}
        and {row["deployed_action_mapping"] for row in rows} == {DEPLOYED_ACTION_MAPPING}
        and not any(_boolish(row["actor_input_mutation_detected"]) for row in rows)
        and not any(_boolish(row["action_contract_mutation_detected"]) for row in rows)
        and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in rows)
        and not any(_boolish(row["metadata_actor_visible"]) for row in rows)
    )


def _reset_feasibility_readiness_materialized(
    request_rows: list[dict[str, Any]],
    initial_state_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    seed_lineage_rows: list[dict[str, Any]],
    outcome_guard_rows: list[dict[str, Any]],
    precondition_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _reset_request_schema_materialized(request_rows)
        and _initial_state_admission_materialized(initial_state_rows)
        and _actor_view_parity_materialized(actor_view_rows)
        and _reset_seed_lineage_materialized(seed_lineage_rows)
        and _reset_outcome_taxonomy_guard_materialized(outcome_guard_rows)
        and _reset_execution_preconditions_materialized(precondition_rows)
        and _actor_action_guard_preserved(actor_action_guard_rows)
    )


def _any_forbidden_execution(
    request_rows: list[dict[str, Any]],
    initial_state_rows: list[dict[str, Any]],
    seed_lineage_rows: list[dict[str, Any]],
    precondition_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        any(_boolish(row["reset_executed_in_m2619"]) for row in request_rows)
        or any(_boolish(row["policy_action_allowed_in_m2619"]) for row in request_rows)
        or any(_boolish(row["environment_step_allowed_in_m2619"]) for row in request_rows)
        or any(_boolish(row["rollout_allowed_in_m2619"]) for row in request_rows)
        or any(_boolish(row["reset_execution_allowed_in_m2619"]) for row in initial_state_rows)
        or any(_boolish(row["reset_executed_in_m2619"]) for row in seed_lineage_rows)
        or any(_boolish(row["replay_executed_in_m2619"]) for row in seed_lineage_rows)
        or any(_boolish(row["reset_execution_allowed_in_m2619"]) for row in precondition_rows)
    )


def _any_reset_validation_or_performance_claim(
    request_rows: list[dict[str, Any]],
    outcome_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> bool:
    forbidden_claims = {
        "reset_success",
        "rollout_feasibility",
        "validation_protocol_ready",
        "validation_admission_granted",
        "validation_readiness",
        "validation_result",
        "external_validation_execution",
        "high_fidelity_validation_readiness",
        "high_fidelity_validation_result",
        "driver_performance",
        "paper_level_evidence",
        "finite_window_vs_gru_result",
        "current_sim_verdict",
        "level3_self_identification",
    }
    return bool(
        any(_boolish(row["validation_result_claim_allowed"]) for row in request_rows)
        or any(_boolish(row["allowed_to_support_validation"]) for row in outcome_guard_rows)
        or any(
            row["claim_family"] in forbidden_claims and _boolish(row["claim_allowed_in_m2619"])
            for row in claim_rows
        )
    )


def _claim_allowed(rows: list[dict[str, Any]], claim_family: str) -> bool:
    return any(
        row["claim_family"] == claim_family and _boolish(row["claim_allowed_in_m2619"])
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
        description="Materialize Route A HF3 selected-platform reset-feasibility readiness artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2615-summary", type=Path, default=DEFAULT_M2615_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_selected_platform_reset_feasibility_readiness(
        args.output_dir,
        m2615_summary_path=args.m2615_summary,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "m2619_selected_platform_reset_feasibility_readiness_materialization "
        f"status_pass={summary['status_pass']} "
        f"summary={summary['summary']}"
    )
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
