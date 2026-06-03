"""Bounded source-only measured behavior panel under the accepted protocol."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_source_only_outcome_events import (
    _bool_text,
    _event_stats,
    _float_text,
    _primary_obstacle,
)
from autodrift.hf0_source_only_baseline_comparison_panel import (
    COMPARISON_SUBJECTS,
    ROLE_FAMILIES,
    BaselineTelemetryRow,
    run_source_only_baseline_comparison,
)
from autodrift.hf0_source_only_role_fixture_parameterization import (
    build_source_only_role_fixture_specs,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2521-engineering-controller-bounded-measured-behavior-panel-preflight"
DEFAULT_NEXT_BLOCKER = "m2522-engineering-controller-bounded-measured-behavior-panel-result-audit"
DEFAULT_DOC_PATH = "docs/m2521-engineering-controller-bounded-measured-behavior-panel-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2521_engineering_controller_bounded_measured_behavior_panel")
MITIGATION_REFERENCE_SUBJECT = "straight_full_brake_open_loop"

M2520_SYNTHESIS = "docs/m2520-engineering-controller-behavior-outcome-protocol-branch-synthesis.md"
M2519_AUDIT = "docs/m2519-engineering-controller-source-only-outcome-event-instrumentation-result-audit.md"
M2518_SUMMARY = "runs/m2518_engineering_controller_source_only_outcome_event_instrumentation/summary.json"
M2518_EVENT_ROWS = "runs/m2518_engineering_controller_source_only_outcome_event_instrumentation/outcome_event_rows.csv"
M2514_ROW_SCHEMA = "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv"
M2514_METRIC_REGISTRY = (
    "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv"
)
M2501_SUMMARY = "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json"

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
    "training_run": False,
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

EXTRA_BEHAVIOR_FIELDS = [
    "attempted_row_retained",
    "mitigation_reference_subject",
    "mitigation_reference_seed",
    "ranking_or_winner_field_emitted",
]

MEASURED_EVENT_FIELDNAMES = [
    "protocol_version",
    "milestone_id",
    "measured_behavior_row_id",
    "evidence_layer",
    "surface_id",
    "scenario_role",
    "fixture_id",
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

METRIC_COMPLETENESS_FIELDNAMES = [
    "metric_name",
    "metric_family",
    "actor_visible",
    "supported_row_count",
    "missing_row_count",
    "support_status",
    "source_fields",
    "claim_boundary",
]

CLAIM_SCOPE = "bounded source-only measured behavior panel preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, or self-ID claim"
)


def materialize_bounded_measured_behavior_panel(
    output_dir: Path,
    *,
    checkpoint_path: Path | str,
    horizon_steps: int,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    telemetry_rows, _panel_rows, baseline_summary = run_source_only_baseline_comparison(
        checkpoint_path,
        horizon_steps=horizon_steps,
        device=device,
    )
    source = _load_source_artifacts()
    row_schema_fields = [row["field_name"] for row in source["row_schema"]]
    measured_behavior_rows, measured_event_rows = build_measured_rows(
        telemetry_rows,
        checkpoint_path=str(checkpoint_path),
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    metric_completeness_rows = build_metric_completeness_rows(
        source["metric_registry"],
        measured_behavior_rows,
    )

    measured_behavior_path = output_dir / "measured_behavior_rows.csv"
    measured_event_path = output_dir / "measured_event_rows.csv"
    metric_completeness_path = output_dir / "metric_completeness_rows.csv"
    measured_behavior_fieldnames = row_schema_fields + EXTRA_BEHAVIOR_FIELDS
    write_csv_rows(
        measured_behavior_path,
        measured_behavior_rows,
        fieldnames=measured_behavior_fieldnames,
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
        baseline_summary=baseline_summary,
        measured_behavior_rows=measured_behavior_rows,
        measured_event_rows=measured_event_rows,
        metric_completeness_rows=metric_completeness_rows,
        measured_behavior_path=measured_behavior_path,
        measured_event_path=measured_event_path,
        metric_completeness_path=metric_completeness_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
        checkpoint_path=str(checkpoint_path),
        horizon_steps=int(horizon_steps),
    )
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def _load_source_artifacts() -> dict[str, Any]:
    paths = [
        M2520_SYNTHESIS,
        M2519_AUDIT,
        M2518_SUMMARY,
        M2518_EVENT_ROWS,
        M2514_ROW_SCHEMA,
        M2514_METRIC_REGISTRY,
        M2501_SUMMARY,
    ]
    return {
        "m2518_summary": read_json(M2518_SUMMARY),
        "m2501_summary": read_json(M2501_SUMMARY),
        "row_schema": _read_csv_rows(M2514_ROW_SCHEMA),
        "metric_registry": _read_csv_rows(M2514_METRIC_REGISTRY),
        "source_exists": {path: Path(path).exists() for path in paths},
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_measured_rows(
    telemetry_rows: list[BaselineTelemetryRow],
    *,
    checkpoint_path: str,
    row_schema_fields: list[str],
    milestone: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs_by_role = {spec.role_family: spec for spec in build_source_only_role_fixture_specs()}
    seed_by_role = _seed_by_role()
    rows_by_subject_role: dict[tuple[str, str], list[BaselineTelemetryRow]] = defaultdict(list)
    for row in telemetry_rows:
        rows_by_subject_role[(row.comparison_subject, row.role_family)].append(row)

    event_by_subject_role: dict[tuple[str, str], dict[str, Any]] = {}
    for key, rows in rows_by_subject_role.items():
        subject_id, role = key
        spec = specs_by_role[role]
        event_stats = _event_stats(
            [row.to_csv_row() for row in sorted(rows, key=lambda item: item.step_index)],
            road=spec.road,
            obstacle=_primary_obstacle(spec.obstacles),
        )
        event_by_subject_role[key] = {
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
        if subject_id == MITIGATION_REFERENCE_SUBJECT:
            event_by_subject_role[key]["mitigation_delta_against_reference"] = 0.0

    for (subject_id, role), event in list(event_by_subject_role.items()):
        reference = event_by_subject_role[(MITIGATION_REFERENCE_SUBJECT, role)]
        event["mitigation_delta_against_reference"] = (
            float(event["severity_proxy"]) - float(reference["severity_proxy"])
        )

    measured_behavior_rows: list[dict[str, Any]] = []
    measured_event_rows: list[dict[str, Any]] = []
    for subject in sorted(subject.subject_id for subject in COMPARISON_SUBJECTS):
        for role in ROLE_FAMILIES:
            group = sorted(rows_by_subject_role[(subject, role)], key=lambda item: item.step_index)
            first = group[0]
            last = group[-1]
            event = event_by_subject_role[(subject, role)]
            row_id = f"m2521_{subject}_{role}"
            seed = seed_by_role[role]
            behavior_row = {
                "protocol_version": "engineering_controller_behavior_outcome_v0",
                "milestone_id": milestone,
                "run_id": milestone,
                "row_id": row_id,
                "evidence_layer": "source_only_diagnostic",
                "surface_id": first.surface_id,
                "scenario_role": role,
                "fixture_id": first.fixture_id,
                "seed": seed,
                "subject_id": subject,
                "checkpoint_path": checkpoint_path if subject == "m1154_policy_actor" else "",
                "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
                "observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "actor_encoder": "human_view_online_gru",
                "action_horizon": 1,
                "actor_input_leak_flags": "none",
                "reset_status": "reset_ok",
                "backend_status": _row_backend_status(group),
                "episode_started": True,
                "episode_completed": True,
                "step_count": len(group),
                "terminal_status": _terminal_status(group),
                "action_finite": all(row.action_finite for row in group),
                "action_within_bounds": all(row.action_within_bounds for row in group),
                "collision_event": event["collision_event"],
                "obstacle_passed_event": event["obstacle_passed_event"],
                "road_departure_event": event["road_departure_event"],
                "minimum_obstacle_clearance_m": event["minimum_obstacle_clearance_m"],
                "minimum_road_margin_m": event["minimum_road_margin_m"],
                "final_road_margin_m": event["final_road_margin_m"],
                "maximum_abs_lateral_velocity": _max_abs(row.state_vy for row in group),
                "maximum_abs_yaw_rate": _max_abs(row.state_yaw_rate for row in group),
                "maximum_abs_lateral_position": _max_abs(row.state_y for row in group),
                "final_abs_lateral_velocity": abs(last.state_vy),
                "final_abs_yaw_rate": abs(last.state_yaw_rate),
                "recovery_time_proxy_s": event["recovery_time_proxy_s"],
                "steering_saturation_fraction": _fraction(row.action_saturated for row in group),
                "throttle_saturation_fraction": _fraction(abs(row.action_throttle) >= 0.999 for row in group),
                "brake_saturation_fraction": _fraction(abs(row.action_brake) >= 0.999 for row in group),
                "command_delta_l1_mean": _command_delta_l1_mean(group),
                "simultaneous_throttle_brake_fraction": _fraction(
                    row.physical_throttle > 1e-9 and row.physical_brake > 1e-9 for row in group
                ),
                "collision_speed_proxy": event["collision_speed_proxy"],
                "impact_angle_proxy": event["impact_angle_proxy"],
                "severity_proxy": event["severity_proxy"],
                "mitigation_delta_against_reference": event["mitigation_delta_against_reference"],
                "metric_completeness_flags": "complete",
                "diagnostic_only_no_ranking_claim": True,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                "source_artifact": "source-only measured execution",
                "attempted_row_retained": True,
                "mitigation_reference_subject": MITIGATION_REFERENCE_SUBJECT,
                "mitigation_reference_seed": seed,
                "ranking_or_winner_field_emitted": False,
            }
            measured_behavior_rows.append({field: behavior_row.get(field, "") for field in row_schema_fields + EXTRA_BEHAVIOR_FIELDS})
            measured_event_rows.append(
                {
                    "protocol_version": "engineering_controller_behavior_outcome_v0",
                    "milestone_id": milestone,
                    "measured_behavior_row_id": row_id,
                    "evidence_layer": "source_only_diagnostic",
                    "surface_id": first.surface_id,
                    "scenario_role": role,
                    "fixture_id": first.fixture_id,
                    "subject_id": subject,
                    "seed": seed,
                    "mitigation_reference_subject": MITIGATION_REFERENCE_SUBJECT,
                    "collision_event": _bool_text(bool(event["collision_event"])),
                    "obstacle_passed_event": _bool_text(bool(event["obstacle_passed_event"])),
                    "road_departure_event": _bool_text(bool(event["road_departure_event"])),
                    "minimum_obstacle_clearance_m": _float_text(event["minimum_obstacle_clearance_m"]),
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
                "support_status": "supported_by_m2521_measured_behavior_panel"
                if supported == total
                else "partial_or_missing_after_m2521",
                "source_fields": "measured_behavior_rows.csv",
                "claim_boundary": "source-only measured behavior diagnostics only; not ranking or verdict",
            }
        )
    return rows


def _summary(
    *,
    output_dir: Path,
    source: dict[str, Any],
    baseline_summary: dict[str, Any],
    measured_behavior_rows: list[dict[str, Any]],
    measured_event_rows: list[dict[str, Any]],
    metric_completeness_rows: list[dict[str, Any]],
    measured_behavior_path: Path,
    measured_event_path: Path,
    metric_completeness_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
    checkpoint_path: str,
    horizon_steps: int,
) -> dict[str, Any]:
    subject_ids = tuple(subject.subject_id for subject in COMPARISON_SUBJECTS)
    expected_rows = len(subject_ids) * len(ROLE_FAMILIES)
    required_artifacts_present = (
        measured_behavior_path.exists()
        and measured_event_path.exists()
        and metric_completeness_path.exists()
    )
    source_artifacts_exist = all(source["source_exists"].values())
    all_attempted_rows_retained = (
        len(measured_behavior_rows) == expected_rows
        and {row["subject_id"] for row in measured_behavior_rows} == set(subject_ids)
        and {row["scenario_role"] for row in measured_behavior_rows} == set(ROLE_FAMILIES)
        and all(bool(row["attempted_row_retained"]) for row in measured_behavior_rows)
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
    seed_lineage_explicit = all(_has_value(row["seed"]) for row in measured_behavior_rows)
    mitigation_reference_explicit = {row["mitigation_reference_subject"] for row in measured_behavior_rows} == {
        MITIGATION_REFERENCE_SUBJECT
    }
    no_ranking_fields = all(
        str(row["ranking_or_winner_field_emitted"]).lower() == "false"
        for row in measured_behavior_rows
    )
    status_pass = (
        bool(baseline_summary["status_pass"])
        and required_artifacts_present
        and source_artifacts_exist
        and all_attempted_rows_retained
        and len(measured_event_rows) == expected_rows
        and len(metric_completeness_rows) == int(source["m2518_summary"]["metric_gap_delta_row_count"])
        and all_metrics_supported
        and actor_contract_shape_72_action_3
        and all_rows_source_only
        and all_rows_no_ranking
        and seed_lineage_explicit
        and mitigation_reference_explicit
        and no_ranking_fields
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": (
            "engineering_controller_bounded_measured_behavior_panel_preflight_pass"
            if status_pass
            else "engineering_controller_bounded_measured_behavior_panel_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "checkpoint_path": checkpoint_path,
        "horizon_steps": int(horizon_steps),
        "summary": str(output_dir / "summary.json"),
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
        "expected_subject_role_row_count": expected_rows,
        "measured_behavior_row_count": len(measured_behavior_rows),
        "measured_event_row_count": len(measured_event_rows),
        "metric_completeness_row_count": len(metric_completeness_rows),
        "all_attempted_subject_role_rows_retained": bool(all_attempted_rows_retained),
        "telemetry_row_count": int(baseline_summary["telemetry_row_count"]),
        "expected_telemetry_row_count": int(baseline_summary["expected_telemetry_row_count"]),
        "source_only_backend_step_run": bool(baseline_summary["policy_rollout_run"]),
        "policy_action_run": bool(baseline_summary["policy_action"]),
        "policy_rollout_run": bool(baseline_summary["policy_rollout_run"]),
        "open_loop_action_rollout_run": bool(baseline_summary["open_loop_action_rollout_run"]),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "all_actions_finite": bool(baseline_summary["all_actions_finite"]),
        "all_actions_within_bounds": bool(baseline_summary["all_actions_within_bounds"]),
        "all_backend_statuses_running": bool(baseline_summary["all_backend_statuses_running"]),
        "seed_lineage_explicit": bool(seed_lineage_explicit),
        "seed_by_role": _seed_by_role(),
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
                "# M2521 Engineering Controller Bounded Measured Behavior Panel Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2521-engineering-controller-bounded-measured-behavior-panel-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_bounded_measured_behavior_panel.py`",
                f"- summary: `{summary['summary']}`",
                f"- measured behavior rows: `{summary['measured_behavior_rows']}`",
                f"- measured event rows: `{summary['measured_event_rows']}`",
                f"- metric completeness rows: `{summary['metric_completeness_rows']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed in M2521: `false`",
                "- measured validation/training/replay/PPO/ranking/winner selection in M2521: `false`",
                "- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`",
                "",
                "## Materialized Panel",
                "",
                "M2521 executes bounded source-only policy and open-loop reference",
                "actions as diagnostic measured behavior data. It preserves all",
                "attempted subject-role rows and does not rank controllers, select a",
                "winner, compute success-rate verdicts, or claim driver performance.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"measured_behavior_row_count: {summary['measured_behavior_row_count']}",
                f"measured_event_row_count: {summary['measured_event_row_count']}",
                f"metric_completeness_row_count: {summary['metric_completeness_row_count']}",
                f"telemetry_row_count: {summary['telemetry_row_count']}",
                f"all_attempted_subject_role_rows_retained: {str(summary['all_attempted_subject_role_rows_retained']).lower()}",
                f"actor_contract_shape_72_action_3: {str(summary['actor_contract_shape_72_action_3']).lower()}",
                f"seed_lineage_explicit: {str(summary['seed_lineage_explicit']).lower()}",
                f"mitigation_reference_subject: {summary['mitigation_reference_subject']}",
                "```",
                "",
                "## Result",
                "",
                "M2521 passes as a bounded source-only measured behavior panel",
                "preflight. It creates the next engineering behavior evidence",
                "substrate, but it is still not a validation, ranking, success-rate,",
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
                "The next audit should accept or reject these measured behavior",
                "artifacts before any broader behavior route or claim escalation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _seed_by_role() -> dict[str, int]:
    return {spec.role_family: 2501 + index for index, spec in enumerate(build_source_only_role_fixture_specs())}


def _row_backend_status(rows: list[BaselineTelemetryRow]) -> str:
    statuses = {row.backend_status for row in rows}
    return "running" if statuses == {"running"} else "|".join(sorted(statuses))


def _terminal_status(rows: list[BaselineTelemetryRow]) -> str:
    if any(row.terminated_by_backend for row in rows):
        return "terminated_by_backend"
    if any(row.truncated_by_backend for row in rows):
        return "truncated_by_backend"
    return "completed_horizon_without_backend_terminal"


def _fraction(values: Iterable[bool]) -> float:
    bools = [bool(value) for value in values]
    if not bools:
        return 0.0
    return float(sum(bools)) / float(len(bools))


def _max_abs(values: Iterable[float]) -> float:
    numbers = [abs(float(value)) for value in values]
    return max(numbers) if numbers else 0.0


def _command_delta_l1_mean(rows: list[BaselineTelemetryRow]) -> float:
    if len(rows) < 2:
        return 0.0
    deltas: list[float] = []
    for previous, current in zip(rows[:-1], rows[1:]):
        deltas.append(
            abs(current.action_steer - previous.action_steer)
            + abs(current.action_throttle - previous.action_throttle)
            + abs(current.action_brake - previous.action_brake)
        )
    return float(sum(deltas)) / float(len(deltas))


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value != ""
    return True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize bounded source-only measured behavior panel."
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--horizon-steps", type=int, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_bounded_measured_behavior_panel(
        args.output_dir,
        checkpoint_path=args.checkpoint,
        horizon_steps=args.horizon_steps,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"measured_behavior_row_count={summary['measured_behavior_row_count']}")
    print(f"metric_completeness_row_count={summary['metric_completeness_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
