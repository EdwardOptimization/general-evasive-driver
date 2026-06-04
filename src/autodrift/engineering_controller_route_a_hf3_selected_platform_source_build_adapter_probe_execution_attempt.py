"""Route A HF3 selected-platform source-build/adapter-probe attempt materialization.

This module only materializes static execution-attempt protocol artifacts. It
does not install, import, build, probe, start a backend, reset, step, roll out,
replay, validate, train, rank, or promote any backend.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2631-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-execution-attempt-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2632-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-execution-attempt-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2631-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-execution-attempt-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2631_engineering_controller_route_a_hf3_selected_platform_"
    "source_build_adapter_probe_execution_attempt"
)
DEFAULT_M2627_SUMMARY = Path(
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_"
    "source_build_adapter_probe_execution/summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"
DEPLOYED_ACTION_MAPPING = "[steer, throttle, brake]"

SOURCE_ARTIFACTS = (
    "docs/m2630-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-design.md",
    "docs/m2629-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-synthesis.md",
    "docs/m2628-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-audit.md",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_command_contract_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_adapter_probe_command_contract_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_dependency_environment_isolation_guard_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_artifact_capture_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_adapter_probe_trace_capture_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks.csv",
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/selected_platform_source_build_adapter_probe_execution_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
    "docs/self-id-go-no-go-paper-route-plan.md",
    "docs/paper-route-finite-window-vs-gru-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform source-build/adapter-probe execution-attempt "
    "protocol materialization only; command attempt/admission rows runtime guards "
    "future log/evidence capture rows failure taxonomy actor/action guard "
    "claim-boundary and gate panels may be materialized for the selected "
    "open/auditable platform family; not dependency execution readiness, source "
    "build execution, source build success, adapter probe execution, adapter probe "
    "success, backend discovery, backend availability, reset execution, reset "
    "success, rollout feasibility, replay execution, validation protocol readiness, "
    "validation admission, external validation execution, high-fidelity validation "
    "readiness/result, ranking, driver performance, paper, FW-vs-GRU, current-sim "
    "verdict, high-fidelity validation, or self-ID"
)

SOURCE_BUILD_ATTEMPT_ADMISSION_FIELDNAMES = [
    "source_build_attempt_admission_id",
    "command_family",
    "selected_platform_family",
    "command_contract_id",
    "source_tree_required",
    "out_of_tree_build_required",
    "command_attempt_schema_materialized_in_m2631",
    "execution_attempt_allowed_after_m2631_audit",
    "source_build_executed_in_m2631",
    "source_build_attempt_executed_in_m2631",
    "dependency_mutation_allowed_in_m2631",
    "network_access_allowed_in_m2631",
    "log_capture_required",
    "artifact_capture_required",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

ADAPTER_PROBE_ATTEMPT_ADMISSION_FIELDNAMES = [
    "adapter_probe_attempt_admission_id",
    "probe_family",
    "selected_platform_family",
    "adapter_probe_contract_id",
    "adapter_import_required",
    "backend_discovery_required",
    "command_attempt_schema_materialized_in_m2631",
    "adapter_probe_executed_in_m2631",
    "adapter_probe_attempt_executed_in_m2631",
    "backend_start_allowed_in_m2631",
    "reset_allowed_in_m2631",
    "trace_capture_required",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_RUNTIME_GUARD_FIELDNAMES = [
    "execution_guard_id",
    "guard_family",
    "selected_platform_family",
    "external_install_allowed_in_m2631",
    "external_import_allowed_in_m2631",
    "dependency_mutation_allowed_in_m2631",
    "source_tree_mutation_allowed_in_m2631",
    "network_access_allowed_in_m2631",
    "external_runtime_allowed_in_m2631",
    "source_build_execution_allowed_in_m2631",
    "adapter_probe_execution_allowed_in_m2631",
    "backend_start_allowed_in_m2631",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

EXECUTION_ATTEMPT_LOG_CAPTURE_FIELDNAMES = [
    "execution_log_capture_id",
    "log_family",
    "selected_platform_family",
    "required_for_future_execution_attempt_audit",
    "command_attempt_schema_materialized_in_m2631",
    "source_build_executed_in_m2631",
    "adapter_probe_executed_in_m2631",
    "log_observed_in_m2631",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

BACKEND_DISCOVERY_EVIDENCE_CAPTURE_FIELDNAMES = [
    "backend_discovery_capture_id",
    "evidence_family",
    "selected_platform_family",
    "required_for_future_backend_availability_audit",
    "required_for_future_reset_admission",
    "backend_discovery_schema_materialized_in_m2631",
    "adapter_probe_executed_in_m2631",
    "backend_started_in_m2631",
    "backend_discovered_claim_allowed_in_m2631",
    "backend_availability_claim_allowed_in_m2631",
    "reset_execution_allowed_in_m2631",
    "evidence_observed_in_m2631",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

EXECUTION_FAILURE_TAXONOMY_FIELDNAMES = [
    "failure_taxonomy_id",
    "failure_field",
    "field_family",
    "required_for_future_execution_attempt_audit",
    "allowed_to_support_failure_classification_after_execution",
    "actor_visible_allowed",
    "materialized_in_m2631",
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
    "claim_allowed_in_m2631",
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

SOURCE_BUILD_ATTEMPTS = (
    (
        "selected_platform_source_build_configure_attempt_admission",
        "configure",
        "selected_platform_source_build_configure_command_contract",
    ),
    (
        "selected_platform_source_build_compile_attempt_admission",
        "compile",
        "selected_platform_source_build_compile_command_contract",
    ),
)

ADAPTER_PROBE_ATTEMPTS = (
    (
        "selected_platform_adapter_import_attempt_admission",
        "adapter_import",
        "selected_platform_adapter_import_probe_contract",
    ),
    (
        "selected_platform_adapter_backend_probe_attempt_admission",
        "backend_probe",
        "selected_platform_adapter_backend_probe_contract",
    ),
)

EXECUTION_GUARDS = (
    ("dependency_install_guard", "dependency_install"),
    ("source_tree_mutation_guard", "source_tree_mutation"),
    ("network_access_guard", "network_access"),
    ("external_runtime_guard", "external_runtime"),
    ("backend_start_guard", "backend_start"),
)

LOG_CAPTURES = (
    ("configure_attempt_log_capture", "configure_attempt_log"),
    ("compile_attempt_log_capture", "compile_attempt_log"),
    ("adapter_import_attempt_log_capture", "adapter_import_attempt_log"),
    ("backend_probe_attempt_log_capture", "backend_probe_attempt_log"),
    ("execution_environment_snapshot_log_capture", "execution_environment_snapshot"),
)

BACKEND_DISCOVERY_CAPTURES = (
    ("backend_factory_metadata_capture", "backend_factory_metadata"),
    ("backend_capability_manifest_capture", "backend_capability_manifest"),
    ("backend_healthcheck_trace_capture", "backend_healthcheck_trace"),
    ("backend_failure_trace_capture", "backend_failure_trace"),
)

FAILURE_FIELDS = (
    ("source_missing", "source_availability"),
    ("configure_failed", "source_build"),
    ("compile_failed", "source_build"),
    ("artifact_missing", "source_build"),
    ("adapter_import_failed", "adapter_probe"),
    ("backend_probe_failed", "adapter_probe"),
    ("backend_unavailable", "backend_discovery"),
    ("dependency_mutation_detected", "execution_guard"),
    ("network_access_detected", "execution_guard"),
    ("timeout", "runtime"),
    ("unknown_failure", "runtime"),
)

ALLOWED_CLAIMS = frozenset(
    {"selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized"}
)

CLAIM_CHECKS = (
    (
        "selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized",
        True,
        "M2631 source-build attempt admission adapter-probe attempt admission runtime "
        "guard log capture backend-discovery evidence failure taxonomy actor/action "
        "guard claim-boundary and gate rows",
    ),
    ("dependency_ready_for_execution", False, "future dependency execution readiness audit"),
    ("source_build_attempt_executed", False, "future explicit source build attempt"),
    ("source_build_succeeded", False, "future source build result audit"),
    ("adapter_probe_attempt_executed", False, "future explicit adapter probe attempt"),
    ("adapter_probe_succeeded", False, "future adapter probe result audit"),
    ("backend_discovered", False, "future backend discovery evidence"),
    ("backend_available", False, "future backend availability execution artifact"),
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
    "source_tree_mutation_performed": False,
    "network_access_used": False,
    "actor_input_mutation_performed": False,
    "action_contract_mutation_performed": False,
    "source_build_run": False,
    "source_build_attempt_run": False,
    "adapter_probe_run": False,
    "adapter_probe_attempt_run": False,
    "backend_start_run": False,
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
    "source_build_success_claim_made": False,
    "adapter_probe_execution_claim_made": False,
    "adapter_probe_success_claim_made": False,
    "backend_discovery_claim_made": False,
    "backend_availability_claim_made": False,
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


def materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt(
    output_dir: Path,
    *,
    m2627_summary_path: Path = DEFAULT_M2627_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2627_summary = read_json(m2627_summary_path)

    source_build_rows = build_source_build_execution_attempt_admission_rows(m2627_summary)
    adapter_probe_rows = build_adapter_probe_execution_attempt_admission_rows(m2627_summary)
    guard_rows = build_dependency_runtime_execution_guard_rows()
    log_rows = build_execution_attempt_log_capture_rows(source_build_rows, adapter_probe_rows)
    backend_rows = build_backend_discovery_evidence_capture_rows(adapter_probe_rows)
    failure_rows = build_execution_failure_taxonomy_rows()
    actor_action_guard_rows = build_actor_action_guard_rows()
    claim_rows = build_claim_boundary_checks(
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2627_summary=m2627_summary,
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        guard_rows=guard_rows,
        log_rows=log_rows,
        backend_rows=backend_rows,
        failure_rows=failure_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
        next_blocker=next_blocker,
    )

    source_build_path = output_dir / "hf3_selected_platform_source_build_execution_attempt_admission_rows.csv"
    adapter_probe_path = output_dir / "hf3_selected_platform_adapter_probe_execution_attempt_admission_rows.csv"
    guard_path = output_dir / "hf3_selected_platform_dependency_runtime_execution_guard_rows.csv"
    log_path = output_dir / "hf3_selected_platform_execution_attempt_log_capture_rows.csv"
    backend_path = output_dir / "hf3_selected_platform_backend_discovery_evidence_capture_rows.csv"
    failure_path = output_dir / "hf3_selected_platform_execution_failure_taxonomy_rows.csv"
    actor_action_guard_path = output_dir / "hf3_selected_platform_execution_attempt_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_selected_platform_execution_attempt_claim_boundary_checks.csv"
    gate_path = output_dir / "selected_platform_source_build_adapter_probe_execution_attempt_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(
        source_build_path,
        source_build_rows,
        fieldnames=SOURCE_BUILD_ATTEMPT_ADMISSION_FIELDNAMES,
    )
    write_csv_rows(
        adapter_probe_path,
        adapter_probe_rows,
        fieldnames=ADAPTER_PROBE_ATTEMPT_ADMISSION_FIELDNAMES,
    )
    write_csv_rows(guard_path, guard_rows, fieldnames=DEPENDENCY_RUNTIME_GUARD_FIELDNAMES)
    write_csv_rows(log_path, log_rows, fieldnames=EXECUTION_ATTEMPT_LOG_CAPTURE_FIELDNAMES)
    write_csv_rows(
        backend_path,
        backend_rows,
        fieldnames=BACKEND_DISCOVERY_EVIDENCE_CAPTURE_FIELDNAMES,
    )
    write_csv_rows(
        failure_path,
        failure_rows,
        fieldnames=EXECUTION_FAILURE_TAXONOMY_FIELDNAMES,
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
        m2627_summary=m2627_summary,
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        guard_rows=guard_rows,
        log_rows=log_rows,
        backend_rows=backend_rows,
        failure_rows=failure_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        source_build_path=source_build_path,
        adapter_probe_path=adapter_probe_path,
        guard_path=guard_path,
        log_path=log_path,
        backend_path=backend_path,
        failure_path=failure_path,
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


def build_source_build_execution_attempt_admission_rows(
    m2627_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2627_source_build_adapter_probe_design_evidence_accepted(
        m2627_summary or {}
    )
    return [
        {
            "source_build_attempt_admission_id": attempt_id,
            "command_family": command_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "command_contract_id": command_contract_id,
            "source_tree_required": True,
            "out_of_tree_build_required": True,
            "command_attempt_schema_materialized_in_m2631": True,
            "execution_attempt_allowed_after_m2631_audit": True,
            "source_build_executed_in_m2631": False,
            "source_build_attempt_executed_in_m2631": False,
            "dependency_mutation_allowed_in_m2631": False,
            "network_access_allowed_in_m2631": False,
            "log_capture_required": True,
            "artifact_capture_required": True,
            "actor_visible_allowed": False,
            "status_pass": bool(parent_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for attempt_id, command_family, command_contract_id in SOURCE_BUILD_ATTEMPTS
    ]


def build_adapter_probe_execution_attempt_admission_rows(
    m2627_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2627_source_build_adapter_probe_design_evidence_accepted(
        m2627_summary or {}
    )
    return [
        {
            "adapter_probe_attempt_admission_id": attempt_id,
            "probe_family": probe_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "adapter_probe_contract_id": probe_contract_id,
            "adapter_import_required": True,
            "backend_discovery_required": True,
            "command_attempt_schema_materialized_in_m2631": True,
            "adapter_probe_executed_in_m2631": False,
            "adapter_probe_attempt_executed_in_m2631": False,
            "backend_start_allowed_in_m2631": False,
            "reset_allowed_in_m2631": False,
            "trace_capture_required": True,
            "actor_visible_allowed": False,
            "status_pass": bool(parent_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for attempt_id, probe_family, probe_contract_id in ADAPTER_PROBE_ATTEMPTS
    ]


def build_dependency_runtime_execution_guard_rows() -> list[dict[str, Any]]:
    return [
        {
            "execution_guard_id": guard_id,
            "guard_family": guard_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "external_install_allowed_in_m2631": False,
            "external_import_allowed_in_m2631": False,
            "dependency_mutation_allowed_in_m2631": False,
            "source_tree_mutation_allowed_in_m2631": False,
            "network_access_allowed_in_m2631": False,
            "external_runtime_allowed_in_m2631": False,
            "source_build_execution_allowed_in_m2631": False,
            "adapter_probe_execution_allowed_in_m2631": False,
            "backend_start_allowed_in_m2631": False,
            "actor_visible_allowed": False,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for guard_id, guard_family in EXECUTION_GUARDS
    ]


def build_execution_attempt_log_capture_rows(
    source_build_rows: list[dict[str, Any]] | None = None,
    adapter_probe_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    attempt_rows_pass = _source_build_attempt_rows_pass(
        source_build_rows or []
    ) and _adapter_probe_attempt_rows_pass(adapter_probe_rows or [])
    return [
        {
            "execution_log_capture_id": capture_id,
            "log_family": log_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "required_for_future_execution_attempt_audit": True,
            "command_attempt_schema_materialized_in_m2631": True,
            "source_build_executed_in_m2631": False,
            "adapter_probe_executed_in_m2631": False,
            "log_observed_in_m2631": False,
            "actor_visible_allowed": False,
            "status_pass": bool(attempt_rows_pass),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for capture_id, log_family in LOG_CAPTURES
    ]


def build_backend_discovery_evidence_capture_rows(
    adapter_probe_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    probe_attempt_rows_pass = _adapter_probe_attempt_rows_pass(adapter_probe_rows or [])
    return [
        {
            "backend_discovery_capture_id": capture_id,
            "evidence_family": evidence_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "required_for_future_backend_availability_audit": True,
            "required_for_future_reset_admission": True,
            "backend_discovery_schema_materialized_in_m2631": True,
            "adapter_probe_executed_in_m2631": False,
            "backend_started_in_m2631": False,
            "backend_discovered_claim_allowed_in_m2631": False,
            "backend_availability_claim_allowed_in_m2631": False,
            "reset_execution_allowed_in_m2631": False,
            "evidence_observed_in_m2631": False,
            "actor_visible_allowed": False,
            "status_pass": bool(probe_attempt_rows_pass),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for capture_id, evidence_family in BACKEND_DISCOVERY_CAPTURES
    ]


def build_execution_failure_taxonomy_rows() -> list[dict[str, Any]]:
    return [
        {
            "failure_taxonomy_id": f"{failure_field}_execution_failure_taxonomy",
            "failure_field": failure_field,
            "field_family": field_family,
            "required_for_future_execution_attempt_audit": True,
            "allowed_to_support_failure_classification_after_execution": True,
            "actor_visible_allowed": False,
            "materialized_in_m2631": True,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for failure_field, field_family in FAILURE_FIELDS
    ]


def build_actor_action_guard_rows() -> list[dict[str, Any]]:
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "actor_action_guard_id": f"{route_role_id}_execution_attempt_actor_action_guard",
                "route_role_id": route_role_id,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
                "actor_input_mutation_detected": False,
                "action_contract_mutation_detected": False,
                "hidden_oracle_actor_input_detected": False,
                "metadata_actor_visible": False,
                "status_pass": bool(P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = _execution_attempt_protocol_materialized(
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2631": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2627_summary: dict[str, Any],
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2631"])
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
            "m2627_m2628_m2629_source_build_adapter_probe_design_evidence_accepted",
            "lineage",
            _m2627_source_build_adapter_probe_design_evidence_accepted(m2627_summary),
            (
                f"m2627_status={m2627_summary.get('status_pass')};"
                f"selected={m2627_summary.get('selected_platform_family_in_m2627')};"
                f"source_build={m2627_summary.get('source_build_executed_in_m2627')};"
                f"adapter_probe={m2627_summary.get('adapter_probe_executed_in_m2627')};"
                f"backend={m2627_summary.get('backend_started_in_m2627')}"
            ),
            f"m2627_status=True;selected={SELECTED_PLATFORM_FAMILY};"
            "source_build=False;adapter_probe=False;backend=False",
            "lineage_invalid",
        ),
        (
            "source_build_attempt_admission_rows_pass",
            "contract",
            _source_build_attempt_rows_pass(source_build_rows),
            f"rows={len(source_build_rows)};selected={_selected_platform_family(source_build_rows)}",
            f"rows=2;selected={SELECTED_PLATFORM_FAMILY};attempt=false;network=false",
            "contract_violation",
        ),
        (
            "adapter_probe_attempt_admission_rows_pass",
            "contract",
            _adapter_probe_attempt_rows_pass(adapter_probe_rows),
            f"rows={len(adapter_probe_rows)};selected={_selected_platform_family(adapter_probe_rows)}",
            f"rows=2;selected={SELECTED_PLATFORM_FAMILY};attempt/backend/reset=false",
            "contract_violation",
        ),
        (
            "dependency_runtime_guard_rows_pass",
            "contract",
            _dependency_runtime_guard_rows_pass(guard_rows),
            f"rows={len(guard_rows)}",
            "rows=5;install/import/mutation/network/runtime/build/probe/backend=false",
            "contract_violation",
        ),
        (
            "execution_attempt_log_capture_rows_pass",
            "contract",
            _execution_attempt_log_capture_rows_pass(log_rows),
            f"rows={len(log_rows)}",
            "rows=5;future capture only;source_build/probe/log_observed=false",
            "contract_violation",
        ),
        (
            "backend_discovery_evidence_capture_rows_pass",
            "contract",
            _backend_discovery_evidence_capture_rows_pass(backend_rows),
            f"rows={len(backend_rows)}",
            "rows=4;future capture only;probe/backend/reset/evidence=false",
            "contract_violation",
        ),
        (
            "execution_failure_taxonomy_rows_pass",
            "claim_boundary",
            _execution_failure_taxonomy_rows_pass(failure_rows),
            f"rows={len(failure_rows)}",
            "rows=11;schema only;actor-visible=false",
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
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;protocol_claim_only=true",
            "objective_overfit",
        ),
        (
            "no_install_import_mutation_build_probe_backend_reset_step_action_rollout_replay_or_validation_execution",
            "claim_boundary",
            not _any_forbidden_execution(source_build_rows, adapter_probe_rows, guard_rows, log_rows, backend_rows),
            "install/import/mutation/build/probe/backend/reset/step/action/rollout/replay/validation=false",
            "install/import/mutation/build/probe/backend/reset/step/action/rollout/replay/validation=false",
            "objective_overfit",
        ),
        (
            "execution_readiness_backend_reset_validation_and_performance_forbidden",
            "claim_boundary",
            not _any_execution_readiness_backend_validation_or_performance_claim(claim_rows),
            "readiness/source-build/probe/backend/reset/validation/result/performance=false",
            "readiness/source-build/probe/backend/reset/validation/result/performance=false",
            "objective_overfit",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            _actor_action_guard_preserved(actor_action_guard_rows),
            "P0 72/3 preserved;metadata actor-visible=false",
            "P0 72/3 preserved;metadata actor-visible=false",
            "contract_violation",
        ),
        (
            "m2632_result_audit_handoff_defined",
            "lineage",
            next_blocker == DEFAULT_NEXT_BLOCKER,
            next_blocker,
            DEFAULT_NEXT_BLOCKER,
            "lineage_invalid",
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
    m2627_summary: dict[str, Any],
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    source_build_path: Path,
    adapter_probe_path: Path,
    guard_path: Path,
    log_path: Path,
    backend_path: Path,
    failure_path: Path,
    actor_action_guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2631"])
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS
    )
    gates_all_pass = _all_status_pass(gate_rows)
    protocol_materialized = _execution_attempt_protocol_materialized(
        source_build_rows,
        adapter_probe_rows,
        guard_rows,
        log_rows,
        backend_rows,
        failure_rows,
        actor_action_guard_rows,
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "result_class": (
            "engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_"
            "execution_attempt_protocol_materialization_preflight_pass"
        ),
        "status_pass": bool(gates_all_pass and not forbidden_claim_allowed and protocol_materialized),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2627_status_pass": bool(m2627_summary.get("status_pass")),
        "m2627_materialization_gates_all_pass": bool(
            m2627_summary.get("materialization_gates_all_pass")
        ),
        "m2627_selected_platform_family": m2627_summary.get("selected_platform_family_in_m2627"),
        "m2627_source_build_executed": bool(
            m2627_summary.get("source_build_executed_in_m2627")
        ),
        "m2627_adapter_probe_executed": bool(
            m2627_summary.get("adapter_probe_executed_in_m2627")
        ),
        "m2627_backend_started": bool(m2627_summary.get("backend_started_in_m2627")),
        "m2627_reset_executed": bool(m2627_summary.get("reset_executed_in_m2627")),
        "m2627_validation_protocol_ready": bool(
            m2627_summary.get("validation_protocol_ready_in_m2627")
        ),
        "source_build_attempt_admission_row_count": len(source_build_rows),
        "source_build_attempt_admission_rows_all_pass": _all_status_pass(source_build_rows),
        "adapter_probe_attempt_admission_row_count": len(adapter_probe_rows),
        "adapter_probe_attempt_admission_rows_all_pass": _all_status_pass(adapter_probe_rows),
        "dependency_runtime_guard_row_count": len(guard_rows),
        "dependency_runtime_guard_rows_all_pass": _all_status_pass(guard_rows),
        "execution_attempt_log_capture_row_count": len(log_rows),
        "execution_attempt_log_capture_rows_all_pass": _all_status_pass(log_rows),
        "backend_discovery_evidence_capture_row_count": len(backend_rows),
        "backend_discovery_evidence_capture_rows_all_pass": _all_status_pass(backend_rows),
        "execution_failure_taxonomy_row_count": len(failure_rows),
        "execution_failure_taxonomy_rows_all_pass": _all_status_pass(failure_rows),
        "actor_action_guard_row_count": len(actor_action_guard_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(actor_action_guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": gates_all_pass,
        "selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized_in_m2631": protocol_materialized,
        "selected_platform_family_in_m2631": SELECTED_PLATFORM_FAMILY,
        "forbidden_claim_allowed_in_m2631": forbidden_claim_allowed,
        "external_install_allowed_in_m2631": False,
        "external_import_allowed_in_m2631": False,
        "runtime_execution_allowed_in_m2631": False,
        "dependency_mutation_allowed_in_m2631": False,
        "source_tree_mutation_allowed_in_m2631": False,
        "network_access_allowed_in_m2631": False,
        "source_build_executed_in_m2631": False,
        "source_build_attempt_executed_in_m2631": False,
        "source_build_success_claim_allowed_in_m2631": False,
        "adapter_probe_executed_in_m2631": False,
        "adapter_probe_attempt_executed_in_m2631": False,
        "adapter_probe_success_claim_allowed_in_m2631": False,
        "backend_started_in_m2631": False,
        "backend_discovered_claim_allowed_in_m2631": False,
        "backend_availability_claim_allowed_in_m2631": False,
        "reset_executed_in_m2631": False,
        "environment_step_executed_in_m2631": False,
        "policy_action_executed_in_m2631": False,
        "rollout_executed_in_m2631": False,
        "replay_executed_in_m2631": False,
        "external_validation_execution_allowed_in_m2631": False,
        "validation_protocol_ready_in_m2631": False,
        "validation_admission_granted_in_m2631": False,
        "validation_result_claim_allowed": False,
        "reset_success_claim_allowed_in_m2631": False,
        "rollout_feasibility_claim_allowed_in_m2631": False,
        "driver_performance_claim_allowed_in_m2631": False,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
        "hidden_oracle_actor_input_detected": False,
        "metadata_actor_visible": False,
        "diagnostics_actor_visible": False,
        "taxonomy_label_actor_visible": False,
        "backend_status_actor_visible": False,
        "build_outcome_actor_visible": False,
        "probe_outcome_actor_visible": False,
        "reset_outcome_actor_visible": False,
        "rollout_outcome_actor_visible": False,
        "validation_outcome_actor_visible": False,
        "selected_platform_actor_visible": False,
        "protocol_status_actor_visible": False,
        "actor_input_mutation_detected": False,
        "action_contract_mutation_detected": False,
        "source_build_attempt_admission_rows": str(source_build_path),
        "adapter_probe_attempt_admission_rows": str(adapter_probe_path),
        "dependency_runtime_guard_rows": str(guard_path),
        "execution_attempt_log_capture_rows": str(log_path),
        "backend_discovery_evidence_capture_rows": str(backend_path),
        "execution_failure_taxonomy_rows": str(failure_path),
        "actor_action_guard_rows": str(actor_action_guard_path),
        "claim_boundary_checks": str(claim_path),
        "execution_attempt_gate_matrix": str(gate_path),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# M2631 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Execution Attempt Materialization Preflight

- status: completed
- result_class: `{summary['result_class']}`
- milestone: `{summary['milestone']}`
- summary: `{summary['summary']}`
- next: `{summary['next_blocker']}`

## Materialized Evidence

```text
status_pass: {summary['status_pass']}
source_build_attempt_admission_rows: {summary['source_build_attempt_admission_row_count']}
adapter_probe_attempt_admission_rows: {summary['adapter_probe_attempt_admission_row_count']}
dependency_runtime_guard_rows: {summary['dependency_runtime_guard_row_count']}
execution_attempt_log_capture_rows: {summary['execution_attempt_log_capture_row_count']}
backend_discovery_evidence_capture_rows: {summary['backend_discovery_evidence_capture_row_count']}
execution_failure_taxonomy_rows: {summary['execution_failure_taxonomy_row_count']}
actor_action_guard_rows: {summary['actor_action_guard_row_count']}
claim_boundary_rows: {summary['claim_boundary_check_count']}
materialization_gates: {summary['materialization_gate_count']}
selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized_in_m2631: {summary['selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized_in_m2631']}
selected_platform_family_in_m2631: {summary['selected_platform_family_in_m2631']}
external_install_allowed_in_m2631: {summary['external_install_allowed_in_m2631']}
external_import_allowed_in_m2631: {summary['external_import_allowed_in_m2631']}
runtime_execution_allowed_in_m2631: {summary['runtime_execution_allowed_in_m2631']}
dependency_mutation_allowed_in_m2631: {summary['dependency_mutation_allowed_in_m2631']}
source_tree_mutation_allowed_in_m2631: {summary['source_tree_mutation_allowed_in_m2631']}
network_access_allowed_in_m2631: {summary['network_access_allowed_in_m2631']}
source_build_executed_in_m2631: {summary['source_build_executed_in_m2631']}
source_build_attempt_executed_in_m2631: {summary['source_build_attempt_executed_in_m2631']}
adapter_probe_executed_in_m2631: {summary['adapter_probe_executed_in_m2631']}
adapter_probe_attempt_executed_in_m2631: {summary['adapter_probe_attempt_executed_in_m2631']}
backend_started_in_m2631: {summary['backend_started_in_m2631']}
backend_discovered_claim_allowed_in_m2631: {summary['backend_discovered_claim_allowed_in_m2631']}
backend_availability_claim_allowed_in_m2631: {summary['backend_availability_claim_allowed_in_m2631']}
reset_executed_in_m2631: {summary['reset_executed_in_m2631']}
environment_step_executed_in_m2631: {summary['environment_step_executed_in_m2631']}
policy_action_executed_in_m2631: {summary['policy_action_executed_in_m2631']}
rollout_executed_in_m2631: {summary['rollout_executed_in_m2631']}
replay_executed_in_m2631: {summary['replay_executed_in_m2631']}
external_validation_execution_allowed_in_m2631: {summary['external_validation_execution_allowed_in_m2631']}
validation_protocol_ready_in_m2631: {summary['validation_protocol_ready_in_m2631']}
validation_admission_granted_in_m2631: {summary['validation_admission_granted_in_m2631']}
validation_result_claim_allowed: {summary['validation_result_claim_allowed']}
reset_success_claim_allowed_in_m2631: {summary['reset_success_claim_allowed_in_m2631']}
rollout_feasibility_claim_allowed_in_m2631: {summary['rollout_feasibility_claim_allowed_in_m2631']}
driver_performance_claim_allowed_in_m2631: {summary['driver_performance_claim_allowed_in_m2631']}
actor contract: P0 observation {summary['observation_shape']} / action {summary['action_shape']}
```

## Artifact Paths

- source-build execution attempt admission rows: `{summary['source_build_attempt_admission_rows']}`
- adapter-probe execution attempt admission rows: `{summary['adapter_probe_attempt_admission_rows']}`
- dependency/runtime guard rows: `{summary['dependency_runtime_guard_rows']}`
- execution-attempt log capture rows: `{summary['execution_attempt_log_capture_rows']}`
- backend-discovery evidence capture rows: `{summary['backend_discovery_evidence_capture_rows']}`
- execution failure taxonomy rows: `{summary['execution_failure_taxonomy_rows']}`
- actor/action guard rows: `{summary['actor_action_guard_rows']}`
- claim-boundary rows: `{summary['claim_boundary_checks']}`
- gate matrix: `{summary['execution_attempt_gate_matrix']}`

## Supported Claims

Supported:

- selected-platform source-build/adapter-probe execution-attempt protocol artifacts are materialized
- command attempt/admission, runtime guard, future log/evidence capture, failure taxonomy, actor/action, claim-boundary, and gate rows are materialized
- selected platform family remains `chrono_vehicle_or_equivalent_open_backend`
- P0 `72/3` actor/action contract is preserved

## Rejected Claims

Rejected:

- dependency ready for execution
- source build attempted, executed, or succeeded
- adapter probe attempted, executed, or succeeded
- backend discovery or backend availability
- reset executed or reset success
- policy action, environment step, rollout, replay, or validation executed
- rollout feasibility
- validation protocol readiness
- validation admission
- validation readiness or result
- external validation execution
- high-fidelity validation readiness or result
- controller ranking, success-rate verdict, winner selection, or checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

## Boundary

M2631 is a static source-build/adapter-probe execution-attempt protocol
materialization preflight. It does not execute source build, adapter probe,
backend start, reset, policy action, environment step, rollout, replay,
validation, training, ranking, promotion, or any high-fidelity simulator.
Execution-attempt failure taxonomy rows and backend-discovery evidence rows are
future audit schema and are not actor-visible.
"""
    path.write_text(text, encoding="utf-8")


def _m2627_source_build_adapter_probe_design_evidence_accepted(
    summary: dict[str, Any],
) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627")
        and summary.get("selected_platform_family_in_m2627") == SELECTED_PLATFORM_FAMILY
        and not summary.get("source_build_executed_in_m2627")
        and not summary.get("adapter_probe_executed_in_m2627")
        and not summary.get("backend_started_in_m2627")
        and not summary.get("reset_executed_in_m2627")
        and not summary.get("validation_protocol_ready_in_m2627")
    )


def _source_build_attempt_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 2
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and all(row["source_tree_required"] for row in rows)
        and all(row["out_of_tree_build_required"] for row in rows)
        and all(row["command_attempt_schema_materialized_in_m2631"] for row in rows)
        and all(row["execution_attempt_allowed_after_m2631_audit"] for row in rows)
        and not any(_boolish(row["source_build_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["source_build_attempt_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["network_access_allowed_in_m2631"]) for row in rows)
        and all(row["log_capture_required"] for row in rows)
        and all(row["artifact_capture_required"] for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _adapter_probe_attempt_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 2
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and all(row["adapter_import_required"] for row in rows)
        and all(row["backend_discovery_required"] for row in rows)
        and all(row["command_attempt_schema_materialized_in_m2631"] for row in rows)
        and not any(_boolish(row["adapter_probe_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["adapter_probe_attempt_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["backend_start_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["reset_allowed_in_m2631"]) for row in rows)
        and all(row["trace_capture_required"] for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _dependency_runtime_guard_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 5
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and not any(_boolish(row["external_install_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["external_import_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["source_tree_mutation_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["network_access_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["external_runtime_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["source_build_execution_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["adapter_probe_execution_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["backend_start_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _execution_attempt_log_capture_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 5
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and all(row["required_for_future_execution_attempt_audit"] for row in rows)
        and all(row["command_attempt_schema_materialized_in_m2631"] for row in rows)
        and not any(_boolish(row["source_build_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["adapter_probe_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["log_observed_in_m2631"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _backend_discovery_evidence_capture_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 4
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and all(row["required_for_future_backend_availability_audit"] for row in rows)
        and all(row["required_for_future_reset_admission"] for row in rows)
        and all(row["backend_discovery_schema_materialized_in_m2631"] for row in rows)
        and not any(_boolish(row["adapter_probe_executed_in_m2631"]) for row in rows)
        and not any(_boolish(row["backend_started_in_m2631"]) for row in rows)
        and not any(_boolish(row["backend_discovered_claim_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["backend_availability_claim_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["reset_execution_allowed_in_m2631"]) for row in rows)
        and not any(_boolish(row["evidence_observed_in_m2631"]) for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _execution_failure_taxonomy_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == len(FAILURE_FIELDS)
        and _all_status_pass(rows)
        and all(row["required_for_future_execution_attempt_audit"] for row in rows)
        and all(row["allowed_to_support_failure_classification_after_execution"] for row in rows)
        and all(row["materialized_in_m2631"] for row in rows)
        and not any(_boolish(row["actor_visible_allowed"]) for row in rows)
    )


def _actor_action_guard_preserved(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 2
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and {row["actor_observation_shape"] for row in rows} == {P0_OBSERVATION_DIM}
        and {row["action_shape"] for row in rows} == {ACTION_DIM}
        and {row["deployed_action_mapping"] for row in rows} == {DEPLOYED_ACTION_MAPPING}
        and not any(_boolish(row["actor_input_mutation_detected"]) for row in rows)
        and not any(_boolish(row["action_contract_mutation_detected"]) for row in rows)
        and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in rows)
        and not any(_boolish(row["metadata_actor_visible"]) for row in rows)
    )


def _execution_attempt_protocol_materialized(
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _source_build_attempt_rows_pass(source_build_rows)
        and _adapter_probe_attempt_rows_pass(adapter_probe_rows)
        and _dependency_runtime_guard_rows_pass(guard_rows)
        and _execution_attempt_log_capture_rows_pass(log_rows)
        and _backend_discovery_evidence_capture_rows_pass(backend_rows)
        and _execution_failure_taxonomy_rows_pass(failure_rows)
        and _actor_action_guard_preserved(actor_action_guard_rows)
    )


def _any_forbidden_execution(
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
) -> bool:
    return any(
        [
            any(_boolish(row["source_build_executed_in_m2631"]) for row in source_build_rows),
            any(_boolish(row["source_build_attempt_executed_in_m2631"]) for row in source_build_rows),
            any(_boolish(row["dependency_mutation_allowed_in_m2631"]) for row in source_build_rows),
            any(_boolish(row["network_access_allowed_in_m2631"]) for row in source_build_rows),
            any(_boolish(row["adapter_probe_executed_in_m2631"]) for row in adapter_probe_rows),
            any(_boolish(row["adapter_probe_attempt_executed_in_m2631"]) for row in adapter_probe_rows),
            any(_boolish(row["backend_start_allowed_in_m2631"]) for row in adapter_probe_rows),
            any(_boolish(row["reset_allowed_in_m2631"]) for row in adapter_probe_rows),
            any(
                _boolish(row[column])
                for row in guard_rows
                for column in [
                    "external_install_allowed_in_m2631",
                    "external_import_allowed_in_m2631",
                    "dependency_mutation_allowed_in_m2631",
                    "source_tree_mutation_allowed_in_m2631",
                    "network_access_allowed_in_m2631",
                    "external_runtime_allowed_in_m2631",
                    "source_build_execution_allowed_in_m2631",
                    "adapter_probe_execution_allowed_in_m2631",
                    "backend_start_allowed_in_m2631",
                ]
            ),
            any(_boolish(row["source_build_executed_in_m2631"]) for row in log_rows),
            any(_boolish(row["adapter_probe_executed_in_m2631"]) for row in log_rows),
            any(_boolish(row["log_observed_in_m2631"]) for row in log_rows),
            any(_boolish(row["adapter_probe_executed_in_m2631"]) for row in backend_rows),
            any(_boolish(row["backend_started_in_m2631"]) for row in backend_rows),
            any(_boolish(row["backend_discovered_claim_allowed_in_m2631"]) for row in backend_rows),
            any(_boolish(row["backend_availability_claim_allowed_in_m2631"]) for row in backend_rows),
            any(_boolish(row["reset_execution_allowed_in_m2631"]) for row in backend_rows),
            any(_boolish(row["evidence_observed_in_m2631"]) for row in backend_rows),
        ]
    )


def _any_execution_readiness_backend_validation_or_performance_claim(
    claim_rows: list[dict[str, Any]],
) -> bool:
    forbidden = {
        "dependency_ready_for_execution",
        "source_build_attempt_executed",
        "source_build_succeeded",
        "adapter_probe_attempt_executed",
        "adapter_probe_succeeded",
        "backend_discovered",
        "backend_available",
        "reset_executed",
        "reset_success",
        "policy_action_executed",
        "environment_step_executed",
        "rollout_executed",
        "rollout_feasibility",
        "replay_executed",
        "validation_protocol_readiness",
        "validation_admission",
        "external_validation_execution",
        "validation_readiness",
        "validation_result",
        "high_fidelity_validation_readiness",
        "high_fidelity_validation_result",
        "driver_performance",
        "controller_family_ranking",
        "winner_selection",
        "success_rate",
        "checkpoint_promotion",
        "current_sim_verdict",
        "paper_level_evidence",
        "finite_window_vs_gru",
        "level3_self_identification",
    }
    return any(
        row["claim_family"] in forbidden and _boolish(row["claim_allowed_in_m2631"])
        for row in claim_rows
    )


def _selected_platform_family(rows: list[dict[str, Any]]) -> str | None:
    selected = {row.get("selected_platform_family") for row in rows}
    if len(selected) == 1:
        return next(iter(selected))
    return None


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2627-summary", type=Path, default=DEFAULT_M2627_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args()

    summary = materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt(
        args.output_dir,
        m2627_summary_path=args.m2627_summary,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")


if __name__ == "__main__":
    main()
