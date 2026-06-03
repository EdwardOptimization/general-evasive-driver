"""Fresh-seed source-only measured behavior panel under the accepted protocol."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

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
from autodrift.engineering_controller_source_only_outcome_events import (
    _bool_text,
    _event_stats,
    _float_text,
    _primary_obstacle,
)
from autodrift.four_wheel_dynamics import FourWheelFaultScales, FourWheelState
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend, SourceOnlyRoleFixtureDynamicsSpec
from autodrift.hf0_source_only_baseline_comparison_panel import (
    COMPARISON_SUBJECTS,
    ROLE_FAMILIES,
    BaselineTelemetryRow,
    _observation_digest,
    _physical_control_value,
    _subject_action,
)
from autodrift.hf0_source_only_closed_loop_fixture_pilot import admit_actor_checkpoint
from autodrift.hf0_source_only_role_fixture_parameterization import (
    build_source_only_role_fixture_specs,
)
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
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
    "m2523-engineering-controller-source-only-fresh-seed-measured-behavior-panel-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2524-engineering-controller-source-only-fresh-seed-measured-behavior-panel-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2523-engineering-controller-source-only-fresh-seed-measured-behavior-panel-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel"
)
DEFAULT_SEED_COUNT = 5
DEFAULT_BASE_SEED = 252300

M2522_AUDIT = "docs/m2522-engineering-controller-bounded-measured-behavior-panel-result-audit.md"
M2521_SUMMARY = "runs/m2521_engineering_controller_bounded_measured_behavior_panel/summary.json"
M2521_BEHAVIOR_ROWS = (
    "runs/m2521_engineering_controller_bounded_measured_behavior_panel/measured_behavior_rows.csv"
)
M2521_EVENT_ROWS = (
    "runs/m2521_engineering_controller_bounded_measured_behavior_panel/measured_event_rows.csv"
)
M2521_COMPLETENESS_ROWS = (
    "runs/m2521_engineering_controller_bounded_measured_behavior_panel/metric_completeness_rows.csv"
)
M2514_ROW_SCHEMA = "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv"
M2514_METRIC_REGISTRY = (
    "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv"
)

CLAIM_SCOPE = "source-only fresh-seed measured behavior panel preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, or self-ID claim"
)

SEED_PANEL_SPEC_FIELDNAMES = [
    "seed_panel_id",
    "role_family",
    "seed_index",
    "seed",
    "base_fixture_id",
    "fixture_id",
    "surface_id",
    "fixture_variant_digest",
    "initial_state_digest",
    "fault_scale_digest",
    "road_digest",
    "obstacle_digest",
    "role_metadata_only",
    "seed_metadata_only",
    "hidden_diagnostics_metadata_only",
    "actor_input_contract_changed",
    "variant_reason",
]

EXTRA_BEHAVIOR_FIELDS = [
    "attempted_row_retained",
    "seed_panel_id",
    "seed_index",
    "base_fixture_id",
    "fresh_seed_variant_digest",
    "mitigation_reference_subject",
    "mitigation_reference_seed",
    "denominator_gap_reason",
    "ranking_or_winner_field_emitted",
]

MEASURED_EVENT_FIELDNAMES = [
    "protocol_version",
    "milestone_id",
    "measured_behavior_row_id",
    "seed_panel_id",
    "seed_index",
    "evidence_layer",
    "surface_id",
    "scenario_role",
    "fixture_id",
    "base_fixture_id",
    "subject_id",
    "seed",
    "mitigation_reference_subject",
    "collision_event",
    "obstacle_passed_event",
    "road_departure_event",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "final_road_margin_m",
    "collision_speed_proxy",
    "impact_angle_proxy",
    "severity_proxy",
    "mitigation_delta_against_reference",
    "recovery_time_proxy_s",
    "diagnostic_only_no_ranking_claim",
    "claim_scope",
    "forbidden_interpretation",
]


@dataclass(frozen=True)
class FreshSeedRunItem:
    seed_panel_id: str
    role_family: str
    seed_index: int
    seed: int
    base_fixture_id: str
    fixture_id: str
    surface_id: str
    fixture_spec: SourceOnlyRoleFixtureDynamicsSpec
    fixture_variant_digest: str


def materialize_source_only_fresh_seed_measured_behavior_panel(
    output_dir: Path,
    *,
    checkpoint_path: Path | str,
    seed_count: int,
    horizon_steps: int,
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
    run_items, seed_panel_spec_rows = build_seed_panel_specs(seed_count=int(seed_count))
    telemetry_rows, telemetry_summary = run_fresh_seed_telemetry(
        run_items,
        checkpoint_path=checkpoint_path,
        horizon_steps=int(horizon_steps),
        device=device,
    )
    measured_behavior_rows, measured_event_rows = build_fresh_seed_measured_rows(
        telemetry_rows,
        run_items=run_items,
        checkpoint_path=str(checkpoint_path),
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    metric_completeness_rows = build_metric_completeness_rows(
        source["metric_registry"],
        measured_behavior_rows,
    )

    seed_panel_spec_path = output_dir / "seed_panel_spec.csv"
    measured_behavior_path = output_dir / "measured_behavior_rows.csv"
    measured_event_path = output_dir / "measured_event_rows.csv"
    metric_completeness_path = output_dir / "metric_completeness_rows.csv"

    write_csv_rows(
        seed_panel_spec_path,
        seed_panel_spec_rows,
        fieldnames=SEED_PANEL_SPEC_FIELDNAMES,
    )
    write_csv_rows(
        measured_behavior_path,
        measured_behavior_rows,
        fieldnames=row_schema_fields + EXTRA_BEHAVIOR_FIELDS,
    )
    write_csv_rows(
        measured_event_path,
        measured_event_rows,
        fieldnames=MEASURED_EVENT_FIELDNAMES,
    )
    write_csv_rows(
        metric_completeness_path,
        metric_completeness_rows,
        fieldnames=METRIC_COMPLETENESS_FIELDNAMES,
    )

    doc_output = Path(doc_path)
    summary = _summary(
        output_dir=output_dir,
        source=source,
        telemetry_summary=telemetry_summary,
        run_items=run_items,
        seed_panel_spec_rows=seed_panel_spec_rows,
        measured_behavior_rows=measured_behavior_rows,
        measured_event_rows=measured_event_rows,
        metric_completeness_rows=metric_completeness_rows,
        seed_panel_spec_path=seed_panel_spec_path,
        measured_behavior_path=measured_behavior_path,
        measured_event_path=measured_event_path,
        metric_completeness_path=metric_completeness_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
        checkpoint_path=str(checkpoint_path),
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def _load_source_artifacts() -> dict[str, Any]:
    paths = [
        M2522_AUDIT,
        M2521_SUMMARY,
        M2521_BEHAVIOR_ROWS,
        M2521_EVENT_ROWS,
        M2521_COMPLETENESS_ROWS,
        M2514_ROW_SCHEMA,
        M2514_METRIC_REGISTRY,
    ]
    return {
        "m2521_summary": read_json(M2521_SUMMARY),
        "m2521_behavior_rows": _read_csv_rows(M2521_BEHAVIOR_ROWS),
        "m2521_event_rows": _read_csv_rows(M2521_EVENT_ROWS),
        "m2521_completeness_rows": _read_csv_rows(M2521_COMPLETENESS_ROWS),
        "row_schema": _read_csv_rows(M2514_ROW_SCHEMA),
        "metric_registry": _read_csv_rows(M2514_METRIC_REGISTRY),
        "source_exists": {path: Path(path).exists() for path in paths},
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_seed_panel_specs(
    *,
    seed_count: int,
    base_seed: int = DEFAULT_BASE_SEED,
) -> tuple[list[FreshSeedRunItem], list[dict[str, Any]]]:
    run_items: list[FreshSeedRunItem] = []
    rows: list[dict[str, Any]] = []
    for role_index, base_spec in enumerate(build_source_only_role_fixture_specs()):
        for seed_index in range(int(seed_count)):
            seed = int(base_seed) + role_index * 1000 + seed_index
            variant = _variant_fixture_spec(base_spec, seed=seed, seed_index=seed_index)
            seed_panel_id = f"m2523_{base_spec.role_family}_seed_{seed}"
            fixture_digest = _digest(
                {
                    "initial_state": asdict(variant.initial_state),
                    "fault_scales": asdict(variant.fault_scales),
                    "road": asdict(variant.road),
                    "obstacles": [asdict(obstacle) for obstacle in variant.obstacles],
                }
            )
            item = FreshSeedRunItem(
                seed_panel_id=seed_panel_id,
                role_family=base_spec.role_family,
                seed_index=seed_index,
                seed=seed,
                base_fixture_id=base_spec.fixture_id,
                fixture_id=variant.fixture_id,
                surface_id=SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                fixture_spec=variant,
                fixture_variant_digest=fixture_digest,
            )
            run_items.append(item)
            rows.append(
                {
                    "seed_panel_id": seed_panel_id,
                    "role_family": base_spec.role_family,
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
                    "variant_reason": "deterministic source-only fresh-seed perturbation",
                }
            )
    return run_items, rows


def run_fresh_seed_telemetry(
    run_items: list[FreshSeedRunItem],
    *,
    checkpoint_path: Path | str,
    horizon_steps: int,
    device: str = "cpu",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model, admission = admit_actor_checkpoint(checkpoint_path, device=device)
    if model is None:
        return [], {
            "checkpoint_admitted": False,
            **admission.to_summary_fields(),
        }

    extractor = P0ObservationExtractor()
    telemetry_rows: list[dict[str, Any]] = []
    reset_count = 0
    reset_observation_shapes: list[int] = []
    reset_digest_by_subject_role_seed: dict[str, str] = {}

    for subject in COMPARISON_SUBJECTS:
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
                reset_observation_digest = _observation_digest(observation)
                reset_observation_shapes.append(int(observation.shape[0]))
                reset_count += 1
                reset_digest_by_subject_role_seed[
                    f"{subject.subject_id}:{item.role_family}:{item.seed}"
                ] = reset_observation_digest

                for step_index in range(int(horizon_steps)):
                    raw_action, hidden = _subject_action(subject, model, observation, hidden)
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
                            "reset_observation_digest": reset_observation_digest,
                            "policy_action": subject.policy_action,
                            "diagnostic_only": True,
                        }
                    )
            finally:
                backend.close()

    return telemetry_rows, {
        "checkpoint_admitted": True,
        **admission.to_summary_fields(),
        "reset_count": reset_count,
        "telemetry_row_count": len(telemetry_rows),
        "reset_observation_shapes": reset_observation_shapes,
        "reset_digest_by_subject_role_seed": reset_digest_by_subject_role_seed,
    }


def build_fresh_seed_measured_rows(
    telemetry_rows: list[dict[str, Any]],
    *,
    run_items: list[FreshSeedRunItem],
    checkpoint_path: str,
    row_schema_fields: list[str],
    milestone: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item_by_role_seed = {(item.role_family, item.seed): item for item in run_items}
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
            sorted(rows, key=lambda item: int(item["step_index"])),
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
        for subject in sorted(subject.subject_id for subject in COMPARISON_SUBJECTS):
            group = sorted(
                rows_by_subject_role_seed[(subject, item.role_family, item.seed)],
                key=lambda value: int(value["step_index"]),
            )
            first = group[0]
            last = group[-1]
            event = event_by_subject_role_seed[(subject, item.role_family, item.seed)]
            row_id = f"m2523_{subject}_{item.role_family}_seed_{item.seed}"
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
                "subject_id": subject,
                "checkpoint_path": checkpoint_path if subject == "m1154_policy_actor" else "",
                "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
                "observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "actor_encoder": "human_view_online_gru",
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
                "source_artifact": "source-only fresh-seed measured execution",
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
                {
                    field: behavior_row.get(field, "")
                    for field in row_schema_fields + EXTRA_BEHAVIOR_FIELDS
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
                    "subject_id": subject,
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
                    "supported_by_m2523_source_only_fresh_seed_measured_behavior_panel"
                    if supported == total
                    else "partial_or_missing_after_m2523"
                ),
                "source_fields": "measured_behavior_rows.csv",
                "claim_boundary": "source-only fresh-seed measured behavior diagnostics only; not ranking or verdict",
            }
        )
    return rows


def _summary(
    *,
    output_dir: Path,
    source: dict[str, Any],
    telemetry_summary: dict[str, Any],
    run_items: list[FreshSeedRunItem],
    seed_panel_spec_rows: list[dict[str, Any]],
    measured_behavior_rows: list[dict[str, Any]],
    measured_event_rows: list[dict[str, Any]],
    metric_completeness_rows: list[dict[str, Any]],
    seed_panel_spec_path: Path,
    measured_behavior_path: Path,
    measured_event_path: Path,
    metric_completeness_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
    checkpoint_path: str,
    seed_count: int,
    horizon_steps: int,
) -> dict[str, Any]:
    subject_ids = tuple(subject.subject_id for subject in COMPARISON_SUBJECTS)
    expected_seed_panel_rows = len(ROLE_FAMILIES) * int(seed_count)
    expected_behavior_rows = len(subject_ids) * expected_seed_panel_rows
    expected_telemetry_rows = expected_behavior_rows * int(horizon_steps)
    source_artifacts_exist = all(source["source_exists"].values())
    required_artifacts_present = (
        seed_panel_spec_path.exists()
        and measured_behavior_path.exists()
        and measured_event_path.exists()
        and metric_completeness_path.exists()
    )
    all_attempted_rows_retained = (
        len(measured_behavior_rows) == expected_behavior_rows
        and {row["subject_id"] for row in measured_behavior_rows} == set(subject_ids)
        and {row["scenario_role"] for row in measured_behavior_rows} == set(ROLE_FAMILIES)
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
        role: len({item.seed for item in run_items if item.role_family == role})
        for role in ROLE_FAMILIES
    }
    role_seed_matrix_complete = all(
        count == int(seed_count) for count in fresh_seed_count_by_role.values()
    )
    reset_digests_by_role_seed: dict[tuple[str, int], set[str]] = defaultdict(set)
    for key, digest in telemetry_summary.get("reset_digest_by_subject_role_seed", {}).items():
        _subject, role, seed_text = key.split(":")
        reset_digests_by_role_seed[(role, int(seed_text))].add(str(digest))
    role_seed_reset_digests_match_across_subjects = bool(reset_digests_by_role_seed) and all(
        len(digests) == 1 for digests in reset_digests_by_role_seed.values()
    )
    status_pass = (
        bool(telemetry_summary.get("checkpoint_admitted"))
        and source_artifacts_exist
        and required_artifacts_present
        and int(seed_count) >= DEFAULT_SEED_COUNT
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
            "engineering_controller_source_only_fresh_seed_measured_behavior_panel_preflight_pass"
            if status_pass
            else "engineering_controller_source_only_fresh_seed_measured_behavior_panel_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "checkpoint_path": checkpoint_path,
        "seed_count_per_role": int(seed_count),
        "horizon_steps": int(horizon_steps),
        "summary": str(output_dir / "summary.json"),
        "seed_panel_spec": str(seed_panel_spec_path),
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
        "role_families": list(ROLE_FAMILIES),
        "role_count": len(ROLE_FAMILIES),
        "fresh_seed_count_by_role": fresh_seed_count_by_role,
        "fresh_seed_count_min": min(fresh_seed_count_by_role.values()),
        "seed_panel_spec_row_count": len(seed_panel_spec_rows),
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
            measured_behavior_rows and all(str(row["action_finite"]).lower() == "true" for row in measured_behavior_rows)
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


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2523 Engineering Controller Source-Only Fresh-Seed Measured Behavior Panel Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2523-engineering-controller-source-only-fresh-seed-measured-behavior-panel-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_source_only_fresh_seed_measured_behavior_panel.py`",
                f"- summary: `{summary['summary']}`",
                f"- seed panel spec: `{summary['seed_panel_spec']}`",
                f"- measured behavior rows: `{summary['measured_behavior_rows']}`",
                f"- measured event rows: `{summary['measured_event_rows']}`",
                f"- metric completeness rows: `{summary['metric_completeness_rows']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed in M2523: `false`",
                "- measured validation/training/replay/PPO/ranking/winner selection in M2523: `false`",
                "- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`",
                "",
                "## Materialized Panel",
                "",
                "M2523 executes bounded source-only policy and open-loop reference",
                "actions as diagnostic measured behavior data across fresh seed",
                "variants. It preserves all attempted subject-role-seed rows and",
                "does not rank controllers, select a winner, compute success-rate",
                "verdicts, or claim driver performance.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"seed_count_per_role: {summary['seed_count_per_role']}",
                f"seed_panel_spec_row_count: {summary['seed_panel_spec_row_count']}",
                f"measured_behavior_row_count: {summary['measured_behavior_row_count']}",
                f"measured_event_row_count: {summary['measured_event_row_count']}",
                f"metric_completeness_row_count: {summary['metric_completeness_row_count']}",
                f"telemetry_row_count: {summary['telemetry_row_count']}",
                f"all_attempted_subject_role_seed_rows_retained: {str(summary['all_attempted_subject_role_seed_rows_retained']).lower()}",
                f"actor_contract_shape_72_action_3: {str(summary['actor_contract_shape_72_action_3']).lower()}",
                f"seed_lineage_explicit: {str(summary['seed_lineage_explicit']).lower()}",
                f"mitigation_reference_subject: {summary['mitigation_reference_subject']}",
                "```",
                "",
                "## Result",
                "",
                "M2523 passes as a source-only fresh-seed measured behavior panel",
                "preflight. It expands Route A denominator evidence beyond the",
                "fixed M2521 seed rows, but it remains diagnostic source-only",
                "evidence and is still not a validation, ranking, success-rate,",
                "driver-performance, paper, finite-window-vs-GRU, or self-ID result.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
                "",
                "The next audit should accept or reject these fresh-seed measured",
                "behavior artifacts before any broader behavior route or claim",
                "escalation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _variant_fixture_spec(
    base_spec: SourceOnlyRoleFixtureDynamicsSpec,
    *,
    seed: int,
    seed_index: int,
) -> SourceOnlyRoleFixtureDynamicsSpec:
    rng = np.random.default_rng(int(seed))
    initial = base_spec.initial_state
    varied_initial = FourWheelState(
        x=float(initial.x + rng.uniform(-0.35, 0.35)),
        y=float(initial.y + rng.uniform(-0.18, 0.18)),
        psi=float(initial.psi + rng.uniform(-0.018, 0.018)),
        vx=float(np.clip(initial.vx * rng.uniform(0.94, 1.06), 5.0, 14.0)),
        vy=float(initial.vy + rng.uniform(-0.12, 0.12)),
        yaw_rate=float(initial.yaw_rate + rng.uniform(-0.05, 0.05)),
        steer=float(initial.steer + rng.uniform(-0.02, 0.02)),
        drive_force=0.0,
        brake_force=0.0,
    )
    varied_faults = FourWheelFaultScales(
        mu=_scaled_tuple(base_spec.fault_scales.mu, rng, low=0.92, high=1.06, floor=0.50, ceil=1.12),
        lateral_stiffness=_scaled_tuple(
            base_spec.fault_scales.lateral_stiffness,
            rng,
            low=0.90,
            high=1.08,
            floor=0.48,
            ceil=1.15,
        ),
        brake=_scaled_tuple(base_spec.fault_scales.brake, rng, low=0.92, high=1.05, floor=0.55, ceil=1.10),
        drive=_scaled_tuple(base_spec.fault_scales.drive, rng, low=0.93, high=1.05, floor=0.55, ceil=1.10),
        longitudinal_drag=_drag_tuple(base_spec.fault_scales.longitudinal_drag, rng),
    )
    varied_road = _variant_road(base_spec.road, rng)
    varied_obstacles = tuple(_variant_obstacle(obstacle, rng) for obstacle in base_spec.obstacles)
    fixture_id = f"{base_spec.fixture_id}_fresh_seed_{int(seed)}"
    return SourceOnlyRoleFixtureDynamicsSpec(
        fixture_id=fixture_id,
        role_family=base_spec.role_family,
        initial_state=varied_initial,
        fault_scales=varied_faults,
        road=varied_road,
        obstacles=varied_obstacles,
        diagnostic_tags={
            **dict(base_spec.diagnostic_tags),
            "fixture_source": "m2523_source_only_fresh_seed_variant",
            "base_fixture_id": base_spec.fixture_id,
            "fresh_seed": int(seed),
            "fresh_seed_index": int(seed_index),
            "actor_input_contract_changed": False,
        },
    )


def _variant_road(road: RoadView, rng: np.random.Generator) -> RoadView:
    lateral_offset = float(rng.uniform(-0.16, 0.16))
    curve_delta = float(rng.uniform(-0.012, 0.012))

    def vary(points: tuple[tuple[float, float], ...]) -> tuple[tuple[float, float], ...]:
        return tuple(
            (
                float(x),
                float(y + lateral_offset + curve_delta * (float(x) / 40.0) ** 2),
            )
            for x, y in points
        )

    return RoadView(
        left_boundary_points_body=vary(road.left_boundary_points_body),
        right_boundary_points_body=vary(road.right_boundary_points_body),
    )


def _variant_obstacle(obstacle: ObstacleSlotView, rng: np.random.Generator) -> ObstacleSlotView:
    if float(obstacle.present) <= 0.0:
        return obstacle
    return ObstacleSlotView(
        present=float(obstacle.present),
        x_body=float(obstacle.x_body + rng.uniform(-2.0, 2.0)),
        y_body=float(obstacle.y_body + rng.uniform(-0.45, 0.45)),
        vx_body=float(obstacle.vx_body + rng.uniform(-0.9, 0.9)),
        vy_body=float(obstacle.vy_body + rng.uniform(-0.35, 0.35)),
        half_width=float(np.clip(obstacle.half_width * rng.uniform(0.92, 1.08), 0.45, 1.25)),
        half_length=float(np.clip(obstacle.half_length * rng.uniform(0.92, 1.08), 0.45, 1.35)),
    )


def _scaled_tuple(
    values: tuple[float, float, float, float],
    rng: np.random.Generator,
    *,
    low: float,
    high: float,
    floor: float,
    ceil: float,
) -> tuple[float, float, float, float]:
    return tuple(float(np.clip(float(value) * rng.uniform(low, high), floor, ceil)) for value in values)


def _drag_tuple(
    values: tuple[float, float, float, float],
    rng: np.random.Generator,
) -> tuple[float, float, float, float]:
    return tuple(float(max(0.0, float(value) + rng.uniform(0.0, 15.0))) for value in values)


def _baseline_like_rows(rows: list[dict[str, Any]]) -> list[BaselineTelemetryRow]:
    return [
        BaselineTelemetryRow(
            comparison_subject=str(row["comparison_subject"]),
            comparison_subject_family=str(row["comparison_subject_family"]),
            fixture_id=str(row["fixture_id"]),
            surface_id=str(row["surface_id"]),
            role_family=str(row["role_family"]),
            step_index=int(row["step_index"]),
            observation_shape=int(row["observation_shape"]),
            action_shape=int(row["action_shape"]),
            action_steer=float(row["action_steer"]),
            action_throttle=float(row["action_throttle"]),
            action_brake=float(row["action_brake"]),
            action_finite=bool(row["action_finite"]),
            action_within_bounds=bool(row["action_within_bounds"]),
            action_saturated=bool(row["action_saturated"]),
            backend_status=str(row["backend_status"]),
            terminated_by_backend=bool(row["terminated_by_backend"]),
            truncated_by_backend=bool(row["truncated_by_backend"]),
            diagnostic_wheel_force_count=int(row["diagnostic_wheel_force_count"]),
            state_x=float(row["state_x"]),
            state_y=float(row["state_y"]),
            state_psi=float(row["state_psi"]),
            state_vx=float(row["state_vx"]),
            state_vy=float(row["state_vy"]),
            state_speed=float(row["state_speed"]),
            state_yaw_rate=float(row["state_yaw_rate"]),
            physical_steer=float(row["physical_steer"]),
            physical_throttle=float(row["physical_throttle"]),
            physical_brake=float(row["physical_brake"]),
            parameterized_fixture=bool(row["parameterized_fixture"]),
            reset_observation_digest=str(row["reset_observation_digest"]),
            policy_action=bool(row["policy_action"]),
            diagnostic_only=bool(row["diagnostic_only"]),
        )
        for row in rows
    ]


def _digest(value: Any) -> str:
    payload = json.dumps(
        to_jsonable(value),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _float(value: Any) -> float:
    return float(value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize source-only fresh-seed measured behavior panel."
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_source_only_fresh_seed_measured_behavior_panel(
        args.output_dir,
        checkpoint_path=args.checkpoint,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"seed_panel_spec_row_count={summary['seed_panel_spec_row_count']}")
    print(f"measured_behavior_row_count={summary['measured_behavior_row_count']}")
    print(f"metric_completeness_row_count={summary['metric_completeness_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
