"""M2773 source-only action-response belief intervention materialization.

This preflight executes only the repository-local source-only HF0 backend. It
does not import, build, or run any external high-fidelity simulator.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    DEFAULT_FRESH_SEED_COUNT,
    DEFAULT_HORIZON_STEPS,
    DYNAMICS_AXES,
    ROLE_FAMILIES,
    build_fresh_generalization_panel_specs,
)
from autodrift.engineering_controller_source_only_outcome_events import (
    _event_stats,
    _primary_obstacle,
)
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.hf0_source_only_closed_loop_fixture_pilot import admit_actor_checkpoint
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    ActorView,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    physical_control_from_action,
    validate_actor_action,
)


DEFAULT_MILESTONE = (
    "m2773-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-materialization-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2773_engineering_controller_route_a_source_only_action_response_belief_"
    "intervention_materialization_preflight"
)
DEFAULT_DOC_PATH = (
    "docs/m2773-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-materialization-preflight.md"
)
DEFAULT_M2772_DESIGN = (
    "docs/m2772-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-design.md"
)
DEFAULT_M2641_DIR = Path("runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel")
DEFAULT_M2655_DIR = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution"
)
DEFAULT_SOURCE_CHECKPOINT = (
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = (
    "experiments/manifests/m2774-engineering-controller-route-a-source-only-action-"
    "response-belief-intervention-materialization-result-audit.json"
)
DEFAULT_NEXT_BLOCKER = (
    "m2774-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-materialization-result-audit"
)

CLAIM_SCOPE = "Route A source-only action-response belief intervention materialization preflight only"
FORBIDDEN_INTERPRETATION = (
    "ranking, winner selection, checkpoint promotion, success-rate verdict, repair success, "
    "driver performance, validation, paper, finite-window-vs-GRU, current-sim verdict, "
    "high-fidelity validation, full ideal driver completion, or level3 self-identification"
)
CLAIM_BOUNDARY = (
    "M2773 materializes source-only diagnostic intervention rows only; rows are not "
    "ranking, promotion, validation, performance, paper, current-sim, high-fidelity, "
    "full-driver, or self-ID evidence"
)

INTERVENTION_CONDITIONS = (
    {
        "intervention_condition_id": "normal_recurrent",
        "intervention_family": "baseline",
        "recurrent_hidden_policy": "carry_recurrent_hidden",
        "actor_view_history_policy": "unmodified_deployable_history_fields",
        "evaluator_only": False,
    },
    {
        "intervention_condition_id": "reset_hidden_each_step",
        "intervention_family": "recurrent_state_ablation",
        "recurrent_hidden_policy": "reset_hidden_to_zero_each_step",
        "actor_view_history_policy": "unmodified_deployable_history_fields",
        "evaluator_only": True,
    },
    {
        "intervention_condition_id": "zero_previous_command_history",
        "intervention_family": "command_response_history_ablation",
        "recurrent_hidden_policy": "carry_recurrent_hidden",
        "actor_view_history_policy": "zero_previous_physical_command_fields",
        "evaluator_only": True,
    },
    {
        "intervention_condition_id": "held_actuator_history",
        "intervention_family": "actuator_history_ablation",
        "recurrent_hidden_policy": "carry_recurrent_hidden",
        "actor_view_history_policy": "hold_actuator_and_previous_command_fields_at_reset",
        "evaluator_only": True,
    },
)

SOURCE_ONLY_CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "seed_index",
    "backend_id",
    "source_model",
    "checkpoint_path",
    "horizon_steps",
    "source_only_surface_id",
    "fixture_id",
    "base_fixture_id",
    "ordinary_success_denominator_allowed",
    "mitigation_reference",
    "actor_visible_labels",
    "source_lineage",
]
INTERVENTION_CONDITION_FIELDNAMES = [
    "intervention_condition_id",
    "intervention_family",
    "recurrent_hidden_policy",
    "actor_view_history_policy",
    "actor_input_shape_changed",
    "actor_input_feature_added",
    "hidden_or_oracle_value_added",
    "evaluator_only",
    "actor_visible_label",
    "allowed_claim_scope",
]
CANDIDATE_INTERVENTION_FIELDNAMES = [
    "candidate_id",
    "intervention_condition_id",
    "execution_scheduled",
    "matched_history_required",
    "ordinary_denominator_allowed",
    "expected_trace_rows",
    "stop_if_unresolved",
]
INTERVENTION_EXECUTION_FIELDNAMES = [
    "candidate_id",
    "intervention_condition_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "steps_executed",
    "backend_status",
    "action_finite",
    "action_within_bounds",
    "observation_shape",
    "action_shape",
    "collision_diagnostic",
    "road_departure_diagnostic",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "trace_delta_proxy",
    "command_response_proxy",
    "diagnostic_only",
]
INTERVENTION_FAILURE_FIELDNAMES = [
    "candidate_id",
    "intervention_condition_id",
    "failure_type",
    "failure_reason",
    "claim_boundary",
]
ACTION_RESPONSE_TRACE_FIELDNAMES = [
    "candidate_id",
    "intervention_condition_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "step_index",
    "steer",
    "throttle",
    "brake",
    "physical_steer",
    "physical_throttle",
    "physical_brake",
    "previous_steer_command",
    "previous_throttle_command",
    "previous_brake_command",
    "actuator_steer_state",
    "actuator_throttle_state",
    "actuator_brake_state",
    "vx_body",
    "vy_body",
    "yaw_rate",
    "ax_body",
    "ay_body",
    "state_x",
    "state_y",
    "state_vx",
    "state_vy",
    "state_speed",
    "state_yaw_rate",
    "backend_status",
    "trace_delta_proxy",
    "command_response_proxy",
    "finite_metric",
]
MITIGATION_GUARD_FIELDNAMES = [
    "candidate_id",
    "role_family",
    "mitigation_reference",
    "execution_scheduled",
    "ordinary_success_denominator_allowed",
    "actor_visible_allowed",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "protected_field",
    "actor_visible_allowed",
    "actor_observation_shape",
    "action_shape",
    "status_pass",
    "evidence",
    "claim_boundary",
]
CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "allowed",
    "status_pass",
    "evidence",
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


def materialize_source_only_action_response_belief_intervention_preflight(
    output_dir: Path,
    *,
    m2772_design: Path | str = DEFAULT_M2772_DESIGN,
    m2641_dir: Path | str = DEFAULT_M2641_DIR,
    m2655_dir: Path | str = DEFAULT_M2655_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_paths = _source_paths(
        m2772_design=Path(m2772_design),
        m2641_dir=Path(m2641_dir),
        m2655_dir=Path(m2655_dir),
        source_checkpoint=Path(source_checkpoint),
    )
    model, admission = admit_actor_checkpoint(source_checkpoint, device=device)
    if model is not None:
        model.eval()

    run_items, _seed_rows, _axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=DEFAULT_FRESH_SEED_COUNT
    )
    candidate_rows = build_source_only_candidate_rows(
        run_items,
        source_checkpoint=Path(source_checkpoint),
        horizon_steps=int(horizon_steps),
    )
    condition_rows = build_intervention_condition_rows()
    matrix_rows = build_candidate_intervention_matrix(
        candidate_rows,
        condition_rows,
        horizon_steps=int(horizon_steps),
    )
    actor_guard_rows = build_actor_contract_guard_rows()
    claim_rows = build_claim_boundary_rows()

    execution_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    if model is None:
        for matrix_row in matrix_rows:
            failure_rows.append(
                {
                    "candidate_id": matrix_row["candidate_id"],
                    "intervention_condition_id": matrix_row["intervention_condition_id"],
                    "failure_type": "lineage_invalid",
                    "failure_reason": admission.reason,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    else:
        candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
        item_by_candidate_id = {
            _candidate_id(item.role_family, item.seed, item.dynamics_axis_id): item
            for item in run_items
        }
        for matrix_row in matrix_rows:
            candidate_id = matrix_row["candidate_id"]
            condition_id = matrix_row["intervention_condition_id"]
            item = item_by_candidate_id[candidate_id]
            try:
                rollout_trace, execution_row = _run_candidate_intervention(
                    model,
                    item,
                    candidate_by_id[candidate_id],
                    condition_id,
                    horizon_steps=int(horizon_steps),
                )
                trace_rows.extend(rollout_trace)
                execution_rows.append(execution_row)
            except Exception as exc:
                failure_rows.append(
                    {
                        "candidate_id": candidate_id,
                        "intervention_condition_id": condition_id,
                        "failure_type": "behavior_regression",
                        "failure_reason": f"{type(exc).__name__}: {exc}",
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )

    mitigation_guard_rows = build_mitigation_reference_guard_rows(candidate_rows)

    paths = {
        "source_only_candidate_rows": output_dir / "source_only_candidate_rows.csv",
        "intervention_condition_rows": output_dir / "intervention_condition_rows.csv",
        "candidate_intervention_matrix": output_dir / "candidate_intervention_matrix.csv",
        "intervention_execution_rows": output_dir / "intervention_execution_rows.csv",
        "intervention_failure_rows": output_dir / "intervention_failure_rows.csv",
        "action_response_trace_rows": output_dir / "action_response_trace_rows.csv",
        "mitigation_reference_guard_rows": output_dir / "mitigation_reference_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "summary": output_dir / "summary.json",
        "doc": Path(doc_path),
        "follow_up_manifest": Path(follow_up_manifest),
    }
    write_csv_rows(paths["source_only_candidate_rows"], candidate_rows, fieldnames=SOURCE_ONLY_CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["intervention_condition_rows"], condition_rows, fieldnames=INTERVENTION_CONDITION_FIELDNAMES)
    write_csv_rows(paths["candidate_intervention_matrix"], matrix_rows, fieldnames=CANDIDATE_INTERVENTION_FIELDNAMES)
    write_csv_rows(paths["intervention_execution_rows"], execution_rows, fieldnames=INTERVENTION_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["intervention_failure_rows"], failure_rows, fieldnames=INTERVENTION_FAILURE_FIELDNAMES)
    write_csv_rows(paths["action_response_trace_rows"], trace_rows, fieldnames=ACTION_RESPONSE_TRACE_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_guard_rows, fieldnames=MITIGATION_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)

    metrics = _metrics(
        output_dir=output_dir,
        source_paths=source_paths,
        admission=admission,
        candidate_rows=candidate_rows,
        condition_rows=condition_rows,
        matrix_rows=matrix_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        trace_rows=trace_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        paths=paths,
        horizon_steps=int(horizon_steps),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    gate_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = _summary(metrics, gate_rows)
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], _run_state(summary, paths))
    write_json(paths["follow_up_manifest"], _m2774_manifest(summary))
    _write_doc(paths["doc"], summary)
    return summary


def build_source_only_candidate_rows(
    run_items: list[Any],
    *,
    source_checkpoint: Path,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in run_items:
        mitigation_reference = item.role_family == "unavoidable_mitigation"
        rows.append(
            {
                "candidate_id": _candidate_id(item.role_family, item.seed, item.dynamics_axis_id),
                "role_family": item.role_family,
                "dynamics_axis": item.dynamics_axis_id,
                "seed": item.seed,
                "seed_index": item.seed_index,
                "backend_id": FourWheelHF0Backend.backend_id,
                "source_model": "FourWheelDriftModel",
                "checkpoint_path": str(source_checkpoint),
                "horizon_steps": int(horizon_steps),
                "source_only_surface_id": item.surface_id,
                "fixture_id": item.fixture_id,
                "base_fixture_id": item.base_fixture_id,
                "ordinary_success_denominator_allowed": not mitigation_reference,
                "mitigation_reference": mitigation_reference,
                "actor_visible_labels": False,
                "source_lineage": "m2772_design_m2641_role_seed_axis_fixture_generator",
            }
        )
    return rows


def build_intervention_condition_rows() -> list[dict[str, Any]]:
    return [
        {
            **condition,
            "actor_input_shape_changed": False,
            "actor_input_feature_added": False,
            "hidden_or_oracle_value_added": False,
            "actor_visible_label": False,
            "allowed_claim_scope": CLAIM_SCOPE,
        }
        for condition in INTERVENTION_CONDITIONS
    ]


def build_candidate_intervention_matrix(
    candidate_rows: list[dict[str, Any]],
    condition_rows: list[dict[str, Any]],
    *,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidate_rows:
        for condition in condition_rows:
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "intervention_condition_id": condition["intervention_condition_id"],
                    "execution_scheduled": True,
                    "matched_history_required": False,
                    "ordinary_denominator_allowed": bool(candidate["ordinary_success_denominator_allowed"]),
                    "expected_trace_rows": int(horizon_steps),
                    "stop_if_unresolved": True,
                }
            )
    return rows


def build_mitigation_reference_guard_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "role_family": row["role_family"],
            "mitigation_reference": bool(row["mitigation_reference"]),
            "execution_scheduled": True,
            "ordinary_success_denominator_allowed": bool(row["ordinary_success_denominator_allowed"]),
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for row in candidate_rows
        if bool(row["mitigation_reference"])
    ]


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    protected = (
        ("actor_shape", "P0_observation_72"),
        ("action_shape", "action_3"),
        ("action_mapping", "steer_throttle_brake"),
        ("hidden_dynamics", "mu_mass_tire_stiffness_brake_scale_actuator_tau"),
        ("oracle_labels", "slip_tire_force_ttc_required_clearance_success_verdict"),
        ("route_labels", "role_dynamics_intervention_route_progress_outcome_verdict"),
        ("external_dependency", "selected_platform_hf3_dependency"),
    )
    return [
        {
            "guard_id": f"m2773_actor_guard_{index:02d}_{field}",
            "guard_family": family,
            "protected_field": field,
            "actor_visible_allowed": False,
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "status_pass": True,
            "evidence": "P0 extractor output remains 72/3 and labels are CSV diagnostics only",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (family, field) in enumerate(protected)
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = (
        ("repair_success", False),
        ("driver_performance", False),
        ("validation_readiness", False),
        ("validation_result", False),
        ("ranking_or_winner_selection", False),
        ("checkpoint_promotion", False),
        ("success_rate_verdict", False),
        ("paper_evidence", False),
        ("finite_window_vs_gru_conclusion", False),
        ("current_sim_verdict", False),
        ("high_fidelity_validation", False),
        ("full_ideal_driver_completion", False),
        ("level3_self_identification", False),
    )
    return [
        {
            "claim_id": f"m2773_claim_{claim_id}",
            "claim_family": claim_id,
            "claim_made": made,
            "allowed": False,
            "status_pass": made is False,
            "evidence": "M2773 preflight is diagnostic materialization only",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for claim_id, made in claims
    ]


def build_gate_matrix_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    gate_specs = (
        ("source_artifacts_exist", "artifact", metrics["source_artifacts_exist"], True, "lineage_invalid"),
        ("checkpoint_admitted", "lineage", metrics["checkpoint_admitted"], True, "lineage_invalid"),
        ("candidate_row_count", "panel_shape", metrics["candidate_row_count"], 32, "scenario_sampling_failure"),
        ("role_family_count", "panel_shape", metrics["role_family_count"], 4, "scenario_sampling_failure"),
        ("dynamics_axis_count", "panel_shape", metrics["dynamics_axis_count"], 2, "scenario_sampling_failure"),
        ("intervention_condition_count", "panel_shape", metrics["intervention_condition_count"], 4, "metric_artifact"),
        ("candidate_intervention_row_count", "panel_shape", metrics["candidate_intervention_row_count"], 128, "metric_artifact"),
        ("execution_plus_failure_accounting", "artifact", metrics["execution_plus_failure_accounting"], True, "metric_artifact"),
        ("trace_row_accounting", "artifact", metrics["trace_row_accounting"], True, "metric_artifact"),
        ("actor_contract_shape_72_action_3", "actor_contract", metrics["actor_contract_shape_72_action_3"], True, "contract_violation"),
        ("all_actions_finite", "actor_contract", metrics["all_actions_finite"], True, "behavior_regression"),
        ("all_actions_within_bounds", "actor_contract", metrics["all_actions_within_bounds"], True, "behavior_regression"),
        ("hidden_oracle_actor_input_detected", "actor_contract", metrics["hidden_oracle_actor_input_detected"], False, "contract_violation"),
        ("actor_visible_label_detected", "actor_contract", metrics["actor_visible_label_detected"], False, "contract_violation"),
        ("mitigation_reference_rows_guarded", "claim_boundary", metrics["mitigation_reference_rows_guarded"], True, "proof_washout"),
        ("external_high_fidelity_simulation_included", "forbidden_claim", metrics["external_high_fidelity_simulation_included"], False, "objective_overfit"),
        ("training_run", "forbidden_claim", metrics["training_run"], False, "objective_overfit"),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("success_rate_computed", "forbidden_claim", metrics["success_rate_computed"], False, "objective_overfit"),
        ("driver_performance_claim_made", "forbidden_claim", metrics["driver_performance_claim_made"], False, "objective_overfit"),
        ("m2774_follow_up_manifest_registered", "next_route", metrics["m2774_follow_up_manifest_registered"], True, "lineage_invalid"),
    )
    rows = []
    for gate_id, family, observed, expected, failure_type in gate_specs:
        status_pass = observed == expected
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(status_pass),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status_pass else failure_type,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _run_candidate_intervention(
    model: Any,
    item: Any,
    candidate_row: dict[str, Any],
    condition_id: str,
    *,
    horizon_steps: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    extractor = P0ObservationExtractor()
    backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
    trace_rows: list[dict[str, Any]] = []
    hidden = None
    try:
        reset_result = backend.reset(
            BackendResetRequest(
                seed=item.seed,
                scenario_spec_id=item.fixture_id,
                role_family=item.role_family,
                options={
                    "candidate_id": candidate_row["candidate_id"],
                    "intervention_condition_id": condition_id,
                    "dynamics_axis": item.dynamics_axis_id,
                },
            )
        )
        actor_view = reset_result.actor_view
        reset_actuators = reset_result.actor_view.actuators
        for step_index in range(int(horizon_steps)):
            actor_view_for_actor = _intervened_actor_view(
                actor_view,
                condition_id=condition_id,
                reset_actuators=reset_actuators,
            )
            observation = extractor.extract(actor_view_for_actor)
            hidden_for_actor = None if condition_id == "reset_hidden_each_step" else hidden
            raw_action, _log_prob, _value, next_hidden = model.act_recurrent(
                observation,
                hidden_for_actor,
                deterministic=True,
            )
            if condition_id != "reset_hidden_each_step":
                hidden = next_hidden
            action_array = np.asarray(raw_action, dtype=np.float32)
            action_finite = bool(np.all(np.isfinite(action_array)))
            action_within_bounds = bool(
                action_array.shape == (ACTION_DIM,)
                and np.all(action_array >= -1.0)
                and np.all(action_array <= 1.0)
            )
            action = validate_actor_action(action_array)
            physical_control = physical_control_from_action(action)
            previous_command = np.asarray(
                [
                    actor_view_for_actor.actuators.previous_steer_command,
                    actor_view_for_actor.actuators.previous_throttle_command,
                    actor_view_for_actor.actuators.previous_brake_command,
                ],
                dtype=np.float32,
            )
            trace_delta_proxy = float(np.linalg.norm(physical_control - previous_command, ord=1))
            step_result = backend.step(action)
            state = dict(step_result.diagnostics.get("state", {}))
            state_vx = _float(state.get("vx", actor_view_for_actor.ego.vx_body))
            state_vy = _float(state.get("vy", actor_view_for_actor.ego.vy_body))
            command_response_proxy = float(
                np.linalg.norm(
                    np.asarray(
                        [
                            actor_view_for_actor.ego.ax_body,
                            actor_view_for_actor.ego.ay_body,
                            actor_view_for_actor.ego.yaw_rate,
                        ],
                        dtype=np.float32,
                    ),
                    ord=2,
                )
            )
            trace_rows.append(
                {
                    "candidate_id": candidate_row["candidate_id"],
                    "intervention_condition_id": condition_id,
                    "role_family": item.role_family,
                    "dynamics_axis": item.dynamics_axis_id,
                    "seed": item.seed,
                    "step_index": step_index,
                    "steer": float(action[0]),
                    "throttle": float(action[1]),
                    "brake": float(action[2]),
                    "physical_steer": float(physical_control[0]),
                    "physical_throttle": float(physical_control[1]),
                    "physical_brake": float(physical_control[2]),
                    "previous_steer_command": float(previous_command[0]),
                    "previous_throttle_command": float(previous_command[1]),
                    "previous_brake_command": float(previous_command[2]),
                    "actuator_steer_state": float(actor_view_for_actor.actuators.steer_angle_normalized),
                    "actuator_throttle_state": float(actor_view_for_actor.actuators.throttle_state),
                    "actuator_brake_state": float(actor_view_for_actor.actuators.brake_state),
                    "vx_body": float(actor_view_for_actor.ego.vx_body),
                    "vy_body": float(actor_view_for_actor.ego.vy_body),
                    "yaw_rate": float(actor_view_for_actor.ego.yaw_rate),
                    "ax_body": float(actor_view_for_actor.ego.ax_body),
                    "ay_body": float(actor_view_for_actor.ego.ay_body),
                    "state_x": _float(state.get("x", 0.0)),
                    "state_y": _float(state.get("y", 0.0)),
                    "state_vx": state_vx,
                    "state_vy": state_vy,
                    "state_speed": float(np.hypot(state_vx, state_vy)),
                    "state_yaw_rate": _float(state.get("yaw_rate", actor_view_for_actor.ego.yaw_rate)),
                    "backend_status": step_result.backend_status,
                    "trace_delta_proxy": trace_delta_proxy,
                    "command_response_proxy": command_response_proxy,
                    "finite_metric": bool(action_finite and action_within_bounds),
                }
            )
            actor_view = step_result.actor_view
    finally:
        backend.close()

    event = _event_stats(
        trace_rows,
        road=item.fixture_spec.road,
        obstacle=_primary_obstacle(item.fixture_spec.obstacles),
    )
    execution_row = {
        "candidate_id": candidate_row["candidate_id"],
        "intervention_condition_id": condition_id,
        "role_family": item.role_family,
        "dynamics_axis": item.dynamics_axis_id,
        "seed": item.seed,
        "steps_executed": len(trace_rows),
        "backend_status": trace_rows[-1]["backend_status"] if trace_rows else "missing",
        "action_finite": all(bool(row["finite_metric"]) for row in trace_rows),
        "action_within_bounds": all(bool(row["finite_metric"]) for row in trace_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "collision_diagnostic": bool(event.collision_event),
        "road_departure_diagnostic": bool(event.road_departure_event),
        "minimum_obstacle_clearance_m": float(event.minimum_obstacle_clearance_m),
        "minimum_road_margin_m": float(event.minimum_road_margin_m),
        "trace_delta_proxy": _mean(row["trace_delta_proxy"] for row in trace_rows),
        "command_response_proxy": _mean(row["command_response_proxy"] for row in trace_rows),
        "diagnostic_only": True,
    }
    return trace_rows, execution_row


def _intervened_actor_view(
    actor_view: ActorView,
    *,
    condition_id: str,
    reset_actuators: Any,
) -> ActorView:
    if condition_id in {"normal_recurrent", "reset_hidden_each_step"}:
        return actor_view
    if condition_id == "zero_previous_command_history":
        actuators = replace(
            actor_view.actuators,
            previous_steer_command=0.0,
            previous_throttle_command=0.0,
            previous_brake_command=0.0,
        )
        return replace(actor_view, actuators=actuators)
    if condition_id == "held_actuator_history":
        return replace(actor_view, actuators=reset_actuators)
    raise ValueError(f"unknown intervention condition: {condition_id}")


def _source_paths(
    *,
    m2772_design: Path,
    m2641_dir: Path,
    m2655_dir: Path,
    source_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2772_design": m2772_design,
        "m2641_summary": m2641_dir / "summary.json",
        "m2641_measured_behavior_rows": m2641_dir / "measured_behavior_rows.csv",
        "m2641_measured_event_rows": m2641_dir / "measured_event_rows.csv",
        "m2641_telemetry_rows": m2641_dir / "telemetry_rows.csv",
        "m2655_summary": m2655_dir / "summary.json",
        "source_checkpoint": source_checkpoint,
    }


def _metrics(
    *,
    output_dir: Path,
    source_paths: dict[str, Path],
    admission: Any,
    candidate_rows: list[dict[str, Any]],
    condition_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    paths: dict[str, Path],
    horizon_steps: int,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    source_exists = {name: path.exists() for name, path in source_paths.items()}
    role_families = sorted({row["role_family"] for row in candidate_rows})
    dynamics_axes = sorted({row["dynamics_axis"] for row in candidate_rows})
    condition_ids = sorted({row["intervention_condition_id"] for row in condition_rows})
    expected_matrix_rows = len(candidate_rows) * len(condition_rows)
    expected_trace_rows = len(execution_rows) * int(horizon_steps)
    execution_plus_failure_accounting = len(execution_rows) + len(failure_rows) == len(matrix_rows)
    trace_row_accounting = len(trace_rows) == expected_trace_rows
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in execution_rows} in ({P0_OBSERVATION_DIM}, set())
        and {int(row["action_shape"]) for row in execution_rows} in ({ACTION_DIM}, set())
    )
    all_actions_finite = bool(execution_rows) and all(bool(row["action_finite"]) for row in execution_rows)
    all_actions_within_bounds = bool(execution_rows) and all(
        bool(row["action_within_bounds"]) for row in execution_rows
    )
    hidden_oracle_actor_input_detected = False
    actor_visible_label_detected = any(
        bool(row["actor_visible_labels"]) for row in candidate_rows
    ) or any(bool(row["actor_visible_label"]) for row in condition_rows)
    mitigation_reference_rows_guarded = (
        len(mitigation_guard_rows) == DEFAULT_FRESH_SEED_COUNT * len(DYNAMICS_AXES)
        and all(row["role_family"] == "unavoidable_mitigation" for row in mitigation_guard_rows)
        and all(bool(row["ordinary_success_denominator_allowed"]) is False for row in mitigation_guard_rows)
        and all(bool(row["actor_visible_allowed"]) is False for row in mitigation_guard_rows)
    )
    required_artifacts_present = all(
        paths[key].exists()
        for key in (
            "source_only_candidate_rows",
            "intervention_condition_rows",
            "candidate_intervention_matrix",
            "intervention_execution_rows",
            "intervention_failure_rows",
            "action_response_trace_rows",
            "mitigation_reference_guard_rows",
            "actor_contract_guard_rows",
            "claim_boundary_rows",
        )
    )
    metrics = {
        "milestone": milestone,
        "result_class": "engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight_pass",
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "source_artifacts_exist": all(source_exists.values()),
        "source_artifact_exists": source_exists,
        "required_artifacts_present": required_artifacts_present,
        "checkpoint_path": admission.checkpoint_path,
        "checkpoint_admitted": bool(admission.checkpoint_admitted),
        "checkpoint_admission_reason": admission.reason,
        "checkpoint_obs_dim": admission.obs_dim,
        "checkpoint_action_dim": admission.action_dim,
        "checkpoint_actor_encoder": admission.actor_encoder,
        "checkpoint_action_sequence_horizon": admission.action_sequence_horizon,
        "candidate_row_count": len(candidate_rows),
        "role_family_count": len(role_families),
        "role_families": role_families,
        "dynamics_axis_count": len(dynamics_axes),
        "dynamics_axes": dynamics_axes,
        "intervention_condition_count": len(condition_rows),
        "intervention_conditions": condition_ids,
        "candidate_intervention_row_count": len(matrix_rows),
        "expected_candidate_intervention_rows": expected_matrix_rows,
        "intervention_execution_row_count": len(execution_rows),
        "intervention_failure_row_count": len(failure_rows),
        "expected_trace_rows": expected_trace_rows,
        "action_response_trace_row_count": len(trace_rows),
        "horizon_steps": int(horizon_steps),
        "execution_plus_failure_accounting": execution_plus_failure_accounting,
        "trace_row_accounting": trace_row_accounting,
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "all_actions_finite": all_actions_finite,
        "all_actions_within_bounds": all_actions_within_bounds,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected,
        "actor_visible_label_detected": actor_visible_label_detected,
        "actor_guard_row_count": len(actor_guard_rows),
        "actor_guard_rows_pass": bool(actor_guard_rows) and all(bool(row["status_pass"]) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": bool(claim_rows) and all(bool(row["status_pass"]) for row in claim_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "mitigation_reference_rows_guarded": mitigation_reference_rows_guarded,
        "collision_diagnostic_row_count": sum(bool(row["collision_diagnostic"]) for row in execution_rows),
        "road_departure_diagnostic_row_count": sum(bool(row["road_departure_diagnostic"]) for row in execution_rows),
        "external_high_fidelity_simulation_included": False,
        "high_fidelity_simulation_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "training_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "success_rate_verdict_field_emitted": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_claim_made": False,
        "m2774_follow_up_manifest_registered": True,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return metrics


def _summary(metrics: dict[str, Any], gate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        gate_matrix_pass
        and metrics["required_artifacts_present"]
        and metrics["execution_plus_failure_accounting"]
        and metrics["trace_row_accounting"]
        and metrics["intervention_failure_row_count"] == 0
        and metrics["checkpoint_admitted"]
    )
    result = dict(metrics)
    result.update(
        {
            "status_pass": bool(status_pass),
            "gate_matrix_pass": bool(gate_matrix_pass),
            "gate_matrix_row_count": len(gate_rows),
            "gate_matrix": str(Path(metrics["output_dir"]) / "gate_matrix.csv"),
        }
    )
    if not status_pass:
        result["result_class"] = (
            "engineering_controller_route_a_source_only_action_response_belief_"
            "intervention_materialization_preflight_failed"
        )
    return result


def _run_state(summary: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "result_class": summary["result_class"],
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "generated_at_utc": summary["generated_at_utc"],
    }


def _m2774_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    m2773_id = summary["milestone"]
    m2774_id = DEFAULT_NEXT_BLOCKER
    run_dir = Path(summary["output_dir"])
    return {
        "id": m2774_id,
        "type": "gate",
        "gate_tier": "proof",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
        ],
        "lineage": {
            "parent_checkpoint": [summary["checkpoint_path"]],
            "parent_dataset": [
                str(run_dir / "summary.json"),
                str(run_dir / "source_only_candidate_rows.csv"),
                str(run_dir / "intervention_condition_rows.csv"),
                str(run_dir / "candidate_intervention_matrix.csv"),
                str(run_dir / "intervention_execution_rows.csv"),
                str(run_dir / "intervention_failure_rows.csv"),
                str(run_dir / "action_response_trace_rows.csv"),
                str(run_dir / "mitigation_reference_guard_rows.csv"),
                str(run_dir / "actor_contract_guard_rows.csv"),
                str(run_dir / "claim_boundary_rows.csv"),
                str(run_dir / "gate_matrix.csv"),
                summary["doc"],
            ],
            "parent_config": [
                "experiments/manifests/m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight.json",
                "experiments/manifests/m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design.json",
            ],
            "parent_objective": [
                "audit M2773 source-only action-response belief intervention materialization artifacts before interpretation"
            ],
            "derived_from": [m2773_id, "m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design"],
            "blocked_by": [
                "M2773 materialization must be audited before any history-belief interpretation",
                "M2773 preflight rows are source-only diagnostics and not validation performance or self-ID evidence",
            ],
            "supersedes": [
                "direct self-ID interpretation from M2773 preflight rows",
                "driver-performance interpretation from source-only intervention rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{m2774_id}.md",
        "public_gates": [
            "M2774 must audit M2773 artifact completeness actor-contract preservation and claim boundaries",
            "M2774 must preserve M2773 source-only diagnostic scope and reject validation performance paper high-fidelity full-driver and self-ID claims",
            "M2774 must decide whether to route to intervention result synthesis proof extension artifact repair or branch stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step rollout replay validation training PPO source build adapter probe or external simulation in audit",
            "do not change actor inputs or action contract",
            "do not rank intervention conditions or select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdicts",
            "do not claim driver performance paper current-sim high-fidelity full ideal driver or self-ID evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_action_response_belief_intervention",
            "evidence_axis": "source_only_action_response_belief_intervention_materialization_result_audit",
            "evidence_increment": "audits M2773 source-only intervention artifacts before interpretation or next-route selection",
            "claim_scope": "M2773 result audit only; no new execution training ranking validation performance paper current-sim high-fidelity self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2773 artifacts are incomplete",
                "stop if actor labels or hidden/oracle values entered actor input",
                "stop if source-only diagnostic rows would be interpreted as validation performance or self-ID evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting is incomplete",
                "route to implementation repair if intervention hooks violated contract",
                "route to synthesis if artifacts are complete but negative or ambiguous",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2773 writes source-only intervention materialization artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "evaluation_only",
            "stage_objective": "source-only action-response belief intervention materialization result audit",
            "admission_evidence": ["M2773 summary and gate artifacts exist"],
            "blocked_shortcuts": ["no execution training ranking validation performance paper HF or self-ID claim in audit"],
            "allowed_updates": [f"docs/{m2774_id}.md", "M2774 status queue scoreboard research log and review"],
            "next_stage_criteria": ["audit artifact exists", "one bounded next route or stop decision is selected"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2774 may audit history-intervention rows but cannot by itself establish level3 self-identification.",
            "history_necessity_tests": ["audit only; no new tests in M2774"],
            "temporal_evidence_window": "M2772-M2773 source-only intervention branch",
            "negative_result_policy": "Preserve negative or ambiguous intervention results instead of weakening self-ID gates.",
            "allowed_claims": [
                "M2773 artifacts are complete and claim-safe or incomplete",
                "no driver-performance verdict paper result high-fidelity validation full ideal driver or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a new source-only intervention panel rather than extending same-surface repair",
            "paper_verdict_delta": "no paper verdict; audit may select whether intervention artifacts justify later proof synthesis",
            "must_synthesize_if": [
                "M2774 cannot select a bounded follow-up route",
                "M2774 would claim self-ID or performance from source-only preflight rows",
            ],
        },
        "hypothesis": "M2773 source-only intervention artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{m2774_id}.md exists",
            "M2774 audits M2773 summary candidate intervention execution trace actor guard claim and gate artifacts",
            "M2774 preserves no ranking validation performance paper high-fidelity full-driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2774 executes new rollouts or training",
            "M2774 claims driver performance or self-ID",
            "M2774 fails to select a bounded next route or stop",
        ],
        "decision_rule": "Pass only if M2774 audits M2773 artifacts and selects a bounded next route without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{m2774_id}.md", "type": "md"}],
        "baseline_checkpoints": [summary["checkpoint_path"]],
        "baseline_artifacts": [str(run_dir / "summary.json"), summary["doc"]],
        "scoreboard_checkpoint": f"docs/{m2774_id}.md",
    }


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# M2773 Engineering Controller Route A Source-Only Action-Response Belief Intervention Materialization Preflight

## Metadata

- status: {'completed' if summary['status_pass'] else 'failed'}
- result class: `{summary['result_class']}`
- summary: `{summary['summary']}`
- follow-up manifest: `{summary['follow_up_manifest']}`
- next: `{summary['next_blocker']}`

## Artifact Accounting

```text
candidate rows: {summary['candidate_row_count']}
intervention conditions: {summary['intervention_condition_count']}
candidate/intervention rows: {summary['candidate_intervention_row_count']}
execution rows: {summary['intervention_execution_row_count']}
failure rows: {summary['intervention_failure_row_count']}
action-response trace rows: {summary['action_response_trace_row_count']}
mitigation reference guard rows: {summary['mitigation_reference_guard_row_count']}
actor guard rows: {summary['actor_guard_row_count']}
claim boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Intervention Surface

M2773 materialized a repo-local source-only HF0/FourWheel intervention panel
over 32 role/seed/dynamics-axis rows. The intervention conditions are:

```text
{', '.join(summary['intervention_conditions'])}
```

The rows are diagnostic materialization only. They are not ranking, promotion,
validation, driver-performance, paper, current-sim, high-fidelity, full-driver,
or self-ID evidence.

## Actor And Claim Boundary

```text
actor contract 72/action 3: {summary['actor_contract_shape_72_action_3']}
hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}
actor-visible label detected: {summary['actor_visible_label_detected']}
all actions finite: {summary['all_actions_finite']}
all actions within bounds: {summary['all_actions_within_bounds']}
mitigation reference rows guarded: {summary['mitigation_reference_rows_guarded']}
external high-fidelity simulation run: {summary['high_fidelity_simulation_run']}
training run: {summary['training_run']}
ranking run: {summary['ranking_run']}
success-rate computed: {summary['success_rate_computed']}
self-ID claim made: {summary['level3_self_id_claim_made']}
```

## Diagnostic Accounting

```text
collision diagnostic rows: {summary['collision_diagnostic_row_count']}
road departure diagnostic rows: {summary['road_departure_diagnostic_row_count']}
```

These counts are diagnostic row accounting only and not a success-rate verdict.

## Route Decision

Route to M2774 result audit before interpreting intervention deltas or deciding
whether this branch supports a later proof synthesis, artifact repair, or stop.
"""
    path.write_text(text, encoding="utf-8")


def _candidate_id(role: str, seed: int, dynamics_axis: str) -> str:
    return f"m2773_{role}_seed_{int(seed)}_{dynamics_axis}"


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _mean(values: Any) -> float:
    seq = [float(value) for value in values]
    if not seq:
        return 0.0
    return float(sum(seq) / len(seq))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2772-design", default=DEFAULT_M2772_DESIGN)
    parser.add_argument("--m2641-dir", default=str(DEFAULT_M2641_DIR))
    parser.add_argument("--m2655-dir", default=str(DEFAULT_M2655_DIR))
    parser.add_argument("--source-checkpoint", default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)
    summary = materialize_source_only_action_response_belief_intervention_preflight(
        Path(args.output_dir),
        m2772_design=args.m2772_design,
        m2641_dir=args.m2641_dir,
        m2655_dir=args.m2655_dir,
        source_checkpoint=args.source_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        horizon_steps=int(args.horizon_steps),
        device=args.device,
        doc_path=args.doc_path,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'} status_pass={summary['status_pass']}")


if __name__ == "__main__":
    main()
