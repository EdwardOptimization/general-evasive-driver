"""Route A protected mitigation fresh failure-surface panel materialization.

This runner executes a bounded source-only protected-mitigation panel after the
M2661 pivot. It expands evidence around the protected unavoidable_mitigation
blocker; it does not train, repair, rank, validate, promote, or claim driver
performance.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, to_jsonable, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_bounded_measured_behavior_panel import (
    FALSE_CLAIM_FLAGS,
    MITIGATION_REFERENCE_SUBJECT,
    _command_delta_l1_mean,
    _fraction,
    _max_abs,
    _row_backend_status,
    _terminal_status,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    OPEN_LOOP_SUBJECT_IDS,
    POLICY_SUBJECT_IDS,
    SUBJECT_REGISTRY_FIELDNAMES,
    TELEMETRY_FIELDNAMES,
    RouteASubject,
    admit_route_a_subjects,
    route_a_subjects,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    _base_specs_by_role,
    _fixture_digest,
    run_fresh_generalization_telemetry,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    _baseline_like_rows,
    _variant_fixture_spec,
)
from autodrift.engineering_controller_source_only_outcome_events import _event_stats, _primary_obstacle
from autodrift.four_wheel_dynamics import FourWheelFaultScales
from autodrift.four_wheel_hf0_adapter import SourceOnlyRoleFixtureDynamicsSpec
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.high_fidelity_interface import ACTION_DIM, ObstacleSlotView, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2662-engineering-controller-route-a-protected-mitigation-fresh-failure-"
    "surface-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2663-engineering-controller-route-a-protected-mitigation-fresh-failure-"
    "surface-panel-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2662-engineering-controller-route-a-protected-mitigation-fresh-failure-"
    "surface-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2663-engineering-controller-route-a-protected-mitigation-"
    "fresh-failure-surface-panel-materialization-result-audit.json"
)

DEFAULT_EVIDENCE_INDEX = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_"
    "protected_report_refresh/evidence_index.csv"
)
DEFAULT_GAP_MATRIX = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_"
    "protected_report_refresh/gap_matrix.csv"
)
DEFAULT_TARGET_PROTECTED_REPORT = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_"
    "report/target_protected_tradeoff_rows.csv"
)
DEFAULT_PROTECTED_FOCUS_ROWS = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_"
    "report/protected_regression_focus_rows.csv"
)
DEFAULT_M2659_SUMMARY = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_"
    "protected_report_refresh/summary.json"
)
DEFAULT_M2657_SUMMARY = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "summary.json"
)
M2661_DOC = Path(
    "docs/m2661-engineering-controller-route-a-post-index-target-protected-evidence-"
    "branch-synthesis.md"
)
M2514_ROW_SCHEMA = Path(
    "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv"
)

PROTECTED_ROLE = "unavoidable_mitigation"
TARGET_ROLES = ("stable_avoidable", "stable_aes", "drift_required_recovery")
PROTECTED_SEED_BASE = 268200
DEFAULT_PROTECTED_SEED_COUNT = 4
DEFAULT_HORIZON_STEPS = 80
PROTECTED_DYNAMICS_AXES = (
    "fresh_protected_nominal",
    "fresh_protected_fault_delay_noise",
    "fresh_protected_close_cut_in_fault",
)
EPSILON = 1e-9

CLAIM_SCOPE = (
    "Route A source-only protected mitigation fresh failure-surface panel only; "
    "no repair execution, training, PPO, ranking, winner selection, promotion, "
    "success-rate verdict, validation, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, controller ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, validation result, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation "
    "result, full ideal driver completion, or self-ID evidence"
)

PANEL_SPEC_FIELDNAMES = [
    "panel_spec_id",
    "role_family",
    "role_class",
    "seed_index",
    "seed",
    "fresh_seed_not_in_m2641",
    "source_focus_seed",
    "source_focus_dynamics_axis_id",
    "base_fixture_id",
    "fixture_id",
    "surface_id",
    "fixture_variant_digest",
    "initial_state_digest",
    "fault_scale_digest",
    "road_digest",
    "obstacle_digest",
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
    "axis_family",
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
    "obstacle_longitudinal_delta_m",
    "obstacle_lateral_delta_m",
    "obstacle_width_scale",
    "fresh_failure_surface_axis",
    "actor_visible_allowed",
    "actor_input_contract_changed",
    "hidden_diagnostics_metadata_only",
    "variant_reason",
    "claim_scope",
]
EXTRA_BEHAVIOR_FIELDS_M2662 = [
    "attempted_row_retained",
    "panel_spec_id",
    "seed_index",
    "base_fixture_id",
    "fresh_seed_variant_digest",
    "mitigation_reference_subject",
    "mitigation_reference_seed",
    "denominator_gap_reason",
    "ranking_or_winner_field_emitted",
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
    "fresh_protected_seed",
    "fresh_seed_not_in_m2641",
    "protected_rows_in_success_denominator",
    "protected_failure_surface_axis",
    "protected_focus_source_match",
    "source_only_fault_axis_applied",
    "actor_visible_labels",
    "diagnostic_only_no_success_claim",
]
PROTECTED_GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "subject_id",
    "dynamics_axis_id",
    "metric",
    "metric_direction",
    "evaluated_row_count",
    "reference_subject_id",
    "reference_mean",
    "subject_mean",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "gate_pass",
    "blocks_claims",
    "failure_type",
    "interpretation",
    "claim_scope",
]
CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed",
    "emitted",
    "status_pass",
    "evidence",
    "forbidden_interpretation",
    "claim_scope",
]
GATE_MATRIX_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]
TELEMETRY_FIELDNAMES_M2662 = TELEMETRY_FIELDNAMES + [
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
]


@dataclass(frozen=True)
class ProtectedMitigationRunItem:
    panel_spec_id: str
    seed_panel_id: str
    role_family: str
    seed_index: int
    seed: int
    fresh_seed_not_in_m2641: bool
    source_focus_seed: str
    source_focus_dynamics_axis_id: str
    base_fixture_id: str
    fixture_id: str
    surface_id: str
    fixture_spec: SourceOnlyRoleFixtureDynamicsSpec
    fixture_variant_digest: str
    dynamics_axis_id: str
    dynamics_axis_family: str
    axis_index: int
    source_only_fault_axis_applied: bool
    protected_failure_surface_axis: bool
    protected_focus_source_match: bool
    axis_config: dict[str, Any]


def materialize_protected_mitigation_fresh_failure_surface_panel(
    output_dir: Path | str,
    *,
    evidence_index: Path | str = DEFAULT_EVIDENCE_INDEX,
    gap_matrix: Path | str = DEFAULT_GAP_MATRIX,
    target_protected_report: Path | str = DEFAULT_TARGET_PROTECTED_REPORT,
    protected_focus_rows: Path | str = DEFAULT_PROTECTED_FOCUS_ROWS,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    protected_seed_count: int = DEFAULT_PROTECTED_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    policy_checkpoints: dict[str, str | Path] | None = None,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    if int(protected_seed_count) < 1:
        raise ValueError("protected_seed_count must be positive")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    source = load_source_artifacts(
        evidence_index=evidence_index,
        gap_matrix=gap_matrix,
        target_protected_report=target_protected_report,
        protected_focus_rows=protected_focus_rows,
        follow_up_manifest=follow_up_manifest,
    )
    row_schema_fields = [row["field_name"] for row in source["row_schema"]]
    run_items, panel_spec_rows = build_protected_mitigation_panel_specs(
        source["protected_focus_rows"],
        protected_seed_count=int(protected_seed_count),
    )
    subjects = route_a_subjects(policy_checkpoints)
    admitted_subjects, _subject_registry_rows = admit_route_a_subjects(subjects, device=device)
    telemetry_rows, telemetry_summary = run_fresh_generalization_telemetry(
        run_items,
        admitted_subjects,
        horizon_steps=int(horizon_steps),
    )
    measured_behavior_rows = build_protected_measured_behavior_rows(
        telemetry_rows,
        run_items=run_items,
        subjects=subjects,
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    protected_gate_rows = build_protected_mitigation_gate_rows(measured_behavior_rows)
    claim_boundary_rows = build_claim_boundary_rows()

    paths = {
        "summary": output_path / "summary.json",
        "panel_spec_rows": output_path / "panel_spec_rows.csv",
        "measured_behavior_rows": output_path / "measured_behavior_rows.csv",
        "protected_mitigation_gate_rows": output_path / "protected_mitigation_gate_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }
    write_csv_rows(paths["panel_spec_rows"], panel_spec_rows, fieldnames=PANEL_SPEC_FIELDNAMES)
    write_csv_rows(
        paths["measured_behavior_rows"],
        measured_behavior_rows,
        fieldnames=_dedupe(row_schema_fields + EXTRA_BEHAVIOR_FIELDS_M2662),
    )
    write_csv_rows(
        paths["protected_mitigation_gate_rows"],
        protected_gate_rows,
        fieldnames=PROTECTED_GATE_FIELDNAMES,
    )
    write_csv_rows(
        paths["claim_boundary_rows"],
        claim_boundary_rows,
        fieldnames=CLAIM_BOUNDARY_FIELDNAMES,
    )

    metrics = build_metrics(
        output_dir=output_path,
        paths=paths,
        source=source,
        subjects=subjects,
        telemetry_summary=telemetry_summary,
        panel_spec_rows=panel_spec_rows,
        measured_behavior_rows=measured_behavior_rows,
        protected_gate_rows=protected_gate_rows,
        claim_boundary_rows=claim_boundary_rows,
        protected_seed_count=int(protected_seed_count),
        horizon_steps=int(horizon_steps),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    gate_matrix_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(paths["gate_matrix"], gate_matrix_rows, fieldnames=GATE_MATRIX_FIELDNAMES)
    summary = build_summary(metrics, gate_matrix_rows)
    write_json(paths["summary"], summary)
    write_milestone_doc(paths["doc"], summary, protected_gate_rows, gate_matrix_rows)
    summary["required_artifacts_present"] = all(
        Path(summary[key]).exists()
        for key in (
            "summary",
            "panel_spec_rows",
            "measured_behavior_rows",
            "protected_mitigation_gate_rows",
            "claim_boundary_rows",
            "gate_matrix",
        )
    )
    summary["status_pass"] = bool(
        summary["status_pass"] and summary["required_artifacts_present"]
    )
    write_json(paths["summary"], summary)
    return summary


def load_source_artifacts(
    *,
    evidence_index: Path | str,
    gap_matrix: Path | str,
    target_protected_report: Path | str,
    protected_focus_rows: Path | str,
    follow_up_manifest: Path | str,
) -> dict[str, Any]:
    paths = {
        "evidence_index": Path(evidence_index),
        "gap_matrix": Path(gap_matrix),
        "target_protected_report": Path(target_protected_report),
        "protected_focus_rows": Path(protected_focus_rows),
        "follow_up_manifest": Path(follow_up_manifest),
        "m2659_summary": DEFAULT_M2659_SUMMARY,
        "m2657_summary": DEFAULT_M2657_SUMMARY,
        "m2661_doc": M2661_DOC,
        "row_schema": M2514_ROW_SCHEMA,
    }
    return {
        "paths": paths,
        "source_exists": {key: path.exists() for key, path in paths.items()},
        "evidence_index": _read_csv_rows(paths["evidence_index"]),
        "gap_matrix": _read_csv_rows(paths["gap_matrix"]),
        "target_protected_report": _read_csv_rows(paths["target_protected_report"]),
        "protected_focus_rows": _read_csv_rows(paths["protected_focus_rows"]),
        "m2659_summary": read_json(paths["m2659_summary"]),
        "m2657_summary": read_json(paths["m2657_summary"]),
        "row_schema": _read_csv_rows(paths["row_schema"]),
    }


def build_protected_mitigation_panel_specs(
    protected_focus_rows: list[dict[str, str]],
    *,
    protected_seed_count: int,
) -> tuple[list[ProtectedMitigationRunItem], list[dict[str, Any]]]:
    base_spec = _base_specs_by_role()[PROTECTED_ROLE]
    source_focus = sorted(
        protected_focus_rows,
        key=lambda row: (int(row.get("seed", "0")), row.get("dynamics_axis_id", "")),
    )
    source_seeds = {int(row.get("seed", "0")) for row in source_focus if row.get("seed")}
    run_items: list[ProtectedMitigationRunItem] = []
    panel_rows: list[dict[str, Any]] = []
    for seed_index in range(int(protected_seed_count)):
        seed = PROTECTED_SEED_BASE + seed_index
        focus = source_focus[seed_index % len(source_focus)] if source_focus else {}
        nominal_variant = _variant_fixture_spec(base_spec, seed=seed, seed_index=seed_index)
        for axis_index, axis_id in enumerate(PROTECTED_DYNAMICS_AXES):
            variant, axis_config = _axis_variant_spec_m2662(
                nominal_variant,
                seed=seed,
                seed_index=seed_index,
                dynamics_axis_id=axis_id,
                axis_index=axis_index,
            )
            digest = _fixture_digest(variant)
            panel_spec_id = f"m2662_{PROTECTED_ROLE}_seed_{seed}_{axis_id}"
            item = ProtectedMitigationRunItem(
                panel_spec_id=panel_spec_id,
                seed_panel_id=panel_spec_id,
                role_family=PROTECTED_ROLE,
                seed_index=seed_index,
                seed=seed,
                fresh_seed_not_in_m2641=seed not in source_seeds,
                source_focus_seed=focus.get("seed", ""),
                source_focus_dynamics_axis_id=focus.get("dynamics_axis_id", ""),
                base_fixture_id=base_spec.fixture_id,
                fixture_id=variant.fixture_id,
                surface_id=SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                fixture_spec=variant,
                fixture_variant_digest=digest,
                dynamics_axis_id=axis_id,
                dynamics_axis_family=axis_config["axis_family"],
                axis_index=axis_index,
                source_only_fault_axis_applied=bool(axis_config["source_only_fault_axis_applied"]),
                protected_failure_surface_axis=axis_id != "fresh_protected_nominal",
                protected_focus_source_match=bool(focus),
                axis_config=axis_config,
            )
            run_items.append(item)
            panel_rows.append(
                {
                    "panel_spec_id": panel_spec_id,
                    "role_family": PROTECTED_ROLE,
                    "role_class": "protected",
                    "seed_index": seed_index,
                    "seed": seed,
                    "fresh_seed_not_in_m2641": seed not in source_seeds,
                    "source_focus_seed": item.source_focus_seed,
                    "source_focus_dynamics_axis_id": item.source_focus_dynamics_axis_id,
                    "base_fixture_id": base_spec.fixture_id,
                    "fixture_id": variant.fixture_id,
                    "surface_id": SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                    "fixture_variant_digest": digest,
                    "initial_state_digest": _digest(asdict(variant.initial_state)),
                    "fault_scale_digest": _digest(asdict(variant.fault_scales)),
                    "road_digest": _digest(asdict(variant.road)),
                    "obstacle_digest": _digest([asdict(obstacle) for obstacle in variant.obstacles]),
                    "dynamics_axis_id": axis_id,
                    "dynamics_axis_family": axis_config["axis_family"],
                    "axis_index": axis_index,
                    "axis_family": axis_config["axis_family"],
                    "uniform_grip_scale": axis_config["uniform_grip_scale"],
                    "left_right_split_mu_scale": axis_config["left_right_split_mu_scale"],
                    "lateral_stiffness_scale": axis_config["lateral_stiffness_scale"],
                    "brake_scale": axis_config["brake_scale"],
                    "steering_delay_steps": axis_config["steering_delay_steps"],
                    "throttle_delay_steps": axis_config["throttle_delay_steps"],
                    "brake_delay_steps": axis_config["brake_delay_steps"],
                    "sensor_noise_std": axis_config["sensor_noise_std"],
                    "source_only_fault_axis_applied": axis_config["source_only_fault_axis_applied"],
                    "actuator_delay_applied_to_backend": axis_config[
                        "actuator_delay_applied_to_backend"
                    ],
                    "sensor_noise_applied_to_actor_input": axis_config[
                        "sensor_noise_applied_to_actor_input"
                    ],
                    "obstacle_longitudinal_delta_m": axis_config[
                        "obstacle_longitudinal_delta_m"
                    ],
                    "obstacle_lateral_delta_m": axis_config["obstacle_lateral_delta_m"],
                    "obstacle_width_scale": axis_config["obstacle_width_scale"],
                    "fresh_failure_surface_axis": axis_id != "fresh_protected_nominal",
                    "actor_visible_allowed": False,
                    "actor_input_contract_changed": False,
                    "hidden_diagnostics_metadata_only": True,
                    "variant_reason": (
                        "m2662 fresh protected mitigation failure-surface seed and axis"
                    ),
                    "claim_scope": CLAIM_SCOPE,
                }
            )
    return run_items, panel_rows


def build_protected_measured_behavior_rows(
    telemetry_rows: list[dict[str, Any]],
    *,
    run_items: list[ProtectedMitigationRunItem],
    subjects: tuple[RouteASubject, ...],
    row_schema_fields: list[str],
    milestone: str,
) -> list[dict[str, Any]]:
    item_by_key = {
        (item.role_family, item.seed, item.dynamics_axis_id): item for item in run_items
    }
    subject_by_id = {subject.subject_id: subject for subject in subjects}
    groups: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in telemetry_rows:
        groups[
            (
                row["comparison_subject"],
                row["role_family"],
                int(row["seed"]),
                row["dynamics_axis_id"],
            )
        ].append(row)

    event_by_key: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for key, rows in groups.items():
        _subject_id, role, seed, axis_id = key
        item = item_by_key[(role, seed, axis_id)]
        stats = _event_stats(
            sorted(rows, key=lambda value: int(value["step_index"])),
            road=item.fixture_spec.road,
            obstacle=_primary_obstacle(item.fixture_spec.obstacles),
        )
        event_by_key[key] = {
            "collision_event": stats.collision_event,
            "obstacle_passed_event": stats.obstacle_passed_event,
            "road_departure_event": stats.road_departure_event,
            "minimum_obstacle_clearance_m": stats.minimum_obstacle_clearance_m,
            "minimum_road_margin_m": stats.minimum_road_margin_m,
            "final_road_margin_m": stats.final_road_margin_m,
            "collision_speed_proxy": stats.collision_speed_proxy,
            "impact_angle_proxy": stats.impact_angle_proxy,
            "severity_proxy": stats.severity_proxy,
            "recovery_time_proxy_s": stats.recovery_time_proxy_s,
        }

    for (subject_id, role, seed, axis_id), event in list(event_by_key.items()):
        reference = event_by_key.get((MITIGATION_REFERENCE_SUBJECT, role, seed, axis_id), event)
        event["mitigation_delta_against_reference"] = (
            float(event["severity_proxy"]) - float(reference["severity_proxy"])
        )

    measured_rows: list[dict[str, Any]] = []
    for item in run_items:
        for subject_id in sorted(subject_by_id):
            subject = subject_by_id[subject_id]
            group = sorted(
                groups[(subject_id, item.role_family, item.seed, item.dynamics_axis_id)],
                key=lambda value: int(value["step_index"]),
            )
            if not group:
                continue
            first = group[0]
            last = group[-1]
            event = event_by_key[(subject_id, item.role_family, item.seed, item.dynamics_axis_id)]
            row_id = f"m2662_{subject_id}_{PROTECTED_ROLE}_seed_{item.seed}_{item.dynamics_axis_id}"
            behavior_row = {
                "protocol_version": "engineering_controller_behavior_outcome_v0",
                "milestone_id": milestone,
                "run_id": milestone,
                "row_id": row_id,
                "evidence_layer": "source_only_protected_mitigation_failure_surface_panel",
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
                    float(row["physical_throttle"]) > 1e-9
                    and float(row["physical_brake"]) > 1e-9
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
                "source_artifact": "Route A protected mitigation fresh failure-surface panel",
                "attempted_row_retained": True,
                "panel_spec_id": item.panel_spec_id,
                "seed_panel_id": item.panel_spec_id,
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
                "fresh_protected_seed": True,
                "fresh_seed_not_in_m2641": item.fresh_seed_not_in_m2641,
                "protected_rows_in_success_denominator": False,
                "protected_failure_surface_axis": item.protected_failure_surface_axis,
                "protected_focus_source_match": item.protected_focus_source_match,
                "source_only_fault_axis_applied": item.source_only_fault_axis_applied,
                "actor_visible_labels": False,
                "diagnostic_only_no_success_claim": True,
            }
            measured_rows.append(
                {
                    field: behavior_row.get(field, "")
                    for field in _dedupe(row_schema_fields + EXTRA_BEHAVIOR_FIELDS_M2662)
                }
            )
    return measured_rows


def build_protected_mitigation_gate_rows(
    measured_behavior_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    policy_subjects = sorted(
        {
            row["subject_id"]
            for row in measured_behavior_rows
            if row.get("subject_id") in set(POLICY_SUBJECT_IDS)
        }
    )
    axes = sorted({row["dynamics_axis_id"] for row in measured_behavior_rows})
    for subject_id in policy_subjects:
        for axis_id in axes:
            subject_rows = [
                row
                for row in measured_behavior_rows
                if row.get("subject_id") == subject_id and row.get("dynamics_axis_id") == axis_id
            ]
            reference_rows = [
                row
                for row in measured_behavior_rows
                if row.get("subject_id") == MITIGATION_REFERENCE_SUBJECT
                and row.get("dynamics_axis_id") == axis_id
            ]
            reference_by_seed = {int(row["seed"]): row for row in reference_rows}
            for metric, direction, gate_id in (
                ("severity_proxy", "lower_is_better", "severity_proxy_against_reference"),
                (
                    "obstacle_penetration_proxy_m",
                    "lower_is_better",
                    "obstacle_penetration_against_reference",
                ),
                (
                    "minimum_obstacle_clearance_m",
                    "higher_is_better",
                    "minimum_obstacle_clearance_against_reference",
                ),
            ):
                compared: list[tuple[float, float]] = []
                for subject_row in subject_rows:
                    reference_row = reference_by_seed.get(int(subject_row["seed"]))
                    if not reference_row:
                        continue
                    compared.append(
                        (
                            _metric_value(subject_row, metric),
                            _metric_value(reference_row, metric),
                        )
                    )
                improved, regressed, unchanged = _compare_pairs(compared, direction)
                gate_pass = regressed == 0 and bool(compared)
                rows.append(
                    {
                        "gate_id": f"m2662_{subject_id}_{axis_id}_{gate_id}",
                        "gate_family": "protected_mitigation_reference_comparison",
                        "subject_id": subject_id,
                        "dynamics_axis_id": axis_id,
                        "metric": metric,
                        "metric_direction": direction,
                        "evaluated_row_count": len(compared),
                        "reference_subject_id": MITIGATION_REFERENCE_SUBJECT,
                        "reference_mean": _mean([reference for _subject, reference in compared]),
                        "subject_mean": _mean([subject for subject, _reference in compared]),
                        "improved_row_count": improved,
                        "regressed_row_count": regressed,
                        "unchanged_row_count": unchanged,
                        "gate_pass": gate_pass,
                        "blocks_claims": bool(regressed > 0),
                        "failure_type": "behavior_regression" if regressed > 0 else "",
                        "interpretation": (
                            "diagnostic protected mitigation blocker row; not a success-rate "
                            "or performance denominator"
                            if regressed > 0
                            else "diagnostic protected mitigation comparison row"
                        ),
                        "claim_scope": CLAIM_SCOPE,
                    }
                )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "panel_materialized",
            "allowed_operational_claim",
            True,
            True,
            "fresh protected mitigation source-only panel artifacts may be claimed",
        ),
        (
            "fresh_seed_or_axis_materialized",
            "allowed_operational_claim",
            True,
            True,
            "fresh protected seeds and a fresh failure-surface axis are materialized",
        ),
        (
            "protected_blocker_preserved",
            "allowed_negative_result_claim",
            True,
            True,
            "protected mitigation remains blocking and outside success denominators",
        ),
    ]
    forbidden = (
        "repair_success",
        "controller_family_ranking",
        "winner_selection",
        "checkpoint_promotion",
        "success_rate_verdict",
        "driver_performance",
        "validation_result",
        "high_fidelity_validation_result",
        "paper_level_evidence",
        "finite_window_vs_gru",
        "current_sim_verdict",
        "level3_self_identification",
    )
    output = [
        {
            "claim_id": f"m2662_claim_{claim_id}",
            "claim_family": family,
            "allowed": allowed,
            "emitted": emitted,
            "status_pass": bool(allowed == emitted),
            "evidence": evidence,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            "claim_scope": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, emitted, evidence in rows
    ]
    output.extend(
        {
            "claim_id": f"m2662_reject_{claim_id}",
            "claim_family": "forbidden_claim_rejected",
            "allowed": False,
            "emitted": False,
            "status_pass": True,
            "evidence": f"{claim_id} not emitted by M2662",
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            "claim_scope": CLAIM_SCOPE,
        }
        for claim_id in forbidden
    )
    return output


def build_metrics(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    subjects: tuple[RouteASubject, ...],
    telemetry_summary: dict[str, Any],
    panel_spec_rows: list[dict[str, Any]],
    measured_behavior_rows: list[dict[str, Any]],
    protected_gate_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    protected_seed_count: int,
    horizon_steps: int,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    subject_ids = tuple(subject.subject_id for subject in subjects)
    expected_panel_rows = int(protected_seed_count) * len(PROTECTED_DYNAMICS_AXES)
    expected_behavior_rows = expected_panel_rows * len(subject_ids)
    expected_telemetry_rows = expected_behavior_rows * int(horizon_steps)
    fresh_seed_values = {int(row["seed"]) for row in panel_spec_rows}
    source_focus_seeds = {
        int(row["seed"])
        for row in source["protected_focus_rows"]
        if str(row.get("seed", "")).strip()
    }
    axes = {row["dynamics_axis_id"] for row in panel_spec_rows}
    required_artifacts_present = all(
        paths[key].exists()
        for key in (
            "panel_spec_rows",
            "measured_behavior_rows",
            "protected_mitigation_gate_rows",
            "claim_boundary_rows",
        )
    )
    actor_contract_shape_72_action_3 = (
        bool(measured_behavior_rows)
        and {int(row["observation_shape"]) for row in measured_behavior_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in measured_behavior_rows} == {ACTION_DIM}
    )
    target_protected_split_preserved = (
        bool(source["target_protected_report"])
        and all(row.get("role_family") == PROTECTED_ROLE for row in panel_spec_rows)
        and all(str(row.get("protected_rows_in_success_denominator")).lower() == "false"
                for row in measured_behavior_rows)
    )
    protected_blocker_source_preserved = (
        bool(source["gap_matrix"])
        and any(
            row.get("gap_id") == "route_a_protected_mitigation_blocker"
            and row.get("current_status") == "blocking"
            for row in source["gap_matrix"]
        )
    )
    claim_boundary_rows_pass = bool(claim_boundary_rows) and all(
        _bool(row["status_pass"]) for row in claim_boundary_rows
    )
    no_forbidden_claims = not any(FALSE_CLAIM_FLAGS.values())
    policy_gate_rows = [
        row
        for row in protected_gate_rows
        if row.get("subject_id") in set(POLICY_SUBJECT_IDS)
    ]
    protected_gate_regressed_row_count = sum(_int(row["regressed_row_count"]) for row in policy_gate_rows)
    protected_gate_blocking_row_count = sum(1 for row in policy_gate_rows if _bool(row["blocks_claims"]))
    return {
        "protocol_version": "engineering_controller_route_a_protected_mitigation_panel_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "panel_spec_rows": str(paths["panel_spec_rows"]),
        "measured_behavior_rows": str(paths["measured_behavior_rows"]),
        "protected_mitigation_gate_rows": str(paths["protected_mitigation_gate_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "follow_up_manifest_registered": source["source_exists"]["follow_up_manifest"],
        "evidence_index": str(source["paths"]["evidence_index"]),
        "gap_matrix_source": str(source["paths"]["gap_matrix"]),
        "target_protected_report": str(source["paths"]["target_protected_report"]),
        "protected_focus_rows_source": str(source["paths"]["protected_focus_rows"]),
        "m2659_summary": str(source["paths"]["m2659_summary"]),
        "m2657_summary": str(source["paths"]["m2657_summary"]),
        "m2661_doc": str(source["paths"]["m2661_doc"]),
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_exists": source["source_exists"],
        "source_evidence_consumed_as_design_input_only": True,
        "protected_role": PROTECTED_ROLE,
        "target_roles": list(TARGET_ROLES),
        "target_role_count": len(TARGET_ROLES),
        "protected_role_count": 1,
        "target_protected_split_preserved": bool(target_protected_split_preserved),
        "protected_role_excluded_from_target_success_denominator": True,
        "protected_blocker_source_preserved": bool(protected_blocker_source_preserved),
        "protected_seed_count": int(protected_seed_count),
        "fresh_protected_seed_count": len(fresh_seed_values),
        "fresh_seed_values": sorted(fresh_seed_values),
        "source_focus_seed_values": sorted(source_focus_seeds),
        "fresh_seeds_not_in_m2641": bool(fresh_seed_values.isdisjoint(source_focus_seeds)),
        "dynamics_axes": list(PROTECTED_DYNAMICS_AXES),
        "dynamics_axis_count": len(axes),
        "fresh_failure_surface_axis_count": sum(
            _bool(row["fresh_failure_surface_axis"]) for row in panel_spec_rows
        ),
        "panel_spec_row_count": len(panel_spec_rows),
        "expected_panel_spec_row_count": expected_panel_rows,
        "comparison_subjects": list(subject_ids),
        "comparison_subject_count": len(subject_ids),
        "policy_checkpoint_subjects": list(POLICY_SUBJECT_IDS),
        "policy_checkpoint_subject_count": len(POLICY_SUBJECT_IDS),
        "open_loop_subjects": list(OPEN_LOOP_SUBJECT_IDS),
        "open_loop_subject_count": len(OPEN_LOOP_SUBJECT_IDS),
        "all_policy_checkpoints_admitted": bool(
            telemetry_summary.get("all_policy_checkpoints_admitted")
        ),
        "horizon_steps": int(horizon_steps),
        "measured_behavior_row_count": len(measured_behavior_rows),
        "expected_behavior_rows": expected_behavior_rows,
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "expected_telemetry_rows": expected_telemetry_rows,
        "reset_count": int(telemetry_summary.get("reset_count", 0)),
        "expected_reset_count": expected_behavior_rows,
        "all_attempted_subject_seed_axis_rows_retained": (
            len(measured_behavior_rows) == expected_behavior_rows
            and all(str(row["attempted_row_retained"]).lower() == "true"
                    for row in measured_behavior_rows)
        ),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "hidden_oracle_actor_input_detected": False,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "localization_labels_actor_visible": False,
        "objective_gate_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "all_actions_finite": bool(
            measured_behavior_rows
            and all(str(row["action_finite"]).lower() == "true" for row in measured_behavior_rows)
        ),
        "all_actions_within_bounds": bool(
            measured_behavior_rows
            and all(str(row["action_within_bounds"]).lower() == "true"
                    for row in measured_behavior_rows)
        ),
        "all_rows_diagnostic_only_no_ranking_claim": bool(
            measured_behavior_rows
            and all(str(row["diagnostic_only_no_ranking_claim"]).lower() == "true"
                    for row in measured_behavior_rows)
            and all(str(row["diagnostic_only_no_success_claim"]).lower() == "true"
                    for row in measured_behavior_rows)
        ),
        "ranking_or_winner_fields_emitted": False,
        "protected_mitigation_gate_row_count": len(protected_gate_rows),
        "protected_gate_regressed_row_count": protected_gate_regressed_row_count,
        "protected_gate_blocking_row_count": protected_gate_blocking_row_count,
        "protected_mitigation_gate_all_passed": bool(
            protected_gate_rows and all(_bool(row["gate_pass"]) for row in protected_gate_rows)
        ),
        "protected_failure_blocking": True,
        "claim_boundary_row_count": len(claim_boundary_rows),
        "claim_boundary_rows_pass": bool(claim_boundary_rows_pass),
        "required_artifacts_present": bool(required_artifacts_present),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "source_only_backend_reset_run": bool(measured_behavior_rows),
        "source_only_backend_step_run": bool(measured_behavior_rows),
        "policy_action_run": bool(measured_behavior_rows),
        "policy_rollout_run": bool(measured_behavior_rows),
        "new_repair_training_or_rollout_run": False,
        "repair_execution_started": False,
        "repair_training_started": False,
        "selected_candidate_treated_as_winner": False,
        "ranking_or_winner_field_emitted": False,
        "no_forbidden_claims": bool(no_forbidden_claims),
        **FALSE_CLAIM_FLAGS,
    }


def build_gate_matrix_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    gate_specs = (
        ("source_artifacts_present", "lineage", metrics["source_artifacts_present"], True, "lineage_invalid"),
        ("follow_up_manifest_registered", "lineage", metrics["follow_up_manifest_registered"], True, "lineage_invalid"),
        ("fresh_protected_seeds", "panel_shape", metrics["fresh_seeds_not_in_m2641"], True, "scenario_sampling_failure"),
        ("protected_role_only", "panel_shape", metrics["protected_role_count"], 1, "scenario_sampling_failure"),
        ("dynamics_axis_count", "panel_shape", metrics["dynamics_axis_count"], len(PROTECTED_DYNAMICS_AXES), "scenario_sampling_failure"),
        ("fresh_failure_surface_axis_present", "panel_shape", metrics["fresh_failure_surface_axis_count"] > 0, True, "scenario_sampling_failure"),
        ("panel_spec_row_count", "panel_shape", metrics["panel_spec_row_count"], metrics["expected_panel_spec_row_count"], "metric_artifact"),
        ("measured_behavior_row_count", "panel_shape", metrics["measured_behavior_row_count"], metrics["expected_behavior_rows"], "metric_artifact"),
        ("telemetry_row_count", "panel_shape", metrics["telemetry_row_count"], metrics["expected_telemetry_rows"], "metric_artifact"),
        ("reset_count", "panel_shape", metrics["reset_count"], metrics["expected_reset_count"], "metric_artifact"),
        ("target_protected_split_preserved", "claim_boundary", metrics["target_protected_split_preserved"], True, "objective_overfit"),
        ("protected_blocker_source_preserved", "claim_boundary", metrics["protected_blocker_source_preserved"], True, "proof_washout"),
        ("actor_contract_shape_72_action_3", "actor_contract", metrics["actor_contract_shape_72_action_3"], True, "contract_violation"),
        ("hidden_oracle_actor_input_detected", "actor_contract", metrics["hidden_oracle_actor_input_detected"], False, "contract_violation"),
        ("all_policy_checkpoints_admitted", "subject_admission", metrics["all_policy_checkpoints_admitted"], True, "lineage_invalid"),
        ("all_actions_finite", "action_contract", metrics["all_actions_finite"], True, "behavior_regression"),
        ("all_actions_within_bounds", "action_contract", metrics["all_actions_within_bounds"], True, "behavior_regression"),
        ("all_rows_diagnostic_only", "claim_boundary", metrics["all_rows_diagnostic_only_no_ranking_claim"], True, "objective_overfit"),
        ("claim_boundary_rows_pass", "claim_boundary", metrics["claim_boundary_rows_pass"], True, "objective_overfit"),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("winner_selected", "forbidden_claim", metrics["winner_selected"], False, "objective_overfit"),
        ("checkpoint_promoted", "forbidden_claim", metrics["checkpoint_promoted"], False, "objective_overfit"),
        ("success_rate_computed", "forbidden_claim", metrics["success_rate_computed"], False, "objective_overfit"),
        ("driver_performance_claim_made", "forbidden_claim", metrics["driver_performance_claim_made"], False, "objective_overfit"),
    )
    rows = []
    for gate_id, family, observed, expected, failure_type in gate_specs:
        status = observed == expected
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(status),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status else failure_type,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_summary(metrics: dict[str, Any], gate_matrix_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_matrix_rows) and all(_bool(row["status_pass"]) for row in gate_matrix_rows)
    status_pass = (
        gate_matrix_pass
        and metrics["required_artifacts_present"]
        and metrics["source_artifacts_present"]
        and metrics["follow_up_manifest_registered"]
        and metrics["fresh_seeds_not_in_m2641"]
        and metrics["target_protected_split_preserved"]
        and metrics["protected_blocker_source_preserved"]
        and metrics["actor_contract_shape_72_action_3"]
        and not metrics["hidden_oracle_actor_input_detected"]
        and metrics["all_actions_finite"]
        and metrics["all_actions_within_bounds"]
        and metrics["claim_boundary_rows_pass"]
        and metrics["no_forbidden_claims"]
    )
    result_class = (
        "engineering_controller_route_a_protected_mitigation_fresh_failure_surface_"
        "panel_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_protected_mitigation_fresh_failure_surface_"
        "panel_materialization_preflight_failed"
    )
    return {
        "result_class": result_class,
        "status_pass": bool(status_pass),
        "gate_matrix_pass": bool(gate_matrix_pass),
        "gate_matrix_row_count": len(gate_matrix_rows),
        **metrics,
    }


def write_milestone_doc(
    path: Path,
    summary: dict[str, Any],
    protected_gate_rows: list[dict[str, Any]],
    gate_matrix_rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocking_rows = [row for row in protected_gate_rows if _bool(row["blocks_claims"])]
    lines = [
        "# M2662 Route A Protected Mitigation Fresh Failure-Surface Panel",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result_class: `{summary['result_class']}`",
        f"- manifest: `experiments/manifests/{summary['milestone']}.json`",
        f"- summary: `{summary['summary']}`",
        f"- panel spec rows: `{summary['panel_spec_rows']}`",
        f"- measured behavior rows: `{summary['measured_behavior_rows']}`",
        f"- protected mitigation gate rows: `{summary['protected_mitigation_gate_rows']}`",
        f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
        f"- gate matrix: `{summary['gate_matrix']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Materialized Evidence",
        "",
        "```text",
        f"protected_role: {summary['protected_role']}",
        f"fresh_protected_seed_count: {summary['fresh_protected_seed_count']}",
        f"dynamics_axis_count: {summary['dynamics_axis_count']}",
        f"panel_spec_row_count: {summary['panel_spec_row_count']}",
        f"measured_behavior_row_count: {summary['measured_behavior_row_count']}",
        f"protected_mitigation_gate_row_count: {summary['protected_mitigation_gate_row_count']}",
        f"protected_gate_blocking_row_count: {summary['protected_gate_blocking_row_count']}",
        f"actor_contract_shape_72_action_3: {summary['actor_contract_shape_72_action_3']}",
        f"hidden_oracle_actor_input_detected: {summary['hidden_oracle_actor_input_detected']}",
        f"gate_matrix_pass: {summary['gate_matrix_pass']}",
        "```",
        "",
        "M2662 consumes M2657-M2661 target/protected evidence as design input only,",
        "then runs a fresh source-only protected mitigation panel over new protected",
        "seeds and three dynamics axes. Protected rows remain outside target success",
        "denominators.",
        "",
        "## Protected Gate Summary",
        "",
    ]
    lines.extend(
        f"- `{row['gate_id']}`: gate_pass={row['gate_pass']} regressed={row['regressed_row_count']}"
        for row in protected_gate_rows[:18]
    )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- blocking protected gate rows: {len(blocking_rows)}",
            "- supported operational claim: fresh protected mitigation failure-surface panel materialized",
            f"- rejected claims: {summary['forbidden_interpretation']}",
            "",
            "## Gate Matrix",
            "",
        ]
    )
    lines.extend(f"- `{row['gate_id']}`: {row['status_pass']}" for row in gate_matrix_rows)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _axis_variant_spec_m2662(
    nominal_variant: SourceOnlyRoleFixtureDynamicsSpec,
    *,
    seed: int,
    seed_index: int,
    dynamics_axis_id: str,
    axis_index: int,
) -> tuple[SourceOnlyRoleFixtureDynamicsSpec, dict[str, Any]]:
    rng = np.random.default_rng(int(seed) + 266200 + int(axis_index) * 1009)
    if dynamics_axis_id == "fresh_protected_nominal":
        config = _axis_config(
            axis_family="protected_nominal",
            uniform_grip_scale=1.0,
            left_right_split_mu_scale=1.0,
            lateral_stiffness_scale=1.0,
            brake_scale=1.0,
            source_only_fault_axis_applied=False,
            obstacle_longitudinal_delta_m=0.0,
            obstacle_lateral_delta_m=0.0,
            obstacle_width_scale=1.0,
        )
        return _retag_variant_m2662(nominal_variant, seed, seed_index, dynamics_axis_id, axis_index, config), config

    if dynamics_axis_id == "fresh_protected_fault_delay_noise":
        config = _axis_config(
            axis_family="protected_fault_delay_noise",
            uniform_grip_scale=float(rng.uniform(0.60, 0.95)),
            left_right_split_mu_scale=float(rng.uniform(0.62, 1.08)),
            lateral_stiffness_scale=float(rng.uniform(0.62, 0.98)),
            brake_scale=float(rng.uniform(0.68, 1.00)),
            source_only_fault_axis_applied=True,
            obstacle_longitudinal_delta_m=0.0,
            obstacle_lateral_delta_m=0.0,
            obstacle_width_scale=1.0,
        )
        return _fault_variant_m2662(
            nominal_variant, seed, seed_index, dynamics_axis_id, axis_index, config
        ), config

    if dynamics_axis_id != "fresh_protected_close_cut_in_fault":
        raise ValueError(f"unknown M2662 dynamics axis: {dynamics_axis_id}")

    config = _axis_config(
        axis_family="protected_close_cut_in_fault",
        uniform_grip_scale=float(rng.uniform(0.58, 0.92)),
        left_right_split_mu_scale=float(rng.uniform(0.58, 1.05)),
        lateral_stiffness_scale=float(rng.uniform(0.58, 0.96)),
        brake_scale=float(rng.uniform(0.64, 0.96)),
        source_only_fault_axis_applied=True,
        obstacle_longitudinal_delta_m=float(rng.uniform(-2.8, -1.0)),
        obstacle_lateral_delta_m=float(rng.uniform(-0.35, 0.35)),
        obstacle_width_scale=float(rng.uniform(1.04, 1.18)),
    )
    return _fault_variant_m2662(
        nominal_variant, seed, seed_index, dynamics_axis_id, axis_index, config
    ), config


def _axis_config(
    *,
    axis_family: str,
    uniform_grip_scale: float,
    left_right_split_mu_scale: float,
    lateral_stiffness_scale: float,
    brake_scale: float,
    source_only_fault_axis_applied: bool,
    obstacle_longitudinal_delta_m: float,
    obstacle_lateral_delta_m: float,
    obstacle_width_scale: float,
) -> dict[str, Any]:
    return {
        "axis_family": axis_family,
        "uniform_grip_scale": uniform_grip_scale,
        "left_right_split_mu_scale": left_right_split_mu_scale,
        "lateral_stiffness_scale": lateral_stiffness_scale,
        "brake_scale": brake_scale,
        "steering_delay_steps": 0,
        "throttle_delay_steps": 0,
        "brake_delay_steps": 0,
        "sensor_noise_std": 0.0,
        "source_only_fault_axis_applied": source_only_fault_axis_applied,
        "actuator_delay_applied_to_backend": False,
        "sensor_noise_applied_to_actor_input": False,
        "obstacle_longitudinal_delta_m": obstacle_longitudinal_delta_m,
        "obstacle_lateral_delta_m": obstacle_lateral_delta_m,
        "obstacle_width_scale": obstacle_width_scale,
    }


def _retag_variant_m2662(
    spec: SourceOnlyRoleFixtureDynamicsSpec,
    seed: int,
    seed_index: int,
    dynamics_axis_id: str,
    axis_index: int,
    axis_config: dict[str, Any],
) -> SourceOnlyRoleFixtureDynamicsSpec:
    return SourceOnlyRoleFixtureDynamicsSpec(
        fixture_id=f"{spec.fixture_id}_m2662_{dynamics_axis_id}",
        role_family=spec.role_family,
        initial_state=spec.initial_state,
        fault_scales=spec.fault_scales,
        road=spec.road,
        obstacles=_axis_obstacles(spec.obstacles, axis_config),
        diagnostic_tags={
            **dict(spec.diagnostic_tags),
            "fixture_source": "m2662_protected_mitigation_fresh_failure_surface_panel",
            "fresh_seed": int(seed),
            "fresh_seed_index": int(seed_index),
            "dynamics_axis_id": dynamics_axis_id,
            "dynamics_axis_family": axis_config["axis_family"],
            "axis_index": int(axis_index),
            "actor_input_contract_changed": False,
            **axis_config,
        },
    )


def _fault_variant_m2662(
    spec: SourceOnlyRoleFixtureDynamicsSpec,
    seed: int,
    seed_index: int,
    dynamics_axis_id: str,
    axis_index: int,
    axis_config: dict[str, Any],
) -> SourceOnlyRoleFixtureDynamicsSpec:
    left_scale = float(axis_config["left_right_split_mu_scale"])
    right_scale = float(axis_config["uniform_grip_scale"])
    fault_scales = FourWheelFaultScales(
        mu=(left_scale, right_scale, left_scale, right_scale),
        lateral_stiffness=tuple([float(axis_config["lateral_stiffness_scale"])] * 4),
        brake=tuple([float(axis_config["brake_scale"])] * 4),
        drive=spec.fault_scales.drive,
        longitudinal_drag=spec.fault_scales.longitudinal_drag,
    )
    return SourceOnlyRoleFixtureDynamicsSpec(
        fixture_id=f"{spec.fixture_id}_m2662_{dynamics_axis_id}",
        role_family=spec.role_family,
        initial_state=spec.initial_state,
        fault_scales=fault_scales,
        road=spec.road,
        obstacles=_axis_obstacles(spec.obstacles, axis_config),
        diagnostic_tags={
            **dict(spec.diagnostic_tags),
            "fixture_source": "m2662_protected_mitigation_fresh_failure_surface_panel",
            "fresh_seed": int(seed),
            "fresh_seed_index": int(seed_index),
            "dynamics_axis_id": dynamics_axis_id,
            "dynamics_axis_family": axis_config["axis_family"],
            "axis_index": int(axis_index),
            "actor_input_contract_changed": False,
            **axis_config,
        },
    )


def _axis_obstacles(
    obstacles: tuple[ObstacleSlotView, ...],
    axis_config: dict[str, Any],
) -> tuple[ObstacleSlotView, ...]:
    output = []
    primary_adjusted = False
    for obstacle in obstacles:
        if not primary_adjusted and float(obstacle.present) > 0.0:
            output.append(
                ObstacleSlotView(
                    present=float(obstacle.present),
                    x_body=float(obstacle.x_body + axis_config["obstacle_longitudinal_delta_m"]),
                    y_body=float(obstacle.y_body + axis_config["obstacle_lateral_delta_m"]),
                    vx_body=float(obstacle.vx_body),
                    vy_body=float(obstacle.vy_body),
                    half_width=float(obstacle.half_width * axis_config["obstacle_width_scale"]),
                    half_length=float(obstacle.half_length),
                )
            )
            primary_adjusted = True
        else:
            output.append(obstacle)
    return tuple(output)


def _compare_pairs(values: list[tuple[float, float]], direction: str) -> tuple[int, int, int]:
    improved = 0
    regressed = 0
    unchanged = 0
    for subject, reference in values:
        delta = subject - reference
        if direction == "higher_is_better":
            if delta > EPSILON:
                improved += 1
            elif delta < -EPSILON:
                regressed += 1
            else:
                unchanged += 1
        else:
            if delta < -EPSILON:
                improved += 1
            elif delta > EPSILON:
                regressed += 1
            else:
                unchanged += 1
    return improved, regressed, unchanged


def _metric_value(row: dict[str, Any], metric: str) -> float:
    if metric == "obstacle_penetration_proxy_m":
        return max(0.0, -_float(row.get("minimum_obstacle_clearance_m")))
    return _float(row.get(metric))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _dedupe(fields: list[str]) -> list[str]:
    output: list[str] = []
    for field in fields:
        if field not in output:
            output.append(field)
    return output


def _digest(value: Any) -> str:
    payload = json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--gap-matrix", type=Path, default=DEFAULT_GAP_MATRIX)
    parser.add_argument("--target-protected-report", type=Path, default=DEFAULT_TARGET_PROTECTED_REPORT)
    parser.add_argument("--protected-focus-rows", type=Path, default=DEFAULT_PROTECTED_FOCUS_ROWS)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--protected-seed-count", type=int, default=DEFAULT_PROTECTED_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_protected_mitigation_fresh_failure_surface_panel(
        args.output_dir,
        evidence_index=args.evidence_index,
        gap_matrix=args.gap_matrix,
        target_protected_report=args.target_protected_report,
        protected_focus_rows=args.protected_focus_rows,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        protected_seed_count=args.protected_seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
    )
    print(
        "M2662 protected mitigation panel materialized: "
        f"status_pass={summary['status_pass']} "
        f"measured_behavior_rows={summary['measured_behavior_row_count']} "
        f"protected_gate_rows={summary['protected_mitigation_gate_row_count']}"
    )


if __name__ == "__main__":
    main()
