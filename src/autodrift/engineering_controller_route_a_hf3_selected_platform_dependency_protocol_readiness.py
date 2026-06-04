"""Route A HF3 selected-platform dependency/protocol readiness materialization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2611-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-"
    "readiness-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2612-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-"
    "readiness-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2611-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-"
    "readiness-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness"
)
DEFAULT_M2607_SUMMARY = Path(
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/"
    "summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"

SOURCE_ARTIFACTS = (
    "docs/m2610-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-design.md",
    "docs/m2609-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-result-materialization-result-synthesis.md",
    "docs/m2608-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-result-materialization-result-audit.md",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/summary.json",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/hf3_after_closure_platform_selection_decision_result_rows.csv",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/hf3_after_closure_platform_selection_candidate_disposition_rows.csv",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/hf3_after_closure_platform_selection_dependency_execution_guard_rows.csv",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/hf3_after_closure_platform_selection_validation_admission_guard_rows.csv",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/hf3_after_closure_platform_selection_decision_result_actor_action_guard_rows.csv",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/hf3_after_closure_platform_selection_decision_result_claim_boundary_checks.csv",
    "runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/after_closure_platform_selection_decision_result_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform dependency/protocol readiness design materialization only; "
    "dependency inventory and protocol skeleton rows may be materialized for the selected open/"
    "auditable platform family; not dependency execution readiness, source/build execution, "
    "validation protocol readiness, validation admission, external validation execution, "
    "high-fidelity validation readiness/result, HF4 discrepancy result, rollout success, "
    "ranking, driver performance, paper, FW-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID"
)

DEPENDENCY_INVENTORY_FIELDNAMES = [
    "dependency_inventory_id",
    "selected_platform_family",
    "dependency_family",
    "dependency_role",
    "source_or_equivalent_trace_required",
    "license_or_api_review_required_later",
    "source_build_or_adapter_probe_required_later",
    "external_install_allowed_in_m2611",
    "external_import_allowed_in_m2611",
    "runtime_execution_allowed_in_m2611",
    "dependency_mutation_allowed_in_m2611",
    "status_pass",
    "claim_boundary",
]

PROBE_READINESS_FIELDNAMES = [
    "probe_readiness_id",
    "selected_platform_family",
    "probe_family",
    "probe_scope",
    "source_or_equivalent_trace_required",
    "static_contract_defined_in_m2611",
    "source_build_executed_in_m2611",
    "adapter_probe_executed_in_m2611",
    "external_install_allowed_in_m2611",
    "external_import_allowed_in_m2611",
    "runtime_execution_allowed_in_m2611",
    "dependency_mutation_allowed_in_m2611",
    "status_pass",
    "claim_boundary",
]

PROTOCOL_SKELETON_FIELDNAMES = [
    "protocol_skeleton_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "action_shape",
    "protocol_skeleton_defined_in_m2611",
    "reset_contract_required_later",
    "rollout_contract_required_later",
    "holdout_or_generalization_policy_required_later",
    "source_build_or_adapter_probe_required_later",
    "reset_allowed_in_m2611",
    "policy_action_allowed_in_m2611",
    "environment_step_allowed_in_m2611",
    "rollout_allowed_in_m2611",
    "external_validation_execution_allowed_in_m2611",
    "validation_protocol_ready_in_m2611",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES = [
    "validation_admission_prerequisite_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "action_shape",
    "dependency_inventory_materialized_in_m2611",
    "protocol_skeleton_materialized_in_m2611",
    "source_build_or_adapter_probe_required_later",
    "reset_feasibility_evidence_required_later",
    "rollout_feasibility_evidence_required_later",
    "executable_protocol_required_later",
    "holdout_or_generalization_policy_required_later",
    "validation_protocol_ready_in_m2611",
    "validation_admission_granted_in_m2611",
    "external_validation_execution_allowed_in_m2611",
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
    "claim_allowed_in_m2611",
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

DEPENDENCY_FAMILIES = (
    (
        "vehicle_dynamics_backend_source",
        "selected open/auditable vehicle dynamics source or equivalent trace",
    ),
    (
        "scenario_adapter_contract",
        "map Route A HF3 roles into a future backend reset and scene contract",
    ),
    (
        "sensor_actor_interface_contract",
        "preserve P0 human-view observation and deployed action contract",
    ),
    (
        "result_export_and_replay_contract",
        "future deterministic replay and artifact export contract",
    ),
)

PROBE_FAMILIES = (
    (
        "source_tree_or_equivalent_trace_probe",
        "static source tree or equivalent trace requirement for the selected platform family",
    ),
    (
        "build_system_contract_probe",
        "static build-system contract placeholder before source build execution",
    ),
    (
        "state_action_adapter_contract_probe",
        "static state/action adapter contract placeholder before adapter probe execution",
    ),
    (
        "deterministic_replay_export_contract_probe",
        "static deterministic replay/export contract placeholder before validation execution",
    ),
)

VALIDATION_ROLES = (
    "stable_avoidable_aeb_feasible",
    "stable_aes_aeb_infeasible",
)

ALLOWED_CLAIMS = frozenset(
    {
        "selected_platform_dependency_protocol_readiness_design_materialized",
        "selected_platform_dependency_inventory_materialized",
        "selected_platform_protocol_skeleton_materialized",
    }
)

CLAIM_CHECKS = (
    (
        "selected_platform_dependency_protocol_readiness_design_materialized",
        True,
        "M2611 dependency inventory source/build/adapter probe readiness protocol skeleton "
        "validation-admission prerequisite actor/action guard claim-boundary and gate rows",
    ),
    (
        "selected_platform_dependency_inventory_materialized",
        True,
        "M2611 selected-platform dependency inventory rows",
    ),
    (
        "selected_platform_protocol_skeleton_materialized",
        True,
        "M2611 selected-platform protocol skeleton rows preserving P0 72/3",
    ),
    ("dependency_ready_for_execution", False, "future dependency execution readiness audit"),
    ("source_build_or_adapter_probe_executed", False, "future explicit source build or adapter probe"),
    ("validation_protocol_ready", False, "future executable protocol-readiness audit"),
    ("validation_admission_granted", False, "future validation-admission audit"),
    ("external_validation_execution", False, "future explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "future platform/protocol readiness and audit"),
    ("high_fidelity_validation_result", False, "future external validation execution result audit"),
    ("hf4_discrepancy_result", False, "future HF4 external validation and discrepancy audit"),
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
    "source_build_run": False,
    "adapter_probe_run": False,
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
    "dependency_execution_readiness_claim_made": False,
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


def materialize_route_a_hf3_selected_platform_dependency_protocol_readiness(
    output_dir: Path,
    *,
    m2607_summary_path: Path = DEFAULT_M2607_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2607_summary = read_json(m2607_summary_path)

    dependency_rows = build_dependency_inventory_rows(m2607_summary)
    probe_rows = build_source_build_adapter_probe_readiness_rows(dependency_rows)
    protocol_rows = build_protocol_skeleton_rows(dependency_rows, probe_rows)
    prerequisite_rows = build_validation_admission_prerequisite_rows(
        dependency_rows,
        protocol_rows,
    )
    guard_rows = build_actor_action_guard_rows(prerequisite_rows)
    claim_rows = build_claim_boundary_checks(
        dependency_rows,
        probe_rows,
        protocol_rows,
        prerequisite_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2607_summary=m2607_summary,
        dependency_rows=dependency_rows,
        probe_rows=probe_rows,
        protocol_rows=protocol_rows,
        prerequisite_rows=prerequisite_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    dependency_path = output_dir / "hf3_selected_platform_dependency_inventory_rows.csv"
    probe_path = output_dir / "hf3_selected_platform_source_build_adapter_probe_readiness_rows.csv"
    protocol_path = output_dir / "hf3_selected_platform_protocol_skeleton_rows.csv"
    prerequisite_path = output_dir / "hf3_selected_platform_validation_admission_prerequisite_rows.csv"
    guard_path = output_dir / "hf3_selected_platform_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_selected_platform_dependency_protocol_claim_boundary_checks.csv"
    gate_path = output_dir / "selected_platform_dependency_protocol_readiness_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(dependency_path, dependency_rows, fieldnames=DEPENDENCY_INVENTORY_FIELDNAMES)
    write_csv_rows(probe_path, probe_rows, fieldnames=PROBE_READINESS_FIELDNAMES)
    write_csv_rows(protocol_path, protocol_rows, fieldnames=PROTOCOL_SKELETON_FIELDNAMES)
    write_csv_rows(
        prerequisite_path,
        prerequisite_rows,
        fieldnames=VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES,
    )
    write_csv_rows(guard_path, guard_rows, fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2607_summary=m2607_summary,
        dependency_rows=dependency_rows,
        probe_rows=probe_rows,
        protocol_rows=protocol_rows,
        prerequisite_rows=prerequisite_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        dependency_path=dependency_path,
        probe_path=probe_path,
        protocol_path=protocol_path,
        prerequisite_path=prerequisite_path,
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


def build_dependency_inventory_rows(
    m2607_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    evidence_accepted = _selected_platform_evidence_accepted(m2607_summary or {})
    rows = []
    for dependency_family, dependency_role in DEPENDENCY_FAMILIES:
        rows.append(
            {
                "dependency_inventory_id": f"{dependency_family}_inventory",
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "dependency_family": dependency_family,
                "dependency_role": dependency_role,
                "source_or_equivalent_trace_required": True,
                "license_or_api_review_required_later": True,
                "source_build_or_adapter_probe_required_later": True,
                "external_install_allowed_in_m2611": False,
                "external_import_allowed_in_m2611": False,
                "runtime_execution_allowed_in_m2611": False,
                "dependency_mutation_allowed_in_m2611": False,
                "status_pass": bool(evidence_accepted),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_source_build_adapter_probe_readiness_rows(
    dependency_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    dependency_inventory_materialized = _dependency_inventory_materialized(dependency_rows or [])
    rows = []
    for probe_family, probe_scope in PROBE_FAMILIES:
        rows.append(
            {
                "probe_readiness_id": f"{probe_family}_readiness",
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "probe_family": probe_family,
                "probe_scope": probe_scope,
                "source_or_equivalent_trace_required": True,
                "static_contract_defined_in_m2611": True,
                "source_build_executed_in_m2611": False,
                "adapter_probe_executed_in_m2611": False,
                "external_install_allowed_in_m2611": False,
                "external_import_allowed_in_m2611": False,
                "runtime_execution_allowed_in_m2611": False,
                "dependency_mutation_allowed_in_m2611": False,
                "status_pass": bool(dependency_inventory_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_protocol_skeleton_rows(
    dependency_rows: list[dict[str, Any]] | None = None,
    probe_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    prerequisites_materialized = bool(
        _dependency_inventory_materialized(dependency_rows or [])
        and _probe_readiness_materialized(probe_rows or [])
    )
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "protocol_skeleton_id": f"{route_role_id}_selected_platform_protocol_skeleton",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "protocol_skeleton_defined_in_m2611": True,
                "reset_contract_required_later": True,
                "rollout_contract_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "source_build_or_adapter_probe_required_later": True,
                "reset_allowed_in_m2611": False,
                "policy_action_allowed_in_m2611": False,
                "environment_step_allowed_in_m2611": False,
                "rollout_allowed_in_m2611": False,
                "external_validation_execution_allowed_in_m2611": False,
                "validation_protocol_ready_in_m2611": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(
                    prerequisites_materialized and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_validation_admission_prerequisite_rows(
    dependency_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dependency_inventory_materialized = _dependency_inventory_materialized(dependency_rows)
    protocol_skeleton_materialized = _protocol_skeleton_materialized(protocol_rows)
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "validation_admission_prerequisite_id": (
                    f"{route_role_id}_selected_platform_validation_admission_prerequisite"
                ),
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "dependency_inventory_materialized_in_m2611": dependency_inventory_materialized,
                "protocol_skeleton_materialized_in_m2611": protocol_skeleton_materialized,
                "source_build_or_adapter_probe_required_later": True,
                "reset_feasibility_evidence_required_later": True,
                "rollout_feasibility_evidence_required_later": True,
                "executable_protocol_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "validation_protocol_ready_in_m2611": False,
                "validation_admission_granted_in_m2611": False,
                "external_validation_execution_allowed_in_m2611": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(
                    dependency_inventory_materialized
                    and protocol_skeleton_materialized
                    and P0_OBSERVATION_DIM == 72
                    and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(
    prerequisite_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for prerequisite in prerequisite_rows:
        rows.append(
            {
                "actor_action_guard_id": (
                    f"{prerequisite['route_role_id']}_selected_platform_actor_action_guard"
                ),
                "route_role_id": prerequisite["route_role_id"],
                "actor_observation_shape": _int_value(
                    prerequisite["actor_observation_shape"],
                    default=-1,
                ),
                "action_shape": _int_value(prerequisite["action_shape"], default=-1),
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
                    _boolish(prerequisite["status_pass"])
                    and _int_value(prerequisite["actor_observation_shape"], default=-1)
                    == P0_OBSERVATION_DIM
                    and _int_value(prerequisite["action_shape"], default=-1) == ACTION_DIM
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    dependency_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = _dependency_protocol_readiness_materialized(
        dependency_rows,
        probe_rows,
        protocol_rows,
        prerequisite_rows,
        guard_rows,
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2611": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2607_summary: dict[str, Any],
    dependency_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2611"])
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
            "m2607_m2608_m2609_m2610_selected_platform_evidence_accepted",
            "lineage",
            _selected_platform_evidence_accepted(m2607_summary),
            (
                f"m2607_status={m2607_summary.get('status_pass')};"
                f"selected={m2607_summary.get('selected_platform_family_in_m2607')};"
                f"protocol_ready={m2607_summary.get('validation_protocol_ready_in_m2607')};"
                f"external_execution={m2607_summary.get('external_validation_execution_allowed_in_m2607')}"
            ),
            f"m2607_status=True;selected={SELECTED_PLATFORM_FAMILY};protocol_ready=False;"
            "external_execution=False",
            "lineage_invalid",
        ),
        (
            "dependency_inventory_rows_pass",
            "contract",
            _dependency_inventory_materialized(dependency_rows),
            f"rows={len(dependency_rows)};selected={_selected_platform_family(dependency_rows)}",
            f"rows=4;selected={SELECTED_PLATFORM_FAMILY};install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "source_build_adapter_probe_readiness_rows_pass",
            "contract",
            _probe_readiness_materialized(probe_rows),
            f"rows={len(probe_rows)}",
            "rows=4;static=true;source_build/adapter_probe/install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "protocol_skeleton_rows_pass",
            "claim_boundary",
            _protocol_skeleton_materialized(protocol_rows),
            f"rows={len(protocol_rows)}",
            "rows=2;obs=72;action=3;execution/readiness/result=false",
            "objective_overfit",
        ),
        (
            "validation_admission_prerequisite_rows_pass",
            "claim_boundary",
            _validation_admission_prerequisites_materialized(prerequisite_rows),
            f"rows={len(prerequisite_rows)}",
            "rows=2;future prerequisites=true;ready/admitted/execution/result=false",
            "objective_overfit",
        ),
        (
            "actor_action_guard_rows_pass",
            "contract",
            _actor_action_guard_preserved(guard_rows),
            f"rows={len(guard_rows)}",
            "rows=2;obs=72;action=3;hidden/status/selection/outcomes=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and len(forbidden_claims_allowed) == 0,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            "rows=20;forbidden_claims=0;materialization_claims_only=true",
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
            "no_external_install_import_runtime_or_dependency_mutation",
            "claim_boundary",
            not _any_external_dependency_action(dependency_rows, probe_rows),
            "install/import/run/mutation=false",
            "install/import/run/mutation=false",
            "objective_overfit",
        ),
        (
            "no_reset_action_step_rollout_or_validation_execution",
            "claim_boundary",
            not any(_boolish(row["reset_allowed_in_m2611"]) for row in protocol_rows)
            and not any(_boolish(row["policy_action_allowed_in_m2611"]) for row in protocol_rows)
            and not any(_boolish(row["environment_step_allowed_in_m2611"]) for row in protocol_rows)
            and not any(_boolish(row["rollout_allowed_in_m2611"]) for row in protocol_rows)
            and not any(
                _boolish(row["external_validation_execution_allowed_in_m2611"])
                for row in protocol_rows
            )
            and not any(
                _boolish(row["external_validation_execution_allowed_in_m2611"])
                for row in prerequisite_rows
            ),
            "reset/action/step/rollout/validation=false",
            "reset/action/step/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "validation_readiness_result_and_performance_forbidden",
            "claim_boundary",
            not any(
                _boolish(row["validation_protocol_ready_in_m2611"]) for row in protocol_rows
            )
            and not any(
                _boolish(row["validation_protocol_ready_in_m2611"])
                for row in prerequisite_rows
            )
            and not any(
                _boolish(row["validation_admission_granted_in_m2611"])
                for row in prerequisite_rows
            )
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in protocol_rows)
            and not any(
                _boolish(row["validation_result_claim_allowed"]) for row in prerequisite_rows
            )
            and not any(
                _boolish(row["claim_allowed_in_m2611"])
                for row in claim_rows
                if row["claim_family"]
                in {
                    "dependency_ready_for_execution",
                    "source_build_or_adapter_probe_executed",
                    "validation_protocol_ready",
                    "validation_admission_granted",
                    "external_validation_execution",
                    "high_fidelity_validation_readiness",
                    "high_fidelity_validation_result",
                    "driver_performance",
                }
            ),
            "dependency/readiness/admission/result/performance=false",
            "dependency/readiness/admission/result/performance=false",
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
    m2607_summary: dict[str, Any],
    dependency_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    dependency_path: Path,
    probe_path: Path,
    protocol_path: Path,
    prerequisite_path: Path,
    guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2611"])
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS
    )
    materialized = _dependency_protocol_readiness_materialized(
        dependency_rows,
        probe_rows,
        protocol_rows,
        prerequisite_rows,
        guard_rows,
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness_"
            "materialization_preflight_pass"
        ),
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_selected_platform_dependency_inventory_rows": str(dependency_path),
        "hf3_selected_platform_source_build_adapter_probe_readiness_rows": str(probe_path),
        "hf3_selected_platform_protocol_skeleton_rows": str(protocol_path),
        "hf3_selected_platform_validation_admission_prerequisite_rows": str(prerequisite_path),
        "hf3_selected_platform_actor_action_guard_rows": str(guard_path),
        "hf3_selected_platform_dependency_protocol_claim_boundary_checks": str(claim_path),
        "selected_platform_dependency_protocol_readiness_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2607_status_pass": bool(m2607_summary.get("status_pass")),
        "m2607_materialization_gates_all_pass": bool(
            m2607_summary.get("materialization_gates_all_pass")
        ),
        "m2607_source_artifacts_exist": bool(m2607_summary.get("source_artifacts_exist")),
        "m2607_platform_selection_decision_result_materialized": bool(
            m2607_summary.get("platform_selection_decision_result_materialized_in_m2607")
        ),
        "m2607_platform_selection_decision_made": bool(
            m2607_summary.get("platform_selection_decision_made_in_m2607")
        ),
        "m2607_selected_platform_family": m2607_summary.get("selected_platform_family_in_m2607"),
        "m2607_selected_platform_family_is_open_auditable": bool(
            m2607_summary.get("selected_platform_family_is_open_auditable")
        ),
        "m2607_black_box_backend_selected": bool(
            m2607_summary.get("black_box_backend_selected_in_m2607")
        ),
        "m2607_repo_local_current_sim_selected": bool(
            m2607_summary.get("repo_local_current_sim_selected_in_m2607")
        ),
        "m2607_validation_protocol_ready": bool(
            m2607_summary.get("validation_protocol_ready_in_m2607")
        ),
        "m2607_validation_admission_granted": bool(
            m2607_summary.get("validation_admission_granted_in_m2607")
        ),
        "m2607_external_validation_execution_allowed": bool(
            m2607_summary.get("external_validation_execution_allowed_in_m2607")
        ),
        "m2607_validation_result_claim_allowed": bool(
            m2607_summary.get("validation_result_claim_allowed")
        ),
        "m2607_driver_performance_claim_allowed": bool(
            m2607_summary.get("driver_performance_claim_allowed_in_m2607")
        ),
        "dependency_inventory_row_count": len(dependency_rows),
        "probe_readiness_row_count": len(probe_rows),
        "protocol_skeleton_row_count": len(protocol_rows),
        "validation_admission_prerequisite_row_count": len(prerequisite_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "dependency_inventory_rows_all_pass": _all_status_pass(dependency_rows),
        "probe_readiness_rows_all_pass": _all_status_pass(probe_rows),
        "protocol_skeleton_rows_all_pass": _all_status_pass(protocol_rows),
        "validation_admission_prerequisite_rows_all_pass": _all_status_pass(prerequisite_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(guard_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "selected_platform_dependency_protocol_readiness_design_materialized_in_m2611": materialized,
        "selected_platform_dependency_inventory_materialized_in_m2611": (
            _dependency_inventory_materialized(dependency_rows)
        ),
        "selected_platform_source_build_adapter_probe_readiness_materialized_in_m2611": (
            _probe_readiness_materialized(probe_rows)
        ),
        "selected_platform_protocol_skeleton_materialized_in_m2611": (
            _protocol_skeleton_materialized(protocol_rows)
        ),
        "selected_platform_validation_admission_prerequisite_materialized_in_m2611": (
            _validation_admission_prerequisites_materialized(prerequisite_rows)
        ),
        "selected_platform_family_in_m2611": SELECTED_PLATFORM_FAMILY,
        "selected_platform_family_is_open_auditable": True,
        "selected_platform_dependency_protocol_readiness_design_materialized_claim_allowed": any(
            row["claim_family"] == "selected_platform_dependency_protocol_readiness_design_materialized"
            and _boolish(row["claim_allowed_in_m2611"])
            for row in claim_rows
        ),
        "selected_platform_dependency_inventory_materialized_claim_allowed": any(
            row["claim_family"] == "selected_platform_dependency_inventory_materialized"
            and _boolish(row["claim_allowed_in_m2611"])
            for row in claim_rows
        ),
        "selected_platform_protocol_skeleton_materialized_claim_allowed": any(
            row["claim_family"] == "selected_platform_protocol_skeleton_materialized"
            and _boolish(row["claim_allowed_in_m2611"])
            for row in claim_rows
        ),
        "forbidden_claim_allowed_in_m2611": forbidden_claim_allowed,
        "external_install_allowed_in_m2611": any(
            _boolish(row["external_install_allowed_in_m2611"]) for row in dependency_rows + probe_rows
        ),
        "external_import_allowed_in_m2611": any(
            _boolish(row["external_import_allowed_in_m2611"]) for row in dependency_rows + probe_rows
        ),
        "runtime_execution_allowed_in_m2611": any(
            _boolish(row["runtime_execution_allowed_in_m2611"]) for row in dependency_rows + probe_rows
        ),
        "dependency_mutation_allowed_in_m2611": any(
            _boolish(row["dependency_mutation_allowed_in_m2611"]) for row in dependency_rows + probe_rows
        ),
        "source_build_executed_in_m2611": any(
            _boolish(row["source_build_executed_in_m2611"]) for row in probe_rows
        ),
        "adapter_probe_executed_in_m2611": any(
            _boolish(row["adapter_probe_executed_in_m2611"]) for row in probe_rows
        ),
        "static_contract_defined_in_m2611": all(
            _boolish(row["static_contract_defined_in_m2611"]) for row in probe_rows
        ),
        "reset_allowed_in_m2611": any(
            _boolish(row["reset_allowed_in_m2611"]) for row in protocol_rows
        ),
        "policy_action_allowed_in_m2611": any(
            _boolish(row["policy_action_allowed_in_m2611"]) for row in protocol_rows
        ),
        "environment_step_allowed_in_m2611": any(
            _boolish(row["environment_step_allowed_in_m2611"]) for row in protocol_rows
        ),
        "rollout_allowed_in_m2611": any(
            _boolish(row["rollout_allowed_in_m2611"]) for row in protocol_rows
        ),
        "external_validation_execution_allowed_in_m2611": any(
            _boolish(row["external_validation_execution_allowed_in_m2611"])
            for row in protocol_rows + prerequisite_rows
        ),
        "validation_protocol_ready_in_m2611": any(
            _boolish(row["validation_protocol_ready_in_m2611"])
            for row in protocol_rows + prerequisite_rows
        ),
        "validation_admission_granted_in_m2611": any(
            _boolish(row["validation_admission_granted_in_m2611"]) for row in prerequisite_rows
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"])
            for row in protocol_rows + prerequisite_rows
        ),
        "driver_performance_claim_allowed_in_m2611": any(
            row["claim_family"] == "driver_performance" and _boolish(row["claim_allowed_in_m2611"])
            for row in claim_rows
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"]) for row in guard_rows
        ),
        "diagnostics_actor_visible": any(
            _boolish(row["diagnostics_actor_visible"]) for row in guard_rows
        ),
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
        "repo_local_static_selected_platform_dependency_protocol_materialization": True,
        "repo_local_boundary_only": True,
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# M2611 Engineering Controller Route A Baseline HF3 Selected-Platform Dependency/Protocol Readiness Materialization Preflight

- status: completed
- result_class: `{summary["result_class"]}`
- milestone: `{summary["milestone"]}`
- summary: `{summary["summary"]}`
- next: `{summary["next_blocker"]}`

## Materialized Evidence

```text
status_pass: {summary["status_pass"]}
dependency_inventory_rows: {summary["dependency_inventory_row_count"]}
source_build_adapter_probe_readiness_rows: {summary["probe_readiness_row_count"]}
protocol_skeleton_rows: {summary["protocol_skeleton_row_count"]}
validation_admission_prerequisite_rows: {summary["validation_admission_prerequisite_row_count"]}
actor_action_guard_rows: {summary["actor_action_guard_row_count"]}
claim_boundary_rows: {summary["claim_boundary_check_count"]}
materialization_gates: {summary["materialization_gate_count"]}
selected_platform_dependency_protocol_readiness_design_materialized_in_m2611: {summary["selected_platform_dependency_protocol_readiness_design_materialized_in_m2611"]}
selected_platform_dependency_inventory_materialized_in_m2611: {summary["selected_platform_dependency_inventory_materialized_in_m2611"]}
selected_platform_protocol_skeleton_materialized_in_m2611: {summary["selected_platform_protocol_skeleton_materialized_in_m2611"]}
selected_platform_family_in_m2611: {summary["selected_platform_family_in_m2611"]}
external_install_allowed_in_m2611: {summary["external_install_allowed_in_m2611"]}
external_import_allowed_in_m2611: {summary["external_import_allowed_in_m2611"]}
runtime_execution_allowed_in_m2611: {summary["runtime_execution_allowed_in_m2611"]}
dependency_mutation_allowed_in_m2611: {summary["dependency_mutation_allowed_in_m2611"]}
source_build_executed_in_m2611: {summary["source_build_executed_in_m2611"]}
adapter_probe_executed_in_m2611: {summary["adapter_probe_executed_in_m2611"]}
validation_protocol_ready_in_m2611: {summary["validation_protocol_ready_in_m2611"]}
validation_admission_granted_in_m2611: {summary["validation_admission_granted_in_m2611"]}
external_validation_execution_allowed_in_m2611: {summary["external_validation_execution_allowed_in_m2611"]}
validation_result_claim_allowed: {summary["validation_result_claim_allowed"]}
driver_performance_claim_allowed_in_m2611: {summary["driver_performance_claim_allowed_in_m2611"]}
actor contract: P0 observation {summary["observation_shape"]} / action {summary["action_shape"]}
```

## Artifact Paths

- dependency inventory rows: `{summary["hf3_selected_platform_dependency_inventory_rows"]}`
- source/build/adapter probe readiness rows: `{summary["hf3_selected_platform_source_build_adapter_probe_readiness_rows"]}`
- protocol skeleton rows: `{summary["hf3_selected_platform_protocol_skeleton_rows"]}`
- validation-admission prerequisite rows: `{summary["hf3_selected_platform_validation_admission_prerequisite_rows"]}`
- actor/action guard rows: `{summary["hf3_selected_platform_actor_action_guard_rows"]}`
- claim-boundary rows: `{summary["hf3_selected_platform_dependency_protocol_claim_boundary_checks"]}`
- gate matrix: `{summary["selected_platform_dependency_protocol_readiness_gate_matrix"]}`

## Supported Claims

Supported:

- selected-platform dependency/protocol readiness design artifacts are materialized
- dependency inventory rows are materialized for `{summary["selected_platform_family_in_m2611"]}`
- protocol skeleton rows are materialized for the two HF3 low-cost pilot roles
- P0 `72/3` actor/action contract is preserved

## Rejected Claims

Rejected:

- dependency ready for execution
- source build or adapter probe executed
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


def _selected_platform_evidence_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("source_artifacts_exist")
        and summary.get("platform_selection_decision_result_materialized_in_m2607")
        and summary.get("platform_selection_decision_made_in_m2607")
        and summary.get("selected_platform_family_in_m2607") == SELECTED_PLATFORM_FAMILY
        and summary.get("selected_platform_family_is_open_auditable")
        and not summary.get("black_box_backend_selected_in_m2607")
        and not summary.get("repo_local_current_sim_selected_in_m2607")
        and summary.get("decision_result_row_count") == 1
        and summary.get("decision_evidence_row_count") == 12
        and summary.get("candidate_disposition_row_count") == 3
        and summary.get("dependency_execution_guard_row_count") == 3
        and summary.get("validation_admission_guard_row_count") == 2
        and summary.get("actor_action_guard_row_count") == 2
        and summary.get("claim_boundary_check_count") == 17
        and summary.get("materialization_gate_count") == 12
        and not summary.get("validation_protocol_ready_in_m2607")
        and not summary.get("validation_admission_granted_in_m2607")
        and not summary.get("external_validation_execution_allowed_in_m2607")
        and not summary.get("validation_result_claim_allowed")
        and not summary.get("driver_performance_claim_allowed_in_m2607")
        and not summary.get("external_install_allowed_in_m2607")
        and not summary.get("external_import_allowed_in_m2607")
        and not summary.get("runtime_execution_allowed_in_m2607")
        and not summary.get("dependency_mutation_allowed_in_m2607")
    )


def _dependency_protocol_readiness_materialized(
    dependency_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _dependency_inventory_materialized(dependency_rows)
        and _probe_readiness_materialized(probe_rows)
        and _protocol_skeleton_materialized(protocol_rows)
        and _validation_admission_prerequisites_materialized(prerequisite_rows)
        and _actor_action_guard_preserved(guard_rows)
    )


def _dependency_inventory_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(DEPENDENCY_FAMILIES)
        and _all_status_pass(rows)
        and {row["dependency_family"] for row in rows}
        == {dependency_family for dependency_family, _ in DEPENDENCY_FAMILIES}
        and {row["selected_platform_family"] for row in rows} == {SELECTED_PLATFORM_FAMILY}
        and all(_boolish(row["source_or_equivalent_trace_required"]) for row in rows)
        and all(_boolish(row["license_or_api_review_required_later"]) for row in rows)
        and all(_boolish(row["source_build_or_adapter_probe_required_later"]) for row in rows)
        and not any(_boolish(row["external_install_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["external_import_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["runtime_execution_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2611"]) for row in rows)
    )


def _probe_readiness_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(PROBE_FAMILIES)
        and _all_status_pass(rows)
        and {row["probe_family"] for row in rows}
        == {probe_family for probe_family, _ in PROBE_FAMILIES}
        and {row["selected_platform_family"] for row in rows} == {SELECTED_PLATFORM_FAMILY}
        and all(_boolish(row["source_or_equivalent_trace_required"]) for row in rows)
        and all(_boolish(row["static_contract_defined_in_m2611"]) for row in rows)
        and not any(_boolish(row["source_build_executed_in_m2611"]) for row in rows)
        and not any(_boolish(row["adapter_probe_executed_in_m2611"]) for row in rows)
        and not any(_boolish(row["external_install_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["external_import_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["runtime_execution_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2611"]) for row in rows)
    )


def _protocol_skeleton_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and {row["selected_platform_family"] for row in rows} == {SELECTED_PLATFORM_FAMILY}
        and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in rows)
        and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in rows)
        and all(_boolish(row["protocol_skeleton_defined_in_m2611"]) for row in rows)
        and all(_boolish(row["reset_contract_required_later"]) for row in rows)
        and all(_boolish(row["rollout_contract_required_later"]) for row in rows)
        and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in rows)
        and all(_boolish(row["source_build_or_adapter_probe_required_later"]) for row in rows)
        and not any(_boolish(row["reset_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["policy_action_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["environment_step_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["rollout_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["external_validation_execution_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["validation_protocol_ready_in_m2611"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _validation_admission_prerequisites_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and {row["selected_platform_family"] for row in rows} == {SELECTED_PLATFORM_FAMILY}
        and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in rows)
        and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in rows)
        and all(_boolish(row["dependency_inventory_materialized_in_m2611"]) for row in rows)
        and all(_boolish(row["protocol_skeleton_materialized_in_m2611"]) for row in rows)
        and all(_boolish(row["source_build_or_adapter_probe_required_later"]) for row in rows)
        and all(_boolish(row["reset_feasibility_evidence_required_later"]) for row in rows)
        and all(_boolish(row["rollout_feasibility_evidence_required_later"]) for row in rows)
        and all(_boolish(row["executable_protocol_required_later"]) for row in rows)
        and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in rows)
        and not any(_boolish(row["validation_protocol_ready_in_m2611"]) for row in rows)
        and not any(_boolish(row["validation_admission_granted_in_m2611"]) for row in rows)
        and not any(_boolish(row["external_validation_execution_allowed_in_m2611"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _actor_action_guard_preserved(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == len(VALIDATION_ROLES)
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in rows)
        and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in rows)
        and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in rows)
        and not any(_boolish(row["diagnostics_actor_visible"]) for row in rows)
        and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in rows)
        and not any(_boolish(row["backend_status_actor_visible"]) for row in rows)
        and not any(_boolish(row["reset_outcome_actor_visible"]) for row in rows)
        and not any(_boolish(row["rollout_outcome_actor_visible"]) for row in rows)
        and not any(_boolish(row["validation_outcome_actor_visible"]) for row in rows)
        and not any(_boolish(row["platform_selection_actor_visible"]) for row in rows)
        and not any(_boolish(row["platform_selection_criteria_actor_visible"]) for row in rows)
        and not any(_boolish(row["platform_selection_decision_actor_visible"]) for row in rows)
        and not any(_boolish(row["selected_platform_actor_visible"]) for row in rows)
        and not any(_boolish(row["protocol_status_actor_visible"]) for row in rows)
        and not any(_boolish(row["action_contract_mutation_detected"]) for row in rows)
    )


def _any_external_dependency_action(
    dependency_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> bool:
    rows = dependency_rows + probe_rows
    return bool(
        any(_boolish(row["external_install_allowed_in_m2611"]) for row in rows)
        or any(_boolish(row["external_import_allowed_in_m2611"]) for row in rows)
        or any(_boolish(row["runtime_execution_allowed_in_m2611"]) for row in rows)
        or any(_boolish(row["dependency_mutation_allowed_in_m2611"]) for row in rows)
        or any(_boolish(row.get("source_build_executed_in_m2611")) for row in rows)
        or any(_boolish(row.get("adapter_probe_executed_in_m2611")) for row in rows)
    )


def _selected_platform_family(rows: list[dict[str, Any]]) -> str:
    selected = {row.get("selected_platform_family") for row in rows}
    return selected.pop() if len(selected) == 1 else "none"


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
    parser.add_argument("--m2607-summary-path", type=Path, default=DEFAULT_M2607_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)

    summary = materialize_route_a_hf3_selected_platform_dependency_protocol_readiness(
        args.output_dir,
        m2607_summary_path=args.m2607_summary_path,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(summary["summary"])
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
