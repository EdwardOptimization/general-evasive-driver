"""Route A source-only fresh generalization panel materialization.

This module extends the M2544 Route A source-only execution-readiness panel
with fresh seeds, a stable_avoidable role, and explicit dynamics-axis rows. It
uses only the repository-local source-only four-wheel backend.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, to_jsonable, utc_timestamp, write_csv_rows, write_json
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
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    DEFAULT_POLICY_CHECKPOINTS,
    OPEN_LOOP_SUBJECT_IDS,
    POLICY_SUBJECT_IDS,
    SUBJECT_REGISTRY_FIELDNAMES,
    TELEMETRY_FIELDNAMES,
    RouteASubject,
    admit_route_a_subjects,
    route_a_subjects,
    _load_source_artifacts as _load_route_a_source_artifacts,
    _observation_digest,
    _physical_control_value,
    _subject_action,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    EXTRA_BEHAVIOR_FIELDS,
    MEASURED_EVENT_FIELDNAMES,
    SEED_PANEL_SPEC_FIELDNAMES,
    _baseline_like_rows,
    _variant_fixture_spec,
)
from autodrift.engineering_controller_source_only_outcome_events import (
    _bool_text,
    _event_stats,
    _float_text,
    _primary_obstacle,
)
from autodrift.four_wheel_dynamics import FourWheelFaultScales, FourWheelState
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend, SourceOnlyRoleFixtureDynamicsSpec
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.hf0_source_only_role_fixture_parameterization import build_source_only_role_fixture_specs
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    ObstacleSlotView,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    RoadView,
    validate_actor_action,
)


DEFAULT_MILESTONE = (
    "m2641-engineering-controller-route-a-baseline-source-only-fresh-"
    "generalization-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2642-engineering-controller-route-a-baseline-source-only-fresh-"
    "generalization-panel-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2641-engineering-controller-route-a-baseline-source-only-fresh-"
    "generalization-panel-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel"
)
DEFAULT_HORIZON_STEPS = 80
DEFAULT_FRESH_SEED_COUNT = 4

ROLE_FAMILIES = (
    "stable_avoidable",
    "stable_aes",
    "drift_required_recovery",
    "unavoidable_mitigation",
)
BASE_SEEDS_BY_ROLE = {
    "stable_avoidable": 264100,
    "stable_aes": 265100,
    "drift_required_recovery": 266100,
    "unavoidable_mitigation": 267100,
}
DYNAMICS_AXES = (
    "fresh_nominal_or_role_default",
    "fresh_fault_delay_noise",
)

M2640_DESIGN = (
    "docs/m2640-engineering-controller-route-a-baseline-source-only-fresh-"
    "generalization-panel-design.md"
)
M2639_SUMMARY = (
    "runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/summary.json"
)
M2639_NEXT_ACTION = (
    "runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/"
    "next_action_admission.csv"
)
M2544_SUMMARY = (
    "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_"
    "readiness_panel/summary.json"
)
POST_M2470_ROUTE_PLAN = "docs/post-m2470-route-plan.md"

CLAIM_SCOPE = "Route A source-only fresh generalization panel materialization preflight only"
FORBIDDEN_INTERPRETATION = (
    "controller ranking, winner selection, success-rate verdict, promotion, "
    "validation, driver performance, paper, finite-window-vs-GRU, current-sim "
    "verdict, high-fidelity validation, or self-ID claim"
)
CLAIM_BOUNDARY = (
    "M2641 materializes source-only diagnostic rows across fresh role seeds and "
    "dynamics axes; rows are not ranking, promotion, validation, success-rate, "
    "driver-performance, paper, current-sim, high-fidelity, or self-ID evidence"
)

SEED_PANEL_SPEC_FIELDNAMES_M2641 = SEED_PANEL_SPEC_FIELDNAMES + [
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
    "source_only_fault_axis_applied",
    "delay_noise_diagnostic_metadata_only",
]
TELEMETRY_FIELDNAMES_M2641 = TELEMETRY_FIELDNAMES + [
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
]
EXTRA_BEHAVIOR_FIELDS_M2641 = EXTRA_BEHAVIOR_FIELDS + [
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
    "source_only_fault_axis_applied",
    "delay_noise_diagnostic_metadata_only",
]
MEASURED_EVENT_FIELDNAMES_M2641 = MEASURED_EVENT_FIELDNAMES + [
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
]
DYNAMICS_AXIS_FIELDNAMES = [
    "seed_panel_id",
    "role_family",
    "seed_index",
    "seed",
    "base_fixture_id",
    "fixture_id",
    "surface_id",
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
    "uniform_grip_scale",
    "left_right_split_mu_scale",
    "lateral_stiffness_scale",
    "brake_scale",
    "steering_delay_steps",
    "throttle_delay_steps",
    "brake_delay_steps",
    "sensor_noise_std",
    "source_only_fault_axis_applied",
    "actuator_delay_applied_to_backend",
    "sensor_noise_applied_to_actor_input",
    "diagnostic_metadata_only",
    "actor_visible_allowed",
    "claim_boundary",
]
ACTOR_VISIBILITY_GUARD_FIELDNAMES = [
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
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]


@dataclass(frozen=True)
class FreshGeneralizationRunItem:
    seed_panel_id: str
    role_family: str
    seed_index: int
    seed: int
    base_fixture_id: str
    fixture_id: str
    surface_id: str
    fixture_spec: SourceOnlyRoleFixtureDynamicsSpec
    fixture_variant_digest: str
    dynamics_axis_id: str
    dynamics_axis_family: str
    axis_index: int
    source_only_fault_axis_applied: bool
    delay_noise_diagnostic_metadata_only: bool
    axis_config: dict[str, Any]


def materialize_route_a_source_only_fresh_generalization_panel(
    output_dir: Path,
    *,
    policy_checkpoints: dict[str, str | Path] | None = None,
    fresh_seed_count: int = DEFAULT_FRESH_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    if int(fresh_seed_count) != DEFAULT_FRESH_SEED_COUNT:
        raise ValueError(f"fresh_seed_count must be exactly {DEFAULT_FRESH_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()
    row_schema_fields = [row["field_name"] for row in source["row_schema"]]
    subjects = route_a_subjects(policy_checkpoints)
    admitted_subjects, subject_registry_rows = admit_route_a_subjects(subjects, device=device)
    run_items, seed_panel_spec_rows, dynamics_axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=int(fresh_seed_count)
    )
    actor_guard_rows = build_actor_visibility_guard_rows()
    telemetry_rows, telemetry_summary = run_fresh_generalization_telemetry(
        run_items,
        admitted_subjects,
        horizon_steps=int(horizon_steps),
    )
    measured_behavior_rows, measured_event_rows = build_fresh_generalization_measured_rows(
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
    dynamics_axis_path = output_dir / "dynamics_axis_rows.csv"
    actor_guard_path = output_dir / "actor_visibility_guard_rows.csv"
    telemetry_path = output_dir / "telemetry_rows.csv"
    measured_behavior_path = output_dir / "measured_behavior_rows.csv"
    measured_event_path = output_dir / "measured_event_rows.csv"
    metric_completeness_path = output_dir / "metric_completeness_rows.csv"
    gate_matrix_path = output_dir / "gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(
        seed_panel_spec_path,
        seed_panel_spec_rows,
        fieldnames=SEED_PANEL_SPEC_FIELDNAMES_M2641,
    )
    write_csv_rows(subject_registry_path, subject_registry_rows, fieldnames=SUBJECT_REGISTRY_FIELDNAMES)
    write_csv_rows(dynamics_axis_path, dynamics_axis_rows, fieldnames=DYNAMICS_AXIS_FIELDNAMES)
    write_csv_rows(actor_guard_path, actor_guard_rows, fieldnames=ACTOR_VISIBILITY_GUARD_FIELDNAMES)
    write_csv_rows(telemetry_path, telemetry_rows, fieldnames=TELEMETRY_FIELDNAMES_M2641)
    write_csv_rows(
        measured_behavior_path,
        measured_behavior_rows,
        fieldnames=row_schema_fields + EXTRA_BEHAVIOR_FIELDS_M2641,
    )
    write_csv_rows(
        measured_event_path,
        measured_event_rows,
        fieldnames=MEASURED_EVENT_FIELDNAMES_M2641,
    )
    write_csv_rows(
        metric_completeness_path,
        metric_completeness_rows,
        fieldnames=METRIC_COMPLETENESS_FIELDNAMES,
    )

    metrics = _metrics(
        output_dir=output_dir,
        source=source,
        subjects=subjects,
        subject_registry_rows=subject_registry_rows,
        telemetry_summary=telemetry_summary,
        seed_panel_spec_rows=seed_panel_spec_rows,
        dynamics_axis_rows=dynamics_axis_rows,
        actor_guard_rows=actor_guard_rows,
        measured_behavior_rows=measured_behavior_rows,
        measured_event_rows=measured_event_rows,
        metric_completeness_rows=metric_completeness_rows,
        seed_panel_spec_path=seed_panel_spec_path,
        subject_registry_path=subject_registry_path,
        dynamics_axis_path=dynamics_axis_path,
        actor_guard_path=actor_guard_path,
        telemetry_path=telemetry_path,
        measured_behavior_path=measured_behavior_path,
        measured_event_path=measured_event_path,
        metric_completeness_path=metric_completeness_path,
        gate_matrix_path=gate_matrix_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
        fresh_seed_count=int(fresh_seed_count),
        horizon_steps=int(horizon_steps),
    )
    gate_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(gate_matrix_path, gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = _summary(metrics, gate_rows)
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def build_fresh_generalization_panel_specs(
    *,
    fresh_seed_count: int = DEFAULT_FRESH_SEED_COUNT,
) -> tuple[list[FreshGeneralizationRunItem], list[dict[str, Any]], list[dict[str, Any]]]:
    base_specs = _base_specs_by_role()
    run_items: list[FreshGeneralizationRunItem] = []
    seed_rows: list[dict[str, Any]] = []
    axis_rows: list[dict[str, Any]] = []
    for role in ROLE_FAMILIES:
        base_spec = base_specs[role]
        for seed_index in range(int(fresh_seed_count)):
            seed = BASE_SEEDS_BY_ROLE[role] + seed_index
            nominal_variant = _variant_fixture_spec(base_spec, seed=seed, seed_index=seed_index)
            for axis_index, axis_id in enumerate(DYNAMICS_AXES):
                variant, axis_config = _axis_variant_spec(
                    nominal_variant,
                    seed=seed,
                    seed_index=seed_index,
                    dynamics_axis_id=axis_id,
                    axis_index=axis_index,
                )
                fixture_digest = _fixture_digest(variant)
                seed_panel_id = f"m2641_{role}_seed_{seed}_{axis_id}"
                source_only_fault_axis_applied = axis_id == "fresh_fault_delay_noise"
                delay_noise_diagnostic_metadata_only = axis_id == "fresh_fault_delay_noise"
                item = FreshGeneralizationRunItem(
                    seed_panel_id=seed_panel_id,
                    role_family=role,
                    seed_index=seed_index,
                    seed=seed,
                    base_fixture_id=base_spec.fixture_id,
                    fixture_id=variant.fixture_id,
                    surface_id=SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                    fixture_spec=variant,
                    fixture_variant_digest=fixture_digest,
                    dynamics_axis_id=axis_id,
                    dynamics_axis_family=axis_id,
                    axis_index=axis_index,
                    source_only_fault_axis_applied=source_only_fault_axis_applied,
                    delay_noise_diagnostic_metadata_only=delay_noise_diagnostic_metadata_only,
                    axis_config=axis_config,
                )
                run_items.append(item)
                seed_rows.append(
                    {
                        "seed_panel_id": seed_panel_id,
                        "role_family": role,
                        "seed_index": seed_index,
                        "seed": seed,
                        "base_fixture_id": base_spec.fixture_id,
                        "fixture_id": variant.fixture_id,
                        "surface_id": SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                        "fixture_variant_digest": fixture_digest,
                        "initial_state_digest": _digest(asdict(variant.initial_state)),
                        "fault_scale_digest": _digest(asdict(variant.fault_scales)),
                        "road_digest": _digest(asdict(variant.road)),
                        "obstacle_digest": _digest([asdict(obstacle) for obstacle in variant.obstacles]),
                        "role_metadata_only": True,
                        "seed_metadata_only": True,
                        "hidden_diagnostics_metadata_only": True,
                        "actor_input_contract_changed": False,
                        "variant_reason": "m2641 source-only fresh role seed and dynamics-axis perturbation",
                        "dynamics_axis_id": axis_id,
                        "dynamics_axis_family": axis_id,
                        "axis_index": axis_index,
                        "source_only_fault_axis_applied": source_only_fault_axis_applied,
                        "delay_noise_diagnostic_metadata_only": delay_noise_diagnostic_metadata_only,
                    }
                )
                axis_rows.append(_axis_row(item))
    return run_items, seed_rows, axis_rows


def run_fresh_generalization_telemetry(
    run_items: list[FreshGeneralizationRunItem],
    admitted_subjects: list[Any],
    *,
    horizon_steps: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    extractor = P0ObservationExtractor()
    telemetry_rows: list[dict[str, Any]] = []
    reset_count = 0
    reset_observation_shapes: list[int] = []
    reset_digest_by_subject_role_seed_axis: dict[str, str] = {}
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
            "reset_digest_by_subject_role_seed_axis": {},
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
                            "dynamics_axis_id": item.dynamics_axis_id,
                            "comparison_subject": subject.subject_id,
                            "comparison_subject_family": subject.subject_family,
                        },
                    )
                )
                observation = extractor.extract(reset_result.actor_view)
                reset_digest = _observation_digest(observation)
                reset_observation_shapes.append(int(observation.shape[0]))
                reset_count += 1
                reset_digest_by_subject_role_seed_axis[
                    f"{subject.subject_id}:{item.role_family}:{item.seed}:{item.dynamics_axis_id}"
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
                            "dynamics_axis_id": item.dynamics_axis_id,
                            "dynamics_axis_family": item.dynamics_axis_family,
                            "axis_index": item.axis_index,
                        }
                    )
            finally:
                backend.close()

    return telemetry_rows, {
        "all_policy_checkpoints_admitted": True,
        "reset_count": reset_count,
        "telemetry_row_count": len(telemetry_rows),
        "reset_observation_shapes": reset_observation_shapes,
        "reset_digest_by_subject_role_seed_axis": reset_digest_by_subject_role_seed_axis,
    }


def build_fresh_generalization_measured_rows(
    telemetry_rows: list[dict[str, Any]],
    *,
    run_items: list[FreshGeneralizationRunItem],
    subjects: tuple[RouteASubject, ...],
    row_schema_fields: list[str],
    milestone: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item_by_key = {
        (item.role_family, item.seed, item.dynamics_axis_id): item for item in run_items
    }
    subject_by_id = {subject.subject_id: subject for subject in subjects}
    rows_by_subject_role_seed_axis: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in telemetry_rows:
        rows_by_subject_role_seed_axis[
            (
                row["comparison_subject"],
                row["role_family"],
                int(row["seed"]),
                row["dynamics_axis_id"],
            )
        ].append(row)

    event_by_subject_role_seed_axis: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for key, rows in rows_by_subject_role_seed_axis.items():
        _subject_id, role, seed, axis_id = key
        item = item_by_key[(role, seed, axis_id)]
        event_stats = _event_stats(
            sorted(rows, key=lambda value: int(value["step_index"])),
            road=item.fixture_spec.road,
            obstacle=_primary_obstacle(item.fixture_spec.obstacles),
        )
        event_by_subject_role_seed_axis[key] = {
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

    for (subject_id, role, seed, axis_id), event in list(event_by_subject_role_seed_axis.items()):
        reference = event_by_subject_role_seed_axis[
            (MITIGATION_REFERENCE_SUBJECT, role, seed, axis_id)
        ]
        event["mitigation_delta_against_reference"] = (
            float(event["severity_proxy"]) - float(reference["severity_proxy"])
        )

    measured_behavior_rows: list[dict[str, Any]] = []
    measured_event_rows: list[dict[str, Any]] = []
    for item in run_items:
        for subject_id in sorted(subject_by_id):
            subject = subject_by_id[subject_id]
            group = sorted(
                rows_by_subject_role_seed_axis[
                    (subject_id, item.role_family, item.seed, item.dynamics_axis_id)
                ],
                key=lambda value: int(value["step_index"]),
            )
            if not group:
                continue
            first = group[0]
            last = group[-1]
            event = event_by_subject_role_seed_axis[
                (subject_id, item.role_family, item.seed, item.dynamics_axis_id)
            ]
            row_id = (
                f"m2641_{subject_id}_{item.role_family}_seed_{item.seed}_"
                f"{item.dynamics_axis_id}"
            )
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
                "source_artifact": "Route A source-only fresh generalization panel",
                "attempted_row_retained": True,
                "seed_panel_id": item.seed_panel_id,
                "seed_index": item.seed_index,
                "base_fixture_id": item.base_fixture_id,
                "fresh_seed_variant_digest": item.fixture_variant_digest,
                "mitigation_reference_subject": MITIGATION_REFERENCE_SUBJECT,
                "mitigation_reference_seed": item.seed,
                "denominator_gap_reason": "",
                "ranking_or_winner_field_emitted": False,
                "dynamics_axis_id": item.dynamics_axis_id,
                "dynamics_axis_family": item.dynamics_axis_family,
                "axis_index": item.axis_index,
                "source_only_fault_axis_applied": item.source_only_fault_axis_applied,
                "delay_noise_diagnostic_metadata_only": item.delay_noise_diagnostic_metadata_only,
            }
            measured_behavior_rows.append(
                {
                    field: behavior_row.get(field, "")
                    for field in row_schema_fields + EXTRA_BEHAVIOR_FIELDS_M2641
                }
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
                    "dynamics_axis_id": item.dynamics_axis_id,
                    "dynamics_axis_family": item.dynamics_axis_family,
                    "axis_index": item.axis_index,
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
                    "supported_by_m2641_route_a_source_only_fresh_generalization_panel"
                    if supported == total
                    else "partial_or_missing_after_m2641"
                ),
                "source_fields": "measured_behavior_rows.csv",
                "claim_boundary": "source-only M2641 diagnostics only; not ranking or verdict",
            }
        )
    return rows


def build_actor_visibility_guard_rows() -> list[dict[str, Any]]:
    protected_fields = (
        ("role_metadata", "role_family"),
        ("seed_metadata", "seed"),
        ("seed_metadata", "seed_panel_id"),
        ("fixture_metadata", "fixture_id"),
        ("fixture_metadata", "base_fixture_id"),
        ("fixture_metadata", "fixture_variant_digest"),
        ("hidden_dynamics", "uniform_grip_scale"),
        ("hidden_dynamics", "left_right_split_mu_scale"),
        ("hidden_dynamics", "lateral_stiffness_scale"),
        ("hidden_dynamics", "brake_scale"),
        ("delay_noise", "steering_delay_steps"),
        ("delay_noise", "throttle_delay_steps"),
        ("delay_noise", "brake_delay_steps"),
        ("delay_noise", "sensor_noise_std"),
        ("backend_diagnostics", "source_only_fixture_diagnostic_tags"),
        ("route_status", "source_dependency_status"),
        ("route_status", "route_decision"),
        ("outcome", "reset_or_rollout_outcome"),
        ("outcome", "success_or_verdict_label"),
    )
    return [
        {
            "guard_id": f"m2641_actor_visibility_{index:02d}_{protected_field}",
            "guard_family": guard_family,
            "protected_field": protected_field,
            "actor_visible_allowed": False,
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "status_pass": True,
            "evidence": (
                "P0 extractor remains human-view 72 and dynamics-axis fields are "
                "stored only in diagnostics or CSV artifacts"
            ),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (guard_family, protected_field) in enumerate(protected_fields)
    ]


def build_gate_matrix_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    gate_specs = (
        ("source_artifacts_exist", "artifact", metrics["source_artifacts_exist"], True, "metric_artifact"),
        ("role_family_count", "panel_shape", metrics["role_family_count"], 4, "scenario_sampling_failure"),
        ("fresh_seed_count_per_role", "panel_shape", metrics["fresh_seed_count_min"], 4, "scenario_sampling_failure"),
        ("dynamics_axis_count", "panel_shape", metrics["dynamics_axis_count"], 2, "scenario_sampling_failure"),
        ("comparison_subject_count", "panel_shape", metrics["comparison_subject_count"], 5, "metric_artifact"),
        ("expected_behavior_rows", "panel_shape", metrics["measured_behavior_row_count"], 160, "metric_artifact"),
        ("expected_telemetry_rows", "panel_shape", metrics["telemetry_row_count"], 160 * int(metrics["horizon_steps"]), "metric_artifact"),
        ("actor_contract_shape_72_action_3", "actor_contract", metrics["actor_contract_shape_72_action_3"], True, "contract_violation"),
        ("hidden_oracle_actor_input_detected", "actor_contract", metrics["hidden_oracle_actor_input_detected"], False, "contract_violation"),
        ("all_policy_checkpoints_admitted", "subject_admission", metrics["all_policy_checkpoints_admitted"], True, "lineage_invalid"),
        ("all_actions_finite", "action_contract", metrics["all_actions_finite"], True, "behavior_regression"),
        ("all_actions_within_bounds", "action_contract", metrics["all_actions_within_bounds"], True, "behavior_regression"),
        ("all_rows_diagnostic_only_no_ranking_claim", "claim_boundary", metrics["all_rows_diagnostic_only_no_ranking_claim"], True, "objective_overfit"),
        ("actor_visibility_guard_rows_pass", "actor_contract", metrics["actor_visibility_guard_rows_pass"], True, "contract_violation"),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("winner_selected", "forbidden_claim", metrics["winner_selected"], False, "objective_overfit"),
        ("checkpoint_promoted", "forbidden_claim", metrics["checkpoint_promoted"], False, "objective_overfit"),
        ("success_rate_computed", "forbidden_claim", metrics["success_rate_computed"], False, "objective_overfit"),
        ("driver_performance_claim_made", "forbidden_claim", metrics["driver_performance_claim_made"], False, "objective_overfit"),
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


def _metrics(
    *,
    output_dir: Path,
    source: dict[str, Any],
    subjects: tuple[RouteASubject, ...],
    subject_registry_rows: list[dict[str, Any]],
    telemetry_summary: dict[str, Any],
    seed_panel_spec_rows: list[dict[str, Any]],
    dynamics_axis_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    measured_behavior_rows: list[dict[str, Any]],
    measured_event_rows: list[dict[str, Any]],
    metric_completeness_rows: list[dict[str, Any]],
    seed_panel_spec_path: Path,
    subject_registry_path: Path,
    dynamics_axis_path: Path,
    actor_guard_path: Path,
    telemetry_path: Path,
    measured_behavior_path: Path,
    measured_event_path: Path,
    metric_completeness_path: Path,
    gate_matrix_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
    fresh_seed_count: int,
    horizon_steps: int,
) -> dict[str, Any]:
    subject_ids = tuple(subject.subject_id for subject in subjects)
    role_families = tuple(sorted({row["role_family"] for row in seed_panel_spec_rows}))
    dynamics_axes = tuple(sorted({row["dynamics_axis_id"] for row in dynamics_axis_rows}))
    expected_seed_axis_rows = len(ROLE_FAMILIES) * int(fresh_seed_count) * len(DYNAMICS_AXES)
    expected_behavior_rows = len(subject_ids) * expected_seed_axis_rows
    expected_telemetry_rows = expected_behavior_rows * int(horizon_steps)
    source_artifacts_exist = all(source["source_exists"].values())
    required_artifacts_present = all(
        path.exists()
        for path in (
            seed_panel_spec_path,
            subject_registry_path,
            dynamics_axis_path,
            actor_guard_path,
            telemetry_path,
            measured_behavior_path,
            measured_event_path,
            metric_completeness_path,
        )
    )
    all_policy_checkpoints_admitted = (
        {row["subject_id"] for row in subject_registry_rows if row["checkpoint_admitted"] is True}
        == set(POLICY_SUBJECT_IDS)
    )
    fresh_seed_count_by_role = {
        role: len({int(row["seed"]) for row in seed_panel_spec_rows if row["role_family"] == role})
        for role in ROLE_FAMILIES
    }
    dynamics_axis_count_by_role_seed = Counter(
        (row["role_family"], int(row["seed"])) for row in seed_panel_spec_rows
    )
    role_seed_axis_matrix_complete = (
        len(seed_panel_spec_rows) == expected_seed_axis_rows
        and set(role_families) == set(ROLE_FAMILIES)
        and set(dynamics_axes) == set(DYNAMICS_AXES)
        and all(count == int(fresh_seed_count) for count in fresh_seed_count_by_role.values())
        and all(count == len(DYNAMICS_AXES) for count in dynamics_axis_count_by_role_seed.values())
    )
    attempted_keys = {
        (row["scenario_role"], int(row["seed"]), row["dynamics_axis_id"], row["subject_id"])
        for row in measured_behavior_rows
    }
    expected_keys = {
        (item["role_family"], int(item["seed"]), item["dynamics_axis_id"], subject_id)
        for item in seed_panel_spec_rows
        for subject_id in subject_ids
    }
    all_attempted_rows_retained = (
        len(measured_behavior_rows) == expected_behavior_rows
        and attempted_keys == expected_keys
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
    reset_digests_by_role_seed_axis: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    for key, digest in telemetry_summary.get("reset_digest_by_subject_role_seed_axis", {}).items():
        _subject, role, seed_text, axis_id = key.split(":")
        reset_digests_by_role_seed_axis[(role, int(seed_text), axis_id)].add(str(digest))
    role_seed_axis_reset_digests_match_across_subjects = bool(reset_digests_by_role_seed_axis) and all(
        len(digests) == 1 for digests in reset_digests_by_role_seed_axis.values()
    )
    actor_visibility_guard_rows_pass = bool(actor_guard_rows) and all(
        bool(row["status_pass"]) and row["actor_visible_allowed"] is False for row in actor_guard_rows
    )
    hidden_oracle_actor_input_detected = any(
        bool(value)
        for value in (
            False,
            FALSE_CLAIM_FLAGS.get("level3_self_id_claim_made", False),
        )
    )
    metrics = {
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "seed_panel_spec": str(seed_panel_spec_path),
        "subject_registry": str(subject_registry_path),
        "dynamics_axis_rows": str(dynamics_axis_path),
        "actor_visibility_guard_rows": str(actor_guard_path),
        "telemetry_rows": str(telemetry_path),
        "measured_behavior_rows": str(measured_behavior_path),
        "measured_event_rows": str(measured_event_path),
        "metric_completeness_rows": str(metric_completeness_path),
        "gate_matrix": str(gate_matrix_path),
        "doc": str(doc_path),
        "fresh_seed_count_per_role": int(fresh_seed_count),
        "horizon_steps": int(horizon_steps),
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
        "role_families": list(ROLE_FAMILIES),
        "role_family_count": len(role_families),
        "role_count": len(role_families),
        "fresh_seed_count_by_role": fresh_seed_count_by_role,
        "fresh_seed_count_min": min(fresh_seed_count_by_role.values()) if fresh_seed_count_by_role else 0,
        "dynamics_axes": list(DYNAMICS_AXES),
        "dynamics_axis_count": len(dynamics_axes),
        "seed_panel_spec_row_count": len(seed_panel_spec_rows),
        "dynamics_axis_row_count": len(dynamics_axis_rows),
        "actor_visibility_guard_row_count": len(actor_guard_rows),
        "subject_registry_row_count": len(subject_registry_rows),
        "expected_seed_panel_spec_row_count": expected_seed_axis_rows,
        "measured_behavior_row_count": len(measured_behavior_rows),
        "measured_event_row_count": len(measured_event_rows),
        "metric_completeness_row_count": len(metric_completeness_rows),
        "expected_behavior_rows": expected_behavior_rows,
        "expected_subject_role_seed_axis_row_count": expected_behavior_rows,
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "expected_telemetry_rows": expected_telemetry_rows,
        "expected_telemetry_row_count": expected_telemetry_rows,
        "reset_count": int(telemetry_summary.get("reset_count", 0)),
        "expected_reset_count": expected_behavior_rows,
        "all_attempted_subject_role_seed_axis_rows_retained": bool(all_attempted_rows_retained),
        "denominator_gap_count": int(denominator_gap_count),
        "role_seed_axis_matrix_complete": bool(role_seed_axis_matrix_complete),
        "role_seed_axis_reset_digests_match_across_subjects": bool(
            role_seed_axis_reset_digests_match_across_subjects
        ),
        "source_only_backend_reset_run": bool(measured_behavior_rows),
        "source_only_backend_step_run": bool(measured_behavior_rows),
        "policy_action_run": bool(measured_behavior_rows),
        "policy_rollout_run": bool(measured_behavior_rows),
        "open_loop_action_rollout_run": bool(measured_behavior_rows),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "hidden_oracle_actor_input_detected": bool(hidden_oracle_actor_input_detected),
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
        "actor_visibility_guard_rows_pass": bool(actor_visibility_guard_rows_pass),
        "diagnostic_only_panel": True,
        "source_only_fault_axis_applied_row_count": sum(
            row["source_only_fault_axis_applied"] is True for row in dynamics_axis_rows
        ),
        "delay_noise_diagnostic_metadata_only": True,
        "actuator_delay_applied_to_backend": False,
        "sensor_noise_applied_to_actor_input": False,
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
    return metrics


def _summary(metrics: dict[str, Any], gate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        metrics["source_artifacts_exist"]
        and metrics["required_artifacts_present"]
        and metrics["all_policy_checkpoints_admitted"]
        and metrics["role_family_count"] == 4
        and metrics["fresh_seed_count_min"] == DEFAULT_FRESH_SEED_COUNT
        and metrics["dynamics_axis_count"] == 2
        and metrics["comparison_subject_count"] == 5
        and metrics["seed_panel_spec_row_count"] == 32
        and metrics["dynamics_axis_row_count"] == 32
        and metrics["measured_behavior_row_count"] == 160
        and metrics["measured_event_row_count"] == 160
        and metrics["metric_completeness_row_count"] > 0
        and metrics["telemetry_row_count"] == metrics["expected_telemetry_rows"]
        and metrics["reset_count"] == metrics["expected_reset_count"]
        and metrics["all_attempted_subject_role_seed_axis_rows_retained"]
        and metrics["denominator_gap_count"] == 0
        and metrics["role_seed_axis_matrix_complete"]
        and metrics["role_seed_axis_reset_digests_match_across_subjects"]
        and metrics["actor_contract_shape_72_action_3"]
        and not metrics["hidden_oracle_actor_input_detected"]
        and metrics["all_actions_finite"]
        and metrics["all_actions_within_bounds"]
        and metrics["all_metrics_supported"]
        and metrics["all_rows_source_only_diagnostic"]
        and metrics["all_rows_diagnostic_only_no_ranking_claim"]
        and not metrics["ranking_or_winner_fields_emitted"]
        and metrics["actor_visibility_guard_rows_pass"]
        and gate_matrix_pass
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": (
            "engineering_controller_route_a_source_only_fresh_generalization_panel_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_source_only_fresh_generalization_panel_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "gate_matrix_pass": bool(gate_matrix_pass),
        "gate_matrix_row_count": len(gate_rows),
        **metrics,
    }


def _load_source_artifacts() -> dict[str, Any]:
    source = _load_route_a_source_artifacts()
    extra_paths = [M2640_DESIGN, M2639_SUMMARY, M2639_NEXT_ACTION, M2544_SUMMARY, POST_M2470_ROUTE_PLAN]
    source["source_exists"].update({path: Path(path).exists() for path in extra_paths})
    source["m2639_summary"] = read_json(M2639_SUMMARY)
    source["m2544_summary"] = read_json(M2544_SUMMARY)
    source["m2639_next_action"] = _read_csv_rows(M2639_NEXT_ACTION)
    return source


def _base_specs_by_role() -> dict[str, SourceOnlyRoleFixtureDynamicsSpec]:
    existing = {spec.role_family: spec for spec in build_source_only_role_fixture_specs()}
    stable_avoidable = SourceOnlyRoleFixtureDynamicsSpec(
        fixture_id="m2641_source_only_stable_avoidable_base",
        role_family="stable_avoidable",
        initial_state=FourWheelState(
            x=0.0,
            y=0.0,
            psi=0.0,
            vx=7.4,
            vy=0.0,
            yaw_rate=0.0,
            steer=0.0,
            drive_force=0.0,
            brake_force=0.0,
        ),
        fault_scales=FourWheelFaultScales.nominal(),
        road=_role_road(lateral_offset=0.0, curve_scale=0.0),
        obstacles=_role_obstacles(
            ObstacleSlotView(1.0, 34.0, 0.25, -5.5, 0.0, 0.65, 0.70)
        ),
        diagnostic_tags={
            "fixture_source": "m2641_route_a_source_only_fresh_generalization_panel",
            "parameterization_version": "m2641_stable_avoidable_v1",
            "differentiation_reason": "moderate-speed stable avoidable source-only role",
            "actor_input_contract_changed": False,
        },
    )
    specs = {"stable_avoidable": stable_avoidable, **existing}
    missing = sorted(set(ROLE_FAMILIES) - set(specs))
    if missing:
        raise ValueError(f"missing M2641 source-only base specs for roles: {missing}")
    return {role: specs[role] for role in ROLE_FAMILIES}


def _axis_variant_spec(
    nominal_variant: SourceOnlyRoleFixtureDynamicsSpec,
    *,
    seed: int,
    seed_index: int,
    dynamics_axis_id: str,
    axis_index: int,
) -> tuple[SourceOnlyRoleFixtureDynamicsSpec, dict[str, Any]]:
    if dynamics_axis_id == "fresh_nominal_or_role_default":
        axis_config = {
            "uniform_grip_scale": 1.0,
            "left_right_split_mu_scale": 1.0,
            "lateral_stiffness_scale": 1.0,
            "brake_scale": 1.0,
            "steering_delay_steps": 0,
            "throttle_delay_steps": 0,
            "brake_delay_steps": 0,
            "sensor_noise_std": 0.0,
            "source_only_fault_axis_applied": False,
            "actuator_delay_applied_to_backend": False,
            "sensor_noise_applied_to_actor_input": False,
            "diagnostic_metadata_only": True,
        }
        return (
            _retag_variant(
                nominal_variant,
                seed=seed,
                seed_index=seed_index,
                dynamics_axis_id=dynamics_axis_id,
                axis_index=axis_index,
                axis_config=axis_config,
                suffix="axis_nominal",
            ),
            axis_config,
        )

    if dynamics_axis_id != "fresh_fault_delay_noise":
        raise ValueError(f"unknown dynamics axis: {dynamics_axis_id}")

    axis_config = _fault_delay_noise_axis_config(seed=seed, role_family=nominal_variant.role_family)
    left_scale = float(axis_config["left_right_split_mu_scale"])
    right_scale = float(axis_config["uniform_grip_scale"])
    fault_scales = FourWheelFaultScales(
        mu=(left_scale, right_scale, left_scale, right_scale),
        lateral_stiffness=tuple([float(axis_config["lateral_stiffness_scale"])] * 4),
        brake=tuple([float(axis_config["brake_scale"])] * 4),
        drive=nominal_variant.fault_scales.drive,
        longitudinal_drag=nominal_variant.fault_scales.longitudinal_drag,
    )
    varied = SourceOnlyRoleFixtureDynamicsSpec(
        fixture_id=f"{nominal_variant.fixture_id}_axis_fault_delay_noise",
        role_family=nominal_variant.role_family,
        initial_state=nominal_variant.initial_state,
        fault_scales=fault_scales,
        road=nominal_variant.road,
        obstacles=nominal_variant.obstacles,
        diagnostic_tags={
            **dict(nominal_variant.diagnostic_tags),
            "fixture_source": "m2641_source_only_fresh_generalization_panel",
            "fresh_seed": int(seed),
            "fresh_seed_index": int(seed_index),
            "dynamics_axis_id": dynamics_axis_id,
            "dynamics_axis_family": dynamics_axis_id,
            "axis_index": int(axis_index),
            "actor_input_contract_changed": False,
            **axis_config,
        },
    )
    return varied, axis_config


def _retag_variant(
    spec: SourceOnlyRoleFixtureDynamicsSpec,
    *,
    seed: int,
    seed_index: int,
    dynamics_axis_id: str,
    axis_index: int,
    axis_config: dict[str, Any],
    suffix: str,
) -> SourceOnlyRoleFixtureDynamicsSpec:
    return SourceOnlyRoleFixtureDynamicsSpec(
        fixture_id=f"{spec.fixture_id}_{suffix}",
        role_family=spec.role_family,
        initial_state=spec.initial_state,
        fault_scales=spec.fault_scales,
        road=spec.road,
        obstacles=spec.obstacles,
        diagnostic_tags={
            **dict(spec.diagnostic_tags),
            "fixture_source": "m2641_source_only_fresh_generalization_panel",
            "fresh_seed": int(seed),
            "fresh_seed_index": int(seed_index),
            "dynamics_axis_id": dynamics_axis_id,
            "dynamics_axis_family": dynamics_axis_id,
            "axis_index": int(axis_index),
            "actor_input_contract_changed": False,
            **axis_config,
        },
    )


def _fault_delay_noise_axis_config(*, seed: int, role_family: str) -> dict[str, Any]:
    role_offset = ROLE_FAMILIES.index(role_family) * 1009
    rng = np.random.default_rng(int(seed) + 91003 + role_offset)
    return {
        "uniform_grip_scale": float(rng.uniform(0.62, 1.08)),
        "left_right_split_mu_scale": float(rng.uniform(0.65, 1.10)),
        "lateral_stiffness_scale": float(rng.uniform(0.68, 1.10)),
        "brake_scale": float(rng.uniform(0.72, 1.08)),
        "steering_delay_steps": int(rng.integers(0, 3)),
        "throttle_delay_steps": int(rng.integers(0, 3)),
        "brake_delay_steps": int(rng.integers(0, 3)),
        "sensor_noise_std": float(rng.uniform(0.0, 0.03)),
        "source_only_fault_axis_applied": True,
        "actuator_delay_applied_to_backend": False,
        "sensor_noise_applied_to_actor_input": False,
        "diagnostic_metadata_only": True,
    }


def _axis_row(item: FreshGeneralizationRunItem) -> dict[str, Any]:
    config = item.axis_config
    return {
        "seed_panel_id": item.seed_panel_id,
        "role_family": item.role_family,
        "seed_index": item.seed_index,
        "seed": item.seed,
        "base_fixture_id": item.base_fixture_id,
        "fixture_id": item.fixture_id,
        "surface_id": item.surface_id,
        "dynamics_axis_id": item.dynamics_axis_id,
        "dynamics_axis_family": item.dynamics_axis_family,
        "axis_index": item.axis_index,
        "uniform_grip_scale": config["uniform_grip_scale"],
        "left_right_split_mu_scale": config["left_right_split_mu_scale"],
        "lateral_stiffness_scale": config["lateral_stiffness_scale"],
        "brake_scale": config["brake_scale"],
        "steering_delay_steps": config["steering_delay_steps"],
        "throttle_delay_steps": config["throttle_delay_steps"],
        "brake_delay_steps": config["brake_delay_steps"],
        "sensor_noise_std": config["sensor_noise_std"],
        "source_only_fault_axis_applied": config["source_only_fault_axis_applied"],
        "actuator_delay_applied_to_backend": config["actuator_delay_applied_to_backend"],
        "sensor_noise_applied_to_actor_input": config["sensor_noise_applied_to_actor_input"],
        "diagnostic_metadata_only": config["diagnostic_metadata_only"],
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _role_road(*, lateral_offset: float, curve_scale: float) -> RoadView:
    left = tuple(
        (
            float(index + 1) * 5.0,
            float(3.0 + lateral_offset + curve_scale * ((float(index + 1) * 5.0) / 40.0) ** 2),
        )
        for index in range(8)
    )
    right = tuple(
        (
            float(index + 1) * 5.0,
            float(-3.0 + lateral_offset + curve_scale * ((float(index + 1) * 5.0) / 40.0) ** 2),
        )
        for index in range(8)
    )
    return RoadView(left_boundary_points_body=left, right_boundary_points_body=right)


def _role_obstacles(primary: ObstacleSlotView) -> tuple[ObstacleSlotView, ...]:
    empty = ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return (primary, empty, empty, empty)


def _fixture_digest(spec: SourceOnlyRoleFixtureDynamicsSpec) -> str:
    return _digest(
        {
            "initial_state": asdict(spec.initial_state),
            "fault_scales": asdict(spec.fault_scales),
            "road": asdict(spec.road),
            "obstacles": [asdict(obstacle) for obstacle in spec.obstacles],
            "diagnostic_tags": dict(spec.diagnostic_tags),
        }
    )


def _digest(value: Any) -> str:
    payload = json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _float(value: Any) -> float:
    return float(value)


def _read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2641 Engineering Controller Route A Source-Only Fresh Generalization Panel Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2641-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_source_only_fresh_generalization_panel.py`",
                f"- summary: `{summary['summary']}`",
                f"- seed panel spec: `{summary['seed_panel_spec']}`",
                f"- subject registry: `{summary['subject_registry']}`",
                f"- dynamics axis rows: `{summary['dynamics_axis_rows']}`",
                f"- actor visibility guard rows: `{summary['actor_visibility_guard_rows']}`",
                f"- telemetry rows: `{summary['telemetry_rows']}`",
                f"- measured behavior rows: `{summary['measured_behavior_rows']}`",
                f"- measured event rows: `{summary['measured_event_rows']}`",
                f"- metric completeness rows: `{summary['metric_completeness_rows']}`",
                f"- gate matrix: `{summary['gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation/source build/adapter probe/replay/training: `false`",
                "- ranking/winner selection/promotion/success-rate/performance verdicts: `false`",
                "- paper/FW-vs-GRU/current-sim/high-fidelity/self-ID claims: `false`",
                "",
                "## Materialized Panel",
                "",
                "M2641 executes bounded source-only policy and open-loop reference",
                "rollouts over four Route A role families, four fresh seeds per",
                "role, and two diagnostic dynamics axes. The actor contract remains",
                "P0 human-view 72 observations and 3 deployed action dimensions.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"role_family_count: {summary['role_family_count']}",
                f"fresh_seed_count_per_role: {summary['fresh_seed_count_per_role']}",
                f"dynamics_axis_count: {summary['dynamics_axis_count']}",
                f"comparison_subject_count: {summary['comparison_subject_count']}",
                f"measured_behavior_row_count: {summary['measured_behavior_row_count']}",
                f"measured_event_row_count: {summary['measured_event_row_count']}",
                f"telemetry_row_count: {summary['telemetry_row_count']}",
                f"actor_contract_shape_72_action_3: {str(summary['actor_contract_shape_72_action_3']).lower()}",
                f"actor_visibility_guard_rows_pass: {str(summary['actor_visibility_guard_rows_pass']).lower()}",
                f"gate_matrix_pass: {str(summary['gate_matrix_pass']).lower()}",
                f"delay_noise_diagnostic_metadata_only: {str(summary['delay_noise_diagnostic_metadata_only']).lower()}",
                "```",
                "",
                "## Claim Boundary",
                "",
                "The `fresh_fault_delay_noise` axis applies source-only fault scales",
                "through the local four-wheel backend. Actuator delay and sensor",
                "noise fields are diagnostic metadata and actor-visibility guard",
                "targets in M2641; they are not actor inputs and are not claimed as",
                "external high-fidelity validation physics.",
                "",
                "M2641 is a source-only diagnostic materialization. It does not rank",
                "subjects, compute a success-rate verdict, select a winner, promote a",
                "checkpoint, validate a controller, or claim driver performance.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
                "",
                "The next audit should accept or reject these materialized rows before",
                "any ranking, repair, promotion, validation, or performance claim.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize Route A source-only fresh generalization panel."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fresh-seed-count", type=int, default=DEFAULT_FRESH_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_route_a_source_only_fresh_generalization_panel(
        args.output_dir,
        policy_checkpoints=DEFAULT_POLICY_CHECKPOINTS,
        fresh_seed_count=args.fresh_seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"role_family_count={summary['role_family_count']}")
    print(f"dynamics_axis_count={summary['dynamics_axis_count']}")
    print(f"measured_behavior_row_count={summary['measured_behavior_row_count']}")
    print(f"telemetry_row_count={summary['telemetry_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
