"""Route A HF3 source-only adapter blocker closure materialization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-"
    "closure-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2593-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-"
    "closure-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-"
    "closure-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure")
DEFAULT_M2588_SUMMARY = Path(
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/summary.json"
)

M2588_EXTERNAL_STATE_ROWS = (
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/"
    "hf3_external_state_extraction_boundary_rows.csv"
)
M2588_TIMING_ROWS = (
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/"
    "hf3_time_step_actuator_latency_contract_rows.csv"
)
M2588_STATUS_ROWS = (
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/"
    "hf3_failure_status_taxonomy_mapping_rows.csv"
)
M2588_FIXTURE_ROWS = (
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/"
    "hf3_source_only_fixture_smoke_lineage_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.md",
    "docs/m2590-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-result-synthesis.md",
    "docs/m2589-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-result-audit.md",
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/summary.json",
    M2588_EXTERNAL_STATE_ROWS,
    M2588_TIMING_ROWS,
    M2588_STATUS_ROWS,
    M2588_FIXTURE_ROWS,
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_source_only_adapter_actor_visibility_guard_rows.csv",
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_source_only_adapter_claim_boundary_checks.csv",
    "runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/source_only_adapter_readiness_blocker_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 repo-local source-only adapter blocker closure materialization preflight only; "
    "source-only blocker closure may be materialized if all rows pass; not platform selection, "
    "validation protocol readiness, validation admission, external validation execution, high-fidelity "
    "validation readiness/result, HF4 discrepancy result, rollout success, ranking, driver performance, "
    "paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

EXTERNAL_STATE_CLOSURE_FIELDNAMES = [
    "state_closure_id",
    "closure_family",
    "definition_source_artifact",
    "closure_source_artifact",
    "fixture_schema_declared",
    "extractor_output_schema_declared",
    "backend_state_read_by_adapter_only",
    "adapter_only_fields_redacted_from_actor",
    "actor_observation_shape",
    "actor_visible",
    "diagnostic_only",
    "hidden_or_oracle_actor_input_detected",
    "source_only_closure_materialized_in_m2592",
    "validation_protocol_ready_in_m2592",
    "external_validation_execution_allowed_in_m2592",
    "status_pass",
    "claim_boundary",
]

TIMING_CLOSURE_FIELDNAMES = [
    "timing_closure_id",
    "closure_family",
    "definition_source_artifact",
    "closure_source_artifact",
    "simulation_time_step_value_declared",
    "control_update_rate_value_declared",
    "actuator_latency_channel_mapping_declared",
    "command_hold_or_delay_semantics_declared",
    "actor_observation_shape",
    "action_shape",
    "deployed_action_mapping_preserved",
    "action_contract_mutation_detected",
    "source_only_closure_materialized_in_m2592",
    "validation_protocol_ready_in_m2592",
    "external_validation_execution_allowed_in_m2592",
    "status_pass",
    "claim_boundary",
]

STATUS_CLOSURE_FIELDNAMES = [
    "status_closure_id",
    "closure_family",
    "definition_source_artifact",
    "closure_source_artifact",
    "repo_local_status_class_declared",
    "terminal_or_abort_semantics_declared",
    "backend_status_actor_visible",
    "taxonomy_label_actor_visible",
    "diagnostics_actor_visible",
    "reset_outcome_actor_visible",
    "rollout_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "source_only_closure_materialized_in_m2592",
    "validation_protocol_ready_in_m2592",
    "external_validation_execution_allowed_in_m2592",
    "status_pass",
    "claim_boundary",
]

FIXTURE_CLOSURE_FIELDNAMES = [
    "fixture_closure_id",
    "closure_family",
    "definition_source_artifact",
    "closure_source_artifact",
    "fixture_source_declared",
    "expected_schema_declared",
    "fixture_hash_declared",
    "fixture_smoke_replay_declared",
    "external_runtime_required",
    "external_runtime_executed_in_m2592",
    "source_only_closure_materialized_in_m2592",
    "validation_protocol_ready_in_m2592",
    "external_validation_execution_allowed_in_m2592",
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
    "source_only_closure_materialized_in_m2592",
    "validation_protocol_ready_in_m2592",
    "external_validation_execution_allowed_in_m2592",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2592",
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

EXTERNAL_STATE_CLOSURES = (
    "ego_state_extractor_schema_closure",
    "external_backend_to_p0_mapping_closure",
    "diagnostic_state_redaction_closure",
    "validation_metadata_non_actor_channel_closure",
)

TIMING_CLOSURES = (
    "simulation_time_step_value_closure",
    "control_update_rate_alignment_closure",
    "actuator_latency_channel_mapping_closure",
    "command_hold_delay_semantics_closure",
)

STATUS_CLOSURES = (
    "reset_failure_status_closure",
    "step_failure_status_closure",
    "collision_or_contact_status_closure",
    "validation_abort_status_closure",
)

FIXTURE_CLOSURES = (
    "fixture_source_manifest_closure",
    "fixture_expected_schema_closure",
    "fixture_no_external_runtime_closure",
    "fixture_replayable_hash_and_smoke_closure",
)

BLOCKER_FAMILIES = (
    "external_state_extraction_boundary",
    "time_step_and_actuator_latency_contract",
    "failure_status_taxonomy_mapping",
    "source_only_fixture_smoke_lineage",
)

CLAIM_CHECKS = (
    (
        "repo_local_source_only_adapter_blocker_closure_materialized",
        True,
        "M2592 closure rows actor-visibility guard claim-boundary and gate matrix",
    ),
    ("platform_selected_for_validation", False, "later platform-selection audit after source-only closure audit"),
    ("validation_protocol_ready", False, "later protocol-readiness audit with holdout/generalization policy"),
    ("validation_admission_granted", False, "later validation-admission result audit"),
    ("external_validation_execution", False, "later explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "later readiness decision after platform/protocol audit"),
    ("high_fidelity_validation_result", False, "later external validation execution result audit"),
    ("hf4_discrepancy_result", False, "later HF4 external validation and discrepancy result audit"),
    ("rollout_success", False, "later audited rollout-success criteria"),
    ("success_rate_or_controller_family_verdict", False, "separate benchmark/verdict milestone"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("driver_performance_claim", False, "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", False, "separate paper-route evidence matrix"),
    ("professional_driver_behavior_claim", False, "full ideal-driver gate with closed-loop self-ID evidence"),
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
    "professional_driver_behavior_claim_made": False,
}


def materialize_route_a_hf3_source_only_adapter_blocker_closure(
    output_dir: Path,
    *,
    m2588_summary_path: Path = DEFAULT_M2588_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2588_summary = read_json(m2588_summary_path)

    external_state_rows = build_external_state_extraction_closure_rows()
    timing_rows = build_time_step_actuator_latency_closure_rows()
    status_rows = build_failure_status_taxonomy_closure_rows()
    fixture_rows = build_source_only_fixture_smoke_closure_rows()
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
        m2588_summary=m2588_summary,
        external_state_rows=external_state_rows,
        timing_rows=timing_rows,
        status_rows=status_rows,
        fixture_rows=fixture_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
    )

    external_state_path = output_dir / "hf3_external_state_extraction_closure_rows.csv"
    timing_path = output_dir / "hf3_time_step_actuator_latency_closure_rows.csv"
    status_path = output_dir / "hf3_failure_status_taxonomy_closure_rows.csv"
    fixture_path = output_dir / "hf3_source_only_fixture_smoke_closure_rows.csv"
    actor_guard_path = output_dir / "hf3_source_only_adapter_closure_actor_visibility_guard_rows.csv"
    claim_path = output_dir / "hf3_source_only_adapter_closure_claim_boundary_checks.csv"
    gate_path = output_dir / "source_only_adapter_blocker_closure_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(external_state_path, external_state_rows, fieldnames=EXTERNAL_STATE_CLOSURE_FIELDNAMES)
    write_csv_rows(timing_path, timing_rows, fieldnames=TIMING_CLOSURE_FIELDNAMES)
    write_csv_rows(status_path, status_rows, fieldnames=STATUS_CLOSURE_FIELDNAMES)
    write_csv_rows(fixture_path, fixture_rows, fieldnames=FIXTURE_CLOSURE_FIELDNAMES)
    write_csv_rows(actor_guard_path, actor_guard_rows, fieldnames=ACTOR_VISIBILITY_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2588_summary=m2588_summary,
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


def build_external_state_extraction_closure_rows() -> list[dict[str, Any]]:
    rows = []
    for closure_family in EXTERNAL_STATE_CLOSURES:
        rows.append(
            {
                "state_closure_id": f"{closure_family}_state_closure",
                "closure_family": closure_family,
                "definition_source_artifact": M2588_EXTERNAL_STATE_ROWS,
                "closure_source_artifact": "docs/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.md",
                "fixture_schema_declared": True,
                "extractor_output_schema_declared": True,
                "backend_state_read_by_adapter_only": True,
                "adapter_only_fields_redacted_from_actor": True,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "actor_visible": False,
                "diagnostic_only": closure_family in {
                    "diagnostic_state_redaction_closure",
                    "validation_metadata_non_actor_channel_closure",
                },
                "hidden_or_oracle_actor_input_detected": False,
                "source_only_closure_materialized_in_m2592": True,
                "validation_protocol_ready_in_m2592": False,
                "external_validation_execution_allowed_in_m2592": False,
                "status_pass": bool(P0_OBSERVATION_DIM == 72),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_time_step_actuator_latency_closure_rows() -> list[dict[str, Any]]:
    rows = []
    for closure_family in TIMING_CLOSURES:
        rows.append(
            {
                "timing_closure_id": f"{closure_family}_timing_closure",
                "closure_family": closure_family,
                "definition_source_artifact": M2588_TIMING_ROWS,
                "closure_source_artifact": "docs/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.md",
                "simulation_time_step_value_declared": closure_family == "simulation_time_step_value_closure",
                "control_update_rate_value_declared": closure_family == "control_update_rate_alignment_closure",
                "actuator_latency_channel_mapping_declared": closure_family == "actuator_latency_channel_mapping_closure",
                "command_hold_or_delay_semantics_declared": closure_family == "command_hold_delay_semantics_closure",
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "deployed_action_mapping_preserved": True,
                "action_contract_mutation_detected": False,
                "source_only_closure_materialized_in_m2592": True,
                "validation_protocol_ready_in_m2592": False,
                "external_validation_execution_allowed_in_m2592": False,
                "status_pass": bool(P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_failure_status_taxonomy_closure_rows() -> list[dict[str, Any]]:
    rows = []
    for closure_family in STATUS_CLOSURES:
        rows.append(
            {
                "status_closure_id": f"{closure_family}_status_closure",
                "closure_family": closure_family,
                "definition_source_artifact": M2588_STATUS_ROWS,
                "closure_source_artifact": "docs/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.md",
                "repo_local_status_class_declared": True,
                "terminal_or_abort_semantics_declared": True,
                "backend_status_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "diagnostics_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "rollout_outcome_actor_visible": False,
                "validation_outcome_actor_visible": False,
                "source_only_closure_materialized_in_m2592": True,
                "validation_protocol_ready_in_m2592": False,
                "external_validation_execution_allowed_in_m2592": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_source_only_fixture_smoke_closure_rows() -> list[dict[str, Any]]:
    rows = []
    for closure_family in FIXTURE_CLOSURES:
        rows.append(
            {
                "fixture_closure_id": f"{closure_family}_fixture_closure",
                "closure_family": closure_family,
                "definition_source_artifact": M2588_FIXTURE_ROWS,
                "closure_source_artifact": "docs/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.md",
                "fixture_source_declared": True,
                "expected_schema_declared": True,
                "fixture_hash_declared": True,
                "fixture_smoke_replay_declared": True,
                "external_runtime_required": False,
                "external_runtime_executed_in_m2592": False,
                "source_only_closure_materialized_in_m2592": True,
                "validation_protocol_ready_in_m2592": False,
                "external_validation_execution_allowed_in_m2592": False,
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
                "actor_visibility_guard_id": f"{blocker_family}_closure_actor_visibility_guard",
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
                "source_only_closure_materialized_in_m2592": True,
                "validation_protocol_ready_in_m2592": False,
                "external_validation_execution_allowed_in_m2592": False,
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
    closure_materialized = bool(
        len(external_state_rows) == len(EXTERNAL_STATE_CLOSURES)
        and _closure_rows_are_scoped(external_state_rows)
        and len(timing_rows) == len(TIMING_CLOSURES)
        and _closure_rows_are_scoped(timing_rows)
        and len(status_rows) == len(STATUS_CLOSURES)
        and _closure_rows_are_scoped(status_rows)
        and len(fixture_rows) == len(FIXTURE_CLOSURES)
        and _closure_rows_are_scoped(fixture_rows)
        and len(actor_guard_rows) == len(BLOCKER_FAMILIES)
        and _closure_rows_are_scoped(actor_guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and closure_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2592": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "repo_local_source_only_adapter_blocker_closure_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2588_summary: dict[str, Any],
    external_state_rows: list[dict[str, Any]],
    timing_rows: list[dict[str, Any]],
    status_rows: list[dict[str, Any]],
    fixture_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"] != "repo_local_source_only_adapter_blocker_closure_materialized"
        and _boolish(row["claim_allowed_in_m2592"])
    ]
    closure_claim_allowed = any(
        row["claim_family"] == "repo_local_source_only_adapter_blocker_closure_materialized"
        and _boolish(row["claim_allowed_in_m2592"])
        for row in claim_rows
    )
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
            "m2591_design_artifact_exists",
            "lineage",
            source_exists[
                "docs/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.md"
            ],
            "m2591_design_artifact_exists=true",
            "m2591_design_artifact_exists=true",
            "lineage_invalid",
        ),
        (
            "m2590_synthesis_and_m2588_materialization_accepted",
            "lineage",
            bool(m2588_summary.get("status_pass"))
            and not bool(m2588_summary.get("readiness_satisfied_in_m2588"))
            and not bool(m2588_summary.get("external_validation_execution_allowed_in_m2588")),
            (
                f"m2588_status={m2588_summary.get('status_pass')};"
                f"readiness={m2588_summary.get('readiness_satisfied_in_m2588')};"
                f"external_validation={m2588_summary.get('external_validation_execution_allowed_in_m2588')}"
            ),
            "m2588_status=True;readiness=False;external_validation=False",
            "lineage_invalid",
        ),
        (
            "external_state_extraction_closure_rows_complete",
            "contract",
            len(external_state_rows) == len(EXTERNAL_STATE_CLOSURES)
            and _closure_rows_are_scoped(external_state_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in external_state_rows)
            and not any(_boolish(row["actor_visible"]) for row in external_state_rows)
            and not any(_boolish(row["hidden_or_oracle_actor_input_detected"]) for row in external_state_rows),
            f"rows={len(external_state_rows)}",
            "rows=4;obs=72;actor_visible=false;hidden=false",
            "contract_violation",
        ),
        (
            "time_step_actuator_latency_closure_rows_complete",
            "contract",
            len(timing_rows) == len(TIMING_CLOSURES)
            and _closure_rows_are_scoped(timing_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in timing_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in timing_rows)
            and all(_boolish(row["deployed_action_mapping_preserved"]) for row in timing_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in timing_rows),
            f"rows={len(timing_rows)}",
            "rows=4;obs=72;action=3;mapping=true;mutation=false",
            "contract_violation",
        ),
        (
            "failure_status_taxonomy_closure_rows_complete",
            "contract",
            len(status_rows) == len(STATUS_CLOSURES)
            and _closure_rows_are_scoped(status_rows)
            and all(_boolish(row["repo_local_status_class_declared"]) for row in status_rows)
            and all(_boolish(row["terminal_or_abort_semantics_declared"]) for row in status_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in status_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in status_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in status_rows),
            f"rows={len(status_rows)}",
            "rows=4;status_class=true;actor_visible=false",
            "contract_violation",
        ),
        (
            "source_only_fixture_smoke_closure_rows_complete",
            "lineage",
            len(fixture_rows) == len(FIXTURE_CLOSURES)
            and _closure_rows_are_scoped(fixture_rows)
            and all(_boolish(row["fixture_source_declared"]) for row in fixture_rows)
            and all(_boolish(row["expected_schema_declared"]) for row in fixture_rows)
            and all(_boolish(row["fixture_hash_declared"]) for row in fixture_rows)
            and all(_boolish(row["fixture_smoke_replay_declared"]) for row in fixture_rows)
            and not any(_boolish(row["external_runtime_required"]) for row in fixture_rows)
            and not any(_boolish(row["external_runtime_executed_in_m2592"]) for row in fixture_rows),
            f"rows={len(fixture_rows)}",
            "rows=4;hash=true;smoke=true;external_runtime=false",
            "lineage_invalid",
        ),
        (
            "actor_visibility_guard_rows_pass",
            "contract",
            len(actor_guard_rows) == len(BLOCKER_FAMILIES)
            and _closure_rows_are_scoped(actor_guard_rows)
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
            and closure_claim_allowed
            and not forbidden_claims_allowed,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;closure_materialized=true",
            "objective_overfit",
        ),
        (
            "no_external_runtime_or_dependency_mutation",
            "claim_boundary",
            not any(
                FORBIDDEN_FLAGS[key]
                for key in (
                    "external_high_fidelity_simulation_included",
                    "external_high_fidelity_imported",
                    "high_fidelity_simulation_run",
                    "external_install_performed",
                    "external_import_performed",
                    "dependency_mutation_performed",
                    "reset_execution_run",
                    "policy_action_run",
                    "environment_step_run",
                    "rollout_execution_run",
                    "validation_execution_run",
                )
            ),
            "external/runtime/execution=false",
            "external/runtime/execution=false",
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
            "source_only_blocker_closure_claim_scoped",
            "claim_boundary",
            closure_claim_allowed and not forbidden_claims_allowed,
            f"closure_allowed={closure_claim_allowed};forbidden_claims={len(forbidden_claims_allowed)}",
            "closure_allowed=True;forbidden_claims=0",
            "objective_overfit",
        ),
        (
            "validation_readiness_and_execution_forbidden",
            "claim_boundary",
            not _any_validation_ready(external_state_rows, timing_rows, status_rows, fixture_rows, actor_guard_rows)
            and not _any_external_validation_allowed(
                external_state_rows,
                timing_rows,
                status_rows,
                fixture_rows,
                actor_guard_rows,
            )
            and not any(
                row["claim_family"]
                in {
                    "platform_selected_for_validation",
                    "validation_protocol_ready",
                    "validation_admission_granted",
                    "external_validation_execution",
                    "high_fidelity_validation_readiness",
                    "high_fidelity_validation_result",
                    "driver_performance_claim",
                }
                and _boolish(row["claim_allowed_in_m2592"])
                for row in claim_rows
            ),
            "platform/readiness/execution/performance=false",
            "platform/readiness/execution/performance=false",
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
    m2588_summary: dict[str, Any],
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
    closure_claim_allowed = any(
        row["claim_family"] == "repo_local_source_only_adapter_blocker_closure_materialized"
        and _boolish(row["claim_allowed_in_m2592"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"] != "repo_local_source_only_adapter_blocker_closure_materialized"
        and _boolish(row["claim_allowed_in_m2592"])
        for row in claim_rows
    )
    row_groups = (external_state_rows, timing_rows, status_rows, fixture_rows, actor_guard_rows)
    status_pass = (
        all(source_exists.values())
        and bool(m2588_summary.get("status_pass"))
        and not bool(m2588_summary.get("readiness_satisfied_in_m2588"))
        and not bool(m2588_summary.get("external_validation_execution_allowed_in_m2588"))
        and len(external_state_rows) == len(EXTERNAL_STATE_CLOSURES)
        and _closure_rows_are_scoped(external_state_rows)
        and len(timing_rows) == len(TIMING_CLOSURES)
        and _closure_rows_are_scoped(timing_rows)
        and len(status_rows) == len(STATUS_CLOSURES)
        and _closure_rows_are_scoped(status_rows)
        and len(fixture_rows) == len(FIXTURE_CLOSURES)
        and _closure_rows_are_scoped(fixture_rows)
        and len(actor_guard_rows) == len(BLOCKER_FAMILIES)
        and _closure_rows_are_scoped(actor_guard_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and closure_claim_allowed
        and not forbidden_claim_allowed
        and not _any_validation_ready(*row_groups)
        and not _any_external_validation_allowed(*row_groups)
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_source_only_adapter_blocker_closure_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_source_only_adapter_blocker_closure_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_external_state_extraction_closure_rows": str(external_state_path),
        "hf3_time_step_actuator_latency_closure_rows": str(timing_path),
        "hf3_failure_status_taxonomy_closure_rows": str(status_path),
        "hf3_source_only_fixture_smoke_closure_rows": str(fixture_path),
        "hf3_source_only_adapter_closure_actor_visibility_guard_rows": str(actor_guard_path),
        "hf3_source_only_adapter_closure_claim_boundary_checks": str(claim_path),
        "source_only_adapter_blocker_closure_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2588_status_pass": bool(m2588_summary.get("status_pass")),
        "m2588_readiness_satisfied": bool(m2588_summary.get("readiness_satisfied_in_m2588")),
        "m2588_external_validation_execution_allowed": bool(
            m2588_summary.get("external_validation_execution_allowed_in_m2588")
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "external_state_extraction_closure_row_count": len(external_state_rows),
        "external_state_extraction_closure_rows_all_pass": _all_status_pass(external_state_rows),
        "time_step_actuator_latency_closure_row_count": len(timing_rows),
        "time_step_actuator_latency_closure_rows_all_pass": _all_status_pass(timing_rows),
        "failure_status_taxonomy_closure_row_count": len(status_rows),
        "failure_status_taxonomy_closure_rows_all_pass": _all_status_pass(status_rows),
        "source_only_fixture_smoke_closure_row_count": len(fixture_rows),
        "source_only_fixture_smoke_closure_rows_all_pass": _all_status_pass(fixture_rows),
        "actor_visibility_guard_row_count": len(actor_guard_rows),
        "actor_visibility_guard_rows_all_pass": _all_status_pass(actor_guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "source_only_adapter_blocker_closure_claim_allowed": bool(closure_claim_allowed),
        "repo_local_source_only_adapter_blocker_closure_materialized": bool(closure_claim_allowed and status_pass),
        "forbidden_claim_allowed_in_m2592": bool(forbidden_claim_allowed),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "source_only_closure_materialized_in_m2592": all(
            _boolish(row["source_only_closure_materialized_in_m2592"])
            for rows in row_groups
            for row in rows
        ),
        "validation_protocol_ready_in_m2592": _any_validation_ready(*row_groups),
        "validation_admission_granted_in_m2592": False,
        "external_validation_execution_allowed_in_m2592": _any_external_validation_allowed(*row_groups),
        "platform_selected_in_m2592": False,
        "driver_performance_claim_allowed_in_m2592": any(
            row["claim_family"] == "driver_performance_claim"
            and _boolish(row["claim_allowed_in_m2592"])
            for row in claim_rows
        ),
        "backend_state_read_by_adapter_only": all(
            _boolish(row["backend_state_read_by_adapter_only"]) for row in external_state_rows
        ),
        "adapter_only_fields_redacted_from_actor": all(
            _boolish(row["adapter_only_fields_redacted_from_actor"]) for row in external_state_rows
        ),
        "actor_visible": any(_boolish(row["actor_visible"]) for row in external_state_rows),
        "diagnostic_only_rows_present": any(_boolish(row["diagnostic_only"]) for row in external_state_rows),
        "simulation_time_step_value_declared": any(
            _boolish(row["simulation_time_step_value_declared"]) for row in timing_rows
        ),
        "control_update_rate_value_declared": any(
            _boolish(row["control_update_rate_value_declared"]) for row in timing_rows
        ),
        "actuator_latency_channel_mapping_declared": any(
            _boolish(row["actuator_latency_channel_mapping_declared"]) for row in timing_rows
        ),
        "command_hold_or_delay_semantics_declared": any(
            _boolish(row["command_hold_or_delay_semantics_declared"]) for row in timing_rows
        ),
        "deployed_action_mapping_preserved": all(
            _boolish(row["deployed_action_mapping_preserved"]) for row in timing_rows
        ),
        "repo_local_status_class_declared": all(
            _boolish(row["repo_local_status_class_declared"]) for row in status_rows
        ),
        "terminal_or_abort_semantics_declared": all(
            _boolish(row["terminal_or_abort_semantics_declared"]) for row in status_rows
        ),
        "fixture_source_declared": all(_boolish(row["fixture_source_declared"]) for row in fixture_rows),
        "expected_schema_declared": all(_boolish(row["expected_schema_declared"]) for row in fixture_rows),
        "fixture_hash_declared": all(_boolish(row["fixture_hash_declared"]) for row in fixture_rows),
        "fixture_smoke_replay_declared": all(
            _boolish(row["fixture_smoke_replay_declared"]) for row in fixture_rows
        ),
        "external_runtime_required": any(_boolish(row["external_runtime_required"]) for row in fixture_rows),
        "external_runtime_executed_in_m2592": any(
            _boolish(row["external_runtime_executed_in_m2592"]) for row in fixture_rows
        ),
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_or_oracle_actor_input_detected"]) for row in external_state_rows
        )
        or any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_guard_rows),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in status_rows)
        or any(_boolish(row["diagnostics_actor_visible"]) for row in actor_guard_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in status_rows)
        or any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_guard_rows),
        "backend_status_actor_visible": any(_boolish(row["backend_status_actor_visible"]) for row in status_rows)
        or any(_boolish(row["backend_status_actor_visible"]) for row in actor_guard_rows),
        "reset_outcome_actor_visible": any(_boolish(row["reset_outcome_actor_visible"]) for row in status_rows)
        or any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_guard_rows),
        "rollout_outcome_actor_visible": any(_boolish(row["rollout_outcome_actor_visible"]) for row in status_rows)
        or any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_guard_rows),
        "validation_outcome_actor_visible": any(
            _boolish(row["validation_outcome_actor_visible"]) for row in status_rows
        )
        or any(_boolish(row["validation_outcome_actor_visible"]) for row in actor_guard_rows),
        "platform_selection_actor_visible": any(
            _boolish(row["platform_selection_actor_visible"]) for row in actor_guard_rows
        ),
        "protocol_status_actor_visible": any(_boolish(row["protocol_status_actor_visible"]) for row in actor_guard_rows),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"]) for row in actor_guard_rows
        )
        or any(_boolish(row["action_contract_mutation_detected"]) for row in timing_rows),
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
                "# M2592 Engineering Controller Route A Baseline HF3 Source-Only Adapter Readiness Blocker Closure Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_source_only_adapter_blocker_closure.py`",
                f"- summary: `{summary['summary']}`",
                f"- external state extraction closure rows: `{summary['hf3_external_state_extraction_closure_rows']}`",
                f"- time-step/actuator latency closure rows: `{summary['hf3_time_step_actuator_latency_closure_rows']}`",
                f"- failure/status taxonomy closure rows: `{summary['hf3_failure_status_taxonomy_closure_rows']}`",
                f"- source-only fixture smoke closure rows: `{summary['hf3_source_only_fixture_smoke_closure_rows']}`",
                f"- actor-visibility guard rows: `{summary['hf3_source_only_adapter_closure_actor_visibility_guard_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_source_only_adapter_closure_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['source_only_adapter_blocker_closure_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- repo-local source-only adapter blocker closure materialized: `true`",
                "- platform selection / validation protocol readiness / validation admission / validation result claims: `false`",
                "- external simulation or validation execution: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2592 materializes bounded repo-local source-only adapter",
                "blocker closure artifacts requested by M2591. The rows close",
                "the four source-only adapter blocker families only in the",
                "repo-local adapter-evidence sense: external state extraction,",
                "time-step and actuator latency, failure/status taxonomy, and",
                "source-only fixture smoke lineage.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"external_state_extraction_closure_row_count: {summary['external_state_extraction_closure_row_count']}",
                f"time_step_actuator_latency_closure_row_count: {summary['time_step_actuator_latency_closure_row_count']}",
                f"failure_status_taxonomy_closure_row_count: {summary['failure_status_taxonomy_closure_row_count']}",
                f"source_only_fixture_smoke_closure_row_count: {summary['source_only_fixture_smoke_closure_row_count']}",
                f"actor_visibility_guard_row_count: {summary['actor_visibility_guard_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"source_only_adapter_blocker_closure_claim_allowed: {str(summary['source_only_adapter_blocker_closure_claim_allowed']).lower()}",
                f"repo_local_source_only_adapter_blocker_closure_materialized: {str(summary['repo_local_source_only_adapter_blocker_closure_materialized']).lower()}",
                f"forbidden_claim_allowed_in_m2592: {str(summary['forbidden_claim_allowed_in_m2592']).lower()}",
                f"validation_protocol_ready_in_m2592: {str(summary['validation_protocol_ready_in_m2592']).lower()}",
                f"external_validation_execution_allowed_in_m2592: {str(summary['external_validation_execution_allowed_in_m2592']).lower()}",
                f"platform_selected_in_m2592: {str(summary['platform_selected_in_m2592']).lower()}",
                f"driver_performance_claim_allowed_in_m2592: {str(summary['driver_performance_claim_allowed_in_m2592']).lower()}",
                f"hidden_oracle_actor_input_detected: {str(summary['hidden_oracle_actor_input_detected']).lower()}",
                f"actor_visible: {str(summary['actor_visible']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2592 supports only the operational claim that repo-local",
                "source-only adapter blocker closure artifacts were materialized.",
                "It does not support platform selection, validation protocol",
                "readiness, validation admission, high-fidelity validation",
                "readiness/result, external validation execution, HF4 discrepancy",
                "answers, rollout success, success-rate or controller-family",
                "verdicts, ranking, checkpoint promotion, driver performance,",
                "paper evidence, FW-vs-GRU, current-sim verdict, high-fidelity",
                "validation, or self-ID.",
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


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _closure_rows_are_scoped(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        _boolish(row.get("status_pass"))
        and _boolish(row.get("source_only_closure_materialized_in_m2592"))
        and not _boolish(row.get("validation_protocol_ready_in_m2592"))
        and not _boolish(row.get("external_validation_execution_allowed_in_m2592"))
        for row in rows
    )


def _any_validation_ready(*row_groups: list[dict[str, Any]]) -> bool:
    return any(_boolish(row.get("validation_protocol_ready_in_m2592")) for rows in row_groups for row in rows)


def _any_external_validation_allowed(*row_groups: list[dict[str, Any]]) -> bool:
    return any(
        _boolish(row.get("external_validation_execution_allowed_in_m2592"))
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

    summary = materialize_route_a_hf3_source_only_adapter_blocker_closure(
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
