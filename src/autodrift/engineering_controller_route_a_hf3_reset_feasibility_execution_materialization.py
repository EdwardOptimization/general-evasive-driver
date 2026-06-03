"""Route A HF3 reset-feasibility execution boundary materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2565-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution")
DEFAULT_HF3_PREFLIGHT_SUMMARY = Path(
    "runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json"
)
DEFAULT_HF3_CANDIDATES = Path(
    "runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_pilot_candidate_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2563-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-design.md",
    "docs/m2562-engineering-controller-route-a-baseline-hf3-low-cost-pilot-result-synthesis.md",
    "docs/m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit.md",
    "runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json",
    "runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_pilot_candidate_rows.csv",
    "runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_reset_feasibility_plan.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 reset-feasibility execution materialization preflight only; "
    "not external simulation, reset execution, policy action, rollout, "
    "ranking, validation, driver performance, paper, FW-vs-GRU, current-sim "
    "verdict, high-fidelity validation, or self-ID"
)

RESET_EXECUTION_STATUS = "planned_not_executed_in_m2564"
PILOT_ADMISSION_STATUS = "not_admitted_reset_execution_preflight_only"

BACKEND_AVAILABILITY_CHECKS = (
    (
        "repo_backend_contract_availability",
        "repo_local_dynamics_backend_contract",
        "src/autodrift/high_fidelity_interface.py",
    ),
    (
        "chrono_vehicle_boundary",
        "external_chrono_vehicle_boundary",
        "declared_external_boundary_no_import",
    ),
    (
        "black_box_simulator_boundary",
        "black_box_simulator_boundary",
        "declared_external_boundary_no_import",
    ),
    (
        "dependency_mutation_boundary",
        "local_dependency_mutation_boundary",
        "no_dependency_mutation_allowed",
    ),
)

RESET_OUTCOME_FIELDS = (
    ("backend_available", "backend_boundary"),
    ("reset_request_valid", "request_contract"),
    ("reset_attempted", "execution_status"),
    ("reset_status", "execution_status"),
    ("actor_view_available", "actor_view_contract"),
    ("diagnostics_available", "diagnostics_contract"),
    ("failure_reason", "failure_taxonomy"),
    ("execution_timestamp", "audit_lineage"),
)

CLAIM_CHECKS = (
    ("pilot_admission", "reset execution audit plus rollout feasibility route"),
    ("reset_execution", "explicit later reset execution milestone"),
    ("reset_success", "measured reset execution artifact and audit"),
    ("rollout_feasibility", "reset success audit plus rollout design"),
    ("high_fidelity_validation_readiness", "audited reset and rollout feasibility evidence"),
    ("controller_ranking_or_winner_selection", "controller-family comparison milestone"),
    ("driver_performance_claim", "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", "separate paper-route evidence matrix"),
)

RESET_CANDIDATE_FIELDNAMES = [
    "reset_candidate_id",
    "source_candidate_id",
    "route_role_id",
    "route_role_label",
    "source_binding_id",
    "source_binding_status",
    "actor_observation_shape",
    "action_shape",
    "pilot_admission_status",
    "reset_execution_status",
    "reset_success_claim_allowed",
    "status_pass",
    "claim_boundary",
]

BACKEND_AVAILABILITY_FIELDNAMES = [
    "availability_check_id",
    "backend_family",
    "availability_source",
    "install_allowed",
    "import_allowed",
    "runtime_execution_allowed",
    "dependency_mutation_allowed",
    "availability_claim_scope",
    "status_pass",
    "claim_boundary",
]

RESET_REQUEST_FIELDNAMES = [
    "request_contract_id",
    "reset_candidate_id",
    "backend_family",
    "scenario_spec_id",
    "seed_policy",
    "actor_observation_shape",
    "action_shape",
    "actor_input_mutation_allowed",
    "oracle_field_allowed",
    "metadata_actor_visible",
    "status_pass",
    "claim_boundary",
]

RESET_PLAN_FIELDNAMES = [
    "reset_plan_id",
    "reset_candidate_id",
    "backend_family",
    "requires_backend_availability",
    "requires_reset_request_contract",
    "reset_execution_allowed_in_m2564",
    "policy_action_allowed_in_m2564",
    "environment_step_allowed_in_m2564",
    "rollout_execution_allowed_in_m2564",
    "required_before_reset_success_claim",
    "status_pass",
    "claim_boundary",
]

OUTCOME_SCHEMA_FIELDNAMES = [
    "outcome_field",
    "field_family",
    "actor_visible_allowed",
    "required_for_execution_audit",
    "allowed_to_support_reset_success_after_execution",
    "allowed_to_support_validation",
    "status_pass",
    "claim_boundary",
]

CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2564",
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

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
    "environment_reset_run": False,
    "reset_execution_run": False,
    "reset_success_claim_made": False,
    "rollout_success_claim_made": False,
    "policy_rollout_run": False,
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
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}


def materialize_route_a_hf3_reset_feasibility_execution_preflight(
    output_dir: Path,
    *,
    hf3_preflight_summary_path: Path = DEFAULT_HF3_PREFLIGHT_SUMMARY,
    hf3_candidates_path: Path = DEFAULT_HF3_CANDIDATES,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    preflight_summary = read_json(hf3_preflight_summary_path)
    candidate_source_rows = _read_csv_rows(hf3_candidates_path)

    reset_candidate_rows = build_reset_execution_candidate_rows(candidate_source_rows)
    backend_rows = build_backend_availability_checks()
    request_rows = build_reset_request_contract_rows(reset_candidate_rows)
    plan_rows = build_reset_execution_plan_rows(reset_candidate_rows)
    outcome_rows = build_reset_outcome_schema_rows()
    claim_rows = build_claim_boundary_checks()
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        preflight_summary=preflight_summary,
        reset_candidate_rows=reset_candidate_rows,
        backend_rows=backend_rows,
        request_rows=request_rows,
        plan_rows=plan_rows,
        outcome_rows=outcome_rows,
        claim_rows=claim_rows,
    )

    reset_candidate_path = output_dir / "hf3_reset_execution_candidate_rows.csv"
    backend_path = output_dir / "hf3_backend_availability_checks.csv"
    request_path = output_dir / "hf3_reset_request_contract.csv"
    plan_path = output_dir / "hf3_reset_execution_plan.csv"
    outcome_path = output_dir / "hf3_reset_outcome_schema.csv"
    claim_path = output_dir / "hf3_claim_boundary_checks.csv"
    gate_path = output_dir / "materialization_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(reset_candidate_path, reset_candidate_rows, fieldnames=RESET_CANDIDATE_FIELDNAMES)
    write_csv_rows(backend_path, backend_rows, fieldnames=BACKEND_AVAILABILITY_FIELDNAMES)
    write_csv_rows(request_path, request_rows, fieldnames=RESET_REQUEST_FIELDNAMES)
    write_csv_rows(plan_path, plan_rows, fieldnames=RESET_PLAN_FIELDNAMES)
    write_csv_rows(outcome_path, outcome_rows, fieldnames=OUTCOME_SCHEMA_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        preflight_summary=preflight_summary,
        reset_candidate_rows=reset_candidate_rows,
        backend_rows=backend_rows,
        request_rows=request_rows,
        plan_rows=plan_rows,
        outcome_rows=outcome_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        reset_candidate_path=reset_candidate_path,
        backend_path=backend_path,
        request_path=request_path,
        plan_path=plan_path,
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


def build_reset_execution_candidate_rows(candidate_source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in candidate_source_rows:
        source_candidate_id = source["candidate_id"]
        reset_candidate_id = source_candidate_id.replace("design_candidate", "reset_execution_candidate")
        obs_shape = _int_value(source.get("actor_observation_shape"), default=-1)
        action_shape = _int_value(source.get("action_shape"), default=-1)
        status_pass = bool(
            _row_passed(source)
            and obs_shape == P0_OBSERVATION_DIM
            and action_shape == ACTION_DIM
            and source.get("hf3_admission_status") == "requires_m2560_reset_and_rollout_feasibility"
            and not _boolish(source.get("validation_claim_allowed"))
        )
        rows.append(
            {
                "reset_candidate_id": reset_candidate_id,
                "source_candidate_id": source_candidate_id,
                "route_role_id": source["route_role_id"],
                "route_role_label": source["route_role_label"],
                "source_binding_id": source["source_binding_id"],
                "source_binding_status": source["source_binding_status"],
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "pilot_admission_status": PILOT_ADMISSION_STATUS,
                "reset_execution_status": RESET_EXECUTION_STATUS,
                "reset_success_claim_allowed": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_backend_availability_checks() -> list[dict[str, Any]]:
    rows = []
    for check_id, backend_family, source in BACKEND_AVAILABILITY_CHECKS:
        rows.append(
            {
                "availability_check_id": check_id,
                "backend_family": backend_family,
                "availability_source": source,
                "install_allowed": False,
                "import_allowed": False,
                "runtime_execution_allowed": False,
                "dependency_mutation_allowed": False,
                "availability_claim_scope": "boundary_record_only_no_runtime_claim",
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_request_contract_rows(reset_candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in reset_candidate_rows:
        route_role_id = candidate["route_role_id"]
        rows.append(
            {
                "request_contract_id": f"{candidate['reset_candidate_id']}_request_contract",
                "reset_candidate_id": candidate["reset_candidate_id"],
                "backend_family": "repo_local_dynamics_backend_contract",
                "scenario_spec_id": f"hf3_reset_feasibility::{route_role_id}",
                "seed_policy": "deterministic_manifest_seed_list_required_before_execution",
                "actor_observation_shape": candidate["actor_observation_shape"],
                "action_shape": candidate["action_shape"],
                "actor_input_mutation_allowed": False,
                "oracle_field_allowed": False,
                "metadata_actor_visible": False,
                "status_pass": bool(
                    _row_passed(candidate)
                    and _int_value(candidate["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM
                    and _int_value(candidate["action_shape"], default=-1) == ACTION_DIM
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_execution_plan_rows(reset_candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in reset_candidate_rows:
        rows.append(
            {
                "reset_plan_id": f"{candidate['reset_candidate_id']}_reset_plan",
                "reset_candidate_id": candidate["reset_candidate_id"],
                "backend_family": "repo_local_dynamics_backend_contract",
                "requires_backend_availability": "hf3_backend_availability_checks",
                "requires_reset_request_contract": "hf3_reset_request_contract",
                "reset_execution_allowed_in_m2564": False,
                "policy_action_allowed_in_m2564": False,
                "environment_step_allowed_in_m2564": False,
                "rollout_execution_allowed_in_m2564": False,
                "required_before_reset_success_claim": "later_measured_reset_execution_artifact_and_audit",
                "status_pass": _row_passed(candidate),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_outcome_schema_rows() -> list[dict[str, Any]]:
    rows = []
    for outcome_field, family in RESET_OUTCOME_FIELDS:
        rows.append(
            {
                "outcome_field": outcome_field,
                "field_family": family,
                "actor_visible_allowed": False,
                "required_for_execution_audit": True,
                "allowed_to_support_reset_success_after_execution": outcome_field
                in {"reset_attempted", "reset_status", "actor_view_available"},
                "allowed_to_support_validation": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks() -> list[dict[str, Any]]:
    rows = []
    for claim_family, evidence_required in CLAIM_CHECKS:
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2564": False,
                "evidence_required_before_claim": evidence_required,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    preflight_summary: dict[str, Any],
    reset_candidate_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    request_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()) and bool(preflight_summary.get("status_pass")),
            f"missing={sum(1 for exists in source_exists.values() if not exists)};m2560_status={preflight_summary.get('status_pass')}",
            "missing=0;m2560_status=True",
            "lineage_invalid",
        ),
        (
            "reset_execution_candidates_complete",
            "scenario",
            len(reset_candidate_rows) == 2
            and _all_status_pass(reset_candidate_rows)
            and not any(_boolish(row["reset_success_claim_allowed"]) for row in reset_candidate_rows),
            f"rows={len(reset_candidate_rows)}",
            "rows=2;reset_success_claim=false",
            "scenario_sampling_failure",
        ),
        (
            "backend_availability_checks_pass",
            "contract",
            len(backend_rows) == len(BACKEND_AVAILABILITY_CHECKS)
            and _all_status_pass(backend_rows)
            and not any(_boolish(row["install_allowed"]) for row in backend_rows)
            and not any(_boolish(row["import_allowed"]) for row in backend_rows)
            and not any(_boolish(row["runtime_execution_allowed"]) for row in backend_rows)
            and not any(_boolish(row["dependency_mutation_allowed"]) for row in backend_rows),
            f"rows={len(backend_rows)}",
            f"rows={len(BACKEND_AVAILABILITY_CHECKS)};install=false;import=false;run=false;dependency=false",
            "contract_violation",
        ),
        (
            "reset_request_contracts_pass",
            "contract",
            len(request_rows) == 2
            and _all_status_pass(request_rows)
            and not any(_boolish(row["actor_input_mutation_allowed"]) for row in request_rows)
            and not any(_boolish(row["oracle_field_allowed"]) for row in request_rows),
            f"rows={len(request_rows)}",
            "rows=2;actor_mutation=false;oracle=false",
            "contract_violation",
        ),
        (
            "reset_execution_plans_pass",
            "scenario",
            len(plan_rows) == 2
            and _all_status_pass(plan_rows)
            and not any(_boolish(row["reset_execution_allowed_in_m2564"]) for row in plan_rows)
            and not any(_boolish(row["policy_action_allowed_in_m2564"]) for row in plan_rows)
            and not any(_boolish(row["environment_step_allowed_in_m2564"]) for row in plan_rows)
            and not any(_boolish(row["rollout_execution_allowed_in_m2564"]) for row in plan_rows),
            f"rows={len(plan_rows)}",
            "rows=2;reset=false;policy_action=false;step=false;rollout=false",
            "scenario_sampling_failure",
        ),
        (
            "reset_outcome_schema_pass",
            "metric",
            len(outcome_rows) == len(RESET_OUTCOME_FIELDS)
            and _all_status_pass(outcome_rows)
            and not any(_boolish(row["actor_visible_allowed"]) for row in outcome_rows)
            and not any(_boolish(row["allowed_to_support_validation"]) for row in outcome_rows),
            f"rows={len(outcome_rows)}",
            f"rows={len(RESET_OUTCOME_FIELDS)};actor_visible=false;validation=false",
            "metric_artifact",
        ),
        (
            "claim_boundary_checks_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not any(_boolish(row["claim_allowed_in_m2564"]) for row in claim_rows),
            f"rows={len(claim_rows)}",
            f"rows={len(CLAIM_CHECKS)};claims=false",
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
            "no_false_claim_flags",
            "claim_boundary",
            not any(FALSE_CLAIM_FLAGS.values()),
            "all false",
            "all false",
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
    preflight_summary: dict[str, Any],
    reset_candidate_rows: list[dict[str, Any]],
    backend_rows: list[dict[str, Any]],
    request_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    reset_candidate_path: Path,
    backend_path: Path,
    request_path: Path,
    plan_path: Path,
    outcome_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    candidate_status_counts = Counter(str(row["reset_execution_status"]) for row in reset_candidate_rows)
    pilot_admission_counts = Counter(str(row["pilot_admission_status"]) for row in reset_candidate_rows)
    backend_family_counts = Counter(str(row["backend_family"]) for row in backend_rows)
    candidate_rows_pilot_admitted = any(
        str(row["pilot_admission_status"]) != PILOT_ADMISSION_STATUS for row in reset_candidate_rows
    )
    reset_success_claim_allowed = any(
        _boolish(row["reset_success_claim_allowed"]) for row in reset_candidate_rows
    )
    status_pass = (
        all(source_exists.values())
        and bool(preflight_summary.get("status_pass"))
        and len(reset_candidate_rows) == 2
        and _all_status_pass(reset_candidate_rows)
        and len(backend_rows) == len(BACKEND_AVAILABILITY_CHECKS)
        and _all_status_pass(backend_rows)
        and len(request_rows) == 2
        and _all_status_pass(request_rows)
        and len(plan_rows) == 2
        and _all_status_pass(plan_rows)
        and len(outcome_rows) == len(RESET_OUTCOME_FIELDS)
        and _all_status_pass(outcome_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_reset_feasibility_execution_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_reset_feasibility_execution_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_reset_execution_candidate_rows": str(reset_candidate_path),
        "hf3_backend_availability_checks": str(backend_path),
        "hf3_reset_request_contract": str(request_path),
        "hf3_reset_execution_plan": str(plan_path),
        "hf3_reset_outcome_schema": str(outcome_path),
        "hf3_claim_boundary_checks": str(claim_path),
        "materialization_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2560_status_pass": bool(preflight_summary.get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "reset_execution_candidate_row_count": len(reset_candidate_rows),
        "reset_execution_candidates_all_pass": _all_status_pass(reset_candidate_rows),
        "reset_execution_status_counts": dict(sorted(candidate_status_counts.items())),
        "pilot_admission_status_counts": dict(sorted(pilot_admission_counts.items())),
        "candidate_rows_pilot_admitted": bool(candidate_rows_pilot_admitted),
        "reset_success_claim_allowed": bool(reset_success_claim_allowed),
        "backend_availability_check_count": len(backend_rows),
        "backend_availability_checks_all_pass": _all_status_pass(backend_rows),
        "backend_family_counts": dict(sorted(backend_family_counts.items())),
        "external_install_allowed": any(_boolish(row["install_allowed"]) for row in backend_rows),
        "external_import_allowed": any(_boolish(row["import_allowed"]) for row in backend_rows),
        "runtime_execution_allowed": any(_boolish(row["runtime_execution_allowed"]) for row in backend_rows),
        "external_runtime_execution_allowed": any(
            _boolish(row["runtime_execution_allowed"]) for row in backend_rows
        ),
        "dependency_mutation_allowed": any(
            _boolish(row["dependency_mutation_allowed"]) for row in backend_rows
        ),
        "reset_request_contract_count": len(request_rows),
        "reset_request_contracts_all_pass": _all_status_pass(request_rows),
        "actor_input_mutation_allowed": any(
            _boolish(row["actor_input_mutation_allowed"]) for row in request_rows
        ),
        "oracle_field_allowed": any(_boolish(row["oracle_field_allowed"]) for row in request_rows),
        "metadata_actor_visible": any(_boolish(row["metadata_actor_visible"]) for row in request_rows),
        "reset_execution_plan_count": len(plan_rows),
        "reset_execution_plans_all_pass": _all_status_pass(plan_rows),
        "reset_execution_allowed_in_m2564": any(
            _boolish(row["reset_execution_allowed_in_m2564"]) for row in plan_rows
        ),
        "policy_action_allowed_in_m2564": any(
            _boolish(row["policy_action_allowed_in_m2564"]) for row in plan_rows
        ),
        "environment_step_allowed_in_m2564": any(
            _boolish(row["environment_step_allowed_in_m2564"]) for row in plan_rows
        ),
        "rollout_execution_allowed_in_m2564": any(
            _boolish(row["rollout_execution_allowed_in_m2564"]) for row in plan_rows
        ),
        "reset_outcome_schema_row_count": len(outcome_rows),
        "reset_outcome_schema_all_pass": _all_status_pass(outcome_rows),
        "outcome_actor_visible_allowed": any(
            _boolish(row["actor_visible_allowed"]) for row in outcome_rows
        ),
        "outcome_validation_allowed": any(
            _boolish(row["allowed_to_support_validation"]) for row in outcome_rows
        ),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "claim_allowed_in_m2564": any(
            _boolish(row["claim_allowed_in_m2564"]) for row in claim_rows
        ),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "hidden_oracle_actor_input_detected": False,
        "external_backend_boundary_only": True,
        **FALSE_CLAIM_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2564 Engineering Controller Route A Baseline HF3 Reset-Feasibility Execution Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_reset_feasibility_execution_materialization.py`",
                f"- summary: `{summary['summary']}`",
                f"- reset candidates: `{summary['hf3_reset_execution_candidate_rows']}`",
                f"- backend availability checks: `{summary['hf3_backend_availability_checks']}`",
                f"- reset request contract: `{summary['hf3_reset_request_contract']}`",
                f"- reset execution plan: `{summary['hf3_reset_execution_plan']}`",
                f"- reset outcome schema: `{summary['hf3_reset_outcome_schema']}`",
                f"- claim-boundary checks: `{summary['hf3_claim_boundary_checks']}`",
                f"- materialization gate matrix: `{summary['materialization_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- reset/policy-action/step/rollout/training/ranking/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2564 materializes Route A HF3 reset-feasibility execution",
                "boundary artifacts for the two accepted pilot candidates. The",
                "rows define backend availability, reset request contracts, reset",
                "execution plans, reset outcome schema, and claim boundaries. They",
                "do not execute reset or grant pilot admission.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"reset_execution_candidate_row_count: {summary['reset_execution_candidate_row_count']}",
                f"backend_availability_check_count: {summary['backend_availability_check_count']}",
                f"reset_request_contract_count: {summary['reset_request_contract_count']}",
                f"reset_execution_plan_count: {summary['reset_execution_plan_count']}",
                f"reset_outcome_schema_row_count: {summary['reset_outcome_schema_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"reset_execution_allowed_in_m2564: {str(summary['reset_execution_allowed_in_m2564']).lower()}",
                f"policy_action_allowed_in_m2564: {str(summary['policy_action_allowed_in_m2564']).lower()}",
                f"environment_step_allowed_in_m2564: {str(summary['environment_step_allowed_in_m2564']).lower()}",
                f"runtime_execution_allowed: {str(summary['runtime_execution_allowed']).lower()}",
                f"claim_allowed_in_m2564: {str(summary['claim_allowed_in_m2564']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2564 is a source-level reset-feasibility execution boundary",
                "materialization. It does not install, import, or run an external",
                "simulator; does not execute reset, policy actions, steps, or",
                "rollouts; does not rank policies, select a winner, promote",
                "checkpoints, compute success rates, validate driver performance,",
                "or provide paper/FW-vs-GRU/current-sim/high-fidelity/self-ID",
                "evidence.",
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
    parser.add_argument("--hf3-preflight-summary", type=Path, default=DEFAULT_HF3_PREFLIGHT_SUMMARY)
    parser.add_argument("--hf3-candidates", type=Path, default=DEFAULT_HF3_CANDIDATES)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_reset_feasibility_execution_preflight(
        args.output_dir,
        hf3_preflight_summary_path=args.hf3_preflight_summary,
        hf3_candidates_path=args.hf3_candidates,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "reset_candidates={reset_execution_candidate_row_count} "
        "backend_checks={backend_availability_check_count} "
        "reset_plans={reset_execution_plan_count} "
        "summary={summary}".format(**summary)
    )


if __name__ == "__main__":
    main()
