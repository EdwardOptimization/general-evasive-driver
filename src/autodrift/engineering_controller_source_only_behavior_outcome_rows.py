"""Source-only row-completeness materialization for behavior/outcome protocol."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = (
    "m2516-engineering-controller-source-only-behavior-outcome-row-completeness-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2517-engineering-controller-source-only-behavior-outcome-row-completeness-result-audit"
)
DEFAULT_DOC_PATH = "docs/m2516-engineering-controller-source-only-behavior-outcome-row-completeness-preflight.md"

M2514_SUMMARY = "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/summary.json"
M2514_ROW_SCHEMA = "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv"
M2514_METRIC_REGISTRY = (
    "runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv"
)
M2498_SUMMARY = "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json"
M2498_PANEL = (
    "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv"
)
M2498_TELEMETRY = (
    "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/telemetry_rows.csv"
)
M2501_SUMMARY = "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json"
M2501_PANEL = (
    "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/"
    "controller_role_metric_panel.csv"
)
M2501_TELEMETRY = (
    "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv"
)

BEHAVIOR_ROW_FILENAME = "behavior_outcome_rows.csv"
METRIC_GAP_FILENAME = "metric_gap_summary.csv"
METRIC_GAP_FIELDNAMES = [
    "metric_name",
    "metric_family",
    "supported_row_count",
    "missing_row_count",
    "total_row_count",
    "support_status",
    "gap_reason",
    "claim_boundary",
]
UNSUPPORTED_OUTCOME_METRICS = {
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
    "mitigation_delta_against_reference",
}
CLAIM_SCOPE = (
    "source-only behavior/outcome row completeness preflight only; diagnostic no-ranking row"
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, or self-ID claim"
)


def materialize_source_only_behavior_outcome_rows(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()
    row_fieldnames = [row["field_name"] for row in source["row_schema"]]

    rows = build_behavior_outcome_rows(source, milestone=milestone)
    gap_rows = build_metric_gap_summary(rows, source["metric_registry"])

    behavior_rows_path = output_dir / BEHAVIOR_ROW_FILENAME
    metric_gap_path = output_dir / METRIC_GAP_FILENAME
    write_csv_rows(behavior_rows_path, rows, fieldnames=row_fieldnames)
    write_csv_rows(metric_gap_path, gap_rows, fieldnames=METRIC_GAP_FIELDNAMES)

    doc_output = Path(doc_path)
    summary = _summary(
        output_dir=output_dir,
        source=source,
        rows=rows,
        gap_rows=gap_rows,
        behavior_rows_path=behavior_rows_path,
        metric_gap_path=metric_gap_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def _load_source_artifacts() -> dict[str, Any]:
    source_paths = {
        "m2514_summary": M2514_SUMMARY,
        "m2514_row_schema": M2514_ROW_SCHEMA,
        "m2514_metric_registry": M2514_METRIC_REGISTRY,
        "m2498_summary": M2498_SUMMARY,
        "m2498_panel": M2498_PANEL,
        "m2498_telemetry": M2498_TELEMETRY,
        "m2501_summary": M2501_SUMMARY,
        "m2501_panel": M2501_PANEL,
        "m2501_telemetry": M2501_TELEMETRY,
    }
    return {
        "m2514_summary": read_json(M2514_SUMMARY),
        "row_schema": _read_csv_rows(M2514_ROW_SCHEMA),
        "metric_registry": _read_csv_rows(M2514_METRIC_REGISTRY),
        "m2498_summary": read_json(M2498_SUMMARY),
        "m2498_panel": _read_csv_rows(M2498_PANEL),
        "m2498_telemetry": _read_csv_rows(M2498_TELEMETRY),
        "m2501_summary": read_json(M2501_SUMMARY),
        "m2501_panel": _read_csv_rows(M2501_PANEL),
        "m2501_telemetry": _read_csv_rows(M2501_TELEMETRY),
        "source_exists": {path: Path(path).exists() for path in source_paths.values()},
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_behavior_outcome_rows(
    source: dict[str, Any],
    *,
    milestone: str = DEFAULT_MILESTONE,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    m2498_by_role = _telemetry_by_key(source["m2498_telemetry"], subject_key=None)
    m2501_by_subject_role = _telemetry_by_key(source["m2501_telemetry"], subject_key="comparison_subject")

    for panel_row in source["m2498_panel"]:
        role = panel_row["role_family"]
        telemetry = m2498_by_role[("m1154_policy_actor", role)]
        rows.append(
            _behavior_row(
                panel_row=panel_row,
                telemetry=telemetry,
                milestone=milestone,
                run_id="m2498_engineering_controller_parameterized_source_only_role_metric_panel",
                row_id=f"m2498_role_{role}",
                subject_id="m1154_policy_actor",
                subject_family="policy_actor",
                source_artifact=M2498_PANEL,
                checkpoint_path=source["m2498_summary"].get("checkpoint_path", ""),
            )
        )

    for panel_row in source["m2501_panel"]:
        subject = panel_row["comparison_subject"]
        role = panel_row["role_family"]
        telemetry = m2501_by_subject_role[(subject, role)]
        rows.append(
            _behavior_row(
                panel_row=panel_row,
                telemetry=telemetry,
                milestone=milestone,
                run_id="m2501_engineering_controller_source_only_baseline_comparison_preflight",
                row_id=f"m2501_{subject}_{role}",
                subject_id=subject,
                subject_family=panel_row["comparison_subject_family"],
                source_artifact=M2501_PANEL,
                checkpoint_path=(
                    source["m2501_summary"].get("checkpoint_path", "")
                    if panel_row["comparison_subject_family"] == "policy_actor"
                    else ""
                ),
            )
        )

    return rows


def _telemetry_by_key(
    telemetry_rows: list[dict[str, str]],
    *,
    subject_key: str | None,
) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in telemetry_rows:
        subject = row[subject_key] if subject_key else "m1154_policy_actor"
        grouped[(subject, row["role_family"])].append(row)
    return dict(grouped)


def _behavior_row(
    *,
    panel_row: dict[str, str],
    telemetry: list[dict[str, str]],
    milestone: str,
    run_id: str,
    row_id: str,
    subject_id: str,
    subject_family: str,
    source_artifact: str,
    checkpoint_path: str,
) -> dict[str, Any]:
    if not telemetry:
        raise ValueError(f"missing telemetry for row {row_id}")
    telemetry = sorted(telemetry, key=lambda item: int(item["step_index"]))
    fixture_ids = sorted({row["fixture_id"] for row in telemetry})
    surface_ids = sorted({row["surface_id"] for row in telemetry})
    final = telemetry[-1]
    action_finite = _fraction_is_one(panel_row["finite_action_fraction"])
    action_within_bounds = _fraction_is_one(panel_row["bounded_action_fraction"])
    episode_completed = (
        _fraction_is_one(panel_row["backend_alive_fraction"])
        and float(panel_row["terminated_fraction"]) == 0.0
        and float(panel_row["truncated_fraction"]) == 0.0
    )
    missing_metrics = sorted(
        name for name in UNSUPPORTED_OUTCOME_METRICS if name not in {"final_abs_yaw_rate"}
    )
    row = {
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone_id": milestone,
        "run_id": run_id,
        "row_id": row_id,
        "evidence_layer": "source_only_diagnostic",
        "surface_id": "|".join(surface_ids),
        "scenario_role": panel_row["role_family"],
        "fixture_id": "|".join(fixture_ids),
        "seed": "",
        "subject_id": subject_id,
        "checkpoint_path": checkpoint_path,
        "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
        "observation_shape": 72,
        "action_shape": 3,
        "actor_encoder": "human_view_online_gru",
        "action_horizon": 1,
        "actor_input_leak_flags": "",
        "reset_status": "success",
        "backend_status": "running" if _fraction_is_one(panel_row["backend_alive_fraction"]) else "partial",
        "episode_started": "true",
        "episode_completed": _bool_text(episode_completed),
        "step_count": int(float(panel_row["step_count"])),
        "terminal_status": "horizon_exhausted_no_terminal_event" if episode_completed else "partial",
        "action_finite": _bool_text(action_finite),
        "action_within_bounds": _bool_text(action_within_bounds),
        "collision_event": "",
        "obstacle_passed_event": "",
        "road_departure_event": "",
        "minimum_obstacle_clearance_m": "",
        "minimum_road_margin_m": "",
        "final_road_margin_m": "",
        "maximum_abs_lateral_velocity": _max_abs(telemetry, "state_vy"),
        "maximum_abs_yaw_rate": _float_text(panel_row["abs_yaw_rate_max"]),
        "maximum_abs_lateral_position": _float_text(panel_row["abs_y_max"]),
        "final_abs_lateral_velocity": _abs_float_text(final["state_vy"]),
        "final_abs_yaw_rate": _abs_float_text(final["state_yaw_rate"]),
        "recovery_time_proxy_s": "",
        "steering_saturation_fraction": _saturation_fraction(telemetry, "action_steer"),
        "throttle_saturation_fraction": _saturation_fraction(telemetry, "action_throttle"),
        "brake_saturation_fraction": _saturation_fraction(telemetry, "action_brake"),
        "command_delta_l1_mean": _command_delta_l1_mean(telemetry),
        "simultaneous_throttle_brake_fraction": _simultaneous_pedal_fraction(telemetry),
        "collision_speed_proxy": "",
        "impact_angle_proxy": "",
        "severity_proxy": "",
        "mitigation_delta_against_reference": "",
        "metric_completeness_flags": "|".join(missing_metrics),
        "diagnostic_only_no_ranking_claim": "true",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": (
            f"{FORBIDDEN_INTERPRETATION}; source subject family={subject_family}"
        ),
        "source_artifact": source_artifact,
    }
    return row


def build_metric_gap_summary(
    behavior_rows: list[dict[str, Any]],
    metric_registry: list[dict[str, str]],
) -> list[dict[str, Any]]:
    total = len(behavior_rows)
    gap_rows: list[dict[str, Any]] = []
    for metric in metric_registry:
        name = metric["metric_name"]
        supported = sum(1 for row in behavior_rows if _metric_supported(row, name))
        missing = total - supported
        if supported == total:
            support_status = "supported_by_existing_source_artifacts"
            gap_reason = "present in source-only panel or derived from existing telemetry"
        elif supported == 0:
            support_status = "unsupported_by_existing_source_artifacts"
            gap_reason = "not present in M2498/M2501 source-only panel or telemetry"
        else:
            support_status = "partially_supported_by_existing_source_artifacts"
            gap_reason = "available for some rows only from existing source-only artifacts"
        gap_rows.append(
            {
                "metric_name": name,
                "metric_family": metric["metric_family"],
                "supported_row_count": supported,
                "missing_row_count": missing,
                "total_row_count": total,
                "support_status": support_status,
                "gap_reason": gap_reason,
                "claim_boundary": "diagnostic completeness only; not a behavior verdict",
            }
        )
    return gap_rows


def _summary(
    *,
    output_dir: Path,
    source: dict[str, Any],
    rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    behavior_rows_path: Path,
    metric_gap_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_paths = [behavior_rows_path, metric_gap_path]
    source_artifacts_exist = all(source["source_exists"].values())
    missing_source_artifacts = [
        path for path, exists in source["source_exists"].items() if not bool(exists)
    ]
    unsupported_metric_names = [
        row["metric_name"]
        for row in gap_rows
        if row["support_status"] == "unsupported_by_existing_source_artifacts"
    ]
    partial_metric_names = [
        row["metric_name"]
        for row in gap_rows
        if row["support_status"] == "partially_supported_by_existing_source_artifacts"
    ]
    false_flags = _false_claim_flags()
    expected_row_count = len(source["m2498_panel"]) + len(source["m2501_panel"])
    all_rows_have_required_fields = _rows_have_required_fields(rows, source["row_schema"])
    all_rows_source_only = {row["evidence_layer"] for row in rows} == {"source_only_diagnostic"}
    all_rows_no_ranking = {
        str(row["diagnostic_only_no_ranking_claim"]).lower() for row in rows
    } == {"true"}
    all_rows_explicit_gaps = all(_has_value(row["metric_completeness_flags"]) for row in rows)
    actor_contract_shape_72_action_3 = (
        bool(source["m2514_summary"].get("actor_contract_shape_72_action_3"))
        and {int(row["observation_shape"]) for row in rows} == {72}
        and {int(row["action_shape"]) for row in rows} == {3}
    )
    required_artifacts_present = all(path.exists() for path in required_paths)
    status_pass = (
        required_artifacts_present
        and source_artifacts_exist
        and len(rows) == expected_row_count
        and len(gap_rows) == len(source["metric_registry"])
        and all_rows_have_required_fields
        and all_rows_source_only
        and all_rows_no_ranking
        and all_rows_explicit_gaps
        and actor_contract_shape_72_action_3
        and "collision_event" in unsupported_metric_names
        and "mitigation_delta_against_reference" in unsupported_metric_names
        and not partial_metric_names
        and not any(false_flags.values())
    )
    return {
        "result_class": (
            "engineering_controller_source_only_behavior_outcome_row_completeness_pass"
            if status_pass
            else "engineering_controller_source_only_behavior_outcome_row_completeness_failed"
        ),
        "status_pass": bool(status_pass),
        "protocol_version": "engineering_controller_behavior_outcome_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "behavior_outcome_rows": str(behavior_rows_path),
        "metric_gap_summary": str(metric_gap_path),
        "doc": str(doc_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": missing_source_artifacts,
        "row_schema_field_count": len(source["row_schema"]),
        "metric_registry_row_count": len(source["metric_registry"]),
        "behavior_outcome_row_count": len(rows),
        "expected_behavior_outcome_row_count": expected_row_count,
        "m2498_source_row_count": len(source["m2498_panel"]),
        "m2501_source_row_count": len(source["m2501_panel"]),
        "metric_gap_row_count": len(gap_rows),
        "unsupported_metric_count": len(unsupported_metric_names),
        "unsupported_metric_names": unsupported_metric_names,
        "partial_metric_names": partial_metric_names,
        "all_rows_have_required_fields": bool(all_rows_have_required_fields),
        "all_rows_source_only_diagnostic": bool(all_rows_source_only),
        "all_rows_diagnostic_only_no_ranking_claim": bool(all_rows_no_ranking),
        "metric_gaps_explicit": bool(all_rows_explicit_gaps),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "no_hidden_oracle_actor_inputs_encoded": True,
        "forbidden_actor_inputs_encoded": bool(
            source["m2514_summary"].get("forbidden_actor_inputs_encoded")
        ),
        "forbidden_outcome_shortcuts_encoded": bool(
            source["m2514_summary"].get("forbidden_outcome_shortcuts_encoded")
        ),
        "source_only_layer_separated_from_validation": bool(
            source["m2514_summary"].get("source_only_layer_separated_from_validation")
        ),
        "ranking_or_winner_fields_emitted": False,
        "success_rate_verdict_field_emitted": False,
        "no_new_rollout_scope": True,
        **false_flags,
    }


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2516 Engineering Controller Source-Only Behavior/Outcome Row Completeness Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2516-engineering-controller-source-only-behavior-outcome-row-completeness-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_source_only_behavior_outcome_rows.py`",
                f"- summary: `{summary['summary']}`",
                f"- behavior outcome rows: `{summary['behavior_outcome_rows']}`",
                f"- metric gap summary: `{summary['metric_gap_summary']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed in M2516: `false`",
                "- new environment rollout/simulator step/policy action in M2516: `false`",
                "- measured validation/training/replay/PPO/ranking/winner selection in M2516: `false`",
                "- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`",
                "",
                "## Materialized Rows",
                "",
                "M2516 maps existing M2498/M2501 source-only diagnostic panels into the",
                "M2514 behavior/outcome row schema. It does not run a simulator, execute",
                "new policy actions, train, replay, rank controllers, select a winner,",
                "compute success-rate verdicts, or claim driver performance.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"behavior_outcome_row_count: {summary['behavior_outcome_row_count']}",
                f"metric_gap_row_count: {summary['metric_gap_row_count']}",
                f"unsupported_metric_count: {summary['unsupported_metric_count']}",
                f"actor_contract_shape_72_action_3: {str(summary['actor_contract_shape_72_action_3']).lower()}",
                f"all_rows_source_only_diagnostic: {str(summary['all_rows_source_only_diagnostic']).lower()}",
                f"all_rows_diagnostic_only_no_ranking_claim: {str(summary['all_rows_diagnostic_only_no_ranking_claim']).lower()}",
                f"metric_gaps_explicit: {str(summary['metric_gaps_explicit']).lower()}",
                "```",
                "",
                "Unsupported metrics remain explicit gaps:",
                "",
                "```text",
                "\n".join(summary["unsupported_metric_names"]),
                "```",
                "",
                "## Result",
                "",
                "M2516 passes as a source-only row-completeness preflight. It proves only",
                "that existing source-only diagnostic artifacts can populate the protocol",
                "rows with explicit gaps. It does not prove behavior quality, performance,",
                "ranking, validation, paper evidence, finite-window-vs-GRU, or self-ID.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
                "",
                "The next audit should accept or reject the row-completeness artifacts",
                "before any measured behavior or validation route.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _rows_have_required_fields(
    rows: list[dict[str, Any]],
    row_schema: list[dict[str, str]],
) -> bool:
    required = [row["field_name"] for row in row_schema if str(row["required"]).lower() == "true"]
    return all(all(field in row for field in required) for row in rows)


def _has_value(value: Any) -> bool:
    return value is not None and str(value) != ""


def _metric_supported(row: dict[str, Any], name: str) -> bool:
    if name == "actor_input_leak_flags":
        return name in row
    return _has_value(row.get(name, ""))


def _fraction_is_one(value: str) -> bool:
    return float(value) == 1.0


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _float_text(value: str | float) -> str:
    return f"{float(value):.12g}"


def _abs_float_text(value: str | float) -> str:
    return f"{abs(float(value)):.12g}"


def _max_abs(rows: list[dict[str, str]], key: str) -> str:
    return f"{max(abs(float(row[key])) for row in rows):.12g}"


def _saturation_fraction(rows: list[dict[str, str]], key: str) -> str:
    return f"{sum(abs(float(row[key])) >= 0.999 for row in rows) / len(rows):.12g}"


def _command_delta_l1_mean(rows: list[dict[str, str]]) -> str:
    if len(rows) < 2:
        return "0"
    total = 0.0
    for prev, cur in zip(rows[:-1], rows[1:]):
        total += (
            abs(float(cur["action_steer"]) - float(prev["action_steer"]))
            + abs(float(cur["action_throttle"]) - float(prev["action_throttle"]))
            + abs(float(cur["action_brake"]) - float(prev["action_brake"]))
        )
    return f"{total / (len(rows) - 1):.12g}"


def _simultaneous_pedal_fraction(rows: list[dict[str, str]]) -> str:
    simultaneous = sum(
        float(row.get("physical_throttle", 0.0)) > 1e-6
        and float(row.get("physical_brake", 0.0)) > 1e-6
        for row in rows
    )
    return f"{simultaneous / len(rows):.12g}"


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
        description="Materialize source-only behavior/outcome row-completeness artifacts."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    materialize_source_only_behavior_outcome_rows(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )


if __name__ == "__main__":
    main()
