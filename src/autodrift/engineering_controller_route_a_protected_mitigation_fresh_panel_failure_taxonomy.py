"""Route A protected mitigation fresh-panel failure taxonomy.

This runner reanalyzes accepted M2662 artifacts. It does not execute
environments, policies, replay, validation, training, ranking, or promotion.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2664-engineering-controller-route-a-protected-mitigation-fresh-panel-"
    "failure-taxonomy-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-"
    "failure-taxonomy-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2664-engineering-controller-route-a-protected-mitigation-fresh-panel-"
    "failure-taxonomy-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2665-engineering-controller-route-a-protected-"
    "mitigation-fresh-panel-failure-taxonomy-materialization-result-audit.json"
)

M2662_SUMMARY = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/"
    "summary.json"
)
M2662_PANEL_SPEC_ROWS = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/"
    "panel_spec_rows.csv"
)
M2662_MEASURED_BEHAVIOR_ROWS = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/"
    "measured_behavior_rows.csv"
)
M2662_PROTECTED_MITIGATION_GATES = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/"
    "protected_mitigation_gate_rows.csv"
)
M2662_CLAIM_BOUNDARY_ROWS = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/"
    "claim_boundary_rows.csv"
)
M2662_GATE_MATRIX = Path(
    "runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/"
    "gate_matrix.csv"
)

CLAIM_SCOPE = (
    "Route A protected mitigation fresh-panel failure taxonomy only; no reset, "
    "rollout, replay, validation, training, ranking, winner selection, "
    "promotion, success-rate verdict, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, controller ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, validation result, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation result, full ideal driver completion, or self-ID "
    "evidence"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

SUBJECT_FIELDNAMES = [
    "taxonomy_id",
    "subject_id",
    "gate_row_count",
    "blocking_gate_row_count",
    "passing_gate_row_count",
    "regressed_row_count",
    "improved_row_count",
    "axis_count",
    "metric_count",
    "seed_count",
    "seed_ids",
    "blocking_fraction",
    "primary_failure_family",
    "protected_blocker_preserved",
    "protected_rows_in_success_denominator",
    "ranking_or_winner_field_emitted",
    "actor_visible_allowed",
    "claim_boundary",
]
AXIS_FIELDNAMES = [
    "taxonomy_id",
    "dynamics_axis_id",
    "dynamics_axis_family",
    "gate_row_count",
    "blocking_gate_row_count",
    "passing_gate_row_count",
    "regressed_row_count",
    "improved_row_count",
    "subject_count",
    "metric_count",
    "seed_count",
    "seed_ids",
    "blocking_fraction",
    "primary_failure_family",
    "protected_blocker_preserved",
    "protected_rows_in_success_denominator",
    "ranking_or_winner_field_emitted",
    "actor_visible_allowed",
    "claim_boundary",
]
METRIC_FIELDNAMES = [
    "taxonomy_id",
    "metric",
    "metric_direction",
    "gate_row_count",
    "blocking_gate_row_count",
    "passing_gate_row_count",
    "regressed_row_count",
    "improved_row_count",
    "subject_count",
    "axis_count",
    "seed_count",
    "seed_ids",
    "blocking_fraction",
    "primary_failure_family",
    "protected_blocker_preserved",
    "protected_rows_in_success_denominator",
    "ranking_or_winner_field_emitted",
    "actor_visible_allowed",
    "claim_boundary",
]
COMBINED_FIELDNAMES = [
    "taxonomy_id",
    "subject_id",
    "dynamics_axis_id",
    "gate_row_count",
    "blocking_gate_row_count",
    "passing_gate_row_count",
    "regressed_row_count",
    "improved_row_count",
    "metric_count",
    "blocking_metrics",
    "passing_metrics",
    "seed_count",
    "seed_ids",
    "blocking_fraction",
    "primary_failure_family",
    "protected_blocker_preserved",
    "protected_rows_in_success_denominator",
    "ranking_or_winner_field_emitted",
    "actor_visible_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2664",
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
    ("failure_taxonomy_materialized", True, "M2664 taxonomy rows and summary"),
    ("protected_blocker_preserved", True, "M2664 protected blocker taxonomy rows"),
    ("follow_up_result_audit_registered", True, "M2665 manifest"),
    ("repair_success", False, "future proof/generalization/promotion gates"),
    ("controller_family_ranking", False, "future ranking gate after explicit admission"),
    ("winner_selection", False, "future promotion gate"),
    ("checkpoint_promotion", False, "future promotion gate"),
    ("success_rate_verdict", False, "future verdict milestone"),
    ("driver_performance", False, "future validation and claim audit"),
    ("validation_result", False, "future validation result"),
    ("high_fidelity_validation_result", False, "future high-fidelity validation"),
    ("paper_level_evidence", False, "future paper evidence matrix"),
    ("finite_window_vs_gru", False, "future controller-family paper route"),
    ("current_sim_verdict", False, "future current-sim synthesis"),
    ("level3_self_identification", False, "future self-ID proof gate"),
    ("full_ideal_driver_completion", False, "future full ideal driver gate"),
)

POLICY_SUBJECTS = {
    "m1154_original_policy",
    "m2532_guarded_repair_policy",
    "m2537_mitigation_preserving_policy",
}


def materialize_failure_taxonomy(
    output_dir: Path | str,
    *,
    summary_path: Path | str = M2662_SUMMARY,
    panel_spec_rows_path: Path | str = M2662_PANEL_SPEC_ROWS,
    measured_behavior_rows_path: Path | str = M2662_MEASURED_BEHAVIOR_ROWS,
    protected_mitigation_gates_path: Path | str = M2662_PROTECTED_MITIGATION_GATES,
    claim_boundary_rows_path: Path | str = M2662_CLAIM_BOUNDARY_ROWS,
    gate_matrix_path: Path | str = M2662_GATE_MATRIX,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    source = load_source_artifacts(
        summary_path=summary_path,
        panel_spec_rows_path=panel_spec_rows_path,
        measured_behavior_rows_path=measured_behavior_rows_path,
        protected_mitigation_gates_path=protected_mitigation_gates_path,
        claim_boundary_rows_path=claim_boundary_rows_path,
        gate_matrix_path=gate_matrix_path,
        follow_up_manifest=follow_up_manifest,
    )
    protected_gate_rows = [
        row
        for row in source["protected_mitigation_gates"]
        if row.get("subject_id") in POLICY_SUBJECTS
    ]
    seed_ids = _seed_ids(source["panel_spec_rows"], source["measured_behavior_rows"])
    subject_rows = build_subject_failure_taxonomy_rows(protected_gate_rows, seed_ids=seed_ids)
    axis_rows = build_axis_failure_taxonomy_rows(
        protected_gate_rows,
        panel_rows=source["panel_spec_rows"],
        seed_ids=seed_ids,
    )
    metric_rows = build_metric_failure_taxonomy_rows(protected_gate_rows, seed_ids=seed_ids)
    combined_rows = build_combined_failure_taxonomy_rows(protected_gate_rows, seed_ids=seed_ids)
    claim_rows = build_claim_boundary_rows()

    paths = {
        "summary": output_path / "summary.json",
        "subject_failure_taxonomy_rows": output_path / "subject_failure_taxonomy_rows.csv",
        "axis_failure_taxonomy_rows": output_path / "axis_failure_taxonomy_rows.csv",
        "metric_failure_taxonomy_rows": output_path / "metric_failure_taxonomy_rows.csv",
        "combined_failure_taxonomy_rows": output_path / "combined_failure_taxonomy_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }
    write_csv_rows(paths["subject_failure_taxonomy_rows"], subject_rows, fieldnames=SUBJECT_FIELDNAMES)
    write_csv_rows(paths["axis_failure_taxonomy_rows"], axis_rows, fieldnames=AXIS_FIELDNAMES)
    write_csv_rows(paths["metric_failure_taxonomy_rows"], metric_rows, fieldnames=METRIC_FIELDNAMES)
    write_csv_rows(paths["combined_failure_taxonomy_rows"], combined_rows, fieldnames=COMBINED_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    metrics = build_metrics(
        output_dir=output_path,
        paths=paths,
        source=source,
        protected_gate_rows=protected_gate_rows,
        subject_rows=subject_rows,
        axis_rows=axis_rows,
        metric_rows=metric_rows,
        combined_rows=combined_rows,
        claim_rows=claim_rows,
        seed_ids=seed_ids,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    gate_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(metrics, gate_rows)
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    summary["required_artifacts_present"] = all(path.exists() for path in paths.values())
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    write_json(paths["summary"], summary)
    return summary


def load_source_artifacts(
    *,
    summary_path: Path | str,
    panel_spec_rows_path: Path | str,
    measured_behavior_rows_path: Path | str,
    protected_mitigation_gates_path: Path | str,
    claim_boundary_rows_path: Path | str,
    gate_matrix_path: Path | str,
    follow_up_manifest: Path | str,
) -> dict[str, Any]:
    paths = {
        "summary": Path(summary_path),
        "panel_spec_rows": Path(panel_spec_rows_path),
        "measured_behavior_rows": Path(measured_behavior_rows_path),
        "protected_mitigation_gates": Path(protected_mitigation_gates_path),
        "m2662_claim_boundary_rows": Path(claim_boundary_rows_path),
        "m2662_gate_matrix": Path(gate_matrix_path),
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "summary": read_json(paths["summary"]),
        "panel_spec_rows": _read_csv_rows(paths["panel_spec_rows"]),
        "measured_behavior_rows": _read_csv_rows(paths["measured_behavior_rows"]),
        "protected_mitigation_gates": _read_csv_rows(paths["protected_mitigation_gates"]),
        "m2662_claim_boundary_rows": _read_csv_rows(paths["m2662_claim_boundary_rows"]),
        "m2662_gate_matrix": _read_csv_rows(paths["m2662_gate_matrix"]),
    }


def build_subject_failure_taxonomy_rows(
    gate_rows: list[dict[str, str]],
    *,
    seed_ids: list[str],
) -> list[dict[str, Any]]:
    grouped = _group_by(gate_rows, ("subject_id",))
    return [
        _taxonomy_row(
            group,
            row_id=f"m2664_subject_failure_{subject_id}",
            fieldnames=SUBJECT_FIELDNAMES,
            subject_id=subject_id,
            seed_ids=seed_ids,
        )
        for (subject_id,), group in sorted(grouped.items())
    ]


def build_axis_failure_taxonomy_rows(
    gate_rows: list[dict[str, str]],
    *,
    panel_rows: list[dict[str, str]],
    seed_ids: list[str],
) -> list[dict[str, Any]]:
    axis_family = {row["dynamics_axis_id"]: row.get("dynamics_axis_family", "") for row in panel_rows}
    grouped = _group_by(gate_rows, ("dynamics_axis_id",))
    rows = []
    for (axis_id,), group in sorted(grouped.items()):
        row = _taxonomy_row(
            group,
            row_id=f"m2664_axis_failure_{axis_id}",
            fieldnames=AXIS_FIELDNAMES,
            dynamics_axis_id=axis_id,
            seed_ids=seed_ids,
        )
        row["dynamics_axis_family"] = axis_family.get(axis_id, "")
        rows.append(row)
    return rows


def build_metric_failure_taxonomy_rows(
    gate_rows: list[dict[str, str]],
    *,
    seed_ids: list[str],
) -> list[dict[str, Any]]:
    grouped = _group_by(gate_rows, ("metric",))
    rows = []
    for (metric,), group in sorted(grouped.items()):
        directions = sorted({row.get("metric_direction", "") for row in group})
        row = _taxonomy_row(
            group,
            row_id=f"m2664_metric_failure_{metric}",
            fieldnames=METRIC_FIELDNAMES,
            metric=metric,
            seed_ids=seed_ids,
        )
        row["metric_direction"] = ";".join(directions)
        rows.append(row)
    return rows


def build_combined_failure_taxonomy_rows(
    gate_rows: list[dict[str, str]],
    *,
    seed_ids: list[str],
) -> list[dict[str, Any]]:
    grouped = _group_by(gate_rows, ("subject_id", "dynamics_axis_id"))
    rows = []
    for (subject_id, axis_id), group in sorted(grouped.items()):
        blocking_metrics = sorted(row["metric"] for row in group if _bool(row.get("blocks_claims")))
        passing_metrics = sorted(row["metric"] for row in group if not _bool(row.get("blocks_claims")))
        row = _taxonomy_row(
            group,
            row_id=f"m2664_combined_failure_{subject_id}_{axis_id}",
            fieldnames=COMBINED_FIELDNAMES,
            subject_id=subject_id,
            dynamics_axis_id=axis_id,
            seed_ids=seed_ids,
        )
        row["blocking_metrics"] = ";".join(blocking_metrics)
        row["passing_metrics"] = ";".join(passing_metrics)
        rows.append(row)
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    allowed = {claim for claim, allowed_flag, _ in CLAIM_CHECKS if allowed_flag}
    return [
        {
            "claim_id": f"m2664_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2664": bool(allowed_flag),
            "status_pass": bool(claim in allowed or not allowed_flag),
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed_flag, evidence_required in CLAIM_CHECKS
    ]


def build_metrics(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    protected_gate_rows: list[dict[str, str]],
    subject_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    combined_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    seed_ids: list[str],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    measured_rows = source["measured_behavior_rows"]
    panel_rows = source["panel_spec_rows"]
    m2662_summary = source["summary"]
    protected_blocking_count = sum(_bool(row.get("blocks_claims")) for row in protected_gate_rows)
    protected_regressed_count = sum(_int(row.get("regressed_row_count")) for row in protected_gate_rows)
    source_artifacts_present = all(source["source_exists"].values())
    source_gate_matrix_pass = bool(source["m2662_gate_matrix"]) and all(
        _bool(row.get("status_pass")) for row in source["m2662_gate_matrix"]
    )
    source_claim_boundary_pass = bool(source["m2662_claim_boundary_rows"]) and all(
        _bool(row.get("status_pass")) for row in source["m2662_claim_boundary_rows"]
    )
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in measured_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in measured_rows} == {ACTION_DIM}
    )
    hidden_oracle_clean = {
        str(row.get("actor_input_leak_flags", "")).lower() for row in measured_rows
    } <= {"", "none"} and not _bool(m2662_summary.get("hidden_oracle_actor_input_detected"))
    target_protected_split_preserved = (
        {row.get("role_class") for row in panel_rows} == {"protected"}
        and {row.get("scenario_role") for row in measured_rows} == {"unavoidable_mitigation"}
        and {_bool(row.get("protected_rows_in_success_denominator")) for row in measured_rows} == {False}
        and _bool(m2662_summary.get("target_protected_split_preserved"))
    )
    taxonomy_labels_actor_visible = any(
        _bool(row.get("actor_visible_allowed")) for rows in (subject_rows, axis_rows, metric_rows, combined_rows) for row in rows
    )
    claim_boundary_pass = all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values())
    broad_blocker_preserved = (
        protected_blocking_count >= 25
        and protected_regressed_count >= 79
        and all(_bool(row["protected_blocker_preserved"]) for row in subject_rows + axis_rows + metric_rows + combined_rows)
    )
    return {
        "protocol_version": "engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy_v0",
        "result_class": "engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy_pending",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "subject_failure_taxonomy_rows": str(paths["subject_failure_taxonomy_rows"]),
        "axis_failure_taxonomy_rows": str(paths["axis_failure_taxonomy_rows"]),
        "metric_failure_taxonomy_rows": str(paths["metric_failure_taxonomy_rows"]),
        "combined_failure_taxonomy_rows": str(paths["combined_failure_taxonomy_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "source_artifacts_present": bool(source_artifacts_present),
        "missing_source_artifacts": [
            name for name, exists in source["source_exists"].items() if not exists
        ],
        "m2662_status_pass": _bool(m2662_summary.get("status_pass")),
        "m2662_gate_matrix_pass": bool(source_gate_matrix_pass),
        "m2662_claim_boundary_pass": bool(source_claim_boundary_pass),
        "m2662_panel_spec_row_count": len(panel_rows),
        "m2662_measured_behavior_row_count": len(measured_rows),
        "m2662_protected_gate_row_count": len(protected_gate_rows),
        "fresh_protected_seed_count": len(seed_ids),
        "fresh_protected_seed_ids": seed_ids,
        "subject_failure_taxonomy_row_count": len(subject_rows),
        "axis_failure_taxonomy_row_count": len(axis_rows),
        "metric_failure_taxonomy_row_count": len(metric_rows),
        "combined_failure_taxonomy_row_count": len(combined_rows),
        "claim_boundary_row_count": len(claim_rows),
        "protected_gate_blocking_row_count": int(protected_blocking_count),
        "protected_gate_passing_row_count": int(len(protected_gate_rows) - protected_blocking_count),
        "protected_gate_regressed_row_count": int(protected_regressed_count),
        "all_policy_subjects_blocking": {row["subject_id"] for row in subject_rows} == POLICY_SUBJECTS
        and all(_int(row["blocking_gate_row_count"]) > 0 for row in subject_rows),
        "all_axes_blocking": all(_int(row["blocking_gate_row_count"]) > 0 for row in axis_rows),
        "all_metrics_blocking": all(_int(row["blocking_gate_row_count"]) > 0 for row in metric_rows),
        "broad_protected_blocker_preserved": bool(broad_blocker_preserved),
        "target_protected_split_preserved": bool(target_protected_split_preserved),
        "protected_rows_in_success_denominator": False,
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "hidden_oracle_actor_input_detected": bool(not hidden_oracle_clean),
        "taxonomy_labels_actor_visible": bool(taxonomy_labels_actor_visible),
        "claim_boundary_pass": bool(claim_boundary_pass),
        "follow_up_manifest_registered": bool(source["source_exists"]["follow_up_manifest"]),
        **FALSE_CLAIM_FLAGS,
    }


def build_gate_matrix_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    gates = (
        ("source_artifacts_present", "artifact", metrics["source_artifacts_present"], True, "metric_artifact"),
        ("m2662_status_pass", "source_status", metrics["m2662_status_pass"], True, "lineage_invalid"),
        ("m2662_gate_matrix_pass", "source_status", metrics["m2662_gate_matrix_pass"], True, "lineage_invalid"),
        ("m2662_claim_boundary_pass", "source_status", metrics["m2662_claim_boundary_pass"], True, "lineage_invalid"),
        ("m2662_panel_spec_row_count", "source_shape", metrics["m2662_panel_spec_row_count"], 12, "metric_artifact"),
        (
            "m2662_measured_behavior_row_count",
            "source_shape",
            metrics["m2662_measured_behavior_row_count"],
            60,
            "metric_artifact",
        ),
        ("m2662_protected_gate_row_count", "source_shape", metrics["m2662_protected_gate_row_count"], 27, "metric_artifact"),
        ("fresh_protected_seed_count", "fresh_panel", metrics["fresh_protected_seed_count"], 4, "scenario_sampling_failure"),
        ("subject_failure_taxonomy_row_count", "taxonomy_shape", metrics["subject_failure_taxonomy_row_count"], 3, "metric_artifact"),
        ("axis_failure_taxonomy_row_count", "taxonomy_shape", metrics["axis_failure_taxonomy_row_count"], 3, "metric_artifact"),
        ("metric_failure_taxonomy_row_count", "taxonomy_shape", metrics["metric_failure_taxonomy_row_count"], 3, "metric_artifact"),
        ("combined_failure_taxonomy_row_count", "taxonomy_shape", metrics["combined_failure_taxonomy_row_count"], 9, "metric_artifact"),
        ("claim_boundary_row_count", "claim_boundary", metrics["claim_boundary_row_count"], len(CLAIM_CHECKS), "objective_overfit"),
        (
            "protected_gate_blocking_row_count",
            "protected_blocker",
            metrics["protected_gate_blocking_row_count"],
            25,
            "behavior_regression",
        ),
        (
            "protected_gate_regressed_row_count",
            "protected_blocker",
            metrics["protected_gate_regressed_row_count"],
            79,
            "behavior_regression",
        ),
        ("all_policy_subjects_blocking", "protected_blocker", metrics["all_policy_subjects_blocking"], True, "behavior_regression"),
        ("all_axes_blocking", "protected_blocker", metrics["all_axes_blocking"], True, "behavior_regression"),
        ("all_metrics_blocking", "protected_blocker", metrics["all_metrics_blocking"], True, "behavior_regression"),
        (
            "broad_protected_blocker_preserved",
            "protected_blocker",
            metrics["broad_protected_blocker_preserved"],
            True,
            "proof_washout",
        ),
        (
            "target_protected_split_preserved",
            "claim_boundary",
            metrics["target_protected_split_preserved"],
            True,
            "objective_overfit",
        ),
        (
            "protected_rows_in_success_denominator",
            "claim_boundary",
            metrics["protected_rows_in_success_denominator"],
            False,
            "objective_overfit",
        ),
        (
            "actor_contract_shape_72_action_3",
            "actor_contract",
            metrics["actor_contract_shape_72_action_3"],
            True,
            "contract_violation",
        ),
        (
            "hidden_oracle_actor_input_detected",
            "actor_contract",
            metrics["hidden_oracle_actor_input_detected"],
            False,
            "contract_violation",
        ),
        (
            "taxonomy_labels_actor_visible",
            "actor_contract",
            metrics["taxonomy_labels_actor_visible"],
            False,
            "contract_violation",
        ),
        ("claim_boundary_pass", "claim_boundary", metrics["claim_boundary_pass"], True, "objective_overfit"),
        (
            "follow_up_manifest_registered",
            "lineage",
            metrics["follow_up_manifest_registered"],
            True,
            "lineage_invalid",
        ),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("winner_selected", "forbidden_claim", metrics["winner_selected"], False, "objective_overfit"),
        ("checkpoint_promoted", "forbidden_claim", metrics["checkpoint_promoted"], False, "objective_overfit"),
        ("success_rate_computed", "forbidden_claim", metrics["success_rate_computed"], False, "objective_overfit"),
        (
            "driver_performance_claim_made",
            "forbidden_claim",
            metrics["driver_performance_claim_made"],
            False,
            "objective_overfit",
        ),
        ("paper_claim_made", "forbidden_claim", metrics["paper_claim_made"], False, "objective_overfit"),
        (
            "finite_window_vs_gru_claim_made",
            "forbidden_claim",
            metrics["finite_window_vs_gru_claim_made"],
            False,
            "objective_overfit",
        ),
        (
            "current_sim_verdict_claim_made",
            "forbidden_claim",
            metrics["current_sim_verdict_claim_made"],
            False,
            "objective_overfit",
        ),
        (
            "high_fidelity_validation_claim_made",
            "forbidden_claim",
            metrics["high_fidelity_validation_claim_made"],
            False,
            "objective_overfit",
        ),
        (
            "level3_self_id_claim_made",
            "forbidden_claim",
            metrics["level3_self_id_claim_made"],
            False,
            "objective_overfit",
        ),
        (
            "full_ideal_driver_gate_passed",
            "forbidden_claim",
            metrics["full_ideal_driver_gate_passed"],
            False,
            "objective_overfit",
        ),
    )
    rows = []
    for gate_id, family, observed, expected, failure_type in gates:
        status = observed == expected
        rows.append(
            {
                "gate_id": f"m2664_gate_{gate_id}",
                "gate_family": family,
                "status_pass": bool(status),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status else failure_type,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_summary(metrics: dict[str, Any], gate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        metrics["source_artifacts_present"]
        and metrics["m2662_status_pass"]
        and metrics["m2662_gate_matrix_pass"]
        and metrics["m2662_claim_boundary_pass"]
        and metrics["m2662_panel_spec_row_count"] == 12
        and metrics["m2662_measured_behavior_row_count"] == 60
        and metrics["m2662_protected_gate_row_count"] == 27
        and metrics["fresh_protected_seed_count"] == 4
        and metrics["subject_failure_taxonomy_row_count"] == 3
        and metrics["axis_failure_taxonomy_row_count"] == 3
        and metrics["metric_failure_taxonomy_row_count"] == 3
        and metrics["combined_failure_taxonomy_row_count"] == 9
        and metrics["claim_boundary_row_count"] == len(CLAIM_CHECKS)
        and metrics["protected_gate_blocking_row_count"] == 25
        and metrics["protected_gate_regressed_row_count"] == 79
        and metrics["all_policy_subjects_blocking"]
        and metrics["all_axes_blocking"]
        and metrics["all_metrics_blocking"]
        and metrics["broad_protected_blocker_preserved"]
        and metrics["target_protected_split_preserved"]
        and not metrics["protected_rows_in_success_denominator"]
        and metrics["actor_contract_shape_72_action_3"]
        and not metrics["hidden_oracle_actor_input_detected"]
        and not metrics["taxonomy_labels_actor_visible"]
        and metrics["claim_boundary_pass"]
        and metrics["follow_up_manifest_registered"]
        and gate_matrix_pass
        and not metrics["ranking_run"]
        and not metrics["winner_selected"]
        and not metrics["checkpoint_promoted"]
        and not metrics["success_rate_computed"]
        and not metrics["driver_performance_claim_made"]
        and not metrics["paper_claim_made"]
        and not metrics["finite_window_vs_gru_claim_made"]
        and not metrics["current_sim_verdict_claim_made"]
        and not metrics["high_fidelity_validation_claim_made"]
        and not metrics["level3_self_id_claim_made"]
        and not metrics["full_ideal_driver_gate_passed"]
    )
    return {
        **metrics,
        "result_class": (
            "engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "gate_matrix_pass": bool(gate_matrix_pass),
        "gate_matrix_row_count": len(gate_rows),
    }


def render_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# M2664 Engineering Controller Route A Protected Mitigation Fresh Panel Failure Taxonomy Materialization Preflight",
        "",
        "- status: completed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2664-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-preflight.json`",
        "- route plan: `docs/post-m2470-route-plan.md`",
        "- implementation: `src/autodrift/engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy.py`",
        f"- summary: `{summary['summary']}`",
        f"- subject taxonomy rows: `{summary['subject_failure_taxonomy_rows']}`",
        f"- axis taxonomy rows: `{summary['axis_failure_taxonomy_rows']}`",
        f"- metric taxonomy rows: `{summary['metric_failure_taxonomy_rows']}`",
        f"- combined taxonomy rows: `{summary['combined_failure_taxonomy_rows']}`",
        f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
        f"- gate matrix: `{summary['gate_matrix']}`",
        f"- next milestone: `{summary['next_blocker']}`",
        "- reset/step/rollout/replay/validation/training/PPO executed: `false`",
        "- ranking/winner/promotion/success-rate/performance claims: `false`",
        "",
        "## Materialized Taxonomy",
        "",
        "M2664 reanalyzes the accepted M2662 fresh protected mitigation panel",
        "into subject, axis, metric, and subject-axis failure taxonomy rows. The",
        "taxonomy is artifact metadata only and is not actor-visible.",
        "",
        "Accepted summary:",
        "",
        "```text",
        f"status_pass: {str(summary['status_pass']).lower()}",
        f"m2662_panel_spec_row_count: {summary['m2662_panel_spec_row_count']}",
        f"m2662_measured_behavior_row_count: {summary['m2662_measured_behavior_row_count']}",
        f"m2662_protected_gate_row_count: {summary['m2662_protected_gate_row_count']}",
        f"fresh_protected_seed_count: {summary['fresh_protected_seed_count']}",
        f"fresh_protected_seed_ids: {','.join(summary['fresh_protected_seed_ids'])}",
        f"subject_failure_taxonomy_row_count: {summary['subject_failure_taxonomy_row_count']}",
        f"axis_failure_taxonomy_row_count: {summary['axis_failure_taxonomy_row_count']}",
        f"metric_failure_taxonomy_row_count: {summary['metric_failure_taxonomy_row_count']}",
        f"combined_failure_taxonomy_row_count: {summary['combined_failure_taxonomy_row_count']}",
        f"protected_gate_blocking_row_count: {summary['protected_gate_blocking_row_count']}",
        f"protected_gate_regressed_row_count: {summary['protected_gate_regressed_row_count']}",
        f"gate_matrix_pass: {str(summary['gate_matrix_pass']).lower()}",
        "```",
        "",
        "## Boundary",
        "",
        "The protected mitigation rows remain outside success denominators. M2664",
        "does not rank controller families, select a winner, promote a checkpoint,",
        "compute success rate, validate a controller, or claim driver performance,",
        "paper-level evidence, finite-window-vs-GRU result, current-sim verdict,",
        "high-fidelity validation, full ideal driver completion, or self-ID.",
        "",
        "Route to:",
        "",
        "```text",
        str(summary["next_blocker"]),
        "```",
    ]
    return "\n".join(lines) + "\n"


def _taxonomy_row(
    group: list[dict[str, str]],
    *,
    row_id: str,
    fieldnames: list[str],
    seed_ids: list[str],
    subject_id: str = "",
    dynamics_axis_id: str = "",
    metric: str = "",
) -> dict[str, Any]:
    gate_count = len(group)
    blocking_count = sum(_bool(row.get("blocks_claims")) for row in group)
    regressed_count = sum(_int(row.get("regressed_row_count")) for row in group)
    improved_count = sum(_int(row.get("improved_row_count")) for row in group)
    blocking_fraction = float(blocking_count / gate_count) if gate_count else 0.0
    row = {
        "taxonomy_id": row_id,
        "subject_id": subject_id,
        "dynamics_axis_id": dynamics_axis_id,
        "dynamics_axis_family": "",
        "metric": metric,
        "metric_direction": "",
        "gate_row_count": gate_count,
        "blocking_gate_row_count": int(blocking_count),
        "passing_gate_row_count": int(gate_count - blocking_count),
        "regressed_row_count": int(regressed_count),
        "improved_row_count": int(improved_count),
        "subject_count": len({row["subject_id"] for row in group}),
        "axis_count": len({row["dynamics_axis_id"] for row in group}),
        "metric_count": len({row["metric"] for row in group}),
        "seed_count": len(seed_ids),
        "seed_ids": ";".join(seed_ids),
        "blocking_fraction": round(blocking_fraction, 6),
        "blocking_metrics": "",
        "passing_metrics": "",
        "primary_failure_family": _failure_family(
            gate_count=gate_count,
            blocking_count=blocking_count,
            regressed_count=regressed_count,
        ),
        "protected_blocker_preserved": bool(blocking_count > 0 and regressed_count > 0),
        "protected_rows_in_success_denominator": False,
        "ranking_or_winner_field_emitted": False,
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }
    return {field: row.get(field, "") for field in fieldnames}


def _failure_family(*, gate_count: int, blocking_count: int, regressed_count: int) -> str:
    if gate_count and blocking_count == gate_count:
        return "saturated_protected_blocker"
    if blocking_count > 0 and regressed_count > 0:
        return "mixed_protected_blocker"
    return "non_blocking_monitor"


def _seed_ids(panel_rows: list[dict[str, str]], measured_rows: list[dict[str, str]]) -> list[str]:
    panel_seeds = {str(row.get("seed", "")) for row in panel_rows if row.get("seed")}
    measured_seeds = {str(row.get("seed", "")) for row in measured_rows if row.get("seed")}
    return sorted(panel_seeds | measured_seeds, key=int)


def _group_by(rows: list[dict[str, str]], keys: tuple[str, ...]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return dict(grouped)


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=M2662_SUMMARY)
    parser.add_argument("--panel-spec-rows", type=Path, default=M2662_PANEL_SPEC_ROWS)
    parser.add_argument("--measured-behavior-rows", type=Path, default=M2662_MEASURED_BEHAVIOR_ROWS)
    parser.add_argument("--protected-mitigation-gates", type=Path, default=M2662_PROTECTED_MITIGATION_GATES)
    parser.add_argument("--claim-boundary-rows", type=Path, default=M2662_CLAIM_BOUNDARY_ROWS)
    parser.add_argument("--gate-matrix", type=Path, default=M2662_GATE_MATRIX)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_failure_taxonomy(
        args.output_dir,
        summary_path=args.summary,
        panel_spec_rows_path=args.panel_spec_rows,
        measured_behavior_rows_path=args.measured_behavior_rows,
        protected_mitigation_gates_path=args.protected_mitigation_gates,
        claim_boundary_rows_path=args.claim_boundary_rows,
        gate_matrix_path=args.gate_matrix,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")


if __name__ == "__main__":
    main()
