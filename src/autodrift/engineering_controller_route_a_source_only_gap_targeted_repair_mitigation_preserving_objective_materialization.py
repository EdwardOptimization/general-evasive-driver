"""M2653 mitigation-preserving objective artifact materialization."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-objective-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2654-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-objective-materialization-branch-synthesis"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization"
)
DEFAULT_DESIGN_DOC = Path(
    "docs/m2652-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-objective-design.md"
)
DEFAULT_LOCALIZATION_SUMMARY = Path(
    "runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization/summary.json"
)
DEFAULT_LOCALIZATION_FINDINGS = Path(
    "runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization/localization_findings.json"
)
DEFAULT_REGRESSION_ROWS = Path(
    "runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization/mitigation_regression_rows.csv"
)
DEFAULT_M2648_GATE_ROWS = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/"
    "repair_gate_evaluation.csv"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-objective-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2654-engineering-controller-route-a-baseline-source-only-"
    "gap-targeted-repair-mitigation-preserving-objective-materialization-branch-synthesis.json"
)

RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization_preflight_failed"
)
CLAIM_SCOPE = "Route A mitigation-preserving objective materialization only"
FORBIDDEN_INTERPRETATION = (
    "repair execution, training, ranking, winner selection, promotion, success-rate "
    "verdict, validation, driver performance, paper, finite-window-vs-GRU, "
    "current-sim verdict, high-fidelity validation, or self-ID claim"
)

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

OBJECTIVE_FAMILY_FIELDNAMES = [
    "objective_family_id",
    "objective_role",
    "source_family",
    "source_roles",
    "source_gate_id",
    "metric_terms",
    "guard_terms",
    "protected_reference_only",
    "ordinary_success_denominator_allowed",
    "actor_visible",
    "claim_scope",
]
PROTECTED_COMPONENT_FIELDNAMES = [
    "component_gate_id",
    "protected_reference_family",
    "source_role",
    "baseline_metric",
    "candidate_metric",
    "pass_condition",
    "tolerance",
    "derived_from_m2650_component",
    "blocks_claims",
    "ordinary_success_denominator_allowed",
    "actor_visible",
    "claim_scope",
]
TARGET_PRESERVATION_FIELDNAMES = [
    "target_gate_id",
    "target_family",
    "source_roles",
    "m2648_evaluated_rows",
    "m2648_improved_rows",
    "m2648_regressed_rows",
    "required_future_condition",
    "target_only_sufficient_for_promotion",
    "blocks_claims",
    "claim_scope",
]
ABORT_RULE_FIELDNAMES = [
    "abort_rule_id",
    "failure_type",
    "condition",
    "route_if_triggered",
    "blocks_repair_execution",
    "blocks_claims",
    "claim_scope",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "expected",
    "observed_or_materialized",
    "status_pass",
    "actor_visible_allowed",
    "claim_scope",
]
CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed",
    "status_pass",
    "reason",
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


def run_objective_materialization(
    output_dir: Path,
    *,
    design_doc: Path | str = DEFAULT_DESIGN_DOC,
    localization_summary: Path | str = DEFAULT_LOCALIZATION_SUMMARY,
    localization_findings: Path | str = DEFAULT_LOCALIZATION_FINDINGS,
    regression_rows: Path | str = DEFAULT_REGRESSION_ROWS,
    m2648_gate_rows: Path | str = DEFAULT_M2648_GATE_ROWS,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    design_path = Path(design_doc)
    summary_path = Path(localization_summary)
    findings_path = Path(localization_findings)
    regression_path = Path(regression_rows)
    gate_path = Path(m2648_gate_rows)
    doc_output_path = Path(doc_path)
    follow_up_manifest_path = Path(follow_up_manifest)

    design_text = design_path.read_text(encoding="utf-8")
    m2650_summary = read_json(summary_path)
    findings = read_json(findings_path)
    regression = read_csv_rows(regression_path)
    gate_rows = read_csv_rows(gate_path)

    objective_rows = build_objective_family_rows()
    protected_rows = build_protected_component_gate_rows(findings)
    target_rows = build_target_preservation_gate_rows(gate_rows)
    abort_rows = build_abort_rule_rows()
    actor_rows = build_actor_contract_guard_rows()
    claim_rows = build_claim_boundary_rows()
    matrix_rows = build_gate_matrix_rows(
        design_text=design_text,
        m2650_summary=m2650_summary,
        findings=findings,
        regression_rows=regression,
        objective_rows=objective_rows,
        protected_rows=protected_rows,
        target_rows=target_rows,
        abort_rows=abort_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up_manifest_path,
    )

    objective_path = output_dir / "objective_family_rows.csv"
    protected_path = output_dir / "protected_component_gate_rows.csv"
    target_path = output_dir / "target_preservation_gate_rows.csv"
    abort_path = output_dir / "abort_rule_rows.csv"
    actor_path = output_dir / "actor_contract_guard_rows.csv"
    claim_path = output_dir / "claim_boundary_rows.csv"
    matrix_path = output_dir / "gate_matrix.csv"
    summary_output_path = output_dir / "summary.json"

    write_csv_rows(objective_path, objective_rows, fieldnames=OBJECTIVE_FAMILY_FIELDNAMES)
    write_csv_rows(protected_path, protected_rows, fieldnames=PROTECTED_COMPONENT_FIELDNAMES)
    write_csv_rows(target_path, target_rows, fieldnames=TARGET_PRESERVATION_FIELDNAMES)
    write_csv_rows(abort_path, abort_rows, fieldnames=ABORT_RULE_FIELDNAMES)
    write_csv_rows(actor_path, actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)
    write_csv_rows(matrix_path, matrix_rows, fieldnames=GATE_MATRIX_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_output_path,
        doc_path=doc_output_path,
        design_path=design_path,
        localization_summary_path=summary_path,
        localization_findings_path=findings_path,
        regression_path=regression_path,
        gate_path=gate_path,
        follow_up_manifest=follow_up_manifest_path,
        objective_path=objective_path,
        protected_path=protected_path,
        target_path=target_path,
        abort_path=abort_path,
        actor_path=actor_path,
        claim_path=claim_path,
        matrix_path=matrix_path,
        objective_rows=objective_rows,
        protected_rows=protected_rows,
        target_rows=target_rows,
        abort_rows=abort_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        matrix_rows=matrix_rows,
        m2650_summary=m2650_summary,
        findings=findings,
        regression_rows=regression,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(summary_output_path, summary)
    write_doc(doc_output_path, summary)
    return summary


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_objective_family_rows() -> list[dict[str, Any]]:
    return [
        {
            "objective_family_id": "road_boundary_margin_target",
            "objective_role": "target",
            "source_family": "road_departure_dominant_gap",
            "source_roles": "stable_avoidable;stable_aes",
            "source_gate_id": "target_road_boundary_margin_control",
            "metric_terms": "minimum_road_margin_m;road_departure_event;minimum_obstacle_clearance_m;command_delta_l1_mean",
            "guard_terms": "no_success_rate;no_ranking;no_actor_visible_labels",
            "protected_reference_only": False,
            "ordinary_success_denominator_allowed": False,
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
        {
            "objective_family_id": "drift_collision_recovery_target",
            "objective_role": "target",
            "source_family": "drift_recovery_mixed_gap",
            "source_roles": "drift_required_recovery",
            "source_gate_id": "target_drift_collision_recovery_tradeoff",
            "metric_terms": "drift_tradeoff_proxy;minimum_obstacle_clearance_m;minimum_road_margin_m;final_abs_lateral_velocity;final_abs_yaw_rate;command_delta_l1_mean",
            "guard_terms": "no_mitigation_row_normalization;no_delay_noise_verdict;no_actor_visible_labels",
            "protected_reference_only": False,
            "ordinary_success_denominator_allowed": False,
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
        {
            "objective_family_id": "mitigation_non_regression_protected",
            "objective_role": "protected_reference",
            "source_family": "mitigation_collision_saturated_reference",
            "source_roles": "unavoidable_mitigation",
            "source_gate_id": "protected_mitigation_reference",
            "metric_terms": "severity_proxy;obstacle_penetration_proxy_m;minimum_obstacle_clearance_m;collision_event;road_departure_event",
            "guard_terms": "blocks_promotion;blocks_performance_claims;not_success_denominator",
            "protected_reference_only": True,
            "ordinary_success_denominator_allowed": False,
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
    ]


def build_protected_component_gate_rows(findings: dict[str, Any]) -> list[dict[str, Any]]:
    regressed = findings.get("regressed_row", {})
    source = regressed.get("localization_row_id", "m2650_protected_regression")
    return [
        protected_component_row(
            "severity_proxy_non_regression",
            "severity_proxy",
            "post severity_proxy <= baseline severity_proxy + 0.0",
            source,
        ),
        protected_component_row(
            "obstacle_penetration_non_regression",
            "obstacle_penetration_proxy_m",
            "post obstacle_penetration_proxy_m <= baseline obstacle_penetration_proxy_m + 0.0",
            source,
        ),
        protected_component_row(
            "minimum_obstacle_clearance_preservation",
            "minimum_obstacle_clearance_m",
            "post minimum_obstacle_clearance_m >= baseline minimum_obstacle_clearance_m - 0.0",
            source,
        ),
        protected_component_row(
            "event_transition_guard",
            "collision_event;road_departure_event",
            "no collision_event false-to-true and no road_departure_event false-to-true",
            source,
        ),
    ]


def protected_component_row(
    gate_id: str,
    metric: str,
    pass_condition: str,
    source: str,
) -> dict[str, Any]:
    return {
        "component_gate_id": gate_id,
        "protected_reference_family": "mitigation_collision_saturated_reference",
        "source_role": "unavoidable_mitigation",
        "baseline_metric": metric,
        "candidate_metric": metric,
        "pass_condition": pass_condition,
        "tolerance": 0.0,
        "derived_from_m2650_component": source,
        "blocks_claims": True,
        "ordinary_success_denominator_allowed": False,
        "actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
    }


def build_target_preservation_gate_rows(gate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_id = {row["gate_id"]: row for row in gate_rows}
    return [
        target_preservation_row(
            by_id["target_road_boundary_margin_control"],
            target_family="road_departure_dominant_gap",
            source_roles="stable_avoidable;stable_aes",
            condition="future candidate preserves no-regression against M2641 and preferably preserves M2648 16/16 improvement",
        ),
        target_preservation_row(
            by_id["target_drift_collision_recovery_tradeoff"],
            target_family="drift_recovery_mixed_gap",
            source_roles="drift_required_recovery",
            condition="future candidate preserves no-regression against M2641 and preferably preserves M2648 8/8 improvement",
        ),
    ]


def target_preservation_row(
    gate_row: dict[str, str],
    *,
    target_family: str,
    source_roles: str,
    condition: str,
) -> dict[str, Any]:
    return {
        "target_gate_id": gate_row["gate_id"],
        "target_family": target_family,
        "source_roles": source_roles,
        "m2648_evaluated_rows": int(gate_row["evaluated_row_count"]),
        "m2648_improved_rows": int(gate_row["improved_row_count"]),
        "m2648_regressed_rows": int(gate_row["regressed_row_count"]),
        "required_future_condition": condition,
        "target_only_sufficient_for_promotion": False,
        "blocks_claims": True,
        "claim_scope": CLAIM_SCOPE,
    }


def build_abort_rule_rows() -> list[dict[str, Any]]:
    specs = [
        ("protected_mitigation_any_regression", "behavior_regression", "protected_mitigation_reference has any regressed row"),
        ("obstacle_penetration_increase", "behavior_regression", "obstacle_penetration_proxy_m increases on any protected mitigation row"),
        ("severity_proxy_increase", "behavior_regression", "severity_proxy increases on any protected mitigation row"),
        ("taxonomy_label_actor_visible", "contract_violation", "taxonomy labels or repair-target labels become actor-visible"),
        ("observation_shape_changed", "contract_violation", "actor observation shape changes from 72"),
        ("action_shape_changed", "contract_violation", "action shape changes from 3"),
        ("hidden_oracle_required", "contract_violation", "hidden or oracle actor inputs are required"),
        ("forbidden_verdict_fields", "proof_washout", "ranking winner success-rate validation or promotion fields are emitted"),
        ("axis_overinterpretation", "objective_overfit", "source-only axis rows are interpreted as robust delay/noise validation"),
    ]
    return [
        {
            "abort_rule_id": rule_id,
            "failure_type": failure_type,
            "condition": condition,
            "route_if_triggered": "artifact_or_implementation_repair_before_execution",
            "blocks_repair_execution": True,
            "blocks_claims": True,
            "claim_scope": CLAIM_SCOPE,
        }
        for rule_id, failure_type, condition in specs
    ]


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    specs = [
        ("observation_shape_72", "actor_contract", "72", str(P0_OBSERVATION_DIM), True),
        ("action_shape_3", "actor_contract", "3", str(ACTION_DIM), True),
        ("actor_input_leak_flags_none", "actor_contract", "none", "none", True),
        ("taxonomy_labels_actor_visible_false", "actor_visibility", "false", "false", False),
        ("repair_target_labels_actor_visible_false", "actor_visibility", "false", "false", False),
        ("route_metadata_actor_visible_false", "actor_visibility", "false", "false", False),
    ]
    return [
        {
            "guard_id": guard_id,
            "guard_family": family,
            "expected": expected,
            "observed_or_materialized": observed,
            "status_pass": True,
            "actor_visible_allowed": actor_visible_allowed,
            "claim_scope": CLAIM_SCOPE,
        }
        for guard_id, family, expected, observed, actor_visible_allowed in specs
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "claim_id": flag,
            "claim_family": "forbidden_claim_or_execution",
            "allowed": False,
            "status_pass": value is False,
            "reason": "M2653 is objective materialization only",
            "claim_scope": CLAIM_SCOPE,
        }
        for flag, value in FALSE_CLAIM_FLAGS.items()
    ]
    rows.append(
        {
            "claim_id": "protected_rows_not_success_denominator",
            "claim_family": "proof_boundary",
            "allowed": False,
            "status_pass": True,
            "reason": "mitigation_collision_saturated_reference remains protected reference only",
            "claim_scope": CLAIM_SCOPE,
        }
    )
    return rows


def build_gate_matrix_rows(
    *,
    design_text: str,
    m2650_summary: dict[str, Any],
    findings: dict[str, Any],
    regression_rows: list[dict[str, str]],
    objective_rows: list[dict[str, Any]],
    protected_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    abort_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    objective_ids = {row["objective_family_id"] for row in objective_rows}
    protected_ids = {row["component_gate_id"] for row in protected_rows}
    target_ids = {row["target_gate_id"] for row in target_rows}
    actor_pass = all(as_bool(row["status_pass"]) for row in actor_rows)
    claim_pass = all(as_bool(row["status_pass"]) for row in claim_rows)
    no_forbidden_execution = not any(FALSE_CLAIM_FLAGS.values())
    rows = [
        gate_row("source_artifacts_read", "source_artifacts", bool(design_text and regression_rows), "present", "present"),
        gate_row(
            "m2650_real_regression_available",
            "source_artifacts",
            m2650_summary.get("real_behavior_regression_localized") is True
            and findings.get("metric_artifact_detected") is False,
            findings.get("localization_class", ""),
            "real_behavior_regression_likely_obstacle_penetration_deepened",
        ),
        gate_row(
            "objective_family_rows_complete",
            "objective_materialization",
            objective_ids
            == {
                "road_boundary_margin_target",
                "drift_collision_recovery_target",
                "mitigation_non_regression_protected",
            },
            ";".join(sorted(objective_ids)),
            "three objective families",
        ),
        gate_row(
            "protected_component_gates_complete",
            "objective_materialization",
            protected_ids
            == {
                "severity_proxy_non_regression",
                "obstacle_penetration_non_regression",
                "minimum_obstacle_clearance_preservation",
                "event_transition_guard",
            },
            ";".join(sorted(protected_ids)),
            "four protected component gates",
        ),
        gate_row(
            "target_preservation_gates_complete",
            "objective_materialization",
            target_ids
            == {
                "target_road_boundary_margin_control",
                "target_drift_collision_recovery_tradeoff",
            },
            ";".join(sorted(target_ids)),
            "two target preservation gates",
        ),
        gate_row("abort_rules_materialized", "objective_materialization", len(abort_rows) >= 9, len(abort_rows), ">=9"),
        gate_row("actor_contract_guards_pass", "actor_contract", actor_pass, actor_pass, "true"),
        gate_row("claim_boundary_rows_pass", "claim_boundary", claim_pass, claim_pass, "true"),
        gate_row(
            "follow_up_manifest_registered",
            "follow_up",
            follow_up_manifest.exists(),
            str(follow_up_manifest),
            "exists",
        ),
        gate_row(
            "no_forbidden_execution_or_claim",
            "claim_boundary",
            no_forbidden_execution,
            no_forbidden_execution,
            "true",
        ),
    ]
    return rows


def gate_row(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else "artifact_incomplete",
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    doc_path: Path,
    design_path: Path,
    localization_summary_path: Path,
    localization_findings_path: Path,
    regression_path: Path,
    gate_path: Path,
    follow_up_manifest: Path,
    objective_path: Path,
    protected_path: Path,
    target_path: Path,
    abort_path: Path,
    actor_path: Path,
    claim_path: Path,
    matrix_path: Path,
    objective_rows: list[dict[str, Any]],
    protected_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    abort_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    m2650_summary: dict[str, Any],
    findings: dict[str, Any],
    regression_rows: list[dict[str, str]],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    artifact_paths = [
        objective_path,
        protected_path,
        target_path,
        abort_path,
        actor_path,
        claim_path,
        matrix_path,
    ]
    required_artifacts_present = all(path.exists() for path in artifact_paths)
    gate_matrix_pass = all(as_bool(row["status_pass"]) for row in matrix_rows)
    protected_ids = sorted(row["component_gate_id"] for row in protected_rows)
    objective_ids = sorted(row["objective_family_id"] for row in objective_rows)
    target_ids = sorted(row["target_gate_id"] for row in target_rows)
    actor_contract_shape_72_action_3 = (
        any(row["guard_id"] == "observation_shape_72" and as_bool(row["status_pass"]) for row in actor_rows)
        and any(row["guard_id"] == "action_shape_3" and as_bool(row["status_pass"]) for row in actor_rows)
    )
    hidden_or_oracle = False
    status_pass = bool(
        required_artifacts_present
        and gate_matrix_pass
        and len(objective_rows) == 3
        and len(protected_rows) == 4
        and len(target_rows) == 2
        and len(abort_rows) >= 9
        and actor_contract_shape_72_action_3
        and not hidden_or_oracle
        and follow_up_manifest.exists()
        and not any(FALSE_CLAIM_FLAGS.values())
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
        "design_doc": str(design_path),
        "localization_summary": str(localization_summary_path),
        "localization_findings": str(localization_findings_path),
        "mitigation_regression_rows": str(regression_path),
        "m2648_gate_rows": str(gate_path),
        "follow_up_manifest": str(follow_up_manifest),
        "objective_family_rows": str(objective_path),
        "protected_component_gate_rows": str(protected_path),
        "target_preservation_gate_rows": str(target_path),
        "abort_rule_rows": str(abort_path),
        "actor_contract_guard_rows": str(actor_path),
        "claim_boundary_rows": str(claim_path),
        "gate_matrix": str(matrix_path),
        "required_artifacts_present": required_artifacts_present,
        "gate_matrix_pass": gate_matrix_pass,
        "objective_family_row_count": len(objective_rows),
        "protected_component_gate_row_count": len(protected_rows),
        "target_preservation_gate_row_count": len(target_rows),
        "abort_rule_row_count": len(abort_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(matrix_rows),
        "objective_family_ids": objective_ids,
        "protected_component_gate_ids": protected_ids,
        "target_preservation_gate_ids": target_ids,
        "m2650_real_behavior_regression_localized": m2650_summary.get(
            "real_behavior_regression_localized", False
        ),
        "m2650_likely_component_driver": m2650_summary.get(
            "likely_severity_proxy_component_driver", ""
        ),
        "m2650_metric_artifact_detected": findings.get("metric_artifact_detected", True),
        "m2650_regression_row_count": len(regression_rows),
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "hidden_or_oracle_actor_inputs_required": hidden_or_oracle,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "protected_mitigation_reference_ordinary_denominator": False,
        "axis_sensitivity_diagnostic_only_preserved": True,
        "source_artifacts_reanalyzed_only": True,
        "new_repair_training_or_rollout_run": False,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2653 Engineering Controller Route A Mitigation-Preserving Objective Materialization Preflight",
                "",
                "- status: completed" if summary["status_pass"] else "- status: failed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2653-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-preflight.json`",
                f"- summary: `{summary['summary']}`",
                f"- objective family rows: `{summary['objective_family_rows']}`",
                f"- protected component gates: `{summary['protected_component_gate_rows']}`",
                f"- target preservation gates: `{summary['target_preservation_gate_rows']}`",
                f"- abort rules: `{summary['abort_rule_rows']}`",
                f"- actor contract guards: `{summary['actor_contract_guard_rows']}`",
                f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
                f"- gate matrix: `{summary['gate_matrix']}`",
                f"- follow-up manifest: `{summary['follow_up_manifest']}`",
                f"- next: `{summary['next_blocker']}`",
                "",
                "## Result",
                "",
                "M2653 materialized deterministic objective and gate rows from M2652.",
                "It did not run repair, training, reset, rollout, replay, validation,",
                "ranking, promotion, or success-rate computation.",
                "",
                "```text",
                f"objective_family_row_count: {summary['objective_family_row_count']}",
                f"protected_component_gate_row_count: {summary['protected_component_gate_row_count']}",
                f"target_preservation_gate_row_count: {summary['target_preservation_gate_row_count']}",
                f"abort_rule_row_count: {summary['abort_rule_row_count']}",
                f"actor_contract_guard_row_count: {summary['actor_contract_guard_row_count']}",
                f"claim_boundary_row_count: {summary['claim_boundary_row_count']}",
                f"gate_matrix_pass: {summary['gate_matrix_pass']}",
                "```",
                "",
                "## Protected Components",
                "",
                "```text",
                "\n".join(summary["protected_component_gate_ids"]),
                "```",
                "",
                "## Decision",
                "",
                "Route to M2654 branch synthesis before implementation repair or a second",
                "repair execution preflight. M2654 must synthesize M2648-M2653 and",
                "decide whether the materialized gate bundle is sufficient for",
                "implementation repair, repair execution, artifact repair, evidence",
                "expansion, pivot, or stop.",
                "",
                "## Rejected Claims",
                "",
                "M2653 does not claim driver performance, ranking, promotion, success",
                "rate, validation, paper evidence, current-sim verdict, high-fidelity",
                "validation, finite-window-vs-GRU evidence, or self-ID.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--design-doc", type=Path, default=DEFAULT_DESIGN_DOC)
    parser.add_argument("--localization-summary", type=Path, default=DEFAULT_LOCALIZATION_SUMMARY)
    parser.add_argument("--localization-findings", type=Path, default=DEFAULT_LOCALIZATION_FINDINGS)
    parser.add_argument("--regression-rows", type=Path, default=DEFAULT_REGRESSION_ROWS)
    parser.add_argument("--m2648-gate-rows", type=Path, default=DEFAULT_M2648_GATE_ROWS)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_objective_materialization(
        args.output_dir,
        design_doc=args.design_doc,
        localization_summary=args.localization_summary,
        localization_findings=args.localization_findings,
        regression_rows=args.regression_rows,
        m2648_gate_rows=args.m2648_gate_rows,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")


if __name__ == "__main__":
    main()
