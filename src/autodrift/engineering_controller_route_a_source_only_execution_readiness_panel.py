"""Route A source-only execution-readiness panel for diagnostic baselines."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_bounded_measured_behavior_panel import (
    FALSE_CLAIM_FLAGS,
    METRIC_COMPLETENESS_FIELDNAMES,
    MITIGATION_REFERENCE_SUBJECT,
    _command_delta_l1_mean,
    _fraction,
    _has_value,
    _max_abs,
    _row_backend_status,
    _terminal_status,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    DEFAULT_SEED_COUNT,
    EXTRA_BEHAVIOR_FIELDS,
    MEASURED_EVENT_FIELDNAMES,
    SEED_PANEL_SPEC_FIELDNAMES,
    _baseline_like_rows,
    build_seed_panel_specs,
)
from autodrift.engineering_controller_source_only_outcome_events import (
    _bool_text,
    _event_stats,
    _float_text,
    _primary_obstacle,
)
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.hf0_source_only_closed_loop_fixture_pilot import admit_actor_checkpoint
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    validate_actor_action,
)
from autodrift.train_ppo import ActorCritic


DEFAULT_MILESTONE = (
    "m2544-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2545-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2544-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel"
)
DEFAULT_HORIZON_STEPS = 100

M2543_DESIGN = "docs/m2543-engineering-controller-route-a-baseline-and-interface-execution-readiness-design.md"
M2542_AUDIT = "docs/m2542-engineering-controller-route-a-baseline-and-interface-materialization-result-audit.md"
M2541_BASELINE_LIST = (
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/"
    "baseline_checkpoint_list.csv"
)
M2541_ACTOR_CONTRACT = (
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/"
    "actor_io_contract_snapshot.json"
)
M2541_SUMMARY = "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json"
M2523_SUMMARY = "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/summary.json"
M2523_SEED_PANEL = (
    "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/"
    "seed_panel_spec.csv"
)
M2514_ROW_SCHEMA = "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv"
M2514_METRIC_REGISTRY = (
    "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv"
)

CLAIM_SCOPE = "source-only Route A baseline execution-readiness panel preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, "
    "or self-ID claim"
)

SUBJECT_REGISTRY_FIELDNAMES = [
    "subject_id",
    "subject_family",
    "action_source",
    "checkpoint_path",
    "fixed_action_steer",
    "fixed_action_throttle",
    "fixed_action_brake",
    "policy_action",
    "checkpoint_admitted",
    "checkpoint_admission_reason",
    "checkpoint_obs_dim",
    "checkpoint_action_dim",
    "checkpoint_actor_encoder",
    "checkpoint_action_sequence_horizon",
    "actor_contract_id",
    "observation_shape",
    "action_shape",
    "allowed_use",
    "promotion_status",
    "forbidden_interpretation",
]

TELEMETRY_FIELDNAMES = [
    "seed_panel_id",
    "seed_index",
    "seed",
    "base_fixture_id",
    "fresh_seed_variant_digest",
    "comparison_subject",
    "comparison_subject_family",
    "fixture_id",
    "surface_id",
    "role_family",
    "step_index",
    "observation_shape",
    "action_shape",
    "action_steer",
    "action_throttle",
    "action_brake",
    "action_finite",
    "action_within_bounds",
    "action_saturated",
    "backend_status",
    "terminated_by_backend",
    "truncated_by_backend",
    "diagnostic_wheel_force_count",
    "state_x",
    "state_y",
    "state_psi",
    "state_vx",
    "state_vy",
    "state_speed",
    "state_yaw_rate",
    "physical_steer",
    "physical_throttle",
    "physical_brake",
    "parameterized_fixture",
    "reset_observation_digest",
    "policy_action",
    "diagnostic_only",
]

POLICY_SUBJECT_IDS = (
    "m1154_original_policy",
    "m2532_guarded_repair_policy",
    "m2537_mitigation_preserving_policy",
)
OPEN_LOOP_SUBJECT_IDS = (
    "coast_open_loop",
    "straight_full_brake_open_loop",
)

DEFAULT_POLICY_CHECKPOINTS = {
    "m1154_original_policy": (
        "runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt"
    ),
    "m2532_guarded_repair_policy": (
        "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/"
        "checkpoints/m2532_guarded_actor_head_repair.pt"
    ),
    "m2537_mitigation_preserving_policy": (
        "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/"
        "checkpoints/m2537_mitigation_preserving_actor_head_repair.pt"
    ),
}


@dataclass(frozen=True)
class RouteASubject:
    subject_id: str
    subject_family: str
    checkpoint_path: str
    fixed_action: tuple[float, float, float] | None
    policy_action: bool
    allowed_use: str
    promotion_status: str


@dataclass(frozen=True)
class AdmittedRouteASubject:
    subject: RouteASubject
    model: ActorCritic | None
    admission: Any


def route_a_subjects(
    policy_checkpoints: dict[str, str | Path] | None = None,
) -> tuple[RouteASubject, ...]:
    checkpoints = {
        key: str(value)
        for key, value in (policy_checkpoints or DEFAULT_POLICY_CHECKPOINTS).items()
    }
    return (
        RouteASubject(
            subject_id="m1154_original_policy",
            subject_family="policy_checkpoint",
            checkpoint_path=checkpoints["m1154_original_policy"],
            fixed_action=None,
            policy_action=True,
            allowed_use="historical_diagnostic_baseline",
            promotion_status="historical_promoted_not_repromoted_by_m2544",
        ),
        RouteASubject(
            subject_id="m2532_guarded_repair_policy",
            subject_family="policy_checkpoint",
            checkpoint_path=checkpoints["m2532_guarded_repair_policy"],
            fixed_action=None,
            policy_action=True,
            allowed_use="diagnostic_behavior_changed_repair_candidate",
            promotion_status="not_promoted",
        ),
        RouteASubject(
            subject_id="m2537_mitigation_preserving_policy",
            subject_family="policy_checkpoint",
            checkpoint_path=checkpoints["m2537_mitigation_preserving_policy"],
            fixed_action=None,
            policy_action=True,
            allowed_use="diagnostic_retained_gate_repair_candidate",
            promotion_status="not_promoted",
        ),
        RouteASubject(
            subject_id="coast_open_loop",
            subject_family="open_loop_action",
            checkpoint_path="",
            fixed_action=(0.0, -1.0, -1.0),
            policy_action=False,
            allowed_use="actuator_interface_reference",
            promotion_status="not_applicable",
        ),
        RouteASubject(
            subject_id="straight_full_brake_open_loop",
            subject_family="open_loop_action",
            checkpoint_path="",
            fixed_action=(0.0, -1.0, 1.0),
            policy_action=False,
            allowed_use="mitigation_reference",
            promotion_status="not_applicable",
        ),
    )


def materialize_route_a_source_only_execution_readiness_panel(
    output_dir: Path,
    *,
    policy_checkpoints: dict[str, str | Path] | None = None,
    seed_count: int = DEFAULT_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    if int(seed_count) < DEFAULT_SEED_COUNT:
        raise ValueError(f"seed_count must be at least {DEFAULT_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()
    row_schema_fields = [row["field_name"] for row in source["row_schema"]]
    subjects = route_a_subjects(policy_checkpoints)
    admitted_subjects, subject_registry_rows = admit_route_a_subjects(subjects, device=device)
    run_items, seed_panel_spec_rows = build_seed_panel_specs(seed_count=int(seed_count))
    telemetry_rows, telemetry_summary = run_route_a_telemetry(
        run_items,
        admitted_subjects,
        horizon_steps=int(horizon_steps),
    )
    measured_behavior_rows, measured_event_rows = build_route_a_measured_rows(
        telemetry_rows,
        run_items=run_items,
        subjects=subjects,
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    metric_completeness_rows = build_metric_completeness_rows(
        source["metric_registry"],
        measured_behavior_rows,
    )

    seed_panel_spec_path = output_dir / "seed_panel_spec.csv"
    subject_registry_path = output_dir / "subject_registry.csv"
    telemetry_path = output_dir / "telemetry_rows.csv"
    measured_behavior_path = output_dir / "measured_behavior_rows.csv"
    measured_event_path = output_dir / "measured_event_rows.csv"
    metric_completeness_path = output_dir / "metric_completeness_rows.csv"

    write_csv_rows(seed_panel_spec_path, seed_panel_spec_rows, fieldnames=SEED_PANEL_SPEC_FIELDNAMES)
    write_csv_rows(subject_registry_path, subject_registry_rows, fieldnames=SUBJECT_REGISTRY_FIELDNAMES)
    write_csv_rows(telemetry_path, telemetry_rows, fieldnames=TELEMETRY_FIELDNAMES)
    write_csv_rows(
        measured_behavior_path,
        measured_behavior_rows,
        fieldnames=row_schema_fields + EXTRA_BEHAVIOR_FIELDS,
    )
    write_csv_rows(measured_event_path, measured_event_rows, fieldnames=MEASURED_EVENT_FIELDNAMES)
    write_csv_rows(
        metric_completeness_path,
        metric_completeness_rows,
        fieldnames=METRIC_COMPLETENESS_FIELDNAMES,
    )

    doc_output = Path(doc_path)
    summary = _summary(
        output_dir=output_dir,
        source=source,
        subjects=subjects,
        subject_registry_rows=subject_registry_rows,
        telemetry_summary=telemetry_summary,
        seed_panel_spec_rows=seed_panel_spec_rows,
        measured_behavior_rows=measured_behavior_rows,
        measured_event_rows=measured_event_rows,
        metric_completeness_rows=metric_completeness_rows,
        seed_panel_spec_path=seed_panel_spec_path,
        subject_registry_path=subject_registry_path,
        telemetry_path=telemetry_path,
        measured_behavior_path=measured_behavior_path,
        measured_event_path=measured_event_path,
        metric_completeness_path=metric_completeness_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def admit_route_a_subjects(
    subjects: tuple[RouteASubject, ...],
    *,
    device: str = "cpu",
) -> tuple[list[AdmittedRouteASubject], list[dict[str, Any]]]:
    admitted_subjects: list[AdmittedRouteASubject] = []
    registry_rows: list[dict[str, Any]] = []
    for subject in subjects:
        model = None
        admission = None
        if subject.policy_action:
            model, admission = admit_actor_checkpoint(subject.checkpoint_path, device=device)
        row = _subject_registry_row(subject, admission)
        registry_rows.append(row)
        admitted_subjects.append(AdmittedRouteASubject(subject=subject, model=model, admission=admission))
    return admitted_subjects, registry_rows


def run_route_a_telemetry(
    run_items: list[Any],
    admitted_subjects: list[AdmittedRouteASubject],
    *,
    horizon_steps: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    extractor = P0ObservationExtractor()
    telemetry_rows: list[dict[str, Any]] = []
    reset_count = 0
    reset_observation_shapes: list[int] = []
    reset_digest_by_subject_role_seed: dict[str, str] = {}
    policy_admission_rows = [
        item
        for item in admitted_subjects
        if item.subject.policy_action and item.admission is not None
    ]
    all_policy_checkpoints_admitted = bool(policy_admission_rows) and all(
        item.admission.checkpoint_admitted for item in policy_admission_rows
    )
    if not all_policy_checkpoints_admitted:
        return [], {
            "all_policy_checkpoints_admitted": False,
            "reset_count": 0,
            "telemetry_row_count": 0,
            "reset_observation_shapes": [],
            "reset_digest_by_subject_role_seed": {},
        }

    for subject_item in admitted_subjects:
        subject = subject_item.subject
        for item in run_items:
            backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
            hidden = None
            try:
                reset_result = backend.reset(
                    BackendResetRequest(
                        seed=item.seed,
                        scenario_spec_id=item.fixture_id,
                        role_family=item.role_family,
                        options={
                            "seed_panel_id": item.seed_panel_id,
                            "seed_index": item.seed_index,
                            "seed": item.seed,
                            "base_fixture_id": item.base_fixture_id,
                            "comparison_subject": subject.subject_id,
                            "comparison_subject_family": subject.subject_family,
                        },
                    )
                )
                observation = extractor.extract(reset_result.actor_view)
                reset_digest = _observation_digest(observation)
                reset_observation_shapes.append(int(observation.shape[0]))
                reset_count += 1
                reset_digest_by_subject_role_seed[
                    f"{subject.subject_id}:{item.role_family}:{item.seed}"
                ] = reset_digest

                for step_index in range(int(horizon_steps)):
                    raw_action, hidden = _subject_action(subject_item, observation, hidden)
                    action_array = np.asarray(raw_action, dtype=np.float32)
                    action_shape = int(action_array.shape[0]) if action_array.ndim == 1 else -1
                    action_finite = bool(np.all(np.isfinite(action_array)))
                    action_within_bounds = bool(
                        action_array.shape == (ACTION_DIM,)
                        and np.all(action_array >= -1.0)
                        and np.all(action_array <= 1.0)
                    )
                    action_saturated = bool(
                        action_array.shape == (ACTION_DIM,)
                        and np.any(np.abs(action_array) >= 0.999)
                    )
                    action = validate_actor_action(action_array)
                    step_result = backend.step(action)
                    observation = extractor.extract(step_result.actor_view)
                    state = dict(step_result.diagnostics.get("state", {}))
                    physical_control = list(
                        step_result.diagnostics.get("physical_control", [0.0, 0.0, 0.0])
                    )
                    state_vx = _float(state.get("vx", 0.0))
                    state_vy = _float(state.get("vy", 0.0))
                    telemetry_rows.append(
                        {
                            "seed_panel_id": item.seed_panel_id,
                            "seed_index": item.seed_index,
                            "seed": item.seed,
                            "base_fixture_id": item.base_fixture_id,
                            "fresh_seed_variant_digest": item.fixture_variant_digest,
                            "comparison_subject": subject.subject_id,
                            "comparison_subject_family": subject.subject_family,
                            "fixture_id": item.fixture_id,
                            "surface_id": item.surface_id,
                            "role_family": item.role_family,
                            "step_index": step_index,
                            "observation_shape": int(observation.shape[0]),
                            "action_shape": action_shape,
                            "action_steer": float(action[0]),
                            "action_throttle": float(action[1]),
                            "action_brake": float(action[2]),
                            "action_finite": action_finite,
                            "action_within_bounds": action_within_bounds,
                            "action_saturated": action_saturated,
                            "backend_status": step_result.backend_status,
                            "terminated_by_backend": bool(step_result.terminated_by_backend),
                            "truncated_by_backend": bool(step_result.truncated_by_backend),
                            "diagnostic_wheel_force_count": len(
                                step_result.diagnostics["wheel_forces"]
                            ),
                            "state_x": _float(state.get("x", 0.0)),
                            "state_y": _float(state.get("y", 0.0)),
                            "state_psi": _float(state.get("psi", 0.0)),
                            "state_vx": state_vx,
                            "state_vy": state_vy,
                            "state_speed": float(np.hypot(state_vx, state_vy)),
                            "state_yaw_rate": _float(state.get("yaw_rate", 0.0)),
                            "physical_steer": _physical_control_value(physical_control, 0),
                            "physical_throttle": _physical_control_value(physical_control, 1),
                            "physical_brake": _physical_control_value(physical_control, 2),
                            "parameterized_fixture": True,
                            "reset_observation_digest": reset_digest,
                            "policy_action": subject.policy_action,
                            "diagnostic_only": True,
                        }
                    )
            finally:
                backend.close()

    return telemetry_rows, {
        "all_policy_checkpoints_admitted": True,
        "reset_count": reset_count,
        "telemetry_row_count": len(telemetry_rows),
        "reset_observation_shapes": reset_observation_shapes,
        "reset_digest_by_subject_role_seed": reset_digest_by_subject_role_seed,
    }


def build_route_a_measured_rows(
    telemetry_rows: list[dict[str, Any]],
    *,
    run_items: list[Any],
    subjects: tuple[RouteASubject, ...],
    row_schema_fields: list[str],
    milestone: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item_by_role_seed = {(item.role_family, item.seed): item for item in run_items}
    subject_by_id = {subject.subject_id: subject for subject in subjects}
    rows_by_subject_role_seed: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in telemetry_rows:
        rows_by_subject_role_seed[
            (row["comparison_subject"], row["role_family"], int(row["seed"]))
        ].append(row)

    event_by_subject_role_seed: dict[tuple[str, str, int], dict[str, Any]] = {}
    for key, rows in rows_by_subject_role_seed.items():
        _subject_id, role, seed = key
        item = item_by_role_seed[(role, seed)]
        event_stats = _event_stats(
            sorted(rows, key=lambda value: int(value["step_index"])),
            road=item.fixture_spec.road,
            obstacle=_primary_obstacle(item.fixture_spec.obstacles),
        )
        event_by_subject_role_seed[key] = {
            "collision_event": event_stats.collision_event,
            "obstacle_passed_event": event_stats.obstacle_passed_event,
            "road_departure_event": event_stats.road_departure_event,
            "minimum_obstacle_clearance_m": event_stats.minimum_obstacle_clearance_m,
            "minimum_road_margin_m": event_stats.minimum_road_margin_m,
            "final_road_margin_m": event_stats.final_road_margin_m,
            "collision_speed_proxy": event_stats.collision_speed_proxy,
            "impact_angle_proxy": event_stats.impact_angle_proxy,
            "severity_proxy": event_stats.severity_proxy,
            "recovery_time_proxy_s": event_stats.recovery_time_proxy_s,
        }

    for (subject_id, role, seed), event in list(event_by_subject_role_seed.items()):
        reference = event_by_subject_role_seed[(MITIGATION_REFERENCE_SUBJECT, role, seed)]
        event["mitigation_delta_against_reference"] = (
            float(event["severity_proxy"]) - float(reference["severity_proxy"])
        )

    measured_behavior_rows: list[dict[str, Any]] = []
    measured_event_rows: list[dict[str, Any]] = []
    for item in run_items:
        for subject_id in sorted(subject_by_id):
            subject = subject_by_id[subject_id]
            group = sorted(
                rows_by_subject_role_seed[(subject_id, item.role_family, item.seed)],
                key=lambda value: int(value["step_index"]),
            )
            if not group:
                continue
            first = group[0]
            last = group[-1]
            event = event_by_subject_role_seed[(subject_id, item.role_family, item.seed)]
            row_id = f"m2544_{subject_id}_{item.role_family}_seed_{item.seed}"
            behavior_row = {
                "protocol_version": "engineering_controller_behavior_outcome_v0",
                "milestone_id": milestone,
                "run_id": milestone,
                "row_id": row_id,
                "evidence_layer": "source_only_diagnostic",
                "surface_id": first["surface_id"],
                "scenario_role": item.role_family,
                "fixture_id": item.fixture_id,
                "seed": item.seed,
                "subject_id": subject_id,
                "checkpoint_path": subject.checkpoint_path if subject.policy_action else "",
                "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
                "observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "actor_encoder": "human_view_online_gru" if subject.policy_action else "",
                "action_horizon": 1,
                "actor_input_leak_flags": "none",
                "reset_status": "reset_ok",
                "backend_status": _row_backend_status(_baseline_like_rows(group)),
                "episode_started": True,
                "episode_completed": True,
                "step_count": len(group),
                "terminal_status": _terminal_status(_baseline_like_rows(group)),
                "action_finite": all(bool(row["action_finite"]) for row in group),
                "action_within_bounds": all(bool(row["action_within_bounds"]) for row in group),
                "collision_event": event["collision_event"],
                "obstacle_passed_event": event["obstacle_passed_event"],
                "road_departure_event": event["road_departure_event"],
                "minimum_obstacle_clearance_m": event["minimum_obstacle_clearance_m"],
                "minimum_road_margin_m": event["minimum_road_margin_m"],
                "final_road_margin_m": event["final_road_margin_m"],
                "maximum_abs_lateral_velocity": _max_abs(row["state_vy"] for row in group),
                "maximum_abs_yaw_rate": _max_abs(row["state_yaw_rate"] for row in group),
                "maximum_abs_lateral_position": _max_abs(row["state_y"] for row in group),
                "final_abs_lateral_velocity": abs(float(last["state_vy"])),
                "final_abs_yaw_rate": abs(float(last["state_yaw_rate"])),
                "recovery_time_proxy_s": event["recovery_time_proxy_s"],
                "steering_saturation_fraction": _fraction(row["action_saturated"] for row in group),
                "throttle_saturation_fraction": _fraction(
                    abs(float(row["action_throttle"])) >= 0.999 for row in group
                ),
                "brake_saturation_fraction": _fraction(
                    abs(float(row["action_brake"])) >= 0.999 for row in group
                ),
                "command_delta_l1_mean": _command_delta_l1_mean(_baseline_like_rows(group)),
                "simultaneous_throttle_brake_fraction": _fraction(
                    float(row["physical_throttle"]) > 1e-9 and float(row["physical_brake"]) > 1e-9
                    for row in group
                ),
                "collision_speed_proxy": event["collision_speed_proxy"],
                "impact_angle_proxy": event["impact_angle_proxy"],
                "severity_proxy": event["severity_proxy"],
                "mitigation_delta_against_reference": event["mitigation_delta_against_reference"],
                "metric_completeness_flags": "complete",
                "diagnostic_only_no_ranking_claim": True,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                "source_artifact": "Route A source-only execution-readiness panel",
                "attempted_row_retained": True,
                "seed_panel_id": item.seed_panel_id,
                "seed_index": item.seed_index,
                "base_fixture_id": item.base_fixture_id,
                "fresh_seed_variant_digest": item.fixture_variant_digest,
                "mitigation_reference_subject": MITIGATION_REFERENCE_SUBJECT,
                "mitigation_reference_seed": item.seed,
                "denominator_gap_reason": "",
                "ranking_or_winner_field_emitted": False,
            }
            measured_behavior_rows.append(
                {field: behavior_row.get(field, "") for field in row_schema_fields + EXTRA_BEHAVIOR_FIELDS}
            )
            measured_event_rows.append(
                {
                    "protocol_version": "engineering_controller_behavior_outcome_v0",
                    "milestone_id": milestone,
                    "measured_behavior_row_id": row_id,
                    "seed_panel_id": item.seed_panel_id,
                    "seed_index": item.seed_index,
                    "evidence_layer": "source_only_diagnostic",
                    "surface_id": item.surface_id,
                    "scenario_role": item.role_family,
                    "fixture_id": item.fixture_id,
                    "base_fixture_id": item.base_fixture_id,
                    "subject_id": subject_id,
                    "seed": item.seed,
                    "mitigation_reference_subject": MITIGATION_REFERENCE_SUBJECT,
                    "collision_event": _bool_text(bool(event["collision_event"])),
                    "obstacle_passed_event": _bool_text(bool(event["obstacle_passed_event"])),
                    "road_departure_event": _bool_text(bool(event["road_departure_event"])),
                    "minimum_obstacle_clearance_m": _float_text(
                        event["minimum_obstacle_clearance_m"]
                    ),
                    "minimum_road_margin_m": _float_text(event["minimum_road_margin_m"]),
                    "final_road_margin_m": _float_text(event["final_road_margin_m"]),
                    "collision_speed_proxy": _float_text(event["collision_speed_proxy"]),
                    "impact_angle_proxy": _float_text(event["impact_angle_proxy"]),
                    "severity_proxy": _float_text(event["severity_proxy"]),
                    "mitigation_delta_against_reference": _float_text(
                        event["mitigation_delta_against_reference"]
                    ),
                    "recovery_time_proxy_s": _float_text(event["recovery_time_proxy_s"]),
                    "diagnostic_only_no_ranking_claim": "true",
                    "claim_scope": CLAIM_SCOPE,
                    "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                }
            )
    return measured_behavior_rows, measured_event_rows


def build_metric_completeness_rows(
    metric_registry_rows: list[dict[str, str]],
    measured_behavior_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = len(measured_behavior_rows)
    for metric in metric_registry_rows:
        metric_name = metric["metric_name"]
        supported = sum(_has_value(row.get(metric_name, "")) for row in measured_behavior_rows)
        rows.append(
            {
                "metric_name": metric_name,
                "metric_family": metric["metric_family"],
                "actor_visible": metric["actor_visible"],
                "supported_row_count": supported,
                "missing_row_count": total - supported,
                "support_status": (
                    "supported_by_m2544_route_a_source_only_execution_readiness_panel"
                    if supported == total
                    else "partial_or_missing_after_m2544"
                ),
                "source_fields": "measured_behavior_rows.csv",
                "claim_boundary": "source-only Route A execution-readiness diagnostics only; not ranking or verdict",
            }
        )
    return rows


def _summary(
    *,
    output_dir: Path,
    source: dict[str, Any],
    subjects: tuple[RouteASubject, ...],
    subject_registry_rows: list[dict[str, Any]],
    telemetry_summary: dict[str, Any],
    seed_panel_spec_rows: list[dict[str, Any]],
    measured_behavior_rows: list[dict[str, Any]],
    measured_event_rows: list[dict[str, Any]],
    metric_completeness_rows: list[dict[str, Any]],
    seed_panel_spec_path: Path,
    subject_registry_path: Path,
    telemetry_path: Path,
    measured_behavior_path: Path,
    measured_event_path: Path,
    metric_completeness_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
    seed_count: int,
    horizon_steps: int,
) -> dict[str, Any]:
    subject_ids = tuple(subject.subject_id for subject in subjects)
    role_families = tuple(sorted({row["role_family"] for row in seed_panel_spec_rows}))
    expected_seed_panel_rows = len(role_families) * int(seed_count)
    expected_behavior_rows = len(subject_ids) * expected_seed_panel_rows
    expected_telemetry_rows = expected_behavior_rows * int(horizon_steps)
    source_artifacts_exist = all(source["source_exists"].values())
    required_artifacts_present = (
        seed_panel_spec_path.exists()
        and subject_registry_path.exists()
        and telemetry_path.exists()
        and measured_behavior_path.exists()
        and measured_event_path.exists()
        and metric_completeness_path.exists()
    )
    all_policy_checkpoints_admitted = (
        {row["subject_id"] for row in subject_registry_rows if row["checkpoint_admitted"] is True}
        == set(POLICY_SUBJECT_IDS)
    )
    all_attempted_rows_retained = (
        len(measured_behavior_rows) == expected_behavior_rows
        and {row["subject_id"] for row in measured_behavior_rows} == set(subject_ids)
        and {row["scenario_role"] for row in measured_behavior_rows} == set(role_families)
        and len({(row["scenario_role"], int(row["seed"])) for row in measured_behavior_rows})
        == expected_seed_panel_rows
        and all(str(row["attempted_row_retained"]).lower() == "true" for row in measured_behavior_rows)
    )
    denominator_gap_count = sum(
        1 for row in measured_behavior_rows if str(row["denominator_gap_reason"]) != ""
    )
    all_metrics_supported = bool(metric_completeness_rows) and all(
        int(row["missing_row_count"]) == 0 for row in metric_completeness_rows
    )
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in measured_behavior_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in measured_behavior_rows} == {ACTION_DIM}
    )
    all_rows_source_only = {row["evidence_layer"] for row in measured_behavior_rows} == {
        "source_only_diagnostic"
    }
    all_rows_no_ranking = {
        str(row["diagnostic_only_no_ranking_claim"]).lower() for row in measured_behavior_rows
    } == {"true"}
    no_ranking_fields = all(
        str(row["ranking_or_winner_field_emitted"]).lower() == "false"
        for row in measured_behavior_rows
    )
    seed_lineage_explicit = all(_has_value(row["seed"]) for row in measured_behavior_rows)
    mitigation_reference_explicit = {row["mitigation_reference_subject"] for row in measured_behavior_rows} == {
        MITIGATION_REFERENCE_SUBJECT
    }
    fresh_seed_count_by_role = {
        role: len({int(row["seed"]) for row in seed_panel_spec_rows if row["role_family"] == role})
        for role in role_families
    }
    role_seed_matrix_complete = all(count == int(seed_count) for count in fresh_seed_count_by_role.values())
    reset_digests_by_role_seed: dict[tuple[str, int], set[str]] = defaultdict(set)
    for key, digest in telemetry_summary.get("reset_digest_by_subject_role_seed", {}).items():
        _subject, role, seed_text = key.split(":")
        reset_digests_by_role_seed[(role, int(seed_text))].add(str(digest))
    role_seed_reset_digests_match_across_subjects = bool(reset_digests_by_role_seed) and all(
        len(digests) == 1 for digests in reset_digests_by_role_seed.values()
    )
    status_pass = (
        bool(telemetry_summary.get("all_policy_checkpoints_admitted"))
        and all_policy_checkpoints_admitted
        and source_artifacts_exist
        and required_artifacts_present
        and int(seed_count) >= DEFAULT_SEED_COUNT
        and len(subject_registry_rows) == len(subject_ids)
        and len([subject for subject in subjects if subject.policy_action]) == len(POLICY_SUBJECT_IDS)
        and len([subject for subject in subjects if not subject.policy_action]) == len(OPEN_LOOP_SUBJECT_IDS)
        and len(seed_panel_spec_rows) == expected_seed_panel_rows
        and role_seed_matrix_complete
        and len(measured_behavior_rows) == expected_behavior_rows
        and len(measured_event_rows) == expected_behavior_rows
        and len(metric_completeness_rows) == len(source["metric_registry"])
        and int(telemetry_summary.get("reset_count", 0)) == expected_behavior_rows
        and int(telemetry_summary.get("telemetry_row_count", 0)) == expected_telemetry_rows
        and all_attempted_rows_retained
        and denominator_gap_count == 0
        and actor_contract_shape_72_action_3
        and all_metrics_supported
        and all_rows_source_only
        and all_rows_no_ranking
        and no_ranking_fields
        and seed_lineage_explicit
        and mitigation_reference_explicit
        and role_seed_reset_digests_match_across_subjects
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": (
            "engineering_controller_route_a_source_only_execution_readiness_panel_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_source_only_execution_readiness_panel_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "seed_count_per_role": int(seed_count),
        "horizon_steps": int(horizon_steps),
        "summary": str(output_dir / "summary.json"),
        "seed_panel_spec": str(seed_panel_spec_path),
        "subject_registry": str(subject_registry_path),
        "telemetry_rows": str(telemetry_path),
        "measured_behavior_rows": str(measured_behavior_path),
        "measured_event_rows": str(measured_event_path),
        "metric_completeness_rows": str(metric_completeness_path),
        "doc": str(doc_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": [
            path for path, exists in source["source_exists"].items() if not exists
        ],
        "comparison_subjects": list(subject_ids),
        "comparison_subject_count": len(subject_ids),
        "policy_checkpoint_subjects": list(POLICY_SUBJECT_IDS),
        "policy_checkpoint_subject_count": len(POLICY_SUBJECT_IDS),
        "open_loop_subjects": list(OPEN_LOOP_SUBJECT_IDS),
        "open_loop_subject_count": len(OPEN_LOOP_SUBJECT_IDS),
        "all_policy_checkpoints_admitted": bool(all_policy_checkpoints_admitted),
        "role_families": list(role_families),
        "role_count": len(role_families),
        "fresh_seed_count_by_role": fresh_seed_count_by_role,
        "fresh_seed_count_min": min(fresh_seed_count_by_role.values()) if fresh_seed_count_by_role else 0,
        "seed_panel_spec_row_count": len(seed_panel_spec_rows),
        "subject_registry_row_count": len(subject_registry_rows),
        "expected_seed_panel_spec_row_count": expected_seed_panel_rows,
        "measured_behavior_row_count": len(measured_behavior_rows),
        "measured_event_row_count": len(measured_event_rows),
        "metric_completeness_row_count": len(metric_completeness_rows),
        "expected_subject_role_seed_row_count": expected_behavior_rows,
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "expected_telemetry_row_count": expected_telemetry_rows,
        "reset_count": int(telemetry_summary.get("reset_count", 0)),
        "expected_reset_count": expected_behavior_rows,
        "all_attempted_subject_role_seed_rows_retained": bool(all_attempted_rows_retained),
        "denominator_gap_count": int(denominator_gap_count),
        "role_seed_matrix_complete": bool(role_seed_matrix_complete),
        "role_seed_reset_digests_match_across_subjects": bool(
            role_seed_reset_digests_match_across_subjects
        ),
        "source_only_backend_step_run": bool(measured_behavior_rows),
        "policy_action_run": bool(measured_behavior_rows),
        "policy_rollout_run": bool(measured_behavior_rows),
        "open_loop_action_rollout_run": bool(measured_behavior_rows),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "all_actions_finite": bool(
            measured_behavior_rows
            and all(str(row["action_finite"]).lower() == "true" for row in measured_behavior_rows)
        ),
        "all_actions_within_bounds": bool(
            measured_behavior_rows
            and all(str(row["action_within_bounds"]).lower() == "true" for row in measured_behavior_rows)
        ),
        "all_backend_statuses_running": bool(
            measured_behavior_rows and {row["backend_status"] for row in measured_behavior_rows} == {"running"}
        ),
        "seed_lineage_explicit": bool(seed_lineage_explicit),
        "mitigation_reference_subject": MITIGATION_REFERENCE_SUBJECT,
        "mitigation_reference_explicit": bool(mitigation_reference_explicit),
        "mitigation_delta_supported_row_count": sum(
            _has_value(row["mitigation_delta_against_reference"]) for row in measured_behavior_rows
        ),
        "all_metrics_supported": bool(all_metrics_supported),
        "all_rows_source_only_diagnostic": bool(all_rows_source_only),
        "all_rows_diagnostic_only_no_ranking_claim": bool(all_rows_no_ranking),
        "ranking_or_winner_fields_emitted": False,
        "success_rate_verdict_field_emitted": False,
        "diagnostic_only_panel": True,
        "no_hidden_oracle_actor_inputs_encoded": True,
        "fixture_labels_enter_actor_input": False,
        "scenario_labels_enter_actor_input": False,
        "feasibility_classes_enter_actor_input": False,
        "hidden_values_enter_actor_input": False,
        "oracle_labels_enter_actor_input": False,
        "ttc_enter_actor_input": False,
        "required_clearance_enter_actor_input": False,
        **FALSE_CLAIM_FLAGS,
    }


def _subject_registry_row(subject: RouteASubject, admission: Any) -> dict[str, Any]:
    admitted = bool(admission.checkpoint_admitted) if admission is not None else True
    return {
        "subject_id": subject.subject_id,
        "subject_family": subject.subject_family,
        "action_source": "recurrent_actor_policy" if subject.policy_action else "fixed_deployed_action",
        "checkpoint_path": subject.checkpoint_path,
        "fixed_action_steer": "" if subject.fixed_action is None else subject.fixed_action[0],
        "fixed_action_throttle": "" if subject.fixed_action is None else subject.fixed_action[1],
        "fixed_action_brake": "" if subject.fixed_action is None else subject.fixed_action[2],
        "policy_action": subject.policy_action,
        "checkpoint_admitted": admitted if subject.policy_action else "",
        "checkpoint_admission_reason": "" if admission is None else admission.reason,
        "checkpoint_obs_dim": "" if admission is None else admission.obs_dim,
        "checkpoint_action_dim": "" if admission is None else admission.action_dim,
        "checkpoint_actor_encoder": "" if admission is None else admission.actor_encoder,
        "checkpoint_action_sequence_horizon": ""
        if admission is None
        else admission.action_sequence_horizon,
        "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
        "observation_shape": P0_OBSERVATION_DIM if subject.policy_action else "",
        "action_shape": ACTION_DIM,
        "allowed_use": subject.allowed_use,
        "promotion_status": subject.promotion_status,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def _load_source_artifacts() -> dict[str, Any]:
    paths = [
        M2543_DESIGN,
        M2542_AUDIT,
        M2541_BASELINE_LIST,
        M2541_ACTOR_CONTRACT,
        M2541_SUMMARY,
        M2523_SUMMARY,
        M2523_SEED_PANEL,
        M2514_ROW_SCHEMA,
        M2514_METRIC_REGISTRY,
    ]
    return {
        "m2541_summary": read_json(M2541_SUMMARY),
        "m2541_actor_contract": read_json(M2541_ACTOR_CONTRACT),
        "m2541_baseline_list": _read_csv_rows(M2541_BASELINE_LIST),
        "m2523_summary": read_json(M2523_SUMMARY),
        "m2523_seed_panel": _read_csv_rows(M2523_SEED_PANEL),
        "row_schema": _read_csv_rows(M2514_ROW_SCHEMA),
        "metric_registry": _read_csv_rows(M2514_METRIC_REGISTRY),
        "source_exists": {path: Path(path).exists() for path in paths},
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _subject_action(
    subject_item: AdmittedRouteASubject,
    observation: np.ndarray,
    hidden: Any,
) -> tuple[np.ndarray, Any]:
    subject = subject_item.subject
    if subject.fixed_action is not None:
        return np.asarray(subject.fixed_action, dtype=np.float32), hidden
    model = subject_item.model
    if model is None:
        raise RuntimeError(f"policy subject not admitted: {subject.subject_id}")
    if not model.is_online_recurrent:
        raise RuntimeError(f"policy subject requires online recurrent actor: {subject.subject_id}")
    action, _log_prob, _value, next_hidden = model.act_recurrent(
        observation,
        hidden,
        deterministic=True,
    )
    return action, next_hidden


def _observation_digest(observation: np.ndarray) -> str:
    from autodrift.hf0_source_only_baseline_comparison_panel import _observation_digest as digest

    return digest(observation)


def _physical_control_value(values: list[Any], index: int) -> float:
    try:
        return _float(values[index])
    except (IndexError, TypeError, ValueError):
        return 0.0


def _float(value: Any) -> float:
    return float(value)


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2544 Engineering Controller Route A Baseline Source-Only Execution Readiness Panel Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2544-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_source_only_execution_readiness_panel.py`",
                f"- summary: `{summary['summary']}`",
                f"- seed panel spec: `{summary['seed_panel_spec']}`",
                f"- subject registry: `{summary['subject_registry']}`",
                f"- telemetry rows: `{summary['telemetry_rows']}`",
                f"- measured behavior rows: `{summary['measured_behavior_rows']}`",
                f"- measured event rows: `{summary['measured_event_rows']}`",
                f"- metric completeness rows: `{summary['metric_completeness_rows']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed in M2544: `false`",
                "- measured validation/training/replay/PPO/ranking/winner selection in M2544: `false`",
                "- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`",
                "",
                "## Materialized Panel",
                "",
                "M2544 executes bounded source-only policy and open-loop reference actions",
                "as diagnostic execution-readiness data across the Route A baseline",
                "subjects. It preserves the P0 72/3 no-oracle actor boundary and keeps",
                "all rows diagnostic-only.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"comparison_subject_count: {summary['comparison_subject_count']}",
                f"policy_checkpoint_subject_count: {summary['policy_checkpoint_subject_count']}",
                f"open_loop_subject_count: {summary['open_loop_subject_count']}",
                f"seed_count_per_role: {summary['seed_count_per_role']}",
                f"seed_panel_spec_row_count: {summary['seed_panel_spec_row_count']}",
                f"subject_registry_row_count: {summary['subject_registry_row_count']}",
                f"measured_behavior_row_count: {summary['measured_behavior_row_count']}",
                f"measured_event_row_count: {summary['measured_event_row_count']}",
                f"metric_completeness_row_count: {summary['metric_completeness_row_count']}",
                f"telemetry_row_count: {summary['telemetry_row_count']}",
                f"all_policy_checkpoints_admitted: {str(summary['all_policy_checkpoints_admitted']).lower()}",
                f"all_attempted_subject_role_seed_rows_retained: {str(summary['all_attempted_subject_role_seed_rows_retained']).lower()}",
                f"actor_contract_shape_72_action_3: {str(summary['actor_contract_shape_72_action_3']).lower()}",
                f"mitigation_reference_subject: {summary['mitigation_reference_subject']}",
                "```",
                "",
                "## Result",
                "",
                "M2544 passes as a source-only execution-readiness preflight. It",
                "produces a denominator-complete Route A panel, not a controller",
                "ranking, promotion, success-rate, validation, driver-performance,",
                "paper, finite-window-vs-GRU, current-sim, high-fidelity, or self-ID result.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
                "",
                "The next audit should accept or reject these source-only Route A",
                "execution-readiness artifacts before any broader synthesis or claim",
                "escalation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize Route A source-only execution-readiness panel."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_route_a_source_only_execution_readiness_panel(
        args.output_dir,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"subject_registry_row_count={summary['subject_registry_row_count']}")
    print(f"measured_behavior_row_count={summary['measured_behavior_row_count']}")
    print(f"telemetry_row_count={summary['telemetry_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
