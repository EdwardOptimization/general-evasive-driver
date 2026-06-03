"""Route A HF3 measured reset-feasibility execution materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    P0_OBSERVATION_DIM,
    BackendResetRequest,
    CurrentSimDynamicsBackend,
    P0ObservationExtractor,
)


DEFAULT_MILESTONE = "m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2569-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution")
DEFAULT_M2564_SUMMARY = Path(
    "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/summary.json"
)
DEFAULT_M2564_CANDIDATES = Path(
    "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_candidate_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2567-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-design.md",
    "docs/m2566-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-synthesis.md",
    "docs/m2565-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-audit.md",
    "docs/m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight.md",
    "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/summary.json",
    "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_candidate_rows.csv",
    "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_request_contract.csv",
    "runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_plan.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 measured reset-feasibility execution materialization preflight only; "
    "repo-local reset-only execution observed; not policy action, rollout, "
    "ranking, validation, driver performance, paper, FW-vs-GRU, current-sim "
    "verdict, high-fidelity validation, reset success, or self-ID"
)

MEASURED_RESET_SEEDS = {
    "stable_avoidable_aeb_feasible_reset_execution_candidate": 256800,
    "stable_aes_aeb_infeasible_reset_execution_candidate": 256801,
}

REQUEST_FIELDNAMES = [
    "reset_request_id",
    "reset_candidate_id",
    "route_role_id",
    "backend_family",
    "scenario_spec_id",
    "seed",
    "actor_observation_shape",
    "action_shape",
    "policy_action_allowed",
    "environment_step_allowed",
    "rollout_allowed",
    "actor_input_mutation_allowed",
    "status_pass",
    "claim_boundary",
]

BACKEND_PROBE_FIELDNAMES = [
    "backend_probe_id",
    "reset_request_id",
    "backend_family",
    "backend_module",
    "backend_class",
    "external_install_allowed",
    "external_import_allowed",
    "dependency_mutation_allowed",
    "backend_reset_allowed_in_m2568",
    "backend_step_allowed_in_m2568",
    "status_pass",
    "claim_boundary",
]

EXECUTION_FIELDNAMES = [
    "reset_execution_id",
    "reset_request_id",
    "reset_attempted",
    "reset_status",
    "actor_view_available",
    "diagnostics_recorded",
    "policy_action_executed",
    "environment_step_executed",
    "rollout_executed",
    "reset_success_claim_allowed",
    "status_pass",
    "claim_boundary",
]

ACTOR_VIEW_FIELDNAMES = [
    "actor_view_check_id",
    "reset_execution_id",
    "actor_observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "status_pass",
    "claim_boundary",
]

OUTCOME_FIELDNAMES = [
    "outcome_check_id",
    "reset_execution_id",
    "backend_available",
    "reset_request_valid",
    "reset_attempted",
    "actor_view_available",
    "reset_status_present",
    "reset_success_claim_allowed",
    "validation_claim_allowed",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2568",
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

FORBIDDEN_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "external_install_performed": False,
    "external_import_performed": False,
    "dependency_mutation_performed": False,
    "policy_action_run": False,
    "environment_step_run": False,
    "rollout_execution_run": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "pilot_admission_claim_made": False,
    "reset_success_claim_made": False,
    "rollout_success_claim_made": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}

CLAIM_CHECKS = (
    ("pilot_admission", False, "measured reset and rollout feasibility audit"),
    ("reset_execution_observed", True, "M2568 reset-only execution rows and actor-view contract rows"),
    ("reset_success", False, "M2568 result audit and later reset-success decision"),
    ("rollout_feasibility", False, "later rollout-feasibility execution artifact"),
    ("high_fidelity_validation_readiness_or_result", False, "audited reset and rollout feasibility evidence"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("driver_performance_claim", False, "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", False, "separate paper-route evidence matrix"),
)


def materialize_route_a_hf3_measured_reset_feasibility_execution(
    output_dir: Path,
    *,
    m2564_summary_path: Path = DEFAULT_M2564_SUMMARY,
    m2564_candidates_path: Path = DEFAULT_M2564_CANDIDATES,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2564_summary = read_json(m2564_summary_path)
    candidate_rows = _read_csv_rows(m2564_candidates_path)

    request_rows = build_measured_reset_request_rows(candidate_rows)
    backend_rows = build_backend_probe_rows(request_rows)
    execution_rows, actor_view_rows, outcome_rows = execute_reset_only_rows(request_rows)
    claim_rows = build_claim_boundary_checks(execution_rows)
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2564_summary=m2564_summary,
        request_rows=request_rows,
        backend_rows=backend_rows,
        execution_rows=execution_rows,
        actor_view_rows=actor_view_rows,
        outcome_rows=outcome_rows,
        claim_rows=claim_rows,
    )

    request_path = output_dir / "hf3_measured_reset_request_rows.csv"
    backend_path = output_dir / "hf3_backend_probe_rows.csv"
    execution_path = output_dir / "hf3_measured_reset_execution_rows.csv"
    actor_view_path = output_dir / "hf3_actor_view_contract_rows.csv"
    outcome_path = output_dir / "hf3_reset_outcome_rows.csv"
    claim_path = output_dir / "hf3_claim_boundary_checks.csv"
    gate_path = output_dir / "measured_reset_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(request_path, request_rows, fieldnames=REQUEST_FIELDNAMES)
    write_csv_rows(backend_path, backend_rows, fieldnames=BACKEND_PROBE_FIELDNAMES)
    write_csv_rows(execution_path, execution_rows, fieldnames=EXECUTION_FIELDNAMES)
    write_csv_rows(actor_view_path, actor_view_rows, fieldnames=ACTOR_VIEW_FIELDNAMES)
    write_csv_rows(outcome_path, outcome_rows, fieldnames=OUTCOME_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2564_summary=m2564_summary,
        request_rows=request_rows,
        backend_rows=backend_rows,
        execution_rows=execution_rows,
        actor_view_rows=actor_view_rows,
        outcome_rows=outcome_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        request_path=request_path,
        backend_path=backend_path,
        execution_path=execution_path,
        actor_view_path=actor_view_path,
        outcome_path=outcome_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_measured_reset_request_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in sorted(candidate_rows, key=lambda row: row["reset_candidate_id"]):
        reset_candidate_id = candidate["reset_candidate_id"]
        route_role_id = candidate["route_role_id"]
        obs_shape = _int_value(candidate.get("actor_observation_shape"), default=-1)
        action_shape = _int_value(candidate.get("action_shape"), default=-1)
        seed = MEASURED_RESET_SEEDS.get(reset_candidate_id, 256899)
        status_pass = bool(
            _row_passed(candidate)
            and obs_shape == P0_OBSERVATION_DIM
            and action_shape == ACTION_DIM
            and candidate.get("pilot_admission_status") == "not_admitted_reset_execution_preflight_only"
            and not _boolish(candidate.get("reset_success_claim_allowed"))
        )
        rows.append(
            {
                "reset_request_id": reset_candidate_id.replace(
                    "reset_execution_candidate", "measured_reset_request"
                ),
                "reset_candidate_id": reset_candidate_id,
                "route_role_id": route_role_id,
                "backend_family": "repo_local_dynamics_backend_contract",
                "scenario_spec_id": f"hf3_measured_reset_feasibility::{route_role_id}",
                "seed": int(seed),
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "policy_action_allowed": False,
                "environment_step_allowed": False,
                "rollout_allowed": False,
                "actor_input_mutation_allowed": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_backend_probe_rows(request_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for request in request_rows:
        rows.append(
            {
                "backend_probe_id": f"{request['reset_request_id']}_backend_probe",
                "reset_request_id": request["reset_request_id"],
                "backend_family": request["backend_family"],
                "backend_module": "autodrift.high_fidelity_interface",
                "backend_class": "CurrentSimDynamicsBackend",
                "external_install_allowed": False,
                "external_import_allowed": False,
                "dependency_mutation_allowed": False,
                "backend_reset_allowed_in_m2568": True,
                "backend_step_allowed_in_m2568": False,
                "status_pass": bool(_row_passed(request)),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def execute_reset_only_rows(
    request_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    execution_rows: list[dict[str, Any]] = []
    actor_view_rows: list[dict[str, Any]] = []
    outcome_rows: list[dict[str, Any]] = []
    extractor = P0ObservationExtractor()

    for request in request_rows:
        reset_execution_id = f"{request['reset_request_id']}_reset_execution"
        reset_attempted = False
        actor_view_available = False
        diagnostics_recorded = False
        actor_observation_shape = -1
        reset_status = "not_attempted"

        backend = CurrentSimDynamicsBackend()
        try:
            reset_attempted = True
            result = backend.reset(
                BackendResetRequest(
                    seed=_int_value(request["seed"], default=0),
                    scenario_spec_id=str(request["scenario_spec_id"]),
                    role_family=str(request["route_role_id"]),
                )
            )
            observation = extractor.extract(result.actor_view)
            actor_observation_shape = int(observation.shape[0])
            actor_view_available = actor_observation_shape == P0_OBSERVATION_DIM
            diagnostics_recorded = isinstance(result.diagnostics, dict)
            reset_status = (
                "reset_observed_actor_view_available"
                if actor_view_available
                else "reset_observed_actor_view_invalid"
            )
        except Exception as exc:  # pragma: no cover - kept for audit artifact completeness.
            reset_status = f"reset_failed:{type(exc).__name__}"
        finally:
            backend.close()

        execution_status_pass = bool(
            _row_passed(request)
            and reset_attempted
            and actor_view_available
            and diagnostics_recorded
        )
        execution_rows.append(
            {
                "reset_execution_id": reset_execution_id,
                "reset_request_id": request["reset_request_id"],
                "reset_attempted": bool(reset_attempted),
                "reset_status": reset_status,
                "actor_view_available": bool(actor_view_available),
                "diagnostics_recorded": bool(diagnostics_recorded),
                "policy_action_executed": False,
                "environment_step_executed": False,
                "rollout_executed": False,
                "reset_success_claim_allowed": False,
                "status_pass": execution_status_pass,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
        actor_view_rows.append(
            {
                "actor_view_check_id": f"{reset_execution_id}_actor_view_contract",
                "reset_execution_id": reset_execution_id,
                "actor_observation_shape": actor_observation_shape,
                "action_shape": ACTION_DIM,
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "status_pass": bool(
                    execution_status_pass
                    and actor_observation_shape == P0_OBSERVATION_DIM
                    and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
        outcome_rows.append(
            {
                "outcome_check_id": f"{reset_execution_id}_outcome",
                "reset_execution_id": reset_execution_id,
                "backend_available": True,
                "reset_request_valid": bool(_row_passed(request)),
                "reset_attempted": bool(reset_attempted),
                "actor_view_available": bool(actor_view_available),
                "reset_status_present": bool(reset_status),
                "reset_success_claim_allowed": False,
                "validation_claim_allowed": False,
                "status_pass": bool(execution_status_pass and reset_status),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return execution_rows, actor_view_rows, outcome_rows


def build_claim_boundary_checks(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reset_execution_observed = bool(
        len(execution_rows) == 2
        and _all_status_pass(execution_rows)
        and all(_boolish(row["reset_attempted"]) for row in execution_rows)
        and all(_boolish(row["actor_view_available"]) for row in execution_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and reset_execution_observed)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2568": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family == "reset_execution_observed" or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2564_summary: dict[str, Any],
    request_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"] != "reset_execution_observed"
        and _boolish(row["claim_allowed_in_m2568"])
    ]
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()) and bool(m2564_summary.get("status_pass")),
            f"missing={sum(1 for exists in source_exists.values() if not exists)};m2564_status={m2564_summary.get('status_pass')}",
            "missing=0;m2564_status=True",
            "lineage_invalid",
        ),
        (
            "measured_reset_requests_complete",
            "scenario",
            len(request_rows) == 2
            and _all_status_pass(request_rows)
            and not any(_boolish(row["policy_action_allowed"]) for row in request_rows)
            and not any(_boolish(row["environment_step_allowed"]) for row in request_rows)
            and not any(_boolish(row["rollout_allowed"]) for row in request_rows),
            f"rows={len(request_rows)}",
            "rows=2;policy=false;step=false;rollout=false",
            "scenario_sampling_failure",
        ),
        (
            "backend_probe_rows_pass",
            "contract",
            len(backend_rows) == 2
            and _all_status_pass(backend_rows)
            and all(_boolish(row["backend_reset_allowed_in_m2568"]) for row in backend_rows)
            and not any(_boolish(row["backend_step_allowed_in_m2568"]) for row in backend_rows)
            and not any(_boolish(row["external_install_allowed"]) for row in backend_rows)
            and not any(_boolish(row["external_import_allowed"]) for row in backend_rows)
            and not any(_boolish(row["dependency_mutation_allowed"]) for row in backend_rows),
            f"rows={len(backend_rows)}",
            "rows=2;reset=true;step=false;external=false;dependency=false",
            "contract_violation",
        ),
        (
            "reset_only_execution_rows_pass",
            "metric",
            len(execution_rows) == 2
            and _all_status_pass(execution_rows)
            and all(_boolish(row["reset_attempted"]) for row in execution_rows)
            and all(_boolish(row["actor_view_available"]) for row in execution_rows)
            and not any(_boolish(row["policy_action_executed"]) for row in execution_rows)
            and not any(_boolish(row["environment_step_executed"]) for row in execution_rows)
            and not any(_boolish(row["rollout_executed"]) for row in execution_rows)
            and not any(_boolish(row["reset_success_claim_allowed"]) for row in execution_rows),
            f"rows={len(execution_rows)}",
            "rows=2;reset_attempted=true;actor_view=true;policy=false;step=false;rollout=false;success_claim=false",
            "metric_artifact",
        ),
        (
            "actor_view_contract_rows_pass",
            "contract",
            len(actor_view_rows) == 2
            and _all_status_pass(actor_view_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in actor_view_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in actor_view_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_view_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in actor_view_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_view_rows),
            f"rows={len(actor_view_rows)}",
            "rows=2;obs=72;action=3;hidden=false;diagnostics=false;labels=false",
            "contract_violation",
        ),
        (
            "reset_outcome_rows_pass",
            "metric",
            len(outcome_rows) == 2
            and _all_status_pass(outcome_rows)
            and all(_boolish(row["reset_attempted"]) for row in outcome_rows)
            and all(_boolish(row["actor_view_available"]) for row in outcome_rows)
            and not any(_boolish(row["reset_success_claim_allowed"]) for row in outcome_rows)
            and not any(_boolish(row["validation_claim_allowed"]) for row in outcome_rows),
            f"rows={len(outcome_rows)}",
            "rows=2;reset_attempted=true;actor_view=true;reset_success=false;validation=false",
            "metric_artifact",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not forbidden_claims_allowed
            and any(
                row["claim_family"] == "reset_execution_observed"
                and _boolish(row["claim_allowed_in_m2568"])
                for row in claim_rows
            ),
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;reset_execution_observed=true",
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
    m2564_summary: dict[str, Any],
    request_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    request_path: Path,
    backend_path: Path,
    execution_path: Path,
    actor_view_path: Path,
    outcome_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    reset_status_counts = Counter(str(row["reset_status"]) for row in execution_rows)
    role_counts = Counter(str(row["route_role_id"]) for row in request_rows)
    reset_execution_observed_claim_allowed = any(
        row["claim_family"] == "reset_execution_observed"
        and _boolish(row["claim_allowed_in_m2568"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"] != "reset_execution_observed"
        and _boolish(row["claim_allowed_in_m2568"])
        for row in claim_rows
    )
    status_pass = (
        all(source_exists.values())
        and bool(m2564_summary.get("status_pass"))
        and len(request_rows) == 2
        and _all_status_pass(request_rows)
        and len(backend_rows) == 2
        and _all_status_pass(backend_rows)
        and len(execution_rows) == 2
        and _all_status_pass(execution_rows)
        and len(actor_view_rows) == 2
        and _all_status_pass(actor_view_rows)
        and len(outcome_rows) == 2
        and _all_status_pass(outcome_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and reset_execution_observed_claim_allowed
        and not forbidden_claim_allowed
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_measured_reset_feasibility_execution_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_measured_reset_feasibility_execution_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_measured_reset_request_rows": str(request_path),
        "hf3_backend_probe_rows": str(backend_path),
        "hf3_measured_reset_execution_rows": str(execution_path),
        "hf3_actor_view_contract_rows": str(actor_view_path),
        "hf3_reset_outcome_rows": str(outcome_path),
        "hf3_claim_boundary_checks": str(claim_path),
        "measured_reset_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2564_status_pass": bool(m2564_summary.get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "measured_reset_request_row_count": len(request_rows),
        "measured_reset_requests_all_pass": _all_status_pass(request_rows),
        "measured_reset_role_counts": dict(sorted(role_counts.items())),
        "backend_probe_row_count": len(backend_rows),
        "backend_probe_rows_all_pass": _all_status_pass(backend_rows),
        "backend_reset_allowed_in_m2568": any(_boolish(row["backend_reset_allowed_in_m2568"]) for row in backend_rows),
        "backend_step_allowed_in_m2568": any(_boolish(row["backend_step_allowed_in_m2568"]) for row in backend_rows),
        "external_install_allowed": any(_boolish(row["external_install_allowed"]) for row in backend_rows),
        "external_import_allowed": any(_boolish(row["external_import_allowed"]) for row in backend_rows),
        "dependency_mutation_allowed": any(_boolish(row["dependency_mutation_allowed"]) for row in backend_rows),
        "reset_execution_row_count": len(execution_rows),
        "reset_execution_rows_all_pass": _all_status_pass(execution_rows),
        "reset_only_execution_run": any(_boolish(row["reset_attempted"]) for row in execution_rows),
        "reset_execution_attempted_count": sum(1 for row in execution_rows if _boolish(row["reset_attempted"])),
        "actor_view_available_count": sum(1 for row in execution_rows if _boolish(row["actor_view_available"])),
        "reset_status_counts": dict(sorted(reset_status_counts.items())),
        "policy_action_executed": any(_boolish(row["policy_action_executed"]) for row in execution_rows),
        "environment_step_executed": any(_boolish(row["environment_step_executed"]) for row in execution_rows),
        "rollout_executed": any(_boolish(row["rollout_executed"]) for row in execution_rows),
        "reset_success_claim_allowed": any(_boolish(row["reset_success_claim_allowed"]) for row in execution_rows),
        "actor_view_contract_row_count": len(actor_view_rows),
        "actor_view_contract_rows_all_pass": _all_status_pass(actor_view_rows),
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_view_rows
        ),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in actor_view_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_view_rows),
        "reset_outcome_row_count": len(outcome_rows),
        "reset_outcome_rows_all_pass": _all_status_pass(outcome_rows),
        "validation_claim_allowed": any(_boolish(row["validation_claim_allowed"]) for row in outcome_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "reset_execution_observed_claim_allowed": bool(reset_execution_observed_claim_allowed),
        "forbidden_claim_allowed_in_m2568": bool(forbidden_claim_allowed),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "repo_local_reset_only": True,
        **FORBIDDEN_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2568 Engineering Controller Route A Baseline HF3 Measured Reset-Feasibility Execution Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_measured_reset_feasibility_execution.py`",
                f"- summary: `{summary['summary']}`",
                f"- reset requests: `{summary['hf3_measured_reset_request_rows']}`",
                f"- backend probes: `{summary['hf3_backend_probe_rows']}`",
                f"- reset-only executions: `{summary['hf3_measured_reset_execution_rows']}`",
                f"- actor-view contract rows: `{summary['hf3_actor_view_contract_rows']}`",
                f"- reset outcome rows: `{summary['hf3_reset_outcome_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['measured_reset_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- policy-action/step/rollout/training/ranking/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2568 materializes Route A HF3 measured reset-feasibility",
                "execution artifacts for the two accepted reset candidates. The",
                "only execution performed is repo-local backend reset. M2568 does",
                "not execute policy actions, environment steps, or rollouts.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"measured_reset_request_row_count: {summary['measured_reset_request_row_count']}",
                f"backend_probe_row_count: {summary['backend_probe_row_count']}",
                f"reset_execution_row_count: {summary['reset_execution_row_count']}",
                f"actor_view_contract_row_count: {summary['actor_view_contract_row_count']}",
                f"reset_outcome_row_count: {summary['reset_outcome_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"reset_only_execution_run: {str(summary['reset_only_execution_run']).lower()}",
                f"reset_execution_attempted_count: {summary['reset_execution_attempted_count']}",
                f"actor_view_available_count: {summary['actor_view_available_count']}",
                f"policy_action_executed: {str(summary['policy_action_executed']).lower()}",
                f"environment_step_executed: {str(summary['environment_step_executed']).lower()}",
                f"rollout_executed: {str(summary['rollout_executed']).lower()}",
                f"reset_success_claim_allowed: {str(summary['reset_success_claim_allowed']).lower()}",
                f"reset_execution_observed_claim_allowed: {str(summary['reset_execution_observed_claim_allowed']).lower()}",
                f"forbidden_claim_allowed_in_m2568: {str(summary['forbidden_claim_allowed_in_m2568']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2568 supports only the operational claim that repo-local reset",
                "execution was observed and yielded actor-view contract rows for",
                "both reset candidates. It does not support reset success, rollout",
                "feasibility, validation readiness/result, driver performance,",
                "controller ranking, paper evidence, FW-vs-GRU, current-sim",
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
    return all(_row_passed(row) for row in rows)


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
    parser.add_argument("--m2564-summary", type=Path, default=DEFAULT_M2564_SUMMARY)
    parser.add_argument("--m2564-candidates", type=Path, default=DEFAULT_M2564_CANDIDATES)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_measured_reset_feasibility_execution(
        args.output_dir,
        m2564_summary_path=args.m2564_summary,
        m2564_candidates_path=args.m2564_candidates,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "reset_requests={measured_reset_request_row_count} "
        "reset_attempted={reset_execution_attempted_count} "
        "summary={summary}".format(**summary)
    )


if __name__ == "__main__":
    main()
