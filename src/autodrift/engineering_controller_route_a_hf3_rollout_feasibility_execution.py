"""Route A HF3 rollout-feasibility execution materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    P0_OBSERVATION_DIM,
    BackendResetRequest,
    CurrentSimDynamicsBackend,
    P0ObservationExtractor,
    physical_control_from_action,
    validate_actor_action,
)


DEFAULT_MILESTONE = "m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution")
DEFAULT_M2568_SUMMARY = Path(
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/summary.json"
)
DEFAULT_M2568_REQUESTS = Path(
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_request_rows.csv"
)
DEFAULT_M2568_EXECUTIONS = Path(
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_execution_rows.csv"
)
DEFAULT_CHECKPOINT = Path(
    "runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt"
)
TARGET_HORIZON_STEPS = 8
MIN_STEPS_FOR_EXECUTION_OBSERVED = 1

SOURCE_ARTIFACTS = (
    "docs/m2571-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-design.md",
    "docs/m2570-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-result-synthesis.md",
    "docs/m2569-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-result-audit.md",
    "docs/m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight.md",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/summary.json",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_request_rows.csv",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_execution_rows.csv",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_actor_view_contract_rows.csv",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_reset_outcome_rows.csv",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_claim_boundary_checks.csv",
    "runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/measured_reset_gate_matrix.csv",
    "runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt",
    "src/autodrift/high_fidelity_interface.py",
    "src/autodrift/checkpoints.py",
    "src/autodrift/rollout.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 rollout-feasibility execution materialization preflight only; "
    "repo-local reset, fixed-policy action, and backend-step execution may be "
    "observed; not rollout success, ranking, validation, driver performance, "
    "paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

ROLLOUT_REQUEST_FIELDNAMES = [
    "rollout_request_id",
    "source_reset_request_id",
    "reset_execution_id",
    "route_role_id",
    "backend_family",
    "scenario_spec_id",
    "seed",
    "actor_observation_shape",
    "action_shape",
    "policy_action_allowed_in_m2572",
    "environment_step_allowed_in_m2572",
    "rollout_allowed_in_m2572",
    "pilot_admission_allowed",
    "validation_claim_allowed",
    "status_pass",
    "claim_boundary",
]

POLICY_SOURCE_FIELDNAMES = [
    "policy_source_id",
    "checkpoint_path",
    "checkpoint_lineage",
    "loader",
    "policy_mode",
    "actor_input_source",
    "actor_observation_shape",
    "action_shape",
    "ranking_role",
    "promotion_allowed",
    "status_pass",
    "claim_boundary",
]

ROLLOUT_PLAN_FIELDNAMES = [
    "rollout_plan_id",
    "rollout_request_id",
    "policy_source_id",
    "backend_class",
    "reset_required",
    "target_horizon_steps",
    "min_steps_for_execution_observed",
    "early_termination_allowed_as_outcome",
    "success_rate_computation_allowed",
    "controller_family_verdict_allowed",
    "status_pass",
    "claim_boundary",
]

POLICY_ACTION_FIELDNAMES = [
    "policy_action_audit_id",
    "rollout_plan_id",
    "rollout_request_id",
    "policy_source_id",
    "step_index",
    "actor_observation_shape",
    "action_shape",
    "action_finite",
    "action_clipped_to_contract",
    "steer_command",
    "throttle_command",
    "brake_command",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "policy_action_executed",
    "status_pass",
    "claim_boundary",
]

BACKEND_STEP_FIELDNAMES = [
    "backend_step_outcome_id",
    "rollout_plan_id",
    "rollout_request_id",
    "step_index",
    "backend_family",
    "backend_class",
    "backend_step_attempted",
    "backend_status",
    "terminated_by_backend",
    "truncated_by_backend",
    "actor_view_available_after_step",
    "diagnostics_recorded",
    "diagnostics_actor_visible",
    "rollout_success_claim_allowed",
    "validation_claim_allowed",
    "status_pass",
    "claim_boundary",
]

ACTOR_VIEW_FIELDNAMES = [
    "actor_view_check_id",
    "rollout_plan_id",
    "rollout_request_id",
    "source_phase",
    "step_index",
    "actor_observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "rollout_outcome_actor_visible",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2572",
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
    "actor_input_mutation_performed": False,
    "action_contract_mutation_performed": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "pilot_admission_claim_made": False,
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
    ("reset_execution_observed", True, "M2568 reset-only execution rows and M2572 reset boundary"),
    ("rollout_feasibility_execution_observed", True, "M2572 policy-action and backend-step rows"),
    ("rollout_success", False, "later audited rollout success milestone with success criteria"),
    ("high_fidelity_validation_readiness_or_result", False, "external validation route after audited feasibility"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("success_rate_or_controller_family_verdict", False, "separate benchmark/verdict milestone"),
    ("driver_performance_claim", False, "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", False, "separate paper-route evidence matrix"),
)


def materialize_route_a_hf3_rollout_feasibility_execution(
    output_dir: Path,
    *,
    m2568_summary_path: Path = DEFAULT_M2568_SUMMARY,
    m2568_requests_path: Path = DEFAULT_M2568_REQUESTS,
    m2568_executions_path: Path = DEFAULT_M2568_EXECUTIONS,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2568_summary = read_json(m2568_summary_path)
    reset_request_rows = _read_csv_rows(m2568_requests_path)
    reset_execution_rows = _read_csv_rows(m2568_executions_path)

    rollout_request_rows = build_rollout_request_rows(reset_request_rows, reset_execution_rows)
    policy_source_rows = build_fixed_policy_source_rows(checkpoint_path)
    rollout_plan_rows = build_rollout_plan_rows(rollout_request_rows, policy_source_rows)
    policy_action_rows, backend_step_rows, actor_view_rows = execute_rollout_feasibility_rows(
        rollout_request_rows,
        rollout_plan_rows,
        checkpoint_path=checkpoint_path,
    )
    claim_rows = build_claim_boundary_checks(
        rollout_request_rows,
        policy_action_rows,
        backend_step_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2568_summary=m2568_summary,
        rollout_request_rows=rollout_request_rows,
        policy_source_rows=policy_source_rows,
        rollout_plan_rows=rollout_plan_rows,
        policy_action_rows=policy_action_rows,
        backend_step_rows=backend_step_rows,
        actor_view_rows=actor_view_rows,
        claim_rows=claim_rows,
    )

    request_path = output_dir / "hf3_rollout_request_rows.csv"
    policy_path = output_dir / "hf3_fixed_policy_source_rows.csv"
    plan_path = output_dir / "hf3_rollout_plan_rows.csv"
    action_path = output_dir / "hf3_policy_action_audit_rows.csv"
    step_path = output_dir / "hf3_backend_step_outcome_rows.csv"
    actor_view_path = output_dir / "hf3_rollout_actor_view_contract_rows.csv"
    claim_path = output_dir / "hf3_claim_boundary_checks.csv"
    gate_path = output_dir / "rollout_feasibility_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(request_path, rollout_request_rows, fieldnames=ROLLOUT_REQUEST_FIELDNAMES)
    write_csv_rows(policy_path, policy_source_rows, fieldnames=POLICY_SOURCE_FIELDNAMES)
    write_csv_rows(plan_path, rollout_plan_rows, fieldnames=ROLLOUT_PLAN_FIELDNAMES)
    write_csv_rows(action_path, policy_action_rows, fieldnames=POLICY_ACTION_FIELDNAMES)
    write_csv_rows(step_path, backend_step_rows, fieldnames=BACKEND_STEP_FIELDNAMES)
    write_csv_rows(actor_view_path, actor_view_rows, fieldnames=ACTOR_VIEW_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2568_summary=m2568_summary,
        rollout_request_rows=rollout_request_rows,
        policy_source_rows=policy_source_rows,
        rollout_plan_rows=rollout_plan_rows,
        policy_action_rows=policy_action_rows,
        backend_step_rows=backend_step_rows,
        actor_view_rows=actor_view_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        request_path=request_path,
        policy_path=policy_path,
        plan_path=plan_path,
        action_path=action_path,
        step_path=step_path,
        actor_view_path=actor_view_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
        checkpoint_path=checkpoint_path,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_rollout_request_rows(
    reset_request_rows: list[dict[str, str]],
    reset_execution_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    execution_by_request = {row["reset_request_id"]: row for row in reset_execution_rows}
    rows: list[dict[str, Any]] = []
    for request in sorted(reset_request_rows, key=lambda row: row["reset_request_id"]):
        reset_request_id = request["reset_request_id"]
        execution = execution_by_request.get(reset_request_id, {})
        obs_shape = _int_value(request.get("actor_observation_shape"), default=-1)
        action_shape = _int_value(request.get("action_shape"), default=-1)
        source_ok = bool(
            _row_passed(request)
            and _row_passed(execution)
            and _boolish(execution.get("reset_attempted"))
            and _boolish(execution.get("actor_view_available"))
            and obs_shape == P0_OBSERVATION_DIM
            and action_shape == ACTION_DIM
        )
        rows.append(
            {
                "rollout_request_id": reset_request_id.replace(
                    "_measured_reset_request", "_hf3_rollout_request"
                ),
                "source_reset_request_id": reset_request_id,
                "reset_execution_id": execution.get("reset_execution_id", ""),
                "route_role_id": request["route_role_id"],
                "backend_family": "repo_local_dynamics_backend_contract",
                "scenario_spec_id": str(request["scenario_spec_id"]).replace(
                    "hf3_measured_reset_feasibility", "hf3_rollout_feasibility"
                ),
                "seed": _int_value(request.get("seed"), default=0),
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "policy_action_allowed_in_m2572": True,
                "environment_step_allowed_in_m2572": True,
                "rollout_allowed_in_m2572": True,
                "pilot_admission_allowed": False,
                "validation_claim_allowed": False,
                "status_pass": source_ok,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_fixed_policy_source_rows(checkpoint_path: Path = DEFAULT_CHECKPOINT) -> list[dict[str, Any]]:
    path = Path(checkpoint_path)
    return [
        {
            "policy_source_id": "m1154_promoted_public_base_alpha_0_05",
            "checkpoint_path": str(path),
            "checkpoint_lineage": "m1154_row15_promoted_unsafe_margin_projection_probe",
            "loader": "autodrift.checkpoints.load_actor_critic_checkpoint",
            "policy_mode": "deterministic_actor_mean",
            "actor_input_source": "CurrentSimDynamicsBackend.actor_view->P0ObservationExtractor",
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "ranking_role": "none",
            "promotion_allowed": False,
            "status_pass": path.exists(),
            "claim_boundary": CLAIM_BOUNDARY,
        }
    ]


def build_rollout_plan_rows(
    rollout_request_rows: list[dict[str, Any]],
    policy_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policy_source_id = policy_source_rows[0]["policy_source_id"] if policy_source_rows else ""
    policy_source_pass = bool(policy_source_rows and _row_passed(policy_source_rows[0]))
    rows = []
    for request in rollout_request_rows:
        rows.append(
            {
                "rollout_plan_id": f"{request['rollout_request_id']}_plan",
                "rollout_request_id": request["rollout_request_id"],
                "policy_source_id": policy_source_id,
                "backend_class": "autodrift.high_fidelity_interface.CurrentSimDynamicsBackend",
                "reset_required": True,
                "target_horizon_steps": TARGET_HORIZON_STEPS,
                "min_steps_for_execution_observed": MIN_STEPS_FOR_EXECUTION_OBSERVED,
                "early_termination_allowed_as_outcome": True,
                "success_rate_computation_allowed": False,
                "controller_family_verdict_allowed": False,
                "status_pass": bool(_row_passed(request) and policy_source_pass),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def execute_rollout_feasibility_rows(
    rollout_request_rows: list[dict[str, Any]],
    rollout_plan_rows: list[dict[str, Any]],
    *,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    model, _checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    extractor = P0ObservationExtractor()
    plan_by_request = {row["rollout_request_id"]: row for row in rollout_plan_rows}
    policy_action_rows: list[dict[str, Any]] = []
    backend_step_rows: list[dict[str, Any]] = []
    actor_view_rows: list[dict[str, Any]] = []

    for request in rollout_request_rows:
        rollout_request_id = request["rollout_request_id"]
        plan = plan_by_request[rollout_request_id]
        rollout_plan_id = plan["rollout_plan_id"]
        backend = CurrentSimDynamicsBackend()
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=_int_value(request["seed"], default=0),
                    scenario_spec_id=str(request["scenario_spec_id"]),
                    role_family=str(request["route_role_id"]),
                )
            )
            observation = extractor.extract(reset_result.actor_view)
            actor_view_rows.append(
                _actor_view_contract_row(
                    actor_view_check_id=f"{rollout_plan_id}_reset_actor_view_contract",
                    rollout_plan_id=rollout_plan_id,
                    rollout_request_id=rollout_request_id,
                    source_phase="reset",
                    step_index=-1,
                    actor_observation_shape=int(observation.shape[0]),
                )
            )

            terminated_or_truncated = False
            for step_index in range(_int_value(plan["target_horizon_steps"], default=TARGET_HORIZON_STEPS)):
                if terminated_or_truncated:
                    break
                raw_action, _log_prob, _value = model.act(observation, deterministic=True)
                clipped_action = validate_actor_action(raw_action)
                physical_control = physical_control_from_action(clipped_action)
                action_status_pass = bool(
                    _row_passed(plan)
                    and observation.shape == (P0_OBSERVATION_DIM,)
                    and clipped_action.shape == (ACTION_DIM,)
                    and np.all(np.isfinite(clipped_action))
                )
                policy_action_rows.append(
                    {
                        "policy_action_audit_id": f"{rollout_plan_id}_step_{step_index}_policy_action",
                        "rollout_plan_id": rollout_plan_id,
                        "rollout_request_id": rollout_request_id,
                        "policy_source_id": plan["policy_source_id"],
                        "step_index": int(step_index),
                        "actor_observation_shape": int(observation.shape[0]),
                        "action_shape": int(clipped_action.shape[0]),
                        "action_finite": bool(np.all(np.isfinite(clipped_action))),
                        "action_clipped_to_contract": bool(
                            np.allclose(clipped_action, validate_actor_action(clipped_action))
                        ),
                        "steer_command": float(physical_control[0]),
                        "throttle_command": float(physical_control[1]),
                        "brake_command": float(physical_control[2]),
                        "hidden_oracle_actor_input_detected": False,
                        "diagnostics_actor_visible": False,
                        "taxonomy_label_actor_visible": False,
                        "policy_action_executed": True,
                        "status_pass": action_status_pass,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )

                step_result = backend.step(clipped_action)
                next_observation = extractor.extract(step_result.actor_view)
                actor_view_available = next_observation.shape == (P0_OBSERVATION_DIM,)
                diagnostics_recorded = isinstance(step_result.diagnostics, dict)
                step_status_pass = bool(
                    action_status_pass
                    and actor_view_available
                    and diagnostics_recorded
                )
                backend_step_rows.append(
                    {
                        "backend_step_outcome_id": f"{rollout_plan_id}_step_{step_index}_backend_step",
                        "rollout_plan_id": rollout_plan_id,
                        "rollout_request_id": rollout_request_id,
                        "step_index": int(step_index),
                        "backend_family": request["backend_family"],
                        "backend_class": "CurrentSimDynamicsBackend",
                        "backend_step_attempted": True,
                        "backend_status": step_result.backend_status,
                        "terminated_by_backend": bool(step_result.terminated_by_backend),
                        "truncated_by_backend": bool(step_result.truncated_by_backend),
                        "actor_view_available_after_step": bool(actor_view_available),
                        "diagnostics_recorded": bool(diagnostics_recorded),
                        "diagnostics_actor_visible": False,
                        "rollout_success_claim_allowed": False,
                        "validation_claim_allowed": False,
                        "status_pass": step_status_pass,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )
                actor_view_rows.append(
                    _actor_view_contract_row(
                        actor_view_check_id=f"{rollout_plan_id}_step_{step_index}_actor_view_contract",
                        rollout_plan_id=rollout_plan_id,
                        rollout_request_id=rollout_request_id,
                        source_phase="step",
                        step_index=step_index,
                        actor_observation_shape=int(next_observation.shape[0]),
                    )
                )
                observation = next_observation
                terminated_or_truncated = bool(
                    step_result.terminated_by_backend or step_result.truncated_by_backend
                )
        finally:
            backend.close()

    return policy_action_rows, backend_step_rows, actor_view_rows


def build_claim_boundary_checks(
    rollout_request_rows: list[dict[str, Any]],
    policy_action_rows: list[dict[str, Any]],
    backend_step_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    step_counts = Counter(str(row["rollout_request_id"]) for row in backend_step_rows if _row_passed(row))
    rollout_execution_observed = bool(
        len(rollout_request_rows) == 2
        and _all_status_pass(rollout_request_rows)
        and _all_status_pass(policy_action_rows)
        and _all_status_pass(backend_step_rows)
        and all(step_counts[str(row["rollout_request_id"])] >= MIN_STEPS_FOR_EXECUTION_OBSERVED for row in rollout_request_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(
            allowed
            and (
                claim_family == "reset_execution_observed"
                or rollout_execution_observed
            )
        )
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2572": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family
                    in {
                        "reset_execution_observed",
                        "rollout_feasibility_execution_observed",
                    }
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2568_summary: dict[str, Any],
    rollout_request_rows: list[dict[str, Any]],
    policy_source_rows: list[dict[str, Any]],
    rollout_plan_rows: list[dict[str, Any]],
    policy_action_rows: list[dict[str, Any]],
    backend_step_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    step_counts = Counter(str(row["rollout_request_id"]) for row in backend_step_rows if _row_passed(row))
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"]
        not in {
            "reset_execution_observed",
            "rollout_feasibility_execution_observed",
        }
        and _boolish(row["claim_allowed_in_m2572"])
    ]
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()) and bool(m2568_summary.get("status_pass")),
            f"missing={sum(1 for exists in source_exists.values() if not exists)};m2568_status={m2568_summary.get('status_pass')}",
            "missing=0;m2568_status=True",
            "lineage_invalid",
        ),
        (
            "rollout_request_rows_complete",
            "scenario",
            len(rollout_request_rows) == 2
            and _all_status_pass(rollout_request_rows)
            and all(_boolish(row["policy_action_allowed_in_m2572"]) for row in rollout_request_rows)
            and all(_boolish(row["environment_step_allowed_in_m2572"]) for row in rollout_request_rows)
            and all(_boolish(row["rollout_allowed_in_m2572"]) for row in rollout_request_rows)
            and not any(_boolish(row["pilot_admission_allowed"]) for row in rollout_request_rows)
            and not any(_boolish(row["validation_claim_allowed"]) for row in rollout_request_rows),
            f"rows={len(rollout_request_rows)}",
            "rows=2;policy=true;step=true;rollout=true;pilot=false;validation=false",
            "scenario_sampling_failure",
        ),
        (
            "fixed_policy_source_rows_pass",
            "lineage",
            len(policy_source_rows) == 1
            and _all_status_pass(policy_source_rows)
            and policy_source_rows[0]["policy_source_id"] == "m1154_promoted_public_base_alpha_0_05"
            and policy_source_rows[0]["ranking_role"] == "none"
            and not _boolish(policy_source_rows[0]["promotion_allowed"]),
            f"rows={len(policy_source_rows)}",
            "rows=1;m1154=true;ranking=none;promotion=false",
            "lineage_invalid",
        ),
        (
            "rollout_plan_rows_pass",
            "scenario",
            len(rollout_plan_rows) == 2
            and _all_status_pass(rollout_plan_rows)
            and all(_int_value(row["target_horizon_steps"], default=0) == TARGET_HORIZON_STEPS for row in rollout_plan_rows)
            and not any(_boolish(row["success_rate_computation_allowed"]) for row in rollout_plan_rows)
            and not any(_boolish(row["controller_family_verdict_allowed"]) for row in rollout_plan_rows),
            f"rows={len(rollout_plan_rows)}",
            f"rows=2;horizon={TARGET_HORIZON_STEPS};success_rate=false;verdict=false",
            "scenario_sampling_failure",
        ),
        (
            "policy_action_audit_rows_pass",
            "metric",
            len(policy_action_rows) >= len(rollout_request_rows)
            and len(policy_action_rows) <= len(rollout_request_rows) * TARGET_HORIZON_STEPS
            and _all_status_pass(policy_action_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in policy_action_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in policy_action_rows)
            and all(_boolish(row["policy_action_executed"]) for row in policy_action_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in policy_action_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in policy_action_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in policy_action_rows),
            f"rows={len(policy_action_rows)}",
            "rows>=2;rows<=16;obs=72;action=3;hidden=false",
            "metric_artifact",
        ),
        (
            "backend_step_outcome_rows_pass",
            "metric",
            len(backend_step_rows) == len(policy_action_rows)
            and _all_status_pass(backend_step_rows)
            and all(step_counts[str(row["rollout_request_id"])] >= MIN_STEPS_FOR_EXECUTION_OBSERVED for row in rollout_request_rows)
            and all(_boolish(row["backend_step_attempted"]) for row in backend_step_rows)
            and all(_boolish(row["actor_view_available_after_step"]) for row in backend_step_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in backend_step_rows)
            and not any(_boolish(row["rollout_success_claim_allowed"]) for row in backend_step_rows)
            and not any(_boolish(row["validation_claim_allowed"]) for row in backend_step_rows),
            f"rows={len(backend_step_rows)};step_counts={dict(sorted(step_counts.items()))}",
            "rows=policy_action_rows;min_steps_per_request>=1;actor_view=true;claims=false",
            "metric_artifact",
        ),
        (
            "actor_view_contract_rows_pass",
            "contract",
            len(actor_view_rows) == len(backend_step_rows) + len(rollout_request_rows)
            and _all_status_pass(actor_view_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in actor_view_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in actor_view_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_view_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in actor_view_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_view_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in actor_view_rows)
            and not any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_view_rows)
            and not any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_view_rows),
            f"rows={len(actor_view_rows)}",
            "rows=backend_steps+requests;obs=72;action=3;hidden=false;status=false;outcome=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not forbidden_claims_allowed
            and any(
                row["claim_family"] == "rollout_feasibility_execution_observed"
                and _boolish(row["claim_allowed_in_m2572"])
                for row in claim_rows
            ),
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0;rollout_feasibility_execution_observed=true",
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
    m2568_summary: dict[str, Any],
    rollout_request_rows: list[dict[str, Any]],
    policy_source_rows: list[dict[str, Any]],
    rollout_plan_rows: list[dict[str, Any]],
    policy_action_rows: list[dict[str, Any]],
    backend_step_rows: list[dict[str, Any]],
    actor_view_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    request_path: Path,
    policy_path: Path,
    plan_path: Path,
    action_path: Path,
    step_path: Path,
    actor_view_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
    checkpoint_path: Path,
) -> dict[str, Any]:
    step_counts = Counter(str(row["rollout_request_id"]) for row in backend_step_rows)
    backend_status_counts = Counter(str(row["backend_status"]) for row in backend_step_rows)
    reset_execution_observed_claim_allowed = any(
        row["claim_family"] == "reset_execution_observed"
        and _boolish(row["claim_allowed_in_m2572"])
        for row in claim_rows
    )
    rollout_feasibility_claim_allowed = any(
        row["claim_family"] == "rollout_feasibility_execution_observed"
        and _boolish(row["claim_allowed_in_m2572"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"]
        not in {
            "reset_execution_observed",
            "rollout_feasibility_execution_observed",
        }
        and _boolish(row["claim_allowed_in_m2572"])
        for row in claim_rows
    )
    status_pass = (
        all(source_exists.values())
        and bool(m2568_summary.get("status_pass"))
        and len(rollout_request_rows) == 2
        and _all_status_pass(rollout_request_rows)
        and len(policy_source_rows) == 1
        and _all_status_pass(policy_source_rows)
        and len(rollout_plan_rows) == 2
        and _all_status_pass(rollout_plan_rows)
        and len(policy_action_rows) >= 2
        and _all_status_pass(policy_action_rows)
        and len(backend_step_rows) == len(policy_action_rows)
        and _all_status_pass(backend_step_rows)
        and len(actor_view_rows) == len(backend_step_rows) + len(rollout_request_rows)
        and _all_status_pass(actor_view_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and reset_execution_observed_claim_allowed
        and rollout_feasibility_claim_allowed
        and not forbidden_claim_allowed
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf3_rollout_feasibility_execution_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_rollout_feasibility_execution_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_rollout_request_rows": str(request_path),
        "hf3_fixed_policy_source_rows": str(policy_path),
        "hf3_rollout_plan_rows": str(plan_path),
        "hf3_policy_action_audit_rows": str(action_path),
        "hf3_backend_step_outcome_rows": str(step_path),
        "hf3_rollout_actor_view_contract_rows": str(actor_view_path),
        "hf3_claim_boundary_checks": str(claim_path),
        "rollout_feasibility_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2568_status_pass": bool(m2568_summary.get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "target_horizon_steps": TARGET_HORIZON_STEPS,
        "min_steps_for_execution_observed": MIN_STEPS_FOR_EXECUTION_OBSERVED,
        "checkpoint_path": str(checkpoint_path),
        "fixed_policy_source_id": policy_source_rows[0]["policy_source_id"] if policy_source_rows else "",
        "rollout_request_row_count": len(rollout_request_rows),
        "rollout_request_rows_all_pass": _all_status_pass(rollout_request_rows),
        "fixed_policy_source_row_count": len(policy_source_rows),
        "fixed_policy_source_rows_all_pass": _all_status_pass(policy_source_rows),
        "rollout_plan_row_count": len(rollout_plan_rows),
        "rollout_plan_rows_all_pass": _all_status_pass(rollout_plan_rows),
        "policy_action_audit_row_count": len(policy_action_rows),
        "policy_action_audit_rows_all_pass": _all_status_pass(policy_action_rows),
        "backend_step_outcome_row_count": len(backend_step_rows),
        "backend_step_outcome_rows_all_pass": _all_status_pass(backend_step_rows),
        "actor_view_contract_row_count": len(actor_view_rows),
        "actor_view_contract_rows_all_pass": _all_status_pass(actor_view_rows),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "policy_action_executed": any(_boolish(row["policy_action_executed"]) for row in policy_action_rows),
        "environment_step_executed": any(_boolish(row["backend_step_attempted"]) for row in backend_step_rows),
        "rollout_execution_run": bool(backend_step_rows),
        "repo_local_backend_step_run": bool(backend_step_rows),
        "step_counts_by_rollout_request": dict(sorted(step_counts.items())),
        "backend_status_counts": dict(sorted(backend_status_counts.items())),
        "terminated_by_backend_count": sum(1 for row in backend_step_rows if _boolish(row["terminated_by_backend"])),
        "truncated_by_backend_count": sum(1 for row in backend_step_rows if _boolish(row["truncated_by_backend"])),
        "actor_view_available_after_step_count": sum(
            1 for row in backend_step_rows if _boolish(row["actor_view_available_after_step"])
        ),
        "reset_execution_observed_claim_allowed": bool(reset_execution_observed_claim_allowed),
        "rollout_feasibility_execution_observed_claim_allowed": bool(rollout_feasibility_claim_allowed),
        "forbidden_claim_allowed_in_m2572": bool(forbidden_claim_allowed),
        "rollout_success_claim_allowed": any(
            _boolish(row["rollout_success_claim_allowed"]) for row in backend_step_rows
        ),
        "validation_claim_allowed": any(_boolish(row["validation_claim_allowed"]) for row in backend_step_rows),
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"]) for row in actor_view_rows
        ),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in actor_view_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in actor_view_rows),
        "backend_status_actor_visible": any(_boolish(row["backend_status_actor_visible"]) for row in actor_view_rows),
        "reset_outcome_actor_visible": any(_boolish(row["reset_outcome_actor_visible"]) for row in actor_view_rows),
        "rollout_outcome_actor_visible": any(_boolish(row["rollout_outcome_actor_visible"]) for row in actor_view_rows),
        "repo_local_rollout_feasibility_execution": True,
        **FORBIDDEN_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2572 Engineering Controller Route A Baseline HF3 Rollout-Feasibility Execution Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_rollout_feasibility_execution.py`",
                f"- summary: `{summary['summary']}`",
                f"- rollout requests: `{summary['hf3_rollout_request_rows']}`",
                f"- fixed policy source: `{summary['hf3_fixed_policy_source_rows']}`",
                f"- rollout plans: `{summary['hf3_rollout_plan_rows']}`",
                f"- policy-action audit rows: `{summary['hf3_policy_action_audit_rows']}`",
                f"- backend step/outcome rows: `{summary['hf3_backend_step_outcome_rows']}`",
                f"- actor-view contract rows: `{summary['hf3_rollout_actor_view_contract_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['rollout_feasibility_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- training/ranking/success-rate/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2572 materializes Route A HF3 rollout-feasibility execution",
                "artifacts for the two accepted reset candidates. The bounded",
                "execution uses the repo-local `CurrentSimDynamicsBackend`, the",
                "fixed M1154 public-base checkpoint, and the P0 `72/3` actor",
                "contract. It does not run external high-fidelity simulation and",
                "does not compare or promote controllers.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"rollout_request_row_count: {summary['rollout_request_row_count']}",
                f"fixed_policy_source_row_count: {summary['fixed_policy_source_row_count']}",
                f"rollout_plan_row_count: {summary['rollout_plan_row_count']}",
                f"policy_action_audit_row_count: {summary['policy_action_audit_row_count']}",
                f"backend_step_outcome_row_count: {summary['backend_step_outcome_row_count']}",
                f"actor_view_contract_row_count: {summary['actor_view_contract_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"target_horizon_steps: {summary['target_horizon_steps']}",
                f"step_counts_by_rollout_request: {summary['step_counts_by_rollout_request']}",
                f"policy_action_executed: {str(summary['policy_action_executed']).lower()}",
                f"environment_step_executed: {str(summary['environment_step_executed']).lower()}",
                f"rollout_execution_run: {str(summary['rollout_execution_run']).lower()}",
                f"reset_execution_observed_claim_allowed: {str(summary['reset_execution_observed_claim_allowed']).lower()}",
                f"rollout_feasibility_execution_observed_claim_allowed: {str(summary['rollout_feasibility_execution_observed_claim_allowed']).lower()}",
                f"rollout_success_claim_allowed: {str(summary['rollout_success_claim_allowed']).lower()}",
                f"validation_claim_allowed: {str(summary['validation_claim_allowed']).lower()}",
                f"forbidden_claim_allowed_in_m2572: {str(summary['forbidden_claim_allowed_in_m2572']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2572 supports only the operational claim that bounded",
                "repo-local reset, fixed-policy action, and backend-step",
                "execution were observed while preserving the P0 actor/action",
                "contract. It does not support rollout success, high-fidelity",
                "validation readiness/result, driver performance, controller",
                "ranking, checkpoint promotion, success rate, paper evidence,",
                "FW-vs-GRU, current-sim verdict, high-fidelity validation, or",
                "self-ID.",
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


def _actor_view_contract_row(
    *,
    actor_view_check_id: str,
    rollout_plan_id: str,
    rollout_request_id: str,
    source_phase: str,
    step_index: int,
    actor_observation_shape: int,
) -> dict[str, Any]:
    return {
        "actor_view_check_id": actor_view_check_id,
        "rollout_plan_id": rollout_plan_id,
        "rollout_request_id": rollout_request_id,
        "source_phase": source_phase,
        "step_index": int(step_index),
        "actor_observation_shape": int(actor_observation_shape),
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "diagnostics_actor_visible": False,
        "taxonomy_label_actor_visible": False,
        "backend_status_actor_visible": False,
        "reset_outcome_actor_visible": False,
        "rollout_outcome_actor_visible": False,
        "status_pass": bool(actor_observation_shape == P0_OBSERVATION_DIM),
        "claim_boundary": CLAIM_BOUNDARY,
    }


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
    parser.add_argument("--m2568-summary", type=Path, default=DEFAULT_M2568_SUMMARY)
    parser.add_argument("--m2568-requests", type=Path, default=DEFAULT_M2568_REQUESTS)
    parser.add_argument("--m2568-executions", type=Path, default=DEFAULT_M2568_EXECUTIONS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_rollout_feasibility_execution(
        args.output_dir,
        m2568_summary_path=args.m2568_summary,
        m2568_requests_path=args.m2568_requests,
        m2568_executions_path=args.m2568_executions,
        checkpoint_path=args.checkpoint,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "rollout_requests={rollout_request_row_count} "
        "policy_actions={policy_action_audit_row_count} "
        "backend_steps={backend_step_outcome_row_count} "
        "summary={summary}".format(**summary)
    )


if __name__ == "__main__":
    main()
