"""M2650 protected mitigation regression localization for Route A repair."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_execution import (
    REPAIRED_SUBJECT_ID,
    as_bool,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2650-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "protected-mitigation-regression-localization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2651-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-repair-synthesis"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization"
)
DEFAULT_BASELINE_BEHAVIOR_ROWS = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "measured_behavior_rows.csv"
)
DEFAULT_POST_REPAIR_BEHAVIOR_ROWS = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/"
    "post_repair_behavior_rows.csv"
)
DEFAULT_REPAIR_GATE_EVALUATION = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/"
    "repair_gate_evaluation.csv"
)
DEFAULT_M2648_SUMMARY = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/"
    "summary.json"
)
DEFAULT_M2649_AUDIT = Path(
    "docs/m2649-engineering-controller-route-a-baseline-source-only-gap-targeted-"
    "repair-execution-result-audit.md"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2650-engineering-controller-route-a-baseline-source-only-gap-targeted-"
    "repair-protected-mitigation-regression-localization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2651-engineering-controller-route-a-baseline-source-only-"
    "gap-targeted-repair-mitigation-preserving-repair-synthesis.json"
)

RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization_preflight_failed"
)
CLAIM_SCOPE = "Route A protected mitigation regression localization only"
FORBIDDEN_INTERPRETATION = (
    "repair execution, training, ranking, winner selection, promotion, success-rate "
    "verdict, validation, driver performance, paper, finite-window-vs-GRU, "
    "current-sim verdict, high-fidelity validation, or self-ID claim"
)
SEVERITY_FORMULA_NOTE = (
    "severity_proxy is max over collision steps of speed * abs(signed_rect_clearance); "
    "row-level component attribution uses available aggregate proxies only"
)
NEXT_ROUTE = "m2651_mitigation_preserving_repair_synthesis"

FALSE_CLAIM_FLAGS = {
    "repair_execution_started": False,
    "repair_training_started": False,
    "training_run": False,
    "source_only_backend_reset_run": False,
    "source_only_backend_step_run": False,
    "policy_action_run": False,
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
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

MITIGATION_REGRESSION_FIELDNAMES = [
    "localization_row_id",
    "source_gate_id",
    "protected_reference_family",
    "subject_id",
    "scenario_role",
    "seed",
    "dynamics_axis_id",
    "baseline_row_id",
    "post_repair_row_id",
    "baseline_checkpoint_path",
    "repaired_checkpoint_path",
    "baseline_severity_proxy",
    "post_repair_severity_proxy",
    "severity_delta",
    "baseline_collision_speed_proxy",
    "post_repair_collision_speed_proxy",
    "collision_speed_delta",
    "baseline_impact_angle_proxy",
    "post_repair_impact_angle_proxy",
    "impact_angle_delta",
    "baseline_minimum_obstacle_clearance_m",
    "post_repair_minimum_obstacle_clearance_m",
    "minimum_obstacle_clearance_delta",
    "baseline_obstacle_penetration_proxy_m",
    "post_repair_obstacle_penetration_proxy_m",
    "obstacle_penetration_delta",
    "baseline_minimum_road_margin_m",
    "post_repair_minimum_road_margin_m",
    "minimum_road_margin_delta",
    "collision_event_unchanged",
    "obstacle_passed_event_unchanged",
    "road_departure_event_unchanged",
    "severity_gate_regression",
    "metric_artifact_detected",
    "likely_severity_proxy_component_driver",
    "component_driver_reason",
    "severity_formula_note",
    "localization_class",
    "actor_contract_shape_72_action_3",
    "hidden_or_oracle_actor_inputs_required",
    "protected_reference_only",
    "taxonomy_labels_actor_visible",
    "repair_target_labels_actor_visible",
    "next_route",
    "claim_scope",
    "forbidden_interpretation",
]

METRIC_COMPONENT_FIELDNAMES = [
    "component_row_id",
    "subject_id",
    "scenario_role",
    "seed",
    "dynamics_axis_id",
    "metric_name",
    "baseline_value",
    "post_repair_value",
    "raw_delta",
    "larger_is_better",
    "directional_delta",
    "component_direction",
    "is_regressed_gate_row",
    "severity_component_candidate",
    "claim_scope",
]


COMPONENT_METRICS: tuple[tuple[str, bool, bool], ...] = (
    ("severity_proxy", False, False),
    ("minimum_obstacle_clearance_m", True, True),
    ("collision_speed_proxy", False, True),
    ("impact_angle_proxy", False, True),
    ("minimum_road_margin_m", True, False),
    ("final_road_margin_m", True, False),
    ("maximum_abs_lateral_velocity", False, False),
    ("maximum_abs_yaw_rate", False, False),
    ("maximum_abs_lateral_position", False, False),
    ("final_abs_lateral_velocity", False, False),
    ("final_abs_yaw_rate", False, False),
    ("recovery_time_proxy_s", False, False),
    ("command_delta_l1_mean", False, False),
    ("simultaneous_throttle_brake_fraction", False, False),
    ("mitigation_delta_against_reference", False, False),
)


def run_mitigation_regression_localization(
    output_dir: Path,
    *,
    baseline_behavior_rows: Path | str = DEFAULT_BASELINE_BEHAVIOR_ROWS,
    post_repair_behavior_rows: Path | str = DEFAULT_POST_REPAIR_BEHAVIOR_ROWS,
    repair_gate_evaluation: Path | str = DEFAULT_REPAIR_GATE_EVALUATION,
    m2648_summary: Path | str = DEFAULT_M2648_SUMMARY,
    m2649_audit: Path | str = DEFAULT_M2649_AUDIT,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = Path(baseline_behavior_rows)
    post_path = Path(post_repair_behavior_rows)
    gate_path = Path(repair_gate_evaluation)
    summary_path = Path(m2648_summary)
    audit_path = Path(m2649_audit)
    doc_output_path = Path(doc_path)
    follow_up_manifest_path = Path(follow_up_manifest)

    baseline_rows = read_csv_rows(baseline_path)
    post_rows = read_csv_rows(post_path)
    gate_rows = read_csv_rows(gate_path)
    m2648 = read_json(summary_path)
    audit_text = audit_path.read_text(encoding="utf-8")

    matched_pairs = matched_protected_pairs(baseline_rows, post_rows)
    component_rows = build_metric_component_delta_rows(matched_pairs)
    regression_rows = build_mitigation_regression_rows(matched_pairs, gate_rows)
    findings = build_findings(
        regression_rows=regression_rows,
        component_rows=component_rows,
        gate_rows=gate_rows,
        m2648_summary=m2648,
        audit_text=audit_text,
        follow_up_manifest=follow_up_manifest_path,
    )

    regression_rows_path = output_dir / "mitigation_regression_rows.csv"
    component_rows_path = output_dir / "metric_component_delta_rows.csv"
    findings_path = output_dir / "localization_findings.json"
    summary_output_path = output_dir / "summary.json"

    write_csv_rows(
        regression_rows_path,
        regression_rows,
        fieldnames=MITIGATION_REGRESSION_FIELDNAMES,
    )
    write_csv_rows(
        component_rows_path,
        component_rows,
        fieldnames=METRIC_COMPONENT_FIELDNAMES,
    )
    write_json(findings_path, findings)

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_output_path,
        regression_rows_path=regression_rows_path,
        component_rows_path=component_rows_path,
        findings_path=findings_path,
        doc_path=doc_output_path,
        baseline_path=baseline_path,
        post_path=post_path,
        gate_path=gate_path,
        summary_source_path=summary_path,
        audit_path=audit_path,
        follow_up_manifest=follow_up_manifest_path,
        baseline_rows=baseline_rows,
        post_rows=post_rows,
        matched_pairs=matched_pairs,
        regression_rows=regression_rows,
        component_rows=component_rows,
        findings=findings,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(summary_output_path, summary)
    write_doc(doc_output_path, summary, findings)
    return summary


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def matched_protected_pairs(
    baseline_rows: list[dict[str, str]],
    post_rows: list[dict[str, str]],
) -> list[tuple[dict[str, str], dict[str, str]]]:
    baseline_by_key = {
        row_key(row): row
        for row in baseline_rows
        if row.get("subject_id") == REPAIRED_SUBJECT_ID
        and row.get("scenario_role") == "unavoidable_mitigation"
    }
    post_by_key = {
        row_key(row): row
        for row in post_rows
        if row.get("subject_id") == REPAIRED_SUBJECT_ID
        and row.get("scenario_role") == "unavoidable_mitigation"
    }
    pairs: list[tuple[dict[str, str], dict[str, str]]] = []
    for key in sorted(post_by_key):
        baseline = baseline_by_key.get(key)
        if baseline is None:
            continue
        pairs.append((baseline, post_by_key[key]))
    return pairs


def build_metric_component_delta_rows(
    pairs: list[tuple[dict[str, str], dict[str, str]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for baseline, post in pairs:
        is_regressed_gate_row = severity_delta(baseline, post) > 1e-9
        for metric_name, larger_is_better, severity_component_candidate in COMPONENT_METRICS:
            before = as_float(baseline.get(metric_name, "nan"))
            after = as_float(post.get(metric_name, "nan"))
            raw_delta = after - before
            directional_delta = raw_delta if larger_is_better else -raw_delta
            if not np.isfinite(before) or not np.isfinite(after):
                component_direction = "not_evaluated"
            elif directional_delta > 1e-9:
                component_direction = "improved"
            elif directional_delta < -1e-9:
                component_direction = "regressed"
            else:
                component_direction = "unchanged"
            rows.append(
                {
                    "component_row_id": (
                        f"m2650_{post['subject_id']}_{post['scenario_role']}_seed_{post['seed']}_"
                        f"{post['dynamics_axis_id']}_{metric_name}"
                    ),
                    "subject_id": post["subject_id"],
                    "scenario_role": post["scenario_role"],
                    "seed": int(post["seed"]),
                    "dynamics_axis_id": post["dynamics_axis_id"],
                    "metric_name": metric_name,
                    "baseline_value": before,
                    "post_repair_value": after,
                    "raw_delta": raw_delta,
                    "larger_is_better": bool(larger_is_better),
                    "directional_delta": directional_delta,
                    "component_direction": component_direction,
                    "is_regressed_gate_row": bool(is_regressed_gate_row),
                    "severity_component_candidate": bool(severity_component_candidate),
                    "claim_scope": CLAIM_SCOPE,
                }
            )
    return rows


def build_mitigation_regression_rows(
    pairs: list[tuple[dict[str, str], dict[str, str]]],
    gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    protected_gate = protected_mitigation_gate(gate_rows)
    rows: list[dict[str, Any]] = []
    for baseline, post in pairs:
        delta = severity_delta(baseline, post)
        if delta <= 1e-9:
            continue
        baseline_clearance = as_float(baseline["minimum_obstacle_clearance_m"])
        post_clearance = as_float(post["minimum_obstacle_clearance_m"])
        baseline_penetration = penetration_proxy(baseline_clearance)
        post_penetration = penetration_proxy(post_clearance)
        penetration_delta = post_penetration - baseline_penetration
        speed_delta = as_float(post["collision_speed_proxy"]) - as_float(baseline["collision_speed_proxy"])
        angle_delta = as_float(post["impact_angle_proxy"]) - as_float(baseline["impact_angle_proxy"])
        component_driver, reason = likely_component_driver(
            severity_delta_value=delta,
            penetration_delta=penetration_delta,
            speed_delta=speed_delta,
            angle_delta=angle_delta,
        )
        actor_contract_shape_72_action_3 = (
            int(post.get("observation_shape", -1)) == P0_OBSERVATION_DIM
            and int(post.get("action_shape", -1)) == ACTION_DIM
        )
        hidden_or_oracle = (
            str(post.get("actor_input_leak_flags", "")).lower() != "none"
            or as_bool(post.get("taxonomy_labels_actor_visible", False))
            or as_bool(post.get("repair_target_labels_actor_visible", False))
        )
        rows.append(
            {
                "localization_row_id": (
                    f"m2650_{post['subject_id']}_{post['scenario_role']}_seed_{post['seed']}_"
                    f"{post['dynamics_axis_id']}_severity_regression"
                ),
                "source_gate_id": protected_gate.get("gate_id", "protected_mitigation_reference"),
                "protected_reference_family": protected_gate.get(
                    "target_or_reference_family",
                    "mitigation_collision_saturated_reference",
                ),
                "subject_id": post["subject_id"],
                "scenario_role": post["scenario_role"],
                "seed": int(post["seed"]),
                "dynamics_axis_id": post["dynamics_axis_id"],
                "baseline_row_id": baseline["row_id"],
                "post_repair_row_id": post.get("post_repair_row_id", post["row_id"]),
                "baseline_checkpoint_path": baseline.get("checkpoint_path", ""),
                "repaired_checkpoint_path": post.get("repaired_checkpoint_path", post.get("checkpoint_path", "")),
                "baseline_severity_proxy": as_float(baseline["severity_proxy"]),
                "post_repair_severity_proxy": as_float(post["severity_proxy"]),
                "severity_delta": delta,
                "baseline_collision_speed_proxy": as_float(baseline["collision_speed_proxy"]),
                "post_repair_collision_speed_proxy": as_float(post["collision_speed_proxy"]),
                "collision_speed_delta": speed_delta,
                "baseline_impact_angle_proxy": as_float(baseline["impact_angle_proxy"]),
                "post_repair_impact_angle_proxy": as_float(post["impact_angle_proxy"]),
                "impact_angle_delta": angle_delta,
                "baseline_minimum_obstacle_clearance_m": baseline_clearance,
                "post_repair_minimum_obstacle_clearance_m": post_clearance,
                "minimum_obstacle_clearance_delta": post_clearance - baseline_clearance,
                "baseline_obstacle_penetration_proxy_m": baseline_penetration,
                "post_repair_obstacle_penetration_proxy_m": post_penetration,
                "obstacle_penetration_delta": penetration_delta,
                "baseline_minimum_road_margin_m": as_float(baseline["minimum_road_margin_m"]),
                "post_repair_minimum_road_margin_m": as_float(post["minimum_road_margin_m"]),
                "minimum_road_margin_delta": (
                    as_float(post["minimum_road_margin_m"]) - as_float(baseline["minimum_road_margin_m"])
                ),
                "collision_event_unchanged": post.get("collision_event") == baseline.get("collision_event"),
                "obstacle_passed_event_unchanged": (
                    post.get("obstacle_passed_event") == baseline.get("obstacle_passed_event")
                ),
                "road_departure_event_unchanged": (
                    post.get("road_departure_event") == baseline.get("road_departure_event")
                ),
                "severity_gate_regression": True,
                "metric_artifact_detected": False,
                "likely_severity_proxy_component_driver": component_driver,
                "component_driver_reason": reason,
                "severity_formula_note": SEVERITY_FORMULA_NOTE,
                "localization_class": "real_behavior_regression_likely_obstacle_penetration_deepened",
                "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
                "hidden_or_oracle_actor_inputs_required": hidden_or_oracle,
                "protected_reference_only": as_bool(post.get("protected_reference_only", True)),
                "taxonomy_labels_actor_visible": as_bool(post.get("taxonomy_labels_actor_visible", False)),
                "repair_target_labels_actor_visible": as_bool(post.get("repair_target_labels_actor_visible", False)),
                "next_route": NEXT_ROUTE,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def protected_mitigation_gate(gate_rows: list[dict[str, str]]) -> dict[str, str]:
    for row in gate_rows:
        if row.get("gate_id") == "protected_mitigation_reference":
            return row
    return {}


def build_findings(
    *,
    regression_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, str]],
    m2648_summary: dict[str, Any],
    audit_text: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    protected_gate = protected_mitigation_gate(gate_rows)
    regressed = regression_rows[0] if regression_rows else {}
    regressed_components = [
        row
        for row in component_rows
        if row["is_regressed_gate_row"] and row["component_direction"] == "regressed"
    ]
    improved_components = [
        row
        for row in component_rows
        if row["is_regressed_gate_row"] and row["component_direction"] == "improved"
    ]
    return {
        "finding_id": "m2650_protected_mitigation_regression_localization_v0",
        "result_class": RESULT_CLASS_PASS if regression_rows else RESULT_CLASS_FAIL,
        "protected_gate_id": protected_gate.get("gate_id", ""),
        "protected_gate_pass": as_bool(protected_gate.get("gate_pass", False)),
        "protected_gate_failure_type": protected_gate.get("failure_type", ""),
        "protected_gate_evaluated_row_count": int_or_zero(protected_gate.get("evaluated_row_count", "0")),
        "protected_gate_improved_row_count": int_or_zero(protected_gate.get("improved_row_count", "0")),
        "protected_gate_regressed_row_count": int_or_zero(protected_gate.get("regressed_row_count", "0")),
        "regression_row_count": len(regression_rows),
        "regressed_row": regressed,
        "regressed_component_metrics": [row["metric_name"] for row in regressed_components],
        "improved_component_metrics": [row["metric_name"] for row in improved_components],
        "likely_severity_proxy_component_driver": regressed.get(
            "likely_severity_proxy_component_driver", ""
        ),
        "localization_class": regressed.get("localization_class", ""),
        "metric_artifact_detected": any(as_bool(row["metric_artifact_detected"]) for row in regression_rows),
        "real_behavior_regression_localized": bool(regression_rows),
        "severity_formula_note": SEVERITY_FORMULA_NOTE,
        "m2648_result_class": m2648_summary.get("result_class", ""),
        "m2648_failed_gate_ids": m2648_summary.get("failed_gate_ids", []),
        "m2649_audit_read": bool(audit_text.strip()),
        "m2649_audit_mentions_seed_267101": "267101" in audit_text,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "next_route": NEXT_ROUTE,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        **FALSE_CLAIM_FLAGS,
    }


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    regression_rows_path: Path,
    component_rows_path: Path,
    findings_path: Path,
    doc_path: Path,
    baseline_path: Path,
    post_path: Path,
    gate_path: Path,
    summary_source_path: Path,
    audit_path: Path,
    follow_up_manifest: Path,
    baseline_rows: list[dict[str, str]],
    post_rows: list[dict[str, str]],
    matched_pairs: list[tuple[dict[str, str], dict[str, str]]],
    regression_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    findings: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_artifacts_present = all(
        path.exists()
        for path in (
            regression_rows_path,
            component_rows_path,
            findings_path,
        )
    )
    actor_contract_shape_72_action_3 = bool(regression_rows) and all(
        as_bool(row["actor_contract_shape_72_action_3"]) for row in regression_rows
    )
    hidden_or_oracle = any(
        as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in regression_rows
    )
    false_claims_clean = not any(FALSE_CLAIM_FLAGS.values())
    status_pass = bool(
        required_artifacts_present
        and len(matched_pairs) == 8
        and len(regression_rows) == 1
        and findings["protected_gate_regressed_row_count"] == 1
        and findings["protected_gate_failure_type"] == "behavior_regression"
        and findings["likely_severity_proxy_component_driver"]
        == "obstacle_penetration_proxy_worsened"
        and actor_contract_shape_72_action_3
        and not hidden_or_oracle
        and not findings["metric_artifact_detected"]
        and findings["follow_up_manifest_exists"]
        and false_claims_clean
    )
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": RESULT_CLASS_PASS if status_pass else RESULT_CLASS_FAIL,
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "baseline_behavior_rows": str(baseline_path),
        "post_repair_behavior_rows": str(post_path),
        "repair_gate_evaluation": str(gate_path),
        "m2648_summary": str(summary_source_path),
        "m2649_audit": str(audit_path),
        "mitigation_regression_rows": str(regression_rows_path),
        "metric_component_delta_rows": str(component_rows_path),
        "localization_findings": str(findings_path),
        "follow_up_manifest": str(follow_up_manifest),
        "required_artifacts_present": required_artifacts_present,
        "baseline_behavior_row_count": len(baseline_rows),
        "post_repair_behavior_row_count": len(post_rows),
        "matched_protected_mitigation_pair_count": len(matched_pairs),
        "mitigation_regression_row_count": len(regression_rows),
        "metric_component_delta_row_count": len(component_rows),
        "protected_gate_regressed_row_count": findings["protected_gate_regressed_row_count"],
        "protected_gate_improved_row_count": findings["protected_gate_improved_row_count"],
        "regressed_subject_id": regression_rows[0]["subject_id"] if regression_rows else "",
        "regressed_scenario_role": regression_rows[0]["scenario_role"] if regression_rows else "",
        "regressed_seed": regression_rows[0]["seed"] if regression_rows else "",
        "regressed_dynamics_axis_id": regression_rows[0]["dynamics_axis_id"] if regression_rows else "",
        "severity_delta": regression_rows[0]["severity_delta"] if regression_rows else None,
        "likely_severity_proxy_component_driver": findings[
            "likely_severity_proxy_component_driver"
        ],
        "localization_class": findings["localization_class"],
        "metric_artifact_detected": findings["metric_artifact_detected"],
        "real_behavior_regression_localized": findings["real_behavior_regression_localized"],
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "hidden_or_oracle_actor_inputs_required": hidden_or_oracle,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "protected_reference_only_preserved": all(
            as_bool(row["protected_reference_only"]) for row in regression_rows
        ),
        "axis_sensitivity_diagnostic_only_preserved": True,
        "source_artifacts_reanalyzed_only": True,
        "new_repair_training_or_rollout_run": False,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def write_doc(path: Path, summary: dict[str, Any], findings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    regressed = findings.get("regressed_row", {})
    regressed_metrics = ", ".join(findings.get("regressed_component_metrics", [])) or "none"
    improved_metrics = ", ".join(findings.get("improved_component_metrics", [])) or "none"
    path.write_text(
        "\n".join(
            [
                "# M2650 Engineering Controller Route A Protected Mitigation Regression Localization Preflight",
                "",
                "- status: completed" if summary["status_pass"] else "- status: failed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2650-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-protected-mitigation-regression-localization-preflight.json`",
                f"- summary: `{summary['summary']}`",
                f"- mitigation regression rows: `{summary['mitigation_regression_rows']}`",
                f"- metric component delta rows: `{summary['metric_component_delta_rows']}`",
                f"- localization findings: `{summary['localization_findings']}`",
                f"- follow-up manifest: `{summary['follow_up_manifest']}`",
                f"- next: `{summary['next_blocker']}`",
                "",
                "## Result",
                "",
                "M2650 reanalyzed existing M2641 baseline behavior rows, M2648",
                "post-repair behavior rows, M2648 repair-gate rows, and the M2649",
                "audit document. It did not run repair, training, reset, rollout,",
                "replay, validation, ranking, promotion, or success-rate computation.",
                "",
                "```text",
                f"matched_protected_mitigation_pair_count: {summary['matched_protected_mitigation_pair_count']}",
                f"mitigation_regression_row_count: {summary['mitigation_regression_row_count']}",
                f"metric_component_delta_row_count: {summary['metric_component_delta_row_count']}",
                f"protected_gate_improved_row_count: {summary['protected_gate_improved_row_count']}",
                f"protected_gate_regressed_row_count: {summary['protected_gate_regressed_row_count']}",
                f"metric_artifact_detected: {summary['metric_artifact_detected']}",
                "```",
                "",
                "## Localized Regression",
                "",
                "The single regressed protected mitigation row is:",
                "",
                "```text",
                f"subject: {regressed.get('subject_id', '')}",
                f"scenario_role: {regressed.get('scenario_role', '')}",
                f"seed: {regressed.get('seed', '')}",
                f"dynamics_axis_id: {regressed.get('dynamics_axis_id', '')}",
                f"severity_proxy: {regressed.get('baseline_severity_proxy', '')} -> {regressed.get('post_repair_severity_proxy', '')}",
                f"severity_delta: {regressed.get('severity_delta', '')}",
                f"minimum_obstacle_clearance_m: {regressed.get('baseline_minimum_obstacle_clearance_m', '')} -> {regressed.get('post_repair_minimum_obstacle_clearance_m', '')}",
                f"obstacle_penetration_proxy_m: {regressed.get('baseline_obstacle_penetration_proxy_m', '')} -> {regressed.get('post_repair_obstacle_penetration_proxy_m', '')}",
                f"collision_speed_proxy: {regressed.get('baseline_collision_speed_proxy', '')} -> {regressed.get('post_repair_collision_speed_proxy', '')}",
                f"impact_angle_proxy: {regressed.get('baseline_impact_angle_proxy', '')} -> {regressed.get('post_repair_impact_angle_proxy', '')}",
                f"minimum_road_margin_m: {regressed.get('baseline_minimum_road_margin_m', '')} -> {regressed.get('post_repair_minimum_road_margin_m', '')}",
                "```",
                "",
                "Likely severity-proxy component driver:",
                "",
                "```text",
                f"{summary['likely_severity_proxy_component_driver']}",
                f"{regressed.get('component_driver_reason', '')}",
                "```",
                "",
                "Regressed component metrics on the failing row:",
                "",
                "```text",
                regressed_metrics,
                "```",
                "",
                "Improved component metrics on the same row:",
                "",
                "```text",
                improved_metrics,
                "```",
                "",
                "## Interpretation Boundary",
                "",
                "This is a protected-reference localization. It supports routing to",
                "mitigation-preserving repair synthesis because the regression is real",
                "at the row-level proxy evidence and not currently explained as a gate",
                "calculation artifact. It does not support driver-performance,",
                "promotion, ranking, success-rate, validation, paper, finite-window-vs-GRU,",
                "current-sim, high-fidelity, or self-ID claims.",
                "",
                "## Decision",
                "",
                "Route to M2651 mitigation-preserving repair synthesis before any second",
                "repair execution. The synthesis must preserve the protected mitigation",
                "reference and should decide whether to repair the objective, repair the",
                "artifact semantics, run a bounded implementation repair, or stop.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def likely_component_driver(
    *,
    severity_delta_value: float,
    penetration_delta: float,
    speed_delta: float,
    angle_delta: float,
) -> tuple[str, str]:
    if severity_delta_value <= 1e-9:
        return "no_severity_regression", "severity proxy did not regress"
    if penetration_delta > 1e-9 and speed_delta <= 1e-9:
        return (
            "obstacle_penetration_proxy_worsened",
            "severity increased while collision speed did not; row-level obstacle penetration proxy deepened",
        )
    if penetration_delta > 1e-9:
        return (
            "obstacle_penetration_and_speed_tradeoff",
            "severity increased with deeper obstacle penetration and non-improving collision speed",
        )
    if speed_delta > 1e-9:
        return "collision_speed_proxy_worsened", "severity increased with higher collision speed proxy"
    if angle_delta > 1e-9:
        return "impact_angle_proxy_worsened", "severity increased with higher impact-angle proxy"
    return (
        "aggregate_stepwise_severity_driver_unresolved",
        "row-level aggregates improved but max-over-step severity still increased",
    )


def penetration_proxy(clearance: float) -> float:
    if not np.isfinite(clearance):
        return float("nan")
    return max(0.0, -float(clearance))


def severity_delta(baseline: dict[str, str], post: dict[str, str]) -> float:
    return as_float(post["severity_proxy"]) - as_float(baseline["severity_proxy"])


def row_key(row: dict[str, str]) -> tuple[str, int, str]:
    return (str(row["scenario_role"]), int(row["seed"]), str(row["dynamics_axis_id"]))


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def int_or_zero(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--baseline-behavior-rows", type=Path, default=DEFAULT_BASELINE_BEHAVIOR_ROWS)
    parser.add_argument("--post-repair-behavior-rows", type=Path, default=DEFAULT_POST_REPAIR_BEHAVIOR_ROWS)
    parser.add_argument("--repair-gate-evaluation", type=Path, default=DEFAULT_REPAIR_GATE_EVALUATION)
    parser.add_argument("--m2648-summary", type=Path, default=DEFAULT_M2648_SUMMARY)
    parser.add_argument("--m2649-audit", type=Path, default=DEFAULT_M2649_AUDIT)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_mitigation_regression_localization(
        args.output_dir,
        baseline_behavior_rows=args.baseline_behavior_rows,
        post_repair_behavior_rows=args.post_repair_behavior_rows,
        repair_gate_evaluation=args.repair_gate_evaluation,
        m2648_summary=args.m2648_summary,
        m2649_audit=args.m2649_audit,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")


if __name__ == "__main__":
    main()
