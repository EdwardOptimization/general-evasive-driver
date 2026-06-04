"""Route A HF3 selected-platform executable-protocol readiness materialization.

This module only materializes static protocol-readiness artifacts. It does not
import, build, probe, reset, step, roll out, validate, train, rank, or promote
any external high-fidelity backend.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2615-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-"
    "readiness-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2616-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-"
    "readiness-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2615-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-"
    "readiness-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness"
)
DEFAULT_M2611_SUMMARY = Path(
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/"
    "summary.json"
)

SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"
DEPLOYED_ACTION_MAPPING = "[steer, throttle, brake]"

SOURCE_ARTIFACTS = (
    "docs/m2614-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-design.md",
    "docs/m2613-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-result-synthesis.md",
    "docs/m2612-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-result-audit.md",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/summary.json",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_dependency_inventory_rows.csv",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_source_build_adapter_probe_readiness_rows.csv",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_protocol_skeleton_rows.csv",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_validation_admission_prerequisite_rows.csv",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_actor_action_guard_rows.csv",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_dependency_protocol_claim_boundary_checks.csv",
    "runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/selected_platform_dependency_protocol_readiness_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform executable-protocol readiness design materialization only; "
    "static executable protocol panels may be materialized for the selected open/auditable "
    "platform family; not dependency execution readiness, source build execution, adapter "
    "probe execution, reset execution, step execution, rollout success, validation protocol "
    "readiness, validation admission, external validation execution, high-fidelity validation "
    "readiness/result, HF4 discrepancy result, ranking, driver performance, paper, "
    "FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

SOURCE_DEPENDENCY_REVIEW_ADMISSION_FIELDNAMES = [
    "source_dependency_review_admission_id",
    "selected_platform_family",
    "review_family",
    "review_scope",
    "source_or_equivalent_trace_required",
    "review_materialized_in_m2615",
    "license_or_api_review_required_later",
    "sandbox_plan_required_before_execution",
    "external_install_allowed_in_m2615",
    "external_import_allowed_in_m2615",
    "runtime_execution_allowed_in_m2615",
    "dependency_mutation_allowed_in_m2615",
    "status_pass",
    "claim_boundary",
]

BUILD_PROBE_PLAN_FIELDNAMES = [
    "build_probe_plan_id",
    "selected_platform_family",
    "plan_family",
    "plan_scope",
    "plan_materialized_in_m2615",
    "source_build_required_later",
    "adapter_probe_required_later",
    "source_build_executed_in_m2615",
    "adapter_probe_executed_in_m2615",
    "external_install_allowed_in_m2615",
    "external_import_allowed_in_m2615",
    "runtime_execution_allowed_in_m2615",
    "dependency_mutation_allowed_in_m2615",
    "status_pass",
    "claim_boundary",
]

RESET_STEP_API_READINESS_FIELDNAMES = [
    "reset_step_api_readiness_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "action_shape",
    "reset_api_contract_defined_in_m2615",
    "step_api_contract_defined_in_m2615",
    "termination_status_contract_defined_in_m2615",
    "reset_executed_in_m2615",
    "environment_step_executed_in_m2615",
    "policy_action_executed_in_m2615",
    "rollout_executed_in_m2615",
    "external_validation_execution_allowed_in_m2615",
    "validation_protocol_ready_in_m2615",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

ACTOR_EXTRACTOR_PARITY_FIELDNAMES = [
    "actor_extractor_parity_id",
    "route_role_id",
    "selected_platform_family",
    "actor_observation_shape",
    "extractor_contract_defined_in_m2615",
    "ego_kinematics_included",
    "actuator_state_included",
    "previous_command_included",
    "road_geometry_included",
    "obstacle_geometry_included",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "selected_platform_actor_visible",
    "protocol_status_actor_visible",
    "status_pass",
    "claim_boundary",
]

ACTION_MAPPING_PARITY_FIELDNAMES = [
    "action_mapping_parity_id",
    "route_role_id",
    "selected_platform_family",
    "action_shape",
    "deployed_action_mapping",
    "action_mapping_contract_defined_in_m2615",
    "steer_command_channel_preserved",
    "throttle_command_channel_preserved",
    "brake_command_channel_preserved",
    "action_contract_mutation_detected",
    "policy_action_executed_in_m2615",
    "status_pass",
    "claim_boundary",
]

SCENARIO_ROLE_BINDING_FIELDNAMES = [
    "scenario_role_binding_id",
    "route_role_id",
    "selected_platform_family",
    "scenario_role_contract_defined_in_m2615",
    "scenario_label_actor_visible",
    "reset_feasibility_evidence_required_later",
    "rollout_feasibility_evidence_required_later",
    "holdout_or_generalization_policy_required_later",
    "reset_executed_in_m2615",
    "rollout_executed_in_m2615",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

RESULT_EXPORT_REPLAY_READINESS_FIELDNAMES = [
    "result_export_replay_readiness_id",
    "selected_platform_family",
    "export_replay_family",
    "export_replay_scope",
    "contract_defined_in_m2615",
    "replay_execution_required_later",
    "validation_execution_required_later",
    "replay_executed_in_m2615",
    "external_validation_execution_allowed_in_m2615",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

VALIDATION_ADMISSION_PREREQUISITE_FIELDNAMES = [
    "validation_admission_prerequisite_id",
    "route_role_id",
    "selected_platform_family",
    "source_dependency_review_materialized_in_m2615",
    "build_probe_plan_materialized_in_m2615",
    "reset_step_api_contract_materialized_in_m2615",
    "actor_extractor_parity_materialized_in_m2615",
    "action_mapping_parity_materialized_in_m2615",
    "scenario_role_binding_materialized_in_m2615",
    "result_export_replay_materialized_in_m2615",
    "source_build_or_adapter_probe_required_later",
    "reset_feasibility_evidence_required_later",
    "rollout_feasibility_evidence_required_later",
    "executable_protocol_required_later",
    "holdout_or_generalization_policy_required_later",
    "validation_protocol_ready_in_m2615",
    "validation_admission_granted_in_m2615",
    "external_validation_execution_allowed_in_m2615",
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
    "claim_allowed_in_m2615",
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

REVIEW_FAMILIES = (
    (
        "selected_platform_source_trace_admission",
        "static source or equivalent trace admission for the selected open/auditable platform",
    ),
    (
        "dependency_license_api_review_admission",
        "future dependency license and API review admission before execution",
    ),
    (
        "execution_sandbox_plan_admission",
        "future execution sandbox and reproducibility plan admission before build/probe",
    ),
    (
        "repo_local_adapter_boundary_admission",
        "repo-local adapter boundary admission without treating current-sim as validation authority",
    ),
)

BUILD_PROBE_PLANS = (
    ("source_build_plan", "static source build plan before any source build is executed"),
    (
        "state_action_adapter_probe_plan",
        "static state/action adapter probe plan before any adapter probe is executed",
    ),
    (
        "deterministic_replay_export_probe_plan",
        "static deterministic replay/export probe plan before replay execution",
    ),
    (
        "failure_status_taxonomy_probe_plan",
        "static failure/status taxonomy plan kept outside actor-visible inputs",
    ),
)

VALIDATION_ROLES = (
    "stable_avoidable_aeb_feasible",
    "stable_aes_aeb_infeasible",
)

EXPORT_REPLAY_FAMILIES = (
    (
        "deterministic_result_schema",
        "static result schema for future validation artifacts",
    ),
    (
        "replay_seed_and_lineage_manifest",
        "static seed and lineage manifest for future deterministic replay",
    ),
    (
        "artifact_export_index",
        "static artifact index for future audit and replay exports",
    ),
)

ALLOWED_CLAIMS = frozenset(
    {
        "selected_platform_executable_protocol_readiness_design_materialized",
        "source_dependency_review_admission_materialized",
        "build_probe_plan_materialized",
        "reset_step_api_contract_materialized",
        "actor_extractor_parity_materialized",
        "action_mapping_parity_materialized",
        "scenario_role_binding_materialized",
        "result_export_replay_readiness_materialized",
    }
)

CLAIM_CHECKS = (
    (
        "selected_platform_executable_protocol_readiness_design_materialized",
        True,
        "M2615 source/dependency review build/probe reset/step actor/action scenario "
        "export/replay validation-admission guard claim-boundary and gate rows",
    ),
    (
        "source_dependency_review_admission_materialized",
        True,
        "M2615 source/dependency review admission rows",
    ),
    ("build_probe_plan_materialized", True, "M2615 build/probe plan rows"),
    ("reset_step_api_contract_materialized", True, "M2615 reset/step API readiness rows"),
    ("actor_extractor_parity_materialized", True, "M2615 actor extractor parity rows"),
    ("action_mapping_parity_materialized", True, "M2615 action mapping parity rows"),
    ("scenario_role_binding_materialized", True, "M2615 scenario-role binding rows"),
    ("result_export_replay_readiness_materialized", True, "M2615 result export/replay rows"),
    ("dependency_ready_for_execution", False, "future dependency execution readiness audit"),
    ("source_build_executed", False, "future explicit source build execution"),
    ("adapter_probe_executed", False, "future explicit adapter probe execution"),
    ("reset_executed", False, "future explicit reset execution"),
    ("environment_step_executed", False, "future explicit environment step execution"),
    ("rollout_success", False, "future audited rollout-success criteria"),
    ("validation_protocol_ready", False, "future executable protocol-readiness audit"),
    ("validation_admission_granted", False, "future validation-admission audit"),
    ("external_validation_execution", False, "future explicit external-validation execution"),
    ("high_fidelity_validation_readiness", False, "future validation readiness audit"),
    ("high_fidelity_validation_result", False, "future external validation result audit"),
    ("hf4_discrepancy_result", False, "future HF4 discrepancy audit"),
    ("success_rate_or_controller_family_verdict", False, "separate verdict milestone"),
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


def materialize_route_a_hf3_selected_platform_executable_protocol_readiness(
    output_dir: Path,
    *,
    m2611_summary_path: Path = DEFAULT_M2611_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2611_summary = read_json(m2611_summary_path)

    review_rows = build_source_dependency_review_admission_rows(m2611_summary)
    build_probe_rows = build_build_probe_plan_rows(review_rows)
    reset_step_rows = build_reset_step_api_readiness_rows(build_probe_rows)
    actor_extractor_rows = build_actor_extractor_parity_rows(reset_step_rows)
    action_mapping_rows = build_action_mapping_parity_rows(reset_step_rows)
    scenario_role_rows = build_scenario_role_binding_rows(reset_step_rows)
    export_replay_rows = build_result_export_replay_readiness_rows(review_rows)
    prerequisite_rows = build_validation_admission_prerequisite_rows(
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
    )
    guard_rows = build_actor_action_guard_rows(prerequisite_rows)
    claim_rows = build_claim_boundary_checks(
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
        prerequisite_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2611_summary=m2611_summary,
        review_rows=review_rows,
        build_probe_rows=build_probe_rows,
        reset_step_rows=reset_step_rows,
        actor_extractor_rows=actor_extractor_rows,
        action_mapping_rows=action_mapping_rows,
        scenario_role_rows=scenario_role_rows,
        export_replay_rows=export_replay_rows,
        prerequisite_rows=prerequisite_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    review_path = output_dir / "hf3_selected_platform_source_dependency_review_admission_rows.csv"
    build_probe_path = output_dir / "hf3_selected_platform_build_probe_plan_rows.csv"
    reset_step_path = output_dir / "hf3_selected_platform_reset_step_api_readiness_rows.csv"
    actor_extractor_path = output_dir / "hf3_selected_platform_actor_extractor_parity_rows.csv"
    action_mapping_path = output_dir / "hf3_selected_platform_action_mapping_parity_rows.csv"
    scenario_role_path = output_dir / "hf3_selected_platform_scenario_role_binding_rows.csv"
    export_replay_path = output_dir / "hf3_selected_platform_result_export_replay_readiness_rows.csv"
    prerequisite_path = (
        output_dir / "hf3_selected_platform_executable_protocol_validation_admission_prerequisite_rows.csv"
    )
    guard_path = output_dir / "hf3_selected_platform_executable_protocol_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_selected_platform_executable_protocol_claim_boundary_checks.csv"
    gate_path = output_dir / "selected_platform_executable_protocol_readiness_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(
        review_path,
        review_rows,
        fieldnames=SOURCE_DEPENDENCY_REVIEW_ADMISSION_FIELDNAMES,
    )
    write_csv_rows(build_probe_path, build_probe_rows, fieldnames=BUILD_PROBE_PLAN_FIELDNAMES)
    write_csv_rows(reset_step_path, reset_step_rows, fieldnames=RESET_STEP_API_READINESS_FIELDNAMES)
    write_csv_rows(
        actor_extractor_path,
        actor_extractor_rows,
        fieldnames=ACTOR_EXTRACTOR_PARITY_FIELDNAMES,
    )
    write_csv_rows(
        action_mapping_path,
        action_mapping_rows,
        fieldnames=ACTION_MAPPING_PARITY_FIELDNAMES,
    )
    write_csv_rows(
        scenario_role_path,
        scenario_role_rows,
        fieldnames=SCENARIO_ROLE_BINDING_FIELDNAMES,
    )
    write_csv_rows(
        export_replay_path,
        export_replay_rows,
        fieldnames=RESULT_EXPORT_REPLAY_READINESS_FIELDNAMES,
    )
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
        m2611_summary=m2611_summary,
        review_rows=review_rows,
        build_probe_rows=build_probe_rows,
        reset_step_rows=reset_step_rows,
        actor_extractor_rows=actor_extractor_rows,
        action_mapping_rows=action_mapping_rows,
        scenario_role_rows=scenario_role_rows,
        export_replay_rows=export_replay_rows,
        prerequisite_rows=prerequisite_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        review_path=review_path,
        build_probe_path=build_probe_path,
        reset_step_path=reset_step_path,
        actor_extractor_path=actor_extractor_path,
        action_mapping_path=action_mapping_path,
        scenario_role_path=scenario_role_path,
        export_replay_path=export_replay_path,
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


def build_source_dependency_review_admission_rows(
    m2611_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    parent_accepted = _m2611_dependency_protocol_evidence_accepted(m2611_summary or {})
    rows = []
    for review_family, review_scope in REVIEW_FAMILIES:
        rows.append(
            {
                "source_dependency_review_admission_id": f"{review_family}_row",
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "review_family": review_family,
                "review_scope": review_scope,
                "source_or_equivalent_trace_required": True,
                "review_materialized_in_m2615": True,
                "license_or_api_review_required_later": True,
                "sandbox_plan_required_before_execution": True,
                "external_install_allowed_in_m2615": False,
                "external_import_allowed_in_m2615": False,
                "runtime_execution_allowed_in_m2615": False,
                "dependency_mutation_allowed_in_m2615": False,
                "status_pass": bool(parent_accepted),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_build_probe_plan_rows(
    review_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    review_materialized = _review_materialized(review_rows or [])
    rows = []
    for plan_family, plan_scope in BUILD_PROBE_PLANS:
        rows.append(
            {
                "build_probe_plan_id": f"{plan_family}_row",
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "plan_family": plan_family,
                "plan_scope": plan_scope,
                "plan_materialized_in_m2615": True,
                "source_build_required_later": True,
                "adapter_probe_required_later": True,
                "source_build_executed_in_m2615": False,
                "adapter_probe_executed_in_m2615": False,
                "external_install_allowed_in_m2615": False,
                "external_import_allowed_in_m2615": False,
                "runtime_execution_allowed_in_m2615": False,
                "dependency_mutation_allowed_in_m2615": False,
                "status_pass": bool(review_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_step_api_readiness_rows(
    build_probe_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    build_probe_materialized = _build_probe_plan_materialized(build_probe_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "reset_step_api_readiness_id": f"{route_role_id}_reset_step_api_readiness",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "reset_api_contract_defined_in_m2615": True,
                "step_api_contract_defined_in_m2615": True,
                "termination_status_contract_defined_in_m2615": True,
                "reset_executed_in_m2615": False,
                "environment_step_executed_in_m2615": False,
                "policy_action_executed_in_m2615": False,
                "rollout_executed_in_m2615": False,
                "external_validation_execution_allowed_in_m2615": False,
                "validation_protocol_ready_in_m2615": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(
                    build_probe_materialized and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_extractor_parity_rows(
    reset_step_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    reset_step_materialized = _reset_step_api_materialized(reset_step_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "actor_extractor_parity_id": f"{route_role_id}_actor_extractor_parity",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "extractor_contract_defined_in_m2615": True,
                "ego_kinematics_included": True,
                "actuator_state_included": True,
                "previous_command_included": True,
                "road_geometry_included": True,
                "obstacle_geometry_included": True,
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "selected_platform_actor_visible": False,
                "protocol_status_actor_visible": False,
                "status_pass": bool(reset_step_materialized and P0_OBSERVATION_DIM == 72),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_action_mapping_parity_rows(
    reset_step_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    reset_step_materialized = _reset_step_api_materialized(reset_step_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "action_mapping_parity_id": f"{route_role_id}_action_mapping_parity",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "action_shape": ACTION_DIM,
                "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
                "action_mapping_contract_defined_in_m2615": True,
                "steer_command_channel_preserved": True,
                "throttle_command_channel_preserved": True,
                "brake_command_channel_preserved": True,
                "action_contract_mutation_detected": False,
                "policy_action_executed_in_m2615": False,
                "status_pass": bool(reset_step_materialized and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_scenario_role_binding_rows(
    reset_step_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    reset_step_materialized = _reset_step_api_materialized(reset_step_rows or [])
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "scenario_role_binding_id": f"{route_role_id}_scenario_role_binding",
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "scenario_role_contract_defined_in_m2615": True,
                "scenario_label_actor_visible": False,
                "reset_feasibility_evidence_required_later": True,
                "rollout_feasibility_evidence_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "reset_executed_in_m2615": False,
                "rollout_executed_in_m2615": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(reset_step_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_result_export_replay_readiness_rows(
    review_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    review_materialized = _review_materialized(review_rows or [])
    rows = []
    for export_replay_family, export_replay_scope in EXPORT_REPLAY_FAMILIES:
        rows.append(
            {
                "result_export_replay_readiness_id": f"{export_replay_family}_row",
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "export_replay_family": export_replay_family,
                "export_replay_scope": export_replay_scope,
                "contract_defined_in_m2615": True,
                "replay_execution_required_later": True,
                "validation_execution_required_later": True,
                "replay_executed_in_m2615": False,
                "external_validation_execution_allowed_in_m2615": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(review_materialized),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_validation_admission_prerequisite_rows(
    review_rows: list[dict[str, Any]],
    build_probe_rows: list[dict[str, Any]],
    reset_step_rows: list[dict[str, Any]],
    actor_extractor_rows: list[dict[str, Any]],
    action_mapping_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    panels = {
        "source_dependency_review_materialized_in_m2615": _review_materialized(review_rows),
        "build_probe_plan_materialized_in_m2615": _build_probe_plan_materialized(build_probe_rows),
        "reset_step_api_contract_materialized_in_m2615": _reset_step_api_materialized(
            reset_step_rows
        ),
        "actor_extractor_parity_materialized_in_m2615": _actor_extractor_parity_materialized(
            actor_extractor_rows
        ),
        "action_mapping_parity_materialized_in_m2615": _action_mapping_parity_materialized(
            action_mapping_rows
        ),
        "scenario_role_binding_materialized_in_m2615": _scenario_role_binding_materialized(
            scenario_role_rows
        ),
        "result_export_replay_materialized_in_m2615": _result_export_replay_materialized(
            export_replay_rows
        ),
    }
    rows = []
    for route_role_id in VALIDATION_ROLES:
        rows.append(
            {
                "validation_admission_prerequisite_id": (
                    f"{route_role_id}_executable_protocol_validation_admission_prerequisite"
                ),
                "route_role_id": route_role_id,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                **panels,
                "source_build_or_adapter_probe_required_later": True,
                "reset_feasibility_evidence_required_later": True,
                "rollout_feasibility_evidence_required_later": True,
                "executable_protocol_required_later": True,
                "holdout_or_generalization_policy_required_later": True,
                "validation_protocol_ready_in_m2615": False,
                "validation_admission_granted_in_m2615": False,
                "external_validation_execution_allowed_in_m2615": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(all(panels.values())),
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
                    f"{prerequisite['route_role_id']}_executable_protocol_actor_action_guard"
                ),
                "route_role_id": prerequisite["route_role_id"],
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
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
                    and P0_OBSERVATION_DIM == 72
                    and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    review_rows: list[dict[str, Any]],
    build_probe_rows: list[dict[str, Any]],
    reset_step_rows: list[dict[str, Any]],
    actor_extractor_rows: list[dict[str, Any]],
    action_mapping_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = _executable_protocol_readiness_materialized(
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
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
                "claim_allowed_in_m2615": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2611_summary: dict[str, Any],
    review_rows: list[dict[str, Any]],
    build_probe_rows: list[dict[str, Any]],
    reset_step_rows: list[dict[str, Any]],
    actor_extractor_rows: list[dict[str, Any]],
    action_mapping_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2615"])
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
            "m2611_m2612_m2613_dependency_protocol_readiness_evidence_accepted",
            "lineage",
            _m2611_dependency_protocol_evidence_accepted(m2611_summary),
            (
                f"m2611_status={m2611_summary.get('status_pass')};"
                f"selected={m2611_summary.get('selected_platform_family_in_m2611')};"
                f"validation_ready={m2611_summary.get('validation_protocol_ready_in_m2611')};"
                f"external_execution={m2611_summary.get('external_validation_execution_allowed_in_m2611')}"
            ),
            f"m2611_status=True;selected={SELECTED_PLATFORM_FAMILY};"
            "validation_ready=False;external_execution=False",
            "lineage_invalid",
        ),
        (
            "source_dependency_review_admission_rows_pass",
            "contract",
            _review_materialized(review_rows),
            f"rows={len(review_rows)};selected={_selected_platform_family(review_rows)}",
            f"rows=4;selected={SELECTED_PLATFORM_FAMILY};install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "build_probe_plan_rows_pass",
            "contract",
            _build_probe_plan_materialized(build_probe_rows),
            f"rows={len(build_probe_rows)}",
            "rows=4;source_build/adapter_probe/install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "reset_step_api_readiness_rows_pass",
            "claim_boundary",
            _reset_step_api_materialized(reset_step_rows),
            f"rows={len(reset_step_rows)}",
            "rows=2;obs=72;action=3;reset/step/action/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "actor_extractor_parity_rows_pass",
            "contract",
            _actor_extractor_parity_materialized(actor_extractor_rows),
            f"rows={len(actor_extractor_rows)}",
            "rows=2;obs=72;deployable actor fields=true;hidden/status/labels=false",
            "contract_violation",
        ),
        (
            "action_mapping_parity_rows_pass",
            "contract",
            _action_mapping_parity_materialized(action_mapping_rows),
            f"rows={len(action_mapping_rows)}",
            "rows=2;action=3;mapping=[steer, throttle, brake];mutation/action=false",
            "contract_violation",
        ),
        (
            "scenario_role_binding_rows_pass",
            "contract",
            _scenario_role_binding_materialized(scenario_role_rows),
            f"rows={len(scenario_role_rows)}",
            "rows=2;role metadata not actor-visible;reset/rollout/result=false",
            "contract_violation",
        ),
        (
            "result_export_replay_readiness_rows_pass",
            "claim_boundary",
            _result_export_replay_materialized(export_replay_rows),
            f"rows={len(export_replay_rows)}",
            "rows=3;replay/validation/result=false",
            "objective_overfit",
        ),
        (
            "validation_admission_prerequisite_rows_pass",
            "claim_boundary",
            _validation_admission_prerequisites_materialized(prerequisite_rows),
            f"rows={len(prerequisite_rows)}",
            "rows=2;all panels materialized;ready/admitted/execution/result=false",
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
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;materialization_claims_only=true",
            "objective_overfit",
        ),
        (
            "no_dependency_build_probe_reset_step_action_rollout_or_validation_execution",
            "claim_boundary",
            not _any_forbidden_execution(
                review_rows,
                build_probe_rows,
                reset_step_rows,
                scenario_role_rows,
                export_replay_rows,
                prerequisite_rows,
            ),
            "install/import/run/mutation/build/probe/reset/step/action/rollout/validation=false",
            "install/import/run/mutation/build/probe/reset/step/action/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "validation_readiness_result_and_performance_forbidden",
            "claim_boundary",
            not _any_validation_or_performance_claim(
                reset_step_rows,
                scenario_role_rows,
                export_replay_rows,
                prerequisite_rows,
                claim_rows,
            ),
            "validation readiness/admission/execution/result/performance=false",
            "validation readiness/admission/execution/result/performance=false",
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
    m2611_summary: dict[str, Any],
    review_rows: list[dict[str, Any]],
    build_probe_rows: list[dict[str, Any]],
    reset_step_rows: list[dict[str, Any]],
    actor_extractor_rows: list[dict[str, Any]],
    action_mapping_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    review_path: Path,
    build_probe_path: Path,
    reset_step_path: Path,
    actor_extractor_path: Path,
    action_mapping_path: Path,
    scenario_role_path: Path,
    export_replay_path: Path,
    prerequisite_path: Path,
    guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    forbidden_claim_allowed = any(
        _boolish(row["claim_allowed_in_m2615"])
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS
    )
    materialized = _executable_protocol_readiness_materialized(
        review_rows,
        build_probe_rows,
        reset_step_rows,
        actor_extractor_rows,
        action_mapping_rows,
        scenario_role_rows,
        export_replay_rows,
        prerequisite_rows,
        guard_rows,
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness_"
            "materialization_preflight_pass"
        ),
        "status_pass": bool(_all_status_pass(gate_rows)),
        "generated_at_utc": utc_timestamp(),
        "summary": str(output_dir / "summary.json"),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "hf3_selected_platform_source_dependency_review_admission_rows": str(review_path),
        "hf3_selected_platform_build_probe_plan_rows": str(build_probe_path),
        "hf3_selected_platform_reset_step_api_readiness_rows": str(reset_step_path),
        "hf3_selected_platform_actor_extractor_parity_rows": str(actor_extractor_path),
        "hf3_selected_platform_action_mapping_parity_rows": str(action_mapping_path),
        "hf3_selected_platform_scenario_role_binding_rows": str(scenario_role_path),
        "hf3_selected_platform_result_export_replay_readiness_rows": str(export_replay_path),
        "hf3_selected_platform_executable_protocol_validation_admission_prerequisite_rows": str(
            prerequisite_path
        ),
        "hf3_selected_platform_executable_protocol_actor_action_guard_rows": str(guard_path),
        "hf3_selected_platform_executable_protocol_claim_boundary_checks": str(claim_path),
        "selected_platform_executable_protocol_readiness_gate_matrix": str(gate_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2611_status_pass": bool(m2611_summary.get("status_pass")),
        "m2611_materialization_gates_all_pass": bool(
            m2611_summary.get("materialization_gates_all_pass")
        ),
        "m2611_source_artifacts_exist": bool(m2611_summary.get("source_artifacts_exist")),
        "m2611_selected_platform_family": m2611_summary.get("selected_platform_family_in_m2611"),
        "m2611_dependency_protocol_readiness_design_materialized": bool(
            m2611_summary.get(
                "selected_platform_dependency_protocol_readiness_design_materialized_in_m2611"
            )
        ),
        "m2611_validation_protocol_ready": bool(
            m2611_summary.get("validation_protocol_ready_in_m2611")
        ),
        "m2611_validation_admission_granted": bool(
            m2611_summary.get("validation_admission_granted_in_m2611")
        ),
        "m2611_external_validation_execution_allowed": bool(
            m2611_summary.get("external_validation_execution_allowed_in_m2611")
        ),
        "m2611_validation_result_claim_allowed": bool(
            m2611_summary.get("validation_result_claim_allowed")
        ),
        "m2611_driver_performance_claim_allowed": bool(
            m2611_summary.get("driver_performance_claim_allowed_in_m2611")
        ),
        "source_dependency_review_admission_row_count": len(review_rows),
        "build_probe_plan_row_count": len(build_probe_rows),
        "reset_step_api_readiness_row_count": len(reset_step_rows),
        "actor_extractor_parity_row_count": len(actor_extractor_rows),
        "action_mapping_parity_row_count": len(action_mapping_rows),
        "scenario_role_binding_row_count": len(scenario_role_rows),
        "result_export_replay_readiness_row_count": len(export_replay_rows),
        "validation_admission_prerequisite_row_count": len(prerequisite_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "source_dependency_review_admission_rows_all_pass": _all_status_pass(review_rows),
        "build_probe_plan_rows_all_pass": _all_status_pass(build_probe_rows),
        "reset_step_api_readiness_rows_all_pass": _all_status_pass(reset_step_rows),
        "actor_extractor_parity_rows_all_pass": _all_status_pass(actor_extractor_rows),
        "action_mapping_parity_rows_all_pass": _all_status_pass(action_mapping_rows),
        "scenario_role_binding_rows_all_pass": _all_status_pass(scenario_role_rows),
        "result_export_replay_readiness_rows_all_pass": _all_status_pass(export_replay_rows),
        "validation_admission_prerequisite_rows_all_pass": _all_status_pass(prerequisite_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(guard_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "selected_platform_executable_protocol_readiness_design_materialized_in_m2615": materialized,
        "selected_platform_family_in_m2615": SELECTED_PLATFORM_FAMILY,
        "selected_platform_family_is_open_auditable": True,
        "source_dependency_review_materialized_in_m2615": _review_materialized(review_rows),
        "build_probe_plan_materialized_in_m2615": _build_probe_plan_materialized(
            build_probe_rows
        ),
        "reset_step_api_contract_materialized_in_m2615": _reset_step_api_materialized(
            reset_step_rows
        ),
        "actor_extractor_parity_materialized_in_m2615": _actor_extractor_parity_materialized(
            actor_extractor_rows
        ),
        "action_mapping_parity_materialized_in_m2615": _action_mapping_parity_materialized(
            action_mapping_rows
        ),
        "scenario_role_binding_materialized_in_m2615": _scenario_role_binding_materialized(
            scenario_role_rows
        ),
        "result_export_replay_materialized_in_m2615": _result_export_replay_materialized(
            export_replay_rows
        ),
        "selected_platform_executable_protocol_readiness_design_materialized_claim_allowed": (
            _claim_allowed(
                claim_rows,
                "selected_platform_executable_protocol_readiness_design_materialized",
            )
        ),
        "source_dependency_review_admission_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "source_dependency_review_admission_materialized",
        ),
        "build_probe_plan_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "build_probe_plan_materialized",
        ),
        "reset_step_api_contract_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "reset_step_api_contract_materialized",
        ),
        "actor_extractor_parity_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "actor_extractor_parity_materialized",
        ),
        "action_mapping_parity_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "action_mapping_parity_materialized",
        ),
        "scenario_role_binding_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "scenario_role_binding_materialized",
        ),
        "result_export_replay_readiness_materialized_claim_allowed": _claim_allowed(
            claim_rows,
            "result_export_replay_readiness_materialized",
        ),
        "forbidden_claim_allowed_in_m2615": forbidden_claim_allowed,
        "external_install_allowed_in_m2615": any(
            _boolish(row["external_install_allowed_in_m2615"]) for row in review_rows + build_probe_rows
        ),
        "external_import_allowed_in_m2615": any(
            _boolish(row["external_import_allowed_in_m2615"]) for row in review_rows + build_probe_rows
        ),
        "runtime_execution_allowed_in_m2615": any(
            _boolish(row["runtime_execution_allowed_in_m2615"]) for row in review_rows + build_probe_rows
        ),
        "dependency_mutation_allowed_in_m2615": any(
            _boolish(row["dependency_mutation_allowed_in_m2615"])
            for row in review_rows + build_probe_rows
        ),
        "source_build_executed_in_m2615": any(
            _boolish(row["source_build_executed_in_m2615"]) for row in build_probe_rows
        ),
        "adapter_probe_executed_in_m2615": any(
            _boolish(row["adapter_probe_executed_in_m2615"]) for row in build_probe_rows
        ),
        "reset_executed_in_m2615": any(
            _boolish(row["reset_executed_in_m2615"]) for row in reset_step_rows + scenario_role_rows
        ),
        "environment_step_executed_in_m2615": any(
            _boolish(row["environment_step_executed_in_m2615"]) for row in reset_step_rows
        ),
        "policy_action_executed_in_m2615": any(
            _boolish(row["policy_action_executed_in_m2615"])
            for row in reset_step_rows + action_mapping_rows
        ),
        "rollout_executed_in_m2615": any(
            _boolish(row["rollout_executed_in_m2615"]) for row in reset_step_rows + scenario_role_rows
        ),
        "replay_executed_in_m2615": any(
            _boolish(row["replay_executed_in_m2615"]) for row in export_replay_rows
        ),
        "external_validation_execution_allowed_in_m2615": any(
            _boolish(row["external_validation_execution_allowed_in_m2615"])
            for row in reset_step_rows + export_replay_rows + prerequisite_rows
        ),
        "validation_protocol_ready_in_m2615": any(
            _boolish(row["validation_protocol_ready_in_m2615"])
            for row in reset_step_rows + prerequisite_rows
        ),
        "validation_admission_granted_in_m2615": any(
            _boolish(row["validation_admission_granted_in_m2615"]) for row in prerequisite_rows
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"])
            for row in reset_step_rows + scenario_role_rows + export_replay_rows + prerequisite_rows
        ),
        "driver_performance_claim_allowed_in_m2615": _claim_allowed(
            claim_rows,
            "driver_performance",
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"])
            for row in actor_extractor_rows + guard_rows
        ),
        "diagnostics_actor_visible": any(
            _boolish(row["diagnostics_actor_visible"]) for row in actor_extractor_rows + guard_rows
        ),
        "taxonomy_label_actor_visible": any(
            _boolish(row["taxonomy_label_actor_visible"])
            for row in actor_extractor_rows + guard_rows
        ),
        "backend_status_actor_visible": any(
            _boolish(row["backend_status_actor_visible"]) for row in actor_extractor_rows + guard_rows
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
            _boolish(row["selected_platform_actor_visible"])
            for row in actor_extractor_rows + guard_rows
        ),
        "protocol_status_actor_visible": any(
            _boolish(row["protocol_status_actor_visible"]) for row in actor_extractor_rows + guard_rows
        ),
        "scenario_label_actor_visible": any(
            _boolish(row["scenario_label_actor_visible"]) for row in scenario_role_rows
        ),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"])
            for row in action_mapping_rows + guard_rows
        ),
        "repo_local_boundary_only": True,
        "repo_local_static_selected_platform_executable_protocol_materialization": True,
    }
    summary.update(FORBIDDEN_FLAGS)
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2615 Engineering Controller Route A Baseline HF3 Selected-Platform "
                "Executable-Protocol Readiness Materialization Preflight",
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
                "source_dependency_review_admission_rows: "
                f"{summary['source_dependency_review_admission_row_count']}",
                f"build_probe_plan_rows: {summary['build_probe_plan_row_count']}",
                f"reset_step_api_readiness_rows: {summary['reset_step_api_readiness_row_count']}",
                f"actor_extractor_parity_rows: {summary['actor_extractor_parity_row_count']}",
                f"action_mapping_parity_rows: {summary['action_mapping_parity_row_count']}",
                f"scenario_role_binding_rows: {summary['scenario_role_binding_row_count']}",
                "result_export_replay_readiness_rows: "
                f"{summary['result_export_replay_readiness_row_count']}",
                "validation_admission_prerequisite_rows: "
                f"{summary['validation_admission_prerequisite_row_count']}",
                f"actor_action_guard_rows: {summary['actor_action_guard_row_count']}",
                f"claim_boundary_rows: {summary['claim_boundary_check_count']}",
                f"materialization_gates: {summary['materialization_gate_count']}",
                "selected_platform_executable_protocol_readiness_design_materialized_in_m2615: "
                f"{summary['selected_platform_executable_protocol_readiness_design_materialized_in_m2615']}",
                f"selected_platform_family_in_m2615: {summary['selected_platform_family_in_m2615']}",
                f"external_install_allowed_in_m2615: {summary['external_install_allowed_in_m2615']}",
                f"external_import_allowed_in_m2615: {summary['external_import_allowed_in_m2615']}",
                f"runtime_execution_allowed_in_m2615: {summary['runtime_execution_allowed_in_m2615']}",
                f"dependency_mutation_allowed_in_m2615: {summary['dependency_mutation_allowed_in_m2615']}",
                f"source_build_executed_in_m2615: {summary['source_build_executed_in_m2615']}",
                f"adapter_probe_executed_in_m2615: {summary['adapter_probe_executed_in_m2615']}",
                f"reset_executed_in_m2615: {summary['reset_executed_in_m2615']}",
                f"environment_step_executed_in_m2615: {summary['environment_step_executed_in_m2615']}",
                f"policy_action_executed_in_m2615: {summary['policy_action_executed_in_m2615']}",
                f"rollout_executed_in_m2615: {summary['rollout_executed_in_m2615']}",
                "external_validation_execution_allowed_in_m2615: "
                f"{summary['external_validation_execution_allowed_in_m2615']}",
                f"validation_protocol_ready_in_m2615: {summary['validation_protocol_ready_in_m2615']}",
                f"validation_admission_granted_in_m2615: {summary['validation_admission_granted_in_m2615']}",
                f"validation_result_claim_allowed: {summary['validation_result_claim_allowed']}",
                "driver_performance_claim_allowed_in_m2615: "
                f"{summary['driver_performance_claim_allowed_in_m2615']}",
                f"actor contract: P0 observation {summary['observation_shape']} / action {summary['action_shape']}",
                "```",
                "",
                "## Artifact Paths",
                "",
                "- source/dependency review admission rows: "
                f"`{summary['hf3_selected_platform_source_dependency_review_admission_rows']}`",
                f"- build/probe plan rows: `{summary['hf3_selected_platform_build_probe_plan_rows']}`",
                f"- reset/step API readiness rows: `{summary['hf3_selected_platform_reset_step_api_readiness_rows']}`",
                f"- actor extractor parity rows: `{summary['hf3_selected_platform_actor_extractor_parity_rows']}`",
                f"- action mapping parity rows: `{summary['hf3_selected_platform_action_mapping_parity_rows']}`",
                f"- scenario-role binding rows: `{summary['hf3_selected_platform_scenario_role_binding_rows']}`",
                f"- result export/replay readiness rows: `{summary['hf3_selected_platform_result_export_replay_readiness_rows']}`",
                "- validation-admission prerequisite rows: "
                f"`{summary['hf3_selected_platform_executable_protocol_validation_admission_prerequisite_rows']}`",
                "- actor/action guard rows: "
                f"`{summary['hf3_selected_platform_executable_protocol_actor_action_guard_rows']}`",
                "- claim-boundary rows: "
                f"`{summary['hf3_selected_platform_executable_protocol_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['selected_platform_executable_protocol_readiness_gate_matrix']}`",
                "",
                "## Supported Claims",
                "",
                "Supported:",
                "",
                "- selected-platform executable-protocol readiness design artifacts are materialized",
                "- source/dependency review admission, build/probe plan, reset/step API, actor "
                "extractor, action mapping, scenario-role, and export/replay static panels are materialized",
                f"- selected platform family remains `{SELECTED_PLATFORM_FAMILY}`",
                "- P0 `72/3` actor/action contract is preserved",
                "",
                "## Rejected Claims",
                "",
                "Rejected:",
                "",
                "- dependency ready for execution",
                "- source build or adapter probe executed",
                "- reset, policy action, environment step, rollout, replay, or validation executed",
                "- validation protocol readiness",
                "- validation admission",
                "- validation readiness or result",
                "- external validation execution",
                "- HF4 discrepancy result",
                "- rollout success",
                "- success-rate or controller-family verdict",
                "- controller ranking or winner selection",
                "- checkpoint promotion",
                "- driver performance",
                "- paper-level evidence",
                "- finite-window-vs-GRU result",
                "- current-sim verdict",
                "- high-fidelity validation result",
                "- level3 self-identification",
                "",
                "## Next Step",
                "",
                "If accepted by audit, route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _m2611_dependency_protocol_evidence_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("materialization_gates_all_pass")
        and summary.get("source_artifacts_exist")
        and summary.get("selected_platform_family_in_m2611") == SELECTED_PLATFORM_FAMILY
        and summary.get("selected_platform_dependency_protocol_readiness_design_materialized_in_m2611")
        and not summary.get("external_install_allowed_in_m2611")
        and not summary.get("external_import_allowed_in_m2611")
        and not summary.get("runtime_execution_allowed_in_m2611")
        and not summary.get("dependency_mutation_allowed_in_m2611")
        and not summary.get("source_build_executed_in_m2611")
        and not summary.get("adapter_probe_executed_in_m2611")
        and not summary.get("validation_protocol_ready_in_m2611")
        and not summary.get("validation_admission_granted_in_m2611")
        and not summary.get("external_validation_execution_allowed_in_m2611")
        and not summary.get("validation_result_claim_allowed")
        and not summary.get("driver_performance_claim_allowed_in_m2611")
        and summary.get("observation_shape") == P0_OBSERVATION_DIM
        and summary.get("action_shape") == ACTION_DIM
    )


def _review_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 4
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and all(_boolish(row["review_materialized_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_install_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_import_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["runtime_execution_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2615"]) for row in rows)
    )


def _build_probe_plan_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 4
        and _all_status_pass(rows)
        and _selected_platform_family(rows) == SELECTED_PLATFORM_FAMILY
        and all(_boolish(row["plan_materialized_in_m2615"]) for row in rows)
        and not any(_boolish(row["source_build_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["adapter_probe_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_install_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_import_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["runtime_execution_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["dependency_mutation_allowed_in_m2615"]) for row in rows)
    )


def _reset_step_api_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(_int_value(row["actor_observation_shape"]) == P0_OBSERVATION_DIM for row in rows)
        and all(_int_value(row["action_shape"]) == ACTION_DIM for row in rows)
        and all(_boolish(row["reset_api_contract_defined_in_m2615"]) for row in rows)
        and all(_boolish(row["step_api_contract_defined_in_m2615"]) for row in rows)
        and all(_boolish(row["termination_status_contract_defined_in_m2615"]) for row in rows)
        and not any(_boolish(row["reset_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["environment_step_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["policy_action_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["rollout_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_validation_execution_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["validation_protocol_ready_in_m2615"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _actor_extractor_parity_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and all(_int_value(row["actor_observation_shape"]) == P0_OBSERVATION_DIM for row in rows)
        and all(_boolish(row["extractor_contract_defined_in_m2615"]) for row in rows)
        and all(_boolish(row["ego_kinematics_included"]) for row in rows)
        and all(_boolish(row["actuator_state_included"]) for row in rows)
        and all(_boolish(row["previous_command_included"]) for row in rows)
        and all(_boolish(row["road_geometry_included"]) for row in rows)
        and all(_boolish(row["obstacle_geometry_included"]) for row in rows)
        and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in rows)
        and not any(_boolish(row["diagnostics_actor_visible"]) for row in rows)
        and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in rows)
        and not any(_boolish(row["backend_status_actor_visible"]) for row in rows)
        and not any(_boolish(row["selected_platform_actor_visible"]) for row in rows)
        and not any(_boolish(row["protocol_status_actor_visible"]) for row in rows)
    )


def _action_mapping_parity_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and all(_int_value(row["action_shape"]) == ACTION_DIM for row in rows)
        and all(row["deployed_action_mapping"] == DEPLOYED_ACTION_MAPPING for row in rows)
        and all(_boolish(row["action_mapping_contract_defined_in_m2615"]) for row in rows)
        and all(_boolish(row["steer_command_channel_preserved"]) for row in rows)
        and all(_boolish(row["throttle_command_channel_preserved"]) for row in rows)
        and all(_boolish(row["brake_command_channel_preserved"]) for row in rows)
        and not any(_boolish(row["action_contract_mutation_detected"]) for row in rows)
        and not any(_boolish(row["policy_action_executed_in_m2615"]) for row in rows)
    )


def _scenario_role_binding_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(_boolish(row["scenario_role_contract_defined_in_m2615"]) for row in rows)
        and not any(_boolish(row["scenario_label_actor_visible"]) for row in rows)
        and all(_boolish(row["reset_feasibility_evidence_required_later"]) for row in rows)
        and all(_boolish(row["rollout_feasibility_evidence_required_later"]) for row in rows)
        and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in rows)
        and not any(_boolish(row["reset_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["rollout_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _result_export_replay_materialized(rows: list[dict[str, Any]]) -> bool:
    return bool(
        len(rows) == 3
        and _all_status_pass(rows)
        and all(_boolish(row["contract_defined_in_m2615"]) for row in rows)
        and all(_boolish(row["replay_execution_required_later"]) for row in rows)
        and all(_boolish(row["validation_execution_required_later"]) for row in rows)
        and not any(_boolish(row["replay_executed_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_validation_execution_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _validation_admission_prerequisites_materialized(rows: list[dict[str, Any]]) -> bool:
    materialized_columns = (
        "source_dependency_review_materialized_in_m2615",
        "build_probe_plan_materialized_in_m2615",
        "reset_step_api_contract_materialized_in_m2615",
        "actor_extractor_parity_materialized_in_m2615",
        "action_mapping_parity_materialized_in_m2615",
        "scenario_role_binding_materialized_in_m2615",
        "result_export_replay_materialized_in_m2615",
    )
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and {row["route_role_id"] for row in rows} == set(VALIDATION_ROLES)
        and all(all(_boolish(row[column]) for column in materialized_columns) for row in rows)
        and all(_boolish(row["source_build_or_adapter_probe_required_later"]) for row in rows)
        and all(_boolish(row["reset_feasibility_evidence_required_later"]) for row in rows)
        and all(_boolish(row["rollout_feasibility_evidence_required_later"]) for row in rows)
        and all(_boolish(row["executable_protocol_required_later"]) for row in rows)
        and all(_boolish(row["holdout_or_generalization_policy_required_later"]) for row in rows)
        and not any(_boolish(row["validation_protocol_ready_in_m2615"]) for row in rows)
        and not any(_boolish(row["validation_admission_granted_in_m2615"]) for row in rows)
        and not any(_boolish(row["external_validation_execution_allowed_in_m2615"]) for row in rows)
        and not any(_boolish(row["validation_result_claim_allowed"]) for row in rows)
    )


def _actor_action_guard_preserved(rows: list[dict[str, Any]]) -> bool:
    forbidden = (
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
    )
    return bool(
        len(rows) == 2
        and _all_status_pass(rows)
        and all(_int_value(row["actor_observation_shape"]) == P0_OBSERVATION_DIM for row in rows)
        and all(_int_value(row["action_shape"]) == ACTION_DIM for row in rows)
        and not any(_boolish(row[key]) for row in rows for key in forbidden)
    )


def _executable_protocol_readiness_materialized(
    review_rows: list[dict[str, Any]],
    build_probe_rows: list[dict[str, Any]],
    reset_step_rows: list[dict[str, Any]],
    actor_extractor_rows: list[dict[str, Any]],
    action_mapping_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        _review_materialized(review_rows)
        and _build_probe_plan_materialized(build_probe_rows)
        and _reset_step_api_materialized(reset_step_rows)
        and _actor_extractor_parity_materialized(actor_extractor_rows)
        and _action_mapping_parity_materialized(action_mapping_rows)
        and _scenario_role_binding_materialized(scenario_role_rows)
        and _result_export_replay_materialized(export_replay_rows)
        and _validation_admission_prerequisites_materialized(prerequisite_rows)
        and _actor_action_guard_preserved(guard_rows)
    )


def _any_forbidden_execution(
    review_rows: list[dict[str, Any]],
    build_probe_rows: list[dict[str, Any]],
    reset_step_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
) -> bool:
    return bool(
        any(
            _boolish(row[key])
            for row in review_rows + build_probe_rows
            for key in (
                "external_install_allowed_in_m2615",
                "external_import_allowed_in_m2615",
                "runtime_execution_allowed_in_m2615",
                "dependency_mutation_allowed_in_m2615",
            )
        )
        or any(
            _boolish(row[key])
            for row in build_probe_rows
            for key in ("source_build_executed_in_m2615", "adapter_probe_executed_in_m2615")
        )
        or any(
            _boolish(row[key])
            for row in reset_step_rows
            for key in (
                "reset_executed_in_m2615",
                "environment_step_executed_in_m2615",
                "policy_action_executed_in_m2615",
                "rollout_executed_in_m2615",
                "external_validation_execution_allowed_in_m2615",
            )
        )
        or any(
            _boolish(row[key])
            for row in scenario_role_rows
            for key in ("reset_executed_in_m2615", "rollout_executed_in_m2615")
        )
        or any(_boolish(row["replay_executed_in_m2615"]) for row in export_replay_rows)
        or any(
            _boolish(row["external_validation_execution_allowed_in_m2615"])
            for row in export_replay_rows + prerequisite_rows
        )
    )


def _any_validation_or_performance_claim(
    reset_step_rows: list[dict[str, Any]],
    scenario_role_rows: list[dict[str, Any]],
    export_replay_rows: list[dict[str, Any]],
    prerequisite_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> bool:
    forbidden_claim_families = {
        "dependency_ready_for_execution",
        "source_build_executed",
        "adapter_probe_executed",
        "reset_executed",
        "environment_step_executed",
        "rollout_success",
        "validation_protocol_ready",
        "validation_admission_granted",
        "external_validation_execution",
        "high_fidelity_validation_readiness",
        "high_fidelity_validation_result",
        "hf4_discrepancy_result",
        "success_rate_or_controller_family_verdict",
        "controller_ranking_or_winner_selection",
        "checkpoint_promotion",
        "driver_performance",
        "paper_level_evidence",
        "finite_window_vs_gru_result",
        "current_sim_verdict",
        "level3_self_identification",
    }
    return bool(
        any(_boolish(row["validation_protocol_ready_in_m2615"]) for row in reset_step_rows)
        or any(_boolish(row["validation_result_claim_allowed"]) for row in reset_step_rows)
        or any(_boolish(row["validation_result_claim_allowed"]) for row in scenario_role_rows)
        or any(_boolish(row["validation_result_claim_allowed"]) for row in export_replay_rows)
        or any(_boolish(row["validation_protocol_ready_in_m2615"]) for row in prerequisite_rows)
        or any(_boolish(row["validation_admission_granted_in_m2615"]) for row in prerequisite_rows)
        or any(
            _boolish(row["external_validation_execution_allowed_in_m2615"])
            for row in prerequisite_rows
        )
        or any(_boolish(row["validation_result_claim_allowed"]) for row in prerequisite_rows)
        or any(
            row["claim_family"] in forbidden_claim_families
            and _boolish(row["claim_allowed_in_m2615"])
            for row in claim_rows
        )
    )


def _claim_allowed(rows: list[dict[str, Any]], claim_family: str) -> bool:
    return any(
        row["claim_family"] == claim_family and _boolish(row["claim_allowed_in_m2615"])
        for row in rows
    )


def _selected_platform_family(rows: list[dict[str, Any]]) -> str:
    families = {row.get("selected_platform_family", "") for row in rows}
    if len(families) == 1:
        return next(iter(families))
    return ",".join(sorted(families))


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def _int_value(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize Route A HF3 selected-platform executable-protocol readiness rows."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2611-summary", type=Path, default=DEFAULT_M2611_SUMMARY)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_selected_platform_executable_protocol_readiness(
        args.output_dir,
        m2611_summary_path=args.m2611_summary,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
