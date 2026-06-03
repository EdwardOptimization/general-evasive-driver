"""Route A HF3 validation-admission materialization preflight."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2580-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2581-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-result-audit"
)
DEFAULT_DOC_PATH = "docs/m2580-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2580_engineering_controller_route_a_hf3_validation_admission")
DEFAULT_M2576_SUMMARY = Path(
    "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/summary.json"
)
DEFAULT_M2576_READINESS_REQUESTS = Path(
    "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/"
    "hf3_validation_readiness_request_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2579-engineering-controller-route-a-baseline-hf3-validation-admission-design.md",
    "docs/m2578-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-result-synthesis.md",
    "docs/m2577-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-result-audit.md",
    "docs/m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight.md",
    "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/summary.json",
    "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/"
    "hf3_validation_readiness_request_rows.csv",
    "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/"
    "hf3_claim_boundary_checks.csv",
    "runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/"
    "validation_readiness_gate_matrix.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 validation-admission materialization preflight only; "
    "admission design artifacts may be materialized; not validation admission, "
    "external simulation, validation execution, validation readiness/result, "
    "HF4 discrepancy result, rollout success, ranking, driver performance, "
    "paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

VALIDATION_ADMISSION_REQUEST_FIELDNAMES = [
    "admission_request_id",
    "source_readiness_request_id",
    "source_rollout_request_id",
    "route_role_id",
    "candidate_role_label",
    "actor_observation_shape",
    "action_shape",
    "boundary_materialized",
    "validation_admission_granted_in_m2580",
    "validation_execution_allowed_in_m2580",
    "external_simulation_allowed_in_m2580",
    "status_pass",
    "claim_boundary",
]

ADMISSION_CRITERIA_FIELDNAMES = [
    "admission_criteria_id",
    "admission_request_id",
    "criteria_family",
    "criteria_description",
    "criteria_satisfied_by_m2580",
    "required_before_validation_admission",
    "status_pass",
    "claim_boundary",
]

EXTERNAL_PLATFORM_READINESS_FIELDNAMES = [
    "external_platform_readiness_id",
    "platform_family",
    "open_auditable_backend_required",
    "install_allowed_in_m2580",
    "import_allowed_in_m2580",
    "runtime_execution_allowed_in_m2580",
    "platform_selected_in_m2580",
    "status_pass",
    "claim_boundary",
]

EVIDENCE_SUFFICIENCY_FIELDNAMES = [
    "evidence_sufficiency_id",
    "evidence_family",
    "available_in_m2580",
    "missing_before_validation_admission",
    "missing_before_validation_readiness",
    "missing_before_validation_result",
    "status_pass",
    "claim_boundary",
]

ACTOR_ACTION_GUARD_FIELDNAMES = [
    "actor_action_guard_id",
    "admission_request_id",
    "actor_observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "rollout_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "action_contract_mutation_detected",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2580",
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

CRITERIA_FAMILIES = (
    (
        "boundary_materialization_accepted",
        "M2576/M2577/M2578 boundary evidence exists and is accepted as boundary input only",
        True,
        False,
    ),
    (
        "actor_action_contract_preserved",
        "P0 observation 72 and action 3 are preserved without actor input mutation",
        True,
        False,
    ),
    (
        "external_platform_ready",
        "Open auditable high-fidelity validation platform is selected and ready",
        False,
        True,
    ),
    (
        "validation_protocol_defined",
        "Validation protocol, holdout roles, and execution/audit procedure are defined",
        False,
        True,
    ),
    (
        "claim_boundary_audited",
        "Validation-admission claim boundary has a follow-up audit row",
        False,
        True,
    ),
    (
        "holdout_or_generalization_policy_defined",
        "Holdout or generalization policy for validation interpretation is defined",
        False,
        True,
    ),
)

PLATFORM_FAMILIES = (
    ("chrono_vehicle_or_equivalent_open_backend", True),
    ("black_box_industry_demonstration_backend", False),
    ("repo_local_current_sim_backend", False),
)

EVIDENCE_FAMILIES = (
    ("m2576_boundary_materialization", True, False, False, False),
    ("m2577_boundary_audit", True, False, False, False),
    ("m2578_boundary_synthesis", True, False, False, False),
    ("external_platform_selection", False, True, True, True),
    ("validation_protocol", False, True, True, True),
    ("validation_execution_result", False, False, False, True),
    ("claim_boundary_audit_after_admission", False, False, True, True),
)

CLAIM_CHECKS = (
    (
        "validation_admission_design_materialized",
        True,
        "M2580 admission request criteria platform evidence guard claim-boundary and gate rows",
    ),
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
    "hf4_discrepancy_result_claim_made": False,
}


def materialize_route_a_hf3_validation_admission(
    output_dir: Path,
    *,
    m2576_summary_path: Path = DEFAULT_M2576_SUMMARY,
    m2576_readiness_requests_path: Path = DEFAULT_M2576_READINESS_REQUESTS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2576_summary = read_json(m2576_summary_path)
    readiness_rows = _read_csv_rows(m2576_readiness_requests_path)

    admission_rows = build_validation_admission_request_rows(readiness_rows)
    criteria_rows = build_admission_criteria_rows(admission_rows)
    platform_rows = build_external_platform_readiness_rows()
    evidence_rows = build_evidence_sufficiency_rows()
    guard_rows = build_actor_action_guard_rows(admission_rows)
    claim_rows = build_claim_boundary_checks(
        admission_rows,
        criteria_rows,
        platform_rows,
        evidence_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2576_summary=m2576_summary,
        admission_rows=admission_rows,
        criteria_rows=criteria_rows,
        platform_rows=platform_rows,
        evidence_rows=evidence_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    admission_path = output_dir / "hf3_validation_admission_request_rows.csv"
    criteria_path = output_dir / "hf3_admission_criteria_rows.csv"
    platform_path = output_dir / "hf3_external_platform_readiness_rows.csv"
    evidence_path = output_dir / "hf3_evidence_sufficiency_rows.csv"
    guard_path = output_dir / "hf3_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_claim_boundary_checks.csv"
    gate_path = output_dir / "validation_admission_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(admission_path, admission_rows, fieldnames=VALIDATION_ADMISSION_REQUEST_FIELDNAMES)
    write_csv_rows(criteria_path, criteria_rows, fieldnames=ADMISSION_CRITERIA_FIELDNAMES)
    write_csv_rows(platform_path, platform_rows, fieldnames=EXTERNAL_PLATFORM_READINESS_FIELDNAMES)
    write_csv_rows(evidence_path, evidence_rows, fieldnames=EVIDENCE_SUFFICIENCY_FIELDNAMES)
    write_csv_rows(guard_path, guard_rows, fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2576_summary=m2576_summary,
        admission_rows=admission_rows,
        criteria_rows=criteria_rows,
        platform_rows=platform_rows,
        evidence_rows=evidence_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        admission_path=admission_path,
        criteria_path=criteria_path,
        platform_path=platform_path,
        evidence_path=evidence_path,
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


def build_validation_admission_request_rows(
    readiness_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for request in sorted(readiness_rows, key=lambda row: row["readiness_request_id"]):
        obs_shape = _int_value(request.get("actor_observation_shape"), default=-1)
        action_shape = _int_value(request.get("action_shape"), default=-1)
        rows.append(
            {
                "admission_request_id": request["readiness_request_id"].replace(
                    "_validation_readiness_request", "_validation_admission_request"
                ),
                "source_readiness_request_id": request["readiness_request_id"],
                "source_rollout_request_id": request["source_rollout_request_id"],
                "route_role_id": request["route_role_id"],
                "candidate_role_label": request["candidate_role_label"],
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "boundary_materialized": bool(_row_passed(request)),
                "validation_admission_granted_in_m2580": False,
                "validation_execution_allowed_in_m2580": False,
                "external_simulation_allowed_in_m2580": False,
                "status_pass": bool(
                    _row_passed(request)
                    and obs_shape == P0_OBSERVATION_DIM
                    and action_shape == ACTION_DIM
                    and not _boolish(request.get("validation_admission_allowed"))
                    and not _boolish(request.get("validation_execution_allowed_in_m2576"))
                    and not _boolish(request.get("external_simulation_allowed_in_m2576"))
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_admission_criteria_rows(admission_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for admission in admission_rows:
        for family, description, satisfied, required in CRITERIA_FAMILIES:
            rows.append(
                {
                    "admission_criteria_id": f"{admission['admission_request_id']}_{family}",
                    "admission_request_id": admission["admission_request_id"],
                    "criteria_family": family,
                    "criteria_description": description,
                    "criteria_satisfied_by_m2580": bool(satisfied),
                    "required_before_validation_admission": bool(required),
                    "status_pass": bool(
                        _row_passed(admission)
                        and (
                            (family in {"boundary_materialization_accepted", "actor_action_contract_preserved"} and satisfied)
                            or (required and not satisfied)
                        )
                    ),
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def build_external_platform_readiness_rows() -> list[dict[str, Any]]:
    rows = []
    for platform_family, open_required in PLATFORM_FAMILIES:
        rows.append(
            {
                "external_platform_readiness_id": f"{platform_family}_external_platform_readiness",
                "platform_family": platform_family,
                "open_auditable_backend_required": bool(open_required),
                "install_allowed_in_m2580": False,
                "import_allowed_in_m2580": False,
                "runtime_execution_allowed_in_m2580": False,
                "platform_selected_in_m2580": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_evidence_sufficiency_rows() -> list[dict[str, Any]]:
    rows = []
    for evidence_family, available, missing_admission, missing_readiness, missing_result in EVIDENCE_FAMILIES:
        rows.append(
            {
                "evidence_sufficiency_id": f"{evidence_family}_evidence_sufficiency",
                "evidence_family": evidence_family,
                "available_in_m2580": bool(available),
                "missing_before_validation_admission": bool(missing_admission),
                "missing_before_validation_readiness": bool(missing_readiness),
                "missing_before_validation_result": bool(missing_result),
                "status_pass": bool(
                    available
                    or missing_admission
                    or missing_readiness
                    or missing_result
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(admission_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for admission in admission_rows:
        rows.append(
            {
                "actor_action_guard_id": f"{admission['admission_request_id']}_actor_action_guard",
                "admission_request_id": admission["admission_request_id"],
                "actor_observation_shape": _int_value(admission["actor_observation_shape"], default=-1),
                "action_shape": _int_value(admission["action_shape"], default=-1),
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "rollout_outcome_actor_visible": False,
                "validation_outcome_actor_visible": False,
                "action_contract_mutation_detected": False,
                "status_pass": bool(
                    _row_passed(admission)
                    and _int_value(admission["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM
                    and _int_value(admission["action_shape"], default=-1) == ACTION_DIM
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    admission_rows: list[dict[str, Any]],
    criteria_rows: list[dict[str, Any]],
    platform_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    design_materialized = bool(
        len(admission_rows) == 2
        and _all_status_pass(admission_rows)
        and len(criteria_rows) == len(admission_rows) * len(CRITERIA_FAMILIES)
        and _all_status_pass(criteria_rows)
        and len(platform_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(platform_rows)
        and len(evidence_rows) == len(EVIDENCE_FAMILIES)
        and _all_status_pass(evidence_rows)
        and len(guard_rows) == len(admission_rows)
        and _all_status_pass(guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and design_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2580": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "validation_admission_design_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2576_summary: dict[str, Any],
    admission_rows: list[dict[str, Any]],
    criteria_rows: list[dict[str, Any]],
    platform_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"] != "validation_admission_design_materialized"
        and _boolish(row["claim_allowed_in_m2580"])
    ]
    satisfied_required_criteria = [
        row for row in criteria_rows
        if _boolish(row["required_before_validation_admission"])
        and _boolish(row["criteria_satisfied_by_m2580"])
    ]
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()) and bool(m2576_summary.get("status_pass")),
            f"missing={sum(1 for exists in source_exists.values() if not exists)};m2576_status={m2576_summary.get('status_pass')}",
            "missing=0;m2576_status=True",
            "lineage_invalid",
        ),
        (
            "validation_admission_request_rows_complete",
            "scenario",
            len(admission_rows) == 2
            and _all_status_pass(admission_rows)
            and not any(_boolish(row["validation_admission_granted_in_m2580"]) for row in admission_rows)
            and not any(_boolish(row["validation_execution_allowed_in_m2580"]) for row in admission_rows)
            and not any(_boolish(row["external_simulation_allowed_in_m2580"]) for row in admission_rows),
            f"rows={len(admission_rows)}",
            "rows=2;validation_admission=false;validation_execution=false;external=false",
            "scenario_sampling_failure",
        ),
        (
            "admission_criteria_rows_pass",
            "claim_boundary",
            len(criteria_rows) == len(admission_rows) * len(CRITERIA_FAMILIES)
            and _all_status_pass(criteria_rows)
            and not satisfied_required_criteria,
            f"rows={len(criteria_rows)};satisfied_required={len(satisfied_required_criteria)}",
            f"rows={len(admission_rows) * len(CRITERIA_FAMILIES)};satisfied_required=0",
            "objective_overfit",
        ),
        (
            "external_platform_readiness_rows_pass",
            "contract",
            len(platform_rows) == len(PLATFORM_FAMILIES)
            and _all_status_pass(platform_rows)
            and any(
                row["platform_family"] == "chrono_vehicle_or_equivalent_open_backend"
                and _boolish(row["open_auditable_backend_required"])
                for row in platform_rows
            )
            and not any(_boolish(row["install_allowed_in_m2580"]) for row in platform_rows)
            and not any(_boolish(row["import_allowed_in_m2580"]) for row in platform_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2580"]) for row in platform_rows)
            and not any(_boolish(row["platform_selected_in_m2580"]) for row in platform_rows),
            f"rows={len(platform_rows)}",
            f"rows={len(PLATFORM_FAMILIES)};install/import/run/selected=false",
            "contract_violation",
        ),
        (
            "evidence_sufficiency_rows_pass",
            "lineage",
            len(evidence_rows) == len(EVIDENCE_FAMILIES)
            and _all_status_pass(evidence_rows)
            and not any(
                row["evidence_family"] in {
                    "external_platform_selection",
                    "validation_protocol",
                    "validation_execution_result",
                    "claim_boundary_audit_after_admission",
                }
                and _boolish(row["available_in_m2580"])
                for row in evidence_rows
            )
            and any(_boolish(row["missing_before_validation_admission"]) for row in evidence_rows)
            and any(_boolish(row["missing_before_validation_readiness"]) for row in evidence_rows)
            and any(_boolish(row["missing_before_validation_result"]) for row in evidence_rows),
            f"rows={len(evidence_rows)}",
            f"rows={len(EVIDENCE_FAMILIES)};missing_admission/readiness/result=true",
            "lineage_invalid",
        ),
        (
            "actor_action_guard_rows_pass",
            "contract",
            len(guard_rows) == len(admission_rows)
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
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in guard_rows),
            f"rows={len(guard_rows)}",
            "rows=admission_rows;obs=72;action=3;hidden/outcomes/mutation=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not forbidden_claims_allowed
            and any(
                row["claim_family"] == "validation_admission_design_materialized"
                and _boolish(row["claim_allowed_in_m2580"])
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
    m2576_summary: dict[str, Any],
    admission_rows: list[dict[str, Any]],
    criteria_rows: list[dict[str, Any]],
    platform_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    admission_path: Path,
    criteria_path: Path,
    platform_path: Path,
    evidence_path: Path,
    guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    role_counts = Counter(str(row["route_role_id"]) for row in admission_rows)
    materialized_claim_allowed = any(
        row["claim_family"] == "validation_admission_design_materialized"
        and _boolish(row["claim_allowed_in_m2580"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"] != "validation_admission_design_materialized"
        and _boolish(row["claim_allowed_in_m2580"])
        for row in claim_rows
    )
    status_pass = (
        all(source_exists.values())
        and bool(m2576_summary.get("status_pass"))
        and len(admission_rows) == 2
        and _all_status_pass(admission_rows)
        and len(criteria_rows) == len(admission_rows) * len(CRITERIA_FAMILIES)
        and _all_status_pass(criteria_rows)
        and len(platform_rows) == len(PLATFORM_FAMILIES)
        and _all_status_pass(platform_rows)
        and len(evidence_rows) == len(EVIDENCE_FAMILIES)
        and _all_status_pass(evidence_rows)
        and len(guard_rows) == len(admission_rows)
        and _all_status_pass(guard_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and materialized_claim_allowed
        and not forbidden_claim_allowed
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_validation_admission_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_validation_admission_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_validation_admission_request_rows": str(admission_path),
        "hf3_admission_criteria_rows": str(criteria_path),
        "hf3_external_platform_readiness_rows": str(platform_path),
        "hf3_evidence_sufficiency_rows": str(evidence_path),
        "hf3_actor_action_guard_rows": str(guard_path),
        "hf3_claim_boundary_checks": str(claim_path),
        "validation_admission_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2576_status_pass": bool(m2576_summary.get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "admission_request_row_count": len(admission_rows),
        "admission_request_rows_all_pass": _all_status_pass(admission_rows),
        "admission_role_counts": dict(sorted(role_counts.items())),
        "admission_criteria_row_count": len(criteria_rows),
        "admission_criteria_rows_all_pass": _all_status_pass(criteria_rows),
        "external_platform_readiness_row_count": len(platform_rows),
        "external_platform_readiness_rows_all_pass": _all_status_pass(platform_rows),
        "evidence_sufficiency_row_count": len(evidence_rows),
        "evidence_sufficiency_rows_all_pass": _all_status_pass(evidence_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "actor_action_guard_rows_all_pass": _all_status_pass(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "validation_admission_design_materialized_claim_allowed": bool(materialized_claim_allowed),
        "forbidden_claim_allowed_in_m2580": bool(forbidden_claim_allowed),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "boundary_materialized": all(_boolish(row["boundary_materialized"]) for row in admission_rows),
        "validation_admission_granted": any(_boolish(row["validation_admission_granted_in_m2580"]) for row in admission_rows),
        "validation_execution_allowed_in_m2580": any(
            _boolish(row["validation_execution_allowed_in_m2580"]) for row in admission_rows
        ),
        "external_simulation_allowed_in_m2580": any(
            _boolish(row["external_simulation_allowed_in_m2580"]) for row in admission_rows
        ),
        "required_criteria_satisfied_in_m2580": any(
            _boolish(row["required_before_validation_admission"])
            and _boolish(row["criteria_satisfied_by_m2580"])
            for row in criteria_rows
        ),
        "install_allowed_in_m2580": any(_boolish(row["install_allowed_in_m2580"]) for row in platform_rows),
        "import_allowed_in_m2580": any(_boolish(row["import_allowed_in_m2580"]) for row in platform_rows),
        "runtime_execution_allowed_in_m2580": any(
            _boolish(row["runtime_execution_allowed_in_m2580"]) for row in platform_rows
        ),
        "platform_selected_in_m2580": any(_boolish(row["platform_selected_in_m2580"]) for row in platform_rows),
        "missing_evidence_before_validation_admission": any(
            _boolish(row["missing_before_validation_admission"]) for row in evidence_rows
        ),
        "missing_evidence_before_validation_readiness": any(
            _boolish(row["missing_before_validation_readiness"]) for row in evidence_rows
        ),
        "missing_evidence_before_validation_result": any(
            _boolish(row["missing_before_validation_result"]) for row in evidence_rows
        ),
        "hidden_oracle_actor_input_detected": any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in guard_rows),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in guard_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in guard_rows),
        "backend_status_actor_visible": any(_boolish(row["backend_status_actor_visible"]) for row in guard_rows),
        "reset_outcome_actor_visible": any(_boolish(row["reset_outcome_actor_visible"]) for row in guard_rows),
        "rollout_outcome_actor_visible": any(_boolish(row["rollout_outcome_actor_visible"]) for row in guard_rows),
        "validation_outcome_actor_visible": any(_boolish(row["validation_outcome_actor_visible"]) for row in guard_rows),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"]) for row in guard_rows
        ),
        "repo_local_static_admission_materialization": True,
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
                "# M2580 Engineering Controller Route A Baseline HF3 Validation-Admission Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2580-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_validation_admission.py`",
                f"- summary: `{summary['summary']}`",
                f"- validation-admission requests: `{summary['hf3_validation_admission_request_rows']}`",
                f"- admission criteria rows: `{summary['hf3_admission_criteria_rows']}`",
                f"- external-platform readiness rows: `{summary['hf3_external_platform_readiness_rows']}`",
                f"- evidence-sufficiency rows: `{summary['hf3_evidence_sufficiency_rows']}`",
                f"- actor/action guard rows: `{summary['hf3_actor_action_guard_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['validation_admission_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- reset/action/step/rollout/validation execution: `false`",
                "- validation admission/readiness/result/ranking/driver-performance claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2580 materializes the bounded Route A HF3 validation-admission",
                "preflight artifacts requested by M2579 for the two accepted HF3",
                "candidates. The rows preserve the P0 actor/action contract,",
                "record admission criteria that are still unsatisfied, keep",
                "external platform selection and runtime execution disallowed,",
                "and keep validation admission/result/performance claims false.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"admission_request_row_count: {summary['admission_request_row_count']}",
                f"admission_criteria_row_count: {summary['admission_criteria_row_count']}",
                f"external_platform_readiness_row_count: {summary['external_platform_readiness_row_count']}",
                f"evidence_sufficiency_row_count: {summary['evidence_sufficiency_row_count']}",
                f"actor_action_guard_row_count: {summary['actor_action_guard_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"validation_admission_design_materialized_claim_allowed: {str(summary['validation_admission_design_materialized_claim_allowed']).lower()}",
                f"forbidden_claim_allowed_in_m2580: {str(summary['forbidden_claim_allowed_in_m2580']).lower()}",
                f"validation_admission_granted: {str(summary['validation_admission_granted']).lower()}",
                f"validation_execution_allowed_in_m2580: {str(summary['validation_execution_allowed_in_m2580']).lower()}",
                f"external_simulation_allowed_in_m2580: {str(summary['external_simulation_allowed_in_m2580']).lower()}",
                f"platform_selected_in_m2580: {str(summary['platform_selected_in_m2580']).lower()}",
                f"missing_evidence_before_validation_admission: {str(summary['missing_evidence_before_validation_admission']).lower()}",
                f"missing_evidence_before_validation_readiness: {str(summary['missing_evidence_before_validation_readiness']).lower()}",
                f"missing_evidence_before_validation_result: {str(summary['missing_evidence_before_validation_result']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2580 supports only the operational claim that bounded",
                "validation-admission design artifacts were materialized. It does",
                "not support validation admission, high-fidelity validation",
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


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_row_passed(row) for row in rows)


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
    parser.add_argument("--m2576-summary", type=Path, default=DEFAULT_M2576_SUMMARY)
    parser.add_argument("--m2576-readiness-requests", type=Path, default=DEFAULT_M2576_READINESS_REQUESTS)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_validation_admission(
        args.output_dir,
        m2576_summary_path=args.m2576_summary,
        m2576_readiness_requests_path=args.m2576_readiness_requests,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "admission_requests={admission_request_row_count} "
        "criteria_rows={admission_criteria_row_count} "
        "design_claim={validation_admission_design_materialized_claim_allowed} "
        "summary={summary}".format(**summary)
    )


if __name__ == "__main__":
    main()
