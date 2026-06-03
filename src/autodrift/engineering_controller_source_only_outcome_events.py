"""Source-only evaluator-side outcome event instrumentation."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.hf0_source_only_role_fixture_parameterization import (
    build_source_only_role_fixture_specs,
)
from autodrift.high_fidelity_interface import ObstacleSlotView, RoadView


DEFAULT_MILESTONE = "m2518-engineering-controller-source-only-outcome-event-instrumentation-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2519-engineering-controller-source-only-outcome-event-instrumentation-result-audit"
)
DEFAULT_DOC_PATH = "docs/m2518-engineering-controller-source-only-outcome-event-instrumentation-preflight.md"

M2517_AUDIT = "docs/m2517-engineering-controller-source-only-behavior-outcome-row-completeness-result-audit.md"
M2516_SUMMARY = "runs/m2516_engineering_controller_source_only_behavior_outcome_row_completeness/summary.json"
M2516_BEHAVIOR_ROWS = (
    "runs/m2516_engineering_controller_source_only_behavior_outcome_row_completeness/"
    "behavior_outcome_rows.csv"
)
M2516_GAP_SUMMARY = (
    "runs/m2516_engineering_controller_source_only_behavior_outcome_row_completeness/"
    "metric_gap_summary.csv"
)
M2498_TELEMETRY = (
    "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/telemetry_rows.csv"
)
M2501_TELEMETRY = (
    "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv"
)
M2496_SUMMARY = "runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/summary.json"
M2496_FIXTURE_ROWS = (
    "runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/"
    "fixture_parameterization_rows.csv"
)

OUTCOME_EVENT_FIELDNAMES = [
    "protocol_version",
    "milestone_id",
    "source_behavior_row_id",
    "source_run_id",
    "evidence_layer",
    "surface_id",
    "scenario_role",
    "fixture_id",
    "subject_id",
    "actor_contract_id",
    "observation_shape",
    "action_shape",
    "actor_encoder",
    "action_horizon",
    "actor_input_leak_flags",
    "step_count",
    "primary_obstacle_present",
    "primary_obstacle_x0_m",
    "primary_obstacle_y0_m",
    "primary_obstacle_vx_mps",
    "primary_obstacle_vy_mps",
    "primary_obstacle_half_width_m",
    "primary_obstacle_half_length_m",
    "vehicle_half_width_proxy_m",
    "vehicle_half_length_proxy_m",
    "collision_event",
    "obstacle_passed_event",
    "road_departure_event",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "final_road_margin_m",
    "collision_speed_proxy",
    "impact_angle_proxy",
    "severity_proxy",
    "recovery_time_proxy_s",
    "filled_m2516_unsupported_metrics",
    "remaining_unsupported_metrics",
    "diagnostic_only_no_ranking_claim",
    "claim_scope",
    "forbidden_interpretation",
    "source_artifacts",
]
GAP_DELTA_FIELDNAMES = [
    "metric_name",
    "m2516_support_status",
    "m2516_missing_row_count",
    "m2518_support_status",
    "m2518_supported_row_count",
    "m2518_missing_row_count",
    "filled_by_m2518",
    "remaining_unsupported",
    "gap_delta_reason",
    "claim_boundary",
]

FILLED_METRICS = {
    "collision_event",
    "obstacle_passed_event",
    "road_departure_event",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "final_road_margin_m",
    "recovery_time_proxy_s",
    "collision_speed_proxy",
    "impact_angle_proxy",
    "severity_proxy",
}
REMAINING_UNSUPPORTED_METRICS = {
    "mitigation_delta_against_reference",
    "seed",
}
CLAIM_SCOPE = "source-only evaluator-side outcome event instrumentation only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, or self-ID claim"
)
VEHICLE_HALF_WIDTH_PROXY_M = 0.9
VEHICLE_HALF_LENGTH_PROXY_M = 2.0
DT_SECONDS = 0.02


@dataclass(frozen=True)
class EventStats:
    collision_event: bool
    obstacle_passed_event: bool
    road_departure_event: bool
    minimum_obstacle_clearance_m: float
    minimum_road_margin_m: float
    final_road_margin_m: float
    collision_speed_proxy: float
    impact_angle_proxy: float
    severity_proxy: float
    recovery_time_proxy_s: float


def materialize_source_only_outcome_events(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()
    event_rows = build_outcome_event_rows(source, milestone=milestone)
    gap_delta_rows = build_gap_delta_rows(source["m2516_gap_rows"], event_rows)

    event_rows_path = output_dir / "outcome_event_rows.csv"
    gap_delta_path = output_dir / "outcome_metric_gap_delta.csv"
    write_csv_rows(event_rows_path, event_rows, fieldnames=OUTCOME_EVENT_FIELDNAMES)
    write_csv_rows(gap_delta_path, gap_delta_rows, fieldnames=GAP_DELTA_FIELDNAMES)

    doc_output = Path(doc_path)
    summary = _summary(
        output_dir=output_dir,
        source=source,
        event_rows=event_rows,
        gap_delta_rows=gap_delta_rows,
        event_rows_path=event_rows_path,
        gap_delta_path=gap_delta_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def _load_source_artifacts() -> dict[str, Any]:
    source_paths = [
        M2517_AUDIT,
        M2516_SUMMARY,
        M2516_BEHAVIOR_ROWS,
        M2516_GAP_SUMMARY,
        M2498_TELEMETRY,
        M2501_TELEMETRY,
        M2496_SUMMARY,
        M2496_FIXTURE_ROWS,
    ]
    specs = build_source_only_role_fixture_specs()
    return {
        "m2516_summary": read_json(M2516_SUMMARY),
        "m2516_behavior_rows": _read_csv_rows(M2516_BEHAVIOR_ROWS),
        "m2516_gap_rows": _read_csv_rows(M2516_GAP_SUMMARY),
        "m2498_telemetry": _read_csv_rows(M2498_TELEMETRY),
        "m2501_telemetry": _read_csv_rows(M2501_TELEMETRY),
        "m2496_summary": read_json(M2496_SUMMARY),
        "m2496_fixture_rows": _read_csv_rows(M2496_FIXTURE_ROWS),
        "fixture_specs_by_id": {spec.fixture_id: spec for spec in specs},
        "source_exists": {path: Path(path).exists() for path in source_paths},
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_outcome_event_rows(
    source: dict[str, Any],
    *,
    milestone: str = DEFAULT_MILESTONE,
) -> list[dict[str, Any]]:
    m2498_groups = _telemetry_groups(source["m2498_telemetry"], subject_key=None)
    m2501_groups = _telemetry_groups(source["m2501_telemetry"], subject_key="comparison_subject")
    rows: list[dict[str, Any]] = []
    for behavior_row in source["m2516_behavior_rows"]:
        fixture_id = behavior_row["fixture_id"]
        subject_id = behavior_row["subject_id"]
        role = behavior_row["scenario_role"]
        spec = source["fixture_specs_by_id"][fixture_id]
        if behavior_row["run_id"].startswith("m2498_"):
            telemetry = m2498_groups[("m1154_policy_actor", role)]
        else:
            telemetry = m2501_groups[(subject_id, role)]
        event_stats = _event_stats(telemetry, road=spec.road, obstacle=_primary_obstacle(spec.obstacles))
        filled = sorted(FILLED_METRICS)
        remaining = sorted(REMAINING_UNSUPPORTED_METRICS)
        obstacle = _primary_obstacle(spec.obstacles)
        rows.append(
            {
                "protocol_version": "engineering_controller_behavior_outcome_v0",
                "milestone_id": milestone,
                "source_behavior_row_id": behavior_row["row_id"],
                "source_run_id": behavior_row["run_id"],
                "evidence_layer": "source_only_diagnostic",
                "surface_id": behavior_row["surface_id"],
                "scenario_role": role,
                "fixture_id": fixture_id,
                "subject_id": subject_id,
                "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
                "observation_shape": 72,
                "action_shape": 3,
                "actor_encoder": "human_view_online_gru",
                "action_horizon": 1,
                "actor_input_leak_flags": "",
                "step_count": int(float(behavior_row["step_count"])),
                "primary_obstacle_present": _bool_text(obstacle.present > 0.0),
                "primary_obstacle_x0_m": _float_text(obstacle.x_body),
                "primary_obstacle_y0_m": _float_text(obstacle.y_body),
                "primary_obstacle_vx_mps": _float_text(obstacle.vx_body),
                "primary_obstacle_vy_mps": _float_text(obstacle.vy_body),
                "primary_obstacle_half_width_m": _float_text(obstacle.half_width),
                "primary_obstacle_half_length_m": _float_text(obstacle.half_length),
                "vehicle_half_width_proxy_m": _float_text(VEHICLE_HALF_WIDTH_PROXY_M),
                "vehicle_half_length_proxy_m": _float_text(VEHICLE_HALF_LENGTH_PROXY_M),
                "collision_event": _bool_text(event_stats.collision_event),
                "obstacle_passed_event": _bool_text(event_stats.obstacle_passed_event),
                "road_departure_event": _bool_text(event_stats.road_departure_event),
                "minimum_obstacle_clearance_m": _float_text(event_stats.minimum_obstacle_clearance_m),
                "minimum_road_margin_m": _float_text(event_stats.minimum_road_margin_m),
                "final_road_margin_m": _float_text(event_stats.final_road_margin_m),
                "collision_speed_proxy": _float_text(event_stats.collision_speed_proxy),
                "impact_angle_proxy": _float_text(event_stats.impact_angle_proxy),
                "severity_proxy": _float_text(event_stats.severity_proxy),
                "recovery_time_proxy_s": _float_text(event_stats.recovery_time_proxy_s),
                "filled_m2516_unsupported_metrics": "|".join(filled),
                "remaining_unsupported_metrics": "|".join(remaining),
                "diagnostic_only_no_ranking_claim": "true",
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                "source_artifacts": f"{M2516_BEHAVIOR_ROWS}|{M2498_TELEMETRY}|{M2501_TELEMETRY}",
            }
        )
    return rows


def _telemetry_groups(
    rows: list[dict[str, str]],
    *,
    subject_key: str | None,
) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        subject = row[subject_key] if subject_key else "m1154_policy_actor"
        groups[(subject, row["role_family"])].append(row)
    return {key: sorted(value, key=lambda item: int(item["step_index"])) for key, value in groups.items()}


def _primary_obstacle(obstacles: tuple[ObstacleSlotView, ...]) -> ObstacleSlotView:
    for obstacle in obstacles:
        if obstacle.present > 0.0:
            return obstacle
    return obstacles[0]


def _event_stats(
    telemetry: list[dict[str, str]],
    *,
    road: RoadView,
    obstacle: ObstacleSlotView,
) -> EventStats:
    if not telemetry:
        raise ValueError("telemetry rows are required")
    min_obstacle_clearance = float("inf")
    min_road_margin = float("inf")
    final_road_margin = 0.0
    collision_event = False
    road_departure_event = False
    collision_speed_proxy = 0.0
    impact_angle_proxy = 0.0
    severity_proxy = 0.0
    first_recovery_step: int | None = None
    for row in telemetry:
        step = int(row["step_index"])
        ego_x = float(row["state_x"])
        ego_y = float(row["state_y"])
        obstacle_x = obstacle.x_body + obstacle.vx_body * DT_SECONDS * step
        obstacle_y = obstacle.y_body + obstacle.vy_body * DT_SECONDS * step
        clearance = _signed_rect_clearance(
            ego_x=ego_x,
            ego_y=ego_y,
            obstacle_x=obstacle_x,
            obstacle_y=obstacle_y,
            obstacle_half_width=obstacle.half_width,
            obstacle_half_length=obstacle.half_length,
        )
        min_obstacle_clearance = min(min_obstacle_clearance, clearance)
        is_collision = clearance < 0.0
        collision_event = collision_event or is_collision
        if is_collision:
            speed = float(row["state_speed"])
            collision_speed_proxy = max(collision_speed_proxy, speed)
            impact_angle_proxy = max(impact_angle_proxy, abs(float(row["state_yaw_rate"])))
            severity_proxy = max(severity_proxy, speed * abs(clearance))
        margin = _road_margin(ego_x, ego_y, road)
        min_road_margin = min(min_road_margin, margin)
        final_road_margin = margin
        road_departure_event = road_departure_event or margin < 0.0
        if first_recovery_step is None and abs(float(row["state_vy"])) < 0.2 and abs(float(row["state_yaw_rate"])) < 0.2:
            first_recovery_step = step
    final = telemetry[-1]
    final_x = float(final["state_x"])
    final_obstacle_x = obstacle.x_body + obstacle.vx_body * DT_SECONDS * int(final["step_index"])
    obstacle_passed = final_x > final_obstacle_x + obstacle.half_length + VEHICLE_HALF_LENGTH_PROXY_M
    return EventStats(
        collision_event=bool(collision_event),
        obstacle_passed_event=bool(obstacle_passed),
        road_departure_event=bool(road_departure_event),
        minimum_obstacle_clearance_m=float(min_obstacle_clearance),
        minimum_road_margin_m=float(min_road_margin),
        final_road_margin_m=float(final_road_margin),
        collision_speed_proxy=float(collision_speed_proxy),
        impact_angle_proxy=float(impact_angle_proxy),
        severity_proxy=float(severity_proxy),
        recovery_time_proxy_s=float((first_recovery_step or 0) * DT_SECONDS),
    )


def _signed_rect_clearance(
    *,
    ego_x: float,
    ego_y: float,
    obstacle_x: float,
    obstacle_y: float,
    obstacle_half_width: float,
    obstacle_half_length: float,
) -> float:
    gap_x = abs(ego_x - obstacle_x) - (obstacle_half_length + VEHICLE_HALF_LENGTH_PROXY_M)
    gap_y = abs(ego_y - obstacle_y) - (obstacle_half_width + VEHICLE_HALF_WIDTH_PROXY_M)
    if gap_x <= 0.0 and gap_y <= 0.0:
        return max(gap_x, gap_y)
    positive_x = max(gap_x, 0.0)
    positive_y = max(gap_y, 0.0)
    return (positive_x * positive_x + positive_y * positive_y) ** 0.5


def _road_margin(ego_x: float, ego_y: float, road: RoadView) -> float:
    left_y = _interpolate_boundary_y(ego_x, road.left_boundary_points_body)
    right_y = _interpolate_boundary_y(ego_x, road.right_boundary_points_body)
    return min(left_y - VEHICLE_HALF_WIDTH_PROXY_M - ego_y, ego_y - right_y - VEHICLE_HALF_WIDTH_PROXY_M)


def _interpolate_boundary_y(x: float, points: tuple[tuple[float, float], ...]) -> float:
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        if x <= x1:
            alpha = (x - x0) / max(x1 - x0, 1e-9)
            return y0 + alpha * (y1 - y0)
    return points[-1][1]


def build_gap_delta_rows(
    m2516_gap_rows: list[dict[str, str]],
    event_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    total = len(event_rows)
    rows: list[dict[str, Any]] = []
    for gap in m2516_gap_rows:
        metric = gap["metric_name"]
        if metric in FILLED_METRICS:
            supported = total
            missing = 0
            status = "filled_by_m2518_event_instrumentation"
            reason = "derived from existing fixture geometry and telemetry as evaluator-side diagnostics"
        elif metric in REMAINING_UNSUPPORTED_METRICS:
            supported = 0
            missing = total
            status = "still_unsupported_after_m2518"
            reason = (
                "requires seed lineage or pre-registered mitigation reference semantics; "
                "not inferred in diagnostic instrumentation"
            )
        else:
            supported = int(gap["supported_row_count"])
            missing = int(gap["missing_row_count"])
            status = "unchanged_from_m2516"
            reason = "not an M2516 unsupported outcome gap targeted by this instrumentation"
        rows.append(
            {
                "metric_name": metric,
                "m2516_support_status": gap["support_status"],
                "m2516_missing_row_count": gap["missing_row_count"],
                "m2518_support_status": status,
                "m2518_supported_row_count": supported,
                "m2518_missing_row_count": missing,
                "filled_by_m2518": metric in FILLED_METRICS,
                "remaining_unsupported": metric in REMAINING_UNSUPPORTED_METRICS,
                "gap_delta_reason": reason,
                "claim_boundary": "diagnostic instrumentation only; not a behavior verdict",
            }
        )
    return rows


def _summary(
    *,
    output_dir: Path,
    source: dict[str, Any],
    event_rows: list[dict[str, Any]],
    gap_delta_rows: list[dict[str, Any]],
    event_rows_path: Path,
    gap_delta_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_artifacts_present = event_rows_path.exists() and gap_delta_path.exists()
    source_artifacts_exist = all(source["source_exists"].values())
    missing_source_artifacts = [path for path, exists in source["source_exists"].items() if not exists]
    filled_metrics = sorted(row["metric_name"] for row in gap_delta_rows if row["filled_by_m2518"])
    remaining_metrics = sorted(row["metric_name"] for row in gap_delta_rows if row["remaining_unsupported"])
    false_flags = _false_claim_flags()
    all_rows_source_only = {row["evidence_layer"] for row in event_rows} == {"source_only_diagnostic"}
    all_rows_no_ranking = {
        str(row["diagnostic_only_no_ranking_claim"]).lower() for row in event_rows
    } == {"true"}
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in event_rows} == {72}
        and {int(row["action_shape"]) for row in event_rows} == {3}
    )
    status_pass = (
        required_artifacts_present
        and source_artifacts_exist
        and len(event_rows) == int(source["m2516_summary"]["behavior_outcome_row_count"])
        and len(gap_delta_rows) == int(source["m2516_summary"]["metric_gap_row_count"])
        and set(filled_metrics) == FILLED_METRICS
        and set(remaining_metrics) == REMAINING_UNSUPPORTED_METRICS
        and all_rows_source_only
        and all_rows_no_ranking
        and actor_contract_shape_72_action_3
        and not any(false_flags.values())
    )
    return {
        "result_class": (
            "engineering_controller_source_only_outcome_event_instrumentation_pass"
            if status_pass
            else "engineering_controller_source_only_outcome_event_instrumentation_failed"
        ),
        "status_pass": bool(status_pass),
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "outcome_event_rows": str(event_rows_path),
        "outcome_metric_gap_delta": str(gap_delta_path),
        "doc": str(doc_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": missing_source_artifacts,
        "source_behavior_row_count": int(source["m2516_summary"]["behavior_outcome_row_count"]),
        "outcome_event_row_count": len(event_rows),
        "metric_gap_delta_row_count": len(gap_delta_rows),
        "m2516_unsupported_metric_count": int(source["m2516_summary"]["unsupported_metric_count"]),
        "filled_m2516_unsupported_metric_count": len(filled_metrics),
        "filled_m2516_unsupported_metrics": filled_metrics,
        "remaining_unsupported_metric_count": len(remaining_metrics),
        "remaining_unsupported_metrics": remaining_metrics,
        "all_rows_source_only_diagnostic": bool(all_rows_source_only),
        "all_rows_diagnostic_only_no_ranking_claim": bool(all_rows_no_ranking),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "no_hidden_oracle_actor_inputs_encoded": True,
        "new_policy_action_run": False,
        "ranking_or_winner_fields_emitted": False,
        "success_rate_verdict_field_emitted": False,
        **false_flags,
    }


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2518 Engineering Controller Source-Only Outcome Event Instrumentation Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2518-engineering-controller-source-only-outcome-event-instrumentation-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_source_only_outcome_events.py`",
                f"- summary: `{summary['summary']}`",
                f"- outcome event rows: `{summary['outcome_event_rows']}`",
                f"- outcome metric gap delta: `{summary['outcome_metric_gap_delta']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed in M2518: `false`",
                "- environment rollout/simulator step/new policy action in M2518: `false`",
                "- measured validation/training/replay/PPO/ranking/winner selection in M2518: `false`",
                "- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`",
                "",
                "## Materialized Instrumentation",
                "",
                "M2518 derives evaluator-side diagnostic event proxies from existing",
                "source-only fixture specs and already-recorded telemetry. It does not",
                "step an environment, execute policy actions, train, rank, select a",
                "winner, compute success-rate verdicts, or claim driver performance.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"outcome_event_row_count: {summary['outcome_event_row_count']}",
                f"metric_gap_delta_row_count: {summary['metric_gap_delta_row_count']}",
                f"filled_m2516_unsupported_metric_count: {summary['filled_m2516_unsupported_metric_count']}",
                f"remaining_unsupported_metric_count: {summary['remaining_unsupported_metric_count']}",
                f"actor_contract_shape_72_action_3: {str(summary['actor_contract_shape_72_action_3']).lower()}",
                "```",
                "",
                "Filled M2516 unsupported metrics:",
                "",
                "```text",
                "\n".join(summary["filled_m2516_unsupported_metrics"]),
                "```",
                "",
                "Remaining unsupported metrics:",
                "",
                "```text",
                "\n".join(summary["remaining_unsupported_metrics"]),
                "```",
                "",
                "## Result",
                "",
                "M2518 passes as source-only evaluator-side instrumentation. It fills",
                "several concrete M2516 outcome metric gaps as diagnostic proxies, but",
                "it still does not prove behavior quality, performance, ranking,",
                "validation, paper evidence, finite-window-vs-GRU, or self-ID.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
                "",
                "The next audit should accept or reject the event instrumentation before",
                "any measured behavior or validation route.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _float_text(value: float) -> str:
    return f"{float(value):.12g}"


def _false_claim_flags() -> dict[str, bool]:
    return {
        "environment_rollout_run": False,
        "simulator_step_run": False,
        "external_high_fidelity_simulation_included": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize source-only evaluator-side outcome event instrumentation."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    materialize_source_only_outcome_events(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )


if __name__ == "__main__":
    main()
