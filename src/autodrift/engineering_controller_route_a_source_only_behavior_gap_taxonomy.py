"""Route A source-only behavior gap taxonomy materialization.

This runner reanalyzes accepted M2641 source-only diagnostic rows. It does not
execute environments, policies, replay, validation, training, ranking, or
promotion.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-"
    "taxonomy-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2645-engineering-controller-route-a-baseline-source-only-behavior-gap-"
    "taxonomy-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy"
)
DEFAULT_DOC_PATH = (
    "docs/m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-"
    "taxonomy-materialization-preflight.md"
)
DEFAULT_NEXT_MANIFEST_PATH = (
    "experiments/manifests/m2645-engineering-controller-route-a-baseline-source-only-"
    "behavior-gap-taxonomy-materialization-result-audit.json"
)

M2641_SUMMARY = (
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "summary.json"
)
M2641_MEASURED_BEHAVIOR_ROWS = (
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "measured_behavior_rows.csv"
)
M2641_MEASURED_EVENT_ROWS = (
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "measured_event_rows.csv"
)
M2641_TELEMETRY_ROWS = (
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "telemetry_rows.csv"
)
M2641_GATE_MATRIX = (
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "gate_matrix.csv"
)
M2641_ACTOR_GUARDS = (
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "actor_visibility_guard_rows.csv"
)
M2642_AUDIT_DOC = (
    "docs/m2642-engineering-controller-route-a-baseline-source-only-fresh-"
    "generalization-panel-materialization-result-audit.md"
)
M2643_SYNTHESIS_DOC = (
    "docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-"
    "generalization-panel-materialization-result-synthesis.md"
)

CLAIM_BOUNDARY = (
    "M2644 materializes source-only behavior-gap taxonomy and repair-target "
    "admission rows only; rows are not ranking, promotion, validation, "
    "success-rate, driver-performance, paper, current-sim, high-fidelity, or "
    "self-ID evidence"
)

ROLE_GAP_FIELDNAMES = [
    "row_id",
    "scenario_role",
    "row_count",
    "subject_count",
    "seed_count",
    "dynamics_axis_count",
    "collision_count",
    "road_departure_count",
    "obstacle_passed_count",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "maximum_severity_proxy",
    "primary_gap_family",
    "repair_target_candidate",
    "admitted_for_repair_target_map",
    "reference_only",
    "ranking_or_winner_field_emitted",
    "diagnostic_only_no_ranking_claim",
    "actor_visible_allowed",
    "claim_boundary",
]
SUBJECT_GAP_FIELDNAMES = [
    "row_id",
    "subject_id",
    "scenario_role",
    "row_count",
    "seed_count",
    "dynamics_axis_count",
    "collision_count",
    "road_departure_count",
    "obstacle_passed_count",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "maximum_abs_lateral_position",
    "maximum_severity_proxy",
    "primary_gap_family",
    "repair_target_candidate",
    "admitted_for_repair_target_map",
    "reference_only",
    "ranking_or_winner_field_emitted",
    "diagnostic_only_no_ranking_claim",
    "actor_visible_allowed",
    "claim_boundary",
]
DYNAMICS_AXIS_GAP_FIELDNAMES = [
    "row_id",
    "dynamics_axis_id",
    "scenario_role",
    "row_count",
    "subject_count",
    "seed_count",
    "collision_count",
    "road_departure_count",
    "obstacle_passed_count",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "maximum_severity_proxy",
    "primary_gap_family",
    "axis_sensitivity_interpretation",
    "ranking_or_winner_field_emitted",
    "diagnostic_only_no_ranking_claim",
    "actor_visible_allowed",
    "claim_boundary",
]
REPAIR_TARGET_FIELDNAMES = [
    "target_id",
    "gap_family",
    "source_row_count",
    "source_role_families",
    "admitted_for_repair_design",
    "reference_only",
    "target_scope",
    "required_audit_before_repair",
    "ranking_or_winner_field_emitted",
    "actor_visible_allowed",
    "claim_boundary",
]
CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2644",
    "status_pass",
    "evidence_required_before_claim",
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

CLAIM_CHECKS = (
    ("behavior_gap_taxonomy_materialized", True, "M2644 summary and taxonomy CSV artifacts"),
    ("repair_target_map_available_for_audit", True, "M2644 repair_target_admission_rows.csv"),
    ("controller_family_ranking", False, "future ranking gate after explicit admission"),
    ("winner_selection", False, "future ranking/promotion gate"),
    ("checkpoint_promotion", False, "future promotion gate"),
    ("success_rate_verdict", False, "future verdict milestone"),
    ("driver_performance", False, "future validation and claim audit"),
    ("validation_result", False, "future validation result"),
    ("high_fidelity_validation_result", False, "future high-fidelity validation"),
    ("paper_level_evidence", False, "future paper evidence matrix"),
    ("finite_window_vs_gru", False, "future controller-family paper route"),
    ("current_sim_verdict", False, "future current-sim synthesis"),
    ("level3_self_identification", False, "future self-ID proof gate"),
)
ALLOWED_CLAIMS = {
    "behavior_gap_taxonomy_materialized",
    "repair_target_map_available_for_audit",
}


def materialize_behavior_gap_taxonomy(
    output_dir: Path,
    *,
    measured_behavior_rows_path: Path | str = M2641_MEASURED_BEHAVIOR_ROWS,
    measured_event_rows_path: Path | str = M2641_MEASURED_EVENT_ROWS,
    telemetry_rows_path: Path | str = M2641_TELEMETRY_ROWS,
    summary_path: Path | str = M2641_SUMMARY,
    gate_matrix_path: Path | str = M2641_GATE_MATRIX,
    actor_guard_path: Path | str = M2641_ACTOR_GUARDS,
    audit_doc_path: Path | str = M2642_AUDIT_DOC,
    synthesis_doc_path: Path | str = M2643_SYNTHESIS_DOC,
    next_manifest_path: Path | str = DEFAULT_NEXT_MANIFEST_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts(
        measured_behavior_rows_path=measured_behavior_rows_path,
        measured_event_rows_path=measured_event_rows_path,
        telemetry_rows_path=telemetry_rows_path,
        summary_path=summary_path,
        gate_matrix_path=gate_matrix_path,
        actor_guard_path=actor_guard_path,
        audit_doc_path=audit_doc_path,
        synthesis_doc_path=synthesis_doc_path,
        next_manifest_path=next_manifest_path,
    )
    rows = source["measured_behavior_rows"]
    role_rows = build_role_gap_rows(rows)
    subject_rows = build_subject_gap_rows(rows)
    axis_rows = build_dynamics_axis_gap_rows(rows)
    repair_rows = build_repair_target_admission_rows(role_rows, axis_rows)
    claim_rows = build_claim_boundary_rows()

    role_path = output_dir / "role_gap_rows.csv"
    subject_path = output_dir / "subject_gap_rows.csv"
    axis_path = output_dir / "dynamics_axis_gap_rows.csv"
    repair_path = output_dir / "repair_target_admission_rows.csv"
    claim_path = output_dir / "claim_boundary_rows.csv"
    gates_path = output_dir / "gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(role_path, role_rows, fieldnames=ROLE_GAP_FIELDNAMES)
    write_csv_rows(subject_path, subject_rows, fieldnames=SUBJECT_GAP_FIELDNAMES)
    write_csv_rows(axis_path, axis_rows, fieldnames=DYNAMICS_AXIS_GAP_FIELDNAMES)
    write_csv_rows(repair_path, repair_rows, fieldnames=REPAIR_TARGET_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)

    metrics = _metrics(
        source=source,
        role_rows=role_rows,
        subject_rows=subject_rows,
        axis_rows=axis_rows,
        repair_rows=repair_rows,
        claim_rows=claim_rows,
        role_path=role_path,
        subject_path=subject_path,
        axis_path=axis_path,
        repair_path=repair_path,
        claim_path=claim_path,
        gates_path=gates_path,
        output_dir=output_dir,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    gate_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(gates_path, gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = _summary(metrics, gate_rows)
    write_json(output_dir / "summary.json", summary)
    _write_doc(doc_output, summary)
    return summary


def build_role_gap_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["scenario_role"]].append(row)
    return [
        _gap_row(
            group,
            row_id=f"m2644_role_gap_{role}",
            scenario_role=role,
            subject_id=None,
            dynamics_axis_id=None,
            fieldnames=ROLE_GAP_FIELDNAMES,
        )
        for role, group in sorted(grouped.items())
    ]


def build_subject_gap_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["subject_id"], row["scenario_role"])].append(row)
    return [
        _gap_row(
            group,
            row_id=f"m2644_subject_gap_{subject_id}_{role}",
            scenario_role=role,
            subject_id=subject_id,
            dynamics_axis_id=None,
            fieldnames=SUBJECT_GAP_FIELDNAMES,
        )
        for (subject_id, role), group in sorted(grouped.items())
    ]


def build_dynamics_axis_gap_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped = defaultdict(list)
    axis_totals = _axis_totals(rows)
    axis_interpretation = _axis_sensitivity_interpretation(axis_totals)
    output = []
    for (axis_id, role), group in sorted(
        ((key, value) for key, value in _group_by(rows, ("dynamics_axis_id", "scenario_role")).items()),
        key=lambda item: item[0],
    ):
        row = _gap_row(
            group,
            row_id=f"m2644_axis_gap_{axis_id}_{role}",
            scenario_role=role,
            subject_id=None,
            dynamics_axis_id=axis_id,
            fieldnames=DYNAMICS_AXIS_GAP_FIELDNAMES,
        )
        row["axis_sensitivity_interpretation"] = axis_interpretation
        output.append(row)
    return output


def build_repair_target_admission_rows(
    role_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    role_by_gap = defaultdict(list)
    count_by_gap = Counter()
    for row in role_rows:
        role_by_gap[row["primary_gap_family"]].append(row["scenario_role"])
        count_by_gap[row["primary_gap_family"]] += int(row["row_count"])
    axis_interpretation = (
        axis_rows[0]["axis_sensitivity_interpretation"] if axis_rows else "axis_sensitivity_unknown"
    )
    rows = []
    for gap_family in (
        "road_departure_dominant_gap",
        "drift_recovery_mixed_gap",
        "mitigation_collision_saturated_reference",
        "axis_sensitivity_not_yet_decisive",
    ):
        if gap_family == "axis_sensitivity_not_yet_decisive":
            source_count = sum(int(row["row_count"]) for row in axis_rows)
            roles = sorted({row["scenario_role"] for row in axis_rows})
            admitted = False
            reference_only = True
            scope = "diagnostic_axis_monitoring_not_repair_target"
        else:
            source_count = count_by_gap[gap_family]
            roles = sorted(set(role_by_gap[gap_family]))
            admitted = gap_family in {"road_departure_dominant_gap", "drift_recovery_mixed_gap"} and source_count > 0
            reference_only = gap_family == "mitigation_collision_saturated_reference"
            scope = _target_scope(gap_family)
        rows.append(
            {
                "target_id": f"m2644_repair_target_{gap_family}",
                "gap_family": gap_family,
                "source_row_count": int(source_count),
                "source_role_families": ";".join(roles),
                "admitted_for_repair_design": bool(admitted),
                "reference_only": bool(reference_only),
                "target_scope": scope,
                "required_audit_before_repair": True,
                "ranking_or_winner_field_emitted": False,
                "actor_visible_allowed": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        rows.append(
            {
                "claim_id": f"m2644_claim_boundary_{claim_family}",
                "claim_family": claim_family,
                "allowed_in_m2644": bool(allowed),
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not allowed),
                "evidence_required_before_claim": evidence,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    gates = (
        ("source_artifacts_exist", "artifact", metrics["source_artifacts_exist"], True, "metric_artifact"),
        ("role_gap_row_count", "taxonomy_shape", metrics["role_gap_row_count"], 4, "metric_artifact"),
        ("subject_gap_row_count", "taxonomy_shape", metrics["subject_gap_row_count"], 20, "metric_artifact"),
        ("dynamics_axis_gap_row_count", "taxonomy_shape", metrics["dynamics_axis_gap_row_count"], 8, "metric_artifact"),
        ("repair_target_admission_row_count", "taxonomy_shape", metrics["repair_target_admission_row_count"], 4, "metric_artifact"),
        ("claim_boundary_row_count", "claim_boundary", metrics["claim_boundary_row_count"], len(CLAIM_CHECKS), "objective_overfit"),
        ("actor_contract_shape_72_action_3", "actor_contract", metrics["actor_contract_shape_72_action_3"], True, "contract_violation"),
        ("taxonomy_labels_actor_visible", "actor_contract", metrics["taxonomy_labels_actor_visible"], False, "contract_violation"),
        ("all_rows_diagnostic_only_no_ranking_claim", "claim_boundary", metrics["all_rows_diagnostic_only_no_ranking_claim"], True, "objective_overfit"),
        ("repair_targets_available_for_audit", "taxonomy_shape", metrics["repair_targets_available_for_audit"], True, "metric_artifact"),
        ("next_audit_manifest_registered", "lineage", metrics["next_audit_manifest_registered"], True, "lineage_invalid"),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("winner_selected", "forbidden_claim", metrics["winner_selected"], False, "objective_overfit"),
        ("success_rate_computed", "forbidden_claim", metrics["success_rate_computed"], False, "objective_overfit"),
        ("driver_performance_claim_made", "forbidden_claim", metrics["driver_performance_claim_made"], False, "objective_overfit"),
    )
    rows = []
    for gate_id, family, observed, expected, failure_type in gates:
        status = observed == expected
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(status),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status else failure_type,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _gap_row(
    group: list[dict[str, str]],
    *,
    row_id: str,
    scenario_role: str,
    subject_id: str | None,
    dynamics_axis_id: str | None,
    fieldnames: list[str],
) -> dict[str, Any]:
    family = _gap_family(group, scenario_role=scenario_role)
    row = {
        "row_id": row_id,
        "subject_id": subject_id or "",
        "dynamics_axis_id": dynamics_axis_id or "",
        "scenario_role": scenario_role,
        "row_count": len(group),
        "subject_count": len({row["subject_id"] for row in group}),
        "seed_count": len({row["seed"] for row in group}),
        "dynamics_axis_count": len({row["dynamics_axis_id"] for row in group}),
        "collision_count": _count_true(group, "collision_event"),
        "road_departure_count": _count_true(group, "road_departure_event"),
        "obstacle_passed_count": _count_true(group, "obstacle_passed_event"),
        "minimum_obstacle_clearance_m": _min_float(group, "minimum_obstacle_clearance_m"),
        "minimum_road_margin_m": _min_float(group, "minimum_road_margin_m"),
        "maximum_abs_lateral_position": _max_float(group, "maximum_abs_lateral_position"),
        "maximum_severity_proxy": _max_float(group, "severity_proxy"),
        "primary_gap_family": family,
        "repair_target_candidate": family in {"road_departure_dominant_gap", "drift_recovery_mixed_gap"},
        "admitted_for_repair_target_map": family in {"road_departure_dominant_gap", "drift_recovery_mixed_gap"},
        "reference_only": family == "mitigation_collision_saturated_reference",
        "axis_sensitivity_interpretation": "",
        "ranking_or_winner_field_emitted": False,
        "diagnostic_only_no_ranking_claim": True,
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return {field: row.get(field, "") for field in fieldnames}


def _metrics(
    *,
    source: dict[str, Any],
    role_rows: list[dict[str, Any]],
    subject_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    role_path: Path,
    subject_path: Path,
    axis_path: Path,
    repair_path: Path,
    claim_path: Path,
    gates_path: Path,
    output_dir: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    measured_rows = source["measured_behavior_rows"]
    gate_rows = source["gate_rows"]
    actor_guard_rows = source["actor_guard_rows"]
    source_artifacts_exist = all(source["source_exists"].values())
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in measured_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in measured_rows} == {ACTION_DIM}
    )
    all_rows_diagnostic = {
        row["diagnostic_only_no_ranking_claim"].lower() for row in measured_rows
    } == {"true"}
    repair_targets_available = any(
        str(row["admitted_for_repair_design"]).lower() == "true" for row in repair_rows
    )
    all_source_gates_pass = bool(gate_rows) and {row["status_pass"] for row in gate_rows} == {"True"}
    all_actor_guards_pass = bool(actor_guard_rows) and {
        row["status_pass"] for row in actor_guard_rows
    } == {"True"}
    return {
        "result_class": "engineering_controller_route_a_source_only_behavior_gap_taxonomy_preflight_pending",
        "protocol_version": "engineering_controller_behavior_gap_taxonomy_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "role_gap_rows": str(role_path),
        "subject_gap_rows": str(subject_path),
        "dynamics_axis_gap_rows": str(axis_path),
        "repair_target_admission_rows": str(repair_path),
        "claim_boundary_rows": str(claim_path),
        "gate_matrix": str(gates_path),
        "doc": str(doc_path),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": [
            path for path, exists in source["source_exists"].items() if not exists
        ],
        "m2641_status_pass": bool(source["summary"].get("status_pass")),
        "m2641_gate_matrix_pass": bool(all_source_gates_pass),
        "m2641_actor_visibility_guard_rows_pass": bool(all_actor_guards_pass),
        "source_measured_behavior_row_count": len(measured_rows),
        "role_gap_row_count": len(role_rows),
        "subject_gap_row_count": len(subject_rows),
        "dynamics_axis_gap_row_count": len(axis_rows),
        "repair_target_admission_row_count": len(repair_rows),
        "claim_boundary_row_count": len(claim_rows),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "taxonomy_labels_actor_visible": False,
        "all_rows_diagnostic_only_no_ranking_claim": bool(all_rows_diagnostic),
        "repair_targets_available_for_audit": bool(repair_targets_available),
        "next_audit_manifest_registered": bool(source["next_manifest_registered"]),
        "road_departure_dominant_gap_present": _family_present(role_rows, "road_departure_dominant_gap"),
        "drift_recovery_mixed_gap_present": _family_present(role_rows, "drift_recovery_mixed_gap"),
        "mitigation_collision_saturated_reference_present": _family_present(
            role_rows, "mitigation_collision_saturated_reference"
        ),
        "axis_sensitivity_not_yet_decisive_present": any(
            row["gap_family"] == "axis_sensitivity_not_yet_decisive" for row in repair_rows
        ),
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "external_high_fidelity_simulation_included": False,
        "high_fidelity_simulation_run": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _summary(metrics: dict[str, Any], gate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        metrics["source_artifacts_exist"]
        and metrics["m2641_status_pass"]
        and metrics["m2641_gate_matrix_pass"]
        and metrics["m2641_actor_visibility_guard_rows_pass"]
        and metrics["source_measured_behavior_row_count"] == 160
        and metrics["role_gap_row_count"] == 4
        and metrics["subject_gap_row_count"] == 20
        and metrics["dynamics_axis_gap_row_count"] == 8
        and metrics["repair_target_admission_row_count"] == 4
        and metrics["claim_boundary_row_count"] == len(CLAIM_CHECKS)
        and metrics["actor_contract_shape_72_action_3"]
        and not metrics["taxonomy_labels_actor_visible"]
        and metrics["all_rows_diagnostic_only_no_ranking_claim"]
        and metrics["repair_targets_available_for_audit"]
        and metrics["next_audit_manifest_registered"]
        and gate_matrix_pass
        and not metrics["ranking_run"]
        and not metrics["winner_selected"]
        and not metrics["success_rate_computed"]
        and not metrics["driver_performance_claim_made"]
    )
    return {
        **metrics,
        "result_class": (
            "engineering_controller_route_a_source_only_behavior_gap_taxonomy_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_source_only_behavior_gap_taxonomy_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "gate_matrix_pass": bool(gate_matrix_pass),
        "gate_matrix_row_count": len(gate_rows),
    }


def _load_source_artifacts(**paths: Any) -> dict[str, Any]:
    normalized = {key: Path(value) for key, value in paths.items()}
    return {
        "summary": read_json(normalized["summary_path"]),
        "measured_behavior_rows": _read_csv_rows(normalized["measured_behavior_rows_path"]),
        "measured_event_rows": _read_csv_rows(normalized["measured_event_rows_path"]),
        "telemetry_row_count": _csv_data_row_count(normalized["telemetry_rows_path"]),
        "gate_rows": _read_csv_rows(normalized["gate_matrix_path"]),
        "actor_guard_rows": _read_csv_rows(normalized["actor_guard_path"]),
        "next_manifest_registered": normalized["next_manifest_path"].exists(),
        "source_exists": {str(path): path.exists() for path in normalized.values()},
    }


def _gap_family(group: list[dict[str, str]], *, scenario_role: str) -> str:
    collision_count = _count_true(group, "collision_event")
    road_count = _count_true(group, "road_departure_event")
    if scenario_role == "unavoidable_mitigation" and collision_count == len(group):
        return "mitigation_collision_saturated_reference"
    if scenario_role == "drift_required_recovery" and collision_count > 0 and road_count > 0:
        return "drift_recovery_mixed_gap"
    if road_count > 0 and collision_count == 0:
        return "road_departure_dominant_gap"
    if collision_count > 0 and road_count > 0:
        return "mixed_collision_and_road_boundary_gap"
    if collision_count > 0:
        return "collision_dominant_gap"
    return "no_collision_margin_monitoring"


def _axis_totals(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    totals = defaultdict(lambda: {"rows": 0, "collisions": 0, "road_departures": 0})
    for row in rows:
        axis = row["dynamics_axis_id"]
        totals[axis]["rows"] += 1
        totals[axis]["collisions"] += int(_truthy(row["collision_event"]))
        totals[axis]["road_departures"] += int(_truthy(row["road_departure_event"]))
    return dict(totals)


def _axis_sensitivity_interpretation(axis_totals: dict[str, dict[str, int]]) -> str:
    if set(axis_totals) != {"fresh_nominal_or_role_default", "fresh_fault_delay_noise"}:
        return "axis_sensitivity_unknown"
    nominal = axis_totals["fresh_nominal_or_role_default"]
    fault = axis_totals["fresh_fault_delay_noise"]
    collision_delta = abs(int(nominal["collisions"]) - int(fault["collisions"]))
    road_delta = abs(int(nominal["road_departures"]) - int(fault["road_departures"]))
    if collision_delta <= 2 and road_delta <= 4:
        return "axis_sensitivity_not_yet_decisive"
    return "axis_sensitivity_candidate"


def _target_scope(gap_family: str) -> str:
    return {
        "road_departure_dominant_gap": "road_boundary_margin_control",
        "drift_recovery_mixed_gap": "drift_collision_recovery_tradeoff",
        "mitigation_collision_saturated_reference": "mitigation_reference_only",
        "axis_sensitivity_not_yet_decisive": "diagnostic_axis_monitoring_not_repair_target",
    }.get(gap_family, "diagnostic_gap_monitoring")


def _group_by(rows: list[dict[str, str]], keys: tuple[str, ...]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def _count_true(rows: list[dict[str, str]], key: str) -> int:
    return sum(_truthy(row[key]) for row in rows)


def _truthy(value: str) -> bool:
    return str(value).lower() == "true"


def _min_float(rows: list[dict[str, str]], key: str) -> float:
    return min(float(row[key]) for row in rows) if rows else 0.0


def _max_float(rows: list[dict[str, str]], key: str) -> float:
    return max(float(row[key]) for row in rows) if rows else 0.0


def _family_present(rows: list[dict[str, Any]], family: str) -> bool:
    return any(row["primary_gap_family"] == family for row in rows)


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_data_row_count(path: Path | str) -> int:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _line in handle) - 1, 0)


def _write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2644 Engineering Controller Route A Source-Only Behavior Gap Taxonomy Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_source_only_behavior_gap_taxonomy.py`",
                f"- summary: `{summary['summary']}`",
                f"- role gap rows: `{summary['role_gap_rows']}`",
                f"- subject gap rows: `{summary['subject_gap_rows']}`",
                f"- dynamics axis gap rows: `{summary['dynamics_axis_gap_rows']}`",
                f"- repair target admission rows: `{summary['repair_target_admission_rows']}`",
                f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
                f"- gate matrix: `{summary['gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- reset/step/rollout/replay/validation/training/PPO executed: `false`",
                "- ranking/winner/promotion/success-rate/performance claims: `false`",
                "",
                "## Materialized Taxonomy",
                "",
                "M2644 reanalyzes the accepted M2641 measured behavior rows into",
                "role, subject, dynamics-axis, repair-target, claim-boundary, and",
                "gate rows. Taxonomy labels and repair-target labels are artifact",
                "metadata only and are not actor-visible inputs.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"source_measured_behavior_row_count: {summary['source_measured_behavior_row_count']}",
                f"role_gap_row_count: {summary['role_gap_row_count']}",
                f"subject_gap_row_count: {summary['subject_gap_row_count']}",
                f"dynamics_axis_gap_row_count: {summary['dynamics_axis_gap_row_count']}",
                f"repair_target_admission_row_count: {summary['repair_target_admission_row_count']}",
                f"claim_boundary_row_count: {summary['claim_boundary_row_count']}",
                f"gate_matrix_pass: {str(summary['gate_matrix_pass']).lower()}",
                f"road_departure_dominant_gap_present: {str(summary['road_departure_dominant_gap_present']).lower()}",
                f"drift_recovery_mixed_gap_present: {str(summary['drift_recovery_mixed_gap_present']).lower()}",
                f"mitigation_collision_saturated_reference_present: {str(summary['mitigation_collision_saturated_reference_present']).lower()}",
                f"axis_sensitivity_not_yet_decisive_present: {str(summary['axis_sensitivity_not_yet_decisive_present']).lower()}",
                "```",
                "",
                "## Result",
                "",
                "M2644 creates a source-only repair-target map for audit. It does",
                "not rank subjects, select a winner, promote checkpoints, compute",
                "success rates, validate a controller, or claim driver performance.",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize Route A source-only behavior gap taxonomy."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--next-manifest-path", type=Path, default=Path(DEFAULT_NEXT_MANIFEST_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_behavior_gap_taxonomy(
        args.output_dir,
        doc_path=args.doc_path,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        next_manifest_path=args.next_manifest_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"role_gap_row_count={summary['role_gap_row_count']}")
    print(f"subject_gap_row_count={summary['subject_gap_row_count']}")
    print(f"dynamics_axis_gap_row_count={summary['dynamics_axis_gap_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
