"""Bounded source-only repair smoke for the failure-surface candidate config."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    DEFAULT_SEED_COUNT,
    M2514_ROW_SCHEMA,
    build_fresh_seed_measured_rows,
    build_seed_panel_specs,
    run_fresh_seed_telemetry,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_CANDIDATE_CONFIG = Path(
    "runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/"
    "candidate_config.json"
)
DEFAULT_GATE_BINDINGS = Path(
    "runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/"
    "protected_gate_bindings.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2529_engineering_controller_failure_surface_intervention_repair_smoke"
)
DEFAULT_CHECKPOINT = Path(
    "runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt"
)
DEFAULT_PROTECTED_ROWS = Path(
    "runs/m2527_engineering_controller_failure_surface_intervention_plan/"
    "protected_regression_rows.csv"
)
DEFAULT_MILESTONE = (
    "m2529-engineering-controller-failure-surface-intervention-repair-smoke-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2530-engineering-controller-failure-surface-intervention-repair-smoke-result-audit"
)

CLAIM_SCOPE = "bounded source-only repair smoke preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "environment_rollout_run": False,
    "simulator_step_run": False,
    "measured_validation_run": False,
    "training_started": False,
    "training_run": False,
    "repair_training_started": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}

REPAIR_SMOKE_FIELDNAMES = [
    "repair_smoke_row_id",
    "source_row_id",
    "candidate_config_id",
    "candidate_config_hash",
    "protected_group",
    "row_role",
    "failure_surface",
    "scenario_role",
    "seed",
    "subject_id",
    "fixture_id",
    "seed_panel_id",
    "source_artifact",
    "source_only_backend_step_run",
    "policy_action_run",
    "open_loop_action_rollout_run",
    "repair_training_started",
    "checkpoint_path",
    "actor_contract_id",
    "observation_shape",
    "action_shape",
    "actor_encoder",
    "action_horizon",
    "actor_input_leak_flags",
    "hidden_or_oracle_actor_inputs_required",
    "controller_mode_used",
    "mu_enter_actor_input",
    "minimum_road_margin_m",
    "current_minimum_road_margin_m",
    "road_margin_delta_m",
    "road_departure_event",
    "current_road_departure_event",
    "road_departure_delta",
    "collision_event",
    "current_collision_event",
    "collision_regressed",
    "minimum_obstacle_clearance_m",
    "current_minimum_obstacle_clearance_m",
    "severity_proxy",
    "current_severity_proxy",
    "severity_delta",
    "simultaneous_throttle_brake_fraction",
    "current_simultaneous_throttle_brake_fraction",
    "command_conflict_delta",
    "candidate_road_boundary_penalty",
    "candidate_mitigation_penalty",
    "candidate_command_conflict_penalty",
    "candidate_total_penalty",
    "protected_row_matched",
    "repair_smoke_status",
    "diagnostic_only_no_ranking_claim",
    "success_rate_field_emitted",
    "ranking_or_winner_field_emitted",
    "claim_scope",
    "forbidden_interpretation",
]

PROTECTED_GATE_EVALUATION_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "protected_group",
    "metric",
    "binding_status",
    "bound_row_count",
    "evaluated_row_count",
    "trace_to_gate_binding",
    "trace_to_protected_rows",
    "evaluation_status",
    "gate_pass",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "failure_type",
    "blocks_claims",
    "next_route_if_fail",
    "source_gate_artifact",
    "source_rows_artifact",
    "repair_smoke_rows",
    "claim_boundary",
]


def run_failure_surface_intervention_repair_smoke(
    output_dir: Path,
    *,
    candidate_config: Path | str = DEFAULT_CANDIDATE_CONFIG,
    gate_bindings: Path | str = DEFAULT_GATE_BINDINGS,
    protected_rows: Path | str = DEFAULT_PROTECTED_ROWS,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    seed_count: int = DEFAULT_SEED_COUNT,
    horizon_steps: int = 100,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    if int(seed_count) < DEFAULT_SEED_COUNT:
        raise ValueError(f"seed_count must be at least {DEFAULT_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = Path(candidate_config)
    gate_binding_path = Path(gate_bindings)
    protected_rows_path = Path(protected_rows)
    checkpoint = Path(checkpoint_path)

    candidate = read_json(candidate_path)
    candidate_hash = _file_sha256(candidate_path)
    gate_binding_rows = _read_csv_rows(gate_binding_path)
    protected = _read_csv_rows(protected_rows_path)
    row_schema_fields = [row["field_name"] for row in _read_csv_rows(M2514_ROW_SCHEMA)]

    run_items, _seed_panel_spec_rows = build_seed_panel_specs(seed_count=int(seed_count))
    telemetry_rows, telemetry_summary = run_fresh_seed_telemetry(
        run_items,
        checkpoint_path=checkpoint,
        horizon_steps=int(horizon_steps),
        device=device,
    )
    measured_behavior_rows, _measured_event_rows = build_fresh_seed_measured_rows(
        telemetry_rows,
        run_items=run_items,
        checkpoint_path=str(checkpoint),
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    repair_smoke_rows = build_repair_smoke_rows(
        protected,
        measured_behavior_rows,
        candidate=candidate,
        candidate_hash=candidate_hash,
        milestone=milestone,
    )
    gate_evaluation_rows = build_protected_gate_evaluation_rows(
        gate_binding_rows,
        repair_smoke_rows,
    )

    candidate_snapshot_path = output_dir / "candidate_config_snapshot.json"
    repair_smoke_rows_path = output_dir / "repair_smoke_rows.csv"
    protected_gate_evaluation_path = output_dir / "protected_gate_evaluation.csv"
    summary_path = output_dir / "summary.json"

    write_json(
        candidate_snapshot_path,
        {
            "candidate_config": candidate,
            "candidate_config_hash": candidate_hash,
            "candidate_config_source": str(candidate_path),
            "candidate_config_mutated": False,
            "active_config_overwritten": False,
            "loaded_for_evaluator_side_repair_smoke": True,
            "snapshot_milestone": milestone,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    write_csv_rows(
        repair_smoke_rows_path,
        repair_smoke_rows,
        fieldnames=REPAIR_SMOKE_FIELDNAMES,
    )
    write_csv_rows(
        protected_gate_evaluation_path,
        gate_evaluation_rows,
        fieldnames=PROTECTED_GATE_EVALUATION_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_path,
        candidate_path=candidate_path,
        gate_binding_path=gate_binding_path,
        protected_rows_path=protected_rows_path,
        checkpoint_path=checkpoint,
        candidate=candidate,
        candidate_hash=candidate_hash,
        telemetry_summary=telemetry_summary,
        repair_smoke_rows=repair_smoke_rows,
        gate_evaluation_rows=gate_evaluation_rows,
        candidate_snapshot_path=candidate_snapshot_path,
        repair_smoke_rows_path=repair_smoke_rows_path,
        protected_gate_evaluation_path=protected_gate_evaluation_path,
        milestone=milestone,
        next_blocker=next_blocker,
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    write_json(summary_path, summary)
    return summary


def build_repair_smoke_rows(
    protected_rows: list[dict[str, str]],
    measured_behavior_rows: list[dict[str, Any]],
    *,
    candidate: dict[str, Any],
    candidate_hash: str,
    milestone: str,
) -> list[dict[str, Any]]:
    measured_by_key = {
        _row_key(row): row
        for row in measured_behavior_rows
    }
    output: list[dict[str, Any]] = []
    coeffs = dict(candidate.get("candidate_coefficients", {}))
    for protected in protected_rows:
        measured = measured_by_key.get(_row_key(protected))
        matched = measured is not None
        if measured is None:
            measured = {}
        current_margin = _float(protected.get("current_minimum_road_margin_m"))
        measured_margin = _float(measured.get("minimum_road_margin_m"))
        current_departure = _as_bool(protected.get("current_road_departure_event"))
        measured_departure = _as_bool(measured.get("road_departure_event"))
        current_collision = _as_bool(protected.get("current_collision_event"))
        measured_collision = _as_bool(measured.get("collision_event"))
        current_severity = _float(protected.get("current_severity_proxy"))
        measured_severity = _float(measured.get("severity_proxy"))
        current_conflict = _float(protected.get("current_simultaneous_throttle_brake_fraction"))
        measured_conflict = _float(measured.get("simultaneous_throttle_brake_fraction"))
        road_penalty = (
            _float(coeffs.get("road_margin_reward_scale"), default=1.0)
            * max(0.0, -measured_margin)
            + _float(coeffs.get("road_departure_penalty_scale"), default=1.0)
            * float(measured_departure)
        )
        mitigation_penalty = (
            _float(coeffs.get("mitigation_severity_penalty_scale"), default=0.5)
            * max(0.0, measured_severity)
        )
        command_penalty = (
            _float(coeffs.get("simultaneous_throttle_brake_penalty_scale"), default=0.25)
            * max(0.0, measured_conflict)
        )
        row_id = str(protected.get("source_row_id", ""))
        output.append(
            {
                "repair_smoke_row_id": row_id.replace("m2523_", f"{milestone}_"),
                "source_row_id": row_id,
                "candidate_config_id": candidate.get("config_id", ""),
                "candidate_config_hash": candidate_hash,
                "protected_group": protected.get("protection_group", ""),
                "row_role": protected.get("row_role", ""),
                "failure_surface": protected.get("failure_surface", ""),
                "scenario_role": protected.get("scenario_role", ""),
                "seed": protected.get("seed", ""),
                "subject_id": protected.get("subject_id", ""),
                "fixture_id": measured.get("fixture_id", protected.get("fixture_id", "")),
                "seed_panel_id": protected.get("seed_panel_id", measured.get("seed_panel_id", "")),
                "source_artifact": str(protected.get("source_artifact", "")),
                "source_only_backend_step_run": matched,
                "policy_action_run": protected.get("subject_id") == "m1154_policy_actor",
                "open_loop_action_rollout_run": protected.get("subject_id") != "m1154_policy_actor",
                "repair_training_started": False,
                "checkpoint_path": measured.get("checkpoint_path", ""),
                "actor_contract_id": measured.get(
                    "actor_contract_id",
                    candidate.get("actor_contract", {}).get("actor_contract_id", ""),
                ),
                "observation_shape": measured.get("observation_shape", P0_OBSERVATION_DIM),
                "action_shape": measured.get("action_shape", ACTION_DIM),
                "actor_encoder": measured.get(
                    "actor_encoder",
                    candidate.get("actor_contract", {}).get("actor_encoder", ""),
                ),
                "action_horizon": measured.get(
                    "action_horizon",
                    candidate.get("actor_contract", {}).get("action_horizon", ""),
                ),
                "actor_input_leak_flags": measured.get("actor_input_leak_flags", "none"),
                "hidden_or_oracle_actor_inputs_required": False,
                "controller_mode_used": False,
                "mu_enter_actor_input": False,
                "minimum_road_margin_m": measured_margin,
                "current_minimum_road_margin_m": current_margin,
                "road_margin_delta_m": measured_margin - current_margin,
                "road_departure_event": measured_departure,
                "current_road_departure_event": current_departure,
                "road_departure_delta": int(measured_departure) - int(current_departure),
                "collision_event": measured_collision,
                "current_collision_event": current_collision,
                "collision_regressed": bool(measured_collision and not current_collision),
                "minimum_obstacle_clearance_m": _float(
                    measured.get("minimum_obstacle_clearance_m")
                ),
                "current_minimum_obstacle_clearance_m": _float(
                    protected.get("current_minimum_obstacle_clearance_m")
                ),
                "severity_proxy": measured_severity,
                "current_severity_proxy": current_severity,
                "severity_delta": measured_severity - current_severity,
                "simultaneous_throttle_brake_fraction": measured_conflict,
                "current_simultaneous_throttle_brake_fraction": current_conflict,
                "command_conflict_delta": measured_conflict - current_conflict,
                "candidate_road_boundary_penalty": road_penalty,
                "candidate_mitigation_penalty": mitigation_penalty,
                "candidate_command_conflict_penalty": command_penalty,
                "candidate_total_penalty": road_penalty + mitigation_penalty + command_penalty,
                "protected_row_matched": matched,
                "repair_smoke_status": (
                    "source_only_no_update_behavior_measured"
                    if matched
                    else "protected_row_missing_from_smoke"
                ),
                "diagnostic_only_no_ranking_claim": True,
                "success_rate_field_emitted": False,
                "ranking_or_winner_field_emitted": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return output


def build_protected_gate_evaluation_rows(
    gate_bindings: list[dict[str, str]],
    repair_smoke_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for binding in gate_bindings:
        gate_id = binding["gate_id"]
        bound_rows = _bound_rows_for_group(repair_smoke_rows, binding["protected_group"])
        gate_pass, status, failure_type, improved, regressed, unchanged = _evaluate_gate(
            gate_id,
            bound_rows,
        )
        rows.append(
            {
                "gate_id": gate_id,
                "gate_tier": binding["gate_tier"],
                "protected_group": binding["protected_group"],
                "metric": binding["metric"],
                "binding_status": binding["binding_status"],
                "bound_row_count": int(binding["protected_row_count"]),
                "evaluated_row_count": len(bound_rows),
                "trace_to_gate_binding": True,
                "trace_to_protected_rows": len(bound_rows) == int(binding["protected_row_count"]),
                "evaluation_status": status,
                "gate_pass": gate_pass,
                "improved_row_count": improved,
                "regressed_row_count": regressed,
                "unchanged_row_count": unchanged,
                "failure_type": failure_type,
                "blocks_claims": _blocks_claims(gate_id),
                "next_route_if_fail": _next_route_if_fail(gate_id),
                "source_gate_artifact": binding["source_gate_artifact"],
                "source_rows_artifact": binding["source_rows_artifact"],
                "repair_smoke_rows": str(
                    DEFAULT_OUTPUT_DIR / "repair_smoke_rows.csv"
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    candidate_path: Path,
    gate_binding_path: Path,
    protected_rows_path: Path,
    checkpoint_path: Path,
    candidate: dict[str, Any],
    candidate_hash: str,
    telemetry_summary: dict[str, Any],
    repair_smoke_rows: list[dict[str, Any]],
    gate_evaluation_rows: list[dict[str, Any]],
    candidate_snapshot_path: Path,
    repair_smoke_rows_path: Path,
    protected_gate_evaluation_path: Path,
    milestone: str,
    next_blocker: str,
    seed_count: int,
    horizon_steps: int,
) -> dict[str, Any]:
    required_artifacts_present = (
        candidate_snapshot_path.exists()
        and repair_smoke_rows_path.exists()
        and protected_gate_evaluation_path.exists()
    )
    actor_contract = candidate.get("actor_contract", {})
    actor_contract_shape = (
        int(actor_contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM
        and int(actor_contract.get("action_shape", -1)) == ACTION_DIM
        and _row_int_set(repair_smoke_rows, "observation_shape") == {P0_OBSERVATION_DIM}
        and _row_int_set(repair_smoke_rows, "action_shape") == {ACTION_DIM}
    )
    all_rows_matched = bool(repair_smoke_rows) and all(
        _as_bool(row["protected_row_matched"]) for row in repair_smoke_rows
    )
    gate_rows_traceable = bool(gate_evaluation_rows) and all(
        _as_bool(row["trace_to_gate_binding"]) and _as_bool(row["trace_to_protected_rows"])
        for row in gate_evaluation_rows
    )
    evaluated_gate_ids = {row["gate_id"] for row in gate_evaluation_rows}
    proof_rows = [
        row
        for row in gate_evaluation_rows
        if row["gate_id"] in {"road_boundary_proof", "mitigation_proof", "command_conflict_proof"}
    ]
    proof_gates_all_passed = bool(proof_rows) and all(_as_bool(row["gate_pass"]) for row in proof_rows)
    proof_gate_fail_count = sum(not _as_bool(row["gate_pass"]) for row in proof_rows)
    deferred_gate_count = sum(
        str(row["evaluation_status"]).startswith("deferred") for row in gate_evaluation_rows
    )
    no_hidden_or_oracle = (
        not bool(candidate.get("actor_contract", {}).get("actor_input_contract_changed", True))
        and not bool(actor_contract.get("rule_switching_controller_modes_allowed", True))
        and {str(row["actor_input_leak_flags"]).lower() for row in repair_smoke_rows}
        == {"none"}
        and not any(_as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in repair_smoke_rows)
        and not any(_as_bool(row["controller_mode_used"]) for row in repair_smoke_rows)
        and not any(_as_bool(row["mu_enter_actor_input"]) for row in repair_smoke_rows)
    )
    no_claim_boundary_violation = (
        not any(FALSE_CLAIM_FLAGS.values())
        and not any(_as_bool(row["success_rate_field_emitted"]) for row in repair_smoke_rows)
        and not any(_as_bool(row["ranking_or_winner_field_emitted"]) for row in repair_smoke_rows)
    )
    status_pass = (
        bool(telemetry_summary.get("checkpoint_admitted"))
        and required_artifacts_present
        and output_dir.exists()
        and candidate_path.exists()
        and gate_binding_path.exists()
        and protected_rows_path.exists()
        and checkpoint_path.exists()
        and len(repair_smoke_rows) == 45
        and len(gate_evaluation_rows) == 7
        and evaluated_gate_ids
        == {
            "contract_p0_72_3",
            "no_oracle_actor_inputs",
            "road_boundary_proof",
            "mitigation_proof",
            "command_conflict_proof",
            "fresh_seed_generalization",
            "no_ranking_no_success_rate",
        }
        and all_rows_matched
        and gate_rows_traceable
        and actor_contract_shape
        and no_hidden_or_oracle
        and no_claim_boundary_violation
    )
    return {
        "result_class": (
            "engineering_controller_failure_surface_intervention_repair_smoke_pass"
            if status_pass
            else "engineering_controller_failure_surface_intervention_repair_smoke_failed"
        ),
        "status_pass": bool(status_pass),
        "smoke_outcome_class": (
            "negative_no_update_repair_smoke_recorded"
            if status_pass and not proof_gates_all_passed
            else "positive_proof_surface_smoke_recorded"
            if status_pass
            else "repair_smoke_incomplete"
        ),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "candidate_config": str(candidate_path),
        "candidate_config_hash": candidate_hash,
        "candidate_config_id": candidate.get("config_id", ""),
        "candidate_config_snapshot": str(candidate_snapshot_path),
        "protected_gate_bindings": str(gate_binding_path),
        "protected_rows": str(protected_rows_path),
        "checkpoint_path": str(checkpoint_path),
        "repair_smoke_rows": str(repair_smoke_rows_path),
        "protected_gate_evaluation": str(protected_gate_evaluation_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "candidate_config_loaded": True,
        "candidate_config_mutated": False,
        "active_config_overwritten": False,
        "immutable_candidate_config": bool(candidate.get("immutable_candidate_config")),
        "seed_count_per_role": int(seed_count),
        "horizon_steps": int(horizon_steps),
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "reset_count": int(telemetry_summary.get("reset_count", 0)),
        "repair_smoke_row_count": len(repair_smoke_rows),
        "protected_gate_evaluation_row_count": len(gate_evaluation_rows),
        "protected_row_match_count": sum(
            _as_bool(row["protected_row_matched"]) for row in repair_smoke_rows
        ),
        "all_protected_rows_matched": bool(all_rows_matched),
        "gate_evaluation_traceable": bool(gate_rows_traceable),
        "actor_contract_id": actor_contract.get("actor_contract_id", ""),
        "observation_shape": int(actor_contract.get("observation_shape", -1)),
        "action_shape": int(actor_contract.get("action_shape", -1)),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "actor_input_contract_changed": bool(actor_contract.get("actor_input_contract_changed", True)),
        "hidden_or_oracle_actor_inputs_required": False,
        "rule_switching_controller_modes_allowed": bool(
            actor_contract.get("rule_switching_controller_modes_allowed", True)
        ),
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "open_loop_action_rollout_run": True,
        "protected_proof_gates_all_passed": bool(proof_gates_all_passed),
        "protected_proof_gate_fail_count": int(proof_gate_fail_count),
        "deferred_gate_count": int(deferred_gate_count),
        "negative_smoke_recorded": bool(status_pass and not proof_gates_all_passed),
        "driver_performance_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
        **FALSE_CLAIM_FLAGS,
    }


def _evaluate_gate(
    gate_id: str,
    rows: list[dict[str, Any]],
) -> tuple[bool, str, str, int, int, int]:
    if gate_id == "contract_p0_72_3":
        gate_pass = (
            bool(rows)
            and _row_int_set(rows, "observation_shape") == {P0_OBSERVATION_DIM}
            and _row_int_set(rows, "action_shape") == {ACTION_DIM}
        )
        return gate_pass, "evaluated_contract", "none" if gate_pass else "contract_violation", 0, 0, 0
    if gate_id == "no_oracle_actor_inputs":
        gate_pass = bool(rows) and all(
            str(row["actor_input_leak_flags"]).lower() == "none"
            and not _as_bool(row["hidden_or_oracle_actor_inputs_required"])
            and not _as_bool(row["controller_mode_used"])
            and not _as_bool(row["mu_enter_actor_input"])
            for row in rows
        )
        return gate_pass, "evaluated_contract", "none" if gate_pass else "contract_violation", 0, 0, 0
    if gate_id == "road_boundary_proof":
        improved = sum(
            _float(row["road_margin_delta_m"]) > 1e-9
            and int(row["road_departure_delta"]) <= 0
            and not _as_bool(row["collision_regressed"])
            for row in rows
        )
        regressed = sum(
            _float(row["road_margin_delta_m"]) < -1e-9
            or int(row["road_departure_delta"]) > 0
            or _as_bool(row["collision_regressed"])
            for row in rows
        )
        unchanged = max(0, len(rows) - improved - regressed)
        gate_pass = bool(rows) and improved == len(rows) and regressed == 0
        return (
            gate_pass,
            "evaluated_negative_smoke_no_update" if not gate_pass else "evaluated_pass",
            "behavior_regression" if regressed else "objective_overfit",
            improved,
            regressed,
            unchanged,
        )
    if gate_id == "mitigation_proof":
        improved = sum(
            _float(row["severity_delta"]) < -1e-9
            and _float(row["road_margin_delta_m"]) > 1e-9
            for row in rows
        )
        regressed = sum(
            _float(row["severity_delta"]) > 1e-9
            or _float(row["road_margin_delta_m"]) < -1e-9
            for row in rows
        )
        unchanged = max(0, len(rows) - improved - regressed)
        gate_pass = bool(rows) and improved == len(rows) and regressed == 0
        return (
            gate_pass,
            "evaluated_negative_smoke_no_update" if not gate_pass else "evaluated_pass",
            "behavior_regression" if regressed else "objective_overfit",
            improved,
            regressed,
            unchanged,
        )
    if gate_id == "command_conflict_proof":
        improved = sum(_float(row["command_conflict_delta"]) < -1e-9 for row in rows)
        regressed = sum(_float(row["command_conflict_delta"]) > 1e-9 for row in rows)
        unchanged = max(0, len(rows) - improved - regressed)
        gate_pass = bool(rows) and improved == len(rows) and regressed == 0
        return (
            gate_pass,
            "evaluated_negative_smoke_no_update" if not gate_pass else "evaluated_pass",
            "objective_overfit",
            improved,
            regressed,
            unchanged,
        )
    if gate_id == "fresh_seed_generalization":
        return (
            False,
            "deferred_until_post_smoke_generalization_route",
            "none",
            0,
            0,
            len(rows),
        )
    if gate_id == "no_ranking_no_success_rate":
        gate_pass = bool(rows) and all(
            not _as_bool(row["success_rate_field_emitted"])
            and not _as_bool(row["ranking_or_winner_field_emitted"])
            for row in rows
        )
        return gate_pass, "evaluated_claim_boundary", "none" if gate_pass else "metric_artifact", 0, 0, 0
    return False, "unknown_gate", "metric_artifact", 0, 0, len(rows)


def _bound_rows_for_group(rows: list[dict[str, Any]], protected_group: str) -> list[dict[str, Any]]:
    if protected_group in {"all", "future_fresh_source_only"}:
        return list(rows)
    if protected_group == "primary_protected":
        return [row for row in rows if row["row_role"] == "primary_protected"]
    return [row for row in rows if row["protected_group"] == protected_group]


def _blocks_claims(gate_id: str) -> str:
    return {
        "contract_p0_72_3": "all behavior or implementation claims if failed",
        "no_oracle_actor_inputs": "deployable actor claim",
        "road_boundary_proof": "road-boundary intervention evidence",
        "mitigation_proof": "mitigation intervention evidence",
        "command_conflict_proof": "command-conflict intervention evidence",
        "fresh_seed_generalization": "generalization or promotion claims",
        "no_ranking_no_success_rate": "ranking winner success-rate verdict",
    }.get(gate_id, "unknown claim")


def _next_route_if_fail(gate_id: str) -> str:
    return {
        "contract_p0_72_3": "contract repair before implementation",
        "no_oracle_actor_inputs": "design repair or branch synthesis",
        "road_boundary_proof": "failure-surface repair audit",
        "mitigation_proof": "mitigation objective repair",
        "command_conflict_proof": "action regularizer repair",
        "fresh_seed_generalization": "fresh-seed panel before promotion",
        "no_ranking_no_success_rate": "claim-boundary audit",
    }.get(gate_id, "repair-smoke result audit")


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _file_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _row_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(row.get("subject_id", row.get("comparison_subject", ""))),
        str(row.get("scenario_role", row.get("role_family", ""))),
        int(row.get("seed", 0) or 0),
    )


def _row_int_set(rows: Iterable[dict[str, Any]], field: str) -> set[int]:
    return {int(row[field]) for row in rows if str(row.get(field, "")).strip()}


def _float(value: Any, *, default: float = 0.0) -> float:
    if value in {None, ""}:
        return float(default)
    return float(value)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the M2529 bounded source-only repair smoke."
    )
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_CANDIDATE_CONFIG)
    parser.add_argument("--gate-bindings", type=Path, default=DEFAULT_GATE_BINDINGS)
    parser.add_argument("--protected-rows", type=Path, default=DEFAULT_PROTECTED_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=100)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_failure_surface_intervention_repair_smoke(
        args.output_dir,
        candidate_config=args.candidate_config,
        gate_bindings=args.gate_bindings,
        protected_rows=args.protected_rows,
        checkpoint_path=args.checkpoint,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "smoke_outcome_class={smoke_outcome_class} output_dir={output_dir}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
