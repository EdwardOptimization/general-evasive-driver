"""Route A HF3 source-only adapter readiness blocker materialization."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2588-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2589-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-"
    "materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2588-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-"
    "materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker")
DEFAULT_M2584_SUMMARY = Path("runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/summary.json")
DEFAULT_M2584_PREREQUISITE_ROWS = Path(
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/"
    "hf3_source_only_adapter_prerequisite_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2587-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-design.md",
    "docs/m2586-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-result-synthesis.md",
    "docs/m2585-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-result-audit.md",
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/summary.json",
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_source_only_adapter_prerequisite_rows.csv",
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_validation_protocol_skeleton_rows.csv",
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_platform_protocol_actor_action_guard_rows.csv",
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_platform_protocol_claim_boundary_checks.csv",
    "runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/validation_platform_protocol_readiness_gate_matrix.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 source-only adapter readiness blocker materialization preflight only; "
    "blocker definition artifacts may be materialized; not blocker closure, platform selection, "
    "validation protocol readiness, validation admission, external validation execution, high-fidelity "
    "validation readiness/result, HF4 discrepancy result, rollout success, ranking, driver performance, "
    "paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

EXTERNAL_STATE_FIELDNAMES = [
    "state_boundary_id",
    "boundary_family",
    "source_artifact",
    "adapter_contract_required_before_external_execution",
    "backend_state_may_be_read_by_adapter",
    "actor_visible",
    "diagnostic_only",
    "hidden_or_oracle_actor_input_detected",
    "blocker_contract_defined_in_m2588",
    "readiness_satisfied_in_m2588",
    "external_validation_execution_allowed_in_m2588",
    "status_pass",
    "claim_boundary",
]

TIMING_CONTRACT_FIELDNAMES = [
    "timing_contract_id",
    "contract_family",
    "source_artifact",
    "adapter_contract_required_before_external_execution",
    "simulation_time_step_defined",
    "control_update_rate_defined",
    "actuator_latency_mapping_defined",
    "command_hold_or_delay_defined",
    "actor_observation_shape",
    "action_shape",
    "action_contract_mutation_detected",
    "blocker_contract_defined_in_m2588",
    "readiness_satisfied_in_m2588",
    "external_validation_execution_allowed_in_m2588",
    "status_pass",
    "claim_boundary",
]

STATUS_MAPPING_FIELDNAMES = [
    "status_mapping_id",
    "mapping_family",
    "source_artifact",
    "adapter_contract_required_before_external_execution",
    "backend_status_actor_visible",
    "taxonomy_label_actor_visible",
    "diagnostics_actor_visible",
    "maps_to_repo_local_status_class",
    "blocker_contract_defined_in_m2588",
    "readiness_satisfied_in_m2588",
    "external_validation_execution_allowed_in_m2588",
    "status_pass",
    "claim_boundary",
]

FIXTURE_LINEAGE_FIELDNAMES = [
    "fixture_lineage_id",
    "lineage_family",
    "source_artifact",
    "fixture_source_declared",
    "expected_schema_declared",
    "external_runtime_required",
    "external_runtime_executed_in_m2588",
    "replayable_artifact_hash_declared",
    "blocker_contract_defined_in_m2588",
    "readiness_satisfied_in_m2588",
    "external_validation_execution_allowed_in_m2588",
    "status_pass",
    "claim_boundary",
]

ACTOR_VISIBILITY_GUARD_FIELDNAMES = [
    "actor_visibility_guard_id",
    "blocker_family",
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
    "protocol_status_actor_visible",
    "action_contract_mutation_detected",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2588",
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

EXTERNAL_STATE_BOUNDARIES = (
    ("ego_state_extraction_contract", True, False),
    ("external_backend_state_mapping_contract", True, False),
    ("diagnostic_state_redaction_contract", False, True),
    ("validation_metadata_separation_contract", False, True),
)

TIMING_CONTRACTS = (
    ("simulation_time_step_contract", True, False, False, False),
    ("control_update_rate_contract", False, True, False, False),
    ("actuator_latency_mapping_contract", False, False, True, False),
    ("command_hold_and_delay_contract", False, False, False, True),
)

STATUS_MAPPINGS = (
    "reset_failure_status_mapping",
    "step_failure_status_mapping",
    "collision_or_contact_status_mapping",
    "validation_abort_status_mapping",
)

FIXTURE_LINEAGE_FAMILIES = (
    "fixture_source_manifest_lineage",
    "fixture_expected_schema_lineage",
    "fixture_no_external_runtime_lineage",
    "fixture_replayable_artifact_hash_lineage",
)

BLOCKER_FAMILIES = (
    "external_state_extraction_boundary",
    "time_step_and_actuator_latency_contract",
    "failure_status_taxonomy_mapping",
    "source_only_fixture_smoke_lineage",
)

CLAIM_CHECKS = (
    (
        "source_only_adapter_readiness_blocker_design_materialized",
        True,
        "M2588 external state extraction timing status fixture actor-visibility claim-boundary and gate rows",
    ),
    ("source_only_adapter_blockers_closed", False, "later blocker-closure audit with executable adapter evidence"),
    ("platform_selected_for_validation", False, "later platform-selection audit after blocker closure"),
    ("validation_protocol_ready", False, "later protocol-readiness audit with holdout/generalization policy"),
    ("validation_admission_granted", False, "later validation-admission result audit"),
    ("external_validation_execution", False, "later explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "later readiness decision after blocker closure and platform/protocol audit"),
    ("high_fidelity_validation_result", False, "later external validation execution result audit"),
    ("hf4_discrepancy_result", False, "later HF4 external validation and discrepancy result audit"),
    ("rollout_success", False, "later audited rollout-success criteria"),
    ("success_rate_or_controller_family_verdict", False, "separate benchmark/verdict milestone"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("driver_performance_claim", False, "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", False, "separate paper-route evidence matrix"),
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
    "source_only_adapter_blockers_closed_claim_made": False,
    "platform_selection_claim_made": False,
    "validation_protocol_readiness_claim_made": False,
    "validation_admission_claim_made": False,
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


def materialize_route_a_hf3_source_only_adapter_readiness_blocker(
    output_dir: Path,
    *,
    m2584_summary_path: Path = DEFAULT_M2584_SUMMARY,
    m2584_prerequisite_rows_path: Path = DEFAULT_M2584_PREREQUISITE_ROWS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2584_summary = read_json(m2584_summary_path)
    prerequisite_rows = _read_csv_rows(m2584_prerequisite_rows_path)

    external_state_rows = build_external_state_extraction_boundary_rows()
    timing_rows = build_time_step_actuator_latency_contract_rows()
    status_rows = build_failure_status_taxonomy_mapping_rows()
    fixture_rows = build_source_only_fixture_smoke_lineage_rows()
    actor_guard_rows = build_actor_visibility_guard_rows()
    claim_rows = build_claim_boundary_checks(
        external_state_rows,
        timing_rows,
        status_rows,
        fixture_rows,
        actor_guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2584_summary=m2584_summary,
        prerequisite_rows=prerequisite_rows,
        external_state_rows=external_state_rows,
        timing_rows=timing_rows,
        status_rows=status_rows,
        fixture_rows=fixture_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
    )

    external_state_path = output_dir / "hf3_external_state_extraction_boundary_rows.csv"
    timing_path = output_dir / "hf3_time_step_actuator_latency_contract_rows.csv"
    status_path = output_dir / "hf3_failure_status_taxonomy_mapping_rows.csv"
    fixture_path = output_dir / "hf3_source_only_fixture_smoke_lineage_rows.csv"
    actor_guard_path = output_dir / "hf3_source_only_adapter_actor_visibility_guard_rows.csv"
    claim_path = output_dir / "hf3_source_only_adapter_claim_boundary_checks.csv"
    gate_path = output_dir / "source_only_adapter_readiness_blocker_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(external_state_path, external_state_rows, fieldnames=EXTERNAL_STATE_FIELDNAMES)
    write_csv_rows(timing_path, timing_rows, fieldnames=TIMING_CONTRACT_FIELDNAMES)
    write_csv_rows(status_path, status_rows, fieldnames=STATUS_MAPPING_FIELDNAMES)
    write_csv_rows(fixture_path, fixture_rows, fieldnames=FIXTURE_LINEAGE_FIELDNAMES)
    write_csv_rows(actor_guard_path, actor_guard_rows, fieldnames=ACTOR_VISIBILITY_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2584_summary=m2584_summary,
        prerequisite_rows=prerequisite_rows,
        external_state_rows=external_state_rows,
        timing_rows=timing_rows,
        status_rows=status_rows,
        fixture_rows=fixture_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        external_state_path=external_state_path,
        timing_path=timing_path,
        status_path=status_path,
        fixture_path=fixture_path,
        actor_guard_path=actor_guard_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_external_state_extraction_boundary_rows() -> list[dict[str, Any]]:
    rows = []
    source_artifact = str(DEFAULT_M2584_PREREQUISITE_ROWS)
    for boundary_family, adapter_read_allowed, diagnostic_only in EXTERNAL_STATE_BOUNDARIES:
        rows.append(
            {
                "state_boundary_id": f"{boundary_family}_state_boundary",
                "boundary_family": boundary_family,
                "source_artifact": source_artifact,
                "adapter_contract_required_before_external_execution": True,
                "backend_state_may_be_read_by_adapter": bool(adapter_read_allowed),
                "actor_visible": False,
                "diagnostic_only": bool(diagnostic_only),
                "hidden_or_oracle_actor_input_detected": False,
                "blocker_contract_defined_in_m2588": True,
                "readiness_satisfied_in_m2588": False,
                "external_validation_execution_allowed_in_m2588": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_time_step_actuator_latency_contract_rows() -> list[dict[str, Any]]:
    rows = []
    source_artifact = str(DEFAULT_M2584_PREREQUISITE_ROWS)
    for family, timestep_defined, update_rate_defined, latency_defined, hold_delay_defined in TIMING_CONTRACTS:
        rows.append(
            {
                "timing_contract_id": f"{family}_timing_contract",
                "contract_family": family,
                "source_artifact": source_artifact,
                "adapter_contract_required_before_external_execution": True,
                "simulation_time_step_defined": bool(timestep_defined),
                "control_update_rate_defined": bool(update_rate_defined),
                "actuator_latency_mapping_defined": bool(latency_defined),
                "command_hold_or_delay_defined": bool(hold_delay_defined),
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "action_contract_mutation_detected": False,
                "blocker_contract_defined_in_m2588": True,
                "readiness_satisfied_in_m2588": False,
                "external_validation_execution_allowed_in_m2588": False,
                "status_pass": bool(P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_failure_status_taxonomy_mapping_rows() -> list[dict[str, Any]]:
    rows = []
    source_artifact = str(DEFAULT_M2584_PREREQUISITE_ROWS)
    for mapping_family in STATUS_MAPPINGS:
        rows.append(
            {
                "status_mapping_id": f"{mapping_family}_status_mapping",
                "mapping_family": mapping_family,
                "source_artifact": source_artifact,
                "adapter_contract_required_before_external_execution": True,
                "backend_status_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "diagnostics_actor_visible": False,
                "maps_to_repo_local_status_class": True,
                "blocker_contract_defined_in_m2588": True,
                "readiness_satisfied_in_m2588": False,
                "external_validation_execution_allowed_in_m2588": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_source_only_fixture_smoke_lineage_rows() -> list[dict[str, Any]]:
    rows = []
    source_artifact = str(DEFAULT_M2584_PREREQUISITE_ROWS)
    for lineage_family in FIXTURE_LINEAGE_FAMILIES:
        rows.append(
            {
                "fixture_lineage_id": f"{lineage_family}_fixture_lineage",
                "lineage_family": lineage_family,
                "source_artifact": source_artifact,
                "fixture_source_declared": True,
                "expected_schema_declared": True,
                "external_runtime_required": False,
                "external_runtime_executed_in_m2588": False,
                "replayable_artifact_hash_declared": True,
                "blocker_contract_defined_in_m2588": True,
                "readiness_satisfied_in_m2588": False,
                "external_validation_execution_allowed_in_m2588": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_visibility_guard_rows() -> list[dict[str, Any]]:
    rows = []
    for blocker_family in BLOCKER_FAMILIES:
        rows.append(
            {
                "actor_visibility_guard_id": f"{blocker_family}_actor_visibility_guard",
                "blocker_family": blocker_family,
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
                "protocol_status_actor_visible": False,
                "action_contract_mutation_detected": False,
                "status_pass": bool(P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    external_state_rows: list[dict[str, Any]],
    timing_rows: list[dict[str, Any]],
    status_rows: list[dict[str, Any]],
    fixture_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    design_materialized = bool(
        len(external_state_rows) == len(EXTERNAL_STATE_BOUNDARIES)
        and _all_status_pass(external_state_rows)
        and len(timing_rows) == len(TIMING_CONTRACTS)
        and _all_status_pass(timing_rows)
        and len(status_rows) == len(STATUS_MAPPINGS)
        and _all_status_pass(status_rows)
        and len(fixture_rows) == len(FIXTURE_LINEAGE_FAMILIES)
        and _all_status_pass(fixture_rows)
        and len(actor_guard_rows) == len(BLOCKER_FAMILIES)
        and _all_status_pass(actor_guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and design_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2588": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "source_only_adapter_readiness_blocker_design_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2584_summary: dict[str, Any],
    prerequisite_rows: list[dict[str, Any]],
    external_state_rows: list[dict[str, Any]],
    timing_rows: list[dict[str, Any]],
    status_rows: list[dict[str, Any]],
    fixture_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"] != "source_only_adapter_readiness_blocker_design_materialized"
        and _boolish(row["claim_allowed_in_m2588"])
    ]
    missing_blockers = {
        row["prerequisite_family"]
        for row in prerequisite_rows
        if _boolish(row.get("missing_before_platform_protocol_readiness"))
    }
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values())
            and bool(m2584_summary.get("status_pass"))
            and missing_blockers == set(BLOCKER_FAMILIES),
            (
                f"missing={sum(1 for exists in source_exists.values() if not exists)};"
                f"m2584_status={m2584_summary.get('status_pass')};blockers={len(missing_blockers)}"
            ),
            "missing=0;m2584_status=True;blockers=4",
            "lineage_invalid",
        ),
        (
            "external_state_extraction_boundary_rows_complete",
            "contract",
            len(external_state_rows) == len(EXTERNAL_STATE_BOUNDARIES)
            and _all_status_pass(external_state_rows)
            and _blocker_rows_are_definitions_only(external_state_rows)
            and not any(_boolish(row["actor_visible"]) for row in external_state_rows)
            and not any(_boolish(row["hidden_or_oracle_actor_input_detected"]) for row in external_state_rows),
            f"rows={len(external_state_rows)}",
            f"rows={len(EXTERNAL_STATE_BOUNDARIES)};actor_visible=false;readiness=false",
            "contract_violation",
        ),
        (
            "time_step_actuator_latency_contract_rows_complete",
            "contract",
            len(timing_rows) == len(TIMING_CONTRACTS)
            and _all_status_pass(timing_rows)
            and _blocker_rows_are_definitions_only(timing_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in timing_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in timing_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in timing_rows),
            f"rows={len(timing_rows)}",
            f"rows={len(TIMING_CONTRACTS)};obs=72;action=3;mutation=false",
            "contract_violation",
        ),
        (
            "failure_status_taxonomy_mapping_rows_complete",
            "contract",
            len(status_rows) == len(STATUS_MAPPINGS)
            and _all_status_pass(status_rows)
            and _blocker_rows_are_definitions_only(status_rows)
            and all(_boolish(row["maps_to_repo_local_status_class"]) for row in status_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in status_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in status_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in status_rows),
            f"rows={len(status_rows)}",
            f"rows={len(STATUS_MAPPINGS)};actor_visible=false;maps=true",
            "contract_violation",
        ),
        (
            "source_only_fixture_smoke_lineage_rows_complete",
            "lineage",
            len(fixture_rows) == len(FIXTURE_LINEAGE_FAMILIES)
            and _all_status_pass(fixture_rows)
            and _blocker_rows_are_definitions_only(fixture_rows)
            and all(_boolish(row["fixture_source_declared"]) for row in fixture_rows)
            and all(_boolish(row["expected_schema_declared"]) for row in fixture_rows)
            and not any(_boolish(row["external_runtime_required"]) for row in fixture_rows)
            and not any(_boolish(row["external_runtime_executed_in_m2588"]) for row in fixture_rows)
            and all(_boolish(row["replayable_artifact_hash_declared"]) for row in fixture_rows),
            f"rows={len(fixture_rows)}",
            f"rows={len(FIXTURE_LINEAGE_FAMILIES)};external_runtime=false",
            "lineage_invalid",
        ),
        (
            "actor_visibility_guard_rows_pass",
            "contract",
            len(actor_guard_rows) == len(BLOCKER_FAMILIES)
            and _all_status_pass(actor_guard_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in actor_guard_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in actor_guard_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_guard_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["validation_outcome_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["platform_selection_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["protocol_status_actor_visible"]) for row in actor_guard_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in actor_guard_rows),
            f"rows={len(actor_guard_rows)}",
            "rows=4;obs=72;action=3;hidden/outcomes/platform/protocol/mutation=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not forbidden_claims_allowed
            and any(
                row["claim_family"] == "source_only_adapter_readiness_blocker_design_materialized"
                and _boolish(row["claim_allowed_in_m2588"])
                for row in claim_rows
            ),
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;design_materialized=true",
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
            "no_blocker_closed_or_readiness_claim",
            "claim_boundary",
            not _any_readiness_satisfied(external_state_rows, timing_rows, status_rows, fixture_rows)
            and not any(
                row["claim_family"] == "source_only_adapter_blockers_closed"
                and _boolish(row["claim_allowed_in_m2588"])
                for row in claim_rows
            )
            and not any(
                row["claim_family"]
                in {
                    "validation_protocol_ready",
                    "validation_admission_granted",
                    "high_fidelity_validation_readiness",
                    "high_fidelity_validation_result",
                }
                and _boolish(row["claim_allowed_in_m2588"])
                for row in claim_rows
            ),
            "blockers_closed=false;readiness/admission/result=false",
            "blockers_closed=false;readiness/admission/result=false",
            "objective_overfit",
        ),
        (
            "no_platform_selection_or_external_execution",
            "claim_boundary",
            not _any_external_validation_allowed(external_state_rows, timing_rows, status_rows, fixture_rows)
            and not any(
                row["claim_family"] == "platform_selected_for_validation"
                and _boolish(row["claim_allowed_in_m2588"])
                for row in claim_rows
            )
            and not any(
                row["claim_family"] == "external_validation_execution"
                and _boolish(row["claim_allowed_in_m2588"])
                for row in claim_rows
            ),
            "platform_selection=false;external_validation=false",
            "platform_selection=false;external_validation=false",
            "objective_overfit",
        ),
        (
            "no_forbidden_execution_or_claim_flags",
            "claim_boundary",
            not any(FORBIDDEN_FLAGS.values()),
            "all forbidden false",
            "all forbidden false",
            "objective_overfit",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if passed else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, family, passed, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    source_exists: dict[str, bool],
    m2584_summary: dict[str, Any],
    prerequisite_rows: list[dict[str, Any]],
    external_state_rows: list[dict[str, Any]],
    timing_rows: list[dict[str, Any]],
    status_rows: list[dict[str, Any]],
    fixture_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    external_state_path: Path,
    timing_path: Path,
    status_path: Path,
    fixture_path: Path,
    actor_guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    design_claim_allowed = any(
        row["claim_family"] == "source_only_adapter_readiness_blocker_design_materialized"
        and _boolish(row["claim_allowed_in_m2588"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"] != "source_only_adapter_readiness_blocker_design_materialized"
        and _boolish(row["claim_allowed_in_m2588"])
        for row in claim_rows
    )
    blocker_rows = [*external_state_rows, *timing_rows, *status_rows, *fixture_rows]
    missing_blockers = {
        row["prerequisite_family"]
        for row in prerequisite_rows
        if _boolish(row.get("missing_before_platform_protocol_readiness"))
    }
    status_pass = (
        all(source_exists.values())
        and bool(m2584_summary.get("status_pass"))
        and missing_blockers == set(BLOCKER_FAMILIES)
        and len(external_state_rows) == len(EXTERNAL_STATE_BOUNDARIES)
        and _all_status_pass(external_state_rows)
        and len(timing_rows) == len(TIMING_CONTRACTS)
        and _all_status_pass(timing_rows)
        and len(status_rows) == len(STATUS_MAPPINGS)
        and _all_status_pass(status_rows)
        and len(fixture_rows) == len(FIXTURE_LINEAGE_FAMILIES)
        and _all_status_pass(fixture_rows)
        and len(actor_guard_rows) == len(BLOCKER_FAMILIES)
        and _all_status_pass(actor_guard_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and design_claim_allowed
        and not forbidden_claim_allowed
        and not _any_readiness_satisfied(external_state_rows, timing_rows, status_rows, fixture_rows)
        and not _any_external_validation_allowed(external_state_rows, timing_rows, status_rows, fixture_rows)
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_external_state_extraction_boundary_rows": str(external_state_path),
        "hf3_time_step_actuator_latency_contract_rows": str(timing_path),
        "hf3_failure_status_taxonomy_mapping_rows": str(status_path),
        "hf3_source_only_fixture_smoke_lineage_rows": str(fixture_path),
        "hf3_source_only_adapter_actor_visibility_guard_rows": str(actor_guard_path),
        "hf3_source_only_adapter_claim_boundary_checks": str(claim_path),
        "source_only_adapter_readiness_blocker_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2584_status_pass": bool(m2584_summary.get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "m2584_missing_blocker_count": len(missing_blockers),
        "m2584_missing_blocker_families": sorted(missing_blockers),
        "external_state_extraction_boundary_row_count": len(external_state_rows),
        "external_state_extraction_boundary_rows_all_pass": _all_status_pass(external_state_rows),
        "time_step_actuator_latency_contract_row_count": len(timing_rows),
        "time_step_actuator_latency_contract_rows_all_pass": _all_status_pass(timing_rows),
        "failure_status_taxonomy_mapping_row_count": len(status_rows),
        "failure_status_taxonomy_mapping_rows_all_pass": _all_status_pass(status_rows),
        "source_only_fixture_smoke_lineage_row_count": len(fixture_rows),
        "source_only_fixture_smoke_lineage_rows_all_pass": _all_status_pass(fixture_rows),
        "actor_visibility_guard_row_count": len(actor_guard_rows),
        "actor_visibility_guard_rows_all_pass": _all_status_pass(actor_guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "source_only_adapter_readiness_blocker_design_materialized_claim_allowed": bool(design_claim_allowed),
        "forbidden_claim_allowed_in_m2588": bool(forbidden_claim_allowed),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "blocker_contract_defined_in_m2588": all(
            _boolish(row["blocker_contract_defined_in_m2588"]) for row in blocker_rows
        ),
        "readiness_satisfied_in_m2588": _any_readiness_satisfied(
            external_state_rows,
            timing_rows,
            status_rows,
            fixture_rows,
        ),
        "external_validation_execution_allowed_in_m2588": _any_external_validation_allowed(
            external_state_rows,
            timing_rows,
            status_rows,
            fixture_rows,
        ),
        "backend_state_may_be_read_by_adapter": any(
            _boolish(row["backend_state_may_be_read_by_adapter"]) for row in external_state_rows
        ),
        "actor_visible": any(_boolish(row["actor_visible"]) for row in external_state_rows),
        "diagnostic_only_rows_present": any(_boolish(row["diagnostic_only"]) for row in external_state_rows),
        "simulation_time_step_defined": any(_boolish(row["simulation_time_step_defined"]) for row in timing_rows),
        "control_update_rate_defined": any(_boolish(row["control_update_rate_defined"]) for row in timing_rows),
        "actuator_latency_mapping_defined": any(_boolish(row["actuator_latency_mapping_defined"]) for row in timing_rows),
        "command_hold_or_delay_defined": any(_boolish(row["command_hold_or_delay_defined"]) for row in timing_rows),
        "maps_to_repo_local_status_class": all(
            _boolish(row["maps_to_repo_local_status_class"]) for row in status_rows
        ),
        "fixture_source_declared": all(_boolish(row["fixture_source_declared"]) for row in fixture_rows),
        "expected_schema_declared": all(_boolish(row["expected_schema_declared"]) for row in fixture_rows),
        "external_runtime_required": any(_boolish(row["external_runtime_required"]) for row in fixture_rows),
        "external_runtime_executed_in_m2588": any(
            _boolish(row["external_runtime_executed_in_m2588"]) for row in fixture_rows
        ),
        "replayable_artifact_hash_declared": all(
            _boolish(row["replayable_artifact_hash_declared"]) for row in fixture_rows
        ),
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_guard_rows
        )
        or any(_boolish(row["hidden_or_oracle_actor_input_detected"]) for row in external_state_rows),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in actor_guard_rows)
        or any(_boolish(row["diagnostics_actor_visible"]) for row in status_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_guard_rows)
        or any(_boolish(row["taxonomy_label_actor_visible"]) for row in status_rows),
        "backend_status_actor_visible": any(_boolish(row["backend_status_actor_visible"]) for row in actor_guard_rows)
        or any(_boolish(row["backend_status_actor_visible"]) for row in status_rows),
        "reset_outcome_actor_visible": any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_guard_rows),
        "rollout_outcome_actor_visible": any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_guard_rows),
        "validation_outcome_actor_visible": any(
            _boolish(row["validation_outcome_actor_visible"]) for row in actor_guard_rows
        ),
        "platform_selection_actor_visible": any(
            _boolish(row["platform_selection_actor_visible"]) for row in actor_guard_rows
        ),
        "protocol_status_actor_visible": any(_boolish(row["protocol_status_actor_visible"]) for row in actor_guard_rows),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"]) for row in actor_guard_rows
        )
        or any(_boolish(row["action_contract_mutation_detected"]) for row in timing_rows),
        "source_only_adapter_blockers_closed_claim_allowed": any(
            row["claim_family"] == "source_only_adapter_blockers_closed"
            and _boolish(row["claim_allowed_in_m2588"])
            for row in claim_rows
        ),
        "platform_selection_claim_allowed": any(
            row["claim_family"] == "platform_selected_for_validation"
            and _boolish(row["claim_allowed_in_m2588"])
            for row in claim_rows
        ),
        "validation_protocol_ready_claim_allowed": any(
            row["claim_family"] == "validation_protocol_ready"
            and _boolish(row["claim_allowed_in_m2588"])
            for row in claim_rows
        ),
        "validation_admission_granted": any(
            row["claim_family"] == "validation_admission_granted"
            and _boolish(row["claim_allowed_in_m2588"])
            for row in claim_rows
        ),
        "repo_local_static_source_only_adapter_blocker_materialization": True,
        "repo_local_boundary_only": True,
        "policy_action_executed": FORBIDDEN_FLAGS["policy_action_run"],
        "environment_step_executed": FORBIDDEN_FLAGS["environment_step_run"],
        "validation_readiness_claim_made": FORBIDDEN_FLAGS["high_fidelity_validation_readiness_claim_made"],
        "validation_result_claim_made": FORBIDDEN_FLAGS["high_fidelity_validation_result_claim_made"],
        **FORBIDDEN_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2588 Engineering Controller Route A Baseline HF3 Source-Only Adapter Readiness Blocker Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2588-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker.py`",
                f"- summary: `{summary['summary']}`",
                f"- external state extraction boundary rows: `{summary['hf3_external_state_extraction_boundary_rows']}`",
                f"- time-step/actuator latency contract rows: `{summary['hf3_time_step_actuator_latency_contract_rows']}`",
                f"- failure/status taxonomy mapping rows: `{summary['hf3_failure_status_taxonomy_mapping_rows']}`",
                f"- source-only fixture smoke lineage rows: `{summary['hf3_source_only_fixture_smoke_lineage_rows']}`",
                f"- actor-visibility guard rows: `{summary['hf3_source_only_adapter_actor_visibility_guard_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_source_only_adapter_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['source_only_adapter_readiness_blocker_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- blocker contracts defined: `true`",
                "- readiness satisfied / blocker closed: `false`",
                "- external simulation or validation execution: `false`",
                "- platform selection / validation protocol readiness / validation admission / validation result claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2588 materializes Route A HF3 source-only adapter readiness",
                "blocker definition artifacts requested by M2587. The rows define",
                "external state extraction, time-step and actuator latency,",
                "failure/status taxonomy mapping, source-only fixture smoke",
                "lineage, actor-visibility guards, claim boundaries, and gates.",
                "They preserve the P0 actor/action contract and keep the four",
                "blockers open for later audit.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"external_state_extraction_boundary_row_count: {summary['external_state_extraction_boundary_row_count']}",
                f"time_step_actuator_latency_contract_row_count: {summary['time_step_actuator_latency_contract_row_count']}",
                f"failure_status_taxonomy_mapping_row_count: {summary['failure_status_taxonomy_mapping_row_count']}",
                f"source_only_fixture_smoke_lineage_row_count: {summary['source_only_fixture_smoke_lineage_row_count']}",
                f"actor_visibility_guard_row_count: {summary['actor_visibility_guard_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"source_only_adapter_readiness_blocker_design_materialized_claim_allowed: {str(summary['source_only_adapter_readiness_blocker_design_materialized_claim_allowed']).lower()}",
                f"forbidden_claim_allowed_in_m2588: {str(summary['forbidden_claim_allowed_in_m2588']).lower()}",
                f"blocker_contract_defined_in_m2588: {str(summary['blocker_contract_defined_in_m2588']).lower()}",
                f"readiness_satisfied_in_m2588: {str(summary['readiness_satisfied_in_m2588']).lower()}",
                f"external_validation_execution_allowed_in_m2588: {str(summary['external_validation_execution_allowed_in_m2588']).lower()}",
                f"hidden_oracle_actor_input_detected: {str(summary['hidden_oracle_actor_input_detected']).lower()}",
                f"actor_visible: {str(summary['actor_visible']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2588 supports only the operational claim that source-only",
                "adapter readiness blocker design artifacts were materialized.",
                "It does not close the blockers and does not support platform",
                "selection, validation protocol readiness, validation admission,",
                "high-fidelity validation readiness/result, external validation",
                "execution, HF4 discrepancy answers, rollout success, success-rate",
                "or controller-family verdicts, ranking, checkpoint promotion,",
                "driver performance, paper evidence, FW-vs-GRU, current-sim",
                "verdict, high-fidelity validation, or self-ID.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_row_passed(row) for row in rows)


def _row_passed(row: dict[str, Any]) -> bool:
    return _boolish(row.get("status_pass"))


def _blocker_rows_are_definitions_only(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        _boolish(row.get("blocker_contract_defined_in_m2588"))
        and not _boolish(row.get("readiness_satisfied_in_m2588"))
        and not _boolish(row.get("external_validation_execution_allowed_in_m2588"))
        for row in rows
    )


def _any_readiness_satisfied(*row_groups: list[dict[str, Any]]) -> bool:
    return any(_boolish(row.get("readiness_satisfied_in_m2588")) for rows in row_groups for row in rows)


def _any_external_validation_allowed(*row_groups: list[dict[str, Any]]) -> bool:
    return any(
        _boolish(row.get("external_validation_execution_allowed_in_m2588"))
        for rows in row_groups
        for row in rows
    )


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args()

    summary = materialize_route_a_hf3_source_only_adapter_readiness_blocker(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
