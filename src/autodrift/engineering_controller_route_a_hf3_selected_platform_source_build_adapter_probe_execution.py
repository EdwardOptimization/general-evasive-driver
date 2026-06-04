"""Route A HF3 selected-platform source-build/adapter-probe materialization.

This module only materializes static source-build/adapter-probe execution design
artifacts. It does not install, import, build, probe, start a backend, reset,
step, roll out, replay, validate, train, rank, or promote any backend.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-execution-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2628-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-execution-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-execution-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution"
)
DEFAULT_M2623_SUMMARY = Path(
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/"
    "summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"
DEPLOYED_ACTION_MAPPING = "[steer, throttle, brake]"

SOURCE_ARTIFACTS = (
    "docs/m2626-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-design.md",
    "docs/m2625-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-synthesis.md",
    "docs/m2624-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-audit.md",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/summary.json",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_backend_availability_fixture_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_invocation_dry_run_contract_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_request_binding_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_actor_view_after_reset_extraction_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_outcome_audit_schema_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_execution_actor_action_guard_rows.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_execution_readiness_claim_boundary_checks.csv",
    "runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/selected_platform_reset_execution_readiness_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
    "docs/self-id-go-no-go-paper-route-plan.md",
    "docs/paper-route-finite-window-vs-gru-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform source-build/adapter-probe execution design "
    "materialization only; command contracts isolation guards future artifact/trace "
    "capture contracts outcome taxonomy actor/action guard claim-boundary and gate "
    "panels may be materialized for the selected open/auditable platform family; "
    "not dependency execution readiness, source build execution, adapter probe "
    "execution, backend availability, reset execution, reset success, rollout "
    "feasibility, replay execution, validation protocol readiness, validation "
    "admission, external validation execution, high-fidelity validation "
    "readiness/result, ranking, driver performance, paper, FW-vs-GRU, current-sim "
    "verdict, high-fidelity validation, or self-ID"
)

SOURCE_BUILD_COMMAND_CONTRACT_FIELDNAMES = [
    "command_contract_id",
    "command_family",
    "selected_platform_family",
    "source_tree_required",
    "out_of_tree_build_required",
    "dependency_mutation_allowed_in_m2627",
    "network_access_allowed_in_m2627",
    "build_execution_allowed_in_m2627",
    "log_capture_required",
    "artifact_capture_required",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

ADAPTER_PROBE_COMMAND_CONTRACT_FIELDNAMES = [
    "adapter_probe_contract_id",
    "probe_family",
    "selected_platform_family",
    "adapter_import_required",
    "backend_discovery_required",
    "backend_start_allowed_in_m2627",
    "reset_allowed_in_m2627",
    "adapter_probe_execution_allowed_in_m2627",
    "trace_capture_required",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_ENVIRONMENT_ISOLATION_GUARD_FIELDNAMES = [
    "isolation_guard_id",
    "guard_family",
    "selected_platform_family",
    "external_install_allowed_in_m2627",
    "external_import_allowed_in_m2627",
    "dependency_mutation_allowed_in_m2627",
    "source_tree_mutation_allowed_in_m2627",
    "network_access_allowed_in_m2627",
    "external_runtime_allowed_in_m2627",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

SOURCE_BUILD_ARTIFACT_CAPTURE_FIELDNAMES = [
    "artifact_capture_id",
    "artifact_family",
    "selected_platform_family",
    "required_for_future_source_build_audit",
    "required_for_future_adapter_probe_admission",
    "materialized_in_m2627",
    "source_build_executed_in_m2627",
    "artifact_observed_in_m2627",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

ADAPTER_PROBE_TRACE_CAPTURE_FIELDNAMES = [
    "trace_capture_id",
    "trace_family",
    "selected_platform_family",
    "required_for_future_adapter_probe_audit",
    "required_for_future_reset_execution_admission",
    "materialized_in_m2627",
    "adapter_probe_executed_in_m2627",
    "backend_started_in_m2627",
    "trace_observed_in_m2627",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

OUTCOME_TAXONOMY_FIELDNAMES = [
    "outcome_taxonomy_id",
    "outcome_field",
    "field_family",
    "required_for_future_source_build_adapter_probe_audit",
    "allowed_to_support_backend_availability_after_execution",
    "allowed_to_support_reset_execution_admission_after_execution",
    "actor_visible_allowed",
    "materialized_in_m2627",
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
    "claim_allowed_in_m2627",
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

SOURCE_BUILD_COMMANDS = (
    ("selected_platform_source_build_configure_command_contract", "configure"),
    ("selected_platform_source_build_compile_command_contract", "compile"),
)

ADAPTER_PROBE_COMMANDS = (
    ("selected_platform_adapter_import_probe_contract", "adapter_import"),
    ("selected_platform_adapter_backend_probe_contract", "backend_probe"),
)

ISOLATION_GUARDS = (
    ("dependency_install_guard", "dependency_install"),
    ("source_tree_mutation_guard", "source_tree_mutation"),
    ("network_access_guard", "network_access"),
    ("external_runtime_guard", "external_runtime"),
)

SOURCE_BUILD_ARTIFACTS = (
    ("configure_log_capture", "configure_log"),
    ("compile_log_capture", "compile_log"),
    ("build_artifact_manifest_capture", "build_artifact_manifest"),
    ("build_environment_snapshot_capture", "build_environment_snapshot"),
)

ADAPTER_PROBE_TRACES = (
    ("adapter_import_trace_capture", "adapter_import_trace"),
    ("backend_factory_trace_capture", "backend_factory_trace"),
    ("backend_capability_trace_capture", "backend_capability_trace"),
    ("adapter_failure_trace_capture", "adapter_failure_trace"),
)

OUTCOME_FIELDS = (
    ("source_available", "source_status"),
    ("configure_attempted", "source_build_status"),
    ("compile_attempted", "source_build_status"),
    ("build_artifact_available", "build_artifact_status"),
    ("adapter_import_attempted", "adapter_probe_status"),
    ("adapter_probe_attempted", "adapter_probe_status"),
    ("backend_discovered", "backend_status"),
    ("probe_status", "probe_status"),
    ("failure_reason", "audit_metadata"),
    ("execution_timestamp", "audit_metadata"),
)

ALLOWED_CLAIMS = frozenset(
    {"selected_platform_source_build_adapter_probe_execution_design_materialized"}
)

CLAIM_CHECKS = (
    (
        "selected_platform_source_build_adapter_probe_execution_design_materialized",
        True,
        "M2627 source-build command contract adapter-probe command contract isolation "
        "guard source-build artifact capture adapter-probe trace capture outcome "
        "taxonomy actor/action guard claim-boundary and gate rows",
    ),
    ("dependency_ready_for_execution", False, "future dependency execution readiness audit"),
    ("source_build_executed", False, "future explicit source build execution"),
    ("adapter_probe_executed", False, "future explicit adapter probe execution"),
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
    "adapter_probe_run": False,
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
    "adapter_probe_execution_claim_made": False,
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


def materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution(
    output_dir: Path,
    *,
    m2623_summary_path: Path = DEFAULT_M2623_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2623_summary = read_json(m2623_summary_path)

    source_build_rows = build_source_build_command_contract_rows(m2623_summary)
    adapter_probe_rows = build_adapter_probe_command_contract_rows(m2623_summary)
    isolation_rows = build_dependency_environment_isolation_guard_rows()
    artifact_rows = build_source_build_artifact_capture_rows(source_build_rows)
    trace_rows = build_adapter_probe_trace_capture_rows(adapter_probe_rows)
    outcome_rows = build_source_build_adapter_probe_outcome_taxonomy_rows()
    actor_action_guard_rows = build_actor_action_guard_rows()
    claim_rows = build_claim_boundary_checks(
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2623_summary=m2623_summary,
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        isolation_rows=isolation_rows,
        artifact_rows=artifact_rows,
        trace_rows=trace_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
    )

    source_build_path = output_dir / "hf3_selected_platform_source_build_command_contract_rows.csv"
    adapter_probe_path = output_dir / "hf3_selected_platform_adapter_probe_command_contract_rows.csv"
    isolation_path = (
        output_dir / "hf3_selected_platform_dependency_environment_isolation_guard_rows.csv"
    )
    artifact_path = output_dir / "hf3_selected_platform_source_build_artifact_capture_rows.csv"
    trace_path = output_dir / "hf3_selected_platform_adapter_probe_trace_capture_rows.csv"
    outcome_path = (
        output_dir / "hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows.csv"
    )
    actor_action_guard_path = (
        output_dir / "hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows.csv"
    )
    claim_path = (
        output_dir / "hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks.csv"
    )
    gate_path = output_dir / "selected_platform_source_build_adapter_probe_execution_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(
        source_build_path,
        source_build_rows,
        fieldnames=SOURCE_BUILD_COMMAND_CONTRACT_FIELDNAMES,
    )
    write_csv_rows(
        adapter_probe_path,
        adapter_probe_rows,
        fieldnames=ADAPTER_PROBE_COMMAND_CONTRACT_FIELDNAMES,
    )
    write_csv_rows(
        isolation_path,
        isolation_rows,
        fieldnames=DEPENDENCY_ENVIRONMENT_ISOLATION_GUARD_FIELDNAMES,
    )
    write_csv_rows(
        artifact_path,
        artifact_rows,
        fieldnames=SOURCE_BUILD_ARTIFACT_CAPTURE_FIELDNAMES,
    )
    write_csv_rows(trace_path, trace_rows, fieldnames=ADAPTER_PROBE_TRACE_CAPTURE_FIELDNAMES)
    write_csv_rows(outcome_path, outcome_rows, fieldnames=OUTCOME_TAXONOMY_FIELDNAMES)
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
        m2623_summary=m2623_summary,
        source_build_rows=source_build_rows,
        adapter_probe_rows=adapter_probe_rows,
        isolation_rows=isolation_rows,
        artifact_rows=artifact_rows,
        trace_rows=trace_rows,
        outcome_rows=outcome_rows,
        actor_action_guard_rows=actor_action_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        source_build_path=source_build_path,
        adapter_probe_path=adapter_probe_path,
        isolation_path=isolation_path,
        artifact_path=artifact_path,
        trace_path=trace_path,
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


def build_source_build_command_contract_rows(
    m2623_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2623_reset_execution_readiness_evidence_accepted(
        m2623_summary or {}
    )
    return [
        {
            "command_contract_id": command_id,
            "command_family": command_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "source_tree_required": True,
            "out_of_tree_build_required": True,
            "dependency_mutation_allowed_in_m2627": False,
            "network_access_allowed_in_m2627": False,
            "build_execution_allowed_in_m2627": False,
            "log_capture_required": True,
            "artifact_capture_required": True,
            "actor_visible_allowed": False,
            "status_pass": bool(parent_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for command_id, command_family in SOURCE_BUILD_COMMANDS
    ]


def build_adapter_probe_command_contract_rows(
    m2623_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2623_reset_execution_readiness_evidence_accepted(
        m2623_summary or {}
    )
    return [
        {
            "adapter_probe_contract_id": probe_id,
            "probe_family": probe_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "adapter_import_required": True,
            "backend_discovery_required": True,
            "backend_start_allowed_in_m2627": False,
            "reset_allowed_in_m2627": False,
            "adapter_probe_execution_allowed_in_m2627": False,
            "trace_capture_required": True,
            "actor_visible_allowed": False,
            "status_pass": bool(parent_accepted),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for probe_id, probe_family in ADAPTER_PROBE_COMMANDS
    ]


def build_dependency_environment_isolation_guard_rows() -> list[dict[str, Any]]:
    return [
        {
            "isolation_guard_id": guard_id,
            "guard_family": guard_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "external_install_allowed_in_m2627": False,
            "external_import_allowed_in_m2627": False,
            "dependency_mutation_allowed_in_m2627": False,
            "source_tree_mutation_allowed_in_m2627": False,
            "network_access_allowed_in_m2627": False,
            "external_runtime_allowed_in_m2627": False,
            "actor_visible_allowed": False,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for guard_id, guard_family in ISOLATION_GUARDS
    ]


def build_source_build_artifact_capture_rows(
    source_build_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    command_contracts_pass = _source_build_command_contracts_pass(
        source_build_rows or []
    )
    return [
        {
            "artifact_capture_id": artifact_id,
            "artifact_family": artifact_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "required_for_future_source_build_audit": True,
            "required_for_future_adapter_probe_admission": True,
            "materialized_in_m2627": True,
            "source_build_executed_in_m2627": False,
            "artifact_observed_in_m2627": False,
            "actor_visible_allowed": False,
            "status_pass": bool(command_contracts_pass),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, artifact_family in SOURCE_BUILD_ARTIFACTS
    ]


def build_adapter_probe_trace_capture_rows(
    adapter_probe_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    probe_contracts_pass = _adapter_probe_command_contracts_pass(
        adapter_probe_rows or []
    )
    return [
        {
            "trace_capture_id": trace_id,
            "trace_family": trace_family,
            "selected_platform_family": SELECTED_PLATFORM_FAMILY,
            "required_for_future_adapter_probe_audit": True,
            "required_for_future_reset_execution_admission": True,
            "materialized_in_m2627": True,
            "adapter_probe_executed_in_m2627": False,
            "backend_started_in_m2627": False,
            "trace_observed_in_m2627": False,
            "actor_visible_allowed": False,
            "status_pass": bool(probe_contracts_pass),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for trace_id, trace_family in ADAPTER_PROBE_TRACES
    ]


def build_source_build_adapter_probe_outcome_taxonomy_rows() -> list[dict[str, Any]]:
    return [
        {
            "outcome_taxonomy_id": f"{outcome_field}_source_build_adapter_probe_outcome_taxonomy",
            "outcome_field": outcome_field,
            "field_family": field_family,
            "required_for_future_source_build_adapter_probe_audit": True,
            "allowed_to_support_backend_availability_after_execution": True,
            "allowed_to_support_reset_execution_admission_after_execution": True,
            "actor_visible_allowed": False,
            "materialized_in_m2627": True,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for outcome_field, field_family in OUTCOME_FIELDS
    ]


def build_actor_action_guard_rows() -> list[dict[str, Any]]:
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "actor_action_guard_id": (
                    f"{route_role_id}_source_build_adapter_probe_actor_action_guard"
                ),
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
    isolation_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = _source_build_adapter_probe_execution_design_materialized(
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
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
                "claim_allowed_in_m2627": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2623_summary: dict[str, Any],
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    isolation_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2627"])
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
            "m2623_m2624_m2625_reset_execution_readiness_evidence_accepted",
            "lineage",
            _m2623_reset_execution_readiness_evidence_accepted(m2623_summary),
            (
                f"m2623_status={m2623_summary.get('status_pass')};"
                f"selected={m2623_summary.get('selected_platform_family_in_m2623')};"
                f"source_build={m2623_summary.get('source_build_executed_in_m2623')};"
                f"adapter_probe={m2623_summary.get('adapter_probe_executed_in_m2623')};"
                f"reset={m2623_summary.get('reset_executed_in_m2623')}"
            ),
            f"m2623_status=True;selected={SELECTED_PLATFORM_FAMILY};"
            "source_build=False;adapter_probe=False;reset=False",
            "lineage_invalid",
        ),
        (
            "source_build_command_contract_rows_pass",
            "contract",
            _source_build_command_contracts_pass(source_build_rows),
            f"rows={len(source_build_rows)};selected={_selected_platform_family(source_build_rows)}",
            f"rows=2;selected={SELECTED_PLATFORM_FAMILY};build=false;network=false",
            "contract_violation",
        ),
        (
            "adapter_probe_command_contract_rows_pass",
            "contract",
            _adapter_probe_command_contracts_pass(adapter_probe_rows),
            f"rows={len(adapter_probe_rows)};selected={_selected_platform_family(adapter_probe_rows)}",
            f"rows=2;selected={SELECTED_PLATFORM_FAMILY};probe/backend/reset=false",
            "contract_violation",
        ),
        (
            "dependency_environment_isolation_guard_rows_pass",
            "contract",
            _isolation_guards_pass(isolation_rows),
            f"rows={len(isolation_rows)}",
            "rows=4;install/import/mutation/network/runtime=false",
            "contract_violation",
        ),
        (
            "source_build_artifact_capture_rows_pass",
            "contract",
            _source_build_artifact_capture_rows_pass(artifact_rows),
            f"rows={len(artifact_rows)}",
            "rows=4;future capture only;source_build=false;observed=false",
            "contract_violation",
        ),
        (
            "adapter_probe_trace_capture_rows_pass",
            "contract",
            _adapter_probe_trace_capture_rows_pass(trace_rows),
            f"rows={len(trace_rows)}",
            "rows=4;future trace only;adapter_probe/backend=false;observed=false",
            "contract_violation",
        ),
        (
            "outcome_taxonomy_rows_pass",
            "claim_boundary",
            _outcome_taxonomy_rows_pass(outcome_rows),
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
            "no_install_import_mutation_build_probe_reset_step_action_rollout_replay_or_validation_execution",
            "claim_boundary",
            not _any_forbidden_execution(
                source_build_rows,
                adapter_probe_rows,
                isolation_rows,
                artifact_rows,
                trace_rows,
            ),
            "install/import/mutation/build/probe/backend/reset/step/action/rollout/replay/validation=false",
            "install/import/mutation/build/probe/backend/reset/step/action/rollout/replay/validation=false",
            "objective_overfit",
        ),
        (
            "source_build_adapter_probe_reset_validation_and_performance_forbidden",
            "claim_boundary",
            not _any_execution_readiness_or_performance_claim(claim_rows),
            "source-build/adapter-probe/backend/reset/validation/readiness/result/performance=false",
            "source-build/adapter-probe/backend/reset/validation/readiness/result/performance=false",
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
    m2623_summary: dict[str, Any],
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    isolation_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    source_build_path: Path,
    adapter_probe_path: Path,
    isolation_path: Path,
    artifact_path: Path,
    trace_path: Path,
    outcome_path: Path,
    actor_action_guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2627"])
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS
    )
    materialized = _source_build_adapter_probe_execution_design_materialized(
        source_build_rows,
        adapter_probe_rows,
        isolation_rows,
        artifact_rows,
        trace_rows,
        outcome_rows,
        actor_action_guard_rows,
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_"
            "execution_design_materialization_preflight_pass"
        ),
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_selected_platform_source_build_command_contract_rows": str(source_build_path),
        "hf3_selected_platform_adapter_probe_command_contract_rows": str(adapter_probe_path),
        "hf3_selected_platform_dependency_environment_isolation_guard_rows": str(
            isolation_path
        ),
        "hf3_selected_platform_source_build_artifact_capture_rows": str(artifact_path),
        "hf3_selected_platform_adapter_probe_trace_capture_rows": str(trace_path),
        "hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows": str(
            outcome_path
        ),
        "hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows": str(
            actor_action_guard_path
        ),
        "hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks": str(
            claim_path
        ),
        "selected_platform_source_build_adapter_probe_execution_gate_matrix": str(
            gate_path
        ),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2623_status_pass": bool(m2623_summary.get("status_pass")),
        "m2623_materialization_gates_all_pass": bool(
            m2623_summary.get("materialization_gates_all_pass")
        ),
        "m2623_selected_platform_family": m2623_summary.get("selected_platform_family_in_m2623"),
        "m2623_reset_execution_readiness_design_materialized": bool(
            m2623_summary.get(
                "selected_platform_reset_execution_readiness_design_materialized_in_m2623"
            )
        ),
        "m2623_source_build_executed": bool(
            m2623_summary.get("source_build_executed_in_m2623")
        ),
        "m2623_adapter_probe_executed": bool(
            m2623_summary.get("adapter_probe_executed_in_m2623")
        ),
        "m2623_reset_executed": bool(m2623_summary.get("reset_executed_in_m2623")),
        "m2623_validation_protocol_ready": bool(
            m2623_summary.get("validation_protocol_ready_in_m2623")
        ),
        "source_build_command_contract_row_count": len(source_build_rows),
        "source_build_command_contract_rows_all_pass": _all_status_pass(source_build_rows),
        "adapter_probe_command_contract_row_count": len(adapter_probe_rows),
        "adapter_probe_command_contract_rows_all_pass": _all_status_pass(adapter_probe_rows),
        "dependency_environment_isolation_guard_row_count": len(isolation_rows),
        "dependency_environment_isolation_guard_rows_all_pass": _all_status_pass(isolation_rows),
        "source_build_artifact_capture_row_count": len(artifact_rows),
        "source_build_artifact_capture_rows_all_pass": _all_status_pass(artifact_rows),
        "adapter_probe_trace_capture_row_count": len(trace_rows),
        "adapter_probe_trace_capture_rows_all_pass": _all_status_pass(trace_rows),
        "outcome_taxonomy_row_count": len(outcome_rows),
        "outcome_taxonomy_rows_all_pass": _all_status_pass(outcome_rows),
        "actor_action_guard_row_count": len(actor_action_guard_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(actor_action_guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627": bool(
            materialized
        ),
        "selected_platform_family_in_m2627": SELECTED_PLATFORM_FAMILY,
        "forbidden_claim_allowed_in_m2627": bool(forbidden_claim_allowed),
        "external_install_allowed_in_m2627": False,
        "external_import_allowed_in_m2627": False,
        "runtime_execution_allowed_in_m2627": False,
        "dependency_mutation_allowed_in_m2627": False,
        "source_tree_mutation_allowed_in_m2627": False,
        "network_access_allowed_in_m2627": False,
        "source_build_executed_in_m2627": False,
        "adapter_probe_executed_in_m2627": False,
        "backend_started_in_m2627": False,
        "reset_executed_in_m2627": False,
        "environment_step_executed_in_m2627": False,
        "policy_action_executed_in_m2627": False,
        "rollout_executed_in_m2627": False,
        "replay_executed_in_m2627": False,
        "external_validation_execution_allowed_in_m2627": False,
        "validation_protocol_ready_in_m2627": False,
        "validation_admission_granted_in_m2627": False,
        "validation_result_claim_allowed": False,
        "backend_availability_claim_allowed_in_m2627": False,
        "reset_success_claim_allowed_in_m2627": False,
        "rollout_feasibility_claim_allowed_in_m2627": False,
        "driver_performance_claim_allowed_in_m2627": False,
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
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2627 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Execution Materialization Preflight",
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
                f"source_build_command_contract_rows: {summary['source_build_command_contract_row_count']}",
                f"adapter_probe_command_contract_rows: {summary['adapter_probe_command_contract_row_count']}",
                f"dependency_environment_isolation_guard_rows: {summary['dependency_environment_isolation_guard_row_count']}",
                f"source_build_artifact_capture_rows: {summary['source_build_artifact_capture_row_count']}",
                f"adapter_probe_trace_capture_rows: {summary['adapter_probe_trace_capture_row_count']}",
                f"outcome_taxonomy_rows: {summary['outcome_taxonomy_row_count']}",
                f"actor_action_guard_rows: {summary['actor_action_guard_row_count']}",
                f"claim_boundary_rows: {summary['claim_boundary_check_count']}",
                f"materialization_gates: {summary['materialization_gate_count']}",
                "selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627: "
                f"{summary['selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627']}",
                f"selected_platform_family_in_m2627: {summary['selected_platform_family_in_m2627']}",
                f"external_install_allowed_in_m2627: {summary['external_install_allowed_in_m2627']}",
                f"external_import_allowed_in_m2627: {summary['external_import_allowed_in_m2627']}",
                f"runtime_execution_allowed_in_m2627: {summary['runtime_execution_allowed_in_m2627']}",
                f"dependency_mutation_allowed_in_m2627: {summary['dependency_mutation_allowed_in_m2627']}",
                f"source_tree_mutation_allowed_in_m2627: {summary['source_tree_mutation_allowed_in_m2627']}",
                f"network_access_allowed_in_m2627: {summary['network_access_allowed_in_m2627']}",
                f"source_build_executed_in_m2627: {summary['source_build_executed_in_m2627']}",
                f"adapter_probe_executed_in_m2627: {summary['adapter_probe_executed_in_m2627']}",
                f"backend_started_in_m2627: {summary['backend_started_in_m2627']}",
                f"reset_executed_in_m2627: {summary['reset_executed_in_m2627']}",
                f"environment_step_executed_in_m2627: {summary['environment_step_executed_in_m2627']}",
                f"policy_action_executed_in_m2627: {summary['policy_action_executed_in_m2627']}",
                f"rollout_executed_in_m2627: {summary['rollout_executed_in_m2627']}",
                f"replay_executed_in_m2627: {summary['replay_executed_in_m2627']}",
                "external_validation_execution_allowed_in_m2627: "
                f"{summary['external_validation_execution_allowed_in_m2627']}",
                f"validation_protocol_ready_in_m2627: {summary['validation_protocol_ready_in_m2627']}",
                f"validation_admission_granted_in_m2627: {summary['validation_admission_granted_in_m2627']}",
                f"validation_result_claim_allowed: {summary['validation_result_claim_allowed']}",
                "backend_availability_claim_allowed_in_m2627: "
                f"{summary['backend_availability_claim_allowed_in_m2627']}",
                f"reset_success_claim_allowed_in_m2627: {summary['reset_success_claim_allowed_in_m2627']}",
                f"rollout_feasibility_claim_allowed_in_m2627: {summary['rollout_feasibility_claim_allowed_in_m2627']}",
                f"driver_performance_claim_allowed_in_m2627: {summary['driver_performance_claim_allowed_in_m2627']}",
                f"actor contract: P0 observation {summary['observation_shape']} / action {summary['action_shape']}",
                "```",
                "",
                "## Artifact Paths",
                "",
                f"- source-build command contract rows: `{summary['hf3_selected_platform_source_build_command_contract_rows']}`",
                f"- adapter-probe command contract rows: `{summary['hf3_selected_platform_adapter_probe_command_contract_rows']}`",
                f"- dependency/environment isolation guard rows: `{summary['hf3_selected_platform_dependency_environment_isolation_guard_rows']}`",
                f"- source-build artifact capture rows: `{summary['hf3_selected_platform_source_build_artifact_capture_rows']}`",
                f"- adapter-probe trace capture rows: `{summary['hf3_selected_platform_adapter_probe_trace_capture_rows']}`",
                f"- source-build/adapter-probe outcome taxonomy rows: `{summary['hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows']}`",
                f"- actor/action guard rows: `{summary['hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows']}`",
                f"- claim-boundary rows: `{summary['hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['selected_platform_source_build_adapter_probe_execution_gate_matrix']}`",
                "",
                "## Supported Claims",
                "",
                "Supported:",
                "",
                "- selected-platform source-build/adapter-probe execution design artifacts are materialized",
                "- command contracts, isolation guards, future artifact/trace capture contracts, outcome taxonomy, actor/action, claim-boundary, and gate rows are materialized",
                f"- selected platform family remains `{SELECTED_PLATFORM_FAMILY}`",
                "- P0 `72/3` actor/action contract is preserved",
                "",
                "## Rejected Claims",
                "",
                "Rejected:",
                "",
                "- dependency ready for execution",
                "- source build or adapter probe executed",
                "- backend availability",
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
                "M2627 is a static source-build/adapter-probe execution design materialization preflight. "
                "It does not execute source build, adapter probe, backend start, reset, policy action, "
                "environment step, rollout, replay, validation, training, ranking, promotion, or any "
                "high-fidelity simulator. Build/probe outcome taxonomy rows are future audit schema and "
                "are not actor-visible.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _m2623_reset_execution_readiness_evidence_accepted(
    summary: dict[str, Any],
) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("selected_platform_family_in_m2623") == SELECTED_PLATFORM_FAMILY
        and summary.get("selected_platform_reset_execution_readiness_design_materialized_in_m2623")
        and not summary.get("source_build_executed_in_m2623")
        and not summary.get("adapter_probe_executed_in_m2623")
        and not summary.get("reset_executed_in_m2623")
        and not summary.get("validation_protocol_ready_in_m2623")
        and not summary.get("validation_admission_granted_in_m2623")
        and not summary.get("driver_performance_claim_allowed_in_m2623")
    )


def _source_build_command_contracts_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 2
        and _all_status_pass(rows)
        and _all_selected_platform(rows)
        and all(row["source_tree_required"] for row in rows)
        and all(row["out_of_tree_build_required"] for row in rows)
        and not any(row["dependency_mutation_allowed_in_m2627"] for row in rows)
        and not any(row["network_access_allowed_in_m2627"] for row in rows)
        and not any(row["build_execution_allowed_in_m2627"] for row in rows)
        and all(row["log_capture_required"] for row in rows)
        and all(row["artifact_capture_required"] for row in rows)
        and not any(row["actor_visible_allowed"] for row in rows)
    )


def _adapter_probe_command_contracts_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 2
        and _all_status_pass(rows)
        and _all_selected_platform(rows)
        and all(row["adapter_import_required"] for row in rows)
        and all(row["backend_discovery_required"] for row in rows)
        and not any(row["backend_start_allowed_in_m2627"] for row in rows)
        and not any(row["reset_allowed_in_m2627"] for row in rows)
        and not any(row["adapter_probe_execution_allowed_in_m2627"] for row in rows)
        and all(row["trace_capture_required"] for row in rows)
        and not any(row["actor_visible_allowed"] for row in rows)
    )


def _isolation_guards_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 4
        and _all_status_pass(rows)
        and _all_selected_platform(rows)
        and not any(row["external_install_allowed_in_m2627"] for row in rows)
        and not any(row["external_import_allowed_in_m2627"] for row in rows)
        and not any(row["dependency_mutation_allowed_in_m2627"] for row in rows)
        and not any(row["source_tree_mutation_allowed_in_m2627"] for row in rows)
        and not any(row["network_access_allowed_in_m2627"] for row in rows)
        and not any(row["external_runtime_allowed_in_m2627"] for row in rows)
        and not any(row["actor_visible_allowed"] for row in rows)
    )


def _source_build_artifact_capture_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 4
        and _all_status_pass(rows)
        and _all_selected_platform(rows)
        and all(row["required_for_future_source_build_audit"] for row in rows)
        and all(row["required_for_future_adapter_probe_admission"] for row in rows)
        and all(row["materialized_in_m2627"] for row in rows)
        and not any(row["source_build_executed_in_m2627"] for row in rows)
        and not any(row["artifact_observed_in_m2627"] for row in rows)
        and not any(row["actor_visible_allowed"] for row in rows)
    )


def _adapter_probe_trace_capture_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 4
        and _all_status_pass(rows)
        and _all_selected_platform(rows)
        and all(row["required_for_future_adapter_probe_audit"] for row in rows)
        and all(row["required_for_future_reset_execution_admission"] for row in rows)
        and all(row["materialized_in_m2627"] for row in rows)
        and not any(row["adapter_probe_executed_in_m2627"] for row in rows)
        and not any(row["backend_started_in_m2627"] for row in rows)
        and not any(row["trace_observed_in_m2627"] for row in rows)
        and not any(row["actor_visible_allowed"] for row in rows)
    )


def _outcome_taxonomy_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 10
        and _all_status_pass(rows)
        and all(row["required_for_future_source_build_adapter_probe_audit"] for row in rows)
        and all(row["allowed_to_support_backend_availability_after_execution"] for row in rows)
        and all(row["allowed_to_support_reset_execution_admission_after_execution"] for row in rows)
        and all(row["materialized_in_m2627"] for row in rows)
        and not any(row["actor_visible_allowed"] for row in rows)
    )


def _actor_action_guard_preserved(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 2
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(row["actor_observation_shape"] == P0_OBSERVATION_DIM for row in rows)
        and all(row["action_shape"] == ACTION_DIM for row in rows)
        and all(row["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING for row in rows)
        and not any(row["actor_input_mutation_detected"] for row in rows)
        and not any(row["action_contract_mutation_detected"] for row in rows)
        and not any(row["hidden_oracle_actor_input_detected"] for row in rows)
        and not any(row["metadata_actor_visible"] for row in rows)
    )


def _source_build_adapter_probe_execution_design_materialized(
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    isolation_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    actor_action_guard_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _source_build_command_contracts_pass(source_build_rows)
        and _adapter_probe_command_contracts_pass(adapter_probe_rows)
        and _isolation_guards_pass(isolation_rows)
        and _source_build_artifact_capture_rows_pass(artifact_rows)
        and _adapter_probe_trace_capture_rows_pass(trace_rows)
        and _outcome_taxonomy_rows_pass(outcome_rows)
        and _actor_action_guard_preserved(actor_action_guard_rows)
    )


def _any_forbidden_execution(
    source_build_rows: list[dict[str, Any]],
    adapter_probe_rows: list[dict[str, Any]],
    isolation_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        any(row["build_execution_allowed_in_m2627"] for row in source_build_rows)
        or any(row["adapter_probe_execution_allowed_in_m2627"] for row in adapter_probe_rows)
        or any(row["backend_start_allowed_in_m2627"] for row in adapter_probe_rows)
        or any(row["reset_allowed_in_m2627"] for row in adapter_probe_rows)
        or any(row["external_install_allowed_in_m2627"] for row in isolation_rows)
        or any(row["external_import_allowed_in_m2627"] for row in isolation_rows)
        or any(row["dependency_mutation_allowed_in_m2627"] for row in isolation_rows)
        or any(row["source_tree_mutation_allowed_in_m2627"] for row in isolation_rows)
        or any(row["network_access_allowed_in_m2627"] for row in isolation_rows)
        or any(row["source_build_executed_in_m2627"] for row in artifact_rows)
        or any(row["adapter_probe_executed_in_m2627"] for row in trace_rows)
        or any(row["backend_started_in_m2627"] for row in trace_rows)
    )


def _any_execution_readiness_or_performance_claim(
    claim_rows: list[dict[str, Any]],
) -> bool:
    forbidden = {
        "dependency_ready_for_execution",
        "source_build_executed",
        "adapter_probe_executed",
        "backend_available",
        "reset_executed",
        "reset_success",
        "rollout_feasibility",
        "validation_protocol_readiness",
        "validation_admission",
        "validation_readiness",
        "validation_result",
        "high_fidelity_validation_readiness",
        "high_fidelity_validation_result",
        "driver_performance",
        "current_sim_verdict",
        "paper_level_evidence",
        "finite_window_vs_gru",
        "level3_self_identification",
    }
    return any(
        row["claim_family"] in forbidden and _boolish(row["claim_allowed_in_m2627"])
        for row in claim_rows
    )


def _all_selected_platform(rows: list[dict[str, Any]]) -> bool:
    return bool(rows and all(row["selected_platform_family"] == SELECTED_PLATFORM_FAMILY for row in rows))


def _selected_platform_family(rows: list[dict[str, Any]]) -> str:
    values = sorted({str(row.get("selected_platform_family", "")) for row in rows})
    return "|".join(values)


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows and all(_boolish(row.get("status_pass")) for row in rows))


def _boolish(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2623-summary", type=Path, default=DEFAULT_M2623_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_selected_platform_source_build_adapter_probe_execution(
        args.output_dir,
        m2623_summary_path=args.m2623_summary,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
