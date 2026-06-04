"""Route A source-only target/protected tradeoff report materialization.

This runner reanalyzes existing M2641, M2648, M2650, and M2655 artifacts. It
does not execute environments, policies, replay, validation, training, ranking,
or promotion.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2657-engineering-controller-route-a-baseline-source-only-target-protected-"
    "tradeoff-report-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2658-engineering-controller-route-a-baseline-source-only-target-protected-"
    "tradeoff-report-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2657-engineering-controller-route-a-baseline-source-only-target-protected-"
    "tradeoff-report-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2658-engineering-controller-route-a-baseline-source-only-"
    "target-protected-tradeoff-report-materialization-result-audit.json"
)

DEFAULT_BASELINE_BEHAVIOR_ROWS = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "measured_behavior_rows.csv"
)
DEFAULT_M2648_POST_REPAIR_ROWS = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/"
    "post_repair_behavior_rows.csv"
)
DEFAULT_M2648_GATES = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/"
    "repair_gate_evaluation.csv"
)
DEFAULT_M2655_POST_REPAIR_ROWS = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/post_repair_behavior_rows.csv"
)
DEFAULT_M2655_CANDIDATE_SWEEP = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/repair_candidate_sweep.csv"
)
DEFAULT_M2655_GATES = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/mitigation_preserving_gate_evaluation.csv"
)
DEFAULT_M2650_LOCALIZATION = Path(
    "runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_regression_localization/summary.json"
)

SUBJECT_ID = "m2537_mitigation_preserving_policy"
TARGET_ROLES = ("stable_avoidable", "stable_aes", "drift_required_recovery")
PROTECTED_ROLE = "unavoidable_mitigation"
SCENARIO_ROLES = TARGET_ROLES + (PROTECTED_ROLE,)
EPSILON = 1e-9

CLAIM_SCOPE = (
    "Route A source-only scenario-role target/protected tradeoff report only; "
    "source artifacts reanalyzed without repair execution, validation, ranking, "
    "promotion, success-rate verdict, driver-performance, paper, current-sim, "
    "high-fidelity validation, finite-window-vs-GRU, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, controller ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, validation result, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation "
    "result, full ideal driver completion, or self-ID evidence"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "source_only_backend_reset_run": False,
    "source_only_backend_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "new_repair_training_or_rollout_run": False,
    "repair_execution_started": False,
    "repair_training_started": False,
    "training_run": False,
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
    "full_ideal_driver_gate_passed": False,
}

ROLE_GATE_IDS = {
    "stable_avoidable": ("target_road_boundary_margin_control",),
    "stable_aes": ("target_road_boundary_margin_control",),
    "drift_required_recovery": ("target_drift_collision_recovery_tradeoff",),
    "unavoidable_mitigation": (
        "severity_proxy_non_regression",
        "obstacle_penetration_non_regression",
        "minimum_obstacle_clearance_preservation",
        "event_transition_guard",
    ),
}
PROTECTED_FAILED_GATE_IDS = (
    "severity_proxy_non_regression",
    "obstacle_penetration_non_regression",
    "minimum_obstacle_clearance_preservation",
)
TARGET_PROTECTED_GATE_IDS = {
    "target_road_boundary_margin_control",
    "target_drift_collision_recovery_tradeoff",
    "protected_mitigation_reference",
    "severity_proxy_non_regression",
    "obstacle_penetration_non_regression",
    "minimum_obstacle_clearance_preservation",
    "event_transition_guard",
}

SCENARIO_ROLE_FIELDNAMES = [
    "row_id",
    "scenario_role",
    "role_class",
    "source_subject_id",
    "baseline_row_count",
    "m2648_row_count",
    "m2655_row_count",
    "seed_count",
    "dynamics_axis_count",
    "primary_metric",
    "primary_metric_direction",
    "baseline_primary_metric_mean",
    "m2648_primary_metric_mean",
    "m2655_primary_metric_mean",
    "m2648_improved_count",
    "m2648_regressed_count",
    "m2648_unchanged_count",
    "m2655_improved_count",
    "m2655_regressed_count",
    "m2655_unchanged_count",
    "m2655_gate_ids",
    "m2655_gate_pass",
    "m2655_failed_gate_ids",
    "protected_role_excluded_from_target_success_denominator",
    "actor_contract_shape_72_action_3",
    "hidden_or_oracle_actor_input_detected",
    "diagnostic_only_no_ranking_claim",
    "ranking_or_winner_field_emitted",
    "blocks_claims",
    "claim_scope",
]

TRADEOFF_FIELDNAMES = [
    "tradeoff_id",
    "source_stage",
    "gate_id",
    "gate_family",
    "target_or_reference_family",
    "scenario_role_group",
    "role_class",
    "metric",
    "evaluated_row_count",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "gate_pass",
    "failure_type",
    "failed_gate_ids",
    "target_preservation_gates_all_passed",
    "protected_component_gates_all_passed",
    "target_and_protected_gates_all_passed",
    "selected_candidate_id",
    "selected_candidate_treated_as_winner",
    "protected_rows_in_success_denominator",
    "blocks_claims",
    "interpretation",
    "claim_scope",
]

PROTECTED_FOCUS_FIELDNAMES = [
    "focus_id",
    "subject_id",
    "scenario_role",
    "seed",
    "dynamics_axis_id",
    "baseline_severity_proxy",
    "m2648_severity_proxy",
    "m2655_severity_proxy",
    "m2648_severity_delta",
    "m2655_severity_delta",
    "baseline_obstacle_penetration_proxy_m",
    "m2648_obstacle_penetration_proxy_m",
    "m2655_obstacle_penetration_proxy_m",
    "m2648_obstacle_penetration_delta",
    "m2655_obstacle_penetration_delta",
    "baseline_minimum_obstacle_clearance_m",
    "m2648_minimum_obstacle_clearance_m",
    "m2655_minimum_obstacle_clearance_m",
    "m2648_clearance_delta",
    "m2655_clearance_delta",
    "m2648_any_protected_component_regressed",
    "m2655_any_protected_component_regressed",
    "m2650_regressed_row_match",
    "blocks_claims",
    "claim_scope",
]

REPORT_GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "blocks_claims",
    "claim_boundary",
]


def materialize_target_protected_tradeoff_report(
    output_dir: Path | str,
    *,
    baseline_behavior_rows: Path | str = DEFAULT_BASELINE_BEHAVIOR_ROWS,
    m2648_post_repair_rows: Path | str = DEFAULT_M2648_POST_REPAIR_ROWS,
    m2648_gates: Path | str = DEFAULT_M2648_GATES,
    m2655_post_repair_rows: Path | str = DEFAULT_M2655_POST_REPAIR_ROWS,
    m2655_candidate_sweep: Path | str = DEFAULT_M2655_CANDIDATE_SWEEP,
    m2655_gates: Path | str = DEFAULT_M2655_GATES,
    m2650_localization: Path | str = DEFAULT_M2650_LOCALIZATION,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source = load_source_artifacts(
        baseline_behavior_rows=baseline_behavior_rows,
        m2648_post_repair_rows=m2648_post_repair_rows,
        m2648_gates=m2648_gates,
        m2655_post_repair_rows=m2655_post_repair_rows,
        m2655_candidate_sweep=m2655_candidate_sweep,
        m2655_gates=m2655_gates,
        m2650_localization=m2650_localization,
        follow_up_manifest=follow_up_manifest,
    )
    baseline_subject_rows = _subject_rows(source["baseline_behavior_rows"])
    m2648_subject_rows = _subject_rows(source["m2648_post_repair_rows"])
    m2655_subject_rows = _subject_rows(source["m2655_post_repair_rows"])
    selected_candidate = _selected_candidate(source["m2655_candidate_sweep"])

    scenario_rows = build_scenario_role_metric_report(
        baseline_subject_rows,
        m2648_subject_rows,
        m2655_subject_rows,
        source["m2655_gates"],
    )
    tradeoff_rows = build_target_protected_tradeoff_rows(
        source["m2648_gates"],
        source["m2655_gates"],
        selected_candidate,
    )
    focus_rows = build_protected_regression_focus_rows(
        baseline_subject_rows,
        m2648_subject_rows,
        m2655_subject_rows,
        source["m2650_localization"],
    )
    report_gate_rows = build_report_gate_evaluation_rows(
        source=source,
        baseline_subject_rows=baseline_subject_rows,
        m2648_subject_rows=m2648_subject_rows,
        m2655_subject_rows=m2655_subject_rows,
        scenario_rows=scenario_rows,
        tradeoff_rows=tradeoff_rows,
        selected_candidate=selected_candidate,
    )

    paths = {
        "summary": output_path / "summary.json",
        "scenario_role_metric_report": output_path / "scenario_role_metric_report.csv",
        "target_protected_tradeoff_rows": output_path / "target_protected_tradeoff_rows.csv",
        "protected_regression_focus_rows": output_path / "protected_regression_focus_rows.csv",
        "report_gate_evaluation": output_path / "report_gate_evaluation.csv",
        "doc": Path(doc_path),
    }
    write_csv_rows(
        paths["scenario_role_metric_report"],
        scenario_rows,
        fieldnames=SCENARIO_ROLE_FIELDNAMES,
    )
    write_csv_rows(
        paths["target_protected_tradeoff_rows"],
        tradeoff_rows,
        fieldnames=TRADEOFF_FIELDNAMES,
    )
    write_csv_rows(
        paths["protected_regression_focus_rows"],
        focus_rows,
        fieldnames=PROTECTED_FOCUS_FIELDNAMES,
    )
    write_csv_rows(
        paths["report_gate_evaluation"],
        report_gate_rows,
        fieldnames=REPORT_GATE_FIELDNAMES,
    )
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        baseline_subject_rows=baseline_subject_rows,
        m2648_subject_rows=m2648_subject_rows,
        m2655_subject_rows=m2655_subject_rows,
        scenario_rows=scenario_rows,
        tradeoff_rows=tradeoff_rows,
        focus_rows=focus_rows,
        report_gate_rows=report_gate_rows,
        selected_candidate=selected_candidate,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(
        render_milestone_doc(summary, scenario_rows, tradeoff_rows, focus_rows, report_gate_rows),
        encoding="utf-8",
    )
    summary["required_artifacts_present"] = all(
        Path(summary[key]).exists()
        for key in (
            "summary",
            "scenario_role_metric_report",
            "target_protected_tradeoff_rows",
            "protected_regression_focus_rows",
            "report_gate_evaluation",
        )
    )
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    write_json(paths["summary"], summary)
    return summary


def load_source_artifacts(
    *,
    baseline_behavior_rows: Path | str,
    m2648_post_repair_rows: Path | str,
    m2648_gates: Path | str,
    m2655_post_repair_rows: Path | str,
    m2655_candidate_sweep: Path | str,
    m2655_gates: Path | str,
    m2650_localization: Path | str,
    follow_up_manifest: Path | str,
) -> dict[str, Any]:
    paths = {
        "baseline_behavior_rows": Path(baseline_behavior_rows),
        "m2648_post_repair_rows": Path(m2648_post_repair_rows),
        "m2648_gates": Path(m2648_gates),
        "m2655_post_repair_rows": Path(m2655_post_repair_rows),
        "m2655_candidate_sweep": Path(m2655_candidate_sweep),
        "m2655_gates": Path(m2655_gates),
        "m2650_localization": Path(m2650_localization),
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "baseline_behavior_rows": _read_csv_rows(paths["baseline_behavior_rows"]),
        "m2648_post_repair_rows": _read_csv_rows(paths["m2648_post_repair_rows"]),
        "m2648_gates": _read_csv_rows(paths["m2648_gates"]),
        "m2655_post_repair_rows": _read_csv_rows(paths["m2655_post_repair_rows"]),
        "m2655_candidate_sweep": _read_csv_rows(paths["m2655_candidate_sweep"]),
        "m2655_gates": _read_csv_rows(paths["m2655_gates"]),
        "m2650_localization": read_json(paths["m2650_localization"]),
    }


def build_scenario_role_metric_report(
    baseline_rows: list[dict[str, str]],
    m2648_rows: list[dict[str, str]],
    m2655_rows: list[dict[str, str]],
    m2655_gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    m2655_gate_by_id = {row["gate_id"]: row for row in m2655_gate_rows}
    rows = []
    for role in SCENARIO_ROLES:
        metric, direction = _role_metric_spec(role)
        baseline_role_rows = [row for row in baseline_rows if row.get("scenario_role") == role]
        m2648_role_rows = [row for row in m2648_rows if row.get("scenario_role") == role]
        m2655_role_rows = [row for row in m2655_rows if row.get("scenario_role") == role]
        m2648_compare = _compare_stage(baseline_role_rows, m2648_role_rows, metric, direction)
        m2655_compare = _compare_stage(baseline_role_rows, m2655_role_rows, metric, direction)
        gate_ids = ROLE_GATE_IDS[role]
        failed_gate_ids = [
            gate_id
            for gate_id in gate_ids
            if not _bool(m2655_gate_by_id.get(gate_id, {}).get("gate_pass"))
        ]
        rows.append(
            {
                "row_id": f"m2657_scenario_role_metric_{role}",
                "scenario_role": role,
                "role_class": _role_class(role),
                "source_subject_id": SUBJECT_ID,
                "baseline_row_count": len(baseline_role_rows),
                "m2648_row_count": len(m2648_role_rows),
                "m2655_row_count": len(m2655_role_rows),
                "seed_count": len({row.get("seed", "") for row in baseline_role_rows}),
                "dynamics_axis_count": len(
                    {row.get("dynamics_axis_id", "") for row in baseline_role_rows}
                ),
                "primary_metric": metric,
                "primary_metric_direction": direction,
                "baseline_primary_metric_mean": m2648_compare["baseline_mean"],
                "m2648_primary_metric_mean": m2648_compare["stage_mean"],
                "m2655_primary_metric_mean": m2655_compare["stage_mean"],
                "m2648_improved_count": m2648_compare["improved_count"],
                "m2648_regressed_count": m2648_compare["regressed_count"],
                "m2648_unchanged_count": m2648_compare["unchanged_count"],
                "m2655_improved_count": m2655_compare["improved_count"],
                "m2655_regressed_count": m2655_compare["regressed_count"],
                "m2655_unchanged_count": m2655_compare["unchanged_count"],
                "m2655_gate_ids": ";".join(gate_ids),
                "m2655_gate_pass": not failed_gate_ids,
                "m2655_failed_gate_ids": ";".join(failed_gate_ids),
                "protected_role_excluded_from_target_success_denominator": role == PROTECTED_ROLE,
                "actor_contract_shape_72_action_3": _actor_contract_shape_ok(
                    baseline_role_rows + m2648_role_rows + m2655_role_rows
                ),
                "hidden_or_oracle_actor_input_detected": _hidden_or_oracle_actor_input_detected(
                    baseline_role_rows + m2648_role_rows + m2655_role_rows
                ),
                "diagnostic_only_no_ranking_claim": _diagnostic_only_rows(
                    baseline_role_rows + m2648_role_rows + m2655_role_rows
                ),
                "ranking_or_winner_field_emitted": _ranking_or_winner_field_emitted(
                    baseline_role_rows + m2648_role_rows + m2655_role_rows
                ),
                "blocks_claims": role == PROTECTED_ROLE and bool(failed_gate_ids),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_protected_tradeoff_rows(
    m2648_gate_rows: list[dict[str, str]],
    m2655_gate_rows: list[dict[str, str]],
    selected_candidate: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for source_stage, gate_rows in (
        ("m2648_gap_targeted_repair_execution", m2648_gate_rows),
        ("m2655_mitigation_preserving_repair_execution", m2655_gate_rows),
    ):
        for gate_row in gate_rows:
            if not _is_target_protected_gate(gate_row):
                continue
            gate_id = gate_row["gate_id"]
            gate_pass = _bool(gate_row.get("gate_pass"))
            row: dict[str, Any] = {
                "tradeoff_id": f"m2657_tradeoff_{source_stage}_{gate_id}",
                "source_stage": source_stage,
                "gate_id": gate_id,
                "gate_family": gate_row.get("gate_family", ""),
                "target_or_reference_family": gate_row.get("target_or_reference_family", ""),
                "scenario_role_group": _gate_role_group(gate_id),
                "role_class": _gate_role_class(gate_id),
                "metric": gate_row.get("metric") or _gate_metric(gate_id),
                "evaluated_row_count": _int(gate_row.get("evaluated_row_count")),
                "improved_row_count": _int(gate_row.get("improved_row_count")),
                "regressed_row_count": _int(gate_row.get("regressed_row_count")),
                "unchanged_row_count": _int(gate_row.get("unchanged_row_count")),
                "gate_pass": gate_pass,
                "failure_type": gate_row.get("failure_type", ""),
                "failed_gate_ids": "" if gate_pass else gate_id,
                "target_preservation_gates_all_passed": "",
                "protected_component_gates_all_passed": "",
                "target_and_protected_gates_all_passed": "",
                "selected_candidate_id": "",
                "selected_candidate_treated_as_winner": False,
                "protected_rows_in_success_denominator": False,
                "blocks_claims": _bool(gate_row.get("blocks_claims")),
                "interpretation": _tradeoff_interpretation(source_stage, gate_id, gate_pass),
                "claim_scope": CLAIM_SCOPE,
            }
            if source_stage.startswith("m2655"):
                row.update(
                    {
                        "target_preservation_gates_all_passed": _bool(
                            selected_candidate.get("target_preservation_gates_all_passed")
                        ),
                        "protected_component_gates_all_passed": _bool(
                            selected_candidate.get("protected_component_gates_all_passed")
                        ),
                        "target_and_protected_gates_all_passed": _bool(
                            selected_candidate.get("target_and_protected_gates_all_passed")
                        ),
                        "selected_candidate_id": selected_candidate.get("candidate_id", ""),
                    }
                )
            rows.append(row)
    return rows


def build_protected_regression_focus_rows(
    baseline_rows: list[dict[str, str]],
    m2648_rows: list[dict[str, str]],
    m2655_rows: list[dict[str, str]],
    m2650_localization: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_protected = [
        row for row in baseline_rows if row.get("scenario_role") == PROTECTED_ROLE
    ]
    m2648_by_key = {_row_key(row): row for row in m2648_rows}
    m2655_by_key = {_row_key(row): row for row in m2655_rows}
    rows = []
    for baseline_row in sorted(baseline_protected, key=lambda row: (_int(row.get("seed")), row.get("dynamics_axis_id", ""))):
        key = _row_key(baseline_row)
        m2648_row = m2648_by_key.get(key, {})
        m2655_row = m2655_by_key.get(key, {})
        baseline_severity = _float(baseline_row.get("severity_proxy"))
        m2648_severity = _float_or_none(m2648_row.get("severity_proxy"))
        m2655_severity = _float_or_none(m2655_row.get("severity_proxy"))
        baseline_penetration = _obstacle_penetration_proxy(baseline_row)
        m2648_penetration = _obstacle_penetration_proxy_or_none(m2648_row)
        m2655_penetration = _obstacle_penetration_proxy_or_none(m2655_row)
        baseline_clearance = _float(baseline_row.get("minimum_obstacle_clearance_m"))
        m2648_clearance = _float_or_none(m2648_row.get("minimum_obstacle_clearance_m"))
        m2655_clearance = _float_or_none(m2655_row.get("minimum_obstacle_clearance_m"))
        m2648_any_regressed = _protected_components_regressed(
            baseline_severity,
            m2648_severity,
            baseline_penetration,
            m2648_penetration,
            baseline_clearance,
            m2648_clearance,
        )
        m2655_any_regressed = _protected_components_regressed(
            baseline_severity,
            m2655_severity,
            baseline_penetration,
            m2655_penetration,
            baseline_clearance,
            m2655_clearance,
        )
        rows.append(
            {
                "focus_id": (
                    f"m2657_protected_focus_{baseline_row.get('seed', '')}_"
                    f"{baseline_row.get('dynamics_axis_id', '')}"
                ),
                "subject_id": SUBJECT_ID,
                "scenario_role": PROTECTED_ROLE,
                "seed": baseline_row.get("seed", ""),
                "dynamics_axis_id": baseline_row.get("dynamics_axis_id", ""),
                "baseline_severity_proxy": baseline_severity,
                "m2648_severity_proxy": _empty_if_none(m2648_severity),
                "m2655_severity_proxy": _empty_if_none(m2655_severity),
                "m2648_severity_delta": _delta_or_empty(m2648_severity, baseline_severity),
                "m2655_severity_delta": _delta_or_empty(m2655_severity, baseline_severity),
                "baseline_obstacle_penetration_proxy_m": baseline_penetration,
                "m2648_obstacle_penetration_proxy_m": _empty_if_none(m2648_penetration),
                "m2655_obstacle_penetration_proxy_m": _empty_if_none(m2655_penetration),
                "m2648_obstacle_penetration_delta": _delta_or_empty(
                    m2648_penetration, baseline_penetration
                ),
                "m2655_obstacle_penetration_delta": _delta_or_empty(
                    m2655_penetration, baseline_penetration
                ),
                "baseline_minimum_obstacle_clearance_m": baseline_clearance,
                "m2648_minimum_obstacle_clearance_m": _empty_if_none(m2648_clearance),
                "m2655_minimum_obstacle_clearance_m": _empty_if_none(m2655_clearance),
                "m2648_clearance_delta": _delta_or_empty(m2648_clearance, baseline_clearance),
                "m2655_clearance_delta": _delta_or_empty(m2655_clearance, baseline_clearance),
                "m2648_any_protected_component_regressed": m2648_any_regressed,
                "m2655_any_protected_component_regressed": m2655_any_regressed,
                "m2650_regressed_row_match": _matches_m2650_regressed_row(
                    baseline_row, m2650_localization
                ),
                "blocks_claims": bool(m2648_any_regressed or m2655_any_regressed),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_report_gate_evaluation_rows(
    *,
    source: dict[str, Any],
    baseline_subject_rows: list[dict[str, str]],
    m2648_subject_rows: list[dict[str, str]],
    m2655_subject_rows: list[dict[str, str]],
    scenario_rows: list[dict[str, Any]],
    tradeoff_rows: list[dict[str, Any]],
    selected_candidate: dict[str, str],
) -> list[dict[str, Any]]:
    target_rows = [row for row in scenario_rows if row["role_class"] == "target"]
    protected_rows = [row for row in scenario_rows if row["role_class"] == "protected"]
    traceability = _traceability_ok(
        baseline_subject_rows,
        m2648_subject_rows,
        m2655_subject_rows,
    )
    target_protected_split = (
        len(target_rows) == 3
        and len(protected_rows) == 1
        and all(not _bool(row["protected_rows_in_success_denominator"]) for row in tradeoff_rows)
        and {row["role_class"] for row in tradeoff_rows} == {"target", "protected"}
    )
    m2655_failed_gate_ids = _selected_failed_gate_ids(selected_candidate)
    m2655_negative_result_preserved = (
        _bool(selected_candidate.get("target_preservation_gates_all_passed"))
        and not _bool(selected_candidate.get("protected_component_gates_all_passed"))
        and not _bool(selected_candidate.get("target_and_protected_gates_all_passed"))
        and set(PROTECTED_FAILED_GATE_IDS).issubset(set(m2655_failed_gate_ids))
    )
    all_subject_rows = baseline_subject_rows + m2648_subject_rows + m2655_subject_rows
    no_forbidden_claims = _no_forbidden_claims(selected_candidate, all_subject_rows)
    gates = (
        (
            "source_artifacts_present",
            "lineage",
            _source_artifacts_present(source),
            True,
            _source_artifact_observation(source),
            "all required source CSV/JSON artifacts and follow-up manifest are present",
            "lineage_invalid",
        ),
        (
            "scenario_role_traceability",
            "scenario_sampling",
            traceability,
            True,
            _traceability_observation(baseline_subject_rows, m2648_subject_rows, m2655_subject_rows),
            "4 scenario roles traced by role/seed/dynamics axis across baseline M2648 and M2655",
            "scenario_sampling_failure",
        ),
        (
            "target_protected_split_explicit",
            "claim_boundary",
            target_protected_split,
            True,
            f"target_roles={len(target_rows)} protected_roles={len(protected_rows)} tradeoff_rows={len(tradeoff_rows)}",
            "target and protected rows are explicit and protected rows are outside success denominators",
            "objective_overfit",
        ),
        (
            "m2655_negative_result_preserved",
            "claim_boundary",
            m2655_negative_result_preserved,
            True,
            (
                "target_preservation="
                f"{selected_candidate.get('target_preservation_gates_all_passed', '')} "
                "protected_component="
                f"{selected_candidate.get('protected_component_gates_all_passed', '')} "
                f"failed={';'.join(m2655_failed_gate_ids)}"
            ),
            "M2655 target gates pass but protected component gates fail",
            "objective_overfit",
        ),
        (
            "actor_contract_p0_72_3_preserved",
            "actor_contract",
            _actor_contract_shape_ok(all_subject_rows),
            True,
            f"observation_shape={P0_OBSERVATION_DIM} action_shape={ACTION_DIM}",
            "P0 human-view observation 72 and action 3 are preserved",
            "contract_violation",
        ),
        (
            "no_hidden_or_oracle_actor_input",
            "actor_contract",
            not _hidden_or_oracle_actor_input_detected(all_subject_rows),
            True,
            "actor_input_leak_flags none and labels actor-invisible",
            "no taxonomy repair target localization objective gate or route labels actor-visible",
            "contract_violation",
        ),
        (
            "no_ranking_promotion_success_rate_claims",
            "claim_boundary",
            no_forbidden_claims,
            True,
            (
                "candidate_selected_for_trace="
                f"{selected_candidate.get('selected_for_repair_trace', '')} "
                f"ranking_or_winner={selected_candidate.get('ranking_or_winner_field_emitted', '')} "
                f"success_rate_field={selected_candidate.get('success_rate_field_emitted', '')}"
            ),
            "no ranking winner promotion success-rate validation or performance claim is emitted",
            "objective_overfit",
        ),
        (
            "follow_up_manifest_registered",
            "lineage",
            source["source_exists"]["follow_up_manifest"],
            True,
            str(source["paths"]["follow_up_manifest"]),
            "one bounded result-audit follow-up manifest is registered",
            "lineage_invalid",
        ),
    )
    rows = []
    for gate_id, family, observed, expected, observed_text, expected_text, failure_type in gates:
        status = observed == expected
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(status),
                "observed": observed_text,
                "expected": expected_text,
                "failure_type": "" if status else failure_type,
                "blocks_claims": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    baseline_subject_rows: list[dict[str, str]],
    m2648_subject_rows: list[dict[str, str]],
    m2655_subject_rows: list[dict[str, str]],
    scenario_rows: list[dict[str, Any]],
    tradeoff_rows: list[dict[str, Any]],
    focus_rows: list[dict[str, Any]],
    report_gate_rows: list[dict[str, Any]],
    selected_candidate: dict[str, str],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    status_pass = all(_bool(row["status_pass"]) for row in report_gate_rows)
    selected_failed_gate_ids = _selected_failed_gate_ids(selected_candidate)
    summary = {
        "protocol_version": "engineering_controller_route_a_target_protected_tradeoff_report_v0",
        "result_class": (
            "engineering_controller_route_a_source_only_target_protected_tradeoff_"
            "report_materialization_preflight_pass"
        ),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "scenario_role_metric_report": str(paths["scenario_role_metric_report"]),
        "target_protected_tradeoff_rows": str(paths["target_protected_tradeoff_rows"]),
        "protected_regression_focus_rows": str(paths["protected_regression_focus_rows"]),
        "report_gate_evaluation": str(paths["report_gate_evaluation"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "follow_up_manifest_registered": source["source_exists"]["follow_up_manifest"],
        "baseline_behavior_rows": str(source["paths"]["baseline_behavior_rows"]),
        "m2648_post_repair_rows": str(source["paths"]["m2648_post_repair_rows"]),
        "m2648_gates": str(source["paths"]["m2648_gates"]),
        "m2655_post_repair_rows": str(source["paths"]["m2655_post_repair_rows"]),
        "m2655_candidate_sweep": str(source["paths"]["m2655_candidate_sweep"]),
        "m2655_gates": str(source["paths"]["m2655_gates"]),
        "m2650_localization": str(source["paths"]["m2650_localization"]),
        "source_artifacts_reanalyzed_only": True,
        "baseline_behavior_row_count": len(source["baseline_behavior_rows"]),
        "m2648_post_repair_behavior_row_count": len(source["m2648_post_repair_rows"]),
        "m2655_post_repair_behavior_row_count": len(source["m2655_post_repair_rows"]),
        "baseline_subject_row_count": len(baseline_subject_rows),
        "m2648_subject_row_count": len(m2648_subject_rows),
        "m2655_subject_row_count": len(m2655_subject_rows),
        "scenario_role_metric_report_row_count": len(scenario_rows),
        "target_protected_tradeoff_row_count": len(tradeoff_rows),
        "protected_regression_focus_row_count": len(focus_rows),
        "report_gate_evaluation_row_count": len(report_gate_rows),
        "target_role_count": sum(1 for row in scenario_rows if row["role_class"] == "target"),
        "protected_role_count": sum(1 for row in scenario_rows if row["role_class"] == "protected"),
        "target_roles": list(TARGET_ROLES),
        "protected_roles": [PROTECTED_ROLE],
        "protected_role_excluded_from_target_success_denominator": True,
        "m2655_selected_candidate_id": selected_candidate.get("candidate_id", ""),
        "m2655_selected_candidate_treated_as_winner": False,
        "m2655_target_preservation_gates_all_passed": _bool(
            selected_candidate.get("target_preservation_gates_all_passed")
        ),
        "m2655_protected_component_gates_all_passed": _bool(
            selected_candidate.get("protected_component_gates_all_passed")
        ),
        "m2655_target_and_protected_gates_all_passed": _bool(
            selected_candidate.get("target_and_protected_gates_all_passed")
        ),
        "m2655_failed_protected_gate_ids": selected_failed_gate_ids,
        "m2655_protected_component_regressed_row_count": _int(
            selected_candidate.get("protected_component_regressed_row_count")
        ),
        "m2650_real_behavior_regression_localized": _bool(
            source["m2650_localization"].get("real_behavior_regression_localized")
        ),
        "m2650_likely_severity_proxy_component_driver": source["m2650_localization"].get(
            "likely_severity_proxy_component_driver", ""
        ),
        "m2650_regressed_scenario_role": source["m2650_localization"].get(
            "regressed_scenario_role", ""
        ),
        "m2650_regressed_seed": source["m2650_localization"].get("regressed_seed", ""),
        "m2650_regressed_dynamics_axis_id": source["m2650_localization"].get(
            "regressed_dynamics_axis_id", ""
        ),
        "actor_contract_shape_72_action_3": _actor_contract_shape_ok(
            baseline_subject_rows + m2648_subject_rows + m2655_subject_rows
        ),
        "hidden_or_oracle_actor_input_detected": _hidden_or_oracle_actor_input_detected(
            baseline_subject_rows + m2648_subject_rows + m2655_subject_rows
        ),
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "localization_labels_actor_visible": False,
        "objective_gate_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "ranking_or_winner_field_emitted": False,
        "selected_candidate_status": "diagnostic_trace_only_not_winner_or_promotion",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": bool(status_pass),
        "required_artifacts_present": False,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def render_milestone_doc(
    summary: dict[str, Any],
    scenario_rows: list[dict[str, Any]],
    tradeoff_rows: list[dict[str, Any]],
    focus_rows: list[dict[str, Any]],
    report_gate_rows: list[dict[str, Any]],
) -> str:
    target_pass_rows = [
        row
        for row in tradeoff_rows
        if row["role_class"] == "target" and _bool(row["gate_pass"])
    ]
    protected_fail_rows = [
        row
        for row in tradeoff_rows
        if row["role_class"] == "protected" and not _bool(row["gate_pass"])
    ]
    protected_regressed_rows = [
        row for row in focus_rows if _bool(row["m2655_any_protected_component_regressed"])
    ]
    gates_pass = all(_bool(row["status_pass"]) for row in report_gate_rows)
    lines = [
        "# M2657 Route A Source-Only Target/Protected Tradeoff Report",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result_class: `{summary['result_class']}`",
        f"- manifest: `experiments/manifests/{summary['milestone']}.json`",
        f"- summary: `{summary['summary']}`",
        f"- scenario-role report: `{summary['scenario_role_metric_report']}`",
        f"- target/protected tradeoff rows: `{summary['target_protected_tradeoff_rows']}`",
        f"- protected regression focus rows: `{summary['protected_regression_focus_rows']}`",
        f"- report gates: `{summary['report_gate_evaluation']}`",
        f"- source rows: baseline {summary['baseline_subject_row_count']}, "
        f"M2648 {summary['m2648_subject_row_count']}, M2655 {summary['m2655_subject_row_count']} "
        f"for `{SUBJECT_ID}`",
        f"- scenario roles: {summary['target_role_count']} target and "
        f"{summary['protected_role_count']} protected",
        f"- target gate rows passed: {len(target_pass_rows)}",
        f"- protected gate rows failed: {len(protected_fail_rows)}",
        f"- M2655 selected diagnostic candidate: `{summary['m2655_selected_candidate_id']}`; "
        "not a winner and not promoted",
        f"- M2655 target preservation gates all passed: "
        f"{summary['m2655_target_preservation_gates_all_passed']}",
        f"- M2655 protected component gates all passed: "
        f"{summary['m2655_protected_component_gates_all_passed']}",
        f"- M2655 target and protected gates all passed: "
        f"{summary['m2655_target_and_protected_gates_all_passed']}",
        f"- failed protected gates: `{';'.join(summary['m2655_failed_protected_gate_ids'])}`",
        f"- M2650 localized protected regression: "
        f"{summary['m2650_real_behavior_regression_localized']} "
        f"({summary['m2650_likely_severity_proxy_component_driver']})",
        f"- M2655 protected focus rows with component regression: "
        f"{len(protected_regressed_rows)} / {summary['protected_regression_focus_row_count']}",
        f"- report gates pass: {gates_pass}",
        f"- actor/action boundary: P0 observation {P0_OBSERVATION_DIM} action {ACTION_DIM}; "
        "no hidden/oracle actor input",
        "- supported operational claim: Route A source-only scenario-role target/protected "
        "tradeoff report was materialized from existing evidence",
        f"- rejected claims: {summary['forbidden_interpretation']}",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Scenario-Role Split",
        "",
    ]
    for row in scenario_rows:
        lines.append(
            "- "
            f"`{row['scenario_role']}` {row['role_class']} metric `{row['primary_metric']}` "
            f"M2648 improved/regressed {row['m2648_improved_count']}/"
            f"{row['m2648_regressed_count']} and M2655 improved/regressed "
            f"{row['m2655_improved_count']}/{row['m2655_regressed_count']}; "
            f"M2655 gates pass {row['m2655_gate_pass']}"
        )
    lines.extend(["", "## Report Gates", ""])
    for row in report_gate_rows:
        lines.append(f"- `{row['gate_id']}`: {row['status_pass']}")
    lines.append("")
    return "\n".join(lines)


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _subject_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("subject_id") == SUBJECT_ID]


def _role_metric_spec(role: str) -> tuple[str, str]:
    if role in {"stable_avoidable", "stable_aes"}:
        return "minimum_road_margin_m", "higher_is_better"
    if role == "drift_required_recovery":
        return "drift_tradeoff_proxy", "higher_is_better"
    return "severity_proxy", "lower_is_better"


def _role_class(role: str) -> str:
    return "protected" if role == PROTECTED_ROLE else "target"


def _compare_stage(
    baseline_rows: list[dict[str, str]],
    stage_rows: list[dict[str, str]],
    metric: str,
    direction: str,
) -> dict[str, Any]:
    stage_by_key = {_row_key(row): row for row in stage_rows}
    baseline_values: list[float] = []
    stage_values: list[float] = []
    improved = 0
    regressed = 0
    unchanged = 0
    for baseline_row in baseline_rows:
        stage_row = stage_by_key.get(_row_key(baseline_row))
        if not stage_row:
            continue
        baseline_value = _metric_value(baseline_row, metric)
        stage_value = _metric_value(stage_row, metric)
        baseline_values.append(baseline_value)
        stage_values.append(stage_value)
        delta = stage_value - baseline_value
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
    return {
        "baseline_mean": _mean(baseline_values),
        "stage_mean": _mean(stage_values),
        "improved_count": improved,
        "regressed_count": regressed,
        "unchanged_count": unchanged,
    }


def _metric_value(row: dict[str, str], metric: str) -> float:
    if metric == "drift_tradeoff_proxy":
        return (
            _float(row.get("minimum_obstacle_clearance_m"))
            + _float(row.get("minimum_road_margin_m"))
            - 0.25 * abs(_float(row.get("final_abs_lateral_velocity")))
            - 0.25 * abs(_float(row.get("final_abs_yaw_rate")))
        )
    return _float(row.get(metric))


def _is_target_protected_gate(row: dict[str, str]) -> bool:
    return row.get("gate_id", "") in TARGET_PROTECTED_GATE_IDS


def _gate_role_group(gate_id: str) -> str:
    if gate_id == "target_road_boundary_margin_control":
        return "stable_avoidable;stable_aes"
    if gate_id == "target_drift_collision_recovery_tradeoff":
        return "drift_required_recovery"
    return PROTECTED_ROLE


def _gate_role_class(gate_id: str) -> str:
    return "target" if gate_id.startswith("target_") else "protected"


def _gate_metric(gate_id: str) -> str:
    if gate_id == "target_road_boundary_margin_control":
        return "minimum_road_margin_m"
    if gate_id == "target_drift_collision_recovery_tradeoff":
        return "drift_tradeoff_proxy"
    if gate_id == "obstacle_penetration_non_regression":
        return "obstacle_penetration_proxy_m"
    if gate_id == "minimum_obstacle_clearance_preservation":
        return "minimum_obstacle_clearance_m"
    if gate_id == "event_transition_guard":
        return "collision_event;road_departure_event;obstacle_passed_event"
    return "severity_proxy"


def _tradeoff_interpretation(source_stage: str, gate_id: str, gate_pass: bool) -> str:
    if gate_id.startswith("target_") and gate_pass:
        return "target gate passes but does not support repair success promotion or performance claims"
    if gate_id.startswith("target_"):
        return "target gate failure would block the repair branch"
    if gate_pass:
        return "protected mitigation component is preserved for this gate"
    if source_stage.startswith("m2655"):
        return "M2655 target preservation is retained but protected mitigation remains blocking"
    return "target-only repair changed behavior but protected mitigation regression blocks claims"


def _selected_candidate(rows: list[dict[str, str]]) -> dict[str, str]:
    for row in rows:
        if _bool(row.get("selected_for_repair_trace")):
            return row
    return rows[0] if rows else {}


def _selected_failed_gate_ids(selected_candidate: dict[str, str]) -> list[str]:
    return [
        item
        for item in str(selected_candidate.get("failed_gate_ids", "")).split(";")
        if item
    ]


def _source_artifacts_present(source: dict[str, Any]) -> bool:
    row_sources = (
        source["baseline_behavior_rows"],
        source["m2648_post_repair_rows"],
        source["m2648_gates"],
        source["m2655_post_repair_rows"],
        source["m2655_candidate_sweep"],
        source["m2655_gates"],
    )
    return (
        all(source["source_exists"].values())
        and all(bool(rows) for rows in row_sources)
        and bool(source["m2650_localization"].get("status_pass"))
    )


def _source_artifact_observation(source: dict[str, Any]) -> str:
    counts = {
        "baseline": len(source["baseline_behavior_rows"]),
        "m2648_rows": len(source["m2648_post_repair_rows"]),
        "m2648_gates": len(source["m2648_gates"]),
        "m2655_rows": len(source["m2655_post_repair_rows"]),
        "m2655_candidates": len(source["m2655_candidate_sweep"]),
        "m2655_gates": len(source["m2655_gates"]),
        "m2650_status_pass": source["m2650_localization"].get("status_pass"),
        "follow_up_manifest": source["source_exists"]["follow_up_manifest"],
    }
    return " ".join(f"{key}={value}" for key, value in counts.items())


def _traceability_ok(
    baseline_rows: list[dict[str, str]],
    m2648_rows: list[dict[str, str]],
    m2655_rows: list[dict[str, str]],
) -> bool:
    for role in SCENARIO_ROLES:
        baseline_keys = {
            _row_key(row) for row in baseline_rows if row.get("scenario_role") == role
        }
        m2648_keys = {
            _row_key(row) for row in m2648_rows if row.get("scenario_role") == role
        }
        m2655_keys = {
            _row_key(row) for row in m2655_rows if row.get("scenario_role") == role
        }
        if len(baseline_keys) != 8 or baseline_keys != m2648_keys or baseline_keys != m2655_keys:
            return False
    return True


def _traceability_observation(
    baseline_rows: list[dict[str, str]],
    m2648_rows: list[dict[str, str]],
    m2655_rows: list[dict[str, str]],
) -> str:
    parts = []
    for role in SCENARIO_ROLES:
        parts.append(
            f"{role}:"
            f"{_role_count(baseline_rows, role)}/"
            f"{_role_count(m2648_rows, role)}/"
            f"{_role_count(m2655_rows, role)}"
        )
    return " ".join(parts)


def _role_count(rows: list[dict[str, str]], role: str) -> int:
    return sum(1 for row in rows if row.get("scenario_role") == role)


def _no_forbidden_claims(
    selected_candidate: dict[str, str],
    rows: list[dict[str, str]],
) -> bool:
    return (
        not _bool(selected_candidate.get("ranking_or_winner_field_emitted"))
        and not _bool(selected_candidate.get("success_rate_field_emitted"))
        and not any(FALSE_CLAIM_FLAGS.values())
        and not _ranking_or_winner_field_emitted(rows)
    )


def _actor_contract_shape_ok(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(
        _int(row.get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(row.get("action_shape")) == ACTION_DIM
        for row in rows
    )


def _hidden_or_oracle_actor_input_detected(rows: list[dict[str, str]]) -> bool:
    visible_label_fields = (
        "taxonomy_labels_actor_visible",
        "repair_target_labels_actor_visible",
        "localization_labels_actor_visible",
        "objective_gate_labels_actor_visible",
        "route_decision_actor_visible",
    )
    for row in rows:
        leak_flags = str(row.get("actor_input_leak_flags", "none")).strip().lower()
        if leak_flags not in {"", "none", "false", "no"}:
            return True
        if any(_bool(row.get(field)) for field in visible_label_fields):
            return True
    return False


def _diagnostic_only_rows(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(
        _bool(row.get("diagnostic_only_no_ranking_claim", True)) for row in rows
    )


def _ranking_or_winner_field_emitted(rows: list[dict[str, str]]) -> bool:
    return any(_bool(row.get("ranking_or_winner_field_emitted")) for row in rows)


def _protected_components_regressed(
    baseline_severity: float,
    stage_severity: float | None,
    baseline_penetration: float,
    stage_penetration: float | None,
    baseline_clearance: float,
    stage_clearance: float | None,
) -> bool:
    severity_regressed = stage_severity is not None and stage_severity - baseline_severity > EPSILON
    penetration_regressed = (
        stage_penetration is not None and stage_penetration - baseline_penetration > EPSILON
    )
    clearance_regressed = stage_clearance is not None and stage_clearance - baseline_clearance < -EPSILON
    return bool(severity_regressed or penetration_regressed or clearance_regressed)


def _matches_m2650_regressed_row(
    row: dict[str, str],
    m2650_localization: dict[str, Any],
) -> bool:
    return (
        row.get("scenario_role") == m2650_localization.get("regressed_scenario_role")
        and str(row.get("seed")) == str(m2650_localization.get("regressed_seed"))
        and row.get("dynamics_axis_id") == m2650_localization.get("regressed_dynamics_axis_id")
        and row.get("subject_id") == m2650_localization.get("regressed_subject_id")
    )


def _row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("scenario_role", "")),
        str(row.get("seed", "")),
        str(row.get("dynamics_axis_id", "")),
    )


def _obstacle_penetration_proxy(row: dict[str, str]) -> float:
    return max(0.0, -_float(row.get("minimum_obstacle_clearance_m")))


def _obstacle_penetration_proxy_or_none(row: dict[str, str]) -> float | None:
    if not row:
        return None
    return _obstacle_penetration_proxy(row)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _empty_if_none(value: float | None) -> float | str:
    return "" if value is None else value


def _delta_or_empty(stage_value: float | None, baseline_value: float) -> float | str:
    return "" if stage_value is None else stage_value - baseline_value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-behavior-rows", default=DEFAULT_BASELINE_BEHAVIOR_ROWS)
    parser.add_argument("--m2648-post-repair-rows", default=DEFAULT_M2648_POST_REPAIR_ROWS)
    parser.add_argument("--m2648-gates", default=DEFAULT_M2648_GATES)
    parser.add_argument("--m2655-post-repair-rows", default=DEFAULT_M2655_POST_REPAIR_ROWS)
    parser.add_argument("--m2655-candidate-sweep", default=DEFAULT_M2655_CANDIDATE_SWEEP)
    parser.add_argument("--m2655-gates", default=DEFAULT_M2655_GATES)
    parser.add_argument("--m2650-localization", default=DEFAULT_M2650_LOCALIZATION)
    parser.add_argument("--follow-up-manifest", default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    materialize_target_protected_tradeoff_report(
        args.output_dir,
        baseline_behavior_rows=args.baseline_behavior_rows,
        m2648_post_repair_rows=args.m2648_post_repair_rows,
        m2648_gates=args.m2648_gates,
        m2655_post_repair_rows=args.m2655_post_repair_rows,
        m2655_candidate_sweep=args.m2655_candidate_sweep,
        m2655_gates=args.m2655_gates,
        m2650_localization=args.m2650_localization,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )


if __name__ == "__main__":
    main()
