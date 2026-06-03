"""Route A HF3 validation-readiness boundary materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2577-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary")
DEFAULT_M2572_SUMMARY = Path(
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json"
)
DEFAULT_M2572_REQUESTS = Path(
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_request_rows.csv"
)
DEFAULT_M2572_ACTOR_VIEW_ROWS = Path(
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_actor_view_contract_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2575-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-design.md",
    "docs/m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis.md",
    "docs/m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit.md",
    "docs/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.md",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_request_rows.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_fixed_policy_source_rows.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_plan_rows.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_policy_action_audit_rows.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_backend_step_outcome_rows.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_actor_view_contract_rows.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_claim_boundary_checks.csv",
    "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/rollout_feasibility_gate_matrix.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 validation-readiness boundary materialization preflight only; "
    "boundary artifacts may be materialized; not validation admission, "
    "external simulation, validation execution, validation readiness/result, "
    "rollout success, ranking, driver performance, paper, FW-vs-GRU, "
    "current-sim verdict, high-fidelity validation, or self-ID"
)

READINESS_REQUEST_FIELDNAMES = [
    "readiness_request_id",
    "source_rollout_request_id",
    "route_role_id",
    "candidate_role_label",
    "actor_observation_shape",
    "action_shape",
    "accepted_feasibility_evidence",
    "validation_admission_allowed",
    "validation_execution_allowed_in_m2576",
    "external_simulation_allowed_in_m2576",
    "status_pass",
    "claim_boundary",
]

EVIDENCE_ADMISSION_FIELDNAMES = [
    "evidence_admission_id",
    "readiness_request_id",
    "source_artifact",
    "source_evidence_type",
    "accepted_as_boundary_input",
    "accepted_as_validation_result",
    "accepted_as_driver_performance",
    "accepted_as_ranking_evidence",
    "status_pass",
    "claim_boundary",
]

PLATFORM_BOUNDARY_FIELDNAMES = [
    "platform_boundary_id",
    "platform_layer",
    "platform_scope",
    "repo_local_adapter_evidence_allowed",
    "external_high_fidelity_execution_allowed_in_m2576",
    "external_validation_result_allowed",
    "preferred_future_platform_direction",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_POLICY_FIELDNAMES = [
    "dependency_policy_id",
    "dependency_family",
    "install_allowed_in_m2576",
    "import_allowed_in_m2576",
    "runtime_execution_allowed_in_m2576",
    "dependency_mutation_allowed_in_m2576",
    "future_validation_allowed_after_readiness_audit",
    "status_pass",
    "claim_boundary",
]

DISCREPANCY_QUESTION_FIELDNAMES = [
    "discrepancy_question_id",
    "route_role_id",
    "hf4_question",
    "requires_external_validation_execution",
    "answer_allowed_in_m2576",
    "driver_performance_claim_allowed",
    "status_pass",
    "claim_boundary",
]
DISCREPANCY_FIELDNAMES = DISCREPANCY_QUESTION_FIELDNAMES

ACTOR_INPUT_ISOLATION_FIELDNAMES = [
    "actor_input_isolation_id",
    "readiness_request_id",
    "actor_observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "rollout_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "status_pass",
    "claim_boundary",
]
ACTOR_INPUT_FIELDNAMES = ACTOR_INPUT_ISOLATION_FIELDNAMES

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2576",
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

EVIDENCE_SOURCES = (
    (
        "m2572_rollout_feasibility_execution_summary",
        "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json",
    ),
    (
        "m2572_policy_action_audit_rows",
        "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_policy_action_audit_rows.csv",
    ),
    (
        "m2572_backend_step_outcome_rows",
        "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_backend_step_outcome_rows.csv",
    ),
    (
        "m2572_actor_view_contract_rows",
        "runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_actor_view_contract_rows.csv",
    ),
    (
        "m2573_result_audit",
        "docs/m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit.md",
    ),
    (
        "m2574_result_synthesis",
        "docs/m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis.md",
    ),
)

PLATFORM_LAYERS = (
    (
        "repo_local_current_sim_adapter",
        "admitted only as repo-local feasibility/readiness-boundary input",
        True,
        False,
        False,
        "internal adapter evidence for readiness boundaries only",
    ),
    (
        "external_high_fidelity_vehicle_dynamics_layer",
        "future validation execution layer after readiness audit",
        False,
        False,
        False,
        "open auditable vehicle dynamics backend such as Chrono/Chrono::Vehicle",
    ),
    (
        "future_hf4_discrepancy_report_layer",
        "future report comparing current-sim and higher-fidelity behavior",
        False,
        False,
        False,
        "requires later audited external validation evidence",
    ),
)

DEPENDENCY_POLICIES = (
    ("chrono_vehicle_or_equivalent_open_backend", True),
    ("black_box_industry_demonstration_backend", False),
    ("repo_local_current_sim_backend", True),
)

HF4_QUESTIONS = (
    "current_sim_failure_reproduces",
    "current_sim_failure_disappears",
    "new_high_fidelity_failure_appears",
    "current_sim_remains_valid_mining_layer",
)

CLAIM_CHECKS = (
    ("validation_readiness_boundary_materialized", True, "M2576 static boundary rows and gate matrix"),
    ("validation_admission", False, "later validation-admission audit"),
    ("external_validation_execution", False, "later explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "audited boundary plus explicit readiness decision"),
    ("high_fidelity_validation_result", False, "later external validation result audit"),
    ("rollout_success", False, "later audited rollout-success criteria"),
    ("success_rate_or_controller_family_verdict", False, "separate benchmark/verdict milestone"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("driver_performance_claim", False, "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", False, "separate paper-route evidence matrix"),
    ("hf4_discrepancy_result", False, "later HF4 external validation and discrepancy result audit"),
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
}


def materialize_route_a_hf3_validation_readiness_boundary(
    output_dir: Path,
    *,
    m2572_summary_path: Path = DEFAULT_M2572_SUMMARY,
    m2572_requests_path: Path = DEFAULT_M2572_REQUESTS,
    m2572_actor_view_rows_path: Path = DEFAULT_M2572_ACTOR_VIEW_ROWS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2572_summary = read_json(m2572_summary_path)
    rollout_request_rows = _read_csv_rows(m2572_requests_path)
    actor_view_contract_rows = _read_csv_rows(m2572_actor_view_rows_path)

    readiness_rows = build_readiness_request_rows(rollout_request_rows)
    evidence_rows = build_evidence_admission_rows(readiness_rows)
    platform_rows = build_platform_boundary_rows()
    dependency_rows = build_dependency_policy_rows()
    discrepancy_rows = build_discrepancy_question_rows(readiness_rows)
    actor_input_rows = build_actor_input_isolation_rows(readiness_rows, actor_view_contract_rows)
    claim_rows = build_claim_boundary_checks(
        readiness_rows,
        evidence_rows,
        platform_rows,
        dependency_rows,
        discrepancy_rows,
        actor_input_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2572_summary=m2572_summary,
        readiness_rows=readiness_rows,
        evidence_rows=evidence_rows,
        platform_rows=platform_rows,
        dependency_rows=dependency_rows,
        discrepancy_rows=discrepancy_rows,
        actor_input_rows=actor_input_rows,
        claim_rows=claim_rows,
    )

    readiness_path = output_dir / "hf3_validation_readiness_request_rows.csv"
    evidence_path = output_dir / "hf3_evidence_admission_rows.csv"
    platform_path = output_dir / "hf3_platform_boundary_rows.csv"
    dependency_path = output_dir / "hf3_dependency_policy_rows.csv"
    discrepancy_path = output_dir / "hf3_scenario_discrepancy_question_rows.csv"
    actor_input_path = output_dir / "hf3_actor_input_isolation_rows.csv"
    claim_path = output_dir / "hf3_claim_boundary_checks.csv"
    gate_path = output_dir / "validation_readiness_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(readiness_path, readiness_rows, fieldnames=READINESS_REQUEST_FIELDNAMES)
    write_csv_rows(evidence_path, evidence_rows, fieldnames=EVIDENCE_ADMISSION_FIELDNAMES)
    write_csv_rows(platform_path, platform_rows, fieldnames=PLATFORM_BOUNDARY_FIELDNAMES)
    write_csv_rows(dependency_path, dependency_rows, fieldnames=DEPENDENCY_POLICY_FIELDNAMES)
    write_csv_rows(discrepancy_path, discrepancy_rows, fieldnames=DISCREPANCY_QUESTION_FIELDNAMES)
    write_csv_rows(actor_input_path, actor_input_rows, fieldnames=ACTOR_INPUT_ISOLATION_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2572_summary=m2572_summary,
        readiness_rows=readiness_rows,
        evidence_rows=evidence_rows,
        platform_rows=platform_rows,
        dependency_rows=dependency_rows,
        discrepancy_rows=discrepancy_rows,
        actor_input_rows=actor_input_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        readiness_path=readiness_path,
        evidence_path=evidence_path,
        platform_path=platform_path,
        dependency_path=dependency_path,
        discrepancy_path=discrepancy_path,
        actor_input_path=actor_input_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_readiness_request_rows(rollout_request_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for request in sorted(rollout_request_rows, key=lambda row: row["rollout_request_id"]):
        obs_shape = _int_value(request.get("actor_observation_shape"), default=-1)
        action_shape = _int_value(request.get("action_shape"), default=-1)
        rows.append(
            {
                "readiness_request_id": request["rollout_request_id"].replace(
                    "_hf3_rollout_request", "_validation_readiness_request"
                ),
                "source_rollout_request_id": request["rollout_request_id"],
                "route_role_id": request["route_role_id"],
                "candidate_role_label": request["route_role_id"].replace("_", " "),
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "accepted_feasibility_evidence": bool(_row_passed(request)),
                "validation_admission_allowed": False,
                "validation_execution_allowed_in_m2576": False,
                "external_simulation_allowed_in_m2576": False,
                "status_pass": bool(
                    _row_passed(request)
                    and obs_shape == P0_OBSERVATION_DIM
                    and action_shape == ACTION_DIM
                    and not _boolish(request.get("pilot_admission_allowed"))
                    and not _boolish(request.get("validation_claim_allowed"))
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_evidence_admission_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for readiness in readiness_rows:
        for evidence_type, source_artifact in EVIDENCE_SOURCES:
            rows.append(
                {
                    "evidence_admission_id": f"{readiness['readiness_request_id']}_{evidence_type}",
                    "readiness_request_id": readiness["readiness_request_id"],
                    "source_artifact": source_artifact,
                    "source_evidence_type": evidence_type,
                    "accepted_as_boundary_input": True,
                    "accepted_as_validation_result": False,
                    "accepted_as_driver_performance": False,
                    "accepted_as_ranking_evidence": False,
                    "status_pass": bool(_row_passed(readiness) and Path(source_artifact).exists()),
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def build_platform_boundary_rows() -> list[dict[str, Any]]:
    rows = []
    for layer, scope, repo_local_allowed, external_allowed, result_allowed, future_direction in PLATFORM_LAYERS:
        rows.append(
            {
                "platform_boundary_id": f"{layer}_platform_boundary",
                "platform_layer": layer,
                "platform_scope": scope,
                "repo_local_adapter_evidence_allowed": repo_local_allowed,
                "external_high_fidelity_execution_allowed_in_m2576": external_allowed,
                "external_validation_result_allowed": result_allowed,
                "preferred_future_platform_direction": future_direction,
                "status_pass": bool(not external_allowed and not result_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_dependency_policy_rows() -> list[dict[str, Any]]:
    rows = []
    for dependency_family, future_allowed in DEPENDENCY_POLICIES:
        rows.append(
            {
                "dependency_policy_id": f"{dependency_family}_dependency_policy",
                "dependency_family": dependency_family,
                "install_allowed_in_m2576": False,
                "import_allowed_in_m2576": False,
                "runtime_execution_allowed_in_m2576": False,
                "dependency_mutation_allowed_in_m2576": False,
                "future_validation_allowed_after_readiness_audit": bool(future_allowed),
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_discrepancy_question_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for readiness in readiness_rows:
        for question in HF4_QUESTIONS:
            rows.append(
                {
                    "discrepancy_question_id": f"{readiness['readiness_request_id']}_{question}",
                    "route_role_id": readiness["route_role_id"],
                    "hf4_question": question,
                    "requires_external_validation_execution": True,
                    "answer_allowed_in_m2576": False,
                    "driver_performance_claim_allowed": False,
                    "status_pass": bool(_row_passed(readiness)),
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def build_actor_input_isolation_rows(
    readiness_rows: list[dict[str, Any]],
    actor_view_contract_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    actor_view_contract_rows = actor_view_contract_rows or []
    actor_rows_by_request: dict[str, list[dict[str, Any]]] = {}
    for actor_row in actor_view_contract_rows:
        actor_rows_by_request.setdefault(str(actor_row.get("rollout_request_id", "")), []).append(actor_row)
    for readiness in readiness_rows:
        source_rows = actor_rows_by_request.get(str(readiness["source_rollout_request_id"]), [])
        source_rows_pass = True
        if actor_view_contract_rows:
            source_rows_pass = bool(source_rows) and _all_status_pass(source_rows) and _actor_view_rows_are_isolated(source_rows)
        rows.append(
            {
                "actor_input_isolation_id": f"{readiness['readiness_request_id']}_actor_input_isolation",
                "readiness_request_id": readiness["readiness_request_id"],
                "actor_observation_shape": _int_value(readiness["actor_observation_shape"], default=-1),
                "action_shape": _int_value(readiness["action_shape"], default=-1),
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "rollout_outcome_actor_visible": False,
                "validation_outcome_actor_visible": False,
                "status_pass": bool(
                    _row_passed(readiness)
                    and source_rows_pass
                    and _int_value(readiness["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM
                    and _int_value(readiness["action_shape"], default=-1) == ACTION_DIM
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    readiness_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    platform_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    discrepancy_rows: list[dict[str, Any]] | None = None,
    actor_input_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    require_discrepancy_rows = discrepancy_rows is not None
    require_actor_input_rows = actor_input_rows is not None
    discrepancy_rows = discrepancy_rows or []
    actor_input_rows = actor_input_rows or []
    boundary_materialized = bool(
        len(readiness_rows) == 2
        and _all_status_pass(readiness_rows)
        and _all_status_pass(evidence_rows)
        and _all_status_pass(platform_rows)
        and _all_status_pass(dependency_rows)
        and (not require_discrepancy_rows or _all_status_pass(discrepancy_rows))
        and (not require_actor_input_rows or _all_status_pass(actor_input_rows))
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and boundary_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2576": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "validation_readiness_boundary_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2572_summary: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    platform_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    discrepancy_rows: list[dict[str, Any]],
    actor_input_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"] != "validation_readiness_boundary_materialized"
        and _boolish(row["claim_allowed_in_m2576"])
    ]
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()) and bool(m2572_summary.get("status_pass")),
            f"missing={sum(1 for exists in source_exists.values() if not exists)};m2572_status={m2572_summary.get('status_pass')}",
            "missing=0;m2572_status=True",
            "lineage_invalid",
        ),
        (
            "validation_readiness_request_rows_complete",
            "scenario",
            len(readiness_rows) == 2
            and _all_status_pass(readiness_rows)
            and not any(_boolish(row["validation_admission_allowed"]) for row in readiness_rows)
            and not any(_boolish(row["validation_execution_allowed_in_m2576"]) for row in readiness_rows)
            and not any(_boolish(row["external_simulation_allowed_in_m2576"]) for row in readiness_rows),
            f"rows={len(readiness_rows)}",
            "rows=2;validation_admission=false;validation_execution=false;external=false",
            "scenario_sampling_failure",
        ),
        (
            "evidence_admission_rows_pass",
            "lineage",
            len(evidence_rows) == len(readiness_rows) * len(EVIDENCE_SOURCES)
            and _all_status_pass(evidence_rows)
            and all(_boolish(row["accepted_as_boundary_input"]) for row in evidence_rows)
            and not any(_boolish(row["accepted_as_validation_result"]) for row in evidence_rows)
            and not any(_boolish(row["accepted_as_driver_performance"]) for row in evidence_rows)
            and not any(_boolish(row["accepted_as_ranking_evidence"]) for row in evidence_rows),
            f"rows={len(evidence_rows)}",
            f"rows={len(readiness_rows) * len(EVIDENCE_SOURCES)};boundary_input=true;claims=false",
            "lineage_invalid",
        ),
        (
            "platform_boundary_rows_pass",
            "contract",
            len(platform_rows) == len(PLATFORM_LAYERS)
            and _all_status_pass(platform_rows)
            and not any(_boolish(row["external_high_fidelity_execution_allowed_in_m2576"]) for row in platform_rows)
            and not any(_boolish(row["external_validation_result_allowed"]) for row in platform_rows),
            f"rows={len(platform_rows)}",
            f"rows={len(PLATFORM_LAYERS)};external_execution=false;validation_result=false",
            "contract_violation",
        ),
        (
            "dependency_policy_rows_pass",
            "contract",
            len(dependency_rows) == len(DEPENDENCY_POLICIES)
            and _all_status_pass(dependency_rows)
            and not any(_boolish(row["install_allowed_in_m2576"]) for row in dependency_rows)
            and not any(_boolish(row["import_allowed_in_m2576"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2576"]) for row in dependency_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2576"]) for row in dependency_rows),
            f"rows={len(dependency_rows)}",
            f"rows={len(DEPENDENCY_POLICIES)};install=false;import=false;run=false;mutation=false",
            "contract_violation",
        ),
        (
            "scenario_discrepancy_question_rows_pass",
            "scenario",
            len(discrepancy_rows) == len(readiness_rows) * len(HF4_QUESTIONS)
            and _all_status_pass(discrepancy_rows)
            and all(_boolish(row["requires_external_validation_execution"]) for row in discrepancy_rows)
            and not any(_boolish(row["answer_allowed_in_m2576"]) for row in discrepancy_rows)
            and not any(_boolish(row["driver_performance_claim_allowed"]) for row in discrepancy_rows),
            f"rows={len(discrepancy_rows)}",
            f"rows={len(readiness_rows) * len(HF4_QUESTIONS)};requires_external=true;answer=false",
            "scenario_sampling_failure",
        ),
        (
            "actor_input_isolation_rows_pass",
            "contract",
            len(actor_input_rows) == len(readiness_rows)
            and _all_status_pass(actor_input_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in actor_input_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in actor_input_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_input_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in actor_input_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_input_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in actor_input_rows)
            and not any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_input_rows)
            and not any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_input_rows)
            and not any(_boolish(row["validation_outcome_actor_visible"]) for row in actor_input_rows),
            f"rows={len(actor_input_rows)}",
            "rows=readiness_rows;obs=72;action=3;hidden=false;all_outcomes=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not forbidden_claims_allowed
            and any(
                row["claim_family"] == "validation_readiness_boundary_materialized"
                and _boolish(row["claim_allowed_in_m2576"])
                for row in claim_rows
            ),
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;boundary_materialized=true",
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
    m2572_summary: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    platform_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    discrepancy_rows: list[dict[str, Any]],
    actor_input_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    readiness_path: Path,
    evidence_path: Path,
    platform_path: Path,
    dependency_path: Path,
    discrepancy_path: Path,
    actor_input_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    role_counts = Counter(str(row["route_role_id"]) for row in readiness_rows)
    validation_boundary_claim_allowed = any(
        row["claim_family"] == "validation_readiness_boundary_materialized"
        and _boolish(row["claim_allowed_in_m2576"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"] != "validation_readiness_boundary_materialized"
        and _boolish(row["claim_allowed_in_m2576"])
        for row in claim_rows
    )
    status_pass = (
        all(source_exists.values())
        and bool(m2572_summary.get("status_pass"))
        and len(readiness_rows) == 2
        and _all_status_pass(readiness_rows)
        and len(evidence_rows) == len(readiness_rows) * len(EVIDENCE_SOURCES)
        and _all_status_pass(evidence_rows)
        and len(platform_rows) == len(PLATFORM_LAYERS)
        and _all_status_pass(platform_rows)
        and len(dependency_rows) == len(DEPENDENCY_POLICIES)
        and _all_status_pass(dependency_rows)
        and len(discrepancy_rows) == len(readiness_rows) * len(HF4_QUESTIONS)
        and _all_status_pass(discrepancy_rows)
        and len(actor_input_rows) == len(readiness_rows)
        and _all_status_pass(actor_input_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and validation_boundary_claim_allowed
        and not forbidden_claim_allowed
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_validation_readiness_boundary_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_validation_readiness_boundary_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_validation_readiness_request_rows": str(readiness_path),
        "hf3_evidence_admission_rows": str(evidence_path),
        "hf3_platform_boundary_rows": str(platform_path),
        "hf3_dependency_policy_rows": str(dependency_path),
        "hf3_scenario_discrepancy_question_rows": str(discrepancy_path),
        "hf3_actor_input_isolation_rows": str(actor_input_path),
        "hf3_claim_boundary_checks": str(claim_path),
        "validation_readiness_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2572_status_pass": bool(m2572_summary.get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "readiness_request_row_count": len(readiness_rows),
        "readiness_request_rows_all_pass": _all_status_pass(readiness_rows),
        "readiness_role_counts": dict(sorted(role_counts.items())),
        "evidence_admission_row_count": len(evidence_rows),
        "evidence_admission_rows_all_pass": _all_status_pass(evidence_rows),
        "platform_boundary_row_count": len(platform_rows),
        "platform_boundary_rows_all_pass": _all_status_pass(platform_rows),
        "dependency_policy_row_count": len(dependency_rows),
        "dependency_policy_rows_all_pass": _all_status_pass(dependency_rows),
        "scenario_discrepancy_question_row_count": len(discrepancy_rows),
        "scenario_discrepancy_question_rows_all_pass": _all_status_pass(discrepancy_rows),
        "actor_input_isolation_row_count": len(actor_input_rows),
        "actor_input_isolation_rows_all_pass": _all_status_pass(actor_input_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "validation_readiness_boundary_materialized_claim_allowed": bool(validation_boundary_claim_allowed),
        "forbidden_claim_allowed_in_m2576": bool(forbidden_claim_allowed),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "validation_admission_allowed": any(_boolish(row["validation_admission_allowed"]) for row in readiness_rows),
        "validation_execution_allowed_in_m2576": any(_boolish(row["validation_execution_allowed_in_m2576"]) for row in readiness_rows),
        "external_simulation_allowed_in_m2576": any(_boolish(row["external_simulation_allowed_in_m2576"]) for row in readiness_rows),
        "accepted_as_validation_result": any(_boolish(row["accepted_as_validation_result"]) for row in evidence_rows),
        "accepted_as_driver_performance": any(_boolish(row["accepted_as_driver_performance"]) for row in evidence_rows),
        "accepted_as_ranking_evidence": any(_boolish(row["accepted_as_ranking_evidence"]) for row in evidence_rows),
        "external_high_fidelity_execution_allowed_in_m2576": any(
            _boolish(row["external_high_fidelity_execution_allowed_in_m2576"]) for row in platform_rows
        ),
        "external_validation_result_allowed": any(_boolish(row["external_validation_result_allowed"]) for row in platform_rows),
        "install_allowed_in_m2576": any(_boolish(row["install_allowed_in_m2576"]) for row in dependency_rows),
        "import_allowed_in_m2576": any(_boolish(row["import_allowed_in_m2576"]) for row in dependency_rows),
        "runtime_execution_allowed_in_m2576": any(_boolish(row["runtime_execution_allowed_in_m2576"]) for row in dependency_rows),
        "dependency_mutation_allowed_in_m2576": any(_boolish(row["dependency_mutation_allowed_in_m2576"]) for row in dependency_rows),
        "hf4_answer_allowed_in_m2576": any(_boolish(row["answer_allowed_in_m2576"]) for row in discrepancy_rows),
        "hf4_driver_performance_claim_allowed": any(_boolish(row["driver_performance_claim_allowed"]) for row in discrepancy_rows),
        "hidden_oracle_actor_input_detected": any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_input_rows),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in actor_input_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_input_rows),
        "backend_status_actor_visible": any(_boolish(row["backend_status_actor_visible"]) for row in actor_input_rows),
        "reset_outcome_actor_visible": any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_input_rows),
        "rollout_outcome_actor_visible": any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_input_rows),
        "validation_outcome_actor_visible": any(_boolish(row["validation_outcome_actor_visible"]) for row in actor_input_rows),
        "repo_local_static_boundary_materialization": True,
        "repo_local_boundary_only": True,
        "answer_allowed_in_m2576": any(_boolish(row["answer_allowed_in_m2576"]) for row in discrepancy_rows),
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
                "# M2576 Engineering Controller Route A Baseline HF3 Validation-Readiness Boundary Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_validation_readiness_boundary.py`",
                f"- summary: `{summary['summary']}`",
                f"- readiness requests: `{summary['hf3_validation_readiness_request_rows']}`",
                f"- evidence admission rows: `{summary['hf3_evidence_admission_rows']}`",
                f"- platform boundary rows: `{summary['hf3_platform_boundary_rows']}`",
                f"- dependency policy rows: `{summary['hf3_dependency_policy_rows']}`",
                f"- scenario-discrepancy question rows: `{summary['hf3_scenario_discrepancy_question_rows']}`",
                f"- actor-input isolation rows: `{summary['hf3_actor_input_isolation_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['validation_readiness_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- reset/action/step/rollout/validation execution: `false`",
                "- validation-readiness/result/ranking/driver-performance claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2576 materializes Route A HF3 validation-readiness boundary",
                "artifacts for the two accepted HF3 candidates. The rows define",
                "which evidence is admitted as boundary input, which platform and",
                "dependency actions remain disallowed, which HF4 discrepancy",
                "questions are future-only, and which claims remain forbidden.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"readiness_request_row_count: {summary['readiness_request_row_count']}",
                f"evidence_admission_row_count: {summary['evidence_admission_row_count']}",
                f"platform_boundary_row_count: {summary['platform_boundary_row_count']}",
                f"dependency_policy_row_count: {summary['dependency_policy_row_count']}",
                f"scenario_discrepancy_question_row_count: {summary['scenario_discrepancy_question_row_count']}",
                f"actor_input_isolation_row_count: {summary['actor_input_isolation_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"validation_readiness_boundary_materialized_claim_allowed: {str(summary['validation_readiness_boundary_materialized_claim_allowed']).lower()}",
                f"forbidden_claim_allowed_in_m2576: {str(summary['forbidden_claim_allowed_in_m2576']).lower()}",
                f"validation_admission_allowed: {str(summary['validation_admission_allowed']).lower()}",
                f"validation_execution_allowed_in_m2576: {str(summary['validation_execution_allowed_in_m2576']).lower()}",
                f"external_simulation_allowed_in_m2576: {str(summary['external_simulation_allowed_in_m2576']).lower()}",
                f"hf4_answer_allowed_in_m2576: {str(summary['hf4_answer_allowed_in_m2576']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2576 supports only the operational claim that static",
                "validation-readiness boundary artifacts were materialized. It",
                "does not support validation admission, validation readiness,",
                "validation result, rollout success, high-fidelity discrepancy",
                "answers, driver performance, controller ranking, checkpoint",
                "promotion, success rate, paper evidence, FW-vs-GRU, current-sim",
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


def _actor_view_rows_are_isolated(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        _int_value(row.get("actor_observation_shape"), default=-1) == P0_OBSERVATION_DIM
        and _int_value(row.get("action_shape"), default=-1) == ACTION_DIM
        and not _boolish(row.get("hidden_oracle_actor_input_detected"))
        and not _boolish(row.get("diagnostics_actor_visible"))
        and not _boolish(row.get("taxonomy_label_actor_visible"))
        and not _boolish(row.get("backend_status_actor_visible"))
        and not _boolish(row.get("reset_outcome_actor_visible"))
        and not _boolish(row.get("rollout_outcome_actor_visible"))
        for row in rows
    )


def _row_passed(row: dict[str, Any]) -> bool:
    return _boolish(row.get("status_pass"))


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2572-summary", type=Path, default=DEFAULT_M2572_SUMMARY)
    parser.add_argument("--m2572-requests", type=Path, default=DEFAULT_M2572_REQUESTS)
    parser.add_argument("--m2572-actor-view-rows", type=Path, default=DEFAULT_M2572_ACTOR_VIEW_ROWS)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_validation_readiness_boundary(
        args.output_dir,
        m2572_summary_path=args.m2572_summary,
        m2572_requests_path=args.m2572_requests,
        m2572_actor_view_rows_path=args.m2572_actor_view_rows,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "readiness_requests={readiness_request_row_count} "
        "evidence_rows={evidence_admission_row_count} "
        "boundary_claim={validation_readiness_boundary_materialized_claim_allowed} "
        "summary={summary}".format(**summary)
    )


if __name__ == "__main__":
    main()
